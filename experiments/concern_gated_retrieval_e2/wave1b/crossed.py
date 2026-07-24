"""COGR-E2b Wave 1b crossed-factorial orchestrator (3 x 3 x 3 = 27 cells).

This module is the per-cell runner for the Wave 1b crossed-factorial
confirmation preregistered in
``experiments/concern_gated_retrieval_e2/wave1b/PREREGISTRATION.md`` §5.

Axes
----

* **Geometry** ∈ ``{LEARNED, FREQ_MATCHED_RANDOM, ORACLE_WITHHELD}``.
  - ``LEARNED`` — Wave 1b's :func:`~experiments.concern_gated_retrieval_e2.wave1b.learned_geometry.learn_graph`
    over the current episode's policy-visible history (context ∪ candidates),
    audit-clean by construction.
  - ``FREQ_MATCHED_RANDOM`` —
    :func:`~experiments.concern_gated_retrieval_e2.wave1b.random_geometry.build_freq_matched_random_graph`
    over the same reference learned graph. Degree-preserving null.
  - ``ORACLE_WITHHELD`` —
    :func:`~experiments.concern_gated_retrieval_e2.wave1b.oracle_geometry.build_oracle_geometry`.
    Evaluator-side ceiling; refused by
    :func:`~experiments.concern_gated_retrieval_e2.wave1b.oracle_geometry.promotion_admit_geometry`.

* **Concern** ∈ ``{FROZEN_WRONG, ONLINE_LEARNED, ORACLE}``.
  - ``FROZEN_WRONG`` — the Wave 0 adversarially wrong prior held fixed
    across seeds. Policy-visible (only ``EpisodeContext.care_anchors``).
  - ``ONLINE_LEARNED`` — start from ``FROZEN_WRONG`` and apply the
    single-receipt confirmatory-mode IPS mirror-descent step between
    seeds. Delegates to
    :func:`experiments.concern_gated_retrieval_e2.wave1a.modal_l4_sweep._apply_online_update`
    so no Wave 1a file is edited.
  - ``ORACLE`` — a high-weight prior on every answer-key node and
    :data:`_ORACLE_CONCERN_BASELINE` on every other candidate. Evaluator-side;
    the ceiling flag :data:`~experiments.concern_gated_retrieval_e2.wave0.baselines.CEILING_MARKER`
    is set on :func:`build_oracle_concern` so
    :func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.promotion_admit`
    refuses it.

* **Family** ∈ ``{delayed_commitments, maintenance_fault, resource_constrained}``.
  Every seed is dispatched to the corresponding
  ``wave1b.families.*_v2`` generator; the ``bucket`` is fixed to
  :class:`~experiments.concern_gated_retrieval_e2.wave0.template_split.TemplateBucket.CONFIRMATION`
  because Wave 1b's confirmatory sweep runs on confirmatory seeds only
  (``PREREGISTRATION.md`` §5).

3 × 3 × 3 = **27 cells**. Each cell runs N=300 seeds paired within the
family's slice of the Wave 0 confirmatory seed range
``[200000, 201999]``.

Per-cell workflow
-----------------

For each seed in the cell's slice:

1. Generate the sealed :class:`EpisodeSpec` (evaluator-side).
2. Wrap it in :class:`SealedEnvironment` and observe once.
3. Build the geometry graph (per-episode) and warp by the running
   concern prior via
   :func:`~experiments.concern_gated_retrieval_e2.wave0.graph_learn.apply_concern_warp`.
4. Rank candidates by PPR score from the context restart, pick the
   top-``budget`` deterministically.
5. Submit the choice through :class:`SealedEnvironment.evaluate` **once**.
   The runner records the call count on
   :attr:`CellRow.sealed_env_evaluate_calls` so downstream receipts can
   regression-check the single-shot invariant.
6. For ``ONLINE_LEARNED``, apply the single-receipt confirmatory-mode
   IPS update via
   :func:`_apply_online_update` on the running concern.

Anti-leakage
------------

* :func:`run_cell` never reaches into
  :attr:`EpisodeSpec.role`, :attr:`EpisodeSpec.utility`, or
  :attr:`EpisodeSpec._answer_key` on the policy path. The two
  evaluator-side factories (:func:`build_oracle_concern`,
  :func:`~experiments.concern_gated_retrieval_e2.wave1b.oracle_geometry.build_oracle_geometry`)
  do dereference sealed fields intentionally and are flagged
  ``is_ceiling_only`` so :func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.promotion_admit`
  and :func:`~experiments.concern_gated_retrieval_e2.wave1b.oracle_geometry.promotion_admit_geometry`
  refuse them.
* Cells whose concern axis is ``ORACLE`` or whose geometry axis is
  ``ORACLE_WITHHELD`` are diagnostic ceilings. :func:`refuse_promotion`
  raises :class:`~experiments.concern_gated_retrieval_e2.wave0.baselines.PromotionRefused`
  when asked to admit such a cell.
* Per-episode nomination callables pass
  :meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.assert_clean`.

Reuse boundary
--------------

Wave 0 and Wave 1a modules are imported (never edited):

* ``wave0.sealed_env`` — sealed environment, contexts, outcomes, and
  audit.
* ``wave0.graph_learn`` — :func:`apply_concern_warp`.
* ``wave0.baselines`` — the :data:`CEILING_MARKER` attribute and the
  :func:`promotion_admit` / :class:`PromotionRefused` pair.
* ``wave0.concern_update`` — :class:`LoggedProbePolicy`, :class:`ProbeReceipt`,
  the poisoning-guard defaults.
* ``wave1a.modal_l4_sweep._apply_online_update`` — the single-receipt
  confirmatory-mode IPS/DR step. Reimplemented as
  :func:`_apply_online_update_step` in this module (byte-identical
  math) so importing this module does not require the Modal SDK; the
  wave1a original is authoritative and any change here must be mirrored.
* ``wave1b.learned_geometry`` — the LEARNED-geometry learner.
* ``wave1b.random_geometry`` — the FREQ_MATCHED_RANDOM null.
* ``wave1b.oracle_geometry`` — the ORACLE_WITHHELD ceiling.
* ``wave1b.families.*_v2`` — the v2 family generators.

Wave 1b scope
-------------

This orchestrator CAN reject L1 or L2 (see the PREREGISTRATION.md §9
fatal gates). It CANNOT establish semantic meaning, selfhood, or an L3
transferable retrieval principle; those are Wave 3+ objects.

The L1 gate is scored on cells with ``concern == FROZEN_WRONG`` and
``geometry ∈ {LEARNED, FREQ_MATCHED_RANDOM, ORACLE_WITHHELD}``. The L2
gate is scored on cells with ``concern == ONLINE_LEARNED`` and
``geometry == LEARNED``. Verdicts are issued **separately**.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Final, Mapping, Sequence

from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    personalized_pagerank,
)
from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    CEILING_MARKER,
    PromotionRefused,
)
from experiments.concern_gated_retrieval_e2.wave0.concern_update import (
    DEFAULT_EPSILON,
    DEFAULT_ETA,
    DEFAULT_MAX_SOURCE_INFLUENCE,
    DEFAULT_WEIGHT_CLIP,
    LoggedProbePolicy,
    NominationPolicy,
    ProbeReceipt,
)
from experiments.concern_gated_retrieval_e2.wave0.graph_learn import (
    apply_concern_warp,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
    IntegrityAudit,
    RetrievalChoice,
    SealedEnvironment,
    SealedOutcome,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.families import (
    delayed_commitments_v2,
    maintenance_fault_v2,
    resource_constrained_v2,
)
from experiments.concern_gated_retrieval_e2.wave1b.learned_geometry import (
    EpisodeHistory,
    HYBRID,
    HistoryEpisode,
    LearnableFeatureSpec,
    learn_graph,
)
from experiments.concern_gated_retrieval_e2.wave1b.oracle_geometry import (
    build_oracle_geometry,
)
from experiments.concern_gated_retrieval_e2.wave1b.random_geometry import (
    build_freq_matched_random_graph,
)


__all__ = [
    "CONCERN_AXIS",
    "CONCERN_FROZEN_WRONG",
    "CONCERN_ONLINE_LEARNED",
    "CONCERN_ORACLE",
    "CellResult",
    "CellRow",
    "CellSpec",
    "DEFAULT_LEARNED_FEATURE_SPEC",
    "DEFAULT_SEEDS_PER_CELL",
    "FAMILY_AXIS",
    "FAMILY_DELAYED",
    "FAMILY_MAINTENANCE",
    "FAMILY_RESOURCE",
    "FAMILY_SEED_RANGES",
    "GEOMETRY_AXIS",
    "GEOM_FREQ_MATCHED_RANDOM",
    "GEOM_LEARNED",
    "GEOM_ORACLE_WITHHELD",
    "build_all_cells",
    "build_oracle_concern",
    "intervene_on_edge",
    "refuse_promotion",
    "run_cell",
]


# --------------------------------------------------------------------------- #
# Axis constants
# --------------------------------------------------------------------------- #


GEOM_LEARNED: Final[str] = "LEARNED"
GEOM_FREQ_MATCHED_RANDOM: Final[str] = "FREQ_MATCHED_RANDOM"
GEOM_ORACLE_WITHHELD: Final[str] = "ORACLE_WITHHELD"

GEOMETRY_AXIS: Final[tuple[str, ...]] = (
    GEOM_LEARNED,
    GEOM_FREQ_MATCHED_RANDOM,
    GEOM_ORACLE_WITHHELD,
)


CONCERN_FROZEN_WRONG: Final[str] = "FROZEN_WRONG"
CONCERN_ONLINE_LEARNED: Final[str] = "ONLINE_LEARNED"
CONCERN_ORACLE: Final[str] = "ORACLE"

CONCERN_AXIS: Final[tuple[str, ...]] = (
    CONCERN_FROZEN_WRONG,
    CONCERN_ONLINE_LEARNED,
    CONCERN_ORACLE,
)


FAMILY_DELAYED: Final[str] = "delayed_commitments"
FAMILY_MAINTENANCE: Final[str] = "maintenance_fault"
FAMILY_RESOURCE: Final[str] = "resource_constrained"

FAMILY_AXIS: Final[tuple[str, ...]] = (
    FAMILY_DELAYED,
    FAMILY_MAINTENANCE,
    FAMILY_RESOURCE,
)


#: Per-family confirmatory seed slices for the 3 x 3 x 3 crossed factorial.
#: Aligned with Wave 1a's ``PREREGISTRATION.md`` §7 slice for
#: ``delayed_commitments`` and ``maintenance_fault``; ``resource_constrained``
#: is aligned to the wave1b v2 family's own confirmatory range
#: (``200600..200899`` — 300 seeds).
FAMILY_SEED_RANGES: Final[Mapping[str, tuple[int, int]]] = MappingProxyType(
    {
        FAMILY_DELAYED: (200_000, 200_299),
        FAMILY_MAINTENANCE: (200_300, 200_599),
        FAMILY_RESOURCE: (200_600, 200_899),
    }
)


#: Default seed count per cell. Wave 1b ``PREREGISTRATION.md`` §5 fixes
#: N = 300 per cell.
DEFAULT_SEEDS_PER_CELL: Final[int] = 300


#: The Wave 1b default LEARNED-geometry feature-family spec.  Uses the
#: :data:`HYBRID` preset (co-occurrence + temporal-lag + learned-embedding)
#: at ``top_k_per_node = 5``.  Kept as a module-level default so the
#: crossed runner and its test suite reference one canonical spec.
DEFAULT_LEARNED_FEATURE_SPEC: Final[LearnableFeatureSpec] = HYBRID


#: Uniform baseline weight the ORACLE-concern factory places on every
#: non-answer candidate. Positive so the mirror-descent update path
#: remains well-posed even if a downstream diagnostic composes it.
_ORACLE_CONCERN_BASELINE: Final[float] = 1e-3


#: High weight the ORACLE-concern factory places on answer-key nodes.
_ORACLE_CONCERN_HIGH: Final[float] = 1.0


#: PPR alpha used by the crossed runner's per-episode ranker. Matches
#: the wave0 baselines convention so an ε → 0 collapse of any
#: perturbed geometry lands on the same PPR fixed point.
_PPR_ALPHA: Final[float] = 0.2
_PPR_TOL: Final[float] = 1e-9


# --------------------------------------------------------------------------- #
# Family generator dispatch
# --------------------------------------------------------------------------- #


_FAMILY_GENERATORS: Final[dict[str, Callable[..., EpisodeSpec]]] = {
    FAMILY_DELAYED: delayed_commitments_v2.generate_episode,
    FAMILY_MAINTENANCE: maintenance_fault_v2.generate_episode,
    FAMILY_RESOURCE: resource_constrained_v2.generate_episode,
}


# --------------------------------------------------------------------------- #
# CellSpec / CellRow / CellResult
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CellSpec:
    """One (geometry, concern, family) cell in the crossed factorial.

    Attributes
    ----------
    geometry:
        One of :data:`GEOMETRY_AXIS`. Selects the reference graph
        construction for the cell.
    concern:
        One of :data:`CONCERN_AXIS`. Selects the initial concern
        factory and — for ``ONLINE_LEARNED`` — whether the runner
        applies the single-receipt confirmatory IPS update between
        seeds.
    family:
        One of :data:`FAMILY_AXIS`. Selects which
        ``wave1b.families.*_v2`` generator produces the cell's sealed
        episodes.
    n_seeds:
        Number of seeds the runner iterates over. Must match
        ``seed_range[1] - seed_range[0] + 1`` so the cell's provenance
        receipt is unambiguous.
    seed_range:
        Inclusive ``(lo, hi)`` seed slice. Must lie inside the family's
        entry in :data:`FAMILY_SEED_RANGES`.
    """

    geometry: str
    concern: str
    family: str
    n_seeds: int
    seed_range: tuple[int, int]

    def __post_init__(self) -> None:
        if self.geometry not in GEOMETRY_AXIS:
            raise ValueError(
                f"geometry must be one of {list(GEOMETRY_AXIS)}; "
                f"got {self.geometry!r}"
            )
        if self.concern not in CONCERN_AXIS:
            raise ValueError(
                f"concern must be one of {list(CONCERN_AXIS)}; "
                f"got {self.concern!r}"
            )
        if self.family not in FAMILY_AXIS:
            raise ValueError(
                f"family must be one of {list(FAMILY_AXIS)}; "
                f"got {self.family!r}"
            )
        if not isinstance(self.n_seeds, int) or isinstance(self.n_seeds, bool):
            raise TypeError("n_seeds must be a non-boolean int")
        if self.n_seeds < 1:
            raise ValueError(f"n_seeds must be >= 1; got {self.n_seeds}")
        if (
            not isinstance(self.seed_range, tuple)
            or len(self.seed_range) != 2
        ):
            raise ValueError(
                "seed_range must be a 2-tuple (lo, hi); got "
                f"{self.seed_range!r}"
            )
        lo, hi = self.seed_range
        if not all(isinstance(x, int) and not isinstance(x, bool) for x in (lo, hi)):
            raise TypeError("seed_range entries must be non-boolean ints")
        if lo > hi:
            raise ValueError(
                f"seed_range lo must be <= hi; got ({lo}, {hi})"
            )
        if (hi - lo + 1) != self.n_seeds:
            raise ValueError(
                "n_seeds must equal seed_range width; got n_seeds="
                f"{self.n_seeds} and seed_range=({lo}, {hi})"
            )
        family_lo, family_hi = FAMILY_SEED_RANGES[self.family]
        if lo < family_lo or hi > family_hi:
            raise ValueError(
                f"seed_range ({lo}, {hi}) is outside the {self.family!r} "
                f"confirmatory slice ({family_lo}, {family_hi})"
            )

    @property
    def cell_id(self) -> str:
        """Stable identifier for the cell — safe for provenance receipts."""
        return (
            f"cogr-wave1b::{self.family}::{self.geometry}::{self.concern}::"
            f"seeds{self.seed_range[0]}-{self.seed_range[1]}"
        )

    def is_ceiling_cell(self) -> bool:
        """``True`` iff either axis level is ceiling-only."""
        return (
            self.geometry == GEOM_ORACLE_WITHHELD
            or self.concern == CONCERN_ORACLE
        )


@dataclass(frozen=True)
class CellRow:
    """One per-seed row inside a :class:`CellResult`.

    Every field is a policy-visible quantity or an aggregate derived
    from :class:`SealedOutcome`. No :attr:`EpisodeSpec.role`,
    :attr:`EpisodeSpec.utility`, or :attr:`EpisodeSpec._answer_key`
    value appears here.
    """

    seed: int
    episode_id: str
    family: str
    budget: int
    selected: tuple[str, ...]
    realized_reward: float
    constraint_preserved: bool
    misretrieval_cost: float
    wall_actions: int
    concern_before: Mapping[str, float]
    concern_after: Mapping[str, float] | None
    receipt: ProbeReceipt
    sealed_env_evaluate_calls: int = 1
    intervention_edge: tuple[str, str] | None = None
    intervention_delta: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.selected, tuple):
            raise TypeError("selected must be a tuple[str, ...]")
        object.__setattr__(
            self, "concern_before", MappingProxyType(dict(self.concern_before))
        )
        if self.concern_after is not None:
            object.__setattr__(
                self,
                "concern_after",
                MappingProxyType(dict(self.concern_after)),
            )


@dataclass(frozen=True)
class CellResult:
    """One cell's frozen receipt.

    Attributes
    ----------
    spec:
        The :class:`CellSpec` this receipt was produced from.
    rows:
        Per-seed :class:`CellRow` receipts, in the seed order the runner
        iterated over.
    aggregate:
        Cell-level statistics — currently ``mean_reward``,
        ``mean_misretrieval_cost``, ``mean_constraint_preserved``. Kept
        as a mapping so downstream analysis can bolt on additional
        summaries without a shape change.
    sealed_env_evaluate_calls:
        Total ``SealedEnvironment.evaluate`` calls across the cell. On
        a well-formed run this equals ``len(rows)`` — one call per
        seed. Recorded so a regression that double-calls the sealed env
        is caught by the tests.
    integrity_audit_passed:
        ``True`` iff :meth:`IntegrityAudit.assert_clean` passed on the
        policy nomination callable used by the cell.
    wall_seconds:
        Cell wall-clock time. Useful when the cell runs on Modal so the
        outer sweep can record per-cell cost against the family.
    """

    spec: CellSpec
    rows: tuple[CellRow, ...]
    aggregate: Mapping[str, float]
    sealed_env_evaluate_calls: int
    integrity_audit_passed: bool
    wall_seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "aggregate", MappingProxyType(dict(self.aggregate))
        )


# --------------------------------------------------------------------------- #
# Concern factories
# --------------------------------------------------------------------------- #


def _frozen_wrong_concern(episode: EpisodeSpec) -> dict[str, float]:
    """Return the Wave 0 wrong prior weights as-is (frozen baseline).

    Policy-visible input; the returned mapping mirrors
    :attr:`EpisodeSpec.care_anchors` which is also on the policy-visible
    :class:`EpisodeContext` view. No sealed field is dereferenced.
    """
    return {
        anchor: max(float(weight), 0.0)
        for anchor, weight in episode.care_anchors.items()
    }


def build_oracle_concern(episode: EpisodeSpec) -> dict[str, float]:
    """Return the evaluator-side ORACLE concern prior.

    **Evaluator-only. CEILING-ONLY.** The body dereferences
    :attr:`EpisodeSpec._answer_key` — a member of
    :attr:`IntegrityAudit.FORBIDDEN_ATTRS` — so any policy callable that
    references this helper fails
    :meth:`IntegrityAudit.assert_clean`. The runtime signal is the
    :data:`CEILING_MARKER` attribute; the Wave 0
    :func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.promotion_admit`
    refuses any callable with the flag set.

    Every answer node receives :data:`_ORACLE_CONCERN_HIGH`; every
    other candidate receives :data:`_ORACLE_CONCERN_BASELINE` so the
    downstream :func:`apply_concern_warp` sees a strictly positive
    prior on every node (the wave0 warp requires non-negative weights
    and a positive-mass restart on downstream PPR).
    """
    answer_key: tuple[str, ...] = episode._answer_key
    answer_set = frozenset(answer_key)
    prior: dict[str, float] = {}
    for node in episode.candidate_nodes:
        prior[node] = _ORACLE_CONCERN_HIGH if node in answer_set else _ORACLE_CONCERN_BASELINE
    for node in episode.context_nodes:
        prior.setdefault(node, _ORACLE_CONCERN_BASELINE)
    return prior


# Flag ORACLE concern factory as CEILING-ONLY. ``promotion_admit`` (imported
# from wave0.baselines) refuses any callable with this attribute truthy.
setattr(build_oracle_concern, CEILING_MARKER, True)


# --------------------------------------------------------------------------- #
# Geometry factories
# --------------------------------------------------------------------------- #


def _learned_geometry_from_context(
    context: EpisodeContext,
    features: LearnableFeatureSpec,
) -> WeightedGraph:
    """Learn a per-episode graph over the policy-visible context view.

    Wraps a single-episode :class:`EpisodeHistory` around
    :func:`~experiments.concern_gated_retrieval_e2.wave1b.learned_geometry.learn_graph`.
    The learner reads only ``context_nodes``, ``candidate_nodes``,
    and ``care_anchors`` — no sealed field. The resulting graph joins
    every visible node pair through the feature families declared by
    ``features`` (co-occurrence, temporal-lag, learned-embedding on the
    default HYBRID preset).
    """
    history = EpisodeHistory(
        episodes=(HistoryEpisode.from_context(context),)
    )
    return learn_graph(history, features)


def _freq_matched_random_from_learned(
    learned_reference: WeightedGraph, seed: int
) -> WeightedGraph:
    """Return the degree-preserving null of ``learned_reference``.

    Delegates to
    :func:`~experiments.concern_gated_retrieval_e2.wave1b.random_geometry.build_freq_matched_random_graph`
    and is a thin shim so the runner has one place to change the seed
    derivation if the wave 1b preregistration §5 replay reserve is ever
    exercised.
    """
    return build_freq_matched_random_graph(learned_reference, seed)


def _make_geometry(
    spec: CellSpec,
    episode: EpisodeSpec,
    context: EpisodeContext,
    features: LearnableFeatureSpec,
) -> WeightedGraph:
    """Return the reference geometry for this ``(spec, episode)`` pair.

    - ``LEARNED``: :func:`_learned_geometry_from_context`.
    - ``FREQ_MATCHED_RANDOM``: null of the learned reference.
    - ``ORACLE_WITHHELD``: evaluator-side oracle geometry (refused for
      promotion).
    """
    if spec.geometry == GEOM_LEARNED:
        return _learned_geometry_from_context(context, features)
    if spec.geometry == GEOM_FREQ_MATCHED_RANDOM:
        learned = _learned_geometry_from_context(context, features)
        return _freq_matched_random_from_learned(learned, episode.seed)
    if spec.geometry == GEOM_ORACLE_WITHHELD:
        return build_oracle_geometry(spec.family, episode.seed)
    # Guarded by CellSpec.__post_init__ — this line is unreachable in
    # well-formed callers.
    raise ValueError(f"unhandled geometry axis: {spec.geometry!r}")


# --------------------------------------------------------------------------- #
# Edge intervention (L1 representation-contribution test)
# --------------------------------------------------------------------------- #


def intervene_on_edge(
    graph: WeightedGraph,
    edge_id: tuple[str, str] | None = None,
) -> WeightedGraph:
    """Remove one edge from ``graph`` and return the resulting graph.

    Used by the L1 representation-contribution test in
    ``PREREGISTRATION.md`` §9 gate G2: the runner scores the sealed
    outcome before and after :func:`intervene_on_edge` on the top-scoring
    edge of the learned graph and reports the signed delta. A learned
    edge that carries genuine representational content must move the
    sealed outcome in the predicted direction (typically downward on
    cells whose task depends on that edge).

    Parameters
    ----------
    graph:
        The :class:`WeightedGraph` to intervene on. Not mutated; a
        new graph is returned.
    edge_id:
        The undirected edge ``(u, v)`` to remove. If ``None``, the
        top-weighted edge is chosen deterministically (ties broken by
        canonical ``(min, max)`` string order). Passing a specific
        edge lets the caller intervene on a policy-selected candidate
        edge; passing ``None`` is the default L1-gate intervention.

    Returns
    -------
    WeightedGraph
        A fresh :class:`WeightedGraph` on the same node set, missing
        the intervened edge. If the edge was not present, the returned
        graph is byte-equivalent to the input (edge subtraction is a
        no-op).

    Raises
    ------
    TypeError
        If ``graph`` is not a :class:`WeightedGraph`.
    ValueError
        If ``edge_id`` is not a 2-tuple of strings.
    """
    if not isinstance(graph, WeightedGraph):
        raise TypeError(
            f"intervene_on_edge requires a WeightedGraph; got "
            f"{type(graph).__name__}"
        )
    edges: list[tuple[str, str, float]] = []
    for u in graph.nodes:
        for v, w in graph.adjacency[u].items():
            if u < v:
                edges.append((u, v, float(w)))
    if edge_id is None:
        if not edges:
            return WeightedGraph.from_edges(graph.nodes, ())
        # Deterministic top-weight selection: descending weight, then
        # canonical (min, max) tuple order on ties.
        ordered = sorted(edges, key=lambda e: (-e[2], (e[0], e[1])))
        target = (ordered[0][0], ordered[0][1])
    else:
        if (
            not isinstance(edge_id, tuple)
            or len(edge_id) != 2
            or not all(isinstance(x, str) for x in edge_id)
        ):
            raise ValueError(
                "edge_id must be a 2-tuple of strings; got "
                f"{edge_id!r}"
            )
        u, v = edge_id
        target = (u, v) if u <= v else (v, u)
    kept: list[tuple[str, str, float]] = []
    for u, v, w in edges:
        if (u, v) == target:
            continue
        kept.append((u, v, w))
    return WeightedGraph.from_edges(graph.nodes, kept)


# --------------------------------------------------------------------------- #
# Ranker / nomination
# --------------------------------------------------------------------------- #


def _positive_care_map(
    concern: Mapping[str, float], graph: WeightedGraph
) -> dict[str, float]:
    """Return a graph-scoped, non-negative concern map safe for warping.

    Filters concern to nodes present in ``graph.nodes`` (apply_concern_warp
    refuses unknown keys) and clamps every weight to ``[0, +∞)``. A key
    absent from the concern map defaults to ``0.0`` inside the warp.
    """
    known = set(graph.nodes)
    filtered: dict[str, float] = {}
    for node, weight in concern.items():
        if node not in known:
            continue
        w = max(float(weight), 0.0)
        if w > 0.0:
            filtered[node] = w
    return filtered


def _restart_distribution(
    nodes: Sequence[str], graph: WeightedGraph
) -> dict[str, float]:
    """Return a uniform restart over ``nodes`` filtered to ``graph.nodes``."""
    known = set(graph.nodes)
    filtered = [n for n in nodes if n in known]
    if not filtered:
        return {}
    mass = 1.0 / len(filtered)
    restart: dict[str, float] = {}
    for n in filtered:
        restart[n] = restart.get(n, 0.0) + mass
    return restart


def _rank_candidates(
    context: EpisodeContext,
    graph: WeightedGraph,
    concern: Mapping[str, float],
) -> tuple[str, ...]:
    """Return the ordered candidate ranking under (graph, concern).

    Composes :func:`apply_concern_warp` and a personalized-PageRank
    restart from the context nodes (falling back to the candidate set
    when the context restart is empty inside the graph). Ranking is
    descending PPR score; ties are broken by the deterministic node id
    ordering so the receipt is byte-stable.
    """
    care = _positive_care_map(concern, graph)
    warped = apply_concern_warp(graph, care) if care else graph
    restart = _restart_distribution(context.context_nodes, warped)
    if not restart:
        restart = _restart_distribution(context.candidate_nodes, warped)
    if not restart:
        # Fully degenerate — fall back to lexicographic ordering so a
        # downstream consumer still receives a deterministic tuple.
        return tuple(sorted(context.candidate_nodes))
    result = personalized_pagerank(
        warped, restart, alpha=_PPR_ALPHA, tolerance=_PPR_TOL
    )
    scores = {
        node: float(result.scores.get(node, 0.0))
        for node in context.candidate_nodes
    }
    return tuple(
        sorted(context.candidate_nodes, key=lambda n: (-scores[n], n))
    )


def _nomination_from_ranking(
    ranking: tuple[str, ...],
) -> NominationPolicy:
    """Return a NominationPolicy that emits the precomputed ranking.

    The returned callable is a closure over a pre-computed ranked
    tuple; :meth:`IntegrityAudit.assert_clean` accepts it because its
    body reads only ``context.candidate_nodes`` and never dereferences
    a sealed field.
    """
    ranked_snapshot = tuple(ranking)

    def nominate(context: EpisodeContext) -> Sequence[str]:
        # Filter to the context's candidate set so a stale ranking (e.g.
        # from a graph that included non-candidate nodes) never leaks
        # into the LoggedProbePolicy wrapper's out-of-set check.
        cand_set = set(context.candidate_nodes)
        return tuple(node for node in ranked_snapshot if node in cand_set)

    return nominate


# --------------------------------------------------------------------------- #
# Promotion admission
# --------------------------------------------------------------------------- #


def refuse_promotion(spec: CellSpec) -> CellSpec:
    """Return ``spec`` if the cell is legal for promotion; else raise.

    Cells with ``spec.geometry == ORACLE_WITHHELD`` or
    ``spec.concern == ORACLE`` are diagnostic ceilings and cannot enter
    the Wave 1b L1 or L2 promotion contest. This function is the shape
    the promotion harness (Wave 1b sibling module) calls before
    admitting a cell.

    Raises :class:`PromotionRefused` with a stable message shape so
    downstream receipts can regex-match on it.
    """
    if not isinstance(spec, CellSpec):
        raise TypeError(
            f"refuse_promotion expects a CellSpec; got {type(spec).__name__}"
        )
    if spec.is_ceiling_cell():
        raise PromotionRefused(
            f"cell {spec.cell_id!r} contains a ceiling axis level "
            f"(geometry={spec.geometry!r}, concern={spec.concern!r}) and "
            "cannot enter a Wave 1b L1 or L2 promotion contest; see "
            "wave1b/PREREGISTRATION.md §5 (crossed factorial) and §9 "
            "(fatal gates)."
        )
    return spec


# --------------------------------------------------------------------------- #
# Cell builder
# --------------------------------------------------------------------------- #


def build_all_cells(
    n_seeds: int = DEFAULT_SEEDS_PER_CELL,
) -> tuple[CellSpec, ...]:
    """Return the 3 x 3 x 3 = 27 cell plan.

    Every ``(geometry, concern, family)`` triple is instantiated with
    the family's confirmatory seed slice from :data:`FAMILY_SEED_RANGES`
    truncated to ``n_seeds``. The default ``n_seeds`` is
    :data:`DEFAULT_SEEDS_PER_CELL` (300); test callers pass a smaller
    value to exercise the runner on a compact fixture.

    The returned tuple is deterministic — geometry axis outer,
    concern axis middle, family axis inner — so a cell index maps 1:1
    onto its position in the crossed lattice.
    """
    if n_seeds <= 0:
        raise ValueError(f"n_seeds must be positive; got {n_seeds}")
    cells: list[CellSpec] = []
    for geometry in GEOMETRY_AXIS:
        for concern in CONCERN_AXIS:
            for family in FAMILY_AXIS:
                lo, hi = FAMILY_SEED_RANGES[family]
                requested_hi = lo + n_seeds - 1
                if requested_hi > hi:
                    raise ValueError(
                        f"n_seeds={n_seeds} exceeds family "
                        f"{family!r} confirmatory slice width "
                        f"{hi - lo + 1}"
                    )
                cells.append(
                    CellSpec(
                        geometry=geometry,
                        concern=concern,
                        family=family,
                        n_seeds=n_seeds,
                        seed_range=(lo, requested_hi),
                    )
                )
    return tuple(cells)


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #


def _initial_concern(
    spec: CellSpec, episode: EpisodeSpec
) -> dict[str, float]:
    """Return the initial concern prior for the cell's concern axis level.

    For the FROZEN_WRONG and ONLINE_LEARNED cells the returned mapping
    is a copy of the wave0 wrong prior surfaced on
    :attr:`EpisodeContext.care_anchors`. For the ORACLE cell the
    returned mapping is produced by :func:`build_oracle_concern`, which
    is CEILING-ONLY.
    """
    if spec.concern == CONCERN_ORACLE:
        return build_oracle_concern(episode)
    return _frozen_wrong_concern(episode)


def _aggregate(rows: Sequence[CellRow]) -> Mapping[str, float]:
    """Cell-level summary statistics over ``rows``."""
    if not rows:
        return MappingProxyType({})
    n = float(len(rows))
    mean_reward = sum(r.realized_reward for r in rows) / n
    mean_miss = sum(r.misretrieval_cost for r in rows) / n
    frac_constraint = sum(1.0 for r in rows if r.constraint_preserved) / n
    return MappingProxyType(
        {
            "mean_reward": float(mean_reward),
            "mean_misretrieval_cost": float(mean_miss),
            "mean_constraint_preserved": float(frac_constraint),
            "n_rows": float(n),
        }
    )


def _apply_online_update_step(
    prior: Mapping[str, float],
    candidate: str,
    selection_propensity: float,
    realized_reward: float,
    source_id: str,
    estimator: str,
    eta: float,
    max_source_influence: float,
    weight_clip: float,
    dr_baseline: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Single-receipt confirmatory-mode IPS/DR mirror-descent step.

    Mirrors
    :func:`experiments.concern_gated_retrieval_e2.wave1a.modal_l4_sweep._apply_online_update`
    byte-for-byte on the math (IPS: ``delta = r / p``; DR:
    ``delta = (r - m_hat) / p + m_hat`` with per-candidate baseline;
    poisoning-guard scale ``msi / |contribution|``; multiplicative
    mirror-descent step ``w * exp(eta * v)`` clipped to
    ``[0, weight_clip]``). Reimplemented here so importing
    :mod:`crossed` does not require the Modal SDK. The wave1a original
    is authoritative — any math change must be mirrored there and here.

    Wave 0's :func:`update_concern` refuses confirmatory receipts at
    its calibration entry point; ``PREREGISTRATION.md`` §5.2 explicitly
    authorises Wave 1a's confirmatory sweep (and by inheritance the
    Wave 1b crossed runner) to consume confirmatory receipts under the
    concern-update rule, so the identical step is inlined here without
    editing any Wave 0 file.
    """
    if estimator not in ("ips", "dr"):
        raise ValueError(f"estimator must be 'ips' or 'dr'; got {estimator!r}")
    if not math.isfinite(float(eta)) or float(eta) <= 0.0:
        raise ValueError("eta must be finite and positive")
    msi = float(max_source_influence)
    if not math.isfinite(msi) or msi <= 0.0:
        raise ValueError("max_source_influence must be finite and positive")
    wclip = float(weight_clip)
    if not math.isfinite(wclip) or wclip <= 0.0:
        raise ValueError("weight_clip must be finite and positive")
    p = float(selection_propensity)
    if not math.isfinite(p) or not (0.0 < p <= 1.0):
        raise ValueError(
            "selection_propensity must be finite and in (0, 1]; got "
            f"{selection_propensity!r}"
        )

    r = float(realized_reward)
    if estimator == "ips":
        delta = r / p
    else:  # dr
        m_hat = float((dr_baseline or {}).get(candidate, 0.0))
        delta = (r - m_hat) / p + m_hat

    # Single trusted source in the confirmatory sweep — the poisoning
    # guard reduces to clamping this one anchor's per-batch contribution.
    contribution = {candidate: delta / 1.0}
    magnitude = abs(contribution[candidate])
    scale = msi / magnitude if magnitude > msi else 1.0

    aggregated: dict[str, float] = {anchor: 0.0 for anchor in prior}
    if candidate in aggregated:
        aggregated[candidate] += contribution[candidate] * scale

    updated: dict[str, float] = {}
    for anchor, w in prior.items():
        v = aggregated.get(anchor, 0.0)
        w_new = float(w) * math.exp(float(eta) * v)
        if not math.isfinite(w_new):
            w_new = wclip if v > 0 else 0.0
        w_new = max(0.0, min(wclip, w_new))
        updated[anchor] = w_new
    return updated


def _score_choice(
    episode: EpisodeSpec, choice: RetrievalChoice
) -> SealedOutcome:
    """Score a retrieval choice via a fresh single-shot sealed env.

    Used by the L1 edge-intervention diagnostic which needs a second,
    independent sealed evaluation of the (possibly counterfactual)
    intervention choice. The wave0 sealed env's single-shot rule
    forbids re-evaluating an existing environment; instantiating a
    fresh one for the counterfactual is the intended pattern.
    """
    env = SealedEnvironment(episode, mode="confirmatory")
    env.observe(seed=episode.seed)
    return env.evaluate(choice)


def run_cell(
    spec: CellSpec,
    *,
    epsilon: float = DEFAULT_EPSILON,
    features: LearnableFeatureSpec = DEFAULT_LEARNED_FEATURE_SPEC,
    eta: float = DEFAULT_ETA,
    max_source_influence: float = DEFAULT_MAX_SOURCE_INFLUENCE,
    weight_clip: float = DEFAULT_WEIGHT_CLIP,
    intervention_edge_index: int | None = None,
) -> CellResult:
    """Execute all N seeds in ``spec`` and return the frozen cell receipt.

    Parameters
    ----------
    spec:
        The :class:`CellSpec` to run.
    epsilon:
        :class:`LoggedProbePolicy` exploration probability. Defaults to
        :data:`DEFAULT_EPSILON` (0.05).  L2-cell replay may raise this
        up to ``0.10`` under the wave1b PREREGISTRATION.md §11 replay
        knobs; the runner itself does not enforce that cap because it
        is a per-cell decision.
    features:
        The :class:`LearnableFeatureSpec` used when building LEARNED /
        FREQ_MATCHED_RANDOM geometry. Defaults to
        :data:`DEFAULT_LEARNED_FEATURE_SPEC` (HYBRID).
    eta, max_source_influence, weight_clip:
        Concern-update hyperparameters. Passed through to
        :func:`_apply_online_update` on ONLINE_LEARNED cells.
    intervention_edge_index:
        If not ``None``, the runner performs the L1 edge-intervention
        diagnostic on every seed: it removes the ``k``-th top-weighted
        edge from the learned reference graph, re-ranks candidates
        against the intervened geometry, scores a *counterfactual*
        retrieval choice through a fresh sealed environment, and
        records ``intervention_delta`` = ``intervened_reward -
        realized_reward`` on the :class:`CellRow`. Cells whose geometry
        axis is not ``LEARNED`` ignore this argument (the intervention
        target is the learned graph). Passing ``0`` selects the
        top-weighted edge — the wave1b PREREGISTRATION.md §9 G2
        default intervention.

    Returns
    -------
    CellResult
        A frozen receipt whose ``sealed_env_evaluate_calls`` equals
        ``len(rows)`` on a well-formed run.
    """
    if not isinstance(spec, CellSpec):
        raise TypeError(
            f"run_cell requires a CellSpec; got {type(spec).__name__}"
        )
    if not isinstance(features, LearnableFeatureSpec):
        raise TypeError(
            "features must be a LearnableFeatureSpec; got "
            f"{type(features).__name__}"
        )

    start = time.time()

    generator = _FAMILY_GENERATORS[spec.family]
    lo, hi = spec.seed_range

    # Concern state — mutable across seeds when the axis is ONLINE_LEARNED.
    running_concern: dict[str, float] | None = None
    integrity_ok = True
    total_evaluate_calls = 0
    rows: list[CellRow] = []

    for seed in range(lo, hi + 1):
        episode: EpisodeSpec = generator(
            seed=seed, bucket=TemplateBucket.CONFIRMATION
        )

        # Concern-prior resolution for this seed.
        # * FROZEN_WRONG / ORACLE cells rebuild the concern from the
        #   current episode every seed — the prior is a fixed function
        #   of ``episode`` and does not depend on any previous seed.
        # * ONLINE_LEARNED cells carry ``running_concern`` across seeds
        #   and initialise it from the very first episode's care
        #   anchors on seed one.
        if spec.concern == CONCERN_ONLINE_LEARNED:
            if running_concern is None:
                running_concern = _initial_concern(spec, episode)
        else:
            running_concern = _initial_concern(spec, episode)

        # Snapshot the pre-decision (pre-update) prior for the row
        # receipt so ``concern_before`` is unambiguously the prior the
        # ranker consumed and (for L2 cells) the input to the mirror-
        # descent step.
        concern_before: dict[str, float] = dict(running_concern)

        env = SealedEnvironment(episode, mode="confirmatory")
        context = env.observe(seed=seed)

        # Build the reference geometry for this seed.
        geometry: WeightedGraph = _make_geometry(
            spec, episode, context, features
        )

        # Rank candidates under (geometry, concern) — the ranking is a
        # pure function of policy-visible inputs on all non-ceiling
        # cells; ceiling cells consult the ORACLE concern / ORACLE
        # geometry evaluator-side factories and are refused for
        # promotion by :func:`refuse_promotion`.
        ranking = _rank_candidates(context, geometry, concern_before)
        nomination = _nomination_from_ranking(ranking)

        try:
            IntegrityAudit.assert_clean(nomination)
        except Exception:
            integrity_ok = False
            raise

        probe_policy = LoggedProbePolicy(nomination, epsilon=epsilon)
        rng = random.Random(f"cogr-wave1b::probe::{spec.cell_id}::{seed}")
        selected_first, receipt = probe_policy.select(context, rng)

        # Pick top-budget deterministically from the audited ranking,
        # honoring the LoggedProbePolicy's recorded first pick so the
        # receipt's propensity accounting is consistent with the actual
        # first slot the policy chose.
        cand_set = set(context.candidate_nodes)
        remaining = [n for n in ranking if n in cand_set and n != selected_first]
        picks = [selected_first] + remaining[: max(context.budget - 1, 0)]
        selected = tuple(picks)

        decision = RetrievalChoice(selected=selected, wall_actions=1)
        outcome = env.evaluate(decision)
        total_evaluate_calls += 1

        # Optional L1 edge-intervention diagnostic. Runs only on cells
        # whose geometry axis is LEARNED (the intervention target is
        # the learned edge).
        intervention_edge: tuple[str, str] | None = None
        intervention_delta: float | None = None
        if (
            intervention_edge_index is not None
            and spec.geometry == GEOM_LEARNED
        ):
            edge_index = int(intervention_edge_index)
            # Enumerate undirected edges in canonical order to pick the
            # k-th top-weighted one deterministically.
            all_edges: list[tuple[str, str, float]] = []
            for u in geometry.nodes:
                for v, w in geometry.adjacency[u].items():
                    if u < v:
                        all_edges.append((u, v, float(w)))
            ordered = sorted(
                all_edges, key=lambda e: (-e[2], (e[0], e[1]))
            )
            if 0 <= edge_index < len(ordered):
                intervention_edge = (
                    ordered[edge_index][0],
                    ordered[edge_index][1],
                )
                intervened = intervene_on_edge(geometry, intervention_edge)
                new_ranking = _rank_candidates(
                    context, intervened, concern_before
                )
                new_cand_set = set(context.candidate_nodes)
                new_remaining = [
                    n for n in new_ranking if n in new_cand_set
                ]
                new_selected = tuple(new_remaining[: context.budget])
                if new_selected != selected:
                    counter_outcome = _score_choice(
                        episode,
                        RetrievalChoice(
                            selected=new_selected, wall_actions=1
                        ),
                    )
                    intervention_delta = float(
                        counter_outcome.realized_reward
                        - outcome.realized_reward
                    )
                    total_evaluate_calls += 1
                else:
                    intervention_delta = 0.0

        concern_after: Mapping[str, float] | None = None
        if spec.concern == CONCERN_ONLINE_LEARNED:
            updated = _apply_online_update_step(
                prior=concern_before,
                candidate=receipt.candidate,
                selection_propensity=float(receipt.selection_propensity),
                realized_reward=float(outcome.realized_reward),
                source_id=receipt.source_id,
                estimator="ips",
                eta=float(eta),
                max_source_influence=float(max_source_influence),
                weight_clip=float(weight_clip),
            )
            concern_after = dict(updated)
            running_concern = dict(updated)

        rows.append(
            CellRow(
                seed=int(seed),
                episode_id=episode.episode_id,
                family=episode.family,
                budget=int(context.budget),
                selected=selected,
                realized_reward=float(outcome.realized_reward),
                constraint_preserved=bool(outcome.constraint_preserved),
                misretrieval_cost=float(outcome.misretrieval_cost),
                wall_actions=int(outcome.wall_actions),
                concern_before=concern_before,
                concern_after=concern_after,
                receipt=receipt,
                sealed_env_evaluate_calls=1,
                intervention_edge=intervention_edge,
                intervention_delta=intervention_delta,
            )
        )

    wall = float(time.time() - start)
    return CellResult(
        spec=spec,
        rows=tuple(rows),
        aggregate=_aggregate(rows),
        sealed_env_evaluate_calls=total_evaluate_calls,
        integrity_audit_passed=integrity_ok,
        wall_seconds=wall,
    )
