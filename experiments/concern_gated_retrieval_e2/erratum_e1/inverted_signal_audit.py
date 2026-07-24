"""Erratum E1 — the inverted-signal leakage gate.

The COGR program's leakage machinery audited two things: that policy code never
dereferences evaluator-only fields (``IntegrityAudit``), and that the *learned
geometry* carries no laundered label information (Wave 1b's G9
label-permutation and randomized-generator controls).

Neither could catch the defect this erratum records. ``care_anchors`` is a
**legitimate, policy-visible** field, so no integrity check fires on reading
it; and the leak lives in the hand-authored prior rather than in the learned
geometry, so G9 never looked at it.

The gate here is deliberately trivial, because the missed defect was trivial:
for every policy-visible signal ``s``, score the candidates by **both** ``s``
and ``-s`` against the answer key. A fixture leaks if *either* ordering reaches
oracle-level hit@1. One sort per signal per direction. Run at fixture-freeze
time, it would have caught this at Wave 0.

Nothing here reads a policy path; it is evaluator-side audit code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Final, Iterable, Mapping, Sequence


__all__ = [
    "ORACLE_LEAK_THRESHOLD",
    "SignalAuditRow",
    "audit_signal",
    "audit_care_anchors",
    "format_audit_table",
]


#: A fixture leaks if either ordering of any policy-visible signal reaches this
#: hit@1. Matches the ``oracle_recall_at_k < 0.8`` floor Wave 1b already used
#: for its generic-signal pre-run assertion, so the two gates agree.
ORACLE_LEAK_THRESHOLD: Final[float] = 0.8


@dataclass(frozen=True)
class SignalAuditRow:
    """hit@1 for one signal, scored in both directions."""

    signal: str
    n_episodes: int
    descending_hit_at_1: float
    ascending_hit_at_1: float

    @property
    def worst(self) -> float:
        """The leakier of the two orderings."""
        return max(self.descending_hit_at_1, self.ascending_hit_at_1)

    @property
    def leaks(self) -> bool:
        return self.worst >= ORACLE_LEAK_THRESHOLD

    @property
    def direction(self) -> str:
        if not self.leaks:
            return "none"
        return (
            "descending"
            if self.descending_hit_at_1 >= self.ascending_hit_at_1
            else "ascending (INVERTED)"
        )


def audit_signal(
    episodes: Iterable[object],
    signal_fn: Callable[[object], Mapping[str, float]],
    *,
    name: str,
) -> SignalAuditRow:
    """Score ``signal_fn`` against the answer key in both directions.

    ``signal_fn`` maps an episode to a per-node numeric signal. Each episode
    must expose ``candidate_nodes`` and the evaluator-only ``_answer_key``.
    """
    desc_hits = 0
    asc_hits = 0
    total = 0
    for episode in episodes:
        candidates: Sequence[str] = tuple(getattr(episode, "candidate_nodes"))
        if not candidates:
            continue
        answer = set(getattr(episode, "_answer_key"))
        signal = signal_fn(episode)
        total += 1
        # Ties broken by node id so both directions are deterministic and a
        # tie cannot be silently resolved in the auditor's favour.
        desc = sorted(candidates, key=lambda n: (-signal.get(n, 0.0), n))
        asc = sorted(candidates, key=lambda n: (signal.get(n, 0.0), n))
        desc_hits += desc[0] in answer
        asc_hits += asc[0] in answer

    if total == 0:
        return SignalAuditRow(name, 0, 0.0, 0.0)
    return SignalAuditRow(name, total, desc_hits / total, asc_hits / total)


def audit_care_anchors(episodes: Iterable[object]) -> SignalAuditRow:
    """Audit the concern prior -- the signal this erratum found leaking."""
    return audit_signal(
        episodes,
        lambda e: dict(getattr(e, "care_anchors")),
        name="care_anchors",
    )


def format_audit_table(rows: Sequence[SignalAuditRow]) -> str:
    """Render audit rows as a fixed-width table for receipts and logs."""
    header = (
        f"{'signal':<22}{'n':>7}{'desc':>9}{'asc':>9}{'worst':>9}  verdict"
    )
    lines = [header, "-" * len(header)]
    for row in rows:
        verdict = f"LEAK ({row.direction})" if row.leaks else "ok"
        lines.append(
            f"{row.signal:<22}{row.n_episodes:>7}"
            f"{row.descending_hit_at_1:>9.4f}{row.ascending_hit_at_1:>9.4f}"
            f"{row.worst:>9.4f}  {verdict}"
        )
    return "\n".join(lines)
