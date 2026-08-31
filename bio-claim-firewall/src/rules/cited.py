"""Internal container pairing a resolved evidence record's three shapes.

`RuleEngine.run()` builds one `CitedRecord` per `evidence_ids[i]` on the
claim (after a successful `EvidenceLedger.get()`), and every section in
`src/rules/sections/` receives the full tuple of them. Keeping the raw dict
alongside the canonicalized form lets `citations.py` check fields
(`snapshot_hash`, `citation_verified`) that `normalize.CanonicalEvidence`
deliberately does not carry, without any section needing to re-fetch from
the ledger itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from normalize import CanonicalEvidence


@dataclass(frozen=True, slots=True)
class CitedRecord:
    """One evidence record a claim cites, resolved and canonicalized once."""

    evidence_id: str
    raw: dict[str, Any]
    canonical: CanonicalEvidence
