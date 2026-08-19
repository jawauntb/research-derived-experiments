from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader


pytest.importorskip("reportlab")

from scripts.build_formal_system_atlas_pdf import (  # noqa: E402
    SOURCE,
    build_pdf,
    lean_declarations,
)


def test_formal_system_atlas_source_has_required_claim_layers() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    for heading in (
        "## Executive verdict",
        "## 2. The master formal object",
        "## 11. Major failures, nulls, and invalid runs",
        "## 14. Hypotheses and what they have borne out",
        "## 16. Open conjectures and decisive next tests",
    ):
        assert heading in source


def test_formal_system_atlas_indexes_complete_lean_surface() -> None:
    declarations = lean_declarations()

    assert len(declarations) == 513
    assert any(name == "crossing_unique" for _, _, _, name in declarations)
    assert any(name == "R_D_uniform_hamming" for _, _, _, name in declarations)


def test_formal_system_atlas_pdf_builds(tmp_path: Path) -> None:
    output = build_pdf(tmp_path / "formal_system_atlas.pdf")
    reader = PdfReader(str(output))
    extracted = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert output.read_bytes().startswith(b"%PDF")
    assert output.stat().st_size > 150_000
    assert len(reader.pages) >= 60
    assert "Appendix B - Exhaustive experiment package ledger" in extracted
    assert "Appendix D - Exhaustive Lean declaration inventory" in extracted
