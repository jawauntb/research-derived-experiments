"""DCR3 — execution-free per-proposition scoring for class-based nomination.

DR3-arc precedent: DR1-DR4 use per-proposition scores of the form
``kind_weight * evidence_weight``. DCR3 adapts that to the DCR1e consensus:

- ``kind_weight`` reflects the DR-arc's stated preference for
  presuppositional / argument-required commitments over asserted ones.
- ``degree`` is the number of documents at the cut that share
  content-stem-equivalent propositions -- a purely execution-free
  quantity computed from the corpus at the cut, with no post-cut access.

Class-level score = sum of member scores (multidoc gating applied
externally in the runner).

No tuning: kind_weight is an ordinal 3/2/1 triple reflecting DR-arc
prior; degree uses the identical Jaccard threshold from
``consensus.py``. This module is committed as-is; a regression test in
run_dcr3 pins the definition.
"""

from __future__ import annotations

from typing import Any, Final, Mapping, Sequence

from experiments.date_cut_retrodiction.consensus import _content, _jaccard, EQUIVALENCE_THRESHOLD


__all__ = [
    "KIND_WEIGHT",
    "score_proposition",
    "degree_in_cut",
]


#: DR-arc's stated preference: presuppositional/argument-required over asserted.
#: These are ordinal and preregistered in DCR3_PREREGISTRATION.md §2.
KIND_WEIGHT: Final[dict[str, int]] = {
    "required_by_argument": 3,
    "presupposed": 2,
    "asserted": 1,
}


def degree_in_cut(
    proposition: Mapping[str, Any],
    cut_propositions: Sequence[Mapping[str, Any]],
    *,
    equivalence_threshold: float = EQUIVALENCE_THRESHOLD,
) -> int:
    """Count distinct documents in the cut that carry content-equivalent props.

    Uses identical Jaccard equivalence to ``consensus.py``: two
    propositions are equivalent iff their content-stem Jaccard is at
    least ``equivalence_threshold``. Returns the number of distinct
    documents (including the proposition's own document if any of its
    docmates qualify).
    """
    my_content = _content(str(proposition.get("statement", "")))
    if not my_content:
        return 0

    docs: set[str] = set()
    for other in cut_propositions:
        other_content = _content(str(other.get("statement", "")))
        if not other_content:
            continue
        if _jaccard(my_content, other_content) >= equivalence_threshold:
            doc = str(other.get("doc_id", ""))
            if doc:
                docs.add(doc)
    return len(docs)


def score_proposition(
    proposition: Mapping[str, Any],
    cut_propositions: Sequence[Mapping[str, Any]],
) -> int:
    """Execution-free score: kind_weight(p) * degree(p)."""
    kind = str(proposition.get("kind", "asserted"))
    weight = KIND_WEIGHT.get(kind, 1)
    d = degree_in_cut(proposition, cut_propositions)
    return weight * d
