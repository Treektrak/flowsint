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
from flowsint_core.core.models import Profile
from flowsint_core.core.postgre_db import get_db
from flowsint_core.core.services import create_chat_service
from flowsint_core.core.services import create_sketch_service
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user

router = APIRouter()

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

    chat_service = create_chat_service(db)
    try:
        provider = chat_service.get_llm_provider(owner_id)
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
    return result


class AnalyzeRequest(BaseModel):
    expert_keys: Optional[List[str]] = None
    investigation_name: Optional[str] = ""


@router.get("/experts")
def list_experts(current_user: Profile = Depends(get_current_user)):
    """Список доступных ИИ-агентов-экспертов."""
    return [
        {"key": e.key, "name": e.name, "emoji": e.emoji} for e in EXPERTS
    ]


@router.post("/sketch/{sketch_id}/analyze")
async def analyze_sketch(
    sketch_id: str,
    body: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Запускает панель ИИ-экспертов над графом скетча и возвращает их
    заключения и сводный синтез (JSON)."""
    return await _analyze(sketch_id, body, db, current_user.id)


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
