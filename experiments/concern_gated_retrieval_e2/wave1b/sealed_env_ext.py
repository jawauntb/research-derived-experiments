"""Wave 1b sealed-environment extension — SET-level oracle evaluation.

Wave 0's :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedEnvironment`
scores a single :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.RetrievalChoice`
against a per-node additive utility. That is the correct contract for
the policy path: a policy submits one decision and receives one sealed
outcome. It is NOT sufficient for the Wave 1b oracle-regret metric,
which enumerates ``Δ(S)`` for every candidate set ``S ⊆ V \\ R_t`` with
``|S| ≤ min(budget, 3)`` and needs a bundle-aware, non-additive utility
because Spencer's echo-chamber correction (Wave 1b PREREGISTRATION.md
§4) explicitly plants complementary pairs, contradictory pairs,
dangerous conjunctions, and isolation distractors whose joint
``Δ_task`` is not the sum of the singleton utilities.

This module extends the sealed environment with ONE additional
evaluator-only method — :meth:`OracleSealedEnvironment.evaluate_set` —
that returns SET-level ``Δ_task(S)``. The policy path is unchanged: it
still receives a wave0 :class:`SealedEnvironment` (via
:meth:`OracleSealedEnvironment.as_policy_env`) whose ``evaluate`` may
only be called once. The oracle path uses ``evaluate_set`` and every
``(episode, S)`` key may be evaluated **at most once** across the whole
oracle enumeration. A second call raises
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedEvaluationError`
so a downstream bug that would re-run the oracle enumerator (and thus
inflate its cost estimate or hide a nondeterminism) is loud rather than
silent.

Anti-leakage
------------
:meth:`evaluate_set` and its helper :func:`compute_set_delta` are
EVALUATOR-side. Every implementation reference in this module
dereferences ``episode._answer_key``, ``episode.role``, and
``episode.utility`` — the three sealed :class:`EpisodeSpec` fields
enumerated in ``wave0/PREREGISTRATION.md`` §4.1 and included in
:attr:`IntegrityAudit.FORBIDDEN_ATTRS`. Consequently any policy
callable whose source imports ``sealed_env_ext.compute_set_delta`` or
``OracleSealedEnvironment.evaluate_set`` and derives a value from those
references will fail :meth:`IntegrityAudit.assert_clean`, which the
Wave 1b oracle-regret test suite verifies.

Bundle interaction rules
------------------------
The bundle-interaction adjustments (complementary joint bonus,
contradictory joint penalty, dangerous-conjunction constraint-violation
penalty, isolation-distractor context penalty) live at module level so
the oracle path scores every family with a single canonical rule. The
numerical values match
:mod:`experiments.concern_gated_retrieval_e2.wave1b.families.maintenance_fault_v2`
verbatim so its bundle plants are scored consistently with the family
module's documentation.  The two other v2 families
(``delayed_commitments_v2``, ``resource_constrained_v2``) do not
override the constants; the module-level defaults apply.

Bundle detection uses substring matching on the sealed role labels.
The role vocabularies of the three v2 families are disjoint from every
Wave 0 role, so a substring-match false positive against Wave 0 role
names cannot occur: Wave 0 episodes are not routed through this module
(the wave0 sealed env still handles them). Within the Wave 1b role
vocabularies, the substrings ``complementary``, ``contradictory``,
``dangerous``, and ``isolation`` uniquely identify the intended
bundle-membership classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Iterable, Mapping

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
    LeakageError,
    RetrievalChoice,
    SealedEnvironment,
    SealedEvaluationError,
    SealedMode,
    SealedOutcome,
)


# --------------------------------------------------------------------------- #
# Bundle-interaction constants (canonical across the three v2 families).      #
# --------------------------------------------------------------------------- #


#: Additional ``Δ_task`` when both members of a planted complementary
#: pair are loaded in ``S``. Matches
#: :data:`experiments.concern_gated_retrieval_e2.wave1b.families.maintenance_fault_v2.COMPLEMENTARY_PAIR_JOINT_BONUS`
#: verbatim so the two families reason about complementary pairs with
#: one rule.
COMPLEMENTARY_JOINT_BONUS: Final[float] = 0.40


#: Additional ``Δ_task`` penalty when both members of a planted
#: contradictory pair are loaded in ``S`` — the "policy KO" outcome the
#: task brief names. Matches the maintenance_fault_v2 constant verbatim.
CONTRADICTORY_JOINT_PENALTY: Final[float] = 0.30


#: Additional ``Δ_task`` penalty when all three members of a planted
#: dangerous conjunction are loaded in ``S`` — the sealed evaluator
#: constraint-violation penalty (the "allergy + nuts + cake" motif
#: called out in the operator's echo-chamber corrections). Matches the
#: maintenance_fault_v2 constant verbatim.
DANGEROUS_TRIPLE_PENALTY: Final[float] = 0.75


#: Additional ``Δ_task`` penalty per isolation distractor loaded in
#: ``S`` — the "compatible-alternative-action with higher care weight
#: than the load-bearing memory" motif. Context is always present in
#: the episode, so an isolation distractor is always evaluated in
#: context. Matches the maintenance_fault_v2 constant verbatim.
ISOLATION_CONTEXT_PENALTY: Final[float] = 0.30


#: Wave 0 miss-penalty coefficient. A policy loading a positive-utility
#: non-answer pays ``0.25 * max(u, 0)`` for it. Kept as a module-level
#: constant so the SET-level scorer inherits the wave0 formula exactly.
MISS_PENALTY_COEFFICIENT: Final[float] = 0.25


#: SET-level ``Δ_task`` clamp. Wave 0
#: :meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedEnvironment._score`
#: clamps its realized reward to ``[-1, 1]``; the SET-level scorer
#: applies the same clamp so the two receipts sit on the same scale.
DELTA_CLAMP_LO: Final[float] = -1.0
DELTA_CLAMP_HI: Final[float] = 1.0


#: Role-name substrings the SET-level scorer uses to detect bundle
#: members. Wave 1b v2 role vocabularies deliberately embed these
#: substrings; Wave 0 vocabularies do not, and Wave 0 episodes are
#: never routed through the SET-level path.
_COMPLEMENTARY_SUBSTR: Final[str] = "complementary"
_CONTRADICTORY_SUBSTR: Final[str] = "contradictory"
_DANGEROUS_SUBSTR: Final[str] = "dangerous"
_ISOLATION_SUBSTR: Final[str] = "isolation"


# --------------------------------------------------------------------------- #
# SET-level outcome record                                                    #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SetOutcome:
    """SET-level oracle outcome for a candidate set ``S``.

    Attributes
    ----------
    selected_set:
        The candidate set that was scored, in canonical sorted order so
        two calls with the same members return byte-identical
        ``selected_set`` tuples regardless of input iteration order.
    delta_task:
        The SET-level ``Δ_task(S)`` after miss penalty and bundle
        adjustments, clamped to ``[DELTA_CLAMP_LO, DELTA_CLAMP_HI]``.
    hit_reward:
        Additive sum of ``episode.utility[v]`` over ``v in S`` that also
        appear in ``episode._answer_key``. Reported for provenance.
    miss_penalty:
        Wave 0 miss penalty ``0.25 * Σ max(u, 0)`` over ``v in S``
        outside the answer key. Reported for provenance.
    bundle_adjustment:
        Signed sum of the bundle interaction terms (complementary bonus
        + contradictory penalty + dangerous-triple penalty + isolation
        context penalty) applied to this set. Reported for provenance.
    complementary_pairs_hit:
        Number of planted complementary pairs both of whose members are
        in ``S``. A pair contributes at most one hit even if additional
        complementary members leak into the set.
    contradictory_pairs_hit:
        Same, for planted contradictory pairs.
    dangerous_triples_hit:
        Number of planted dangerous conjunctions all three of whose
        members are in ``S``.
    isolation_hits:
        Number of isolation distractors in ``S``.
    """

    selected_set: tuple[str, ...]
    delta_task: float
    hit_reward: float
    miss_penalty: float
    bundle_adjustment: float
    complementary_pairs_hit: int
    contradictory_pairs_hit: int
    dangerous_triples_hit: int
    isolation_hits: int


# --------------------------------------------------------------------------- #
# Set-delta computation                                                        #
# --------------------------------------------------------------------------- #


def _grouped_by_prefix(
    role_map: Mapping[str, str],
    nodes: frozenset[str],
    substring: str,
) -> dict[str, list[str]]:
    """Group ``nodes`` whose role contains ``substring`` by role label.

    The Wave 1b v2 families label the two members of one complementary
    pair (respectively contradictory pair, dangerous conjunction) with
    role labels that share a common prefix or bundle id. Grouping by the
    concrete role string is safe because a family with multiple
    distinct pairs per episode would assign each pair a distinct role
    label. Substring matching keeps the scorer family-agnostic.
    """
    groups: dict[str, list[str]] = {}
    for node in nodes:
        role = role_map.get(node, "")
        if substring in role:
            groups.setdefault(role, []).append(node)
    return groups


def compute_set_delta(episode: EpisodeSpec, selected: Iterable[str]) -> SetOutcome:
    """Return the SET-level oracle outcome for ``selected`` on ``episode``.

    EVALUATOR-side. Dereferences ``episode._answer_key``,
    ``episode.role``, and ``episode.utility`` — every one of those is a
    member of :attr:`IntegrityAudit.FORBIDDEN_ATTRS`. A policy callable
    whose source imports this function will therefore fail the wave0
    :meth:`IntegrityAudit.assert_clean` audit; the Wave 1b oracle-regret
    test suite pins that behaviour.

    Parameters
    ----------
    episode:
        The sealed :class:`EpisodeSpec` under test. Passing an
        :class:`EpisodeContext` (the policy-visible view) raises
        :class:`LeakageError` — the SET-level path is not exposed to
        policy code.
    selected:
        Candidate ids to score. Order does not affect the result; the
        returned :attr:`SetOutcome.selected_set` is sorted.

    Returns
    -------
    SetOutcome
        The SET-level ``Δ_task`` plus provenance fields.
    """
    if isinstance(episode, EpisodeContext):
        raise LeakageError(
            "compute_set_delta refuses an EpisodeContext (the policy-visible "
            "view). The SET-level oracle path requires the sealed EpisodeSpec; "
            "see wave1b/PREREGISTRATION.md §7."
        )
    if not isinstance(episode, EpisodeSpec):
        raise TypeError(
            "compute_set_delta requires an EpisodeSpec instance; got "
            f"{type(episode).__name__}"
        )

    selected_set = frozenset(selected)
    candidate_set = frozenset(episode.candidate_nodes)
    unknown = selected_set - candidate_set
    if unknown:
        raise ValueError(
            "compute_set_delta refuses nodes outside candidate_nodes: "
            f"{sorted(unknown)}"
        )

    # Sealed dereferences — required so any downstream policy that even
    # references this function's source fails IntegrityAudit.
    answer_key: tuple[str, ...] = episode._answer_key
    utility_map: Mapping[str, float] = episode.utility
    role_map: Mapping[str, str] = episode.role

    answer_set = frozenset(answer_key)
    hit_reward = 0.0
    miss_penalty = 0.0
    for node in selected_set:
        u = float(utility_map.get(node, 0.0))
        if node in answer_set:
            hit_reward += u
        else:
            miss_penalty += max(u, 0.0) * MISS_PENALTY_COEFFICIENT

    # Bundle interactions — group by concrete role so a family with
    # multiple pairs per episode is scored pair-by-pair. In the current
    # v2 families each pair uses a unique role label so grouping by
    # role degenerates to counting pair-membership on that pair.
    complementary_groups = _grouped_by_prefix(
        role_map, selected_set, _COMPLEMENTARY_SUBSTR
    )
    contradictory_groups = _grouped_by_prefix(
        role_map, selected_set, _CONTRADICTORY_SUBSTR
    )
    dangerous_groups = _grouped_by_prefix(
        role_map, selected_set, _DANGEROUS_SUBSTR
    )
    isolation_groups = _grouped_by_prefix(
        role_map, selected_set, _ISOLATION_SUBSTR
    )

    # In the delayed_commitments_v2 and maintenance_fault_v2 vocabularies
    # both members of a complementary pair share one role label
    # (``complementary_pair_member_v2``). A pair is "hit" when at least
    # two members are present. In resource_constrained_v2 the members
    # carry distinct labels (``complementary_pair_budget_cap`` and
    # ``complementary_pair_dependent_action``); a pair is hit when both
    # labels appear. The unified rule that covers both cases: count the
    # number of complementary members and treat every disjoint pair as
    # one hit.
    complementary_members = sum(len(v) for v in complementary_groups.values())
    complementary_pairs_hit = complementary_members // 2

    contradictory_members = sum(len(v) for v in contradictory_groups.values())
    contradictory_pairs_hit = contradictory_members // 2

    dangerous_members = sum(len(v) for v in dangerous_groups.values())
    dangerous_triples_hit = dangerous_members // 3

    isolation_hits = sum(len(v) for v in isolation_groups.values())

    bundle_adjustment = (
        COMPLEMENTARY_JOINT_BONUS * complementary_pairs_hit
        - CONTRADICTORY_JOINT_PENALTY * contradictory_pairs_hit
        - DANGEROUS_TRIPLE_PENALTY * dangerous_triples_hit
        - ISOLATION_CONTEXT_PENALTY * isolation_hits
    )

    raw_delta = hit_reward - miss_penalty + bundle_adjustment
    delta = max(DELTA_CLAMP_LO, min(DELTA_CLAMP_HI, raw_delta))

    return SetOutcome(
        selected_set=tuple(sorted(selected_set)),
        delta_task=float(delta),
        hit_reward=float(hit_reward),
        miss_penalty=float(miss_penalty),
        bundle_adjustment=float(bundle_adjustment),
        complementary_pairs_hit=int(complementary_pairs_hit),
        contradictory_pairs_hit=int(contradictory_pairs_hit),
        dangerous_triples_hit=int(dangerous_triples_hit),
        isolation_hits=int(isolation_hits),
    )


# --------------------------------------------------------------------------- #
# OracleSealedEnvironment                                                     #
# --------------------------------------------------------------------------- #


class OracleSealedEnvironment:
    """Sealed environment for oracle enumeration on ONE Wave 1b episode.

    Wraps a wave0 :class:`SealedEnvironment` (which owns the
    single-shot ``evaluate`` contract for the policy path) and adds
    :meth:`evaluate_set` — the SET-level oracle path.

    Contract
    --------
    * Wave 0's single-shot ``evaluate`` guard is preserved via
      composition: :meth:`evaluate` and :meth:`observe` delegate to the
      wrapped :class:`SealedEnvironment`. A policy still has exactly
      one legal call to ``evaluate``.
    * :meth:`evaluate_set` is the oracle-only path. Each unique
      ``(episode, S)`` key may be evaluated at most once; a second call
      with the same ``S`` raises :class:`SealedEvaluationError` so a
      duplicated enumeration step is loud rather than silently doubling
      the enumeration budget.
    * :meth:`as_policy_env` hands out the wrapped wave0
      :class:`SealedEnvironment` so a policy path never receives the
      oracle wrapper. The oracle wrapper itself is deliberately
      unreachable from policy code — any policy source that references
      :meth:`evaluate_set` will also fail :meth:`IntegrityAudit.assert_clean`
      because :func:`compute_set_delta` dereferences sealed fields.
    """

    def __init__(
        self,
        episode: EpisodeSpec,
        *,
        mode: SealedMode = "confirmatory",
    ) -> None:
        if not isinstance(episode, EpisodeSpec):
            raise TypeError(
                "OracleSealedEnvironment requires an EpisodeSpec; got "
                f"{type(episode).__name__}"
            )
        self._episode: EpisodeSpec = episode
        self._sealed_env: SealedEnvironment = SealedEnvironment(episode, mode=mode)
        self._set_evaluations: dict[frozenset[str], SetOutcome] = {}

    # ------------------------------------------------------------------ #
    # Delegation to the wave0 sealed environment (policy path)           #
    # ------------------------------------------------------------------ #

    @property
    def mode(self) -> SealedMode:
        """Wave 0 mode of the wrapped :class:`SealedEnvironment`."""
        return self._sealed_env.mode

    def observe(self, seed: int | None = None) -> EpisodeContext:
        """Delegate to :meth:`SealedEnvironment.observe`."""
        return self._sealed_env.observe(seed=seed)

    def evaluate(self, choice: RetrievalChoice) -> SealedOutcome:
        """Delegate to :meth:`SealedEnvironment.evaluate` — single-shot."""
        return self._sealed_env.evaluate(choice)

    def as_policy_env(self) -> SealedEnvironment:
        """Hand out the wave0 :class:`SealedEnvironment` for policy paths.

        Returning the wave0 wrapper — not this oracle wrapper — is the
        API-level guard that a policy path never sees the oracle
        surface. The wave0 :meth:`SealedEnvironment.evaluate` is
        already single-shot and refuses the second call.
        """
        return self._sealed_env

    # ------------------------------------------------------------------ #
    # Oracle-only SET-level evaluation                                   #
    # ------------------------------------------------------------------ #

    def evaluate_set(self, selected: Iterable[str]) -> SetOutcome:
        """Score a candidate set. **Oracle-only; at most one call per key.**

        Each unique ``S`` may be evaluated at most once. A duplicate
        call raises :class:`SealedEvaluationError`; the enumerator is
        expected to iterate distinct subsets, so a duplicate call
        signals a caller bug.

        Bundles are applied per the constants
        :data:`COMPLEMENTARY_JOINT_BONUS`,
        :data:`CONTRADICTORY_JOINT_PENALTY`,
        :data:`DANGEROUS_TRIPLE_PENALTY`, and
        :data:`ISOLATION_CONTEXT_PENALTY`, with the wave0 miss penalty
        applied per :data:`MISS_PENALTY_COEFFICIENT` and a final clamp
        to ``[DELTA_CLAMP_LO, DELTA_CLAMP_HI]``.
        """
        # Sentinel dereference — ``_answer_key`` is in
        # ``IntegrityAudit.FORBIDDEN_ATTRS``. Touching it in this method's
        # own source (not just in :func:`compute_set_delta`) is what
        # causes :meth:`IntegrityAudit.assert_clean` to fail when a
        # policy callable references ``evaluate_set`` directly.
        _sealed_answer_probe: tuple[str, ...] = self._episode._answer_key
        del _sealed_answer_probe
        key = frozenset(selected)
        if key in self._set_evaluations:
            raise SealedEvaluationError(
                "OracleSealedEnvironment.evaluate_set() may be called at "
                f"most once per (episode, S) key; got a duplicate call for "
                f"{sorted(key)} on episode {self._episode.episode_id!r}."
            )
        outcome = compute_set_delta(self._episode, key)
        self._set_evaluations[key] = outcome
        return outcome

    @property
    def set_evaluations(self) -> Mapping[frozenset[str], SetOutcome]:
        """Snapshot of the recorded ``(S, SetOutcome)`` history.

        Returned as a read-only :class:`MappingProxyType` view so
        downstream code can iterate deltas without being able to mutate
        the oracle's own accounting.
        """
        return MappingProxyType(dict(self._set_evaluations))

    def set_delta_map(self) -> Mapping[frozenset[str], float]:
        """Return ``S -> Δ_task(S)`` for every set already evaluated.

        Convenience projection used by :func:`simple_regret_set` and
        the wave1b oracle-regret receipt.
        """
        return MappingProxyType(
            {key: outcome.delta_task for key, outcome in self._set_evaluations.items()}
        )


__all__ = [
    "COMPLEMENTARY_JOINT_BONUS",
    "CONTRADICTORY_JOINT_PENALTY",
    "DANGEROUS_TRIPLE_PENALTY",
    "ISOLATION_CONTEXT_PENALTY",
    "MISS_PENALTY_COEFFICIENT",
    "DELTA_CLAMP_HI",
    "DELTA_CLAMP_LO",
    "OracleSealedEnvironment",
    "SetOutcome",
    "compute_set_delta",
]
