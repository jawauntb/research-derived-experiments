"""Exception type raised by src/normalize on malformed input or unresolved CURIEs.

The verifier's fault taxonomy (spec/fault_taxonomy.md) is a closed enum; this
module is only ever authorized to raise the `UNKNOWN_ENTITY` fault (surfaced
to the rule engine via `Snapshot.resolve()`-style calls inside
`normalize_claim()` / `normalize_evidence()`). Everything else this module
rejects — malformed shape, wrong types on fields that should already have
passed JSON Schema validation before reaching here — is a defensive contract
violation upstream of this module, not a claim-level rejection. Those errors
carry `fault_code=None` rather than inventing a new taxonomy code.
"""

from __future__ import annotations


class NormalizationError(Exception):
    """Raised when a Claim or EvidenceRecord dict cannot be normalized.

    Attributes:
        fault_code: `"UNKNOWN_ENTITY"` for an unresolved CURIE (the only fault
            code this module is authorized to raise, per
            spec/fault_taxonomy.md); `None` for defensive shape/type
            mismatches that indicate the input never actually passed schema
            validation.
        curie: The offending CURIE, if this error was raised while resolving
            one.
        where: A dotted path describing which field failed (e.g.
            `"subject.id"`, `"cell_context.cell_type"`), useful for logging
            and for the rule engine's own error reporting.
    """

    def __init__(
        self,
        message: str,
        *,
        fault_code: str | None = None,
        curie: str | None = None,
        where: str | None = None,
    ) -> None:
        super().__init__(message)
        self.fault_code = fault_code
        self.curie = curie
        self.where = where

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return (
            f"NormalizationError({self.args[0]!r}, fault_code={self.fault_code!r}, "
            f"curie={self.curie!r}, where={self.where!r})"
        )
