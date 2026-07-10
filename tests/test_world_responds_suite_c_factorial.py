from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from experiments.world_responds.suite_c_contract import SuiteCMechanisms
from experiments.world_responds.suite_c_factorial_ablation import (
    DEFAULT_SEEDS,
    PRIMARY_METRIC,
    render_markdown,
    run_factorial_suite,
    run_factorial_trial,
    write_artifacts,
)
from experiments.world_responds.suite_c_reengagement import run_trial


@pytest.fixture(scope="module")
def factorial_payload() -> dict[str, Any]:
    return run_factorial_suite(seeds=DEFAULT_SEEDS)


def test_factorial_uses_complete_paired_existing_suite_harness(
    factorial_payload: dict[str, Any],
) -> None:
    rows = factorial_payload["factorial_rows"]
    summary = factorial_payload["summary"]

    assert len(rows) == 8 * len(DEFAULT_SEEDS)
    assert {row["seed"] for row in rows} == set(DEFAULT_SEEDS)
    assert all(row["base_condition"] == "burst_then_refractory" for row in rows)
    assert all(row["detect"] and row["saturate"] for row in rows)
    assert summary["gates"]["F0_integrity"]["pass"]
    assert summary["gates"]["F6_transported_controls"]["pass"]


def test_all_on_cell_is_exact_existing_policy_row() -> None:
    seed = DEFAULT_SEEDS[0]
    factorial = run_factorial_trial(seed, (True, True, True))
    reference = run_trial("burst_then_refractory", seed)

    for key, value in reference.items():
        if key == "condition":
            assert factorial["base_condition"] == value
        else:
            assert factorial[key] == value
    assert factorial[PRIMARY_METRIC] == reference["candidate_terminal_pass"]


def test_frozen_factorial_verdict_rejects_strong_m4_subset_claim(
    factorial_payload: dict[str, Any],
) -> None:
    summary = factorial_payload["summary"]
    gates = summary["gates"]
    effects = summary["factorial_effects"][PRIMARY_METRIC]

    assert summary["strict_verdict"] == "FAIL"
    assert gates["F1_full_loop_replication"]["pass"]
    assert not gates["F2_single_removal_necessity"]["pass"]
    assert not gates["F3_main_effects"]["pass"]
    assert gates["F4_interactions"]["pass"]
    assert not gates["F5_no_interaction_rescue"]["pass"]
    assert effects["reopen"]["effect"] == pytest.approx(1.0)
    assert effects["allocate"]["effect"] == pytest.approx(0.0)
    assert effects["cool"]["effect"] == pytest.approx(0.0)


def test_component_interventions_are_restricted_to_real_base_policy() -> None:
    with pytest.raises(ValueError, match="apply only to burst_then_refractory"):
        run_trial(
            "decision_refractory",
            DEFAULT_SEEDS[0],
            mechanisms=SuiteCMechanisms(cool=False),
        )


def test_artifact_writes_are_idempotent(
    factorial_payload: dict[str, Any], tmp_path: Path
) -> None:
    raw = tmp_path / "artifact.json"
    summary_json = tmp_path / "summary.json"
    summary_md = tmp_path / "summary.md"

    write_artifacts(
        factorial_payload,
        out=raw,
        summary_json=summary_json,
        summary_md=summary_md,
    )
    first = (raw.read_bytes(), summary_json.read_bytes(), summary_md.read_bytes())
    write_artifacts(
        factorial_payload,
        out=raw,
        summary_json=summary_json,
        summary_md=summary_md,
    )

    assert first == (raw.read_bytes(), summary_json.read_bytes(), summary_md.read_bytes())
    assert json.loads(summary_json.read_text())["strict_verdict"] == "FAIL"
    assert summary_md.read_text() == render_markdown(factorial_payload["summary"])


def test_factorial_rejects_underpowered_or_duplicate_seed_sets() -> None:
    with pytest.raises(ValueError, match="at least five"):
        run_factorial_suite(seeds=(1, 2, 3, 4))
    with pytest.raises(ValueError, match="must be unique"):
        run_factorial_suite(seeds=(1, 2, 3, 4, 4))
