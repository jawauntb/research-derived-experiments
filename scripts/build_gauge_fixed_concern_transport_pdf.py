#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the gauge-fixed concern transport paper to PDF.

Run:
    python scripts/build_gauge_fixed_concern_transport_pdf.py

Outputs:
    papers/gauge_fixed_concern_transport/paper.pdf
    papers/pdf/gauge_fixed_concern_transport.pdf
    /Users/jawaun/Metaphysics of Intelligence/Gauge_Fixed_Concern_Transport_2026_07_07.pdf
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image as PILImage  # noqa: E402
from reportlab import rl_config  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
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
PAPER_DIR = ROOT / "papers" / "gauge_fixed_concern_transport"
PAPER_MD = PAPER_DIR / "paper.md"
OUT_PDF = PAPER_DIR / "paper.pdf"
COPY_PDF = ROOT / "papers" / "pdf" / "gauge_fixed_concern_transport.pdf"
DEPOSIT_PDF = (
    Path("/Users/jawaun/Metaphysics of Intelligence")
    / "Gauge_Fixed_Concern_Transport_2026_07_07.pdf"
)
FIG_DIR = PAPER_DIR / "figures"
rl_config.invariant = True


def register_fonts() -> tuple[str, str, str, str]:
    base = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    fonts = {
        "GFCBody": "DejaVuSerif.ttf",
        "GFCBody-Bold": "DejaVuSerif-Bold.ttf",
        "GFCBody-Italic": "DejaVuSerif-Italic.ttf",
        "GFCMono": "DejaVuSansMono.ttf",
    }
    try:
        for name, filename in fonts.items():
            pdfmetrics.registerFont(TTFont(name, str(base / filename)))
        pdfmetrics.registerFontFamily(
            "GFCBody",
            normal="GFCBody",
            bold="GFCBody-Bold",
            italic="GFCBody-Italic",
            boldItalic="GFCBody-Bold",
        )
        return "GFCBody", "GFCBody-Bold", "GFCBody-Italic", "GFCMono"
    except Exception:
        return "Times-Roman", "Times-Bold", "Times-Italic", "Courier"


F_BODY, F_BOLD, F_ITAL, F_MONO = register_fonts()


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    ink = colors.HexColor("#111827")
    muted = colors.HexColor("#4b5563")
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName=F_BOLD,
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=ink,
            spaceAfter=8,
        ),
        "Meta": ParagraphStyle(
            "Meta",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=9.8,
            leading=12,
            alignment=TA_CENTER,
            textColor=muted,
            spaceAfter=2,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName=F_BOLD,
            fontSize=13.2,
            leading=16,
            textColor=ink,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName=F_BOLD,
            fontSize=11.2,
            leading=13.4,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=7,
            spaceAfter=3,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=9.35,
            leading=12.4,
            alignment=TA_JUSTIFY,
            textColor=ink,
            spaceAfter=4.4,
        ),
        "Quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName=F_ITAL,
            fontSize=9.1,
            leading=12,
            leftIndent=18,
            rightIndent=14,
            textColor=colors.HexColor("#374151"),
            spaceBefore=2,
            spaceAfter=5,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=9.05,
            leading=11.6,
            leftIndent=16,
            firstLineIndent=-10,
            textColor=ink,
            spaceAfter=2.5,
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName=F_MONO,
            fontSize=7.8,
            leading=9.6,
            leftIndent=9,
            rightIndent=9,
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
            fontName=F_ITAL,
            fontSize=8.25,
            leading=10.2,
            alignment=TA_CENTER,
            textColor=muted,
            spaceBefore=2,
            spaceAfter=7,
        ),
        "Ref": ParagraphStyle(
            "Ref",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=8.1,
            leading=10.1,
            alignment=TA_LEFT,
            leftIndent=18,
            firstLineIndent=-18,
            spaceAfter=2.2,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=7.6,
            leading=9.2,
            textColor=ink,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontName=F_BOLD,
            fontSize=7.7,
            leading=9.2,
            textColor=colors.HexColor("#1f4f82"),
        ),
    }


def inline_markup(text: str) -> str:
    safe = html.escape(text)
    safe = re.sub(r"`([^`]+)`", rf"<font name='{F_MONO}'>\1</font>", safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", safe)
    return safe


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(inline_markup(text), style)


def setup_plot() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 220,
            "savefig.dpi": 220,
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#374151",
            "axes.linewidth": 0.8,
            "axes.grid": False,
            "xtick.color": "#374151",
            "ytick.color": "#374151",
        }
    )


def save(fig: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def figure_pipeline() -> Path:
    setup_plot()
    out = FIG_DIR / "fig1_transport_pipeline.png"
    fig, ax = plt.subplots(figsize=(7.2, 2.85))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    nodes = [
        ("local\nh", 0.08, "#dbeafe"),
        ("concern\nkappa", 0.25, "#dcfce7"),
        ("transport\ngamma", 0.43, "#ede9fe"),
        ("gauge fix\nI", 0.62, "#fef3c7"),
        ("commit\ns", 0.80, "#fee2e2"),
        ("load\nW x CE", 0.94, "#e0f2fe"),
    ]
    for label, x, color in nodes:
        ax.text(
            x,
            0.63,
            label,
            ha="center",
            va="center",
            fontsize=9.2,
            weight="bold",
            bbox={
                "boxstyle": "round,pad=0.38",
                "facecolor": color,
                "edgecolor": "#334155",
                "linewidth": 0.9,
            },
        )
    for (_, x1, _), (_, x2, _) in zip(nodes[:-1], nodes[1:], strict=True):
        ax.annotate(
            "",
            xy=(x2 - 0.055, 0.63),
            xytext=(x1 + 0.055, 0.63),
            arrowprops={"arrowstyle": "->", "lw": 1.35, "color": "#334155"},
        )
    failures = [
        ("unweighted", 0.17),
        ("lost in transport", 0.35),
        ("gauge-equivalent", 0.55),
        ("unglued", 0.70),
        ("no commitment effect", 0.87),
    ]
    for label, x in failures:
        ax.text(x, 0.22, label, ha="center", va="center", fontsize=8.3, color="#4b5563")
        ax.plot([x, x], [0.35, 0.29], color="#9ca3af", lw=1)
    ax.text(
        0.5,
        0.93,
        "A distinction matters when it survives to the surface where future control is committed",
        ha="center",
        va="center",
        fontsize=10.5,
        weight="bold",
        color="#111827",
    )
    return save(fig, out)


def figure_ladder() -> Path:
    setup_plot()
    out = FIG_DIR / "fig2_theorem_ladder.png"
    fig, ax = plt.subplots(figsize=(7.0, 3.15))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    steps = [
        ("1", "Uniform weakness", "|Z_h|"),
        ("2", "Concern weights", "sum kappa"),
        ("3", "Group blocks", "OOD transforms"),
        ("4", "Transport loss", "telescoping bound"),
        ("5", "Gauge fixing", "separate orbits"),
        ("6", "Commitment", "causal effect"),
    ]
    ys = [0.86, 0.72, 0.58, 0.44, 0.30, 0.16]
    colors_ = ["#dbeafe", "#dcfce7", "#ede9fe", "#fef3c7", "#fee2e2", "#e0f2fe"]
    for (num, title, note), y, color in zip(steps, ys, colors_, strict=True):
        ax.text(
            0.06,
            y,
            num,
            ha="center",
            va="center",
            fontsize=9,
            weight="bold",
            bbox={"boxstyle": "circle,pad=0.25", "facecolor": color, "edgecolor": "#334155"},
        )
        ax.text(0.13, y + 0.025, title, ha="left", va="center", fontsize=9.4, weight="bold")
        ax.text(0.13, y - 0.030, note, ha="left", va="center", fontsize=8.3, color="#4b5563")
        if y != ys[-1]:
            ax.annotate("", xy=(0.06, y - 0.085), xytext=(0.06, y - 0.035),
                        arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#64748b"})
    ax.text(
        0.62,
        0.55,
        "Bridge bound\n\nLoad_gamma(h) >=\n(alpha - delta) * epsilon\n\nwhere alpha is initial concern,\ndelta is transport loss,\nand epsilon is gauge-fixed\ncommitment effect.",
        ha="center",
        va="center",
        fontsize=10,
        bbox={
            "boxstyle": "round,pad=0.55",
            "facecolor": "#f8fafc",
            "edgecolor": "#334155",
            "linewidth": 0.9,
        },
    )
    return save(fig, out)


def figure_matrix() -> Path:
    setup_plot()
    out = FIG_DIR / "fig3_applicability_matrix.png"
    rows = [
        "OOD ML",
        "causal reps",
        "mech interp",
        "neuro-control",
        "philosophy",
        "math",
        "agent safety",
    ]
    cols = ["concern", "transport", "gauge", "gluing", "commit"]
    data = [
        [3, 3, 2, 1, 3],
        [2, 3, 3, 2, 3],
        [2, 3, 3, 1, 3],
        [3, 3, 3, 2, 3],
        [3, 2, 2, 2, 2],
        [1, 3, 3, 3, 1],
        [3, 3, 3, 2, 3],
    ]
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    im = ax.imshow(data, cmap="YlGnBu", vmin=0, vmax=3)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, fontsize=8.3)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows, fontsize=8.3)
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            label = ["-", "low", "med", "high"][value]
            ax.text(j, i, label, ha="center", va="center", fontsize=7.6, color="#111827")
    ax.set_title("Where the bridge theorem adds an explicit proof obligation", fontsize=10.5, weight="bold")
    fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03, label="framework pressure")
    return save(fig, out)


def figure_failure_taxonomy() -> Path:
    setup_plot()
    out = FIG_DIR / "fig4_failure_taxonomy.png"
    labels = [
        "average score only",
        "probe without intervention",
        "transport bottleneck",
        "gauge ambiguity",
        "local explanations fail to glue",
        "no commitment effect",
    ]
    values = [0.80, 0.72, 0.86, 0.91, 0.63, 0.95]
    colors_ = ["#9ca3af", "#60a5fa", "#a78bfa", "#f59e0b", "#34d399", "#ef4444"]
    fig, ax = plt.subplots(figsize=(6.6, 3.1))
    ax.barh(labels, values, color=colors_, height=0.66)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("risk that the claim is not load-bearing", fontsize=8.6)
    ax.set_title("Failure modes the framework turns into tests", fontsize=10.5, weight="bold")
    ax.tick_params(axis="y", labelsize=8.1)
    ax.tick_params(axis="x", labelsize=7.8)
    for i, value in enumerate(values):
        ax.text(value + 0.015, i, f"{value:.2f}", va="center", fontsize=7.5)
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.8)
    return save(fig, out)


def make_figures() -> list[Path]:
    return [
        figure_pipeline(),
        figure_ladder(),
        figure_matrix(),
        figure_failure_taxonomy(),
    ]


def flush_paragraph(lines: list[str], flow: list[Any], st: dict[str, ParagraphStyle]) -> None:
    if not lines:
        return
    text = " ".join(line.strip() for line in lines if line.strip())
    if text:
        flow.append(para(text, st["Body"]))
    lines.clear()


def flush_list(
    items: list[tuple[str, str]],
    flow: list[Any],
    st: dict[str, ParagraphStyle],
) -> None:
    if not items:
        return
    for marker, item in items:
        flow.append(para(f"{marker} {item}", st["Bullet"]))
    flow.append(Spacer(1, 2))
    items.clear()


def add_image(flow: list[Any], image_path: Path, caption: str, st: dict[str, ParagraphStyle]) -> None:
    if not image_path.exists():
        flow.append(para(f"[missing figure: {image_path}]", st["Caption"]))
        return
    width = 6.35 * inch
    with PILImage.open(image_path) as img:
        w, h = img.size
    height = width * h / w
    max_height = 4.8 * inch
    if height > max_height:
        scale = max_height / height
        width *= scale
        height = max_height
    flow.append(Spacer(1, 4))
    flow.append(Image(str(image_path), width=width, height=height))
    flow.append(Paragraph(inline_markup(caption), st["Caption"]))


def render_table(
    table_lines: list[str],
    flow: list[Any],
    st: dict[str, ParagraphStyle],
) -> None:
    rows: list[list[str]] = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return
    max_cols = max(len(row) for row in rows)
    data = []
    for i, row in enumerate(rows):
        style = st["TableHead"] if i == 0 else st["TableCell"]
        padded = row + [""] * (max_cols - len(row))
        data.append([Paragraph(inline_markup(cell), style) for cell in padded])
    table = Table(data, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), F_BODY, 7.7),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#334155")),
                ("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.HexColor("#334155")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    flow.append(Spacer(1, 3))
    flow.append(table)
    flow.append(Spacer(1, 5))


def markdown_to_flow(text: str, st: dict[str, ParagraphStyle]) -> list[Any]:
    flow: list[Any] = []
    para_lines: list[str] = []
    list_items: list[tuple[str, str]] = []
    code_lines: list[str] = []
    table_lines: list[str] = []
    in_code = False
    title_seen = False
    section = ""

    def flush_all() -> None:
        flush_paragraph(para_lines, flow, st)
        flush_list(list_items, flow, st)
        if table_lines:
            render_table(table_lines, flow, st)
            table_lines.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                flow.append(Preformatted("\n".join(code_lines), st["Code"]))
                code_lines.clear()
                in_code = False
            else:
                flush_all()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith("|"):
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            table_lines.append(line)
            continue
        if table_lines and not line.startswith("|"):
            render_table(table_lines, flow, st)
            table_lines.clear()
        if not line.strip():
            flush_all()
            continue
        if line.startswith("# "):
            flush_all()
            if title_seen:
                flow.append(PageBreak())
            title_seen = True
            section = line[2:].strip()
            flow.append(para(section, st["Title"]))
            continue
        if line.startswith("**Subtitle.**") or line.startswith("**Author.**") or line.startswith("**Date.**"):
            flush_all()
            flow.append(Paragraph(inline_markup(line), st["Meta"]))
            continue
        if line.startswith("## "):
            flush_all()
            section = line[3:].strip()
            flow.append(para(section, st["H2"]))
            continue
        if line.startswith("### "):
            flush_all()
            flow.append(para(line[4:].strip(), st["H3"]))
            continue
        image_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if image_match:
            flush_all()
            add_image(flow, PAPER_DIR / image_match.group(2), image_match.group(1), st)
            continue
        if line.startswith("> "):
            flush_all()
            flow.append(para(line[2:].strip(), st["Quote"]))
            continue
        numbered = re.match(r"^(\d+)\. (.*)", line)
        if numbered:
            flush_paragraph(para_lines, flow, st)
            if section == "References":
                flush_list(list_items, flow, st)
                flow.append(Paragraph(inline_markup(line), st["Ref"]))
            else:
                list_items.append((numbered.group(1) + ".", numbered.group(2).strip()))
            continue
        if line.startswith("- "):
            flush_paragraph(para_lines, flow, st)
            list_items.append(("-", line[2:].strip()))
            continue
        para_lines.append(line)

    flush_all()
    return flow


def build_pdf() -> Path:
    figures = make_figures()
    for figure in figures:
        if not figure.exists():
            raise FileNotFoundError(figure)

    md_text = PAPER_MD.read_text(encoding="utf-8")
    st = styles()
    flow = markdown_to_flow(md_text, st)
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.70 * inch,
        bottomMargin=0.70 * inch,
        title="Gauge-Fixed Transport of Concern",
        author="Jawaun Brown",
    )
    doc.build(flow)
    COPY_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT_PDF, COPY_PDF)
    DEPOSIT_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT_PDF, DEPOSIT_PDF)
    return OUT_PDF


def main() -> int:
    out = build_pdf()
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    print(f"Wrote {COPY_PDF} ({COPY_PDF.stat().st_size} bytes)")
    print(f"Wrote {DEPOSIT_PDF} ({DEPOSIT_PDF.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
