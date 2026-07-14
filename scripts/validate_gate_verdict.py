#!/usr/bin/env python3
"""Validate canonical per-gate verdict files and their claim links."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Never, cast

try:
    from scripts.research_contracts import (
        CLAIM_ID,
        CLAIM_TIERS,
        EVIDENCE_STATUSES,
        SCHEMA_VERSION,
        SHA256,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/validate_gate_verdict.py
    from research_contracts import CLAIM_ID, CLAIM_TIERS, EVIDENCE_STATUSES, SCHEMA_VERSION, SHA256

try:
    from scripts.validate_experiment_manifest import validate as validate_manifest
except ModuleNotFoundError:  # Direct execution: python scripts/validate_gate_verdict.py
    from validate_experiment_manifest import validate as validate_manifest


ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "docs" / "claim_registry.json"
REQUIRED_FIELDS = {
    "schema_version",
    "gate_id",
    "claim_id",
    "claim_tier",
    "status",
    "observed",
    "expected",
    "evidence_refs",
}
OPTIONAL_FIELDS = {"threshold", "unit", "preregistration_sha256", "notes"}


def fail(message: str) -> Never:
    raise ValueError(message)


def known_claim_ids(path: Path = CLAIMS) -> set[str]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read claim registry: {exc}")
    claims = payload.get("claims") if isinstance(payload, dict) else None
    if not isinstance(claims, list):
        fail("claim registry claims must be a list")
    return {
        claim["claim_id"]
        for claim in claims
        if isinstance(claim, dict) and isinstance(claim.get("claim_id"), str)
    }


def _inferred_manifest(path: Path) -> Path | None:
    if path.parent.name == "gate_verdicts" and path.parent.parent.name == "results":
        return path.parent.parent.parent / "experiment_manifest.json"
    return None


def validate(
    path: Path,
    *,
    claims: set[str] | None = None,
    root: Path = ROOT,
    manifest_path: Path | None = None,
) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")
    if not isinstance(payload, dict):
        fail("gate verdict must be an object")
    verdict = cast(dict[str, object], payload)
    missing = REQUIRED_FIELDS - set(verdict)
    if missing:
        fail(f"gate verdict is missing required field: {sorted(missing)[0]}")
    unknown = set(verdict) - REQUIRED_FIELDS - OPTIONAL_FIELDS
    if unknown:
        fail(f"gate verdict contains unknown field: {sorted(unknown)[0]}")
    if verdict["schema_version"] != SCHEMA_VERSION:
        fail(f"schema_version must be '{SCHEMA_VERSION}'")
    for field in ("gate_id", "claim_id", "claim_tier", "status"):
        value = verdict[field]
        if not isinstance(value, str) or not value.strip():
            fail(f"{field} must be a non-empty string")
    gate_id = cast(str, verdict["gate_id"])
    claim_id = cast(str, verdict["claim_id"])
    if CLAIM_ID.fullmatch(gate_id) is None:
        fail(f"gate_id has invalid format: {gate_id}")
    if CLAIM_ID.fullmatch(claim_id) is None:
        fail(f"claim_id has invalid format: {claim_id}")
    if claims is not None and claim_id not in claims:
        fail(f"claim_id is not registered: {claim_id}")
    linked_manifest = manifest_path or _inferred_manifest(path)
    if linked_manifest is not None:
        try:
            manifest = validate_manifest(linked_manifest)
        except ValueError as exc:
            fail(f"cannot validate neighboring experiment manifest: {exc}")
        gates = cast(list[object], manifest["gates"])
        manifest_gate_ids: set[str] = set()
        for gate in gates:
            if isinstance(gate, dict):
                gate_id_value = cast(dict[str, object], gate).get("gate_id")
                if isinstance(gate_id_value, str):
                    manifest_gate_ids.add(gate_id_value)
        if gate_id not in manifest_gate_ids:
            fail(f"gate_id is not registered in experiment manifest: {gate_id}")
    if verdict["claim_tier"] not in CLAIM_TIERS:
        fail(f"claim_tier is not canonical: {verdict['claim_tier']}")
    if verdict["status"] not in EVIDENCE_STATUSES:
        fail(f"status is not canonical: {verdict['status']}")
    refs_value = verdict["evidence_refs"]
    if (
        not isinstance(refs_value, list)
        or not refs_value
        or any(not isinstance(ref, str) or not ref.strip() for ref in refs_value)
    ):
        fail("evidence_refs must be a non-empty list of paths")
    refs = cast(list[str], refs_value)
    if len(refs) != len(set(refs)):
        fail("evidence_refs contains duplicate values")
    for ref in refs:
        ref_path = root / ref
        if ref.startswith("/") or ".." in Path(ref).parts or not ref_path.is_file():
            fail(f"evidence_ref does not resolve to a committed file: {ref}")
    if "unit" in verdict and not isinstance(verdict["unit"], str):
        fail("unit must be a string")
    if "notes" in verdict and not isinstance(verdict["notes"], str):
        fail("notes must be a string")
    if "preregistration_sha256" in verdict:
        digest = verdict["preregistration_sha256"]
        if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
            fail("preregistration_sha256 must be a lowercase SHA-256 digest")
    return verdict


def discover_verdicts(root: Path = ROOT) -> list[Path]:
    experiments = root / "experiments"
    return sorted(experiments.glob("*/results/gate_verdicts/*.json")) if experiments.exists() else []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "verdicts",
        nargs="*",
        type=Path,
        help="gate verdict JSON files (default: experiments/*/results/gate_verdicts/*.json)",
    )
    args = parser.parse_args(argv)
    paths = args.verdicts or discover_verdicts()
    claims = known_claim_ids()
    for path in paths:
        try:
            verdict = validate(path, claims=claims)
        except ValueError as exc:
            print(f"[gate-verdict] FAIL: {exc}", file=sys.stderr)
            return 1
        print(f"[gate-verdict] PASS: {path} ({verdict['gate_id']}={verdict['status']})")
    if not paths:
        print("[gate-verdict] PASS: no gate verdicts discovered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
