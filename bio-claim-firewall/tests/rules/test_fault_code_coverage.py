"""Every fault code in spec/fault_taxonomy.md's closed enum has at least
one test whose `fault_code == <code>` assertion passes against the
fixtures pack. Data-driven from tests/fixtures/expectations.jsonl.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from normalize import CanonicalClaim, normalize_claim

from rules import RuleEngine

SPEC_DIR = Path(__file__).resolve().parents[2] / "spec"


def _closed_fault_codes() -> list[str]:
    verdict_schema = json.loads((SPEC_DIR / "verdict.schema.json").read_text())
    return sorted(c for c in verdict_schema["properties"]["fault_code"]["enum"] if c is not None)


CLOSED_FAULT_CODES = _closed_fault_codes()


def _hand_build_canonical_claim(claim_dict: dict) -> CanonicalClaim:
    """Bypass normalize_claim -- for the two fixtures whose adversarial
    condition cannot survive schema validation + normalization (see
    test_r_ent.py / test_r_rel.py's own RULES-DECISIONs)."""
    return CanonicalClaim(
        schema_version=claim_dict["schema_version"],
        claim_id=claim_dict["claim_id"],
        subject_id=claim_dict["subject"]["id"],
        subject_label=claim_dict["subject"]["label"],
        relation=claim_dict["relation"],
        object_id=claim_dict["object"]["id"],
        object_label=claim_dict["object"]["label"],
        polarity=claim_dict["polarity"],
        species=claim_dict["species"],
        cell_type=claim_dict["cell_context"]["cell_type"],
        cell_type_ancestors=(),
        cell_line=claim_dict["cell_context"].get("cell_line"),
        state=claim_dict["cell_context"].get("state"),
        assay=claim_dict["assay_context"]["assay"],
        perturbation=claim_dict["assay_context"].get("perturbation"),
        evidence_ids=tuple(claim_dict["evidence_ids"]),
        confidence_language=claim_dict["confidence_language"],
        requested_status=claim_dict["requested_status"],
    )


def test_every_closed_fault_code_is_represented_in_expectations(expectations):
    covered = {e["expected_fault_code"] for e in expectations if e.get("expected_fault_code")}
    missing = set(CLOSED_FAULT_CODES) - covered
    assert not missing, f"expectations.jsonl has no REJECTED coverage for {sorted(missing)}"


@pytest.mark.parametrize("fault_code", CLOSED_FAULT_CODES)
def test_fault_code_reachable_via_engine(fault_code, bundle, load_claim, expectations):
    entry = next(
        e
        for e in expectations
        if e.get("expected_fault_code") == fault_code and e["claim_path"].endswith("__invalid.json")
    )
    name = entry["claim_path"].split("/")[-1]
    claim_dict = load_claim(name)

    if entry.get("schema_invalid") or name == "UNKNOWN_ENTITY__invalid.json":
        # These two fixtures fail before a CanonicalClaim can exist via
        # the real pipeline (schema validation / normalize_claim
        # respectively) -- see test_r_rel.py / test_r_ent.py.
        canonical = _hand_build_canonical_claim(claim_dict)
    else:
        canonical = normalize_claim(claim_dict, bundle)

    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == fault_code
