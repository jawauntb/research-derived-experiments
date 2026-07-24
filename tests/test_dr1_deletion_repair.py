"""Regression tests for DR1 — deletion-repair nomination on toy systems.

These pin the properties that make DR1's verdict meaningful. In particular the
tie-breaking test pins the erratum-E1 defect that fired during DR1's own
construction: alphabetical tie-breaking handed a completely silent nominator
real top-3 credit.
"""

from __future__ import annotations

import pytest

from experiments.deletion_repair.nominators import (
    cost_attribution,
    rank,
    score_all,
    tie_fraction,
    weakness_gain,
)
from experiments.deletion_repair.oracle import (
    MAX_DELETION_SIZE,
    build_oracle,
    enumerate_deletions,
)
from experiments.deletion_repair.run_dr1 import score_toy
from experiments.deletion_repair.toys import (
    all_toys,
    build_toy_kinematics,
    build_toy_transduction,
)


def test_alpha_does_not_discriminate_on_kinematics() -> None:
    """The over-specification must be free on the child task, or there is no puzzle."""
    toy = build_toy_kinematics()
    # Both the Galilean member (k=0) and the Lorentz member (k=1) must satisfy
    # alpha; if alpha could tell them apart the deletion would be trivial.
    galilean = next(h for h in toy.hypotheses if h["k"] == 0.0)
    lorentz = next(h for h in toy.hypotheses if h["k"] == 1.0)

    assert toy.fits_alpha(galilean)
    assert toy.fits_alpha(lorentz)
    # But omega separates them.
    assert not toy.fits_omega(galilean)
    assert toy.fits_omega(lorentz)


def test_baseline_representation_cannot_reach_omega() -> None:
    """R as held must fail the parent task on both toys, else nothing is at stake."""
    for toy in all_toys():
        base = toy.extension()
        assert base, "the held representation must be satisfiable"
        assert any(toy.fits_alpha(h) for h in base), "R must solve the child task"
        assert not any(
            toy.fits_omega(h) and toy.cost(h) <= toy.omega_cost_budget for h in base
        ), f"{toy.name}: R already reaches omega, so there is no deletion to find"


def test_oracle_enumerates_all_small_deletions() -> None:
    for toy in all_toys():
        deletions = enumerate_deletions(toy)
        assert deletions
        assert all(1 <= len(d) <= MAX_DELETION_SIZE for d in deletions)
        assert len(set(deletions)) == len(deletions), "duplicate candidates"
        assert all(tuple(sorted(d)) == d for d in deletions), "unstable ordering"


def test_negatives_exist_in_the_oracle() -> None:
    """There must be valid-but-useless deletions, or recall@k is meaningless."""
    for toy in all_toys():
        oracle = build_oracle(toy)
        useless = [
            r for r in oracle.rows if r.valid_on_alpha and not r.covers_omega
        ]
        assert len(useless) >= 3, (
            f"{toy.name}: only {len(useless)} valid-but-useless deletions; "
            "the oracle needs negatives for recall to mean anything"
        )


def test_kinematics_load_bearing_is_the_entangled_pair() -> None:
    """Neither facet alone frees the extension -- the pair is the move."""
    toy = build_toy_kinematics()
    oracle = build_oracle(toy)
    assert oracle.load_bearing == (
        ("absolute_simultaneity", "no_length_contraction"),
    )
    # Each singleton on its own is worthless: the other facet still pins k=0.
    assert weakness_gain(toy, ("absolute_simultaneity",)) == 0.0
    assert weakness_gain(toy, ("no_length_contraction",)) == 0.0


def test_cost_is_silent_on_kinematics_and_weakness_fires() -> None:
    toy = build_toy_kinematics()
    deletions = enumerate_deletions(toy)
    scores = score_all(toy, deletions)

    assert tie_fraction(scores["cost"]) == 1.0, "cost must be flat on TK"
    assert all(cost_attribution(toy, d) == 0.0 for d in deletions)
    assert tie_fraction(scores["weakness"]) < 1.0, "weakness must have an opinion on TK"


def test_cost_fires_on_transduction() -> None:
    toy = build_toy_transduction()
    dropping_sequential = ("sequential_state_update",)
    assert cost_attribution(toy, dropping_sequential) > 0.0
    assert cost_attribution(toy, ("bounded_state",)) == 0.0


def test_tie_breaking_is_shuffled_not_alphabetical() -> None:
    """Pins the E1 defect found during DR1's construction.

    A completely flat nominator must score at chance. Alphabetical ordering
    would instead hand it whichever candidate sorts first -- a permitted field
    (the alphabet) carrying information it has not earned.
    """
    flat: dict[tuple[str, ...], float] = {
        ("aaa",): 0.0,
        ("bbb",): 0.0,
        ("ccc",): 0.0,
        ("ddd",): 0.0,
    }
    ordering = rank(flat)

    assert sorted(ordering) == sorted(flat), "ranking must be a permutation"
    assert ordering != sorted(flat), (
        "a flat nominator was ranked alphabetically; that is the E1 failure mode"
    )
    assert rank(flat) == ordering, "tie-breaking must be reproducible under its seed"


def test_scoring_is_deterministic() -> None:
    for toy in all_toys():
        assert score_toy(toy) == score_toy(toy)


@pytest.mark.parametrize("toy_name", ["toy_kinematics", "toy_transduction"])
def test_recall_denominator_is_capped_at_k(toy_name: str) -> None:
    toy = next(t for t in all_toys() if t.name == toy_name)
    score = score_toy(toy)
    for entry in score.scores.values():
        assert 1 <= entry.recall_denominator <= 3
        assert 0.0 <= entry.recall_at_k <= 1.0
