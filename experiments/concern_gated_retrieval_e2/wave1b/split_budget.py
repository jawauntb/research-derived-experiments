"""Wave 1b ``k_split_care_uncertain_audit`` split-budget ABLATION baseline.

This module implements the labelled split-budget ablation named in
Wave 1b ``PREREGISTRATION.md`` §8 and the Spencer echo-chamber design
correction #5. It is EXPLICITLY an ablation — **not** the promotion
path. L1 promotion is scored on the pure candidate mechanism
(``wave0.baselines.multiplicative_ppr``); the split-budget receipt is
reported alongside so a reviewer can rule out "naive uncertainty +
audit exploration" as the source of any observed Wave 1b gain.

The 70/20/10 default is not theoretically privileged — it is a
starting split. The module exposes :data:`SPLITS_TO_REPORT` = three
grid points (70/20/10, 50/30/20, 80/10/10) so the sensitivity of the
ablation to the split choice is visible in the receipt.

Composition
-----------

For a retrieval budget ``k`` and a :class:`SplitFractions` triple
``(care, uncertain, audit)``:

    k_care      = round(care      * k)
    k_uncertain = round(uncertain * k)
    k_audit     = k - k_care - k_uncertain      # (must be >= 1)

The three slots are filled by disjoint mechanisms:

* **k_care** slots come from
  :func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.multiplicative_ppr`
  — the Wave 0 candidate mechanism.
* **k_uncertain** slots come from :func:`ensemble_variance_ranker`,
  which perturbs the sealed context's ``care_anchors`` with
  deterministic ε-scaled Gaussian noise, runs concern-warped PPR for
  each perturbation, and ranks candidates by the per-candidate PPR-
  score variance across the ensemble. Candidates already chosen for
  the ``k_care`` slot are skipped so the three slots remain disjoint.
* **k_audit** slots come from a deterministic weighted-random
  independent inverse-frequency sample (weights are drawn from the
  same rarity table Wave 0's ``freq_only`` baseline uses).

The returned tuple is the disjoint concatenation in the order
``(care, uncertain, audit)`` and never contains duplicates.

Anti-leakage
------------

Every helper in this module consumes only the policy-visible
:class:`EpisodeContext` view. No sealed ``role``, ``utility``, or
``_answer_key`` attribute is dereferenced. The module is intended to
pass :meth:`IntegrityAudit.assert_clean` on the top-level ``k_split``
entry point and on every helper it dispatches to.
"""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from typing import Final, Iterable, Sequence

from experiments.concern_gated_retrieval.graph import (
    WeightedGraph,
    personalized_pagerank,
)
from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    RankFn,
    multiplicative_ppr,
)
from experiments.concern_gated_retrieval_e2.wave0.graph_learn import (
    FAMILY_NAMES as _WAVE0_FAMILY_NAMES,
    apply_concern_warp,
    build_withheld_graph,
    rarity_scores,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import EpisodeContext


# --------------------------------------------------------------------------- #
# SplitFractions                                                              #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SplitFractions:
    """Fractional split of the retrieval budget across the three slots.

    ``care + uncertain + audit`` must sum to ``1.0`` (within a
    ``1e-9`` absolute tolerance) and each fraction must lie in
    ``[0.0, 1.0]``. The dataclass is frozen so a split can be used as
    a stable receipt key.
    """

    care: float
    uncertain: float
    audit: float

    def __post_init__(self) -> None:
        for name, value in (
            ("care", self.care),
            ("uncertain", self.uncertain),
            ("audit", self.audit),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(
                    f"SplitFractions.{name} must be a non-boolean float; got "
                    f"{type(value).__name__}"
                )
            fvalue = float(value)
            if not math.isfinite(fvalue):
                raise ValueError(
                    f"SplitFractions.{name} must be finite; got {value!r}"
                )
            if fvalue < 0.0 or fvalue > 1.0:
                raise ValueError(
                    f"SplitFractions.{name} must lie in [0, 1]; got {value!r}"
                )
        total = float(self.care) + float(self.uncertain) + float(self.audit)
        if not math.isclose(total, 1.0, abs_tol=1e-9):
            raise ValueError(
                "SplitFractions must sum to 1.0 (within 1e-9); "
                f"got care={self.care} + uncertain={self.uncertain} + "
                f"audit={self.audit} = {total}"
            )


#: The three reported split grid points. Wave 1b PROVENANCE §8 records
#: the k_split receipt for each entry so the ablation's sensitivity to
#: the split choice is visible.
SPLITS_TO_REPORT: Final[tuple[SplitFractions, ...]] = (
    SplitFractions(0.70, 0.20, 0.10),
    SplitFractions(0.50, 0.30, 0.20),
    SplitFractions(0.80, 0.10, 0.10),
)


# --------------------------------------------------------------------------- #
# Deterministic salt / tie-break helpers                                      #
# --------------------------------------------------------------------------- #


def _episode_salt(context: EpisodeContext, purpose: str) -> str:
    """Deterministic per-episode / per-purpose salt string."""
    return (
        f"cogr-wave1b-split::{purpose}::{context.family}::{context.seed}::"
        f"{context.episode_id}"
    )


def _tie_break_hash(salt: str, node: str) -> int:
    """SHA-256-derived deterministic tie-breaker integer."""
    key = f"{salt}::{node}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big", signed=False)


# --------------------------------------------------------------------------- #
# Local graph (mirrors the wave0 baselines convention)                        #
# --------------------------------------------------------------------------- #


def _local_graph(context: EpisodeContext) -> WeightedGraph:
    """Build a family-agnostic local graph from the sealed context view.

    Mirrors the private ``_local_graph`` helper in
    :mod:`~experiments.concern_gated_retrieval_e2.wave0.baselines`
    intentionally so the ensemble variance ranker's concern-warp PPR
    runs on the same topology as ``multiplicative_ppr`` — a single
    perturbation with ``epsilon = 0`` and the true concern collapses
    onto ``care_only_ppr``. Reimplemented here rather than imported
    so this module does not reach through a module-private name.
    """
    all_nodes = list(
        dict.fromkeys(list(context.context_nodes) + list(context.candidate_nodes))
    )
    edges: list[tuple[str, str, float]] = []
    ctx_nodes = tuple(context.context_nodes)
    cands = tuple(context.candidate_nodes)
    for ctx in ctx_nodes:
        for cand in cands:
            edges.append((ctx, cand, 1.0))
    for i in range(len(cands)):
        for j in range(i + 1, len(cands)):
            edges.append((cands[i], cands[j], 0.1))
    if not edges and len(all_nodes) >= 2:
        edges.append((all_nodes[0], all_nodes[1], 1.0))
    return WeightedGraph.from_edges(all_nodes, edges)


# --------------------------------------------------------------------------- #
# Ensemble variance ranker                                                    #
# --------------------------------------------------------------------------- #


#: Default ensemble cardinality declared in the task brief.
DEFAULT_ENSEMBLE_SIZE: Final[int] = 5

#: Default perturbation size used when :func:`ensemble_variance_ranker`
#: is invoked without an explicit ``epsilon``. Wave 1b PROVENANCE §8
#: records the default so a rerun that overrides it is loud.
DEFAULT_PERTURBATION_EPSILON: Final[float] = 0.1

#: PPR alpha for the concern-warped fixed point. Kept in sync with the
#: wave0 baselines' `_ppr_scores` alpha so ε = 0 → ``care_only_ppr``.
_PPR_ALPHA: Final[float] = 0.2
_PPR_TOL: Final[float] = 1e-9

#: Concern-warp strength for the ensemble ranker. Fixed at 1.0 to match
#: the wave0 :data:`DEFAULT_WARP_STRENGTH`.
_WARP_STRENGTH: Final[float] = 1.0


def _perturbed_care_map(
    context: EpisodeContext,
    graph_nodes: Sequence[str],
    epsilon: float,
    ensemble_idx: int,
) -> dict[str, float]:
    """Return a deterministic ε-scaled Gaussian perturbation of care anchors.

    The base draws are ``N(0, 1)`` samples seeded per
    ``(episode, ensemble_idx)``; the returned map is
    ``max(0, base_care + epsilon * z)`` per node so a larger
    ``epsilon`` scales the SAME underlying draws proportionally. That
    makes the resulting per-candidate score variance monotonically
    non-decreasing in ``epsilon`` (up to the ReLU clamp), which is the
    monotone-in-perturbation-size invariant the wave 1b tests pin.
    """
    if epsilon < 0.0 or not math.isfinite(epsilon):
        raise ValueError(f"epsilon must be finite and non-negative; got {epsilon!r}")
    salt = _episode_salt(context, f"variance-perturbation::{ensemble_idx}")
    rng = random.Random(salt)
    perturbed: dict[str, float] = {}
    # Iterate in graph_nodes order so the random stream is deterministic
    # and independent of the caller's iteration order over care_anchors.
    for node in graph_nodes:
        base = float(context.care_anchors.get(node, 0.0))
        raw_noise = rng.gauss(0.0, 1.0)
        perturbed[node] = max(0.0, base + float(epsilon) * raw_noise)
    return perturbed


def _perturbed_ppr_scores(
    context: EpisodeContext,
    graph: WeightedGraph,
    epsilon: float,
    ensemble_idx: int,
) -> dict[str, float]:
    """Concern-warped PPR score per candidate for one ensemble perturbation."""
    perturbed_care = _perturbed_care_map(
        context, graph.nodes, epsilon, ensemble_idx
    )
    warped = apply_concern_warp(graph, perturbed_care, strength=_WARP_STRENGTH)

    restart_nodes: list[str] = list(context.context_nodes)
    if not restart_nodes:
        restart_nodes = list(context.candidate_nodes)
    graph_node_set = set(warped.nodes)
    restart_nodes = [n for n in restart_nodes if n in graph_node_set]
    if not restart_nodes:
        return {node: 0.0 for node in context.candidate_nodes}
    mass = 1.0 / len(restart_nodes)
    restart: dict[str, float] = {}
    for node in restart_nodes:
        restart[node] = restart.get(node, 0.0) + mass
    result = personalized_pagerank(
        warped, restart, alpha=_PPR_ALPHA, tolerance=_PPR_TOL
    )
    return {
        node: float(result.scores.get(node, 0.0))
        for node in context.candidate_nodes
    }


class _EnsembleVarianceRanker:
    """RankFn-compatible closure holding pre-computed per-candidate variances.

    The ranker is bound to the ``context`` passed to
    :func:`ensemble_variance_ranker`; the bound context supplies both
    the variance table and the deterministic tie-break salt.
    ``__call__`` accepts the RankFn signature ``(context, budget)`` and
    returns the top ``budget`` candidates by decreasing variance.
    """

    def __init__(
        self,
        context: EpisodeContext,
        n_ensemble: int,
        epsilon: float,
    ) -> None:
        if not isinstance(context, EpisodeContext):
            raise TypeError(
                "ensemble_variance_ranker requires an EpisodeContext; got "
                f"{type(context).__name__}"
            )
        if not isinstance(n_ensemble, int) or isinstance(n_ensemble, bool):
            raise TypeError("n_ensemble must be a non-boolean int")
        if n_ensemble <= 1:
            raise ValueError(
                f"n_ensemble must be >= 2 for a variance to be defined; got {n_ensemble}"
            )
        self._context = context
        self._n_ensemble = int(n_ensemble)
        self._epsilon = float(epsilon)

        graph = _local_graph(context)
        scores_per_ensemble: list[dict[str, float]] = []
        for i in range(self._n_ensemble):
            scores_per_ensemble.append(
                _perturbed_ppr_scores(context, graph, self._epsilon, i)
            )

        variances: dict[str, float] = {}
        for node in context.candidate_nodes:
            vals = [d.get(node, 0.0) for d in scores_per_ensemble]
            if not vals:
                variances[node] = 0.0
                continue
            mean = sum(vals) / len(vals)
            variances[node] = sum((v - mean) ** 2 for v in vals) / len(vals)
        # Frozen for the lifetime of the ranker so ``variances`` reads
        # are stable across repeated __call__ invocations.
        self.variances: dict[str, float] = dict(variances)

    @property
    def n_ensemble(self) -> int:
        return self._n_ensemble

    @property
    def epsilon(self) -> float:
        return self._epsilon

    def __call__(
        self, context: EpisodeContext, budget: int
    ) -> tuple[str, ...]:
        if budget < 0:
            raise ValueError("budget must be non-negative")
        if budget == 0:
            return ()
        salt = _episode_salt(self._context, "variance-rank")
        ordered = sorted(
            self._context.candidate_nodes,
            key=lambda node: (
                -float(self.variances.get(node, 0.0)),
                _tie_break_hash(salt, node),
            ),
        )
        cutoff = min(budget, len(ordered))
        return tuple(ordered[:cutoff])


def ensemble_variance_ranker(
    context: EpisodeContext,
    n_ensemble: int = DEFAULT_ENSEMBLE_SIZE,
    *,
    epsilon: float = DEFAULT_PERTURBATION_EPSILON,
) -> RankFn:
    """Return a :data:`RankFn` bound to ``context`` that ranks by ensemble variance.

    Builds ``n_ensemble`` ε-perturbed concern-warped rankings on the
    :func:`_local_graph`, computes the per-candidate PPR-score
    variance across the ensemble, and returns a callable that emits
    the top-``budget`` candidates by decreasing variance. Ties are
    broken by a deterministic per-episode SHA-256 hash so the ranking
    is byte-reproducible.

    Parameters
    ----------
    context:
        The sealed :class:`EpisodeContext` view. Sealed EpisodeSpec
        attributes are never read.
    n_ensemble:
        Number of perturbations. Must be >= 2. Defaults to
        :data:`DEFAULT_ENSEMBLE_SIZE` (5) per the task brief.
    epsilon:
        Standard-deviation scale of the additive Gaussian perturbation
        applied to ``context.care_anchors`` before each PPR run.
        Larger ``epsilon`` widens the induced score variance
        monotonically; ``epsilon = 0`` collapses every ensemble member
        onto the same ranking and yields zero variance for every
        candidate.
    """
    return _EnsembleVarianceRanker(context, n_ensemble, epsilon)


# --------------------------------------------------------------------------- #
# Inverse-frequency audit sampler                                             #
# --------------------------------------------------------------------------- #


#: Fixed calibration-seed window used to build the rarity batch. Matches
#: the wave0 baselines convention so the audit slot's frequency weights
#: are drawn from the same statistical population ``freq_only`` sees.
_RARITY_SEED_WINDOW: Final[tuple[int, ...]] = tuple(range(100_000, 100_010))


def _rarity_for_family(family: str) -> dict[str, float]:
    """Return the inverse-frequency rarity table for the audit slot."""
    if family not in _WAVE0_FAMILY_NAMES:
        return {}
    if family == "delayed_commitments":
        size = 32
    else:
        size = 16
    graphs = tuple(
        build_withheld_graph(seed=s, size=size, family=family)
        for s in _RARITY_SEED_WINDOW
    )
    return dict(rarity_scores(iter(graphs)))


def _inverse_frequency_audit_sample(
    context: EpisodeContext,
    budget: int,
    exclude: Iterable[str],
    splits: SplitFractions,
) -> tuple[str, ...]:
    """Deterministic weighted-random sample without replacement.

    Weights are per-candidate inverse-frequency rarity scores drawn
    from :func:`_rarity_for_family`. Candidates outside the withheld-
    graph namespace (e.g. ``maintenance_fault`` node ids) fall back to
    a uniform weight of ``1.0`` — the same degenerate-case behaviour
    documented in :func:`wave0.baselines.freq_only`. The salt embeds
    the split fractions so the two other reported grid points sample
    different audit picks per episode; that variability is exactly
    what makes the ablation informative across splits.
    """
    if budget <= 0:
        return ()
    exclude_set = set(exclude)
    pool: list[str] = [
        node for node in context.candidate_nodes if node not in exclude_set
    ]
    if not pool:
        return ()
    rarity = _rarity_for_family(context.family)
    weights: list[float] = [max(float(rarity.get(node, 1.0)), 0.0) for node in pool]
    # If every rarity weight is exactly zero (defensive against a future
    # rarity implementation that returns zeros), fall back to uniform.
    if sum(weights) <= 0.0:
        weights = [1.0] * len(pool)

    salt = (
        f"cogr-wave1b-split::audit::{context.family}::{context.seed}::"
        f"{context.episode_id}::"
        f"{splits.care:.9f}-{splits.uncertain:.9f}-{splits.audit:.9f}"
    )
    rng = random.Random(salt)

    selected: list[str] = []
    remaining_pool: list[str] = list(pool)
    remaining_weights: list[float] = list(weights)
    take = min(budget, len(remaining_pool))
    for _ in range(take):
        total = sum(remaining_weights)
        if total <= 0.0:
            idx = rng.randrange(len(remaining_pool))
        else:
            draw = rng.uniform(0.0, total)
            acc = 0.0
            idx = len(remaining_pool) - 1
            for i, w in enumerate(remaining_weights):
                acc += w
                if draw <= acc:
                    idx = i
                    break
        selected.append(remaining_pool.pop(idx))
        remaining_weights.pop(idx)
    return tuple(selected)


# --------------------------------------------------------------------------- #
# k_split                                                                     #
# --------------------------------------------------------------------------- #


def k_split(
    context: EpisodeContext,
    budget: int,
    splits: SplitFractions,
) -> tuple[str, ...]:
    """Split-budget ablation baseline returning the disjoint concatenation.

    See the module docstring for the composition. The three slots are
    filled in order ``(k_care, k_uncertain, k_audit)`` and returned as
    a single tuple that never contains duplicates.

    Raises
    ------
    ValueError
        If ``budget < 0``, if the requested split leaves
        ``k_audit < 1``, or if the composition would need to draw
        more distinct nodes than the candidate set contains.
    TypeError
        If ``splits`` is not a :class:`SplitFractions` instance.
    """
    if not isinstance(splits, SplitFractions):
        raise TypeError(
            "k_split requires a SplitFractions instance for splits; got "
            f"{type(splits).__name__}"
        )
    if not isinstance(budget, int) or isinstance(budget, bool):
        raise TypeError("budget must be a non-boolean int")
    if budget < 0:
        raise ValueError(f"budget must be non-negative; got {budget}")
    if budget == 0:
        return ()

    k_care = int(round(splits.care * budget))
    k_uncertain = int(round(splits.uncertain * budget))
    k_audit = budget - k_care - k_uncertain
    if k_audit < 1:
        raise ValueError(
            "k_split requires k_audit >= 1; got "
            f"k_care={k_care}, k_uncertain={k_uncertain}, k_audit={k_audit} "
            f"for budget={budget} and splits=(care={splits.care}, "
            f"uncertain={splits.uncertain}, audit={splits.audit})"
        )

    if budget > len(context.candidate_nodes):
        raise ValueError(
            "k_split budget exceeds candidate set: "
            f"budget={budget}, |candidates|={len(context.candidate_nodes)}"
        )

    # ---- k_care slot -----------------------------------------------------
    care_picks: tuple[str, ...] = multiplicative_ppr(context, k_care)
    if len(set(care_picks)) != len(care_picks):
        raise RuntimeError(
            "multiplicative_ppr returned duplicate picks; wave0 contract"
            " violation."
        )

    # ---- k_uncertain slot ------------------------------------------------
    care_set = set(care_picks)
    uncertain_picks: list[str] = []
    if k_uncertain > 0:
        ranker = ensemble_variance_ranker(
            context,
            n_ensemble=DEFAULT_ENSEMBLE_SIZE,
            epsilon=DEFAULT_PERTURBATION_EPSILON,
        )
        # Ask the ranker for the full ordered candidate list so we can
        # skip any candidate the k_care slot already took and still
        # promote the next-highest-variance survivor.
        variance_ranked = ranker(context, len(context.candidate_nodes))
        for node in variance_ranked:
            if node in care_set:
                continue
            uncertain_picks.append(node)
            if len(uncertain_picks) == k_uncertain:
                break

    # ---- k_audit slot ----------------------------------------------------
    exclude_from_audit = care_set | set(uncertain_picks)
    audit_picks = _inverse_frequency_audit_sample(
        context, k_audit, exclude_from_audit, splits
    )

    combined = tuple(care_picks) + tuple(uncertain_picks) + tuple(audit_picks)
    if len(set(combined)) != len(combined):
        raise RuntimeError(
            "k_split composition produced duplicates across slots; this is a"
            " logic bug in the disjoint-selection guard."
        )
    return combined


__all__ = [
    "DEFAULT_ENSEMBLE_SIZE",
    "DEFAULT_PERTURBATION_EPSILON",
    "SPLITS_TO_REPORT",
    "SplitFractions",
    "ensemble_variance_ranker",
    "k_split",
]
