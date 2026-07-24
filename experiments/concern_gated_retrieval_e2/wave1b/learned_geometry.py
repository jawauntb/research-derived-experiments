"""Wave 1b learned graph geometry from PERMITTED policy-visible features.

Wave 1a's LEARNED-geometry arm depended on the Wave 0 fixed-withheld
generator; Wave 1b needs a real learner that can compete against the
frequency-matched-random and oracle-withheld cells on its own merits.
This module supplies that learner. It reads only the
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeContext`
surface — ``context_nodes``, ``candidate_nodes`` (ordered by stream
position: index 0 == most recent), ``care_anchors`` — plus optional
logged sealed outcomes (``realized_reward`` on
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedOutcome`,
which the policy sees on every episode). It **never** reads
``EpisodeSpec.role``, ``EpisodeSpec.utility``, or
``EpisodeSpec._answer_key``; :meth:`IntegrityAudit.assert_clean` pins
that at import time via the test suite.

Feature families
----------------

Four permitted-feature families are supported. Each emits a sparse
weighted edge set (top-K neighbours per node); :func:`learn_graph`
merges the per-family edges into one canonical
:class:`~experiments.concern_gated_retrieval.graph.WeightedGraph`.

* ``co_occurrence`` — count node pairs that co-occur in the visible
  set (``context_nodes ∪ candidate_nodes``). Weighted by a symmetric
  PMI-style normaliser ``count(a,b) / sqrt(count(a) * count(b))`` and
  gated below :attr:`LearnableFeatureSpec.min_cooccurrence_count`.
* ``temporal_lag`` — count pairs at bounded stream-position lag inside
  the same episode's ``candidate_nodes``. Weight decays as
  ``1 / (1 + lag)`` and only pairs with ``lag <=
  LearnableFeatureSpec.temporal_window`` are eligible.
* ``causal_intervention`` — for each ordered pair ``(a, b)`` estimate
  the surface lift ``P(b in candidates | a in context) - P(b in
  candidates)``. Negative-lift entries are dropped so the resulting
  edge weight is non-negative (WeightedGraph.from_edges refuses
  negative weights). This is a purely observational proxy for
  intervention lift — Wave 1b runs no online intervention here — but
  it exposes systematically enriched conditional co-occurrence that
  the co-occurrence family alone smooths away.
* ``learned_embedding`` — assign each node a co-occurrence embedding
  by projecting its visible-set neighbourhood into ``embedding_dim``
  via a deterministic hash-seeded Gaussian random projection. Edge
  weight = max(0, cosine similarity). Because the projection matrix
  is a pure function of ``LearnableFeatureSpec.seed``, the learner is
  byte-deterministic across processes.

Presets
-------

* :data:`MINIMAL_COOC` — co-occurrence only, ``top_k=5``.
* :data:`TEMPORAL_LAG_5` — temporal-lag only, window 5.
* :data:`EMBEDDING_ONLY` — learned embedding only.
* :data:`HYBRID` — the three additive families combined; the
  ``family_weights`` map exposes the per-family multipliers so a
  downstream ablation can zero any one family out. ``HYBRID`` does
  NOT include ``causal_intervention`` by default because that family
  is quadratic in ``|nodes|`` and Wave 1b keeps it as an opt-in
  observational lift rather than a default hybrid ingredient.

Sparsification
--------------

Each family produces per-pair weights over the visible node universe.
:func:`_topk_neighbourhood` retains, for every node, the top-K
neighbours by combined weight; the resulting edge set is the union of
those per-node neighbourhoods. Post-selection ``max_degree`` (default
``2 * top_k_per_node``) is enforced to bound the fan-out contributed
by a single hub node, so the returned graph has bounded degree.

Shuffled-labels control (Wave 1b's first integrity self-test)
-------------------------------------------------------------

Because :func:`learn_graph` is label-blind, the natural anti-leakage
audit is: measure the mean edge-mass placed on each episode's actual
load-bearing node, then permute the load-bearing identity uniformly
across episodes and measure the mean mass under the permutation. If
the ratio is near one (equivalently, the z-score against the shuffle
distribution is small), the learner has no channel through which the
sealed answer could reach the graph. :func:`shuffled_labels_control`
runs the audit and returns a receipt; the audit function is
evaluator-only — its body dereferences ``episode._answer_key`` so
:meth:`IntegrityAudit.assert_clean` refuses any policy callable that
imports it. :func:`learn_graph` and every family learner remain
audit-clean.

Reuse boundary
--------------

Imports frozen Wave 0 primitives
(:class:`~experiments.concern_gated_retrieval.graph.WeightedGraph`,
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeContext`,
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`,
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedOutcome`,
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.LeakageError`)
and never edits them. This module does not import
:mod:`experiments.concern_gated_retrieval_e2.wave0.graph_learn` — Wave
0's fixed-withheld generator is a distinct object supplying the
``ORACLE_WITHHELD`` geometry axis of the E2b crossed factorial.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Mapping, Sequence

from experiments.concern_gated_retrieval.graph import WeightedGraph
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
    LeakageError,
    SealedOutcome,
)


# --------------------------------------------------------------------------- #
# Feature-family registry                                                     #
# --------------------------------------------------------------------------- #


FEATURE_COOCCURRENCE: Final[str] = "co_occurrence"
FEATURE_TEMPORAL_LAG: Final[str] = "temporal_lag"
FEATURE_CAUSAL_INTERVENTION: Final[str] = "causal_intervention"
FEATURE_LEARNED_EMBEDDING: Final[str] = "learned_embedding"


#: Every feature family the learner accepts. :func:`learn_graph` refuses
#: :class:`LearnableFeatureSpec` values that name any other family so a
#: mistyped preset is a loud failure rather than a silent no-op.
FEATURE_FAMILIES: Final[tuple[str, ...]] = (
    FEATURE_COOCCURRENCE,
    FEATURE_TEMPORAL_LAG,
    FEATURE_CAUSAL_INTERVENTION,
    FEATURE_LEARNED_EMBEDDING,
)


# --------------------------------------------------------------------------- #
# HistoryEpisode / EpisodeHistory                                             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class HistoryEpisode:
    """Policy-visible per-episode record used by the graph learner.

    The record intentionally mirrors the
    :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeContext`
    view — ``context_nodes``, ``candidate_nodes``, ``care_anchors``,
    ``budget`` — plus an optional ``realized_reward`` scalar taken from
    the sealed outcome the policy already received. No role labels,
    per-node utility, or answer keys ever appear on this dataclass.

    Notes
    -----
    ``candidate_nodes`` is ordered by ascending stream position: index
    ``0`` is the most recent event (per the Wave 0
    ``info_matched_recency`` convention where ``score = 1 / (1 + i)``).
    The ``temporal_lag`` feature family relies on that convention.
    """

    episode_id: str
    family: str
    seed: int
    context_nodes: tuple[str, ...]
    candidate_nodes: tuple[str, ...]
    care_anchors: Mapping[str, float]
    realized_reward: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.episode_id, str) or not self.episode_id:
            raise ValueError("episode_id must be a non-empty string")
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("family must be a non-empty string")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be a non-boolean int")
        if not isinstance(self.context_nodes, tuple) or not all(
            isinstance(n, str) for n in self.context_nodes
        ):
            raise TypeError("context_nodes must be a tuple[str, ...]")
        if not isinstance(self.candidate_nodes, tuple) or not all(
            isinstance(n, str) for n in self.candidate_nodes
        ):
            raise TypeError("candidate_nodes must be a tuple[str, ...]")
        object.__setattr__(
            self,
            "care_anchors",
            MappingProxyType(dict(self.care_anchors)),
        )

    @classmethod
    def from_context(
        cls,
        context: EpisodeContext,
        *,
        outcome: SealedOutcome | None = None,
    ) -> "HistoryEpisode":
        """Build a :class:`HistoryEpisode` from a policy-visible context.

        ``outcome`` may be the :class:`SealedOutcome` the policy already
        obtained from :meth:`SealedEnvironment.evaluate`; only its
        ``realized_reward`` scalar is copied across so no evaluator-only
        field is ever propagated into the history.
        """
        realized: float | None = None
        if outcome is not None:
            realized = float(outcome.realized_reward)
        return cls(
            episode_id=context.episode_id,
            family=context.family,
            seed=context.seed,
            context_nodes=tuple(context.context_nodes),
            candidate_nodes=tuple(context.candidate_nodes),
            care_anchors=dict(context.care_anchors),
            realized_reward=realized,
        )


@dataclass(frozen=True)
class EpisodeHistory:
    """Immutable sequence of :class:`HistoryEpisode` records."""

    episodes: tuple[HistoryEpisode, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.episodes, tuple):
            raise TypeError("EpisodeHistory.episodes must be a tuple")
        for ep in self.episodes:
            if not isinstance(ep, HistoryEpisode):
                raise TypeError(
                    "EpisodeHistory.episodes entries must be HistoryEpisode "
                    f"instances; got {type(ep).__name__}"
                )

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self.episodes)


# --------------------------------------------------------------------------- #
# LearnableFeatureSpec + presets                                              #
# --------------------------------------------------------------------------- #


#: Default per-node neighbour retention. Kept low so the learned graph
#: is aggressively sparse — Wave 1b's PPR primitive iterates over
#: neighbours per step, so a bounded degree keeps the run cost stable.
DEFAULT_TOP_K_PER_NODE: Final[int] = 5


#: Default max-degree multiplier applied post-sparsification. The
#: learned graph's per-node degree is bounded at
#: ``2 * top_k_per_node``: a node's own top-K plus at most K reverse
#: edges from nodes for which it happens to be a top-K neighbour but
#: which are themselves not in its own top-K.
DEFAULT_MAX_DEGREE_MULTIPLIER: Final[int] = 2


@dataclass(frozen=True)
class LearnableFeatureSpec:
    """Frozen configuration for :func:`learn_graph`.

    ``families`` names the feature families to combine. ``top_k_per_node``
    caps the per-node neighbourhood after combination.
    ``temporal_window`` governs the ``temporal_lag`` decay cutoff.
    ``embedding_dim`` and ``embedding_seed`` control the
    ``learned_embedding`` random projection. ``family_weights`` supplies
    per-family multipliers when combining more than one family;
    unspecified families default to ``1.0``.

    The dataclass is frozen so a spec can be used as a stable receipt key.
    """

    families: tuple[str, ...]
    top_k_per_node: int = DEFAULT_TOP_K_PER_NODE
    temporal_window: int = 5
    embedding_dim: int = 16
    embedding_seed: int = 0
    min_cooccurrence_count: int = 2
    family_weights: Mapping[str, float] = field(default_factory=dict)
    max_degree_multiplier: int = DEFAULT_MAX_DEGREE_MULTIPLIER

    def __post_init__(self) -> None:
        if not isinstance(self.families, tuple) or not self.families:
            raise ValueError(
                "families must be a non-empty tuple of feature family names"
            )
        for name in self.families:
            if name not in FEATURE_FAMILIES:
                raise ValueError(
                    f"unknown feature family: {name!r}; expected one of "
                    f"{list(FEATURE_FAMILIES)}"
                )
        if len(set(self.families)) != len(self.families):
            raise ValueError("families must not contain duplicates")
        if self.top_k_per_node < 1:
            raise ValueError("top_k_per_node must be >= 1")
        if self.temporal_window < 1:
            raise ValueError("temporal_window must be >= 1")
        if self.embedding_dim < 1:
            raise ValueError("embedding_dim must be >= 1")
        if self.min_cooccurrence_count < 1:
            raise ValueError("min_cooccurrence_count must be >= 1")
        if self.max_degree_multiplier < 1:
            raise ValueError("max_degree_multiplier must be >= 1")
        for name, weight in self.family_weights.items():
            if name not in FEATURE_FAMILIES:
                raise ValueError(
                    f"family_weights key {name!r} is not a known feature "
                    "family"
                )
            if not isinstance(weight, (int, float)) or not math.isfinite(weight):
                raise ValueError(
                    "family_weights values must be finite floats"
                )
            if weight < 0:
                raise ValueError(
                    "family_weights values must be non-negative"
                )
        object.__setattr__(
            self,
            "family_weights",
            MappingProxyType(dict(self.family_weights)),
        )


#: Minimal preset — co-occurrence only. The default Wave 1b starting
#: geometry for the LEARNED axis; every other preset adds to it.
MINIMAL_COOC: Final[LearnableFeatureSpec] = LearnableFeatureSpec(
    families=(FEATURE_COOCCURRENCE,),
)


#: Temporal-lag only, window 5. Used by the wave 1b sensitivity study
#: that asks "does bounded co-occurrence alone recover recency
#: structure?"
TEMPORAL_LAG_5: Final[LearnableFeatureSpec] = LearnableFeatureSpec(
    families=(FEATURE_TEMPORAL_LAG,),
    temporal_window=5,
)


#: Learned-embedding only. Used by the wave 1b ablation that isolates
#: the random-projection contribution.
EMBEDDING_ONLY: Final[LearnableFeatureSpec] = LearnableFeatureSpec(
    families=(FEATURE_LEARNED_EMBEDDING,),
)


#: Additive combination of the three cheap families
#: (``co_occurrence``, ``temporal_lag``, ``learned_embedding``).
#: ``causal_intervention`` is left out on purpose because its cost is
#: quadratic in the visible node universe and Wave 1b keeps it as an
#: opt-in observational lift rather than a default hybrid ingredient.
HYBRID: Final[LearnableFeatureSpec] = LearnableFeatureSpec(
    families=(
        FEATURE_COOCCURRENCE,
        FEATURE_TEMPORAL_LAG,
        FEATURE_LEARNED_EMBEDDING,
    ),
)


# --------------------------------------------------------------------------- #
# Public entry point                                                          #
# --------------------------------------------------------------------------- #


def learn_graph(
    history: EpisodeHistory,
    features: LearnableFeatureSpec,
) -> WeightedGraph:
    """Return the sparse learned :class:`WeightedGraph` for a history.

    Anti-leakage
    ------------
    ``learn_graph`` and every family helper it dispatches to consume
    only :class:`HistoryEpisode` fields — which mirror the policy-
    visible :class:`EpisodeContext` view — and never touch the sealed
    :class:`EpisodeSpec` attributes enumerated in
    :attr:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.FORBIDDEN_ATTRS`.
    The wave 1b test suite pins that with
    :meth:`IntegrityAudit.assert_clean(learn_graph)`.

    Determinism
    -----------
    Given the same ``history`` and ``features``, the returned graph is
    byte-identical: node order is ``tuple(sorted(nodes))``; edge order
    is the deterministic output of :func:`_finalize_edges`, and every
    RNG stream is keyed by ``features.embedding_seed`` alone.
    """
    if not isinstance(history, EpisodeHistory):
        raise TypeError(
            "learn_graph requires an EpisodeHistory instance; got "
            f"{type(history).__name__}"
        )
    if not isinstance(features, LearnableFeatureSpec):
        raise TypeError(
            "learn_graph requires a LearnableFeatureSpec instance; got "
            f"{type(features).__name__}"
        )

    nodes = _gather_nodes(history)
    if not nodes:
        return WeightedGraph.from_edges((), ())

    combined: dict[frozenset[str], float] = {}
    for family in features.families:
        family_weight = float(features.family_weights.get(family, 1.0))
        if family_weight <= 0.0:
            continue
        family_edges = _FAMILY_LEARNERS[family](history, features)
        for key, weight in family_edges.items():
            combined[key] = combined.get(key, 0.0) + family_weight * weight

    edge_list = _finalize_edges(
        combined,
        nodes=nodes,
        top_k=features.top_k_per_node,
        max_degree=features.top_k_per_node * features.max_degree_multiplier,
    )
    return WeightedGraph.from_edges(tuple(sorted(nodes)), tuple(edge_list))


# --------------------------------------------------------------------------- #
# Feature-family learners                                                     #
# --------------------------------------------------------------------------- #


def _gather_nodes(history: EpisodeHistory) -> tuple[str, ...]:
    """Return the deterministic sorted tuple of all visible node ids."""
    seen: set[str] = set()
    for ep in history.episodes:
        seen.update(ep.context_nodes)
        seen.update(ep.candidate_nodes)
    return tuple(sorted(seen))


def _visible_nodes(ep: HistoryEpisode) -> tuple[str, ...]:
    """Deduplicated tuple of nodes visible in one episode."""
    return tuple(dict.fromkeys(tuple(ep.context_nodes) + tuple(ep.candidate_nodes)))


def _cooccurrence_edges(
    history: EpisodeHistory,
    features: LearnableFeatureSpec,
) -> dict[frozenset[str], float]:
    """Symmetric normalised co-occurrence over each episode's visible set."""
    counts: dict[str, int] = {}
    pair_counts: dict[frozenset[str], int] = {}
    for ep in history.episodes:
        observed = _visible_nodes(ep)
        for node in observed:
            counts[node] = counts.get(node, 0) + 1
        # Pair enumeration is O(|observed|^2). Wave 1b episodes have
        # |observed| bounded by ~30, so this stays cheap.
        for i in range(len(observed)):
            for j in range(i + 1, len(observed)):
                a, b = observed[i], observed[j]
                if a == b:
                    continue
                key = frozenset((a, b))
                pair_counts[key] = pair_counts.get(key, 0) + 1
    edges: dict[frozenset[str], float] = {}
    for key, cnt in pair_counts.items():
        if cnt < features.min_cooccurrence_count:
            continue
        a, b = tuple(key)
        denom = math.sqrt(max(counts[a], 1) * max(counts[b], 1))
        edges[key] = cnt / denom
    return edges


def _temporal_lag_edges(
    history: EpisodeHistory,
    features: LearnableFeatureSpec,
) -> dict[frozenset[str], float]:
    """Recency-decayed lag co-occurrence inside each episode's stream."""
    window = features.temporal_window
    edges: dict[frozenset[str], float] = {}
    for ep in history.episodes:
        stream = ep.candidate_nodes
        n = len(stream)
        for i in range(n):
            a = stream[i]
            j_max = min(n, i + 1 + window)
            for j in range(i + 1, j_max):
                b = stream[j]
                if a == b:
                    continue
                lag = j - i
                key = frozenset((a, b))
                edges[key] = edges.get(key, 0.0) + 1.0 / (1.0 + lag)
    return edges


def _causal_intervention_edges(
    history: EpisodeHistory,
    features: LearnableFeatureSpec,
) -> dict[frozenset[str], float]:
    """Observational lift ``P(b in candidates | a in context) - P(b in candidates)``.

    This is an OBSERVATIONAL surrogate for intervention lift — the
    learner runs no online intervention here. Negative-lift entries
    are dropped so the resulting edge weight is non-negative, which
    :meth:`WeightedGraph.from_edges` requires.
    """
    total = len(history.episodes)
    if total == 0:
        return {}
    b_in_candidates: dict[str, int] = {}
    a_in_context: dict[str, int] = {}
    ab_joint: dict[tuple[str, str], int] = {}
    for ep in history.episodes:
        cands = frozenset(ep.candidate_nodes)
        ctxs = frozenset(ep.context_nodes)
        for b in cands:
            b_in_candidates[b] = b_in_candidates.get(b, 0) + 1
        for a in ctxs:
            a_in_context[a] = a_in_context.get(a, 0) + 1
        for a in ctxs:
            for b in cands:
                if a == b:
                    continue
                key = (a, b)
                ab_joint[key] = ab_joint.get(key, 0) + 1
    edges: dict[frozenset[str], float] = {}
    for (a, b), joint in ab_joint.items():
        n_a = a_in_context.get(a, 0)
        if n_a <= 0:
            continue
        p_b_given_a = joint / n_a
        p_b = b_in_candidates.get(b, 0) / total
        lift = p_b_given_a - p_b
        if lift <= 0:
            continue
        key = frozenset((a, b))
        # Symmetric merge: keep the maximum of the two directional lifts.
        edges[key] = max(edges.get(key, 0.0), lift)
    return edges


def _learned_embedding_edges(
    history: EpisodeHistory,
    features: LearnableFeatureSpec,
) -> dict[frozenset[str], float]:
    """Cosine similarity of per-node co-occurrence random projections.

    Each node ``a`` has an embedding
        e_a = Σ_b R[b]  for every b co-occurring with a in some episode
    where ``R[b]`` is a ``dim``-dimensional Gaussian vector keyed by
    ``(features.embedding_seed, b)``. The random projection is a pure
    function of the seed and node id, so successive calls with the same
    ``LearnableFeatureSpec`` return byte-identical embeddings even
    across processes.
    """
    nodes = _gather_nodes(history)
    if not nodes:
        return {}
    dim = features.embedding_dim
    proj: dict[str, tuple[float, ...]] = {
        node: _hashed_gaussian_vector(node, features.embedding_seed, dim)
        for node in nodes
    }
    emb: dict[str, list[float]] = {node: [0.0] * dim for node in nodes}
    for ep in history.episodes:
        observed = _visible_nodes(ep)
        for a in observed:
            ea = emb[a]
            for b in observed:
                if a == b:
                    continue
                rb = proj[b]
                for k in range(dim):
                    ea[k] += rb[k]
    norms: dict[str, float] = {}
    for node in nodes:
        ev = emb[node]
        norms[node] = math.sqrt(sum(x * x for x in ev))
    edges: dict[frozenset[str], float] = {}
    sorted_nodes = list(nodes)
    for i, a in enumerate(sorted_nodes):
        na = norms[a]
        if na <= 0.0:
            continue
        ea = emb[a]
        for j in range(i + 1, len(sorted_nodes)):
            b = sorted_nodes[j]
            nb = norms[b]
            if nb <= 0.0:
                continue
            eb = emb[b]
            dot = 0.0
            for k in range(dim):
                dot += ea[k] * eb[k]
            sim = dot / (na * nb)
            if sim <= 0.0:
                continue
            edges[frozenset((a, b))] = sim
    return edges


_FAMILY_LEARNERS = {
    FEATURE_COOCCURRENCE: _cooccurrence_edges,
    FEATURE_TEMPORAL_LAG: _temporal_lag_edges,
    FEATURE_CAUSAL_INTERVENTION: _causal_intervention_edges,
    FEATURE_LEARNED_EMBEDDING: _learned_embedding_edges,
}


def _hashed_gaussian_vector(
    node: str,
    seed: int,
    dim: int,
) -> tuple[float, ...]:
    """Deterministic Gaussian random vector keyed by ``(seed, node)``.

    Uses SHA-256 over ``"cogr-e2-wave1b::embedding::{seed}::{node}"`` to
    seed a :class:`random.Random`, then draws ``dim`` standard-normal
    samples. Two processes with the same ``(seed, node, dim)`` triple
    produce byte-identical vectors.
    """
    digest = hashlib.sha256(
        f"cogr-e2-wave1b::embedding::{seed}::{node}".encode("utf-8")
    ).digest()
    # Random.seed accepts arbitrary bytes; we spread the 256-bit digest
    # over the RNG state so different node ids yield uncorrelated draws.
    rng = random.Random(digest)
    return tuple(rng.gauss(0.0, 1.0) for _ in range(dim))


# --------------------------------------------------------------------------- #
# Sparsification                                                              #
# --------------------------------------------------------------------------- #


def _finalize_edges(
    combined: Mapping[frozenset[str], float],
    *,
    nodes: Sequence[str],
    top_k: int,
    max_degree: int,
) -> list[tuple[str, str, float]]:
    """Return the sparse edge list with top-K neighbourhoods per node.

    The routine is a two-stage funnel:

    1. **Top-K per node.** For every node, order its incident pairs by
       descending weight (ties broken by the neighbour's node id in
       ascending order) and keep the top ``top_k``. The pair is
       emitted into the candidate edge set if it appears in the top-K
       neighbourhood of *either* endpoint.
    2. **Max-degree post-cap.** Walk the surviving edges in deterministic
       order (by descending weight, ties broken lexicographically on
       the sorted pair) and skip an edge if adding it would push either
       endpoint's degree above ``max_degree``. The cap defends against
       a single hub node accumulating more than ``max_degree``
       neighbours through repeated reverse-K appearances.

    Both stages preserve determinism and never inspect anything beyond
    the pair keys and weights.
    """
    if not combined:
        return []
    per_node: dict[str, list[tuple[str, float]]] = {node: [] for node in nodes}
    for key, weight in combined.items():
        a, b = tuple(key)
        # frozenset iteration order is not stable across interpreters;
        # canonicalise so the (a, b) pair name is deterministic.
        if a > b:
            a, b = b, a
        per_node.setdefault(a, []).append((b, weight))
        per_node.setdefault(b, []).append((a, weight))
    candidate_edges: dict[frozenset[str], float] = {}
    for node, neighbours in per_node.items():
        neighbours.sort(key=lambda item: (-item[1], item[0]))
        for other, weight in neighbours[:top_k]:
            candidate_edges[frozenset((node, other))] = weight
    # Deterministic order for the cap walk: descending weight, then
    # canonical (a, b) name for ties.
    ordered = sorted(
        candidate_edges.items(),
        key=lambda item: (
            -item[1],
            sorted(item[0]),
        ),
    )
    degree: dict[str, int] = {node: 0 for node in nodes}
    kept: list[tuple[str, str, float]] = []
    for key, weight in ordered:
        a, b = sorted(key)
        if degree.get(a, 0) >= max_degree:
            continue
        if degree.get(b, 0) >= max_degree:
            continue
        kept.append((a, b, weight))
        degree[a] = degree.get(a, 0) + 1
        degree[b] = degree.get(b, 0) + 1
    return kept


# --------------------------------------------------------------------------- #
# Shuffled-labels integrity self-test (evaluator-only)                        #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ShuffleControlReceipt:
    """Result receipt from :func:`shuffled_labels_control`.

    ``actual_mean_mass`` is the mean edge-mass placed on each episode's
    true load-bearing node by the learned graph. ``shuffle_mean_mass``
    and ``shuffle_std_mass`` describe the null distribution under
    uniform-random per-episode load-bearing selection. ``z_score`` is
    the standardised difference ``(actual - shuffle_mean) /
    shuffle_std`` (denominator clipped to a small floor so a
    degenerate zero-variance shuffle stays finite). ``passed`` is
    ``abs(z_score) <= tolerance``.
    """

    actual_mean_mass: float
    shuffle_mean_mass: float
    shuffle_std_mass: float
    n_shuffles: int
    z_score: float
    tolerance: float
    passed: bool


#: Default z-score tolerance for :func:`shuffled_labels_control`. A
#: label-blind learner is expected to sit within 2.5 sigma of the
#: shuffle null even for modest histories; a wider tolerance would let
#: a mild leak through, a narrower one would spuriously trip on small
#: samples.
DEFAULT_SHUFFLE_TOLERANCE: Final[float] = 2.5


def shuffled_labels_control(
    episodes: Sequence[EpisodeSpec],
    history: EpisodeHistory,
    features: LearnableFeatureSpec,
    *,
    n_shuffles: int = 200,
    seed: int = 0,
    tolerance: float = DEFAULT_SHUFFLE_TOLERANCE,
) -> ShuffleControlReceipt:
    """Return the label-permutation audit receipt for :func:`learn_graph`.

    Evaluator-only. Reads ``episode._answer_key`` on every ``EpisodeSpec``
    in ``episodes`` to identify each episode's load-bearing node. Every
    policy callable whose source imports this function will fail
    :meth:`IntegrityAudit.assert_clean`, exactly as the Wave 1b
    integrity contract requires.

    The audit proceeds in three steps:

    1. **Build the learned graph.** ``learn_graph(history, features)``
       is label-blind by construction.
    2. **Score the actual load-bearing mass.** For each ``episode`` in
       ``episodes`` whose ``episode_id`` matches a
       :class:`HistoryEpisode` in ``history``, sum the incident edge
       weights on ``episode._answer_key[0]`` and average across
       episodes.
    3. **Score the shuffled null.** Repeat step 2 ``n_shuffles`` times,
       each time picking a uniformly random load-bearing node per
       episode from that episode's ``candidate_nodes``. Report
       mean/std/z-score against the null.

    A well-behaved (label-blind) learner sits within ``tolerance``
    standard deviations of the shuffle mean. A learner that has leaked
    the sealed answer key shows up as a large positive z-score.
    """
    if not isinstance(history, EpisodeHistory):
        raise TypeError(
            "shuffled_labels_control requires an EpisodeHistory instance"
        )
    if not isinstance(features, LearnableFeatureSpec):
        raise TypeError(
            "shuffled_labels_control requires a LearnableFeatureSpec instance"
        )
    if n_shuffles < 1:
        raise ValueError("n_shuffles must be >= 1")
    if not (isinstance(tolerance, (int, float)) and math.isfinite(tolerance)):
        raise ValueError("tolerance must be a finite float")

    for ep in episodes:
        if not isinstance(ep, EpisodeSpec):
            raise LeakageError(
                "shuffled_labels_control requires sealed EpisodeSpec "
                "instances (never EpisodeContext); the policy-visible "
                "view does not carry the sealed answer key needed for "
                "the integrity self-test."
            )

    # Evaluator-only sealed-field dereference. Trips IntegrityAudit on
    # any policy callable that imports shuffled_labels_control.
    load_bearing_by_episode: dict[str, str] = {}
    for ep in episodes:
        answer_key = ep._answer_key
        if not answer_key:
            continue
        load_bearing_by_episode[ep.episode_id] = answer_key[0]

    graph = learn_graph(history, features)

    def _mass(node: str) -> float:
        return float(sum(graph.adjacency.get(node, {}).values()))

    matched: list[tuple[HistoryEpisode, str]] = []
    for hist_ep in history.episodes:
        node = load_bearing_by_episode.get(hist_ep.episode_id)
        if node is None:
            continue
        matched.append((hist_ep, node))

    if not matched:
        return ShuffleControlReceipt(
            actual_mean_mass=0.0,
            shuffle_mean_mass=0.0,
            shuffle_std_mass=0.0,
            n_shuffles=int(n_shuffles),
            z_score=0.0,
            tolerance=float(tolerance),
            passed=True,
        )

    actual_mean = sum(_mass(node) for _, node in matched) / len(matched)

    rng = random.Random(
        f"cogr-e2-wave1b::shuffled_labels_control::{seed}"
    )
    shuffle_means: list[float] = []
    for _ in range(int(n_shuffles)):
        total = 0.0
        count = 0
        for hist_ep, _true in matched:
            cands = hist_ep.candidate_nodes
            if not cands:
                continue
            fake = cands[rng.randrange(len(cands))]
            total += _mass(fake)
            count += 1
        if count == 0:
            shuffle_means.append(0.0)
        else:
            shuffle_means.append(total / count)

    mean = sum(shuffle_means) / len(shuffle_means)
    if len(shuffle_means) > 1:
        variance = sum((v - mean) ** 2 for v in shuffle_means) / (
            len(shuffle_means) - 1
        )
    else:
        variance = 0.0
    std = math.sqrt(variance)
    z = (actual_mean - mean) / max(std, 1e-9)
    passed = abs(z) <= float(tolerance)
    return ShuffleControlReceipt(
        actual_mean_mass=float(actual_mean),
        shuffle_mean_mass=float(mean),
        shuffle_std_mass=float(std),
        n_shuffles=int(n_shuffles),
        z_score=float(z),
        tolerance=float(tolerance),
        passed=bool(passed),
    )


__all__ = [
    "DEFAULT_MAX_DEGREE_MULTIPLIER",
    "DEFAULT_SHUFFLE_TOLERANCE",
    "DEFAULT_TOP_K_PER_NODE",
    "EMBEDDING_ONLY",
    "EpisodeHistory",
    "FEATURE_CAUSAL_INTERVENTION",
    "FEATURE_COOCCURRENCE",
    "FEATURE_FAMILIES",
    "FEATURE_LEARNED_EMBEDDING",
    "FEATURE_TEMPORAL_LAG",
    "HistoryEpisode",
    "HYBRID",
    "LearnableFeatureSpec",
    "MINIMAL_COOC",
    "ShuffleControlReceipt",
    "TEMPORAL_LAG_5",
    "learn_graph",
    "shuffled_labels_control",
]
