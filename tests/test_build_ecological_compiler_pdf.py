from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader
from pytest import MonkeyPatch, raises

from scripts import build_ecological_compiler_pdf as builder


def test_ecological_compiler_pdf_builds_with_registered_verdict(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    output = tmp_path / "ecological-compiler.pdf"
    monkeypatch.setattr(builder, "OUTPUT", output)

    built = builder.build()
    reader = PdfReader(str(built))
    rendered = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert built == output
    assert built.stat().st_size > 50_000
    assert len(reader.pages) >= 10
    assert reader.metadata is not None
    assert reader.metadata.title == "The Ecological Compiler"
    assert reader.metadata.author == "Jawaun Brown"
    summary = builder.json.loads(builder.SUMMARY.read_text())
    expected_verdict = str(summary["verdict"]).upper()
    assert f"Registered verdict: {expected_verdict}" in rendered
    assert "The registered headline failed" in rendered
    assert "Figure 1. Registered ordered-logit estimates" in rendered
    assert "References" in rendered


def test_ecological_compiler_pdf_uses_portable_font_fallback(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    output = tmp_path / "fallback-fonts.pdf"
    monkeypatch.setattr(builder, "OUTPUT", output)
    monkeypatch.setattr(builder, "FONT_ROOT", tmp_path / "missing-fonts")

    assert builder.build() == output
    assert output.stat().st_size > 50_000


def test_ecological_compiler_pdf_rejects_stale_result_digest(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    source = tmp_path / "paper.md"
    source.write_text(
        re.sub(
            r"(?<=final result JSON has SHA-256 digest `)[0-9a-f]{64}(?=`)",
            "0" * 64,
            builder.SOURCE.read_text(),
        )
    )
    monkeypatch.setattr(builder, "SOURCE", source)
    monkeypatch.setattr(builder, "OUTPUT", tmp_path / "stale.pdf")

    with raises(ValueError, match="paper result digest"):
        builder.build()


def test_ecological_compiler_pdf_requires_registered_figure(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(builder, "FIGURE", tmp_path / "missing.png")
    monkeypatch.setattr(builder, "OUTPUT", tmp_path / "missing-figure.pdf")

    with raises(FileNotFoundError, match="registered coefficient figure"):
        builder.build()
