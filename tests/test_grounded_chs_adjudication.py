from __future__ import annotations

from pathlib import Path

import pytest

from experiments.grounded_statecharts.chs_adjudication import (
    INJECTED_SEAL_PROTOCOL_VERSION,
    PROTOCOL_VERSION,
    generate_injected_results,
    seal_from_injected_faults,
    seal_from_paired_contrasts,
    summarize_combined_coverage,
)
from experiments.grounded_statecharts.counterfactual_search import (
    COMPONENTS,
    CounterfactualHarnessPilot,
    FaultCase,
)
from experiments.grounded_statecharts.evaluation import (
    LiveEpisode,
    harness_digest_for,
    public_rows,
    run_episode,
    smoke_tasks,
)
from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET

INJECTED_FAULT_CASES = FaultCase.load_many(
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "grounded_statecharts"
    / "fixtures"
    / "counterfactual_faults.json"
)


def _row(*, task, condition: str, seed: int) -> dict:
    episode = LiveEpisode(
        episode_id=f"ep-{task.task_id}-{condition}",
        run_id="chs-adj",
        task=task,
        condition=condition,
        repeat_index=0,
        model_id="fixture-deterministic-v1",
        provider_id="fixture",
        adapter_id="fixture",
        harness_digest=harness_digest_for(condition),
        budget=DEFAULT_PILOT_BUDGET,
        seed=seed,
    )
    return run_episode(episode).public_row


def test_paired_contrast_seals_orchestration_without_heuristic() -> None:
    artifact = next(task for task in smoke_tasks() if task.family == "artifact_completion")
    constraint = next(
        task for task in smoke_tasks() if task.family == "recursive_constrained_tool_use"
    )
    rows = [
        _row(task=artifact, condition="statechart_g0", seed=1),
        _row(task=artifact, condition="statechart_g3", seed=1),
        _row(task=constraint, condition="envelope_only", seed=2),
        _row(task=constraint, condition="envelope_external_guards", seed=2),
        _row(task=artifact, condition="wrong_edge_guard", seed=3),
    ]
    # Under harness-v2, G0 false completion may be repaired only on G3; fixture
    # already encodes that pattern. External enforcement may recover envelope fails.
    sealed = seal_from_paired_contrasts(rows)
    assert sealed
    assert all(item["protocol_version"] == PROTOCOL_VERSION for item in sealed)
    assert all(item["label_status"] == "sealed_by_paired_contrast" for item in sealed)
    assert "predicted_component" not in sealed[0]
    components = {item["responsible_component"] for item in sealed}
    assert components <= {"orchestration", "output"}


def test_public_rows_never_carry_sealed_labels() -> None:
    rows = public_rows(
        [
            run_episode(
                LiveEpisode(
                    episode_id="no-label",
                    run_id="chs-adj",
                    task=smoke_tasks()[0],
                    condition="statechart_g0",
                    repeat_index=0,
                    model_id="fixture-deterministic-v1",
                    provider_id="fixture",
                    adapter_id="fixture",
                    harness_digest=harness_digest_for("statechart_g0"),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=9,
                )
            )
        ]
    )
    assert "responsible_component" not in rows[0]
    assert "predicted_component" not in rows[0]


def test_injected_fault_seal_covers_all_six_surfaces_independently_of_live_rows() -> None:
    sealed = seal_from_injected_faults(INJECTED_FAULT_CASES)
    assert len(sealed) == len(INJECTED_FAULT_CASES) == 6
    assert {item["responsible_component"] for item in sealed} == set(COMPONENTS)
    assert all(
        item["protocol_version"] == INJECTED_SEAL_PROTOCOL_VERSION for item in sealed
    )
    assert all(
        item["label_status"] == "sealed_by_injected_fault_construction" for item in sealed
    )
    # Ground truth is the fixture's declared component, not a heuristic-harvest
    # prediction: no candidate/heuristic vocabulary should leak into the seal.
    assert all("predicted_component" not in item for item in sealed)
    assert all("heuristic_rule" not in item for item in sealed)


def test_injected_fault_seal_abstains_when_search_recovery_is_ambiguous() -> None:
    class _AmbiguousResult:
        counterfactual_repair_success = True
        placebo_credit = False
        recovered_component = None  # search could not credit a unique repair

    class _StubPilot:
        def run(self, case: FaultCase) -> _AmbiguousResult:
            return _AmbiguousResult()

    sealed = seal_from_injected_faults(INJECTED_FAULT_CASES, pilot=_StubPilot())
    assert sealed == []


def test_injected_fault_seal_abstains_when_repair_fails_or_placebo_credited() -> None:
    class _UnrepairedResult:
        counterfactual_repair_success = False
        placebo_credit = False
        recovered_component = None

    class _PlaceboCreditedResult:
        counterfactual_repair_success = True
        placebo_credit = True
        recovered_component = "context"

    class _StubPilot:
        def __init__(self, result: object) -> None:
            self._result = result

        def run(self, case: FaultCase) -> object:
            return self._result

    case = INJECTED_FAULT_CASES[0]
    assert seal_from_injected_faults([case], pilot=_StubPilot(_UnrepairedResult())) == []
    assert seal_from_injected_faults([case], pilot=_StubPilot(_PlaceboCreditedResult())) == []


def test_injected_fault_seal_matches_direct_pilot_run() -> None:
    pilot = CounterfactualHarnessPilot()
    sealed = seal_from_injected_faults(INJECTED_FAULT_CASES, pilot=pilot)
    by_fault = {item["fault_id"]: item for item in sealed}
    for case in INJECTED_FAULT_CASES:
        result = pilot.run(case)
        assert by_fault[case.fault_id]["responsible_component"] == result.recovered_component


def test_generate_injected_results_refuses_artifacts_output_dir(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="artifacts"):
        generate_injected_results(output_dir=tmp_path / "artifacts" / "chs_injected_faults")


def test_generate_injected_results_writes_public_safe_summary_under_results(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "results" / "chs_injected_faults"
    summary = generate_injected_results(output_dir=out_dir)
    assert summary["gates"]["six_surface_chs1_claim"] is False
    assert summary["gates"]["heuristic_harvest_not_used"] is True
    assert set(summary["components_covered"]) == set(COMPONENTS)
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "labels.jsonl").exists()


def test_combined_coverage_reports_tiers_without_claiming_six_surface_chs1() -> None:
    live_sealed = seal_from_paired_contrasts(
        [
            _row(
                task=next(
                    task for task in smoke_tasks() if task.family == "artifact_completion"
                ),
                condition="wrong_edge_guard",
                seed=3,
            )
        ]
    )
    injected_sealed = seal_from_injected_faults(INJECTED_FAULT_CASES)
    coverage = summarize_combined_coverage(live_sealed, injected_sealed)
    assert coverage["live_paired_contrast_components"] == ["output"]
    assert set(coverage["injected_fault_seal_components"]) == set(COMPONENTS)
    assert set(coverage["any_tier_sealed_components"]) == set(COMPONENTS)
    assert coverage["six_surface_any_tier_protocol_coverage"] is True
    # The combined view must never upgrade to a real six-surface CHS1 claim.
    assert coverage["six_surface_live_withheld_chs1"] is False


def test_injected_seal_extends_counterfactual_search_types_directly() -> None:
    # The injected tier must reuse counterfactual_search.py's FaultCase and
    # CounterfactualHarnessPilot directly rather than redefining a parallel
    # fault-case type or evaluator.
    import experiments.grounded_statecharts.chs_adjudication as chs_adjudication
    import experiments.grounded_statecharts.counterfactual_search as counterfactual_search

    assert chs_adjudication.FaultCase is counterfactual_search.FaultCase
    assert chs_adjudication.CounterfactualHarnessPilot is counterfactual_search.CounterfactualHarnessPilot
    assert chs_adjudication.COMPONENTS is counterfactual_search.COMPONENTS
