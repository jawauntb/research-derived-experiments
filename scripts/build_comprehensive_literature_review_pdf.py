from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

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
OUT = ROOT / "papers" / "comprehensive_literature_review"
PAPER_MD = OUT / "paper.md"
OUT_PDF = OUT / "Comprehensive_Literature_Review_and_Research_Synthesis.pdf"
TMP = ROOT / "tmp" / "comprehensive_literature_review"
AUDIT = ROOT / "papers" / "exhaustive_literature_audit"
EXTERNAL = ROOT / "papers" / "external_citation_review"


UNREAD_STATUSES = {
    "unresolved_external_reference",
    "manual_foundational_reference",
    "resolved_metadata_only",
}


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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=19.5,
            leading=23.5,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1e2d3d"),
            spaceAfter=12,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13.4,
            leading=16.2,
            textColor=colors.HexColor("#273b59"),
            spaceBefore=8,
            spaceAfter=5,
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.8,
            leading=13.1,
            textColor=colors.HexColor("#35506b"),
            spaceBefore=5,
            spaceAfter=3,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=11.45,
            spaceAfter=3.5,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.45,
            leading=10.8,
            leftIndent=13,
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=6.15,
            leading=7.35,
        ),
        "HeadSmall": ParagraphStyle(
            "HeadSmall",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=6.35,
            leading=7.5,
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
            flow.append(Spacer(1, 0.03 * inch))
            lines.clear()

    def flush_list() -> None:
        if not list_items:
            return
        for item in list_items:
            prefix = "" if re.match(r"^\d+\. ", item) else "- "
            flow.append(para(prefix + item, st["Bullet"]))
        flow.append(Spacer(1, 0.035 * inch))
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_unread_register() -> list[dict[str, Any]]:
    rows = load_json(EXTERNAL / "external_citation_ledger.json")
    unread = [
        {
            "candidate_id": row["candidate_id"],
            "status": row["status"],
            "evidence_level": row["evidence_level"],
            "title": row["title"],
            "year": row["year"],
            "topics": row["topics"],
            "reason": row["limitations"],
            "source_rows": row["audit_ids"],
            "source_files": row["source_files"],
            "raw_reference": row["raw_reference"],
        }
        for row in rows
        if row["status"] in UNREAD_STATUSES
    ]
    unread = sorted(unread, key=lambda row: (row["status"], row["title"].lower(), row["candidate_id"]))
    write_csv(OUT / "unread_sources.csv", unread)

    lines = [
        "# Unread and Unresolved Source Register",
        "",
        "These rows were not treated as full external evidence in the canonical review. They require full-text reading, exact bibliographic repair, or both.",
        "",
    ]
    for row in unread:
        lines.extend(
            [
                f"## {row['title']} ({row['year'] or 'n.d.'})",
                "",
                f"- Candidate ID: {row['candidate_id']}",
                f"- Status: {row['status']}",
                f"- Evidence level: {row['evidence_level']}",
                f"- Topics: {row['topics']}",
                f"- Why unread/unresolved: {row['reason']}",
                f"- Source rows: {row['source_rows']}",
                f"- Raw reference: {row['raw_reference']}",
                "",
            ]
        )
    (OUT / "unread_sources.md").write_text("\n".join(lines) + "\n")
    return unread


def make_figures() -> list[tuple[str, Path]]:
    TMP.mkdir(parents=True, exist_ok=True)
    audit = load_json(AUDIT / "audit_summary.json")
    external = load_json(EXTERNAL / "enrichment_summary.json")

    figures: list[tuple[str, Path]] = []

    fig1 = TMP / "evidence_stack.png"
    labels = ["paper sources", "local PDFs", "citation rows", "external candidates", "abstract resolved", "unread/unresolved"]
    vals = [
        audit["paper_source_count"],
        audit["tracked_pdf_count"],
        audit["reference_count_unique"],
        external["candidate_count"],
        external["status_counts"]["resolved_with_abstract"],
        sum(
            external["status_counts"][status]
            for status in ["manual_foundational_reference", "resolved_metadata_only", "unresolved_external_reference"]
        ),
    ]
    plt.figure(figsize=(9.2, 4.7), dpi=180)
    plt.barh(labels, vals, color=["#2a9d8f", "#3a86ff", "#8338ec", "#ffbe0b", "#7fb069", "#ef8354"], edgecolor="#222")
    plt.title("Evidence stack for the canonical review")
    plt.xlabel("count")
    plt.tight_layout()
    plt.savefig(fig1)
    plt.close()
    figures.append(("Figure 1. Evidence stack: local corpus, external candidates, and unresolved source debt.", fig1))

    fig2 = TMP / "topic_coverage.png"
    topic_counts = external["topic_counts"]
    labels = list(topic_counts.keys())
    vals = [topic_counts[label] for label in labels]
    plt.figure(figsize=(9.2, 4.7), dpi=180)
    plt.barh(labels, vals, color="#4d9de0", edgecolor="#222")
    plt.title("External citation topic coverage")
    plt.xlabel("candidate count")
    plt.tight_layout()
    plt.savefig(fig2)
    plt.close()
    figures.append(("Figure 2. Topic coverage across atomized outside citation candidates.", fig2))

    fig3 = TMP / "research_program_stack.png"
    labels = [
        "proxy resistance",
        "OOD invariance",
        "boundary probes",
        "causal intervention",
        "uncertainty value",
        "viability constraints",
    ]
    vals = [6, 5, 4, 3, 2, 1]
    plt.figure(figsize=(8.8, 4.8), dpi=180)
    plt.barh(labels, vals, color=["#264653", "#2a9d8f", "#8ab17d", "#e9c46a", "#f4a261", "#e76f51"], edgecolor="#222")
    plt.title("Conceptual stack for minimal agency experiments")
    plt.xticks([])
    plt.tight_layout()
    plt.savefig(fig3)
    plt.close()
    figures.append(("Figure 3. Research program stack from viability to proxy-resistant benchmark design.", fig3))
    return figures


def add_figures(flow: list, st: dict[str, ParagraphStyle]) -> None:
    flow.append(PageBreak())
    flow.append(para("Visual Summary", st["H2"]))
    for caption, fig in make_figures():
        flow.append(para(caption, st["H3"]))
        flow.append(Image(str(fig), width=6.45 * inch, height=3.29 * inch))
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


def add_claim_matrix(flow: list, st: dict[str, ParagraphStyle]) -> None:
    text = (EXTERNAL / "claim_evidence_matrix.md").read_text()
    flow.append(PageBreak())
    flow.append(para("Appendix A: Claim Evidence Matrix", st["H2"]))
    rows = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip().replace("<br>", "\n") for cell in line.strip("|").split("|")]
        rows.append([para(cell, st["HeadSmall" if not rows else "Small"]) for cell in cells])
    table = Table(rows, colWidths=[1.45 * inch, 3.65 * inch, 1.65 * inch], repeatRows=1)
    table.setStyle(table_style())
    flow.append(table)


def add_unread_appendix(flow: list, st: dict[str, ParagraphStyle], unread: list[dict[str, Any]]) -> None:
    flow.append(PageBreak())
    flow.append(para("Appendix B: Unread and Unresolved Source Register", st["H2"]))
    flow.append(
        para(
            f"This appendix lists {len(unread)} sources or source fragments not treated as full external evidence. They are retained as required reading or bibliography-repair debt.",
            st["Body"],
        )
    )
    rows = [
        [
            para("ID", st["HeadSmall"]),
            para("Status", st["HeadSmall"]),
            para("Source or fragment", st["HeadSmall"]),
            para("Reason / source rows", st["HeadSmall"]),
        ]
    ]
    for row in unread:
        reason = f"{row['reason']} Source rows: {row['source_rows']}"
        rows.append(
            [
                para(row["candidate_id"], st["Small"]),
                para(row["status"], st["Small"]),
                para(f"{row['title']} ({row['year'] or 'n.d.'}) - {row['raw_reference']}", st["Small"]),
                para(reason, st["Small"]),
            ]
        )
    table = Table(rows, colWidths=[0.65 * inch, 1.25 * inch, 3.65 * inch, 1.2 * inch], repeatRows=1)
    table.setStyle(table_style())
    flow.append(table)


def add_resolved_appendix(flow: list, st: dict[str, ParagraphStyle]) -> None:
    rows_data = [
        row
        for row in load_json(EXTERNAL / "external_citation_ledger.json")
        if row["status"] == "resolved_with_abstract"
    ]
    rows_data = sorted(rows_data, key=lambda row: (row["topics"], row["year"], row["title"]))
    flow.append(PageBreak())
    flow.append(para("Appendix C: Abstract-Resolved External Sources", st["H2"]))
    rows = [
        [
            para("Title", st["HeadSmall"]),
            para("Topics", st["HeadSmall"]),
            para("Evidence note", st["HeadSmall"]),
        ]
    ]
    for row in rows_data:
        rows.append(
            [
                para(f"{row['title']} ({row['year'] or 'n.d.'})", st["Small"]),
                para(row["topics"].replace(";", ", "), st["Small"]),
                para(row["abstract_summary"], st["Small"]),
            ]
        )
    table = Table(rows, colWidths=[2.05 * inch, 1.55 * inch, 3.15 * inch], repeatRows=1)
    table.setStyle(table_style())
    flow.append(table)


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#56606b"))
    canvas.drawString(0.72 * inch, 0.44 * inch, "Comprehensive literature review and research synthesis")
    canvas.drawRightString(7.75 * inch, 0.44 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    unread = build_unread_register()
    st = styles()
    flow = markdown_flow(PAPER_MD.read_text(), st)
    add_figures(flow, st)
    add_claim_matrix(flow, st)
    add_unread_appendix(flow, st, unread)
    add_resolved_appendix(flow, st)
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.58 * inch,
        bottomMargin=0.65 * inch,
        title="Comprehensive Literature Review and Research Synthesis",
    )
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(OUT_PDF)


if __name__ == "__main__":
    build_pdf()
