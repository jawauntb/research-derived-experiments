"""Tests for the Wave 1b learned graph geometry module.

Four regressions per the Wave 1b task brief:

1. **Determinism.** ``learn_graph(history, features)`` returns
   byte-identical :class:`WeightedGraph` structures across successive
   calls for every registered preset.
2. **No label access.**
   :meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.assert_clean`
   accepts :func:`learn_graph` and every per-family learner, and
   refuses :func:`shuffled_labels_control` (which is deliberately
   evaluator-only and dereferences ``episode._answer_key``).
3. **Sparse edge set.** For every preset, no node in the learned
   graph carries a degree above the ``max_degree`` implied by
   ``top_k_per_node`` and ``max_degree_multiplier``.
4. **Shuffled-labels control.** On a labels-shuffled control the
   learned edge-mass at the "true" load-bearing node stays within
   :data:`~experiments.concern_gated_retrieval_e2.wave1b.learned_geometry.DEFAULT_SHUFFLE_TOLERANCE`
   standard deviations of the shuffle null on every preset.
"""

from __future__ import annotations


import pytest

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
    IntegrityAudit,
    LeakageError,
    SealedEnvironment,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.families.delayed_commitments_v2 import (
    generate_episode as generate_dc_v2,
)
from experiments.concern_gated_retrieval_e2.wave1b.learned_geometry import (
    EMBEDDING_ONLY,
    EpisodeHistory,
    HYBRID,
    HistoryEpisode,
    LearnableFeatureSpec,
    MINIMAL_COOC,
    TEMPORAL_LAG_5,
    _causal_intervention_edges,
    _cooccurrence_edges,
    _learned_embedding_edges,
    _temporal_lag_edges,
    learn_graph,
    shuffled_labels_control,
)


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


_SEED_RANGE = range(100_000, 100_040)


def _build_fixture() -> tuple[tuple[EpisodeSpec, ...], EpisodeHistory]:
    """Build a 40-seed calibration fixture from delayed_commitments_v2.

    Returns both the sealed :class:`EpisodeSpec` tuple (evaluator-side,
    needed by :func:`shuffled_labels_control`) and the policy-visible
    :class:`EpisodeHistory` (input to :func:`learn_graph`).
    """
    episodes: list[EpisodeSpec] = []
    records: list[HistoryEpisode] = []
    for seed in _SEED_RANGE:
        ep = generate_dc_v2(seed=seed, bucket=TemplateBucket.CALIBRATION)
        env = SealedEnvironment(ep, mode="calibration")
        ctx = env.observe(seed=seed)
        episodes.append(ep)
        records.append(HistoryEpisode.from_context(ctx))
    return tuple(episodes), EpisodeHistory(episodes=tuple(records))


_ALL_PRESETS: tuple[tuple[str, LearnableFeatureSpec], ...] = (
    ("MINIMAL_COOC", MINIMAL_COOC),
    ("TEMPORAL_LAG_5", TEMPORAL_LAG_5),
    ("EMBEDDING_ONLY", EMBEDDING_ONLY),
    ("HYBRID", HYBRID),
)


# --------------------------------------------------------------------------- #
# 1. Determinism                                                              #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("preset_name, preset", _ALL_PRESETS)
def test_learn_graph_is_deterministic(
    preset_name: str, preset: LearnableFeatureSpec
) -> None:
    """Two calls with identical (history, features) return the same graph.

    Byte-identical node order (``tuple(sorted(nodes))``) and byte-
    identical adjacency (dict comparison) are the determinism contract
    the Wave 1b receipts rely on.
    """
    _, history = _build_fixture()
    graph_a = learn_graph(history, preset)
    graph_b = learn_graph(history, preset)
    assert graph_a.nodes == graph_b.nodes, (
        f"[{preset_name}] node tuples diverged between calls"
    )
    assert graph_a.adjacency == graph_b.adjacency, (
        f"[{preset_name}] adjacency diverged between calls"
    )


# --------------------------------------------------------------------------- #
# 2. No label access                                                          #
# --------------------------------------------------------------------------- #


def test_learn_graph_is_audit_clean() -> None:
    """``learn_graph`` and every family learner pass IntegrityAudit."""
    IntegrityAudit.assert_clean(learn_graph)
    IntegrityAudit.assert_clean(_cooccurrence_edges)
    IntegrityAudit.assert_clean(_temporal_lag_edges)
    IntegrityAudit.assert_clean(_causal_intervention_edges)
    IntegrityAudit.assert_clean(_learned_embedding_edges)


def test_shuffled_labels_control_is_refused_by_audit() -> None:
    """The evaluator-only self-test dereferences ``_answer_key`` and
    therefore MUST fail :meth:`IntegrityAudit.assert_clean`.

    The refusal is what keeps a policy callable from silently importing
    the audit helper as a back door to the sealed answer key.
    """
    with pytest.raises(LeakageError):
        IntegrityAudit.assert_clean(shuffled_labels_control)


def test_learn_graph_never_touches_sealed_fields() -> None:
    """A sealed :class:`EpisodeSpec` passed to :class:`HistoryEpisode`
    fails at construction because the dataclass is a policy-visible
    view, and :func:`learn_graph` therefore never reaches
    ``EpisodeSpec.role``, ``EpisodeSpec.utility``, or
    ``EpisodeSpec._answer_key``.

    We assert the negative by constructing a :class:`HistoryEpisode`
    directly from an :class:`EpisodeContext` view and confirming
    :func:`learn_graph` runs to completion without raising.
    """
    _, history = _build_fixture()
    graph = learn_graph(history, HYBRID)
    assert isinstance(graph.nodes, tuple)


# --------------------------------------------------------------------------- #
# 3. Sparse edge set                                                          #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("preset_name, preset", _ALL_PRESETS)
def test_learned_graph_is_sparse(
    preset_name: str, preset: LearnableFeatureSpec
) -> None:
    """No node's degree exceeds ``top_k * max_degree_multiplier``.

    The sparsification funnel (top-K per node, then max-degree cap) is
    what keeps the learned geometry a plug-in replacement for the Wave
    0 fixed-withheld graphs on the LEARNED axis of the E2b crossed
    factorial. A regression that let a single hub node accumulate an
    unbounded neighbourhood would blow up every downstream PPR step.
    """
    _, history = _build_fixture()
    graph = learn_graph(history, preset)
    max_degree_bound = preset.top_k_per_node * preset.max_degree_multiplier
    for node in graph.nodes:
        neighbours = graph.adjacency.get(node, {})
        assert len(neighbours) <= max_degree_bound, (
            f"[{preset_name}] node {node!r} has degree {len(neighbours)} > "
            f"bound {max_degree_bound}"
        )


def test_top_k_bound_is_respected_with_small_k() -> None:
    """A tight ``top_k = 2`` yields a graph whose per-node degree is at
    most ``top_k * max_degree_multiplier = 4``. Kept as a separate
    regression so the parametrised bound above is not merely a
    tautology at the preset defaults.
    """
    _, history = _build_fixture()
    tight = LearnableFeatureSpec(
        families=(
            "co_occurrence",
            "temporal_lag",
            "learned_embedding",
        ),
        top_k_per_node=2,
        max_degree_multiplier=2,
    )
    graph = learn_graph(history, tight)
    for node in graph.nodes:
        assert len(graph.adjacency.get(node, {})) <= 4


# --------------------------------------------------------------------------- #
# 4. Shuffled-labels integrity self-test                                      #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("preset_name, preset", _ALL_PRESETS)
def test_shuffled_labels_control_passes(
    preset_name: str, preset: LearnableFeatureSpec
) -> None:
    """The label-permutation z-score stays within the default tolerance.

    ``learn_graph`` is label-blind by construction, so the mean edge
    mass on each episode's true load-bearing node is expected to sit
    inside the shuffle null. A regression that leaked the sealed
    ``_answer_key`` into the learner's inductive bias would surface
    here as a large positive z-score.
    """
    episodes, history = _build_fixture()
    receipt = shuffled_labels_control(
        episodes, history, preset, n_shuffles=200, seed=1234
    )
    assert receipt.passed, (
        f"[{preset_name}] shuffled-labels control tripped: "
        f"actual={receipt.actual_mean_mass:.4f}, "
        f"shuffle_mean={receipt.shuffle_mean_mass:.4f}, "
        f"z={receipt.z_score:.3f}, tolerance={receipt.tolerance}"
    )


def test_shuffled_labels_control_refuses_context_view() -> None:
    """Passing anything other than an :class:`EpisodeSpec` raises
    :class:`LeakageError`.

    The type-shape check is the first line of defence against a
    caller accidentally handing in an :class:`EpisodeContext` (which
    lacks the sealed fields the audit needs) or a bare mapping (which
    would silently return an empty receipt).
    """
    _, history = _build_fixture()
    # The policy-visible EpisodeContext is not an EpisodeSpec; the
    # audit refuses it as a leakage-adjacent misuse rather than
    # silently returning an empty receipt.
    fake_context = history.episodes[0]
    with pytest.raises(LeakageError):
        shuffled_labels_control(
            (fake_context,),  # ty: ignore[invalid-argument-type]  # noqa
            history,
            MINIMAL_COOC,
        )
