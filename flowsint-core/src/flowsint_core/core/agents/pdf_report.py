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


def _mcell(pdf, h, text, size=10.5, style="", color=_DARK, align="L", indent=0.0, markdown=True):
    """Безопасная обёртка multi_cell: всегда сбрасывает X к левому полю."""
    pdf.set_font("DejaVu", style, size)
    pdf.set_text_color(*color)
    pdf.set_x(pdf.l_margin + indent)
    width = pdf.epw - indent
    pdf.multi_cell(
        width, h, text, align=align, markdown=markdown,
        new_x="LMARGIN", new_y="NEXT",
    )


def _build_pdf(data: Dict[str, Any], font_dir: str):
    from fpdf import FPDF

    class Report(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font("DejaVu", "", 8)
            self.set_text_color(*_MUTED)
            self.cell(0, 10, f"Flowsint · ИИ-аналитика · стр. {self.page_no()}", align="C")

    pdf = Report(format="A4")
    pdf.add_font("DejaVu", "", f"{font_dir}/DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", f"{font_dir}/DejaVuSans-Bold.ttf")
    pdf.add_font("DejaVu", "I", f"{font_dir}/DejaVuSans-Oblique.ttf")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(18, 18, 18)

    _title_page(pdf, data)
    for expert in data.get("experts", []):
        analysis = expert.get("analysis")
        if not analysis:
            continue
        _section_header(pdf, _strip_emoji(expert.get("name", "Эксперт")))
        _render_markdown(pdf, analysis)

    synthesis = data.get("synthesis")
    if synthesis:
        _section_header(pdf, "Синтез — управленческое резюме")
        _render_markdown(pdf, synthesis)

    return bytes(pdf.output())


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


def _section_header(pdf, title: str):
    pdf.add_page()
    pdf.set_fill_color(*_PRIMARY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 11, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_text_color(*_DARK)


_BULLET = "•  "


def _render_markdown(pdf, md: str):
    for raw in md.split("\n"):
        stripped = raw.strip()
        if not stripped:
            pdf.ln(2)
            continue
        # горизонтальный разделитель
        if re.match(r"^([-*_])\1{2,}$", stripped):
            pdf.ln(1)
            pdf.set_draw_color(220, 220, 225)
            pdf.set_line_width(0.2)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
            continue
        # заголовки
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            sizes = {1: 14, 2: 12.5, 3: 11.5, 4: 11}
            pdf.ln(2)
            _mcell(pdf, 7, _strip_emoji(m.group(2)), size=sizes.get(level, 11), style="B", color=_PRIMARY)
            pdf.ln(1)
            continue
        # маркированный список
        lm = re.match(r"^[-*+]\s+(.*)$", stripped)
        if lm:
            _mcell(pdf, 6, _BULLET + _strip_emoji(lm.group(1)), size=10.5, indent=4)
            continue
        # нумерованный список
        nm = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if nm:
            _mcell(pdf, 6, f"{nm.group(1)}.  " + _strip_emoji(nm.group(2)), size=10.5, indent=4)
            continue
        # обычный абзац
        _mcell(pdf, 6, _strip_emoji(stripped), size=10.5)


def generate_report_pdf(
    data: Dict[str, Any], font_dir: str, generated_at: Optional[str] = None
) -> bytes:
    """Собирает PDF-отчёт из результата панели экспертов (run_panel)."""
    payload = dict(data)
    if generated_at:
        payload["generated_at"] = generated_at
    return _build_pdf(payload, font_dir)
