"""Tests for the Wave 1b statistical leakage-audit module.

Three regressions per the Wave 1b task brief for G9 (`leakage_audit`):

1. **Passes on a genuinely leakage-free feature set.** The wave1b
   ``learn_graph(history, MINIMAL_COOC)`` learner reads only the
   policy-visible ``EpisodeContext`` fields and is byte-blind to
   ``EpisodeSpec._answer_key``. Both audits must return
   :attr:`AuditVerdict.passed` = ``True`` on the delayed_commitments_v2
   calibration fixture, and calling :func:`raise_if_leaked` on the
   returned verdict must NOT raise.

2. **Fires on a planted-leak feature set.** A deliberately leaky
   ``learn_fn`` — one that reads a closure over the sealed
   ``_answer_key`` and emits an edge from every visible node to that
   episode's true load-bearing node — inflates the top-K PPR hit rate
   at the load-bearing node far above the permutation null. The audit
   must return :attr:`AuditVerdict.passed` = ``False`` (both label
   permutation and randomized generator) and :func:`raise_if_leaked`
   must raise :class:`LeakageError`.

3. **Deterministic.** Two calls to each audit with identical inputs
   (same seeds, same fixture, same learn_fn, same audit_seed / seed)
   return byte-identical :class:`AuditVerdict` values. Byte-identical
   means every field on the frozen dataclass compares equal.

These three tests together pin the audit's specificity (it doesn't
false-positive on a real label-blind learner), sensitivity (it
detects a real leak), and reproducibility (it can be replayed in
PROVENANCE receipts).
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval.graph import WeightedGraph
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.families.delayed_commitments_v2 import (
    generate_episode as generate_dc_v2,
)
from experiments.concern_gated_retrieval_e2.wave1b.leakage_audit import (
    AUDIT_LABEL_PERMUTATION,
    AUDIT_RANDOMIZED_GENERATOR,
    AuditVerdict,
    DEFAULT_TOLERANCE,
    LeakageError,
    audit_label_permutation,
    audit_randomized_generator,
    raise_if_leaked,
)
from experiments.concern_gated_retrieval_e2.wave1b.learned_geometry import (
    EpisodeHistory,
    MINIMAL_COOC,
    learn_graph,
)


# --------------------------------------------------------------------------- #
# Fixture builders                                                            #
# --------------------------------------------------------------------------- #


#: Calibration seed range small enough that both audits finish quickly
#: yet large enough that the null distribution has meaningful spread
#: (24 episodes -> permutation hit-rate resolution = 1/24 ≈ 0.042).
#: The 200-offset used by :func:`audit_randomized_generator`'s default
#: ``generator_offsets`` keeps the shifted seeds inside the wave0
#: calibration window ``[100_000, 100_999]``.
_SEED_RANGE = tuple(range(100_000, 100_024))


def _fixture_episodes() -> tuple[EpisodeSpec, ...]:
    """Sealed calibration episodes from delayed_commitments_v2."""
    return tuple(
        generate_dc_v2(seed=seed, bucket=TemplateBucket.CALIBRATION)
        for seed in _SEED_RANGE
    )


def _clean_learn_fn(history: EpisodeHistory) -> WeightedGraph:
    """Label-blind reference learner used by the "no leak" test.

    Uses the wave1b co-occurrence-only preset because it is the cheapest
    audit-clean learner in the suite; a preset with more feature
    families would also pass but takes longer.
    """
    return learn_graph(history, MINIMAL_COOC)


def _make_leaky_learn_fn(episodes: tuple[EpisodeSpec, ...]):
    """Return a learner that has "leaked" — its edges route mass to answers.

    The closure captures the sealed load-bearing node for every episode
    id (an evaluator-side operation done outside the audit). The
    returned ``learn_fn`` then reads the visible EpisodeHistory the
    audit hands it, and for every visible episode plants heavyweight
    edges from every context node to the episode's cheat-registered
    load-bearing node. A statistically clean learner would never do
    this; the audit exists precisely to catch it.
    """
    answer_by_id = {
        ep.episode_id: ep._answer_key[0]
        for ep in episodes
        if ep._answer_key
    }
    fake_weight = 20.0

    def leaky_learn(history: EpisodeHistory) -> WeightedGraph:
        seen_nodes: set[str] = set()
        edges: list[tuple[str, str, float]] = []
        for hist_ep in history.episodes:
            lb = answer_by_id.get(hist_ep.episode_id)
            if lb is None:
                continue
            seen_nodes.add(lb)
            for ctx in hist_ep.context_nodes:
                seen_nodes.add(ctx)
                if ctx == lb:
                    continue
                edges.append((ctx, lb, fake_weight))
            # Also touch each candidate so the graph node set matches
            # the wave1b visible universe (co-occurrence pattern).
            for cand in hist_ep.candidate_nodes:
                seen_nodes.add(cand)
        return WeightedGraph.from_edges(tuple(sorted(seen_nodes)), tuple(edges))

    return leaky_learn


# --------------------------------------------------------------------------- #
# 1. Passes on a genuinely leakage-free feature set                           #
# --------------------------------------------------------------------------- #


def test_audits_pass_on_leakage_free_learner() -> None:
    """The wave1b MINIMAL_COOC learner is label-blind → both audits pass.

    Because ``learn_graph`` never dereferences a sealed
    :class:`EpisodeSpec` attribute, the label-permutation null and the
    randomized-generator null distributions BOTH contain the observed
    hit rate. ``passed`` must be ``True`` for both audits and
    :func:`raise_if_leaked` must not raise on either verdict.
    """
    episodes = _fixture_episodes()

    label_verdict = audit_label_permutation(
        _clean_learn_fn,
        episodes,
        n_permutations=50,
        seed=17,
    )
    assert isinstance(label_verdict, AuditVerdict)
    assert label_verdict.audit == AUDIT_LABEL_PERMUTATION
    assert label_verdict.tolerance == DEFAULT_TOLERANCE
    assert label_verdict.n_samples > 0, (
        "label-permutation audit produced zero eligible episodes"
    )
    assert label_verdict.passed, (
        "label-permutation audit false-positive on a genuinely "
        f"label-blind learner: {label_verdict.reason}"
    )
    # raise_if_leaked must be a no-op on pass.
    raise_if_leaked(label_verdict)

    generator_verdict = audit_randomized_generator(
        _clean_learn_fn,
        generate_dc_v2,
        _SEED_RANGE,
        n_permutations=50,
        audit_seed=17,
    )
    assert isinstance(generator_verdict, AuditVerdict)
    assert generator_verdict.audit == AUDIT_RANDOMIZED_GENERATOR
    assert generator_verdict.n_samples > 0
    assert generator_verdict.passed, (
        "randomized-generator audit false-positive on a genuinely "
        f"label-blind learner: {generator_verdict.reason}"
    )
    raise_if_leaked(generator_verdict)


# --------------------------------------------------------------------------- #
# 2. Fires on a planted-leak feature set                                      #
# --------------------------------------------------------------------------- #


def test_audits_fire_on_planted_leak_learner() -> None:
    """A learner that routes mass to sealed answers fails both audits.

    The observed top-K PPR hit rate under the leaky learner sits at or
    near 1.0 (every context restart pushes mass down the planted heavy
    edges into the true load-bearing node). Under uniform per-episode
    label permutation the null hit rate is roughly
    ``top_k / |candidate_nodes|`` — well below 1.0. The permutation
    p-value therefore drops well below the ``DEFAULT_TOLERANCE`` bar,
    ``passed`` is ``False``, and :func:`raise_if_leaked` raises
    :class:`LeakageError`.

    The same argument applies to :func:`audit_randomized_generator`:
    the leaky learner has been given the answer keys for BOTH generator
    offsets via its closure, so both regenerated batches trip the
    permutation null.
    """
    episodes = _fixture_episodes()
    # Closure over all seeds we'll audit: base + offset=200 (default
    # generator_offsets in audit_randomized_generator).
    all_seeds = list(_SEED_RANGE) + [s + 200 for s in _SEED_RANGE]
    all_episodes = tuple(
        generate_dc_v2(seed=seed, bucket=TemplateBucket.CALIBRATION)
        for seed in all_seeds
    )
    leaky_fn = _make_leaky_learn_fn(all_episodes)

    label_verdict = audit_label_permutation(
        leaky_fn,
        episodes,
        n_permutations=100,
        seed=17,
    )
    assert isinstance(label_verdict, AuditVerdict)
    assert not label_verdict.passed, (
        "label-permutation audit failed to detect a planted answer-key "
        f"leak; verdict: {label_verdict.reason}"
    )
    # Observed statistic must clearly exceed the null mean.
    assert label_verdict.observed_stat > label_verdict.null_mean, (
        "planted leak did not shift the observed hit rate above the "
        f"permutation null mean: {label_verdict.reason}"
    )
    with pytest.raises(LeakageError):
        raise_if_leaked(label_verdict)

    generator_verdict = audit_randomized_generator(
        leaky_fn,
        generate_dc_v2,
        _SEED_RANGE,
        n_permutations=100,
        audit_seed=17,
    )
    assert isinstance(generator_verdict, AuditVerdict)
    assert not generator_verdict.passed, (
        "randomized-generator audit failed to detect a planted leak; "
        f"verdict: {generator_verdict.reason}"
    )
    with pytest.raises(LeakageError):
        raise_if_leaked(generator_verdict)


# --------------------------------------------------------------------------- #
# 3. Determinism                                                              #
# --------------------------------------------------------------------------- #


def test_audits_are_deterministic() -> None:
    """Two calls with identical inputs return byte-identical verdicts.

    The audit's downstream PROVENANCE row must be replayable to the
    same p-value / z-score across processes. Both audits are pure
    functions of ``(learn_fn, history/seeds, params, seed)``; the RNG
    is seeded by an audit-scoped string.
    """
    episodes = _fixture_episodes()

    verdict_a = audit_label_permutation(
        _clean_learn_fn,
        episodes,
        n_permutations=30,
        seed=42,
    )
    verdict_b = audit_label_permutation(
        _clean_learn_fn,
        episodes,
        n_permutations=30,
        seed=42,
    )
    assert verdict_a == verdict_b, (
        "audit_label_permutation is nondeterministic: "
        f"{verdict_a!r} vs {verdict_b!r}"
    )

    gen_a = audit_randomized_generator(
        _clean_learn_fn,
        generate_dc_v2,
        _SEED_RANGE,
        n_permutations=30,
        audit_seed=42,
    )
    gen_b = audit_randomized_generator(
        _clean_learn_fn,
        generate_dc_v2,
        _SEED_RANGE,
        n_permutations=30,
        audit_seed=42,
    )
    assert gen_a == gen_b, (
        "audit_randomized_generator is nondeterministic: "
        f"{gen_a!r} vs {gen_b!r}"
    )

    # Different seeds must generally NOT produce the same permutation
    # null; this catches a regression where the audit accidentally
    # ignores its seed argument. We only assert the RNG stream differs
    # via the reason string (which embeds the p-value), not the passed
    # bit — a genuinely label-blind learner may pass at both seeds.
    verdict_c = audit_label_permutation(
        _clean_learn_fn,
        episodes,
        n_permutations=30,
        seed=99,
    )
    assert verdict_c.reason != verdict_a.reason or verdict_c.p_value != verdict_a.p_value, (
        "audit_label_permutation returned identical receipt across "
        "different seed inputs; RNG salt likely ignored"
    )
