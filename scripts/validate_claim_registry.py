#!/usr/bin/env python3
"""Validate claim records and their references to the canonical evidence registry."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "docs" / "claim_registry.json"
EVIDENCE = ROOT / "docs" / "program_evidence_registry.json"
STATUSES = {"supported", "rejected", "open", "inconclusive"}
TIERS = {"descriptive", "internal", "external", "causal", "theoretical"}
CLAIM_ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")
EVIDENCE_ID = re.compile(r"^EVID-[A-Z0-9][A-Z0-9_-]{2,63}$")


def require_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicate values")
    return value


def validate(claims_path: Path = CLAIMS, evidence_path: Path = EVIDENCE) -> dict:
    try:
        claims = json.loads(claims_path.read_text())
        evidence = json.loads(evidence_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read registry: {exc}") from exc
    if claims.get("schema_version") != "1.0":
        raise ValueError("claim registry schema_version must be '1.0'")
    evidence_ids = {item["evidence_id"] for item in evidence.get("records", [])}
    seen: set[str] = set()
    for index, claim in enumerate(claims.get("claims", [])):
        label = f"claims[{index}]"
        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or CLAIM_ID.fullmatch(claim_id) is None:
            raise ValueError(f"{label}.claim_id is invalid")
        if claim_id in seen:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        seen.add(claim_id)
        for key in ("statement", "claim_tier", "status"):
            if not isinstance(claim.get(key), str) or not claim[key].strip():
                raise ValueError(f"{label}.{key} must be a non-empty string")
        if claim["claim_tier"] not in TIERS:
            raise ValueError(f"{label}.claim_tier is not canonical: {claim['claim_tier']}")
        if claim["status"] not in STATUSES:
            raise ValueError(f"{label}.status is not canonical: {claim['status']}")
        refs = require_list(claim.get("evidence_ids"), f"{label}.evidence_ids")
        for ref in refs:
            if not isinstance(ref, str) or EVIDENCE_ID.fullmatch(ref) is None or ref not in evidence_ids:
                raise ValueError(f"{label} references unknown evidence: {ref}")
        source_refs = require_list(claim.get("source_refs"), f"{label}.source_refs")
        if any(not isinstance(ref, str) or not ref.strip() for ref in source_refs):
            raise ValueError(f"{label}.source_refs contains an empty reference")
    return claims


def main() -> int:
    try:
        payload = validate()
    except ValueError as exc:
        print(f"[claims] FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"[claims] PASS: {len(payload['claims'])} claims reference canonical evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
