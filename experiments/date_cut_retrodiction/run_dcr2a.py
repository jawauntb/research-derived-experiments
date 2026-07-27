"""DCR2a — score the DCR1e consensus by class vs by proposition.

DCR1f established that T1 is a spectrum of realisations, not a discrete
commitment. DR5 (parallel theorem paper) formalises: a proposition-ranking
nominator cannot distinguish a commitment D from any specific r_i in
realisations(D).

DCR2a asks the empirical companion question: does class-based scoring
surface T1 in a way proposition-based scoring does not? See
``DCR2A_PREREGISTRATION.md`` for the five preregistered gates.

Runs class scoring under all three aggregation rules
(``cardinality``, ``coverage``, ``spread``), plus a proposition-blind
baseline, at each DCR1e cut. Reports the load-bearing comparison:

- rank of T1 as a class under each aggregation rule
- rank of the highest-scored T1 realisation under the proposition-blind
  baseline

Load-bearing gate (N3): rank_of_T1_class < rank_of_best_T1_realisation.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr2a
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from experiments.date_cut_retrodiction.corpus import sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.dcr1e import PRESUP_CONSENSUS_DIR
from experiments.date_cut_retrodiction.nominate_by_class import (
    AGGREGATION_RULES,
    assign_classes,
    best_realisation_rank,
    proposition_blind_ranks,
    rank_classes,
    rank_of_class_key,
    score_classes,
)
from experiments.date_cut_retrodiction.run_dcr1 import load_extractions


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr2a_verdict.json"

#: N2 preregistered threshold: T1 class must have at least this many
#: members at the 1904 cut.
N2_T1_MIN: Final[int] = 5


def _score_fn(p: Mapping[str, Any]) -> int:
    """Proposition-blind score: length of the statement in words.

    Simple, defensible baseline: longer statements carry more content and
    would be favoured by a naive length-based nominator. Any score
    function that is a function only of the individual proposition
    counts; word count is the least-tuned option and lets the paper argue
    that the class-vs-proposition comparison is not sensitive to score
    choice.
    """
    return len(str(p.get("statement", "")).split())


def _score_at_cut(
    consensus: dict[str, list[dict[str, Any]]],
    year: int,
) -> dict[str, Any]:
    doc_ids = [s.doc_id for s in sources_at_or_before(year)]
    propositions: list[dict[str, Any]] = []
    for d in doc_ids:
        propositions.extend(consensus.get(d, []))

    classes, unclassified = assign_classes(propositions)
    #: Add "unclassified" as its own class for scoring completeness.
    all_classes = dict(classes)
    all_classes["unclassified"] = unclassified
    scored = score_classes(all_classes)

    rankings: dict[str, list[tuple[str, int]]] = {}
    class_ranks: dict[str, dict[str, int]] = {}
    for rule in AGGREGATION_RULES:
        ranking = rank_classes(scored, rule=rule)
        rankings[rule] = ranking
        for cls_key in scored:
            class_ranks.setdefault(cls_key, {})[rule] = rank_of_class_key(
                ranking, cls_key
            )

    proposition_ranking = proposition_blind_ranks(propositions, score_fn=_score_fn)

    #: T1 realisation identities: (doc_id, statement) pairs of the
    #: propositions target_v4 assigned to the T1 class at this cut.
    t1_ids: set[tuple[str, str]] = {
        (str(m.get("doc_id", "")), str(m.get("statement", "")))
        for m in classes["T1_absolute_simultaneity"]
    }
    t2_ids: set[tuple[str, str]] = {
        (str(m.get("doc_id", "")), str(m.get("statement", "")))
        for m in classes["T2_privileged_frame"]
    }
    t3_ids: set[tuple[str, str]] = {
        (str(m.get("doc_id", "")), str(m.get("statement", "")))
        for m in classes["T3_local_time_artifice"]
    }

    best_ranks_proposition_blind = {
        "T1_absolute_simultaneity": best_realisation_rank(
            proposition_ranking, realisation_docids_and_statements=t1_ids
        ),
        "T2_privileged_frame": best_realisation_rank(
            proposition_ranking, realisation_docids_and_statements=t2_ids
        ),
        "T3_local_time_artifice": best_realisation_rank(
            proposition_ranking, realisation_docids_and_statements=t3_ids
        ),
    }

    return {
        "cut_year": year,
        "n_propositions": len(propositions),
        "n_documents": len(doc_ids),
        "class_sizes": {k: v.n_members for k, v in scored.items()},
        "class_coverage": {k: v.n_documents for k, v in scored.items()},
        "class_ranks_by_rule": class_ranks,
        "proposition_blind_baseline": {
            "n_propositions_ranked": len(proposition_ranking),
            "best_rank_per_class": best_ranks_proposition_blind,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DCR2a class-vs-proposition scoring.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    consensus = load_extractions(PRESUP_CONSENSUS_DIR)

    by_cut: dict[str, Any] = {}
    for cut in CUTS:
        by_cut[str(cut.year)] = _score_at_cut(consensus, cut.year)

    target = by_cut["1904"]
    placebo = by_cut["1880"]

    n_t1_at_1904 = target["class_sizes"]["T1_absolute_simultaneity"]
    n1 = target["class_sizes"]["unclassified"] < 0.95 * target["n_propositions"]
    n2 = n_t1_at_1904 >= N2_T1_MIN

    #: N3: T1 class rank higher than any single T1 realisation
    #: proposition-blind rank. Under proposition-blind ranking, best T1
    #: realisation gets rank R_prop. Under class ranking (any rule), T1
    #: class gets rank R_class. N3 asks R_class < R_prop for at least one
    #: aggregation rule.
    r_prop = target["proposition_blind_baseline"]["best_rank_per_class"][
        "T1_absolute_simultaneity"
    ]
    r_class_by_rule = {
        rule: target["class_ranks_by_rule"]["T1_absolute_simultaneity"][rule]
        for rule in AGGREGATION_RULES
    }
    n3 = any(r > 0 and r_prop > 0 and r < r_prop for r in r_class_by_rule.values())

    #: N4: T1 class rank at 1880 must be rank 3 or worse (below top-2)
    #: under every aggregation rule. Because there is only one T1
    #: realisation at 1880 (Maxwell), cardinality naturally puts T1
    #: below T2/T3/unclassified.
    r_t1_1880_by_rule = {
        rule: placebo["class_ranks_by_rule"]["T1_absolute_simultaneity"][rule]
        for rule in AGGREGATION_RULES
    }
    n4 = all(r >= 3 for r in r_t1_1880_by_rule.values() if r > 0)

    #: N5 is met by construction — the comparison table is the payload.
    n5 = True

    all_gates_pass = n1 and n2 and n3 and n4 and n5

    if all_gates_pass:
        licensed = (
            "DR5_empirical_companion_confirmed_on_this_corpus: class-based "
            "scoring surfaces T1 in a rank position higher than proposition-"
            "blind scoring gives any specific T1 realisation. DCR1f wall is "
            "avoidable via class-aware nomination on this corpus."
        )
    elif not n3:
        licensed = (
            "class_scoring_does_not_beat_proposition_baseline_on_this_corpus: "
            "T1 is not surfaced above proposition-blind ranking's best T1 "
            "realisation. Either T1 really is subordinate here or the "
            "aggregation rule is wrong. Try a different rule."
        )
    elif not n4:
        licensed = (
            "class_scoring_fails_placebo: T1 outranks other classes at 1880 "
            "under some rule, meaning cardinality-1 hits inflate the class "
            "rank. Aggregation rule must require multi-document coverage."
        )
    elif not n2:
        licensed = (
            "T1_class_too_small_at_1904: target_v4 lost coverage. Investigate "
            "extractor/matcher regression before drawing class-scoring "
            "conclusions."
        )
    elif not n1:
        licensed = (
            "class_scheme_too_narrow: over 95% of consensus propositions are "
            "unclassified. Introduce more facets before drawing conclusions."
        )
    else:
        licensed = "mixed_or_inconclusive"

    verdict: dict[str, Any] = {
        "kind": "dcr2a_verdict",
        "purpose": (
            "Empirical companion to DR5: does class-based scoring surface T1 "
            "in a way proposition-based scoring cannot?"
        ),
        "cuts": by_cut,
        "T1_at_1904": {
            "n_members": n_t1_at_1904,
            "n_documents": target["class_coverage"]["T1_absolute_simultaneity"],
            "class_rank_by_rule": r_class_by_rule,
            "best_realisation_rank_proposition_blind": r_prop,
            "class_beats_proposition_by": {
                rule: r_prop - r if (r > 0 and r_prop > 0) else None
                for rule, r in r_class_by_rule.items()
            },
        },
        "T1_at_1880_placebo": {
            "n_members": placebo["class_sizes"]["T1_absolute_simultaneity"],
            "class_rank_by_rule": r_t1_1880_by_rule,
        },
        "gates": {
            "N1_class_assignment_complete": {
                "unclassified_at_1904": target["class_sizes"]["unclassified"],
                "n_propositions_1904": target["n_propositions"],
                "decision": "GO" if n1 else "NO_GO",
            },
            "N2_T1_class_non_empty_at_1904": {
                "n_members": n_t1_at_1904,
                "threshold": N2_T1_MIN,
                "decision": "GO" if n2 else "NO_GO",
            },
            "N3_class_rank_beats_proposition_rank": {
                "class_rank_by_rule": r_class_by_rule,
                "proposition_blind_best_rank": r_prop,
                "decision": "GO" if n3 else "NO_GO",
            },
            "N4_placebo_T1_class_ranks_low_at_1880": {
                "rank_at_1880_by_rule": r_t1_1880_by_rule,
                "decision": "GO" if n4 else "NO_GO",
            },
            "N5_comparison_table_produced": {
                "decision": "GO" if n5 else "NO_GO",
            },
        },
        "overall_decision": "GO" if all_gates_pass else "NO_GO",
        "licensed_reading": licensed,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
