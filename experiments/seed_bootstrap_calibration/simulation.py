"""Deterministic simulation of seed-count and bootstrap-coverage policies.

The simulation treats seeds as the independent experimental units. Each seed
contains paired treatment-control episode differences. The naive interval
resamples those episode differences as if they were independent; the paired
seed-cluster interval resamples seed-level paired means.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

Method: TypeAlias = Literal[
    "naive_row_percentile",
    "paired_seed_cluster_percentile",
]
METHODS: tuple[Method, ...] = (
    "naive_row_percentile",
    "paired_seed_cluster_percentile",
)
FloatArray: TypeAlias = NDArray[np.float64]

PROMOTION_COVERAGE = 0.90
PROMOTION_POWER = 0.80
PROMOTION_SIGN_STABILITY = 0.90
PROMOTION_NULL_FALSE_POSITIVE_RATE = 0.10
PILOT_COVERAGE = 0.80
PILOT_SIGN_STABILITY = 0.70
PILOT_NULL_FALSE_POSITIVE_RATE = 0.20


@dataclass(frozen=True)
class Regime:
    """A preregistered data-generating regime and precision target."""

    name: str
    claim_type: str
    effect: float
    noise_sd: float
    hierarchy_sd: float
    target_width: float


@dataclass(frozen=True)
class CalibrationConfig:
    """Fixed simulation grid and deterministic sampling budget."""

    seed_counts: tuple[int, ...]
    episodes_per_seed: int
    monte_carlo_reps: int
    bootstrap_reps: int
    confidence: float
    simulation_seed: int
    regimes: tuple[Regime, ...]
    methods: tuple[Method, ...] = METHODS


DEFAULT_CONFIG = CalibrationConfig(
    seed_counts=(3, 5, 8, 10, 16, 64),
    episodes_per_seed=4,
    monte_carlo_reps=200,
    bootstrap_reps=300,
    confidence=0.95,
    simulation_seed=20260714,
    regimes=(
        Regime(
            name="null_iid",
            claim_type="null_calibration",
            effect=0.0,
            noise_sd=1.0,
            hierarchy_sd=0.0,
            target_width=0.50,
        ),
        Regime(
            name="moderate_iid",
            claim_type="directional_effect",
            effect=0.5,
            noise_sd=1.0,
            hierarchy_sd=0.0,
            target_width=0.50,
        ),
        Regime(
            name="moderate_hierarchy",
            claim_type="directional_effect",
            effect=0.5,
            noise_sd=0.7,
            hierarchy_sd=0.8,
            target_width=0.75,
        ),
        Regime(
            name="null_hierarchy",
            claim_type="null_calibration",
            effect=0.0,
            noise_sd=0.7,
            hierarchy_sd=1.0,
            target_width=0.75,
        ),
        Regime(
            name="weak_high_noise_hierarchy",
            claim_type="directional_effect",
            effect=0.2,
            noise_sd=1.5,
            hierarchy_sd=1.2,
            target_width=0.80,
        ),
    ),
)


def _validate_config(config: CalibrationConfig) -> None:
    if not config.seed_counts or any(count < 2 for count in config.seed_counts):
        raise ValueError("seed_counts must contain values >= 2")
    if len(config.seed_counts) != len(set(config.seed_counts)):
        raise ValueError("seed_counts must be unique")
    if config.episodes_per_seed < 1:
        raise ValueError("episodes_per_seed must be positive")
    if config.monte_carlo_reps < 1 or config.bootstrap_reps < 2:
        raise ValueError("simulation and bootstrap repetitions must be positive")
    if not 0.0 < config.confidence < 1.0:
        raise ValueError("confidence must be between zero and one")
    if not config.regimes:
        raise ValueError("at least one regime is required")
    regime_names = [regime.name for regime in config.regimes]
    if len(regime_names) != len(set(regime_names)):
        raise ValueError("regime names must be unique")
    if len(config.methods) != len(set(config.methods)):
        raise ValueError("methods must be unique")
    required_methods = set(METHODS)
    if set(config.methods) != required_methods:
        raise ValueError(f"methods must be exactly {sorted(required_methods)}")
    for regime in config.regimes:
        if regime.noise_sd < 0.0 or regime.hierarchy_sd < 0.0:
            raise ValueError("standard deviations cannot be negative")
        if regime.target_width <= 0.0:
            raise ValueError("target_width must be positive")


def _config_dict(config: CalibrationConfig) -> dict[str, Any]:
    return asdict(config)


def _config_sha256(config: CalibrationConfig) -> str:
    encoded = json.dumps(
        _config_dict(config), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bootstrap_interval(
    paired_differences: FloatArray,
    *,
    method: Method,
    bootstrap_reps: int,
    confidence: float,
    seed: int,
) -> tuple[float, float]:
    """Return a percentile interval under the requested resampling scheme."""

    values = np.asarray(paired_differences, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 1:
        raise ValueError("paired_differences must have shape (>=2 seeds, >=1 episodes)")
    if bootstrap_reps < 2:
        raise ValueError("bootstrap_reps must be at least two")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between zero and one")

    rng = np.random.default_rng(seed)
    if method == "naive_row_percentile":
        flattened = values.reshape(-1)
        indices = rng.integers(
            0,
            flattened.size,
            size=(bootstrap_reps, flattened.size),
        )
        bootstrap_means = flattened[indices].mean(axis=1)
    elif method == "paired_seed_cluster_percentile":
        seed_means = values.mean(axis=1)
        indices = rng.integers(
            0,
            seed_means.size,
            size=(bootstrap_reps, seed_means.size),
        )
        bootstrap_means = seed_means[indices].mean(axis=1)
    else:
        raise ValueError(f"unsupported bootstrap method: {method}")

    tail = (1.0 - confidence) / 2.0
    low, high = np.quantile(bootstrap_means, [tail, 1.0 - tail])
    return float(low), float(high)


def _paired_differences(
    regime: Regime,
    *,
    seed_count: int,
    episodes_per_seed: int,
    rng: np.random.Generator,
) -> FloatArray:
    """Generate paired treatment-control differences with seed heterogeneity."""

    seed_effects = rng.normal(0.0, regime.hierarchy_sd, size=(seed_count, 1))
    paired_episode_noise = rng.normal(
        0.0,
        regime.noise_sd,
        size=(seed_count, episodes_per_seed),
    )
    return cast(
        FloatArray,
        regime.effect + seed_effects + paired_episode_noise,
    )


def _simulate_cell(
    regime: Regime,
    seed_count: int,
    method: Method,
    config: CalibrationConfig,
    *,
    datasets: list[FloatArray],
    rng: np.random.Generator,
) -> dict[str, Any]:
    covered = 0
    rejected_zero = 0
    correct_direction = 0
    widths: list[float] = []

    for values in datasets:
        bootstrap_seed = int(rng.integers(0, np.iinfo(np.int64).max))
        low, high = bootstrap_interval(
            values,
            method=method,
            bootstrap_reps=config.bootstrap_reps,
            confidence=config.confidence,
            seed=bootstrap_seed,
        )
        estimate = float(values.mean())
        covered += int(low <= regime.effect <= high)
        rejected_zero += int(low > 0.0 or high < 0.0)
        if regime.effect > 0.0:
            correct_direction += int(estimate > 0.0)
        elif regime.effect < 0.0:
            correct_direction += int(estimate < 0.0)
        widths.append(high - low)

    repetitions = config.monte_carlo_reps
    is_null = regime.effect == 0.0
    return {
        "regime": regime.name,
        "claim_type": regime.claim_type,
        "seed_count": seed_count,
        "method": method,
        "coverage": round(covered / repetitions, 4),
        "mean_width": round(float(np.mean(widths)), 4),
        "power": None if is_null else round(rejected_zero / repetitions, 4),
        "false_positive_rate": round(rejected_zero / repetitions, 4)
        if is_null
        else None,
        "sign_stability": None
        if is_null
        else round(correct_direction / repetitions, 4),
        "monte_carlo_reps": repetitions,
    }


def _decision_row(
    regime: Regime,
    seed_count: int,
    cell: dict[str, Any],
) -> dict[str, Any]:
    coverage = float(cell["coverage"])
    width = float(cell["mean_width"])
    promotion_checks = {
        "coverage_at_least_0_90": coverage >= PROMOTION_COVERAGE,
        "width_within_target": width <= regime.target_width,
    }
    pilot_checks = {"coverage_at_least_0_80": coverage >= PILOT_COVERAGE}

    if regime.effect == 0.0:
        false_positive_rate = float(cell["false_positive_rate"])
        promotion_checks["false_positive_rate_at_most_0_10"] = (
            false_positive_rate <= PROMOTION_NULL_FALSE_POSITIVE_RATE
        )
        pilot_checks["false_positive_rate_at_most_0_20"] = (
            false_positive_rate <= PILOT_NULL_FALSE_POSITIVE_RATE
        )
    else:
        power = float(cell["power"])
        sign_stability = float(cell["sign_stability"])
        promotion_checks["power_at_least_0_80"] = power >= PROMOTION_POWER
        promotion_checks["sign_stability_at_least_0_90"] = (
            sign_stability >= PROMOTION_SIGN_STABILITY
        )
        pilot_checks["sign_stability_at_least_0_70"] = (
            sign_stability >= PILOT_SIGN_STABILITY
        )

    if all(promotion_checks.values()):
        recommendation = "promotion_ready"
        failed_checks: list[str] = []
    elif all(pilot_checks.values()):
        recommendation = "pilot_only"
        failed_checks = [
            name for name, passed in promotion_checks.items() if not passed
        ]
    else:
        recommendation = "insufficient"
        failed_checks = [name for name, passed in pilot_checks.items() if not passed]

    return {
        "regime": regime.name,
        "claim_type": regime.claim_type,
        "seed_count": seed_count,
        "estimator": "paired_seed_cluster_percentile",
        "target_width": regime.target_width,
        "coverage": coverage,
        "mean_width": width,
        "power": cell["power"],
        "false_positive_rate": cell["false_positive_rate"],
        "sign_stability": cell["sign_stability"],
        "recommendation": recommendation,
        "failed_checks": failed_checks,
    }


def _evaluate_gates(
    config: CalibrationConfig,
    cells: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> dict[str, bool]:
    by_key = {
        (str(cell["regime"]), int(cell["seed_count"]), str(cell["method"])): cell
        for cell in cells
    }
    expected_cells = len(config.regimes) * len(config.seed_counts) * len(config.methods)
    hierarchical_regimes = [
        regime for regime in config.regimes if regime.hierarchy_sd > 0.0
    ]
    undercoverage_deltas = []
    for regime in hierarchical_regimes:
        for seed_count in config.seed_counts:
            naive = by_key[(regime.name, seed_count, "naive_row_percentile")]
            clustered = by_key[
                (regime.name, seed_count, "paired_seed_cluster_percentile")
            ]
            undercoverage_deltas.append(
                float(clustered["coverage"]) - float(naive["coverage"])
            )

    promoted = [row for row in decisions if row["recommendation"] == "promotion_ready"]
    weak_decisions = [
        row for row in decisions if row["regime"] == "weak_high_noise_hierarchy"
    ]
    null_hierarchy_largest = by_key.get(
        (
            "null_hierarchy",
            max(config.seed_counts),
            "paired_seed_cluster_percentile",
        )
    )
    return {
        "all_preregistered_cells_reported": len(cells) == expected_cells,
        "hierarchical_undercoverage_detected": bool(undercoverage_deltas)
        and max(undercoverage_deltas) >= 0.05,
        "promotion_bars_undercoverage": all(
            float(row["coverage"]) >= PROMOTION_COVERAGE for row in promoted
        ),
        "promotion_meets_precision": all(
            float(row["mean_width"]) <= float(row["target_width"]) for row in promoted
        ),
        "largest_seed_null_fpr_controlled": (
            null_hierarchy_largest is None
            or float(null_hierarchy_largest["false_positive_rate"])
            <= PROMOTION_NULL_FALSE_POSITIVE_RATE
        ),
        "negative_regime_preserved": bool(weak_decisions)
        and all(row["recommendation"] != "promotion_ready" for row in weak_decisions),
    }


def run_calibration(config: CalibrationConfig = DEFAULT_CONFIG) -> dict[str, Any]:
    """Run every preregistered regime/seed/method cell without filtering."""

    _validate_config(config)
    rng = np.random.default_rng(config.simulation_seed)
    cells: list[dict[str, Any]] = []
    for regime in config.regimes:
        for seed_count in config.seed_counts:
            datasets = [
                _paired_differences(
                    regime,
                    seed_count=seed_count,
                    episodes_per_seed=config.episodes_per_seed,
                    rng=rng,
                )
                for _ in range(config.monte_carlo_reps)
            ]
            cells.extend(
                _simulate_cell(
                    regime,
                    seed_count,
                    method,
                    config,
                    datasets=datasets,
                    rng=rng,
                )
                for method in config.methods
            )
    clustered_cells = {
        (str(cell["regime"]), int(cell["seed_count"])): cell
        for cell in cells
        if cell["method"] == "paired_seed_cluster_percentile"
    }
    decisions = [
        _decision_row(regime, seed_count, clustered_cells[(regime.name, seed_count)])
        for regime in config.regimes
        for seed_count in config.seed_counts
    ]
    gates = _evaluate_gates(config, cells, decisions)
    return {
        "experiment_id": "S-022_seed_bootstrap_calibration",
        "status": "complete" if all(gates.values()) else "mixed_or_negative",
        "config_sha256": _config_sha256(config),
        "config": _config_dict(config),
        "model": {
            "estimand": "population mean paired treatment-control difference",
            "independent_unit": "seed",
            "nested_unit": "paired episode within seed",
            "data_generating_equation": (
                "difference = effect + seed_heterogeneity + paired_episode_noise"
            ),
        },
        "preregistered_thresholds": {
            "promotion_coverage": PROMOTION_COVERAGE,
            "promotion_power": PROMOTION_POWER,
            "promotion_sign_stability": PROMOTION_SIGN_STABILITY,
            "promotion_null_false_positive_rate": PROMOTION_NULL_FALSE_POSITIVE_RATE,
            "pilot_coverage": PILOT_COVERAGE,
            "pilot_sign_stability": PILOT_SIGN_STABILITY,
            "pilot_null_false_positive_rate": PILOT_NULL_FALSE_POSITIVE_RATE,
        },
        "cells": cells,
        "decision_table": decisions,
        "gates": gates,
    }


def build_public_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Allowlist aggregate fields safe to commit as the public result."""

    return {
        key: result[key]
        for key in (
            "experiment_id",
            "status",
            "config_sha256",
            "config",
            "model",
            "preregistered_thresholds",
            "cells",
            "decision_table",
            "gates",
        )
    } | {
        "allowed_claim": (
            "Within the preregistered synthetic regimes, treating nested episode "
            "rows as independent can understate uncertainty; promotion decisions "
            "must use seed-cluster resampling and meet the reported gates."
        ),
        "non_claims": [
            "This simulation does not establish one universal seed floor.",
            "Synthetic variance regimes do not replace calibration on public-safe empirical rows.",
            "A passing synthetic cell is not evidence for any model mechanism or field claim.",
        ],
    }


def _format_metric(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_markdown(summary: dict[str, Any]) -> str:
    """Render a human-auditable aggregate result report."""

    config = cast(dict[str, Any], summary["config"])
    gates = cast(dict[str, bool], summary["gates"])
    cells = cast(list[dict[str, Any]], summary["cells"])
    decisions = cast(list[dict[str, Any]], summary["decision_table"])
    lines = [
        "# S-022 Seed and Bootstrap Calibration",
        "",
        f"Status: **{summary['status']}**",
        "",
        "## Preregistered setup",
        "",
        f"- Configuration SHA-256: `{summary['config_sha256']}`",
        f"- Seed counts: `{config['seed_counts']}`",
        f"- Monte Carlo repetitions per cell: `{config['monte_carlo_reps']}`",
        f"- Bootstrap repetitions per interval: `{config['bootstrap_reps']}`",
        "- Independent resampling unit: seed; paired episode differences remain grouped.",
        "",
        "## Gates",
        "",
    ]
    lines.extend(
        f"- `{name}`: **{'PASS' if passed else 'FAIL'}**"
        for name, passed in gates.items()
    )
    lines.extend(
        [
            "",
            "## Method comparison",
            "",
            "| Regime | Seeds | Method | Coverage | Width | Power | FPR | Sign stability |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for cell in cells:
        lines.append(
            "| {regime} | {seed_count} | `{method}` | {coverage} | {mean_width} | "
            "{power} | {false_positive_rate} | {sign_stability} |".format(
                **{key: _format_metric(value) for key, value in cell.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Decision table",
            "",
            "| Regime | Seeds | Coverage | Width / target | Power | FPR | Sign | Recommendation |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in decisions:
        lines.append(
            "| {regime} | {seed_count} | {coverage} | {mean_width} / {target_width} | "
            "{power} | {false_positive_rate} | {sign_stability} | **{recommendation}** |".format(
                **{key: _format_metric(value) for key, value in row.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            str(summary["allowed_claim"]),
            "",
            "Negative regimes are retained as primary outcomes; no cell was dropped or retuned after simulation.",
            "",
            "This is a local synthetic calibration. It must be followed by calibration against representative public-safe empirical variance structures before a repository-wide policy is promoted.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_public_summary(
    summary: dict[str, Any], output_dir: Path
) -> tuple[Path, Path]:
    """Write the allowlisted JSON and matching Markdown report."""

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "summary.json"
    markdown_path = output_dir / "summary.md"
    json_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(render_markdown(summary), encoding="utf-8")
    return json_path, markdown_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/seed_bootstrap_calibration/results"),
    )
    args = parser.parse_args()
    summary = build_public_summary(run_calibration())
    for path in write_public_summary(summary, args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
