"""Оркестратор панели ИИ-агентов-экспертов.

Запускает выбранных экспертов параллельно над одним графом расследования,
затем сводит их заключения синтез-агентом в единое резюме.
"""
import asyncio
from typing import Any, Dict, List, Optional

from ..llm import ChatMessage, LLMProvider, MessageRole
from .experts import EXPERTS, SYNTHESIS_PROMPT, Expert


async def _run_expert(
    provider: LLMProvider, expert: Expert, user_prompt: str
) -> Dict[str, Any]:
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=expert.system_prompt),
        ChatMessage(role=MessageRole.USER, content=user_prompt),
    ]
    try:
        analysis = await provider.complete(messages)
        return {
            "key": expert.key,
            "name": expert.name,
            "emoji": expert.emoji,
            "analysis": analysis,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "key": expert.key,
            "name": expert.name,
            "emoji": expert.emoji,
            "analysis": None,
            "error": str(exc),
        }


async def _synthesize(
    provider: LLMProvider, expert_results: List[Dict[str, Any]]
) -> Optional[str]:
    sections = []
    for r in expert_results:
        if r.get("analysis"):
            sections.append(f"## {r['emoji']} {r['name']}\n\n{r['analysis']}")
    if not sections:
        return None
    joined = "\n\n---\n\n".join(sections)
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=SYNTHESIS_PROMPT),
        ChatMessage(
            role=MessageRole.USER,
            content=f"Заключения экспертов:\n\n{joined}",
        ),
    ]
    try:
        return await provider.complete(messages)
    except Exception as exc:  # noqa: BLE001
        return f"(Не удалось выполнить синтез: {exc})"


async def run_panel(
    provider: LLMProvider,
    user_prompt: str,
    expert_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Запускает панель экспертов и синтез. Возвращает заключения и сводку."""
    selected: List[Expert] = (
        [e for e in EXPERTS if e.key in expert_keys] if expert_keys else list(EXPERTS)
    )

    expert_results = await asyncio.gather(
        *[_run_expert(provider, e, user_prompt) for e in selected]
    )
    expert_results = list(expert_results)

    synthesis = await _synthesize(provider, expert_results)

    return {
        "experts": expert_results,
        "synthesis": synthesis,
    }
