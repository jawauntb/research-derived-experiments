"""Tests for the Wave 1b frequency-matched random geometry null.

Six invariants matching the Wave 1b build brief for the matched-budget
graph null:

1. **Determinism.** ``build_freq_matched_random_graph(reference, seed)``
   is a pure function of its inputs. Two calls with identical
   ``(reference, seed)`` return byte-identical
   :class:`~experiments.concern_gated_retrieval.graph.WeightedGraph`
   objects. Different seeds produce different edge sets.

2. **Node preservation.** The returned graph has the same node set,
   in the same order, as the reference. The null does not invent or
   drop nodes.

3. **Degree preservation (per-node).** Every node's degree in the
   null exactly matches its degree in the reference — the double
   edge swap invariant. This is the *matched-budget* claim: two
   graphs with identical per-node degree sequence and identical
   total edge count.

4. **Weight preservation (multiset).** The multiset of edge weights
   in the null matches the multiset in the reference — no weight is
   dropped or invented; only weight assignments are permuted.

5. **Structure differs.** The null's canonical edge set is different
   from the reference's canonical edge set on non-trivial reference
   graphs. If this ever equals the reference, the null has failed to
   provide a matched-budget contrast.

6. **Anti-leakage.** :func:`build_freq_matched_random_graph` is
   :meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.assert_clean`
   — it dereferences no sealed :class:`EpisodeSpec` attribute
   (``role``, ``utility``, ``_answer_key``).

The random-geometry null is the L1 gate's "same density, same degree,
random targets" contrast; a candidate mechanism whose gain against
this null vanishes has no representation-contribution claim
(``PREREGISTRATION.md`` §5, §9).
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    personalized_pagerank,
)
from experiments.concern_gated_retrieval_e2.wave0.graph_learn import (
    FAMILY_NAMES,
    build_withheld_graph,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    IntegrityAudit,
    LeakageError,
)
from experiments.concern_gated_retrieval_e2.wave1b.random_geometry import (
    DEFAULT_SWAP_MULTIPLIER,
    MIN_SWAP_ATTEMPTS,
    build_freq_matched_random_graph,
)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _reference_graph(family: str = "delayed_commitments", size: int = 32) -> WeightedGraph:
    """Return a Wave 0 fixed-withheld graph to use as the null's reference."""
    return build_withheld_graph(seed=100_000, size=size, family=family)


def _degree_map(graph: WeightedGraph) -> dict[str, int]:
    return {node: len(graph.adjacency[node]) for node in graph.nodes}


def _weight_multiset(graph: WeightedGraph) -> list[float]:
    """Return the sorted list of undirected edge weights."""
    weights: list[float] = []
    for u in graph.nodes:
        for v, w in graph.adjacency[u].items():
            if u < v:
                weights.append(float(w))
    return sorted(weights)


def _canonical_edge_set(graph: WeightedGraph) -> set[tuple[str, str]]:
    edges: set[tuple[str, str]] = set()
    for u in graph.nodes:
        for v in graph.adjacency[u]:
            if u < v:
                edges.add((u, v))
    return edges


# --------------------------------------------------------------------------- #
# (1) Determinism                                                             #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_freq_matched_random_is_deterministic_given_seed(family: str) -> None:
    ref = _reference_graph(family=family)

    left = build_freq_matched_random_graph(ref, seed=20260724)
    right = build_freq_matched_random_graph(ref, seed=20260724)

    assert left.nodes == right.nodes
    assert left.adjacency == right.adjacency


def test_freq_matched_random_differs_across_seeds() -> None:
    ref = _reference_graph(size=32)

    a = build_freq_matched_random_graph(ref, seed=1)
    b = build_freq_matched_random_graph(ref, seed=2)

    # Same node set and per-node degree, but the actual edge
    # configuration must differ across seeds; the null would be
    # useless otherwise.
    assert a.nodes == b.nodes
    assert _canonical_edge_set(a) != _canonical_edge_set(b)


# --------------------------------------------------------------------------- #
# (2) Node preservation                                                       #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_freq_matched_random_preserves_node_set_and_order(family: str) -> None:
    ref = _reference_graph(family=family)
    null = build_freq_matched_random_graph(ref, seed=7)

    assert null.nodes == ref.nodes
    assert set(null.adjacency.keys()) == set(ref.adjacency.keys())


# --------------------------------------------------------------------------- #
# (3) Degree preservation                                                     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_freq_matched_random_preserves_per_node_degree(family: str) -> None:
    ref = _reference_graph(family=family)
    null = build_freq_matched_random_graph(ref, seed=13)

    ref_deg = _degree_map(ref)
    null_deg = _degree_map(null)

    # The whole point of double edge swap: per-node degree preserved.
    assert null_deg == ref_deg


def test_freq_matched_random_preserves_total_edge_count() -> None:
    ref = _reference_graph(size=48)
    null = build_freq_matched_random_graph(ref, seed=97)

    ref_edges = sum(_degree_map(ref).values()) // 2
    null_edges = sum(_degree_map(null).values()) // 2

    assert ref_edges == null_edges
    assert ref_edges > 0  # non-trivial reference


# --------------------------------------------------------------------------- #
# (4) Weight multiset preservation                                            #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_freq_matched_random_preserves_weight_multiset(family: str) -> None:
    ref = _reference_graph(family=family)
    null = build_freq_matched_random_graph(ref, seed=57)

    ref_weights = _weight_multiset(ref)
    null_weights = _weight_multiset(null)

    assert len(ref_weights) == len(null_weights)
    # Sorted equality: multiset preservation, weight identity is
    # permuted across edges.
    for r, n in zip(ref_weights, null_weights):
        assert r == pytest.approx(n)


# --------------------------------------------------------------------------- #
# (5) Structure differs                                                       #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_freq_matched_random_edge_set_differs_from_reference(family: str) -> None:
    ref = _reference_graph(family=family)
    null = build_freq_matched_random_graph(ref, seed=101)

    ref_edges = _canonical_edge_set(ref)
    null_edges = _canonical_edge_set(null)

    # Under double-edge swap on a non-trivial graph, the returned
    # edge set must differ from the reference's — this is the
    # matched-budget "null" property.
    assert null_edges != ref_edges
    # And they overlap only partially; a very small overlap is
    # expected under random rewiring.
    overlap = ref_edges & null_edges
    assert len(overlap) < len(ref_edges)


# --------------------------------------------------------------------------- #
# (6) Anti-leakage                                                            #
# --------------------------------------------------------------------------- #


def test_build_freq_matched_random_is_integrity_audit_clean() -> None:
    # The null must be safely callable from a policy path — it has no
    # access to sealed fields.
    IntegrityAudit.assert_clean(build_freq_matched_random_graph)


# --------------------------------------------------------------------------- #
# Argument validation                                                          #
# --------------------------------------------------------------------------- #


def test_rejects_non_weighted_graph_reference() -> None:
    with pytest.raises(TypeError):
        build_freq_matched_random_graph("not-a-graph", seed=1)  # ty: ignore[invalid-argument-type]  # noqa


def test_rejects_non_int_seed() -> None:
    ref = _reference_graph(size=12)
    with pytest.raises(TypeError):
        build_freq_matched_random_graph(ref, seed=1.5)  # ty: ignore[invalid-argument-type]  # noqa


def test_rejects_boolean_seed() -> None:
    ref = _reference_graph(size=12)
    with pytest.raises(TypeError):
        build_freq_matched_random_graph(ref, seed=True)  # noqa


def test_rejects_non_positive_swap_multiplier() -> None:
    ref = _reference_graph(size=12)
    with pytest.raises(ValueError):
        build_freq_matched_random_graph(ref, seed=1, swap_multiplier=0)


# --------------------------------------------------------------------------- #
# Edge cases                                                                   #
# --------------------------------------------------------------------------- #


def test_empty_reference_returns_empty_graph() -> None:
    # An empty edge set means no swap is possible; the null degenerates
    # to the (empty) reference on the same node set.
    ref = WeightedGraph.from_edges(("a", "b", "c"), ())
    null = build_freq_matched_random_graph(ref, seed=1)

    assert null.nodes == ref.nodes
    assert all(not null.adjacency[node] for node in null.nodes)


def test_single_edge_reference_is_returned_unchanged_on_topology() -> None:
    # With one edge the double-edge swap cannot pick two distinct
    # edges; the null returns the reference topology. Weight multiset
    # still matches (trivially: one weight).
    ref = WeightedGraph.from_edges(("a", "b", "c"), (("a", "b", 0.7),))
    null = build_freq_matched_random_graph(ref, seed=5)

    assert null.nodes == ref.nodes
    assert _canonical_edge_set(null) == _canonical_edge_set(ref)
    assert _weight_multiset(null) == _weight_multiset(ref)


# --------------------------------------------------------------------------- #
# Sanity: the null is a well-formed PPR input                                  #
# --------------------------------------------------------------------------- #


def test_null_geometry_supports_personalized_pagerank() -> None:
    ref = _reference_graph(size=24)
    null = build_freq_matched_random_graph(ref, seed=333)

    restart = {null.nodes[0]: 1.0}
    result = personalized_pagerank(
        null, restart, tolerance=1e-12, max_iterations=500
    )

    assert result.l1_residual < 1e-9
    assert sum(result.scores.values()) == pytest.approx(1.0, abs=1e-10)


# --------------------------------------------------------------------------- #
# Constants                                                                    #
# --------------------------------------------------------------------------- #


def test_module_constants_are_documented_positive_values() -> None:
    assert DEFAULT_SWAP_MULTIPLIER > 0
    assert MIN_SWAP_ATTEMPTS > 0


# --------------------------------------------------------------------------- #
# Extra: no self-loops or duplicates leak through                              #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_null_has_no_self_loops(family: str) -> None:
    ref = _reference_graph(family=family)
    null = build_freq_matched_random_graph(ref, seed=99)
    for node in null.nodes:
        assert node not in null.adjacency[node]


@pytest.mark.parametrize("family", sorted(FAMILY_NAMES))
def test_null_adjacency_is_symmetric(family: str) -> None:
    # WeightedGraph.from_edges symmetrises edges, so this is really a
    # regression check that the null did not construct a directed
    # adjacency by accident.
    ref = _reference_graph(family=family)
    null = build_freq_matched_random_graph(ref, seed=11)
    for u in null.nodes:
        for v, w in null.adjacency[u].items():
            assert u in null.adjacency[v]
            assert null.adjacency[v][u] == pytest.approx(w)


def test_leakage_error_is_not_raised_on_typical_use() -> None:
    # If anti-leakage were subtly wrong, ``build_freq_matched_random_graph``
    # would trip LeakageError somewhere upstream. Confirm the happy path
    # is silent.
    ref = _reference_graph(size=16)
    try:
        build_freq_matched_random_graph(ref, seed=1)
    except LeakageError as exc:  # pragma: no cover - defensive
        pytest.fail(f"unexpected LeakageError on happy path: {exc}")
