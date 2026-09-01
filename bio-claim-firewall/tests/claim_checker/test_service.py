"""Behavioral tests for the deterministic K562 claim-checking surface."""

from __future__ import annotations

from types import MappingProxyType, SimpleNamespace

import pytest
from claim_checker.__main__ import format_result
from claim_checker.service import (
    ClaimCheckInputError,
    ClaimCheckResult,
    check_k562_claim,
)
from evidence import EvidenceLedger
from evidence.snapshot import SnapshotBundle
from worlds import K562_WORLD

_SOURCE_HASHES = {
    contract.source: contract.sha256 for contract in K562_WORLD.source_contracts
}


def _record(
    *,
    evidence_id: str = "perturbseq.replogle_2022:test-record",
    sign: str = "positive",
    subject_id: str = "HGNC:1",
    subject_label: str = "MED19",
    object_id: str = "HGNC:2",
    object_label: str = "GYPB",
) -> dict:
    return {
        "evidence_id": evidence_id,
        "source": "perturbseq.replogle_2022",
        "snapshot_hash": "a" * 64,
        "record_type": "perturbation_effect",
        "subject": {"id": subject_id, "label": subject_label},
        "object": {"id": object_id, "label": object_label},
        "species": "NCBITaxon:9606",
        "cell_context": {
            "cell_type": "CL:0000988",
            "cell_line": "CLO:0007059",
            "state": "resting",
        },
        "assay_context": {
            "assay": "CRISPRi_screen",
            "perturbation": f"CRISPRi:{subject_id}",
        },
        "observation_type": "interventional",
        "effect": {
            "sign": sign,
            "magnitude": 1.25,
            "magnitude_scale": "zscore_mean_expression",
            "significance": None,
            "n_replicates": None,
        },
        "contradicts": [],
        "retrieved_at": "2026-08-31T00:00:00+00:00",
        "license": "CC0-1.0",
        "schema_version": "0.1.0",
        "source_citation": "Replogle et al. 2022",
    }


def _bundle(*records: dict) -> SnapshotBundle:
    labels = {
        "HGNC:1": "MED19",
        "HGNC:2": "GYPB",
        "NCBITaxon:9606": "Homo sapiens",
        "CL:0000988": "hematopoietic cell",
        "CLO:0007059": "K-562 cell",
    }
    return SnapshotBundle(
        manifests={
            source: SimpleNamespace(sha256=digest)
            for source, digest in _SOURCE_HASHES.items()
        },
        ledger=EvidenceLedger(
            {record["evidence_id"]: record for record in records},
            _SOURCE_HASHES,
        ),
        curies=frozenset(labels),
        alias_map=MappingProxyType({}),
        ancestor_map=MappingProxyType({}),
        labels=MappingProxyType(labels),
    )


def test_check_accepts_exact_hgnc_symbols_against_one_frozen_record():
    result = check_k562_claim(_bundle(_record()), "med19", "GYPB", "increases")

    assert result.verdict["verdict"] == "ACCEPTED_CONDITIONALLY"
    assert result.evidence is not None
    assert result.claim is not None
    assert result.evidence["evidence_id"] == "perturbseq.replogle_2022:test-record"
    assert result.evidence["citation"] == "Replogle et al. 2022"
    assert result.claim["subject"] == {"id": "HGNC:1", "label": "MED19"}
    assert result.claim["object"] == {"id": "HGNC:2", "label": "GYPB"}
    assert result.as_dict()["verdict"]["snapshot_hashes"] == _SOURCE_HASHES


def test_check_uses_the_verifier_to_reject_a_sign_reversal():
    result = check_k562_claim(_bundle(_record()), "MED19", "GYPB", "decreases")

    assert result.verdict["verdict"] == "REJECTED"
    assert result.verdict["fault_code"] == "SIGN_MISMATCH"
    assert result.evidence is not None
    assert result.evidence["effect_sign"] == "positive"


def test_check_fails_closed_to_inconclusive_when_the_pair_is_not_frozen():
    result = check_k562_claim(_bundle(_record()), "MED19", "GYPB", "increases")
    missing = check_k562_claim(_bundle(), "MED19", "GYPB", "increases")

    assert result.verdict["verdict"] == "ACCEPTED_CONDITIONALLY"
    assert missing.verdict["verdict"] == "INCONCLUSIVE"
    assert missing.verdict["reason"] == (
        "No exact frozen Replogle 2022 K562 CRISPRi record matches this gene pair."
    )
    assert missing.verdict["checker_version"] == "0.1.0"
    assert missing.verdict["snapshot_hashes"] == _SOURCE_HASHES
    assert missing.claim is None
    assert missing.evidence is None


def test_check_reports_a_measured_null_effect_without_claiming_the_pair_is_absent():
    result = check_k562_claim(
        _bundle(_record(sign="null")), "MED19", "GYPB", "increases"
    )

    assert result.verdict["verdict"] == "INCONCLUSIVE"
    assert result.verdict["reason"] == (
        "The exact frozen Replogle 2022 K562 CRISPRi record for this gene "
        "pair records no directional effect."
    )
    assert result.verdict["snapshot_hashes"] == _SOURCE_HASHES
    assert result.claim is None
    assert result.evidence is None


def test_check_refuses_ambiguous_frozen_evidence_instead_of_picking_one():
    first = _record(evidence_id="perturbseq.replogle_2022:first")
    second = _record(evidence_id="perturbseq.replogle_2022:second")

    result = check_k562_claim(_bundle(first, second), "MED19", "GYPB", "increases")

    assert result.verdict["verdict"] == "INCONCLUSIVE"
    assert result.verdict["reason"] == (
        "Multiple exact frozen Replogle 2022 K562 CRISPRi records match this gene pair."
    )
    assert result.verdict["snapshot_hashes"] == _SOURCE_HASHES
    assert result.claim is None
    assert result.evidence is None


def test_legacy_wrapper_rejects_hash_valid_foreign_source_bundle():
    bundle = _bundle(_record())
    manifests = dict(bundle.manifests)
    manifests["foreign.source"] = manifests.pop("perturbseq.replogle_2022")
    foreign_bundle = SnapshotBundle(
        manifests=manifests,
        ledger=bundle.ledger,
        curies=bundle.curies,
        alias_map=bundle.alias_map,
        ancestor_map=bundle.ancestor_map,
        labels=bundle.labels,
    )

    result = check_k562_claim(foreign_bundle, "MED19", "GYPB", "increases")

    assert result.verdict["verdict"] == "CHECKER_ERROR"
    assert "sources do not exactly match" in result.verdict["checker_error"]["message"]


@pytest.mark.parametrize("value", ["raises", "", "more strongly increases"])
def test_check_rejects_directions_outside_its_declared_claim_grammar(value):
    with pytest.raises(ClaimCheckInputError, match="increases or decreases"):
        check_k562_claim(_bundle(_record()), "MED19", "GYPB", value)


def test_check_rejects_an_unknown_gene_symbol_without_asking_the_verifier_to_guess():
    with pytest.raises(ClaimCheckInputError, match="does not resolve"):
        check_k562_claim(_bundle(_record()), "NOT_A_GENE", "GYPB", "increases")


def test_text_rendering_exposes_the_decisive_rule_and_scope_for_an_acceptance():
    result = check_k562_claim(_bundle(_record()), "MED19", "GYPB", "increases")

    rendered = format_result(result)

    assert "Winning rule: R-EDGE-02" in rendered
    assert "magnitude 1.25 zscore_mean_expression" in rendered
    assert "significance not reported" in rendered
    assert "Scope: only in cell_line=CLO:0007059" in rendered


def test_text_rendering_keeps_a_checker_failure_separate_from_claim_evidence():
    result = ClaimCheckResult(
        claim={"subject": {"label": "MED19"}},
        evidence={"evidence_id": "replogle:test"},
        verdict={
            "verdict": "CHECKER_ERROR",
            "checker_error": {"stage": "run_rules", "message": "rule load failed"},
        },
    )
    rendered = format_result(result)

    assert (
        rendered
        == "Verdict: CHECKER_ERROR\nChecker error: run_rules — rule load failed"
    )
