from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "papers" / "external_citation_review"
PAPER_MD = REVIEW / "paper.md"
OUT_PDF = REVIEW / "paper.pdf"
TMP = ROOT / "tmp" / "external_citation_review"


def sanitize(text: str) -> str:
    replacements = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "\u00d7": "x",
        "\u2248": "approx.",
        "\u2192": "->",
        "\u2260": "!=",
        "\u2264": "<=",
        "\u2265": ">=",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.replace("**", "")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = text.replace("&", "&amp;")
    text = text.replace("<font name='Courier'>", "%%FONT%%").replace("</font>", "%%ENDFONT%%")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("%%FONT%%", "<font name='Courier'>").replace("%%ENDFONT%%", "</font>")
    return text


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(sanitize(text), style)


def load_json(name: str):
    return json.loads((REVIEW / name).read_text())


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#203040"),
            spaceAfter=12,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13.8,
            leading=16.8,
            textColor=colors.HexColor("#253858"),
            spaceBefore=9,
            spaceAfter=5,
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13.5,
            textColor=colors.HexColor("#324a5f"),
            spaceBefore=6,
            spaceAfter=3,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.05,
            leading=11.75,
            spaceAfter=4,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.65,
            leading=11.1,
            leftIndent=14,
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=6.4,
            leading=7.6,
        ),
        "HeadSmall": ParagraphStyle(
            "HeadSmall",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=6.6,
            leading=7.8,
            textColor=colors.white,
        ),
    }


def markdown_flow(text: str, st: dict[str, ParagraphStyle]) -> list:
    flow: list = []
    list_items: list[str] = []
    lines: list[str] = []

    def flush_para() -> None:
        if lines:
            flow.append(para(" ".join(lines), st["Body"]))
            flow.append(Spacer(1, 0.035 * inch))
            lines.clear()

    def flush_list() -> None:
        if not list_items:
            return
        for item in list_items:
            prefix = "" if re.match(r"^\d+\. ", item) else "- "
            flow.append(para(prefix + item, st["Bullet"]))
        flow.append(Spacer(1, 0.04 * inch))
        list_items.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            flush_para()
            flush_list()
            continue
        if line.startswith("# "):
            flush_para()
            flush_list()
            flow.append(para(line[2:], st["Title"]))
        elif line.startswith("## "):
            flush_para()
            flush_list()
            flow.append(para(line[3:], st["H2"]))
        elif line.startswith("### "):
            flush_para()
            flush_list()
            flow.append(para(line[4:], st["H3"]))
        elif line.startswith("- "):
            flush_para()
            list_items.append(line[2:].strip())
        elif re.match(r"^\d+\. ", line):
            flush_para()
            list_items.append(line.strip())
        else:
            lines.append(line)
    flush_para()
    flush_list()
    return flow


def make_figures() -> list[Path]:
    TMP.mkdir(parents=True, exist_ok=True)
    summary = load_json("enrichment_summary.json")
    figs: list[Path] = []

    fig1 = TMP / "status_counts.png"
    labels = list(summary["status_counts"].keys())
    vals = [summary["status_counts"][label] for label in labels]
    plt.figure(figsize=(9.2, 4.8), dpi=180)
    plt.barh(labels, vals, color=["#2a9d8f", "#8ab17d", "#f4a261", "#e76f51"], edgecolor="#222")
    plt.title("External citation resolution status")
    plt.xlabel("atomized candidate count")
    plt.tight_layout()
    plt.savefig(fig1)
    plt.close()
    figs.append(fig1)

    fig2 = TMP / "topic_counts.png"
    labels = list(summary["topic_counts"].keys())
    vals = [summary["topic_counts"][label] for label in labels]
    plt.figure(figsize=(9.2, 4.8), dpi=180)
    plt.barh(labels, vals, color="#4d9de0", edgecolor="#222")
    plt.title("External citation topic coverage")
    plt.xlabel("candidate count tagged")
    plt.tight_layout()
    plt.savefig(fig2)
    plt.close()
    figs.append(fig2)

    fig3 = TMP / "evidence_counts.png"
    labels = list(summary["evidence_level_counts"].keys())
    vals = [summary["evidence_level_counts"][label] for label in labels]
    plt.figure(figsize=(8.4, 4.8), dpi=180)
    plt.pie(vals, labels=labels, autopct="%1.0f%%", colors=["#7fb069", "#f2c14e", "#ef8354"])
    plt.title("Evidence level mix")
    plt.tight_layout()
    plt.savefig(fig3)
    plt.close()
    figs.append(fig3)
    return figs


def add_figures(flow: list, st: dict[str, ParagraphStyle]) -> None:
    flow.append(PageBreak())
    flow.append(para("Figures", st["H2"]))
    captions = [
        "Figure 1. How many atomized external references were resolved, preserved as manual seeds, or left unresolved.",
        "Figure 2. Topic coverage across resolved and unresolved external/reference candidates.",
        "Figure 3. Evidence-level mix after arXiv/OpenAlex/Semantic Scholar exact-ID/DOI/web-search repair.",
    ]
    for caption, fig in zip(captions, make_figures(), strict=True):
        flow.append(para(caption, st["H3"]))
        flow.append(Image(str(fig), width=6.45 * inch, height=3.36 * inch))
        flow.append(Spacer(1, 0.08 * inch))


def table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#253858")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c7d0d9")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]
    )


def add_evidence_appendix(flow: list, st: dict[str, ParagraphStyle]) -> None:
    rows_data = load_json("external_citation_ledger.json")
    flow.append(PageBreak())
    flow.append(para("Appendix A: External Citation Evidence Ledger", st["H2"]))
    flow.append(
        para(
            f"This appendix lists all {len(rows_data)} atomized external/reference candidates. Abstract summaries are condensed notes, not copied abstracts.",
            st["Body"],
        )
    )
    rows = [
        [
            para("ID", st["HeadSmall"]),
            para("Status", st["HeadSmall"]),
            para("Title / evidence note", st["HeadSmall"]),
            para("Source / URL", st["HeadSmall"]),
        ]
    ]
    for item in rows_data:
        note = f"{item['title']} ({item['year'] or 'n.d.'}) - {item['abstract_summary']}"
        source = item["url"] or item["doi"] or item["arxiv_id"] or item["audit_ids"]
        rows.append(
            [
                para(item["candidate_id"], st["Small"]),
                para(f"{item['status']} / {item['evidence_level']}", st["Small"]),
                para(note, st["Small"]),
                para(source, st["Small"]),
            ]
        )
    table = Table(rows, colWidths=[0.68 * inch, 1.3 * inch, 3.65 * inch, 1.1 * inch], repeatRows=1)
    table.setStyle(table_style())
    flow.append(table)


def add_claim_matrix(flow: list, st: dict[str, ParagraphStyle]) -> None:
    text = (REVIEW / "claim_evidence_matrix.md").read_text()
    flow.append(PageBreak())
    flow.append(para("Appendix B: Claim Evidence Matrix", st["H2"]))
    rows = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        rows.append([para(cell.replace("<br>", "\n"), st["HeadSmall" if not rows else "Small"]) for cell in cells])
    table = Table(rows, colWidths=[1.6 * inch, 3.4 * inch, 1.75 * inch], repeatRows=1)
    table.setStyle(table_style())
    flow.append(table)


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#56606b"))
    canvas.drawString(0.72 * inch, 0.44 * inch, "External-citation literature review")
    canvas.drawRightString(7.75 * inch, 0.44 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf() -> None:
    st = styles()
    flow = markdown_flow(PAPER_MD.read_text(), st)
    add_figures(flow, st)
    add_claim_matrix(flow, st)
    add_evidence_appendix(flow, st)
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.65 * inch,
        title="External-Citation Literature Review",
    )
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(OUT_PDF)


if __name__ == "__main__":
    build_pdf()
