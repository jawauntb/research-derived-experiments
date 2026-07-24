"""Wave 1b frequency-matched random geometry — the matched-budget graph null.

The Wave 1b crossed factorial (``PREREGISTRATION.md`` §5) sweeps the
geometry axis over three levels:

* ``LEARNED`` — the candidate mechanism's learned graph.
* ``FREQ_MATCHED_RANDOM`` — this module: same node set, same per-node
  degree, same weight distribution as the reference learned graph, but
  edge *targets* are randomised. It is the correct null for the L1
  representation-contribution question ("does the *structure* of the
  learned graph matter, or is any graph with the same density and
  degree distribution sufficient?"). If the candidate mechanism
  composed with :func:`build_freq_matched_random_graph` matches the
  candidate mechanism composed with the learned graph, the L1
  representation claim fails.
* ``ORACLE_WITHHELD`` — the ceiling-only oracle geometry built by
  :mod:`experiments.concern_gated_retrieval_e2.wave1b.oracle_geometry`,
  refused by the promotion harness.

Design
------

The construction is a **degree-preserving double edge swap** starting
from the reference graph. Each swap picks two edges ``(a, b)`` and
``(c, d)``, proposes the rewired pair ``(a, d)`` and ``(c, b)``, and
accepts the swap when the proposal introduces no self-loop and no
duplicate edge. Double edge swaps preserve each node's degree exactly,
so the returned graph has the identical per-node degree sequence as
``learned_graph_reference``. The weight multiset is preserved (weights
are carried by the swapped edges and then re-shuffled across edges to
break any residual correlation between weight and position). No node
identity carries a role label, so the null is anti-leakage clean.

Anti-leakage
------------

:func:`build_freq_matched_random_graph` reads only the reference
``WeightedGraph`` and a numeric seed. It does not consult
``EpisodeSpec.role``, ``EpisodeSpec.utility``, ``EpisodeSpec._answer_key``,
or any evaluator-only field enumerated in ``wave0/PREREGISTRATION.md``
§4.1. The module is designed to pass
:meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.assert_clean`.

Reuse boundary
--------------

The reference graph is a Wave 0
:class:`~experiments.concern_gated_retrieval.graph.WeightedGraph`. The
Wave 1b runner supplies whatever learned or withheld graph it wants to
null-test. Callers commonly pass
:func:`~experiments.concern_gated_retrieval_e2.wave0.graph_learn.build_withheld_graph`
output for the fixed-withheld baseline null; the runner may also pass a
learned graph produced by its own graph-learning code. This module
holds no knowledge of how the reference was constructed.
"""

from __future__ import annotations

import random
from typing import Final

from experiments.concern_gated_retrieval.graph import WeightedGraph


#: Default number of swap attempts per reference edge. Empirically,
#: ``E * 10`` swaps mix a small graph well beyond any residual
#: correlation with the reference's edge set (see the Wave 1b test
#: suite's swap-count sensitivity check). Kept as a module-level
#: constant so a downstream sensitivity study can override it
#: deliberately; the receipt records the override.
DEFAULT_SWAP_MULTIPLIER: Final[int] = 10


#: Absolute floor on the number of swap attempts, in case a very small
#: reference (few edges) would otherwise perform too few swaps for the
#: null to be a meaningful rewire.
MIN_SWAP_ATTEMPTS: Final[int] = 64


def _rng(seed: int) -> random.Random:
    """Return a deterministic PRNG scoped to this module.

    Scoping the seed by module name means the same integer seed used
    elsewhere in the codebase produces a distinct stream here — no
    cross-module correlation between the null geometry and, e.g., the
    Wave 0 wrong-prior sampler.
    """
    return random.Random(f"cogr-e2-wave1b::freq_matched_random_geometry::{seed}")


def _canonical_edge(u: str, v: str) -> tuple[str, str]:
    """Return the undirected edge in canonical (min, max) form."""
    return (u, v) if u <= v else (v, u)


def _collect_undirected_edges(
    graph: WeightedGraph,
) -> tuple[list[tuple[str, str]], list[float]]:
    """Return the reference graph's undirected edge list and weight list.

    Each undirected edge appears exactly once (canonicalised so ``u <=
    v``). Weights are collected in the same order as the edges, so
    ``edges[i]`` and ``weights[i]`` refer to the same undirected edge.
    """
    edges: list[tuple[str, str]] = []
    weights: list[float] = []
    for u in graph.nodes:
        for v, w in graph.adjacency[u].items():
            if u < v:  # count each undirected edge exactly once
                edges.append((u, v))
                weights.append(float(w))
    return edges, weights


def build_freq_matched_random_graph(
    learned_graph_reference: WeightedGraph,
    seed: int,
    *,
    swap_multiplier: int = DEFAULT_SWAP_MULTIPLIER,
) -> WeightedGraph:
    """Return a degree-preserving random null of ``learned_graph_reference``.

    Same node set, same per-node degree sequence, same weight multiset
    as the reference; edge *targets* are randomised via double edge
    swaps.

    Parameters
    ----------
    learned_graph_reference:
        The reference :class:`WeightedGraph`. Must be an undirected
        weighted graph produced by any Wave 0 / Wave 1b geometry
        builder. The reference is not mutated.
    seed:
        Deterministic seed. Two calls with the same ``(reference,
        seed)`` return byte-identical graphs.
    swap_multiplier:
        The number of swap attempts is
        ``max(MIN_SWAP_ATTEMPTS, swap_multiplier * E)`` where ``E`` is
        the reference edge count. Kept as a keyword-only override so a
        sensitivity study can push it higher without changing the
        default receipt.

    Returns
    -------
    WeightedGraph
        The rewired null geometry over the same node set. Every node
        in ``learned_graph_reference.nodes`` appears in the returned
        graph in the same order. Every node's degree matches the
        reference exactly. The weight multiset matches the reference.

    Raises
    ------
    TypeError
        If ``learned_graph_reference`` is not a
        :class:`WeightedGraph`, or ``seed`` is not an ``int``.
    ValueError
        If ``swap_multiplier`` is not a positive integer.
    """
    if not isinstance(learned_graph_reference, WeightedGraph):
        raise TypeError(
            "learned_graph_reference must be a WeightedGraph; got "
            f"{type(learned_graph_reference).__name__}"
        )
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be int (not bool)")
    if not isinstance(swap_multiplier, int) or swap_multiplier <= 0:
        raise ValueError("swap_multiplier must be a positive int")

    rng = _rng(seed)
    nodes = learned_graph_reference.nodes

    edges, weights = _collect_undirected_edges(learned_graph_reference)

    # Empty or single-edge reference — no swap possible; return a
    # rewire-null that mirrors the empty structure. Weight multiset is
    # trivially preserved.
    if len(edges) < 2:
        return WeightedGraph.from_edges(
            nodes,
            tuple((u, v, w) for (u, v), w in zip(edges, weights)),
        )

    # ``edge_positions[canonical(u, v)] = index into edges`` — O(1)
    # membership + O(1) update on swap.
    edge_positions: dict[tuple[str, str], int] = {
        _canonical_edge(u, v): i for i, (u, v) in enumerate(edges)
    }

    num_swaps = max(MIN_SWAP_ATTEMPTS, swap_multiplier * len(edges))

    for _ in range(num_swaps):
        i = rng.randrange(len(edges))
        j = rng.randrange(len(edges))
        if i == j:
            continue
        a, b = edges[i]
        c, d = edges[j]
        # Randomly orient the second edge so we sample from both
        # ``(a,d)/(c,b)`` and ``(a,c)/(b,d)`` rewire patterns.
        if rng.random() < 0.5:
            c, d = d, c

        # Refuse self-loops.
        if a == d or c == b:
            continue

        new1 = _canonical_edge(a, d)
        new2 = _canonical_edge(c, b)

        # Refuse if the two proposed edges collapse onto each other.
        if new1 == new2:
            continue
        # Refuse if either proposed edge already exists elsewhere in
        # the graph (i.e. would produce a duplicate).
        if new1 in edge_positions and edge_positions[new1] not in (i, j):
            continue
        if new2 in edge_positions and edge_positions[new2] not in (i, j):
            continue

        # Accept the swap: remove old canonical keys, install new.
        old1 = _canonical_edge(a, b)
        old2 = _canonical_edge(c, d)
        del edge_positions[old1]
        del edge_positions[old2]
        edges[i] = new1
        edges[j] = new2
        edge_positions[new1] = i
        edge_positions[new2] = j

    # Shuffle weight assignment across the (rewired) edges so any
    # residual correlation between original edge identity and weight
    # is broken. The weight multiset is invariant under permutation.
    shuffled_weights = list(weights)
    rng.shuffle(shuffled_weights)

    final_edges: list[tuple[str, str, float]] = [
        (u, v, w) for (u, v), w in zip(edges, shuffled_weights)
    ]
    return WeightedGraph.from_edges(nodes, final_edges)


__all__ = [
    "DEFAULT_SWAP_MULTIPLIER",
    "MIN_SWAP_ATTEMPTS",
    "build_freq_matched_random_graph",
]
