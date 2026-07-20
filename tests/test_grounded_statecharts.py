from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from experiments.grounded_statecharts.run_fixture import generate_results
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
