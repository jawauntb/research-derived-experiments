"""Erratum E1 — does Wave 1b's L1 KILL survive the repaired prior?

`ERRATUM.md` §4 argues analytically that the inverted-oracle leak cannot have
produced Wave 1b's L1 KILL: the contrast is ``LEARNED`` vs
``FREQ_MATCHED_RANDOM`` geometry with ``FROZEN_WRONG`` concern held *identical*
in both arms, so the leak is present equally on both sides and cancels in the
paired difference.

That is an argument. This module measures it.

Method: run Wave 1b's **own** ``crossed.run_cell`` code path unchanged, and
swap only the concern prior, by wrapping the module-level
``crossed._FAMILY_GENERATORS`` so each generated episode passes through
``prior_repair.repair_wrong_prior``. Everything else -- geometry construction,
ranking, sealed scoring, seeds -- is byte-identical to the confirmatory run.

If the L1 contrast stays at approximately zero under a non-leaky prior, the
KILL is confirmed on clean data and is upgraded from argued to measured. If it
moves, the headline result of PR #413 needs revisiting.

Run:
    COGR_WAVE0_CONFIRMATORY_RUN=1 uv run --no-sync python -m \\
      experiments.concern_gated_retrieval_e2.erratum_e1.verify_l1_under_repair
"""

from __future__ import annotations

import argparse
import contextlib
import json
import random
import statistics
from pathlib import Path
from typing import Any, Callable, Final, Iterator, Sequence

from experiments.concern_gated_retrieval_e2.wave1b import crossed
from experiments.concern_gated_retrieval_e2.wave1b.crossed import (
    CONCERN_FROZEN_WRONG,
    CellSpec,
    run_cell,
)

from experiments.concern_gated_retrieval_e2.erratum_e1.prior_repair import (
    DEFAULT_SUPPRESSED_SET_SIZE,
    repair_wrong_prior,
)


__all__ = ["main", "paired_contrast", "repaired_generators"]

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_PATH = (
    ROOT
    / "experiments"
    / "concern_gated_retrieval_e2"
    / "erratum_e1"
    / "results"
    / "l1_under_repair_receipt.json"
)

#: Wave 1b's frozen per-family L1 threshold (PREREGISTRATION.md section 11).
DELTA_THRESH_L1: Final[dict[str, float]] = {
    "delayed_commitments": 0.04845,
    "maintenance_fault": 0.05340,
    "resource_constrained": 0.05000,
}

#: The confirmatory slice Wave 1b actually ran for delayed_commitments.
DEFAULT_FAMILY: Final[str] = "delayed_commitments"
DEFAULT_SEED_LO: Final[int] = 200_000
BOOTSTRAP_RESAMPLES: Final[int] = 2_000
BOOTSTRAP_SEED: Final[int] = 20_260_724


@contextlib.contextmanager
def repaired_generators(k: int = DEFAULT_SUPPRESSED_SET_SIZE) -> Iterator[None]:
    """Temporarily wrap Wave 1b's family generators with the prior repair.

    Wave 1b's package is frozen and is not edited on disk; this patches the
    in-memory dispatch table for the duration of the block only.
    """
    original: dict[str, Callable[..., Any]] = dict(crossed._FAMILY_GENERATORS)
    try:
        for name, generate in original.items():

            def wrapped(*args: Any, _g=generate, **kwargs: Any) -> Any:
                return repair_wrong_prior(_g(*args, **kwargs), k=k)

            crossed._FAMILY_GENERATORS[name] = wrapped
        yield
    finally:
        crossed._FAMILY_GENERATORS.clear()
        crossed._FAMILY_GENERATORS.update(original)


def _rewards(result: Any) -> dict[int, float]:
    return {int(row.seed): float(row.realized_reward) for row in result.rows}


def paired_contrast(
    learned: dict[int, float],
    random_geom: dict[int, float],
) -> dict[str, float]:
    """Paired learned-minus-random contrast with a bootstrap 95% CI."""
    seeds = sorted(set(learned) & set(random_geom))
    diffs = [learned[s] - random_geom[s] for s in seeds]
    rng = random.Random(BOOTSTRAP_SEED)
    means = sorted(
        statistics.fmean(rng.choices(diffs, k=len(diffs)))
        for _ in range(BOOTSTRAP_RESAMPLES)
    )
    return {
        "n_pairs": float(len(diffs)),
        "mean_learned": statistics.fmean([learned[s] for s in seeds]),
        "mean_random": statistics.fmean([random_geom[s] for s in seeds]),
        "mean_delta": statistics.fmean(diffs),
        "ci_lo": means[int(0.025 * BOOTSTRAP_RESAMPLES)],
        "ci_hi": means[int(0.975 * BOOTSTRAP_RESAMPLES)],
    }


def _run_arm(family: str, seed_lo: int, n_seeds: int) -> dict[str, dict[int, float]]:
    """Run the two L1 geometry arms and return per-seed rewards for each."""
    out: dict[str, dict[int, float]] = {}
    for geometry in ("LEARNED", "FREQ_MATCHED_RANDOM"):
        spec = CellSpec(
            geometry=geometry,
            concern=CONCERN_FROZEN_WRONG,
            family=family,
            n_seeds=n_seeds,
            seed_range=(seed_lo, seed_lo + n_seeds - 1),
        )
        out[geometry] = _rewards(run_cell(spec))
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify L1 under the repaired prior.")
    parser.add_argument("--family", default=DEFAULT_FAMILY)
    parser.add_argument("--seed-lo", type=int, default=DEFAULT_SEED_LO)
    parser.add_argument("--n-seeds", type=int, default=300)
    parser.add_argument("--k", type=int, default=DEFAULT_SUPPRESSED_SET_SIZE)
    parser.add_argument("--out", type=Path, default=RECEIPT_PATH)
    args = parser.parse_args(argv)

    threshold = DELTA_THRESH_L1[args.family]

    original = _run_arm(args.family, args.seed_lo, args.n_seeds)
    before = paired_contrast(original["LEARNED"], original["FREQ_MATCHED_RANDOM"])

    with repaired_generators(k=args.k):
        repaired = _run_arm(args.family, args.seed_lo, args.n_seeds)
    after = paired_contrast(repaired["LEARNED"], repaired["FREQ_MATCHED_RANDOM"])

    def verdict(c: dict[str, float]) -> str:
        # Wave 1b L1 GO required mean_delta > 0 clearing the frozen threshold.
        return "PASS" if (c["mean_delta"] >= threshold and c["ci_lo"] > 0) else "KILL"

    receipt = {
        "kind": "cogr_erratum_e1_l1_under_repair",
        "family": args.family,
        "seed_range": [args.seed_lo, args.seed_lo + args.n_seeds - 1],
        "delta_thresh_L1": threshold,
        "suppressed_set_size_k": args.k,
        "original_prior": {**before, "l1_verdict": verdict(before)},
        "repaired_prior": {**after, "l1_verdict": verdict(after)},
        "kill_confirmed_on_clean_data": verdict(after) == "KILL",
        "verdict_unchanged_by_repair": verdict(before) == verdict(after),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
