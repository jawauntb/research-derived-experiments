"""SnapshotBundle: ontology snapshots + the EvidenceLedger, as one immutable object.

Implements the ``Snapshot`` protocol defined by ``src/normalize/snapshot.py``
so that ``normalize_claim`` / ``normalize_evidence`` and the ``src/rules/``
cascade can be given the same bundle. The protocol is the canonical
contract; every method here matches its signature exactly (see
``bio-claim-firewall/src/INTERFACES.md``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

# Bare-form imports resolve via the top-level `bio-claim-firewall/conftest.py`
# which puts `bio-claim-firewall/src/` on sys.path. Not re-exporting the
# Snapshot protocol here — callers who want the protocol type import it
# directly from `normalize.snapshot`.
from normalize.errors import NormalizationError

from .ledger import EvidenceLedger
from .manifest import Manifest


@dataclass(frozen=True, slots=True)
class SnapshotBundle:
    """Merged, read-only view over every ontology snapshot plus the evidence ledger.

    Satisfies the ``Snapshot`` protocol from ``src/normalize/snapshot.py`` —
    ``contains``, ``canonicalize``, ``ancestors``, ``aliases`` all match its
    signatures and postconditions. Additionally exposes ``.ledger`` for rule
    modules that need evidence lookups directly (R-CONTRA-01 etc. via
    ``EvidenceLedger.list_by``).

    Built only by ``loader.load_bundle`` — constructing one by hand bypasses
    the hash-verification ``load_bundle`` performs, which defeats the point
    of a "frozen, hash-verified" snapshot. Tests may still construct one
    directly when they need to isolate SnapshotBundle's own logic from the
    loader.
    """

    manifests: Mapping[str, Manifest]
    ledger: EvidenceLedger
    curies: frozenset[str]
    alias_map: Mapping[str, str]
    ancestor_map: Mapping[str, tuple[str, ...]]
    # EVIDENCE-DECISION: optional, purely-rendering CURIE -> human-readable
    # label map, populated by loader.load_bundle from each ontology
    # source's optional `labels.jsonl` (see loader.py). Defaults to an
    # empty immutable mapping so existing callers that construct a
    # SnapshotBundle by hand (tests isolating SnapshotBundle's own logic
    # from the loader) don't need to pass it. `MappingProxyType` rather
    # than a bare `{}` default because a frozen dataclass's
    # `default_factory=dict` would otherwise hand back a *mutable* dict --
    # harmless in practice (nothing here mutates it) but inconsistent with
    # every other field on this frozen, read-only bundle.
    labels: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def contains(self, curie: str) -> bool:
        """True iff ``curie`` resolves, as-is, in a loaded ontology snapshot.

        Deprecated aliases (that forward-map onto a canonical CURIE via
        ``canonicalize``) return False here — R-ENT-02's semantics per the
        normalize.Snapshot protocol: ``contains`` is an as-is membership
        check, not a resolvability check. Callers who want the resolvability
        check compose ``contains(canonicalize(x))``.
        """
        return curie in self.curies

    def canonicalize(self, curie: str) -> str:
        """Forward-map a deprecated CURIE to its current canonical id.

        Returns ``curie`` unchanged if it is already canonical in a loaded
        snapshot. Raises ``NormalizationError`` (fault_code="UNKNOWN_ENTITY")
        if ``curie`` is neither canonical nor a known deprecated alias — the
        contract the normalize.Snapshot protocol imposes so ``normalize_claim``
        / ``normalize_evidence`` can surface UNKNOWN_ENTITY without doing a
        separate ``contains`` check for every CURIE-shaped field.
        """
        if curie in self.alias_map:
            return self.alias_map[curie]
        if curie in self.curies:
            return curie
        raise NormalizationError(
            f"{curie!r} does not resolve in any loaded ontology snapshot",
            fault_code="UNKNOWN_ENTITY",
            curie=curie,
        )

    def ancestors(self, curie: str) -> tuple[str, ...]:
        """The Cell Ontology ``is_a`` ancestor closure, specific to general.

        Only meaningful for ``CL:`` CURIEs — implementations return an empty
        tuple for any other prefix. The closure is precomputed and stored
        verbatim per-CURIE by the ontology snapshot file
        (``cell_ontology.jsonl``), so this is an O(1) dict lookup, not a
        graph walk. Returns ``()`` for a CURIE with no recorded ancestors
        (including one absent from the snapshot entirely) — callers combine
        it with ``contains`` when they need to distinguish "root/no
        ancestors" from "unknown CURIE".
        """
        return self.ancestor_map.get(curie, ())

    def label(self, curie: str) -> str | None:
        """The human-readable label recorded for ``curie`` by a loaded
        ontology snapshot's ``labels.jsonl``, or ``None`` if none was
        recorded (including for a CURIE absent from every snapshot
        entirely). Purely for rendering -- e.g. ``src/rules/licensing.py``'s
        accepted conditions -- never used for identity/matching.
        """
        return self.labels.get(curie)

    def aliases(self, curie: str) -> tuple[str, ...]:
        """The deprecated CURIEs that forward-map onto this canonical ``curie``.

        Reverse of ``canonicalize``: iterates the loaded ``deprecated ->
        canonical`` mapping and returns the deprecated keys that point at
        ``curie``. O(n) in the total alias count (small; there are at most a
        few thousand deprecated CURIEs across all loaded ontology sources).
        Returns ``()`` if no deprecated CURIE forwards onto ``curie``.
        """
        return tuple(dep for dep, canon in self.alias_map.items() if canon == curie)
