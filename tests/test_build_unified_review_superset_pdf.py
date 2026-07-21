from __future__ import annotations

from pathlib import Path

import pytest


pytest.importorskip("reportlab")

from scripts.build_unified_review_superset_pdf import SOURCE, build_pdf, validate_source  # noqa: E402


def test_unified_review_source_has_all_four_parts() -> None:
    validate_source(SOURCE.read_text(encoding="utf-8"))


def test_unified_review_superset_pdf_builds(tmp_path: Path) -> None:
    output = build_pdf(tmp_path / "unified_review_superset.pdf")

    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 150_000
