from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.grounded_statecharts.chs_repair_search import (
    DEFAULT_CASES,
    WITHHELD_SEAL_PROTOCOL_VERSION,
    WithheldSealedLabel,
    generate_withheld_results,
    generate_withheld_seals,
    score_withheld_repair_search,
    seal_withheld_labels,
)
from experiments.grounded_statecharts.counterfactual_search import (
    COMPONENTS,
    BlindCounterfactualHarnessPilot,
    BlindFaultCase,
    BlindSearchResult,
    CounterfactualHarnessPilot,
    FaultCase,
)

CASES = FaultCase.load_many(DEFAULT_CASES)


def test_blind_fault_case_and_result_have_no_responsible_component_attribute() -> None:
    # The core structural guarantee: the types the search consumes and
    # returns cannot carry a ground-truth label because neither defines one.
    assert "responsible_component" not in BlindFaultCase.__dataclass_fields__
    assert "responsible_component" not in BlindSearchResult.__dataclass_fields__
    blind_case = BlindFaultCase.from_fault_case(CASES[0])
    assert not hasattr(blind_case, "responsible_component")
    result = BlindCounterfactualHarnessPilot().run(blind_case)
    assert not hasattr(result, "responsible_component")


def test_blind_pilot_matches_original_pilot_on_every_fixture() -> None:
    # The blind search must be the *same* equal-budget repair/placebo
    # search, not a weaker stand-in: its behavioral output must match the
    # original pilot's exactly, case by case.
    original_pilot = CounterfactualHarnessPilot()
    blind_pilot = BlindCounterfactualHarnessPilot()
    for case in CASES:
        original = original_pilot.run(case)
        blind = blind_pilot.run(BlindFaultCase.from_fault_case(case))
        assert blind.fault_id == original.fault_id
        assert blind.recovered_component == original.recovered_component
        assert blind.evaluation_budget == original.evaluation_budget
        assert blind.counterfactual_repair_success == original.counterfactual_repair_success
        assert blind.trace_repair_success == original.trace_repair_success
        assert blind.noop_identity == original.noop_identity
        assert blind.placebo_credit == original.placebo_credit
        assert blind.original_outcome == original.original_outcome
        assert [i.to_dict() for i in blind.interventions] == [
            i.to_dict() for i in original.interventions
        ]


def test_seal_withheld_labels_covers_all_six_surfaces() -> None:
    sealed = seal_withheld_labels(CASES)
    assert len(sealed) == 6
    assert {row["responsible_component"] for row in sealed} == set(COMPONENTS)
    assert all(row["protocol_version"] == WITHHELD_SEAL_PROTOCOL_VERSION for row in sealed)
    assert all(row["label_status"] == "sealed_withheld_at_score_time" for row in sealed)


def test_withheld_sealed_label_loader_rejects_unknown_protocol_version(tmp_path: Path) -> None:
    bad_path = tmp_path / "labels.jsonl"
    bad_path.write_text(
        json.dumps(
            {
                "case_id": "withheld-seal:x",
                "fault_id": "fault-context-summary-drop",
                "responsible_component": "context",
                "protocol_version": "not-the-real-version",
                "label_status": "sealed_withheld_at_score_time",
            }
        )
        + "\n"
    )
    with pytest.raises(ValueError, match="protocol version"):
        WithheldSealedLabel.load_many(bad_path)


def test_withheld_sealed_label_loader_rejects_missing_surface_coverage(tmp_path: Path) -> None:
    sealed = seal_withheld_labels(CASES)
    incomplete_path = tmp_path / "labels.jsonl"
    incomplete_path.write_text(
        "".join(json.dumps(row) + "\n" for row in sealed[:-1])
    )
    with pytest.raises(ValueError, match="every harness surface"):
        WithheldSealedLabel.load_many(incomplete_path)


def test_generate_withheld_seals_refuses_artifacts_output_dir(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="artifacts"):
        generate_withheld_seals(output_dir=tmp_path / "artifacts" / "chs_withheld_seals")


def test_generate_withheld_seals_writes_public_safe_bundle(tmp_path: Path) -> None:
    out_dir = tmp_path / "results" / "chs_withheld_seals"
    summary = generate_withheld_seals(output_dir=out_dir)
    assert all(summary["gates"].values())
    assert set(summary["components_covered"]) == set(COMPONENTS)
    assert (out_dir / "labels.jsonl").exists()
    assert (out_dir / "summary.json").exists()


def test_score_withheld_repair_search_matches_sealed_labels(tmp_path: Path) -> None:
    seal_dir = tmp_path / "results" / "chs_withheld_seals"
    generate_withheld_seals(output_dir=seal_dir)
    sealed_labels = WithheldSealedLabel.load_many(seal_dir / "labels.jsonl")

    rows = score_withheld_repair_search(sealed_labels, CASES)
    assert len(rows) == 6
    assert all(row["withheld_top1_correct"] for row in rows)
    assert all(row["counterfactual_repair_success"] for row in rows)
    assert not any(row["placebo_credit"] for row in rows)
    for row in rows:
        assert row["equal_budget_repair_vs_placebo"] is True
        assert row["placebo_arm_cost"] == 1
        assert set(row["repair_arm_costs"].values()) == {1}
        assert row["total_arms"] == len(COMPONENTS) + 1


def test_score_withheld_repair_search_raises_on_missing_case_coverage() -> None:
    seal_dir_labels = [
        {
            "case_id": f"withheld-seal:{case.fault_id}",
            "fault_id": case.fault_id,
            "responsible_component": case.responsible_component,
            "protocol_version": WITHHELD_SEAL_PROTOCOL_VERSION,
            "label_status": "sealed_withheld_at_score_time",
        }
        for case in CASES
    ]
    sealed = tuple(
        WithheldSealedLabel(row["fault_id"], row["responsible_component"])
        for row in seal_dir_labels
        if row["fault_id"] != CASES[0].fault_id
    )
    with pytest.raises(ValueError, match="missing a withheld sealed label"):
        score_withheld_repair_search(sealed, CASES)


def test_generate_withheld_results_writes_public_safe_bundle_and_passes_all_gates(
    tmp_path: Path,
) -> None:
    seal_dir = tmp_path / "results" / "chs_withheld_seals"
    generate_withheld_seals(output_dir=seal_dir)

    out_dir = tmp_path / "results" / "chs_withheld_seal_search"
    summary = generate_withheld_results(
        sealed_labels_path=seal_dir / "labels.jsonl", output_dir=out_dir
    )
    assert all(summary["gates"].values())
    assert summary["metrics"]["withheld_top1_attribution"] == 1.0
    assert summary["metrics"]["placebo_false_credit_rate"] == 0.0
    assert summary["metrics"]["mean_evaluation_budget"] == 7.0
    assert any("CHS1" in claim for claim in summary["non_claims"])

    rows = [json.loads(line) for line in (out_dir / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 6
    assert {row["fault_id"] for row in rows} == {case.fault_id for case in CASES}
    assert (out_dir / "summary.json").exists()


def test_generate_withheld_results_refuses_artifacts_output_dir(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="artifacts"):
        generate_withheld_results(output_dir=tmp_path / "artifacts" / "chs_withheld_seal_search")


def test_generate_withheld_results_raises_when_search_disagrees_with_a_sealed_label(
    tmp_path: Path,
) -> None:
    seal_dir = tmp_path / "results" / "chs_withheld_seals"
    generate_withheld_seals(output_dir=seal_dir)
    rows = [
        json.loads(line)
        for line in (seal_dir / "labels.jsonl").read_text().splitlines()
        if line.strip()
    ]
    first, second = dict(rows[0]), dict(rows[1])
    first["responsible_component"], second["responsible_component"] = (
        second["responsible_component"],
        first["responsible_component"],
    )
    corrupted_path = tmp_path / "corrupted_labels.jsonl"
    corrupted_path.write_text(
        "".join(json.dumps(row) + "\n" for row in ([first, second] + rows[2:]))
    )
    with pytest.raises(RuntimeError, match="gates failed"):
        generate_withheld_results(
            sealed_labels_path=corrupted_path,
            output_dir=tmp_path / "results" / "chs_withheld_seal_search",
        )
