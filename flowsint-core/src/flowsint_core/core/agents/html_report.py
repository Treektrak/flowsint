"""Профессиональный PDF-отчёт через HTML/CSS (WeasyPrint).

Фирменная палитра Lunmart (синий/жёлтый/белый). Markdown заключений
рендерится в HTML (с таблицами), графики — инлайновый SVG: схема графа,
таймлайн событий, матрица связей, дашборд и диаграмма распределения.
"""
import html
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional

# --- Палитра Lunmart ---
BLUE_50 = "#eef4fb"
BLUE_100 = "#d9e6f3"
BLUE_200 = "#b3cce6"
BLUE_500 = "#1d5288"
BLUE_600 = "#0d3357"
BLUE_700 = "#082743"
YEL_100 = "#fff2c7"
YEL_400 = "#ffd35a"
YEL_500 = "#ffbf2f"
YEL_600 = "#e6a300"
BG = "#f5f7fb"
SURFACE = "#ffffff"
TEXT = "#0a2540"
MUTED = "#64748b"
SUBTLE = "#94a3b8"

_TYPE_COLORS = {
    "domain": "#2e8b57", "website": "#3ca06e", "ip": "#1d5288", "asn": "#825ac8",
    "cidr": "#9670d2", "dnsrecord": "#5a96b4", "sslcertificate": "#4682a0",
    "email": "#e6a300", "phone": "#d29640", "individual": "#c84646",
    "username": "#b45a8c", "socialaccount": "#aa6496", "organization": "#8c643c",
    "malware": "#a02828", "weapon": "#6e3c3c", "cryptowallet": "#c8a028",
    "cryptowallettransaction": "#be9628", "bankaccount": "#3c8c78",
    "creditcard": "#469682", "location": "#78825a", "device": "#646e82",
    "document": "#7878a0", "leak": "#b43c5a", "phrase": "#78787f",
    "message": "#82789c", "port": "#5082aa",
}
_DEFAULT_COLOR = "#6e7890"

_TYPE_RU = {
    "domain": "Домены", "website": "Сайты", "ip": "IP-адреса", "asn": "ASN",
    "cidr": "CIDR", "dnsrecord": "DNS-записи", "sslcertificate": "SSL-сертификаты",
    "email": "Email", "phone": "Телефоны", "individual": "Личности",
    "username": "Имена польз.", "socialaccount": "Соцаккаунты",
    "organization": "Организации", "malware": "ВПО", "weapon": "Оружие",
    "cryptowallet": "Криптокошельки", "cryptowallettransaction": "Криптотранзакции",
    "bankaccount": "Банк. счета", "creditcard": "Карты", "location": "Локации",
    "device": "Устройства", "document": "Документы", "leak": "Утечки",
    "phrase": "Фразы", "message": "Сообщения", "port": "Порты",
}

_DATE_FIELDS = (
    "date", "timestamp", "created_at", "date_creation", "valid_from",
    "valid_until", "first_seen", "last_seen", "birth_date", "death_date",
)
_DATE_RE = re.compile(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})|(\d{1,2})[.](\d{1,2})[.](\d{4})")


def _esc(s: Any) -> str:
    return html.escape(str(s if s is not None else ""))


def _extract_date(value):
    if not isinstance(value, str):
        return None
    m = _DATE_RE.search(value)
    if not m:
        return None
    if m.group(1):
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return f"{m.group(6)}-{int(m.group(5)):02d}-{int(m.group(4)):02d}"


def _md_to_html(md: str) -> str:
    import markdown
    return markdown.markdown(
        md or "", extensions=["tables", "sane_lists", "nl2br", "fenced_code"]
    )


# ---------- SVG-графики ----------

def _graph_svg(nodes, rels, highlight=None, width=760, height=420):
    if not nodes:
        return ""
    highlight = {h.lower() for h in (highlight or [])}
    have = all(n.get("x") is not None and n.get("y") is not None for n in nodes)
    pts = []
    pad = 30
    if have:
        xs = [float(n["x"]) for n in nodes]; ys = [float(n["y"]) for n in nodes]
        mnx, mxx, mny, mxy = min(xs), max(xs), min(ys), max(ys)
        dx = (mxx - mnx) or 1; dy = (mxy - mny) or 1
        for n in nodes:
            pts.append((pad + (float(n["x"]) - mnx) / dx * (width - 2 * pad),
                        pad + (float(n["y"]) - mny) / dy * (height - 2 * pad)))
    else:
        cx, cy = width / 2, height / 2; r = min(width, height) / 2 - pad
        for i in range(len(nodes)):
            a = 2 * math.pi * i / max(len(nodes), 1)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    idx = {n.get("id"): i for i, n in enumerate(nodes)}

    def is_hl(n):
        lbl = (n.get("nodeLabel") or "").lower()
        return any(h and (h in lbl or lbl in h) for h in highlight)
    any_hl = any(is_hl(n) for n in nodes) if highlight else False

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="graph">']
    for r in rels:
        si, ti = idx.get(r.get("source")), idx.get(r.get("target"))
        if si is None or ti is None:
            continue
        hl = any_hl and is_hl(nodes[si]) and is_hl(nodes[ti])
        col = YEL_600 if hl else "#cfd6e0"
        sw = 2 if hl else 1
        parts.append(f'<line x1="{pts[si][0]:.0f}" y1="{pts[si][1]:.0f}" x2="{pts[ti][0]:.0f}" y2="{pts[ti][1]:.0f}" stroke="{col}" stroke-width="{sw}"/>')
    for i, n in enumerate(nodes):
        hl = is_hl(n)
        col = _TYPE_COLORS.get((n.get("nodeType") or "").lower(), _DEFAULT_COLOR)
        if any_hl and not hl:
            col = "#d2d8e0"
        r = 8 if (hl or not any_hl) else 5
        x, y = pts[i]
        stroke = f' stroke="{YEL_600}" stroke-width="2.5"' if hl else ' stroke="#ffffff" stroke-width="1.5"'
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}"{stroke}/>')
        if hl or (not any_hl and len(nodes) <= 18):
            lbl = _esc((n.get("nodeLabel") or "")[:24])
            weight = "600" if hl else "400"
            fill = TEXT if hl else MUTED
            parts.append(f'<text x="{x + r + 3:.0f}" y="{y + 3:.0f}" font-size="10" font-weight="{weight}" fill="{fill}">{lbl}</text>')
    parts.append("</svg>")
    return "".join(parts)


def _timeline_html(nodes):
    events = []
    for n in nodes:
        props = n.get("nodeProperties") or {}
        for f in _DATE_FIELDS:
            d = _extract_date(props.get(f))
            if d:
                events.append((d, n.get("nodeLabel") or ""))
                break
    events = sorted(set(events))
    if len(events) < 2:
        return '<p class="muted">Недостаточно датированных событий для построения шкалы.</p>'
    rows = "".join(
        f'<div class="tl-item"><div class="tl-dot"></div><div class="tl-date">{_esc(d)}</div>'
        f'<div class="tl-event">{_esc(lbl)}</div></div>'
        for d, lbl in events
    )
    return f'<div class="timeline">{rows}</div>'


def _matrix_html(nodes, rels):
    if not nodes or not rels:
        return '<p class="muted">Недостаточно связей для построения матрицы.</p>'
    deg = {n.get("id"): 0 for n in nodes}
    pair = set()
    for r in rels:
        s, t = r.get("source"), r.get("target")
        if s in deg and t in deg:
            deg[s] += 1; deg[t] += 1; pair.add(frozenset((s, t)))
    top = [n for n in sorted(nodes, key=lambda n: deg.get(n.get("id"), 0), reverse=True)
           if deg.get(n.get("id"), 0) > 0][:14]
    if len(top) < 2:
        return '<p class="muted">Недостаточно связей для построения матрицы.</p>'
    ids = [n.get("id") for n in top]
    labels = [(n.get("nodeLabel") or "")[:18] for n in top]
    k = len(top)
    head = "".join(f'<th class="mx-num">{j+1}</th>' for j in range(k))
    body = ""
    for i in range(k):
        cells = ""
        for j in range(k):
            if i == j:
                cells += '<td class="mx-self"></td>'
            elif frozenset((ids[i], ids[j])) in pair:
                cells += '<td class="mx-on"></td>'
            else:
                cells += '<td class="mx-off"></td>'
        body += f'<tr><td class="mx-label">{i+1}. {_esc(labels[i])}</td>{cells}</tr>'
    return f'<table class="matrix"><tr><td></td>{head}</tr>{body}</table>'


def _dashboard_html(data):
    nodes = data.get("graph_nodes") or []
    rels = data.get("graph_rels") or []
    experts = [e for e in data.get("experts", []) if e.get("analysis")]
    keys = set()
    for e in experts:
        for k in e.get("key_entities") or []:
            keys.add(k.lower())
    ntypes = len({(n.get("nodeType") or "").lower() for n in nodes})
    cards = [
        (len(nodes), "сущностей"), (len(rels), "связей"), (ntypes, "типов"),
        (len(experts), "экспертиз"), (len(keys), "ключевых находок"),
    ]
    return '<div class="kpi">' + "".join(
        f'<div class="kpi-card"><div class="kpi-val">{v}</div><div class="kpi-lbl">{_esc(l)}</div></div>'
        for v, l in cards
    ) + "</div>"


def _entity_bars_html(nodes):
    counts = Counter((n.get("nodeType") or "?").lower() for n in nodes)
    if not counts:
        return ""
    mx = max(counts.values())
    rows = ""
    for t, c in counts.most_common():
        col = _TYPE_COLORS.get(t, _DEFAULT_COLOR)
        w = max(3, c / mx * 100)
        rows += (
            f'<div class="bar-row"><div class="bar-lbl">{_esc(_TYPE_RU.get(t, t))}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{w:.0f}%;background:{col}"></div></div>'
            f'<div class="bar-num">{c}</div></div>'
        )
    return f'<div class="bars">{rows}</div>'


# ---------- CSS ----------

def _css() -> str:
    return f"""
@page {{
  size: A4; margin: 18mm 16mm 20mm 16mm;
  @bottom-center {{ content: "Traceon · ИИ-аналитика · стр. " counter(page) " из " counter(pages);
    font-size: 8pt; color: {SUBTLE}; }}
}}
* {{ box-sizing: border-box; }}
body {{ font-family: "DejaVu Sans", sans-serif; color: {TEXT}; font-size: 10pt; line-height: 1.5; }}
h1,h2,h3,h4 {{ color: {BLUE_600}; line-height: 1.25; }}
h2 {{ font-size: 14pt; border-bottom: 2px solid {YEL_500}; padding-bottom: 4px; margin-top: 6px; }}
h3 {{ font-size: 12pt; color: {BLUE_500}; }}
h4 {{ font-size: 10.5pt; color: {BLUE_500}; }}
a {{ color: {BLUE_500}; }}
p {{ margin: 5px 0; }}
strong {{ color: {BLUE_600}; }}
.muted {{ color: {MUTED}; font-style: italic; font-size: 9pt; }}

/* титул */
.cover {{ text-align: center; padding-top: 60mm; page-break-after: always; }}
.cover .brand {{ font-size: 13pt; letter-spacing: 3px; color: {YEL_600}; font-weight: 700; }}
.cover h1 {{ font-size: 30pt; color: {BLUE_600}; margin: 10px 0; }}
.cover .rule {{ width: 90px; height: 4px; background: {YEL_500}; margin: 14px auto; border-radius: 2px; }}
.cover .subj {{ font-size: 16pt; color: {TEXT}; font-weight: 600; margin: 18px 40px; }}
.cover .meta {{ color: {MUTED}; font-size: 10pt; margin-top: 16px; }}
.cover .disc {{ color: {SUBTLE}; font-size: 8pt; font-style: italic; margin: 30px 40px 0; }}

/* секции */
.section {{ page-break-before: always; }}
.sec-title {{ background: {BLUE_500}; color: #fff; padding: 8px 14px; border-radius: 6px;
  font-size: 14pt; font-weight: 700; margin-bottom: 12px; }}
.sec-title .em {{ color: {YEL_400}; }}

/* KPI */
.kpi {{ display: flex; gap: 8px; margin: 6px 0 14px; }}
.kpi-card {{ flex: 1; background: {BLUE_50}; border: 1px solid {BLUE_100}; border-radius: 8px;
  padding: 10px 4px; text-align: center; }}
.kpi-val {{ font-size: 24pt; font-weight: 700; color: {BLUE_500}; }}
.kpi-lbl {{ font-size: 8pt; color: {MUTED}; text-transform: uppercase; letter-spacing: .5px; }}

/* bars */
.bars {{ margin: 6px 0; }}
.bar-row {{ display: flex; align-items: center; gap: 8px; margin: 3px 0; }}
.bar-lbl {{ width: 120px; font-size: 9pt; color: {TEXT}; }}
.bar-track {{ flex: 1; background: {BLUE_50}; border-radius: 4px; height: 14px; }}
.bar-fill {{ height: 14px; border-radius: 4px; }}
.bar-num {{ width: 28px; font-size: 9pt; font-weight: 700; color: {BLUE_600}; }}

/* schema */
.graph {{ width: 100%; height: auto; background: {SURFACE}; border: 1px solid {BLUE_100}; border-radius: 8px; }}
.card-note {{ font-size: 9pt; color: {MUTED}; margin-bottom: 4px; }}

/* timeline */
.timeline {{ border-left: 3px solid {BLUE_200}; margin: 8px 0 8px 6px; padding-left: 14px; }}
.tl-item {{ position: relative; margin: 8px 0; }}
.tl-dot {{ position: absolute; left: -20px; top: 3px; width: 9px; height: 9px; background: {YEL_500};
  border: 2px solid #fff; border-radius: 50%; }}
.tl-date {{ font-weight: 700; color: {BLUE_600}; font-size: 9.5pt; }}
.tl-event {{ font-size: 9.5pt; color: {TEXT}; }}

/* matrix */
.matrix {{ border-collapse: collapse; font-size: 7.5pt; margin: 6px 0; }}
.matrix td, .matrix th {{ width: 16px; height: 16px; border: 1px solid #e4e7ed; text-align: center; }}
.matrix .mx-label {{ width: auto; text-align: left; padding: 0 6px; color: {TEXT}; white-space: nowrap; }}
.matrix .mx-num {{ color: {MUTED}; font-weight: 400; }}
.matrix .mx-on {{ background: {YEL_500}; }}
.matrix .mx-off {{ background: {BG}; }}
.matrix .mx-self {{ background: {BLUE_100}; }}

/* expert conclusion */
.conclusion {{ background: {YEL_100}; border-left: 5px solid {YEL_500}; padding: 8px 12px;
  border-radius: 4px; margin: 8px 0; font-weight: 600; color: {BLUE_700}; }}
.keylist {{ background: {BLUE_50}; border-radius: 6px; padding: 6px 10px; font-size: 9pt; margin: 6px 0; }}
.keylist b {{ color: {BLUE_500}; }}

/* таблицы из markdown */
table {{ border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9pt; }}
th {{ background: {BLUE_500}; color: #fff; padding: 5px 8px; text-align: left; font-weight: 600; }}
td {{ padding: 4px 8px; border-bottom: 1px solid #e8ecf1; vertical-align: top; }}
tbody tr:nth-child(even) {{ background: {BLUE_50}; }}
ul, ol {{ margin: 5px 0; padding-left: 20px; }}
li {{ margin: 2px 0; }}
code {{ background: {BLUE_50}; padding: 1px 4px; border-radius: 3px; font-size: 8.5pt; }}

/* письма-запросы как официальные документы */
.letters h3 {{ background: {BLUE_50}; border-left: 4px solid {BLUE_500}; padding: 6px 10px;
  border-radius: 0 4px 4px 0; margin-top: 16px; color: {BLUE_600}; font-size: 11pt; }}
.letters p {{ font-size: 9.5pt; }}
.letters ul, .letters ol {{ font-size: 9.5pt; }}
"""


def _expert_section(expert, nodes, rels):
    name = _esc(expert.get("name", "Эксперт"))
    conclusion = expert.get("conclusion")
    keys = expert.get("key_entities") or []
    parts = [f'<div class="section"><div class="sec-title">{name}</div>']
    if conclusion:
        parts.append(f'<div class="conclusion">Вывод: {_esc(conclusion)}</div>')
    if nodes and keys:
        parts.append('<div class="card-note">Схема с выделением ключевых для этой экспертизы сущностей:</div>')
        parts.append(_graph_svg(nodes, rels, highlight=keys, height=360))
        parts.append('<div class="keylist"><b>Ключевые сущности:</b> ' + _esc(", ".join(keys)) + "</div>")
    parts.append(_md_to_html(expert.get("analysis") or ""))
    parts.append("</div>")
    return "".join(parts)


def generate_report_html_pdf(data: Dict[str, Any], generated_at: Optional[str] = None) -> bytes:
    from weasyprint import HTML

    nodes = data.get("graph_nodes") or []
    rels = data.get("graph_rels") or []
    name = _esc(data.get("investigation_name") or "Без названия")
    experts = [e for e in data.get("experts", []) if e.get("analysis")]

    body = [f"<style>{_css()}</style>"]
    # титул
    body.append(
        f'<div class="cover"><div class="brand">TRACEON</div>'
        f'<h1>Аналитический отчёт<br>OSINT-расследования</h1>'
        f'<div class="rule"></div><div class="subj">{name}</div>'
        f'<div class="meta">Сущностей: {len(nodes)} · Связей: {len(rels)} · Экспертиз: {len(experts)}'
        + (f'<br>Сформировано: {_esc(generated_at)}' if generated_at else "")
        + '</div>'
        '<div class="disc">Отчёт сформирован ИИ-агентами на основе данных графа расследования. '
        'Выводы носят аналитический характер и требуют процессуальной проверки.</div></div>'
    )
    # сводка
    if nodes:
        body.append('<div class="section"><div class="sec-title">Сводка</div>')
        body.append(_dashboard_html(data))
        body.append("<h3>Распределение сущностей по типам</h3>")
        body.append(_entity_bars_html(nodes))
        body.append("<h3>Хронология событий</h3>")
        body.append(_timeline_html(nodes))
        body.append("</div>")
        # схема + матрица
        body.append('<div class="section"><div class="sec-title">Схема расследования</div>')
        body.append('<div class="card-note">Полный граф связей. Цвет узла соответствует типу сущности.</div>')
        body.append(_graph_svg(nodes, rels, height=440))
        body.append("<h3>Матрица связей (кто с кем связан)</h3>")
        body.append(_matrix_html(nodes, rels))
        body.append("</div>")
    # эксперты
    for e in experts:
        body.append(_expert_section(e, nodes, rels))
    # синтез
    syn = data.get("synthesis")
    if syn:
        body.append('<div class="section"><div class="sec-title">Синтез — управленческое резюме</div>')
        body.append(_md_to_html(syn))
        body.append("</div>")

    # шаблоны писем-запросов в органы
    letters = data.get("letters")
    if letters:
        body.append('<div class="section"><div class="sec-title">Шаблоны запросов в надлежащие органы</div>')
        body.append('<div class="card-note">Готовые проекты официальных писем. Поля в [квадратных скобках] '
                    'подлежат заполнению. Перед отправкой проверьте актуальность реквизитов и норм права.</div>')
        body.append(f'<div class="letters">{_md_to_html(letters)}</div>')
        body.append("</div>")

    full = f"<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'></head><body>{''.join(body)}</body></html>"
    return HTML(string=full).write_pdf()
