"""Byte-stable smoke test for the load-bearing prose test scaffolding."""

from __future__ import annotations

import json
from pathlib import Path

from experiments.load_bearing_prose_test.run_lbpt_smoke import (
    DEFAULT_SUMMARY_PATH,
    FIXTURE_FILES,
    build_summary,
    write_summary,
)


def test_build_summary_is_deterministic() -> None:
    first = build_summary()
    second = build_summary()
    assert first == second
    assert first["summary_digest"]
    # Digest must be a lowercase hex SHA-256 string.
    assert len(first["summary_digest"]) == 64
    assert all(ch in "0123456789abcdef" for ch in first["summary_digest"])


def test_fixture_files_all_load_and_declare_kappa() -> None:
    package_dir = Path(__file__).resolve().parents[1] / "experiments" / "load_bearing_prose_test"
    for name in FIXTURE_FILES:
        payload = json.loads((package_dir / "fixtures" / name).read_text())
        assert "family" in payload
        assert "kappa" in payload
        assert isinstance(payload["plans"], list)
        assert payload["plans"], f"fixture {name} has no plans"


def test_summary_matches_frozen_receipt() -> None:
    package_dir = Path(__file__).resolve().parents[1] / "experiments" / "load_bearing_prose_test"
    frozen = json.loads((package_dir / "results" / "summary.json").read_text())
    live = build_summary()
    assert frozen == live


def test_smoke_writes_receipt_when_invoked(tmp_path: Path) -> None:
    target = tmp_path / "summary.json"
    written = write_summary(target)
    assert written == target
    payload = json.loads(target.read_text())
    assert payload["package"] == "load_bearing_prose_test"
    assert payload["run_id"] == "load_bearing_prose_test_scaffold_2026_07_21"


def test_default_summary_path_lives_under_results_dir() -> None:
    assert DEFAULT_SUMMARY_PATH.parent.name == "results"
    assert DEFAULT_SUMMARY_PATH.name == "summary.json"
