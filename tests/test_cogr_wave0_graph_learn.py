"""Tests for the Wave 0 fixed-withheld-geometry / graph-learn stubs.

Covers the three invariants named by the Wave 0 build brief:

1. determinism given a seed;
2. concern warp preserves node support and edge sign; and
3. personalized PageRank fixed-point residual < 1e-9 on a small graph.

These tests do not consult any evaluator-only field. They exercise only
the policy-visible surface of ``experiments.concern_gated_retrieval_e2
.wave0.graph_learn`` and the pilot's numerical primitives.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    personalized_pagerank,
)
from experiments.concern_gated_retrieval_e2.wave0.graph_learn import (
    DEFAULT_WARP_STRENGTH,
    FAMILY_NAMES,
    MIN_GRAPH_SIZE,
    apply_concern_warp,
    build_withheld_graph,
    rarity_scores,
)


# --- determinism -----------------------------------------------------------


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_build_withheld_graph_is_deterministic_given_seed(family: str) -> None:
    left = build_withheld_graph(seed=100042, size=16, family=family)
    right = build_withheld_graph(seed=100042, size=16, family=family)

    assert left.nodes == right.nodes
    assert left.adjacency == right.adjacency


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_build_withheld_graph_differs_across_seeds(family: str) -> None:
    a = build_withheld_graph(seed=100000, size=16, family=family)
    b = build_withheld_graph(seed=100001, size=16, family=family)

    # Node names carry the seed, so node sets differ; the adjacency dict
    # is also different because the seeded stream diverges. We assert on
    # the adjacency key set to make the test intent explicit.
    assert set(a.adjacency.keys()) != set(b.adjacency.keys())


def test_build_withheld_graph_families_have_disjoint_node_namespaces() -> None:
    seed = 100000
    size = 16
    graphs = {
        family: build_withheld_graph(seed=seed, size=size, family=family)
        for family in FAMILY_NAMES
    }
    node_sets = {family: set(g.nodes) for family, g in graphs.items()}
    families = list(node_sets)
    for i in range(len(families)):
        for j in range(i + 1, len(families)):
            assert node_sets[families[i]].isdisjoint(node_sets[families[j]])


def test_build_withheld_graph_rejects_unknown_family() -> None:
    with pytest.raises(ValueError):
        build_withheld_graph(seed=100000, size=16, family="answer_key")


def test_build_withheld_graph_rejects_below_min_size() -> None:
    with pytest.raises(ValueError):
        build_withheld_graph(
            seed=100000, size=MIN_GRAPH_SIZE - 1, family="delayed_commitments"
        )


def test_build_withheld_graph_rejects_non_int_seed() -> None:
    with pytest.raises(TypeError):
        build_withheld_graph(
            seed=1.0,  # ty: ignore[invalid-argument-type]  # noqa
            size=16,
            family="delayed_commitments",
        )


# --- concern warp preserves support ----------------------------------------


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_concern_warp_preserves_node_support(family: str) -> None:
    graph = build_withheld_graph(seed=100000, size=12, family=family)

    # Adversarially misspecified prior in miniature: overweight two
    # nodes, suppress one, leave the rest at uniform baseline (0.0). The
    # test does not read any role label; it uses positional indices only.
    concern = {node: 0.0 for node in graph.nodes}
    concern[graph.nodes[0]] = 1.0
    concern[graph.nodes[1]] = 1.0
    concern[graph.nodes[2]] = 0.05

    warped = apply_concern_warp(graph, concern)

    assert warped.nodes == graph.nodes
    for node in graph.nodes:
        assert node in warped.adjacency
    for node, neighbors in graph.adjacency.items():
        for neighbor, weight in neighbors.items():
            if weight > 0:
                assert warped.adjacency[node][neighbor] > 0


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_concern_warp_with_zero_prior_is_identity(family: str) -> None:
    graph = build_withheld_graph(seed=100003, size=12, family=family)
    warped = apply_concern_warp(graph, {node: 0.0 for node in graph.nodes})

    assert warped.nodes == graph.nodes
    for node, neighbors in graph.adjacency.items():
        for neighbor, weight in neighbors.items():
            assert warped.adjacency[node][neighbor] == pytest.approx(weight)


def test_concern_warp_rejects_unknown_nodes() -> None:
    graph = build_withheld_graph(seed=100000, size=8, family="maintenance_fault")

    with pytest.raises(ValueError):
        apply_concern_warp(graph, {"stranger": 1.0})


def test_concern_warp_rejects_non_mapping() -> None:
    graph = build_withheld_graph(seed=100000, size=8, family="delayed_commitments")

    with pytest.raises(TypeError):
        apply_concern_warp(graph, ["not", "a", "mapping"])  # ty: ignore[invalid-argument-type]  # noqa


def test_default_warp_strength_is_documented_positive_value() -> None:
    assert DEFAULT_WARP_STRENGTH > 0


# --- PPR fixed-point residual ---------------------------------------------


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_ppr_fixed_point_residual_below_tolerance(family: str) -> None:
    graph = build_withheld_graph(seed=100000, size=12, family=family)
    restart = {graph.nodes[0]: 1.0}

    result = personalized_pagerank(
        graph, restart, tolerance=1e-14, max_iterations=1000
    )

    assert result.l1_residual < 1e-9
    assert sum(result.scores.values()) == pytest.approx(1.0, abs=1e-10)


def test_ppr_fixed_point_residual_survives_concern_warp() -> None:
    graph = build_withheld_graph(seed=100000, size=12, family="delayed_commitments")
    concern = {node: 0.0 for node in graph.nodes}
    concern[graph.nodes[0]] = 1.0
    concern[graph.nodes[3]] = 0.05
    warped = apply_concern_warp(graph, concern)

    result = personalized_pagerank(
        warped,
        {warped.nodes[0]: 1.0},
        tolerance=1e-14,
        max_iterations=1000,
    )

    assert result.l1_residual < 1e-9


# --- rarity aggregator ----------------------------------------------------


def test_rarity_scores_is_deterministic_over_batch_order_and_form() -> None:
    seeds = [100000, 100001, 100002, 100003]
    graphs = [
        build_withheld_graph(seed=s, size=10, family="delayed_commitments")
        for s in seeds
    ]

    from_list = rarity_scores(graphs)
    from_iter = rarity_scores(iter(graphs))

    assert from_list == from_iter


def test_rarity_scores_puts_shared_nodes_below_singletons() -> None:
    shared = build_withheld_graph(seed=100000, size=10, family="maintenance_fault")
    unique = build_withheld_graph(seed=100050, size=10, family="maintenance_fault")

    scores = rarity_scores([shared, shared, shared, unique])

    shared_nodes = set(shared.nodes) - set(unique.nodes)
    unique_nodes = set(unique.nodes) - set(shared.nodes)
    assert shared_nodes and unique_nodes
    for shared_node in shared_nodes:
        for unique_node in unique_nodes:
            assert scores[shared_node] < scores[unique_node]


def test_rarity_scores_empty_batch_returns_empty_dict() -> None:
    assert rarity_scores([]) == {}


def test_rarity_scores_rejects_non_graph_element() -> None:
    with pytest.raises(TypeError):
        rarity_scores([WeightedGraph.from_edges(("a", "b"), (("a", "b", 1.0),)), 42])  # ty: ignore[invalid-argument-type]  # noqa
