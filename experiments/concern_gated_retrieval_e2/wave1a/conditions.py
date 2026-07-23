"""COGR-E2a condition registry (Wave 1a scaffold).

This module is the enum-like registry of the five Wave 1a experimental
conditions plus the diagnostic oracle ceiling. It is *scaffolding only* —
Wave 1a experiment logic (the concern-update rule under screen, the
paired-seed variance estimator, the specificity comparison against Wave 0
info-matched second signals) belongs to sibling modules whose contract this
registry fixes.

Registered conditions
---------------------

Every condition is one :class:`Condition` object exposing three fields:

* ``initial_concern_factory`` — an *evaluator-side* callable that maps a
  sealed :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`
  to a numeric ``dict[str, float]`` concern prior over the episode's
  candidate anchors. Because these factories run before the policy-visible
  view is minted, they may legally read sealed fields on the
  :class:`EpisodeSpec` (``role``, ``utility``, ``_answer_key``,
  ``care_anchors``). Their *output* is what the policy sees, not their
  implementation. The runner is responsible for enforcing that the returned
  prior lives on the non-negative orthant and shares its key set with the
  observed candidate/anchor space.
* ``update_rule`` — the on-line concern-update estimator name, one of
  ``"ips"`` or ``"dr"``, or ``None`` for a frozen condition. The runner
  passes the name through to
  :func:`experiments.concern_gated_retrieval_e2.wave0.concern_update.update_concern`
  via its ``estimator`` argument.
* ``promotion_eligible`` — ``False`` for the oracle ceiling; ``True`` for
  every other condition. The oracle is a diagnostic-only ceiling
  (PREREGISTRATION.md §4 note "Oracle is diagnostic"), so
  :func:`promotion_admit_condition` refuses it with
  :class:`PromotionRefused`.

Wave 1a scope
-------------

Wave 1a is a **screen** for the concern-update rule on fixed withheld
geometry. It CAN reject the rule (see the fatal gates in
``PREREGISTRATION.md`` §5). It CANNOT establish learned memory geometry
(a Wave 1b object), an L1 dual-source-retrieval claim (Wave 1b), or an L2
history-derived-concern-recovery claim (also Wave 1b).

Anti-leakage
------------

Condition factories that touch sealed fields are labelled
``policy_visible=False`` so the runner can gate them behind the sealed-env
boundary. Only the numeric prior they emit is exposed to the policy code
path; the sealed :class:`EpisodeSpec` never reaches the nomination policy,
the :class:`LoggedProbePolicy` wrapper, or
:func:`update_concern`. See ``../wave0/PREREGISTRATION.md`` §4.1 for the
enumeration of evaluator-only fields, ``wave0.sealed_env.IntegrityAudit``
for the AST audit the runner applies to policy callables, and this file's
:func:`_uniform_over_candidates` helper for the reference safe factory.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Final, Literal, Mapping

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import EpisodeSpec

__all__ = [
    "CONDITIONS",
    "Condition",
    "PromotionRefused",
    "UpdateRuleName",
    "FROZEN_WRONG",
    "ONLINE_IPS",
    "ONLINE_DR",
    "ORACLE_CEILING",
    "SHUFFLED",
    "WRONG_AGENT",
    "condition_by_name",
    "promotion_admit_condition",
    "promotable_conditions",
]


UpdateRuleName = Literal["ips", "dr"]


# --------------------------------------------------------------------------- #
# Names (frozen at Wave 1a signature time)
# --------------------------------------------------------------------------- #


#: Frozen-wrong baseline — Wave 0 adversarially wrong prior, no update.
FROZEN_WRONG: Final[str] = "frozen_wrong"

#: On-line-learned candidate — IPS variant of ``update_concern``.
ONLINE_IPS: Final[str] = "online_learned_ips"

#: On-line-learned candidate — doubly-robust variant of ``update_concern``.
ONLINE_DR: Final[str] = "online_learned_dr"

#: Diagnostic oracle ceiling. Never promotable.
ORACLE_CEILING: Final[str] = "oracle_ceiling"

#: Anchor-label-shuffled control (rejects "any anchor-conditioned update
#: helps").
SHUFFLED: Final[str] = "shuffled"

#: Wrong-agent-profile control (rejects "any historical profile helps").
WRONG_AGENT: Final[str] = "wrong_agent"


# --------------------------------------------------------------------------- #
# Condition dataclass
# --------------------------------------------------------------------------- #


ConcernFactory = Callable[[EpisodeSpec], Mapping[str, float]]


class PromotionRefused(RuntimeError):
    """Raised when the promotion harness refuses to admit a condition.

    Wave 1a refuses a condition whose ``promotion_eligible`` flag is
    ``False``. The oracle ceiling is the sole such condition in the Wave
    1a registry; it is a diagnostic-only ceiling and cannot enter a
    promotion contest. The refusal message shape is stable so downstream
    receipts can regex-match on it.
    """


@dataclass(frozen=True)
class Condition:
    """One Wave 1a experimental condition.

    Every field is frozen at registration time; the registry itself is
    immutable at import.
    """

    name: str
    initial_concern_factory: ConcernFactory
    update_rule: UpdateRuleName | None
    promotion_eligible: bool
    #: ``False`` for factories that legitimately dereference sealed
    #: :class:`EpisodeSpec` fields (``oracle_ceiling``, ``wrong_agent``).
    #: The runner refuses to pass such factories through
    #: ``IntegrityAudit.assert_clean``; their output — the numeric prior
    #: — is what the policy sees, not their implementation.
    factory_reads_sealed_fields: bool

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Condition.name must be a non-empty string")
        if self.update_rule not in (None, "ips", "dr"):
            raise ValueError(
                "Condition.update_rule must be None, 'ips', or 'dr'; got "
                f"{self.update_rule!r}"
            )
        if not callable(self.initial_concern_factory):
            raise TypeError("Condition.initial_concern_factory must be callable")


# --------------------------------------------------------------------------- #
# Factory implementations
# --------------------------------------------------------------------------- #


def _validate_prior_output(
    prior: Mapping[str, float], episode: EpisodeSpec
) -> dict[str, float]:
    """Return a validated, non-negative-only copy of ``prior``.

    Every anchor id in the returned mapping is guaranteed to sit inside
    the observed candidate set of ``episode``, so the policy-visible view
    consuming the prior cannot reach a node the sealed view does not
    expose. Anchors with weight ``<= 0`` are dropped.
    """
    candidate_set = frozenset(episode.candidate_nodes)
    validated: dict[str, float] = {}
    for anchor, weight in prior.items():
        if anchor not in candidate_set:
            # Silently drop anchors outside the candidate set — the
            # runner will not surface them to the policy anyway, but a
            # missing key is easier to reason about than a spurious one.
            continue
        try:
            w = float(weight)
        except (TypeError, ValueError):
            continue
        if w > 0.0:
            validated[anchor] = w
    return validated


def _frozen_wrong_prior(episode: EpisodeSpec) -> Mapping[str, float]:
    """Return the Wave 0 wrong-prior weights as-is (frozen baseline)."""

    return _validate_prior_output(episode.care_anchors, episode)


def _online_learned_prior(episode: EpisodeSpec) -> Mapping[str, float]:
    """Return the Wave 0 wrong prior; the update rule mutates it later.

    On-line-learned variants start from the same adversarially wrong prior
    as the frozen baseline. The variant's update rule (``"ips"`` or
    ``"dr"``) is applied post-outcome by
    :func:`~experiments.concern_gated_retrieval_e2.wave0.concern_update.update_concern`.
    """
    return _validate_prior_output(episode.care_anchors, episode)


def _oracle_prior(episode: EpisodeSpec) -> Mapping[str, float]:
    """Return an oracle concern prior derived from the sealed answer key.

    **Evaluator-side.** Reads ``episode._answer_key`` — a sealed field.
    The prior places a fixed high weight on every answer node and leaves
    every other candidate at a small positive uniform baseline so
    downstream ``update_concern`` calls have a strictly positive prior on
    every anchor. The policy sees only the numeric prior.
    """
    high = 1.0
    uniform = 1e-3
    prior: dict[str, float] = {}
    answer_set = frozenset(episode._answer_key)
    for node in episode.candidate_nodes:
        prior[node] = high if node in answer_set else uniform
    return _validate_prior_output(prior, episode)


def _deterministic_permutation(seed_material: str, nodes: tuple[str, ...]) -> list[str]:
    """Return a deterministic permutation of ``nodes`` from ``seed_material``.

    Deterministic across processes: the tie-break sorts by
    ``sha256(seed_material || node)``. Wave 1a's shuffled and wrong-agent
    controls both use this helper so their permutations are byte-stable
    receipts.
    """
    if not nodes:
        return []
    ordered = sorted(
        nodes,
        key=lambda node: hashlib.sha256(
            f"{seed_material}::{node}".encode("utf-8")
        ).digest(),
    )
    return ordered


def _shuffled_prior(episode: EpisodeSpec) -> Mapping[str, float]:
    """Return the Wave 0 wrong-prior weights with anchor labels permuted.

    The permutation is a pure function of ``(episode.episode_id,
    episode.seed)`` so the receipt is byte-stable. The magnitude
    distribution matches the frozen wrong prior — only the anchor
    identity is scrambled.
    """
    base = dict(episode.care_anchors)
    anchors = tuple(base.keys())
    if not anchors:
        return {}
    permuted_order = _deterministic_permutation(
        f"cogr-wave1a::shuffled::{episode.episode_id}::{episode.seed}", anchors
    )
    weights_sorted_by_original = [base[a] for a in anchors]
    # Re-assign the same magnitudes to the permuted labels.
    prior = {
        permuted_order[i]: weights_sorted_by_original[i]
        for i in range(len(anchors))
    }
    return _validate_prior_output(prior, episode)


def _wrong_agent_prior(episode: EpisodeSpec) -> Mapping[str, float]:
    """Return a concern prior drawn from a *different* agent's history.

    **Evaluator-side.** Wave 1a proxies "a different agent's history" as a
    deterministic re-ranking of the wrong-prior magnitudes over the same
    candidate set, seeded by a different agent id derived from the
    episode. This is a control: if this profile achieves an outcome mean
    within ``sigma_hat_multiplicative_wave0`` of the on-line-learned
    condition, the specificity gate KILLs the update rule
    (PREREGISTRATION.md §5.3).
    """
    base = dict(episode.care_anchors)
    if not base:
        return {}
    weights = sorted(base.values(), reverse=True)
    permuted_nodes = _deterministic_permutation(
        f"cogr-wave1a::wrong-agent::{episode.family}::{episode.seed}",
        tuple(base.keys()),
    )
    prior = {permuted_nodes[i]: weights[i] for i in range(len(permuted_nodes))}
    return _validate_prior_output(prior, episode)


def _uniform_over_candidates(episode: EpisodeSpec) -> Mapping[str, float]:
    """Reference *safe* factory: uniform mass over candidate nodes.

    Exposed for unit tests and downstream diagnostics. Does not
    dereference any sealed field; safe to pass through
    :meth:`IntegrityAudit.assert_clean`.
    """
    candidates = tuple(episode.candidate_nodes)
    if not candidates:
        return {}
    weight = 1.0 / len(candidates)
    return _validate_prior_output({n: weight for n in candidates}, episode)


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #


CONDITIONS: Final[Mapping[str, Condition]] = MappingProxyType(
    {
        FROZEN_WRONG: Condition(
            name=FROZEN_WRONG,
            initial_concern_factory=_frozen_wrong_prior,
            update_rule=None,
            promotion_eligible=True,
            factory_reads_sealed_fields=False,
        ),
        ONLINE_IPS: Condition(
            name=ONLINE_IPS,
            initial_concern_factory=_online_learned_prior,
            update_rule="ips",
            promotion_eligible=True,
            factory_reads_sealed_fields=False,
        ),
        ONLINE_DR: Condition(
            name=ONLINE_DR,
            initial_concern_factory=_online_learned_prior,
            update_rule="dr",
            promotion_eligible=True,
            factory_reads_sealed_fields=False,
        ),
        ORACLE_CEILING: Condition(
            name=ORACLE_CEILING,
            initial_concern_factory=_oracle_prior,
            update_rule=None,
            promotion_eligible=False,  # diagnostic ceiling only
            factory_reads_sealed_fields=True,
        ),
        SHUFFLED: Condition(
            name=SHUFFLED,
            initial_concern_factory=_shuffled_prior,
            update_rule=None,
            promotion_eligible=True,
            factory_reads_sealed_fields=False,
        ),
        WRONG_AGENT: Condition(
            name=WRONG_AGENT,
            initial_concern_factory=_wrong_agent_prior,
            update_rule=None,
            promotion_eligible=True,
            factory_reads_sealed_fields=True,
        ),
    }
)


def condition_by_name(name: str) -> Condition:
    """Return the registered :class:`Condition` for ``name``.

    Raises :class:`KeyError` on an unknown name. Provided so callers do
    not need to import the registry directly.
    """
    return CONDITIONS[name]


def promotion_admit_condition(condition: Condition) -> Condition:
    """Return ``condition`` if it is legal for a Wave 1a screen; else raise.

    A condition whose ``promotion_eligible`` is ``False`` is refused. The
    oracle ceiling is the only such condition in the Wave 1a registry;
    calling this on the oracle raises :class:`PromotionRefused` with a
    stable message shape.
    """
    if not isinstance(condition, Condition):
        raise TypeError(
            f"promotion_admit_condition expects a Condition; got "
            f"{type(condition).__name__}"
        )
    if not condition.promotion_eligible:
        raise PromotionRefused(
            f"condition {condition.name!r} is flagged CEILING-ONLY / diagnostic-"
            "only and cannot enter a Wave 1a screen or Wave 1b promotion "
            "contest; see wave1a/PREREGISTRATION.md §4"
        )
    return condition


def promotable_conditions() -> tuple[Condition, ...]:
    """Return every condition whose ``promotion_eligible`` is ``True``.

    Order matches the Wave 1a preregistration §4 table (C1, C2a, C2b, C4,
    C5). The oracle (C3) is intentionally omitted.
    """
    return tuple(c for c in CONDITIONS.values() if c.promotion_eligible)
