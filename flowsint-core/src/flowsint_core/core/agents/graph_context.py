"""Сериализация графа расследования в текстовый контекст для LLM."""
from typing import Any, Dict, List


def _node_line(node: Dict[str, Any]) -> str:
    ntype = node.get("nodeType", "?")
    label = node.get("nodeLabel", "?")
    props = node.get("nodeProperties") or {}
    # значимые свойства, кроме служебных
    extras = []
    for k, v in props.items():
        if k in ("nodeLabel",) or v in (None, "", [], {}):
            continue
        extras.append(f"{k}={v}")
    suffix = f" ({'; '.join(extras)})" if extras else ""
    return f"- [{ntype}] {label}{suffix}"


def serialize_graph(nodes: List[Dict[str, Any]], rels: List[Dict[str, Any]]) -> str:
    """Превращает узлы и связи графа в компактный человекочитаемый текст."""
    id_to_label = {
        n.get("id"): f"{n.get('nodeLabel', '?')} [{n.get('nodeType', '?')}]"
        for n in nodes
    }

    lines: List[str] = []
    lines.append(f"СУЩНОСТИ ({len(nodes)}):")
    for n in nodes:
        lines.append(_node_line(n))

    lines.append("")
    lines.append(f"СВЯЗИ ({len(rels)}):")
    if not rels:
        lines.append("- (связей нет)")
    for r in rels:
        src = id_to_label.get(r.get("source"), "?")
        tgt = id_to_label.get(r.get("target"), "?")
        label = r.get("label") or "СВЯЗАН_С"
        lines.append(f"- {src} --{label}--> {tgt}")

    return "\n".join(lines)


def build_user_prompt(graph_text: str, investigation_name: str = "") -> str:
    header = (
        f"Граф расследования «{investigation_name}».\n\n" if investigation_name else ""
    )
    return (
        f"{header}Ниже приведён граф OSINT-расследования. Проанализируй его в рамках "
        f"своей экспертизы и сформируй аналитический раздел отчёта.\n\n"
        f"=== ДАННЫЕ ГРАФА ===\n{graph_text}\n=== КОНЕЦ ДАННЫХ ==="
    )
