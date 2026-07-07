from __future__ import annotations

import re
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
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
PAPER_DIR = ROOT / "papers" / "comprehensive_literature_review"
PAPER_MD = PAPER_DIR / "paper.md"
TMP_DIR = ROOT / "tmp" / "lit_review_v2"
OUT_PDF = PAPER_DIR / "paper.pdf"


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
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("**", "").replace("*", "")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = text.replace("&", "&amp;")
    text = text.replace("<font name='Courier'>", "%%FONT%%").replace("</font>", "%%ENDFONT%%")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    return text.replace("%%FONT%%", "<font name='Courier'>").replace("%%ENDFONT%%", "</font>")


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(sanitize(text), style)


def source_records() -> list[dict[str, str]]:
    roots = ["papers", "docs", "notes", "references", "coherence-testbench", "formal"]
    records: list[dict[str, str]] = []
    for root_name in roots:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".md", ".tex", ".bib"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(errors="ignore")
            title = ""
            tex_title = re.search(r"\\title\{(.+?)\}\s*\\author", text, re.S)
            if tex_title:
                title = tex_title.group(1)
                title = re.sub(r"\\vspace\{[^}]+\}", "", title)
                title = title.replace("\\\\", " ")
                title = re.sub(r"\\[a-zA-Z]+\{([^}]+)\}", r"\1", title)
                title = re.sub(r"\s+", " ", title).strip()
            for line in text.splitlines()[:100]:
                if title:
                    break
                stripped = line.strip()
                if stripped.startswith("# "):
                    title = stripped[2:].strip()
                    break
                match = re.search(r"\\title\{(.+?)\}", stripped)
                if match:
                    title = match.group(1).strip()
                    break
            records.append({"file": rel, "title": title, "chars": str(len(text))})
    return records


def make_figures() -> list[Path]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    fig1 = TMP_DIR / "action_surface_stack.png"
    fig2 = TMP_DIR / "evidence_matrix.png"
    fig3 = TMP_DIR / "theorem_law_ladder.png"

    surfaces = [
        ("Viability / concern", "What matters"),
        ("Representation", "What is preserved"),
        ("Attribution", "Who or what caused it"),
        ("Inquiry", "When to ask again"),
        ("Planning", "How prediction selects action"),
        ("Memory", "What reaches future commitment"),
        ("OOD compatibility", "What survives shift"),
        ("Stress transduction", "How global constraint acts locally"),
    ]
    palette = ["#f2c14e", "#7fb069", "#4d9de0", "#e15554", "#7768ae", "#3bb273", "#ef8354", "#5d737e"]
    plt.figure(figsize=(10, 5.8), dpi=180)
    ax = plt.gca()
    for idx, (name, desc) in enumerate(surfaces):
        y = len(surfaces) - idx - 1
        ax.barh(y, 0.82, left=0.09, height=0.62, color=palette[idx], edgecolor="#222222")
        ax.text(0.12, y + 0.08, name, fontsize=10, weight="bold", va="center")
        ax.text(0.48, y + 0.08, desc, fontsize=9.2, va="center")
        if idx < len(surfaces) - 1:
            ax.annotate("", xy=(0.5, y - 0.36), xytext=(0.5, y - 0.02), arrowprops={"arrowstyle": "->", "lw": 1.0})
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.7, len(surfaces) - 0.25)
    ax.set_title("Action-surface stack: where a variable becomes agent-relevant")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(fig1)
    plt.close()

    fields = ["ML", "Neuro", "Phil/Bio", "Math", "Internal"]
    laws = ["Compression", "Geometry", "Intervention", "Inquiry", "Memory", "OOD", "Stress"]
    vals = [
        [3, 3, 3, 2, 2, 3, 1],
        [2, 3, 3, 3, 2, 1, 2],
        [2, 2, 1, 2, 2, 1, 3],
        [3, 3, 2, 1, 2, 3, 1],
        [3, 3, 3, 3, 3, 3, 3],
    ]
    plt.figure(figsize=(9.2, 4.8), dpi=180)
    ax = plt.gca()
    im = ax.imshow(vals, cmap="YlGnBu", vmin=0, vmax=3)
    ax.set_xticks(range(len(laws)), laws, rotation=30, ha="right")
    ax.set_yticks(range(len(fields)), fields)
    for i, row in enumerate(vals):
        for j, val in enumerate(row):
            ax.text(j, i, str(val), ha="center", va="center", color="#111111", weight="bold")
    ax.set_title("Evidence density by field and invariant (0-3 qualitative audit)")
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("density")
    plt.tight_layout()
    plt.savefig(fig2)
    plt.close()

    rows = [
        ("Established theorem", "No-free-lunch, non-identifiability, equivariance, rate-distortion"),
        ("Empirical law", "Reafference, re-engagement, commitment memory, compatibility selection"),
        ("Formal conjecture", "Action-surface sufficiency and anti-proxy benchmark standards"),
    ]
    plt.figure(figsize=(10, 3.8), dpi=180)
    ax = plt.gca()
    for idx, (level, example) in enumerate(rows):
        y = 2 - idx
        ax.scatter([0.12], [y], s=1800, color=["#273043", "#4d9de0", "#f2c14e"][idx], edgecolor="#222222")
        ax.text(0.12, y, str(idx + 1), color="white" if idx < 2 else "#111111", ha="center", va="center", weight="bold")
        ax.text(0.23, y + 0.10, level, fontsize=11, weight="bold", va="center")
        ax.text(0.23, y - 0.12, "\n".join(textwrap.wrap(example, 72)), fontsize=9.2, va="center")
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.55, 2.55)
    ax.set_title("Do not collapse theorem, law, and conjecture")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(fig3)
    plt.close()
    return [fig1, fig2, fig3]


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=22, leading=27, alignment=TA_CENTER, textColor=colors.HexColor("#1f2933"), spaceAfter=10),
        "Subtitle": ParagraphStyle("Subtitle", parent=base["Title"], fontName="Helvetica", fontSize=14, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#405066"), spaceAfter=12),
        "H2": ParagraphStyle("H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=14.5, leading=17.5, textColor=colors.HexColor("#273043"), spaceBefore=10, spaceAfter=5),
        "H3": ParagraphStyle("H3", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.HexColor("#324a5f"), spaceBefore=7, spaceAfter=3),
        "Body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.3, leading=12.2, spaceAfter=4),
        "Bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=8.9, leading=11.6, leftIndent=14),
        "Quote": ParagraphStyle("Quote", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=10.0, leading=13.4, leftIndent=0.25 * inch, rightIndent=0.25 * inch, textColor=colors.HexColor("#38434f")),
        "Small": ParagraphStyle("Small", parent=base["BodyText"], fontName="Helvetica", fontSize=7.4, leading=9.0),
        "HeadSmall": ParagraphStyle("HeadSmall", parent=base["BodyText"], fontName="Helvetica-Bold", fontSize=7.7, leading=9.2, textColor=colors.white),
    }


def markdown_flow(text: str, st: dict[str, ParagraphStyle]) -> list:
    flow: list = []
    list_items: list[str] = []
    para_lines: list[str] = []

    def flush_para() -> None:
        if para_lines:
            flow.append(para(" ".join(para_lines), st["Body"]))
            flow.append(Spacer(1, 0.04 * inch))
            para_lines.clear()

    def flush_list() -> None:
        if not list_items:
            return
        for item in list_items:
            prefix = "" if re.match(r"^\d+\. ", item) else "- "
            flow.append(para(f"{prefix}{item}", st["Bullet"]))
        flow.append(Spacer(1, 0.05 * inch))
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
            flow.append(para(line[2:].strip(), st["Quote"]))
        else:
            para_lines.append(line)
    flush_para()
    flush_list()
    return flow


def add_appendix(flow: list, st: dict[str, ParagraphStyle]) -> None:
    records = source_records()
    primary = [
        r
        for r in records
        if r["file"].startswith("papers/")
        and (r["file"].endswith("paper.md") or r["file"].endswith("paper.tex"))
        and "comprehensive_literature_review" not in r["file"]
    ]
    flow.append(PageBreak())
    flow.append(para("Appendix A: Primary Paper Coverage", st["H2"]))
    flow.append(para(f"The audit found {len(records)} repository text sources. The table below lists the primary paper files covered by the synthesis.", st["Body"]))
    rows = [[para("File", st["HeadSmall"]), para("Parsed title", st["HeadSmall"])]]
    for r in primary:
        title = r.get("title") or "(title not parsed)"
        rows.append([para(r["file"], st["Small"]), para(title, st["Small"])])
    table = Table(rows, colWidths=[2.35 * inch, 4.35 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#273043")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bcc6d0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    flow.append(table)


def build() -> None:
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    figs = make_figures()
    st = styles()
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title="From Concern to Action Surfaces",
        author="Research Derived Experiments",
    )
    flow = markdown_flow(PAPER_MD.read_text(), st)
    flow.append(PageBreak())
    flow.append(para("Figures", st["H2"]))
    flow.append(KeepTogether([para("Figure 1. Action-surface stack.", st["H3"]), Image(str(figs[0]), width=6.5 * inch, height=3.77 * inch)]))
    flow.append(Spacer(1, 0.1 * inch))
    flow.append(KeepTogether([para("Figure 2. Cross-field invariant density.", st["H3"]), Image(str(figs[1]), width=6.4 * inch, height=3.34 * inch)]))
    flow.append(PageBreak())
    flow.append(KeepTogether([para("Figure 3. Theorem/law/conjecture discipline.", st["H3"]), Image(str(figs[2]), width=6.5 * inch, height=2.47 * inch)]))
    add_appendix(flow, st)

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#697586"))
        canvas.drawString(0.65 * inch, 0.35 * inch, "From Concern to Action Surfaces")
        canvas.drawRightString(7.85 * inch, 0.35 * inch, str(document.page))
        canvas.restoreState()

    doc.build(flow, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
