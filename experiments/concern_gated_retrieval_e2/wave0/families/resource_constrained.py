"""Wave 0 ``resource_constrained`` procedural family.

This module is one of the three procedural family generators declared by
``experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md`` §6.3
(``resource_constrained``). The family instantiates the abstract Wave 0
retrieval problem — *identify the off-context fact whose loading would
improve the sealed outcome* — through a **ledger / obligation surface**:

* A hidden prior obligation (a resource reservation, a committed budget, or
  a standing dependency) changes which otherwise-valid action is best.
* The active context proposes actions consistent with the currently visible
  resource state.
* The off-context memory records the prior obligation that invalidates one
  of those actions.
* Distractors are three kinds:
  1. **Context-only alternate actions** — a right-half (action) node that
     the active context also plausibly justifies but is not the
     load-bearing pick.
  2. **Care-only global obligations** — a left-half (obligation) node the
     wrong prior brightens but that does not intersect the currently
     active resources.
  3. **Neutral policy notes** — nodes with neither strong context nor
     strong care alignment; they occupy candidate slots without being
     rewarding to load.

The concern prior is **adversarially misspecified** per PREREGISTRATION.md
§5:

* the alarm region (a "recent large-magnitude transaction" proxy) is
  inflated to ``w_alarm_init = 1.0``;
* the true load-bearing obligation region is **suppressed** to
  ``w_commit_init = 0.05`` — strictly below the uniform baseline;
* at least one other true commitment region is left at uniform, so the
  wrong prior is not a total inversion and a correctly designed method
  has surface to grip on.

Wave 0 does **not** update this prior. Wave 0 does **not** claim learned
memory geometry, concern recovery, semantic meaning, or selfhood. Wave 0
is calibration and family scaffolding plus wrong-prior initialization —
that is the entire promotable claim of this wave (see
``experiments/concern_gated_retrieval_e2/README.md`` § "Claim boundary").

Reuse boundary. This module imports :func:`.graph_learn.build_withheld_graph`
for the fixed withheld geometry and (via that module) the frozen L0 pilot's
:class:`~experiments.concern_gated_retrieval.graph.WeightedGraph`. It does
not fork the pilot's graph or PageRank primitives.

Anti-leakage. The generator never reads role labels, answer keys, future
utilities, oracle concern, wrong-agent labels, or paraphrase-family ids
from any input — its output *is* the sealed template. Every returned
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`
carries the sealed role/utility/answer key inside the evaluator-only
fields enumerated in PREREGISTRATION.md §4.1. Policy code obtains only
the :class:`EpisodeContext` view from
:class:`SealedEnvironment.observe`; it never sees an ``EpisodeSpec``.
"""

from __future__ import annotations

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


#: Procedural family name. Matches
#: :data:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.ProceduralFamily`
#: literal ``"resource_constrained"``.
FAMILY_NAME: Final[ProceduralFamily] = "resource_constrained"

#: Human-readable id prefix per PREREGISTRATION.md §6.3
#: (``RC-C-*`` for calibration, ``RC-X-*`` for confirmatory).
FAMILY_ID_PREFIX: Final[str] = "RC"

#: Number of calibration templates emitted by :func:`calibration_slate`.
#: Wave 0's build brief asks for at least 30 templates per family; 32 is
#: chosen to match the confirmatory count reserved in PREREGISTRATION.md
#: §6.3 and yields a clean seed range.
NUM_CALIBRATION_TEMPLATES: Final[int] = 32

#: Number of confirmatory templates the family registers ids for. Wave 0
#: never surfaces confirmatory rows to a caller — the
#: :class:`~experiments.concern_gated_retrieval_e2.wave0.template_split.TemplateRegistry`
#: gates them behind ``allow_confirmation=True`` **and** the caller-side
#: ``COGR_WAVE0_CONFIRMATORY_RUN`` env token — but the count is declared
#: here so downstream Wave 0 code can size the confirmatory reservation.
NUM_CONFIRMATORY_TEMPLATES: Final[int] = 32

#: Calibration seeds live in the block ``[100_200, 100_200 + 32)`` — a
#: sub-range of PREREGISTRATION.md §10's declared calibration seed range
#: ``100_000..100_999``. Each of the three procedural families uses a
#: disjoint 200-seed block inside that master range so cross-family seed
#: collisions cannot happen.
CALIBRATION_SEED_START: Final[int] = 100_200
CALIBRATION_SEED_END: Final[int] = CALIBRATION_SEED_START + NUM_CALIBRATION_TEMPLATES

#: Confirmatory seeds live in ``[200_200, 200_200 + 32)`` — a sub-range
#: of PREREGISTRATION.md §10's declared confirmatory seed range
#: ``200_000..201_999``. Wave 0 never generates against these seeds.
CONFIRMATORY_SEED_START: Final[int] = 200_200
CONFIRMATORY_SEED_END: Final[int] = CONFIRMATORY_SEED_START + NUM_CONFIRMATORY_TEMPLATES

#: The retrieval budget submitted to the sealed environment. Chosen so a
#: correctly aligned policy can afford to load the load-bearing obligation
#: plus at most one filler candidate; a wrong-prior policy that spends both
#: slots on the alarm-plus-context-alt pair walks away with a negative
#: sealed reward.
DEFAULT_BUDGET: Final[int] = 2

#: Number of nodes in the fixed withheld graph per template. Must be at
#: least :data:`~experiments.concern_gated_retrieval_e2.wave0.graph_learn.MIN_GRAPH_SIZE`
#: and even so the bipartite split has equal-size halves.
DEFAULT_GRAPH_SIZE: Final[int] = 16


# --------------------------------------------------------------------------- #
# Wrong-prior magnitudes (frozen; PREREGISTRATION.md §5)
# --------------------------------------------------------------------------- #


#: Weight the wrong prior places on the alarm region.
W_ALARM_INIT: Final[float] = 1.0

#: Weight the wrong prior places on the suppressed true commitment region.
#: Strictly below :data:`W_UNIFORM_INIT`.
W_COMMIT_SUPPRESSED_INIT: Final[float] = 0.05

#: Uniform baseline weight for all other policy-visible nodes.
W_UNIFORM_INIT: Final[float] = 0.5


# --------------------------------------------------------------------------- #
# Sealed utility magnitudes (frozen; PREREGISTRATION.md §6, bounded reward)
# --------------------------------------------------------------------------- #


#: Sealed reward for loading the load-bearing obligation. The differential
#: over the best positive-utility distractor is at most ``0.6`` per
#: PREREGISTRATION.md §6, so no reasonable two-sided method starts at
#: ceiling on this family.
U_OBLIGATION: Final[float] = 0.60

#: Sealed positive-utility distractors trigger the sealed_env miss penalty
#: (``0.25 * max(u, 0)`` per selected non-answer). We keep them modest so
#: the reward domain stays in ``[-1, +1]`` and headroom to the oracle
#: ceiling remains strictly positive for every calibration seed.
U_ALARM: Final[float] = 0.20
U_CONTEXT_ALT: Final[float] = 0.15
U_CARE_GLOBAL: Final[float] = 0.10
U_NEUTRAL_NOTE: Final[float] = 0.00


# --------------------------------------------------------------------------- #
# Sealed role labels (evaluator-only; enumerated for the receipt)
# --------------------------------------------------------------------------- #


#: The load-bearing prior obligation. Answer key.
ROLE_OBLIGATION: Final[str] = "prior_obligation"

#: Inflated alarm distractor. "Recent large-magnitude transaction" proxy.
ROLE_ALARM: Final[str] = "recent_large_transaction_alarm"

#: Context-only alternate action distractor.
ROLE_CONTEXT_ALT: Final[str] = "context_only_alternate_action"

#: Care-only global obligation that does not intersect current resources.
ROLE_CARE_GLOBAL: Final[str] = "care_only_global_obligation"

#: Neutral policy note; occupies a candidate slot without payoff.
ROLE_NEUTRAL: Final[str] = "neutral_policy_note"

#: Currently active context nodes (pending actions on the visible ledger).
#: These live in ``EpisodeSpec.context_nodes`` and are never candidates.
ROLE_CONTEXT_ACTION: Final[str] = "context_pending_action"


# --------------------------------------------------------------------------- #
# Per-template layout
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _RoleLayout:
    """Deterministic role-to-node-index assignment for one template.

    The layout is a *pure function* of ``(seed, size)`` and never consults
    any evaluator-only field. It picks:

    * two indices in the ``left`` (obligation) half — the load-bearing
      obligation and the care-only global obligation;
    * three indices in the ``right`` (action) half — the alarm distractor,
      the context-only alternate action, and one currently-active pending
      action that lives in ``context_nodes``;
    * two additional indices (one left, one right) as neutral policy notes;
    * one more right-half index as a second currently-active pending
      action, so ``len(context_nodes) == 2``.

    All eight roles are drawn from distinct indices.
    """

    obligation_idx: int  # left half; load-bearing answer
    care_global_idx: int  # left half; care-only distractor
    neutral_left_idx: int  # left half; neutral note
    alarm_idx: int  # right half; inflated distractor
    context_alt_idx: int  # right half; context-only distractor
    context_action_a_idx: int  # right half; active context
    context_action_b_idx: int  # right half; active context
    neutral_right_idx: int  # right half; neutral note


def _rng(seed: int, salt: str) -> random.Random:
    """Deterministic per-purpose PRNG scoped by ``(seed, salt)``."""
    return random.Random(f"cogr-e2-wave0::resource_constrained::{salt}::{seed}")


def _pick_layout(seed: int, size: int) -> _RoleLayout:
    """Assign the eight roles to distinct node indices for ``(seed, size)``.

    The bipartite split places left = obligations, right = actions, matching
    the ``resource_constrained`` topology in
    :func:`~experiments.concern_gated_retrieval_e2.wave0.graph_learn._resource_constrained_edges`.
    The layout uses a seeded PRNG separate from the edge PRNG so that
    template-to-template variation is genuinely per-template, not a
    projection of the edge stream.
    """
    if size < 8 or size % 2 != 0:
        raise ValueError(
            "resource_constrained requires an even DEFAULT_GRAPH_SIZE >= 8; "
            f"got size={size}"
        )
    split = size // 2
    left = list(range(0, split))
    right = list(range(split, size))
    rng = _rng(seed, "layout")
    rng.shuffle(left)
    rng.shuffle(right)
    # Left half needs three distinct indices; right half needs five.
    if len(left) < 3 or len(right) < 5:
        raise ValueError(
            "resource_constrained requires DEFAULT_GRAPH_SIZE >= 10 to fit "
            f"the eight-role layout; got size={size}"
        )
    return _RoleLayout(
        obligation_idx=left[0],
        care_global_idx=left[1],
        neutral_left_idx=left[2],
        alarm_idx=right[0],
        context_alt_idx=right[1],
        context_action_a_idx=right[2],
        context_action_b_idx=right[3],
        neutral_right_idx=right[4],
    )


def _node_name(seed: int, index: int) -> str:
    """Node id shared with :func:`graph_learn.build_withheld_graph`.

    Kept in lock-step so :func:`generate_episode` can pass the same node
    ids to a later concern-warp / PPR step without re-mapping.
    """
    return f"{FAMILY_NAME}_s{seed:06d}_n{index:03d}"


# --------------------------------------------------------------------------- #
# Public API
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
            f"family {FAMILY_NAME!r} ({lo}..{hi - 1}); refusing to generate"
        )


def _template_display_id(seed: int, bucket: TemplateBucket) -> str:
    """Return the human-readable per-template id, e.g. ``RC-C-03``.

    The numeric suffix is ``seed - <bucket_start> + 1`` (1-indexed to match
    the PREREGISTRATION.md §6.3 naming ``RC-C-01`` / ``RC-X-01``).
    """
    if bucket is TemplateBucket.CALIBRATION:
        letter, start = "C", CALIBRATION_SEED_START
    else:
        letter, start = "X", CONFIRMATORY_SEED_START
    return f"{FAMILY_ID_PREFIX}-{letter}-{seed - start + 1:02d}"


def _bucket_to_split(bucket: TemplateBucket) -> TemplateFamilySplit:
    """Map the template registry bucket onto the sealed-env split literal."""
    if bucket is TemplateBucket.CALIBRATION:
        return "calibration"
    return "confirmatory"


def _wrong_prior(nodes: tuple[str, ...], layout: _RoleLayout, seed: int) -> Mapping[str, float]:
    """Build the adversarially misspecified concern prior over ``nodes``.

    Every graph node gets a weight:

    * :data:`W_ALARM_INIT` on the alarm node;
    * :data:`W_COMMIT_SUPPRESSED_INIT` on the load-bearing obligation node;
    * :data:`W_UNIFORM_INIT` on every other node — including the care-only
      global obligation, so a well-designed method has surface to grip on.

    The prior is deterministic in ``(seed, layout)`` and carries no role
    identity — the caller sees only a ``node_id -> weight`` map.
    """
    alarm = _node_name(seed, layout.alarm_idx)
    obligation = _node_name(seed, layout.obligation_idx)
    prior: dict[str, float] = {node: W_UNIFORM_INIT for node in nodes}
    prior[alarm] = W_ALARM_INIT
    prior[obligation] = W_COMMIT_SUPPRESSED_INIT
    return MappingProxyType(prior)


def _sealed_role_map(layout: _RoleLayout, seed: int) -> Mapping[str, str]:
    return {
        _node_name(seed, layout.obligation_idx): ROLE_OBLIGATION,
        _node_name(seed, layout.alarm_idx): ROLE_ALARM,
        _node_name(seed, layout.context_alt_idx): ROLE_CONTEXT_ALT,
        _node_name(seed, layout.care_global_idx): ROLE_CARE_GLOBAL,
        _node_name(seed, layout.neutral_left_idx): ROLE_NEUTRAL,
        _node_name(seed, layout.neutral_right_idx): ROLE_NEUTRAL,
        _node_name(seed, layout.context_action_a_idx): ROLE_CONTEXT_ACTION,
        _node_name(seed, layout.context_action_b_idx): ROLE_CONTEXT_ACTION,
    }


def _sealed_utility_map(layout: _RoleLayout, seed: int) -> Mapping[str, float]:
    return {
        _node_name(seed, layout.obligation_idx): U_OBLIGATION,
        _node_name(seed, layout.alarm_idx): U_ALARM,
        _node_name(seed, layout.context_alt_idx): U_CONTEXT_ALT,
        _node_name(seed, layout.care_global_idx): U_CARE_GLOBAL,
        _node_name(seed, layout.neutral_left_idx): U_NEUTRAL_NOTE,
        _node_name(seed, layout.neutral_right_idx): U_NEUTRAL_NOTE,
    }


def _candidate_nodes(layout: _RoleLayout, seed: int) -> tuple[str, ...]:
    """Deterministic candidate set for one template.

    Order is fixed by role, not by seeded shuffle, so a policy cannot
    infer the answer from a per-seed permutation. The active pending
    actions live in ``context_nodes`` and are excluded from the
    candidate set.
    """
    return (
        _node_name(seed, layout.obligation_idx),
        _node_name(seed, layout.alarm_idx),
        _node_name(seed, layout.context_alt_idx),
        _node_name(seed, layout.care_global_idx),
        _node_name(seed, layout.neutral_left_idx),
        _node_name(seed, layout.neutral_right_idx),
    )


def _context_nodes(layout: _RoleLayout, seed: int) -> tuple[str, ...]:
    return (
        _node_name(seed, layout.context_action_a_idx),
        _node_name(seed, layout.context_action_b_idx),
    )


def generate_episode(
    seed: int,
    bucket: TemplateBucket,
    holdout: str | None = None,
) -> EpisodeSpec:
    """Return one sealed :class:`EpisodeSpec` for the resource-constrained family.

    Parameters
    ----------
    seed:
        Generator seed. Must lie in the calibration or confirmatory seed
        range for this family (see :data:`CALIBRATION_SEED_START` and
        :data:`CONFIRMATORY_SEED_START`); an out-of-range seed raises
        :class:`ValueError`.
    bucket:
        The template bucket. Determines both the seed range and the
        :attr:`EpisodeSpec.template_family_split` tag placed on the
        returned episode. Wave 0 policy code must only ever consume
        ``CALIBRATION`` episodes; the ``CONFIRMATION`` branch exists so
        Wave 1 can call the same generator without a family-specific
        code fork.
    holdout:
        Optional paraphrase-family holdout id recorded on the episode.
        Wave 0 never conditions on it; it is passed through so Wave 1's
        paraphrase-family split can register the intended holdout at
        template-construction time. If ``None``, no holdout is recorded.

    Returns
    -------
    EpisodeSpec
        A frozen sealed episode carrying the evaluator-only role, utility,
        and answer-key inside the sealed fields, and the policy-visible
        context / candidates / wrong-prior weights on the exposed fields.

    Anti-leakage
    ------------
    The returned :class:`EpisodeSpec` is the *evaluator-side* object.
    Callers must wrap it in a
    :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedEnvironment`
    before any policy code sees it; the sealed environment's ``observe``
    method returns the policy-visible :class:`EpisodeContext` view stripped
    of role, utility, and answer key.
    """
    _validate_bucket(bucket)
    _validate_seed(seed, bucket)
    if holdout is not None and (not isinstance(holdout, str) or not holdout):
        raise ValueError("holdout must be a non-empty string or None")

    size = DEFAULT_GRAPH_SIZE
    layout = _pick_layout(seed, size)

    # Nodes are read from the fixed withheld graph so that this template's
    # policy-visible node ids are exactly the ids the retrieval PPR step
    # will see. The graph is not carried on the EpisodeSpec (the sealed
    # scoring does not need it), but its node id space is authoritative.
    graph: WeightedGraph = build_withheld_graph(
        seed=seed, size=size, family=FAMILY_NAME
    )
    nodes = graph.nodes

    context_nodes = _context_nodes(layout, seed)
    candidate_nodes = _candidate_nodes(layout, seed)
    care_anchors = _wrong_prior(nodes, layout, seed)
    role = _sealed_role_map(layout, seed)
    utility = _sealed_utility_map(layout, seed)
    obligation = _node_name(seed, layout.obligation_idx)
    answer_key: tuple[str, ...] = (obligation,)

    display_id = _template_display_id(seed, bucket)
    # A process-stable id used by the calibration receipt to check that
    # ``seed 100207 in resource_constrained`` names the same row on every
    # host. Distinct from the human-readable ``RC-C-08`` display id.
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
    """Return the calibration seeds this family will iterate over.

    Deterministic and process-stable: exactly
    ``range(CALIBRATION_SEED_START, CALIBRATION_SEED_END)`` in ascending
    order. The Wave 0 calibration slate consumes the return value one
    seed per template.
    """
    return tuple(range(CALIBRATION_SEED_START, CALIBRATION_SEED_END))


def confirmatory_seeds() -> tuple[int, ...]:
    """Return the confirmatory seeds reserved for Wave 1.

    Wave 0 code never calls :func:`generate_episode` with a bucket of
    :attr:`TemplateBucket.CONFIRMATION`. This helper exists so the
    calibration receipt can declare which seed range Wave 0 refuses to
    touch; it is not a permission to touch it.
    """
    return tuple(range(CONFIRMATORY_SEED_START, CONFIRMATORY_SEED_END))


def calibration_slate() -> tuple[EpisodeSpec, ...]:
    """Return the full Wave 0 calibration slate for this family.

    One :class:`EpisodeSpec` per calibration seed, in ascending seed
    order. The slate has :data:`NUM_CALIBRATION_TEMPLATES` entries (at
    least 30 per the Wave 0 build brief). Every returned episode carries
    ``template_family_split == "calibration"`` and belongs to the
    calibration seed range for this family.

    The slate is not memoized — Wave 0's callers construct it once at
    Modal spawn time and pass the tuple to the sealed-env driver.
    """
    return tuple(
        generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        for seed in calibration_seeds()
    )


__all__ = [
    "CALIBRATION_SEED_END",
    "CALIBRATION_SEED_START",
    "CONFIRMATORY_SEED_END",
    "CONFIRMATORY_SEED_START",
    "DEFAULT_BUDGET",
    "DEFAULT_GRAPH_SIZE",
    "FAMILY_ID_PREFIX",
    "FAMILY_NAME",
    "NUM_CALIBRATION_TEMPLATES",
    "NUM_CONFIRMATORY_TEMPLATES",
    "ROLE_ALARM",
    "ROLE_CARE_GLOBAL",
    "ROLE_CONTEXT_ACTION",
    "ROLE_CONTEXT_ALT",
    "ROLE_NEUTRAL",
    "ROLE_OBLIGATION",
    "U_ALARM",
    "U_CARE_GLOBAL",
    "U_CONTEXT_ALT",
    "U_NEUTRAL_NOTE",
    "U_OBLIGATION",
    "W_ALARM_INIT",
    "W_COMMIT_SUPPRESSED_INIT",
    "W_UNIFORM_INIT",
    "calibration_seeds",
    "calibration_slate",
    "confirmatory_seeds",
    "generate_episode",
]
