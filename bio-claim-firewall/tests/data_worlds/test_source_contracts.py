from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "data" / "scripts" / "worlds"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _common import (
    SourceIntegrityError,
    acquire_bytes,
    contract_digest,
    fixture_manifest,
    load_contract,
    preflight_contract,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "data" / "manifests" / "worlds"
EXPECTED_WORLDS = {
    "clinical-trials-sec": "RESEARCHED",
    "open-targets": "RESEARCHED",
    "arc-vcc": "RESEARCHED",
    "neurovault": "RESEARCHED_DEFERRED",
    "flywire-codex": "RESEARCHED_DEFERRED",
}


def test_all_ranked_contracts_are_structurally_valid_and_independent():
    paths = sorted(CONTRACTS.glob("*.json"))
    assert {path.stem for path in paths} == set(EXPECTED_WORLDS)
    contracts = [load_contract(path) for path in paths]
    assert {contract["world_id"]: contract["state"] for contract in contracts} == EXPECTED_WORLDS
    assert len({contract_digest(contract) for contract in contracts}) == 5
    for contract in contracts:
        assert contract["rank"] in range(1, 6)
        assert contract["evidence_paths"]["audit_card"].startswith("experiments/evidence_worlds/")
        assert all(source["official_url"].startswith("https://") for source in contract["sources"])


def test_registry_references_each_contract_and_card():
    registry = (ROOT / "data" / "worlds" / "registry.yaml").read_text(encoding="utf-8")
    for world_id in EXPECTED_WORLDS:
        assert f'world_id: "{world_id}"' in registry
        assert f'data/manifests/worlds/{world_id}.json' in registry
        card = ROOT / "experiments" / "evidence_worlds" / "preregistration" / f"{world_id}.yaml"
        assert card.is_file()
        assert f'world_id: "{world_id}"' in card.read_text(encoding="utf-8")


def test_preflight_is_no_network_and_reports_unresolved_gates():
    first = preflight_contract(CONTRACTS / "flywire-codex.json")
    second = preflight_contract(CONTRACTS / "flywire-codex.json")
    assert first == second
    assert first["state"] == "RESEARCHED_DEFERRED"
    assert "internal_use_license" in first["fatal_gate_unknown_or_not_run"]
    assert first["ready_for_acquisition"] is False


def test_contract_digest_changes_when_contract_changes():
    contract = load_contract(CONTRACTS / "open-targets.json")
    digest = contract_digest(contract)
    changed = dict(contract)
    changed["version"] = "27.01"
    assert contract_digest(changed) != digest


def test_acquisition_reuses_verified_cache_without_fetching(tmp_path: Path):
    destination = tmp_path / "cache" / "sample.bin"
    payload = b"bounded fixture\n"
    destination.parent.mkdir()
    destination.write_bytes(payload)
    result = acquire_bytes(
        "https://official.example/sample.bin",
        destination,
        expected_sha256=__import__("hashlib").sha256(payload).hexdigest(),
        source_kind="immutable_release",
        fetcher=lambda _url: pytest.fail("verified cache must not fetch"),
    )
    assert result["status"] == "cached"
    assert result["changed"] is False


@pytest.mark.parametrize(
    ("source_kind", "code", "new_version_required"),
    [("immutable_release", "IMMUTABLE_DRIFT", False), ("rolling_snapshot", "ROLLING_DRIFT_NEW_VERSION_REQUIRED", True)],
)
def test_changed_cached_bytes_never_replace_retained_snapshot(tmp_path: Path, source_kind: str, code: str, new_version_required: bool):
    destination = tmp_path / "sample.bin"
    destination.write_bytes(b"retained")
    with pytest.raises(SourceIntegrityError) as error:
        acquire_bytes("https://official.example/sample.bin", destination, expected_sha256="0" * 64, source_kind=source_kind)
    assert error.value.code == code
    assert error.value.new_version_required is new_version_required
    assert destination.read_bytes() == b"retained"


def test_fixture_manifest_is_deterministic_and_excludes_its_own_output(tmp_path: Path):
    (tmp_path / "sample.txt").write_text("fixture\n", encoding="utf-8")
    first = fixture_manifest(tmp_path)
    (tmp_path / "fixture-manifest.json").write_text(json.dumps(first), encoding="utf-8")
    assert fixture_manifest(tmp_path) == first


@pytest.mark.parametrize("path", [
    "bio-claim-firewall/data/worlds/registry.yaml",
    "bio-claim-firewall/data/manifests/worlds/open-targets.json",
    "bio-claim-firewall/data/scripts/worlds/_common.py",
    "bio-claim-firewall/experiments/evidence_worlds/preregistration/open-targets.yaml",
])
def test_tracked_contract_paths_are_not_ignored(path: str):
    result = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT.parent, check=False)
    assert result.returncode == 1
