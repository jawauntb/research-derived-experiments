from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import numpy as np
import pytest

from experiments.world_responds.suite_c_neural_transfer import (
    FEATURE_NAMES,
    LEARNED_CONDITION,
    MATCHED_RANDOM_CONDITION,
    ProbeHead,
    run_neural_transfer_suite,
    summarize_neural_records,
)
from experiments.world_responds.summarize_suite_c_neural_transfer import (
    PAPER_MD,
    PUBLIC_SUMMARY_JSON,
    build_public_summary,
    build_artifacts,
    validate_release_summary,
    validate_payload,
    validate_tracked_release_summary,
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


@pytest.fixture(scope="module")
def neural_payload() -> dict[str, Any]:
    return run_neural_transfer_suite(
        train_seeds=[301, 401, 501, 601, 701, 801, 901, 1001],
        calibration_seeds=[1301, 1401, 1501, 1601],
        eval_seeds=[2301, 2401, 2501, 2601],
        base_seed=20260706,
    )


def test_neural_transfer_passes_with_heldout_learned_head(neural_payload: dict[str, Any]) -> None:
    summary = neural_payload["summary"]
    gates = summary["gates"]

    assert gates["suite_pass"]["pass"]
    assert gates["C1_silence_replication"]["pass"]
    assert gates["C2_reengagement"]["pass"]
    assert gates["C3_recovery"]["pass"]
    assert gates["C4_no_false_calm"]["pass"]
    assert gates["C5_cost_aware_inquiry"]["pass"]
    assert gates["C6_reopenability"]["pass"]
    assert gates["N1_learned_signal_controls"]["pass"]
    assert neural_payload["training"]["train_accuracy_at_0_5"] > 0.80


def test_learned_controls_fail_for_distinct_reasons(neural_payload: dict[str, Any]) -> None:
    rows = {row["condition"]: row for row in neural_payload["summary"]["by_condition"]}
    learned = rows[LEARNED_CONDITION]
    stale = rows["stale_signal_head"]
    wrong = rows["wrong_signal_head"]
    suppressed = rows["signal_suppression_head"]
    matched = rows[MATCHED_RANDOM_CONDITION]

    assert stale["recovery_rate"] < learned["recovery_rate"]
    assert wrong["first_selectivity_ratio"] < 2.0
    assert suppressed["final_component_mae"] > learned["final_component_mae"]
    assert matched["first_selectivity_ratio"] < learned["first_selectivity_ratio"]


def test_probe_head_record_round_trips(neural_payload: dict[str, Any]) -> None:
    head = ProbeHead.from_record(neural_payload["model"])
    again = ProbeHead.from_record(head.to_record())
    features = np.asarray([0.3, 0.4, 0.2, 0.3, 0.1, 0.05, 0.2, 0.1, 1.0, 0.0])

    assert neural_payload["model"]["feature_names"] == list(FEATURE_NAMES)
    assert again.to_record() == head.to_record()
    assert again.probability(features) == pytest.approx(head.probability(features))


def test_neural_transfer_is_deterministic_for_fixed_seeds() -> None:
    train_seeds = [11, 22, 33, 44]
    calibration_seeds = [55, 66]
    eval_seeds = [77, 88]
    first = run_neural_transfer_suite(
        train_seeds=train_seeds,
        calibration_seeds=calibration_seeds,
        eval_seeds=eval_seeds,
        base_seed=20260706,
    )
    second = run_neural_transfer_suite(
        train_seeds=train_seeds,
        calibration_seeds=calibration_seeds,
        eval_seeds=eval_seeds,
        base_seed=20260706,
    )

    assert _canonical(first["model"]) == _canonical(second["model"])
    assert _canonical(first["calibration"]) == _canonical(second["calibration"])
    assert _canonical(first["rows"]) == _canonical(second["rows"])
    assert _canonical(first["summary"]) == _canonical(second["summary"])


def test_artifact_builder_validates_payload_and_writes_public_contract(
    neural_payload: dict[str, Any],
    tmp_path,
) -> None:
    validate_payload(neural_payload)
    paths = build_artifacts(neural_payload, tmp_path)
    rel_paths = {path.relative_to(tmp_path).as_posix() for path in paths}

    assert "experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.md" in rel_paths
    assert PUBLIC_SUMMARY_JSON.as_posix() in rel_paths
    assert PAPER_MD.as_posix() in rel_paths
    assert "docs/paper_reviews/suite_c_neural_probe_transfer_critical_review.md" in rel_paths
    assert "papers/habituated_reengagement/figures/suite_c_neural_fig1_gate_status.png" in rel_paths

    public_summary = json.loads((tmp_path / PUBLIC_SUMMARY_JSON).read_text())
    paper = (tmp_path / PAPER_MD).read_text()

    validate_release_summary(public_summary)
    assert public_summary["minimum_pass_rule"]["passed"]
    assert public_summary["gates"]
    assert public_summary["baselines"]
    assert public_summary["artifacts"]["paper_pdf"] == "papers/habituated_reengagement/suite_c_neural_probe_transfer.pdf"
    assert "Learned Inquiry Without False Calm" in paper


def test_checked_in_release_summary_is_current_and_schema_valid() -> None:
    validate_tracked_release_summary()


def test_release_schema_validation_rejects_missing_required_field(
    neural_payload: dict[str, Any],
) -> None:
    public_summary = build_public_summary(neural_payload)
    public_summary.pop("gates")

    with pytest.raises(ValueError, match="gates"):
        validate_release_summary(public_summary)


def test_artifact_builder_rejects_tampered_matched_budget(
    neural_payload: dict[str, Any],
) -> None:
    tampered = deepcopy(neural_payload)
    matched = next(row for row in tampered["rows"] if row["condition"] == MATCHED_RANDOM_CONDITION)
    matched["target_probe_count"] = int(matched["target_probe_count"]) + 1

    with pytest.raises(ValueError, match="stale budget"):
        validate_payload(tampered)


def test_artifact_builder_rejects_missing_gate_metric(
    neural_payload: dict[str, Any],
) -> None:
    tampered = deepcopy(neural_payload)
    for row in tampered["rows"]:
        if row["condition"] == LEARNED_CONDITION:
            row.pop("final_component_mae")

    with pytest.raises(ValueError, match="final_component_mae"):
        validate_payload(tampered)


def test_artifact_builder_rejects_unknown_manifest_conditions(
    neural_payload: dict[str, Any],
) -> None:
    tampered = deepcopy(neural_payload)
    tampered["manifest"]["conditions"] = [*tampered["manifest"]["conditions"], "extra_condition"]

    with pytest.raises(ValueError, match="manifest conditions"):
        validate_payload(tampered)


def _for_condition(
    rows: list[dict[str, Any]],
    condition: str,
    updates: dict[str, Any],
) -> None:
    for row in rows:
        if row["condition"] == condition:
            row.update(updates)


@pytest.mark.parametrize(
    ("gate_name", "mutator"),
    [
        (
            "C1_silence_replication",
            lambda rows: _for_condition(
                rows,
                "p22_learned_current_replay",
                {"affected_probe_density_post_shift": 0.2},
            ),
        ),
        (
            "C2_reengagement",
            lambda rows: _for_condition(
                rows,
                LEARNED_CONDITION,
                {"first_reengagement_ratio": 0.1},
            ),
        ),
        (
            "C3_recovery",
            lambda rows: _for_condition(
                rows,
                LEARNED_CONDITION,
                {"recovery_pass": False, "final_component_mae": 0.8},
            ),
        ),
        (
            "C4_no_false_calm",
            lambda rows: _for_condition(
                rows,
                LEARNED_CONDITION,
                {"no_false_calm": False},
            ),
        ),
        (
            "C5_cost_aware_inquiry",
            lambda rows: _for_condition(
                rows,
                MATCHED_RANDOM_CONDITION,
                {"first_selectivity_ratio": 99.0},
            ),
        ),
        (
            "C6_reopenability",
            lambda rows: _for_condition(
                rows,
                LEARNED_CONDITION,
                {"second_reopen_ratio": 0.0},
            ),
        ),
        (
            "N1_learned_signal_controls",
            lambda rows: _for_condition(
                rows,
                "stale_signal_head",
                {"recovery_pass": True, "first_reengagement_ratio": 1.0},
            ),
        ),
        (
            "N1_learned_signal_controls",
            lambda rows: _for_condition(
                rows,
                "wrong_signal_head",
                {"first_selectivity_ratio": 3.0},
            ),
        ),
        (
            "N1_learned_signal_controls",
            lambda rows: _for_condition(
                rows,
                "signal_suppression_head",
                {"no_false_calm": True, "final_component_mae": 0.01},
            ),
        ),
    ],
)
def test_gate_failures_make_neural_transfer_fail(
    neural_payload: dict[str, Any],
    gate_name: str,
    mutator,
) -> None:
    rows = deepcopy(neural_payload["rows"])
    mutator(rows)

    summary = summarize_neural_records(rows)

    assert not summary["gates"][gate_name]["pass"]
    assert not summary["gates"]["suite_pass"]["pass"]


def test_modal_budget_estimator_reports_budget_status() -> None:
    modal_runner = pytest.importorskip(
        "experiments.world_responds.modal_suite_c_neural_transfer",
        reason="Modal package is only required for Modal-backed quality runs",
    )

    assert modal_runner._estimate_cost(1, 1.0, 10.0)["within_budget"]
    assert not modal_runner._estimate_cost(10_000, 1.0, 1.0)["within_budget"]


def test_modal_quality_commands_include_release_validator() -> None:
    modal_runner = pytest.importorskip(
        "experiments.world_responds.modal_suite_c_neural_transfer",
        reason="Modal package is only required for Modal-backed quality runs",
    )
    commands = modal_runner.quality_commands("python")

    assert any(
        "experiments.world_responds.validate_suite_c_neural_transfer_release" in command
        for command in commands
    )
