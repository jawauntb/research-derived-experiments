"""DR4 — DR3 rerun with the costly toy's base rate repaired.

Run:
    uv run --no-sync python -m experiments.deletion_repair.run_dr4

Gates frozen in ``DR4_PREREGISTRATION.md``. Local CPU, seconds.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping, Sequence

from experiments.deletion_repair.dr3_toys import DR3Toy
from experiments.deletion_repair.dr4_toys import dr4_toys
from experiments.deletion_repair.nominators import rank, tie_fraction


__all__ = ["main", "score_toy", "dr4_scores", "enumerate_deletions"]

MAX_D: Final[int] = 3
SPEEDUP_TARGET: Final[float] = 10.0
ROOT = Path(__file__).resolve().parents[2]
VERDICT_PATH = ROOT / "experiments" / "deletion_repair" / "results" / "dr4_verdict.json"

Scores = dict[tuple[str, ...], float]


def enumerate_deletions(toy: DR3Toy, max_size: int = MAX_D) -> tuple[tuple[str, ...], ...]:
    names = [p.name for p in toy.deletable]
    out: list[tuple[str, ...]] = []
    for size in range(1, max_size + 1):
        out.extend(tuple(sorted(c)) for c in itertools.combinations(names, size))
    return tuple(out)


def weakness_gain(toy: DR3Toy, deletion: Sequence[str]) -> float:
    return float(len(toy.extension(frozenset(deletion))) - len(toy.extension()))


def cost_relief(toy: DR3Toy, deletion: Sequence[str]) -> float:
    """Resource commitment released by dropping ``deletion``.

    Note what this is *not*: a minimum over the extension. That was DR2's
    theorem premise, and severing it is the entire point of DR3.
    """
    return float(
        toy.representation_cost() - toy.representation_cost(frozenset(deletion))
    )


def _normalise(v: Mapping[tuple[str, ...], float]) -> Scores:
    peak = max((abs(x) for x in v.values()), default=0.0)
    return {k: 0.0 for k in v} if peak <= 0.0 else {k: x / peak for k, x in v.items()}


def dr4_scores(toy: DR3Toy, deletions: Sequence[tuple[str, ...]]) -> dict[str, Scores]:
    weak: Scores = {d: weakness_gain(toy, d) for d in deletions}
    cost: Scores = {d: cost_relief(toy, d) for d in deletions}
    nw, nc = _normalise(weak), _normalise(cost)
    wr = {d: i for i, d in enumerate(rank(weak), start=1)}
    cr = {d: i for i, d in enumerate(rank(cost), start=1)}
    rng = random.Random(20_260_724)
    return {
        "weakness": weak,
        "cost": cost,
        "max_disjunction": {d: max(nw[d], nc[d]) for d in deletions},
        "sum_disjunction": {d: nw[d] + nc[d] for d in deletions},
        "minrank_disjunction": {d: -float(min(wr[d], cr[d])) for d in deletions},
        "random": {d: rng.random() for d in deletions},
        "size_only": {d: float(len(d)) for d in deletions},
    }


@dataclass(frozen=True)
class NomResult:
    verifications_to_first_hit: int
    speedup_vs_random: float
    tie_fraction: float


@dataclass(frozen=True)
class ToyResult:
    toy: str
    n_candidates: int
    n_load_bearing: int
    expected_random: float
    independence: dict[str, int]
    results: dict[str, NomResult]


def score_toy(toy: DR3Toy) -> ToyResult:
    deletions = enumerate_deletions(toy)
    load_bearing = {
        d
        for d in deletions
        if toy.valid_on_alpha(frozenset(d)) and toy.covers_omega(frozenset(d))
    }
    n = len(deletions)
    expected_random = (n + 1) / (len(load_bearing) + 1)

    independence = {
        "cost_positive_weakness_zero": sum(
            1 for d in deletions if cost_relief(toy, d) > 0 and weakness_gain(toy, d) == 0
        ),
        "weakness_positive_cost_zero": sum(
            1 for d in deletions if cost_relief(toy, d) == 0 and weakness_gain(toy, d) > 0
        ),
        "both_positive": sum(
            1 for d in deletions if cost_relief(toy, d) > 0 and weakness_gain(toy, d) > 0
        ),
    }

    out: dict[str, NomResult] = {}
    for name, scores in dr4_scores(toy, deletions).items():
        ordering = rank(scores)
        first = next(
            (i for i, d in enumerate(ordering, start=1) if d in load_bearing), n
        )
        out[name] = NomResult(first, expected_random / first, tie_fraction(scores))

    return ToyResult(
        toy=toy.name,
        n_candidates=n,
        n_load_bearing=len(load_bearing),
        expected_random=expected_random,
        independence=independence,
        results=out,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DR4.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    by_toy = {t.name: score_toy(t) for t in dr4_toys()}
    rk = by_toy["restrictive_kinematics"]
    ct = by_toy["calibrated_costly_transduction"]
    singles = ("weakness", "cost")
    combiners = ("sum_disjunction", "minrank_disjunction", "max_disjunction")

    # H1''': independence -- cost fires where weakness is silent.
    h1 = ct.independence["cost_positive_weakness_zero"] > 0

    # H2''': complementarity -- the best single nominator differs between toys.
    best_single = {
        name: min(t.results[n].verifications_to_first_hit for n in singles)
        for name, t in by_toy.items()
    }
    argmin = {
        name: min(singles, key=lambda n: t.results[n].verifications_to_first_hit)
        for name, t in by_toy.items()
    }
    h2 = argmin["restrictive_kinematics"] != argmin["calibrated_costly_transduction"]

    # H3''': a combiner matches the best single on BOTH toys.
    matching = [
        c
        for c in combiners
        if all(
            t.results[c].verifications_to_first_hit <= best_single[name]
            for name, t in by_toy.items()
        )
    ]
    h3 = bool(matching)

    # H4''': speedup, on a toy whose base rate makes 10x reachable.
    h4 = all(
        max(r.speedup_vs_random for r in t.results.values()) >= SPEEDUP_TARGET
        for t in by_toy.values()
    )

    verdict = {
        "kind": "dr4_verdict",
        "toys": {
            name: {
                "n_candidates": t.n_candidates,
                "n_load_bearing": t.n_load_bearing,
                "expected_random_verifications": t.expected_random,
                "independence": t.independence,
                "nominators": {
                    n: {
                        "verifications_to_first_hit": r.verifications_to_first_hit,
                        "speedup_vs_random": r.speedup_vs_random,
                        "tie_fraction": r.tie_fraction,
                        "silent": r.tie_fraction >= 1.0,
                    }
                    for n, r in t.results.items()
                },
            }
            for name, t in by_toy.items()
        },
        "H1_independence_restored": {
            "cost_positive_weakness_zero_on_costly_toy": ct.independence[
                "cost_positive_weakness_zero"
            ],
            "decision": "GO" if h1 else "NO_GO",
        },
        "H2_complementarity": {
            "best_single_per_toy": argmin,
            "decision": "GO" if h2 else "NO_GO",
        },
        "H3_combiner_matches_best_single_on_both": {
            "matching_combiners": matching,
            "decision": "GO" if h3 else "NO_GO",
        },
        "H4_speedup_retained": {"decision": "GO" if h4 else "NO_GO"},
        "overall_decision": "GO" if (h1 and h2 and h3 and h4) else "NO_GO",
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
