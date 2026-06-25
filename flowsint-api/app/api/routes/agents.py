"""Роуты ИИ-агентов-экспертов: анализ графа расследования панелью экспертов."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from flowsint_core.core.agents import (
    EXPERTS,
    build_user_prompt,
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
    заключения и сводный синтез."""
    # 1. Получаем граф расследования
    sketch_service = create_sketch_service(db)
    try:
        graph = sketch_service.get_graph(UUID(sketch_id), current_user.id, None)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"Граф не найден: {exc}")

    nodes = graph.get("nds", []) if isinstance(graph, dict) else []
    rels = graph.get("rls", []) if isinstance(graph, dict) else []
    if not nodes:
        raise HTTPException(status_code=400, detail="Граф пуст — нечего анализировать.")

    # 2. Готовим контекст для экспертов
    graph_text = serialize_graph(nodes, rels)
    user_prompt = build_user_prompt(graph_text, body.investigation_name or "")

    # 3. Получаем LLM-провайдер (по LLM_PROVIDER + ключ из Vault пользователя)
    chat_service = create_chat_service(db)
    try:
        provider = chat_service.get_llm_provider(current_user.id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=400,
            detail=(
                "Не настроен LLM-провайдер или отсутствует API-ключ в Хранилище. "
                f"Подробности: {exc}"
            ),
        )

    # 4. Запускаем панель экспертов + синтез
    result = await run_panel(provider, user_prompt, body.expert_keys)
    result["sketch_id"] = sketch_id
    result["nodes_count"] = len(nodes)
    result["rels_count"] = len(rels)
    return result
