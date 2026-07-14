from __future__ import annotations

import math

from experiments.passive_active_phase_map.core import (
    ExperimentConfig,
    compare_transition_models,
    evaluate_hysteresis,
    run_experiment,
)


def _curve_rows(*, discontinuous: bool) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for architecture in ("linear", "tanh"):
        for seed in range(5):
            for index in range(11):
                coupling = index / 10
                if discontinuous:
                    value = 0.1 + 0.05 * coupling + (0.7 if coupling >= 0.5 else 0.0)
                else:
                    value = 0.1 + 0.8 / (1.0 + math.exp(-8.0 * (coupling - 0.5)))
                rows.append(
                    {
                        "architecture": architecture,
                        "seed": seed,
                        "coupling": coupling,
                        "causal_specific_effect": value + seed * 0.0005,
                    }
                )
    return rows


def test_model_comparison_distinguishes_jump_from_smooth_crossover() -> None:
    smooth = compare_transition_models(_curve_rows(discontinuous=False), "causal_specific_effect")
    jump = compare_transition_models(_curve_rows(discontinuous=True), "causal_specific_effect")

    assert smooth["preferred_model"] == "smooth"
    assert smooth["segmented_advantage"] < 0.10
    assert jump["preferred_model"] == "segmented"
    assert jump["segmented_advantage"] >= 0.10


def test_hysteresis_gate_rejects_identical_direction_curves() -> None:
    rows: list[dict[str, float | int | str]] = []
    for architecture in ("linear", "tanh"):
        for seed in range(5):
            for coupling in (0.0, 0.25, 0.5, 0.75, 1.0):
                value = coupling + seed * 0.001
                for condition in ("continuation", "reinit", "washout"):
                    for direction in ("forward", "reverse"):
                        rows.append(
                            {
                                "architecture": architecture,
                                "seed": seed,
                                "coupling": coupling,
                                "condition": condition,
                                "direction": direction,
                                "causal_specific_effect": value,
                            }
                        )

    verdict = evaluate_hysteresis(rows, bootstrap_samples=200, bootstrap_seed=17)

    assert verdict["pass"] is False
    assert verdict["verdict"] == "no_hysteresis"
    assert verdict["contiguous_significant_points"] == 0
    assert verdict["loop_area"] == 0.0
    point = verdict["conditions"]["continuation"]["pointwise"][0]
    assert point["n_seed_clusters"] == 5
    assert point["architectures_per_seed"] == 2
    assert "n_pairs" not in point


def test_hysteresis_gate_requires_exact_direction_budget_matching() -> None:
    rows: list[dict[str, float | int | str]] = []
    for architecture in ("linear", "tanh"):
        for seed in range(5):
            for coupling in (0.0, 0.25, 0.5, 0.75, 1.0):
                for condition in ("continuation", "reinit", "washout"):
                    for direction in ("forward", "reverse"):
                        effect = 0.08 if condition != "reinit" and direction == "forward" else 0.0
                        rows.append(
                            {
                                "architecture": architecture,
                                "seed": seed,
                                "coupling": coupling,
                                "condition": condition,
                                "direction": direction,
                                "causal_specific_effect": coupling + effect,
                                "total_updates": 100,
                            }
                        )

    matched = evaluate_hysteresis(rows, bootstrap_samples=200, bootstrap_seed=17)
    assert matched["pass"] is True
    assert matched["budget_matched"] is True
    assert all(
        point["n_seed_clusters"] == 5
        and point["architectures_per_seed"] == 2
        for point in matched["conditions"]["continuation"]["pointwise"]
    )

    mismatched_rows = [dict(row) for row in rows]
    mismatched_rows[1]["total_updates"] = 99
    mismatched = evaluate_hysteresis(
        mismatched_rows,
        bootstrap_samples=200,
        bootstrap_seed=17,
    )
    assert mismatched["pass"] is False
    assert mismatched["budget_matched"] is False


def test_hysteresis_bootstrap_clusters_architectures_within_seed() -> None:
    def rows_for(architectures: tuple[str, ...]) -> list[dict[str, float | int | str]]:
        rows: list[dict[str, float | int | str]] = []
        seed_effects = (-0.20, -0.10, -0.05, 0.05, 0.20)
        for architecture in architectures:
            for seed, effect in enumerate(seed_effects):
                for condition in ("continuation", "reinit", "washout"):
                    for direction in ("forward", "reverse"):
                        rows.append(
                            {
                                "architecture": architecture,
                                "seed": seed,
                                "coupling": 0.5,
                                "condition": condition,
                                "direction": direction,
                                "causal_specific_effect": effect
                                if direction == "forward"
                                else 0.0,
                                "total_updates": 100,
                            }
                        )
        return rows

    two_architectures = evaluate_hysteresis(
        rows_for(("linear", "tanh")),
        bootstrap_samples=500,
        bootstrap_seed=29,
    )
    duplicated_architectures = evaluate_hysteresis(
        rows_for(("linear", "linear_copy", "tanh", "tanh_copy")),
        bootstrap_samples=500,
        bootstrap_seed=29,
    )

    two_point = two_architectures["conditions"]["continuation"]["pointwise"][0]
    duplicated_point = duplicated_architectures["conditions"]["continuation"]["pointwise"][0]
    assert math.isclose(two_point["ci95_low"], duplicated_point["ci95_low"])
    assert math.isclose(two_point["ci95_high"], duplicated_point["ci95_high"])
    assert duplicated_point["n_seed_clusters"] == 5
    assert duplicated_point["architectures_per_seed"] == 4


def test_tiny_registered_experiment_is_deterministic_and_bounded() -> None:
    config = ExperimentConfig(
        couplings=(0.0, 0.5, 1.0),
        architectures=("linear", "tanh"),
        seeds=(0, 1),
        samples=96,
        phase_updates=24,
        path_updates=12,
        washout_updates=4,
        retention_checkpoints=(0, 4, 8),
        bootstrap_samples=100,
    )

    first = run_experiment(config)
    second = run_experiment(config)

    assert first == second
    assert first["manifest"]["architectures"] == ["linear", "tanh"]
    assert first["manifest"]["seeds"] == [0, 1]
    assert len(first["phase_rows"]) == 12
    assert {row["order_parameter"] for row in first["phase_curve"]} == {
        "causal_specific_effect",
        "perturbation_failure_rate",
        "viability_buffer",
        "geometry_gap",
        "return",
    }
    assert first["summary"]["bifurcation"]["verdict"] in {
        "bifurcation",
        "bifurcation_not_supported",
    }
    assert first["summary"]["hysteresis"]["verdict"] in {
        "hysteresis",
        "no_hysteresis",
    }
    assert first["summary"]["hysteresis"]["budget_matched"] is True

    path_rows = first["hysteresis_rows"]
    for condition in ("continuation", "reinit", "washout"):
        for architecture in ("linear", "tanh"):
            for seed in (0, 1):
                for coupling in (0.0, 0.5, 1.0):
                    pair = [
                        row
                        for row in path_rows
                        if row["condition"] == condition
                        and row["architecture"] == architecture
                        and row["seed"] == seed
                        and row["coupling"] == coupling
                    ]
                    assert {row["direction"] for row in pair} == {"forward", "reverse"}
                    assert len({row["total_updates"] for row in pair}) == 1
