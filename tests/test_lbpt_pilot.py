"""Tests for the pilot runner."""

from __future__ import annotations

import json
from pathlib import Path

from experiments.load_bearing_prose_test.executor import build_plan_executor
from experiments.load_bearing_prose_test.run_lbpt_pilot import (
    FIXTURE_FILES,
    PilotRow,
    build_pilot_output,
    write_pilot_output,
)


def test_pilot_runs_deterministically_over_both_families() -> None:
    executor = build_plan_executor(kind="fixture")
    rows_a, summary_a = build_pilot_output(executor=executor, seed=20260721)
    rows_b, summary_b = build_pilot_output(executor=executor, seed=20260721)
    # Compare row dicts (dataclass identity may differ across runs).
    assert [r.to_dict() for r in rows_a] == [r.to_dict() for r in rows_b]
    assert summary_a == summary_b


def test_pilot_output_covers_every_fixture_plan() -> None:
    executor = build_plan_executor(kind="fixture")
    rows, summary = build_pilot_output(executor=executor)
    plan_ids: set[str] = set()
    for name in FIXTURE_FILES:
        payload = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "experiments"
                / "load_bearing_prose_test"
                / "fixtures"
                / name
            ).read_text()
        )
        for plan in payload["plans"]:
            plan_ids.add(plan["plan_id"])
    observed = {row.plan_id for row in rows}
    assert observed == plan_ids
    assert summary["n_rows"] == len(rows)


def test_pilot_control_condition_is_zero_load_bearing_for_rct() -> None:
    """envelope_external_guards should rescue commitment surface fully for rct."""

    executor = build_plan_executor(kind="fixture")
    _, summary = build_pilot_output(executor=executor)
    rct = summary["families"]["recursive_constrained_tool_use"]
    assert rct["control"]["load_bearing_rate"] == 0.0
    # And the primary condition must not be zero — otherwise the substrate
    # can't distinguish load-bearing from inert claims at all.
    assert rct["primary"]["load_bearing_rate"] > 0.0


def test_pilot_row_serializes_all_declared_fields() -> None:
    row = PilotRow(
        family="artifact_completion",
        plan_id="ac001",
        plan_digest="0" * 64,
        claim_id="ac001::c001",
        claim_text="x",
        kappa_mention=False,
        primary_condition="statechart_g0",
        control_condition="statechart_g3",
        baseline_surface_digest="0" * 64,
        delete_delta=True,
        negate_delta=False,
        paraphrase_delta=False,
        is_load_bearing=True,
        paraphrase_invariant=True,
        control_delete_delta=True,
        control_negate_delta=False,
    )
    payload = row.to_dict()
    assert set(payload.keys()) == {
        "family",
        "plan_id",
        "plan_digest",
        "claim_id",
        "claim_text",
        "kappa_mention",
        "primary_condition",
        "control_condition",
        "baseline_surface_digest",
        "delete_delta",
        "negate_delta",
        "paraphrase_delta",
        "is_load_bearing",
        "paraphrase_invariant",
        "control_delete_delta",
        "control_negate_delta",
    }


def test_write_pilot_output_creates_rows_and_summary_files(tmp_path: Path) -> None:
    executor = build_plan_executor(kind="fixture")
    rows_path = tmp_path / "rows.jsonl"
    summary_path = tmp_path / "summary.json"
    written_rows, written_summary = write_pilot_output(
        executor=executor,
        rows_path=rows_path,
        summary_path=summary_path,
    )
    assert written_rows == rows_path
    assert written_summary == summary_path
    assert summary_path.read_text()
    lines = [line for line in rows_path.read_text().splitlines() if line]
    assert lines
    for line in lines:
        payload = json.loads(line)
        assert payload["family"] in {
            "artifact_completion",
            "recursive_constrained_tool_use",
        }
