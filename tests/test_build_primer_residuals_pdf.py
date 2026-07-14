from __future__ import annotations

from pathlib import Path

from scripts.build_primer_residuals_pdf import SOURCE, build_pdf, validate_source


def test_primer_residual_source_has_all_article_sections() -> None:
    validate_source(SOURCE.read_text(encoding="utf-8"))


def test_primer_residual_pdf_builds(tmp_path: Path) -> None:
    output = build_pdf(tmp_path / "primer_residuals.pdf")

    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 100_000
