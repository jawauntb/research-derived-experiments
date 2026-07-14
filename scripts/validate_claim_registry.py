#!/usr/bin/env python3
"""Validate claim records and their references to the canonical evidence registry."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

try:
    from scripts.research_contracts import (
        CLAIM_ID,
        CLAIM_STATUSES,
        CLAIM_TIERS,
        EVIDENCE_ID,
        SCHEMA_VERSION,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/validate_claim_registry.py
    from research_contracts import (
        CLAIM_ID,
        CLAIM_STATUSES,
        CLAIM_TIERS,
        EVIDENCE_ID,
        SCHEMA_VERSION,
    )

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "docs" / "claim_registry.json"
EVIDENCE = ROOT / "docs" / "program_evidence_registry.json"
STATUSES = CLAIM_STATUSES
TIERS = CLAIM_TIERS
ROOT_FIELDS = {"schema_version", "generated_by", "claims"}
CLAIM_FIELDS = {"claim_id", "statement", "claim_tier", "status", "evidence_ids", "source_refs"}


def require_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label} must contain only strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicate values")
    return cast(list[str], value)


def validate(claims_path: Path = CLAIMS, evidence_path: Path = EVIDENCE) -> dict:
    try:
        claims = json.loads(claims_path.read_text())
        evidence = json.loads(evidence_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read registry: {exc}") from exc
    if not isinstance(claims, dict) or set(claims) != ROOT_FIELDS:
        raise ValueError(f"claim registry root fields must be exactly {sorted(ROOT_FIELDS)}")
    if claims.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"claim registry schema_version must be '{SCHEMA_VERSION}'")
    if not isinstance(claims.get("generated_by"), str) or not claims["generated_by"].strip():
        raise ValueError("claim registry generated_by must be a non-empty string")
    claim_records = claims.get("claims")
    if not isinstance(claim_records, list):
        raise ValueError("claim registry claims must be a list")
    if not isinstance(evidence, dict) or not isinstance(evidence.get("records"), list):
        raise ValueError("evidence registry records must be a list")
    evidence_by_id = {
        item.get("evidence_id"): item
        for item in evidence["records"]
        if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
    }
    seen: set[str] = set()
    claim_edges: dict[str, set[str]] = {}
    for index, claim in enumerate(claim_records):
        label = f"claims[{index}]"
        if not isinstance(claim, dict):
            raise ValueError(f"{label} must be an object")
        claim_record = cast(dict[str, object], claim)
        if set(claim_record) != CLAIM_FIELDS:
            raise ValueError(f"{label} fields must be exactly {sorted(CLAIM_FIELDS)}")
        claim_id = claim_record.get("claim_id")
        if not isinstance(claim_id, str) or CLAIM_ID.fullmatch(claim_id) is None:
            raise ValueError(f"{label}.claim_id is invalid")
        if claim_id in seen:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        seen.add(claim_id)
        for key in ("statement", "claim_tier", "status"):
            value = claim_record.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{label}.{key} must be a non-empty string")
        claim_tier = cast(str, claim_record["claim_tier"])
        status = cast(str, claim_record["status"])
        if claim_tier not in TIERS:
            raise ValueError(f"{label}.claim_tier is not canonical: {claim_tier}")
        if status not in STATUSES:
            raise ValueError(f"{label}.status is not canonical: {status}")
        refs = require_list(claim_record.get("evidence_ids"), f"{label}.evidence_ids")
        for ref in refs:
            if EVIDENCE_ID.fullmatch(ref) is None or ref not in evidence_by_id:
                raise ValueError(f"{label} references unknown evidence: {ref}")
        claim_edges[claim_id] = set(refs)
        source_refs = require_list(claim_record.get("source_refs"), f"{label}.source_refs")
        if any(not isinstance(ref, str) or not ref.strip() for ref in source_refs):
            raise ValueError(f"{label}.source_refs contains an empty reference")
    for evidence_id, record in evidence_by_id.items():
        linked_claims = record.get("claim_ids")
        if not isinstance(linked_claims, list):
            raise ValueError(f"evidence {evidence_id} claim_ids must be a list")
        for claim_id in linked_claims:
            if claim_id not in claim_edges:
                raise ValueError(f"evidence {evidence_id} references unknown claim: {claim_id}")
            if evidence_id not in claim_edges[claim_id]:
                raise ValueError(
                    f"claim/evidence edge is not bidirectional: {claim_id} -> {evidence_id}"
                )
    for claim_id, linked_evidence in claim_edges.items():
        for evidence_id in linked_evidence:
            record = evidence_by_id[evidence_id]
            linked_claims = record.get("claim_ids")
            if not isinstance(linked_claims, list) or claim_id not in linked_claims:
                raise ValueError(
                    f"claim/evidence edge is not bidirectional: {claim_id} -> {evidence_id}"
                )
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
