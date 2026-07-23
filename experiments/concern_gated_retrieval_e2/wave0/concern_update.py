"""Concern-update off-policy learner for COGR Wave 0 (exploratory only).

This module is the Wave 0 **exploratory** scaffolding for a concern-update
rule that Wave 1 (COGR-E2a) will actually test. It exists so the Wave 1
concern-recovery screen can be *rejectable*: it fixes the propensity-logging
contract, the off-policy estimator families (IPS, doubly-robust), the
non-negative mirror-descent step, and the typed single-source influence
bound (the poisoning guard). Wave 0 does not, and cannot, claim concern
recovery from these primitives; the wave's promotable claim is calibration
and family scaffolding + wrong-prior initialization (see
``experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md`` §5).

What this module contains
-------------------------

* :class:`ProbeReceipt` — a policy-visible frozen dataclass carrying the
  ``(episode_id, candidate, selection_propensity, source_id,
  template_family_split, exploratory)`` tuple that
  :class:`LoggedProbePolicy` writes for every retrieval decision. The
  ``template_family_split`` tag preserves the disjoint calibration /
  confirmatory family split at the receipt boundary (Wave 0 anti-leakage
  contract, PREREGISTRATION.md §4.1).
* :class:`LoggedProbePolicy` — a stochastic wrapper around a caller-supplied
  nomination policy. With probability ``epsilon`` (default 0.05 during
  calibration) it selects a uniform random candidate from the full
  candidate set; otherwise it selects the top-ranked candidate from the
  wrapped policy. Every selection emits a :class:`ProbeReceipt` whose
  ``selection_propensity`` is the probability the *logging* policy would
  select the recorded candidate — the quantity IPS and DR estimators
  divide by.
* :func:`update_concern` — an off-policy concern-anchor update. Given a
  prior ``dict[anchor -> weight]``, a batch of receipts, and the matched
  sealed outcomes, it returns a new non-negative prior via a
  multiplicative (exponentiated) mirror-descent step. The estimator kind
  is ``"ips"`` (Horvitz–Thompson inverse-propensity scores) or ``"dr"``
  (doubly-robust with a per-candidate control-variate baseline).
* :data:`DEFAULT_MAX_SOURCE_INFLUENCE` and the guard inside
  :func:`update_concern` — the poisoning guard. Per-source total
  contribution magnitude is clamped to a caller-configurable bound before
  the mirror-descent step is applied (PREREGISTRATION.md §4.4).

Wave 0 anti-leakage contract
----------------------------

This module never dereferences the sealed :class:`EpisodeSpec` fields
``role``, ``utility``, or ``_answer_key``; the sole evaluator surface it
consumes is :class:`SealedOutcome.realized_reward`, which is by
construction post-decision. Every :class:`ProbeReceipt` carries the
``template_family_split`` tag so the runtime family-split guard
(:func:`experiments.concern_gated_retrieval_e2.wave0.template_split.assert_calibration_only`)
can refuse a confirmatory receipt at a calibration entry point.

Reuse boundary
--------------

This module does not fork PPR, the pilot's ``coincidence_scores``, or the
epiplexity estimator. It consumes only the sealed-env dataclasses and the
policy-visible ``EpisodeContext``. Wave 1 will introduce the concern-anchor
mapping and the learned-geometry variant on top of this interface; the
exponential mirror-descent step is a Wave 0 scaffold that Wave 1 may
freeze or replace, but its non-negativity, boundedness, and
poisoning-guard semantics are the Wave 0 contract.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Sequence

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    SealedOutcome,
    TemplateFamilySplit,
)

__all__ = [
    "DEFAULT_EPSILON",
    "DEFAULT_ETA",
    "DEFAULT_MAX_SOURCE_INFLUENCE",
    "DEFAULT_SOURCE_ID",
    "DEFAULT_WEIGHT_CLIP",
    "Estimator",
    "LoggedProbePolicy",
    "NominationPolicy",
    "ProbeReceipt",
    "update_concern",
]


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #


#: Default exploration probability during Wave 0 calibration. A small
#: positive floor is the exploration coverage the Wave 1 COGR-E2a screen
#: requires (roadmap §"L2 recovery"). The value is deliberately small so
#: the wrapped nomination policy dominates on typical rows; the estimators
#: below rely only on strict positivity.
DEFAULT_EPSILON: float = 0.05


#: Default mirror-descent step size. Small enough that a single batch of
#: bounded receipts cannot flip a concern anchor's weight by more than a
#: factor of ``exp(DEFAULT_ETA * DEFAULT_MAX_SOURCE_INFLUENCE)`` per source,
#: which is the poisoning-guard tolerance recorded on every update receipt.
DEFAULT_ETA: float = 0.10


#: Maximum aggregate magnitude of one source's contribution to the
#: aggregated value-of-anchor vector before the mirror-descent step. The
#: guard is documented in PREREGISTRATION.md §4.4. Wave 1's targeted
#: poisoning stress will exercise this bound; Wave 0 only registers the
#: shape (see the roadmap's §"Fatal gates by claim: Adversarial input").
DEFAULT_MAX_SOURCE_INFLUENCE: float = 1.0


#: Default per-anchor weight clip. Concern weights live on the non-negative
#: orthant; the clip keeps them inside a bounded box so a runaway
#: multiplicative update cannot blow up numerically. Chosen to be well
#: above the Wave 0 wrong-prior alarm weight ``W_ALARM_INIT = 1.0`` but
#: below the range where the pilot's PPR fixed point becomes numerically
#: sensitive.
DEFAULT_WEIGHT_CLIP: float = 8.0


#: Source id assigned to a receipt whose caller did not declare a
#: provenance channel. Wave 1 typed-source support will require callers
#: to name every non-trusted feedback source explicitly; Wave 0 uses this
#: default so the poisoning-guard receipt is well-formed even in the
#: simplest calibration probe.
DEFAULT_SOURCE_ID: str = "trusted"


Estimator = Literal["ips", "dr"]

#: Nomination policy signature. Wave 0 nomination policies take the
#: sealed :class:`EpisodeContext` and return a ranked tuple of candidate
#: node ids. The tuple's first entry is the greedy pick used by
#: :class:`LoggedProbePolicy` when it does not explore. Candidates outside
#: :attr:`EpisodeContext.candidate_nodes` are rejected at select time.
NominationPolicy = Callable[[EpisodeContext], Sequence[str]]


# --------------------------------------------------------------------------- #
# ProbeReceipt
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ProbeReceipt:
    """A logged retrieval probe with its policy-visible propensity.

    Every :class:`LoggedProbePolicy.select` call writes exactly one
    ``ProbeReceipt``. The tuple ``(episode_id, candidate,
    selection_propensity)`` is the anti-leakage contract required by
    Wave 1 COGR-E2a (roadmap §"L2 recovery: exploration coverage, logged
    propensities, negative updates"). The additional fields fix Wave 0
    conventions:

    * ``source_id`` — provenance of the outcome that will be paired with
      this receipt. Wave 0 calibration uses :data:`DEFAULT_SOURCE_ID` on
      every receipt; Wave 1 typed-source support will require callers to
      pass an explicit id per source. The poisoning guard in
      :func:`update_concern` bounds any single source's aggregate
      contribution to the concern update.
    * ``template_family_split`` — ``"calibration"`` or ``"confirmatory"``,
      copied from the sealed :class:`EpisodeContext`. A confirmatory
      receipt in a calibration update pipeline is a fatal integrity
      failure and is refused by :func:`update_concern`.
    * ``exploratory`` — ``True`` when the receipt records an
      epsilon-random exploratory pick, ``False`` when it records the
      wrapped nomination policy's greedy pick. Kept for calibration
      reporting; the estimator does not condition on it.

    The receipt is intentionally minimal: it does not carry the sealed
    outcome, role labels, per-node utility, or the answer key. The
    matched :class:`SealedOutcome` is passed alongside the receipt into
    :func:`update_concern`.
    """

    episode_id: str
    candidate: str
    selection_propensity: float
    source_id: str
    template_family_split: TemplateFamilySplit
    exploratory: bool

    def __post_init__(self) -> None:
        if not isinstance(self.episode_id, str) or not self.episode_id:
            raise ValueError("episode_id must be a non-empty string")
        if not isinstance(self.candidate, str) or not self.candidate:
            raise ValueError("candidate must be a non-empty string")
        if not isinstance(self.source_id, str) or not self.source_id:
            raise ValueError("source_id must be a non-empty string")
        if self.template_family_split not in ("calibration", "confirmatory"):
            raise ValueError(
                "template_family_split must be 'calibration' or 'confirmatory'; "
                f"got {self.template_family_split!r}"
            )
        if not (
            isinstance(self.selection_propensity, float)
            or isinstance(self.selection_propensity, int)
        ) or isinstance(self.selection_propensity, bool):
            raise TypeError("selection_propensity must be a real number")
        prop = float(self.selection_propensity)
        if not math.isfinite(prop) or not (0.0 < prop <= 1.0):
            raise ValueError(
                "selection_propensity must be a finite value in (0, 1]; "
                f"got {self.selection_propensity!r}"
            )


# --------------------------------------------------------------------------- #
# LoggedProbePolicy
# --------------------------------------------------------------------------- #


class LoggedProbePolicy:
    """Epsilon-greedy wrapper around a nomination policy.

    With probability :attr:`epsilon` the wrapper selects a candidate
    uniformly at random from :attr:`EpisodeContext.candidate_nodes`;
    otherwise it selects the top-ranked candidate returned by the wrapped
    nomination policy. Every :meth:`select` call returns
    ``(selected_candidate, probe_receipt)`` where ``probe_receipt`` is the
    logging-policy propensity of the recorded ``candidate``:

    ``p(candidate) = (1 - epsilon) * 1[candidate is wrapped_top]
                     + epsilon / len(context.candidate_nodes)``

    This is the exact quantity that IPS and DR estimators divide by, so
    downstream :func:`update_concern` calls are numerically well-posed
    (the propensity is bounded strictly below zero only in the
    degenerate ``epsilon == 0`` case, which the constructor forbids for
    a calibration policy).

    Wave 0 scope. Wave 0 uses this wrapper only to prove the propensity
    contract; the wrapped nomination policy in Wave 0 calibration is
    permitted to be any deterministic ranker over the sealed
    :class:`EpisodeContext`. Wave 1 COGR-E2a will freeze the wrapped
    policy and score the recovered concern against the calibration
    receipt; Wave 0 registers no such score.
    """

    def __init__(
        self,
        nomination: NominationPolicy,
        *,
        epsilon: float = DEFAULT_EPSILON,
        source_id: str = DEFAULT_SOURCE_ID,
    ) -> None:
        if not callable(nomination):
            raise TypeError("nomination must be a callable NominationPolicy")
        if not isinstance(epsilon, (float, int)) or isinstance(epsilon, bool):
            raise TypeError("epsilon must be a real number")
        eps = float(epsilon)
        if not math.isfinite(eps) or not (0.0 < eps <= 1.0):
            raise ValueError(
                "epsilon must lie in (0, 1]; a strictly positive floor is the "
                "exploration-coverage requirement in the Wave 0 roadmap"
            )
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("source_id must be a non-empty string")
        self._nomination = nomination
        self._epsilon = eps
        self._source_id = source_id

    # ------------------------------------------------------------------ #
    # Introspection
    # ------------------------------------------------------------------ #

    @property
    def epsilon(self) -> float:
        return self._epsilon

    @property
    def source_id(self) -> str:
        return self._source_id

    # ------------------------------------------------------------------ #
    # Selection
    # ------------------------------------------------------------------ #

    def select(
        self,
        context: EpisodeContext,
        rng: random.Random,
    ) -> tuple[str, ProbeReceipt]:
        """Return one selection and its logging-policy receipt.

        ``rng`` is a caller-supplied :class:`random.Random` instance. The
        wrapper never constructs a PRNG of its own so callers are able to
        drive determinism from a stated seed (satisfying the Wave 0
        calibration determinism gate).

        Raises :class:`ValueError` if the wrapped nomination policy
        returns an empty ranking or a ranking whose entries fall outside
        the sealed :attr:`EpisodeContext.candidate_nodes` set.
        """

        if not isinstance(context, EpisodeContext):
            raise TypeError("context must be an EpisodeContext")
        if not isinstance(rng, random.Random):
            raise TypeError("rng must be a random.Random instance")
        candidates = tuple(context.candidate_nodes)
        if not candidates:
            raise ValueError("EpisodeContext.candidate_nodes is empty")

        ranking = tuple(self._nomination(context))
        if not ranking:
            raise ValueError("nomination policy returned an empty ranking")
        unknown = set(ranking) - set(candidates)
        if unknown:
            raise ValueError(
                "nomination policy returned candidates outside the sealed "
                f"candidate set: {sorted(unknown)}"
            )
        greedy_pick = ranking[0]
        n = len(candidates)
        # Draw first, then decide. This keeps the RNG-consumption pattern
        # identical between exploratory and exploit paths, which the
        # determinism regression test relies on.
        u = rng.random()
        random_index = rng.randrange(n)
        random_pick = candidates[random_index]
        if u < self._epsilon:
            selected = random_pick
            exploratory = True
        else:
            selected = greedy_pick
            exploratory = False

        # Logging-policy propensity of the *recorded* candidate.
        prop = self._epsilon / n
        if selected == greedy_pick:
            prop += 1.0 - self._epsilon
        # Numerical safety: strictly positive by construction because
        # epsilon > 0 and n >= 1.
        assert prop > 0.0, "propensity must be strictly positive"

        receipt = ProbeReceipt(
            episode_id=context.episode_id,
            candidate=selected,
            selection_propensity=float(prop),
            source_id=self._source_id,
            template_family_split=context.template_family_split,
            exploratory=exploratory,
        )
        return selected, receipt


# --------------------------------------------------------------------------- #
# update_concern
# --------------------------------------------------------------------------- #


def _validate_prior(prior: Mapping[str, float]) -> dict[str, float]:
    if not isinstance(prior, Mapping):
        raise TypeError("prior must be a Mapping[str, float]")
    validated: dict[str, float] = {}
    for anchor, weight in prior.items():
        if not isinstance(anchor, str) or not anchor:
            raise ValueError("prior anchors must be non-empty strings")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise TypeError(f"prior[{anchor!r}] must be a real number")
        w = float(weight)
        if not math.isfinite(w) or w < 0.0:
            raise ValueError(
                f"prior[{anchor!r}] must be finite and non-negative; got {weight!r}"
            )
        validated[anchor] = w
    return validated


def _match_receipts_outcomes(
    receipts: Sequence[ProbeReceipt],
    outcomes: Sequence[SealedOutcome],
) -> None:
    if len(receipts) != len(outcomes):
        raise ValueError(
            "receipts and outcomes must be the same length; got "
            f"{len(receipts)} and {len(outcomes)}"
        )
    for i, (receipt, outcome) in enumerate(zip(receipts, outcomes)):
        if not isinstance(receipt, ProbeReceipt):
            raise TypeError(f"receipts[{i}] is not a ProbeReceipt")
        if not isinstance(outcome, SealedOutcome):
            raise TypeError(f"outcomes[{i}] is not a SealedOutcome")
        if receipt.template_family_split != outcome.template_family_split:
            raise ValueError(
                "receipt/outcome template_family_split mismatch at index "
                f"{i}: {receipt.template_family_split!r} vs "
                f"{outcome.template_family_split!r}"
            )


def _dr_baseline(
    receipts: Sequence[ProbeReceipt],
    outcomes: Sequence[SealedOutcome],
) -> dict[str, float]:
    """Return a per-candidate mean-outcome baseline for DR.

    A candidate seen only once falls back to the global mean outcome so
    the DR residual has zero conditional expectation under the logging
    policy. Baselines never consult evaluator-only fields; they consume
    only :attr:`SealedOutcome.realized_reward`.
    """

    per_candidate: dict[str, list[float]] = {}
    global_sum = 0.0
    global_n = 0
    for receipt, outcome in zip(receipts, outcomes):
        per_candidate.setdefault(receipt.candidate, []).append(
            float(outcome.realized_reward)
        )
        global_sum += float(outcome.realized_reward)
        global_n += 1
    global_mean = global_sum / global_n if global_n else 0.0
    baseline: dict[str, float] = {}
    for candidate, rewards in per_candidate.items():
        if len(rewards) >= 2:
            baseline[candidate] = sum(rewards) / len(rewards)
        else:
            baseline[candidate] = global_mean
    return baseline


def update_concern(
    prior: Mapping[str, float],
    receipts: Sequence[ProbeReceipt],
    outcomes: Sequence[SealedOutcome],
    estimator: Estimator = "ips",
    *,
    eta: float = DEFAULT_ETA,
    max_source_influence: float = DEFAULT_MAX_SOURCE_INFLUENCE,
    weight_clip: float = DEFAULT_WEIGHT_CLIP,
) -> dict[str, float]:
    """Return an updated concern-anchor prior.

    Parameters
    ----------
    prior:
        Non-negative concern weights over anchor node ids. Anchors that
        never appear in ``receipts`` are carried through unchanged. The
        returned mapping shares its key set with ``prior``.
    receipts:
        Sequence of :class:`ProbeReceipt` from
        :meth:`LoggedProbePolicy.select`. All receipts must carry the
        same :attr:`template_family_split` — mixing calibration and
        confirmatory receipts in a single call is a fatal integrity
        error.
    outcomes:
        Sequence of :class:`SealedOutcome` paired with ``receipts``.
        ``update_concern`` never consults any evaluator-only field; only
        :attr:`SealedOutcome.realized_reward` and
        :attr:`SealedOutcome.template_family_split` are read.
    estimator:
        ``"ips"`` (Horvitz–Thompson inverse propensity scores) or
        ``"dr"`` (doubly-robust with a per-candidate control-variate
        baseline computed by :func:`_dr_baseline`).
    eta:
        Mirror-descent step size. ``> 0``.
    max_source_influence:
        Poisoning-guard cap. Every unique ``receipt.source_id`` has its
        aggregate contribution magnitude ``sum |v_hat_a from s|`` clamped
        to this value before the mirror-descent step is taken. Documented
        in PREREGISTRATION.md §4.4.
    weight_clip:
        Upper bound on each updated concern weight. Keeps the
        multiplicative update numerically stable.

    Returns
    -------
    dict[str, float]
        A new mapping ``anchor -> weight`` with the same key set as
        ``prior`` and every value in ``[0, weight_clip]``.

    Notes
    -----
    The multiplicative update is
    ``w'_a = clip(w_a * exp(eta * v_hat_a), 0, weight_clip)`` where
    ``v_hat_a`` is the estimator's value estimate for anchor ``a``. The
    exponential form keeps weights on the non-negative orthant without
    an explicit projection step and matches the Bregman-divergence form
    of mirror descent that is standard for non-negative reweighting.
    """

    if estimator not in ("ips", "dr"):
        raise ValueError(f"estimator must be 'ips' or 'dr'; got {estimator!r}")
    if not isinstance(eta, (int, float)) or isinstance(eta, bool):
        raise TypeError("eta must be a real number")
    eta_f = float(eta)
    if not math.isfinite(eta_f) or eta_f <= 0.0:
        raise ValueError("eta must be finite and positive")
    if (
        not isinstance(max_source_influence, (int, float))
        or isinstance(max_source_influence, bool)
    ):
        raise TypeError("max_source_influence must be a real number")
    msi = float(max_source_influence)
    if not math.isfinite(msi) or msi <= 0.0:
        raise ValueError("max_source_influence must be finite and positive")
    if not isinstance(weight_clip, (int, float)) or isinstance(weight_clip, bool):
        raise TypeError("weight_clip must be a real number")
    wclip = float(weight_clip)
    if not math.isfinite(wclip) or wclip <= 0.0:
        raise ValueError("weight_clip must be finite and positive")

    validated_prior = _validate_prior(prior)
    _match_receipts_outcomes(receipts, outcomes)

    if not receipts:
        # No new evidence — return an independent copy of the prior.
        return dict(validated_prior)

    # Family-split guard. Refuses any confirmatory receipt at this
    # calibration entry point (Wave 0 anti-leakage §4.1). A homogeneous
    # calibration batch is a hard integrity requirement.
    splits = {r.template_family_split for r in receipts}
    if len(splits) > 1:
        raise ValueError(
            "receipts must all share one template_family_split; got "
            f"{sorted(splits)}"
        )
    (only_split,) = splits
    if only_split != "calibration":
        raise ValueError(
            "update_concern refuses a confirmatory receipt batch at a "
            "calibration entry point; see PREREGISTRATION.md §4.1"
        )

    # Estimator: build per-source per-anchor contributions.
    if estimator == "dr":
        baseline = _dr_baseline(receipts, outcomes)
    else:
        baseline = {}

    per_source: dict[str, dict[str, float]] = {}
    for receipt, outcome in zip(receipts, outcomes):
        anchor = receipt.candidate
        r = float(outcome.realized_reward)
        p = float(receipt.selection_propensity)
        # ProbeReceipt.__post_init__ guarantees p > 0.
        if estimator == "ips":
            delta = r / p
        else:  # dr
            m_hat = baseline.get(anchor, 0.0)
            delta = (r - m_hat) / p + m_hat
        src = per_source.setdefault(receipt.source_id, {})
        src[anchor] = src.get(anchor, 0.0) + delta

    # Poisoning guard: clamp per-source aggregate magnitude. Every
    # source's per-anchor contribution to the batch-mean value estimate
    # is the source's sum-of-deltas divided by the total receipt count;
    # if the aggregate magnitude (sum over anchors of the absolute
    # per-anchor contribution) exceeds ``max_source_influence`` the
    # source's contributions are scaled down proportionally before the
    # mirror-descent step. This bounds any single source's influence on
    # the update irrespective of how many receipts it produced.
    total_receipts = len(receipts)
    aggregated: dict[str, float] = {anchor: 0.0 for anchor in validated_prior}
    for source_id, per_anchor in per_source.items():
        # Per-source contribution to the batch-mean value estimate.
        contribution = {
            anchor: value / total_receipts for anchor, value in per_anchor.items()
        }
        magnitude = sum(abs(v) for v in contribution.values())
        if magnitude > msi:
            scale = msi / magnitude
        else:
            scale = 1.0
        for anchor, value in contribution.items():
            # Anchors probed but absent from the prior are dropped
            # rather than synthesized: Wave 0 does not grow the anchor
            # set from receipts. Wave 1 may relax this.
            if anchor not in aggregated:
                continue
            aggregated[anchor] += value * scale

    # Multiplicative (exponentiated) mirror-descent step. Non-negative
    # by construction; clip to weight_clip.
    updated: dict[str, float] = {}
    for anchor, w in validated_prior.items():
        v = aggregated.get(anchor, 0.0)
        w_new = w * math.exp(eta_f * v)
        if not math.isfinite(w_new):
            # Numerical safety: the poisoning guard bounds the exponent's
            # argument, but callers can still pass pathological eta.
            w_new = wclip if v > 0 else 0.0
        w_new = max(0.0, min(wclip, w_new))
        updated[anchor] = w_new

    # Return a plain dict so callers can further mutate if desired;
    # freeze via MappingProxyType when the prior is exposed on a
    # public dataclass, not here.
    return updated
