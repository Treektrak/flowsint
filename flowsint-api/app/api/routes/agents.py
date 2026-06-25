"""Роуты ИИ-агентов-экспертов: анализ графа расследования панелью экспертов."""
import math
import os
import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from flowsint_core.core.agents import (
    EXPERTS,
    SF_PRESETS,
    build_user_prompt,
    extract_graph,
    generate_report_html_pdf,
    generate_report_pdf,
    run_panel,
    serialize_graph,
    sf_events_to_graph,
    sf_list_modules,
    sf_run_scan,
)
from flowsint_core.core.graph import GraphNode
from flowsint_core.core.llm import create_llm_provider
from flowsint_core.core.models import Profile
from flowsint_core.core.postgre_db import get_db
from flowsint_core.core.services import create_chat_service
from flowsint_core.core.services import create_sketch_service
from flowsint_core.core.services.vault_service import create_vault_service
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user


def _resolve_provider(db: Session, owner_id, provider_name: Optional[str], model: Optional[str]):
    if provider_name:
        vault = create_vault_service(db)
        api_key = vault.get_secret(owner_id, f"{provider_name.upper()}_API_KEY")
        return create_llm_provider(provider=provider_name, api_key=api_key, model=model)
    return create_chat_service(db).get_llm_provider(owner_id)

router = APIRouter()

# Доступные провайдеры и их модели (id + читаемая подпись) для выбора в UI
PROVIDER_MODELS = {
    "anthropic": {
        "label": "Anthropic (Claude)",
        "models": [
            {"id": "claude-haiku-4-5-20251001", "label": "Haiku 4.5 (быстрая)"},
            {"id": "claude-sonnet-4-6", "label": "Sonnet 4.6 (сбалансированная)"},
            {"id": "claude-opus-4-8", "label": "Opus 4.8 (самая мощная)"},
        ],
    },
    "openai": {
        "label": "OpenAI",
        "models": [
            {"id": "gpt-4o", "label": "GPT-4o"},
            {"id": "gpt-4o-mini", "label": "GPT-4o mini (быстрая)"},
        ],
    },
    "deepseek": {
        "label": "DeepSeek",
        "models": [
            {"id": "deepseek-chat", "label": "DeepSeek Chat"},
            {"id": "deepseek-reasoner", "label": "DeepSeek Reasoner (рассуждающая)"},
        ],
    },
    "mistral": {
        "label": "Mistral",
        "models": [
            {"id": "mistral-large-latest", "label": "Mistral Large"},
            {"id": "mistral-small-latest", "label": "Mistral Small"},
        ],
    },
}

_FONT_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "fonts")
)


async def _analyze(
    sketch_id: str, body: "AnalyzeRequest", db: Session, owner_id
) -> dict:
    sketch_service = create_sketch_service(db)
    try:
        graph = sketch_service.get_graph(UUID(sketch_id), owner_id, None)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"Граф не найден: {exc}")

    nodes = graph.get("nds", []) if isinstance(graph, dict) else []
    rels = graph.get("rls", []) if isinstance(graph, dict) else []
    if not nodes:
        raise HTTPException(status_code=400, detail="Граф пуст — нечего анализировать.")

    graph_text = serialize_graph(nodes, rels)
    user_prompt = build_user_prompt(graph_text, body.investigation_name or "")

    try:
        if body.provider:
            # явный выбор провайдера/модели из UI: ключ берём из Vault
            vault = create_vault_service(db)
            vault_key = f"{body.provider.upper()}_API_KEY"
            api_key = vault.get_secret(owner_id, vault_key)
            provider = create_llm_provider(
                provider=body.provider, api_key=api_key, model=body.model
            )
        else:
            # провайдер по умолчанию (LLM_PROVIDER + ключ из Vault)
            provider = create_chat_service(db).get_llm_provider(owner_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail=(
                "Не настроен LLM-провайдер или отсутствует API-ключ в Хранилище. "
                f"Подробности: {exc}"
            ),
        )

    result = await run_panel(provider, user_prompt, body.expert_keys)
    result["sketch_id"] = sketch_id
    result["nodes_count"] = len(nodes)
    result["rels_count"] = len(rels)
    result["investigation_name"] = body.investigation_name or ""
    # для отрисовки схемы в PDF
    result["graph_nodes"] = nodes
    result["graph_rels"] = rels
    return result


class AnalyzeRequest(BaseModel):
    expert_keys: Optional[List[str]] = None
    investigation_name: Optional[str] = ""
    provider: Optional[str] = None
    model: Optional[str] = None


@router.get("/experts")
def list_experts(current_user: Profile = Depends(get_current_user)):
    """Список доступных ИИ-агентов-экспертов."""
    return [
        {"key": e.key, "name": e.name, "emoji": e.emoji} for e in EXPERTS
    ]


@router.get("/models")
def list_models(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Список LLM-провайдеров и моделей. Помечает те, для которых есть ключ в Vault."""
    vault = create_vault_service(db)
    out = []
    for provider, cfg in PROVIDER_MODELS.items():
        has_key = bool(vault.get_secret(current_user.id, f"{provider.upper()}_API_KEY"))
        out.append(
            {
                "provider": provider,
                "label": cfg["label"],
                "models": cfg["models"],
                "has_key": has_key,
            }
        )
    return out


@router.post("/sketch/{sketch_id}/analyze")
async def analyze_sketch(
    sketch_id: str,
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Запускает панель ИИ-экспертов над графом скетча и возвращает их
    заключения и сводный синтез (JSON)."""
    result = await _analyze(sketch_id, body, db, current_user.id)
    # граф нужен только для PDF — в JSON-ответе его не дублируем
    result.pop("graph_nodes", None)
    result.pop("graph_rels", None)
    return result


@router.post("/sketch/{sketch_id}/report")
async def report_sketch(
    sketch_id: str,
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Запускает панель экспертов и возвращает готовый PDF-отчёт."""
    result = await _analyze(sketch_id, body, db, current_user.id)
    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")
    try:
        # Профессиональная HTML/CSS-вёрстка (WeasyPrint). При сбое — запасной fpdf2.
        try:
            pdf_bytes = generate_report_html_pdf(result, generated_at=generated_at)
        except Exception:
            pdf_bytes = generate_report_pdf(result, _FONT_DIR, generated_at=generated_at)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Не удалось сформировать PDF: {exc}")

    filename = "flowsint-report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class AiImportRequest(BaseModel):
    text: str
    provider: Optional[str] = None
    model: Optional[str] = None


@router.post("/sketch/{sketch_id}/ai-import")
async def ai_import(
    sketch_id: str,
    body: AiImportRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """ИИ-извлечение сущностей и связей из текста с добавлением их в граф."""
    if not (body.text or "").strip():
        raise HTTPException(status_code=400, detail="Пустой текст.")
    try:
        provider = _resolve_provider(db, current_user.id, body.provider, body.model)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"LLM не настроен: {exc}")

    result = await extract_graph(provider, body.text)
    nodes = result.get("nodes", [])
    edges = result.get("edges", [])
    if not nodes:
        raise HTTPException(status_code=422, detail=result.get("error") or "Сущности не найдены в тексте.")

    sketch_service = create_sketch_service(db)
    now = datetime.utcnow().isoformat()
    keymap = {}
    added = 0
    for i, n in enumerate(nodes):
        ang = 2 * math.pi * i / max(len(nodes), 1)
        gn = GraphNode(
            id="tmp-" + uuid.uuid4().hex,
            nodeLabel=n["label"],
            nodeType=n["type"],
            nodeShape="circle",
            nodeMetadata={"created_at": now},
            nodeProperties=n["properties"],
            x=400.0 + 260.0 * math.cos(ang),
            y=320.0 + 260.0 * math.sin(ang),
        )
        try:
            res = sketch_service.add_node(UUID(sketch_id), current_user.id, gn)
            node_obj = res.get("node") if isinstance(res, dict) else res
            node_id = getattr(node_obj, "id", None)
            if node_id is None and isinstance(node_obj, dict):
                node_id = node_obj.get("id")
            if node_id:
                keymap[n["key"]] = node_id
                added += 1
        except Exception:
            continue

    ecount = 0
    for e in edges:
        s, t = keymap.get(e["source"]), keymap.get(e["target"])
        if not s or not t:
            continue
        try:
            sketch_service.add_relationship(UUID(sketch_id), current_user.id, s, t, e["label"])
            ecount += 1
        except Exception:
            continue

    return {"nodes_added": added, "edges_added": ecount}


def _add_nodes_edges(sketch_service, sketch_id: str, owner_id, nodes, edges):
    """Добавляет извлечённые узлы и связи в граф. Возвращает (added, ecount)."""
    now = datetime.utcnow().isoformat()
    keymap = {}
    added = 0
    n = len(nodes)
    for i, nd in enumerate(nodes):
        ang = 2 * math.pi * i / max(n, 1)
        ring = 220 + (i % 3) * 120
        gn = GraphNode(
            id="tmp-" + uuid.uuid4().hex,
            nodeLabel=nd["label"], nodeType=nd["type"], nodeShape="circle",
            nodeMetadata={"created_at": now}, nodeProperties=nd["properties"],
            x=500.0 + ring * math.cos(ang), y=380.0 + ring * math.sin(ang),
        )
        try:
            res = sketch_service.add_node(UUID(sketch_id), owner_id, gn)
            node_obj = res.get("node") if isinstance(res, dict) else res
            node_id = getattr(node_obj, "id", None)
            if node_id is None and isinstance(node_obj, dict):
                node_id = node_obj.get("id")
            if node_id:
                keymap[nd["key"]] = node_id
                added += 1
        except Exception:
            continue
    ecount = 0
    for e in edges:
        s, t = keymap.get(e["source"]), keymap.get(e["target"])
        if not s or not t:
            continue
        try:
            sketch_service.add_relationship(UUID(sketch_id), owner_id, s, t, e["label"])
            ecount += 1
        except Exception:
            continue
    return added, ecount


@router.get("/spiderfoot/modules")
def spiderfoot_modules(current_user: Profile = Depends(get_current_user)):
    """Список модулей встроенного SpiderFoot и доступные пресеты."""
    mods = sf_list_modules()
    return {"count": len(mods), "modules": mods, "presets": list(SF_PRESETS.keys())}


class SpiderfootScanRequest(BaseModel):
    target: str
    preset: Optional[str] = "fast"
    modules: Optional[List[str]] = None


@router.post("/sketch/{sketch_id}/spiderfoot-scan")
async def spiderfoot_scan(
    sketch_id: str,
    body: SpiderfootScanRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Запускает встроенный SpiderFoot по цели и импортирует результаты в граф."""
    target = (body.target or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="Не указана цель скана.")
    try:
        events = sf_run_scan(target, modules=body.modules, preset=body.preset or "fast")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Ошибка SpiderFoot: {exc}")

    nodes, edges = sf_events_to_graph(events, target)
    if not nodes:
        return {"nodes_added": 0, "edges_added": 0, "events": len(events)}

    sketch_service = create_sketch_service(db)
    added, ecount = _add_nodes_edges(sketch_service, sketch_id, current_user.id, nodes, edges)
    return {"nodes_added": added, "edges_added": ecount, "events": len(events)}
