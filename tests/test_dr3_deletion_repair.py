"""Regression tests for DR3 — cost moved off the extension.

The load-bearing test is :func:`test_the_dr2_theorem_is_broken_by_construction`,
which pins the whole point of DR3: once cost stops being a minimum over the
extension, ``cost > 0 and weakness == 0`` becomes reachable.
"""

from __future__ import annotations

from experiments.deletion_repair.dr3_toys import (
    build_costly_toy,
    build_restrictive_toy,
    dr3_toys,
)
from experiments.deletion_repair.run_dr3 import (
    cost_relief,
    enumerate_deletions,
    score_toy,
    weakness_gain,
)


def test_the_dr2_theorem_is_broken_by_construction() -> None:
    """DR2 proved cost>0 implies weakness>0. DR3 severs the premise."""
    toy = build_costly_toy()
    independent = [
        d
        for d in enumerate_deletions(toy)
        if cost_relief(toy, d) > 0.0 and weakness_gain(toy, d) == 0.0
    ]
    assert independent, (
        "DR3's whole purpose is to admit cost relief without extension growth; "
        "if this is empty the fix did not take"
    )


def test_costly_proposition_is_vacuous_as_a_predicate() -> None:
    """`sequential_schedule` must filter nothing, or the axes stay coupled."""
    toy = build_costly_toy()
    full = toy.extension()
    without = toy.extension(frozenset({"sequential_schedule"}))
    assert len(full) == len(without)
    assert toy.proposition_costs["sequential_schedule"] > 0.0


def test_restrictive_toy_has_zero_representation_cost() -> None:
    toy = build_restrictive_toy()
    assert toy.representation_cost() == 0.0
    for deletion in enumerate_deletions(toy)[:50]:
        assert cost_relief(toy, deletion) == 0.0


def test_each_toy_isolates_one_axis() -> None:
    rk, ct = build_restrictive_toy(), build_costly_toy()
    rk_result, ct_result = score_toy(rk), score_toy(ct)

    assert rk_result.results["cost"].tie_fraction == 1.0, "cost must be silent on RK"
    assert ct_result.results["weakness"].tie_fraction == 1.0, "weakness silent on CT"


def test_complementarity_the_best_single_nominator_differs() -> None:
    """DR2's H1' restated -- now reachable because the theorem's premise is gone."""
    best = {}
    for toy in dr3_toys():
        result = score_toy(toy)
        best[toy.name] = min(
            ("weakness", "cost"),
            key=lambda n: result.results[n].verifications_to_first_hit,
        )
    assert best["restrictive_kinematics"] == "weakness"
    assert best["costly_transduction"] == "cost"


def test_speedup_is_bounded_by_the_base_rate() -> None:
    """Pins the H4'' defect: the gate was unachievable, not merely unmet."""
    for toy in dr3_toys():
        result = score_toy(toy)
        best_speedup = max(r.speedup_vs_random for r in result.results.values())
        assert best_speedup <= result.expected_random + 1e-9, (
            "speedup cannot exceed expected_random, since verifications >= 1"
        )


def test_nominators_reach_the_theoretical_optimum_on_both_toys() -> None:
    for toy in dr3_toys():
        result = score_toy(toy)
        assert min(r.verifications_to_first_hit for r in result.results.values()) == 1
