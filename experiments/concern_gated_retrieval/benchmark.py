"""Deterministic synthetic benchmark for concern-gated retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import isfinite
from typing import Callable, Mapping, Sequence

import numpy as np

from experiments.concern_gated_retrieval.epiplexity import ReservoirEpiplexity
from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    coincidence_scores,
    personalized_pagerank,
)


ANCHORS = ("commitment", "family", "global_alarm")
POLICIES = ("context", "care", "additive", "coincidence", "verified")
ORACLE_CARE_WEIGHTS = {
    "commitment": 1.5,
    "family": 1.5,
    "global_alarm": 0.25,
}


@dataclass(frozen=True)
class Candidate:
    node: str
    role: str
    anchor: str | None
    utility: float
    future_kind: str


@dataclass(frozen=True)
class SyntheticEpisode:
    episode_id: str
    graph: WeightedGraph
    active_nodes: tuple[str, ...]
    care_anchors: tuple[str, ...]
    candidates: tuple[Candidate, ...]
    load_bearing_node: str
    seed: int
    regime: str


@dataclass(frozen=True)
class EpisodeRanking:
    policy: str
    ranked_nodes: tuple[str, ...]
    top_role: str | None
    load_bearing_rank: int | None
    ppr_residual: float


@dataclass(frozen=True)
class EvaluationResult:
    episodes: int
    hit_at_1: dict[str, float]
    mean_reciprocal_rank: dict[str, float]
    distractor_at_1: dict[str, float]
    verifier_precision: float
    verifier_recall: float
    max_ppr_residual: float
    rankings: tuple[EpisodeRanking, ...]


@dataclass(frozen=True)
class CareLearningResult:
    initial_weights: dict[str, float]
    learned_weights: dict[str, float]
    selected_load_bearing_rate: float
    mean_selected_utility: float


@dataclass(frozen=True)
class EpiplexityControlAudit:
    """Worst-case registered structured-versus-control comparison."""

    minimum_margin_bits: float
    worst_seed: int
    worst_regime: str
    worst_control_role: str
    role_minimum_bits: dict[str, float]
    role_maximum_bits: dict[str, float]


def _jitter(rng: np.random.Generator, scale: float) -> float:
    return float(rng.uniform(1 - scale, 1 + scale))


def generate_episode(seed: int, *, regime: str = "base") -> SyntheticEpisode:
    """Generate one graph with dual, one-sided, and coincidence-trap nodes."""

    if regime not in {"base", "sparse", "noisy"}:
        raise ValueError(f"unknown regime: {regime}")
    rng = np.random.default_rng(seed)
    target_anchor = ("commitment", "family")[seed % 2]
    other_anchor = "family" if target_anchor == "commitment" else "commitment"
    prefix = f"e{seed}"
    active = f"{prefix}:active"
    load = f"{prefix}:load"
    context_only = f"{prefix}:context_only"
    care_only = f"{prefix}:care_only"
    alarm = f"{prefix}:alarm"
    coincidence_trap = f"{prefix}:coincidence_trap"
    neutral = f"{prefix}:neutral"
    nodes = [
        active,
        *ANCHORS,
        load,
        context_only,
        care_only,
        alarm,
        coincidence_trap,
        neutral,
    ]
    jitter_scale = {"base": 0.08, "sparse": 0.12, "noisy": 0.2}[regime]
    density = {"base": 1.0, "sparse": 0.78, "noisy": 1.12}[regime]
    edges = [
        (active, load, 1.15 * _jitter(rng, jitter_scale)),
        (target_anchor, load, 1.15 * _jitter(rng, jitter_scale)),
        (active, context_only, 2.4 * _jitter(rng, jitter_scale)),
        (target_anchor, context_only, 0.025 * density),
        (active, care_only, 0.025 * density),
        (other_anchor, care_only, 2.4 * _jitter(rng, jitter_scale)),
        (active, alarm, 0.08 * density),
        ("global_alarm", alarm, 2.8 * _jitter(rng, jitter_scale)),
        (
            active,
            coincidence_trap,
            0.82 * _jitter(rng, jitter_scale),
        ),
        (
            "global_alarm",
            coincidence_trap,
            0.9 * _jitter(rng, jitter_scale),
        ),
        (active, neutral, 0.22 * density),
        (target_anchor, neutral, 0.16 * density),
        (other_anchor, neutral, 0.16 * density),
        ("commitment", "family", 0.04 * density),
        ("commitment", "global_alarm", 0.025 * density),
        ("family", "global_alarm", 0.025 * density),
    ]
    if regime == "noisy":
        edges.extend(
            [
                (other_anchor, load, 0.12 * _jitter(rng, jitter_scale)),
                (target_anchor, alarm, 0.13 * _jitter(rng, jitter_scale)),
                (
                    other_anchor,
                    coincidence_trap,
                    0.14 * _jitter(rng, jitter_scale),
                ),
                ("global_alarm", neutral, 0.16),
            ]
        )

    candidates = (
        Candidate(load, "load_bearing", target_anchor, 1.0, "structured"),
        Candidate(context_only, "context_only", None, 0.0, "constant"),
        Candidate(care_only, "care_only", other_anchor, 0.0, "constant"),
        Candidate(alarm, "alarm", "global_alarm", -1.0, "noise"),
        Candidate(
            coincidence_trap,
            "coincidence_trap",
            "global_alarm",
            -0.75,
            "noise",
        ),
        Candidate(neutral, "neutral", None, 0.0, "constant"),
    )
    return SyntheticEpisode(
        episode_id=f"{prefix}:{regime}",
        graph=WeightedGraph.from_edges(nodes, edges),
        active_nodes=(active,),
        care_anchors=ANCHORS,
        candidates=candidates,
        load_bearing_node=load,
        seed=seed,
        regime=regime,
    )


def generate_episodes(
    seeds: Sequence[int],
    *,
    regimes: Sequence[str] = ("base", "sparse", "noisy"),
) -> tuple[SyntheticEpisode, ...]:
    return tuple(
        generate_episode(seed, regime=regime)
        for regime in regimes
        for seed in seeds
    )


def _future_data(candidate: Candidate, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Return goal-conditioned future inputs and candidate-dependent targets."""

    phase = np.linspace(-np.pi, np.pi, 128, dtype=np.float64)
    inputs = np.column_stack(
        (
            np.sin(phase),
            np.cos(phase),
            np.sin(2 * phase),
            np.cos(2 * phase),
        )
    )
    structured_targets = np.column_stack(
        (
            1.4 * inputs[:, 0] - 0.6 * inputs[:, 3],
            0.8 * inputs[:, 1] + 1.1 * inputs[:, 2],
        )
    )
    if candidate.future_kind == "structured":
        targets = structured_targets
    elif candidate.future_kind == "noise":
        role_seed = sum(
            (index + 1) * ord(character)
            for index, character in enumerate(candidate.role)
        )
        rng = np.random.default_rng(seed * 1009 + role_seed)
        targets = structured_targets[rng.permutation(len(structured_targets))]
    elif candidate.future_kind == "constant":
        targets = np.zeros((len(inputs), 2), dtype=np.float64)
    else:
        raise ValueError(f"unknown future kind: {candidate.future_kind}")
    return inputs, targets


@lru_cache(maxsize=None)
def _default_candidate_epiplexity(candidate: Candidate, seed: int) -> float:
    estimator = ReservoirEpiplexity(
        input_dimension=4,
        width=16,
        ridge=2.0,
        seed=20260723,
    )
    inputs, targets = _future_data(candidate, seed)
    return estimator.score(inputs, targets)


def candidate_epiplexity(
    candidate: Candidate,
    seed: int,
    *,
    estimator: ReservoirEpiplexity | None = None,
) -> float:
    if estimator is None:
        return _default_candidate_epiplexity(candidate, seed)
    inputs, targets = _future_data(candidate, seed)
    return estimator.score(inputs, targets)


def epiplexity_control_audit(
    episodes: Sequence[SyntheticEpisode],
    *,
    scorer: Callable[[Candidate, int], float] = candidate_epiplexity,
) -> EpiplexityControlAudit:
    """Evaluate the fatal epiplexity margin over every registered episode."""

    if not episodes:
        raise ValueError("at least one episode is required")
    role_values: dict[str, list[float]] = {}
    minimum_margin = float("inf")
    worst_seed = -1
    worst_regime = ""
    worst_role = ""
    comparison_count = 0
    for episode in episodes:
        by_role = {candidate.role: candidate for candidate in episode.candidates}
        structured = scorer(by_role["load_bearing"], episode.seed)
        if not isfinite(structured):
            raise ValueError("structured epiplexity score must be finite")
        role_values.setdefault("load_bearing", []).append(structured)
        for role, candidate in by_role.items():
            if role == "load_bearing":
                continue
            control = scorer(candidate, episode.seed)
            if not isfinite(control):
                raise ValueError("control epiplexity score must be finite")
            role_values.setdefault(role, []).append(control)
            margin = structured - control
            if not isfinite(margin):
                raise ValueError("epiplexity margin must be finite")
            comparison_count += 1
            if margin < minimum_margin:
                minimum_margin = margin
                worst_seed = episode.seed
                worst_regime = episode.regime
                worst_role = role
    if comparison_count == 0:
        raise ValueError("at least one epiplexity control comparison is required")
    return EpiplexityControlAudit(
        minimum_margin_bits=minimum_margin,
        worst_seed=worst_seed,
        worst_regime=worst_regime,
        worst_control_role=worst_role,
        role_minimum_bits={
            role: min(values) for role, values in sorted(role_values.items())
        },
        role_maximum_bits={
            role: max(values) for role, values in sorted(role_values.items())
        },
    )


def rank_episode(
    episode: SyntheticEpisode,
    care_weights: Mapping[str, float],
    *,
    warp_strength: float = 0.45,
    nomination_k: int = 3,
    epiplexity_threshold: float = 0.75,
) -> dict[str, EpisodeRanking]:
    graph = episode.graph.concern_warped(care_weights, strength=warp_strength)
    context_restart = {node: 1.0 for node in episode.active_nodes}
    care_restart = {
        anchor: care_weights.get(anchor, 0.0)
        for anchor in episode.care_anchors
    }
    uniform_restart = {node: 1.0 for node in graph.nodes}
    context = personalized_pagerank(graph, context_restart)
    care = personalized_pagerank(graph, care_restart)
    frequency = personalized_pagerank(graph, uniform_restart)
    candidates = [candidate.node for candidate in episode.candidates]
    roles = {candidate.node: candidate.role for candidate in episode.candidates}

    raw_scores = {
        "context": {node: context.scores[node] for node in candidates},
        "care": {node: care.scores[node] for node in candidates},
        "additive": {
            node: context.scores[node] + care.scores[node] for node in candidates
        },
        "coincidence": coincidence_scores(
            context.scores,
            care.scores,
            frequency.scores,
            candidates,
        ),
    }
    rankings: dict[str, EpisodeRanking] = {}
    residual = max(context.l1_residual, care.l1_residual, frequency.l1_residual)
    for policy, scores in raw_scores.items():
        ranked = tuple(sorted(candidates, key=lambda node: (-scores[node], node)))
        rankings[policy] = _ranking_receipt(
            policy,
            ranked,
            episode.load_bearing_node,
            roles,
            residual,
        )

    nominated = rankings["coincidence"].ranked_nodes[:nomination_k]
    verified_scores: dict[str, float] = {}
    by_node = {candidate.node: candidate for candidate in episode.candidates}
    for node in nominated:
        score = candidate_epiplexity(by_node[node], episode.seed)
        if score > epiplexity_threshold:
            verified_scores[node] = score
    verified = tuple(
        sorted(verified_scores, key=lambda node: (-verified_scores[node], node))
    )
    rankings["verified"] = _ranking_receipt(
        "verified",
        verified,
        episode.load_bearing_node,
        roles,
        residual,
    )
    return rankings


def _ranking_receipt(
    policy: str,
    ranked_nodes: tuple[str, ...],
    load_bearing_node: str,
    roles: Mapping[str, str],
    residual: float,
) -> EpisodeRanking:
    try:
        load_rank = ranked_nodes.index(load_bearing_node) + 1
    except ValueError:
        load_rank = None
    return EpisodeRanking(
        policy=policy,
        ranked_nodes=ranked_nodes,
        top_role=roles[ranked_nodes[0]] if ranked_nodes else None,
        load_bearing_rank=load_rank,
        ppr_residual=residual,
    )


def evaluate_episodes(
    episodes: Sequence[SyntheticEpisode],
    care_weights: Mapping[str, float],
) -> EvaluationResult:
    if not episodes:
        raise ValueError("at least one episode is required")
    all_rankings: list[EpisodeRanking] = []
    by_policy: dict[str, list[EpisodeRanking]] = {policy: [] for policy in POLICIES}
    verifier_true_positives = 0
    verifier_predictions = 0
    for episode in episodes:
        rankings = rank_episode(episode, care_weights)
        for policy in POLICIES:
            ranking = rankings[policy]
            by_policy[policy].append(ranking)
            all_rankings.append(ranking)
        verified = rankings["verified"]
        verifier_predictions += len(verified.ranked_nodes)
        verifier_true_positives += int(
            episode.load_bearing_node in verified.ranked_nodes
        )

    count = len(episodes)
    hit_at_1 = {
        policy: sum(ranking.load_bearing_rank == 1 for ranking in rankings) / count
        for policy, rankings in by_policy.items()
    }
    mean_reciprocal_rank = {
        policy: sum(
            0.0 if ranking.load_bearing_rank is None else 1 / ranking.load_bearing_rank
            for ranking in rankings
        )
        / count
        for policy, rankings in by_policy.items()
    }
    distractor_at_1 = {
        policy: sum(
            ranking.top_role in {"alarm", "coincidence_trap"}
            for ranking in rankings
        )
        / count
        for policy, rankings in by_policy.items()
    }
    return EvaluationResult(
        episodes=count,
        hit_at_1=hit_at_1,
        mean_reciprocal_rank=mean_reciprocal_rank,
        distractor_at_1=distractor_at_1,
        verifier_precision=(
            verifier_true_positives / verifier_predictions
            if verifier_predictions
            else 0.0
        ),
        verifier_recall=verifier_true_positives / count,
        max_ppr_residual=max(ranking.ppr_residual for ranking in all_rankings),
        rankings=tuple(all_rankings),
    )


def learn_care_weights(
    episodes: Sequence[SyntheticEpisode],
    *,
    learning_rate: float = 0.2,
    lower: float = 0.05,
    upper: float = 2.0,
) -> CareLearningResult:
    """Update only the anchor attached to the actually nominated candidate."""

    weights = {anchor: 1.0 for anchor in ANCHORS}
    initial = dict(weights)
    selected_utility: list[float] = []
    selected_load_bearing = 0
    for episode in episodes:
        ranking = rank_episode(episode, weights)["coincidence"]
        selected = ranking.ranked_nodes[0]
        candidate = next(item for item in episode.candidates if item.node == selected)
        selected_utility.append(candidate.utility)
        selected_load_bearing += candidate.role == "load_bearing"
        if candidate.anchor is not None:
            weights[candidate.anchor] = min(
                upper,
                max(
                    lower,
                    weights[candidate.anchor] + learning_rate * candidate.utility,
                ),
            )
    count = len(episodes)
    return CareLearningResult(
        initial_weights=initial,
        learned_weights=weights,
        selected_load_bearing_rate=selected_load_bearing / count if count else 0.0,
        mean_selected_utility=sum(selected_utility) / count if count else 0.0,
    )
