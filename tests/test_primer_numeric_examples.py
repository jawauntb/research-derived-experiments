"""Regression tests for the executable arithmetic in the mathematics primer."""

from __future__ import annotations

import math
from pathlib import Path


PRIMER = Path(__file__).parents[1] / "docs/primers/mathematics_of_constraint_primer.html"


def _primer_source() -> str:
    return PRIMER.read_text(encoding="utf-8")


def _rho_star(weight: float, dimension: float, multiplier: float) -> float:
    """Pointwise KKT solution for the positive-price Lagrangian."""

    return ((2.0 * weight) / (dimension * multiplier)) ** (dimension / (dimension + 2.0))


def _multiplier_for_budget(weights: list[float], dimension: float, budget: float) -> float:
    """Solve the active-budget equation for equal-measure cells."""

    exponent = dimension / (dimension + 2.0)
    coefficient_sum = sum((2.0 * weight / dimension) ** exponent for weight in weights)
    return (coefficient_sum / budget) ** (1.0 / exponent)


def test_lagrangian_sign_and_kkt_toy_allocation_are_bounded() -> None:
    source = _primer_source()

    assert "&nbsp;+&nbsp; λ·ρ(x)" in source
    assert "&nbsp;−&nbsp; λB" in source
    assert "&nbsp;−&nbsp; λ·ρ(x)" not in source
    assert "&nbsp;−&nbsp; λ &nbsp;=&nbsp; 0" not in source
    assert "&nbsp;+&nbsp; λ &nbsp;=&nbsp; 0" in source

    # Two equal cells give an exact hand-check from the primer: d=1, w=(1, 8), B=3.
    weights = [1.0, 8.0]
    dimension = 1.0
    budget = 3.0
    multiplier = _multiplier_for_budget(weights, dimension, budget)
    allocation = [_rho_star(weight, dimension, multiplier) for weight in weights]

    assert math.isclose(multiplier, 2.0, rel_tol=1e-12, abs_tol=1e-12)
    assert all(
        math.isclose(value, expected, rel_tol=1e-12, abs_tol=1e-12)
        for value, expected in zip(allocation, [1.0, 2.0])
    )
    assert math.isclose(sum(allocation), budget, rel_tol=1e-12, abs_tol=1e-12)

    residuals = [
        -(2.0 / dimension) * weight * allocation_value ** (-(dimension + 2.0) / dimension)
        + multiplier
        for weight, allocation_value in zip(weights, allocation)
    ]
    assert all(math.isclose(residual, 0.0, abs_tol=1e-12) for residual in residuals)

    def lagrangian(values: list[float]) -> float:
        distortion = sum(
            weight * value ** (-2.0 / dimension) for weight, value in zip(weights, values)
        )
        return distortion + multiplier * (sum(values) - budget)

    # The positive multiplier makes the priced minimization coercive as density grows;
    # the old negative sign would instead run to -infinity.
    assert lagrangian([1.0e6, 1.0e6]) > lagrangian([1.0, 1.0])


def test_discount_arithmetic_for_one_hundred_steps() -> None:
    assert math.isclose(0.99**100, 0.3660323412732292, rel_tol=1e-12)
    assert math.isclose(0.5**100, 7.888609052210118e-31, rel_tol=1e-12)

    source = _primer_source()
    assert "γ = 0.5, ~7.9×10<sup>−31</sup> of its face value" in source
    assert "γ = 0.5, ~0.001×" not in source


def test_value_of_information_is_positive_expected_error_reduction() -> None:
    mae_now = [0.8, 0.6, 0.4]
    mae_after = [0.5, 0.5, 0.25]
    reduction = sum(now - after for now, after in zip(mae_now, mae_after)) / len(mae_now)

    assert math.isclose(reduction, 0.18333333333333335, rel_tol=1e-12)
    assert reduction > 0.0

    source = _primer_source()
    assert "MAE<sub>now</sub> − MAE<sub>after</sub>" in source
    assert "MAE<sub>after</sub> − MAE<sub>now</sub>" not in source
    assert "heuristic is not" in source
