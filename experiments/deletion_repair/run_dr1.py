"""DR1 orchestrator — score the nominators against the exhaustive oracle.

Run:
    uv run --no-sync python -m experiments.deletion_repair.run_dr1

Local CPU, seconds. Writes ``results/dr1_verdict.json``. The gates are frozen
in ``PREREGISTRATION.md`` sections 5 and 6 and are not tuned to produce a GO.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence

from experiments.deletion_repair.nominators import (
    NOMINATORS,
    rank,
    score_all,
    tie_fraction,
)
from experiments.deletion_repair.oracle import build_oracle
from experiments.deletion_repair.toys import ToySystem, all_toys


__all__ = ["main", "score_toy", "ToyScore"]

K: Final[int] = 3
ROOT = Path(__file__).resolve().parents[2]
VERDICT_PATH = ROOT / "experiments" / "deletion_repair" / "results" / "dr1_verdict.json"


@dataclass(frozen=True)
class NominatorScore:
    nominator: str
    recall_at_k: float
    hits_at_k: int
    recall_denominator: int
    simple_regret: int
    rank_of_first_load_bearing: int | None
    tie_fraction: float
    top_k: tuple[tuple[str, ...], ...]

    @property
    def silent(self) -> bool:
        """A nominator with every candidate tied has no opinion at all."""
        return self.tie_fraction >= 1.0


@dataclass(frozen=True)
class ToyScore:
    toy: str
    n_candidates: int
    load_bearing: tuple[tuple[str, ...], ...]
    scores: dict[str, NominatorScore]


def score_toy(toy: ToySystem, k: int = K) -> ToyScore:
    oracle = build_oracle(toy)
    load_bearing = set(oracle.load_bearing)
    deletions = [row.deletion for row in oracle.rows]
    all_scores = score_all(toy, deletions)

    denominator = min(k, len(load_bearing)) or 1
    out: dict[str, NominatorScore] = {}
    for name in NOMINATORS:
        scores = all_scores[name]
        ordering = rank(scores)
        top = tuple(ordering[:k])
        hits = sum(1 for d in top if d in load_bearing)
        first: int | None = None
        for index, deletion in enumerate(ordering, start=1):
            if deletion in load_bearing:
                first = index
                break
        out[name] = NominatorScore(
            nominator=name,
            recall_at_k=hits / denominator,
            hits_at_k=hits,
            recall_denominator=denominator,
            simple_regret=0 if (ordering and ordering[0] in load_bearing) else 1,
            rank_of_first_load_bearing=first,
            tie_fraction=tie_fraction(scores),
            top_k=top,
        )

    return ToyScore(
        toy=toy.name,
        n_candidates=len(deletions),
        load_bearing=tuple(sorted(load_bearing)),
        scores=out,
    )


def _in_top_k(score: ToyScore, nominator: str) -> bool:
    return score.scores[nominator].hits_at_k > 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR1.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    by_toy = {toy.name: score_toy(toy) for toy in all_toys()}
    tk = by_toy["toy_kinematics"]
    tt = by_toy["toy_transduction"]

    # --- H1: no single nominator succeeds on both toys (frozen section 6) ---
    h1_tk = _in_top_k(tk, "weakness") and not _in_top_k(tk, "cost")
    h1_tt = _in_top_k(tt, "cost") and not _in_top_k(tt, "weakness")
    h1_pass = bool(h1_tk and h1_tt)

    # --- H2: disjunctive is at least as good as the better single nominator ---
    def h2_for(score: ToyScore) -> bool:
        best_single = max(
            score.scores["weakness"].recall_at_k, score.scores["cost"].recall_at_k
        )
        return score.scores["disjunctive"].recall_at_k >= best_single

    h2_pass = bool(h2_for(tk) and h2_for(tt))

    # --- sanity: the real nominators must beat the controls somewhere ---
    def beats_controls(score: ToyScore, nominator: str) -> bool:
        ctrl = max(
            score.scores["random"].recall_at_k, score.scores["size_only"].recall_at_k
        )
        return score.scores[nominator].recall_at_k > ctrl

    sanity = any(
        beats_controls(s, n) for s in (tk, tt) for n in ("weakness", "cost")
    )

    verdict = {
        "kind": "dr1_verdict",
        "k": K,
        "toys": {
            name: {
                "n_candidates": s.n_candidates,
                "load_bearing": [list(d) for d in s.load_bearing],
                "nominators": {
                    n: {
                        "recall_at_k": v.recall_at_k,
                        "hits_at_k": v.hits_at_k,
                        "recall_denominator": v.recall_denominator,
                        "simple_regret": v.simple_regret,
                        "rank_of_first_load_bearing": v.rank_of_first_load_bearing,
                        "tie_fraction": v.tie_fraction,
                        "silent": v.silent,
                        "top_k": [list(d) for d in v.top_k],
                    }
                    for n, v in s.scores.items()
                },
            }
            for name, s in by_toy.items()
        },
        "H1_no_single_nominator_wins_both": {
            "tk_weakness_yes_cost_no": h1_tk,
            "tt_cost_yes_weakness_no": h1_tt,
            "decision": "GO" if h1_pass else "NO_GO",
        },
        "H2_disjunctive_at_least_best_single": {
            "toy_kinematics": h2_for(tk),
            "toy_transduction": h2_for(tt),
            "decision": "GO" if h2_pass else "NO_GO",
        },
        "sanity_beats_controls": sanity,
        "overall_decision": "GO" if (h1_pass and h2_pass and sanity) else "NO_GO",
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
