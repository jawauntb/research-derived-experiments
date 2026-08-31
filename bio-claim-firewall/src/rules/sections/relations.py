"""§2 Relation grammar -- R-REL-01, R-REL-02.

# RULES-DECISION: `INVALID_RELATION__invalid.json`'s adversarial value
# (`relation="regulates_epigenetically"`) is outside `claim.schema.json`'s
# closed `relation` enum, so it fails JSON-Schema validation before a
# `CanonicalClaim` can exist -- the fixture is intentionally not
# schema-valid (`expectations.jsonl`'s `schema_invalid: true`). Per the
# task brief, `tests/rules/test_r_rel.py` exercises R-REL-01 with a
# hand-built `CanonicalClaim` carrying a bogus `relation` string instead
# (Option 2). `CanonicalClaim.relation` is typed `Literal[...]` but that is
# a static-analysis-only annotation -- nothing at runtime stops a
# dataclass from holding an arbitrary string -- so this check is real,
# reachable code, not dead weight.
#
# RULES-DECISION: R-REL-02's condition ("polarity != none for binds or
# expressed_in") is a strict SUBSET of R-REL-01's ("(relation, polarity)
# is not a row of the grammar table") -- `ALLOWED_RELATION_POLARITY` only
# contains `(binds, none)`/`(expressed_in, none)`, so any other polarity
# for those two relations already fails R-REL-01 too. Checking R-REL-01
# first would make R-REL-02 permanently unreachable (dead code, and
# unmutation-testable). We check the more specific R-REL-02 condition
# FIRST, falling through to the general R-REL-01 check only when it
# doesn't apply -- the same "more specific rule wins" precedent
# `spec/inference_rules.md` §8 sets explicitly for R-CERT-02/R-CAUS-03.
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason
from ._shared import ALLOWED_RELATION_POLARITY

_NO_SIGN_RELATIONS = frozenset({"binds", "expressed_in"})


def check_all(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[Reason]:
    # MUTATION-POINT: binds/expressed_in are sign-less relations; any
    # polarity other than "none" overclaims a direction that doesn't exist.
    # Checked before R-REL-01 -- see the RULES-DECISION above.
    if claim.relation in _NO_SIGN_RELATIONS and claim.polarity != "none":
        return [
            Reason(
                rule_id="R-REL-02",
                message=f"relation {claim.relation!r} has no defined sign; "
                f"polarity must be 'none', got {claim.polarity!r}",
            )
        ]

    # MUTATION-POINT: (relation, polarity) must be a row of the grammar table.
    if (claim.relation, claim.polarity) not in ALLOWED_RELATION_POLARITY:
        return [
            Reason(
                rule_id="R-REL-01",
                message=f"(relation={claim.relation!r}, polarity={claim.polarity!r}) "
                f"is not a permitted pair in the relation grammar",
            )
        ]
    return []
