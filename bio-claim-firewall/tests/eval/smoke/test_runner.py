"""Contract tests for the preregistered live-model smoke runner."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from eval.smoke import runner
from eval.smoke.runner import (
    SmokeCase,
    SmokeGateError,
    assert_schema_valid_proposed_claims,
    assert_verdict_gates,
    evidence_for_case,
    load_cases,
    preflight,
    run_smoke,
)


class _Ledger:
    def __init__(self, records):
        self.records = {record["evidence_id"]: record for record in records}
        self.requested_ids = []

    def list_by(self, subject_id, object_id):
        return [
            record
            for record in self.records.values()
            if record["subject"]["id"] == subject_id
            and record["object"]["id"] == object_id
        ]

    def get(self, evidence_id):
        self.requested_ids.append(evidence_id)
        try:
            return self.records[evidence_id]
        except KeyError as exc:
            raise LookupError(evidence_id) from exc

    def snapshot_hashes(self):
        return {"perturbseq.replogle_2022": "a" * 64}


def _record(
    evidence_id="perturbseq.replogle_2022:test",
    sign="positive",
    *,
    subject="HGNC:1",
    object_="HGNC:2",
):
    return {
        "evidence_id": evidence_id,
        "subject": {"id": subject},
        "object": {"id": object_},
        "effect": {"sign": sign},
    }


def _valid_claim(evidence_id: str, index: int = 1) -> dict:
    return {
        "schema_version": "0.1.0",
        "claim_id": f"00000000-0000-4000-8000-{index:012d}",
        "subject": {"id": "HGNC:1", "label": "GENE1"},
        "relation": "increases",
        "object": {"id": "HGNC:2", "label": "GENE2"},
        "polarity": "positive",
        "species": "NCBITaxon:9606",
        "cell_context": {"cell_type": "CL:0000000", "cell_line": None, "state": None},
        "assay_context": {"assay": "CRISPRi_screen", "perturbation": "CRISPRi:HGNC:1"},
        "evidence_ids": [evidence_id],
        "confidence_language": "supported",
        "requested_status": "hypothesis",
    }


def _cases_and_bundle() -> tuple[tuple[SmokeCase, ...], SimpleNamespace]:
    cases = tuple(
        SmokeCase(
            f"SMOKE-{index:02d}",
            f"question {index}",
            f"HGNC:{index}",
            f"HGNC:{index + 10}",
            "positive",
        )
        for index in range(1, 6)
    )
    records = [
        _record(
            f"perturbseq.replogle_2022:{index}",
            subject=case.subject_id,
            object_=case.object_id,
        )
        for index, case in enumerate(cases, start=1)
    ]
    manifests = {
        source: SimpleNamespace(sha256=f"{index:064x}")
        for index, source in enumerate(runner._REQUIRED_SOURCES, start=1)
    }
    return cases, SimpleNamespace(ledger=_Ledger(records), manifests=manifests)


def _config_path(tmp_path: Path) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text("tasks: {}\nproviders: {}\n", encoding="utf-8")
    return path


def _install_mocked_pipeline(
    monkeypatch, bundle, *, fail_on_call: int | None = None, invalid_claim: bool = False
):
    import evidence
    import model_manager
    import orchestrator
    import proposer
    import repairer

    class FakeModelManager:
        def __init__(self, config_path):
            self.config_path = config_path

    class FakeProposer:
        def __init__(self, manager):
            self.manager = manager

    class FakeRepairer:
        def __init__(self, manager):
            self.manager = manager

    class FakeOrchestrator:
        instances = []

        def __init__(self, proposer_, repairer_, verifier_config, snapshot, config):
            self.proposer = proposer_
            self.repairer = repairer_
            self.verifier_config = verifier_config
            self.snapshot = snapshot
            self.config = config
            self.calls = []
            type(self).instances.append(self)

        def run(self, question, evidence_records):
            self.calls.append((question, evidence_records))
            call_number = len(self.calls)
            if fail_on_call == call_number:
                raise RuntimeError(f"model dispatch failed at case {call_number}")

            evidence_id = evidence_records[0]["evidence_id"]
            claim = _valid_claim(evidence_id, call_number)
            if invalid_claim:
                claim["relation"] = "not-a-relation"
            trajectory_id = f"trajectory-{call_number}"
            receipt = {
                "trajectory_id": trajectory_id,
                "attempts": [{"stage": "propose", "proposed_claim": claim}],
            }
            with self.config.trajectory_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(receipt) + "\n")
            verdict = {
                "verdict": "ACCEPTED_CONDITIONALLY",
                "derivation": {"evidence_ids": [evidence_id]},
            }
            return SimpleNamespace(
                trajectory_id=trajectory_id,
                final_verdicts=(verdict,),
                attempts=1,
                status="accepted",
            )

    monkeypatch.setattr(evidence, "load_bundle", lambda data_root: bundle)
    monkeypatch.setattr(model_manager, "ModelManager", FakeModelManager)
    monkeypatch.setattr(orchestrator, "Orchestrator", FakeOrchestrator)
    monkeypatch.setattr(proposer, "Proposer", FakeProposer)
    monkeypatch.setattr(repairer, "Repairer", FakeRepairer)
    return FakeOrchestrator


def test_frozen_manifest_has_five_unique_cases_and_immutable_identity(tmp_path):
    cases = load_cases(runner._DEFAULT_QUESTIONS)

    assert len(cases) == 5
    assert len({case.case_id for case in cases}) == 5

    copy_path = tmp_path / "questions.json"
    copy_path.write_bytes(runner._DEFAULT_QUESTIONS.read_bytes())
    assert load_cases(copy_path) == cases

    copy_path.write_text(copy_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(SmokeGateError, match="digest"):
        load_cases(copy_path)


def test_evidence_selector_fails_closed_unless_exactly_one_signed_record_matches():
    case = SmokeCase("case", "q", "HGNC:1", "HGNC:2", "positive")
    bundle = SimpleNamespace(ledger=_Ledger([_record(), _record("other", "negative")]))

    assert (
        evidence_for_case(bundle, case)["evidence_id"]
        == "perturbseq.replogle_2022:test"
    )

    ambiguous = SimpleNamespace(ledger=_Ledger([_record(), _record("second")]))
    with pytest.raises(SmokeGateError, match="exactly one"):
        evidence_for_case(ambiguous, case)


@pytest.mark.parametrize(
    ("verdicts", "message"),
    [
        ([], "no verifier verdict"),
        ([None], "non-object verdict"),
        ([{}], "unknown verdict"),
        ([{"verdict": "CHECKER_ERROR", "checker_error": {}}], "CHECKER_ERROR"),
        ([{"verdict": "ACCEPTED_CONDITIONALLY"}], "missing its derivation"),
        (
            [{"verdict": "ACCEPTED_CONDITIONALLY", "derivation": []}],
            "missing its derivation",
        ),
        (
            [{"verdict": "ACCEPTED_CONDITIONALLY", "derivation": {"evidence_ids": []}}],
            "at least one",
        ),
        (
            [
                {
                    "verdict": "ACCEPTED_CONDITIONALLY",
                    "derivation": {"evidence_ids": [""]},
                }
            ],
            "invalid evidence",
        ),
        (
            [
                {
                    "verdict": "ACCEPTED_CONDITIONALLY",
                    "derivation": {"evidence_ids": [1]},
                }
            ],
            "invalid evidence",
        ),
    ],
)
def test_verdict_gates_fail_closed_on_malformed_verdicts(verdicts, message):
    with pytest.raises(SmokeGateError, match=message):
        assert_verdict_gates(SimpleNamespace(ledger=_Ledger([])), verdicts)


def test_verdict_gates_accept_rejection_and_inconclusive_and_require_resolvable_derivations():
    record = _record("source:1")
    ledger = _Ledger([record])
    bundle = SimpleNamespace(ledger=ledger)

    assert_verdict_gates(bundle, [{"verdict": "REJECTED"}, {"verdict": "INCONCLUSIVE"}])
    assert_verdict_gates(
        bundle,
        [
            {
                "verdict": "ACCEPTED_CONDITIONALLY",
                "derivation": {"evidence_ids": ["source:1"]},
            }
        ],
    )
    assert ledger.requested_ids == ["source:1"]

    with pytest.raises(SmokeGateError, match="unresolved"):
        assert_verdict_gates(
            bundle,
            [
                {
                    "verdict": "ACCEPTED_CONDITIONALLY",
                    "derivation": {"evidence_ids": ["unknown"]},
                }
            ],
        )


def test_schema_gate_rejects_invalid_or_absent_proposals():
    valid_trajectory = {
        "attempts": [{"stage": "propose", "proposed_claim": _valid_claim("source:1")}]
    }
    assert_schema_valid_proposed_claims(valid_trajectory)

    invalid_trajectory = {
        "attempts": [{"stage": "propose", "proposed_claim": {"relation": "bad"}}]
    }
    with pytest.raises(SmokeGateError, match="not schema-valid"):
        assert_schema_valid_proposed_claims(invalid_trajectory)

    with pytest.raises(SmokeGateError, match="no durable proposed claims"):
        assert_schema_valid_proposed_claims({"attempts": []})


@pytest.mark.parametrize(
    "missing_package", ["openai", "httpx", "tenacity", "truststore"]
)
def test_provider_preflight_requires_every_openai_provider_dependency(
    tmp_path, monkeypatch, missing_package
):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "tasks": {"proposer": {"provider": "provider"}},
                "providers": {
                    "provider": {"type": "openai_sdk", "api_key_env": "TOKEN"}
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda package: object())

    assert runner._provider_preflight(config_path, {"TOKEN": "present"}) == []
    assert runner._provider_preflight(config_path, {}) == [
        "configured provider credential is absent: TOKEN"
    ]

    monkeypatch.setattr(
        runner.importlib.util,
        "find_spec",
        lambda package: None if package == missing_package else object(),
    )
    assert (
        f"missing optional dependency {missing_package}"
        in runner._provider_preflight(config_path, {"TOKEN": "present"})
    )


@pytest.mark.parametrize("missing_package", ["ollama", "httpx", "tenacity"])
def test_provider_preflight_requires_every_ollama_provider_dependency(
    tmp_path, monkeypatch, missing_package
):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "tasks": {"proposer": {"provider": "provider"}},
                "providers": {"provider": {"type": "ollama"}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda package: object())

    assert runner._provider_preflight(config_path, {}) == []

    monkeypatch.setattr(
        runner.importlib.util,
        "find_spec",
        lambda package: None if package == missing_package else object(),
    )
    assert (
        f"missing optional dependency {missing_package}"
        in runner._provider_preflight(config_path, {})
    )


def test_provider_preflight_handles_unsupported_and_malformed_configs(
    tmp_path, monkeypatch
):
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda package: object())

    config_path.write_text(
        json.dumps(
            {
                "tasks": {"proposer": {"provider": "provider"}},
                "providers": {"provider": {"type": "unsupported"}},
            }
        ),
        encoding="utf-8",
    )
    assert (
        "unsupported smoke-study provider type: 'unsupported'"
        in runner._provider_preflight(config_path, {})
    )

    config_path.write_text("tasks: []", encoding="utf-8")
    assert runner._provider_preflight(config_path, {})[0].startswith(
        "cannot read proposer provider"
    )


def test_preflight_reports_hash_failure_without_networking(tmp_path, monkeypatch):
    import evidence

    monkeypatch.setattr(runner, "_missing_data_sources", lambda data_root: [])
    monkeypatch.setattr(
        evidence,
        "load_bundle",
        lambda data_root: (_ for _ in ()).throw(RuntimeError("hash mismatch")),
    )
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda package: object())
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        json.dumps(
            {
                "tasks": {"proposer": {"provider": "provider"}},
                "providers": {"provider": {"type": "ollama"}},
            }
        ),
        encoding="utf-8",
    )

    errors = preflight(data_root=tmp_path, config_path=config_path, environ={})

    assert errors == ["frozen pilot snapshot did not load hash-verified: hash mismatch"]


def test_preflight_reports_missing_provider_and_data_prerequisites(tmp_path):
    errors = preflight(
        data_root=tmp_path / "missing-data",
        config_path=tmp_path / "missing-config.yaml",
        environ={},
    )

    assert any("model config does not exist" in error for error in errors)
    assert any("missing frozen pilot sources" in error for error in errors)


def test_source_manifest_hashes_require_exactly_the_preregistered_six_sources():
    _, bundle = _cases_and_bundle()
    assert set(runner._source_manifest_hashes(bundle)) == set(runner._REQUIRED_SOURCES)

    bundle.manifests["unpreregistered.source"] = SimpleNamespace(sha256="f" * 64)
    with pytest.raises(SmokeGateError, match="unexpected"):
        runner._source_manifest_hashes(bundle)

    bundle.manifests.pop("unpreregistered.source")
    bundle.manifests.pop("hgnc.2026_pilot")
    with pytest.raises(SmokeGateError, match="missing"):
        runner._source_manifest_hashes(bundle)


def test_run_smoke_writes_five_complete_mocked_case_receipts(tmp_path, monkeypatch):
    cases, bundle = _cases_and_bundle()
    fake_orchestrator = _install_mocked_pipeline(monkeypatch, bundle)
    trajectory_path = tmp_path / "five-cases.jsonl"
    summary_path = tmp_path / "five-cases.summary.json"

    summary = run_smoke(
        data_root=tmp_path / "data",
        config_path=_config_path(tmp_path),
        cases=cases,
        trajectory_path=trajectory_path,
        summary_path=summary_path,
        questions_path=runner._DEFAULT_QUESTIONS,
        checker_version="0.1.0",
    )

    assert summary["status"] == "passed"
    assert len(summary["cases"]) == 5
    assert set(summary["source_manifest_hashes"]) == set(runner._REQUIRED_SOURCES)
    assert (
        summary["questions_manifest"]["approved_sha256"]
        == runner._APPROVED_QUESTIONS_SHA256
    )
    assert [case["case_id"] for case in summary["cases"]] == [
        case.case_id for case in cases
    ]
    assert all(
        case["attempts"] == 1 and case["verdicts"] == ["ACCEPTED_CONDITIONALLY"]
        for case in summary["cases"]
    )
    assert len(fake_orchestrator.instances) == 1
    instance = fake_orchestrator.instances[0]
    assert instance.config.max_repair_attempts == 0
    assert len(instance.calls) == 5
    assert len(trajectory_path.read_text(encoding="utf-8").splitlines()) == 5
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary


def test_run_smoke_writes_failed_receipt_after_second_mocked_dispatch(
    tmp_path, monkeypatch
):
    cases, bundle = _cases_and_bundle()
    fake_orchestrator = _install_mocked_pipeline(monkeypatch, bundle, fail_on_call=2)
    trajectory_path = tmp_path / "fails.jsonl"
    summary_path = tmp_path / "fails.summary.json"

    with pytest.raises(RuntimeError, match="case 2"):
        run_smoke(
            data_root=tmp_path / "data",
            config_path=_config_path(tmp_path),
            cases=cases,
            trajectory_path=trajectory_path,
            summary_path=summary_path,
            questions_path=runner._DEFAULT_QUESTIONS,
            checker_version="0.1.0",
        )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert len(summary["cases"]) == 1
    assert "case 2" in summary["error"]
    assert len(fake_orchestrator.instances[0].calls) == 2
    assert len(trajectory_path.read_text(encoding="utf-8").splitlines()) == 1


def test_run_smoke_refuses_schema_invalid_model_output_before_passing(
    tmp_path, monkeypatch
):
    cases, bundle = _cases_and_bundle()
    _install_mocked_pipeline(monkeypatch, bundle, invalid_claim=True)
    trajectory_path = tmp_path / "invalid.jsonl"
    summary_path = tmp_path / "invalid.summary.json"

    with pytest.raises(SmokeGateError, match="not schema-valid"):
        run_smoke(
            data_root=tmp_path / "data",
            config_path=_config_path(tmp_path),
            cases=cases,
            trajectory_path=trajectory_path,
            summary_path=summary_path,
            questions_path=runner._DEFAULT_QUESTIONS,
            checker_version="0.1.0",
        )

    assert json.loads(summary_path.read_text(encoding="utf-8"))["status"] == "failed"


def test_reservation_is_exclusive_for_one_output_pair(tmp_path):
    trajectory_path = tmp_path / "reserved.jsonl"
    summary_path = tmp_path / "reserved.summary.json"
    reservation_path = runner._reserve_run(trajectory_path, summary_path)

    with pytest.raises(SmokeGateError, match="refusing to mix"):
        runner._reserve_run(trajectory_path, summary_path)

    assert (
        json.loads(reservation_path.read_text(encoding="utf-8"))["status"] == "reserved"
    )


def test_cli_preflight_never_calls_smoke_runner(monkeypatch):
    monkeypatch.setattr(runner, "preflight", lambda **kwargs: [])
    monkeypatch.setattr(
        runner,
        "run_smoke",
        lambda **kwargs: pytest.fail("smoke must not run in preflight"),
    )

    assert runner.main(["--preflight"]) == 0
