#!/usr/bin/env python3
"""Conditional randomization audit for the E1 misspecification gap.

The harness freezes the original candidate pools and true deployments, then
redraws only the marginal-preserving misspecified concern assignment. It is
stdlib-only and intended for reproducible CPU execution.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import mean, pstdev
from typing import Sequence

from experiments.commitment_surface.core import (
    biased_train_perfect_completion,
    misspecified_deployment,
    random_train_perfect_completion,
    unequal_deployment,
)


OBSERVED_GAP = -0.054159416947479166
DEFAULT_BASE_SEED = 202607092136
DEFAULT_REPLICATES = 2048
DEFAULT_MODULI = (7, 11, 13)
DEFAULT_STRUCTURAL_SEEDS = 32
DEFAULT_FOCUS_FRACTION = 0.25
DEFAULT_FOCUS_WEIGHT = 10.0
DEFAULT_N_CANDIDATES = 300
DEFAULT_TRAIN_WINDOW_FRAC = 0.5


@dataclass(frozen=True)
class PreparedCell:
    """Frozen E1 structure sufficient for conditional randomization."""

    modulus: int
    structural_seed: int
    n_positions: int
    n_focus: int
    candidate_masks: tuple[int, ...]
    candidate_true_accuracies: tuple[float, ...]
    unweighted_accuracy: float
    true_focus_mask: int
    original_misspec_gap: float
    structure_hash: str
    candidate_position_coverage: tuple[float, ...]


def _correctness_mask(
    table: tuple[int, ...], modulus: int, pairs: Sequence[tuple[int, int]]
) -> int:
    mask = 0
    for position, (a, b) in enumerate(pairs):
        if table[a * modulus + b] == (a + b) % modulus:
            mask |= 1 << position
    return mask


def _focus_mask(kappa: Sequence[float]) -> int:
    mask = 0
    for position, weight in enumerate(kappa):
        if weight > 1.0:
            mask |= 1 << position
    return mask


def _pick_weighted(
    candidate_masks: Sequence[int], focus_mask: int, focus_weight: float
) -> int:
    """Return first maximal candidate, matching core selector tie-breaking."""
    extra = focus_weight - 1.0
    best_index = 0
    first = candidate_masks[0]
    best_score = first.bit_count() + extra * (first & focus_mask).bit_count()
    for index in range(1, len(candidate_masks)):
        candidate = candidate_masks[index]
        score = candidate.bit_count() + extra * (candidate & focus_mask).bit_count()
        if score > best_score:
            best_score = score
            best_index = index
    return best_index


def prepare_cell(
    *,
    modulus: int,
    structural_seed: int,
    focus_fraction: float = DEFAULT_FOCUS_FRACTION,
    focus_weight: float = DEFAULT_FOCUS_WEIGHT,
    n_candidates: int = DEFAULT_N_CANDIDATES,
    train_window_frac: float = DEFAULT_TRAIN_WINDOW_FRAC,
) -> PreparedCell:
    """Reconstruct one original E1 cell and freeze all non-null structure."""
    rng = random.Random(structural_seed)
    train_window = max(2, int(round(modulus * train_window_frac)))
    train_pairs = [
        (a, b) for a in range(train_window) for b in range(modulus)
    ]
    ood_pairs = [
        (a, b) for a in range(train_window, modulus) for b in range(modulus)
    ]
    wellspec = unequal_deployment(
        ood_pairs,
        rng=random.Random(structural_seed + 7),
        focus_fraction=focus_fraction,
        focus_weight=focus_weight,
    )
    high_focus = {
        pair for pair, weight in zip(wellspec.pairs, wellspec.kappa)
        if weight > 1.0
    }

    candidates = [
        random_train_perfect_completion(
            modulus, train_pairs, rng=rng, ood_correct_prob=0.30
        )
        for _ in range(n_candidates)
    ]
    candidates.extend(
        biased_train_perfect_completion(
            modulus,
            train_pairs,
            high_focus,
            rng=rng,
            high_correct_prob=0.75,
            low_correct_prob=0.20,
        )
        for _ in range(n_candidates // 4)
    )

    masks = tuple(_correctness_mask(table, modulus, ood_pairs) for table in candidates)
    true_focus_mask = _focus_mask(wellspec.kappa)
    n_focus = true_focus_mask.bit_count()
    denominator = len(ood_pairs) + (focus_weight - 1.0) * n_focus
    accuracies = tuple(
        (
            mask.bit_count()
            + (focus_weight - 1.0) * (mask & true_focus_mask).bit_count()
        )
        / denominator
        for mask in masks
    )
    unweighted_index = max(range(len(masks)), key=lambda index: masks[index].bit_count())
    unweighted_accuracy = accuracies[unweighted_index]

    original_misspec = misspecified_deployment(
        ood_pairs,
        rng=random.Random(structural_seed + 11),
        focus_fraction=focus_fraction,
        focus_weight=focus_weight,
    )
    original_index = _pick_weighted(
        masks, _focus_mask(original_misspec.kappa), focus_weight
    )

    digest = hashlib.sha256()
    digest.update(
        json.dumps(
            {
                "modulus": modulus,
                "structural_seed": structural_seed,
                "ood_pairs": ood_pairs,
                "wellspec_kappa": wellspec.kappa,
            },
            sort_keys=True,
        ).encode()
    )
    for table in candidates:
        digest.update(json.dumps(table).encode())

    coverage = tuple(
        sum(bool(mask & (1 << position)) for mask in masks) / len(masks)
        for position in range(len(ood_pairs))
    )
    return PreparedCell(
        modulus=modulus,
        structural_seed=structural_seed,
        n_positions=len(ood_pairs),
        n_focus=n_focus,
        candidate_masks=masks,
        candidate_true_accuracies=accuracies,
        unweighted_accuracy=unweighted_accuracy,
        true_focus_mask=true_focus_mask,
        original_misspec_gap=accuracies[original_index] - unweighted_accuracy,
        structure_hash=digest.hexdigest(),
        candidate_position_coverage=coverage,
    )


def derive_assignment_seed(
    base_seed: int, replicate: int, modulus: int, structural_seed: int
) -> int:
    """Derive a stable namespaced 128-bit seed for one assignment."""
    namespace = f"{base_seed}|{replicate}|{modulus}|{structural_seed}"
    return int.from_bytes(hashlib.sha256(namespace.encode()).digest()[:16], "big")


def quantile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must lie in [0, 1]")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    p = successes / trials
    denominator = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denominator
    half = (
        z
        * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
        / denominator
    )
    return center - half, center + half


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    x_mean = mean(xs)
    y_mean = mean(ys)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    denominator = math.sqrt(
        sum((x - x_mean) ** 2 for x in xs)
        * sum((y - y_mean) ** 2 for y in ys)
    )
    return numerator / denominator if denominator else 0.0


def _distribution(values: Sequence[float], observed_gap: float) -> dict[str, object]:
    average = mean(values)
    sd = pstdev(values)
    half_width = 1.96 * sd / math.sqrt(len(values))
    tail_count = sum(value <= observed_gap for value in values)
    tail_low, tail_high = wilson_interval(tail_count, len(values))
    probabilities = (0.005, 0.025, 0.05, 0.5, 0.95, 0.975, 0.995)
    return {
        "n": len(values),
        "observed_gap": observed_gap,
        "mean": average,
        "variance": sd * sd,
        "sd": sd,
        "mean_ci95": [average - half_width, average + half_width],
        "quantiles": {f"{p:.3f}": quantile(values, p) for p in probabilities},
        "tail_count_gap_le_observed": tail_count,
        "probability_gap_le_observed": tail_count / len(values),
        "probability_gap_le_observed_wilson95": [tail_low, tail_high],
    }


def run_randomization_audit(
    *,
    moduli: Sequence[int] = DEFAULT_MODULI,
    structural_seeds: int = DEFAULT_STRUCTURAL_SEEDS,
    replicates: int = DEFAULT_REPLICATES,
    base_seed: int = DEFAULT_BASE_SEED,
    focus_fraction: float = DEFAULT_FOCUS_FRACTION,
    focus_weight: float = DEFAULT_FOCUS_WEIGHT,
    n_candidates: int = DEFAULT_N_CANDIDATES,
    train_window_frac: float = DEFAULT_TRAIN_WINDOW_FRAC,
    observed_gap: float = OBSERVED_GAP,
) -> dict[str, object]:
    if replicates < 2:
        raise ValueError("replicates must be at least 2")
    cells = [
        prepare_cell(
            modulus=modulus,
            structural_seed=seed,
            focus_fraction=focus_fraction,
            focus_weight=focus_weight,
            n_candidates=n_candidates,
            train_window_frac=train_window_frac,
        )
        for modulus in moduli
        for seed in range(structural_seeds)
    ]
    initial_hashes = tuple(cell.structure_hash for cell in cells)
    frozen_structure_digest = hashlib.sha256(
        "|".join(initial_hashes).encode()
    ).hexdigest()
    observed_reconstructed = mean(cell.original_misspec_gap for cell in cells)
    observed_by_modulus = {
        modulus: mean(
            cell.original_misspec_gap
            for cell in cells
            if cell.modulus == modulus
        )
        for modulus in moduli
    }

    aggregate_gaps: list[float] = []
    per_modulus_gaps = {modulus: [] for modulus in moduli}
    inclusion_counts = [
        [0 for _ in range(cell.n_positions)] for cell in cells
    ]
    seen_seeds: set[int] = set()
    cardinality_ok = True
    overlap_observed = 0.0
    overlap_expected = 0.0
    overlap_variance = 0.0

    for replicate in range(replicates):
        total_gap = 0.0
        modulus_totals = {modulus: 0.0 for modulus in moduli}
        modulus_counts = {modulus: 0 for modulus in moduli}
        for cell_index, cell in enumerate(cells):
            assignment_seed = derive_assignment_seed(
                base_seed, replicate, cell.modulus, cell.structural_seed
            )
            if assignment_seed in seen_seeds:
                raise RuntimeError("derived assignment seed collision")
            seen_seeds.add(assignment_seed)
            positions = random.Random(assignment_seed).sample(
                range(cell.n_positions), cell.n_focus
            )
            focus_mask = sum(1 << position for position in positions)
            cardinality_ok &= focus_mask.bit_count() == cell.n_focus
            for position in positions:
                inclusion_counts[cell_index][position] += 1

            selected_index = _pick_weighted(
                cell.candidate_masks, focus_mask, focus_weight
            )
            gap = (
                cell.candidate_true_accuracies[selected_index]
                - cell.unweighted_accuracy
            )
            total_gap += gap
            modulus_totals[cell.modulus] += gap
            modulus_counts[cell.modulus] += 1

            overlap_observed += (focus_mask & cell.true_focus_mask).bit_count()
            n = cell.n_positions
            sample_size = cell.n_focus
            true_size = cell.true_focus_mask.bit_count()
            overlap_expected += sample_size * true_size / n
            if n > 1:
                overlap_variance += (
                    sample_size
                    * (true_size / n)
                    * (1.0 - true_size / n)
                    * ((n - sample_size) / (n - 1))
                )

        aggregate_gaps.append(total_gap / len(cells))
        for modulus in moduli:
            per_modulus_gaps[modulus].append(
                modulus_totals[modulus] / modulus_counts[modulus]
            )

    expected_seed_count = replicates * len(cells)
    max_inclusion_z = 0.0
    inclusion_rates: list[float] = []
    candidate_coverages: list[float] = []
    true_focus_labels: list[float] = []
    for cell, counts in zip(cells, inclusion_counts):
        probability = cell.n_focus / cell.n_positions
        expected = replicates * probability
        standard_error = math.sqrt(replicates * probability * (1.0 - probability))
        for position, count in enumerate(counts):
            max_inclusion_z = max(
                max_inclusion_z, abs(count - expected) / standard_error
            )
            inclusion_rates.append(count / replicates)
            candidate_coverages.append(cell.candidate_position_coverage[position])
            true_focus_labels.append(
                float(bool(cell.true_focus_mask & (1 << position)))
            )

    overlap_z = (
        (overlap_observed - overlap_expected) / math.sqrt(overlap_variance)
        if overlap_variance
        else 0.0
    )
    lag1 = pearson(aggregate_gaps[:-1], aggregate_gaps[1:])
    final_hashes = tuple(cell.structure_hash for cell in cells)
    checks = {
        "observed_gap_reconstruction_matches": math.isclose(
            observed_reconstructed, observed_gap, abs_tol=1e-15
        ),
        "structure_invariant": initial_hashes == final_hashes,
        "assignment_cardinality_preserved": cardinality_ok,
        "derived_assignment_seeds_unique": len(seen_seeds) == expected_seed_count,
        "independent_of_candidate_coverage_by_construction": True,
        "exchangeable_fixed_cardinality_by_construction": True,
        "max_abs_position_inclusion_z_le_5": max_inclusion_z <= 5.0,
        "abs_hypergeometric_overlap_z_le_4": abs(overlap_z) <= 4.0,
        "abs_lag1_gap_autocorrelation_le_0p10": abs(lag1) <= 0.10,
    }
    assumptions_pass = all(checks.values())
    overall = _distribution(aggregate_gaps, observed_gap)
    tail_probability = float(overall["probability_gap_le_observed"])
    if not assumptions_pass:
        verdict = "INCONCLUSIVE_ASSUMPTIONS_FAILED"
    elif tail_probability < 0.025:
        verdict = "SYSTEMATIC_ANTICORRELATION_INDICATED"
    else:
        verdict = "CONSISTENT_WITH_RANDOM_ASSIGNMENT_VARIANCE"

    return {
        "preregistration": (
            "papers/commitment_surface/"
            "e1_misspecification_variance_preregistration_2026-07-09.md"
        ),
        "config": {
            "moduli": list(moduli),
            "structural_seeds": structural_seeds,
            "n_structural_cells": len(cells),
            "replicates": replicates,
            "base_seed": base_seed,
            "focus_fraction": focus_fraction,
            "focus_weight": focus_weight,
            "n_candidates": n_candidates,
            "train_window_frac": train_window_frac,
            "observed_gap": observed_gap,
        },
        "observed_gap_reconstructed": observed_reconstructed,
        "null_distribution": overall,
        "per_modulus": {
            str(modulus): _distribution(values, observed_by_modulus[modulus])
            for modulus, values in per_modulus_gaps.items()
        },
        "assumption_audit": {
            "checks": checks,
            "all_checks_pass": assumptions_pass,
            "frozen_structure_sha256": frozen_structure_digest,
            "n_unique_assignment_seeds": len(seen_seeds),
            "expected_assignment_seeds": expected_seed_count,
            "max_abs_position_inclusion_z": max_inclusion_z,
            "hypergeometric_overlap": {
                "observed_total": overlap_observed,
                "expected_total": overlap_expected,
                "z": overlap_z,
            },
            "lag1_aggregate_gap_autocorrelation": lag1,
            "position_inclusion_correlation_with_candidate_coverage": pearson(
                inclusion_rates, candidate_coverages
            ),
            "position_inclusion_correlation_with_true_focus": pearson(
                inclusion_rates, true_focus_labels
            ),
            "fixed_cardinality_note": (
                "Weights are exchangeable, not iid, within an assignment; "
                "equal coordinate marginals are the corollary requirement."
            ),
            "conditional_independence_note": (
                "Candidate pools and C_star are frozen before namespaced RNG "
                "seeds draw misspecified focus positions."
            ),
        },
        "gate": {
            "lower_tail_alpha": 0.025,
            "original_frozen_equivalence_gate_remains_failed": True,
            "verdict": verdict,
        },
        "aggregate_replicate_gaps": aggregate_gaps,
    }


def write_markdown(result: dict[str, object], path: Path) -> None:
    config = result["config"]
    null = result["null_distribution"]
    audit = result["assumption_audit"]
    gate = result["gate"]
    quantiles = null["quantiles"]
    checks = audit["checks"]
    lines = [
        "# E1 Follow-up — Misspecification Variance Quantification",
        "",
        f"Preregistration: `{result['preregistration']}`",
        "",
        "## Result",
        "",
        f"- Verdict: **{gate['verdict']}**",
        f"- Original observed gap: `{config['observed_gap']:.15f}`",
        (
            "- Reconstructed original gap: "
            f"`{result['observed_gap_reconstructed']:.15f}`"
        ),
        f"- Null replicates: {config['replicates']} over {config['n_structural_cells']} frozen cells",
        f"- Null mean gap: {null['mean']:.6f}",
        f"- Null variance: {null['variance']:.9f}",
        f"- Null SD: {null['sd']:.6f}",
        (
            "- 95% CI for null mean: "
            f"[{null['mean_ci95'][0]:.6f}, {null['mean_ci95'][1]:.6f}]"
        ),
        (
            "- `P(null gap <= observed)`: "
            f"{null['probability_gap_le_observed']:.6f} "
            f"({null['tail_count_gap_le_observed']}/{null['n']}); Wilson 95% CI "
            f"[{null['probability_gap_le_observed_wilson95'][0]:.6f}, "
            f"{null['probability_gap_le_observed_wilson95'][1]:.6f}]"
        ),
        "",
        "The original frozen ±0.05 sub-gate remains a strict failure. The follow-up gate only decides whether that failed realization is surprising under independent marginal-preserving reassignment.",
        "",
        "## Null quantiles",
        "",
        "| Quantile | Gap |",
        "|---:|---:|",
    ]
    for probability, value in quantiles.items():
        lines.append(f"| {float(probability) * 100:.1f}% | {value:.6f} |")
    lines.extend([
        "",
        "## Per-modulus null distribution",
        "",
        "| Modulus | Observed | Mean | SD | 2.5% | Median | 97.5% | Lower-tail P |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for modulus, distribution in result["per_modulus"].items():
        q = distribution["quantiles"]
        lines.append(
            f"| {modulus} | {distribution['observed_gap']:.6f} | "
            f"{distribution['mean']:.6f} | {distribution['sd']:.6f} | "
            f"{q['0.025']:.6f} | {q['0.500']:.6f} | {q['0.975']:.6f} | "
            f"{distribution['probability_gap_le_observed']:.6f} |"
        )
    lines.extend([
        "",
        "## Independence and exchangeability audit",
        "",
    ])
    for name, passed in checks.items():
        lines.append(f"- `{name}`: **{'PASS' if passed else 'FAIL'}**")
    overlap = audit["hypergeometric_overlap"]
    lines.extend([
        "",
        f"- Maximum absolute position-inclusion z: {audit['max_abs_position_inclusion_z']:.3f}",
        (
            "- True-focus overlap: observed "
            f"{overlap['observed_total']:.1f}, expected {overlap['expected_total']:.1f}, "
            f"z={overlap['z']:.3f}"
        ),
        f"- Lag-1 aggregate-gap autocorrelation: {audit['lag1_aggregate_gap_autocorrelation']:.4f}",
        (
            "- Inclusion-rate correlation with candidate coverage: "
            f"{audit['position_inclusion_correlation_with_candidate_coverage']:.4f}"
        ),
        (
            "- Inclusion-rate correlation with true-focus membership: "
            f"{audit['position_inclusion_correlation_with_true_focus']:.4f}"
        ),
        "",
        audit["fixed_cardinality_note"],
        "",
        audit["conditional_independence_note"],
        "",
        "## Claim boundary",
        "",
        "This conditional randomization test diagnoses the frozen E1 candidate pools and deployments. It does not establish equivalence in other candidate families, and it does not turn the original gate into a pass. The score-level in-expectation identity does not imply equality after nonlinear argmax selection.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--moduli", default=",".join(map(str, DEFAULT_MODULI)))
    parser.add_argument("--structural-seeds", type=int, default=DEFAULT_STRUCTURAL_SEEDS)
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    parser.add_argument("--base-seed", type=int, default=DEFAULT_BASE_SEED)
    parser.add_argument("--focus-fraction", type=float, default=DEFAULT_FOCUS_FRACTION)
    parser.add_argument("--focus-weight", type=float, default=DEFAULT_FOCUS_WEIGHT)
    parser.add_argument("--n-candidates", type=int, default=DEFAULT_N_CANDIDATES)
    parser.add_argument("--train-window-frac", type=float, default=DEFAULT_TRAIN_WINDOW_FRAC)
    parser.add_argument("--observed-gap", type=float, default=OBSERVED_GAP)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/commitment_surface/results/"
            "e1_misspecification_variance.json"
        ),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path(
            "experiments/commitment_surface/results/"
            "e1_misspecification_variance.md"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.replicates < 500:
        raise ValueError("the preregistered public run requires at least 500 replicates")
    result = run_randomization_audit(
        moduli=tuple(int(value) for value in args.moduli.split(",") if value),
        structural_seeds=args.structural_seeds,
        replicates=args.replicates,
        base_seed=args.base_seed,
        focus_fraction=args.focus_fraction,
        focus_weight=args.focus_weight,
        n_candidates=args.n_candidates,
        train_window_frac=args.train_window_frac,
        observed_gap=args.observed_gap,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, args.summary)
    print(json.dumps({
        "verdict": result["gate"]["verdict"],
        "null_mean": result["null_distribution"]["mean"],
        "tail_probability": result["null_distribution"]["probability_gap_le_observed"],
        "assumptions_pass": result["assumption_audit"]["all_checks_pass"],
        "out": str(args.out),
        "summary": str(args.summary),
    }, indent=2))


if __name__ == "__main__":
    main()
