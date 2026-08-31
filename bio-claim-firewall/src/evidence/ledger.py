"""In-memory, dict-backed evidence ledger."""

from __future__ import annotations

from typing import Any

from .errors import EvidenceError


class EvidenceLedger:
    """All evidence records loaded from the frozen data root, keyed by ``evidence_id``.

    Constructed by ``loader.load_bundle``; not meant to be built by hand
    outside tests. ``records`` and ``record_file_hashes`` are taken by
    reference, not copied -- the loader owns the only reference that
    matters and this ledger is treated as read-only after construction.
    """

    def __init__(
        self,
        records: dict[str, dict[str, Any]],
        record_file_hashes: dict[str, str],
    ) -> None:
        self._records = records
        self._record_file_hashes = record_file_hashes

        # EVIDENCE-DECISION: precompute a (subject_id, object_id) -> [records]
        # index at construction time. R-CONTRA-01 needs repeated
        # same-subject/object scans across the whole ledger (opposite-sign
        # contradiction lookups); doing that as a linear scan per call would
        # make list_by O(n) per rule check instead of O(matches).
        self._by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for record in records.values():
            key = (record["subject"]["id"], record["object"]["id"])
            self._by_pair.setdefault(key, []).append(record)

    def get(self, evidence_id: str) -> dict[str, Any]:
        """Return the record for ``evidence_id``.

        Raises ``EvidenceError("BAD_CITATION", evidence_id=...)`` if it is
        not in the frozen ledger -- R-CITE-01.
        """
        try:
            return self._records[evidence_id]
        except KeyError as exc:
            raise EvidenceError("BAD_CITATION", evidence_id=evidence_id) from exc

    def list_by(
        self,
        subject_id: str,
        object_id: str,
        cell_type: str | None = None,
        cell_line: str | None = None,
        state: str | None = None,
        assay: str | None = None,
    ) -> list[dict[str, Any]]:
        """Records with this exact ``(subject_id, object_id)`` pair, optionally
        narrowed by context fields. Feeds R-CONTRA-01's opposite-sign scan.

        Each optional filter is applied only when non-``None``; ``None``
        means "don't filter on this field" (not "match null"), matching the
        claim-side waiver semantics in inference_rules.md §5.
        """
        candidates = self._by_pair.get((subject_id, object_id), [])
        if cell_type is None and cell_line is None and state is None and assay is None:
            return list(candidates)

        matched: list[dict[str, Any]] = []
        for record in candidates:
            cell_context = record["cell_context"]
            assay_context = record["assay_context"]
            if cell_type is not None and cell_context.get("cell_type") != cell_type:
                continue
            if cell_line is not None and cell_context.get("cell_line") != cell_line:
                continue
            if state is not None and cell_context.get("state") != state:
                continue
            if assay is not None and assay_context.get("assay") != assay:
                continue
            matched.append(record)
        return matched

    def count(self) -> int:
        """Total number of evidence records loaded across every source."""
        return len(self._records)

    def snapshot_hashes(self) -> dict[str, str]:
        """Map ``source name -> sha256`` of the ``records.jsonl`` file that
        source's records were loaded from (equal to that source's manifest
        ``sha256`` by construction -- ``load_bundle`` fails closed otherwise).
        """
        return dict(self._record_file_hashes)
