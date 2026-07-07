from __future__ import annotations

import json
import math
import re
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "comprehensive_literature_review.md"
OUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "lit_review"
PDF = OUT_DIR / "comprehensive_literature_review.pdf"


def clean_text(text: str) -> str:
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u0394": "Delta",
        "\u00e9": "e",
        "\u00f6": "o",
        "\u00f1": "n",
        "\u00fc": "u",
        "\u00e1": "a",
        "\u00ed": "i",
        "\u00e0": "a",
        "\u00e8": "e",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("**", "").replace("*", "")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = text.replace("&", "&amp;")
    text = text.replace("<font name='Courier'>", "%%FONT%%")
    text = text.replace("</font>", "%%ENDFONT%%")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("%%FONT%%", "<font name='Courier'>")
    text = text.replace("%%ENDFONT%%", "</font>")
    return text


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(clean_text(text), style)


def load_source_index() -> list[dict]:
    path = TMP_DIR / "source_index.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())


def load_references() -> list[str]:
    path = TMP_DIR / "references_raw.json"
    if not path.exists():
        return []
    rows = json.loads(path.read_text())
    seen: set[str] = set()
    refs: list[str] = []
    for row in rows:
        text = re.sub(r"\s+", " ", row.get("text", "")).strip()
        if len(text) < 10:
            continue
        text = text.lstrip("- ").strip()
        key = re.sub(r"[^a-z0-9]+", " ", text.lower())[:120]
        if key in seen:
            continue
        seen.add(key)
        refs.append(text)
    return refs


def make_visuals() -> list[Path]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    graph_path = TMP_DIR / "review_concept_map.png"
    timeline_path = TMP_DIR / "review_arc_timeline.png"

    nodes = {
        "Concern": "#f2c14e",
        "Geometry": "#7fb069",
        "Self/world": "#4d9de0",
        "Inquiry": "#e15554",
        "Planning": "#7768ae",
        "Memory": "#3bb273",
        "OOD structure": "#ef8354",
        "Governance": "#5d737e",
        "Viability": "#f2c14e",
        "Intervention": "#4d9de0",
        "Calibration": "#e15554",
        "Symmetry": "#ef8354",
    }
    edges = [
        ("Viability", "Concern"),
        ("Concern", "Geometry"),
        ("Geometry", "Planning"),
        ("Geometry", "OOD structure"),
        ("Self/world", "Intervention"),
        ("Intervention", "Calibration"),
        ("Inquiry", "Calibration"),
        ("Inquiry", "Memory"),
        ("Memory", "Planning"),
        ("OOD structure", "Symmetry"),
        ("Governance", "Concern"),
        ("Governance", "Planning"),
        ("Concern", "Self/world"),
        ("Planning", "Intervention"),
    ]
    pos = {
        "Viability": (0.03, 0.72),
        "Concern": (0.22, 0.72),
        "Geometry": (0.42, 0.72),
        "Planning": (0.65, 0.75),
        "Governance": (0.86, 0.72),
        "Self/world": (0.20, 0.46),
        "Intervention": (0.40, 0.46),
        "Calibration": (0.62, 0.46),
        "Inquiry": (0.82, 0.46),
        "Memory": (0.74, 0.20),
        "OOD structure": (0.36, 0.20),
        "Symmetry": (0.14, 0.20),
    }
    plt.figure(figsize=(10, 7), dpi=180)
    ax = plt.gca()
    for a, b in edges:
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color="#30343f", alpha=0.35, linewidth=1.8)
    for name, color in nodes.items():
        x, y = pos[name]
        circle = plt.Circle((x, y), 0.07, facecolor=color, edgecolor="#222222", linewidth=1.2)
        ax.add_patch(circle)
        label = "\n".join(textwrap.wrap(name, width=12))
        ax.text(x, y, label, ha="center", va="center", fontsize=9, weight="bold")
    plt.title("Program concept map: constraints become action surfaces", fontsize=14)
    plt.xlim(-0.06, 0.98)
    plt.ylim(0.07, 0.86)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(graph_path)
    plt.close()

    arcs = [
        ("Concern geometry", 1, 4),
        ("Boundary failure", 3, 5),
        ("Self/world attribution", 5, 6),
        ("Re-engagement", 7, 4),
        ("Planning closure", 8, 3),
        ("Long-horizon memory", 9, 4),
        ("Structure-compatible OOD", 10, 5),
        ("Typed ontology", 11, 3),
        ("Virtual governance", 12, 3),
    ]
    plt.figure(figsize=(10, 5.5), dpi=180)
    y = list(range(len(arcs)))
    colors_ = ["#f2c14e", "#7fb069", "#4d9de0", "#e15554", "#7768ae", "#3bb273", "#ef8354", "#8d99ae", "#5d737e"]
    for idx, (name, start, span) in enumerate(arcs):
        plt.barh(idx, span, left=start, color=colors_[idx], edgecolor="#222222", height=0.58)
        plt.text(start + span / 2, idx, name, ha="center", va="center", fontsize=8.5, weight="bold")
    plt.yticks([])
    plt.xticks(range(1, 17), [f"P{x}" for x in range(1, 17)], fontsize=8)
    plt.xlabel("Approximate research progression, not strict paper numbering")
    plt.title("Research arcs and when they become load-bearing")
    plt.grid(axis="x", alpha=0.18)
    plt.tight_layout()
    plt.savefig(timeline_path)
    plt.close()

    return [graph_path, timeline_path]


def markdown_to_flowables(text: str, styles: dict[str, ParagraphStyle]) -> list:
    flow = []
    pending_list: list[str] = []

    def flush_list() -> None:
        nonlocal pending_list
        if not pending_list:
            return
        rows = [[paragraph(f"• {item}", styles["Bullet"])] for item in pending_list]
        table = Table(rows, colWidths=[6.7 * inch])
        table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
        flow.append(table)
        flow.append(Spacer(1, 0.06 * inch))
        pending_list = []

    paras: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            flush_list()
            if paras:
                flow.append(paragraph(" ".join(paras), styles["Body"]))
                flow.append(Spacer(1, 0.07 * inch))
                paras = []
            continue
        if line.startswith("# "):
            flush_list()
            if paras:
                flow.append(paragraph(" ".join(paras), styles["Body"]))
                paras = []
            flow.append(paragraph(line[2:], styles["Title"]))
            flow.append(Spacer(1, 0.16 * inch))
        elif line.startswith("## "):
            flush_list()
            if paras:
                flow.append(paragraph(" ".join(paras), styles["Body"]))
                paras = []
            flow.append(Spacer(1, 0.08 * inch))
            flow.append(paragraph(line[3:], styles["H2"]))
        elif line.startswith("### "):
            flush_list()
            if paras:
                flow.append(paragraph(" ".join(paras), styles["Body"]))
                paras = []
            flow.append(Spacer(1, 0.04 * inch))
            flow.append(paragraph(line[4:], styles["H3"]))
        elif line.startswith("- "):
            if paras:
                flow.append(paragraph(" ".join(paras), styles["Body"]))
                paras = []
            pending_list.append(line[2:].strip())
        elif re.match(r"^\d+\. ", line):
            if paras:
                flow.append(paragraph(" ".join(paras), styles["Body"]))
                paras = []
            pending_list.append(line.strip())
        elif line.startswith("> "):
            flush_list()
            if paras:
                flow.append(paragraph(" ".join(paras), styles["Body"]))
                paras = []
            flow.append(paragraph(line[2:].strip(), styles["Quote"]))
        else:
            paras.append(line)
    flush_list()
    if paras:
        flow.append(paragraph(" ".join(paras), styles["Body"]))
    return flow


def add_source_appendix(flow: list, styles: dict[str, ParagraphStyle]) -> None:
    records = load_source_index()
    papers = [
        r
        for r in records
        if r.get("file", "").startswith("papers/")
        and (r.get("file", "").endswith("paper.md") or r.get("file", "").endswith("paper.tex"))
    ]
    if not papers:
        return
    flow.append(PageBreak())
    flow.append(paragraph("Appendix A: Repository Paper Coverage", styles["H2"]))
    intro = (
        "This table is generated from the repository source index and records the primary paper files "
        "covered by the review. It is intentionally compact; paper PDFs, preregistrations, reviews, notes, "
        "and figures were also included where they supplied evidence or framing."
    )
    flow.append(paragraph(intro, styles["Body"]))
    rows = [[paragraph("File", styles["TableHead"]), paragraph("Title", styles["TableHead"])]]
    for r in papers:
        rows.append(
            [
                paragraph(r.get("file", ""), styles["TableSmall"]),
                paragraph(r.get("title", "") or "(title parsed from TeX/PDF package)", styles["TableSmall"]),
            ]
        )
    table = Table(rows, colWidths=[2.5 * inch, 4.2 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#273043")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b8c1cc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    flow.append(table)


def add_reference_appendix(flow: list, styles: dict[str, ParagraphStyle]) -> None:
    refs = load_references()
    if not refs:
        return
    flow.append(PageBreak())
    flow.append(paragraph("Appendix B: Extracted Citation Surface", styles["H2"]))
    flow.append(
        paragraph(
            "The following unique-ish reference lines were extracted from paper reference sections, notes, "
            "source manifests, and BibTeX files. Some are internal companion papers rather than external sources.",
            styles["Body"],
        )
    )
    for idx, ref in enumerate(refs[:260], start=1):
        wrapped = f"{idx}. {ref}"
        flow.append(paragraph(wrapped, styles["Ref"]))
    if len(refs) > 260:
        flow.append(paragraph(f"... {len(refs) - 260} additional raw lines omitted for print length.", styles["Ref"]))


def build_pdf() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    visuals = make_visuals()

    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.HexColor("#1f2933"),
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor("#273043"),
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=15,
            spaceBefore=7,
            spaceAfter=4,
            textColor=colors.HexColor("#324a5f"),
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.7,
            leading=13.1,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=12.4,
        ),
        "Quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=10.3,
            leading=14,
            leftIndent=0.25 * inch,
            rightIndent=0.25 * inch,
            textColor=colors.HexColor("#38434f"),
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=colors.white,
        ),
        "TableSmall": ParagraphStyle(
            "TableSmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.3,
            leading=9,
        ),
        "Ref": ParagraphStyle(
            "Ref",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.4,
            leading=9.2,
            leftIndent=0.12 * inch,
            firstLineIndent=-0.12 * inch,
        ),
    }

    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title="Comprehensive Literature Review",
        author="Research Derived Experiments",
    )

    flow = markdown_to_flowables(DOC.read_text(), styles)
    visual_flow = [
        PageBreak(),
        KeepTogether(
            [
                paragraph("Visual overview", styles["H2"]),
                paragraph(
                    "The concept map shows the program's recurring move from viability constraints to local action surfaces. "
                    "The arc timeline is approximate and shows when each theme becomes experimentally load-bearing.",
                    styles["Body"],
                ),
                Image(str(visuals[0]), width=6.4 * inch, height=4.45 * inch),
                Spacer(1, 0.1 * inch),
                Image(str(visuals[1]), width=6.4 * inch, height=3.52 * inch),
            ]
        )
    ]
    flow.extend(visual_flow)
    add_source_appendix(flow, styles)
    add_reference_appendix(flow, styles)

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#697586"))
        canvas.drawString(0.65 * inch, 0.35 * inch, "Comprehensive Literature Review - Research Derived Experiments")
        canvas.drawRightString(7.85 * inch, 0.35 * inch, str(document.page))
        canvas.restoreState()

    doc.build(flow, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build_pdf()
