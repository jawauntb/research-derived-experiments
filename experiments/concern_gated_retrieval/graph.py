"""Weighted graph diffusion primitives for off-context retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence


@dataclass(frozen=True)
class WeightedGraph:
    """An undirected graph with finite, non-negative edge weights."""

    nodes: tuple[str, ...]
    adjacency: dict[str, dict[str, float]]

    @classmethod
    def from_edges(
        cls,
        nodes: Sequence[str],
        edges: Sequence[tuple[str, str, float]],
    ) -> WeightedGraph:
        ordered_nodes = tuple(dict.fromkeys(nodes))
        adjacency = {node: {} for node in ordered_nodes}
        for left, right, weight in edges:
            if left not in adjacency or right not in adjacency:
                raise ValueError(f"edge names unknown node: {(left, right)}")
            if left == right:
                raise ValueError("self-edges are not supported")
            if not isfinite(weight) or weight < 0:
                raise ValueError("edge weights must be finite and non-negative")
            if weight == 0:
                continue
            adjacency[left][right] = adjacency[left].get(right, 0.0) + weight
            adjacency[right][left] = adjacency[right].get(left, 0.0) + weight
        return cls(nodes=ordered_nodes, adjacency=adjacency)

    def concern_warped(
        self,
        care_weights: Mapping[str, float],
        *,
        strength: float,
    ) -> WeightedGraph:
        """Return a graph whose edges are smoothly strengthened by concern.

        The multiplier is ``1 + strength * (c_i + c_j) / 2``. It is positive
        for non-negative care weights and preserves graph support and symmetry.
        """

        if not isfinite(strength) or strength < 0:
            raise ValueError("warp strength must be finite and non-negative")
        for value in care_weights.values():
            if not isfinite(value) or value < 0:
                raise ValueError("care weights must be finite and non-negative")

        edges: list[tuple[str, str, float]] = []
        for left in self.nodes:
            for right, base_weight in self.adjacency[left].items():
                if left >= right:
                    continue
                care = (care_weights.get(left, 0.0) + care_weights.get(right, 0.0)) / 2
                edges.append((left, right, base_weight * (1 + strength * care)))
        return WeightedGraph.from_edges(self.nodes, edges)


@dataclass(frozen=True)
class PPRResult:
    """A converged personalized PageRank vector and its numerical receipt."""

    scores: dict[str, float]
    iterations: int
    l1_residual: float


def _normalize_restart(
    nodes: Sequence[str],
    restart: Mapping[str, float],
) -> dict[str, float]:
    unknown = set(restart) - set(nodes)
    if unknown:
        raise ValueError(f"restart contains unknown nodes: {sorted(unknown)}")
    if any(not isfinite(value) or value < 0 for value in restart.values()):
        raise ValueError("restart weights must be finite and non-negative")
    total = sum(restart.values())
    if total <= 0:
        raise ValueError("restart weights must contain positive mass")
    return {node: restart.get(node, 0.0) / total for node in nodes}


def _pagerank_step(
    graph: WeightedGraph,
    degrees: Mapping[str, float],
    scores: Mapping[str, float],
    restart: Mapping[str, float],
    alpha: float,
) -> dict[str, float]:
    next_scores = {node: alpha * restart[node] for node in graph.nodes}
    continuation = 1 - alpha
    for source in graph.nodes:
        source_mass = continuation * scores[source]
        neighbors = graph.adjacency[source]
        degree = degrees[source]
        if degree == 0:
            for target in graph.nodes:
                next_scores[target] += source_mass * restart[target]
            continue
        for target, weight in neighbors.items():
            next_scores[target] += source_mass * weight / degree
    return next_scores


def personalized_pagerank(
    graph: WeightedGraph,
    restart: Mapping[str, float],
    *,
    alpha: float = 0.2,
    tolerance: float = 1e-12,
    max_iterations: int = 500,
) -> PPRResult:
    """Solve ``r = alpha*pi + (1-alpha) P^T r`` by power iteration."""

    if not 0 < alpha <= 1:
        raise ValueError("alpha must be in (0, 1]")
    if tolerance <= 0 or not isfinite(tolerance):
        raise ValueError("tolerance must be finite and positive")
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")

    normalized_restart = _normalize_restart(graph.nodes, restart)
    scores = dict(normalized_restart)
    degrees = {
        node: sum(graph.adjacency[node].values())
        for node in graph.nodes
    }
    for iterations in range(1, max_iterations + 1):
        next_scores = _pagerank_step(
            graph,
            degrees,
            scores,
            normalized_restart,
            alpha,
        )
        delta = sum(abs(next_scores[node] - scores[node]) for node in graph.nodes)
        scores = next_scores
        if delta <= tolerance:
            break
    else:
        raise RuntimeError("personalized PageRank did not converge")

    fixed_point = _pagerank_step(
        graph,
        degrees,
        scores,
        normalized_restart,
        alpha,
    )
    residual = sum(abs(fixed_point[node] - scores[node]) for node in graph.nodes)
    return PPRResult(scores=scores, iterations=iterations, l1_residual=residual)


def coincidence_scores(
    context_scores: Mapping[str, float],
    care_scores: Mapping[str, float],
    frequency_scores: Mapping[str, float],
    candidates: Sequence[str],
    *,
    rarity_exponent: float = 0.25,
    epsilon: float = 1e-15,
) -> dict[str, float]:
    """Return the rarity-corrected Hadamard product on candidate nodes."""

    if rarity_exponent < 0 or not isfinite(rarity_exponent):
        raise ValueError("rarity exponent must be finite and non-negative")
    if epsilon <= 0 or not isfinite(epsilon):
        raise ValueError("epsilon must be finite and positive")
    common = set(context_scores) & set(care_scores) & set(frequency_scores)
    if missing := set(candidates) - common:
        raise ValueError(f"candidate scores are missing nodes: {sorted(missing)}")
    return {
        node: (
            context_scores[node]
            * care_scores[node]
            / max(frequency_scores[node], epsilon) ** rarity_exponent
        )
        for node in candidates
    }
