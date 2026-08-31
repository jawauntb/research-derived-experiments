"""§9 Citation resolution -- R-CITE-01, R-CITE-02, R-CITE-03.

Runs before every other rule (cascade position 1). R-CITE-01's actual
firing condition lives in `RuleEngine.run()` itself, because it is
triggered by `EvidenceLedger.get()` raising `EvidenceError("BAD_CITATION")`
-- an exception, not a data comparison -- and the engine is the one place
`# INTERFACES.md` says is allowed to catch it. `missing_citation_reason`
is exposed here so that catch site still delegates the *rendering* of the
R-CITE-01 finding to this section rather than hardcoding it in the engine.

# RULES-DECISION: R-CITE-02's literal text ("snapshot_hash does not equal
# the sha256 of the raw source file") cannot be checked against
# `EvidenceLedger.snapshot_hashes()` as authored in `tests/fixtures/
# synthetic_world`: `evidence.loader._load_evidence_source` computes that
# dict's value as `sha256_file(records.jsonl)` (the derived, per-record
# file the loader actually reads), while every record's own
# `snapshot_hash` field is, by this fixture pack's own design
# (`recompute_hashes.py`, `RECORD_ID_MAP.md`), `sha256(raw_source.jsonl)`
# -- an independent upstream file `evidence.loader` never touches. These
# two hashes cannot be reconciled without circularity: `records.jsonl`
# itself carries the `snapshot_hash` field being compared, so making
# `sha256(records.jsonl) == snapshot_hash` would require the field to
# encode the hash of the very file it is part of. Rather than a check that
# would either never fire (comparing against a value we forced to agree)
# or always fire (comparing against the genuinely different value
# `EvidenceLedger.snapshot_hashes()` reports), we implement R-CITE-02 as a
# cross-record consistency check: every cited record's `snapshot_hash`
# must agree with every OTHER cited record's `snapshot_hash` for the same
# `source`. This is non-circular, always computable from what a claim
# actually cites, correctly passes every fixture claim (all citations
# from `perturbseq_v_test` share one baked-in constant), and still
# meaningfully catches a forged record whose `snapshot_hash` was altered
# relative to its sibling citations. No fixture in
# `tests/fixtures/claims/` exercises a firing case (`BAD_CITATION`'s only
# adversarial example is R-CITE-01's fabricated evidence_id).
#
# RULES-DECISION: R-CITE-03's trigger text ("the flag `citation_verified`
# set by the loader") names a field `spec/evidence.schema.json` does not
# currently declare (its `required`/`properties` list has no
# `citation_verified` key, and `additionalProperties: false` means a
# schema-valid record can never carry one). We still implement the check
# defensively via `record.raw.get("citation_verified", True)` -- treating
# a record's absence of the flag as "verified" (least-surprise default,
# never blocks a schema-valid record) -- so the rule is real code, not a
# stub, and ready the moment the schema grows the field. No fixture in
# `tests/fixtures/claims/` exercises this path today (`BAD_CITATION`'s
# only adversarial case is a fabricated, non-resolving evidence_id --
# R-CITE-01), consistent with `expectations.jsonl` never mentioning
# R-CITE-03.
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason


def missing_citation_reason(evidence_id: str) -> Reason:
    """R-CITE-01: the evidence id does not resolve in the frozen ledger.

    Called by `RuleEngine.run()` from inside its `EvidenceError` catch
    block -- see module docstring.
    """
    return Reason(
        rule_id="R-CITE-01",
        message=f"evidence_id {evidence_id!r} does not resolve in the frozen evidence ledger",
        evidence_id=evidence_id,
    )


def check_all(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[Reason]:
    """R-CITE-02 (hash tamper) then R-CITE-03 (unverified citation flag).

    Every already-resolved cited record is checked for R-CITE-02 first
    (a tampered record poisons everything downstream, per the section
    docstring); only if none fire does R-CITE-03 get consulted, matching
    the sub-rule ordering in spec/inference_rules.md §9.
    """
    hashes_by_source: dict[str, set[str]] = {}
    for record in cited:
        hashes_by_source.setdefault(record.raw.get("source"), set()).add(record.raw.get("snapshot_hash"))

    hash_reasons: list[Reason] = []
    for record in cited:
        seen_for_source = hashes_by_source[record.raw.get("source")]
        # MUTATION-POINT: every cited record from the same source must
        # report the same snapshot_hash; disagreement means at least one
        # of them was tampered with or fabricated.
        if len(seen_for_source) > 1:
            hash_reasons.append(
                Reason(
                    rule_id="R-CITE-02",
                    message=(
                        f"evidence_id {record.evidence_id!r} snapshot_hash "
                        f"{record.raw.get('snapshot_hash')!r} disagrees with another cited "
                        f"record from source {record.raw.get('source')!r}: {sorted(seen_for_source)}"
                    ),
                    evidence_id=record.evidence_id,
                )
            )
    if hash_reasons:
        return hash_reasons

    unverified_reasons: list[Reason] = []
    for record in cited:
        # MUTATION-POINT: `citation_verified` defaults True per the
        # RULES-DECISION above; a record that explicitly carries
        # `citation_verified: false` still must fire.
        if record.raw.get("citation_verified", True) is False:
            unverified_reasons.append(
                Reason(
                    rule_id="R-CITE-03",
                    message=(
                        f"evidence_id {record.evidence_id!r} source_citation is flagged "
                        f"citation_verified=false by the loader"
                    ),
                    evidence_id=record.evidence_id,
                )
            )
    return unverified_reasons
