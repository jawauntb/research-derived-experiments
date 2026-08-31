"""§0 Coverage envelope -- R-SCOPE-90, R-SCOPE-91 (sections/coverage.py)."""

from __future__ import annotations


def test_out_of_scope_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("OUT_OF_SCOPE__invalid.json"))
    result = run_claim("OUT_OF_SCOPE__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "OUT_OF_SCOPE"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-SCOPE-90"


def test_out_of_scope_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("OUT_OF_SCOPE__valid.json"))
    result = run_claim("OUT_OF_SCOPE__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def test_r_scope_91_fires_when_ledger_is_empty(bundle):
    # RULES-DECISION (see sections/coverage.py): with no whole-ledger
    # record-type scan available, R-SCOPE-91 is approximated via
    # `EvidenceLedger.count() == 0`. No fixture claim exercises this (the
    # synthetic world's ledger is never empty), so this direct unit test
    # is R-SCOPE-91's only coverage -- it targets `coverage.check` itself
    # rather than routing through the full claim pipeline.
    from normalize import CanonicalClaim

    from rules.sections import coverage

    empty_claim = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="33333333-3333-3333-3333-333333333333",
        subject_id="HGNC:5173",
        subject_label="IL6",
        relation="binds",
        object_id="HGNC:8975",
        object_label="IL6R",
        polarity="none",
        species="NCBITaxon:9606",
        cell_type="unspecified",
        cell_type_ancestors=(),
        cell_line=None,
        state=None,
        assay="co-IP",
        perturbation=None,
        evidence_ids=("perturbseq_v_test:5bde6e0544a4736f",),
        confidence_language="observed",
        requested_status="hypothesis",
    )

    class _EmptyLedger:
        def count(self) -> int:
            return 0

    class _EmptyLedgerBundle:
        ledger = _EmptyLedger()

    reason = coverage.check(empty_claim, cited=(), snapshot=_EmptyLedgerBundle())
    assert reason is not None
    assert reason.rule_id == "R-SCOPE-91"
