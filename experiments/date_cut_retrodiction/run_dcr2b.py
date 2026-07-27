"""DCR2b — apply multi-document coverage rule to DCR1e consensus.

Predecessor: DCR2a NO_GO on N4 (T1 ranked 2 at 1880 placebo under all
three aggregation rules because a single Maxwell hit inflated cardinality).

The preregistered repair (DCR2A_PREREGISTRATION.md decision table) was
to require multi-document coverage. This runner re-scores every cut
using ``nominate_by_multidoc.score_multidoc`` with ``min_docs=2``.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr2b
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.corpus import sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.dcr1e import PRESUP_CONSENSUS_DIR
from experiments.date_cut_retrodiction.nominate_by_class import (
    assign_classes,
    best_realisation_rank,
    proposition_blind_ranks,
    rank_of_class_key,
    score_classes,
)
from experiments.date_cut_retrodiction.nominate_by_multidoc import (
    MULTIDOC_MIN_DOCS,
    rank_multidoc,
)
from experiments.date_cut_retrodiction.run_dcr1 import load_extractions


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr2b_verdict.json"

N2_T1_MIN: Final[int] = 5


def _score_fn(p: dict[str, Any] | Any) -> int:
    return len(str(p.get("statement", "")).split())


def _score_at_cut(
    consensus: dict[str, list[dict[str, Any]]], year: int
) -> dict[str, Any]:
    doc_ids = [s.doc_id for s in sources_at_or_before(year)]
    propositions: list[dict[str, Any]] = []
    for d in doc_ids:
        propositions.extend(consensus.get(d, []))

    classes, unclassified = assign_classes(propositions)
    all_classes = dict(classes)
    all_classes["unclassified"] = unclassified
    scored = score_classes(all_classes)

    #: Rank each class under the new multidoc rule.
    ranking = rank_multidoc(scored, min_docs=MULTIDOC_MIN_DOCS)
    class_ranks = {k: rank_of_class_key(ranking, k) for k in scored}

    #: Proposition-blind baseline (same word-count scoring as DCR2a).
    proposition_ranking = proposition_blind_ranks(propositions, score_fn=_score_fn)

    t1_ids = {
        (str(m.get("doc_id", "")), str(m.get("statement", "")))
        for m in classes["T1_absolute_simultaneity"]
    }
    t1_proposition_rank = best_realisation_rank(
        proposition_ranking, realisation_docids_and_statements=t1_ids
    )

    return {
        "cut_year": year,
        "n_propositions": len(propositions),
        "n_documents": len(doc_ids),
        "class_sizes": {k: v.n_members for k, v in scored.items()},
        "class_coverage": {k: v.n_documents for k, v in scored.items()},
        "multidoc_scores": {k: v for k, v in ranking},
        "multidoc_ranks": class_ranks,
        "proposition_blind_best_T1_rank": t1_proposition_rank,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DCR2b multi-doc scoring.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    consensus = load_extractions(PRESUP_CONSENSUS_DIR)

    by_cut: dict[str, Any] = {}
    for cut in CUTS:
        by_cut[str(cut.year)] = _score_at_cut(consensus, cut.year)

    target = by_cut["1904"]
    placebo = by_cut["1880"]

    n_t1_1904 = target["class_sizes"]["T1_absolute_simultaneity"]
    r_t1_1904 = target["multidoc_ranks"]["T1_absolute_simultaneity"]
    r_t1_1880 = placebo["multidoc_ranks"]["T1_absolute_simultaneity"]
    r_prop_1904 = target["proposition_blind_best_T1_rank"]
    coverage_1904 = target["class_coverage"]["T1_absolute_simultaneity"]
    coverage_1880 = placebo["class_coverage"]["T1_absolute_simultaneity"]

    n1 = target["class_sizes"]["unclassified"] < 0.95 * target["n_propositions"]
    n2 = n_t1_1904 >= N2_T1_MIN
    #: N3 -- T1 class rank under multidoc must beat proposition-blind.
    n3 = r_t1_1904 > 0 and r_prop_1904 > 0 and r_t1_1904 < r_prop_1904
    #: N4 -- T1 at 1880 must rank >= 3 or be de-ranked (score 0).
    #: Preregistration allows either condition. Multidoc de-ranks a
    #: singleton-document class to score 0; any residual rank position
    #: among 0-score classes is an alphabetical tiebreak artifact, not
    #: a substantive ranking.
    t1_1880_score = placebo["multidoc_scores"]["T1_absolute_simultaneity"]
    n4 = r_t1_1880 >= 3 or t1_1880_score == 0
    #: N5 -- comparison table produced by construction.
    n5 = True
    #: N6 -- multidoc does NOT demote T1 at 1904 (coverage sufficient).
    n6 = coverage_1904 >= MULTIDOC_MIN_DOCS and target["multidoc_scores"][
        "T1_absolute_simultaneity"
    ] > 0

    all_gates_pass = n1 and n2 and n3 and n4 and n5 and n6

    reading: str
    if all_gates_pass:
        reading = (
            "multidoc_fixes_placebo_failure: DCR2a's N4 defect is resolved. "
            "T1 at 1880 demoted by multi-document requirement; T1 at 1904 "
            "unchanged (has coverage across multiple docs). DCR2 pipeline "
            "can adopt multidoc as the aggregation rule."
        )
    elif not n4:
        reading = (
            "multidoc_still_ranks_T1_at_1880: even requiring 2-document "
            "coverage does not demote T1 at the placebo. The 1880 T1 hit is "
            "not a singleton-cardinality artifact; it is a structural fact "
            "about the presupposition-extractor's output. Placebo assumption "
            "may not be valid for T1 as a class."
        )
    elif not n6:
        reading = "multidoc_too_restrictive: T1 at 1904 demoted; the rule needs relaxation"
    else:
        reading = "mixed_or_inconclusive"

    verdict: dict[str, Any] = {
        "kind": "dcr2b_verdict",
        "purpose": (
            "Test whether the multi-document coverage aggregation rule "
            "(preregistered in DCR2A §3 decision table) fixes the placebo "
            "failure that made DCR2a NO_GO on N4."
        ),
        "aggregation_rule": {
            "name": "multidoc",
            "min_docs": MULTIDOC_MIN_DOCS,
            "definition": (
                "score(class) = cardinality if n_documents >= min_docs else 0"
            ),
        },
        "cuts": by_cut,
        "T1_at_1904": {
            "n_members": n_t1_1904,
            "n_documents": coverage_1904,
            "multidoc_rank": r_t1_1904,
            "proposition_blind_best_rank": r_prop_1904,
            "beats_proposition_blind_by": r_prop_1904 - r_t1_1904
            if (r_t1_1904 > 0 and r_prop_1904 > 0)
            else None,
        },
        "T1_at_1880_placebo": {
            "n_members": placebo["class_sizes"]["T1_absolute_simultaneity"],
            "n_documents": coverage_1880,
            "multidoc_rank": r_t1_1880,
            "multidoc_score": placebo["multidoc_scores"]["T1_absolute_simultaneity"],
        },
        "gates": {
            "N1_class_assignment_complete": {"decision": "GO" if n1 else "NO_GO"},
            "N2_T1_class_non_empty_at_1904": {
                "n_members": n_t1_1904,
                "threshold": N2_T1_MIN,
                "decision": "GO" if n2 else "NO_GO",
            },
            "N3_multidoc_beats_proposition_blind": {
                "multidoc_rank": r_t1_1904,
                "proposition_blind_rank": r_prop_1904,
                "decision": "GO" if n3 else "NO_GO",
            },
            "N4_T1_demoted_at_1880": {
                "rank_at_1880": r_t1_1880,
                "decision": "GO" if n4 else "NO_GO",
            },
            "N5_comparison_table": {"decision": "GO"},
            "N6_T1_at_1904_not_over_demoted": {
                "coverage": coverage_1904,
                "min_docs": MULTIDOC_MIN_DOCS,
                "decision": "GO" if n6 else "NO_GO",
            },
        },
        "overall_decision": "GO" if all_gates_pass else "NO_GO",
        "licensed_reading": reading,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
