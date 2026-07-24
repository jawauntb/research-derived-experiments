"""Tests for the Wave 1b oracle-withheld geometry (CEILING-ONLY).

The oracle geometry is a diagnostic ceiling for the Wave 1b crossed
factorial (``PREREGISTRATION.md`` §5). It reads the sealed
:attr:`EpisodeSpec._answer_key`, builds a graph whose PPR from context
lands overwhelming mass on the answer nodes, and is **refused by the
promotion harness**. The tests here pin that ceiling-only contract
plus the graph-shape properties the crossed runner relies on.

Six invariants match the Wave 1b build brief:

1. **Determinism.** ``build_oracle_geometry(family, seed)`` is a pure
   function of its inputs. Same inputs, byte-identical
   :class:`WeightedGraph`. Different seeds produce different graphs.

2. **Family coverage.** The three Wave 1b v2 families
   (``delayed_commitments``, ``maintenance_fault``,
   ``resource_constrained``) are accepted; any other family name
   raises ``ValueError``.

3. **Oracle structure.** Every context-node to every answer-node
   edge exists with the frozen :data:`ORACLE_EDGE_WEIGHT`. A
   background chain over non-answer candidates keeps the graph
   connected. No oracle edge is missing on any accepted family.

4. **Ceiling refusal.** :func:`build_oracle_geometry` is flagged with
   the :data:`CEILING_MARKER`, and both the module-local
   :func:`promotion_admit_geometry` and the Wave 0
   :func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.promotion_admit`
   refuse it with :class:`PromotionRefused`.

5. **Anti-leakage (deliberate).** The function's source
   dereferences :attr:`EpisodeSpec._answer_key`, so
   :meth:`IntegrityAudit.assert_clean` **fails** on it. This test
   pins the failure — a policy path is not allowed to call an
   oracle-geometry builder.

6. **PPR sanity.** The oracle geometry, when handed to
   :func:`personalized_pagerank` with a restart concentrated on the
   context nodes, places the majority of the resulting mass on the
   answer nodes. This is what makes the geometry a *ceiling*.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    personalized_pagerank,
)
from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    CEILING_MARKER,
    PromotionRefused,
    promotion_admit,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    IntegrityAudit,
    LeakageError,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.families import (
    delayed_commitments_v2,
    maintenance_fault_v2,
    resource_constrained_v2,
)
from experiments.concern_gated_retrieval_e2.wave1b.oracle_geometry import (
    BACKGROUND_EDGE_WEIGHT,
    ORACLE_EDGE_WEIGHT,
    SUPPORTED_FAMILIES,
    build_oracle_geometry,
    promotion_admit_geometry,
)


# --------------------------------------------------------------------------- #
# Fixtures — family-specific confirmatory seeds                                #
# --------------------------------------------------------------------------- #


#: One valid confirmatory seed per family. RC2's confirmatory range
#: starts at 200_600 (300 templates), while DC2 and MF2 use the shared
#: [200_000, 201_999] window — so the fixture emits a family-appropriate
#: seed rather than a single global constant.
_FAMILY_SEEDS: dict[str, int] = {
    "delayed_commitments": 200_000,
    "maintenance_fault": 200_000,
    "resource_constrained": 200_600,
}


def _all_families() -> list[str]:
    return sorted(SUPPORTED_FAMILIES)


# --------------------------------------------------------------------------- #
# (1) Determinism                                                              #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", _all_families())
def test_oracle_geometry_is_deterministic_given_family_and_seed(family: str) -> None:
    seed = _FAMILY_SEEDS[family]
    left = build_oracle_geometry(family, seed=seed)
    right = build_oracle_geometry(family, seed=seed)

    assert left.nodes == right.nodes
    assert left.adjacency == right.adjacency


@pytest.mark.parametrize("family", ["delayed_commitments", "maintenance_fault"])
def test_oracle_geometry_differs_across_seeds(family: str) -> None:
    a = build_oracle_geometry(family, seed=200_000)
    b = build_oracle_geometry(family, seed=200_001)

    # Node ids embed the seed, so the whole graph namespace differs;
    # equivalently, the two adjacency dicts share no keys.
    assert set(a.adjacency.keys()).isdisjoint(set(b.adjacency.keys()))


# --------------------------------------------------------------------------- #
# (2) Family coverage                                                          #
# --------------------------------------------------------------------------- #


def test_supported_families_matches_wave1b_v2_registry() -> None:
    assert SUPPORTED_FAMILIES == {
        "delayed_commitments",
        "maintenance_fault",
        "resource_constrained",
    }


def test_oracle_geometry_rejects_unknown_family() -> None:
    with pytest.raises(ValueError):
        build_oracle_geometry("answer_key", seed=200_000)


def test_oracle_geometry_rejects_out_of_range_seed() -> None:
    with pytest.raises(ValueError):
        build_oracle_geometry("delayed_commitments", seed=150_000)


def test_oracle_geometry_rejects_non_int_seed() -> None:
    with pytest.raises(TypeError):
        build_oracle_geometry("delayed_commitments", seed=200_000.5)  # ty: ignore[invalid-argument-type]  # noqa


def test_oracle_geometry_rejects_boolean_seed() -> None:
    with pytest.raises(TypeError):
        build_oracle_geometry("delayed_commitments", seed=True)  # noqa


def test_oracle_geometry_rejects_non_positive_weights() -> None:
    with pytest.raises(ValueError):
        build_oracle_geometry(
            "delayed_commitments", seed=200_000, oracle_weight=0.0
        )
    with pytest.raises(ValueError):
        build_oracle_geometry(
            "delayed_commitments", seed=200_000, background_weight=0.0
        )


# --------------------------------------------------------------------------- #
# (3) Oracle structure                                                          #
# --------------------------------------------------------------------------- #


def _generate_episode(family: str, seed: int):
    """Return the sealed EpisodeSpec used by the oracle-geometry builder."""
    if family == "delayed_commitments":
        return delayed_commitments_v2.generate_episode(
            seed=seed, bucket=TemplateBucket.CONFIRMATION
        )
    if family == "maintenance_fault":
        return maintenance_fault_v2.generate_episode(
            seed=seed, bucket=TemplateBucket.CONFIRMATION
        )
    if family == "resource_constrained":
        return resource_constrained_v2.generate_episode(
            seed=seed, bucket=TemplateBucket.CONFIRMATION
        )
    raise AssertionError(f"unknown family {family!r} in test helper")


@pytest.mark.parametrize("family", _all_families())
def test_oracle_geometry_wires_context_to_every_answer(family: str) -> None:
    seed = _FAMILY_SEEDS[family]
    episode = _generate_episode(family, seed)
    graph = build_oracle_geometry(family, seed=seed)

    context_nodes = tuple(episode.context_nodes)
    answer_key = tuple(episode._answer_key)

    for ctx in context_nodes:
        for ans in answer_key:
            if ctx == ans:
                continue
            assert ctx in graph.adjacency, f"context node missing: {ctx!r}"
            assert ans in graph.adjacency[ctx], (
                f"oracle edge missing: {ctx!r} -> {ans!r}"
            )
            # The oracle edge weight is applied on top of any background
            # weight that later bridges the two clusters, so the recorded
            # weight is at least ``ORACLE_EDGE_WEIGHT``.
            assert graph.adjacency[ctx][ans] >= ORACLE_EDGE_WEIGHT


@pytest.mark.parametrize("family", _all_families())
def test_oracle_geometry_node_set_is_context_union_candidates(
    family: str,
) -> None:
    seed = _FAMILY_SEEDS[family]
    episode = _generate_episode(family, seed)
    graph = build_oracle_geometry(family, seed=seed)

    expected_nodes = set(episode.context_nodes) | set(episode.candidate_nodes)
    assert set(graph.nodes) == expected_nodes


@pytest.mark.parametrize("family", _all_families())
def test_oracle_geometry_carries_background_chain(family: str) -> None:
    seed = _FAMILY_SEEDS[family]
    episode = _generate_episode(family, seed)
    graph = build_oracle_geometry(family, seed=seed)

    non_answer_candidates = [
        c for c in episode.candidate_nodes if c not in episode._answer_key
    ]
    if len(non_answer_candidates) < 2:
        pytest.skip("family emits fewer than two non-answer candidates")

    # Consecutive non-answer candidates are chained with background
    # weight so the graph stays connected outside the oracle cluster.
    for left, right in zip(non_answer_candidates, non_answer_candidates[1:]):
        assert right in graph.adjacency[left], (
            f"background chain missing: {left!r} -> {right!r}"
        )


# --------------------------------------------------------------------------- #
# (4) Ceiling refusal                                                          #
# --------------------------------------------------------------------------- #


def test_build_oracle_geometry_is_flagged_ceiling_only() -> None:
    assert getattr(build_oracle_geometry, CEILING_MARKER, False) is True


def test_promotion_admit_geometry_refuses_oracle_geometry() -> None:
    with pytest.raises(PromotionRefused) as excinfo:
        promotion_admit_geometry(build_oracle_geometry)
    # The message shape is stable so downstream receipts can regex on it.
    assert "CEILING-ONLY" in str(excinfo.value)


def test_wave0_promotion_admit_also_refuses_oracle_geometry() -> None:
    # The same Wave 0 baseline-side harness refuses the oracle
    # geometry, because both harnesses key off the same
    # :data:`CEILING_MARKER` attribute.
    with pytest.raises(PromotionRefused):
        promotion_admit(build_oracle_geometry)


def test_promotion_admit_geometry_admits_a_non_ceiling_geometry() -> None:
    # A geometry builder without the ceiling marker must be admitted
    # unchanged, so the harness does not accidentally block promotable
    # geometry (the LEARNED / FREQ_MATCHED_RANDOM axis levels).
    def _fake_learned_geometry(seed: int) -> WeightedGraph:
        return WeightedGraph.from_edges(("a", "b"), (("a", "b", 1.0),))

    admitted = promotion_admit_geometry(_fake_learned_geometry)
    assert admitted is _fake_learned_geometry


# --------------------------------------------------------------------------- #
# (5) Anti-leakage — deliberate audit failure                                  #
# --------------------------------------------------------------------------- #


def test_build_oracle_geometry_fails_integrity_audit_by_design() -> None:
    # The oracle geometry dereferences _answer_key, which is in
    # IntegrityAudit.FORBIDDEN_ATTRS. That the audit fires here is
    # the *feature*: any policy that ever imports this builder would
    # inherit the flagged reference at its call site.
    with pytest.raises(LeakageError) as excinfo:
        IntegrityAudit.assert_clean(build_oracle_geometry)
    assert "_answer_key" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# (6) PPR sanity — oracle really is a ceiling                                  #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", _all_families())
def test_oracle_geometry_concentrates_ppr_mass_on_answer(family: str) -> None:
    seed = _FAMILY_SEEDS[family]
    episode = _generate_episode(family, seed)
    graph = build_oracle_geometry(family, seed=seed)

    # Restart is uniform over the context nodes — the natural PPR
    # seed the crossed runner uses.
    context_nodes = tuple(episode.context_nodes)
    restart = {node: 1.0 / len(context_nodes) for node in context_nodes}

    result = personalized_pagerank(
        graph, restart, tolerance=1e-12, max_iterations=1000
    )
    assert result.l1_residual < 1e-9

    answer_mass = sum(result.scores.get(node, 0.0) for node in episode._answer_key)
    # The oracle geometry funnels the restart mass toward the answer
    # nodes. With one answer node and (say) 12 non-answer candidates
    # plus a strong 5.0-vs-0.01 weight ratio, the answer takes the
    # dominant share. A conservative floor of 0.20 comfortably clears
    # the ceiling claim while leaving slack for the sparse background
    # chain's diffusion; a tighter fit would over-constrain the
    # geometry across the three families.
    assert answer_mass > 0.20, (
        f"oracle geometry did not concentrate PPR mass on answer for "
        f"family {family!r}: answer_mass={answer_mass:.4f}"
    )


# --------------------------------------------------------------------------- #
# Constants                                                                    #
# --------------------------------------------------------------------------- #


def test_module_constants_are_positive() -> None:
    assert ORACLE_EDGE_WEIGHT > 0
    assert BACKGROUND_EDGE_WEIGHT > 0
    # The oracle weight must be substantially above the background so
    # PPR mass concentration is real, not marginal.
    assert ORACLE_EDGE_WEIGHT > BACKGROUND_EDGE_WEIGHT * 100
