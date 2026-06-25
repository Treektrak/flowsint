"""Роуты ИИ-агентов-экспертов: анализ графа расследования панелью экспертов."""
import os
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from flowsint_core.core.agents import (
    EXPERTS,
    build_user_prompt,
    generate_report_pdf,
    run_panel,
    serialize_graph,
)
from flowsint_core.core.llm import create_llm_provider
from flowsint_core.core.models import Profile
from flowsint_core.core.postgre_db import get_db
from flowsint_core.core.services import create_chat_service
from flowsint_core.core.services import create_sketch_service
from flowsint_core.core.services.vault_service import create_vault_service
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user

router = APIRouter()

# Доступные провайдеры и их модели (для выбора в UI)
PROVIDER_MODELS = {
    "anthropic": ["claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5-20251001"],
    "openai": ["gpt-4o", "gpt-4o-mini"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "mistral": ["mistral-large-latest", "mistral-small-latest"],
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
    for provider, models in PROVIDER_MODELS.items():
        has_key = bool(vault.get_secret(current_user.id, f"{provider.upper()}_API_KEY"))
        out.append({"provider": provider, "models": models, "has_key": has_key})
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
        pdf_bytes = generate_report_pdf(result, _FONT_DIR, generated_at=generated_at)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Не удалось сформировать PDF: {exc}")

    filename = "flowsint-report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
