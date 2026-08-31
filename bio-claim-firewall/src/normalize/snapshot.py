"""Protocol describing the frozen-ontology-snapshot interface src/normalize needs.

This is a structural (`typing.Protocol`) contract only — no implementation
lives here. The real implementation is built by the evidence-loading module,
which reads the frozen ontology / alias / evidence snapshots under `data/`
and satisfies this Protocol. Anything with this shape (including
`tests/normalize/conftest.py`'s `FakeSnapshot`) can be passed to
`normalize_claim` / `normalize_evidence`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Snapshot(Protocol):
    """Read-only view over the verifier's frozen ontology/alias snapshots."""

    def contains(self, curie: str) -> bool:
        """Return True iff `curie` resolves, as-is, in the snapshot (no alias hop)."""
        ...

    def canonicalize(self, curie: str) -> str:
        """Forward-map a (possibly deprecated) CURIE to its current canonical id.

        Returns `curie` unchanged if it is already canonical. Raises
        `NormalizationError` (fault_code="UNKNOWN_ENTITY") if `curie` cannot
        be resolved by any means (not canonical, not a known alias).
        """
        ...

    def ancestors(self, curie: str) -> tuple[str, ...]:
        """Return the Cell Ontology `is_a` ancestor closure, specific to general.

        Only meaningful for `CL:` CURIEs; implementations return an empty
        tuple for any other prefix.
        """
        ...

    def aliases(self, curie: str) -> tuple[str, ...]:
        """Return the deprecated CURIEs that forward-map onto this canonical `curie`."""
        ...
