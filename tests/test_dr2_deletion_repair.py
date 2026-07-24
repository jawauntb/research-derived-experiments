"""Regression tests for DR2 — scaled deletion-repair nomination.

The load-bearing test here is :func:`test_cost_support_is_a_subset_of_weakness_support`,
which pins DR2's central result: within this formalisation, cost attribution can
never fire where weakness gain is silent. That is a theorem, not a measurement,
and the test exists so a future change to either nominator that appears to
violate it is caught rather than celebrated.
"""

from __future__ import annotations

import pytest

from experiments.deletion_repair.dr2_toys import (
    build_scaled_kinematics,
    build_scaled_transduction,
    dr2_toys,
)
from experiments.deletion_repair.nominators import cost_attribution, weakness_gain
from experiments.deletion_repair.oracle import build_oracle, enumerate_deletions
from experiments.deletion_repair.run_dr2 import MAX_D, dr2_nominator_scores, score_toy


def test_cost_support_is_a_subset_of_weakness_support() -> None:
    """DR2's central result, and the reason H1' is structurally unreachable.

    ``ext(R) ⊆ ext(R \\ D)`` always, because deleting constraints can only admit
    hypotheses. A minimum taken over a superset can only fall, so a strict cost
    improvement requires the extension to have strictly grown -- which is
    exactly a positive weakness gain. Hence ``cost > 0 ⟹ weakness > 0``.
    """
    for toy in dr2_toys():
        for deletion in enumerate_deletions(toy, MAX_D):
            if cost_attribution(toy, deletion) > 0.0:
                assert weakness_gain(toy, deletion) > 0.0, (
                    f"{toy.name}: {deletion} improves cost without enlarging the "
                    "extension, which is impossible when cost is a minimum over "
                    "the extension"
                )


def test_deleting_constraints_never_shrinks_the_extension() -> None:
    """The monotonicity the theorem rests on."""
    for toy in dr2_toys():
        base = len(toy.extension())
        for deletion in enumerate_deletions(toy, MAX_D):
            assert len(toy.extension(frozenset(deletion))) >= base


def test_scaled_toys_have_a_low_base_rate() -> None:
    """DR1's TT failed because random scored 0.67; DR2 must not repeat that."""
    for toy in dr2_toys():
        oracle = build_oracle(toy, MAX_D)
        base_rate = len(oracle.load_bearing) / len(oracle.rows)
        assert 0.0 < base_rate < 0.05, (
            f"{toy.name}: base rate {base_rate:.4f} is too high for "
            "verifications-to-first-hit to discriminate"
        )


def test_search_space_is_large_enough_to_need_a_nominator() -> None:
    """DR1's decisive limitation was 21 candidates; DR2 must be far past that."""
    for toy in dr2_toys():
        assert len(enumerate_deletions(toy, MAX_D)) >= 1000


def test_kinematics_needs_the_full_facet_triple() -> None:
    """No subset of the entangled facets frees anything."""
    toy = build_scaled_kinematics()
    facets = ("absolute_simultaneity", "no_length_contraction", "no_time_dilation")

    assert build_oracle(toy, MAX_D).load_bearing == (tuple(sorted(facets)),)
    for size in (1, 2):
        for i in range(len(facets) - size + 1):
            assert weakness_gain(toy, facets[i : i + size]) == 0.0


def test_transduction_requires_discharging_the_dangling_obligation() -> None:
    """Dropping recurrence alone loses order information and fails omega."""
    toy = build_scaled_transduction()
    load_bearing = set(build_oracle(toy, MAX_D).load_bearing)

    assert ("sequential_state_update",) not in load_bearing
    assert ("no_positional_input", "sequential_state_update") in load_bearing
    assert all(
        "sequential_state_update" in d and "no_positional_input" in d
        for d in load_bearing
    )


def test_max_disjunction_is_the_defect_dr1_named() -> None:
    """``max`` must still be beaten by at least one of the two fixes."""
    results = {t.name: score_toy(t) for t in dr2_toys()}
    for name, toy_result in results.items():
        best_single = min(
            toy_result.results[n].verifications_to_first_hit
            for n in ("weakness", "cost")
        )
        fixes = [
            toy_result.results[n].verifications_to_first_hit
            for n in ("sum_disjunction", "minrank_disjunction")
        ]
        assert min(fixes) <= best_single, f"{name}: neither combiner fix matched"


def test_nominators_beat_random_decisively() -> None:
    for toy in dr2_toys():
        result = score_toy(toy)
        best = min(r.verifications_to_first_hit for r in result.results.values())
        assert best < result.results["random"].verifications_to_first_hit


@pytest.mark.parametrize("nominator", ["weakness", "cost", "sum_disjunction"])
def test_scores_are_deterministic(nominator: str) -> None:
    toy = build_scaled_transduction()
    deletions = enumerate_deletions(toy, MAX_D)
    first = dr2_nominator_scores(toy, deletions)[nominator]
    second = dr2_nominator_scores(toy, deletions)[nominator]
    assert first == second
