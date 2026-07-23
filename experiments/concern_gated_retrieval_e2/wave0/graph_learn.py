"""Wave 0 fixed-withheld-geometry and graph-learning stubs.

Wave 0 uses **fixed withheld geometry** produced by procedural rules whose
inputs are exactly ``(seed, size, family)``. The generators never consult
any evaluator-only field enumerated in ``PREREGISTRATION.md`` §4.1 — role
labels, answer keys, future utilities, oracle concern, wrong-agent labels,
paraphrase-family ids, or sealed outcome receipts. The concern warp is
policy-visible: it consumes a numeric mapping over node ids and carries no
role identity.

This module contains only Wave 0 objects: the fixed-geometry builder, the
concern warp facade, and a rarity aggregator. All Wave 1 objects — learned
graph structure, learned concern updates, sealed environments, and
confirmatory rows — are explicitly out of scope for Wave 0 and belong to
``experiments/concern_gated_retrieval_e2/wave1/`` (COGR-E2a, then E2b).

Reused numerical primitives:
    * :class:`~experiments.concern_gated_retrieval.graph.WeightedGraph`
    * :func:`~experiments.concern_gated_retrieval.graph.personalized_pagerank`

The frozen L0 pilot package is imported here and **never** edited. See
``experiments/concern_gated_retrieval_e2/README.md`` for the reuse boundary.
"""

from __future__ import annotations

import math
import random
from typing import Iterable, Mapping

from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    personalized_pagerank as _personalized_pagerank,
)

# Re-export the pilot's PPR primitive at the Wave 0 module boundary so
# downstream Wave 0 callers do not need to reach through the pilot import
# path. Do NOT fork this primitive; this is a name-level alias only.
personalized_pagerank = _personalized_pagerank


# The three procedural families declared by PREREGISTRATION.md §6. Wave 0
# calibration code refuses any family name not in this set — including
# confirmatory-only names — and thereby preserves the calibration /
# confirmatory family split at the geometry-builder boundary.
FAMILY_NAMES: frozenset[str] = frozenset(
    {"delayed_commitments", "maintenance_fault", "resource_constrained"}
)


# Default warp strength used by Wave 0's calibration slate. The pilot's
# ``WeightedGraph.concern_warped`` multiplier is ``1 + strength * mean(c)``.
# A finite non-negative strength preserves node support and edge sign.
# Confirmatory rows will use a frozen strength recorded in the calibration
# manifest; Wave 0 exposes this default only.
DEFAULT_WARP_STRENGTH: float = 1.0


# Minimum node count per withheld graph. Below this the PPR fixed point
# becomes trivial and the rarity aggregator has an unstable denominator on
# small calibration batches. Wave 0 calibration always requests sizes far
# above this floor.
MIN_GRAPH_SIZE: int = 6


def _validate_family(family: str) -> None:
    """Reject any family name outside the Wave 0 declared set."""
    if family not in FAMILY_NAMES:
        raise ValueError(
            f"unknown Wave 0 family: {family!r}; expected one of "
            f"{sorted(FAMILY_NAMES)}"
        )


def _node_name(family: str, seed: int, index: int) -> str:
    """Return a procedural node id independent of any evaluator field.

    Names are a pure function of ``(family, seed, index)``. The generator
    therefore has no channel through which a role label, answer key, or
    other evaluator-only field could reach the constructed graph.
    """
    return f"{family}_s{seed:06d}_n{index:03d}"


def _rng(seed: int, family: str, salt: str) -> random.Random:
    """Return a deterministic per-family / per-purpose PRNG.

    The seeded stream is scoped by ``(seed, family, salt)`` so that two
    families invoked with the same seed produce structurally distinct
    graphs. The salt separates different structural components inside a
    family (backbone vs. skip edges vs. cross-links).
    """
    return random.Random(f"cogr-e2-wave0::{family}::{salt}::{seed}")


def _delayed_commitments_edges(
    seed: int, size: int
) -> list[tuple[str, str, float]]:
    """Timeline chain plus modulo-anchor skip edges.

    Nodes are strung along a temporal chain (a rough proxy for the
    ``history`` order that a delayed-commitments family emits). Skip edges
    connect indices whose separation matches a small set of seeded
    modulus offsets, proxying the date-anchor structure of that surface
    without ever consulting a role label.
    """
    rng = _rng(seed, "delayed_commitments", "edges")
    family = "delayed_commitments"
    edges: list[tuple[str, str, float]] = []
    # Backbone chain.
    for i in range(size - 1):
        weight = 1.0 + rng.random() * 0.25
        edges.append(
            (_node_name(family, seed, i), _node_name(family, seed, i + 1), weight)
        )
    # Modulo-anchor skip edges.
    offsets = sorted({rng.randint(3, 7) for _ in range(3)})
    for start in range(size):
        for offset in offsets:
            end = start + offset
            if end >= size:
                continue
            weight = 0.4 + rng.random() * 0.3
            edges.append(
                (
                    _node_name(family, seed, start),
                    _node_name(family, seed, end),
                    weight,
                )
            )
    return edges


def _maintenance_fault_edges(
    seed: int, size: int
) -> list[tuple[str, str, float]]:
    """Log-stream chain with a boilerplate hub and delayed cross-links.

    A single hub node broadcasts to every other node with a modest weight
    (proxy for boilerplate warnings). A chain runs from node 1 to the last
    index. A small number of cross-links jump from early chain nodes to
    later ones, proxying the "old observation only becomes load-bearing
    when a later symptom appears" surface. Role labels are absent from
    this construction; the "hub" is procedurally the first node, not a
    labelled alarm.
    """
    rng = _rng(seed, "maintenance_fault", "edges")
    family = "maintenance_fault"
    edges: list[tuple[str, str, float]] = []
    hub = _node_name(family, seed, 0)
    # Boilerplate hub broadcast.
    for i in range(1, size):
        weight = 0.5 + rng.random() * 0.2
        edges.append((hub, _node_name(family, seed, i), weight))
    # Log chain from index 1 onward.
    for i in range(1, size - 1):
        weight = 1.0 + rng.random() * 0.25
        edges.append(
            (_node_name(family, seed, i), _node_name(family, seed, i + 1), weight)
        )
    # Delayed cross-links: early observation to a later symptom.
    num_cross = max(1, size // 5)
    early_ceiling = max(1, size // 3)
    for _ in range(num_cross):
        early = rng.randint(1, early_ceiling)
        later_low = early + 2
        if later_low >= size:
            continue
        later = rng.randint(later_low, size - 1)
        weight = 0.3 + rng.random() * 0.4
        edges.append(
            (
                _node_name(family, seed, early),
                _node_name(family, seed, later),
                weight,
            )
        )
    return edges


def _resource_constrained_edges(
    seed: int, size: int
) -> list[tuple[str, str, float]]:
    """Bipartite obligation/action links with recurrent within-half constraints.

    Node indices are informally split into "left" and "right" halves; the
    backbone is bipartite (left <-> right), a proxy for the ledger-style
    obligation-to-action mapping this family emits. A modest number of
    within-half constraints add the "prior obligation constrains which
    otherwise-valid action is best" flavor. Role labels are absent; the
    split is a pure function of ``size``, not of any evaluator field.
    """
    rng = _rng(seed, "resource_constrained", "edges")
    family = "resource_constrained"
    edges: list[tuple[str, str, float]] = []
    split = size // 2
    left = list(range(0, split))
    right = list(range(split, size))
    fanout = max(2, size // 4)
    # Bipartite backbone.
    for i in left:
        targets = rng.sample(right, k=min(fanout, len(right)))
        for j in targets:
            weight = 0.7 + rng.random() * 0.3
            edges.append(
                (
                    _node_name(family, seed, i),
                    _node_name(family, seed, j),
                    weight,
                )
            )
    # Within-half obligations (left side).
    num_within = max(1, size // 3)
    if len(left) >= 2:
        for _ in range(num_within):
            i = rng.randint(0, split - 1)
            j = rng.randint(0, split - 1)
            while j == i:
                j = rng.randint(0, split - 1)
            weight = 0.35 + rng.random() * 0.35
            edges.append(
                (
                    _node_name(family, seed, i),
                    _node_name(family, seed, j),
                    weight,
                )
            )
    # Within-half obligations (right side).
    if len(right) >= 2:
        for _ in range(num_within):
            i = rng.randint(split, size - 1)
            j = rng.randint(split, size - 1)
            while j == i:
                j = rng.randint(split, size - 1)
            weight = 0.35 + rng.random() * 0.35
            edges.append(
                (
                    _node_name(family, seed, i),
                    _node_name(family, seed, j),
                    weight,
                )
            )
    return edges


_FAMILY_EDGE_BUILDERS = {
    "delayed_commitments": _delayed_commitments_edges,
    "maintenance_fault": _maintenance_fault_edges,
    "resource_constrained": _resource_constrained_edges,
}


def build_withheld_graph(seed: int, size: int, family: str) -> WeightedGraph:
    """Return the fixed withheld weighted graph for a Wave 0 family.

    Only ``(seed, size, family)`` determines the topology and weights.
    Successive calls with the same arguments are byte-identical. The
    generator does not read role labels, answer keys, future utilities,
    oracle concern, wrong-agent labels, paraphrase-family ids, or any
    other evaluator-only field enumerated in PREREGISTRATION.md §4.1.

    Wave 0 uses this fixed geometry only. Wave 1 (E2b) will introduce
    learned graph structure; that work lives in a separate module and is
    out of scope here.
    """
    _validate_family(family)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be int")
    if size < MIN_GRAPH_SIZE:
        raise ValueError(f"size must be >= {MIN_GRAPH_SIZE}; got {size}")
    nodes = tuple(_node_name(family, seed, i) for i in range(size))
    edges = _FAMILY_EDGE_BUILDERS[family](seed, size)
    return WeightedGraph.from_edges(nodes, edges)


def apply_concern_warp(
    graph: WeightedGraph,
    concern: Mapping[str, float],
    *,
    strength: float = DEFAULT_WARP_STRENGTH,
) -> WeightedGraph:
    """Apply a concern-weighted edge warp to a fixed withheld graph.

    Delegates to the pilot's
    :meth:`~experiments.concern_gated_retrieval.graph.WeightedGraph.concern_warped`
    primitive. The multiplier ``1 + strength * (c_i + c_j) / 2`` is >= 1
    for non-negative concern weights, so:

    * every node in ``graph`` appears in the returned graph;
    * every positive-weight edge remains positive-weight; and
    * graph support is preserved.

    ``concern`` is a policy-visible numeric mapping over node ids. It
    carries no role identity. This function does not consult any
    evaluator-only field, and refuses concern maps that reference nodes
    outside the graph to keep the input surface auditable.
    """
    if not isinstance(concern, Mapping):
        raise TypeError("concern must be a Mapping[str, float]")
    unknown = set(concern) - set(graph.nodes)
    if unknown:
        raise ValueError(f"concern contains unknown nodes: {sorted(unknown)}")
    return graph.concern_warped(dict(concern), strength=strength)


def rarity_scores(
    graphs_iter: Iterable[WeightedGraph],
    *,
    epsilon: float = 1e-9,
) -> dict[str, float]:
    """Return per-node inverse-frequency rarity scores across a graph batch.

    Node identity is treated as the sole grouping key. Rarity is defined
    as ``1 / max(fraction_of_graphs_containing_node, epsilon)`` so that a
    node in every graph receives a score near ``1.0`` and a node in only
    one graph out of ``N`` receives a score near ``N``. The output shape
    mirrors the pilot's frequency-based rarity correction so downstream
    Wave 0 code paths can plug this into a rarity-corrected Hadamard
    product without changing the pilot's numerical semantics.

    The iterable is consumed exactly once. Every element must be a
    :class:`WeightedGraph`; ``rarity_scores`` never reads edges, only
    ``graph.nodes``, and therefore never consults role labels.
    """
    if epsilon <= 0 or not math.isfinite(epsilon):
        raise ValueError("epsilon must be finite and positive")
    counts: dict[str, int] = {}
    total = 0
    for graph in graphs_iter:
        if not isinstance(graph, WeightedGraph):
            raise TypeError("rarity_scores requires WeightedGraph inputs")
        total += 1
        # Deduplicate within a single graph — a node exists or does not.
        for node in set(graph.nodes):
            counts[node] = counts.get(node, 0) + 1
    if total == 0:
        return {}
    return {
        node: 1.0 / max(count / total, epsilon)
        for node, count in counts.items()
    }
