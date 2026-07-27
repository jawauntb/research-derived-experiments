#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the Constraint-Swap falsification paper to deterministic PDF."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from reportlab import rl_config
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, Preformatted, SimpleDocTemplate

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_gauge_fixed_concern_transport_pdf as renderer  # noqa: E402


PAPER_DIR = ROOT / "papers" / "constraint_swap_causal_geometry"
PAPER_MD = PAPER_DIR / "paper.md"
OUT_PDF = PAPER_DIR / "paper.pdf"
COPY_PDF = ROOT / "papers" / "pdf" / "constraint_swap_causal_geometry.pdf"
DEPOSIT_PDF = (
    Path("/Users/jawaun/Metaphysics of Intelligence")
    / "Constraint_Swap_Causal_Geometry_2026_07_27.pdf"
)
FIGURES = (
    PAPER_DIR / "figures" / "fig1_registered_chain.png",
    PAPER_DIR / "figures" / "fig2_geometry_swap.png",
    PAPER_DIR / "figures" / "fig3_interventions.png",
    PAPER_DIR / "figures" / "fig4_gates.png",
)
setattr(rl_config, "invariant", True)


def _page_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont(renderer.F_BODY, 7.6)
    canvas.setFillColorRGB(0.35, 0.39, 0.45)
    canvas.drawString(0.72 * inch, 0.42 * inch, "Constraint Is Not Geometry")
    canvas.drawRightString(
        letter[0] - 0.72 * inch,
        0.42 * inch,
        f"Page {document.page}",
    )
    canvas.restoreState()


def build_pdf(
    *,
    output_pdf: Path = OUT_PDF,
    copy_pdf: Path | None = COPY_PDF,
    deposit_pdf: Path | None = None,
) -> Path:
    for figure in FIGURES:
        if not figure.exists():
            raise FileNotFoundError(
                f"Missing {figure}; run scripts/make_constraint_swap_causal_geometry_figures.py"
            )
    renderer.PAPER_DIR = PAPER_DIR
    flow = renderer.markdown_to_flow(
        PAPER_MD.read_text(encoding="utf-8"),
        renderer.styles(),
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
        title="Constraint Is Not Geometry",
        author="Jawaun Brown",
        subject="Preregistered constraint-swap causal geometry experiment",
    )
    document.build(
        flow,
        onFirstPage=_page_footer,
        onLaterPages=_page_footer,
    )
    if copy_pdf is not None:
        copy_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_pdf, copy_pdf)
    if deposit_pdf is not None:
        deposit_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output_pdf, deposit_pdf)
    return output_pdf


def main() -> int:
    deposit = DEPOSIT_PDF if DEPOSIT_PDF.parent.is_dir() else None
    output = build_pdf(deposit_pdf=deposit)
    print(f"Wrote {output} ({output.stat().st_size} bytes)")
    print(f"Wrote {COPY_PDF} ({COPY_PDF.stat().st_size} bytes)")
    if deposit is not None:
        print(f"Wrote {deposit} ({deposit.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
