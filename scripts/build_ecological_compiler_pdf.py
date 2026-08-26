#!/usr/bin/env python3
"""Build the Ecological Compiler essay as a publication-ready PDF."""

from __future__ import annotations

import html
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import Font
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "papers" / "ecological_compiler" / "paper.md"
SUMMARY = ROOT / "experiments" / "ecological_compiler" / "results" / "summary.json"
FIGURE = (
    ROOT / "experiments" / "ecological_compiler" / "results" / "model_coefficients.png"
)
OUTPUT = ROOT / "output" / "pdf" / "the_ecological_compiler_2026-08-26.pdf"
DATE = "AUGUST 26, 2026"
LEFT_MARGIN = 0.88 * inch
RIGHT_MARGIN = 0.88 * inch
TOP_MARGIN = 0.83 * inch
BOTTOM_MARGIN = 0.78 * inch
FONT_ROOT = Path("/System/Library/Fonts/Supplemental")

NAVY = colors.HexColor("#15283B")
TEAL = colors.HexColor("#147D7A")
COPPER = colors.HexColor("#BF6B35")
INK = colors.HexColor("#26333D")
SLATE = colors.HexColor("#657681")
PALE = colors.HexColor("#EFF5F3")
RULE = colors.HexColor("#D3DEE2")


def register_fonts() -> None:
    local_fonts = {
        "TNR": FONT_ROOT / "Times New Roman.ttf",
        "TNR-Bold": FONT_ROOT / "Times New Roman Bold.ttf",
        "TNR-Italic": FONT_ROOT / "Times New Roman Italic.ttf",
        "TNR-BoldItalic": FONT_ROOT / "Times New Roman Bold Italic.ttf",
    }
    if all(path.is_file() for path in local_fonts.values()):
        for name, path in local_fonts.items():
            pdfmetrics.registerFont(TTFont(name, path))
    else:
        builtin_fonts = {
            "TNR": "Times-Roman",
            "TNR-Bold": "Times-Bold",
            "TNR-Italic": "Times-Italic",
            "TNR-BoldItalic": "Times-BoldItalic",
        }
        for name, face in builtin_fonts.items():
            pdfmetrics.registerFont(Font(name, face, "WinAnsiEncoding"))
    pdfmetrics.registerFontFamily(
        "TNR",
        normal="TNR",
        bold="TNR-Bold",
        italic="TNR-Italic",
        boldItalic="TNR-BoldItalic",
    )


def inline_markup(value: object) -> str:
    text = str(value)
    tokens: list[str] = []

    def hold(pattern: str, replacement: str) -> None:
        nonlocal text

        def replace(match: re.Match[str]) -> str:
            tokens.append(replacement.format(html.escape(match.group(1))))
            return f"@@TOKEN{len(tokens) - 1}@@"

        text = re.sub(pattern, replace, text)

    hold(r"<((?:https?://)[^>]+)>", '<link href="{0}" color="#147D7A">{0}</link>')
    hold(r"`([^`]+)`", '<font name="Courier" color="#315B67">{0}</font>')
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    for index, token in enumerate(tokens):
        text = text.replace(f"@@TOKEN{index}@@", token)
    return text


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Kicker": ParagraphStyle(
            "Kicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.6,
            leading=11,
            tracking=1.6,
            alignment=TA_CENTER,
            textColor=TEAL,
            spaceAfter=18,
        ),
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=33,
            alignment=TA_CENTER,
            textColor=NAVY,
            spaceAfter=14,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="TNR-Italic",
            fontSize=15,
            leading=20,
            alignment=TA_CENTER,
            textColor=INK,
            spaceAfter=24,
        ),
        "Byline": ParagraphStyle(
            "Byline",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=SLATE,
        ),
        "Abstract": ParagraphStyle(
            "Abstract",
            parent=base["BodyText"],
            fontName="TNR",
            fontSize=9.3,
            leading=13.2,
            leftIndent=24,
            rightIndent=24,
            borderColor=TEAL,
            borderWidth=1.2,
            borderPadding=12,
            backColor=PALE,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=9,
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=NAVY,
            spaceBefore=16,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=TEAL,
            spaceBefore=11,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="TNR",
            fontSize=9.45,
            leading=13.15,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=6.2,
        ),
        "Reference": ParagraphStyle(
            "Reference",
            parent=base["BodyText"],
            fontName="TNR",
            fontSize=8.2,
            leading=10.4,
            leftIndent=14,
            firstLineIndent=-14,
            textColor=INK,
            spaceAfter=4.5,
        ),
        "Equation": ParagraphStyle(
            "Equation",
            parent=base["BodyText"],
            fontName="TNR-Italic",
            fontSize=10.2,
            leading=14,
            alignment=TA_CENTER,
            textColor=NAVY,
            borderColor=RULE,
            borderWidth=0.7,
            borderPadding=9,
            backColor=colors.HexColor("#F7F9FA"),
            leftIndent=24,
            rightIndent=24,
            spaceBefore=5,
            spaceAfter=9,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="TNR",
            fontSize=9.25,
            leading=12.8,
            leftIndent=18,
            firstLineIndent=-10,
            bulletIndent=3,
            textColor=INK,
            spaceAfter=4,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=9,
            textColor=colors.white,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="TNR",
            fontSize=7.5,
            leading=9.4,
            textColor=INK,
        ),
        "TOCHead": ParagraphStyle(
            "TOCHead",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=NAVY,
            spaceAfter=14,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=9.4,
            textColor=SLATE,
            alignment=TA_LEFT,
            spaceBefore=4,
            spaceAfter=9,
        ),
    }


class EssayTemplate(BaseDocTemplate):
    def afterFlowable(self, flowable: object) -> None:  # noqa: N802
        if not isinstance(flowable, Paragraph) or flowable.style.name != "H1":
            return
        title = flowable.getPlainText()
        key = f"section-{self.seq.nextf('section')}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=0)
        self.notify("TOCEntry", (0, title, self.page, key))


def page_furniture(canvas: Any, document: EssayTemplate) -> None:
    canvas.saveState()
    width, height = letter
    if document.page > 1:
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(
            0.72 * inch, height - 0.61 * inch, width - 0.72 * inch, height - 0.61 * inch
        )
        canvas.setFont("Helvetica", 7.1)
        canvas.setFillColor(SLATE)
        canvas.drawString(0.72 * inch, height - 0.46 * inch, "THE ECOLOGICAL COMPILER")
        canvas.drawRightString(
            width - 0.72 * inch, height - 0.46 * inch, "JAWAUN BROWN"
        )
        canvas.line(0.72 * inch, 0.57 * inch, width - 0.72 * inch, 0.57 * inch)
        canvas.drawString(0.72 * inch, 0.38 * inch, "Research Derived Experiments")
        canvas.drawRightString(width - 0.72 * inch, 0.38 * inch, f"{document.page}")
    canvas.restoreState()


def cover(st: dict[str, ParagraphStyle], summary: dict[str, Any]) -> list[Any]:
    gates = summary["gates"]
    passed = sum(value == "PASS" for value in gates.values())
    failed = len(gates) - passed
    adjusted_societies = int(summary["models"]["m1"]["n"])
    registered_resamples = sum(
        int(result["requested_draws"]) for result in summary["uncertainty"].values()
    )
    verdict = str(summary["verdict"]).upper()
    claim_tier = str(summary["claim_tier"])
    metric_style = ParagraphStyle(
        "Metric",
        parent=st["Title"],
        fontSize=22,
        leading=25,
        textColor=TEAL,
        spaceAfter=1,
    )
    metric_label = ParagraphStyle(
        "MetricLabel",
        parent=st["Byline"],
        fontSize=7.4,
        leading=9.2,
    )
    metrics = Table(
        [
            [
                Paragraph(f"{adjusted_societies:,}", metric_style),
                Paragraph(f"{registered_resamples:,}", metric_style),
                Paragraph(f"{passed} / {failed}", metric_style),
            ],
            [
                Paragraph("adjusted societies", metric_label),
                Paragraph("registered resamples", metric_label),
                Paragraph("gates passed / failed", metric_label),
            ],
        ],
        colWidths=[2.05 * inch] * 3,
        style=TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBEFORE", (1, 0), (1, -1), 0.6, RULE),
                ("LINEBEFORE", (2, 0), (2, -1), 0.6, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        ),
    )
    return [
        Spacer(1, 0.72 * inch),
        Paragraph("RESEARCH ESSAY + PREREGISTERED STUDY", st["Kicker"]),
        Paragraph("The Ecological Compiler", st["Title"]),
        Paragraph(
            "Marine Nutrition, Maritime Connectivity, and the Persistence of Collective Capability",
            st["Subtitle"],
        ),
        Spacer(1, 0.08 * inch),
        metrics,
        Spacer(1, 0.46 * inch),
        Paragraph("Jawaun Brown", st["Byline"]),
        Paragraph(DATE, st["Byline"]),
        Spacer(1, 0.22 * inch),
        Paragraph(
            f"Registered verdict: <b>{verdict}</b> at the {claim_tier} claim tier",
            ParagraphStyle(
                "Verdict",
                parent=st["Byline"],
                fontName="Helvetica-Bold",
                textColor=COPPER,
            ),
        ),
        PageBreak(),
    ]


def render_table(rows: list[list[str]], st: dict[str, ParagraphStyle]) -> LongTable:
    n_columns = len(rows[0])
    if n_columns == 5:
        widths = [1.72 * inch, 0.62 * inch, 1.15 * inch, 1.2 * inch, 0.72 * inch]
    elif n_columns == 3:
        widths = [1.65 * inch, 0.58 * inch, 4.02 * inch]
    else:
        widths = [6.25 * inch / n_columns] * n_columns
    rendered = []
    for row_index, row in enumerate(rows):
        style = st["TableHead"] if row_index == 0 else st["TableCell"]
        rendered.append([Paragraph(inline_markup(cell), style) for cell in row])
    result = LongTable(rendered, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.35, RULE),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F4F7F8")],
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return result


def clean_equation(lines: list[str]) -> str:
    value = " ".join(line.strip() for line in lines)
    replacements = {
        r"\text{": "",
        "}": "",
        r"\rightarrow": "  ->  ",
        r"\neq": " != ",
        r"\times": " x ",
        r"\eta": "eta",
        r"\Delta": "Delta",
        r"\[": "",
        r"\]": "",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value


def narrative_flow(markdown: str, st: dict[str, ParagraphStyle]) -> list[Any]:
    lines = markdown.splitlines()
    flow: list[Any] = []
    paragraph: list[str] = []
    equation: list[str] = []
    in_equation = False
    in_references = False
    index = 0

    def flush() -> None:
        if not paragraph:
            return
        style = st["Reference"] if in_references else st["Body"]
        flow.append(Paragraph(inline_markup(" ".join(paragraph)), style))
        paragraph.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        if line.strip() == r"\[":
            flush()
            in_equation = True
            equation.clear()
            index += 1
            continue
        if in_equation:
            if line.strip() == r"\]":
                flow.append(
                    Paragraph(inline_markup(clean_equation(equation)), st["Equation"])
                )
                in_equation = False
            else:
                equation.append(line)
            index += 1
            continue
        if (
            line.startswith("|")
            and index + 1 < len(lines)
            and re.match(r"^\|(?:\s*:?-+:?\s*\|)+$", lines[index + 1].strip())
        ):
            flush()
            rows: list[list[str]] = []
            rows.append([cell.strip() for cell in line.strip("|").split("|")])
            index += 2
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                rows.append(
                    [
                        cell.strip()
                        for cell in lines[index].strip().strip("|").split("|")
                    ]
                )
                index += 1
            flow.append(render_table(rows, st))
            flow.append(Spacer(1, 0.1 * inch))
            continue
        heading = re.match(r"^(#{2,3})\s+(.+)$", line)
        if heading:
            flush()
            title = heading.group(2)
            in_references = title == "References"
            style = st["H1"] if len(heading.group(1)) == 2 else st["H2"]
            flow.append(Paragraph(inline_markup(title), style))
            if title == "IV. The result: a signal that does not generalize":
                chart = Image(str(FIGURE), width=5.95 * inch, height=3.4 * inch)
                flow.extend(
                    [
                        Spacer(1, 0.05 * inch),
                        chart,
                        Paragraph(
                            "Figure 1. Registered ordered-logit estimates. The orange interval is the 300-draw language-family block interval for M1; thin intervals are optimizer-Hessian approximations and are not the primary uncertainty estimate.",
                            st["Caption"],
                        ),
                    ]
                )
            index += 1
            continue
        numbered = re.match(r"^(\d+)\.\s+(.+)$", line)
        if numbered:
            flush()
            flow.append(
                Paragraph(
                    inline_markup(numbered.group(2)),
                    st["Bullet"],
                    bulletText=f"{numbered.group(1)}.",
                )
            )
            index += 1
            continue
        if not line.strip():
            flush()
            index += 1
            continue
        if (
            line.startswith("# ")
            or line.startswith("**Jawaun Brown**")
            or line.startswith("**August 26")
        ):
            index += 1
            continue
        paragraph.append(line.strip())
        index += 1
    flush()
    return flow


def build() -> Path:
    register_fonts()
    if not FIGURE.is_file():
        raise FileNotFoundError(f"registered coefficient figure not found: {FIGURE}")
    summary_bytes = SUMMARY.read_bytes()
    summary = json.loads(summary_bytes)
    markdown = SOURCE.read_text(encoding="utf-8")
    digest_match = re.search(
        r"final result JSON has SHA-256 digest `([0-9a-f]{64})`", markdown
    )
    if digest_match is None:
        raise ValueError("paper does not declare the final result JSON digest")
    actual_digest = hashlib.sha256(summary_bytes).hexdigest()
    if digest_match.group(1) != actual_digest:
        raise ValueError(
            "paper result digest does not match experiments/ecological_compiler/"
            "results/summary.json"
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    st = styles()
    document = EssayTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="The Ecological Compiler",
        author="Jawaun Brown",
        subject="Marine nutrition, maritime connectivity, and collective capability",
        creator="Research Derived Experiments",
    )
    frame = Frame(
        LEFT_MARGIN,
        BOTTOM_MARGIN,
        document.width,
        document.height,
        id="body",
    )
    document.addPageTemplates(
        [PageTemplate(id="essay", frames=[frame], onPage=page_furniture)]
    )

    abstract_match = re.search(r"### Abstract\n\n(.+?)\n\n## I\.", markdown, flags=re.S)
    if abstract_match is None:
        raise ValueError("paper abstract not found")
    story = cover(st, summary)
    story.append(Paragraph("Abstract", st["H1"]))
    story.append(
        Paragraph(
            inline_markup(abstract_match.group(1).replace("\n", " ")), st["Abstract"]
        )
    )
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1",
            fontName="TNR",
            fontSize=9.2,
            leading=13,
            leftIndent=0,
            firstLineIndent=0,
            textColor=INK,
            spaceBefore=2,
        )
    ]
    story.extend([PageBreak(), Paragraph("Contents", st["TOCHead"]), toc, PageBreak()])
    narrative = markdown[markdown.index("## I.") :]
    story.extend(narrative_flow(narrative, st))
    document.multiBuild(story)

    reader = PdfReader(str(OUTPUT))
    if len(reader.pages) < 10:
        raise RuntimeError(f"unexpectedly short PDF: {len(reader.pages)} pages")
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
    rendered_verdict = f"Registered verdict: {str(summary['verdict']).upper()}"
    for required in (
        "The Ecological Compiler",
        "The registered headline failed",
        rendered_verdict,
        "Figure 1. Registered ordered-logit estimates",
        "References",
    ):
        if required not in extracted:
            raise RuntimeError(f"missing rendered text: {required}")
    return OUTPUT


if __name__ == "__main__":
    print(build())
