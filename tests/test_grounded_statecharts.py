from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from experiments.grounded_statecharts.constraint_transport import (
    ConstraintEnvelope,
    ConstraintTransportBenchmark,
    TransportTask,
    tamper_controls,
    validate_lineage,
)
from experiments.grounded_statecharts.counterfactual_search import (
    COMPONENTS,
    CounterfactualHarnessPilot,
    DeterministicHarnessEvaluator,
    FaultCase,
    HarnessConfig,
)
from experiments.grounded_statecharts.run_counterfactual_search import (
    generate_results as generate_counterfactual_results,
)
from experiments.grounded_statecharts.run_constraint_transport import (
    generate_results as generate_transport_results,
)
from experiments.grounded_statecharts.run_fixture import generate_results
from experiments.grounded_statecharts.harness_unlearning import (
    MemoryLedger,
    MemoryStatus,
    evaluate_causal_use,
)
from experiments.grounded_statecharts.run_harness_unlearning import (
    generate_results as generate_unlearning_results,
)
from experiments.grounded_statecharts.runtime import Fixture, HarnessManifest, ReplayEngine


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "experiments" / "grounded_statecharts"


def load_inputs() -> tuple[Fixture, HarnessManifest, HarnessManifest]:
    fixture = Fixture.load(PACKAGE_ROOT / "fixtures" / "false_success.json")
    original = HarnessManifest.load(PACKAGE_ROOT / "manifests" / "self_report.json")
    guarded = HarnessManifest.load(PACKAGE_ROOT / "manifests" / "independent_artifact.json")
    return fixture, original, guarded


def test_noop_replay_is_exact_and_guard_prevents_false_completion() -> None:
    fixture, original_manifest, guarded_manifest = load_inputs()
    engine = ReplayEngine()
    checkpoint = engine.checkpoint_before_verification(fixture, original_manifest)

    original = engine.replay(checkpoint, fixture, original_manifest)
    noop = engine.replay(checkpoint, fixture, original_manifest)
    guarded = engine.replay(
        checkpoint,
        fixture,
        original_manifest,
        guarded_manifest,
    )

    assert original.events == noop.events
    assert original.to_dict() == noop.to_dict()
    assert original.false_completion is True
    assert guarded.false_completion is False
    assert guarded.task_success is True
    assert guarded.repair_count == 1
    assert [event.state_after for event in guarded.events][-4:] == [
        "repair",
        "act",
        "verify",
        "commit",
    ]


def test_counterfactual_replay_rejects_more_than_one_changed_component() -> None:
    fixture, original_manifest, guarded_manifest = load_inputs()
    with pytest.raises(ValueError, match="unsupported guard kind"):
        replace(
            guarded_manifest,
            guard={**guarded_manifest.guard, "kind": "unknown_guard"},
        )
    invalid_manifest = replace(guarded_manifest, version="2.0")
    checkpoint = ReplayEngine().checkpoint_before_verification(fixture, original_manifest)

    with pytest.raises(ValueError, match="exactly one changed component"):
        ReplayEngine().replay(
            checkpoint,
            fixture,
            original_manifest,
            invalid_manifest,
        )


def test_public_events_match_the_typed_schema_surface() -> None:
    fixture, original_manifest, guarded_manifest = load_inputs()
    engine = ReplayEngine()
    checkpoint = engine.checkpoint_before_verification(fixture, original_manifest)
    guarded = engine.replay(checkpoint, fixture, original_manifest, guarded_manifest)
    schema = json.loads((PACKAGE_ROOT / "schemas" / "event.schema.json").read_text())

    assert all(set(event.to_dict()) == set(schema["required"]) for event in guarded.events)
    guard_schema = schema["properties"]["guard_results"]["items"]["properties"]
    assert guard_schema["independence_level"]["type"] == "string"
    assert checkpoint.next_event_index == len(checkpoint.event_prefix)
    assert checkpoint.next_logical_timestamp == len(checkpoint.event_prefix)
    assert [event.event_index for event in guarded.events] == list(range(len(guarded.events)))
    assert [event.timestamp_logical for event in guarded.events] == list(
        range(len(guarded.events))
    )


def test_committed_replay_bundle_regenerates_byte_for_byte(tmp_path: Path) -> None:
    generate_results(tmp_path)

    for name in (
        "summary.json",
        "checkpoint.json",
        "original.jsonl",
        "noop_replay.jsonl",
        "guarded_replay.jsonl",
        "replay.html",
    ):
        assert (tmp_path / name).read_bytes() == (PACKAGE_ROOT / "results" / name).read_bytes()


def load_transport_tasks() -> tuple[TransportTask, ...]:
    return TransportTask.load_many(PACKAGE_ROOT / "fixtures" / "constraint_transport.json")


def test_typed_constraint_lineage_survives_four_levels_and_rejects_tampering() -> None:
    task = load_transport_tasks()[0]
    root = ConstraintEnvelope.root(
        envelope_id="env-test-root",
        objective=task.objective,
        constraints=(task.constraint,),
        capability_grants=task.capability_grants,
    )
    lineage = [root]
    for depth in range(1, 5):
        lineage.append(lineage[-1].derive(envelope_id=f"env-test-d{depth}"))

    schema = json.loads(
        (PACKAGE_ROOT / "schemas" / "constraint-envelope.schema.json").read_text()
    )
    assert validate_lineage(tuple(lineage)) is True
    assert all(set(envelope.to_dict()) == set(schema["required"]) for envelope in lineage)
    assert all(envelope.constraints == (task.constraint,) for envelope in lineage)
    assert all(tamper_controls(task).values())


def test_constraint_transport_reports_joint_success_separately_from_raw_utility() -> None:
    outcomes = ConstraintTransportBenchmark(load_transport_tasks()).run_all()
    typed = [outcome for outcome in outcomes if outcome.condition == "typed_guarded"]
    baseline = [outcome for outcome in outcomes if outcome.condition == "lossy_prompt"]

    assert len(outcomes) == 16
    assert {outcome.delegation_depth for outcome in outcomes} == {1, 2, 3, 4}
    assert all(outcome.task_success and outcome.joint_success for outcome in typed)
    assert all(not outcome.critical_violation for outcome in typed)
    assert all(outcome.task_success for outcome in baseline)
    assert sum(outcome.joint_success for outcome in baseline) == 2
    assert {
        outcome.first_loss_depth for outcome in baseline if outcome.delegation_depth > 1
    } == {2}


def test_committed_constraint_transport_bundle_regenerates_byte_for_byte(
    tmp_path: Path,
) -> None:
    summary = generate_transport_results(tmp_path)

    assert all(summary["gates"].values())
    for name in ("summary.json", "episodes.jsonl", "lineage.jsonl", "replay.html"):
        committed = PACKAGE_ROOT / "results" / "constraint_transport" / name
        assert (tmp_path / name).read_bytes() == committed.read_bytes()


def load_fault_cases() -> tuple[FaultCase, ...]:
    return FaultCase.load_many(PACKAGE_ROOT / "fixtures" / "counterfactual_faults.json")


def test_counterfactual_fault_fixtures_cover_surfaces_and_change_outcomes() -> None:
    cases = load_fault_cases()
    evaluator = DeterministicHarnessEvaluator()

    assert {case.responsible_component for case in cases} == set(COMPONENTS)
    for case in cases:
        assert evaluator.evaluate(case, HarnessConfig.clean()).joint_success is True
        assert (
            evaluator.evaluate(case, HarnessConfig.faulted(case)).joint_success is False
        )


def test_counterfactual_search_recovers_faults_and_beats_equal_budget_trace() -> None:
    results = CounterfactualHarnessPilot().run_all(load_fault_cases())

    assert len(results) == 6
    assert all(result.evaluation_budget == 7 for result in results)
    assert all(result.noop_identity and result.attribution_correct for result in results)
    assert all(result.counterfactual_repair_success for result in results)
    assert not any(result.trace_repair_success for result in results)
    assert not any(result.placebo_credit for result in results)
    assert all(sum(item.accepted_credit for item in result.interventions) == 1 for result in results)


def test_committed_counterfactual_search_bundle_regenerates_byte_for_byte(
    tmp_path: Path,
) -> None:
    summary = generate_counterfactual_results(tmp_path)

    assert all(summary["gates"].values())
    for name in ("summary.json", "cases.jsonl", "interventions.jsonl", "replay.html"):
        committed = PACKAGE_ROOT / "results" / "counterfactual_search" / name
        assert (tmp_path / name).read_bytes() == committed.read_bytes()


def test_memory_causal_use_requires_suppressing_declared_descendants() -> None:
    ledger, regimes = MemoryLedger.load(
        PACKAGE_ROOT / "fixtures" / "harness_unlearning.json"
    )
    gate = evaluate_causal_use(
        ledger,
        regimes["v3"],
        target_memory_id="mem-tool-v2",
        placebo_memory_id="mem-color-placebo",
    )

    assert gate.passed is True
    assert gate.observed.joint_success is False
    assert gate.target_only_suppressed.joint_success is False
    assert gate.target_family_suppressed.joint_success is True
    assert gate.placebo_suppressed == gate.observed


def test_memory_ledger_rejects_skipping_quarantine() -> None:
    ledger, _ = MemoryLedger.load(PACKAGE_ROOT / "fixtures" / "harness_unlearning.json")

    with pytest.raises(ValueError, match="illegal memory transition"):
        ledger.transition_family(
            "mem-tool-v2",
            MemoryStatus.RETIRED,
            reason="skip required influence gate",
            evidence_ref="test://invalid",
        )


def test_committed_harness_unlearning_bundle_regenerates_byte_for_byte(
    tmp_path: Path,
) -> None:
    summary = generate_unlearning_results(tmp_path)

    assert all(summary["gates"].values())
    for name in (
        "summary.json",
        "causal_use.json",
        "ledger.json",
        "events.jsonl",
        "phases.jsonl",
        "replay.html",
    ):
        committed = PACKAGE_ROOT / "results" / "harness_unlearning" / name
        assert (tmp_path / name).read_bytes() == committed.read_bytes()
