"""COGR-E2a Wave 1a fixed-prior control runners.

Wave 1a's screen decision rests on comparing the on-line-learned
concern-update variants (``ONLINE_IPS``, ``ONLINE_DR``) against four
fixed-prior conditions: the ``FROZEN_WRONG`` baseline, the ``SHUFFLED``
and ``WRONG_AGENT`` specificity controls, and the diagnostic
``ORACLE_CEILING`` (never promoted).  This module supplies the batch
runners the sweep uses to produce the confirmatory receipts for those
four fixed-prior conditions.

Public entry points
-------------------

* :func:`run_frozen_wrong` — baseline ``C1``.
* :func:`run_oracle_ceiling` — diagnostic ceiling ``C3``.  Reported for
  every family but the runner does **not** invoke
  :func:`~experiments.concern_gated_retrieval_e2.wave1a.conditions.promotion_admit_condition`
  on the oracle condition so a diagnostic receipt can still be emitted
  for the ceiling-headroom table.  The promotion harness itself refuses
  the oracle (``PromotionRefused`` on
  :func:`promotion_admit_condition`); callers who forward a
  :class:`ControlTrace` from this function into the promotion contest
  path get the refusal.  See
  ``wave1a/PREREGISTRATION.md`` §4 "Oracle is diagnostic".
* :func:`run_shuffled` — anchor-label-shuffled control ``C4``.
* :func:`run_wrong_agent` — different-agent-history control ``C5``.

Reuse boundary
--------------

Each runner iterates a caller-supplied seed sequence, generates the
sealed :class:`EpisodeSpec` for one Wave 0 procedural family via that
family's ``generate_episode`` (all under
:attr:`TemplateBucket.CONFIRMATION`), and delegates the per-episode
work to :func:`run_e2a_episode`.  Determinism is a first-class
contract: a given ``(family, seed)`` pair produces a byte-identical
:class:`ControlTrace` on every process because (1) the Wave 0 family
generators are pure in ``(seed, bucket, holdout)``, (2)
:class:`LoggedProbePolicy` is driven by a caller-supplied
``random.Random(rng_seed)`` and Wave 1a locks ``rng_seed = seed`` on
the control path, and (3) the fixed-prior conditions never mutate their
prior between episodes.

Anti-leakage
------------

Sealed :class:`EpisodeSpec` objects never leave this module; each is
handed straight to :func:`run_e2a_episode`, which is the single choke
point where the sealed environment is constructed.  The oracle and
wrong-agent factories are the only two Wave 1a factories that legally
dereference sealed fields, and they do so on the evaluator side of the
runner boundary — their numeric prior output is what the policy sees.
The runners here do not observe, evaluate, or dereference sealed fields
themselves.

Wave 1a scope
-------------

This module can only produce receipts for **fixed-prior** conditions;
the two on-line-learned variants live on a sibling sweep runner that
Wave 1a's confirmatory Modal launch composes.  A screen that fails on
one of the fatal gates in ``PREREGISTRATION.md`` §5 KILLs the
concern-update rule — the honor-the-preregistration rule forbids
post-hoc threshold, corpus, seed-range, or family swaps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Final, Mapping, Sequence, cast

from experiments.concern_gated_retrieval_e2.wave0.families import (
    delayed_commitments as _dc_family,
    maintenance_fault as _mf_family,
    resource_constrained as _rc_family,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
    ProceduralFamily,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1a.conditions import (
    CONDITIONS,
    Condition,
    FROZEN_WRONG,
    ORACLE_CEILING,
    SHUFFLED,
    WRONG_AGENT,
)
from experiments.concern_gated_retrieval_e2.wave1a.e2a_runner import (
    E2aEpisodeResult,
    run_e2a_episode,
)

__all__ = [
    "CONTROL_CONDITION_NAMES",
    "ControlTrace",
    "run_frozen_wrong",
    "run_oracle_ceiling",
    "run_shuffled",
    "run_wrong_agent",
]


#: Ordered tuple of the four control-runner condition names this module
#: exposes.  ``ORACLE_CEILING`` is included because the runner emits a
#: diagnostic-only receipt for it; ``ONLINE_IPS`` and ``ONLINE_DR`` are
#: not — they live on the sibling sweep runner.
CONTROL_CONDITION_NAMES: Final[tuple[str, ...]] = (
    FROZEN_WRONG,
    ORACLE_CEILING,
    SHUFFLED,
    WRONG_AGENT,
)


#: Dispatch table binding each Wave 0 procedural family name to its
#: sealed ``generate_episode`` callable.  Wave 1a control runners route
#: through this table so a caller-supplied ``family`` string is the
#: single source of truth for which family generator fires.
_FAMILY_GENERATORS: Final[Mapping[str, Callable[..., EpisodeSpec]]] = {
    _dc_family.FAMILY_NAME: _dc_family.generate_episode,
    _mf_family.FAMILY_NAME: _mf_family.generate_episode,
    _rc_family.FAMILY_NAME: _rc_family.generate_episode,
}


@dataclass(frozen=True)
class ControlTrace:
    """Batch receipt emitted by a Wave 1a control runner.

    A :class:`ControlTrace` is a byte-stable per-``(condition, family,
    seeds)`` receipt: the ``results`` field carries one
    :class:`E2aEpisodeResult` per input seed, in seed order, and the
    aggregate ``mean_realized_reward`` is the paired-seed reward mean
    Wave 1a's screen aggregator joins against.  Every field is frozen at
    construction and no field references a sealed :class:`EpisodeSpec`
    or an evaluator-only value.

    Attributes
    ----------
    condition_name:
        The Wave 1a condition name (``FROZEN_WRONG`` / ``ORACLE_CEILING``
        / ``SHUFFLED`` / ``WRONG_AGENT``).
    family:
        The Wave 0 procedural family this batch was drawn from.  One of
        ``delayed_commitments`` / ``maintenance_fault`` /
        ``resource_constrained``.
    seeds:
        The tuple of caller-supplied seeds in traversal order.  Every
        seed must lie in the confirmatory range
        ``[200000, 201999]`` — the Wave 0 family generators refuse a
        calibration seed for a :attr:`TemplateBucket.CONFIRMATION`
        request with :class:`ValueError`, so a mis-tagged seed fails
        early.
    results:
        One :class:`E2aEpisodeResult` per seed, in the same order as
        :attr:`seeds`.  ``len(results) == len(seeds)`` is enforced on
        construction.
    mean_realized_reward:
        Mean of :attr:`SealedOutcome.realized_reward` across
        :attr:`results`.  ``0.0`` on an empty batch (a caller who passes
        zero seeds).  This is the aggregate the screen decision rule
        (§6.3) consumes for the fixed-prior conditions; the on-line-
        learned variants are aggregated the same way on a sibling
        runner.
    sealed_env_evaluate_calls:
        Sum of :attr:`E2aEpisodeResult.sealed_env_evaluate_calls` across
        :attr:`results`.  Equal to ``len(results)`` on a successful
        batch — the sealed environment's single-shot rule is what makes
        this a regression check rather than an experiment knob.
    promotion_eligible:
        ``True`` when the condition is promotable, ``False`` for the
        diagnostic-only oracle ceiling.  Callers routing a
        :class:`ControlTrace` into the Wave 1a screen contest should
        gate on this flag first;
        :func:`promotion_admit_condition` on the underlying
        :class:`Condition` provides the enforced refusal.
    """

    condition_name: str
    family: ProceduralFamily
    seeds: tuple[int, ...]
    results: tuple[E2aEpisodeResult, ...]
    mean_realized_reward: float
    sealed_env_evaluate_calls: int
    promotion_eligible: bool

    #: Kept empty on the current control runners.  Reserved so the sweep
    #: aggregator can bolt on family-level diagnostics without a shape
    #: change to receipts already on disk.
    extras: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.condition_name, str) or not self.condition_name:
            raise ValueError("condition_name must be a non-empty string")
        if len(self.results) != len(self.seeds):
            raise ValueError(
                "ControlTrace.results and .seeds must have the same length; "
                f"got {len(self.results)} results vs {len(self.seeds)} seeds"
            )


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _validate_family(family: str) -> "ProceduralFamily":
    if not isinstance(family, str) or not family:
        raise TypeError("family must be a non-empty string")
    if family not in _FAMILY_GENERATORS:
        raise ValueError(
            f"unknown Wave 0 family: {family!r}; expected one of "
            f"{sorted(_FAMILY_GENERATORS)}"
        )
    return cast("ProceduralFamily", family)


def _validate_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    if isinstance(seeds, (str, bytes)):
        raise TypeError("seeds must be a Sequence[int], not a str/bytes")
    materialised = tuple(seeds)
    for i, seed in enumerate(materialised):
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError(
                f"seeds[{i}] must be a non-boolean int; got {type(seed).__name__}"
            )
    return materialised


def _run_batch(
    condition: Condition,
    family: str,
    seeds: Sequence[int],
) -> ControlTrace:
    """Common batch driver behind the four public control runners.

    The public runners differ only in which :class:`Condition` they
    dispatch to; the seed loop, family-generator dispatch, and
    aggregation shape are identical.  Consolidating them here keeps the
    determinism contract single-sourced: every fixed-prior control that
    Wave 1a runs walks the same code path.
    """

    family_name = _validate_family(family)
    seed_tuple = _validate_seeds(seeds)
    generator = _FAMILY_GENERATORS[family_name]

    results: list[E2aEpisodeResult] = []
    reward_sum = 0.0
    evaluate_calls = 0
    for seed in seed_tuple:
        # Confirmatory bucket is fixed for Wave 1a; a calibration-seeded
        # replay would go through a separate calibration-mode helper on
        # the sweep runner, not this control path.  Passing a calibration
        # seed here surfaces the Wave 0 family generator's ValueError.
        episode = generator(seed=seed, bucket=TemplateBucket.CONFIRMATION)
        # Byte-stable determinism: locking ``rng_seed = seed`` on the
        # controls path makes the LoggedProbePolicy draw deterministic
        # given (family, seed) alone, so byte-identical ControlTraces
        # replay on any host.
        result = run_e2a_episode(episode, condition, rng_seed=seed)
        results.append(result)
        reward_sum += float(result.outcome.realized_reward)
        evaluate_calls += int(result.sealed_env_evaluate_calls)

    n = len(results)
    mean_reward = reward_sum / n if n > 0 else 0.0

    return ControlTrace(
        condition_name=condition.name,
        family=family_name,
        seeds=seed_tuple,
        results=tuple(results),
        mean_realized_reward=float(mean_reward),
        sealed_env_evaluate_calls=int(evaluate_calls),
        promotion_eligible=bool(condition.promotion_eligible),
    )


# --------------------------------------------------------------------------- #
# Public control runners
# --------------------------------------------------------------------------- #


def run_frozen_wrong(family: str, seeds: Sequence[int]) -> ControlTrace:
    """Return the ``FROZEN_WRONG`` (C1) baseline trace for ``(family, seeds)``.

    Wave 1a's baseline — the Wave 0 adversarially wrong prior held fixed
    across every episode with no update rule applied.  Every other
    condition's confirmatory reward mean is scored against this trace
    per the paired-seed variance estimator declared in
    ``PREREGISTRATION.md`` §6.  Deterministic in ``(family, seed)``: a
    repeat call with the same arguments yields a byte-identical
    :class:`ControlTrace`.
    """

    return _run_batch(CONDITIONS[FROZEN_WRONG], family, seeds)


def run_oracle_ceiling(family: str, seeds: Sequence[int]) -> ControlTrace:
    """Return the ``ORACLE_CEILING`` (C3) diagnostic trace for ``(family, seeds)``.

    The oracle prior places a fixed high weight on every answer node
    (evaluator-side; the policy never sees the sealed fields).  The
    trace populates the ceiling-headroom column in Wave 1a's per-family
    receipt but is **never** promotable — the returned
    :class:`ControlTrace` carries ``promotion_eligible=False`` and
    :func:`promotion_admit_condition` on the underlying oracle
    :class:`Condition` raises :class:`PromotionRefused` per
    ``PREREGISTRATION.md`` §4 "Oracle is diagnostic".  This runner still
    executes the oracle so the diagnostic ceiling receipt is available;
    the refusal happens at the promotion boundary, not here.
    """

    return _run_batch(CONDITIONS[ORACLE_CEILING], family, seeds)


def run_shuffled(family: str, seeds: Sequence[int]) -> ControlTrace:
    """Return the ``SHUFFLED`` (C4) anchor-permutation trace.

    The concern factory permutes the Wave 0 wrong-prior anchor labels
    with a SHA-256-driven permutation seeded by
    ``(episode.episode_id, episode.seed)`` (see
    ``wave1a.conditions._shuffled_prior``).  The magnitude distribution
    matches the frozen wrong prior — only the anchor identity is
    scrambled.  If this control's confirmatory reward mean falls within
    ``sigma_hat_multiplicative_wave0`` of the on-line-learned variant on
    any family, the screen KILLs on specificity (§5.3).
    """

    return _run_batch(CONDITIONS[SHUFFLED], family, seeds)


def run_wrong_agent(family: str, seeds: Sequence[int]) -> ControlTrace:
    """Return the ``WRONG_AGENT`` (C5) different-agent-history trace.

    The concern factory proxies "a different agent's history" as a
    deterministic re-ranking of the wrong-prior magnitudes over the same
    candidate set, seeded by
    ``(episode.family, episode.seed)`` (see
    ``wave1a.conditions._wrong_agent_prior``).  If this control's
    confirmatory reward mean falls within
    ``sigma_hat_multiplicative_wave0`` of the on-line-learned variant on
    any family, the screen KILLs on specificity (§5.3).
    """

    return _run_batch(CONDITIONS[WRONG_AGENT], family, seeds)
