"""Class-based scoring over the DCR1e consensus, for DCR2a.

The DCR1f arc reached its ceiling when target_v4 caught 7 T1 realisations
at the 1904 cut but also caught Maxwell 1865 at the 1880 placebo, and
failed held-out validation at 32.5%. The programmatic conclusion (DCR1f
§7): T1 is not a discrete commitment; it is a spectrum, and any
proposition-ranking nominator is agnostic between a commitment D and any
specific realisation r_i in the corpus.

This module implements the class-based counterpart. Propositions are
assigned to a class using target_v4's facet regex; each class is scored
under three aggregation rules (cardinality, coverage, spread); classes
are ranked; and the rank of the T1 class is compared to the rank a
proposition-blind nominator would assign to any specific T1 realisation.

The load-bearing observation this module supports (DCR2a N3): under
proposition-blind scoring, T1's best realisation lands at rank P_prop;
under class-based scoring, T1 as a class lands at rank P_class; DCR2a
asks whether P_class < P_prop.

This module does NOT import from the DR1-DR4 nominator infrastructure.
That is a deliberate simplification: DCR2a's question is about
class-vs-proposition scoring, not about the full deletion-repair pipeline.
A DCR2b would combine the two.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from experiments.date_cut_retrodiction.target_v4 import match_facets_v4


__all__ = [
    "AGGREGATION_RULES",
    "ClassScore",
    "assign_classes",
    "score_classes",
    "rank_classes",
    "proposition_blind_ranks",
]


@dataclass(frozen=True)
class ClassScore:
    key: str
    n_members: int
    n_documents: int
    cardinality: int
    coverage: int
    spread: int
    members: tuple[dict[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "n_members": self.n_members,
            "n_documents": self.n_documents,
            "cardinality": self.cardinality,
            "coverage": self.coverage,
            "spread": self.spread,
            "members": list(self.members),
        }


AGGREGATION_RULES: tuple[str, ...] = ("cardinality", "coverage", "spread")


def assign_classes(
    propositions: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Group propositions by target_v4 facet.

    A proposition can in principle belong to more than one class (the
    matcher matches across facets independently); this implementation
    treats each firing as a separate class membership. Propositions that
    match no facet go into ``unclassified``. Returned as (dict, list) of
    (class_dict, unclassified_list).
    """
    hits = match_facets_v4(propositions)
    classes: dict[str, list[dict[str, Any]]] = {
        "T1_absolute_simultaneity": [],
        "T2_privileged_frame": [],
        "T3_local_time_artifice": [],
    }
    for facet_key, matched in hits.items():
        classes[facet_key] = [dict(m) for m in matched]

    matched_ids: set[tuple[str, str]] = set()
    for facet_hits in hits.values():
        for h in facet_hits:
            matched_ids.add((str(h.get("doc_id", "")), str(h.get("statement", ""))))

    unclassified: list[dict[str, Any]] = []
    for p in propositions:
        key = (str(p.get("doc_id", "")), str(p.get("statement", "")))
        if key not in matched_ids:
            unclassified.append(dict(p))

    return classes, unclassified


def score_classes(
    classes: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, ClassScore]:
    """Score each class under all three aggregation rules."""
    scored: dict[str, ClassScore] = {}
    for key, members in classes.items():
        n = len(members)
        docs = {str(m.get("doc_id", "")) for m in members}
        n_docs = len(docs)
        scored[key] = ClassScore(
            key=key,
            n_members=n,
            n_documents=n_docs,
            cardinality=n,
            coverage=n_docs,
            spread=n * n_docs,
            members=tuple(dict(m) for m in members),
        )
    return scored


def rank_classes(
    scored: Mapping[str, ClassScore], *, rule: str
) -> list[tuple[str, int]]:
    """Return a ranking of class keys by score under ``rule``. Ties broken by key."""
    if rule not in AGGREGATION_RULES:
        raise ValueError(f"unknown rule: {rule!r}")
    scoring: Callable[[ClassScore], int] = {
        "cardinality": lambda c: c.cardinality,
        "coverage": lambda c: c.coverage,
        "spread": lambda c: c.spread,
    }[rule]
    ordered = sorted(scored.values(), key=lambda c: (-scoring(c), c.key))
    return [(c.key, scoring(c)) for c in ordered]


def proposition_blind_ranks(
    propositions: Sequence[Mapping[str, Any]],
    *,
    score_fn: Callable[[Mapping[str, Any]], int],
) -> list[tuple[dict[str, Any], int]]:
    """Rank every proposition individually by score_fn, best first.

    ``score_fn`` receives a proposition and returns an int score. Ties
    broken by (statement) alphabetical.
    """
    scored = [(dict(p), score_fn(p)) for p in propositions]
    scored.sort(key=lambda pair: (-pair[1], pair[0].get("statement", "")))
    return scored


def rank_of_class_key(
    ranking: Sequence[tuple[str, int]], key: str
) -> int:
    """Return the 1-indexed rank of ``key`` in ``ranking``."""
    for i, (k, _) in enumerate(ranking, start=1):
        if k == key:
            return i
    return -1


def best_realisation_rank(
    ranking: Sequence[tuple[dict[str, Any], int]],
    *,
    realisation_docids_and_statements: set[tuple[str, str]],
) -> int:
    """Return the 1-indexed rank of the highest-ranked proposition that
    belongs to a target realisation set."""
    for i, (p, _) in enumerate(ranking, start=1):
        key = (str(p.get("doc_id", "")), str(p.get("statement", "")))
        if key in realisation_docids_and_statements:
            return i
    return -1
