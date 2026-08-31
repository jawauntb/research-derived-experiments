"""Maps a `schema.SchemaFailure` to a (fault_code, rule_id) REJECTED
decision, or `None` when the violation should instead surface as
`CHECKER_ERROR` -- per this task's brief and spec/fault_taxonomy.md.

Only two schema-layer shapes are trusted enough to be treated as claim-level
faults (a `REJECTED_*` verdict) rather than a checker error:

- A CURIE-shaped field (`subject.id`, `object.id`, `species`) with the
  wrong prefix/shape -- `claim.schema.json`'s own regex already encodes
  the allowed-prefix table, so a `pattern` failure there is exactly
  R-ENT-01's trigger ("any CURIE's prefix is not in the table above").
- `relation` outside the closed enum -- exactly R-REL-01's trigger.

Everything else (a missing required field, wrong type, disallowed extra
property, an empty `evidence_ids` array, ...) means the untrusted proposer
emitted something the verifier cannot even interpret as a candidate claim.
Per spec/fault_taxonomy.md's own framing ("that is a proposer problem, not
a checker gap") and this task's explicit instruction, those are NOT folded
into the closed `fault_code` enum -- they surface as `CHECKER_ERROR`
instead, never as an invented/repurposed `REJECTED_*` code.
"""

from __future__ import annotations

from .schema import SchemaFailure

_ENTITY_CURIE_FIELDS = ("subject.id", "object.id", "species")


def fault_code_for_schema_failure(failure: SchemaFailure) -> tuple[str, str] | None:
    """Return `(fault_code, rule_id)` for a REJECTED-eligible schema failure,
    or `None` if it must instead render as `CHECKER_ERROR`.
    """
    if failure.constraint_kind == "pattern" and any(
        failure.field_path.startswith(prefix) for prefix in _ENTITY_CURIE_FIELDS
    ):
        return "UNKNOWN_ENTITY", "R-ENT-01"

    if failure.field_path == "relation" and failure.constraint_kind == "enum":
        return "INVALID_RELATION", "R-REL-01"

    if failure.field_path.endswith("evidence_ids") and failure.constraint_kind == "minItems":
        # MAPPING-DECISION: explicitly named in the task brief as a
        # CHECKER_ERROR path, not BAD_CITATION/UNSUPPORTED_EDGE -- an empty
        # evidence_ids array never reaches the rule cascade at all (it's a
        # schema violation, since claim.schema.json requires minItems: 1),
        # so there is no evidence-lookup fault to attribute here.
        return None

    return None
