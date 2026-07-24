"""Wave 1b oracle-withheld geometry — **CEILING-ONLY, refused by harness**.

The Wave 1b crossed factorial (``PREREGISTRATION.md`` §5) sweeps the
geometry axis over three levels:

* ``LEARNED`` — the candidate mechanism's learned graph.
* ``FREQ_MATCHED_RANDOM`` — the matched-budget graph null built by
  :mod:`experiments.concern_gated_retrieval_e2.wave1b.random_geometry`.
* ``ORACLE_WITHHELD`` — this module. An evaluator-side geometry that
  places high-weight edges from every context node directly to every
  answer-key node, so a downstream personalized-PageRank walk from the
  context nodes lands mass on the answers by construction. The oracle
  geometry is a diagnostic ceiling. Any policy composed with it
  measures the headroom above the promotable cells, never their
  promotion candidate.

Anti-leakage — *by design*
--------------------------

:func:`build_oracle_geometry` dereferences
:attr:`EpisodeSpec._answer_key` — a member of
:attr:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.FORBIDDEN_ATTRS`.
That dereference is deliberate: the whole point of an oracle geometry
is that it consults the sealed answer key. Consequently
:meth:`IntegrityAudit.assert_clean` **fails** on this function's
source. That failure is not a bug; it is the compile-time signal that
oracle-geometry callables must never be routed through a policy path.

The runtime signal is :attr:`build_oracle_geometry.is_ceiling_only`
set to ``True`` (using the same :data:`CEILING_MARKER` attribute the
Wave 0 baseline slate uses for :func:`oracle_ceiling`). The promotion
harness — either the reused Wave 0
:func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.promotion_admit`
or the module-local :func:`promotion_admit_geometry` wrapper — refuses
any callable with this attribute truthy, raising
:class:`~experiments.concern_gated_retrieval_e2.wave0.baselines.PromotionRefused`.
That refusal is what keeps the oracle geometry from silently entering
the L1 or L2 gate.

Reuse boundary
--------------

The oracle geometry is built per ``(family, seed)`` from the family
generator that Wave 1b uses in confirmatory rows. Supported families
are the three Wave 1b v2 families
(``delayed_commitments``, ``maintenance_fault``, ``resource_constrained``).
The evaluator loads the sealed :class:`EpisodeSpec` from the matching
family module, reads its context and answer-key fields, and returns a
:class:`WeightedGraph` over the union of ``context_nodes`` and
``candidate_nodes``. The graph is undirected and weighted; the
oracle-weight and background-weight coefficients are frozen module
constants.
"""

from __future__ import annotations

from typing import Callable, Final

from experiments.concern_gated_retrieval.graph import WeightedGraph
from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    CEILING_MARKER,
    PromotionRefused,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.families import (
    delayed_commitments_v2,
    maintenance_fault_v2,
    resource_constrained_v2,
)


#: Weight placed on an oracle edge ``(context_node, answer_node)``. Set
#: generously above the background so a personalized-PageRank walk from
#: the context lands overwhelming mass on the answer nodes. The exact
#: magnitude is not tuned to any promotion threshold — the oracle is
#: refused, so no threshold is being defended.
ORACLE_EDGE_WEIGHT: Final[float] = 5.0


#: Background edge weight placed on a sparse chain over the remaining
#: candidate nodes. The chain keeps the returned graph connected so a
#: downstream PPR consumer receives a well-formed input, without adding
#: enough weight to compete with the oracle edges.
BACKGROUND_EDGE_WEIGHT: Final[float] = 0.01


#: The three Wave 1b family names the oracle geometry accepts. Any
#: other name — including unknown-family typos and Wave 0's frozen
#: family names outside the v2 redesign — raises ``ValueError``.
SUPPORTED_FAMILIES: Final[frozenset[str]] = frozenset(
    {"delayed_commitments", "maintenance_fault", "resource_constrained"}
)


#: Registry mapping family name -> the family module's
#: ``generate_episode`` callable. Populated at import so the runtime
#: dispatch has no per-call lookup cost.
_FAMILY_GENERATORS: Final[dict[str, Callable[..., EpisodeSpec]]] = {
    "delayed_commitments": delayed_commitments_v2.generate_episode,
    "maintenance_fault": maintenance_fault_v2.generate_episode,
    "resource_constrained": resource_constrained_v2.generate_episode,
}


#: Seed-range boundaries for the auto-detected bucket. Kept aligned
#: with the Wave 0 seed partition
#: (``100_000..100_999`` calibration, ``200_000..201_999`` confirmatory)
#: named in ``wave0/PREREGISTRATION.md`` §7 and inherited by the Wave
#: 1b PREREGISTRATION.md §5 sample plan.
_CALIBRATION_SEED_MIN: Final[int] = 100_000
_CALIBRATION_SEED_MAX: Final[int] = 100_999
_CONFIRMATORY_SEED_MIN: Final[int] = 200_000
_CONFIRMATORY_SEED_MAX: Final[int] = 201_999


def _classify_bucket(seed: int) -> TemplateBucket:
    """Auto-classify a seed into the calibration or confirmatory bucket.

    Wave 1b confirmatory seeds live in ``[200_000, 201_999]`` and Wave
    0 calibration seeds live in ``[100_000, 100_999]``. Seeds outside
    both windows raise ``ValueError`` — the caller must use a
    Wave-partitioned seed even for the oracle diagnostic so
    calibration-only receipts never see confirmatory oracle rows and
    vice-versa.
    """
    if _CALIBRATION_SEED_MIN <= seed <= _CALIBRATION_SEED_MAX:
        return TemplateBucket.CALIBRATION
    if _CONFIRMATORY_SEED_MIN <= seed <= _CONFIRMATORY_SEED_MAX:
        return TemplateBucket.CONFIRMATION
    raise ValueError(
        f"seed {seed} is outside both the calibration "
        f"[{_CALIBRATION_SEED_MIN}, {_CALIBRATION_SEED_MAX}] and "
        f"confirmatory [{_CONFIRMATORY_SEED_MIN}, {_CONFIRMATORY_SEED_MAX}] "
        "windows; oracle geometry refuses to auto-detect the bucket"
    )


def build_oracle_geometry(
    family: str,
    seed: int,
    *,
    oracle_weight: float = ORACLE_EDGE_WEIGHT,
    background_weight: float = BACKGROUND_EDGE_WEIGHT,
) -> WeightedGraph:
    """Return the CEILING-ONLY oracle-withheld graph for ``(family, seed)``.

    Evaluator-side. This function is **refused by the promotion
    harness** — see :func:`promotion_admit_geometry` and
    :attr:`is_ceiling_only`.

    The returned :class:`WeightedGraph` covers the union of the sealed
    episode's ``context_nodes`` and ``candidate_nodes``. It places one
    high-weight edge between every context node and every answer-key
    node (``oracle_weight``), plus a sparse background chain over the
    remaining candidate nodes (``background_weight``) so the resulting
    graph is connected without diluting the oracle signal.

    Parameters
    ----------
    family:
        One of :data:`SUPPORTED_FAMILIES`. Any other name raises
        ``ValueError``.
    seed:
        Wave 1b confirmatory or Wave 0 calibration seed. Auto-classified
        into a :class:`TemplateBucket`. Family-specific seed-range
        restrictions still apply (the v2 family modules validate their
        own accepted ranges), so an out-of-range seed for the chosen
        family raises the family module's ``ValueError`` unchanged.
    oracle_weight:
        Weight placed on context->answer edges. Default
        :data:`ORACLE_EDGE_WEIGHT`. Kept as a keyword override so a
        diagnostic can dial the oracle signal down for a sensitivity
        study; the default is what enters the L1 ceiling receipt.
    background_weight:
        Weight placed on chain edges over non-answer candidate nodes.
        Default :data:`BACKGROUND_EDGE_WEIGHT`. Must be strictly
        positive so :meth:`WeightedGraph.from_edges` keeps the edge.

    Returns
    -------
    WeightedGraph
        The oracle geometry over the episode's context + candidate
        nodes. Every node appears in a stable order (context first,
        then candidates), so two calls with the same
        ``(family, seed, oracle_weight, background_weight)`` return
        byte-identical graphs.

    Raises
    ------
    ValueError
        If ``family`` is unknown, if ``seed`` sits outside the union of
        the calibration and confirmatory windows, or if the family's
        seed-range validator rejects the seed. Also raised for
        non-positive weights.
    TypeError
        If ``seed`` is not an ``int`` (or is a ``bool``).

    Anti-leakage
    ------------
    The body dereferences :attr:`EpisodeSpec._answer_key` — a sealed
    field enumerated in :attr:`IntegrityAudit.FORBIDDEN_ATTRS`. That
    reference is what makes the function evaluator-only and what
    causes :meth:`IntegrityAudit.assert_clean` to flag it. The
    function is additionally flagged CEILING-ONLY at import via
    :data:`CEILING_MARKER`, so :func:`promotion_admit_geometry`
    (and Wave 0's :func:`promotion_admit`) refuse it before it can
    reach a promotion contest.
    """
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(
            f"unknown family {family!r}; oracle geometry supports "
            f"{sorted(SUPPORTED_FAMILIES)}"
        )
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be int (not bool)")
    if not oracle_weight > 0:
        raise ValueError("oracle_weight must be positive")
    if not background_weight > 0:
        raise ValueError("background_weight must be positive")

    bucket = _classify_bucket(seed)
    generator = _FAMILY_GENERATORS[family]
    episode: EpisodeSpec = generator(seed=seed, bucket=bucket)

    # Evaluator-only sealed-field dereference. IntegrityAudit.assert_clean
    # will flag this line and refuse any policy that references
    # build_oracle_geometry — see the module docstring.
    answer_key: tuple[str, ...] = episode._answer_key

    context_nodes = tuple(episode.context_nodes)
    candidate_nodes = tuple(episode.candidate_nodes)

    # Deduplicate while preserving order: context first, then any
    # candidate not already in context.
    seen: set[str] = set()
    nodes: list[str] = []
    for node in (*context_nodes, *candidate_nodes):
        if node in seen:
            continue
        seen.add(node)
        nodes.append(node)

    edges: list[tuple[str, str, float]] = []

    # Oracle edges: every context node to every answer node. Skip
    # self-loops (would raise in WeightedGraph.from_edges) and skip
    # answer nodes that (defensively) do not appear in the candidate
    # set — the sealed contract guarantees they do, but we filter for
    # robustness.
    answer_in_nodes = tuple(a for a in answer_key if a in seen)
    for ctx in context_nodes:
        for ans in answer_in_nodes:
            if ctx == ans:
                continue
            edges.append((ctx, ans, float(oracle_weight)))

    # Background chain over non-answer candidate nodes to keep the
    # graph connected. A sparse chain gives PPR a walking surface
    # outside the oracle-directed cluster without diluting the answer
    # mass.
    non_answer_candidates = [c for c in candidate_nodes if c not in answer_key]
    for i in range(len(non_answer_candidates) - 1):
        left = non_answer_candidates[i]
        right = non_answer_candidates[i + 1]
        if left == right:
            continue
        edges.append((left, right, float(background_weight)))

    # Bridge from the chain into the oracle cluster so the graph is
    # connected end-to-end. If there is at least one non-answer
    # candidate and at least one answer node, add a background edge
    # from the first non-answer candidate to the first answer node.
    if non_answer_candidates and answer_in_nodes:
        edges.append(
            (non_answer_candidates[0], answer_in_nodes[0], float(background_weight))
        )

    return WeightedGraph.from_edges(tuple(nodes), tuple(edges))


# Flag the oracle geometry as CEILING-ONLY. Setting this attribute is
# the affordance the promotion harness uses to refuse a callable —
# identical to the flag Wave 0 uses on
# :func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.oracle_ceiling`.
setattr(build_oracle_geometry, CEILING_MARKER, True)


def promotion_admit_geometry(
    geometry_builder: Callable[..., WeightedGraph],
) -> Callable[..., WeightedGraph]:
    """Return ``geometry_builder`` if it is legal for promotion; else raise.

    Refuses any callable whose :data:`CEILING_MARKER` attribute is
    truthy. The refusal message is stable so downstream receipts can
    regex-match on it. Semantically identical to the Wave 0
    :func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.promotion_admit`
    baseline-side harness; kept here as a geometry-typed wrapper so
    callers do not need to import baseline machinery just to admit a
    geometry function.
    """
    if getattr(geometry_builder, CEILING_MARKER, False):
        raise PromotionRefused(
            f"geometry builder "
            f"{getattr(geometry_builder, '__name__', geometry_builder)!r} "
            "is flagged CEILING-ONLY and cannot enter a Wave 1b L1 or L2 "
            "promotion contest; see wave1b/PREREGISTRATION.md §5 and the "
            "ORACLE_WITHHELD level of the geometry axis."
        )
    return geometry_builder


__all__ = [
    "BACKGROUND_EDGE_WEIGHT",
    "ORACLE_EDGE_WEIGHT",
    "SUPPORTED_FAMILIES",
    "build_oracle_geometry",
    "promotion_admit_geometry",
]
