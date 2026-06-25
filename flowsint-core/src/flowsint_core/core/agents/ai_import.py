"""ИИ-извлечение сущностей и связей из произвольного текста в граф расследования.

Принимает текст (выписка, переписка, лог, документ), просит LLM выделить
сущности известных Traceon-типов и связи между ними, возвращает структуру
для добавления в граф.
"""
import json
import re
from typing import Any, Dict, List

from ..llm import ChatMessage, LLMProvider, MessageRole

# Поддерживаемые типы сущностей (ключи). cryptowallettransaction исключён —
# его модель ломает чтение графа; крипто-операции кладём как phrase.
_TYPES = [
    "phrase", "location", "individual", "username", "organization", "phone",
    "email", "socialaccount", "message", "asn", "cidr", "domain", "website",
    "ip", "port", "dnsrecord", "sslcertificate", "webtracker", "credential",
    "session", "device", "malware", "weapon", "document", "file",
    "bankaccount", "creditcard", "leak", "cryptowallet", "cryptonft",
]

# основное поле-значение для каждого типа (label_key)
_LABEL_KEY = {
    "phrase": "text", "location": "address", "individual": "full_name",
    "username": "value", "organization": "name", "phone": "number",
    "email": "email", "socialaccount": "username", "message": "content",
    "asn": "asn_str", "cidr": "network", "domain": "domain", "website": "url",
    "ip": "address", "port": "number", "dnsrecord": "value",
    "sslcertificate": "subject", "webtracker": "name", "credential": "username",
    "session": "session_id", "device": "device_id", "malware": "name",
    "weapon": "name", "document": "title", "file": "filename",
    "bankaccount": "account_number", "creditcard": "card_number",
    "leak": "name", "cryptowallet": "address", "cryptonft": "name",
}

_SYSTEM = (
    "Ты — система извлечения структурированных данных для OSINT-графа расследования. "
    "Из присланного текста выдели РЕАЛЬНЫЕ сущности и связи между ними.\n\n"
    "Доступные типы сущностей (используй строго эти ключи):\n"
    + ", ".join(_TYPES) + "\n\n"
    "Правила:\n"
    "- Извлекай только сущности, явно присутствующие в тексте; не выдумывай.\n"
    "- Для крипто-транзакций используй тип phrase (с описанием в text).\n"
    "- Каждой сущности дай короткий уникальный key (n1, n2, ...), type из списка, "
    "label (человекочитаемая подпись) и properties (значимые поля на русском).\n"
    "- Связи (edges) — осмысленные, с краткой подписью на русском в ВЕРХНЕМ_РЕГИСТРЕ "
    "(например ВЛАДЕЕТ, ПЕРЕВОД, СВЯЗАН_С, EMAIL).\n\n"
    "Верни СТРОГО валидный JSON без пояснений и markdown, формат:\n"
    '{"nodes":[{"key":"n1","type":"domain","label":"example.com",'
    '"properties":{"domain":"example.com"}}],'
    '"edges":[{"source":"n1","target":"n2","label":"СВЯЗАН_С"}]}'
)


def _parse_json(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if m:
        raw = m.group(1)
    else:
        m = re.search(r"(\{.*\})", raw, re.DOTALL)
        if m:
            raw = m.group(1)
    return json.loads(raw)


async def extract_graph(provider: LLMProvider, text: str) -> Dict[str, Any]:
    """Извлекает {nodes, edges} из текста через LLM."""
    text = (text or "").strip()
    if not text:
        return {"nodes": [], "edges": []}
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=_SYSTEM),
        ChatMessage(role=MessageRole.USER, content=f"ТЕКСТ ДЛЯ АНАЛИЗА:\n\n{text[:16000]}"),
    ]
    raw = await provider.complete(messages)
    try:
        data = _parse_json(raw)
    except Exception:
        return {"nodes": [], "edges": [], "error": "Не удалось разобрать ответ ИИ."}

    nodes = data.get("nodes", []) if isinstance(data, dict) else []
    edges = data.get("edges", []) if isinstance(data, dict) else []

    # нормализация
    clean_nodes = []
    seen_keys = set()
    for n in nodes:
        if not isinstance(n, dict):
            continue
        ntype = str(n.get("type", "")).lower().strip()
        if ntype not in _TYPES:
            ntype = "phrase"
        key = str(n.get("key") or "").strip()
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        label = str(n.get("label") or n.get("properties", {}).get(_LABEL_KEY.get(ntype, ""), "") or "?")
        props = n.get("properties") if isinstance(n.get("properties"), dict) else {}
        props = {str(k): v for k, v in props.items()}
        props["nodeLabel"] = label
        # гарантируем наличие label_key
        lk = _LABEL_KEY.get(ntype)
        if lk and lk not in props:
            props[lk] = label
        clean_nodes.append({"key": key, "type": ntype, "label": label, "properties": props})

    clean_edges = []
    for e in edges:
        if not isinstance(e, dict):
            continue
        s, t = str(e.get("source") or ""), str(e.get("target") or "")
        if s in seen_keys and t in seen_keys and s != t:
            clean_edges.append({"source": s, "target": t, "label": str(e.get("label") or "СВЯЗАН_С")})

    return {"nodes": clean_nodes, "edges": clean_edges}
