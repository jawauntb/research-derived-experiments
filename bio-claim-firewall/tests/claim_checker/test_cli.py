"""Command-line contract tests for the bounded K562 claim checker."""

from __future__ import annotations

import json

import pytest

from claim_checker import __main__ as cli
from claim_checker.service import ClaimCheckInputError, ClaimCheckResult


def test_empty_claim_is_not_silently_discarded_when_positionals_are_present(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["--claim", "", "MED19", "GYPB", "increases"])

    assert error.value.code == 2
    assert "--claim cannot be combined" in capsys.readouterr().err


def test_json_mode_keeps_argument_errors_machine_readable(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(["--json"])

    assert error.value.code == 2
    assert json.loads(capsys.readouterr().out) == {
        "error": {
            "kind": "input_error",
            "message": "provide SUBJECT OBJECT DIRECTION, or use --claim",
        }
    }


def test_json_mode_keeps_input_errors_machine_readable(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_bundle", lambda _: object())
    monkeypatch.setattr(
        cli,
        "check_k562_claim",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ClaimCheckInputError("bad input")
        ),
    )

    assert cli.main(["MED19", "GYPB", "increases", "--json"]) == 2
    assert json.loads(capsys.readouterr().out) == {
        "error": {"kind": "input_error", "message": "bad input"}
    }


def test_checker_error_is_machine_visible_and_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_bundle", lambda _: object())
    monkeypatch.setattr(
        cli,
        "check_k562_claim",
        lambda *_args, **_kwargs: ClaimCheckResult(
            claim={"subject": {"label": "MED19"}},
            evidence={"evidence_id": "replogle:test"},
            verdict={
                "verdict": "CHECKER_ERROR",
                "checker_error": {"stage": "run_rules", "message": "rule load failed"},
            },
        ),
    )

    assert cli.main(["MED19", "GYPB", "increases", "--json"]) == 4
    assert json.loads(capsys.readouterr().out)["verdict"]["verdict"] == "CHECKER_ERROR"
