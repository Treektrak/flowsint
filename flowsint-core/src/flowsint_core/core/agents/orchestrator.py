"""Оркестратор панели ИИ-агентов-экспертов.

Запускает выбранных экспертов параллельно над одним графом расследования,
затем сводит их заключения синтез-агентом в единое резюме.
"""
import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple

from ..llm import ChatMessage, LLMProvider, MessageRole
from .experts import EXPERTS, LETTERS_PROMPT, SYNTHESIS_PROMPT, Expert


def _parse_tail(analysis: str) -> Tuple[str, List[str], Optional[str]]:
    """Извлекает из ответа эксперта строки «КЛЮЧЕВЫЕ СУЩНОСТИ:» и «ВЫВОД:»,
    возвращает (очищенный_текст, список_сущностей, вывод)."""
    key_entities: List[str] = []
    conclusion: Optional[str] = None

    m_ent = re.search(r"^\s*КЛЮЧЕВЫЕ\s+СУЩНОСТИ\s*:\s*(.+)$", analysis, re.MULTILINE | re.IGNORECASE)
    if m_ent:
        raw = m_ent.group(1).strip()
        key_entities = [e.strip(" •*-`«»\"'") for e in raw.split(",") if e.strip()]

    m_con = re.search(r"^\s*ВЫВОД\s*:\s*(.+)$", analysis, re.MULTILINE | re.IGNORECASE)
    if m_con:
        conclusion = m_con.group(1).strip()

    # убираем служебные строки из основного текста
    cleaned = re.sub(
        r"^\s*(КЛЮЧЕВЫЕ\s+СУЩНОСТИ|ВЫВОД)\s*:.*$", "", analysis,
        flags=re.MULTILINE | re.IGNORECASE,
    ).rstrip()
    return cleaned, key_entities, conclusion


async def _run_expert(
    provider: LLMProvider, expert: Expert, user_prompt: str
) -> Dict[str, Any]:
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=expert.system_prompt),
        ChatMessage(role=MessageRole.USER, content=user_prompt),
    ]
    try:
        raw = await provider.complete(messages)
        cleaned, key_entities, conclusion = _parse_tail(raw)
        return {
            "key": expert.key,
            "name": expert.name,
            "emoji": expert.emoji,
            "analysis": cleaned,
            "key_entities": key_entities,
            "conclusion": conclusion,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "key": expert.key,
            "name": expert.name,
            "emoji": expert.emoji,
            "analysis": None,
            "key_entities": [],
            "conclusion": None,
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


async def _generate_letters(provider: LLMProvider, user_prompt: str) -> Optional[str]:
    """Генерирует готовые шаблоны официальных писем-запросов в органы."""
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=LETTERS_PROMPT),
        ChatMessage(role=MessageRole.USER, content=user_prompt),
    ]
    try:
        return await provider.complete(messages)
    except Exception:  # noqa: BLE001
        return None


async def run_panel(
    provider: LLMProvider,
    user_prompt: str,
    expert_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Запускает панель экспертов, синтез и генерацию писем-запросов."""
    selected: List[Expert] = (
        [e for e in EXPERTS if e.key in expert_keys] if expert_keys else list(EXPERTS)
    )

    expert_results = list(
        await asyncio.gather(*[_run_expert(provider, e, user_prompt) for e in selected])
    )

    # синтез и письма-запросы параллельно
    synthesis, letters = await asyncio.gather(
        _synthesize(provider, expert_results),
        _generate_letters(provider, user_prompt),
    )

    return {
        "experts": expert_results,
        "synthesis": synthesis,
        "letters": letters,
    }
