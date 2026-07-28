#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the Information-Limited Discovery paper to deterministic PDF."""

from __future__ import annotations

import re
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
    Table,
)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_gauge_fixed_concern_transport_pdf as renderer  # noqa: E402


PAPER_DIR = ROOT / "papers" / "information_limited_discovery"
PAPER_MARKDOWN = PAPER_DIR / "paper.md"
OUTPUT_PDF = PAPER_DIR / "paper.pdf"
COPY_PDF = ROOT / "papers" / "pdf" / "information_limited_discovery.pdf"
DEPOSIT_PDF = (
    Path("/Users/jawaun/Metaphysics of Intelligence")
    / "Information_Limited_Discovery_2026_07_27.pdf"
)
setattr(rl_config, "invariant", True)


def _plain_math(value: str) -> str:
    """Convert this paper's small LaTeX vocabulary to readable Unicode."""

    text = " ".join(line.strip() for line in value.splitlines())
    function_patterns = (
        (r"\\operatorname\{([^{}]+)\}", r"\1"),
        (r"\\mathcal\{([^{}]+)\}", r"\1"),
        (r"\\mathcal\s+([A-Za-z])", r"\1"),
        (r"\\mathbb\{([^{}]+)\}", r"\1"),
        (r"\\mathbb\s+([A-Za-z])", r"\1"),
        (r"\\text\{([^{}]+)\}", r"\1"),
    )
    for pattern, replacement in function_patterns:
        text = re.sub(pattern, replacement, text)
    replacements = (
        (r"\Gamma", "Γ"),
        (r"\tau", "τ"),
        (r"\star", "*"),
        (r"\rightarrow", "→"),
        (r"\to", "→"),
        (r"\subseteq", "⊆"),
        (r"\in", "∈"),
        (r"\notin", "∉"),
        (r"\ne", "≠"),
        (r"\forall", "∀"),
        (r"\exists", "∃"),
        (r"\land", "∧"),
        (r"\square", "□"),
        (r"\ldots", "..."),
        (r"\quad", "  "),
        (r"\,", " "),
        (r"\;", " "),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r"_\{([^{}]+)\}", r"_\1", text)
    text = re.sub(r"\^\{([^{}]+)\}", r"^\1", text)
    text = text.replace(r"\{", "{").replace(r"\}", "}")
    text = text.replace(r"\*", "*")
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\\([A-Za-z]+)", r"\1", text)
    text = text.replace("N_>0", "N>0")
    return re.sub(r"\s+", " ", text).strip()


def normalize_markdown(text: str) -> str:
    """Make equations and punctuation safe for the ReportLab renderer."""

    text = re.sub(
        r"\\\[(.+?)\\\]",
        lambda match: "\n```text\n" + _plain_math(match.group(1)) + "\n```\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\\\((.+?)\\\]",
        lambda match: _plain_math(match.group(1)),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\\\((.+?)\\\)",
        lambda match: _plain_math(match.group(1)),
        text,
        flags=re.DOTALL,
    )
    text = (
        text.replace("\N{EM DASH}", "-")
        .replace("\N{EN DASH}", "-")
        .replace("\N{NON-BREAKING HYPHEN}", "-")
    )
    text = text.replace(
        "\n## Reproducibility\n",
        "\n[[PAGEBREAK]]\n## Reproducibility\n",
    )
    lines = text.splitlines()
    joined: list[str] = []
    in_code = False
    for line in lines:
        if line.startswith("```"):
            in_code = not in_code
            joined.append(line)
            continue
        if (
            not in_code
            and line.startswith(("  ", "\t"))
            and joined
            and re.match(r"^(?:- |\d+\. )", joined[-1])
        ):
            joined[-1] = f"{joined[-1].rstrip()} {line.strip()}"
            continue
        joined.append(line)
    return "\n".join(joined) + ("\n" if text.endswith("\n") else "")


def _page_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont(renderer.F_BODY, 7.6)
    canvas.setFillColorRGB(0.35, 0.39, 0.45)
    canvas.drawString(
        0.72 * inch,
        0.42 * inch,
        "Information-Limited Discovery",
    )
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
    deposit_pdf: Path | None = None,
) -> Path:
    markdown = normalize_markdown(PAPER_MARKDOWN.read_text(encoding="utf-8"))
    style_map = renderer.styles()
    setattr(style_map["H2"], "keepWithNext", True)
    setattr(style_map["H2"], "spaceAfter", 7)
    setattr(style_map["H3"], "keepWithNext", True)
    setattr(style_map["H3"], "spaceAfter", 5)
    flow = []
    for index, section in enumerate(markdown.split("[[PAGEBREAK]]")):
        if index:
            flow.append(PageBreak())
        flow.extend(
            renderer.markdown_to_flow(
                section,
                style_map,
                paper_dir=PAPER_DIR,
            )
        )
    flow = [
        KeepTogether([item])
        if isinstance(item, (Preformatted, Table))
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
        title="Information-Limited Discovery",
        author="Jawaun Brown",
        subject="Obstruction certificates for counterexample-first scientific reasoning",
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
        if not deposit_pdf.parent.is_dir():
            raise FileNotFoundError(
                f"archive directory does not exist: {deposit_pdf.parent}"
            )
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
