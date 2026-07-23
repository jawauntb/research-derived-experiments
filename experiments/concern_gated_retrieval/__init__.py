"""Concern-gated off-context retrieval experiment.

The package contains a deterministic synthetic benchmark for testing whether
two-sided graph diffusion can nominate facts that are jointly close to active
context and persistent concern, followed by a bounded-observer epiplexity
check on goal-conditioned reachable futures.
"""

from experiments.concern_gated_retrieval.benchmark import (
    CareLearningResult,
    EpiplexityControlAudit,
    EvaluationResult,
    SyntheticEpisode,
    evaluate_episodes,
    epiplexity_control_audit,
    generate_episodes,
    learn_care_weights,
)
from experiments.concern_gated_retrieval.epiplexity import ReservoirEpiplexity
from experiments.concern_gated_retrieval.graph import (
    PPRResult,
    WeightedGraph,
    coincidence_scores,
    personalized_pagerank,
)

__all__ = [
    "CareLearningResult",
    "EpiplexityControlAudit",
    "EvaluationResult",
    "PPRResult",
    "ReservoirEpiplexity",
    "SyntheticEpisode",
    "WeightedGraph",
    "coincidence_scores",
    "evaluate_episodes",
    "epiplexity_control_audit",
    "generate_episodes",
    "learn_care_weights",
    "personalized_pagerank",
]
