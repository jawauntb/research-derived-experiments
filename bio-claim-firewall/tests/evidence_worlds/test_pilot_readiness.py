from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from experiments.evidence_worlds.evaluation.pilot_readiness import (
    CLINICAL_REVIEW_PATH,
    CONTROL_CORPUS_PATH,
    FIXTURE_ROOT,
    MANIFEST_ROOT,
    SOURCE_TERMS_REVIEW_PATH,
    ControlResult,
    GateEvidence,
    _load_protocol,
    _world_result,
    evaluate_pilot,
    write_report,
)
from worlds import WorldRegistryError


def test_real_world_evaluation_passes_exact_nonempty_protocols() -> None:
    report = evaluate_pilot()

    assert report["evaluation_mode"] == "offline_deterministic_locked_controls"
    assert report["pilot_ready"] is True
    assert report["decision"] == "READY_FOR_BOUNDED_PILOT"
    assert all(report["readiness_requirements"].values())
    assert {world["world_id"] for world in report["worlds"]} == {
        "arc-vcc",
        "open-targets",
        "clinical-trials-sec",
    }
    for world in report["worlds"]:
        assert world["manifest_state"] == "ADMITTED"
        assert world["status"] == "PASS"
        assert world["protocol_exact"] is True
        assert len(world["fatal_gates"]) == 6
        assert len(world["controls"]) == 5
        assert all(gate["status"] == "PASS" for gate in world["fatal_gates"])
        assert all(control["passed"] for control in world["controls"])
        assert {control["kind"] for control in world["controls"]} == {
            "positive",
            "negative",
            "null",
            "corruption",
            "cross_world",
        }
        expected_artifacts = {
            "registry_sha256",
            "evaluator_sha256",
            "manifest_sha256",
            "fixture_corpus_sha256",
            "preregistration_sha256",
            "control_corpus_sha256",
            "source_terms_review_sha256",
        }
        if world["world_id"] == "clinical-trials-sec":
            expected_artifacts.add("clinical_review_sha256")
        assert set(world["artifacts"]) == expected_artifacts
        assert all(len(value) == 64 for value in world["artifacts"].values())
        negative = next(
            control for control in world["controls"] if control["kind"] == "negative"
        )
        assert negative["observed"] == "REJECTED"


def test_declared_scenario_locators_are_not_labeled_as_live_inspection() -> None:
    report = evaluate_pilot()
    worlds = {world["world_id"]: world for world in report["worlds"]}

    for world_id in ("clinical-trials-sec", "open-targets"):
        scenario = worlds[world_id]["inspectable_scenario"]
        assert scenario["status"] == "DECLARED"
        assert scenario["observed"] == "ACCEPTED"
        assert "does not retrieve" in scenario["scope_note"]
        assert scenario["source_locators"]
        assert all(
            locator.startswith("https://") for locator in scenario["source_locators"]
        )
    assert "commercial usefulness" in " ".join(report["limitations"])
    assert not any(
        "commercial_coverage" in key for key in report["readiness_requirements"]
    )
    assert report["readiness_requirements"][
        "declared_clinical_and_open_targets_registered_locators_exact"
    ]
    assert report["readiness_requirements"]["preregistered_operator_reviews_current"]
    assert report["review_freshness"]["source_terms_max_age_days"] == 90
    assert report["review_freshness"]["clinical_relationship_max_age_days"] == 90


def test_clinical_locked_control_exercises_post_cutoff_reason() -> None:
    report = evaluate_pilot()
    clinical = next(
        world
        for world in report["worlds"]
        if world["world_id"] == "clinical-trials-sec"
    )
    cutoff = next(
        control
        for control in clinical["controls"]
        if control["control_id"] == "clinical-trials-null-post-cutoff"
    )

    assert cutoff["observed"] == "INCONCLUSIVE"
    assert cutoff["reason_code"] == "POST_CUTOFF_EVIDENCE"
    assert cutoff["passed"] is True


def test_license_gate_requires_exact_registry_and_reviewed_terms(
    tmp_path: Path,
) -> None:
    manifest_root = tmp_path / "manifests"
    shutil.copytree(MANIFEST_ROOT, manifest_root)
    manifest_path = manifest_root / "open-targets.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"][0]["license"]["id"] = "FAKE-LICENSE"
    manifest["sources"][0]["license"]["reference_url"] = "https://example.invalid/fake"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = evaluate_pilot(manifest_root=manifest_root)
    open_targets = next(
        world for world in report["worlds"] if world["world_id"] == "open-targets"
    )
    license_gate = next(
        gate
        for gate in open_targets["fatal_gates"]
        if gate["gate_id"] == "license_and_redistribution"
    )

    assert report["pilot_ready"] is False
    assert license_gate["status"] == "FAIL"


def test_coordinated_fake_manifest_and_review_urls_cannot_pass(
    tmp_path: Path,
) -> None:
    manifest_root = tmp_path / "manifests"
    shutil.copytree(MANIFEST_ROOT, manifest_root)
    manifest_path = manifest_root / "open-targets.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"][0]["official_url"] = "https://example.invalid/source"
    manifest["sources"][0]["license"]["reference_url"] = "https://example.invalid/terms"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    source_review = json.loads(SOURCE_TERMS_REVIEW_PATH.read_text(encoding="utf-8"))
    review_row = next(
        row for row in source_review["sources"] if row["world_id"] == "open-targets"
    )
    review_row["official_url"] = "https://example.invalid/source"
    review_row["terms_reference_url"] = "https://example.invalid/terms"
    source_review_path = tmp_path / "source-terms-review.json"
    source_review_path.write_text(json.dumps(source_review), encoding="utf-8")

    report = evaluate_pilot(
        manifest_root=manifest_root,
        source_terms_review_path=source_review_path,
    )
    open_targets = next(
        world for world in report["worlds"] if world["world_id"] == "open-targets"
    )
    license_gate = next(
        gate
        for gate in open_targets["fatal_gates"]
        if gate["gate_id"] == "license_and_redistribution"
    )

    assert report["pilot_ready"] is False
    assert license_gate["status"] == "FAIL"


def test_stale_source_terms_review_cannot_pass(tmp_path: Path) -> None:
    source_review = json.loads(SOURCE_TERMS_REVIEW_PATH.read_text(encoding="utf-8"))
    source_review["reviewed_at"] = "2025-01-01T00:00:00Z"
    source_review_path = tmp_path / "stale-source-terms-review.json"
    source_review_path.write_text(json.dumps(source_review), encoding="utf-8")

    report = evaluate_pilot(source_terms_review_path=source_review_path)

    assert report["pilot_ready"] is False
    assert (
        report["readiness_requirements"]["preregistered_operator_reviews_current"]
        is False
    )
    for world in report["worlds"]:
        license_gate = next(
            gate
            for gate in world["fatal_gates"]
            if gate["gate_id"]
            in {
                "dataset_license_scope",
                "license_and_redistribution",
                "license_and_custody",
            }
        )
        assert license_gate["status"] == "FAIL"


def test_fake_scenario_locator_cannot_satisfy_declared_scenario_gate(
    tmp_path: Path,
) -> None:
    corpus = json.loads(CONTROL_CORPUS_PATH.read_text(encoding="utf-8"))
    open_targets = next(
        world for world in corpus["worlds"] if world["world_id"] == "open-targets"
    )
    open_targets["inspectable_scenario"]["source_locators"] = [
        "https://example.invalid/forged-scenario"
    ]
    corpus_path = tmp_path / "forged-scenario-corpus.json"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")

    report = evaluate_pilot(control_corpus_path=corpus_path)
    result = next(
        world for world in report["worlds"] if world["world_id"] == "open-targets"
    )

    assert report["pilot_ready"] is False
    assert result["inspectable_scenario"]["status"] == "FAIL"
    assert (
        report["readiness_requirements"][
            "declared_clinical_and_open_targets_registered_locators_exact"
        ]
        is False
    )


def test_source_terms_and_clinical_review_artifacts_are_hash_bound(
    tmp_path: Path,
) -> None:
    source_review = json.loads(SOURCE_TERMS_REVIEW_PATH.read_text(encoding="utf-8"))
    source_review["sources"][0]["terms_reference_url"] = (
        "https://example.invalid/not-reviewed"
    )
    source_review_path = tmp_path / "source-terms-review.json"
    source_review_path.write_text(json.dumps(source_review), encoding="utf-8")
    source_report = evaluate_pilot(source_terms_review_path=source_review_path)
    assert source_report["pilot_ready"] is False

    clinical_review = json.loads(CLINICAL_REVIEW_PATH.read_text(encoding="utf-8"))
    clinical_review["relationship_confirmed"] = False
    clinical_review_path = tmp_path / "clinical-review.json"
    clinical_review_path.write_text(json.dumps(clinical_review), encoding="utf-8")
    clinical_report = evaluate_pilot(clinical_review_path=clinical_review_path)
    clinical = next(
        world
        for world in clinical_report["worlds"]
        if world["world_id"] == "clinical-trials-sec"
    )
    complete_hashes = next(
        gate
        for gate in clinical["fatal_gates"]
        if gate["gate_id"] == "complete_hashes_and_schema"
    )
    assert clinical_report["pilot_ready"] is False
    assert complete_hashes["status"] == "FAIL"


def test_deferred_worlds_are_explicitly_excluded() -> None:
    report = evaluate_pilot()
    deferred = {item["world_id"]: item for item in report["deferred_worlds"]}

    assert set(deferred) == {"flywire-codex", "neurovault"}
    assert all(item["status"] == "DEFERRED" for item in deferred.values())
    assert all(
        item["world_id"] not in {world["world_id"] for world in report["worlds"]}
        for item in report["deferred_worlds"]
    )


def test_empty_or_incomplete_protocol_cannot_pass_vacuously() -> None:
    empty = _world_result("empty", {"version": "1"}, [], [], {})
    missing_gate = _world_result(
        "missing",
        {"version": "1"},
        [_passing_control("positive")],
        [GateEvidence("gate-a", "PASS", "ok")],
        {},
        required_gate_ids=("gate-a", "gate-b"),
        required_control_ids=("positive",),
    )
    duplicate_control = _world_result(
        "duplicate",
        {"version": "1"},
        [_passing_control("same"), _passing_control("same")],
        [GateEvidence("gate-a", "PASS", "ok")],
        {},
        required_gate_ids=("gate-a",),
        required_control_ids=("same", "different"),
    )

    assert empty["status"] == "FAIL"
    assert missing_gate["status"] == "FAIL"
    assert missing_gate["protocol_exact"] is False
    assert duplicate_control["status"] == "FAIL"
    assert duplicate_control["protocol_exact"] is False


def test_locked_protocol_rejects_missing_or_duplicate_gates_and_controls(
    tmp_path: Path,
) -> None:
    original = json.loads(CONTROL_CORPUS_PATH.read_text(encoding="utf-8"))

    missing_gate = json.loads(json.dumps(original))
    missing_gate["worlds"][0]["fatal_gate_ids"] = []
    missing_path = tmp_path / "missing-gate.json"
    missing_path.write_text(json.dumps(missing_gate), encoding="utf-8")
    with pytest.raises(ValueError, match="fatal gate set"):
        _load_protocol(missing_path)

    duplicate_gate = json.loads(json.dumps(original))
    duplicate_gate["worlds"][0]["fatal_gate_ids"][1] = duplicate_gate["worlds"][0][
        "fatal_gate_ids"
    ][0]
    duplicate_gate_path = tmp_path / "duplicate-gate.json"
    duplicate_gate_path.write_text(json.dumps(duplicate_gate), encoding="utf-8")
    with pytest.raises(ValueError, match="fatal gate set"):
        _load_protocol(duplicate_gate_path)

    missing_control = json.loads(json.dumps(original))
    missing_control["worlds"][0]["controls"].pop()
    missing_control_path = tmp_path / "missing-control.json"
    missing_control_path.write_text(json.dumps(missing_control), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one control"):
        _load_protocol(missing_control_path)

    duplicate_control = json.loads(json.dumps(original))
    duplicate_control["worlds"][0]["controls"][1]["control_id"] = duplicate_control[
        "worlds"
    ][0]["controls"][0]["control_id"]
    duplicate_control_path = tmp_path / "duplicate-control.json"
    duplicate_control_path.write_text(json.dumps(duplicate_control), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate control ids"):
        _load_protocol(duplicate_control_path)


def test_coordinated_fixture_and_manifest_hash_drift_cannot_pass(
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "fixtures"
    manifest_root = tmp_path / "manifests"
    shutil.copytree(FIXTURE_ROOT, fixture_root)
    shutil.copytree(MANIFEST_ROOT, manifest_root)

    fixture_path = fixture_root / "open_targets" / "release-26.06.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture["source_hashes"]["open-targets-graphql-26-06"] = "a" * 64
    payload = {
        key: fixture[key]
        for key in (
            "schema_version",
            "world_id",
            "version",
            "source_hashes",
            "records",
        )
    }
    fixture["integrity_sha256"] = _canonical_digest(payload)
    fixture_path.write_text(
        json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    manifest_path = manifest_root / "open-targets.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["transformation"]["sha256"] = hashlib.sha256(
        fixture_path.read_bytes()
    ).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(
        (WorldRegistryError, ValueError),
        match="(source|artifact) hashes do not exactly match registered world",
    ):
        evaluate_pilot(
            fixture_root=fixture_root,
            manifest_root=manifest_root,
        )


def test_fatal_gate_is_noncompensatory() -> None:
    result = _world_result(
        "example",
        {"version": "1"},
        [_passing_control("required-control")],
        [GateEvidence("required-gate", "FAIL", "fixture was tampered")],
        {},
        required_gate_ids=("required-gate",),
        required_control_ids=("required-control",),
    )

    assert result["status"] == "FAIL"


def test_evaluation_and_report_are_stable(tmp_path: Path) -> None:
    first = evaluate_pilot()
    second = evaluate_pilot()
    assert first == second

    written = write_report(tmp_path)
    assert written == first
    assert (
        json.loads((tmp_path / "pilot_readiness.json").read_text(encoding="utf-8"))
        == first
    )
    markdown = (tmp_path / "pilot_readiness.md").read_text(encoding="utf-8")
    assert "READY_FOR_BOUNDED_PILOT" in markdown
    assert "buyer_discovery" not in markdown
    assert "authenticity" in markdown
    assert "Readiness requirements" in markdown


def _passing_control(control_id: str) -> ControlResult:
    return ControlResult(
        control_id=control_id,
        kind="positive",
        expected=("ACCEPTED",),
        expected_reason_codes=(),
        observed="ACCEPTED",
        passed=True,
        reason_code="PASS",
        message="ok",
    )


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
