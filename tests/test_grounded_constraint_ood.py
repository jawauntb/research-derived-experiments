from __future__ import annotations

import json

import pytest

from experiments.grounded_statecharts.constraint_ood import (
    OOD_KILL_THRESHOLD,
    ParaphraseCase,
    generate_results,
    run_deeper_delegation_depth_probe,
    run_held_out_paraphrase_probe,
)


def test_generate_results_runs_both_probes_on_fixture_only(tmp_path) -> None:
    summary = generate_results(tmp_path)

    assert all(summary["gates"].values())
    assert summary["probes"]["held_out_paraphrase"]["adapter_id"] == "fixture"
    assert summary["probes"]["held_out_paraphrase"]["provider_failures"] == []
    assert summary["kill_criteria"]["threshold"] == OOD_KILL_THRESHOLD

    paraphrase_rows = [
        json.loads(line)
        for line in (tmp_path / "paraphrase_rows.jsonl").read_text().splitlines()
    ]
    depth_rows = [
        json.loads(line) for line in (tmp_path / "depth_rows.jsonl").read_text().splitlines()
    ]
    assert len(paraphrase_rows) == 8  # 4 tasks x 2 conditions
    assert {row["condition"] for row in paraphrase_rows} == {
        "envelope_only",
        "envelope_external_guards",
    }
    assert len(depth_rows) == 8  # 2 depths x 2 conditions x 2 task families


def test_held_out_paraphrase_probe_preserves_check_spec_identity() -> None:
    result = run_held_out_paraphrase_probe(adapter_id="fixture")

    assert result["preserves_constraint_identity"] is True
    assert result["family"] == "recursive_constrained_tool_use"
    # Fixture executor never reads instruction text, so the mechanics-only
    # delta is guaranteed to be the trivial 1.0 -- this locks that fact down
    # so a future change to FixtureExecutor's behavior would be caught here.
    assert result["joint_success_effect"]["point_estimate"] == 1.0


def test_paraphrase_cases_load_and_reject_duplicates(tmp_path) -> None:
    cases = ParaphraseCase.load_many()
    assert len(cases) >= 4
    assert len({case.task_id for case in cases}) == len(cases)

    duplicate_path = tmp_path / "dupes.json"
    duplicate_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "cases": [
                    {"task_id": "a", "paraphrased_instruction": "one"},
                    {"task_id": "a", "paraphrased_instruction": "two"},
                ],
            }
        )
    )
    with pytest.raises(ValueError, match="unique"):
        ParaphraseCase.load_many(duplicate_path)


def test_deeper_delegation_depth_probe_exceeds_committed_ceiling() -> None:
    result = run_deeper_delegation_depth_probe()

    assert result["depths"] == [5, 6]
    assert min(result["depths"]) > 4
    assert result["typed_lineage_valid_beyond_ceiling"] is True
    assert result["typed_constraint_survival_beyond_ceiling"] is True
    assert result["kill_triggered"] is False
    assert result["joint_success_delta"] == pytest.approx(1.0)


def test_deeper_delegation_depth_probe_rejects_committed_depths() -> None:
    with pytest.raises(ValueError, match="beyond the committed ceiling"):
        run_deeper_delegation_depth_probe(depths=(1, 2))
