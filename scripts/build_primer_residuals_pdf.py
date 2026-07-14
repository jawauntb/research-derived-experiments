#!/usr/bin/env python3
"""Build the post-merge primer residual-work register PDF."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

from reportlab import rl_config  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    CondPageBreak,
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "primers" / "primer_residuals_2026_07_14.md"
DEFAULT_OUTPUT = (
    ROOT / "output" / "pdf" / "primer_derived_research_residuals_2026_07_14.pdf"
)
TITLE = "Primer-Derived Research Program: Residual Work Register"
BASELINE = "Post-merge baseline: origin/main 0413098 - 2026-07-14"

setattr(rl_config, "invariant", True)

INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#5E6A7D")
ACCENT = colors.HexColor("#2563A6")
ACCENT_DARK = colors.HexColor("#173C68")
PALE_BLUE = colors.HexColor("#EAF2FA")
PALE_GRAY = colors.HexColor("#F4F6F8")
RULE = colors.HexColor("#CAD3DE")


def _register_fonts() -> tuple[str, str, str, str]:
    font_root = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    font_files = {
        "ResidualBody": "DejaVuSerif.ttf",
        "ResidualBody-Bold": "DejaVuSerif-Bold.ttf",
        "ResidualSans": "DejaVuSans.ttf",
        "ResidualSans-Bold": "DejaVuSans-Bold.ttf",
        "ResidualMono": "DejaVuSansMono.ttf",
    }
    try:
        for name, filename in font_files.items():
            pdfmetrics.registerFont(TTFont(name, str(font_root / filename)))
        pdfmetrics.registerFontFamily(
            "ResidualBody",
            normal="ResidualBody",
            bold="ResidualBody-Bold",
            italic="ResidualBody",
            boldItalic="ResidualBody-Bold",
        )
        return (
            "ResidualBody",
            "ResidualBody-Bold",
            "ResidualSans",
            "ResidualSans-Bold",
        )
    except Exception:
        return "Times-Roman", "Times-Bold", "Helvetica", "Helvetica-Bold"


F_BODY, F_BODY_BOLD, F_SANS, F_SANS_BOLD = _register_fonts()


def _styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=sample["Normal"],
            fontName=F_SANS_BOLD,
            fontSize=9,
            leading=11,
            textColor=ACCENT,
            alignment=TA_CENTER,
            tracking=1.2,
            spaceAfter=12,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=sample["Title"],
            fontName=F_SANS_BOLD,
            fontSize=25,
            leading=30,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            parent=sample["Normal"],
            fontName=F_SANS,
            fontSize=9.5,
            leading=14,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=5,
        ),
        "cover_summary": ParagraphStyle(
            "cover_summary",
            parent=sample["Normal"],
            fontName=F_BODY,
            fontSize=10.2,
            leading=15,
            textColor=INK,
            leftIndent=14,
            rightIndent=14,
            spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=sample["Heading1"],
            fontName=F_SANS_BOLD,
            fontSize=15,
            leading=18,
            textColor=ACCENT_DARK,
            spaceBefore=12,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "h2",
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
            fontSize=9.3,
            leading=13.4,
            textColor=INK,
            spaceAfter=6,
            allowWidows=0,
            allowOrphans=0,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=sample["BodyText"],
            fontName=F_BODY,
            fontSize=8.9,
            leading=12.7,
            textColor=INK,
            leftIndent=0,
            rightIndent=2,
            spaceAfter=3,
            allowWidows=0,
            allowOrphans=0,
        ),
        "number": ParagraphStyle(
            "number",
            parent=sample["BodyText"],
            fontName=F_BODY,
            fontSize=9,
            leading=13,
            textColor=INK,
            leftIndent=0,
            spaceAfter=3,
        ),
        "small": ParagraphStyle(
            "small",
            parent=sample["BodyText"],
            fontName=F_SANS,
            fontSize=7.8,
            leading=10.5,
            textColor=MUTED,
        ),
    }


def _inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(
        r"`([^`]+)`",
        lambda match: (
            '<font name="ResidualMono" size="7.5" color="#334155">'
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
        "## Article 1 - History, lineage, and trajectory residuals",
        "## Article 2 - Mathematics of constraint residuals",
        "## Article 3 - Philosophy: what it means residuals",
        "## Article 4 - Science of the program residuals",
        "## Article 5 - Software engineering residuals",
        "## Article 6 - Systems theory and complexity residuals",
        "M5 is complete as an experiment",
        "Recommended immediate queue",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise ValueError(f"Residual source is missing required sections: {missing}")
    if "\u2011" in text:
        raise ValueError("Residual source contains a nonbreaking hyphen")


def _cover(styles: dict[str, ParagraphStyle]) -> list[Any]:
    summary = (
        "A residual-only execution register after reconciling the six primer backlogs "
        "with merged contracts, experiments, M5, and the locked root quality gate. "
        "Completed negative results are preserved as completions; invalid runs remain "
        "non-evidence; overlapping work is collapsed into dependency-ordered waves."
    )
    control = Table(
        [
            ["Baseline", "origin/main 0413098"],
            ["Reconciled", "2026-07-14"],
            ["Scope", "Six primers and shared program infrastructure"],
            ["Disposition", "Residual work only"],
        ],
        colWidths=[1.15 * inch, 4.45 * inch],
        hAlign="CENTER",
    )
    control.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), F_SANS_BOLD),
                ("FONTNAME", (1, 0), (1, -1), F_SANS),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("TEXTCOLOR", (0, 0), (0, -1), ACCENT_DARK),
                ("TEXTCOLOR", (1, 0), (1, -1), INK),
                ("BACKGROUND", (0, 0), (-1, -1), PALE_GRAY),
                ("BOX", (0, 0), (-1, -1), 0.6, RULE),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, RULE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [
        Spacer(1, 0.72 * inch),
        Paragraph("RESEARCH PROGRAM OPERATING DOCUMENT", styles["cover_kicker"]),
        Paragraph(TITLE, styles["cover_title"]),
        HRFlowable(width="36%", thickness=2.2, color=ACCENT, hAlign="CENTER"),
        Spacer(1, 18),
        Paragraph("Human research director: Jawaun Brown", styles["cover_meta"]),
        Paragraph("Compiled by Codex", styles["cover_meta"]),
        Spacer(1, 20),
        Table(
            [[Paragraph(summary, styles["cover_summary"])]],
            colWidths=[5.75 * inch],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#AFC7DF")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ]
            ),
        ),
        Spacer(1, 24),
        control,
        Spacer(1, 18),
        Paragraph(
            "This artifact is a planning synthesis. Canonical scientific state remains in "
            "experiment manifests, evidence records, gate verdicts, and preregistrations.",
            styles["small"],
        ),
        PageBreak(),
    ]


def _body_flow(text: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
    lines = text.splitlines()
    flow: list[Any] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith("# "):
            index += 1
            continue
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if heading.startswith("Article ") or heading in {
                "Recommended immediate queue",
            }:
                flow.append(PageBreak())
            else:
                flow.append(CondPageBreak(1.1 * inch))
            flow.append(Paragraph(_inline(heading), styles["h1"]))
            flow.append(HRFlowable(width="100%", thickness=0.6, color=RULE))
            flow.append(Spacer(1, 3))
            index += 1
            continue
        if stripped.startswith("### "):
            flow.append(CondPageBreak(0.72 * inch))
            flow.append(Paragraph(_inline(stripped[4:].strip()), styles["h2"]))
            index += 1
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
                    bulletFontSize=6,
                    bulletColor=ACCENT,
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
                    bulletFontSize=8.2,
                    bulletColor=ACCENT_DARK,
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
    canvas.setLineWidth(0.5)
    canvas.line(0.8 * inch, 0.55 * inch, 7.7 * inch, 0.55 * inch)
    canvas.setFont(F_SANS, 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawCentredString(4.25 * inch, 0.36 * inch, BASELINE)
    canvas.restoreState()


def _later_pages(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(MUTED)
    canvas.setFont(F_SANS, 7.2)
    canvas.drawString(0.72 * inch, height - 0.48 * inch, "PRIMER RESIDUAL WORK REGISTER")
    canvas.drawRightString(width - 0.72 * inch, height - 0.48 * inch, "2026-07-14")
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(0.72 * inch, height - 0.57 * inch, width - 0.72 * inch, height - 0.57 * inch)
    canvas.line(0.72 * inch, 0.55 * inch, width - 0.72 * inch, 0.55 * inch)
    canvas.drawString(0.72 * inch, 0.35 * inch, "origin/main 0413098")
    canvas.drawRightString(width - 0.72 * inch, 0.35 * inch, f"Page {doc.page}")
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
        leftMargin=0.76 * inch,
        rightMargin=0.76 * inch,
        topMargin=0.74 * inch,
        bottomMargin=0.72 * inch,
        title=TITLE,
        author="Jawaun Brown; compiled by Codex",
        subject="Post-merge residual work across six research-program primers",
        creator="Research Derived Experiments",
        pageCompression=1,
    )
    document.build(flow, onFirstPage=_first_page, onLaterPages=_later_pages)
    return out_path


def main() -> int:
    output = build_pdf()
    print(f"Wrote {output} ({output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
