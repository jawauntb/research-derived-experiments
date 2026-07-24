"""Wave 1b ``resource_constrained_v2`` procedural family.

Redesigns the Wave 0 ``resource_constrained`` family under the Wave 1b
``PREREGISTRATION.md`` §4 corrections (Spencer echo-chamber critique + the
Wave 1a KILL scope):

* **Recency != oracle.** The load-bearing prior obligation is placed at a
  random *non-recent* position of the candidate event stream on every
  episode. The last three candidate slots are permanent recency
  distractors (a recent large-magnitude transaction alarm, a
  semantic-similarity decoy, and a recent neutral confirmation). The Wave
  0 baseline :func:`experiments.concern_gated_retrieval_e2.wave0.baselines.info_matched_recency`
  scores by ``1 / (1 + candidate_index)`` so any candidate at index >= 3
  is never in a top-2 recency pick — the pre-run assertion in
  ``PREREGISTRATION.md`` §4 (``oracle_recall_at_k(recency) < 0.8``)
  therefore holds structurally on every seed.

* **Bundle utilities are first-class.** Each episode plants, from
  ``PREREGISTRATION.md`` §4:

  - a useful singleton (the load-bearing prior obligation);
  - a contradictory pair — two obligations that are each useful alone but
    contradict when loaded together (an ``approval_grant`` and a
    ``rescission_note`` that overlap on scope);
  - a complementary pair — a budget cap set by a past decision plus a
    proposed action whose cost depends on that cap (each useless alone,
    valuable together);
  - a dangerous conjunction — three separately approved actions whose
    joint execution exceeds a resource limit not enforced per action;
  - an isolation distractor — a compatible-alternative-action with a
    higher care weight than the load-bearing obligation that appears
    useful on its own but harms the trajectory in context.

  The bundle membership is recorded on the evaluator-only ``role`` map,
  and :func:`bundle_manifest` extracts a :class:`BundleManifest` that the
  Wave 1b SET-level oracle enumerator consumes.

* **Same public API.** :func:`generate_episode`, :func:`calibration_seeds`,
  :func:`confirmatory_seeds`, and :func:`calibration_slate` mirror the
  Wave 0 module. The v2 module also exposes :func:`event_stream_order`,
  :func:`bundle_manifest`, and :data:`RECENT_ROLES` for the Wave 1b
  runner. The v2 module does NOT construct a Wave 0 withheld graph; the
  Wave 1b runner builds its own graph on the episode's node ids per
  ``PREREGISTRATION.md`` §4 (``LEARNED`` /
  ``FREQ_MATCHED_RANDOM`` / ``ORACLE_WITHHELD``).

Wrong prior (PREREGISTRATION.md §5 inherited from Wave 0). The
``care_anchors`` map still places ``W_ALARM_INIT = 1.0`` on the recent
large-magnitude transaction alarm, ``W_COMMIT_SUPPRESSED_INIT = 0.05`` on
the load-bearing prior obligation, and the uniform baseline
``W_UNIFORM_INIT = 0.5`` on the care-only global obligation so the wrong
prior is adversarial without being a total inversion. The isolation
distractor carries ``W_ISOLATION_INIT = 0.8`` — high enough that a
care-only top-``budget`` pick prefers the alarm plus the isolation
distractor over the true load-bearing obligation, but below the alarm so
the frozen "alarm is the loudest wrong-prior region" invariant survives.

Anti-leakage. :func:`generate_episode` never reads role labels, answer
keys, future utilities, or any evaluator-only field on its inputs. Every
returned :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`
carries the sealed role, utility, and answer key inside the evaluator-only
fields enumerated in ``wave0/PREREGISTRATION.md`` §4.1. The bundle-manifest
extractor and the event-stream helper are documented as evaluator-side
utilities; the Wave 0 :class:`IntegrityAudit` refuses any policy path that
calls them because both dereference ``episode.role``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
    ProceduralFamily,
    TemplateFamilySplit,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
    stable_template_id,
)


# --------------------------------------------------------------------------- #
# Family identity
# --------------------------------------------------------------------------- #

#: Procedural family name. Kept identical to the Wave 0 literal so the
#: sealed-env :data:`ProceduralFamily` guard admits the v2 episodes and so
#: the Wave 1b crossed runner can pair v2 rows with the Wave 0 wrong-prior
#: contract without any name remapping. The "v2" suffix lives on the
#: MODULE name; the FAMILY name stays ``"resource_constrained"``.
FAMILY_NAME: Final[ProceduralFamily] = "resource_constrained"

#: Human-readable id prefix. The v2 templates use the ``RC2-C-*`` /
#: ``RC2-X-*`` prefixes so a receipt row is unambiguously identifiable as
#: a v2 row even after the family literal is stripped.
FAMILY_ID_PREFIX: Final[str] = "RC2"

#: Number of calibration templates emitted by :func:`calibration_slate`.
#: Wave 1b's build brief inherits the Wave 0 floor of 30 templates per
#: family; 32 gives a clean seed range and matches the Wave 0 count for
#: parity.
NUM_CALIBRATION_TEMPLATES: Final[int] = 32

#: Number of confirmatory templates the family registers ids for. Sized
#: at the Wave 1b confirmatory seeds-per-cell requirement (``N = 300``,
#: ``PREREGISTRATION.md`` §5), so a Wave 1b cell can iterate a full
#: confirmatory strip without exhausting the reservation.
NUM_CONFIRMATORY_TEMPLATES: Final[int] = 300

#: Calibration seed sub-range for the v2 family. Sits inside Wave 0's
#: master calibration range ``100_000..100_999`` and is disjoint from
#: Wave 0's ``resource_constrained`` calibration slice
#: ``[100_200, 100_232)`` so a mixed run does not step on the frozen
#: Wave 0 receipt.
CALIBRATION_SEED_START: Final[int] = 100_600
CALIBRATION_SEED_END: Final[int] = CALIBRATION_SEED_START + NUM_CALIBRATION_TEMPLATES

#: Confirmatory seed sub-range for the v2 family. Sits inside Wave 0's
#: master confirmatory range ``200_000..201_999`` and is disjoint from
#: Wave 0's ``resource_constrained`` confirmatory slice
#: ``[200_200, 200_232)``.
CONFIRMATORY_SEED_START: Final[int] = 200_600
CONFIRMATORY_SEED_END: Final[int] = CONFIRMATORY_SEED_START + NUM_CONFIRMATORY_TEMPLATES

#: Retrieval budget scored by the sealed environment. Kept at 2 for
#: parity with the Wave 0 family so the wave0 sealed_env miss-penalty
#: arithmetic (``0.25 * max(u, 0)`` per non-answer selected) applies
#: unchanged.
DEFAULT_BUDGET: Final[int] = 2

#: Total number of event-stream positions per episode. 14 candidate slots
#: plus 2 always-visible context (pending) actions = 16. The candidate
#: count sits well below the Wave 1b oracle-enumerator ceiling
#: ``|V \\ R_t| <= 20`` (``PREREGISTRATION.md`` §7).
DEFAULT_GRAPH_SIZE: Final[int] = 16

#: Number of candidate slots per episode. 3 recency-locked recent
#: distractors plus 11 non-recent roles.
NUM_CANDIDATES: Final[int] = 14

#: Number of recency-locked recent-distractor slots at the *front* of
#: :attr:`EpisodeSpec.candidate_nodes`. The Wave 0 recency baseline
#: :func:`experiments.concern_gated_retrieval_e2.wave0.baselines.info_matched_recency`
#: scores each candidate by ``1 / (1 + index)``; keeping the load-bearing
#: obligation at a candidate index ``>= NUM_RECENT_SLOTS`` guarantees a
#: recency top-``budget`` pick never selects it, on any seed.
NUM_RECENT_SLOTS: Final[int] = 3


# --------------------------------------------------------------------------- #
# Wrong-prior magnitudes (frozen; inherit Wave 0's contract, add ISOLATION)
# --------------------------------------------------------------------------- #

#: Weight the wrong prior places on the recent large-transaction alarm.
W_ALARM_INIT: Final[float] = 1.0

#: Weight the wrong prior places on the load-bearing prior obligation.
#: Strictly below :data:`W_UNIFORM_INIT` — the prior actively suppresses
#: the true answer, matching the Wave 0 contract in
#: ``wave0/PREREGISTRATION.md`` §5(2).
W_COMMIT_SUPPRESSED_INIT: Final[float] = 0.05

#: Uniform baseline weight for policy-visible nodes without a dedicated
#: wrong-prior magnitude. Also the frozen weight of the care-only global
#: obligation, matching ``wave0/PREREGISTRATION.md`` §5(3): the wrong
#: prior is not a total inversion.
W_UNIFORM_INIT: Final[float] = 0.5

#: Weight the wrong prior places on the isolation distractor. Sits
#: strictly between the uniform baseline and the alarm weight so a
#: care-only top-``budget=2`` pick returns (alarm, isolation-distractor)
#: — never the suppressed load-bearing obligation. This is what makes
#: the isolation distractor a "compatible-alternative-action with higher
#: care weight than the load-bearing obligation" per the Wave 1b task
#: brief.
W_ISOLATION_INIT: Final[float] = 0.8


# --------------------------------------------------------------------------- #
# Sealed utility magnitudes (frozen; PREREGISTRATION.md §6 bounded reward)
# --------------------------------------------------------------------------- #

#: Sealed reward for loading the load-bearing prior obligation. Its
#: differential over the largest positive-utility distractor stays inside
#: the Wave 0 non-ceiling cap of ``0.6``, so no policy starts at ceiling.
U_OBLIGATION: Final[float] = 0.60

#: Positive-utility distractor magnitudes. The wave0 sealed environment
#: charges ``0.25 * max(u, 0)`` per selected non-answer, so keeping every
#: distractor's utility inside ``[0, 0.2]`` bounds the miss penalty and
#: keeps the sealed reward inside the ``[-1, +1]`` clamp.
U_ALARM: Final[float] = 0.20
U_ISOLATION_DISTRACTOR: Final[float] = 0.15
U_CONTRADICTORY_MEMBER: Final[float] = 0.15
U_SEMANTIC_DECOY: Final[float] = 0.10
U_CARE_GLOBAL: Final[float] = 0.10
U_DANGEROUS_MEMBER: Final[float] = 0.05
U_COMPLEMENTARY_MEMBER: Final[float] = 0.00
U_NEUTRAL: Final[float] = 0.00


# --------------------------------------------------------------------------- #
# Role labels (evaluator-only; recorded on ``EpisodeSpec.role``)
# --------------------------------------------------------------------------- #

#: Load-bearing prior obligation. Answer key.
ROLE_OBLIGATION: Final[str] = "prior_obligation"

#: Recent large-magnitude transaction alarm; loudest wrong-prior distractor.
ROLE_ALARM: Final[str] = "recent_large_transaction_alarm"

#: Care-only global obligation; matches the wrong prior's uniform
#: baseline. Kept for parity with the Wave 0 family so the wrong-prior
#: property test's "at least one true commitment region left at uniform"
#: check still holds.
ROLE_CARE_GLOBAL: Final[str] = "care_only_global_obligation"

#: Context-only alternate action (kept for parity with wave0 vocabulary;
#: the v2 layout uses the isolation-distractor role in this slot).
ROLE_CONTEXT_ALT: Final[str] = "context_only_alternate_action"

#: Neutral policy note; utility 0.0 filler.
ROLE_NEUTRAL: Final[str] = "neutral_policy_note"

#: Currently active pending action; part of ``context_nodes``, never a
#: candidate.
ROLE_CONTEXT_ACTION: Final[str] = "context_pending_action"

#: Complementary-pair member A — the budget cap set by a past decision.
#: Alone, ``Delta_task ~ 0``; loaded with the dependent proposed action,
#: ``Delta_task > 0``.
ROLE_COMPLEMENTARY_A: Final[str] = "complementary_pair_budget_cap"

#: Complementary-pair member B — the proposed action whose cost depends
#: on the cap. Alone, ``Delta_task ~ 0``; loaded with the cap,
#: ``Delta_task > 0``.
ROLE_COMPLEMENTARY_B: Final[str] = "complementary_pair_dependent_action"

#: Contradictory-pair member A — an approval grant that opens a scope.
ROLE_CONTRADICTORY_A: Final[str] = "contradictory_pair_approval_grant"

#: Contradictory-pair member B — a rescission note that closes the same
#: scope. Each is useful alone; loaded together their guidance
#: contradicts and net utility collapses below either alone.
ROLE_CONTRADICTORY_B: Final[str] = "contradictory_pair_rescission_note"

#: Dangerous-conjunction member A — separately approved action A. Safe
#: alone; jointly (A, B, C) exceed a resource limit that the sealed
#: evaluator treats as a constraint violation.
ROLE_DANGEROUS_A: Final[str] = "dangerous_conjunction_approved_action_a"

#: Dangerous-conjunction member B — separately approved action B. Safe
#: alone; jointly (A, B, C) exceed the resource limit.
ROLE_DANGEROUS_B: Final[str] = "dangerous_conjunction_approved_action_b"

#: Dangerous-conjunction member C — separately approved action C. Safe
#: alone; jointly (A, B, C) exceed the resource limit.
ROLE_DANGEROUS_C: Final[str] = "dangerous_conjunction_approved_action_c"

#: Isolation distractor — a compatible-alternative-action with a higher
#: care weight than the load-bearing obligation. Looks useful alone;
#: loaded alongside the active context, it harms the trajectory.
ROLE_ISOLATION_DISTRACTOR: Final[str] = "isolation_distractor_compat_alt_action"

#: Recent semantic-similarity decoy. Sits in the front of
#: ``candidate_nodes`` (recent) and is designed to maximise embedding
#: similarity to the active context — the "semantic-decoy" required by
#: ``PREREGISTRATION.md`` §4(3).
ROLE_SEMANTIC_DECOY: Final[str] = "recent_semantic_similarity_decoy"

#: Recent neutral confirmation. Sits in the front of ``candidate_nodes``
#: (recent), utility 0.0. Serves as a valid zero-utility filler for the
#: oracle-pick helper used by the anti-ceiling test.
ROLE_RECENT_NEUTRAL: Final[str] = "recent_neutral_confirmation"


#: Set of role labels that occupy the recency-locked front of
#: ``candidate_nodes``. Public because the Wave 1b crossed runner and
#: the pre-run recency-decoupling assertion both need to know which
#: roles are recent by construction.
RECENT_ROLES: Final[frozenset[str]] = frozenset(
    {ROLE_ALARM, ROLE_SEMANTIC_DECOY, ROLE_RECENT_NEUTRAL}
)


# --------------------------------------------------------------------------- #
# Per-episode role layout
# --------------------------------------------------------------------------- #

# Non-recent role slots. Exactly ``NUM_CANDIDATES - NUM_RECENT_SLOTS = 11``
# roles are placed at candidate indices ``[NUM_RECENT_SLOTS, NUM_CANDIDATES)``.
_NON_RECENT_ROLES: Final[tuple[str, ...]] = (
    ROLE_OBLIGATION,
    ROLE_COMPLEMENTARY_A,
    ROLE_COMPLEMENTARY_B,
    ROLE_CONTRADICTORY_A,
    ROLE_CONTRADICTORY_B,
    ROLE_DANGEROUS_A,
    ROLE_DANGEROUS_B,
    ROLE_DANGEROUS_C,
    ROLE_CARE_GLOBAL,
    ROLE_ISOLATION_DISTRACTOR,
    ROLE_NEUTRAL,
)

# Recent role slots. Exactly ``NUM_RECENT_SLOTS = 3`` roles occupy
# candidate indices ``[0, NUM_RECENT_SLOTS)`` — the recency-locked front
# of the tuple.
_RECENT_ROLE_SLOTS: Final[tuple[str, ...]] = (
    ROLE_ALARM,
    ROLE_SEMANTIC_DECOY,
    ROLE_RECENT_NEUTRAL,
)


@dataclass(frozen=True)
class _EpisodeLayout:
    """Concrete per-episode assignment of roles to candidate indices.

    The layout is a *pure function* of ``(seed, holdout)``. Two
    independent PRNGs perturb the non-recent and recent halves so
    seed-to-seed variation of the two halves cannot be inferred from one
    another. The recent front is a shuffled permutation of
    :data:`_RECENT_ROLE_SLOTS`; the non-recent tail is a shuffled
    permutation of :data:`_NON_RECENT_ROLES`.

    Attributes
    ----------
    role_at_index:
        Length-:data:`NUM_CANDIDATES` tuple whose ``i``-th entry is the
        role string sitting at candidate index ``i``. Indices
        ``[0, NUM_RECENT_SLOTS)`` are recent; indices
        ``[NUM_RECENT_SLOTS, NUM_CANDIDATES)`` are non-recent.
    load_bearing_index:
        Candidate index of :data:`ROLE_OBLIGATION`. Always
        ``>= NUM_RECENT_SLOTS`` by construction, so
        ``info_matched_recency`` never selects it at ``budget = 2``.
    """

    role_at_index: tuple[str, ...]
    load_bearing_index: int


def _rng(seed: int, holdout: str | None, salt: str) -> random.Random:
    """Deterministic per-purpose PRNG scoped by ``(seed, holdout, salt)``."""
    return random.Random(
        f"cogr-e2-wave1b::resource_constrained_v2::{salt}::{seed}::{holdout or ''}"
    )


def _pick_layout(seed: int, holdout: str | None) -> _EpisodeLayout:
    """Assign every candidate index a role for the given ``(seed, holdout)``.

    The non-recent tail is a seeded permutation of :data:`_NON_RECENT_ROLES`
    across indices ``[NUM_RECENT_SLOTS, NUM_CANDIDATES)`` — so
    :data:`ROLE_OBLIGATION` lands at a uniformly random non-recent index on
    every episode. That satisfies ``PREREGISTRATION.md`` §4(1) strictly
    (100% of episodes have a non-recent load-bearing memory, well above
    the required 50%).

    The recent front is a seeded permutation of :data:`_RECENT_ROLE_SLOTS`
    across indices ``[0, NUM_RECENT_SLOTS)``. Permuting the recent front
    prevents a policy from memorising the exact index of the alarm across
    seeds.
    """
    non_recent_rng = _rng(seed, holdout, "non_recent_layout")
    non_recent_order = list(_NON_RECENT_ROLES)
    non_recent_rng.shuffle(non_recent_order)

    recent_rng = _rng(seed, holdout, "recent_layout")
    recent_order = list(_RECENT_ROLE_SLOTS)
    recent_rng.shuffle(recent_order)

    role_at_index = tuple(recent_order) + tuple(non_recent_order)
    load_bearing_index = role_at_index.index(ROLE_OBLIGATION)

    # Belt-and-braces: the layout must satisfy the recency-decoupling
    # invariant on every seed. If this ever fails a downstream Wave 1b
    # cell would silently reproduce the Wave 1a KILL scope.
    if load_bearing_index < NUM_RECENT_SLOTS:
        raise AssertionError(
            "resource_constrained_v2 layout placed load-bearing obligation "
            "at a recent candidate index — recency-decoupling invariant "
            "violated."
        )
    if len(role_at_index) != NUM_CANDIDATES:
        raise AssertionError(
            "resource_constrained_v2 layout has the wrong number of "
            f"candidate slots (got {len(role_at_index)}, want "
            f"{NUM_CANDIDATES})."
        )

    return _EpisodeLayout(
        role_at_index=role_at_index,
        load_bearing_index=load_bearing_index,
    )


# --------------------------------------------------------------------------- #
# Node ids
# --------------------------------------------------------------------------- #


def _candidate_node_id(seed: int, index: int) -> str:
    """Return the candidate node id for ``(seed, candidate_index)``.

    Ids encode only the seed and the candidate index — not the role.
    Encoding the role would be an anti-leakage breach because
    ``candidate_nodes`` and their names are policy-visible.
    """
    return f"rc2_s{seed:06d}_c{index:02d}"


def _context_node_id(seed: int, index: int) -> str:
    """Return the pending-action node id for ``(seed, context_index)``.

    Two context nodes per episode; index 0 and 1.
    """
    return f"rc2_s{seed:06d}_x{index:02d}"


# --------------------------------------------------------------------------- #
# Assemblers
# --------------------------------------------------------------------------- #


def _candidate_nodes(seed: int) -> tuple[str, ...]:
    """Return the candidate id tuple in canonical index order (recent first).

    Order is by candidate index ``i in [0, NUM_CANDIDATES)`` and is a
    pure function of the seed. Recency baselines score by index, so this
    order is the recency signal.
    """
    return tuple(_candidate_node_id(seed, i) for i in range(NUM_CANDIDATES))


def _context_nodes(seed: int) -> tuple[str, ...]:
    return tuple(_context_node_id(seed, i) for i in range(2))


def _role_map(layout: _EpisodeLayout, seed: int) -> Mapping[str, str]:
    """Sealed role map: candidate node -> role, plus the context actions."""
    role: dict[str, str] = {}
    for i, r in enumerate(layout.role_at_index):
        role[_candidate_node_id(seed, i)] = r
    for j in range(2):
        role[_context_node_id(seed, j)] = ROLE_CONTEXT_ACTION
    return role


_ROLE_UTILITY: Final[Mapping[str, float]] = MappingProxyType(
    {
        ROLE_OBLIGATION: U_OBLIGATION,
        ROLE_ALARM: U_ALARM,
        ROLE_ISOLATION_DISTRACTOR: U_ISOLATION_DISTRACTOR,
        ROLE_CONTRADICTORY_A: U_CONTRADICTORY_MEMBER,
        ROLE_CONTRADICTORY_B: U_CONTRADICTORY_MEMBER,
        ROLE_SEMANTIC_DECOY: U_SEMANTIC_DECOY,
        ROLE_CARE_GLOBAL: U_CARE_GLOBAL,
        ROLE_DANGEROUS_A: U_DANGEROUS_MEMBER,
        ROLE_DANGEROUS_B: U_DANGEROUS_MEMBER,
        ROLE_DANGEROUS_C: U_DANGEROUS_MEMBER,
        ROLE_COMPLEMENTARY_A: U_COMPLEMENTARY_MEMBER,
        ROLE_COMPLEMENTARY_B: U_COMPLEMENTARY_MEMBER,
        ROLE_NEUTRAL: U_NEUTRAL,
        ROLE_RECENT_NEUTRAL: U_NEUTRAL,
    }
)


def _utility_map(layout: _EpisodeLayout, seed: int) -> Mapping[str, float]:
    """Sealed per-candidate singleton utility used by wave0 sealed_env.

    The wave0 :class:`SealedEnvironment` scores against ``answer_key``
    additively — ``hit_reward - miss_penalty`` where
    ``miss_penalty = 0.25 * max(u, 0)`` per non-answer selected. This map
    supplies those per-node utilities. Bundle-level interaction utilities
    (contradictory, complementary, dangerous, isolation) are recorded on
    the evaluator-side :class:`BundleManifest` and evaluated by the Wave
    1b SET-level oracle enumerator, not by the wave0 sealed env.
    """
    utility: dict[str, float] = {}
    for i, r in enumerate(layout.role_at_index):
        utility[_candidate_node_id(seed, i)] = float(_ROLE_UTILITY[r])
    return utility


def _care_anchors(layout: _EpisodeLayout, seed: int) -> Mapping[str, float]:
    """Adversarially misspecified concern prior for the v2 family.

    Every policy-visible node in the episode (candidates + context
    actions) receives a weight:

    * :data:`W_ALARM_INIT` on the recent large-transaction alarm;
    * :data:`W_ISOLATION_INIT` on the isolation distractor — above
      uniform so a care-only top-``budget=2`` returns
      (alarm, isolation-distractor), but strictly below the alarm so the
      alarm remains the loudest wrong-prior region (invariant carried
      from Wave 0's ``resource_constrained`` design);
    * :data:`W_COMMIT_SUPPRESSED_INIT` on the load-bearing prior
      obligation — strictly below uniform, so the wrong prior actively
      suppresses the answer region;
    * :data:`W_UNIFORM_INIT` on every remaining node, including the
      care-only global obligation and the context pending actions, so
      the wrong prior is not a total inversion.
    """
    prior: dict[str, float] = {}
    for i, r in enumerate(layout.role_at_index):
        node = _candidate_node_id(seed, i)
        if r == ROLE_ALARM:
            prior[node] = W_ALARM_INIT
        elif r == ROLE_OBLIGATION:
            prior[node] = W_COMMIT_SUPPRESSED_INIT
        elif r == ROLE_ISOLATION_DISTRACTOR:
            prior[node] = W_ISOLATION_INIT
        else:
            prior[node] = W_UNIFORM_INIT
    for j in range(2):
        prior[_context_node_id(seed, j)] = W_UNIFORM_INIT
    return MappingProxyType(prior)


# --------------------------------------------------------------------------- #
# Public evaluator-side helpers
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BundleManifest:
    """Evaluator-side record of the planted bundle structures.

    Consumed by the Wave 1b SET-level oracle enumerator to score
    ``Delta_task(S)`` on candidate sets and to compute the interaction-
    recovery metric named by ``PREREGISTRATION.md`` §7.

    Attributes
    ----------
    load_bearing_singleton:
        Node id of the load-bearing prior obligation. ``Delta_task > 0``
        alone (a "useful singleton" per §4(i)).
    contradictory_pair:
        The two contradictory-pair members. Each has positive singleton
        ``Delta_task``; loaded together their guidance contradicts and
        the joint ``Delta_task`` collapses (§4(ii)).
    complementary_pair:
        (budget-cap, dependent-action) — each useless alone,
        ``Delta_task > 0`` together (§4(iii)).
    dangerous_conjunction:
        Three separately approved actions, each safe alone; jointly
        their execution violates the sealed evaluator's resource
        constraint (§4(iv)).
    isolation_distractor:
        Compatible-alternative-action with a higher care weight than the
        load-bearing obligation. Positive ``Delta_task`` alone; harmful
        when loaded with the active context (§4(v)).
    """

    load_bearing_singleton: str
    contradictory_pair: tuple[str, str]
    complementary_pair: tuple[str, str]
    dangerous_conjunction: tuple[str, str, str]
    isolation_distractor: str


def bundle_manifest(episode: EpisodeSpec) -> BundleManifest:
    """Extract the planted :class:`BundleManifest` from a v2 episode.

    Evaluator-side helper. Reads the sealed :attr:`EpisodeSpec.role`
    field, so any policy that calls it is flagged by the Wave 0
    :class:`IntegrityAudit`. The Wave 1b SET-level oracle enumerator is
    the only intended caller.

    Raises :class:`ValueError` if the episode does not carry the v2 role
    vocabulary (e.g. a Wave 0 ``resource_constrained`` episode was
    passed by mistake).
    """
    role = dict(episode.role)
    by_role: dict[str, list[str]] = {}
    for node, r in role.items():
        by_role.setdefault(r, []).append(node)

    def _one(name: str) -> str:
        nodes = by_role.get(name, [])
        if len(nodes) != 1:
            raise ValueError(
                f"resource_constrained_v2 bundle_manifest expects exactly "
                f"one node with role {name!r}; got {nodes!r}"
            )
        return nodes[0]

    contradictory = (_one(ROLE_CONTRADICTORY_A), _one(ROLE_CONTRADICTORY_B))
    complementary = (_one(ROLE_COMPLEMENTARY_A), _one(ROLE_COMPLEMENTARY_B))
    dangerous = (
        _one(ROLE_DANGEROUS_A),
        _one(ROLE_DANGEROUS_B),
        _one(ROLE_DANGEROUS_C),
    )
    return BundleManifest(
        load_bearing_singleton=_one(ROLE_OBLIGATION),
        contradictory_pair=contradictory,
        complementary_pair=complementary,
        dangerous_conjunction=dangerous,
        isolation_distractor=_one(ROLE_ISOLATION_DISTRACTOR),
    )


def event_stream_order(episode: EpisodeSpec) -> tuple[str, ...]:
    """Return the candidate ids in chronological order (oldest first).

    ``candidate_nodes`` stores candidates in recency order (index 0 is
    most recent). This helper returns the reverse — the chronological
    order the family conceptually emits, oldest first — so the Wave 1b
    runner can drive the sealed environment with an event-stream view
    that reads left-to-right in time.

    The helper reads only ``episode.candidate_nodes`` and is therefore
    safe for policy paths, but the returned order is the same recency
    projection any policy can compute from ``candidate_nodes`` alone —
    it exposes no evaluator-only field.
    """
    return tuple(reversed(episode.candidate_nodes))


def load_bearing_candidate_index(episode: EpisodeSpec) -> int:
    """Return the candidate index of the load-bearing obligation.

    Evaluator-side helper — reads :attr:`EpisodeSpec.role`. Used by the
    pre-run recency-decoupling assertion to confirm that no v2 episode
    places the load-bearing obligation at a recent candidate index.
    """
    role = dict(episode.role)
    for i, node in enumerate(episode.candidate_nodes):
        if role.get(node) == ROLE_OBLIGATION:
            return i
    raise ValueError(
        "resource_constrained_v2 episode is missing a ROLE_OBLIGATION node"
    )


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #


def _validate_bucket(bucket: TemplateBucket) -> None:
    if not isinstance(bucket, TemplateBucket):
        raise TypeError(
            "bucket must be a TemplateBucket instance; got "
            f"{type(bucket).__name__}"
        )


def _validate_seed(seed: int, bucket: TemplateBucket) -> None:
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be a non-boolean int")
    if bucket is TemplateBucket.CALIBRATION:
        lo, hi = CALIBRATION_SEED_START, CALIBRATION_SEED_END
    else:
        lo, hi = CONFIRMATORY_SEED_START, CONFIRMATORY_SEED_END
    if not (lo <= seed < hi):
        raise ValueError(
            f"seed {seed} is outside the declared {bucket.value} range for "
            f"family {FAMILY_NAME!r} v2 ({lo}..{hi - 1}); refusing to generate"
        )


def _validate_holdout(holdout: str | None) -> None:
    if holdout is None:
        return
    if not isinstance(holdout, str) or not holdout:
        raise ValueError("holdout must be a non-empty string or None")


def _template_display_id(seed: int, bucket: TemplateBucket) -> str:
    """Return the human-readable per-template id (e.g. ``RC2-C-03``)."""
    if bucket is TemplateBucket.CALIBRATION:
        letter, start = "C", CALIBRATION_SEED_START
    else:
        letter, start = "X", CONFIRMATORY_SEED_START
    return f"{FAMILY_ID_PREFIX}-{letter}-{seed - start + 1:03d}"


def _bucket_to_split(bucket: TemplateBucket) -> TemplateFamilySplit:
    if bucket is TemplateBucket.CALIBRATION:
        return "calibration"
    return "confirmatory"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def generate_episode(
    seed: int,
    bucket: TemplateBucket,
    holdout: str | None = None,
) -> EpisodeSpec:
    """Return one sealed :class:`EpisodeSpec` for the v2 family.

    Parameters
    ----------
    seed:
        Generator seed. Must lie in the calibration or confirmatory
        sub-range declared by :data:`CALIBRATION_SEED_START` /
        :data:`CONFIRMATORY_SEED_START`; an out-of-range seed raises
        :class:`ValueError`.
    bucket:
        The template bucket. Determines both the seed range and the
        :attr:`EpisodeSpec.template_family_split` tag placed on the
        returned episode.
    holdout:
        Optional paraphrase-family holdout id recorded on the episode
        id. The v2 module carries the holdout through the id and the
        layout PRNGs but does not otherwise condition on it — the Wave
        1b crossed runner uses the holdout to keep confirmatory rows
        disjoint from any calibration paraphrases.

    Returns
    -------
    EpisodeSpec
        A frozen sealed episode carrying policy-visible context,
        candidates, care anchors, and budget, plus the sealed role,
        per-node utility, and answer key inside the evaluator-only
        fields enumerated in ``wave0/PREREGISTRATION.md`` §4.1. The
        sealed environment strips the sealed fields before any policy
        view is returned.

    Anti-leakage
    ------------
    The returned :class:`EpisodeSpec` is the evaluator-side object.
    Callers must wrap it in a :class:`SealedEnvironment` before any
    policy code sees it; the sealed environment's ``observe`` method
    returns the policy-visible :class:`EpisodeContext` view stripped of
    role, utility, and answer key.
    """
    _validate_bucket(bucket)
    _validate_seed(seed, bucket)
    _validate_holdout(holdout)

    layout = _pick_layout(seed, holdout)

    candidate_nodes = _candidate_nodes(seed)
    context_nodes = _context_nodes(seed)
    care_anchors = _care_anchors(layout, seed)
    role = _role_map(layout, seed)
    utility = _utility_map(layout, seed)
    load_bearing = _candidate_node_id(seed, layout.load_bearing_index)
    answer_key: tuple[str, ...] = (load_bearing,)

    display_id = _template_display_id(seed, bucket)
    stable_id = stable_template_id(FAMILY_NAME, seed, bucket)
    episode_id = f"{display_id}-{stable_id}"
    if holdout is not None:
        episode_id = f"{episode_id}-h{holdout}"

    return EpisodeSpec(
        episode_id=episode_id,
        template_family_split=_bucket_to_split(bucket),
        family=FAMILY_NAME,
        seed=seed,
        context_nodes=context_nodes,
        care_anchors=care_anchors,
        candidate_nodes=candidate_nodes,
        budget=DEFAULT_BUDGET,
        role=role,
        utility=utility,
        _answer_key=answer_key,
    )


def calibration_seeds() -> tuple[int, ...]:
    """Return the calibration seeds this family iterates over.

    Deterministic and process-stable: exactly
    ``range(CALIBRATION_SEED_START, CALIBRATION_SEED_END)`` in ascending
    order.
    """
    return tuple(range(CALIBRATION_SEED_START, CALIBRATION_SEED_END))


def confirmatory_seeds() -> tuple[int, ...]:
    """Return the confirmatory seeds reserved for the Wave 1b crossed run.

    Wave 1b calibration code paths never generate against this range —
    the seed-range guard in :func:`generate_episode` refuses a
    confirmatory seed in a calibration bucket and vice versa.
    """
    return tuple(range(CONFIRMATORY_SEED_START, CONFIRMATORY_SEED_END))


def calibration_slate() -> tuple[EpisodeSpec, ...]:
    """Return the full Wave 1b calibration slate for the v2 family.

    One :class:`EpisodeSpec` per calibration seed, in ascending seed
    order. The slate has :data:`NUM_CALIBRATION_TEMPLATES` entries
    (>= 30 per the Wave 0 build brief inherited by Wave 1b). Every
    returned episode carries ``template_family_split == "calibration"``
    and belongs to the calibration seed range for this family.
    """
    return tuple(
        generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        for seed in calibration_seeds()
    )


__all__ = [
    "BundleManifest",
    "CALIBRATION_SEED_END",
    "CALIBRATION_SEED_START",
    "CONFIRMATORY_SEED_END",
    "CONFIRMATORY_SEED_START",
    "DEFAULT_BUDGET",
    "DEFAULT_GRAPH_SIZE",
    "FAMILY_ID_PREFIX",
    "FAMILY_NAME",
    "NUM_CALIBRATION_TEMPLATES",
    "NUM_CANDIDATES",
    "NUM_CONFIRMATORY_TEMPLATES",
    "NUM_RECENT_SLOTS",
    "RECENT_ROLES",
    "ROLE_ALARM",
    "ROLE_CARE_GLOBAL",
    "ROLE_COMPLEMENTARY_A",
    "ROLE_COMPLEMENTARY_B",
    "ROLE_CONTEXT_ACTION",
    "ROLE_CONTEXT_ALT",
    "ROLE_CONTRADICTORY_A",
    "ROLE_CONTRADICTORY_B",
    "ROLE_DANGEROUS_A",
    "ROLE_DANGEROUS_B",
    "ROLE_DANGEROUS_C",
    "ROLE_ISOLATION_DISTRACTOR",
    "ROLE_NEUTRAL",
    "ROLE_OBLIGATION",
    "ROLE_RECENT_NEUTRAL",
    "ROLE_SEMANTIC_DECOY",
    "U_ALARM",
    "U_CARE_GLOBAL",
    "U_COMPLEMENTARY_MEMBER",
    "U_CONTRADICTORY_MEMBER",
    "U_DANGEROUS_MEMBER",
    "U_ISOLATION_DISTRACTOR",
    "U_NEUTRAL",
    "U_OBLIGATION",
    "U_SEMANTIC_DECOY",
    "W_ALARM_INIT",
    "W_COMMIT_SUPPRESSED_INIT",
    "W_ISOLATION_INIT",
    "W_UNIFORM_INIT",
    "bundle_manifest",
    "calibration_seeds",
    "calibration_slate",
    "confirmatory_seeds",
    "event_stream_order",
    "generate_episode",
    "load_bearing_candidate_index",
]
