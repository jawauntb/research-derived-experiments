#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the Concern-Gated Retrieval Wave 1a (E2a) report to PDF.

Run:
    python scripts/build_cogr_wave1a_pdf.py

Inputs (produced upstream by report-draft and report-figures):
    papers/concern_gated_retrieval_e2a/paper.md
    papers/concern_gated_retrieval_e2a/figures/*.png  (dark-mode figures)

Outputs:
    papers/concern_gated_retrieval_e2a/paper.pdf
    papers/pdf/concern_gated_retrieval_e2a.pdf
    /Users/jawaun/Metaphysics of Intelligence/Concern_Gated_Retrieval_E2a_2026_07_24.pdf
        (only if the archive parent directory already exists; do NOT create it).

Follows the pattern in ``scripts/build_cogr_wave0_pdf.py``: a deterministic
ReportLab build with a monospace body font (DejaVu Sans Mono when a
matplotlib TTF is available, otherwise ReportLab's built-in Courier),
JUSTIFY-set body paragraphs, and image references embedded from the
markdown-side ``![...](...)`` links. The figures themselves come from the
Wave 1a report-figures step; this script does not regenerate them and does
not require any specific naming convention beyond what paper.md references.

Wave 1a (COGR-E2a) is a SCREEN, not a promotion. It can KILL the online
concern update rule; it cannot by itself establish learned geometry or L2
credit. Those live in Wave 1b (E2b). The claim boundary is documented in
``docs/concern_gated_retrieval_research_program.md`` and
``experiments/concern_gated_retrieval_e2/wave1a/PREREGISTRATION.md``.
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
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
PAPER_DIR = ROOT / "papers" / "concern_gated_retrieval_e2a"
PAPER_MD = PAPER_DIR / "paper.md"
OUT_PDF = PAPER_DIR / "paper.pdf"
COPY_PDF = ROOT / "papers" / "pdf" / "concern_gated_retrieval_e2a.pdf"
DEPOSIT_PDF = (
    Path("/Users/jawaun/Metaphysics of Intelligence")
    / "Concern_Gated_Retrieval_E2a_2026_07_24.pdf"
)
FIG_DIR = PAPER_DIR / "figures"

# Deterministic PDF output for reproducibility.
rl_config.invariant = True


def register_fonts() -> tuple[str, str, str, str]:
    """Register a monospace-first font family.

    The Wave 1a report body is set in a monospace face so code, receipts, and
    prose share a single visual clock. We prefer DejaVu Sans Mono when the
    matplotlib TTF ships with the environment; otherwise we fall back to
    ReportLab's built-in Courier so the build never fails on font resolution.
    Returns ``(body, bold, italic, mono)``.
    """
    base = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    fonts = {
        "CGRW1aMonoBody": "DejaVuSansMono.ttf",
        "CGRW1aMonoBody-Bold": "DejaVuSansMono-Bold.ttf",
        "CGRW1aMonoBody-Italic": "DejaVuSansMono-Oblique.ttf",
        "CGRW1aMono": "DejaVuSansMono.ttf",
    }
    try:
        for name, filename in fonts.items():
            pdfmetrics.registerFont(TTFont(name, str(base / filename)))
        pdfmetrics.registerFontFamily(
            "CGRW1aMonoBody",
            normal="CGRW1aMonoBody",
            bold="CGRW1aMonoBody-Bold",
            italic="CGRW1aMonoBody-Italic",
            boldItalic="CGRW1aMonoBody-Bold",
        )
        return (
            "CGRW1aMonoBody",
            "CGRW1aMonoBody-Bold",
            "CGRW1aMonoBody-Italic",
            "CGRW1aMono",
        )
    except Exception:
        # ReportLab built-in Courier family is always available.
        return "Courier", "Courier-Bold", "Courier-Oblique", "Courier"


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
            fontSize=17,
            leading=21,
            alignment=TA_CENTER,
            textColor=ink,
            spaceAfter=8,
        ),
        "Meta": ParagraphStyle(
            "Meta",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=9.2,
            leading=11.6,
            alignment=TA_CENTER,
            textColor=muted,
            spaceAfter=2,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName=F_BOLD,
            fontSize=12.8,
            leading=15.4,
            textColor=ink,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName=F_BOLD,
            fontSize=11.0,
            leading=13.2,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=7,
            spaceAfter=3,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=8.8,
            leading=11.7,
            alignment=TA_JUSTIFY,
            textColor=ink,
            spaceAfter=4.4,
        ),
        "Quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName=F_ITAL,
            fontSize=8.6,
            leading=11.4,
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
            fontSize=8.55,
            leading=11.0,
            leftIndent=16,
            firstLineIndent=-10,
            textColor=ink,
            spaceAfter=2.5,
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName=F_MONO,
            fontSize=7.4,
            leading=9.2,
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
            fontSize=8.1,
            leading=10.0,
            alignment=TA_CENTER,
            textColor=muted,
            spaceBefore=2,
            spaceAfter=7,
        ),
        "Ref": ParagraphStyle(
            "Ref",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=7.9,
            leading=9.9,
            alignment=TA_LEFT,
            leftIndent=18,
            firstLineIndent=-18,
            spaceAfter=2.2,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName=F_BODY,
            fontSize=7.4,
            leading=9.0,
            textColor=ink,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontName=F_BOLD,
            fontSize=7.5,
            leading=9.0,
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


def _resolve_image(image_ref: str) -> Path:
    """Resolve a markdown image reference against the paper directory.

    Absolute paths and paths already anchored inside ``PAPER_DIR`` are used
    as-is; anything else is treated as relative to ``PAPER_DIR``. If the
    literal path does not exist, look for a same-``figN``-prefixed
    ``*_dark.png`` variant in ``FIG_DIR`` -- this lets a paper.md written
    against a generic name like ``figures/fig3.png`` still embed the actual
    ``figures/fig3_family_matrix_dark.png`` the report-figures step produced.
    """
    candidate = Path(image_ref)
    if not candidate.is_absolute():
        candidate = PAPER_DIR / candidate
    if candidate.exists():
        return candidate
    # Only auto-resolve when the referenced stem starts with "fig<digit>",
    # matching the Wave 1a figure-naming convention (inherited from Wave 0).
    stem = candidate.stem
    prefix_match = re.match(r"^(fig\d+)", stem)
    if prefix_match and FIG_DIR.is_dir():
        prefix = prefix_match.group(1) + "_"
        for match in sorted(FIG_DIR.glob(f"{prefix}*_dark.png")):
            return match
    return candidate


def _figure_embed_line(fig_path: Path, alt: str) -> str:
    """Format a markdown image embed relative to ``PAPER_DIR``."""
    try:
        rel = fig_path.relative_to(PAPER_DIR).as_posix()
    except ValueError:
        rel = str(fig_path)
    return f"![{alt}]({rel})"


def _augment_markdown_with_figures(md_text: str) -> str:
    """Inject dark-mode figure embeds when paper.md has none of its own.

    The Wave 1a report is produced by two independent workflow steps
    (report-draft writes prose, report-figures writes PNGs). Some drafts
    reference figures only in text; the PDF builder must still surface the
    dark-mode variants. If the markdown already contains any ``![](...)``
    image embed we leave it alone -- the author has committed to their own
    layout. Otherwise we append a ``## Figures`` section that embeds each
    discovered ``figures/fig*_dark.png`` in filename order.
    """
    if re.search(r"^!\[", md_text, flags=re.MULTILINE):
        return md_text
    if not FIG_DIR.is_dir():
        return md_text
    dark_variants = sorted(FIG_DIR.glob("fig*_dark.png"))
    if not dark_variants:
        return md_text
    section_lines = ["", "## Figures", ""]
    for idx, fig_path in enumerate(dark_variants, start=1):
        caption = f"Figure {idx}. {fig_path.stem.replace('_', ' ')}."
        section_lines.append(_figure_embed_line(fig_path, caption))
        section_lines.append("")
    if not md_text.endswith("\n"):
        md_text += "\n"
    return md_text + "\n".join(section_lines) + "\n"


def add_image(flow: list[Any], image_path: Path, caption: str, st: dict[str, ParagraphStyle]) -> None:
    if not image_path.exists():
        flow.append(para(f"[missing figure: {image_path}]", st["Caption"]))
        if caption:
            flow.append(Paragraph(inline_markup(caption), st["Caption"]))
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
    if caption:
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
                ("FONT", (0, 0), (-1, -1), F_BODY, 7.5),
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
        if (
            line.startswith("**Subtitle.**")
            or line.startswith("**Author.**")
            or line.startswith("**Date.**")
            or line.startswith("**Status.**")
        ):
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
            add_image(
                flow,
                _resolve_image(image_match.group(2)),
                image_match.group(1),
                st,
            )
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


def build_pdf(*, deposit_pdf: Path | None = None) -> Path:
    """Build the Wave 1a PDF from ``PAPER_MD`` and return the output path.

    Also writes a copy to ``COPY_PDF`` and, when ``deposit_pdf`` is provided,
    mirrors the file into the external Metaphysics archive. The caller decides
    whether to pass ``deposit_pdf`` -- ``main()`` only passes it when the
    archive parent directory already exists so this script never creates it.
    """
    if not PAPER_MD.exists():
        raise FileNotFoundError(
            f"paper.md not found at {PAPER_MD}. Run the report-draft step first."
        )

    md_text = PAPER_MD.read_text(encoding="utf-8")
    md_text = _augment_markdown_with_figures(md_text)
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
        title="Concern-Gated Retrieval Wave 1a (E2a) Report",
        author="Jawaun Brown",
    )
    doc.build(flow)
    COPY_PDF.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT_PDF, COPY_PDF)
    if deposit_pdf is not None:
        # Deliberate: only mirror to the deposit path when its parent exists.
        # Do not create the archive directory here.
        if deposit_pdf.parent.is_dir():
            shutil.copyfile(OUT_PDF, deposit_pdf)
    return OUT_PDF


def main() -> int:
    deposit_pdf = DEPOSIT_PDF if DEPOSIT_PDF.parent.is_dir() else None
    out = build_pdf(deposit_pdf=deposit_pdf)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    print(f"Wrote {COPY_PDF} ({COPY_PDF.stat().st_size} bytes)")
    if deposit_pdf is not None and deposit_pdf.exists():
        print(f"Wrote {deposit_pdf} ({deposit_pdf.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
