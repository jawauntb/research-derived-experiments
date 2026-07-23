#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 fan-out for the Concern-Gated Retrieval Wave 1a E2a confirmatory
sweep.

Wave 1a operating rules (see
``docs/concern_gated_retrieval_research_program.md`` and
``experiments/concern_gated_retrieval_e2/wave1a/PREREGISTRATION.md``):

* L4 GPU only. Modal H100 is explicitly forbidden by the wave rule
  (``PREREGISTRATION.md`` §7).
* ``max_containers=32`` — explicitly authorized by the human director for
  Wave 1a; Wave 0's ``max_containers=10`` ceiling does not apply.
* ``single_use_containers=True``, ``retries=1``, ``cpu=4``,
  ``memory=16384``, ``timeout=1800`` per the build brief.
* Doppler scope: ``/Users/jawaun/superoptimizers``.
* Deploy the image before spawning (per the deployed-image rule); the
  deployed image hash is recorded in ``PROVENANCE.md``.
* Budget guard: refuse to dispatch if the conservative timeout-based
  cost estimate exceeds ``$20`` (build brief).

App name: ``research-derived-cogr-wave1a-e2a``.

Cell shape
----------

A cell is one ``(family, seed_batch)`` pair from the confirmatory seed
allocation in ``PREREGISTRATION.md`` §7:

* ``delayed_commitments``: seeds ``200000..200299``
* ``maintenance_fault``:  seeds ``200300..200599``
* ``resource_constrained``: seeds ``200600..200899``

The default cell plan is one cell per family (300 confirmatory seeds
each). The on-line-learned variants (``ONLINE_IPS``, ``ONLINE_DR``)
apply a mirror-descent update to a running concern-anchor prior between
episodes; that sequential dependency makes per-family cells the
natural granularity. Reserved replay seeds ``200900..201999`` are NOT
touched by the default plan; they are opened only when a fatal gate in
``PREREGISTRATION.md`` §5 fails and the ex-ante replay knobs in §7 are
exercised.

Every cell writes one payload per arm per seed to the raw artifact at
``artifacts/cogr_wave1a/e2a_rows.json``. The downstream
``run_confirmatory.py`` aggregator reshapes those rows into
per-family :class:`SpecificityReport` objects, runs the
propensity-weighted coverage audit, scores every family through
:func:`score_e2a_all`, and writes the screen verdict to
``experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json``.

Anti-leakage boundary
---------------------

The cell function is *evaluator-side* orchestration code. It composes
:func:`experiments.concern_gated_retrieval_e2.wave1a.e2a_runner.run_e2a_episode`
which is the single choke point where the sealed
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedEnvironment`
is constructed and where the policy-side nomination callable is passed
through :meth:`IntegrityAudit.assert_clean`. The receipts and outcomes
returned by :func:`run_e2a_episode` are policy-visible; the
answer-key node list (``EpisodeSpec._answer_key``) is copied through
into the cell payload for evaluator-side computation of the family
``TCR(f)`` in the aggregator, and it never enters a policy callable.

Wave 0 reuse
------------

* :func:`~experiments.concern_gated_retrieval_e2.wave0.graph_learn.build_withheld_graph`
  supplies the fixed withheld geometry indirectly, through the Wave 0
  family generators. Wave 1a does not learn edges.
* :class:`~experiments.concern_gated_retrieval_e2.wave0.concern_update.LoggedProbePolicy`
  is the sole exploration surface. Every receipt-producing arm goes
  through it with ``epsilon = DEFAULT_EPSILON`` (Wave 1a §5.1 floor).
* :func:`~experiments.concern_gated_retrieval_e2.wave0.concern_update.update_concern`
  supplies the calibration-mode off-policy update. Wave 0's helper
  refuses confirmatory batches at its calibration entry point; per
  ``PREREGISTRATION.md`` §5.2, Wave 1a's *confirmatory sweep* is
  authorized to consume confirmatory receipts. :func:`_apply_online_update`
  in this module mirrors the identical math of ``update_concern`` for a
  single-receipt confirmatory batch, so the sweep can carry a running
  concern-anchor prior across confirmatory episodes without editing any
  Wave 0 file.

Wave 1a scope
-------------

This sweep CAN reject the concern-update rule (via the fatal gates the
downstream aggregator scores). It CANNOT establish learned memory
geometry (Wave 1b / COGR-E2b), the L1 dual-source-retrieval mechanism
claim (Wave 1b), or the L2 history-derived-concern-recovery claim
(also Wave 1b). Per the honor-the-preregistration rule, only the knobs
enumerated in ``PREREGISTRATION.md`` §7 may be rerun after a KILL.
"""

from __future__ import annotations

import importlib
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence


# Extend ``sys.path`` for two runtimes:
#   * inside the Modal container the repo lives at ``/root/project`` (see
#     :func:`_image` below);
#   * locally (dry-run, ``modal deploy``) the repo root is the first
#     ancestor that contains ``experiments/``.
sys.path.insert(0, "/root/project")
for _parent in Path(__file__).resolve().parents:
    if (_parent / "experiments").exists():
        sys.path.insert(0, str(_parent))
        break


modal = importlib.import_module("modal")


# --------------------------------------------------------------------------- #
# Modal constants (frozen at the wave build brief)
# --------------------------------------------------------------------------- #


APP_NAME: Final[str] = "research-derived-cogr-wave1a-e2a"
GPU: Final[str] = "L4"
TIMEOUT_SECONDS: Final[int] = 1800
CPU: Final[int] = 4
MEMORY_MB: Final[int] = 16_384
#: Concurrent-container ceiling. Wave 1a explicitly authorises up to 32
#: containers (PREREGISTRATION.md §7); Wave 0's ``10`` cap does not apply.
CONTAINER_CEILING: Final[int] = 32
#: Modal L4 rate approximation in USD per GPU-second (``$0.80/hr / 3600``).
GPU_RATE_PER_SECOND: Final[float] = 0.80 / 3600.0
#: Budget hard cap. The Modal local entrypoint refuses to dispatch if the
#: conservative timeout-based estimate exceeds this value.
HARD_CAP_USD: Final[float] = 20.0


# --------------------------------------------------------------------------- #
# Confirmatory seed allocation (PREREGISTRATION.md §7)
# --------------------------------------------------------------------------- #


#: Preregistered per-family confirmatory seed range (§7 allocation table).
#:
#: These are the ranges named in ``PREREGISTRATION.md`` §7. Two of the
#: three families accept them as-is (``delayed_commitments`` and
#: ``maintenance_fault`` both admit the whole confirmatory pool
#: ``200000..201999``). The third family, ``resource_constrained``, only
#: exposes 32 confirmatory templates in the Wave 0 generator
#: (``CONFIRMATORY_SEED_START = 200_200``,
#: ``CONFIRMATORY_SEED_END = 200_232``) — the wave1a §7 allocation
#: ``200600..200899`` is outside the generator's accepted range and would
#: raise ``ValueError`` at ``TemplateBucket.CONFIRMATION`` dispatch.
#: ``FAMILY_SEED_RANGES`` therefore resolves that family's range from the
#: generator's actual ``confirmatory_seeds()`` while keeping the other
#: two families on the §7 allocation. The resulting per-family sample
#: sizes are ``(300, 300, 32)``; a redesigned preregistration that grows
#: ``resource_constrained``'s confirmatory template pool would restore
#: full 300-seed power on that family (currently a scaffold gap, not a
#: post-hoc knob swap).
#:
#: Calibration seeds ``100000..100999`` are inaccessible; the Wave 0
#: template-split guard raises :class:`LeakageError` on misuse. Wave 1a
#: runs with ``COGR_WAVE0_CONFIRMATORY_RUN=1`` set at Modal spawn time.
def _resolve_family_seed_ranges() -> Mapping[str, tuple[int, ...]]:
    """Return the per-family confirmatory seed tuples used by the sweep."""

    # Delayed / maintenance families accept the §7 slice directly.
    # Resource-constrained is clamped to the generator's actual
    # confirmatory range because its confirmatory template count is 32
    # (scaffold limit; the preregistration §7 ``200600..200899`` slice
    # would be refused at dispatch).
    from experiments.concern_gated_retrieval_e2.wave0.families import (
        resource_constrained as _rc_family,
    )

    return {
        "delayed_commitments": tuple(range(200_000, 200_299 + 1)),
        "maintenance_fault": tuple(range(200_300, 200_599 + 1)),
        "resource_constrained": _rc_family.confirmatory_seeds(),
    }


FAMILY_SEED_RANGES: Final[Mapping[str, tuple[int, ...]]] = _resolve_family_seed_ranges()


#: The §7 preregistered slice for ``resource_constrained``, kept as an
#: informational constant so downstream provenance receipts document the
#: divergence from the family generator's actual accepted range.
PREREGISTERED_RESOURCE_CONSTRAINED_RANGE: Final[tuple[int, int]] = (
    200_600,
    200_899,
)


#: Reserved replay range from ``PREREGISTRATION.md`` §7.  Only replayable
#: knobs (LoggedProbePolicy.epsilon up to 0.10, update_concern.eta in
#: [0.05, 0.20], cell-level rejection replay capped at 30%) may draw
#: seeds from here.  Never entered by the default plan.
REPLAY_RESERVE_RANGE: Final[tuple[int, int]] = (200_900, 201_999)


DEFAULT_ARTIFACT_PATH: Final[Path] = Path("artifacts/cogr_wave1a/e2a_rows.json")


# --------------------------------------------------------------------------- #
# Arm / condition names — kept as literals so the container's imports
# below don't need the wave1a.specificity / wave1a.conditions modules at
# module load time (the modules are imported inside :func:`execute_cell`).
# --------------------------------------------------------------------------- #


ARM_FROZEN_WRONG: Final[str] = "frozen_wrong"
ARM_ONLINE_IPS: Final[str] = "online_learned_ips"
ARM_ONLINE_DR: Final[str] = "online_learned_dr"
COMPARATOR_INFO_MATCHED_VALUE: Final[str] = "info_matched_value"
COMPARATOR_INFO_MATCHED_PRIORITY: Final[str] = "info_matched_priority"
COMPARATOR_INFO_MATCHED_RECENCY: Final[str] = "info_matched_recency"
COMPARATOR_WRONG_AGENT: Final[str] = "wrong_agent"
CONDITION_ARM_SHUFFLED: Final[str] = "condition::shuffled"
CONDITION_ARM_WRONG_AGENT: Final[str] = "condition::wrong_agent"
CONDITION_ARM_ORACLE: Final[str] = "condition::oracle_ceiling"


#: Arms that populate :class:`SpecificityRow.rewards` in the downstream
#: aggregator.  These are the seven canonical Wave 1a specificity slots.
SPECIFICITY_ARMS: Final[tuple[str, ...]] = (
    ARM_FROZEN_WRONG,
    ARM_ONLINE_IPS,
    ARM_ONLINE_DR,
    COMPARATOR_INFO_MATCHED_VALUE,
    COMPARATOR_INFO_MATCHED_PRIORITY,
    COMPARATOR_INFO_MATCHED_RECENCY,
    COMPARATOR_WRONG_AGENT,
)


#: Arms whose receipts enter the coverage audit (``PREREGISTRATION.md``
#: §5.1). C2a, C2b, C4, C5 receipts are gated; C1 baseline receipts are
#: not (the baseline concern is fixed by construction).
COVERAGE_AUDIT_ARMS: Final[tuple[str, ...]] = (
    ARM_ONLINE_IPS,
    ARM_ONLINE_DR,
    CONDITION_ARM_SHUFFLED,
    CONDITION_ARM_WRONG_AGENT,
)


# --------------------------------------------------------------------------- #
# CellPlan
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CellPlan:
    """One ``(family, seed_batch)`` cell to run on Modal.

    Serialisable to a plain dict via :meth:`to_dict` so Modal can pass
    the plan across container boundaries. :meth:`from_dict` is the only
    supported deserialization; ad-hoc ``**kwargs`` construction is
    intentionally not exposed to callers.

    Attributes
    ----------
    family:
        One of ``delayed_commitments`` / ``maintenance_fault`` /
        ``resource_constrained``.
    seeds:
        Confirmatory seeds in the family's allocation from
        ``PREREGISTRATION.md`` §7. Every seed lies in ``[200000, 201999]``;
        the Wave 0 family generators refuse anything else at
        ``TemplateBucket.CONFIRMATION``.
    cell_id:
        Stable identifier of the shape
        ``cogr-wave1a::{family}::seeds{lo}-{hi}``. Used as a receipt key.
    """

    family: str
    seeds: tuple[int, ...]
    cell_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "seeds": list(self.seeds),
            "cell_id": self.cell_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CellPlan":
        return cls(
            family=str(data["family"]),
            seeds=tuple(int(s) for s in data["seeds"]),
            cell_id=str(data["cell_id"]),
        )


def build_cells(
    *,
    families: Sequence[str] = tuple(FAMILY_SEED_RANGES),
    seed_batch_size: int | None = None,
) -> tuple[CellPlan, ...]:
    """Return the confirmatory cell plan.

    The default plan produces one cell per family covering the family's
    entire confirmatory seed tuple in :data:`FAMILY_SEED_RANGES` (300
    seeds for ``delayed_commitments`` / ``maintenance_fault``, 32 for
    ``resource_constrained``; see the constant's docstring for the
    scaffold gap on the third family). Passing an explicit
    ``seed_batch_size`` splits each family's range into contiguous
    batches; use this only for smoke runs — the on-line-learned variants
    depend on the sequential order of seeds inside a cell so cross-cell
    splits break the running concern state.
    """
    unknown = tuple(f for f in families if f not in FAMILY_SEED_RANGES)
    if unknown:
        raise ValueError(f"unknown families: {unknown!r}")
    if seed_batch_size is not None and seed_batch_size <= 0:
        raise ValueError("seed_batch_size must be positive when provided")

    cells: list[CellPlan] = []
    for family in families:
        seeds = tuple(FAMILY_SEED_RANGES[family])
        if not seeds:
            continue
        if seed_batch_size is None:
            batches: list[tuple[int, ...]] = [seeds]
        else:
            batches = [
                tuple(seeds[i : i + seed_batch_size])
                for i in range(0, len(seeds), seed_batch_size)
            ]
        for batch in batches:
            if not batch:
                continue
            cell_id = (
                f"cogr-wave1a::{family}::seeds{batch[0]}-{batch[-1]}"
            )
            cells.append(
                CellPlan(family=family, seeds=batch, cell_id=cell_id)
            )
    return tuple(cells)


# --------------------------------------------------------------------------- #
# Budget guard
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BudgetEstimate:
    """Conservative Modal-cost estimate for one Wave 1a sweep dispatch."""

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
    hard_cap_usd: float = HARD_CAP_USD,
    max_containers: int = CONTAINER_CEILING,
    cell_timeout_seconds: int = TIMEOUT_SECONDS,
    gpu_rate_per_second: float = GPU_RATE_PER_SECOND,
) -> BudgetEstimate:
    """Return a conservative Modal-cost estimate for ``n_cells``.

    Two figures:

    * ``conservative_cost_usd`` — every cell burns its full timeout, sums
      linearly. Used to decide whether to refuse the run.
    * ``wallclock_upper_bound_cost_usd`` — cells fan out over
      ``max_containers`` in parallel; each wave burns its full timeout.

    ``within_hard_cap`` is true iff
    ``conservative_cost_usd <= hard_cap_usd``. The Modal entrypoint
    refuses to dispatch when this is false, per the build brief's ``$20``
    cap.
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
        waves
        * min(n_cells, max_containers)
        * cell_timeout_seconds
        * gpu_rate_per_second
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
# Confirmatory-mode online update helper
# --------------------------------------------------------------------------- #


def _apply_online_update(
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
    """Apply one confirmatory-mode IPS/DR mirror-descent step.

    Mirrors the math of
    :func:`experiments.concern_gated_retrieval_e2.wave0.concern_update.update_concern`
    for a single-receipt batch. The Wave 0 helper refuses confirmatory
    receipts at its calibration entry point; ``PREREGISTRATION.md`` §5.2
    explicitly authorises Wave 1a's confirmatory sweep to accumulate
    ``template_family_split = "confirmatory"`` receipts under the
    concern-update rule, so we inline the identical step here without
    editing any Wave 0 file.

    The estimator, poisoning guard (single ``source_id`` at magnitude
    ``max_source_influence``), and multiplicative mirror-descent step
    with ``weight_clip`` match Wave 0's implementation exactly. On the
    single-receipt DR path a per-candidate baseline is used when
    ``dr_baseline`` is supplied (the sweep runner accumulates a running
    per-candidate mean-reward table for this).
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

    # Multiplicative (exponentiated) mirror-descent step.
    updated: dict[str, float] = {}
    for anchor, w in prior.items():
        v = aggregated.get(anchor, 0.0)
        w_new = float(w) * math.exp(float(eta) * v)
        if not math.isfinite(w_new):
            w_new = wclip if v > 0 else 0.0
        w_new = max(0.0, min(wclip, w_new))
        updated[anchor] = w_new
    return updated


# --------------------------------------------------------------------------- #
# Cell execution
# --------------------------------------------------------------------------- #


def execute_cell(cell_dict: Mapping[str, Any]) -> dict[str, Any]:
    """Run one Wave 1a confirmatory cell locally.

    Called by :func:`run_cell` on the Modal side and directly by tests /
    the local dispatch path.  Emits per-arm rows for each ``(family,
    seed)`` in the plan:

    * seven arms populate :class:`SpecificityRow.rewards` in the
      downstream aggregator: ``frozen_wrong``, ``online_learned_ips``,
      ``online_learned_dr``, ``info_matched_value``,
      ``info_matched_priority``, ``info_matched_recency``, and
      ``wrong_agent`` (the ranker-level wrong-agent comparator);
    * three condition-level arms populate the coverage audit and the
      diagnostic ceiling receipt: ``condition::shuffled``,
      ``condition::wrong_agent``, and ``condition::oracle_ceiling``.

    The ``online_learned_ips`` and ``online_learned_dr`` arms use a
    running concern-anchor prior updated via
    :func:`_apply_online_update` after every seed. The remaining arms
    use the frozen wrong prior held constant across seeds.
    """
    # Container-side import shim.
    import sys as _sys

    _sys.path.insert(0, "/root/project")

    # Wave 0 primitives.
    from experiments.concern_gated_retrieval_e2.wave0.baselines import (
        info_matched_priority,
        info_matched_recency,
        info_matched_value,
        wrong_agent_concern,
    )
    from experiments.concern_gated_retrieval_e2.wave0.concern_update import (
        DEFAULT_ETA,
        DEFAULT_MAX_SOURCE_INFLUENCE,
        DEFAULT_WEIGHT_CLIP,
    )
    from experiments.concern_gated_retrieval_e2.wave0.families import (
        delayed_commitments as _dc_family,
        maintenance_fault as _mf_family,
        resource_constrained as _rc_family,
    )
    from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
        EpisodeContext,
    )
    from experiments.concern_gated_retrieval_e2.wave0.template_split import (
        TemplateBucket,
    )
    from experiments.concern_gated_retrieval_e2.wave1a.conditions import (
        CONDITIONS,
        FROZEN_WRONG,
        ORACLE_CEILING,
        SHUFFLED,
        WRONG_AGENT,
    )
    from experiments.concern_gated_retrieval_e2.wave1a.e2a_runner import (
        run_e2a_episode,
    )

    plan = CellPlan.from_dict(cell_dict)

    generators = {
        _dc_family.FAMILY_NAME: _dc_family.generate_episode,
        _mf_family.FAMILY_NAME: _mf_family.generate_episode,
        _rc_family.FAMILY_NAME: _rc_family.generate_episode,
    }
    if plan.family not in generators:
        raise ValueError(f"unknown Wave 0 family: {plan.family!r}")
    generator = generators[plan.family]

    def _concern_biased_factory(concern: Mapping[str, float]):
        """Return a Wave 1a-style nomination factory over ``concern``.

        Byte-identical to the scaffold ``_concern_biased_ranker`` in
        :mod:`experiments.concern_gated_retrieval_e2.wave1a.e2a_runner`;
        re-declared here so the sweep runner can pass a factory whose
        concern is *the sweep's running concern*, not the condition's
        initial factory output.
        """
        snap = dict(concern)

        def factory(_concern_from_condition: Mapping[str, float]):
            def rank(context: EpisodeContext):
                return tuple(
                    sorted(
                        context.candidate_nodes,
                        key=lambda n: (-float(snap.get(n, 0.0)), n),
                    )
                )

            return rank

        return factory

    def _wrap_baseline_as_factory(baseline):
        """Adapt a Wave 0 ``RankFn`` into a Wave 1a nomination factory."""

        def factory(_concern: Mapping[str, float]):
            def nomination(context: EpisodeContext):
                budget = int(context.budget)
                if budget <= 0:
                    budget = len(context.candidate_nodes)
                return baseline(context, budget)

            return nomination

        return factory

    baseline_factories = {
        COMPARATOR_INFO_MATCHED_VALUE: _wrap_baseline_as_factory(info_matched_value),
        COMPARATOR_INFO_MATCHED_PRIORITY: _wrap_baseline_as_factory(
            info_matched_priority
        ),
        COMPARATOR_INFO_MATCHED_RECENCY: _wrap_baseline_as_factory(
            info_matched_recency
        ),
        COMPARATOR_WRONG_AGENT: _wrap_baseline_as_factory(wrong_agent_concern),
    }

    frozen_condition = CONDITIONS[FROZEN_WRONG]
    shuffled_condition = CONDITIONS[SHUFFLED]
    wrong_agent_condition = CONDITIONS[WRONG_AGENT]
    oracle_condition = CONDITIONS[ORACLE_CEILING]

    # Running concern-anchor priors for the on-line-learned variants.
    # Initialised from the *first* episode's ``care_anchors`` — the Wave
    # 0 wrong prior. The generator is pure in ``(seed, bucket)`` so this
    # is byte-identical across processes.
    running_ips: dict[str, float] | None = None
    running_dr: dict[str, float] | None = None
    #: DR baseline table: running per-candidate mean realized reward.
    dr_reward_sum: dict[str, float] = {}
    dr_reward_count: dict[str, int] = {}
    dr_global_sum = 0.0
    dr_global_count = 0

    def _dr_baseline_snapshot() -> dict[str, float]:
        global_mean = (
            dr_global_sum / dr_global_count if dr_global_count > 0 else 0.0
        )
        snap: dict[str, float] = {}
        for cand, cnt in dr_reward_count.items():
            if cnt >= 2:
                snap[cand] = dr_reward_sum[cand] / cnt
            else:
                snap[cand] = global_mean
        return snap

    start = time.time()
    rows: list[dict[str, Any]] = []

    for seed in plan.seeds:
        episode = generator(
            seed=int(seed), bucket=TemplateBucket.CONFIRMATION
        )

        # Evaluator-side snapshot of the answer key for the aggregator's
        # per-family TCR union. Never passed into a policy callable.
        answer_key_nodes = tuple(episode._answer_key)  # noqa: SLF001

        # First-seed initialisation from the family generator's wrong prior.
        if running_ips is None:
            running_ips = dict(episode.care_anchors)
        if running_dr is None:
            running_dr = dict(episode.care_anchors)

        # ------------------------------------------------------------- #
        # Specificity slate — seven arms scored on the SAME sealed episode
        # ------------------------------------------------------------- #

        # ARM_FROZEN_WRONG (C1 baseline).
        r_c1 = run_e2a_episode(
            episode, frozen_condition, rng_seed=int(seed)
        )
        rows.append(
            _row_from_result(
                plan=plan,
                seed=int(seed),
                episode_id=episode.episode_id,
                arm=ARM_FROZEN_WRONG,
                arm_kind="specificity",
                condition_name=FROZEN_WRONG,
                result=r_c1,
                answer_key_nodes=answer_key_nodes,
            )
        )

        # ARM_ONLINE_IPS (C2a) — running concern injected via factory.
        ips_factory = _concern_biased_factory(running_ips)
        r_ips = run_e2a_episode(
            episode,
            frozen_condition,
            rng_seed=int(seed),
            nomination_factory=ips_factory,
        )
        rows.append(
            _row_from_result(
                plan=plan,
                seed=int(seed),
                episode_id=episode.episode_id,
                arm=ARM_ONLINE_IPS,
                arm_kind="specificity",
                condition_name="online_learned_ips",
                result=r_ips,
                answer_key_nodes=(),
            )
        )
        # Update the running IPS concern for the next seed.
        running_ips = _apply_online_update(
            prior=running_ips,
            candidate=r_ips.receipt.candidate,
            selection_propensity=float(r_ips.receipt.selection_propensity),
            realized_reward=float(r_ips.outcome.realized_reward),
            source_id=r_ips.receipt.source_id,
            estimator="ips",
            eta=DEFAULT_ETA,
            max_source_influence=DEFAULT_MAX_SOURCE_INFLUENCE,
            weight_clip=DEFAULT_WEIGHT_CLIP,
        )

        # ARM_ONLINE_DR (C2b) — same channel with a doubly-robust update.
        dr_factory = _concern_biased_factory(running_dr)
        r_dr = run_e2a_episode(
            episode,
            frozen_condition,
            rng_seed=int(seed),
            nomination_factory=dr_factory,
        )
        rows.append(
            _row_from_result(
                plan=plan,
                seed=int(seed),
                episode_id=episode.episode_id,
                arm=ARM_ONLINE_DR,
                arm_kind="specificity",
                condition_name="online_learned_dr",
                result=r_dr,
                answer_key_nodes=(),
            )
        )
        # Update the DR baseline table BEFORE applying the update, so
        # the estimator uses the pre-update snapshot as its baseline.
        dr_snapshot = _dr_baseline_snapshot()
        cand_dr = r_dr.receipt.candidate
        reward_dr = float(r_dr.outcome.realized_reward)
        dr_reward_sum[cand_dr] = dr_reward_sum.get(cand_dr, 0.0) + reward_dr
        dr_reward_count[cand_dr] = dr_reward_count.get(cand_dr, 0) + 1
        dr_global_sum += reward_dr
        dr_global_count += 1
        running_dr = _apply_online_update(
            prior=running_dr,
            candidate=cand_dr,
            selection_propensity=float(r_dr.receipt.selection_propensity),
            realized_reward=reward_dr,
            source_id=r_dr.receipt.source_id,
            estimator="dr",
            eta=DEFAULT_ETA,
            max_source_influence=DEFAULT_MAX_SOURCE_INFLUENCE,
            weight_clip=DEFAULT_WEIGHT_CLIP,
            dr_baseline=dr_snapshot,
        )

        # COMPARATORS — Wave 0 baselines injected as nomination factory
        # against the frozen wrong prior. This isolates the *ranking*
        # signal from the *concern* signal: the concern is fixed at the
        # baseline row's value; only the ranker changes.
        for arm, baseline_factory in baseline_factories.items():
            r_cmp = run_e2a_episode(
                episode,
                frozen_condition,
                rng_seed=int(seed),
                nomination_factory=baseline_factory,
            )
            rows.append(
                _row_from_result(
                    plan=plan,
                    seed=int(seed),
                    episode_id=episode.episode_id,
                    arm=arm,
                    arm_kind="specificity",
                    condition_name=FROZEN_WRONG,
                    result=r_cmp,
                    answer_key_nodes=(),
                )
            )

        # ------------------------------------------------------------- #
        # Condition-only arms — receipts feed the coverage audit and the
        # diagnostic ceiling receipt. Their rewards do NOT enter
        # SpecificityRow.rewards.
        # ------------------------------------------------------------- #

        r_shuffled = run_e2a_episode(
            episode, shuffled_condition, rng_seed=int(seed)
        )
        rows.append(
            _row_from_result(
                plan=plan,
                seed=int(seed),
                episode_id=episode.episode_id,
                arm=CONDITION_ARM_SHUFFLED,
                arm_kind="condition",
                condition_name=SHUFFLED,
                result=r_shuffled,
                answer_key_nodes=(),
            )
        )
        r_wrong_agent = run_e2a_episode(
            episode, wrong_agent_condition, rng_seed=int(seed)
        )
        rows.append(
            _row_from_result(
                plan=plan,
                seed=int(seed),
                episode_id=episode.episode_id,
                arm=CONDITION_ARM_WRONG_AGENT,
                arm_kind="condition",
                condition_name=WRONG_AGENT,
                result=r_wrong_agent,
                answer_key_nodes=(),
            )
        )
        r_oracle = run_e2a_episode(
            episode, oracle_condition, rng_seed=int(seed)
        )
        rows.append(
            _row_from_result(
                plan=plan,
                seed=int(seed),
                episode_id=episode.episode_id,
                arm=CONDITION_ARM_ORACLE,
                arm_kind="condition",
                condition_name=ORACLE_CEILING,
                result=r_oracle,
                answer_key_nodes=(),
            )
        )

    wall = float(time.time() - start)
    return {
        "cell": plan.to_dict(),
        "rows": rows,
        "wall_seconds": wall,
        "n_rows": len(rows),
    }


def _row_from_result(
    *,
    plan: CellPlan,
    seed: int,
    episode_id: str,
    arm: str,
    arm_kind: str,
    condition_name: str,
    result: Any,
    answer_key_nodes: tuple[str, ...],
) -> dict[str, Any]:
    """Flatten one :class:`E2aEpisodeResult` into a JSON-safe row."""

    return {
        "family": plan.family,
        "seed": int(seed),
        "episode_id": episode_id,
        "arm": arm,
        "arm_kind": arm_kind,
        "condition": condition_name,
        "realized_reward": float(result.outcome.realized_reward),
        "constraint_preserved": bool(result.outcome.constraint_preserved),
        "misretrieval_cost": float(result.outcome.misretrieval_cost),
        "candidate": str(result.receipt.candidate),
        "selection_propensity": float(result.receipt.selection_propensity),
        "exploratory": bool(result.receipt.exploratory),
        "source_id": str(result.receipt.source_id),
        "template_family_split": str(result.receipt.template_family_split),
        "cell_id": plan.cell_id,
        # ``answer_key_nodes`` is evaluator-side; the aggregator uses
        # it to union the per-family TCR for the coverage audit. Kept
        # on the first arm per (family, seed) only to shrink the JSON.
        "answer_key_nodes": list(answer_key_nodes),
    }


def merge_payloads(payloads: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Merge per-cell payloads into a single receipt.

    The receipt shape carries the flattened row list, one entry per cell
    with its wall-clock and row count, and the aggregate row count so
    the aggregator can regression-check the total.
    """
    rows: list[dict[str, Any]] = []
    cell_receipts: list[dict[str, Any]] = []
    for payload in payloads:
        rows.extend(payload.get("rows", []))
        cell_receipts.append(
            {
                "cell": payload.get("cell"),
                "wall_seconds": payload.get("wall_seconds"),
                "n_rows": len(payload.get("rows", [])),
            }
        )
    return {
        "kind": "cogr_wave1a_e2a_run",
        "app_name": APP_NAME,
        "gpu": GPU,
        "cell_receipts": cell_receipts,
        "rows": rows,
        "n_rows_total": len(rows),
    }


def write_rows(payload: Mapping[str, Any], out_path: Path) -> None:
    """Write the merged payload as pretty-printed JSON."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# Modal function / entrypoint
# --------------------------------------------------------------------------- #


def _image() -> Any:
    """Return the Modal image the L4 workers run inside.

    Mirrors Wave 0's image so container behaviour is stable across the
    two waves. ``add_local_dir(".")`` ships the local project into
    ``/root/project``.
    """
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git")
        .pip_install(
            "numpy>=1.26,<2.2",
            "pytest>=8,<10",
            "ruff>=0.8,<1.0",
            "sentence-transformers>=3.0,<6",
            "torch>=2.3,<2.8",
            "uv>=0.7,<1.0",
        )
        .add_local_dir(
            ".",
            remote_path="/root/project",
            ignore=[
                ".git",
                ".worktrees",
                ".venv",
                "__pycache__",
                "*.pyc",
                "artifacts",
                "references/papers",
                "references/text",
                "references/html",
                "tmp",
                "output",
                "papers/*/paper.pdf",
                "papers/pdf",
                "**/*.png",
            ],
        )
    )


IMAGE = _image()
app = modal.App(name=APP_NAME)


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=CPU,
    memory=MEMORY_MB,
    max_containers=CONTAINER_CEILING,
    single_use_containers=True,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    """Run one Wave 1a confirmatory cell inside an L4 worker.

    ``arg`` is a plain dict shaped by :meth:`CellPlan.to_dict`. Returns
    ``{"cell": {...}, "rows": [...], "wall_seconds": ..., "n_rows": ...}``.
    The container re-imports :func:`execute_cell` locally so the Modal
    deploy step and the fan-out step exchange only plain dicts.
    """
    import sys as _sys

    _sys.path.insert(0, "/root/project")
    from experiments.concern_gated_retrieval_e2.wave1a.modal_l4_sweep import (
        execute_cell as _execute_cell,
    )

    return _execute_cell(arg)


def _preset_cells(preset: str) -> tuple[CellPlan, ...]:
    if preset == "confirmatory":
        return build_cells()
    if preset == "smoke":
        return build_cells(
            families=("delayed_commitments",),
            seed_batch_size=4,
        )[:1]
    raise SystemExit(f"unknown preset {preset!r}")


@app.local_entrypoint()
def main(
    preset: str = "confirmatory",
    out: str = str(DEFAULT_ARTIFACT_PATH),
    hard_cap_usd: float = HARD_CAP_USD,
    dry_run_budget: bool = False,
) -> None:
    """Modal local entrypoint. Fans out over cells and writes the rows JSON.

    Steps:

    1. Build the cell plan for ``preset``.
    2. Estimate cost. Refuse if the conservative timeout-based cost
       exceeds ``hard_cap_usd`` (default ``$20``).
    3. If ``dry_run_budget`` is truthy, print the plan and return.
    4. Fan out :func:`run_cell` across the cell list using ``.map`` and
       merge the per-cell payloads via :func:`merge_payloads`.
    5. Write the raw JSON receipt to ``out``
       (default ``artifacts/cogr_wave1a/e2a_rows.json``, a gitignored
       raw-artifacts path per ``AGENTS.md``). The public verdict is
       produced by :mod:`.run_confirmatory` from the raw receipt.
    """
    cells = _preset_cells(preset)
    estimate = estimate_cost_usd(
        len(cells),
        hard_cap_usd=hard_cap_usd,
        max_containers=CONTAINER_CEILING,
        cell_timeout_seconds=TIMEOUT_SECONDS,
        gpu_rate_per_second=GPU_RATE_PER_SECOND,
    )
    manifest = {
        "kind": "cogr_wave1a_modal_manifest",
        "app": APP_NAME,
        "preset": preset,
        "gpu": GPU,
        "cpu": CPU,
        "memory_mb": MEMORY_MB,
        "max_containers": CONTAINER_CEILING,
        "timeout_seconds": TIMEOUT_SECONDS,
        "gpu_rate_per_second": GPU_RATE_PER_SECOND,
        "n_cells": len(cells),
        "hard_cap_usd": hard_cap_usd,
        "confirmatory_seed_range": [200_000, 201_999],
        "replay_reserve_range": list(REPLAY_RESERVE_RANGE),
        "estimate": {
            "conservative_cost_usd": estimate.conservative_cost_usd,
            "wallclock_upper_bound_cost_usd": (
                estimate.wallclock_upper_bound_cost_usd
            ),
            "wallclock_upper_bound_seconds": (
                estimate.wallclock_upper_bound_seconds
            ),
            "within_hard_cap": estimate.within_hard_cap,
        },
    }
    print(
        json.dumps(
            {"kind": "dry-run manifest", "manifest": manifest},
            indent=2,
            sort_keys=True,
        )
    )

    if not estimate.within_hard_cap:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate.conservative_cost_usd:.2f} exceeds hard cap "
            f"${hard_cap_usd:.2f} (Wave 1a build brief)."
        )
    if dry_run_budget:
        return

    cell_args = [cell.to_dict() for cell in cells]
    payloads = list(run_cell.map(cell_args))
    merged = merge_payloads(payloads)
    merged["manifest"] = manifest

    raw_out_path = Path(out)
    write_rows(merged, raw_out_path)
    print(f"Wrote raw Wave 1a confirmatory rows to {raw_out_path}")


__all__ = [
    "APP_NAME",
    "ARM_FROZEN_WRONG",
    "ARM_ONLINE_DR",
    "ARM_ONLINE_IPS",
    "BudgetEstimate",
    "COMPARATOR_INFO_MATCHED_PRIORITY",
    "COMPARATOR_INFO_MATCHED_RECENCY",
    "COMPARATOR_INFO_MATCHED_VALUE",
    "COMPARATOR_WRONG_AGENT",
    "CONDITION_ARM_ORACLE",
    "CONDITION_ARM_SHUFFLED",
    "CONDITION_ARM_WRONG_AGENT",
    "CONTAINER_CEILING",
    "COVERAGE_AUDIT_ARMS",
    "CPU",
    "CellPlan",
    "DEFAULT_ARTIFACT_PATH",
    "FAMILY_SEED_RANGES",
    "GPU",
    "GPU_RATE_PER_SECOND",
    "HARD_CAP_USD",
    "IMAGE",
    "MEMORY_MB",
    "PREREGISTERED_RESOURCE_CONSTRAINED_RANGE",
    "REPLAY_RESERVE_RANGE",
    "SPECIFICITY_ARMS",
    "TIMEOUT_SECONDS",
    "app",
    "build_cells",
    "estimate_cost_usd",
    "execute_cell",
    "main",
    "merge_payloads",
    "run_cell",
    "write_rows",
]
