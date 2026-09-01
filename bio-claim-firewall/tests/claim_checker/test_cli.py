"""Command-line contract tests for legacy and registered evidence worlds."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from claim_checker import __main__ as cli
from claim_checker.service import ClaimCheckInputError, ClaimCheckResult

REPO_ROOT = Path(__file__).resolve().parents[3]
FIREWALL_ROOT = REPO_ROOT / "bio-claim-firewall"
PUBLIC_RECEIPTS = json.loads(
    (REPO_ROOT / "sites/bio_claim_firewall/receipts.json").read_text(encoding="utf-8")
)["receipts"]
PUBLIC_BY_ID = {receipt["receipt_id"]: receipt for receipt in PUBLIC_RECEIPTS}


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


@pytest.mark.parametrize(
    ("receipt_id", "world_id", "world_version", "fixture"),
    [
        (
            "trial-positive",
            "clinical-trials-sec",
            "2025-09-01_2026-09-01",
            "tests/fixtures/worlds/clinical_trials/fixture.json",
        ),
        (
            "targets-positive",
            "open-targets",
            "26.06",
            "tests/fixtures/worlds/open_targets/release-26.06.json",
        ),
        (
            "arc-positive",
            "arc-vcc",
            "2025-h1-measurements",
            "tests/fixtures/worlds/arc_vcc",
        ),
    ],
)
def test_registered_world_cli_receipt_matches_public_export(
    receipt_id, world_id, world_version, fixture, capsys
):
    public = PUBLIC_BY_ID[receipt_id]

    exit_code = cli.main(
        [
            "--world-id",
            world_id,
            "--world-version",
            world_version,
            "--fixture",
            str(FIREWALL_ROOT / fixture),
            "--claim-json",
            json.dumps(public["normalized_claim"]),
            "--json",
        ]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    canonical = output["receipt"]["canonical_payload"]
    public_citation_ids = [item["engine_id"] for item in public["citations"]]
    assert output["receipt"]["receipt_id"] == public["engine_receipt_id"]
    assert (canonical.get("outcome") or canonical["verdict"]) == public["outcome"]
    assert canonical.get("winning_rule") == public["winning_rule"]["id"] or (
        isinstance(canonical.get("winning_rule"), dict)
        and canonical["winning_rule"].get("id") == public["winning_rule"]["id"]
    )
    assert canonical.get("citations", []) == public_citation_ids
    assert canonical["world_digest"] == public["world_digest"]
    assert canonical["world_id"] == public["world_id"] == world_id
    assert canonical["checker_version"] == public["checker_version"]
    if world_id == "clinical-trials-sec":
        assert canonical["checker_version"] == "clinical-trials-sec/0.2.0"


def test_registered_world_requires_claim_json_and_explicit_fixture(capsys):
    with pytest.raises(SystemExit) as error:
        cli.main(
            [
                "--world-id",
                "open-targets",
                "--world-version",
                "26.06",
                "--claim-json",
                "{}",
                "--json",
            ]
        )

    assert error.value.code == 2
    assert (
        "--fixture is required"
        in json.loads(capsys.readouterr().out)["error"]["message"]
    )


def test_explicit_k562_world_uses_the_selected_fixture(monkeypatch, tmp_path, capsys):
    fixture = object()
    observed = {}

    def fake_load(path, *, allowed_sources):
        observed["path"] = path
        observed["allowed_sources"] = allowed_sources
        return fixture

    def fake_check(bundle, world_id, world_version, claim, *, checker_version):
        observed.update(
            {
                "bundle": bundle,
                "world_id": world_id,
                "world_version": world_version,
                "claim": claim,
                "checker_version": checker_version,
            }
        )
        return ClaimCheckResult(None, None, {"verdict": "INCONCLUSIVE"})

    monkeypatch.setattr(cli, "load_bundle", fake_load)
    monkeypatch.setattr(cli, "check_claim", fake_check)

    assert (
        cli.main(
            [
                "MED19",
                "GYPB",
                "increases",
                "--world-id",
                "replogle-k562",
                "--world-version",
                "2022-pilot",
                "--fixture",
                str(tmp_path),
                "--json",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["verdict"]["verdict"] == "INCONCLUSIVE"
    assert observed["path"] == tmp_path
    assert observed["bundle"] is fixture
    assert observed["world_id"] == "replogle-k562"
    assert observed["world_version"] == "2022-pilot"
    assert observed["claim"] == {
        "subject": "MED19",
        "object": "GYPB",
        "direction": "increases",
    }
    assert observed["allowed_sources"]


def test_fixture_without_explicit_world_is_rejected(capsys, tmp_path):
    with pytest.raises(SystemExit) as error:
        cli.main(
            [
                "MED19",
                "GYPB",
                "increases",
                "--fixture",
                str(tmp_path),
                "--json",
            ]
        )

    assert error.value.code == 2
    assert (
        "--fixture requires" in json.loads(capsys.readouterr().out)["error"]["message"]
    )


def test_registered_world_text_output_is_generic(capsys):
    public = PUBLIC_BY_ID["targets-positive"]

    assert (
        cli.main(
            [
                "--world-id",
                "open-targets",
                "--world-version",
                "26.06",
                "--fixture",
                str(
                    FIREWALL_ROOT
                    / "tests/fixtures/worlds/open_targets/release-26.06.json"
                ),
                "--claim-json",
                json.dumps(public["normalized_claim"]),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "World: open-targets / 26.06" in output
    assert "Winning rule: OT.ASSOCIATION.02" in output
    assert "frozen K562 CRISPRi evidence" not in output
