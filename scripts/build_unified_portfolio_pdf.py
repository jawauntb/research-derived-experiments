#!/usr/bin/env python3
"""Build the unified finite-representations portfolio PDF.

Run:
    python scripts/build_unified_portfolio_pdf.py

Outputs:
    papers/pdf/unified_metric_weakness_portfolio/finite_representations_portfolio.pdf
    papers/pdf/unified_metric_weakness_portfolio/finite_representations_portfolio_with_bookmarks.pdf
    papers/pdf/unified_metric_weakness_portfolio/README.txt
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
import textwrap

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "papers" / "pdf" / "unified_metric_weakness_portfolio"
OUT_PDF = OUT_DIR / "finite_representations_portfolio.pdf"
OUT_BOOKMARKS_PDF = OUT_DIR / "finite_representations_portfolio_with_bookmarks.pdf"
OUT_README = OUT_DIR / "README.txt"


@dataclass(frozen=True)
class PaperSpec:
    number: int
    title: str
    subtitle: str
    source: Path
    bookmark: str


PAPERS = [
    PaperSpec(
        1,
        "Value-Weighted Training Deforms Learned Metrics Across RNN, Transformer, and JEPA-Style Spatial Models",
        "Flagship moved-location intervention",
        ROOT / "papers" / "pdf" / "concern_deforms_metric.pdf",
        "Paper 1 - Value-Weighted Training",
    ),
    PaperSpec(
        2,
        "A Measured Effective-Dimension Law for Value-Weighted Metric Deformation in Path-Integration RNNs",
        "Companion scaling diagnostic",
        ROOT / "papers" / "pdf" / "reward_deformation_effective_dimension_law.pdf",
        "Paper 2 - Effective-Dimension Law",
    ),
    PaperSpec(
        3,
        "Symmetry-Compatible Hypothesis Volume Predicts Out-of-Distribution Generalization",
        "Weakness, not generic compression alone, in shortcut-compatible learning problems",
        ROOT / "papers" / "pdf" / "weakness_predicts_ood.pdf",
        "Paper 3 - Symmetry-Compatible Hypothesis Volume",
    ),
    PaperSpec(
        4,
        "Translation Augmentation Produces Toroidal Codes and Larger-Arena Generalization in Path-Integration RNNs",
        "Negative mediation result for weakness as the governing scalar",
        ROOT / "papers" / "pdf" / "weakness_predicts_topology.pdf",
        "Paper 4 - Translation Augmentation and Toroidal Codes",
    ),
]


EXECUTIVE_OVERVIEW = [
    (
        "Metric allocation is experimentally movable.",
        "In finite-capacity spatial models, externally specified value weights causally reshape "
        "local representational geometry. Moving the priority field moves local metric density "
        "across RNN, Transformer, and JEPA-style spatial models.",
    ),
    (
        "The scaling exponent measures effective allocation dimension.",
        "A value-weighted rate-distortion derivation predicts a physical two-dimensional exponent, "
        "but the measured RNN exponent is near the one-dimensional family. The exponent therefore "
        "reports the effective dimension through which the learned code reallocates capacity, not "
        "merely the physical dimension of the arena.",
    ),
    (
        "Symmetry-compatible hypothesis volume predicts OOD completion.",
        "In shortcut-compatible finite tasks, the relevant simplicity is not generic compression "
        "alone but compatibility with the transformations that generate missing deployment cases.",
    ),
    (
        "The weakness program has a real boundary.",
        "In path-integration topology, translation augmentation produces toroidal, larger-arena-"
        "generalizing codes, but weakness does not govern torus formation or mediate the OOD "
        "effect. This negative result bounds the theory rather than weakening the empirical program.",
    ),
]


READING_GUIDE = [
    "Paper 1 is the flagship empirical result: value-weighted training deforms learned metrics "
    "across RNN, Transformer, and JEPA-style spatial models.",
    "Paper 2 is the companion scaling diagnostic: the exponent of value-weighted metric "
    "deformation reveals an effective allocation dimension near one in the tested RNN harness.",
    "Paper 3 is the broader model-selection result: symmetry-compatible hypothesis volume predicts "
    "out-of-distribution generalization in shortcut-compatible symbolic, MLP, and vision tasks.",
    "Paper 4 is the boundary/negative result: translation augmentation produces toroidal and larger-"
    "arena-generalizing path-integration codes, but weakness is not the governing scalar of torus "
    "formation in this harness.",
    "Together, the papers argue that finite learned representations allocate resolution and "
    "generalization capacity according to externally supplied structure, while also identifying "
    "where the strongest theory fails.",
]


README_TEXT = """Unified portfolio PDF
Order:
1. Value-Weighted Training Deforms Learned Metrics Across RNN, Transformer, and JEPA-Style Spatial Models
2. A Measured Effective-Dimension Law for Value-Weighted Metric Deformation in Path-Integration RNNs
3. Symmetry-Compatible Hypothesis Volume Predicts Out-of-Distribution Generalization
4. Translation Augmentation Produces Toroidal Codes and Larger-Arena Generalization in Path-Integration RNNs
This portfolio is intended as a single readable research packet. Paper 1 is the flagship result; Paper 2 is its scaling/mechanistic companion; Paper 3 broadens the framework to symmetry-compatible OOD generalization; Paper 4 gives the negative topology mediation boundary condition.
"""


def paragraph_style() -> tuple[ParagraphStyle, ParagraphStyle, ParagraphStyle, ParagraphStyle]:
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "PortfolioTitle",
        parent=styles["Title"],
        fontName="Times-Bold",
        fontSize=21,
        leading=26,
        textColor=colors.HexColor("#111827"),
        spaceAfter=18,
    )
    subtitle = ParagraphStyle(
        "PortfolioSubtitle",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#374151"),
        spaceAfter=8,
    )
    heading = ParagraphStyle(
        "PortfolioHeading",
        parent=styles["Heading1"],
        fontName="Times-Bold",
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#111827"),
        spaceAfter=16,
    )
    body = ParagraphStyle(
        "PortfolioBody",
        parent=styles["BodyText"],
        fontName="Times-Roman",
        fontSize=10.8,
        leading=15.2,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=10,
    )
    return title, subtitle, heading, body


def build_front_matter(path: Path) -> None:
    title, subtitle, heading, body = paragraph_style()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title="Finite Representations Portfolio",
        author="Jawaun Brown",
    )
    flow = [
        Spacer(1, 1.35 * inch),
        Paragraph("Finite Representations Allocate Resolution and Generalization Under Structure", title),
        Paragraph(
            "Four Research-Derived Experiments on Metric Deformation,<br/>"
            "Effective Dimension, Weakness, and Toroidal Topology",
            subtitle,
        ),
        Spacer(1, 0.35 * inch),
        Paragraph("Jawaun Brown", subtitle),
        Paragraph("July 2026", subtitle),
        PageBreak(),
        Paragraph("Executive Overview", heading),
        Paragraph("This portfolio collects four linked research-derived experiments on finite learned representations.", body),
    ]
    for idx, (lead, text) in enumerate(EXECUTIVE_OVERVIEW, start=1):
        flow.append(Paragraph(f"{idx}. <b>{lead}</b> {text}", body))
    flow.extend([PageBreak(), Paragraph("Reading Guide", heading)])
    flow.extend(Paragraph(item, body) for item in READING_GUIDE)
    doc.build(flow)


def build_divider(path: Path, paper: PaperSpec) -> None:
    title, subtitle, _, body = paragraph_style()
    number_style = ParagraphStyle(
        "PaperNumber",
        parent=subtitle,
        fontName="Times-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=16,
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title=f"Paper {paper.number}",
        author="Jawaun Brown",
    )
    flow = [
        Spacer(1, 1.5 * inch),
        Paragraph(f"Paper {paper.number}", number_style),
        Paragraph(paper.title, title),
        Paragraph(paper.subtitle, subtitle),
        Spacer(1, 0.25 * inch),
        Paragraph("Included as part of the unified finite-representations research portfolio.", body),
    ]
    doc.build(flow)


def append_pdf(writer: PdfWriter, source: Path) -> int:
    reader = PdfReader(str(source))
    for page in reader.pages:
        writer.add_page(page)
    return len(reader.pages)


def write_merged_pdf(path: Path, front_pdf: Path, dividers: dict[int, Path], *, bookmarks: bool) -> dict[str, int]:
    writer = PdfWriter()
    page_starts: dict[str, int] = {}

    page_starts["Executive Overview"] = 1
    page_starts["Reading Guide"] = 2
    append_pdf(writer, front_pdf)

    for paper in PAPERS:
        page_starts[paper.bookmark] = len(writer.pages)
        append_pdf(writer, dividers[paper.number])
        append_pdf(writer, paper.source)

    if bookmarks:
        writer.add_outline_item("Executive Overview", page_starts["Executive Overview"])
        writer.add_outline_item("Reading Guide", page_starts["Reading Guide"])
        for paper in PAPERS:
            writer.add_outline_item(paper.bookmark, page_starts[paper.bookmark])

    with path.open("wb") as handle:
        writer.write(handle)
    return page_starts


def expected_page_count() -> int:
    return 3 + len(PAPERS) + sum(len(PdfReader(str(paper.source)).pages) for paper in PAPERS)


def outline_titles(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    titles: list[str] = []

    def walk(items: list[object]) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item)
            else:
                title = getattr(item, "title", None)
                if title:
                    titles.append(str(title))

    walk(reader.outline)
    return titles


def verify_outputs(page_starts: dict[str, int]) -> None:
    expected = expected_page_count()
    for path in (OUT_PDF, OUT_BOOKMARKS_PDF):
        actual = len(PdfReader(str(path)).pages)
        if actual != expected:
            raise RuntimeError(f"{path} has {actual} pages; expected {expected}")

    required_bookmarks = [
        "Executive Overview",
        "Reading Guide",
        "Paper 1 - Value-Weighted Training",
        "Paper 2 - Effective-Dimension Law",
        "Paper 3 - Symmetry-Compatible Hypothesis Volume",
        "Paper 4 - Translation Augmentation and Toroidal Codes",
    ]
    titles = outline_titles(OUT_BOOKMARKS_PDF)
    missing = [title for title in required_bookmarks if title not in titles]
    if missing:
        raise RuntimeError(f"missing bookmarks: {missing}")

    if page_starts["Paper 1 - Value-Weighted Training"] != 3:
        raise RuntimeError("Paper 1 divider did not start after the three front-matter pages")


def main() -> None:
    missing = [paper.source for paper in PAPERS if not paper.source.exists()]
    if missing:
        raise FileNotFoundError(f"missing source PDFs: {missing}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_README.write_text(README_TEXT, encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="portfolio_pdf_") as tmp:
        tmpdir = Path(tmp)
        front_pdf = tmpdir / "front_matter.pdf"
        build_front_matter(front_pdf)
        dividers: dict[int, Path] = {}
        for paper in PAPERS:
            divider = tmpdir / f"divider_{paper.number}.pdf"
            build_divider(divider, paper)
            dividers[paper.number] = divider

        write_merged_pdf(OUT_PDF, front_pdf, dividers, bookmarks=False)
        starts = write_merged_pdf(OUT_BOOKMARKS_PDF, front_pdf, dividers, bookmarks=True)

    verify_outputs(starts)
    expected = expected_page_count()
    print(f"[portfolio] wrote {OUT_PDF.relative_to(ROOT)} ({expected} pages)")
    print(f"[portfolio] wrote {OUT_BOOKMARKS_PDF.relative_to(ROOT)} ({expected} pages)")
    print(f"[portfolio] wrote {OUT_README.relative_to(ROOT)}")
    print("[portfolio] bookmarks:")
    for line in textwrap.indent("\n".join(outline_titles(OUT_BOOKMARKS_PDF)), "  ").splitlines():
        print(line)


if __name__ == "__main__":
    main()
