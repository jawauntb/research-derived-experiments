"""Wave 0 calibration orchestrator for Concern-Gated Retrieval E2.

This is the pure-Python orchestrator that drives the Wave 0 calibration
sweep. It sweeps four dimensions declared by the build brief —

* ``family`` in ``{delayed_commitments, maintenance_fault, resource_constrained}``,
* ``retrieval_budget`` in a small grid of top-k budgets,
* ``distractor_density`` in ``{light, medium, heavy}`` (encoded as disjoint
  calibration-seed sub-ranges so the varying template shapes give different
  candidate-density regimes without touching the family generators), and
* ``epsilon`` in a small exploration-probability grid used only by the
  :class:`~experiments.concern_gated_retrieval_e2.wave0.concern_update.LoggedProbePolicy`
  coverage-reporting side-channel (Wave 0 does **not** update the wrong
  prior at evaluation time; the epsilon axis sizes the exploration
  coverage the Wave 1 COGR-E2a screen will require).

For every ``(family, distractor_density, budget)`` cell it runs the full
Wave 0 baseline slate from
:mod:`experiments.concern_gated_retrieval_e2.wave0.baselines` against a
batch of calibration seeds, scores each rank against a
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedEnvironment`,
and emits one row per ``(cell, seed, baseline)``. The aggregator then
produces the per-family variance estimate and the frozen threshold
proposal shape declared by ``PREREGISTRATION.md`` §8.

Anti-leakage boundary. This module is **evaluator-side** code: it is
allowed to touch the sealed
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`
answer key to register the oracle ceiling and to score realized outcomes.
Baseline callables in :mod:`.baselines` are policy-side code and pass
:meth:`IntegrityAudit.assert_clean` at their import; this orchestrator
never dereferences a sealed field inside a rank callable and never asks a
rank callable to inspect the answer key.

Wave 0 style boundary. This orchestrator produces calibration variance
receipts plus threshold proposals. It does **not** claim learned memory
geometry, concern recovery, semantic meaning, or selfhood. See
``docs/concern_gated_retrieval_research_program.md`` for the claim ladder.

Reuse boundary. Imports :class:`WeightedGraph` and
:func:`personalized_pagerank` only transitively via
:mod:`.baselines`; imports the sealed-environment types and the
:class:`LoggedProbePolicy` scaffolding directly. Does not fork any pilot
primitive.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Final, Mapping, Sequence

from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    BASELINES,
    CANDIDATE_MECHANISM,
    CEILING_MARKER,
    EMBEDDING_PROVENANCE,
    clear_oracle_answers,
    learned_one_stage_parameter_count,
    register_oracle_answer,
)
from experiments.concern_gated_retrieval_e2.wave0.concern_update import (
    DEFAULT_SOURCE_ID,
    LoggedProbePolicy,
)
from experiments.concern_gated_retrieval_e2.wave0.families import (
    delayed_commitments as _delayed_commitments,
    maintenance_fault as _maintenance_fault,
    resource_constrained as _resource_constrained,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
    RetrievalChoice,
    SealedEnvironment,
    SealedOutcome,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
    assert_calibration_only,
)


# --------------------------------------------------------------------------- #
# Public constants
# --------------------------------------------------------------------------- #


#: The three procedural families declared by ``PREREGISTRATION.md`` §6.
#: Canonical order — downstream receipts iterate this tuple.
FAMILIES: Final[tuple[str, ...]] = (
    "delayed_commitments",
    "maintenance_fault",
    "resource_constrained",
)


#: The candidate mechanism this Wave 0 sweep centers variance on. Wave 1
#: will contest promotion against the best matched-budget baseline from
#: :data:`BEST_MATCHED_BASELINES`; Wave 0 records the variance so that
#: contest is adjudicable.
CANDIDATE_MECHANISM_NAME: Final[str] = "multiplicative_ppr"


#: Baselines eligible for the "best matched-budget alternative" in
#: PREREGISTRATION.md §8.1. Order is documentation only; the aggregator
#: picks the highest-mean baseline over this set per family.
BEST_MATCHED_BASELINES: Final[tuple[str, ...]] = (
    "additive_ppr",
    "learned_one_stage",
    "info_matched_value",
    "info_matched_priority",
    "info_matched_recency",
    "embedding_similarity",
)


#: Ceiling baseline used only to compute ``headroom_to_ceiling``. Never
#: eligible for promotion; PREREGISTRATION.md §7 flags it CEILING-ONLY.
CEILING_BASELINE: Final[str] = "oracle_ceiling"


#: Bounded reward domain declared by PREREGISTRATION.md §6.
BOUNDED_REWARD_LOW: Final[float] = -1.0
BOUNDED_REWARD_HIGH: Final[float] = 1.0
BOUNDED_REWARD_RANGE: Final[float] = BOUNDED_REWARD_HIGH - BOUNDED_REWARD_LOW


#: Non-ceiling gate from PREREGISTRATION.md §9.2 — no baseline may saturate
#: within ``NON_CEILING_TOLERANCE * BOUNDED_REWARD_RANGE`` of the oracle.
NON_CEILING_TOLERANCE: Final[float] = 0.05


#: Default budget when the family does not pin one. Every Wave 0 family
#: currently pins ``budget=2`` on the :class:`EpisodeSpec` it emits; the
#: sweep passes each cell's declared budget through unchanged.
DEFAULT_BUDGET_GRID: Final[tuple[int, ...]] = (1, 2)


#: The distractor-density levels the sweep partitions the calibration
#: seed range into. Each level names a disjoint seed slice per family;
#: the actual per-family index ranges are derived in
#: :func:`_family_seed_slices` so a family with a narrower calibration
#: seed range (``resource_constrained``: 32 seeds) still yields three
#: well-formed batches.
DENSITY_LEVELS: Final[tuple[str, ...]] = ("light", "medium", "heavy")


#: Epsilon values for the LoggedProbePolicy coverage-reporting side
#: channel. The wrapped nomination policy is always the candidate
#: mechanism; the reported quantity is exploration coverage on the
#: alarm-suppressed commitment region for Wave 1 E2a sizing. Wave 0 does
#: not use these epsilons to update the wrong prior — that is a Wave 1
#: object. ``epsilon`` cannot be zero (LoggedProbePolicy forbids it).
EPSILON_GRID: Final[tuple[float, ...]] = (0.05, 0.10, 0.25)


#: Default cap on the number of seeds per (family, density) cell. Kept
#: modest so a full sweep fits under the Wave 0 Modal budget. The
#: aggregator reports the effective sample size per cell so downstream
#: variance readers can weight rows by ``n``.
DEFAULT_SEEDS_PER_CELL: Final[int] = 24


# --------------------------------------------------------------------------- #
# Family adapters
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _FamilyAdapter:
    """Uniform accessor for the three Wave 0 procedural families.

    The three family modules expose ``generate_episode(seed, bucket,
    holdout=None) -> EpisodeSpec`` but declare their calibration seed
    range through different attribute names. This adapter normalizes the
    accessors so :func:`_family_seed_slices` and :func:`build_cells` can
    iterate over them uniformly.
    """

    name: str
    module: Any
    seed_low: int
    seed_high_inclusive: int

    def calibration_seeds(self) -> tuple[int, ...]:
        # ``resource_constrained`` exposes ``calibration_seeds()`` directly
        # and defines only a 32-seed range; the other two families
        # declare ``CALIBRATION_SEED_MIN`` / ``CALIBRATION_SEED_MAX`` and
        # allow the full 1000-seed range.
        fn = getattr(self.module, "calibration_seeds", None)
        if fn is not None:
            return tuple(fn())
        return tuple(range(self.seed_low, self.seed_high_inclusive + 1))

    def generate_episode(self, seed: int) -> EpisodeSpec:
        return self.module.generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)


def _family_adapters() -> tuple[_FamilyAdapter, ...]:
    return (
        _FamilyAdapter(
            name="delayed_commitments",
            module=_delayed_commitments,
            seed_low=_delayed_commitments.CALIBRATION_SEED_MIN,
            seed_high_inclusive=_delayed_commitments.CALIBRATION_SEED_MAX,
        ),
        _FamilyAdapter(
            name="maintenance_fault",
            module=_maintenance_fault,
            seed_low=_maintenance_fault.CALIBRATION_SEED_MIN,
            seed_high_inclusive=_maintenance_fault.CALIBRATION_SEED_MAX,
        ),
        _FamilyAdapter(
            name="resource_constrained",
            module=_resource_constrained,
            seed_low=_resource_constrained.CALIBRATION_SEED_START,
            seed_high_inclusive=_resource_constrained.CALIBRATION_SEED_END - 1,
        ),
    )


_ADAPTERS: Final[Mapping[str, _FamilyAdapter]] = {
    adapter.name: adapter for adapter in _family_adapters()
}


def _family_seed_slices(
    family: str, *, seeds_per_cell: int
) -> Mapping[str, tuple[int, ...]]:
    """Return ``{density_level: seeds}`` for one family.

    The slice construction is deterministic: the calibration seed range
    is split into three equal-size contiguous chunks (`light`, `medium`,
    `heavy`), and each chunk is truncated to ``seeds_per_cell`` entries.
    ``resource_constrained`` has only 32 calibration seeds; the slicer
    truncates gracefully rather than raising, so a full sweep across
    every family runs without special-casing.
    """
    adapter = _ADAPTERS[family]
    all_seeds = adapter.calibration_seeds()
    n = len(all_seeds)
    if n == 0:
        raise ValueError(f"family {family!r} exposes no calibration seeds")
    third = max(n // 3, 1)
    windows = {
        "light": all_seeds[:third],
        "medium": all_seeds[third : 2 * third],
        "heavy": all_seeds[2 * third :],
    }
    return {
        level: tuple(seq[:seeds_per_cell]) for level, seq in windows.items()
    }


# --------------------------------------------------------------------------- #
# Cell plan builder
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CellPlan:
    """One (family, density, budget, epsilon) cell to run.

    Serializable to a plain dict via :meth:`to_dict` so Modal can pass
    the plan across container boundaries. The reverse constructor
    :meth:`from_dict` is the only supported deserialization; ad-hoc
    ``**kwargs`` construction is deliberately not exposed to callers.
    """

    family: str
    density_level: str
    budget: int
    epsilon: float
    seeds: tuple[int, ...]
    cell_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "density_level": self.density_level,
            "budget": self.budget,
            "epsilon": self.epsilon,
            "seeds": list(self.seeds),
            "cell_id": self.cell_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CellPlan":
        return cls(
            family=str(data["family"]),
            density_level=str(data["density_level"]),
            budget=int(data["budget"]),
            epsilon=float(data["epsilon"]),
            seeds=tuple(int(s) for s in data["seeds"]),
            cell_id=str(data["cell_id"]),
        )


def build_cells(
    *,
    families: Sequence[str] = FAMILIES,
    density_levels: Sequence[str] = DENSITY_LEVELS,
    budgets: Sequence[int] = DEFAULT_BUDGET_GRID,
    epsilons: Sequence[float] = (0.05,),
    seeds_per_cell: int = DEFAULT_SEEDS_PER_CELL,
) -> tuple[CellPlan, ...]:
    """Return the cell grid for the Wave 0 calibration sweep.

    A cell is one ``(family, density_level, budget, epsilon)`` combination
    with its seed batch resolved. The default grid is small enough to
    fit under the Wave 0 Modal budget (see :func:`estimate_cost_usd`);
    callers may shrink it further by passing fewer values on each axis.
    """
    unknown = tuple(f for f in families if f not in _ADAPTERS)
    if unknown:
        raise ValueError(f"unknown families: {unknown!r}")
    for level in density_levels:
        if level not in DENSITY_LEVELS:
            raise ValueError(f"unknown density_level {level!r}")
    if not budgets or any(b < 0 for b in budgets):
        raise ValueError("budgets must be a non-empty sequence of non-negatives")
    if not epsilons or any(not math.isfinite(e) or e <= 0.0 or e > 1.0 for e in epsilons):
        raise ValueError("epsilons must lie in (0, 1] and be finite")

    cells: list[CellPlan] = []
    for family in families:
        slices = _family_seed_slices(family, seeds_per_cell=seeds_per_cell)
        for level in density_levels:
            seeds = slices[level]
            if not seeds:
                continue
            for budget in budgets:
                for epsilon in epsilons:
                    cell_id = (
                        f"cogr-wave0::{family}::{level}::"
                        f"b{budget}::e{epsilon:.3f}::n{len(seeds)}"
                    )
                    cells.append(
                        CellPlan(
                            family=family,
                            density_level=level,
                            budget=budget,
                            epsilon=epsilon,
                            seeds=seeds,
                            cell_id=cell_id,
                        )
                    )
    return tuple(cells)


# --------------------------------------------------------------------------- #
# Cell execution
# --------------------------------------------------------------------------- #


def _register_oracle_from_spec(spec: EpisodeSpec) -> None:
    """Register the sealed answer key on the oracle module registry.

    The registry is read only by :func:`baselines.oracle_ceiling`; this
    keeps the oracle rank callable clean of any sealed-field access.
    Evaluator code is entitled to see the answer key.
    """
    register_oracle_answer(spec.episode_id, spec._answer_key)  # noqa: SLF001


def _apply_budget(baseline_budget: int, spec_budget: int) -> int:
    """Return the effective retrieval budget for one baseline call.

    The sweep budget from the cell plan (``baseline_budget``) caps the
    episode's own budget (``spec_budget``). Wave 0 families pin
    ``spec_budget = 2``; the cell may cap it lower to size how budget
    change affects the multiplicative-vs-matched contrast.
    """
    return int(min(max(baseline_budget, 0), spec_budget))


def _run_baselines_on_episode(
    spec: EpisodeSpec,
    context: EpisodeContext,
    env: SealedEnvironment,
    budget: int,
) -> dict[str, dict[str, Any]]:
    """Score every baseline in the slate on one sealed episode.

    Returns ``{baseline_name: {selected, sealed_outcome, ...}}``. Because
    :meth:`SealedEnvironment.evaluate` is single-shot per episode, this
    function creates one sealed environment per (episode, baseline) pair;
    the caller is responsible for supplying fresh :class:`SealedEnvironment`
    instances via :func:`_run_cell_rows`.
    """
    raise NotImplementedError  # replaced by inline loop below for clarity


def _score_episode(
    adapter: _FamilyAdapter,
    seed: int,
    plan: CellPlan,
) -> list[dict[str, Any]]:
    """Score every baseline in the slate against a fresh sealed env per row.

    Each baseline gets its own :class:`SealedEnvironment` — the sealed
    contract is single-shot per episode, so multiple baselines cannot
    share one environment. Constructing a fresh env per baseline row is
    cheap (the sealed env's state is a handful of tuples/dicts).
    """
    spec = adapter.generate_episode(seed)
    assert_calibration_only(_row_bucket_tag(spec))
    _register_oracle_from_spec(spec)

    baseline_budget = _apply_budget(plan.budget, spec.budget)
    rows: list[dict[str, Any]] = []
    for name, rank_fn in BASELINES.items():
        env = SealedEnvironment(spec, mode="calibration")
        context = env.observe(seed=spec.seed)
        ranked = tuple(rank_fn(context, baseline_budget))
        # Deduplicate defensively — every Wave 0 rank callable already
        # returns a tuple of unique nodes, but a downstream Wave 1
        # extension might not, and RetrievalChoice enforces uniqueness.
        seen: set[str] = set()
        deduped: list[str] = []
        for node in ranked:
            if node in seen:
                continue
            seen.add(node)
            deduped.append(node)
        choice = RetrievalChoice(
            selected=tuple(deduped[:baseline_budget]),
            wall_actions=len(deduped[:baseline_budget]),
        )
        outcome: SealedOutcome = env.evaluate(choice)
        rows.append(
            {
                "family": plan.family,
                "density_level": plan.density_level,
                "budget": baseline_budget,
                "epsilon": plan.epsilon,
                "seed": int(seed),
                "episode_id": spec.episode_id,
                "template_family_split": outcome.template_family_split,
                "baseline": name,
                "selected": list(choice.selected),
                "realized_reward": float(outcome.realized_reward),
                "constraint_preserved": bool(outcome.constraint_preserved),
                "misretrieval_cost": float(outcome.misretrieval_cost),
                "wall_actions": int(outcome.wall_actions),
                "is_ceiling_only": bool(getattr(rank_fn, CEILING_MARKER, False)),
            }
        )
    return rows


def _row_bucket_tag(spec: EpisodeSpec) -> Any:
    """Return a lightweight object carrying the ``TemplateBucket`` tag.

    :func:`assert_calibration_only` accepts any object with a
    ``bucket`` attribute, so we wrap the calibration-mode episode in an
    ad-hoc holder rather than passing the spec directly (the spec's
    ``template_family_split`` is a string, not the enum instance the
    tripwire expects).
    """

    class _Tag:
        bucket = TemplateBucket.CALIBRATION

    if spec.template_family_split != "calibration":
        # The sealed environment already refuses confirmatory episodes
        # when mode=='calibration', but the tripwire is a second, static
        # layer of defence.
        raise RuntimeError(
            "calibration orchestrator received a non-calibration episode"
        )
    return _Tag()


def _log_probe_coverage(
    adapter: _FamilyAdapter,
    seeds: Sequence[int],
    epsilon: float,
) -> dict[str, float]:
    """Return exploration coverage stats for the LoggedProbePolicy side channel.

    Wave 0 does not update the wrong prior; this call sizes the fraction
    of exploratory receipts and the exploration coverage on the alarm-
    suppressed commitment region so Wave 1 E2a can pick an epsilon that
    meets the roadmap's adequate-exploration gate.
    """
    if not seeds:
        return {
            "n_probes": 0.0,
            "exploration_fraction": 0.0,
            "mean_selection_propensity": 0.0,
        }

    def _rank_shim(ctx: EpisodeContext) -> Sequence[str]:
        return CANDIDATE_MECHANISM(ctx, max(1, len(ctx.candidate_nodes)))

    policy = LoggedProbePolicy(_rank_shim, epsilon=epsilon, source_id=DEFAULT_SOURCE_ID)
    exploratory = 0
    total = 0
    prop_sum = 0.0
    for seed in seeds:
        spec = adapter.generate_episode(seed)
        env = SealedEnvironment(spec, mode="calibration")
        ctx = env.observe(seed=spec.seed)
        rng = random.Random(f"cogr-wave0::probe::{spec.episode_id}::{epsilon:.6f}")
        _selected, receipt = policy.select(ctx, rng)
        total += 1
        exploratory += int(receipt.exploratory)
        prop_sum += float(receipt.selection_propensity)
    return {
        "n_probes": float(total),
        "exploration_fraction": float(exploratory / total),
        "mean_selection_propensity": float(prop_sum / total),
    }


def execute_cell(cell_dict: Mapping[str, Any]) -> dict[str, Any]:
    """Run one calibration cell and return its rows and a receipt.

    ``cell_dict`` is a plain dict shaped by :meth:`CellPlan.to_dict`.
    Returns ``{"cell": cell_dict, "rows": [...], "coverage": {...},
    "wall_seconds": float}``. The rows are baseline-level; the aggregator
    :func:`summarize_rows` reduces them into per-family variance rows.

    Called locally by the CPU CLI and remotely by
    :mod:`.modal_l4_sweep.run_cell`. The function is idempotent and does
    not write to disk itself.
    """
    plan = CellPlan.from_dict(cell_dict)
    adapter = _ADAPTERS.get(plan.family)
    if adapter is None:
        raise ValueError(f"unknown family {plan.family!r}")
    clear_oracle_answers()
    start = time.time()
    rows: list[dict[str, Any]] = []
    for seed in plan.seeds:
        rows.extend(_score_episode(adapter, seed, plan))
    coverage = _log_probe_coverage(adapter, plan.seeds, plan.epsilon)
    clear_oracle_answers()
    return {
        "cell": plan.to_dict(),
        "rows": rows,
        "coverage": coverage,
        "wall_seconds": float(time.time() - start),
    }


# --------------------------------------------------------------------------- #
# Aggregation and threshold proposal
# --------------------------------------------------------------------------- #


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(statistics.fmean(values)), float(statistics.pstdev(values))


def _bootstrap_mean_ci(
    values: Sequence[float],
    *,
    n_bootstrap: int = 200,
    ci: float = 0.95,
    seed: int = 20260723,
) -> tuple[float, float]:
    if len(values) < 2:
        base = float(values[0]) if values else 0.0
        return base, base
    rng = random.Random(seed)
    n = len(values)
    means: list[float] = []
    for _ in range(n_bootstrap):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_index = max(int((1 - ci) / 2 * n_bootstrap), 0)
    hi_index = min(int((1 + ci) / 2 * n_bootstrap), n_bootstrap - 1)
    return means[lo_index], means[hi_index]


def summarize_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Reduce baseline-level rows to a per-family variance summary.

    The summary carries per-baseline per-family mean, standard deviation,
    sample count, and bootstrap CI on the reward; the top-level
    per-family block carries the PREREGISTRATION.md §8.1 threshold row
    shape (``mu_hat_multiplicative``, ``sigma_hat_multiplicative``,
    ``mu_hat_best_matched``, ``sigma_hat_best_matched``,
    ``headroom_to_ceiling``, ``delta_thresh_L1``, best-matched winner id).
    Rows with the ceiling baseline contribute only to
    ``mu_hat_oracle_ceiling`` and never to ``mu_hat_best_matched``.
    """
    per_family: dict[str, dict[str, Any]] = {}
    for family in FAMILIES:
        family_rows = [row for row in rows if row.get("family") == family]
        by_baseline: dict[str, list[float]] = {}
        constraint_preserved: dict[str, list[float]] = {}
        for row in family_rows:
            name = str(row["baseline"])
            by_baseline.setdefault(name, []).append(float(row["realized_reward"]))
            constraint_preserved.setdefault(name, []).append(
                1.0 if row.get("constraint_preserved") else 0.0
            )
        baseline_stats: dict[str, dict[str, Any]] = {}
        for name, values in by_baseline.items():
            mean, std = _mean_std(values)
            ci_lo, ci_hi = _bootstrap_mean_ci(values)
            baseline_stats[name] = {
                "n": len(values),
                "mean_realized_reward": mean,
                "std_realized_reward": std,
                "bootstrap_ci_lo": ci_lo,
                "bootstrap_ci_hi": ci_hi,
                "constraint_preserved_rate": (
                    sum(constraint_preserved[name]) / len(constraint_preserved[name])
                    if constraint_preserved.get(name)
                    else 0.0
                ),
            }

        mu_candidate = baseline_stats.get(CANDIDATE_MECHANISM_NAME, {}).get(
            "mean_realized_reward", 0.0
        )
        sigma_candidate = baseline_stats.get(CANDIDATE_MECHANISM_NAME, {}).get(
            "std_realized_reward", 0.0
        )
        mu_oracle = baseline_stats.get(CEILING_BASELINE, {}).get(
            "mean_realized_reward", 0.0
        )

        best_name: str | None = None
        best_mean = -math.inf
        best_std = 0.0
        for name in BEST_MATCHED_BASELINES:
            entry = baseline_stats.get(name)
            if entry is None:
                continue
            if entry["mean_realized_reward"] > best_mean:
                best_mean = entry["mean_realized_reward"]
                best_std = entry["std_realized_reward"]
                best_name = name
        if best_name is None:
            best_mean = 0.0
            best_std = 0.0

        headroom_to_ceiling = mu_oracle - mu_candidate
        delta_thresh_l1 = max(
            2.0 * best_std,
            0.10 * max(headroom_to_ceiling, 0.0),
        )
        # Non-ceiling gate flag: no baseline may saturate within tolerance
        # of the oracle ceiling (PREREGISTRATION.md §9.2). We compute the
        # worst offender and flag the family if it triggers.
        non_candidate_max = max(
            (
                stats["mean_realized_reward"]
                for name, stats in baseline_stats.items()
                if name != CEILING_BASELINE
            ),
            default=0.0,
        )
        non_ceiling_headroom = mu_oracle - non_candidate_max
        non_ceiling_ok = non_ceiling_headroom >= (
            NON_CEILING_TOLERANCE * BOUNDED_REWARD_RANGE
        )

        per_family[family] = {
            "baselines": baseline_stats,
            "mu_hat_multiplicative": mu_candidate,
            "sigma_hat_multiplicative": sigma_candidate,
            "mu_hat_best_matched": best_mean,
            "sigma_hat_best_matched": best_std,
            "best_matched_baseline": best_name,
            "mu_hat_oracle_ceiling": mu_oracle,
            "headroom_to_ceiling": headroom_to_ceiling,
            "delta_thresh_L1": delta_thresh_l1,
            "non_ceiling_headroom": non_ceiling_headroom,
            "non_ceiling_ok": bool(non_ceiling_ok),
            "n_rows": len(family_rows),
        }

    aggregated_reward = [float(row["realized_reward"]) for row in rows]
    grand_mean, grand_std = _mean_std(aggregated_reward)
    return {
        "kind": "cogr_wave0_calibration_summary",
        "candidate_mechanism": CANDIDATE_MECHANISM_NAME,
        "ceiling_baseline": CEILING_BASELINE,
        "best_matched_pool": list(BEST_MATCHED_BASELINES),
        "embedding_provenance": EMBEDDING_PROVENANCE,
        "learned_one_stage_param_count": learned_one_stage_parameter_count(),
        "families": per_family,
        "grand_mean_realized_reward": grand_mean,
        "grand_std_realized_reward": grand_std,
        "n_rows_total": len(rows),
    }


# --------------------------------------------------------------------------- #
# Cost / budget helpers
# --------------------------------------------------------------------------- #


#: Modal L4 rate approximation, USD per GPU-second. ``$0.80/hr / 3600``.
L4_GPU_RATE_PER_SECOND: Final[float] = 0.80 / 3600.0

#: Conservative per-cell timeout ceiling in seconds. The Modal function
#: is configured with the same value; the budget estimator uses this to
#: bound worst-case cost.
CELL_TIMEOUT_SECONDS: Final[int] = 1800

#: Concurrent-container ceiling per user request. The budget estimator
#: uses this to derive a wall-clock bound.
MAX_CONTAINERS: Final[int] = 10


@dataclass(frozen=True)
class BudgetEstimate:
    """Conservative Modal-cost estimate for one Wave 0 sweep dispatch."""

    n_cells: int
    max_containers: int
    cell_timeout_seconds: int
    gpu_rate_per_second: float
    conservative_cost_usd: float
    wallclock_upper_bound_seconds: float
    wallclock_upper_bound_cost_usd: float
    hard_cap_usd: float
    within_hard_cap: bool


def estimate_cost_usd(
    n_cells: int,
    *,
    hard_cap_usd: float = 10.0,
    max_containers: int = MAX_CONTAINERS,
    cell_timeout_seconds: int = CELL_TIMEOUT_SECONDS,
    gpu_rate_per_second: float = L4_GPU_RATE_PER_SECOND,
) -> BudgetEstimate:
    """Return a conservative Modal-cost estimate for ``n_cells``.

    Two figures:

    * ``conservative_cost_usd`` — every cell burns its full timeout, sums
      linearly. Used to decide whether to refuse the run.
    * ``wallclock_upper_bound_cost_usd`` — cells fan out over
      ``max_containers`` in parallel; each wave burns its full timeout.
      Reflects the wall-clock-bounded figure the build brief cites.

    ``within_hard_cap`` is true iff ``conservative_cost_usd <=
    hard_cap_usd``. The Modal entrypoint refuses to dispatch when this
    is false, per the build brief's ``$10`` cap.
    """
    if n_cells < 0:
        raise ValueError("n_cells must be non-negative")
    if max_containers < 1:
        raise ValueError("max_containers must be positive")
    if cell_timeout_seconds < 1:
        raise ValueError("cell_timeout_seconds must be positive")
    if gpu_rate_per_second < 0:
        raise ValueError("gpu_rate_per_second must be non-negative")
    conservative = n_cells * cell_timeout_seconds * gpu_rate_per_second
    waves = math.ceil(n_cells / max_containers) if n_cells else 0
    wallclock_seconds = waves * cell_timeout_seconds
    wallclock_cost = (
        waves * min(n_cells, max_containers) * cell_timeout_seconds * gpu_rate_per_second
    )
    return BudgetEstimate(
        n_cells=n_cells,
        max_containers=max_containers,
        cell_timeout_seconds=cell_timeout_seconds,
        gpu_rate_per_second=gpu_rate_per_second,
        conservative_cost_usd=conservative,
        wallclock_upper_bound_seconds=float(wallclock_seconds),
        wallclock_upper_bound_cost_usd=wallclock_cost,
        hard_cap_usd=hard_cap_usd,
        within_hard_cap=conservative <= hard_cap_usd,
    )


# --------------------------------------------------------------------------- #
# Local dispatcher (CPU-only; used by CLI and by tests)
# --------------------------------------------------------------------------- #


def run_local(
    cells: Sequence[CellPlan],
    *,
    on_cell: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    """Execute every cell locally on the current process.

    Wave 0 Modal dispatch calls :func:`execute_cell` inside a container;
    this helper is the CPU-only equivalent used by the CLI and by
    regression tests. Returns the list of per-cell payloads (rows +
    coverage + wall_seconds), in cell order.
    """
    payloads: list[dict[str, Any]] = []
    for cell in cells:
        payload = execute_cell(cell.to_dict())
        payloads.append(payload)
        if on_cell is not None:
            on_cell(payload)
    return payloads


def merge_payloads(payloads: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Merge per-cell payloads into a run-level manifest.

    The merged payload carries the flattened baseline rows, the
    per-cell wall-clock and coverage receipts, and the aggregated
    variance summary produced by :func:`summarize_rows`. This is the
    full raw receipt; :func:`slim_public_summary` drops the per-row
    data for the committed public receipt path.
    """
    rows: list[dict[str, Any]] = []
    cell_receipts: list[dict[str, Any]] = []
    for payload in payloads:
        rows.extend(payload.get("rows", []))
        cell_receipts.append(
            {
                "cell": payload.get("cell"),
                "coverage": payload.get("coverage"),
                "wall_seconds": payload.get("wall_seconds"),
                "n_rows": len(payload.get("rows", [])),
            }
        )
    summary = summarize_rows(rows)
    return {
        "kind": "cogr_wave0_calibration_run",
        "cells": cell_receipts,
        "rows": rows,
        "summary": summary,
    }


def slim_public_summary(merged: Mapping[str, Any]) -> dict[str, Any]:
    """Return the merged payload with per-row baseline data removed.

    Wave 0's committed public receipt at
    ``experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json``
    intentionally keeps only the per-cell coverage receipts and the
    aggregated variance / threshold summary. The raw baseline rows
    live under gitignored ``artifacts/cogr_wave0/`` per ``AGENTS.md``.
    """
    slim = {
        "kind": "cogr_wave0_calibration_summary",
        "cells": list(merged.get("cells", [])),
        "summary": dict(merged.get("summary", {})),
    }
    if "manifest" in merged:
        slim["manifest"] = merged["manifest"]
    return slim


def write_calibration_summary(
    payload: Mapping[str, Any], out_path: Path
) -> None:
    """Write the merged payload as pretty-printed JSON.

    Wave 0's committed public receipt lives under
    ``experiments/concern_gated_retrieval_e2/wave0/results/`` (call with
    :func:`slim_public_summary` first). Raw per-episode receipts belong
    under gitignored ``artifacts/`` per ``AGENTS.md``.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


DEFAULT_SUMMARY_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "results" / "calibration_summary.json"
)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.concern_gated_retrieval_e2.wave0.calibrate",
        description=(
            "Wave 0 calibration orchestrator: runs the sweep locally and "
            "writes the calibration summary JSON. Modal fan-out lives in "
            "modal_l4_sweep.py."
        ),
    )
    parser.add_argument(
        "--preset",
        default="calibration",
        choices=("calibration", "smoke"),
        help=(
            "'calibration' runs the default 3-family x 3-density x 2-budget "
            "grid; 'smoke' runs a 1-cell subset for CI-time verification."
        ),
    )
    parser.add_argument(
        "--seeds-per-cell",
        type=int,
        default=DEFAULT_SEEDS_PER_CELL,
        help="Cap on the seed batch size per (family, density) cell.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_SUMMARY_PATH,
        help="Path for the calibration summary JSON.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the cell plan and cost estimate without running.",
    )
    return parser


def _preset_cells(preset: str, seeds_per_cell: int) -> tuple[CellPlan, ...]:
    if preset == "smoke":
        return build_cells(
            families=("delayed_commitments",),
            density_levels=("light",),
            budgets=(2,),
            epsilons=(0.05,),
            seeds_per_cell=min(seeds_per_cell, 4),
        )
    if preset == "calibration":
        return build_cells(seeds_per_cell=seeds_per_cell)
    raise ValueError(f"unknown preset {preset!r}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _cli_parser()
    args = parser.parse_args(argv)
    cells = _preset_cells(args.preset, args.seeds_per_cell)
    estimate = estimate_cost_usd(len(cells))
    print(
        json.dumps(
            {
                "kind": "cogr_wave0_calibration_plan",
                "preset": args.preset,
                "n_cells": len(cells),
                "seeds_per_cell": args.seeds_per_cell,
                "estimate": {
                    "conservative_cost_usd": estimate.conservative_cost_usd,
                    "wallclock_upper_bound_cost_usd": (
                        estimate.wallclock_upper_bound_cost_usd
                    ),
                    "wallclock_upper_bound_seconds": (
                        estimate.wallclock_upper_bound_seconds
                    ),
                    "hard_cap_usd": estimate.hard_cap_usd,
                    "within_hard_cap": estimate.within_hard_cap,
                    "max_containers": estimate.max_containers,
                    "gpu_rate_per_second": estimate.gpu_rate_per_second,
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not estimate.within_hard_cap:
        print(
            "Refusing to run: conservative cost estimate exceeds hard cap.",
        )
        return 1
    if args.dry_run:
        return 0
    payloads = run_local(cells)
    merged = merge_payloads(payloads)
    write_calibration_summary(slim_public_summary(merged), args.out)
    print(f"Wrote calibration summary to {args.out}")
    return 0


__all__ = [
    "BEST_MATCHED_BASELINES",
    "BOUNDED_REWARD_HIGH",
    "BOUNDED_REWARD_LOW",
    "BOUNDED_REWARD_RANGE",
    "BudgetEstimate",
    "CANDIDATE_MECHANISM_NAME",
    "CEILING_BASELINE",
    "CELL_TIMEOUT_SECONDS",
    "CellPlan",
    "DEFAULT_BUDGET_GRID",
    "DEFAULT_SEEDS_PER_CELL",
    "DEFAULT_SUMMARY_PATH",
    "DENSITY_LEVELS",
    "EPSILON_GRID",
    "FAMILIES",
    "L4_GPU_RATE_PER_SECOND",
    "MAX_CONTAINERS",
    "NON_CEILING_TOLERANCE",
    "build_cells",
    "estimate_cost_usd",
    "execute_cell",
    "main",
    "merge_payloads",
    "run_local",
    "slim_public_summary",
    "summarize_rows",
    "write_calibration_summary",
]


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
