"""Генерация PDF-отчёта из заключений ИИ-агентов-экспертов (fpdf2).

Рендерит управленческий отчёт: титул, разделы экспертов и синтез.
Поддерживает кириллицу через встраиваемый шрифт DejaVu и базовый Markdown
(заголовки, списки, **жирный**/__курсив__, разделители)."""
import re
from typing import Any, Dict, Optional

# Фирменные цвета (тёмно-синий + акцент)
_PRIMARY = (37, 99, 130)
_ACCENT = (217, 119, 66)
_MUTED = (110, 110, 120)
_DARK = (33, 37, 41)


def _strip_emoji(text: str) -> str:
    """Убирает emoji и символы вне базовых плоскостей (нет глифов в DejaVu)."""
    return re.sub(
        "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE00-\U0000FE0F\U00002190-\U000021FF\U00002B00-\U00002BFF]",
        "",
        text,
    ).strip()


def _break_long_tokens(text: str, max_len: int = 42) -> str:
    """Вставляет пробелы в сверхдлинные «слова» (крипто-адреса, хэши),
    чтобы fpdf2 мог перенести строку (иначе ошибка переноса)."""
    def fix(word: str) -> str:
        if len(word) <= max_len:
            return word
        return " ".join(word[i : i + max_len] for i in range(0, len(word), max_len))

    return " ".join(fix(w) for w in text.split(" "))


def _mcell(pdf, h, text, size=10.5, style="", color=_DARK, align="L", indent=0.0, markdown=True):
    """Безопасная обёртка multi_cell: всегда сбрасывает X к левому полю."""
    pdf.set_font("DejaVu", style, size)
    pdf.set_text_color(*color)
    pdf.set_x(pdf.l_margin + indent)
    width = pdf.epw - indent
    pdf.multi_cell(
        width, h, _break_long_tokens(text), align=align, markdown=markdown,
        new_x="LMARGIN", new_y="NEXT", wrapmode="CHAR",
    )


def _build_pdf(data: Dict[str, Any], font_dir: str):
    from fpdf import FPDF

    class Report(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(*_MUTED)
            self.cell(0, 10, f"Traceon · ИИ-аналитика · стр. {self.page_no()}", align="C")

    pdf = Report(format="A4")
    pdf.add_font("DejaVu", "", f"{font_dir}/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", f"{font_dir}/DejaVuSans-Bold.ttf")
    pdf.add_font("DejaVu", "I", f"{font_dir}/DejaVuSans-Oblique.ttf")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(18, 18, 18)

    _title_page(pdf, data)

    nodes = data.get("graph_nodes") or []
    rels = data.get("graph_rels") or []

    # Общая схема расследования + статистика
    if nodes:
        _section_header(pdf, "Схема расследования")
        _mcell(pdf, 5.5, "Полный граф связей расследования. Цвет узла соответствует типу сущности.", size=9, style="I", color=_MUTED, markdown=False)
        pdf.ln(2)
        _draw_graph(pdf, nodes, rels, height=118)
        # диаграмма распределения сущностей по типам
        pdf.ln(2)
        _mcell(pdf, 6.5, "Распределение сущностей по типам", size=11.5, style="B", color=_PRIMARY, markdown=False)
        pdf.ln(1)
        _draw_entity_chart(pdf, nodes)

    for expert in data.get("experts", []):
        analysis = expert.get("analysis")
        if not analysis:
            continue
        _section_header(pdf, _strip_emoji(expert.get("name", "Эксперт")))

        conclusion = expert.get("conclusion")
        if conclusion:
            _conclusion_box(pdf, conclusion)

        key_entities = expert.get("key_entities") or []
        if nodes and key_entities:
            _mcell(pdf, 5.5, "Схема с выделением ключевых для этой экспертизы сущностей:", size=9, style="I", color=_MUTED, markdown=False)
            pdf.ln(1)
            _draw_graph(pdf, nodes, rels, highlight=key_entities, height=88)
            _mcell(pdf, 6, "Ключевые сущности: " + ", ".join(_strip_emoji(k) for k in key_entities), size=9.5, style="B", color=_PRIMARY, markdown=False)
            pdf.ln(2)

        _render_markdown(pdf, analysis)

    synthesis = data.get("synthesis")
    if synthesis:
        _section_header(pdf, "Синтез — управленческое резюме")
        _render_markdown(pdf, synthesis)

    return bytes(pdf.output())


def _conclusion_box(pdf, text: str):
    """Рисует акцентный блок с главным выводом эксперта."""
    text = _strip_emoji(text)
    pdf.set_fill_color(248, 240, 233)
    pdf.set_draw_color(*_ACCENT)
    y0 = pdf.get_y()
    pdf.set_font("DejaVu", "B", 10.5)
    pdf.set_text_color(*_DARK)
    pdf.set_x(pdf.l_margin)
    # левая акцентная полоса + светлая заливка
    pdf.multi_cell(pdf.epw, 6, "Вывод: " + text, border=0, fill=True,
                   new_x="LMARGIN", new_y="NEXT", markdown=False, wrapmode="CHAR")
    y1 = pdf.get_y()
    pdf.set_line_width(1.2)
    pdf.line(pdf.l_margin, y0, pdf.l_margin, y1)
    pdf.ln(3)


def _title_page(pdf, data: Dict[str, Any]):
    pdf.add_page()
    pdf.ln(38)
    _mcell(pdf, 12, "Аналитический отчёт\nOSINT-расследования", size=26, style="B", color=_PRIMARY, align="C", markdown=False)
    pdf.ln(4)
    pdf.set_draw_color(*_ACCENT)
    pdf.set_line_width(1)
    pdf.line(70, pdf.get_y(), pdf.w - 70, pdf.get_y())
    pdf.ln(10)

    name = _strip_emoji(data.get("investigation_name") or "Без названия")
    _mcell(pdf, 9, name, size=16, style="B", color=_DARK, align="C", markdown=False)
    pdf.ln(8)

    meta_line = (
        f"Сущностей в графе: {data.get('nodes_count', '—')}     "
        f"Связей: {data.get('rels_count', '—')}"
    )
    _mcell(pdf, 7, meta_line, size=11, color=_MUTED, align="C", markdown=False)
    generated = data.get("generated_at", "")
    if generated:
        _mcell(pdf, 7, f"Сформировано: {generated}", size=11, color=_MUTED, align="C", markdown=False)
    pdf.ln(10)

    experts = [e for e in data.get("experts", []) if e.get("analysis")]
    if experts:
        _mcell(pdf, 7, "Заключения подготовили:", size=11, style="B", color=_PRIMARY, align="C", markdown=False)
        for e in experts:
            _mcell(pdf, 6, _strip_emoji(e.get("name", "")), size=10, color=_DARK, align="C", markdown=False)

    pdf.ln(12)
    _mcell(
        pdf, 5,
        "Отчёт сформирован ИИ-агентами на основе данных графа расследования. "
        "Выводы носят аналитический характер и требуют процессуальной проверки.",
        size=8, style="I", color=_MUTED, align="C", markdown=False,
    )


# Цвета узлов по типу сущности
_TYPE_COLORS = {
    "domain": (46, 139, 87), "website": (60, 160, 110),
    "ip": (52, 120, 200), "asn": (130, 90, 200), "cidr": (150, 110, 210),
    "dnsrecord": (90, 150, 180), "sslcertificate": (70, 130, 160),
    "email": (217, 119, 66), "phone": (210, 150, 60),
    "individual": (200, 70, 70), "username": (180, 90, 140),
    "socialaccount": (170, 100, 150), "organization": (140, 100, 60),
    "malware": (160, 40, 40), "weapon": (110, 60, 60),
    "cryptowallet": (200, 160, 40), "cryptowallettransaction": (190, 150, 40),
    "bankaccount": (60, 140, 120), "creditcard": (70, 150, 130),
    "location": (120, 130, 90), "device": (100, 110, 130),
    "document": (120, 120, 150), "leak": (180, 60, 90),
    "phrase": (120, 120, 130), "message": (130, 120, 150),
    "port": (80, 130, 170),
}
_DEFAULT_NODE_COLOR = (110, 120, 140)


def _layout_positions(nodes, x0, y0, w, h):
    """Нормализует координаты узлов (x,y) в прямоугольник холста.
    Если координат нет — раскладывает по окружности."""
    import math

    pts = []
    have_coords = all(
        n.get("x") is not None and n.get("y") is not None for n in nodes
    ) and len(nodes) > 0
    if have_coords:
        xs = [float(n["x"]) for n in nodes]
        ys = [float(n["y"]) for n in nodes]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        dx = (maxx - minx) or 1.0
        dy = (maxy - miny) or 1.0
        pad = 8
        for n in nodes:
            px = x0 + pad + (float(n["x"]) - minx) / dx * (w - 2 * pad)
            py = y0 + pad + (float(n["y"]) - miny) / dy * (h - 2 * pad)
            pts.append((px, py))
    else:
        cx, cy = x0 + w / 2, y0 + h / 2
        r = min(w, h) / 2 - 12
        for i, _ in enumerate(nodes):
            ang = 2 * math.pi * i / max(len(nodes), 1)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def _draw_graph(pdf, nodes, rels, highlight=None, height=105):
    """Рисует схему графа: связи + узлы, подсвечивая названия из highlight."""
    if not nodes:
        return
    highlight = {h.lower() for h in (highlight or [])}
    x0, y0 = pdf.l_margin, pdf.get_y()
    w = pdf.epw
    pts = _layout_positions(nodes, x0, y0, w, height)
    id_to_idx = {n.get("id"): i for i, n in enumerate(nodes)}

    def is_hl(n):
        lbl = (n.get("nodeLabel") or "").lower()
        return any(h and (h in lbl or lbl in h) for h in highlight)

    any_hl = any(is_hl(n) for n in nodes) if highlight else False

    # связи
    for r in rels:
        si = id_to_idx.get(r.get("source"))
        ti = id_to_idx.get(r.get("target"))
        if si is None or ti is None:
            continue
        hl_edge = any_hl and (is_hl(nodes[si]) and is_hl(nodes[ti]))
        if hl_edge:
            pdf.set_draw_color(*_ACCENT)
            pdf.set_line_width(0.6)
        else:
            pdf.set_draw_color(205, 208, 215)
            pdf.set_line_width(0.2)
        pdf.line(pts[si][0], pts[si][1], pts[ti][0], pts[ti][1])

    # узлы
    for i, n in enumerate(nodes):
        ntype = (n.get("nodeType") or "").lower()
        color = _TYPE_COLORS.get(ntype, _DEFAULT_NODE_COLOR)
        hl = is_hl(n)
        rad = 2.6 if (hl or not any_hl) else 1.6
        px, py = pts[i]
        if any_hl and not hl:
            # приглушённый
            pdf.set_fill_color(210, 213, 220)
        else:
            pdf.set_fill_color(*color)
        pdf.ellipse(px - rad, py - rad, rad * 2, rad * 2, style="F")
        if hl:
            pdf.set_draw_color(*_ACCENT)
            pdf.set_line_width(0.5)
            pdf.ellipse(px - rad - 0.8, py - rad - 0.8, (rad + 0.8) * 2, (rad + 0.8) * 2, style="D")
        # подпись: для подсвеченных всегда, иначе только если узлов немного
        show_label = hl or (not any_hl and len(nodes) <= 18)
        if show_label:
            label = _strip_emoji(n.get("nodeLabel") or "")[:22]
            pdf.set_font("DejaVu", "B" if hl else "", 6.5)
            pdf.set_text_color(*(_DARK if hl else _MUTED))
            pdf.text(px + rad + 0.8, py + 1.5, label)

    pdf.set_y(y0 + height + 4)


_TYPE_RU_SHORT = {
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


def _draw_entity_chart(pdf, nodes):
    """Горизонтальная столбчатая диаграмма распределения сущностей по типам."""
    from collections import Counter

    counts = Counter((n.get("nodeType") or "?").lower() for n in nodes)
    if not counts:
        return
    items = counts.most_common()
    maxv = max(c for _, c in items)
    x0 = pdf.l_margin
    label_w = 36
    bar_max = pdf.epw - label_w - 14
    bar_h = 5.0
    gap = 2.2
    for ntype, cnt in items:
        if pdf.get_y() + bar_h > pdf.h - 22:
            pdf.add_page()
        y = pdf.get_y()
        # подпись типа
        pdf.set_font("DejaVu", "", 8.5)
        pdf.set_text_color(*_DARK)
        pdf.set_xy(x0, y)
        pdf.cell(label_w, bar_h, _TYPE_RU_SHORT.get(ntype, ntype)[:18], align="L")
        # бар
        color = _TYPE_COLORS.get(ntype, _DEFAULT_NODE_COLOR)
        w = max(1.5, bar_max * cnt / maxv)
        pdf.set_fill_color(*color)
        pdf.rect(x0 + label_w, y + 0.6, w, bar_h - 1.2, style="F")
        # число
        pdf.set_font("DejaVu", "B", 8.5)
        pdf.set_text_color(*_DARK)
        pdf.set_xy(x0 + label_w + w + 1.5, y)
        pdf.cell(10, bar_h, str(cnt), align="L")
        pdf.set_y(y + bar_h + gap)
    pdf.ln(2)


def _section_header(pdf, title: str):
    pdf.add_page()
    pdf.set_fill_color(*_PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 11, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_text_color(*_DARK)


_BULLET = "•  "


def _is_table_row(line: str) -> bool:
    return line.count("|") >= 2


def _is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?[\s:|\-]+\|?\s*$", line)) and "-" in line and "|" in line


def _parse_table_row(line: str):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _render_table(pdf, rows):
    """Рисует распарсенную markdown-таблицу через fpdf2 table API."""
    if not rows:
        return
    header = rows[0]
    body = rows[1:]
    ncols = max(len(r) for r in rows)
    pdf.ln(1)
    pdf.set_font("DejaVu", "", 8.5)
    pdf.set_draw_color(210, 214, 222)
    try:
        with pdf.table(
            borders_layout="MINIMAL",
            cell_fill_color=(244, 247, 250),
            cell_fill_mode="ROWS",
            line_height=5.2,
            text_align="LEFT",
            width=pdf.epw,
        ) as table:
            hr = table.row()
            for c in range(ncols):
                pdf.set_font("DejaVu", "B", 8.5)
                pdf.set_text_color(*_PRIMARY)
                hr.cell(_strip_emoji(header[c]) if c < len(header) else "")
            for r in body:
                row = table.row()
                for c in range(ncols):
                    pdf.set_font("DejaVu", "", 8.5)
                    pdf.set_text_color(*_DARK)
                    txt = _break_long_tokens(_strip_emoji(r[c])) if c < len(r) else ""
                    row.cell(txt)
    except Exception:
        # запасной вариант: текстом
        for r in rows:
            _mcell(pdf, 5.5, " | ".join(_strip_emoji(x) for x in r), size=8.5)
    pdf.set_text_color(*_DARK)
    pdf.ln(2)


def _render_markdown(pdf, md: str):
    lines = md.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        # таблица: строка с | и следующая — разделитель
        if _is_table_row(raw) and i + 1 < n and _is_table_separator(lines[i + 1]):
            rows = [_parse_table_row(raw)]
            j = i + 2
            while j < n and _is_table_row(lines[j]) and not _is_table_separator(lines[j]):
                rows.append(_parse_table_row(lines[j]))
                j += 1
            _render_table(pdf, rows)
            i = j
            continue
        if not stripped:
            pdf.ln(2)
            i += 1
            continue
        # горизонтальный разделитель
        if re.match(r"^([-*_])\1{2,}$", stripped):
            pdf.ln(1)
            pdf.set_draw_color(220, 220, 225)
            pdf.set_line_width(0.2)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
            i += 1
            continue
        # заголовки
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            sizes = {1: 14, 2: 12.5, 3: 11.5, 4: 11}
            pdf.ln(2)
            _mcell(pdf, 7, _strip_emoji(m.group(2)), size=sizes.get(level, 11), style="B", color=_PRIMARY)
            pdf.ln(1)
            i += 1
            continue
        # маркированный список
        lm = re.match(r"^[-*+]\s+(.*)$", stripped)
        if lm:
            _mcell(pdf, 6, _BULLET + _strip_emoji(lm.group(1)), size=10.5, indent=4)
            i += 1
            continue
        # нумерованный список
        nm = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if nm:
            _mcell(pdf, 6, f"{nm.group(1)}.  " + _strip_emoji(nm.group(2)), size=10.5, indent=4)
            i += 1
            continue
        # обычный абзац
        _mcell(pdf, 6, _strip_emoji(stripped), size=10.5)
        i += 1


def generate_report_pdf(
    data: Dict[str, Any], font_dir: str, generated_at: Optional[str] = None
) -> bytes:
    """Собирает PDF-отчёт из результата панели экспертов (run_panel)."""
    payload = dict(data)
    if generated_at:
        payload["generated_at"] = generated_at
    return _build_pdf(payload, font_dir)
