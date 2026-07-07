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
AUDIT = ROOT / "papers" / "exhaustive_literature_audit"
PAPER_MD = AUDIT / "paper.md"
OUT_PDF = AUDIT / "paper.pdf"
TMP = ROOT / "tmp" / "exhaustive_lit_audit"


def sanitize(text: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "\u0394": "Delta",
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
    return json.loads((AUDIT / name).read_text())


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=21, leading=25, alignment=TA_CENTER, textColor=colors.HexColor("#1f2933"), spaceAfter=12),
        "H2": ParagraphStyle("H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=14.2, leading=17, textColor=colors.HexColor("#273043"), spaceBefore=9, spaceAfter=5),
        "H3": ParagraphStyle("H3", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=11.2, leading=13.5, textColor=colors.HexColor("#324a5f"), spaceBefore=6, spaceAfter=3),
        "Body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.1, leading=11.8, spaceAfter=4),
        "Bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.7, leading=11.2, leftIndent=14),
        "Small": ParagraphStyle("Small", parent=base["BodyText"], fontName="Helvetica", fontSize=6.6, leading=7.8),
        "HeadSmall": ParagraphStyle("HeadSmall", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=6.8, leading=8.0, textColor=colors.white),
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
        elif line.startswith("> "):
            flush_para()
            flush_list()
            flow.append(para(line[2:].strip(), st["Body"]))
        else:
            lines.append(line)
    flush_para()
    flush_list()
    return flow


def make_figures() -> list[Path]:
    TMP.mkdir(parents=True, exist_ok=True)
    summary = load_json("audit_summary.json")
    fig1 = TMP / "audit_counts.png"
    fig2 = TMP / "reference_kinds.png"
    fig3 = TMP / "pdf_tags.png"

    paper_counts = summary["paper_counts"]
    labels = list(paper_counts.keys())
    vals = [paper_counts[label] for label in labels]
    plt.figure(figsize=(9.2, 4.8), dpi=180)
    plt.barh(labels, vals, color="#4d9de0", edgecolor="#222222")
    plt.title("Tracked paper-source coverage")
    plt.xlabel("count")
    plt.tight_layout()
    plt.savefig(fig1)
    plt.close()

    ref_counts = summary["reference_counts"]
    labels = list(ref_counts.keys())
    vals = [ref_counts[label] for label in labels]
    plt.figure(figsize=(9.2, 4.8), dpi=180)
    colors_ = ["#ef8354", "#7fb069", "#7768ae", "#f2c14e", "#e15554"]
    plt.barh(labels, vals, color=colors_[: len(labels)], edgecolor="#222222")
    plt.title("Citation/reference item classes")
    plt.xlabel("unique extracted items")
    plt.tight_layout()
    plt.savefig(fig2)
    plt.close()

    tag_counts = summary["pdf_keyword_counts"]
    labels = list(tag_counts.keys())
    vals = [tag_counts[label] for label in labels]
    plt.figure(figsize=(9.2, 4.8), dpi=180)
    plt.barh(labels, vals, color="#3bb273", edgecolor="#222222")
    plt.title("Tracked PDF topic tags from full-page extraction")
    plt.xlabel("PDF count tagged")
    plt.tight_layout()
    plt.savefig(fig3)
    plt.close()
    return [fig1, fig2, fig3]


def add_figures(flow: list, st: dict[str, ParagraphStyle]) -> None:
    figs = make_figures()
    flow.append(PageBreak())
    flow.append(para("Figures", st["H2"]))
    for idx, fig in enumerate(figs, start=1):
        flow.append(para(f"Figure {idx}. Audit coverage chart.", st["H3"]))
        flow.append(Image(str(fig), width=6.5 * inch, height=3.39 * inch))
        flow.append(Spacer(1, 0.08 * inch))


def table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#273043")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bcc6d0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]
    )


def add_citation_appendix(flow: list, st: dict[str, ParagraphStyle]) -> None:
    refs = load_json("citation_ledger.json")
    flow.append(PageBreak())
    flow.append(para("Appendix A: Every Extracted Citation/Reference Item", st["H2"]))
    flow.append(para(f"This appendix lists all {len(refs)} deduplicated citation/reference items extracted from tracked paper sources. Ambiguous rows are intentionally preserved rather than hidden.", st["Body"]))
    rows = [[para("ID", st["HeadSmall"]), para("Kind/status", st["HeadSmall"]), para("Citation or reference item", st["HeadSmall"]), para("Source files", st["HeadSmall"])]]
    for ref in refs:
        status = ref["kind"].replace("_", " ")
        rows.append(
            [
                para(ref["id"], st["Small"]),
                para(status, st["Small"]),
                para(ref["raw"], st["Small"]),
                para(ref["source_files"].replace(";", "; "), st["Small"]),
            ]
        )
    table = Table(rows, colWidths=[0.42 * inch, 1.42 * inch, 3.35 * inch, 1.55 * inch], repeatRows=1)
    table.setStyle(table_style())
    flow.append(table)


def add_pdf_appendix(flow: list, st: dict[str, ParagraphStyle]) -> None:
    pdfs = load_json("pdf_review_ledger.json")
    flow.append(PageBreak())
    flow.append(para("Appendix B: Every Tracked PDF Reviewed", st["H2"]))
    flow.append(para(f"This appendix lists all {len(pdfs)} tracked PDFs reviewed by full-page text extraction.", st["Body"]))
    rows = [[para("PDF", st["HeadSmall"]), para("Pages", st["HeadSmall"]), para("Parsed title", st["HeadSmall"]), para("Tags and summary", st["HeadSmall"])]]
    for pdf in pdfs:
        summary = f"Tags: {pdf['keywords']}. Summary: {pdf['summary'][:420]}"
        rows.append(
            [
                para(pdf["file"], st["Small"]),
                para(pdf["pages"], st["Small"]),
                para(pdf["title"], st["Small"]),
                para(summary, st["Small"]),
            ]
        )
    table = Table(rows, colWidths=[1.85 * inch, 0.38 * inch, 1.8 * inch, 2.7 * inch], repeatRows=1)
    table.setStyle(table_style())
    flow.append(table)


def add_source_appendix(flow: list, st: dict[str, ParagraphStyle]) -> None:
    sources = load_json("paper_source_ledger.json")
    flow.append(PageBreak())
    flow.append(para("Appendix C: Tracked Paper Source Inventory", st["H2"]))
    rows = [[para("File", st["HeadSmall"]), para("Kind", st["HeadSmall"]), para("Title", st["HeadSmall"])]]
    for source in sources:
        rows.append([para(source["file"], st["Small"]), para(source["kind"], st["Small"]), para(source["title"], st["Small"])])
    table = Table(rows, colWidths=[2.25 * inch, 1.15 * inch, 3.35 * inch], repeatRows=1)
    table.setStyle(table_style())
    flow.append(table)


def build() -> None:
    st = styles()
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.58 * inch,
        bottomMargin=0.58 * inch,
        title="Exhaustive Literature and PDF Audit",
        author="Research Derived Experiments",
    )
    flow = markdown_flow(PAPER_MD.read_text(), st)
    add_figures(flow, st)
    add_citation_appendix(flow, st)
    add_pdf_appendix(flow, st)
    add_source_appendix(flow, st)

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#697586"))
        canvas.drawString(0.55 * inch, 0.32 * inch, "Exhaustive Literature and PDF Audit")
        canvas.drawRightString(8.0 * inch, 0.32 * inch, str(document.page))
        canvas.restoreState()

    doc.build(flow, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
