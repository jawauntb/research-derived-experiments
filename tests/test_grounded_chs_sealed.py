from __future__ import annotations

import json

from experiments.grounded_statecharts.chs_sealed import generate_results


def test_chs_sealed_scores_clean_and_single_fault_cases(tmp_path) -> None:
    summary = generate_results(tmp_path)

    rows = [json.loads(line) for line in (tmp_path / "rows.jsonl").read_text().splitlines()]

    assert summary["gates"] == {
        "one_no_fault_case": True,
        "six_single_fault_cases": True,
        "sealed_fixture_alignment": True,
        "no_provider_calls": True,
    }
    assert summary["metrics"]["top1_attribution"] == 1.0
    assert len(rows) == 7
    assert next(row for row in rows if row["case_kind"] == "no_fault") == {
        "case_id": "clean-reference",
        "fault_id": None,
        "case_kind": "no_fault",
        "sealed_component": None,
        "predicted_component": None,
        "top1_correct": True,
        "counterfactual_repair_success": True,
        "evaluation_budget": 0,
    }
