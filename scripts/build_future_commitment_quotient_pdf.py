#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the Future-Commitment Quotient paper to deterministic PDF."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from reportlab import rl_config
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_gauge_fixed_concern_transport_pdf as renderer  # noqa: E402


PAPER_DIR = ROOT / "papers" / "future_commitment_quotient"
PAPER_MARKDOWN = PAPER_DIR / "paper.md"
OUTPUT_PDF = PAPER_DIR / "paper.pdf"
COPY_PDF = ROOT / "papers" / "pdf" / "future_commitment_quotient.pdf"
FIGURES = (
    PAPER_DIR / "figures" / "fig1_factorial.png",
    PAPER_DIR / "figures" / "fig2_predictors.png",
)
setattr(rl_config, "invariant", True)


def _page_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont(renderer.F_BODY, 7.6)
    canvas.setFillColorRGB(0.35, 0.39, 0.45)
    canvas.drawString(0.72 * inch, 0.42 * inch, "Future-Commitment Quotient")
    canvas.drawRightString(
        letter[0] - 0.72 * inch,
        0.42 * inch,
        f"Page {document.page}",
    )
    canvas.restoreState()


def build_pdf(
    *,
    output_pdf: Path = OUTPUT_PDF,
    copy_pdf: Path | None = COPY_PDF,
) -> Path:
    for figure in FIGURES:
        if not figure.exists():
            raise FileNotFoundError(
                f"Missing {figure}; run "
                "scripts/make_future_commitment_quotient_figures.py"
            )
    markdown_sections = PAPER_MARKDOWN.read_text(encoding="utf-8").split(
        "[[PAGEBREAK]]"
    )
    flow = []
    for index, section in enumerate(markdown_sections):
        if index:
            flow.append(PageBreak())
        flow.extend(
            renderer.markdown_to_flow(
                section,
                renderer.styles(),
                paper_dir=PAPER_DIR,
            )
        )
    flow = [
        KeepTogether([item])
        if isinstance(item, Preformatted)
        or (isinstance(item, Paragraph) and item.style.name == "Ref")
        else item
        for item in flow
    ]
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_pdf),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.70 * inch,
        bottomMargin=0.72 * inch,
        title="The Coordinates Are Not the Causal Object",
        author="Jawaun Brown",
        subject="Exact future-commitment quotients in deterministic finite agents",
    )
    document.build(
        flow,
        onFirstPage=_page_footer,
        onLaterPages=_page_footer,
    )
    if copy_pdf is not None:
        copy_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_pdf, copy_pdf)
    return output_pdf


def main() -> int:
    output = build_pdf()
    print(f"Wrote {output} ({output.stat().st_size} bytes)")
    print(f"Wrote {COPY_PDF} ({COPY_PDF.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
