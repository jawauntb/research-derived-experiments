#!/usr/bin/env python3
"""Run the multi-family symbolic weakness benchmark.

For each of N independent trials, sample a task family and parameters, build
candidate hypotheses, score them, and record which selector picks the
invariant rule and what OOD accuracy it gets.

Output is a JSON document with:

- manifest: seeds, family configs, selectors, weakness definition.
- per_trial: (family, selector, family_of_chosen, ood_accuracy, ...).
- summary: per (family, selector) mean OOD accuracy, invariant-pick rate,
  per-family confidence intervals (Wilson 95%).
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from experiments.symbolic_weakness.families import (
    color_permutation_trial,
    cyclic_prefix_trial,
    dihedral_reflection_trial,
    parity_coset_trial,
)
from experiments.symbolic_weakness.selectors import SELECTORS, consistent_metrics


@dataclass(frozen=True)
class FamilyConfig:
    name: str
    description: str
    default_kwargs: dict[str, Any]
    domain_choices: list[dict[str, Any]]


FAMILY_CONFIGS: list[FamilyConfig] = [
    FamilyConfig(
        name="cyclic_prefix_shift",
        description="Z_n cyclic prefix shift; local patch vs global shift",
        default_kwargs={"modulus": 11, "train_window": 3},
        domain_choices=[
            {"modulus": 7, "train_window": 3},
            {"modulus": 11, "train_window": 3},
            {"modulus": 11, "train_window": 4},
            {"modulus": 13, "train_window": 3},
            {"modulus": 13, "train_window": 5},
        ],
    ),
    FamilyConfig(
        name="dihedral_reflection",
        description="D_n reflection with rotation shortcut",
        default_kwargs={"modulus": 11, "train_window": 3},
        domain_choices=[
            {"modulus": 7, "train_window": 3},
            {"modulus": 9, "train_window": 3},
            {"modulus": 11, "train_window": 3},
            {"modulus": 11, "train_window": 4},
            {"modulus": 13, "train_window": 4},
        ],
    ),
    FamilyConfig(
        name="parity_coset",
        description="Z_2-parity swap with single-coset training",
        default_kwargs={"domain_size": 8},
        domain_choices=[
            {"domain_size": 6},
            {"domain_size": 8},
            {"domain_size": 10},
        ],
    ),
    FamilyConfig(
        name="color_permutation",
        description="S_n permutation truth with sparse training support",
        default_kwargs={"domain_size": 5, "train_window": 2},
        domain_choices=[
            {"domain_size": 4, "train_window": 2},
            {"domain_size": 5, "train_window": 2},
            {"domain_size": 6, "train_window": 3},
        ],
    ),
]

FAMILY_BUILDERS = {
    "cyclic_prefix_shift": cyclic_prefix_trial,
    "dihedral_reflection": dihedral_reflection_trial,
    "parity_coset": parity_coset_trial,
    "color_permutation": color_permutation_trial,
}


@dataclass(frozen=True)
class TrialResult:
    trial_id: int
    family: str
    config: str
    selector: str
    chosen_family: str
    chosen_name: str
    train_accuracy: float
    ood_accuracy: float
    is_invariant: int
    form_length: int
    weakness_oracle: int


def _wilson_ci(p: float, n: int, *, z: float = 1.959963984540054) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half_width = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half_width), min(1.0, centre + half_width))


def run_trials(
    *,
    families: list[str],
    trials_per_family: int,
    seed: int,
) -> list[TrialResult]:
    rng = random.Random(seed)
    results: list[TrialResult] = []
    trial_id = 0
    for family in families:
        cfg = next((c for c in FAMILY_CONFIGS if c.name == family), None)
        if cfg is None:
            raise KeyError(f"unknown family: {family}")
        builder = FAMILY_BUILDERS[family]
        for _ in range(trials_per_family):
            config = rng.choice(cfg.domain_choices)
            trial_seed = rng.randrange(0, 2**31 - 1)
            trial = builder(rng=random.Random(trial_seed), **config)  # type: ignore[arg-type]
            metrics = consistent_metrics(trial, rng)
            config_label = ",".join(f"{k}={v}" for k, v in sorted(config.items()))
            for selector_name, selector in SELECTORS.items():
                chosen = selector(metrics, rng)
                results.append(
                    TrialResult(
                        trial_id=trial_id,
                        family=family,
                        config=config_label,
                        selector=selector_name,
                        chosen_family=chosen.family,
                        chosen_name=chosen.name,
                        train_accuracy=chosen.train_accuracy,
                        ood_accuracy=chosen.ood_accuracy,
                        is_invariant=int(chosen.family == "invariant"),
                        form_length=chosen.form_length,
                        weakness_oracle=chosen.weakness_oracle,
                    )
                )
            trial_id += 1
    return results


def summarize(results: list[TrialResult]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, list[TrialResult]]] = {}
    for r in results:
        grouped.setdefault(r.family, {}).setdefault(r.selector, []).append(r)
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for family, by_selector in grouped.items():
        out[family] = {}
        for selector, items in by_selector.items():
            n = len(items)
            invariant_rate = mean(item.is_invariant for item in items)
            mean_ood = mean(item.ood_accuracy for item in items)
            mean_train = mean(item.train_accuracy for item in items)
            ci_low, ci_high = _wilson_ci(invariant_rate, n)
            out[family][selector] = {
                "n_trials": n,
                "invariant_rate": invariant_rate,
                "invariant_rate_ci95": [ci_low, ci_high],
                "mean_ood_accuracy": mean_ood,
                "mean_train_accuracy": mean_train,
            }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--families",
        default="cyclic_prefix_shift,dihedral_reflection,parity_coset,color_permutation",
    )
    parser.add_argument("--trials-per-family", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260609)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    families = [f.strip() for f in args.families.split(",") if f.strip()]
    results = run_trials(
        families=families,
        trials_per_family=args.trials_per_family,
        seed=args.seed,
    )
    summary = summarize(results)
    payload = {
        "manifest": {
            "families": families,
            "trials_per_family": args.trials_per_family,
            "seed": args.seed,
            "selectors": sorted(SELECTORS),
        },
        "summary": summary,
        "results": [asdict(r) for r in results],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")

    # Print a compact summary to stdout.
    print("=== Symbolic Weakness Benchmark Summary ===")
    for family, by_selector in summary.items():
        print(f"\n[{family}]")
        rows = [
            (selector, stats["invariant_rate"], stats["mean_ood_accuracy"], stats["n_trials"])
            for selector, stats in by_selector.items()
        ]
        rows.sort(key=lambda r: -r[1])
        for selector, rate, ood, n in rows:
            print(f"  {selector:30s} inv_rate={rate:.3f} mean_ood={ood:.3f} (n={n})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
