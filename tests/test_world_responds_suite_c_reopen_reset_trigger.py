from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from experiments.world_responds.suite_c_reopen_reset_trigger import (
    ARMS,
    CALIBRATION_RECEIPT,
    DEFAULT_CONFIG,
    DEFAULT_SEEDS,
    FROZEN_CALIBRATION_FILE_SHA256,
    FROZEN_CALIBRATION_RECEIPT_SHA256,
    INTEGRITY_FLOAT_DECIMALS,
    _integrity_sha256,
    build_probe_plan,
    calibrate_trigger_thresholds,
    evaluate_gates,
    run_m5_suite,
    write_artifacts,
)
from experiments.world_responds.suite_c_reengagement import run_trial


@pytest.fixture(scope="module")
def calibration() -> dict[str, Any]:
    return calibrate_trigger_thresholds(DEFAULT_SEEDS)


@pytest.fixture(scope="module")
def payload(calibration: dict[str, Any]) -> dict[str, Any]:
    return run_m5_suite(seeds=DEFAULT_SEEDS, calibration=calibration)


def test_calibration_is_pre_shift_deterministic_and_outcome_blind(
    calibration: dict[str, Any],
) -> None:
    replay = calibrate_trigger_thresholds(DEFAULT_SEEDS)
    committed = json.loads(CALIBRATION_RECEIPT.read_text())

    assert calibration == replay == committed
    assert calibration["window"] == [12, 23]
    assert calibration["source"] == "m4_full_on_reference_pre_first_shift"
    assert calibration["thresholds"]["T_util"] > calibration["max_scores"]["T_util"]
    assert calibration["thresholds"]["T_norm"] > calibration["max_scores"]["T_norm"]
    assert calibration["receipt_sha256"] == FROZEN_CALIBRATION_RECEIPT_SHA256
    assert hashlib.sha256(CALIBRATION_RECEIPT.read_bytes()).hexdigest() == (
        FROZEN_CALIBRATION_FILE_SHA256
    )


def test_probe_plan_is_arm_independent_and_matches_immutable_m4_budget() -> None:
    seed = DEFAULT_SEEDS[0]
    plan = build_probe_plan(seed)
    replay = build_probe_plan(seed)

    assert plan == replay
    assert plan["source_condition"] == (
        "burst_then_refractory__allocate_0_cool_0_reopen_1"
    )
    assert len(plan["slots"]) == plan["budget"]
    assert len(plan["plan_id"]) == 64


def test_probe_trace_is_opt_in_and_preserves_the_default_trial_contract() -> None:
    seed = DEFAULT_SEEDS[0]
    default = run_trial("burst_then_refractory", seed)
    traced = run_trial("burst_then_refractory", seed, include_probe_trace=True)
    trace = traced.pop("probe_trace")

    assert "probe_trace" not in default
    assert traced == default
    assert len(trace) == default["total_probes"]


def test_integrity_hash_ignores_only_subprecision_float_noise() -> None:
    baseline = {"value": 0.12345678901234, "negative_zero": -0.0}
    subprecision = {"value": 0.123456789012341, "negative_zero": 0.0}
    visible_change = {"value": 0.12345678911234, "negative_zero": 0.0}

    assert INTEGRITY_FLOAT_DECIMALS == 12
    assert _integrity_sha256(baseline) == _integrity_sha256(subprecision)
    assert _integrity_sha256(baseline) != _integrity_sha256(visible_change)


def test_complete_grid_has_exact_matched_actual_probe_counts(
    payload: dict[str, Any],
) -> None:
    rows = payload["rows"]
    assert len(rows) == len(DEFAULT_SEEDS) * len(ARMS)
    assert {(row["seed"], row["arm"]) for row in rows} == {
        (seed, arm) for seed in DEFAULT_SEEDS for arm in ARMS
    }

    by_seed: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_seed.setdefault(int(row["seed"]), []).append(row)
    for seed_rows in by_seed.values():
        assert len({row["plan_id"] for row in seed_rows}) == 1
        assert len({row["total_probes"] for row in seed_rows}) == 1
        assert all(row["total_probes"] == row["probe_budget"] for row in seed_rows)

    assert payload["summary"]["gates"]["F0_integrity"]["matched_actual_probes"]
    assert payload["summary"]["gates"]["F0_integrity"]["transported_controls_pass"]
    assert payload["summary"]["gates"]["F0_integrity"]["coupled_random_schedule"]
    assert payload["summary"]["gates"]["F0_integrity"]["integrity_manifest_valid"]
    assert all(
        row["random_schedule_id"] == row["false_calm_random_schedule_id"]
        for row in rows
    )


def test_none_is_a_true_second_shift_floor(payload: dict[str, Any]) -> None:
    none_rows = [row for row in payload["rows"] if row["arm"] == "T_none"]
    assert len(none_rows) == len(DEFAULT_SEEDS)
    assert all(row["latency"] == 12 for row in none_rows)
    assert all(not row["terminal_pass"] for row in none_rows)
    assert all(row["affected_post_second_probes"] == 0 for row in none_rows)
    assert payload["summary"]["gates"]["F5_none_floor"]["pass"]


def test_false_calm_uses_open_window_occupancy(payload: dict[str, Any]) -> None:
    periodic = [row for row in payload["rows"] if row["arm"] == "T_periodic"]
    commit = [row for row in payload["rows"] if row["arm"] == "T_commit"]

    assert all(row["false_reopen_rate"] == pytest.approx(8 / 12) for row in periodic)
    assert all(row["false_reopen_rate"] == pytest.approx(0.0) for row in commit)


def test_arm_execution_order_cannot_change_rows(calibration: dict[str, Any]) -> None:
    forward = run_m5_suite(seeds=DEFAULT_SEEDS[:2], calibration=calibration)
    reverse = run_m5_suite(
        seeds=DEFAULT_SEEDS[:2], calibration=calibration, arms=tuple(reversed(ARMS))
    )

    forward_rows = sorted(forward["rows"], key=lambda row: (row["seed"], row["arm"]))
    reverse_rows = sorted(reverse["rows"], key=lambda row: (row["seed"], row["arm"]))
    assert forward_rows == reverse_rows


def test_integrity_gate_fails_closed_on_one_probe_mismatch(
    payload: dict[str, Any],
) -> None:
    rows = deepcopy(payload["rows"])
    rows[0]["total_probes"] += 1
    summary = evaluate_gates(
        rows,
        payload["reference_suite"],
        DEFAULT_SEEDS,
        payload["calibration"],
        deterministic_replay=True,
    )

    assert not summary["gates"]["F0_integrity"]["pass"]
    assert summary["strict_verdict"] == "FAIL"


def test_integrity_gate_keeps_final_row_floats_exact(
    payload: dict[str, Any],
) -> None:
    rows = deepcopy(payload["rows"])
    rows[0]["final_mae"] += 1e-13
    summary = evaluate_gates(
        rows,
        payload["reference_suite"],
        DEFAULT_SEEDS,
        payload["calibration"],
        deterministic_replay=True,
    )

    assert not summary["gates"]["F0_integrity"]["integrity_manifest_valid"]
    assert summary["strict_verdict"] == "FAIL"


def test_integrity_gate_fails_closed_on_missing_arm(payload: dict[str, Any]) -> None:
    rows = deepcopy(payload["rows"][:-1])
    summary = evaluate_gates(
        rows,
        payload["reference_suite"],
        DEFAULT_SEEDS,
        payload["calibration"],
        deterministic_replay=True,
    )

    assert not summary["gates"]["F0_integrity"]["pass"]
    assert not summary["gates"]["F0_integrity"]["complete_grid"]
    assert not summary["gates"]["F1_commit_8_of_8"]["evaluated"]
    assert summary["strict_verdict"] == "FAIL"


def test_integrity_gate_rejects_self_signed_replacement_calibration(
    payload: dict[str, Any],
) -> None:
    replacement = deepcopy(payload["calibration"])
    replacement["thresholds"]["T_norm"] += 1.0
    core = {key: value for key, value in replacement.items() if key != "receipt_sha256"}
    replacement["receipt_sha256"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    summary = evaluate_gates(
        payload["rows"],
        payload["reference_suite"],
        DEFAULT_SEEDS,
        replacement,
        deterministic_replay=True,
    )

    assert not summary["gates"]["F0_integrity"]["calibration_receipt_valid"]
    assert summary["strict_verdict"] == "FAIL"


def test_integrity_gate_rejects_non_frozen_seed_grid(
    payload: dict[str, Any],
) -> None:
    reduced_seeds = DEFAULT_SEEDS[:2]
    rows = [row for row in payload["rows"] if int(row["seed"]) in reduced_seeds]
    summary = evaluate_gates(
        rows,
        payload["reference_suite"],
        reduced_seeds,
        payload["calibration"],
        deterministic_replay=True,
    )

    assert summary["gates"]["F0_integrity"]["complete_grid"]
    assert not summary["gates"]["F0_integrity"]["frozen_seed_grid"]
    assert summary["strict_verdict"] == "FAIL"


def test_integrity_gate_rejects_non_frozen_config(payload: dict[str, Any]) -> None:
    summary = evaluate_gates(
        payload["rows"],
        payload["reference_suite"],
        DEFAULT_SEEDS,
        payload["calibration"],
        deterministic_replay=True,
        cfg=replace(DEFAULT_CONFIG, recovery_threshold=0.13),
    )

    assert not summary["gates"]["F0_integrity"]["frozen_config"]
    assert summary["strict_verdict"] == "FAIL"


def test_custom_artifact_paths_are_recorded_in_the_rerun_command(
    calibration: dict[str, Any], tmp_path: Path
) -> None:
    custom = run_m5_suite(
        seeds=DEFAULT_SEEDS[:1],
        calibration=calibration,
        out=tmp_path / "raw.json",
        summary_json=tmp_path / "public.json",
        summary_md=tmp_path / "public.md",
    )
    command = custom["manifest"]["command"]

    assert f"--out {tmp_path / 'raw.json'}" in command
    assert f"--summary-json {tmp_path / 'public.json'}" in command
    assert f"--summary-md {tmp_path / 'public.md'}" in command


def test_canonical_result_preserves_the_frozen_strict_verdict(
    payload: dict[str, Any],
) -> None:
    summary = payload["summary"]
    assert summary["strict_verdict"] == "FAIL"
    assert {name: gate["pass"] for name, gate in summary["gates"].items()} == {
        "F0_integrity": True,
        "F1_commit_8_of_8": True,
        "F2_latency_dominance": False,
        "F3_specificity": False,
        "F4_joint_non_domination": True,
        "F5_none_floor": True,
    }
    assert (
        summary["gates"]["F2_latency_dominance"]["contrasts"]["T_periodic"][
            "median_internal_minus_commit"
        ]
        == 0.0
    )
    assert (
        summary["gates"]["F3_specificity"]["contrasts"]["T_norm"][
            "internal_minus_commit"
        ]
        == 0.0
    )


def test_artifact_writes_are_byte_idempotent(
    payload: dict[str, Any], tmp_path: Path
) -> None:
    raw = tmp_path / "raw.json"
    public_json = tmp_path / "summary.json"
    public_md = tmp_path / "summary.md"
    write_artifacts(payload, out=raw, summary_json=public_json, summary_md=public_md)
    first = (raw.read_bytes(), public_json.read_bytes(), public_md.read_bytes())
    write_artifacts(payload, out=raw, summary_json=public_json, summary_md=public_md)

    assert first == (raw.read_bytes(), public_json.read_bytes(), public_md.read_bytes())
    public = json.loads(public_json.read_text())
    for raw_only_key in (
        "factorial_rows",
        "rows",
        "probe_plans",
        "reference_suite",
        "probe_trace",
        "trigger_events",
    ):
        assert raw_only_key not in public
