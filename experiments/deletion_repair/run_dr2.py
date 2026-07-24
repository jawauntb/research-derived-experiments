"""DR2 — does cheap nomination beat exhaustive search when exhaustive hurts?

Run:
    uv run --no-sync python -m experiments.deletion_repair.run_dr2

Gates are frozen in ``DR2_PREREGISTRATION.md`` §6 and are not tuned to produce
a GO. Local CPU, seconds. Writes ``results/dr2_verdict.json``.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping, Sequence

from experiments.deletion_repair.dr2_toys import dr2_toys
from experiments.deletion_repair.nominators import (
    cost_attribution,
    rank,
    tie_fraction,
    weakness_gain,
)
from experiments.deletion_repair.oracle import build_oracle, enumerate_deletions
from experiments.deletion_repair.toys import ToySystem


__all__ = ["main", "score_toy", "dr2_nominator_scores"]

MAX_D: Final[int] = 3
RECALL_K: Final[int] = 10
SPEEDUP_TARGET: Final[float] = 10.0
ROOT = Path(__file__).resolve().parents[2]
VERDICT_PATH = ROOT / "experiments" / "deletion_repair" / "results" / "dr2_verdict.json"

Scores = dict[tuple[str, ...], float]


def _normalise(values: Mapping[tuple[str, ...], float]) -> Scores:
    peak = max((abs(v) for v in values.values()), default=0.0)
    if peak <= 0.0:
        return {k: 0.0 for k in values}
    return {k: v / peak for k, v in values.items()}


def _rank_positions(scores: Scores) -> dict[tuple[str, ...], int]:
    return {d: i for i, d in enumerate(rank(scores), start=1)}


def dr2_nominator_scores(
    toy: ToySystem, deletions: Sequence[tuple[str, ...]]
) -> dict[str, Scores]:
    """All seven nominators. Higher score is better for every one of them."""
    import random as _random

    weak: Scores = {d: weakness_gain(toy, d) for d in deletions}
    cost: Scores = {d: cost_attribution(toy, d) for d in deletions}
    nw, nc = _normalise(weak), _normalise(cost)

    # Fix B: min-of-ranks -- being ranked highly by EITHER signal suffices.
    # Negated so that, as everywhere else, larger is better.
    wr, cr = _rank_positions(weak), _rank_positions(cost)
    minrank: Scores = {d: -float(min(wr[d], cr[d])) for d in deletions}

    rng = _random.Random(20_260_724)
    return {
        "weakness": weak,
        "cost": cost,
        "max_disjunction": {d: max(nw[d], nc[d]) for d in deletions},
        "sum_disjunction": {d: nw[d] + nc[d] for d in deletions},
        "minrank_disjunction": minrank,
        "random": {d: rng.random() for d in deletions},
        "size_only": {d: float(len(d)) for d in deletions},
    }


@dataclass(frozen=True)
class NominatorResult:
    nominator: str
    verifications_to_first_hit: int
    speedup_vs_random: float
    recall_at_k: float
    tie_fraction: float

    @property
    def silent(self) -> bool:
        return self.tie_fraction >= 1.0


@dataclass(frozen=True)
class ToyResult:
    toy: str
    n_candidates: int
    n_load_bearing: int
    expected_random: float
    results: dict[str, NominatorResult]

    @property
    def best_nominator(self) -> str:
        return min(
            self.results, key=lambda n: self.results[n].verifications_to_first_hit
        )


def score_toy(toy: ToySystem) -> ToyResult:
    oracle = build_oracle(toy, MAX_D)
    load_bearing = set(oracle.load_bearing)
    deletions = enumerate_deletions(toy, MAX_D)
    n = len(deletions)
    expected_random = (n + 1) / (len(load_bearing) + 1)

    out: dict[str, NominatorResult] = {}
    for name, scores in dr2_nominator_scores(toy, deletions).items():
        ordering = rank(scores)
        first = next(
            (i for i, d in enumerate(ordering, start=1) if d in load_bearing), n
        )
        hits = sum(1 for d in ordering[:RECALL_K] if d in load_bearing)
        out[name] = NominatorResult(
            nominator=name,
            verifications_to_first_hit=first,
            speedup_vs_random=expected_random / first,
            recall_at_k=hits / min(RECALL_K, len(load_bearing)),
            tie_fraction=tie_fraction(scores),
        )

    return ToyResult(
        toy=toy.name,
        n_candidates=n,
        n_load_bearing=len(load_bearing),
        expected_random=expected_random,
        results=out,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR2.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    by_toy = {t.name: score_toy(t) for t in dr2_toys()}
    sk = by_toy["scaled_kinematics"]
    st = by_toy["scaled_transduction"]

    # H1' dominance: the argmin nominator differs between the two toys.
    singles = ("weakness", "cost")
    best_single_sk = min(singles, key=lambda n: sk.results[n].verifications_to_first_hit)
    best_single_st = min(singles, key=lambda n: st.results[n].verifications_to_first_hit)
    h1 = best_single_sk != best_single_st

    # H2' combiner fix: sum or minrank no worse than the better single, on both.
    def better_single(toy: ToyResult) -> int:
        return min(toy.results[n].verifications_to_first_hit for n in singles)

    def combiner_ok(name: str) -> bool:
        return all(
            t.results[name].verifications_to_first_hit <= better_single(t)
            for t in (sk, st)
        )

    fixed = [n for n in ("sum_disjunction", "minrank_disjunction") if combiner_ok(n)]
    h2 = bool(fixed)

    # H3' earns its keep: best nominator gets >= 10x speedup on BOTH toys.
    h3 = all(
        max(r.speedup_vs_random for r in t.results.values()) >= SPEEDUP_TARGET
        for t in (sk, st)
    )

    verdict = {
        "kind": "dr2_verdict",
        "max_deletion_size": MAX_D,
        "speedup_target": SPEEDUP_TARGET,
        "toys": {
            name: {
                "n_candidates": t.n_candidates,
                "n_load_bearing": t.n_load_bearing,
                "base_rate": t.n_load_bearing / t.n_candidates,
                "expected_random_verifications": t.expected_random,
                "best_nominator": t.best_nominator,
                "nominators": {
                    n: {
                        "verifications_to_first_hit": r.verifications_to_first_hit,
                        "speedup_vs_random": r.speedup_vs_random,
                        "recall_at_10": r.recall_at_k,
                        "tie_fraction": r.tie_fraction,
                        "silent": r.silent,
                    }
                    for n, r in t.results.items()
                },
            }
            for name, t in by_toy.items()
        },
        "H1_dominance": {
            "best_single_scaled_kinematics": best_single_sk,
            "best_single_scaled_transduction": best_single_st,
            "decision": "GO" if h1 else "NO_GO",
        },
        "H2_combiner_fix": {
            "combiners_matching_best_single_on_both": fixed,
            "max_disjunction_ok": combiner_ok("max_disjunction"),
            "decision": "GO" if h2 else "NO_GO",
        },
        "H3_earns_its_keep": {
            "sk_best_speedup": max(r.speedup_vs_random for r in sk.results.values()),
            "st_best_speedup": max(r.speedup_vs_random for r in st.results.values()),
            "decision": "GO" if h3 else "NO_GO",
        },
        "overall_decision": "GO" if (h1 and h2 and h3) else "NO_GO",
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
