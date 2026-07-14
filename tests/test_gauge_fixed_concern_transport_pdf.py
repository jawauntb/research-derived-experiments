from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


CODEX_PYTHON_PACKAGES = (
    Path.home()
    / ".cache"
    / "codex-runtimes"
    / "codex-primary-runtime"
    / "dependencies"
    / "python"
)
python_tag = f"python{sys.version_info.major}.{sys.version_info.minor}"
for candidate in CODEX_PYTHON_PACKAGES.glob(f"lib/{python_tag}/site-packages"):
    if candidate.exists():
        sys.path.insert(0, str(candidate))


@pytest.mark.skipif(importlib.util.find_spec("reportlab") is None, reason="reportlab unavailable")
def test_gauge_fixed_concern_transport_pdf_builds(tmp_path: Path) -> None:
    from scripts.build_gauge_fixed_concern_transport_pdf import (
        COPY_PDF,
        FIG_DIR,
        build_pdf,
    )

    deposit_pdf = tmp_path / "archive" / "gauge_fixed_concern_transport.pdf"
    out = build_pdf(deposit_pdf=deposit_pdf)

    assert out.exists()
    assert out.stat().st_size > 100_000
    assert COPY_PDF.exists()
    assert COPY_PDF.stat().st_size == out.stat().st_size
    assert deposit_pdf.exists()
    assert deposit_pdf.stat().st_size == out.stat().st_size

    expected_figures = {
        "fig1_transport_pipeline.png",
        "fig2_theorem_ladder.png",
        "fig3_applicability_matrix.png",
        "fig4_failure_taxonomy.png",
    }
    assert expected_figures.issubset({path.name for path in Path(FIG_DIR).glob("*.png")})
