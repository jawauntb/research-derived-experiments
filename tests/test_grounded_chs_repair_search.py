from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.grounded_statecharts.chs_repair_search import (
    DEFAULT_CASES,
    DEFAULT_FIXTURE_LABELS,
    DEFAULT_SEALED_LABELS,
    SealedInjectedLabel,
    generate_results,
    score_equal_budget_repair_search,
)
from experiments.grounded_statecharts.chs_sealed import SealedLabel
from experiments.grounded_statecharts.counterfactual_search import COMPONENTS, FaultCase

FIXTURE_LABELS = SealedLabel.load_many(DEFAULT_FIXTURE_LABELS)
CASES = FaultCase.load_many(DEFAULT_CASES)


def test_sealed_injected_label_loader_covers_all_six_surfaces() -> None:
    labels = SealedInjectedLabel.load_many(DEFAULT_SEALED_LABELS)
    assert len(labels) == 6
    assert {label.responsible_component for label in labels} == set(COMPONENTS)


def test_sealed_injected_label_loader_rejects_unknown_protocol_version(tmp_path: Path) -> None:
    bad_path = tmp_path / "labels.jsonl"
    bad_path.write_text(
        json.dumps(
            {
                "case_id": "seal:x",
                "fault_id": "fault-context-summary-drop",
                "responsible_component": "context",
                "protocol_version": "not-the-real-version",
                "label_status": "sealed_by_injected_fault_construction",
            }
        )
        + "\n"
    )
    with pytest.raises(ValueError, match="protocol version"):
        SealedInjectedLabel.load_many(bad_path)


def test_sealed_injected_label_loader_rejects_missing_surface_coverage(tmp_path: Path) -> None:
    rows = [
        json.loads(line)
        for line in DEFAULT_SEALED_LABELS.read_text().splitlines()
        if line.strip()
    ]
    incomplete_path = tmp_path / "labels.jsonl"
    incomplete_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows[:-1])
    )
    with pytest.raises(ValueError, match="every harness surface"):
        SealedInjectedLabel.load_many(incomplete_path)


def test_score_equal_budget_repair_search_matches_both_label_sources() -> None:
    sealed_labels = SealedInjectedLabel.load_many(DEFAULT_SEALED_LABELS)
    rows = score_equal_budget_repair_search(sealed_labels, FIXTURE_LABELS, CASES)
    assert len(rows) == 6
    assert all(row["sealed_top1_correct"] for row in rows)
    assert all(row["fixture_top1_correct"] for row in rows)
    assert all(row["label_sources_agree"] for row in rows)
    assert all(row["counterfactual_repair_success"] for row in rows)
    assert not any(row["placebo_credit"] for row in rows)
    # Equal budget: every repair arm and the placebo arm cost exactly 1, so no
    # arm gets a search advantage over any other.
    for row in rows:
        assert row["equal_budget_repair_vs_placebo"] is True
        assert row["placebo_arm_cost"] == 1
        assert set(row["repair_arm_costs"].values()) == {1}
        assert row["total_arms"] == len(COMPONENTS) + 1


def test_score_equal_budget_repair_search_raises_on_missing_case_coverage() -> None:
    sealed_labels = SealedInjectedLabel.load_many(DEFAULT_SEALED_LABELS)
    sealed_missing = tuple(
        label for label in sealed_labels if label.fault_id != CASES[0].fault_id
    )
    with pytest.raises(ValueError, match="missing a sealed injected label"):
        score_equal_budget_repair_search(sealed_missing, FIXTURE_LABELS, CASES)
    # Drop one case's fixture label but keep every sealed label -- must raise,
    # not silently score five of six surfaces.
    fixture_missing = tuple(
        label for label in FIXTURE_LABELS if label.fault_id != CASES[0].fault_id
    )
    with pytest.raises(ValueError, match="missing a fixture label"):
        score_equal_budget_repair_search(sealed_labels, fixture_missing, CASES)


def test_generate_results_writes_public_safe_bundle_and_passes_all_gates(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "results" / "chs_repair_search"
    summary = generate_results(output_dir=out_dir)

    assert all(summary["gates"].values())
    assert summary["metrics"]["sealed_top1_attribution"] == 1.0
    assert summary["metrics"]["fixture_top1_attribution"] == 1.0
    assert summary["metrics"]["placebo_false_credit_rate"] == 0.0
    assert summary["metrics"]["mean_evaluation_budget"] == 7.0
    assert "not CHS1" in summary["allowed_claim"] or any(
        "CHS1" in claim for claim in summary["non_claims"]
    )

    rows = [json.loads(line) for line in (out_dir / "rows.jsonl").read_text().splitlines()]
    assert len(rows) == 6
    assert {row["fault_id"] for row in rows} == {case.fault_id for case in CASES}
    assert (out_dir / "summary.json").exists()


def test_generate_results_refuses_artifacts_output_dir(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="artifacts"):
        generate_results(output_dir=tmp_path / "artifacts" / "chs_repair_search")


def test_generate_results_raises_when_a_fresh_search_disagrees_with_a_sealed_label(
    tmp_path: Path,
) -> None:
    # Swap responsible_component between two sealed rows so surface coverage
    # (the loader's own gate) is untouched, but each row's fault_id/component
    # pairing no longer matches what a fresh equal-budget search recovers.
    # The runner must fail its gates rather than silently publish a
    # mismatched attribution as passing.
    rows = [
        json.loads(line)
        for line in DEFAULT_SEALED_LABELS.read_text().splitlines()
        if line.strip()
    ]
    first, second = dict(rows[0]), dict(rows[1])
    first["responsible_component"], second["responsible_component"] = (
        second["responsible_component"],
        first["responsible_component"],
    )
    corrupted_path = tmp_path / "labels.jsonl"
    corrupted_path.write_text(
        "".join(json.dumps(row) + "\n" for row in ([first, second] + rows[2:]))
    )
    with pytest.raises(RuntimeError, match="gates failed"):
        generate_results(
            sealed_labels_path=corrupted_path, output_dir=tmp_path / "results" / "chs_repair_search"
        )
