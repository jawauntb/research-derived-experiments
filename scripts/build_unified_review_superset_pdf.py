#!/usr/bin/env python3
"""Build the unified citation-grounded review superset PDF."""

from __future__ import annotations

import argparse
import html
import re
import textwrap
from pathlib import Path
from typing import Any

from reportlab import rl_config  # type: ignore[import-untyped]  # noqa: E402
from reportlab.lib import colors  # type: ignore[import-untyped]  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # type: ignore[import-untyped]  # noqa: E402
from reportlab.lib.pagesizes import letter  # type: ignore[import-untyped]  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]  # noqa: E402
from reportlab.lib.units import inch  # type: ignore[import-untyped]  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]  # noqa: E402
from reportlab.platypus import (  # type: ignore[import-untyped]  # noqa: E402
    CondPageBreak,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    LongTable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "papers" / "unified_citation_grounded_review"
SOURCE = PAPER_DIR / "paper.md"
DEFAULT_OUTPUT = PAPER_DIR / "paper.pdf"
TITLE = "Unified Citation-Grounded Review Superset"
SUBTITLE = (
    "Modular Master Framework, Formal Knowledge Ontology, Executable AI Reviewer, "
    "and Alpha Research Operating System"
)
DOCUMENT_DATE = "2026-07-20"

setattr(rl_config, "invariant", True)

INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#5B6678")
BLUE = colors.HexColor("#175CD3")
BLUE_DARK = colors.HexColor("#123A72")
TEAL = colors.HexColor("#0F766E")
PURPLE = colors.HexColor("#6D28D9")
AMBER = colors.HexColor("#B45309")
PALE_BLUE = colors.HexColor("#EAF2FF")
PALE_TEAL = colors.HexColor("#E9F7F5")
PALE_PURPLE = colors.HexColor("#F2ECFF")
PALE_AMBER = colors.HexColor("#FFF5E8")
PALE_GRAY = colors.HexColor("#F4F6F8")
RULE = colors.HexColor("#C8D0DB")
WHITE = colors.white


def _register_fonts() -> tuple[str, str, str, str, str]:
    font_root = Path("/System/Library/Fonts/Supplemental")
    font_files = {
        "SupersetBody": "Times New Roman.ttf",
        "SupersetBody-Bold": "Times New Roman Bold.ttf",
        "SupersetBody-Italic": "Times New Roman Italic.ttf",
        "SupersetSans": "Arial.ttf",
        "SupersetSans-Bold": "Arial Bold.ttf",
        "SupersetMono": "Courier New.ttf",
    }
    try:
        if not all((font_root / filename).exists() for filename in font_files.values()):
            raise FileNotFoundError("Optional system fonts are unavailable")
        for name, filename in font_files.items():
            pdfmetrics.registerFont(TTFont(name, str(font_root / filename)))
        pdfmetrics.registerFontFamily(
            "SupersetBody",
            normal="SupersetBody",
            bold="SupersetBody-Bold",
            italic="SupersetBody-Italic",
            boldItalic="SupersetBody-Bold",
        )
        return (
            "SupersetBody",
            "SupersetBody-Bold",
            "SupersetBody-Italic",
            "SupersetSans",
            "SupersetSans-Bold",
        )
    except Exception:
        return "Times-Roman", "Times-Bold", "Times-Italic", "Helvetica", "Helvetica-Bold"


F_BODY, F_BODY_BOLD, F_BODY_ITALIC, F_SANS, F_SANS_BOLD = _register_fonts()
F_MONO = "SupersetMono" if "SupersetMono" in pdfmetrics.getRegisteredFontNames() else "Courier"


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=sample["Normal"],
            fontName=F_SANS_BOLD,
            fontSize=8.5,
            leading=10,
            textColor=BLUE,
            alignment=TA_CENTER,
            tracking=1.1,
            spaceAfter=10,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=sample["Title"],
            fontName=F_SANS_BOLD,
            fontSize=25,
            leading=29,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=sample["Normal"],
            fontName=F_BODY,
            fontSize=11.5,
            leading=16,
            textColor=MUTED,
            alignment=TA_CENTER,
            leftIndent=18,
            rightIndent=18,
            spaceAfter=8,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            parent=sample["Normal"],
            fontName=F_SANS,
            fontSize=8.4,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
        "chapter": ParagraphStyle(
            "chapter",
            parent=sample["Heading1"],
            fontName=F_SANS_BOLD,
            fontSize=16.5,
            leading=20,
            textColor=BLUE_DARK,
            spaceBefore=8,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "part1": ParagraphStyle(
            "part1",
            parent=sample["Heading1"],
            fontName=F_SANS_BOLD,
            fontSize=18,
            leading=22,
            textColor=BLUE,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "part2": ParagraphStyle(
            "part2",
            parent=sample["Heading1"],
            fontName=F_SANS_BOLD,
            fontSize=18,
            leading=22,
            textColor=TEAL,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "part3": ParagraphStyle(
            "part3",
            parent=sample["Heading1"],
            fontName=F_SANS_BOLD,
            fontSize=18,
            leading=22,
            textColor=PURPLE,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "part4": ParagraphStyle(
            "part4",
            parent=sample["Heading1"],
            fontName=F_SANS_BOLD,
            fontSize=18,
            leading=22,
            textColor=AMBER,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "appendix": ParagraphStyle(
            "appendix",
            parent=sample["Heading1"],
            fontName=F_SANS_BOLD,
            fontSize=16,
            leading=19,
            textColor=AMBER,
            spaceBefore=10,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "section": ParagraphStyle(
            "section",
            parent=sample["Heading2"],
            fontName=F_SANS_BOLD,
            fontSize=11.2,
            leading=14,
            textColor=INK,
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "body",
            parent=sample["BodyText"],
            fontName=F_BODY,
            fontSize=8.85,
            leading=12.6,
            textColor=INK,
            spaceAfter=5.2,
            allowWidows=0,
            allowOrphans=0,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=sample["BodyText"],
            fontName=F_BODY,
            fontSize=8.65,
            leading=12.2,
            textColor=INK,
            spaceAfter=2.4,
        ),
        "number": ParagraphStyle(
            "number",
            parent=sample["BodyText"],
            fontName=F_BODY,
            fontSize=8.65,
            leading=12.2,
            textColor=INK,
            spaceAfter=2.4,
        ),
        "small": ParagraphStyle(
            "small",
            parent=sample["BodyText"],
            fontName=F_SANS,
            fontSize=7.6,
            leading=10,
            textColor=MUTED,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=sample["Normal"],
            fontName=F_SANS_BOLD,
            fontSize=7.15,
            leading=8.8,
            textColor=WHITE,
            alignment=TA_LEFT,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=sample["Normal"],
            fontName=F_SANS,
            fontSize=6.85,
            leading=9.1,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        "code": ParagraphStyle(
            "code",
            parent=sample["Code"],
            fontName=F_MONO,
            fontSize=6.6,
            leading=8.7,
            textColor=colors.HexColor("#27364A"),
            leftIndent=6,
            rightIndent=6,
            spaceBefore=0,
            spaceAfter=0,
        ),
    }


def _inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#175CD3">\1</link>',
        escaped,
    )
    escaped = re.sub(
        r"`([^`]+)`",
        lambda match: (
            f'<font name="{F_MONO}" size="7.1" color="#334155">'
            + match.group(1)
            + "</font>"
        ),
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)
    return escaped


def validate_source(text: str) -> None:
    required = [
        "## Part I - Modular master framework",
        "## Part II - Formal knowledge ontology",
        "## Part III - Executable AI reviewer",
        "## Part IV - Modular alpha research operating system",
        "### 14. Decisive contradiction-resolution protocol",
        "### 22. Ontological invariants and validation rules",
        "### 32. Master system prompt",
        "### 49. Promotion, demotion, and validation gates",
        "## Appendix A - Source map",
        "[A1 pp. 1-3]",
        "[C1 pp. 16-25]",
        "[E1 pp. 13-17]",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError(f"Unified review source is missing required sections: {missing}")
    forbidden = ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"]
    present = [value for value in forbidden if value in text]
    if present:
        raise ValueError(f"Unified review source contains forbidden dash characters: {present}")


def _cover(styles: dict[str, ParagraphStyle]) -> list[Any]:
    summary = (
        "A lossless consolidation of five review frameworks and nine primary sources. "
        "Shared invariants are normalized once; domain-specific gates remain modular; "
        "apparent contradictions are resolved by object, scope, conditions, representation, "
        "validity layer, evidence, and decisive tests; the resulting controls are then "
        "applied to a composable alpha-research operating system."
    )
    summary_box = Table(
        [[Paragraph(summary, styles["body"])]],
        colWidths=[5.95 * inch],
        hAlign="CENTER",
    )
    summary_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#AFC6E8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    flow_table = Table(
        [
            [
                Paragraph("<b>PART I</b><br/>Modular master framework", styles["table_cell"]),
                Paragraph("->", styles["cover_meta"]),
                Paragraph("<b>PART II</b><br/>Formal knowledge ontology", styles["table_cell"]),
                Paragraph("->", styles["cover_meta"]),
                Paragraph("<b>PART III</b><br/>Executable AI reviewer", styles["table_cell"]),
                Paragraph("->", styles["cover_meta"]),
                Paragraph("<b>PART IV</b><br/>Alpha research system", styles["table_cell"]),
            ]
        ],
        colWidths=[
            1.30 * inch,
            0.22 * inch,
            1.30 * inch,
            0.22 * inch,
            1.30 * inch,
            0.22 * inch,
            1.30 * inch,
        ],
        hAlign="CENTER",
    )
    flow_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), PALE_BLUE),
                ("BACKGROUND", (2, 0), (2, 0), PALE_TEAL),
                ("BACKGROUND", (4, 0), (4, 0), PALE_PURPLE),
                ("BACKGROUND", (6, 0), (6, 0), PALE_AMBER),
                ("BOX", (0, 0), (0, 0), 0.7, BLUE),
                ("BOX", (2, 0), (2, 0), 0.7, TEAL),
                ("BOX", (4, 0), (4, 0), 0.7, PURPLE),
                ("BOX", (6, 0), (6, 0), 0.7, AMBER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    control = Table(
        [
            ["Primary sources", "9", "Review frameworks", "5"],
            ["Shared knowledge units", "18", "Domain modules", "5"],
            ["Review passes", "8", "Validity layers", "6"],
            ["Alpha modules", "18", "Promotion gates", "9"],
        ],
        colWidths=[1.7 * inch, 0.6 * inch, 1.7 * inch, 0.6 * inch],
        hAlign="CENTER",
    )
    control.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), F_SANS),
                ("FONTNAME", (0, 0), (0, -1), F_SANS_BOLD),
                ("FONTNAME", (2, 0), (2, -1), F_SANS_BOLD),
                ("FONTSIZE", (0, 0), (-1, -1), 7.8),
                ("TEXTCOLOR", (0, 0), (-1, -1), INK),
                ("BACKGROUND", (0, 0), (-1, -1), PALE_GRAY),
                ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, RULE),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("ALIGN", (3, 0), (3, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return [
        Spacer(1, 0.42 * inch),
        Paragraph("CITATION-GROUNDED QUANTITATIVE REVIEW", styles["cover_kicker"]),
        Paragraph(TITLE, styles["cover_title"]),
        HRFlowable(width="34%", thickness=2.3, color=BLUE, hAlign="CENTER"),
        Spacer(1, 12),
        Paragraph(SUBTITLE, styles["cover_subtitle"]),
        Spacer(1, 14),
        summary_box,
        Spacer(1, 18),
        KeepTogether([flow_table]),
        Spacer(1, 20),
        control,
        Spacer(1, 18),
        Paragraph("Human research director: Jawaun Brown", styles["cover_meta"]),
        Paragraph("Compiled by Codex from user-supplied sources", styles["cover_meta"]),
        Paragraph(f"Version 1.0 - {DOCUMENT_DATE}", styles["cover_meta"]),
        Spacer(1, 12),
        Paragraph(
            "This document is a methodological synthesis, not an author impersonation, endorsement, or investment recommendation.",
            styles["small"],
        ),
        PageBreak(),
    ]


def _table_widths(headers: list[str]) -> list[float]:
    count = len(headers)
    total = 6.92 * inch
    first = headers[0].strip().lower() if headers else ""
    if count == 2:
        return [1.62 * inch, total - 1.62 * inch]
    if count == 3:
        if first in {"id", "key", "tag", "pass"}:
            return [0.55 * inch, 2.62 * inch, total - 3.17 * inch]
        return [1.25 * inch, 2.35 * inch, total - 3.60 * inch]
    if count == 4:
        return [1.05 * inch, 2.18 * inch, 1.32 * inch, total - 4.55 * inch]
    if count == 5:
        return [1.18 * inch, 1.35 * inch, 1.35 * inch, 1.52 * inch, total - 5.40 * inch]
    if count == 6:
        return [1.55 * inch, 1.03 * inch, 1.03 * inch, 1.03 * inch, 1.03 * inch, total - 5.67 * inch]
    return [total / max(1, count)] * count


def _parse_table(lines: list[str], index: int) -> tuple[Any, int]:
    raw_rows: list[list[str]] = []
    while index < len(lines) and lines[index].strip().startswith("|"):
        raw_rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
        index += 1
    if len(raw_rows) < 2 or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in raw_rows[1]):
        raise ValueError(f"Malformed markdown table near row: {raw_rows[:2]}")
    headers = raw_rows[0]
    body = raw_rows[2:]
    styles = _styles()
    data: list[list[Paragraph]] = [
        [Paragraph(_inline(cell), styles["table_header"]) for cell in headers]
    ]
    for row in body:
        padded = row + [""] * (len(headers) - len(row))
        data.append([Paragraph(_inline(cell), styles["table_cell"]) for cell in padded[: len(headers)]])
    table = LongTable(
        data,
        colWidths=_table_widths(headers),
        repeatRows=1,
        hAlign="CENTER",
        splitByRow=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE_GRAY]),
                ("BOX", (0, 0), (-1, -1), 0.45, RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.22, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table, index


def _wrap_code(code: str, width: int = 96) -> str:
    wrapped: list[str] = []
    for line in code.splitlines():
        if not line:
            wrapped.append("")
            continue
        indent = len(line) - len(line.lstrip(" "))
        prefix = " " * indent
        chunks = textwrap.wrap(
            line.strip(),
            width=max(28, width - indent),
            subsequent_indent=prefix + "  ",
            break_long_words=False,
            break_on_hyphens=False,
        )
        wrapped.extend([prefix + chunks[0].lstrip()] + chunks[1:] if chunks else [line])
    return "\n".join(wrapped)


def _chapter_style(heading: str, styles: dict[str, ParagraphStyle]) -> ParagraphStyle:
    if heading.startswith("Part I "):
        return styles["part1"]
    if heading.startswith("Part II "):
        return styles["part2"]
    if heading.startswith("Part III "):
        return styles["part3"]
    if heading.startswith("Part IV "):
        return styles["part4"]
    if heading.startswith("Appendix "):
        return styles["appendix"]
    return styles["chapter"]


def _body_flow(text: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
    lines = text.splitlines()
    flow: list[Any] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith("# "):
            index += 1
            continue
        if stripped == "[[PAGEBREAK]]":
            flow.append(PageBreak())
            index += 1
            continue
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if heading.startswith("Part "):
                flow.extend(
                    [
                        Spacer(1, 0.16 * inch),
                        Paragraph(_inline(heading), _chapter_style(heading, styles)),
                        HRFlowable(width="100%", thickness=1.2, color=_chapter_style(heading, styles).textColor),
                        Spacer(1, 5),
                    ]
                )
            else:
                flow.append(CondPageBreak(1.0 * inch))
                flow.append(Paragraph(_inline(heading), _chapter_style(heading, styles)))
                flow.append(HRFlowable(width="100%", thickness=0.7, color=RULE))
                flow.append(Spacer(1, 3))
            index += 1
            continue
        if stripped.startswith("### "):
            flow.append(CondPageBreak(0.72 * inch))
            flow.append(Paragraph(_inline(stripped[4:].strip()), styles["section"]))
            index += 1
            continue
        if stripped.startswith("#### "):
            flow.append(CondPageBreak(0.58 * inch))
            flow.append(Paragraph(_inline(stripped[5:].strip()), styles["section"]))
            index += 1
            continue
        if stripped.startswith("|"):
            table, index = _parse_table(lines, index)
            flow.extend([Spacer(1, 2), table, Spacer(1, 6)])
            continue
        if stripped.startswith("```"):
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index >= len(lines):
                raise ValueError("Unclosed fenced code block")
            index += 1
            wrapped_lines = _wrap_code("\n".join(code_lines)).splitlines()
            chunks = [wrapped_lines[pos : pos + 16] for pos in range(0, len(wrapped_lines), 16)]
            block = LongTable(
                [[Preformatted("\n".join(chunk), styles["code"])] for chunk in chunks],
                colWidths=[6.82 * inch],
                hAlign="CENTER",
                splitByRow=1,
            )
            block.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), PALE_GRAY),
                        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, 0), 5),
                        ("TOPPADDING", (0, 1), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -2), 0),
                        ("BOTTOMPADDING", (0, -1), (-1, -1), 4),
                    ]
                )
            )
            flow.extend([Spacer(1, 2), block, Spacer(1, 5)])
            continue
        if stripped.startswith("- "):
            items: list[ListItem] = []
            while index < len(lines) and lines[index].strip().startswith("- "):
                item_text = lines[index].strip()[2:].strip()
                items.append(ListItem(Paragraph(_inline(item_text), styles["bullet"])))
                index += 1
            flow.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="circle",
                    leftIndent=16,
                    bulletFontName=F_SANS,
                    bulletFontSize=5.8,
                    bulletColor=BLUE,
                    spaceAfter=5,
                )
            )
            continue
        if re.match(r"^\d+\.\s", stripped):
            items = []
            while index < len(lines) and re.match(r"^\d+\.\s", lines[index].strip()):
                item_text = re.sub(r"^\d+\.\s+", "", lines[index].strip())
                items.append(ListItem(Paragraph(_inline(item_text), styles["number"])))
                index += 1
            flow.append(
                ListFlowable(
                    items,
                    bulletType="1",
                    start="1",
                    leftIndent=19,
                    bulletFontName=F_SANS_BOLD,
                    bulletFontSize=7.5,
                    bulletColor=BLUE_DARK,
                    spaceAfter=6,
                )
            )
            continue
        flow.append(Paragraph(_inline(stripped), styles["body"]))
        index += 1
    return flow


def _first_page(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.45)
    canvas.line(0.78 * inch, 0.48 * inch, 7.72 * inch, 0.48 * inch)
    canvas.setFont(F_SANS, 7.0)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(4.25 * inch, 0.30 * inch, "SOURCE-GROUNDED SYNTHESIS - VERSION 1.0")
    canvas.restoreState()


def _later_pages(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    width, height = letter
    canvas.setFont(F_SANS, 7.0)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.68 * inch, height - 0.43 * inch, "UNIFIED CITATION-GROUNDED REVIEW SUPERSET")
    canvas.drawRightString(width - 0.68 * inch, height - 0.43 * inch, DOCUMENT_DATE)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.45)
    canvas.line(0.68 * inch, height - 0.51 * inch, width - 0.68 * inch, height - 0.51 * inch)
    canvas.line(0.68 * inch, 0.48 * inch, width - 0.68 * inch, 0.48 * inch)
    canvas.drawString(
        0.68 * inch,
        0.30 * inch,
        "Framework -> ontology -> executable reviewer -> alpha research system",
    )
    canvas.drawRightString(width - 0.68 * inch, 0.30 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(out_path: Path = DEFAULT_OUTPUT) -> Path:
    text = SOURCE.read_text(encoding="utf-8")
    validate_source(text)
    styles = _styles()
    flow = _cover(styles)
    flow.extend(_body_flow(text, styles))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=0.70 * inch,
        rightMargin=0.70 * inch,
        topMargin=0.66 * inch,
        bottomMargin=0.64 * inch,
        title=TITLE,
        author="Jawaun Brown; compiled by Codex",
        subject=SUBTITLE,
        creator="Research Derived Experiments",
        keywords=(
            "review framework, knowledge ontology, AI reviewer, information geometry, "
            "financial modeling, alpha research, equities, ETFs, equity options"
        ),
        pageCompression=1,
    )
    document.build(flow, onFirstPage=_first_page, onLaterPages=_later_pages)
    return out_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination PDF path (default: repository output/pdf path).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output = build_pdf(args.output)
    print(f"Wrote {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
