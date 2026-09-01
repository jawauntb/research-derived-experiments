from __future__ import annotations

import json
from pathlib import Path

from experiments.evidence_worlds.evaluation.pilot_readiness import (
    GateEvidence,
    _world_result,
    evaluate_pilot,
    write_report,
)


def test_real_world_evaluation_passes_all_controls_and_fatal_gates() -> None:
    report = evaluate_pilot()

    assert report["evaluation_mode"] == "offline_deterministic"
    assert report["pilot_ready"] is True
    assert report["decision"] == "READY_FOR_BOUNDED_PILOT"
    assert {world["world_id"] for world in report["worlds"]} == {
        "arc-vcc",
        "open-targets",
        "clinical-trials-sec",
    }
    for world in report["worlds"]:
        assert world["status"] == "PASS"
        assert all(gate["status"] == "PASS" for gate in world["fatal_gates"])
        assert all(control["passed"] for control in world["controls"])
        assert {control["kind"] for control in world["controls"]} == {
            "positive",
            "negative",
            "null",
            "corruption",
            "cross_world",
        }


def test_deferred_worlds_are_explicitly_excluded() -> None:
    report = evaluate_pilot()
    deferred = {item["world_id"]: item for item in report["deferred_worlds"]}

    assert set(deferred) == {"flywire-codex", "neurovault"}
    assert all(item["status"] == "DEFERRED" for item in deferred.values())
    assert all(item["world_id"] not in {w["world_id"] for w in report["worlds"]} for item in report["deferred_worlds"])


def test_fatal_gate_is_noncompensatory() -> None:
    result = _world_result(
        "example",
        {"version": "1"},
        [],
        [GateEvidence("required_gate", "FAIL", "fixture was tampered")],
        {},
    )

    assert result["status"] == "FAIL"


def test_evaluation_and_report_are_stable(tmp_path: Path) -> None:
    first = evaluate_pilot()
    second = evaluate_pilot()
    assert first == second

    written = write_report(tmp_path)
    assert written == first
    assert json.loads((tmp_path / "pilot_readiness.json").read_text(encoding="utf-8")) == first
    markdown = (tmp_path / "pilot_readiness.md").read_text(encoding="utf-8")
    assert "READY_FOR_BOUNDED_PILOT" in markdown
    assert "buyer_discovery" not in markdown
    assert "authenticity" in markdown
