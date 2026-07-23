"""COGR-E2a Wave 1a specificity-contrast harness.

Wave 1a's Specificity gate (``PREREGISTRATION.md`` §5.3, ``PROMOTION_
CONTRACT.md`` G3) demands that the on-line-learned concern-update rule
outperform every information-matched generic signal — value, priority,
recency — imported from the Wave 0 baseline slate, on the SAME seed set,
and that the wrong-agent baseline not sit within
``sigma_hat_multiplicative_wave0`` of the on-line-learned mean on any
family.  This module supplies the per-family, per-seed contrast harness
the sweep runner and the promotion harness (``score_e2a``) consume.

Public surface (Wave 1b will import from here without re-implementing):

* :class:`SpecificityRow` — one row per seed, holding the realized
  sealed-outcome reward for every arm (frozen-wrong, online-learned IPS,
  online-learned DR, and the four comparators).
* :class:`ContrastAggregate` — one row per ``(variant, comparator)`` pair
  carrying the paired-seed mean delta, cluster-robust SE (one cluster
  per seed), and the ``mean - 2 * SE`` lower confidence bound.  Cluster-
  robust because Wave 1a's paired-seed design uses each seed as a
  cluster (§5.4, §6.3 of ``PREREGISTRATION.md``); the estimator reduces
  to the standard paired SE ``s / sqrt(K)`` when there is exactly one
  observation per cluster, and generalises transparently if the sweep
  later grows per-seed sample sizes (multi-probe rollouts are a Wave 1b
  object).
* :class:`SpecificityReport` — the frozen aggregate a family's
  confirmatory sweep publishes.  Every arm's mean and the
  ``ContrastAggregate`` slate are frozen at construction so downstream
  receipts and the promotion harness get a byte-stable view.
* :func:`run_specificity_contrast(family, seeds)` — the batch entry
  point.  Runs every arm on the same seed set (paired at the seed
  level), collects the six arm rewards per seed, and returns a
  :class:`SpecificityReport`.

Reuse boundary
--------------

* Wave 0 baselines: ``info_matched_value``, ``info_matched_priority``,
  ``info_matched_recency``, ``wrong_agent_concern`` are imported from
  ``wave0.baselines`` unchanged.  Wave 0 audits every baseline through
  ``IntegrityAudit.assert_clean`` at module import time, so a leaky
  comparator fails CI at collection; Wave 1a re-audits the wrapped
  nomination via ``run_e2a_episode``'s policy-side audit as an extra
  defence-in-depth.
* Conditions: ``FROZEN_WRONG`` supplies the anchor (Wave 1a §4 baseline
  row) and every comparator ranker rides on the same frozen-wrong
  concern prior so the comparator's contribution to the reward
  isolates the ranking signal, not the concern signal.  ``ONLINE_IPS``
  and ``ONLINE_DR`` are dispatched with the default concern-biased
  ranker on ``run_e2a_episode`` — the sweep runner's on-line-learned
  variants.  Confirmatory-mode ``update_concern`` behaviour is
  Wave 1a scaffolding (see ``e2a_runner.run_e2a_episode``); this module
  consumes the runner's realized reward without owning the update
  contract.

Wave 1a scope
-------------

This harness CAN reject the concern-update rule via the Specificity
gate.  It CANNOT establish learned memory geometry (Wave 1b), the L1
dual-source-retrieval mechanism claim (Wave 1b), or the L2
history-derived-concern-recovery claim (also Wave 1b).  Per the honor-
the-preregistration rule, only knobs enumerated in
``PREREGISTRATION.md`` §7 may be rerun after a KILL.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Callable, Final, Mapping, Sequence

from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    RankFn,
    info_matched_priority,
    info_matched_recency,
    info_matched_value,
    wrong_agent_concern,
)
from experiments.concern_gated_retrieval_e2.wave0.concern_update import (
    DEFAULT_EPSILON,
    NominationPolicy,
)
from experiments.concern_gated_retrieval_e2.wave0.families import (
    delayed_commitments as _dc_family,
    maintenance_fault as _mf_family,
    resource_constrained as _rc_family,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1a.conditions import (
    CONDITIONS,
    FROZEN_WRONG,
    ONLINE_DR,
    ONLINE_IPS,
    ORACLE_CEILING,
)
from experiments.concern_gated_retrieval_e2.wave1a.e2a_runner import (
    run_e2a_episode,
)

__all__ = [
    "ARM_FROZEN_WRONG",
    "ARM_ONLINE_IPS",
    "ARM_ONLINE_DR",
    "COMPARATOR_INFO_MATCHED_VALUE",
    "COMPARATOR_INFO_MATCHED_PRIORITY",
    "COMPARATOR_INFO_MATCHED_RECENCY",
    "COMPARATOR_WRONG_AGENT",
    "COMPARATORS",
    "ContrastAggregate",
    "SpecificityReport",
    "SpecificityRow",
    "VARIANTS",
    "cluster_robust_se",
    "compute_contrast_aggregate",
    "run_specificity_contrast",
]


# --------------------------------------------------------------------------- #
# Arm names (frozen)
# --------------------------------------------------------------------------- #


#: The baseline arm.  Every ``(variant, comparator)`` contrast is scored
#: against the on-line-learned variant, not this baseline; the baseline
#: is carried on the row so the promotion harness can perform the
#: per-family reversal check (§5.4) without re-running the sweep.
ARM_FROZEN_WRONG: Final[str] = "frozen_wrong"

#: On-line-learned IPS candidate variant.
ARM_ONLINE_IPS: Final[str] = "online_learned_ips"

#: On-line-learned DR candidate variant.
ARM_ONLINE_DR: Final[str] = "online_learned_dr"

#: Wave 0 info-matched value baseline (utility proxy from care anchors).
COMPARATOR_INFO_MATCHED_VALUE: Final[str] = "info_matched_value"

#: Wave 0 info-matched priority baseline (``care_weight * ctx_ppr``).
COMPARATOR_INFO_MATCHED_PRIORITY: Final[str] = "info_matched_priority"

#: Wave 0 info-matched recency baseline (candidate ordering).
COMPARATOR_INFO_MATCHED_RECENCY: Final[str] = "info_matched_recency"

#: Wave 0 wrong-agent-permuted concern baseline (from
#: ``wave0.baselines.wrong_agent_concern``).  This is the *ranker*-level
#: wrong-agent control against which the on-line-learned variant must
#: separate; Wave 1a additionally runs the ``WRONG_AGENT`` condition on
#: the fixed-prior sweep (see ``wave1a.controls.run_wrong_agent``) for
#: the coverage / propensity receipts.  The two are complementary: this
#: one exercises the specificity gate directly, the other exercises the
#: propensity gate.
COMPARATOR_WRONG_AGENT: Final[str] = "wrong_agent"


#: Canonical variant order (matches ``PREREGISTRATION.md`` §6.1).
VARIANTS: Final[tuple[str, ...]] = (ARM_ONLINE_IPS, ARM_ONLINE_DR)


#: Canonical comparator order.  Matches ``PREREGISTRATION.md`` §5.3.
#: Every ``ContrastAggregate`` in the returned :class:`SpecificityReport`
#: is emitted in ``(variant, comparator)`` lexicographic order over
#: this tuple × :data:`VARIANTS`.
COMPARATORS: Final[tuple[str, ...]] = (
    COMPARATOR_INFO_MATCHED_VALUE,
    COMPARATOR_INFO_MATCHED_PRIORITY,
    COMPARATOR_INFO_MATCHED_RECENCY,
    COMPARATOR_WRONG_AGENT,
)


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SpecificityRow:
    """One per-seed, per-family paired receipt.

    Every arm's realized sealed-outcome reward is carried in a single
    frozen mapping so callers building synthetic rows for the promotion
    harness (or downstream Wave 1b joins) do not need to reason about
    slot order.  Missing arms are a construction-time error; the frozen
    key set is a Wave 1a contract.

    Attributes
    ----------
    family:
        The Wave 0 procedural family the seed was drawn from.
    seed:
        The confirmatory seed (in ``[200000, 201999]``) driving this row.
    episode_id:
        The sealed :class:`EpisodeSpec.episode_id`.  Wave 1b paired-seed
        joins consume this key.
    rewards:
        Frozen mapping from arm name to realized sealed-outcome reward.
        Must contain every arm in
        ``VARIANTS + COMPARATORS + (ARM_FROZEN_WRONG,)``.
    """

    family: str
    seed: int
    episode_id: str
    rewards: Mapping[str, float]

    def __post_init__(self) -> None:
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("SpecificityRow.family must be a non-empty string")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("SpecificityRow.seed must be a non-boolean int")
        if not isinstance(self.episode_id, str) or not self.episode_id:
            raise ValueError("SpecificityRow.episode_id must be a non-empty string")
        expected_arms = frozenset(
            (ARM_FROZEN_WRONG,) + VARIANTS + COMPARATORS
        )
        if not isinstance(self.rewards, Mapping):
            raise TypeError("SpecificityRow.rewards must be a Mapping")
        missing = expected_arms - set(self.rewards.keys())
        if missing:
            raise ValueError(
                f"SpecificityRow.rewards missing arms {sorted(missing)}; "
                f"expected the union of ARM_FROZEN_WRONG, VARIANTS, and "
                f"COMPARATORS"
            )
        for arm, reward in self.rewards.items():
            if not isinstance(reward, (int, float)) or isinstance(reward, bool):
                raise TypeError(
                    f"SpecificityRow.rewards[{arm!r}] must be a real number"
                )
            if not math.isfinite(float(reward)):
                raise ValueError(
                    f"SpecificityRow.rewards[{arm!r}] must be finite"
                )
        object.__setattr__(
            self, "rewards", MappingProxyType(dict(self.rewards))
        )


@dataclass(frozen=True)
class ContrastAggregate:
    """One aggregate contrast row: variant vs comparator.

    Attributes
    ----------
    variant:
        The on-line-learned arm being scored (one of :data:`VARIANTS`).
    comparator:
        The comparator arm the variant is compared against (one of
        :data:`COMPARATORS`).
    n_clusters:
        Number of seeds (each seed is one cluster on the paired-seed
        design).  Wave 1b multi-probe rollouts may grow the per-cluster
        observation count; the field name uses ``n_clusters`` for that
        generality.
    mean_delta:
        Paired-seed mean of ``variant_reward - comparator_reward``.  A
        positive value means the variant beats the comparator.
    cluster_robust_se:
        Cluster-robust standard error of ``mean_delta`` with each seed
        as one cluster.  For one observation per cluster this reduces
        to the standard paired-seed SE ``s / sqrt(K)`` where ``s^2 =
        sum((d_i - mean)^2) / (K - 1)``.
    lower_bound_2se:
        ``mean_delta - 2 * cluster_robust_se``.  The screen decision
        rule in ``PREREGISTRATION.md`` §6.3 compares this lower bound
        against the per-family threshold ``delta_thresh_E2a_{f}``.
    """

    variant: str
    comparator: str
    n_clusters: int
    mean_delta: float
    cluster_robust_se: float
    lower_bound_2se: float


@dataclass(frozen=True)
class SpecificityReport:
    """Frozen per-family aggregate emitted by :func:`run_specificity_contrast`.

    Attributes
    ----------
    family:
        The Wave 0 procedural family.
    seeds:
        The seed order (traversal order in the run).
    rows:
        One :class:`SpecificityRow` per seed.
    variants:
        Snapshot of :data:`VARIANTS` present in the report.
    comparators:
        Snapshot of :data:`COMPARATORS` present in the report.  If a
        caller inserted ``"oracle_ceiling"`` here, the promotion harness
        (``promotion_harness.score_e2a``) refuses the report with
        :class:`PromotionRefused`.
    contrasts:
        One :class:`ContrastAggregate` per ``(variant, comparator)``
        pair, in the same order as
        ``[(v, c) for v in variants for c in comparators]``.
    arm_means:
        Frozen mapping from arm name to sample mean reward.
    frozen_wrong_mean:
        Convenience alias for ``arm_means[ARM_FROZEN_WRONG]``.  The
        promotion harness's family-reversal check reads this value
        without redoing the mean.
    """

    family: str
    seeds: tuple[int, ...]
    rows: tuple[SpecificityRow, ...]
    variants: tuple[str, ...]
    comparators: tuple[str, ...]
    contrasts: tuple[ContrastAggregate, ...]
    arm_means: Mapping[str, float]
    frozen_wrong_mean: float

    #: Reserved so downstream receipts can bolt on family-level
    #: diagnostics (coverage summary, propensity ESS) without a shape
    #: change to receipts already on disk.
    extras: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("SpecificityReport.family must be a non-empty string")
        if len(self.rows) != len(self.seeds):
            raise ValueError(
                "SpecificityReport.rows and .seeds must have the same length; "
                f"got {len(self.rows)} rows vs {len(self.seeds)} seeds"
            )
        if not isinstance(self.arm_means, Mapping):
            raise TypeError("SpecificityReport.arm_means must be a Mapping")
        object.__setattr__(
            self, "arm_means", MappingProxyType(dict(self.arm_means))
        )


# --------------------------------------------------------------------------- #
# Cluster-robust standard error
# --------------------------------------------------------------------------- #


def cluster_robust_se(deltas: Sequence[float]) -> float:
    """Return the cluster-robust SE with one observation per cluster.

    For paired-seed data with each seed as one cluster the cluster-
    robust SE reduces to the standard paired-seed SE::

        V_CR = (K / (K - 1)) * Σ u_i^2 / K^2
             = Σ (d_i - mean)^2 / (K * (K - 1))
        SE_CR = sqrt(V_CR)

    Returns ``0.0`` for ``K < 2`` — the sample SE of a single point is
    undefined, and Wave 1a's screen decision rule sizes ``2 * SE`` so a
    zero SE on a one-cluster batch triggers the deeper ``n_clusters``
    audit in the promotion harness.  Non-finite deltas raise.

    Parameters
    ----------
    deltas:
        Sequence of per-cluster paired differences.

    Returns
    -------
    float
        The cluster-robust standard error of the mean.
    """

    values = list(deltas)
    for i, d in enumerate(values):
        if not isinstance(d, (int, float)) or isinstance(d, bool):
            raise TypeError(f"deltas[{i}] must be a real number")
        if not math.isfinite(float(d)):
            raise ValueError(f"deltas[{i}] must be finite; got {d!r}")
    k = len(values)
    if k < 2:
        return 0.0
    mean = sum(values) / k
    ssq = sum((float(d) - mean) ** 2 for d in values)
    variance = ssq / (k * (k - 1))
    return math.sqrt(max(variance, 0.0))


def compute_contrast_aggregate(
    rows: Sequence[SpecificityRow],
    *,
    variant: str,
    comparator: str,
) -> ContrastAggregate:
    """Compute one :class:`ContrastAggregate` from a per-seed row batch.

    Every row must carry both ``variant`` and ``comparator`` in its
    ``rewards`` mapping.  Pure function; safe to call from tests and
    downstream promotion-harness code.
    """

    if variant not in VARIANTS:
        raise ValueError(
            f"variant must be one of {VARIANTS}; got {variant!r}"
        )
    if comparator not in COMPARATORS:
        raise ValueError(
            f"comparator must be one of {COMPARATORS}; got {comparator!r}"
        )
    deltas: list[float] = []
    for i, row in enumerate(rows):
        if not isinstance(row, SpecificityRow):
            raise TypeError(f"rows[{i}] is not a SpecificityRow")
        if variant not in row.rewards or comparator not in row.rewards:
            raise ValueError(
                f"rows[{i}] missing arm reward for {variant!r} or "
                f"{comparator!r}"
            )
        deltas.append(
            float(row.rewards[variant]) - float(row.rewards[comparator])
        )
    n = len(deltas)
    mean_delta = sum(deltas) / n if n > 0 else 0.0
    se = cluster_robust_se(deltas)
    return ContrastAggregate(
        variant=variant,
        comparator=comparator,
        n_clusters=n,
        mean_delta=float(mean_delta),
        cluster_robust_se=float(se),
        lower_bound_2se=float(mean_delta - 2.0 * se),
    )


# --------------------------------------------------------------------------- #
# Family generator dispatch
# --------------------------------------------------------------------------- #


_FAMILY_GENERATORS: Final[Mapping[str, Callable[..., EpisodeSpec]]] = {
    _dc_family.FAMILY_NAME: _dc_family.generate_episode,
    _mf_family.FAMILY_NAME: _mf_family.generate_episode,
    _rc_family.FAMILY_NAME: _rc_family.generate_episode,
}


def _validate_family(family: str) -> str:
    if not isinstance(family, str) or not family:
        raise TypeError("family must be a non-empty string")
    if family not in _FAMILY_GENERATORS:
        raise ValueError(
            f"unknown Wave 0 family: {family!r}; expected one of "
            f"{sorted(_FAMILY_GENERATORS)}"
        )
    return family


def _validate_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    if isinstance(seeds, (str, bytes)):
        raise TypeError("seeds must be a Sequence[int], not str/bytes")
    materialised = tuple(seeds)
    if not materialised:
        raise ValueError("seeds must be non-empty")
    for i, seed in enumerate(materialised):
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError(
                f"seeds[{i}] must be a non-boolean int; got {type(seed).__name__}"
            )
    return materialised


# --------------------------------------------------------------------------- #
# Nomination-factory adapters for wave0.baselines RankFn
# --------------------------------------------------------------------------- #


def _wrap_baseline_as_factory(
    baseline: RankFn,
) -> Callable[[Mapping[str, float]], NominationPolicy]:
    """Return a factory that yields a NominationPolicy from a Wave 0 RankFn.

    The wave0 ``RankFn`` signature is ``(EpisodeContext, budget) ->
    tuple[str, ...]``; the ``NominationPolicy`` signature the runner
    expects is ``(EpisodeContext) -> Sequence[str]``.  This adapter
    binds ``budget`` from ``context.budget`` and ignores the concern
    prior (the info-matched baselines already compute their own signal
    from the sealed ``EpisodeContext``).

    The wrapped nomination callable stays
    :meth:`IntegrityAudit.assert_clean`-clean because it only reads
    ``context.budget`` and ``context.candidate_nodes`` and delegates to
    the wave0 baseline, which itself was already audited at wave0
    import time.
    """

    _baseline = baseline

    def factory(_concern: Mapping[str, float]) -> NominationPolicy:
        def nomination(context: EpisodeContext) -> Sequence[str]:
            budget = int(context.budget)
            if budget <= 0:
                budget = len(context.candidate_nodes)
            return _baseline(context, budget)

        return nomination

    return factory


#: Table mapping comparator arm name -> a nomination-factory adapter over
#: the corresponding Wave 0 baseline.  Frozen at module import.
_COMPARATOR_FACTORIES: Final[
    Mapping[str, Callable[[Mapping[str, float]], NominationPolicy]]
] = MappingProxyType(
    {
        COMPARATOR_INFO_MATCHED_VALUE: _wrap_baseline_as_factory(info_matched_value),
        COMPARATOR_INFO_MATCHED_PRIORITY: _wrap_baseline_as_factory(
            info_matched_priority
        ),
        COMPARATOR_INFO_MATCHED_RECENCY: _wrap_baseline_as_factory(
            info_matched_recency
        ),
        COMPARATOR_WRONG_AGENT: _wrap_baseline_as_factory(wrong_agent_concern),
    }
)


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #


def run_specificity_contrast(
    family: str,
    seeds: Sequence[int],
    *,
    epsilon: float = DEFAULT_EPSILON,
) -> SpecificityReport:
    """Run the Wave 1a specificity contrast on ``(family, seeds)``.

    For every seed, executes each of the six arms
    (``FROZEN_WRONG``, ``ONLINE_IPS``, ``ONLINE_DR``, ``info_matched_value``,
    ``info_matched_priority``, ``info_matched_recency``,
    ``wrong_agent``) against the SAME sealed :class:`EpisodeSpec` and
    collects the realized sealed-outcome reward.  Determinism is a
    scaffolding contract: with ``epsilon = DEFAULT_EPSILON`` and
    ``rng_seed = seed`` (locked inside the runner) a repeat call yields
    a byte-identical :class:`SpecificityReport` on any host.

    Parameters
    ----------
    family:
        One of ``delayed_commitments`` / ``maintenance_fault`` /
        ``resource_constrained``.  Any other value raises.
    seeds:
        Sequence of confirmatory seeds in ``[200000, 201999]``.  The
        Wave 0 family generator's confirmatory-seed guard raises
        ``ValueError`` on a calibration seed; the honor-the-
        preregistration rule forbids sneaking calibration seeds through
        the harness.
    epsilon:
        ``LoggedProbePolicy`` exploration probability.  Locked at
        :data:`DEFAULT_EPSILON` (``0.05``) by default per Wave 1a
        §5.1.  The Wave 0 constructor refuses ``epsilon <= 0``; the
        replay knob in ``PREREGISTRATION.md`` §7 permits up to
        ``epsilon = 0.10`` on a §5.1 coverage failure and no more.

    Returns
    -------
    SpecificityReport
        A frozen per-family aggregate carrying every seed's paired row
        plus the contrast slate.  The oracle is NOT included in
        :attr:`SpecificityReport.comparators` — Wave 1a §4 marks it as
        diagnostic-only, and the promotion harness refuses a report
        that references it.
    """

    family_name = _validate_family(family)
    seed_tuple = _validate_seeds(seeds)
    generator = _FAMILY_GENERATORS[family_name]

    frozen_condition = CONDITIONS[FROZEN_WRONG]
    online_ips_condition = CONDITIONS[ONLINE_IPS]
    online_dr_condition = CONDITIONS[ONLINE_DR]

    rows: list[SpecificityRow] = []
    for seed in seed_tuple:
        episode = generator(seed=seed, bucket=TemplateBucket.CONFIRMATION)
        rewards: dict[str, float] = {}

        # Baseline: frozen-wrong condition, default (concern-biased) ranker.
        rewards[ARM_FROZEN_WRONG] = float(
            run_e2a_episode(
                episode,
                frozen_condition,
                rng_seed=seed,
                epsilon=epsilon,
            ).outcome.realized_reward
        )

        # Candidate variants: on-line-learned IPS / DR, default ranker.
        rewards[ARM_ONLINE_IPS] = float(
            run_e2a_episode(
                episode,
                online_ips_condition,
                rng_seed=seed,
                epsilon=epsilon,
            ).outcome.realized_reward
        )
        rewards[ARM_ONLINE_DR] = float(
            run_e2a_episode(
                episode,
                online_dr_condition,
                rng_seed=seed,
                epsilon=epsilon,
            ).outcome.realized_reward
        )

        # Comparators: frozen-wrong condition (concern held fixed at the
        # wrong prior) with the wave0 baseline as the nomination policy.
        # This isolates the ranking signal — the concern signal is the
        # same as the baseline row above.
        for comparator_name, factory in _COMPARATOR_FACTORIES.items():
            rewards[comparator_name] = float(
                run_e2a_episode(
                    episode,
                    frozen_condition,
                    rng_seed=seed,
                    epsilon=epsilon,
                    nomination_factory=factory,
                ).outcome.realized_reward
            )

        rows.append(
            SpecificityRow(
                family=family_name,
                seed=seed,
                episode_id=episode.episode_id,
                rewards=rewards,
            )
        )

    # Aggregate arm means.
    arm_means: dict[str, float] = {}
    n_rows = len(rows)
    for arm in (ARM_FROZEN_WRONG,) + VARIANTS + COMPARATORS:
        arm_means[arm] = (
            sum(float(row.rewards[arm]) for row in rows) / n_rows
            if n_rows > 0
            else 0.0
        )

    # Contrast aggregates, one per (variant, comparator) pair in the
    # canonical order.  The oracle is intentionally excluded from
    # COMPARATORS — see the docstring.
    contrasts: list[ContrastAggregate] = []
    for variant in VARIANTS:
        for comparator in COMPARATORS:
            contrasts.append(
                compute_contrast_aggregate(
                    rows, variant=variant, comparator=comparator
                )
            )

    # Guard: no comparator name silently collided with the oracle.  A
    # future editor who adds "oracle_ceiling" to COMPARATORS breaks the
    # Wave 1a §4 "Oracle is diagnostic" rule; catch it here as well as
    # in the promotion harness.
    if ORACLE_CEILING in COMPARATORS:
        raise RuntimeError(
            "Wave 1a specificity harness illegally advertises the "
            "oracle_ceiling as a promotable comparator; the oracle is "
            "diagnostic-only (wave1a/PREREGISTRATION.md §4)."
        )

    return SpecificityReport(
        family=family_name,
        seeds=seed_tuple,
        rows=tuple(rows),
        variants=VARIANTS,
        comparators=COMPARATORS,
        contrasts=tuple(contrasts),
        arm_means=arm_means,
        frozen_wrong_mean=float(arm_means[ARM_FROZEN_WRONG]),
    )
