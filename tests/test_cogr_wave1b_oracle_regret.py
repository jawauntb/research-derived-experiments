"""Tests for the Wave 1b SET-level oracle-regret metric harness.

Six regressions per the Wave 1b task brief:

1. Exhaustive set enumeration is correct on a small hand-designed toy
   episode where every candidate subset's ``Δ_task`` is analytically
   computable from the wave 0 additive rule and the wave 1b bundle
   adjustments.
2. The SET-level :func:`oracle_recall_at_k` formula matches
   ``|selected ∩ union(oracle_top_k_sets)| / budget`` on hand-designed
   selected / oracle tuples covering the four boundary cases.
3. :func:`interaction_recovery` correctly identifies planted
   complementary-pair recovery and planted dangerous-conjunction
   avoidance / non-avoidance across the four bundle-plant cases.
4. :meth:`OracleSealedEnvironment.evaluate_set` refuses a second call
   with the same ``(episode, S)`` key (the wave 1b enumeration-budget
   guard).
5. :func:`regret_ci` is byte-deterministic for a fixed seed and returns
   a sensible interval on toy data.
6. :meth:`IntegrityAudit.assert_clean` refuses every wave 1b oracle-path
   entry point because each function's source dereferences a sealed
   :class:`EpisodeSpec` attribute (a member of
   :attr:`IntegrityAudit.FORBIDDEN_ATTRS`).
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
    IntegrityAudit,
    LeakageError,
    SealedEnvironment,
    SealedEvaluationError,
)
from experiments.concern_gated_retrieval_e2.wave1b.oracle_receipt import (
    INTERACTION_RECOVERY_KEYS,
    PLANTED_BUNDLES_RECOVERED_KEYS,
    OracleReceipt,
)
from experiments.concern_gated_retrieval_e2.wave1b.oracle_regret import (
    DEFAULT_BOOTSTRAP_RESAMPLES,
    MAX_ORACLE_ENUMERATION_CARDINALITY,
    PlantedBundles,
    build_oracle_receipt,
    compute_oracle_topk_sets,
    cumulative_regret,
    enumerate_set_deltas,
    interaction_recovery,
    oracle_recall_at_k,
    planted_bundles_from_manifest,
    planted_bundles_recovered,
    regret_ci,
    simple_regret_set,
)
from experiments.concern_gated_retrieval_e2.wave1b.sealed_env_ext import (
    COMPLEMENTARY_JOINT_BONUS,
    DANGEROUS_TRIPLE_PENALTY,
    ISOLATION_CONTEXT_PENALTY,
    OracleSealedEnvironment,
    SetOutcome,
    compute_set_delta,
)


# --------------------------------------------------------------------------- #
# Toy episode helpers                                                          #
# --------------------------------------------------------------------------- #


def _make_toy_episode(
    *,
    role_map: dict[str, str],
    utility_map: dict[str, float],
    answer_key: tuple[str, ...],
    candidate_nodes: tuple[str, ...] | None = None,
    budget: int = 2,
    seed: int = 200_000,
    family: str = "delayed_commitments",
    split: str = "confirmatory",
) -> EpisodeSpec:
    """Return a small hand-designed :class:`EpisodeSpec` for the tests.

    The candidate set defaults to the sorted keys of ``role_map`` so
    the caller can declare a compact toy layout in one dict.
    """
    if candidate_nodes is None:
        candidate_nodes = tuple(sorted(role_map))
    return EpisodeSpec(
        episode_id=f"toy::{family}::{seed}",
        template_family_split=split,  # ty: ignore[invalid-argument-type]  # noqa
        family=family,  # ty: ignore[invalid-argument-type]  # noqa
        seed=seed,
        context_nodes=("ctx0",),
        care_anchors={node: 0.5 for node in candidate_nodes},
        candidate_nodes=candidate_nodes,
        budget=budget,
        role=role_map,
        utility=utility_map,
        _answer_key=answer_key,
    )


# --------------------------------------------------------------------------- #
# 1. Exhaustive set enumeration is correct on a hand-designed toy.             #
# --------------------------------------------------------------------------- #


def test_exhaustive_set_enumeration_matches_hand_computed_deltas() -> None:
    """Enumerate a toy episode where every subset's Δ is computable by hand.

    Layout:
      * ``L`` — the answer-key node (utility 0.5).
      * ``A`` — a distractor (utility 0.2, non-answer).
      * ``B`` — a distractor (utility 0.1, non-answer).
      * ``C`` — a zero-utility filler.

    Wave 0 additive scoring:
      Δ({L})    = 0.5
      Δ({A})    = -0.25 * 0.2 = -0.05
      Δ({B})    = -0.25 * 0.1 = -0.025
      Δ({C})    = 0.0
      Δ({L, A}) = 0.5 - 0.25 * 0.2 = 0.45
      Δ({L, B}) = 0.5 - 0.25 * 0.1 = 0.475
      Δ({L, C}) = 0.5
      Δ({A, B}) = -0.25 * (0.2 + 0.1) = -0.075
      Δ({A, C}) = -0.05
      Δ({B, C}) = -0.025
      Δ({})     = 0.0

    No bundles → no bundle adjustment.
    """
    episode = _make_toy_episode(
        role_map={
            "L": "role_load_bearing",
            "A": "role_distractor_a",
            "B": "role_distractor_b",
            "C": "role_neutral",
        },
        utility_map={"L": 0.5, "A": 0.2, "B": 0.1, "C": 0.0},
        answer_key=("L",),
        budget=2,
    )
    enumeration = enumerate_set_deltas(episode, budget=2)
    delta_map = enumeration.delta_map

    def _key(*nodes: str) -> frozenset[str]:
        return frozenset(nodes)

    # 1 empty + 4 singletons + 6 pairs = 11 subsets at |S| ≤ 2.
    assert enumeration.total_sets_enumerated == 11
    assert delta_map[_key()] == pytest.approx(0.0)
    assert delta_map[_key("L")] == pytest.approx(0.5)
    assert delta_map[_key("A")] == pytest.approx(-0.05)
    assert delta_map[_key("B")] == pytest.approx(-0.025)
    assert delta_map[_key("C")] == pytest.approx(0.0)
    assert delta_map[_key("L", "A")] == pytest.approx(0.45)
    assert delta_map[_key("L", "B")] == pytest.approx(0.475)
    assert delta_map[_key("L", "C")] == pytest.approx(0.5)
    assert delta_map[_key("A", "B")] == pytest.approx(-0.075)
    assert delta_map[_key("A", "C")] == pytest.approx(-0.05)
    assert delta_map[_key("B", "C")] == pytest.approx(-0.025)

    # Top-k by descending Δ. Ties broken by canonical-sorted tuple
    # order. ``{L, C}`` (Δ=0.5) and ``{L}`` (Δ=0.5) tie; canonical
    # sort of {L, C} is ("C", "L"), which is lex-less-than ("L",) —
    # so the pair sorts first.
    top_k = enumeration.top_k_sets
    assert top_k[0] == ("C", "L")
    assert top_k[1] == ("L",)


def test_bundle_adjustments_applied_in_set_delta() -> None:
    """Complementary bonus, dangerous penalty, and isolation penalty apply.

    Toy episode plants:
      * ``L``  — answer key (utility 0.4).
      * ``P1``, ``P2`` — complementary pair (each utility 0.05).
      * ``D1``, ``D2``, ``D3`` — dangerous conjunction (each utility 0.05).
      * ``I``  — isolation distractor (utility 0.3).

    Cases:
      * ``{P1, P2}``            picks up +COMPLEMENTARY_JOINT_BONUS.
      * ``{D1, D2, D3}``        picks up -DANGEROUS_TRIPLE_PENALTY (clamped).
      * ``{I}``                 picks up -ISOLATION_CONTEXT_PENALTY.
    """
    episode = _make_toy_episode(
        role_map={
            "L": "role_load_bearing",
            "P1": "complementary_pair_member",
            "P2": "complementary_pair_member",
            "D1": "dangerous_conjunction_member",
            "D2": "dangerous_conjunction_member",
            "D3": "dangerous_conjunction_member",
            "I": "isolation_distractor",
        },
        utility_map={
            "L": 0.4,
            "P1": 0.05,
            "P2": 0.05,
            "D1": 0.05,
            "D2": 0.05,
            "D3": 0.05,
            "I": 0.3,
        },
        answer_key=("L",),
        budget=3,
    )

    # {P1, P2}: 0 hit_reward, miss = 0.25*(0.05+0.05) = 0.025, bonus = 0.40.
    p_outcome = compute_set_delta(episode, frozenset({"P1", "P2"}))
    assert p_outcome.complementary_pairs_hit == 1
    assert p_outcome.delta_task == pytest.approx(
        -0.025 + COMPLEMENTARY_JOINT_BONUS
    )

    # {D1, D2, D3}: 0 hit_reward, miss = 0.25 * 0.15 = 0.0375,
    # bundle = -DANGEROUS_TRIPLE_PENALTY.
    d_outcome = compute_set_delta(episode, frozenset({"D1", "D2", "D3"}))
    assert d_outcome.dangerous_triples_hit == 1
    assert d_outcome.delta_task == pytest.approx(
        -0.0375 - DANGEROUS_TRIPLE_PENALTY
    )

    # {I}: 0 hit_reward, miss = 0.25 * 0.3 = 0.075, isolation = -0.30.
    i_outcome = compute_set_delta(episode, frozenset({"I"}))
    assert i_outcome.isolation_hits == 1
    assert i_outcome.delta_task == pytest.approx(
        -0.075 - ISOLATION_CONTEXT_PENALTY
    )


# --------------------------------------------------------------------------- #
# 2. SET-level Recall@k formula correct.                                       #
# --------------------------------------------------------------------------- #


def test_oracle_recall_at_k_formula_boundary_cases() -> None:
    """Cover empty overlap, partial overlap, full overlap, and duplicates."""
    # Empty overlap: selected disjoint from oracle union.
    assert oracle_recall_at_k(
        selected_set=("a", "b"),
        oracle_top_k_sets=(("c",), ("d", "e")),
        budget=2,
    ) == pytest.approx(0.0)

    # Partial overlap: one of two selected in the oracle union.
    # Denominator is budget (=2), not |selected|.
    assert oracle_recall_at_k(
        selected_set=("a", "b"),
        oracle_top_k_sets=(("a",), ("c",)),
        budget=2,
    ) == pytest.approx(0.5)

    # Full overlap: both selected in the oracle union.
    assert oracle_recall_at_k(
        selected_set=("a", "b"),
        oracle_top_k_sets=(("a", "b"), ("c",)),
        budget=2,
    ) == pytest.approx(1.0)

    # Oracle union deduplicated across the top-k sets — the same node
    # appearing in multiple sets does not inflate recall.
    assert oracle_recall_at_k(
        selected_set=("a",),
        oracle_top_k_sets=(("a",), ("a", "b"), ("a", "c")),
        budget=1,
    ) == pytest.approx(1.0)

    # Larger union than selected — recall bounded by budget.
    assert oracle_recall_at_k(
        selected_set=("a",),
        oracle_top_k_sets=(("a", "b", "c"),),
        budget=1,
    ) == pytest.approx(1.0)


def test_oracle_recall_at_k_rejects_zero_budget() -> None:
    """``budget = 0`` is refused — a policy that retrieves nothing is not scored here."""
    with pytest.raises(ValueError, match="positive"):
        oracle_recall_at_k(("a",), (("a",),), budget=0)


def test_simple_regret_set_uses_max_over_delta_map() -> None:
    """``simple_regret_set`` is the max Δ minus the selected Δ."""
    delta_map = {
        frozenset({"a"}): 0.9,
        frozenset({"a", "b"}): 0.8,
        frozenset({"c"}): 0.1,
    }
    # Oracle best is {a} (0.9); policy picked {c} (0.1) → regret = 0.8.
    regret = simple_regret_set(
        selected_set=("c",),
        oracle_top_k_sets=(("a",), ("a", "b")),
        delta_sets=delta_map,
    )
    assert regret == pytest.approx(0.8)

    # Policy tied with oracle → regret = 0.
    tied = simple_regret_set(
        selected_set=("a",),
        oracle_top_k_sets=(("a",),),
        delta_sets=delta_map,
    )
    assert tied == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# 3. interaction_recovery identifies complementary + dangerous cases.          #
# --------------------------------------------------------------------------- #


def test_interaction_recovery_identifies_complementary_and_dangerous_cases() -> None:
    """Four planting configurations exercised.

    * complementary pair recovered   → num_complementary_recovered == 1
    * complementary pair not recovered (one member missing) → 0
    * dangerous conjunction fully loaded → NOT avoided (avoided_flag=False)
    * dangerous conjunction partially loaded → avoided (True)
    """
    planted = PlantedBundles(
        useful_singletons=("L",),
        complementary_pairs=(("P1", "P2"), ("Q1", "Q2")),
        dangerous_conjunctions=(("D1", "D2", "D3"), ("E1", "E2", "E3")),
        isolation_distractors=("I",),
    )

    # Selected set:
    #  * recovers pair (P1, P2)
    #  * misses pair (Q1, Q2) — only Q1 loaded
    #  * fully loads dangerous (D1, D2, D3) — NOT avoided
    #  * partially loads dangerous (E1) — avoided
    selected = ("P1", "P2", "Q1", "D1", "D2", "D3", "E1")

    receipt = interaction_recovery(selected, planted)

    # Schema check.
    assert set(receipt.keys()) == set(INTERACTION_RECOVERY_KEYS)

    complementary = dict(receipt["complementary_recovered"])
    assert complementary[("P1", "P2")] is True
    assert complementary[("Q1", "Q2")] is False
    assert receipt["num_complementary_recovered"] == 1

    dangerous = dict(receipt["dangerous_avoided"])
    assert dangerous[("D1", "D2", "D3")] is False  # NOT avoided (all loaded)
    assert dangerous[("E1", "E2", "E3")] is True  # avoided
    assert receipt["num_dangerous_avoided"] == 1


def test_planted_bundles_recovered_summary_schema() -> None:
    """``planted_bundles_recovered`` returns the pinned key set."""
    planted = PlantedBundles(
        useful_singletons=("L",),
        complementary_pairs=(("P1", "P2"),),
        contradictory_pairs=(("K1", "K2"),),
        dangerous_conjunctions=(("D1", "D2", "D3"),),
        isolation_distractors=("I",),
    )
    summary = planted_bundles_recovered(("L", "P1", "P2"), planted)
    assert set(summary.keys()) == set(PLANTED_BUNDLES_RECOVERED_KEYS)
    assert summary["useful_singletons_recovered"] == 1
    assert summary["complementary_pairs_recovered"] == 1
    assert summary["contradictory_pairs_avoided"] == 1  # K1, K2 not loaded
    assert summary["dangerous_conjunctions_avoided"] == 1
    assert summary["isolation_distractors_avoided"] == 1


# --------------------------------------------------------------------------- #
# 4. evaluate_set one-call-per-key enforced.                                    #
# --------------------------------------------------------------------------- #


def test_evaluate_set_refuses_duplicate_key() -> None:
    """A second ``evaluate_set`` call with the same ``S`` raises."""
    episode = _make_toy_episode(
        role_map={"L": "role_load_bearing", "A": "role_distractor"},
        utility_map={"L": 0.5, "A": 0.1},
        answer_key=("L",),
        budget=2,
    )
    env = OracleSealedEnvironment(episode, mode="confirmatory")
    env.observe(seed=episode.seed)

    first = env.evaluate_set(frozenset({"L"}))
    assert isinstance(first, SetOutcome)

    with pytest.raises(SealedEvaluationError, match="at most once per"):
        env.evaluate_set(frozenset({"L"}))

    # Order-independent equality: {"L", "A"} vs {"A", "L"} should also
    # collide on the second call.
    env.evaluate_set(frozenset({"L", "A"}))
    with pytest.raises(SealedEvaluationError, match="at most once per"):
        env.evaluate_set(frozenset({"A", "L"}))


def test_evaluate_set_records_history() -> None:
    """Recorded ``(S, SetOutcome)`` history is exposed as an immutable snapshot."""
    episode = _make_toy_episode(
        role_map={"L": "role_load_bearing", "A": "role_distractor"},
        utility_map={"L": 0.5, "A": 0.1},
        answer_key=("L",),
        budget=2,
    )
    env = OracleSealedEnvironment(episode, mode="confirmatory")
    env.observe(seed=episode.seed)
    env.evaluate_set(frozenset({"L"}))
    env.evaluate_set(frozenset({"L", "A"}))

    history = env.set_evaluations
    assert frozenset({"L"}) in history
    assert frozenset({"L", "A"}) in history
    assert history[frozenset({"L"})].delta_task == pytest.approx(0.5)

    delta_map = env.set_delta_map()
    assert delta_map[frozenset({"L"})] == pytest.approx(0.5)
    assert delta_map[frozenset({"L", "A"})] == pytest.approx(0.475)


# --------------------------------------------------------------------------- #
# 5. Deterministic bootstrap CI.                                                #
# --------------------------------------------------------------------------- #


def test_regret_ci_is_byte_deterministic_for_fixed_seed() -> None:
    """Same input + same seed → byte-identical CI bounds."""
    values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    ci_a = regret_ci(values, n_bootstrap=500, seed=42)
    ci_b = regret_ci(values, n_bootstrap=500, seed=42)
    assert ci_a == ci_b
    # A different seed should typically yield a different pair (this is
    # a probabilistic assertion, but with 500 resamples the collision
    # probability is ~0).
    ci_c = regret_ci(values, n_bootstrap=500, seed=43)
    assert ci_a != ci_c


def test_regret_ci_bounds_bracket_the_mean() -> None:
    """The 95% CI on a large N bracket the sample mean."""
    # Constant vector → CI collapses to the value.
    constant = [0.42] * 50
    lo, hi = regret_ci(constant, n_bootstrap=200, seed=0)
    assert lo == pytest.approx(0.42)
    assert hi == pytest.approx(0.42)

    # Uniform-ish data: CI must bracket the mean.
    values = [i / 100.0 for i in range(100)]
    mean = sum(values) / len(values)
    lo, hi = regret_ci(values, n_bootstrap=DEFAULT_BOOTSTRAP_RESAMPLES, seed=0)
    assert lo <= mean <= hi


def test_regret_ci_empty_input_returns_zero_pair() -> None:
    """Empty input returns ``(0.0, 0.0)`` rather than raising."""
    assert regret_ci([], n_bootstrap=10, seed=0) == (0.0, 0.0)


def test_cumulative_regret_sums_receipts() -> None:
    """``cumulative_regret`` sums the ``simple_regret_set`` of the receipts."""
    receipts = [
        _make_dummy_receipt(regret=0.1),
        _make_dummy_receipt(regret=0.2),
        _make_dummy_receipt(regret=0.3),
    ]
    assert cumulative_regret(receipts) == pytest.approx(0.6)


def _make_dummy_receipt(*, regret: float) -> OracleReceipt:
    """Return a syntactically-valid receipt with the given simple regret."""
    return OracleReceipt(
        policy="candidate",
        family="delayed_commitments",
        seed=200_000,
        selected_set=("L",),
        oracle_top_k_sets=(("L",),),
        recall_at_k=1.0,
        simple_regret_set=regret,
        interaction_recovery={
            "complementary_recovered": (),
            "dangerous_avoided": (),
            "num_complementary_recovered": 0,
            "num_dangerous_avoided": 0,
        },
        planted_bundles_recovered={
            "useful_singletons_recovered": 1,
            "complementary_pairs_recovered": 0,
            "contradictory_pairs_avoided": 0,
            "dangerous_conjunctions_avoided": 0,
            "isolation_distractors_avoided": 0,
        },
    )


# --------------------------------------------------------------------------- #
# 6. IntegrityAudit refuses policy access to the oracle path.                  #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "callable_",
    [
        compute_oracle_topk_sets,
        enumerate_set_deltas,
        compute_set_delta,
        OracleSealedEnvironment.evaluate_set,
    ],
    ids=[
        "compute_oracle_topk_sets",
        "enumerate_set_deltas",
        "compute_set_delta",
        "OracleSealedEnvironment.evaluate_set",
    ],
)
def test_integrity_audit_refuses_policy_access_to_oracle_path(callable_) -> None:
    """Every oracle-path entry point dereferences a sealed attribute.

    :meth:`IntegrityAudit.assert_clean` walks the callable's source
    looking for :class:`ast.Attribute` nodes whose ``attr`` is in
    :attr:`IntegrityAudit.FORBIDDEN_ATTRS` (``role``, ``utility``,
    ``_answer_key``). Each oracle-path function explicitly touches
    ``episode._answer_key`` (or ``self._episode._answer_key`` /
    ``episode.utility`` / ``episode.role``) so a policy callable that
    imports or references the function propagates the sealed attribute
    reference and fails the audit.
    """
    with pytest.raises(LeakageError):
        IntegrityAudit.assert_clean(callable_)


def test_compute_oracle_topk_sets_refuses_episode_context() -> None:
    """Passing the policy-visible ``EpisodeContext`` raises ``LeakageError``."""
    episode = _make_toy_episode(
        role_map={"L": "role_load_bearing", "A": "role_distractor"},
        utility_map={"L": 0.5, "A": 0.1},
        answer_key=("L",),
        budget=2,
    )
    env = SealedEnvironment(episode, mode="confirmatory")
    context = env.observe(seed=episode.seed)
    assert isinstance(context, EpisodeContext)
    with pytest.raises(LeakageError):
        compute_oracle_topk_sets(context, budget=2)  # ty: ignore[invalid-argument-type]  # noqa


# --------------------------------------------------------------------------- #
# Additional consistency checks (do not count toward the six-test target).     #
# --------------------------------------------------------------------------- #


def test_build_oracle_receipt_composes_metrics_end_to_end() -> None:
    """``build_oracle_receipt`` fills in every field with self-consistent metrics."""
    episode = _make_toy_episode(
        role_map={
            "L": "role_load_bearing",
            "A": "role_distractor",
            "P1": "complementary_pair_member",
            "P2": "complementary_pair_member",
        },
        utility_map={"L": 0.5, "A": 0.1, "P1": 0.05, "P2": 0.05},
        answer_key=("L",),
        budget=2,
    )
    enumeration = enumerate_set_deltas(episode, budget=2)
    planted = PlantedBundles(
        useful_singletons=("L",),
        complementary_pairs=(("P1", "P2"),),
    )
    receipt = build_oracle_receipt(
        policy="candidate",
        family="delayed_commitments",
        seed=episode.seed,
        selected_set=("P1", "P2"),
        enumeration=enumeration,
        planted_bundles=planted,
    )
    assert receipt.recall_at_k >= 0.0
    assert receipt.simple_regret_set >= 0.0
    assert receipt.interaction_recovery["num_complementary_recovered"] == 1
    # Selected {P1, P2} doesn't include L, so useful_singleton recovery is 0.
    assert receipt.planted_bundles_recovered["useful_singletons_recovered"] == 0


def test_max_cardinality_guard_refuses_oversized_candidate_set() -> None:
    """A candidate set larger than the enumeration ceiling is refused."""
    n = MAX_ORACLE_ENUMERATION_CARDINALITY + 1
    candidates = tuple(f"n{i}" for i in range(n))
    episode = _make_toy_episode(
        role_map={c: "role_neutral" for c in candidates},
        utility_map={c: 0.0 for c in candidates},
        answer_key=("n0",),
        candidate_nodes=candidates,
        budget=2,
    )
    with pytest.raises(ValueError, match="oracle enumeration refuses"):
        enumerate_set_deltas(episode, budget=2)


def test_planted_bundles_from_manifest_normalizes_family_schemas() -> None:
    """Duck-typed conversion handles both wave 1b manifest schemas."""

    class _DcMfManifest:
        useful_singleton = "L"
        complementary_pair = ("P1", "P2")
        contradictory_pair = None
        dangerous_conjunction = None
        isolation_distractor = None

    dcmf = planted_bundles_from_manifest(_DcMfManifest())
    assert dcmf.useful_singletons == ("L",)
    assert dcmf.complementary_pairs == (("P1", "P2"),)
    assert dcmf.contradictory_pairs == ()
    assert dcmf.dangerous_conjunctions == ()
    assert dcmf.isolation_distractors == ()

    class _RcManifest:
        load_bearing_singleton = "L"
        complementary_pair = ("P1", "P2")
        contradictory_pair = ("K1", "K2")
        dangerous_conjunction = ("D1", "D2", "D3")
        isolation_distractor = "I"

    rc = planted_bundles_from_manifest(_RcManifest())
    assert rc.useful_singletons == ("L",)
    assert rc.complementary_pairs == (("P1", "P2"),)
    assert rc.contradictory_pairs == (("K1", "K2"),)
    assert rc.dangerous_conjunctions == (("D1", "D2", "D3"),)
    assert rc.isolation_distractors == ("I",)
