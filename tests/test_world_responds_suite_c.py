from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Callable

import pytest

from experiments.world_responds.summarize_suite_c import (
    PUBLIC_SUMMARY_JSON,
    build_artifacts,
    validate_payload,
)
from experiments.world_responds.suite_c_reengagement import (
    CONDITIONS,
    CANDIDATE_CONDITIONS,
    run_suite,
    run_trial,
    summarize_records,
)


def test_suite_c_passes_with_decision_layer_candidate() -> None:
    payload = run_suite(seeds=[20260706, 20261709, 20262712])
    summary = payload["summary"]

    assert summary["gates"]["suite_pass"]["pass"]
    assert summary["headline_condition"] in CANDIDATE_CONDITIONS
    assert summary["gates"]["C1_silence_replication"]["pass"]
    assert summary["gates"]["C2_reengagement"]["pass"]
    assert summary["gates"]["C3_recovery"]["pass"]
    assert summary["gates"]["C4_no_false_calm"]["pass"]
    assert summary["gates"]["C5_cost_aware_inquiry"]["pass"]
    assert summary["gates"]["C6_reopenability"]["pass"]


def test_signal_layer_cooling_is_rejected_as_false_calm() -> None:
    rows = [run_trial("fixed_surprise_decrement", seed) for seed in [1, 2, 3, 4]]
    summary = summarize_records(
        rows
        + [run_trial(condition, 1) for condition in CONDITIONS if condition != "fixed_surprise_decrement"]
        + [run_trial("matched_random_time_budget", 1, target_probe_count=58)]
    )
    fixed = next(row for row in summary["by_condition"] if row["condition"] == "fixed_surprise_decrement")

    assert fixed["no_false_calm_rate"] < 0.5
    assert fixed["final_component_mae"] > 0.12


def test_matched_random_budget_does_not_match_selectivity() -> None:
    payload = run_suite(seeds=[7, 11, 13])
    rows = {row["condition"]: row for row in payload["summary"]["by_condition"]}
    headline = rows[payload["summary"]["headline_condition"]]
    matched = rows["matched_random_time_budget"]

    assert matched["total_probes"] == headline["total_probes"]
    assert payload["manifest"]["matched_budget_condition"] == payload["summary"]["headline_condition"]
    assert matched["first_selectivity_ratio"] < headline["first_selectivity_ratio"]

    headline_by_seed = {
        row["seed"]: row["total_probes"]
        for row in payload["rows"]
        if row["condition"] == payload["summary"]["headline_condition"]
    }
    for row in payload["rows"]:
        if row["condition"] == "matched_random_time_budget":
            assert row["target_probe_count"] == headline_by_seed[row["seed"]]


def test_trial_rows_are_deterministic() -> None:
    first = run_trial("decision_refractory", 123)
    second = run_trial("decision_refractory", 123)

    assert first == second
    assert first["first_selectivity_ratio"] >= 2.0
    assert first["second_reopen_ratio"] >= 1.0


def _failing_summary(mutator: Callable[[list[dict[str, Any]], str], None]) -> dict[str, Any]:
    payload = run_suite(seeds=[20260706, 20261709, 20262712])
    rows = deepcopy(payload["rows"])
    mutator(rows, payload["summary"]["headline_condition"])
    return summarize_records(rows)


def _for_conditions(
    rows: list[dict[str, Any]],
    conditions: tuple[str, ...],
    update: dict[str, Any],
) -> None:
    for row in rows:
        if row["condition"] in conditions:
            row.update(update)


@pytest.mark.parametrize(
    ("gate_name", "mutator"),
    [
        (
            "C1_silence_replication",
            lambda rows, _headline: _for_conditions(
                rows,
                ("p22_learned_current_replay",),
                {"affected_probe_density_post_shift": 0.2},
            ),
        ),
        (
            "C2_reengagement",
            lambda rows, _headline: _for_conditions(
                rows,
                CANDIDATE_CONDITIONS,
                {"first_reengagement_ratio": 0.1},
            ),
        ),
        (
            "C3_recovery",
            lambda rows, _headline: _for_conditions(
                rows,
                CANDIDATE_CONDITIONS,
                {"recovery_pass": False, "final_component_mae": 0.8},
            ),
        ),
        (
            "C4_no_false_calm",
            lambda rows, _headline: _for_conditions(
                rows,
                CANDIDATE_CONDITIONS,
                {"no_false_calm": False},
            ),
        ),
        (
            "C5_cost_aware_inquiry",
            lambda rows, _headline: _for_conditions(
                rows,
                ("matched_random_time_budget",),
                {"first_selectivity_ratio": 99.0},
            ),
        ),
        (
            "C6_reopenability",
            lambda rows, _headline: _for_conditions(
                rows,
                CANDIDATE_CONDITIONS,
                {"second_reopen_ratio": 0.0},
            ),
        ),
    ],
)
def test_gate_failures_make_suite_fail(
    gate_name: str,
    mutator: Callable[[list[dict[str, Any]], str], None],
) -> None:
    summary = _failing_summary(mutator)

    assert not summary["gates"][gate_name]["pass"]
    assert not summary["gates"]["suite_pass"]["pass"]


def test_artifact_builder_validates_payload_and_writes_public_contract(tmp_path) -> None:
    payload = run_suite(seeds=[20260706, 20261709, 20262712])

    validate_payload(payload)
    paths = build_artifacts(payload, tmp_path)
    rel_paths = {path.relative_to(tmp_path).as_posix() for path in paths}

    assert "experiments/world_responds/results/suite_c_reengagement_2026_07_06.md" in rel_paths
    assert PUBLIC_SUMMARY_JSON.as_posix() in rel_paths
    assert "experiments/world_responds/BENCHMARK_CARD.md" in rel_paths
    assert "papers/habituated_reengagement/suite_c_reengagement_under_world_change.md" in rel_paths
    assert (
        "docs/paper_reviews/suite_c_reengagement_under_world_change_critical_review.md"
        in rel_paths
    )
    assert "papers/habituated_reengagement/figures/suite_c_fig1_gate_status.png" in rel_paths

    report = (
        tmp_path / "experiments/world_responds/results/suite_c_reengagement_2026_07_06.md"
    ).read_text()
    card = (tmp_path / "experiments/world_responds/BENCHMARK_CARD.md").read_text()
    paper = (
        tmp_path / "papers/habituated_reengagement/suite_c_reengagement_under_world_change.md"
    ).read_text()
    public_summary = json.loads((tmp_path / PUBLIC_SUMMARY_JSON).read_text())

    assert "| C1_silence_replication |" in report
    assert "Public release summary" in card
    assert "figures/suite_c_fig1_gate_status.png" in paper
    assert (
        public_summary["score_axes"]["inquiry"]["matched_budget_condition"]
        == payload["summary"]["headline_condition"]
    )


def test_artifact_builder_rejects_tampered_summary(tmp_path) -> None:
    payload = run_suite(seeds=[20260706, 20261709, 20262712])
    payload["summary"]["headline_condition"] = "p22_learned_current_replay"

    with pytest.raises(ValueError, match="summary does not match"):
        build_artifacts(payload, tmp_path)


def test_modal_budget_estimator_reports_budget_status() -> None:
    modal_runner = pytest.importorskip(
        "experiments.world_responds.modal_suite_c_reengagement",
        reason="Modal package is only required for Modal-backed quality runs",
    )

    assert modal_runner._estimate_cost(1, 1.0)["within_budget"]
    assert not modal_runner._estimate_cost(10_000, 1.0)["within_budget"]
