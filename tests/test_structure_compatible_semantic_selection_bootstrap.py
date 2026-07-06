from __future__ import annotations

from experiments.structure_compatible_generalization.semantic_selection_bootstrap import (
    bootstrap_selection_records,
    build_bootstrap_report,
)
from experiments.structure_compatible_generalization.semantic_selection_control import (
    run_fixture_selection_control_sweep,
    semantic_selection_payload,
    selection_records,
)


def test_semantic_selection_bootstrap_is_deterministic_on_fixture() -> None:
    rows = run_fixture_selection_control_sweep(n_zoos=3, configs_per_zoo=8)
    records = selection_records(rows)

    first = bootstrap_selection_records(records, reps=25, seed=123)
    second = bootstrap_selection_records(records, reps=25, seed=123)

    assert first == second
    assert first["learned_lift_vs_random"]["ci95_low"] > 0.0


def test_semantic_selection_bootstrap_report_uses_zoo_units() -> None:
    rows = run_fixture_selection_control_sweep(n_zoos=4, configs_per_zoo=8)
    payload = semantic_selection_payload(rows=rows, manifest={"fixture": True})

    report = build_bootstrap_report(payload, reps=25, seed=123)

    assert report["bootstrap_unit"] == "selection_zoo"
    assert report["n_zoos"] >= 20
    assert report["point_summary"]["gates"]["min_zoo_count"]
    assert report["point_summary"]["gates"]["wrong_control_fails"]
    assert report["point_metrics"]["learned_lift_vs_random"] > 0.0
