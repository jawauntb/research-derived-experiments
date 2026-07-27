"""Reanalysis of the 32-seed frozen data under the intervention-algebra reframe.

Preregistered in `REANALYSIS_INTERVENTION_ALGEBRA_PREREGISTRATION.md`.
No new training, no new interventions -- only the frozen seed rows.

Test: are the preregistered A-side and B-side univariate intervention
effects approximately UNCORRELATED across seeds (evidence for
constraint-specific structure invisible to univariate G3/G4), or are
they correlated (evidence for shared-artifact dominance)?

Run:
    uv run --no-sync python -m experiments.constraint_swap_causal_geometry.reanalysis_intervention_algebra
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any, Final, Sequence

import numpy as np


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
SEED_ROWS: Final[Path] = _PACKAGE / "results" / "registered_seed_rows.jsonl"
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "reanalysis_intervention_algebra.json"

CORR_MAX: Final[float] = 0.30
PERM_ALPHA: Final[float] = 0.05
PERM_TRIALS: Final[int] = 10000
PERM_SEED: Final[int] = 20260727


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    xm = x - x.mean()
    ym = y - y.mean()
    denom = float(np.sqrt((xm * xm).sum() * (ym * ym).sum()))
    if denom == 0.0:
        return 0.0
    return float((xm * ym).sum() / denom)


def _permutation_p_gt_threshold(
    x: np.ndarray, y: np.ndarray, threshold: float, trials: int, seed: int
) -> float:
    """Under H0 that |corr| >= threshold, estimate p by shuffling y across seeds."""
    rng = random.Random(seed)
    hits = 0
    y_indices = list(range(len(y)))
    for _ in range(trials):
        rng.shuffle(y_indices)
        y_shuffled = y[y_indices]
        if abs(_pearson(x, y_shuffled)) >= threshold:
            hits += 1
    return hits / trials


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Constraint Swap intervention-algebra reanalysis.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    rows: list[dict[str, Any]] = []
    for line in SEED_ROWS.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))

    #: Extract the four preregistered intervention effects from primary topology.
    undo_a = np.array([r["primary"]["undo_A_specific_harm"] for r in rows])
    undo_b = np.array([r["primary"]["undo_B_specific_harm"] for r in rows])
    rescue_a = np.array([r["primary"]["rescue_A_specific_gain"] for r in rows])
    rescue_b = np.array([r["primary"]["rescue_B_specific_gain"] for r in rows])

    r_undo = _pearson(undo_a, undo_b)
    r_rescue = _pearson(rescue_a, rescue_b)

    p_undo = _permutation_p_gt_threshold(
        undo_a, undo_b, CORR_MAX, PERM_TRIALS, PERM_SEED
    )
    p_rescue = _permutation_p_gt_threshold(
        rescue_a, rescue_b, CORR_MAX, PERM_TRIALS, PERM_SEED + 1
    )

    r1 = abs(r_undo) < CORR_MAX
    r2 = abs(r_rescue) < CORR_MAX
    #: R3 requires both permutation-tests to reject "|r| >= 0.30" at p < 0.05.
    r3 = (p_undo < PERM_ALPHA) and (p_rescue < PERM_ALPHA)

    overall_go = r1 and r2 and r3

    if overall_go:
        reading = (
            "intervention_algebra_reframe_supported_on_this_data: A-side and "
            "B-side univariate intervention effects are approximately "
            "uncorrelated across seeds. Consistent with constraint-specific "
            "structure invisible to univariate G3/G4 gates. Would justify "
            "repeating on a real vision-language model with activation "
            "patching."
        )
    elif not r1 or not r2:
        reading = (
            "intervention_effects_are_correlated_across_seeds: A-side and "
            "B-side effects are driven by shared seed-level structure, not "
            "constraint-specific mechanism. Third serial null on the "
            "intervention-algebra reframe (with DCR3b if that also fails)."
        )
    else:
        reading = "correlations below 0.30 but permutation test does not reject"

    verdict: dict[str, Any] = {
        "kind": "constraint_swap_intervention_algebra_reanalysis",
        "purpose": (
            "Test whether preregistered A-side and B-side intervention "
            "effects on the frozen 32-seed data are approximately "
            "uncorrelated across seeds, as the intervention-algebra reframe "
            "would predict for constraint-specific structure invisible to "
            "univariate G3/G4 gates."
        ),
        "n_seeds": len(rows),
        "r_undo": r_undo,
        "r_rescue": r_rescue,
        "permutation_test_p_undo": p_undo,
        "permutation_test_p_rescue": p_rescue,
        "gates": {
            "R1_r_undo_below_0p30": {
                "value": r_undo,
                "abs_value": abs(r_undo),
                "threshold": CORR_MAX,
                "decision": "GO" if r1 else "NO_GO",
            },
            "R2_r_rescue_below_0p30": {
                "value": r_rescue,
                "abs_value": abs(r_rescue),
                "threshold": CORR_MAX,
                "decision": "GO" if r2 else "NO_GO",
            },
            "R3_permutation_test_rejects": {
                "p_undo": p_undo,
                "p_rescue": p_rescue,
                "alpha": PERM_ALPHA,
                "decision": "GO" if r3 else "NO_GO",
            },
        },
        "overall_decision": "GO" if overall_go else "NO_GO",
        "licensed_reading": reading,
        "descriptive_statistics": {
            "undo_A_specific_harm": {
                "mean": float(undo_a.mean()),
                "std": float(undo_a.std()),
                "min": float(undo_a.min()),
                "max": float(undo_a.max()),
            },
            "undo_B_specific_harm": {
                "mean": float(undo_b.mean()),
                "std": float(undo_b.std()),
                "min": float(undo_b.min()),
                "max": float(undo_b.max()),
            },
            "rescue_A_specific_gain": {
                "mean": float(rescue_a.mean()),
                "std": float(rescue_a.std()),
                "min": float(rescue_a.min()),
                "max": float(rescue_a.max()),
            },
            "rescue_B_specific_gain": {
                "mean": float(rescue_b.mean()),
                "std": float(rescue_b.std()),
                "min": float(rescue_b.min()),
                "max": float(rescue_b.max()),
            },
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
