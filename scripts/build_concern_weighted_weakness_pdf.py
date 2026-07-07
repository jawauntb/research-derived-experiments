#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the concern-weighted weakness theory note to PDF.

Run:
    python scripts/build_concern_weighted_weakness_pdf.py

Outputs:
    papers/concern_weighted_weakness/paper.pdf
    papers/pdf/concern_weighted_weakness.pdf
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "papers" / "concern_weighted_weakness"
PAPER_MD = PAPER_DIR / "paper.md"
OUT_PDF = PAPER_DIR / "paper.pdf"
COPY_PDF = ROOT / "papers" / "pdf" / "concern_weighted_weakness.pdf"
FIG_DIR = PAPER_DIR / "figures"


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=20,
            leading=23,
            alignment=TA_CENTER,
            spaceAfter=8,
            textColor=colors.HexColor("#111827"),
        ),
        "Meta": ParagraphStyle(
            "Meta",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=2,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=13,
            leading=15,
            spaceBefore=9,
            spaceAfter=4,
            textColor=colors.HexColor("#111827"),
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Times-Bold",
            fontSize=11.4,
            leading=13,
            spaceBefore=7,
            spaceAfter=3,
            textColor=colors.HexColor("#1f2937"),
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=9.45,
            leading=12.2,
            spaceAfter=4.5,
            alignment=TA_LEFT,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=9.1,
            leading=11.5,
            leftIndent=14,
            firstLineIndent=-8,
            spaceAfter=2.5,
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.8,
            leading=9.5,
            leftIndent=10,
            rightIndent=10,
            spaceBefore=3,
            spaceAfter=5,
            backColor=colors.HexColor("#f8fafc"),
            borderColor=colors.HexColor("#d1d5db"),
            borderWidth=0.4,
            borderPadding=5,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Times-Italic",
            fontSize=8.2,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4b5563"),
            spaceBefore=2,
            spaceAfter=7,
        ),
        "Ref": ParagraphStyle(
            "Ref",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=8.3,
            leading=10.2,
            leftIndent=14,
            firstLineIndent=-14,
            spaceAfter=2.2,
        ),
    }


def inline_markup(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(inline_markup(text), style)


def make_ladder_figure() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "fig1_theorem_ladder.png"
    fig, ax = plt.subplots(figsize=(7.0, 2.35), dpi=200)
    ax.axis("off")
    labels = [
        "Bennett\nextension\n|Z_h|",
        "Restrict\nto U",
        "Group\nblocks",
        "Concern\nweights",
        "Load-bearing\ngates",
    ]
    xs = [0.08, 0.29, 0.50, 0.71, 0.92]
    for i, (x, label) in enumerate(zip(xs, labels, strict=True)):
        color = "#dbeafe" if i < 2 else "#dcfce7" if i < 4 else "#fee2e2"
        ax.text(
            x,
            0.52,
            label,
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": color,
                "edgecolor": "#334155",
                "linewidth": 0.8,
            },
        )
    for x1, x2 in zip(xs[:-1], xs[1:], strict=True):
        ax.annotate(
            "",
            xy=(x2 - 0.075, 0.52),
            xytext=(x1 + 0.075, 0.52),
            arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "#334155"},
        )
    ax.text(
        0.5,
        0.12,
        "The first four steps are proved; load-bearing gates are the formal evaluation filter.",
        ha="center",
        va="center",
        fontsize=8.4,
        color="#475569",
    )
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def add_image(flow: list[Any], image_path: Path, caption: str, st: dict[str, ParagraphStyle]) -> None:
    flow.append(Spacer(1, 4))
    flow.append(Image(str(image_path), width=6.4 * inch, height=2.15 * inch))
    flow.append(Paragraph(inline_markup(caption), st["Caption"]))


def flush_paragraph(lines: list[str], flow: list[Any], st: dict[str, ParagraphStyle]) -> None:
    if not lines:
        return
    text = " ".join(line.strip() for line in lines if line.strip())
    if text:
        flow.append(para(text, st["Body"]))
    lines.clear()


def flush_list(items: list[str], flow: list[Any], st: dict[str, ParagraphStyle]) -> None:
    if not items:
        return
    for item in items:
        flow.append(para("- " + item, st["Bullet"]))
    flow.append(Spacer(1, 2))
    items.clear()


def markdown_to_flow(text: str, st: dict[str, ParagraphStyle]) -> list[Any]:
    flow: list[Any] = []
    para_lines: list[str] = []
    list_items: list[str] = []
    code_lines: list[str] = []
    in_code = False
    title_seen = False

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                flow.append(Preformatted("\n".join(code_lines), st["Code"]))
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph(para_lines, flow, st)
                flush_list(list_items, flow, st)
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            continue
        if line.startswith("# "):
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            if title_seen:
                flow.append(PageBreak())
            title_seen = True
            flow.append(para(line[2:].strip(), st["Title"]))
            continue
        if line.startswith("**Subtitle.**") or line.startswith("**Author.**"):
            flush_paragraph(para_lines, flow, st)
            flow.append(Paragraph(inline_markup(line), st["Meta"]))
            continue
        if line.startswith("## "):
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            flow.append(para(line[3:].strip(), st["H2"]))
            continue
        if line.startswith("### "):
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            flow.append(para(line[4:].strip(), st["H3"]))
            continue
        image_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if image_match:
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            add_image(flow, PAPER_DIR / image_match.group(2), image_match.group(1), st)
            continue
        if re.match(r"^\d+\. ", line):
            flush_paragraph(para_lines, flow, st)
            list_items.append(re.sub(r"^\d+\. ", "", line).strip())
            continue
        if line.startswith("- "):
            flush_paragraph(para_lines, flow, st)
            list_items.append(line[2:].strip())
            continue
        para_lines.append(line)

    flush_paragraph(para_lines, flow, st)
    flush_list(list_items, flow, st)
    return flow


def build_pdf() -> Path:
    fig = make_ladder_figure()
    md_text = PAPER_MD.read_text(encoding="utf-8")
    if "![Theorem ladder]" not in md_text:
        insertion = (
            "\n![Theorem ladder](figures/fig1_theorem_ladder.png)\n\n"
        )
        md_text = md_text.replace("## 2. Setup\n", insertion + "## 2. Setup\n")
    st = styles()
    flow = markdown_to_flow(md_text, st)
    # Ensure the generated figure exists even if the markdown was edited later.
    assert fig.exists()
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.72 * inch,
        title="Concern-Weighted Weakness",
        author="Jawaun Brown",
    )
    doc.build(flow)
    COPY_PDF.parent.mkdir(parents=True, exist_ok=True)
    COPY_PDF.write_bytes(OUT_PDF.read_bytes())
    return OUT_PDF


def main() -> int:
    out = build_pdf()
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    print(f"Wrote {COPY_PDF} ({COPY_PDF.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
