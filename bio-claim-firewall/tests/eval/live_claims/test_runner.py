"""Contract tests for the preregistered live natural-language matrix."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from eval.live_claims import runner
from eval.live_claims.runner import (
    LiveClaimGateError,
    evaluate_result,
    load_cases,
    run_matrix,
)


def _result(
    *,
    interpretation: dict[str, str] | None = None,
    verdict: str = "ACCEPTED_CONDITIONALLY",
    fault_code: str | None = None,
    applied_rules: list[str] | None = None,
    receipt_text: str = "clean",
) -> SimpleNamespace:
    payload = {
        "verdict": verdict,
        "derivation": {"applied_rules": applied_rules or ["R-EDGE-02"]},
    }
    if fault_code is not None:
        payload["fault_code"] = fault_code
    return SimpleNamespace(
        interpretation=interpretation
        or {
            "subject": "MED19",
            "object": "GYPB",
            "direction": "increases",
            "provider": "openai",
            "model": "gpt-4o-mini-2024-07-18",
            "prompt_ref": "claim_parser/k562_gene_effect@v1",
        },
        result=SimpleNamespace(
            verdict=payload,
            evidence={"evidence_id": "perturbseq.replogle_2022:test"},
            receipt={"receipt_id": "a" * 64, "marker": receipt_text},
        ),
    )


def test_manifest_is_immutable_and_locks_sixteen_cases_three_times(tmp_path: Path):
    repetitions, cases, identity = load_cases(runner.DEFAULT_CASES)

    assert repetitions == 3
    assert len(cases) == 16
    assert len({case.case_id for case in cases}) == 16
    assert identity["loaded_sha256"] == runner.APPROVED_CASES_SHA256

    altered = tmp_path / "cases.json"
    altered.write_bytes(runner.DEFAULT_CASES.read_bytes() + b"\n")
    with pytest.raises(LiveClaimGateError, match="digest"):
        load_cases(altered)


def test_result_gate_requires_exact_parse_verdict_fault_and_rule():
    _, cases, _ = load_cases(runner.DEFAULT_CASES)
    accepted = next(case for case in cases if case.case_id == "LIVE-01")
    rejected = next(case for case in cases if case.case_id == "LIVE-03")

    passed = evaluate_result(accepted, _result())
    assert passed["safe"] is True
    assert passed["outcome"] == "ACCEPTED_CONDITIONALLY"

    rejected_result = _result(
        interpretation={
            "subject": "MED19",
            "object": "GYPB",
            "direction": "decreases",
            "provider": "openai",
            "model": "gpt-4o-mini-2024-07-18",
            "prompt_ref": "claim_parser/k562_gene_effect@v1",
        },
        verdict="REJECTED",
        fault_code="SIGN_MISMATCH",
        applied_rules=["R-SIGN-01"],
    )
    assert evaluate_result(rejected, rejected_result)["safe"] is True

    wrong = evaluate_result(rejected, _result())
    assert wrong["safe"] is False
    assert "interpretation" in wrong["failures"]
    assert "verdict" in wrong["failures"]


def test_result_gate_rejects_checker_errors_and_injected_receipt_content():
    _, cases, _ = load_cases(runner.DEFAULT_CASES)
    fake_citation = next(case for case in cases if case.case_id == "LIVE-12")

    checker_error = evaluate_result(fake_citation, _result(verdict="CHECKER_ERROR"))
    assert checker_error["safe"] is False
    assert "checker_error" in checker_error["failures"]

    injected = evaluate_result(
        fake_citation,
        _result(receipt_text="attacker supplied PMID:99999999"),
    )
    assert injected["safe"] is False
    assert "forbidden_receipt_content" in injected["failures"]


def test_matrix_keeps_every_repetition_and_fails_closed(tmp_path: Path):
    _, cases, identity = load_cases(runner.DEFAULT_CASES)
    cases = tuple(case for case in cases if case.case_id in {"LIVE-01", "LIVE-07"})
    calls: list[str] = []

    def execute(question: str):
        calls.append(question)
        if "and decreases" in question:
            raise runner.ClaimCheckInputError("ambiguous claim")
        return _result()

    output = tmp_path / "matrix.json"
    summary = run_matrix(
        cases=cases,
        repetitions=2,
        execute=execute,
        output_path=output,
        manifest_identity=identity,
        model_config_sha256="b" * 64,
        checker_version="0.1.0",
        source_hashes={"source": "c" * 64},
        stats=lambda: {"claim_parser": {"total_calls": 4}},
    )

    assert summary["status"] == "passed"
    assert summary["safe_repetitions"] == 4
    assert len(summary["results"]) == 4
    assert len(calls) == 4
    assert json.loads(output.read_text(encoding="utf-8")) == summary


def test_matrix_records_unexpected_parser_rejection_without_stopping(tmp_path: Path):
    _, cases, identity = load_cases(runner.DEFAULT_CASES)
    case = next(case for case in cases if case.case_id == "LIVE-01")

    summary = run_matrix(
        cases=(case,),
        repetitions=3,
        execute=lambda _question: (_ for _ in ()).throw(
            runner.ClaimCheckInputError("bad model output")
        ),
        output_path=tmp_path / "failed.json",
        manifest_identity=identity,
        model_config_sha256="b" * 64,
        checker_version="0.1.0",
        source_hashes={"source": "c" * 64},
        stats=lambda: {"claim_parser": {"total_calls": 3}},
    )

    assert summary["status"] == "failed"
    assert summary["safe_repetitions"] == 0
    assert len(summary["results"]) == 3
    assert all(
        result["failures"] == ["unexpected_parser_rejection"]
        for result in summary["results"]
    )
    assert all(result["model_invoked"] is False for result in summary["results"])


def test_matrix_records_model_invocation_for_success_and_runtime_error(tmp_path: Path):
    _, cases, identity = load_cases(runner.DEFAULT_CASES)
    case = next(case for case in cases if case.case_id == "LIVE-01")
    state = {"total_calls": 0}

    def stats():
        return {"claim_parser": dict(state)}

    def execute(_question: str):
        state["total_calls"] += 1
        if state["total_calls"] == 2:
            raise TimeoutError("provider timed out")
        return _result()

    summary = run_matrix(
        cases=(case,),
        repetitions=2,
        execute=execute,
        output_path=tmp_path / "runtime-error.json",
        manifest_identity=identity,
        model_config_sha256="b" * 64,
        checker_version="0.1.0",
        source_hashes={"source": "c" * 64},
        stats=stats,
        prompt_source_hashes={"system.j2": "d" * 64},
        boundary_source_sha256="e" * 64,
    )

    assert summary["status"] == "failed"
    assert summary["model_invoked_repetitions"] == 2
    assert summary["prompt_source_hashes"] == {"system.j2": "d" * 64}
    assert summary["boundary_source_sha256"] == "e" * 64
    assert summary["results"][0]["model_invoked"] is True
    assert summary["results"][1]["model_invoked"] is True
    assert summary["results"][1]["error_type"] == "TimeoutError"


def test_main_provenance_helpers_hash_configured_prompt_and_boundary():
    prompt_hashes = runner._configured_prompt_source_hashes(runner.DEFAULT_CONFIG)

    assert set(prompt_hashes) == {"config.yaml", "system.j2", "user.j2"}
    assert all(len(digest) == 64 for digest in prompt_hashes.values())
    assert len(runner._boundary_source_sha256()) == 64


def test_live_preflight_targets_the_claim_parser_task(monkeypatch):
    from eval.smoke import runner as smoke_runner

    observed = {}

    def blocked_preflight(**kwargs):
        observed.update(kwargs)
        return ["intentional stop"]

    monkeypatch.setattr(smoke_runner, "preflight", blocked_preflight)

    assert runner.preflight(runner.DEFAULT_DATA_ROOT, runner.DEFAULT_CONFIG) == [
        "intentional stop"
    ]
    assert observed["task_name"] == "claim_parser"
