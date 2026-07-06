from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest

from experiments.world_responds.suite_c_teacher_free import (
    MATCHED_RANDOM_CONDITION,
    SUPPRESSION_CONTROL_CONDITION,
    TEACHER_FREE_CONDITION,
    run_teacher_free_suite,
    summarize_teacher_free_records,
)
from experiments.world_responds.summarize_suite_c_teacher_free import (
    PUBLIC_SUMMARY_JSON,
    REPORT_MD,
    ROWS_JSONL,
    build_artifacts,
    validate_payload,
)


@pytest.fixture(scope="module")
def teacher_free_payload() -> dict[str, Any]:
    return run_teacher_free_suite(
        train_seeds=[111, 222, 333],
        calibration_seeds=[444, 555, 666, 777],
        eval_seeds=[888, 999, 1110, 1221],
        base_seed=20260706,
    )


def test_teacher_free_suite_passes_without_teacher_labels(
    teacher_free_payload: dict[str, Any],
) -> None:
    gates = teacher_free_payload["summary"]["gates"]

    assert gates["suite_pass"]["pass"]
    assert gates["C1_silence_replication"]["pass"]
    assert gates["C2_reengagement"]["pass"]
    assert gates["C3_recovery"]["pass"]
    assert gates["C4_no_false_calm"]["pass"]
    assert gates["C5_cost_aware_inquiry"]["pass"]
    assert gates["C6_reopenability"]["pass"]
    assert gates["T1_teacher_free_training"]["pass"]
    assert gates["N1_learned_signal_controls"]["pass"]
    assert not teacher_free_payload["training"]["teacher_labels_used"]
    assert not teacher_free_payload["training"]["teacher_actions_used"]
    assert not teacher_free_payload["training"]["teacher_probabilities_used"]


def test_teacher_free_controls_fail_for_distinct_reasons(
    teacher_free_payload: dict[str, Any],
) -> None:
    rows = {row["condition"]: row for row in teacher_free_payload["summary"]["by_condition"]}
    learned = rows[TEACHER_FREE_CONDITION]
    matched = rows[MATCHED_RANDOM_CONDITION]
    suppressed = rows[SUPPRESSION_CONTROL_CONDITION]

    assert matched["first_selectivity_ratio"] < learned["first_selectivity_ratio"]
    assert suppressed["final_component_mae"] > learned["final_component_mae"]
    assert suppressed["no_false_calm_rate"] == 0.0


def test_teacher_free_payload_is_deterministic() -> None:
    kwargs: dict[str, Any] = {
        "train_seeds": [11, 22, 33],
        "calibration_seeds": [44, 55, 66, 77],
        "eval_seeds": [88, 99, 111, 122],
        "base_seed": 20260706,
    }
    first = run_teacher_free_suite(**kwargs)
    second = run_teacher_free_suite(**kwargs)

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_teacher_free_artifact_builder_writes_public_rows(
    teacher_free_payload: dict[str, Any],
    tmp_path,
) -> None:
    validate_payload(teacher_free_payload)
    paths = build_artifacts(teacher_free_payload, tmp_path)
    rel_paths = {path.relative_to(tmp_path).as_posix() for path in paths}

    assert ROWS_JSONL.as_posix() in rel_paths
    assert PUBLIC_SUMMARY_JSON.as_posix() in rel_paths
    assert REPORT_MD.as_posix() in rel_paths

    rows = (tmp_path / ROWS_JSONL).read_text().strip().splitlines()
    summary = json.loads((tmp_path / PUBLIC_SUMMARY_JSON).read_text())
    report = (tmp_path / REPORT_MD).read_text()

    assert len(rows) == teacher_free_payload["summary"]["n_rows"]
    assert summary["minimum_pass_rule"]["passed"]
    assert "T1_teacher_free_training" in report


@pytest.mark.parametrize(
    ("gate_name", "condition", "updates"),
    [
        (
            "C2_reengagement",
            TEACHER_FREE_CONDITION,
            {"first_reengagement_ratio": 0.1},
        ),
        (
            "C3_recovery",
            TEACHER_FREE_CONDITION,
            {"recovery_pass": False, "final_component_mae": 0.9},
        ),
        (
            "T1_teacher_free_training",
            TEACHER_FREE_CONDITION,
            {"teacher_labels_used": True},
        ),
    ],
)
def test_gate_failures_make_teacher_free_suite_fail(
    teacher_free_payload: dict[str, Any],
    gate_name: str,
    condition: str,
    updates: dict[str, Any],
) -> None:
    rows = deepcopy(teacher_free_payload["rows"])
    for row in rows:
        if row["condition"] == condition:
            row.update(updates)

    summary = summarize_teacher_free_records(rows)

    assert not summary["gates"][gate_name]["pass"]
    assert not summary["gates"]["suite_pass"]["pass"]
