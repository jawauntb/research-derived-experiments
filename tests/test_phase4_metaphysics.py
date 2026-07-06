from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.phase4_metaphysics.core import TRACKS, run_cell, run_suite, summarize_rows


def test_smoke_suite_runs_all_tracks() -> None:
    payload = run_suite("smoke", seeds=1)
    assert payload["summary"]["n_rows"] > 0
    assert set(payload["summary"]["by_track"]) == set(TRACKS)
    assert "all_pass" in payload["summary"]["gates"]


def test_each_track_cell_is_deterministic() -> None:
    for track in TRACKS:
        first = run_cell(track, seed=2, preset="smoke")
        second = run_cell(track, seed=2, preset="smoke")
        assert first == second


def test_summary_contains_expected_gate_metrics() -> None:
    rows = []
    for track in TRACKS:
        rows.extend(run_cell(track, seed=0, preset="smoke"))
    summary = summarize_rows(rows)
    gates = summary["gates"]
    assert gates["language_scale"]["intervention_ratio"] > 1.0
    assert gates["probe_value"]["learned_voi_spearman"] > gates["probe_value"]["current_error_reduction"]
    assert gates["beyond_ceiling"]["shared_mae"] > gates["beyond_ceiling"]["role_mae"]
