"""The engine runs sections in the documented cascade order and stops at
the first rule that fires -- spec/inference_rules.md's `§Rule cascade
order`. Each claim below is hand-crafted so a LATER section's rule would
also fire if the cascade ever reached it, proving the earlier one really
does stop the cascade rather than just happening to be the only violation
present.
"""

from __future__ import annotations

from normalize import CanonicalClaim, normalize_claim

from rules import RuleEngine

_CLAIM_BAD_CITATION_AND_WOULD_BE_CONTEXT_MISMATCH = {
    "schema_version": "0.1.0",
    "claim_id": "11111111-1111-1111-1111-111111111111",
    "subject": {"id": "HGNC:1097", "label": "BRCA1"},
    "relation": "increases",
    "object": {"id": "HGNC:6407", "label": "KRAS"},
    "polarity": "positive",
    "species": "NCBITaxon:9606",
    # cell_line=CLO:0037231 (RPE1) would mismatch R1's CLO:0009454 (K562)
    # under R-CTX-03 -- IF the citation below resolved at all.
    "cell_context": {"cell_type": "CL:0000000", "cell_line": "CLO:0037231", "state": "resting"},
    "assay_context": {"assay": "CRISPRi_screen", "perturbation": "CRISPRi:HGNC:1097"},
    # Fabricated, non-resolving evidence_id -- R-CITE-01's territory.
    "evidence_ids": ["perturbseq_v_test:0000000000000000"],
    "confidence_language": "supported",
    "requested_status": "hypothesis",
}


def test_bad_citation_stops_cascade_before_context_mismatch(bundle):
    canonical = normalize_claim(_CLAIM_BAD_CITATION_AND_WOULD_BE_CONTEXT_MISMATCH, bundle)
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == "BAD_CITATION"
    assert len(result.reasons) == 1
    assert result.reasons[0].rule_id == "R-CITE-01"


def test_unknown_entity_stops_cascade_before_out_of_scope(bundle):
    # Hand-built CanonicalClaim bypassing normalize_claim (same bypass
    # pattern the task sanctions for INVALID_RELATION/R-REL-01 testing):
    # subject_id is unresolvable (R-ENT-02) AND species is outside the
    # coverage envelope (R-SCOPE-90, cascade position 3, AFTER R-ENT-* at
    # position 2). The citation resolves (a real evidence_id, R1) so the
    # cascade legitimately reaches R-ENT-* before anything else could stop
    # it first.
    canonical = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="22222222-2222-2222-2222-222222222222",
        subject_id="HGNC:9999999",
        subject_label="MADEUPKINASE",
        relation="increases",
        object_id="HGNC:6407",
        object_label="KRAS",
        polarity="positive",
        species="NCBITaxon:10090",  # mouse -- would fire R-SCOPE-90 if reached
        cell_type="unspecified",
        cell_type_ancestors=(),
        cell_line=None,
        state=None,
        assay="CRISPRi_screen",
        perturbation="CRISPRi:HGNC:9999999",
        evidence_ids=("perturbseq_v_test:fc1d7ea4dd7c21a7",),  # R1: a real citation
        confidence_language="observed",
        requested_status="hypothesis",
    )
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == "UNKNOWN_ENTITY"
    assert result.reasons[0].rule_id.startswith("R-ENT-")
