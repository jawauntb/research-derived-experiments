"""§1 Allowed prefixes -- R-ENT-01, R-ENT-02, R-ENT-03.

# RULES-DECISION: In the full `verify()` pipeline (src/INTERFACES.md),
# `normalize.normalize_claim()` already canonicalizes every CURIE-shaped
# field on the claim and raises `NormalizationError(fault_code=
# "UNKNOWN_ENTITY")` before a `CanonicalClaim` can even exist -- so a
# `RuleEngine.run()` call in that pipeline will never actually observe an
# unresolved entity on `canonical_claim` itself. `RuleEngine` should not
# structurally assume its caller always did that (defense in depth: the
# engine's contract is "given a `CanonicalClaim`", not "given a
# `CanonicalClaim` known to have come from a real `normalize_claim` call"),
# so this section re-validates `canonical_claim`'s own entity fields
# directly against the `Snapshot`. This also makes R-ENT-01/02/03
# independently testable/mutation-testable within `tests/rules/` by
# hand-building a `CanonicalClaim` with a bad id -- the same bypass the
# task's own instructions sanction for R-REL-01 (see "Handling
# INVALID_RELATION's schema-invalid fixture").
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason

ALLOWED_PREFIXES: frozenset[str] = frozenset(
    {"HGNC", "ENSEMBL", "UNIPROT", "MONDO", "CL", "GO", "CHEBI", "REACT", "NCBITaxon", "CLO"}
)

_UNSPECIFIED = "unspecified"


def _prefix_of(curie: str) -> str:
    return curie.split(":", 1)[0] if ":" in curie else curie


def _check_curie(
    curie: str,
    *,
    where: str,
    snapshot: SnapshotBundle,
    unresolved_rule_id: str,
) -> Reason | None:
    prefix = _prefix_of(curie)
    # MUTATION-POINT: an unlisted prefix is UNKNOWN_ENTITY regardless of
    # anything else -- R-ENT-01.
    if prefix not in ALLOWED_PREFIXES:
        return Reason(
            rule_id="R-ENT-01",
            message=f"{where} {curie!r} uses prefix {prefix!r}, which is not in the allowed-prefix table",
        )
    # MUTATION-POINT: an allowed prefix whose id isn't actually resolvable
    # in the frozen snapshot -- R-ENT-02 (or R-ENT-03 for cell_type).
    if not snapshot.contains(curie):
        return Reason(
            rule_id=unresolved_rule_id,
            message=f"{where} {curie!r} has an allowed prefix but does not resolve in the frozen snapshot",
        )
    return None


def check_all(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[Reason]:
    """Check every CURIE-shaped claim field, in subject/object/species/cell_type order.

    Stops at the first field with a finding (per-field, R-ENT-01 is
    checked before R-ENT-02/03), but reports every finding for that first
    problematic *rule* across all fields it applies to -- e.g. if both
    `subject.id` and `object.id` use a disallowed prefix, both R-ENT-01
    Reasons are returned together.
    """
    targets: list[tuple[str, str, str]] = [
        (claim.subject_id, "subject.id", "R-ENT-02"),
        (claim.object_id, "object.id", "R-ENT-02"),
        (claim.species, "species", "R-ENT-02"),
    ]
    if claim.cell_type != _UNSPECIFIED:
        targets.append((claim.cell_type, "cell_context.cell_type", "R-ENT-03"))
    if claim.cell_line is not None:
        targets.append((claim.cell_line, "cell_context.cell_line", "R-ENT-02"))

    reasons = [
        r
        for curie, where, unresolved_rule_id in targets
        if (r := _check_curie(curie, where=where, snapshot=snapshot, unresolved_rule_id=unresolved_rule_id))
        is not None
    ]
    if not reasons:
        return []

    # First-fired-rule-stops-the-section: keep only the highest-priority
    # rule id present (R-ENT-01 before R-ENT-02/03), across all targets.
    if any(r.rule_id == "R-ENT-01" for r in reasons):
        return [r for r in reasons if r.rule_id == "R-ENT-01"]
    return reasons
