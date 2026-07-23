"""Delayed commitments procedural family (Wave 0).

Wave 0's first procedural family. It instantiates the abstract Wave 0
retrieval problem — *identify the off-context fact whose loading would
improve the sealed outcome* — through the **delayed commitments** surface:

* **Active context.** A busy day's calendar entries (near-term meetings,
  chores, a couple of pending errands). The current representation is
  small and occupied with these items.
* **Off-context load-bearing fact.** A date-anchored personal commitment
  — a partner's birthday, a scheduled dependency, a promise — that was
  mentioned earlier in the day and has been out of active representation
  for many events. Loading it changes the sealed reward.
* **Distractors.**

  - *Context-only calendar trivia.* Items PPR-adjacent to the busy-day
    context but useless for the commitment (e.g. how many days in the
    month, a nearby unrelated meeting).
  - *Care-only chronic alarm.* A globally important but presently
    irrelevant crisis (a chronic news-style alert region the wrong prior
    overweights, PREREGISTRATION.md §5).
  - *Neutral filler.* Items neither elevated by the wrong prior nor
    PPR-adjacent to the busy-day context.

Wrong prior (PREREGISTRATION.md §5). ``care_anchors`` places
``w_alarm_init = 1.0`` on the current-day trending-news region,
``w_commit_init = 0.05`` on the date-anchored personal-obligation region,
and a small positive uniform baseline on every other node. At least one
true commitment region (the commitment neighbor) stays at uniform, so
the wrong prior is not a total inversion (PREREGISTRATION.md §5(3)).

Non-ceiling (PREREGISTRATION.md §6). The load-bearing target's utility
differential over the best positive-utility distractor is at most
``MAX_UTILITY_DIFF = 0.6`` so no reasonable two-sided method starts at
ceiling. The withheld graph places the commitment zone far from the
active-context zone along the family's timeline chain, so a plain
context-only personalized PageRank on the fixed withheld geometry can
not trivially hit@1 = 1 on every seed. That non-ceiling property is
regression-tested by ``tests/test_cogr_wave0_delayed_commitments.py``.

Own vocabulary. The role labels defined here (``off_context_commitment``,
``current_day_trending``, ``calendar_trivia``, …) are deliberately
disjoint from the frozen L0 pilot's role vocabulary in
``experiments/concern_gated_retrieval/benchmark.py`` (which uses
``commitment`` / ``family`` / ``global_alarm``). Wave 0's build brief
requires each procedural family to carry its own vocabulary; this
module honors that constraint.

Anti-leakage. The generator is a pure function of ``(seed, bucket,
holdout)``. It does not read role labels, answer keys, future utilities,
oracle concern, wrong-agent labels, paraphrase-family ids, generator
seed kinds, epiplexity future targets, or any sealed-outcome receipt —
every evaluator-only field enumerated in PREREGISTRATION.md §4.1. Every
returned :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`
carries role labels, per-node utility, and the answer key inside sealed
fields; the sealed environment strips them before any policy view is
returned.

Reuse boundary. Imports :func:`.graph_learn.build_withheld_graph` for the
authoritative node id space and (transitively) the frozen L0 pilot's
:class:`~experiments.concern_gated_retrieval.graph.WeightedGraph`. Does
not fork the pilot's graph or PageRank primitives, and does not depend
on ``experiments/concern_gated_retrieval/benchmark.py`` roles directly.

Wave 0 style boundary: this module describes calibration data
scaffolding plus wrong-prior initialization. It does not model learned
memory geometry, concern recovery, meaning, or selfhood.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping

from experiments.concern_gated_retrieval.graph import WeightedGraph
from experiments.concern_gated_retrieval_e2.wave0.graph_learn import (
    build_withheld_graph,
)
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
# Public constants
# --------------------------------------------------------------------------- #


#: Procedural family name. Matches the
#: :data:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.ProceduralFamily`
#: literal ``"delayed_commitments"``.
FAMILY_NAME: Final[ProceduralFamily] = "delayed_commitments"


#: Human-readable id prefix per PREREGISTRATION.md §6.1 (``DC-C-*`` for
#: calibration templates and ``DC-X-*`` for confirmatory templates).
FAMILY_ID_PREFIX: Final[str] = "DC"


#: Wave 0 wrong-prior weights (PREREGISTRATION.md §5). Frozen; not tuned
#: after Wave 0 signature. Wave 1 confirmatory rows are evaluated against
#: these exact weights via the frozen calibration receipt.
W_ALARM_INIT: Final[float] = 1.0
W_COMMIT_INIT: Final[float] = 0.05

#: Small positive uniform baseline for the non-alarm, non-commitment
#: regions. Kept strictly between :data:`W_COMMIT_INIT` and
#: :data:`W_ALARM_INIT` so the prior is adversarial rather than a total
#: inversion (PREREGISTRATION.md §5(3)).
W_UNIFORM_INIT: Final[float] = 0.20


#: Bounded reward differential ceiling (PREREGISTRATION.md §6). The
#: family clips the load-bearing target's utility to ensure the expected
#: differential over the best positive-utility distractor never exceeds
#: this value; that keeps every family non-ceiling.
MAX_UTILITY_DIFF: Final[float] = 0.6


#: Calibration seed range declared by PREREGISTRATION.md §10. Seeds
#: outside this range are refused for
#: :attr:`TemplateBucket.CALIBRATION` requests.
CALIBRATION_SEED_MIN: Final[int] = 100_000
CALIBRATION_SEED_MAX: Final[int] = 100_999

#: Confirmatory seed range declared by PREREGISTRATION.md §10. Seeds
#: outside this range are refused for
#: :attr:`TemplateBucket.CONFIRMATION` requests. Wave 0 policy code
#: never touches this range.
CONFIRMATION_SEED_MIN: Final[int] = 200_000
CONFIRMATION_SEED_MAX: Final[int] = 201_999


#: Fixed withheld-graph size for delayed_commitments. Kept in lock-step
#: with :func:`~experiments.concern_gated_retrieval_e2.wave0.graph_learn.build_withheld_graph`
#: so the episode's context / candidate / care node ids are exactly the
#: ids the withheld graph carries. Sized generously above
#: ``graph_learn.MIN_GRAPH_SIZE`` so four disjoint index zones fit.
GRAPH_SIZE: Final[int] = 32


#: Retrieval budget the sealed environment scores against. Small so the
#: policy must actually rank and choose; a wrong-prior policy that spends
#: both slots on the alarm cluster gets no positive utility on the
#: answer key.
DEFAULT_BUDGET: Final[int] = 2


# --------------------------------------------------------------------------- #
# Family-local role vocabulary (own, disjoint from the L0 pilot roles)
# --------------------------------------------------------------------------- #


#: The load-bearing off-context commitment. This is the answer key.
ROLE_LOAD_BEARING: Final[str] = "off_context_commitment"

#: The current-day trending news the wrong prior over-brightens.
ROLE_ALARM: Final[str] = "current_day_trending"

#: A calendar-trivia distractor: PPR-adjacent to the busy-day context but
#: not the load-bearing commitment.
ROLE_CONTEXT_DISTRACTOR: Final[str] = "calendar_trivia"

#: A commitment-lookalike distractor: sits in the commitment zone but is
#: not the answer. Wave 0 uses this to size the utility differential
#: cleanly (no distractor gets the load-bearing reward).
ROLE_COMMITMENT_NEIGHBOR: Final[str] = "adjacent_commitment_lookalike"

#: Neutral filler: neither loud nor context-adjacent. Occupies candidate
#: slots without payoff.
ROLE_NEUTRAL: Final[str] = "neutral_filler"

#: Active-context roles never appear in the candidate set; they name the
#: nodes returned in :attr:`EpisodeSpec.context_nodes`.
ROLE_CONTEXT_ITEM: Final[str] = "busy_day_context_item"


# --------------------------------------------------------------------------- #
# Sealed utility magnitudes (frozen; PREREGISTRATION.md §6, bounded reward)
# --------------------------------------------------------------------------- #


#: Sealed reward for loading the load-bearing off-context commitment.
#: Kept just below the +1.0 sealed-env clamp so a single correct
#: retrieval yields near-maximal reward without saturating.
U_LOAD_BEARING: Final[float] = 0.55

#: Positive miss-penalty distractors trigger the sealed_env miss cost
#: (``0.25 * max(u, 0)`` per selected non-answer). We keep them small so
#: the reward domain stays in ``[-1, +1]`` and the oracle-ceiling
#: headroom stays strictly positive on every seed.
U_ALARM: Final[float] = 0.15
U_CONTEXT_DISTRACTOR: Final[float] = 0.10
U_COMMITMENT_NEIGHBOR: Final[float] = 0.10
U_NEUTRAL: Final[float] = 0.00


# --------------------------------------------------------------------------- #
# Index zones inside the withheld graph
# --------------------------------------------------------------------------- #

# The withheld graph for ``delayed_commitments`` is a timeline chain plus
# a small set of seeded modulo-anchor skip edges (see
# :func:`~experiments.concern_gated_retrieval_e2.wave0.graph_learn._delayed_commitments_edges`).
# Placing the load-bearing commitment far from the active-context window
# along that chain is how Wave 0 keeps a plain context-only PPR baseline
# from trivially hitting the answer on every seed.
_CONTEXT_ZONE: Final[tuple[int, ...]] = tuple(range(2, 8))       # 6 indices
_ALARM_ZONE: Final[tuple[int, ...]] = tuple(range(10, 15))       # 5 indices
_COMMITMENT_ZONE: Final[tuple[int, ...]] = tuple(range(20, 27))  # 7 indices
_NEUTRAL_ZONE: Final[tuple[int, ...]] = tuple(range(27, 32))     # 5 indices


# --------------------------------------------------------------------------- #
# Paraphrase families and templates
# --------------------------------------------------------------------------- #


#: Paraphrase families for the delayed_commitments surface. Each family
#: represents a distinct wording style for the commitment (a partner's
#: birthday framing, a wedding anniversary framing, a child-school
#: deadline framing, a friend-host-night framing). The paraphrase-family
#: holdout is a Wave 0 required diversity axis (PREREGISTRATION.md §6.1
#: "Holdout scheme"). Test-side callers hold out at least one paraphrase
#: family per template from calibration.
PARAPHRASE_FAMILIES: Final[tuple[str, ...]] = (
    "partner_birthday",
    "wedding_anniversary",
    "child_school_deadline",
    "friend_host_night",
)


@dataclass(frozen=True)
class _TemplateSpec:
    """Static, deterministic per-template shape.

    A ``_TemplateSpec`` fixes the *macro* shape of a delayed_commitments
    episode: how many calendar-trivia distractors sit in the candidate
    set, how many alarm entries the wrong prior brightens, how many
    neutral filler items compete for the budget, and how many
    commitment-neighbor lookalikes sit in the commitment zone. The seed
    then perturbs which specific index each role lands on and the
    per-node utility magnitudes (within bounded ranges), so every
    ``(template_id, seed)`` pair is a distinct row but every seed within
    a template shares the same abstract retrieval problem.
    """

    template_id: str
    paraphrase_family: str
    bucket: TemplateBucket
    context_distractors: int
    alarms: int
    neutrals: int
    commitment_neighbors: int


def _build_templates() -> tuple[_TemplateSpec, ...]:
    """Return the frozen list of 48 delayed_commitments templates.

    16 calibration templates (``DC-C-01`` … ``DC-C-16``) and 32
    confirmatory templates (``DC-X-01`` … ``DC-X-32``) per
    PREREGISTRATION.md §6.1. Structural knobs vary across templates so
    the Wave 0 variance estimate covers a realistic spread. Every
    template respects the withheld-graph zone capacities declared above
    (``_CONTEXT_ZONE``, ``_ALARM_ZONE``, ``_COMMITMENT_ZONE``,
    ``_NEUTRAL_ZONE``) so no template runs the candidate set out of
    distinct graph indices.
    """
    templates: list[_TemplateSpec] = []

    # 16 calibration template shapes. Fields: (ctx_distractors, alarms,
    # neutrals, commitment_neighbors). Shapes fit inside the zone
    # capacities (context 6, alarm 5, neutral 5, commitment 7 minus one
    # slot reserved for the load-bearing answer).
    cal_shapes = [
        (2, 2, 2, 1),
        (2, 2, 2, 2),
        (3, 2, 2, 1),
        (3, 2, 2, 2),
        (2, 3, 2, 1),
        (2, 3, 2, 2),
        (3, 3, 2, 1),
        (3, 3, 2, 2),
        (2, 2, 3, 1),
        (2, 2, 3, 2),
        (3, 2, 3, 1),
        (3, 2, 3, 2),
        (2, 3, 3, 1),
        (2, 3, 3, 2),
        (3, 3, 3, 1),
        (3, 3, 3, 2),
    ]
    for i, (cd, al, ne, cn) in enumerate(cal_shapes, start=1):
        templates.append(
            _TemplateSpec(
                template_id=f"{FAMILY_ID_PREFIX}-C-{i:02d}",
                paraphrase_family=PARAPHRASE_FAMILIES[
                    (i - 1) % len(PARAPHRASE_FAMILIES)
                ],
                bucket=TemplateBucket.CALIBRATION,
                context_distractors=cd,
                alarms=al,
                neutrals=ne,
                commitment_neighbors=cn,
            )
        )

    # 32 confirmatory templates. Registered here for parity with
    # PREREGISTRATION.md §6.1. Wave 0 policy code never generates them;
    # they surface only when the caller-side template-registry gate has
    # been unlocked (see template_split.py).
    conf_shapes = [
        (2, 2, 2, 1), (2, 2, 2, 2), (3, 2, 2, 1), (3, 2, 2, 2),
        (2, 3, 2, 1), (2, 3, 2, 2), (3, 3, 2, 1), (3, 3, 2, 2),
        (2, 2, 3, 1), (2, 2, 3, 2), (3, 2, 3, 1), (3, 2, 3, 2),
        (2, 3, 3, 1), (2, 3, 3, 2), (3, 3, 3, 1), (3, 3, 3, 2),
        (2, 2, 4, 1), (2, 2, 4, 2), (3, 2, 4, 1), (3, 2, 4, 2),
        (2, 3, 4, 1), (2, 3, 4, 2), (3, 3, 4, 1), (3, 3, 4, 2),
        (2, 4, 2, 1), (2, 4, 2, 2), (3, 4, 2, 1), (3, 4, 2, 2),
        (2, 4, 3, 1), (2, 4, 3, 2), (3, 4, 3, 1), (3, 4, 3, 2),
    ]
    for i, (cd, al, ne, cn) in enumerate(conf_shapes, start=1):
        templates.append(
            _TemplateSpec(
                template_id=f"{FAMILY_ID_PREFIX}-X-{i:02d}",
                paraphrase_family=PARAPHRASE_FAMILIES[
                    (i - 1) % len(PARAPHRASE_FAMILIES)
                ],
                bucket=TemplateBucket.CONFIRMATION,
                context_distractors=cd,
                alarms=al,
                neutrals=ne,
                commitment_neighbors=cn,
            )
        )

    return tuple(templates)


#: Frozen list of all delayed_commitments templates (calibration +
#: confirmatory). ``len(TEMPLATES) == 48``, which is above the Wave 0
#: floor of 30 distinct templates. Wave 0 policy code only sees the
#: calibration subset via :func:`generate_episode`; the confirmatory
#: subset is registered here so the Wave 0 registry is authoritative
#: and seed-range validation can refuse a confirmatory seed in a
#: calibration call and vice versa.
TEMPLATES: Final[tuple[_TemplateSpec, ...]] = _build_templates()


#: Public template-id list in the canonical order that :data:`TEMPLATES`
#: iterates. Downstream Wave 0 receipts print these ids verbatim.
TEMPLATE_IDS: Final[tuple[str, ...]] = tuple(t.template_id for t in TEMPLATES)


def _templates_by_bucket(bucket: TemplateBucket) -> tuple[_TemplateSpec, ...]:
    return tuple(t for t in TEMPLATES if t.bucket is bucket)


def paraphrase_family_of(template_id: str) -> str:
    """Return the paraphrase family for a registered template id.

    Raises :class:`KeyError` when the id is not in :data:`TEMPLATES`.
    This is a lookup helper for the calibration receipt; it never
    surfaces confirmatory data to a policy caller because the caller has
    to already know the template id.
    """
    for template in TEMPLATES:
        if template.template_id == template_id:
            return template.paraphrase_family
    raise KeyError(f"unknown delayed_commitments template id: {template_id!r}")


# --------------------------------------------------------------------------- #
# Seed / holdout / bucket validation
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
        if not (CALIBRATION_SEED_MIN <= seed <= CALIBRATION_SEED_MAX):
            raise ValueError(
                f"calibration seed must be in "
                f"[{CALIBRATION_SEED_MIN}, {CALIBRATION_SEED_MAX}]; "
                f"got {seed}"
            )
    else:  # CONFIRMATION
        if not (CONFIRMATION_SEED_MIN <= seed <= CONFIRMATION_SEED_MAX):
            raise ValueError(
                f"confirmatory seed must be in "
                f"[{CONFIRMATION_SEED_MIN}, {CONFIRMATION_SEED_MAX}]; "
                f"got {seed}"
            )


def _classify_holdout(holdout: str | None) -> tuple[str | None, str | None]:
    """Split a holdout string into (paraphrase_family, template_id).

    Wave 0 supports two holdout kinds: whole-paraphrase-family holdout
    and whole-template holdout (PREREGISTRATION.md §6.1 "Holdout scheme"
    and the Wave 0 build brief). Both are exposed through a single
    ``holdout: str | None`` parameter to preserve API parity with the
    sibling families. The kind is inferred from the string:

    * a member of :data:`PARAPHRASE_FAMILIES` → paraphrase-family
      holdout;
    * a member of :data:`TEMPLATE_IDS` → whole-template holdout;
    * ``None`` → no holdout;
    * anything else → :class:`ValueError`.

    Returns ``(paraphrase_family, template_id)`` where at most one is
    non-``None``. The generator filters the calibration template pool
    accordingly.
    """
    if holdout is None:
        return (None, None)
    if not isinstance(holdout, str) or not holdout:
        raise TypeError("holdout must be a non-empty str or None")
    if holdout in PARAPHRASE_FAMILIES:
        return (holdout, None)
    if holdout in TEMPLATE_IDS:
        return (None, holdout)
    raise ValueError(
        "holdout must be a paraphrase family in "
        f"{list(PARAPHRASE_FAMILIES)} or a template id in TEMPLATE_IDS; "
        f"got {holdout!r}"
    )


def _select_template(
    seed: int,
    bucket: TemplateBucket,
    holdout: str | None,
) -> _TemplateSpec:
    """Pick one template deterministically for ``(seed, bucket, holdout)``.

    The candidate pool is every template in ``bucket`` whose
    ``paraphrase_family`` is not the paraphrase-family holdout (if any)
    and whose ``template_id`` is not the whole-template holdout (if
    any). The selection uses SHA-256 over ``(family, bucket, seed,
    holdout)`` and is process-stable — a seed's template is the same on
    every host.
    """
    pool = _templates_by_bucket(bucket)
    paraphrase_holdout, template_holdout = _classify_holdout(holdout)
    if paraphrase_holdout is not None:
        pool = tuple(
            t for t in pool if t.paraphrase_family != paraphrase_holdout
        )
    if template_holdout is not None:
        pool = tuple(t for t in pool if t.template_id != template_holdout)
    if not pool:
        raise ValueError(
            "no delayed_commitments templates remain after applying "
            f"holdout {holdout!r} to bucket {bucket.value!r}"
        )
    key = (
        f"cogr-e2-wave0::{FAMILY_NAME}::{bucket.value}::{seed}::"
        f"{holdout or ''}"
    ).encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    index = int(digest[:16], 16) % len(pool)
    return pool[index]


# --------------------------------------------------------------------------- #
# Node id and slot placement
# --------------------------------------------------------------------------- #


def _node_name(seed: int, index: int) -> str:
    """Return the withheld-graph-aligned node id for ``(seed, index)``.

    Matches :func:`graph_learn._node_name` so that the withheld graph
    built by :func:`graph_learn.build_withheld_graph(seed, size,
    "delayed_commitments")` shares its node namespace with the
    episode's context, candidate, and care-anchor node ids. Downstream
    Wave 0 baselines can plug the episode ids straight into a PPR run
    on the withheld graph without re-mapping.
    """
    return f"{FAMILY_NAME}_s{seed:06d}_n{index:03d}"


def _rng(seed: int, template_id: str, salt: str) -> random.Random:
    """Deterministic per-purpose PRNG scoped by ``(seed, template, salt)``."""
    return random.Random(
        f"cogr-e2-wave0::{FAMILY_NAME}::{template_id}::{salt}::{seed}"
    )


def _pick_distinct(
    rng: random.Random, zone: tuple[int, ...], count: int
) -> tuple[int, ...]:
    """Sample ``count`` distinct indices from ``zone`` without replacement.

    Raises :class:`ValueError` if ``count`` exceeds ``len(zone)``. Wave 0
    template shapes never request more indices than a zone contains;
    this guard exists so a shape-table typo fails loudly at generation
    time instead of silently truncating.
    """
    if count < 0:
        raise ValueError("count must be non-negative")
    if count > len(zone):
        raise ValueError(
            f"cannot draw {count} distinct indices from zone of size "
            f"{len(zone)}"
        )
    return tuple(rng.sample(list(zone), k=count))


@dataclass(frozen=True)
class _RoleLayout:
    """Deterministic per-episode role-to-index assignment.

    A layout binds concrete withheld-graph indices to the roles named by
    the family-local vocabulary. It is a pure function of
    ``(template_spec, seed)`` — the layout hash never consults any
    evaluator-only field.
    """

    load_bearing_idx: int
    alarm_idxs: tuple[int, ...]
    context_distractor_idxs: tuple[int, ...]
    commitment_neighbor_idxs: tuple[int, ...]
    neutral_idxs: tuple[int, ...]
    context_item_idxs: tuple[int, ...]


def _pick_layout(template: _TemplateSpec, seed: int) -> _RoleLayout:
    """Bind each role to a distinct withheld-graph index.

    The commitment zone yields the load-bearing index first (a random
    index in ``_COMMITMENT_ZONE``), then any commitment-neighbor
    lookalikes fill in the remaining commitment-zone slots. Alarm,
    context-distractor, and neutral roles draw from their respective
    zones. Active-context items come from the remaining unassigned
    entries of :data:`_CONTEXT_ZONE`, so the busy-day context is
    distinct from the calendar-trivia distractors that are candidates.
    """
    rng = _rng(seed, template.template_id, "layout")

    # Commitment zone: load-bearing + commitment neighbors.
    commitment_slots = _pick_distinct(
        rng, _COMMITMENT_ZONE, 1 + template.commitment_neighbors
    )
    load_bearing_idx = commitment_slots[0]
    commitment_neighbor_idxs = commitment_slots[1:]

    # Alarm zone.
    alarm_idxs = _pick_distinct(rng, _ALARM_ZONE, template.alarms)

    # Context zone: calendar-trivia distractors first, then the active
    # context items fall on any remaining context-zone indices.
    context_distractor_idxs = _pick_distinct(
        rng, _CONTEXT_ZONE, template.context_distractors
    )
    remaining_context = tuple(
        idx for idx in _CONTEXT_ZONE if idx not in context_distractor_idxs
    )
    if not remaining_context:
        # Zone capacities are sized so this is unreachable for every
        # declared template shape; guard-rail for future shape edits.
        raise ValueError(
            "context zone exhausted by distractors; template shape must "
            "leave at least one index for the active context"
        )
    # Use up to two active-context items so the busy-day context is a
    # small, occupied set.
    ctx_take = min(2, len(remaining_context))
    context_item_idxs = tuple(remaining_context[:ctx_take])

    # Neutral zone.
    neutral_idxs = _pick_distinct(rng, _NEUTRAL_ZONE, template.neutrals)

    return _RoleLayout(
        load_bearing_idx=load_bearing_idx,
        alarm_idxs=alarm_idxs,
        context_distractor_idxs=context_distractor_idxs,
        commitment_neighbor_idxs=commitment_neighbor_idxs,
        neutral_idxs=neutral_idxs,
        context_item_idxs=context_item_idxs,
    )


# --------------------------------------------------------------------------- #
# Wrong-prior, role, utility, and candidate assemblers
# --------------------------------------------------------------------------- #


def _wrong_prior(
    nodes: tuple[str, ...], layout: _RoleLayout, seed: int
) -> Mapping[str, float]:
    """Build the adversarially misspecified concern prior over ``nodes``.

    Every withheld-graph node gets a weight:

    * :data:`W_ALARM_INIT` on every alarm-zone node picked by the
      layout;
    * :data:`W_COMMIT_INIT` on the load-bearing commitment node —
      strictly *below* the uniform baseline, so the wrong prior actively
      suppresses the answer region (PREREGISTRATION.md §5(2));
    * :data:`W_UNIFORM_INIT` on every other node, including the
      commitment neighbors — so the wrong prior is not a total
      inversion (PREREGISTRATION.md §5(3)).

    The prior is deterministic in ``(seed, layout)`` and carries no
    role identity — the caller sees only a ``node_id -> weight`` map.
    """
    load_bearing = _node_name(seed, layout.load_bearing_idx)
    prior: dict[str, float] = {node: W_UNIFORM_INIT for node in nodes}
    for idx in layout.alarm_idxs:
        prior[_node_name(seed, idx)] = W_ALARM_INIT
    prior[load_bearing] = W_COMMIT_INIT
    return MappingProxyType(prior)


def _sealed_role_map(layout: _RoleLayout, seed: int) -> Mapping[str, str]:
    """Return the sealed role labels for every named node.

    Includes the active-context items so the calibration receipt can
    verify that context items and calendar-trivia distractors are
    distinct nodes (i.e. the busy-day context is not itself the
    candidate set).
    """
    role: dict[str, str] = {
        _node_name(seed, layout.load_bearing_idx): ROLE_LOAD_BEARING,
    }
    for idx in layout.alarm_idxs:
        role[_node_name(seed, idx)] = ROLE_ALARM
    for idx in layout.context_distractor_idxs:
        role[_node_name(seed, idx)] = ROLE_CONTEXT_DISTRACTOR
    for idx in layout.commitment_neighbor_idxs:
        role[_node_name(seed, idx)] = ROLE_COMMITMENT_NEIGHBOR
    for idx in layout.neutral_idxs:
        role[_node_name(seed, idx)] = ROLE_NEUTRAL
    for idx in layout.context_item_idxs:
        role[_node_name(seed, idx)] = ROLE_CONTEXT_ITEM
    return role


def _sealed_utility_map(
    layout: _RoleLayout, seed: int, template: _TemplateSpec
) -> Mapping[str, float]:
    """Sealed per-candidate utility with the non-ceiling clamp applied.

    Utility is fixed per role (the frozen ``U_*`` constants) and
    additionally clipped so the load-bearing target's differential over
    the best positive-utility distractor never exceeds
    :data:`MAX_UTILITY_DIFF`. That clip is a per-episode assertion of
    PREREGISTRATION.md §6's bounded-reward domain requirement.
    """
    rng = _rng(seed, template.template_id, "utility")

    utility: dict[str, float] = {}
    for idx in layout.alarm_idxs:
        utility[_node_name(seed, idx)] = U_ALARM + rng.uniform(-0.02, 0.02)
    for idx in layout.context_distractor_idxs:
        utility[_node_name(seed, idx)] = (
            U_CONTEXT_DISTRACTOR + rng.uniform(-0.02, 0.02)
        )
    for idx in layout.commitment_neighbor_idxs:
        utility[_node_name(seed, idx)] = (
            U_COMMITMENT_NEIGHBOR + rng.uniform(-0.02, 0.02)
        )
    for idx in layout.neutral_idxs:
        utility[_node_name(seed, idx)] = U_NEUTRAL + rng.uniform(-0.01, 0.01)

    load_bearing_node = _node_name(seed, layout.load_bearing_idx)
    utility[load_bearing_node] = U_LOAD_BEARING + rng.uniform(-0.02, 0.02)

    # Non-ceiling clamp: bound the load-bearing utility so its
    # differential over the best positive-utility distractor stays
    # inside MAX_UTILITY_DIFF. Distractors here have positive utility,
    # so the max is well-defined.
    distractor_ceiling = max(
        (u for node, u in utility.items() if node != load_bearing_node),
        default=0.0,
    )
    max_allowed = distractor_ceiling + MAX_UTILITY_DIFF
    if utility[load_bearing_node] > max_allowed:
        utility[load_bearing_node] = max_allowed

    return utility


def _candidate_nodes(layout: _RoleLayout, seed: int) -> tuple[str, ...]:
    """Return the candidate set in a role-ordered, seed-stable order.

    Order is fixed by role — load-bearing first, then alarms, then
    calendar-trivia distractors, then commitment neighbors, then
    neutrals. Wave 0 does not shuffle candidates per seed; the sealed
    environment's answer key is a set, not a rank list, and a policy
    that reads candidate order gains no information about the answer.
    """
    ordered: list[str] = [_node_name(seed, layout.load_bearing_idx)]
    for idx in layout.alarm_idxs:
        ordered.append(_node_name(seed, idx))
    for idx in layout.context_distractor_idxs:
        ordered.append(_node_name(seed, idx))
    for idx in layout.commitment_neighbor_idxs:
        ordered.append(_node_name(seed, idx))
    for idx in layout.neutral_idxs:
        ordered.append(_node_name(seed, idx))
    return tuple(ordered)


def _context_nodes(layout: _RoleLayout, seed: int) -> tuple[str, ...]:
    return tuple(_node_name(seed, idx) for idx in layout.context_item_idxs)


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
    """Return one sealed :class:`EpisodeSpec` for the delayed_commitments family.

    Parameters
    ----------
    seed:
        Row-level seed. Must lie in the declared calibration range
        ``[CALIBRATION_SEED_MIN, CALIBRATION_SEED_MAX]`` for
        :attr:`TemplateBucket.CALIBRATION` requests, or in the declared
        confirmatory range ``[CONFIRMATION_SEED_MIN,
        CONFIRMATION_SEED_MAX]`` for :attr:`TemplateBucket.CONFIRMATION`.
        An out-of-range seed raises :class:`ValueError`
        (PREREGISTRATION.md §10).
    bucket:
        The template family the caller is generating for. Confirmatory
        rows are only produced when the caller-side registry gate has
        already unlocked confirmatory access; see
        :mod:`experiments.concern_gated_retrieval_e2.wave0.template_split`.
    holdout:
        Optional holdout tag. Wave 0 supports two holdout kinds through
        the same parameter:

        * a paraphrase-family name in :data:`PARAPHRASE_FAMILIES`
          removes every template of that family from the selection
          pool;
        * a template id in :data:`TEMPLATE_IDS` removes that specific
          template.

        ``None`` (default) uses every template in the requested bucket.
        Any other value raises :class:`ValueError`.

    Returns
    -------
    EpisodeSpec
        A frozen sealed episode carrying policy-visible context, care
        anchors, candidate set, and budget, plus the sealed role
        labels, per-node utility, and answer key inside the
        evaluator-only fields. The sealed environment strips the sealed
        fields before any policy view is returned.

    Wave 0 style
    ------------
    The returned episode encodes calibration data plus the wrong prior
    of PREREGISTRATION.md §5. It is not a claim about learned memory,
    concern recovery, semantic meaning, or selfhood.
    """
    _validate_bucket(bucket)
    _validate_seed(seed, bucket)
    _classify_holdout(holdout)  # early validation before template pick

    template = _select_template(seed, bucket, holdout)
    layout = _pick_layout(template, seed)

    # Build the withheld graph so the episode's node namespace matches
    # the geometry a Wave 0 policy will run PPR on. The graph is not
    # carried on the EpisodeSpec (the sealed scoring does not need it),
    # but its node id set is authoritative.
    graph: WeightedGraph = build_withheld_graph(
        seed=seed, size=GRAPH_SIZE, family=FAMILY_NAME
    )
    nodes = graph.nodes

    context_nodes = _context_nodes(layout, seed)
    candidate_nodes = _candidate_nodes(layout, seed)
    care_anchors = _wrong_prior(nodes, layout, seed)
    role = _sealed_role_map(layout, seed)
    utility = _sealed_utility_map(layout, seed, template)
    answer_key: tuple[str, ...] = (_node_name(seed, layout.load_bearing_idx),)

    stable_id = stable_template_id(FAMILY_NAME, seed, bucket)
    episode_id = f"{template.template_id}::{stable_id}"
    if holdout is not None:
        episode_id = f"{episode_id}::h-{holdout}"

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


def calibration_template_ids() -> tuple[str, ...]:
    """Return the ordered tuple of calibration template ids.

    Deterministic and process-stable: exactly the ``DC-C-*`` entries of
    :data:`TEMPLATE_IDS`. Downstream Wave 0 calibration receipts iterate
    this tuple to build a per-template statistics table.
    """
    return tuple(
        t.template_id for t in TEMPLATES if t.bucket is TemplateBucket.CALIBRATION
    )


def confirmatory_template_ids() -> tuple[str, ...]:
    """Return the ordered tuple of confirmatory template ids.

    Wave 0 policy code never invokes :func:`generate_episode` on these
    ids. The helper exists so the calibration receipt can declare which
    template ids Wave 0 refuses to touch; it is not a permission to
    touch them.
    """
    return tuple(
        t.template_id for t in TEMPLATES if t.bucket is TemplateBucket.CONFIRMATION
    )


__all__ = [
    "CALIBRATION_SEED_MAX",
    "CALIBRATION_SEED_MIN",
    "CONFIRMATION_SEED_MAX",
    "CONFIRMATION_SEED_MIN",
    "DEFAULT_BUDGET",
    "FAMILY_ID_PREFIX",
    "FAMILY_NAME",
    "GRAPH_SIZE",
    "MAX_UTILITY_DIFF",
    "PARAPHRASE_FAMILIES",
    "ROLE_ALARM",
    "ROLE_COMMITMENT_NEIGHBOR",
    "ROLE_CONTEXT_DISTRACTOR",
    "ROLE_CONTEXT_ITEM",
    "ROLE_LOAD_BEARING",
    "ROLE_NEUTRAL",
    "TEMPLATE_IDS",
    "TEMPLATES",
    "U_ALARM",
    "U_COMMITMENT_NEIGHBOR",
    "U_CONTEXT_DISTRACTOR",
    "U_LOAD_BEARING",
    "U_NEUTRAL",
    "W_ALARM_INIT",
    "W_COMMIT_INIT",
    "W_UNIFORM_INIT",
    "calibration_template_ids",
    "confirmatory_template_ids",
    "generate_episode",
    "paraphrase_family_of",
]
