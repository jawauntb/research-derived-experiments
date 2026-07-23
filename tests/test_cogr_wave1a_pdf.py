"""Smoke test for the Concern-Gated Retrieval Wave 1a (E2a) PDF builder.

The Wave 1a paper markdown and figures are produced by upstream workflow
steps (report-draft and report-figures). This test only runs when
``papers/concern_gated_retrieval_e2a/paper.md`` exists so it can be
committed alongside the builder without blocking green CI before the
upstream steps land.

When the markdown does exist, we build the PDF into a temporary directory
(so we do not clobber the committed one) and assert only that the build
completes and the resulting file is >= 30 KB. We deliberately do not assert
on figure existence -- resilience to a partial upstream is by design, and
mirrors the Wave 0 smoke-test posture.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


# Codex CLI ships some Python deps in a side cache; mirror the existing
# Wave 0 test pattern so the smoke test can import reportlab regardless
# of which runtime picks the module up.
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


REPO_ROOT = Path(__file__).resolve().parents[1]
PAPER_MD = REPO_ROOT / "papers" / "concern_gated_retrieval_e2a" / "paper.md"


@pytest.mark.skipif(
    not PAPER_MD.exists(),
    reason="Wave 1a paper.md not yet produced by upstream report-draft step",
)
@pytest.mark.skipif(
    importlib.util.find_spec("reportlab") is None,
    reason="reportlab unavailable",
)
def test_cogr_wave1a_pdf_builds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import build_cogr_wave1a_pdf as paper_builder

    out_pdf = tmp_path / "paper" / "paper.pdf"
    copy_pdf = tmp_path / "pdf" / "concern_gated_retrieval_e2a.pdf"
    monkeypatch.setattr(paper_builder, "OUT_PDF", out_pdf)
    monkeypatch.setattr(paper_builder, "COPY_PDF", copy_pdf)

    # Never touch the real Metaphysics archive from a test run.
    out = paper_builder.build_pdf(deposit_pdf=None)

    assert out.exists()
    assert out.stat().st_size >= 30_000, (
        f"Wave 1a PDF at {out} is only {out.stat().st_size} bytes; expected >= 30 KB."
    )
    assert copy_pdf.exists()
    assert copy_pdf.stat().st_size == out.stat().st_size
    assert out.read_bytes().startswith(b"%PDF")
