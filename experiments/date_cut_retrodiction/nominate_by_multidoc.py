"""Multi-document coverage aggregation rule for DCR2b.

DCR2a's three rules all fired T1 at rank 2 at the 1880 placebo because a
single Maxwell 1865 hit dominated cardinality-based scoring. The
preregistered repair is to require multi-document coverage: a class with
members from fewer than ``min_docs`` distinct documents is de-ranked to
score 0, regardless of its member count.

This module does not edit ``nominate_by_class.py``. It composes with the
same ``ClassScore`` type by re-computing scores under the new rule.
"""

from __future__ import annotations

from typing import Final, Mapping, Sequence

from experiments.date_cut_retrodiction.nominate_by_class import ClassScore


__all__ = ["MULTIDOC_MIN_DOCS", "score_multidoc", "rank_multidoc"]

#: Preregistered threshold. A class must contribute from at least this
#: many distinct documents to be eligible for ranking. Singletons get 0.
MULTIDOC_MIN_DOCS: Final[int] = 2


def score_multidoc(
    scored: Mapping[str, ClassScore], *, min_docs: int = MULTIDOC_MIN_DOCS
) -> dict[str, int]:
    """Return the multidoc score for each class.

    Score is class cardinality if ``n_documents >= min_docs``, else 0.
    """
    return {
        key: (c.cardinality if c.n_documents >= min_docs else 0)
        for key, c in scored.items()
    }


def rank_multidoc(
    scored: Mapping[str, ClassScore], *, min_docs: int = MULTIDOC_MIN_DOCS
) -> list[tuple[str, int]]:
    """Return ranking (key, score) under the multidoc rule, best first.

    Ties broken by class key alphabetically.
    """
    scores = score_multidoc(scored, min_docs=min_docs)
    ordered = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    return ordered


def rank_of(ranking: Sequence[tuple[str, int]], key: str) -> int:
    for i, (k, _) in enumerate(ranking, start=1):
        if k == key:
            return i
    return -1
