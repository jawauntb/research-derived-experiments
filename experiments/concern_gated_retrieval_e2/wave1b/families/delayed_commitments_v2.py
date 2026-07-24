"""Wave 1b redesigned ``delayed_commitments`` procedural family.

Wave 1a's KILL on ``delayed_commitments`` was two orthogonal problems:

1. ``info_matched_recency`` reproduced the oracle ceiling byte-for-byte
   because Wave 0's family placed the load-bearing memory at a
   family-consistent temporal offset that recency-ranking happened to
   catch every seed.
2. Utility was scored per-candidate additively, so the "useful bundle"
   / "dangerous conjunction" / "contradictory pair" phenomena that
   Spencer's echo-chamber critique named were not observable at all.

This v2 module addresses both. The load-bearing memory is placed at a
random NON-recent stream position on the great majority of episodes
(per-template mix ensures the aggregate rate is well under 50% even in
the ``load_bearing_recent`` variants). Every episode plants exactly one
"useful singleton" (the load-bearing memory itself) plus one additional
bundle plant drawn from the four combinatorial types
(``contradictory_pair``, ``complementary_pair``,
``dangerous_conjunction``, ``isolation_distractor``) selected by the
episode's template. The per-episode planting is recorded in an
evaluator-only :class:`BundleManifest`.

Anti-leakage. Every quantity the policy sees comes through
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeContext`.
The sealed :attr:`EpisodeSpec.role`, :attr:`EpisodeSpec.utility`, and
:attr:`EpisodeSpec._answer_key` fields carry the plant identities.
:class:`BundleManifest` lives in a module-level registry keyed by
``episode_id``; the accessor :func:`bundle_manifest` requires the sealed
:class:`EpisodeSpec` (never :class:`EpisodeContext`) and reads
``episode._answer_key`` inside its body so
:meth:`IntegrityAudit.assert_clean` flags any policy that even mentions
the sealed field.

Reuse boundary. Imports frozen Wave 0 primitives
(``build_withheld_graph``, ``SealedEnvironment``, ``EpisodeSpec``,
``TemplateBucket``, ``stable_template_id``) and never edits them. Uses
the same seed range partitioning as Wave 0 so paired-seed variance
estimation against Wave 0's calibration receipt stays legal.

Bundle contract. The additive scoring inside
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedEnvironment._score`
does not by itself realise non-additive bundle utilities. Wave 1b's
``utility.py`` and ``bundle_oracle.py`` (separate modules, not this file)
compose sealed rewards with the bundle labels this module plants to
produce the SET-level ``Delta_task`` and interaction-recovery metrics
Wave 1b's L1 gate scores against. This module's responsibility is
exclusively: (a) plant the bundle members at labelled positions, (b)
guarantee non-recent load-bearing placement, (c) emit the manifest so
downstream code can compute the non-additive quantities. It does not
itself claim non-additive utility inside the sealed env.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Final, Mapping, Sequence

from experiments.concern_gated_retrieval.graph import WeightedGraph
from experiments.concern_gated_retrieval_e2.wave0.graph_learn import (
    build_withheld_graph,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
    LeakageError,
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


#: Procedural family literal shared with Wave 0's
#: :data:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.ProceduralFamily`
#: enum. Wave 1b reuses the Wave 0 family tag so the sealed environment
#: and template-split guards accept v2 episodes without a schema change.
FAMILY_NAME: Final[ProceduralFamily] = "delayed_commitments"


#: Human-readable id prefix for v2 templates. Distinct from Wave 0's
#: ``DC`` so a v2 template id can never be mistaken for a Wave 0 one in
#: a receipt.
FAMILY_ID_PREFIX: Final[str] = "DC2"


#: Wave 0 adversarial-prior magnitudes (frozen; Wave 1b inherits them
#: unchanged so paired-seed variance estimates against Wave 0's frozen
#: calibration receipt stay legal).
W_ALARM_INIT: Final[float] = 1.0
W_COMMIT_INIT: Final[float] = 0.05
W_UNIFORM_INIT: Final[float] = 0.20


#: Bounded reward differential ceiling. The per-episode utility clamp
#: keeps the load-bearing target's expected differential over the best
#: positive-utility distractor at or below this value; that is the Wave
#: 0 non-ceiling contract carried into v2.
MAX_UTILITY_DIFF: Final[float] = 0.6


#: Calibration seed range. Wave 0 calibration seeds
#: ``100000..100999`` are the only inputs a v2 calibration call may
#: consume. Confirmatory seeds live in the disjoint window
#: ``200000..201999`` and are refused for calibration bucket requests.
CALIBRATION_SEED_MIN: Final[int] = 100_000
CALIBRATION_SEED_MAX: Final[int] = 100_999
CONFIRMATION_SEED_MIN: Final[int] = 200_000
CONFIRMATION_SEED_MAX: Final[int] = 201_999


#: Withheld-graph size for v2 episodes. Sized generously above the Wave
#: 0 v1 default (32) so the v2 zone layout — busy-day context, alarm
#: zone, mid-stream candidate pool that hosts the load-bearing memory
#: and the bundle plants, and neutral filler — fits without overlap.
GRAPH_SIZE: Final[int] = 64


#: Retrieval budget the sealed environment scores against. Kept at the
#: Wave 0 default (2) so any Wave 1b policy that runs on both Wave 0 and
#: Wave 1b families receives an identical decision surface.
DEFAULT_BUDGET: Final[int] = 2


# --------------------------------------------------------------------------- #
# Sealed utility magnitudes (per-node, additive scorer input only)
# --------------------------------------------------------------------------- #


U_LOAD_BEARING: Final[float] = 0.55
U_ALARM: Final[float] = 0.15
U_RECENT_DISTRACTOR: Final[float] = 0.10
U_SEMANTIC_DECOY: Final[float] = 0.12
U_CONTRADICTORY_MEMBER: Final[float] = 0.20
U_COMPLEMENTARY_MEMBER: Final[float] = 0.05
U_DANGEROUS_MEMBER: Final[float] = 0.10
U_ISOLATION_DISTRACTOR: Final[float] = 0.30
U_NEUTRAL: Final[float] = 0.00


# --------------------------------------------------------------------------- #
# Family-local role vocabulary (own; disjoint from wave0 v1 vocabulary)
# --------------------------------------------------------------------------- #


ROLE_LOAD_BEARING: Final[str] = "off_context_commitment_v2"
ROLE_ALARM: Final[str] = "current_day_trending_v2"
ROLE_RECENT_DISTRACTOR: Final[str] = "recent_calendar_item_v2"
ROLE_SEMANTIC_DECOY: Final[str] = "semantic_lookalike_v2"
ROLE_CONTRADICTORY: Final[str] = "contradictory_pair_member_v2"
ROLE_COMPLEMENTARY: Final[str] = "complementary_pair_member_v2"
ROLE_DANGEROUS: Final[str] = "dangerous_conjunction_member_v2"
ROLE_ISOLATION: Final[str] = "isolation_distractor_v2"
ROLE_NEUTRAL: Final[str] = "neutral_filler_v2"
ROLE_CONTEXT_ITEM: Final[str] = "busy_day_context_item_v2"


# --------------------------------------------------------------------------- #
# Paraphrase families
# --------------------------------------------------------------------------- #


PARAPHRASE_FAMILIES: Final[tuple[str, ...]] = (
    "partner_birthday",
    "wedding_anniversary",
    "child_school_deadline",
    "friend_host_night",
)


# --------------------------------------------------------------------------- #
# Bundle-plant taxonomy
# --------------------------------------------------------------------------- #


#: The five bundle types Spencer's echo-chamber correction requires.
#: :func:`generate_episode` guarantees the useful singleton (the
#: load-bearing memory) is planted every episode; the four other types
#: are planted per template so a uniform sample over the calibration
#: pool reaches every type.
BUNDLE_USEFUL_SINGLETON: Final[str] = "useful_singleton"
BUNDLE_CONTRADICTORY_PAIR: Final[str] = "contradictory_pair"
BUNDLE_COMPLEMENTARY_PAIR: Final[str] = "complementary_pair"
BUNDLE_DANGEROUS_CONJUNCTION: Final[str] = "dangerous_conjunction"
BUNDLE_ISOLATION_DISTRACTOR: Final[str] = "isolation_distractor"

BUNDLE_TYPES: Final[tuple[str, ...]] = (
    BUNDLE_USEFUL_SINGLETON,
    BUNDLE_CONTRADICTORY_PAIR,
    BUNDLE_COMPLEMENTARY_PAIR,
    BUNDLE_DANGEROUS_CONJUNCTION,
    BUNDLE_ISOLATION_DISTRACTOR,
)


_NON_SINGLETON_BUNDLES: Final[tuple[str, ...]] = (
    BUNDLE_CONTRADICTORY_PAIR,
    BUNDLE_COMPLEMENTARY_PAIR,
    BUNDLE_DANGEROUS_CONJUNCTION,
    BUNDLE_ISOLATION_DISTRACTOR,
)


# --------------------------------------------------------------------------- #
# BundleManifest — evaluator-only per-episode receipt
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BundleManifest:
    """Evaluator-only manifest of planted bundle members for one episode.

    Every field on this record is evaluator-only. The manifest is stored
    in a module-level registry keyed by ``episode_id`` and returned by
    :func:`bundle_manifest`, which requires the sealed
    :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`
    (never the policy-visible
    :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeContext`)
    and dereferences ``episode._answer_key`` inside its body so
    :meth:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.IntegrityAudit.assert_clean`
    flags every policy that even parses a reference to it. The manifest
    is downstream fuel for the SET-level oracle enumerator and the
    interaction-recovery receipt; it is not policy-visible.

    Attributes
    ----------
    episode_id:
        The sealed episode id the manifest belongs to.
    seed:
        Row-level seed. Reproduces the manifest deterministically.
    primary_bundle_type:
        Which of :data:`BUNDLE_TYPES` this episode's template focused
        on. ``BUNDLE_USEFUL_SINGLETON`` is the trivial case (no
        additional non-singleton plant); the other four names identify
        which combinatorial bundle sits in the candidate set alongside
        the load-bearing memory.
    useful_singleton:
        The load-bearing memory node id. Always non-``None``.
    contradictory_pair, complementary_pair, dangerous_conjunction,
    isolation_distractor:
        The corresponding planted candidate node ids for the four
        non-singleton bundle types. Exactly one of these four is
        non-``None`` per episode (matching
        ``primary_bundle_type``); the others are ``None``.
    semantic_decoy:
        Candidate labelled as the highest-embedding-similarity
        non-load-bearing item for this episode. Provides the
        ``embedding_similarity`` baseline with a labelled non-answer to
        prefer.
    stream_positions:
        Mapping from candidate node id to its position in the event
        stream (0 = most recent, per the Wave 0
        ``info_matched_recency`` convention where
        ``score = 1 / (1 + position)``). The tuple
        ``EpisodeSpec.candidate_nodes`` is emitted in ascending
        ``stream_positions`` order so the wave0 baseline receives its
        positions unaltered.
    load_bearing_position:
        Shorthand for ``stream_positions[useful_singleton]``.
    recent_positions:
        The stream positions the wave0 ``info_matched_recency`` baseline
        weights above chance (positions ``0``, ``1``, ``2`` under Wave
        0's ``1/(1+i)`` weighting). Downstream analysis compares
        ``load_bearing_position`` against this set.
    """

    episode_id: str
    seed: int
    primary_bundle_type: str
    useful_singleton: str
    contradictory_pair: tuple[str, str] | None
    complementary_pair: tuple[str, str] | None
    dangerous_conjunction: tuple[str, str, str] | None
    isolation_distractor: str | None
    semantic_decoy: str
    stream_positions: Mapping[str, int]
    load_bearing_position: int
    recent_positions: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.primary_bundle_type not in BUNDLE_TYPES:
            raise ValueError(
                "primary_bundle_type must be one of "
                f"{list(BUNDLE_TYPES)}; got {self.primary_bundle_type!r}"
            )
        object.__setattr__(
            self,
            "stream_positions",
            MappingProxyType(dict(self.stream_positions)),
        )


#: Module-level per-episode manifest registry. Populated by
#: :func:`generate_episode` and read by :func:`bundle_manifest`. The
#: registry is keyed by ``episode_id`` and grows for the lifetime of the
#: interpreter; test-suite consumers may call :func:`clear_manifests` to
#: reset it between rows.
_MANIFEST_REGISTRY: dict[str, BundleManifest] = {}


def clear_manifests() -> None:
    """Drop every registered bundle manifest. Used by tests between rows."""
    _MANIFEST_REGISTRY.clear()


# --------------------------------------------------------------------------- #
# Template registry
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _TemplateSpec:
    """Static, deterministic per-template shape.

    Fixes the macro shape of one v2 episode: which bundle to plant, how
    many recent distractors to emit, how many alarm distractors the
    wrong prior brightens, how many neutral filler slots exist, and
    whether this template is one of the (minority) variants that places
    the load-bearing memory inside the recent-position window.
    """

    template_id: str
    paraphrase_family: str
    bucket: TemplateBucket
    primary_bundle_type: str
    n_recent_distractors: int  # 3-5 per anti-recency constraint
    n_alarms: int
    n_neutrals: int
    load_bearing_recent: bool


def _build_templates() -> tuple[_TemplateSpec, ...]:
    """Return the frozen v2 template list.

    Calibration templates cover every bundle type at multiple
    recent-distractor counts. A minority of templates (``load_bearing_recent
    = True``) place the load-bearing memory inside the recent-position
    window; this keeps the sweep honest — a real "recency = oracle"
    reversal would appear at that variant, not be silently designed
    away. The aggregate fraction of episodes with
    ``load_bearing_recent`` templates stays well below 50% under uniform
    template selection.
    """
    templates: list[_TemplateSpec] = []

    # Calibration pool: 30 templates.
    # bundle types x n_recent x load_bearing_recent flag.
    cal_shapes: list[tuple[str, int, bool]] = []
    for bundle in (BUNDLE_USEFUL_SINGLETON,) + _NON_SINGLETON_BUNDLES:
        for n_recent in (3, 4, 5):
            cal_shapes.append((bundle, n_recent, False))
        # One recent-variant per bundle so the aggregate lb_recent rate
        # is 1 out of 4 == 25% per bundle group.
        cal_shapes.append((bundle, 4, True))
    # We now have 5 * (3 + 1) = 20 shapes; extend with mid-count non-recent
    # variants to hit 30.
    for bundle in (BUNDLE_USEFUL_SINGLETON,) + _NON_SINGLETON_BUNDLES:
        cal_shapes.append((bundle, 3, False))
        cal_shapes.append((bundle, 5, False))
    for i, (bundle, n_recent, lb_recent) in enumerate(cal_shapes, start=1):
        templates.append(
            _TemplateSpec(
                template_id=f"{FAMILY_ID_PREFIX}-C-{i:02d}",
                paraphrase_family=PARAPHRASE_FAMILIES[
                    (i - 1) % len(PARAPHRASE_FAMILIES)
                ],
                bucket=TemplateBucket.CALIBRATION,
                primary_bundle_type=bundle,
                n_recent_distractors=n_recent,
                n_alarms=2,
                n_neutrals=2,
                load_bearing_recent=lb_recent,
            )
        )

    # Confirmatory pool: 40 templates covering the same shape space.
    conf_shapes: list[tuple[str, int, bool]] = []
    for bundle in (BUNDLE_USEFUL_SINGLETON,) + _NON_SINGLETON_BUNDLES:
        for n_recent in (3, 4, 5):
            conf_shapes.append((bundle, n_recent, False))
        conf_shapes.append((bundle, 4, True))
    for bundle in (BUNDLE_USEFUL_SINGLETON,) + _NON_SINGLETON_BUNDLES:
        for n_recent in (3, 5):
            conf_shapes.append((bundle, n_recent, False))
        conf_shapes.append((bundle, 4, False))
    for i, (bundle, n_recent, lb_recent) in enumerate(conf_shapes, start=1):
        templates.append(
            _TemplateSpec(
                template_id=f"{FAMILY_ID_PREFIX}-X-{i:02d}",
                paraphrase_family=PARAPHRASE_FAMILIES[
                    (i - 1) % len(PARAPHRASE_FAMILIES)
                ],
                bucket=TemplateBucket.CONFIRMATION,
                primary_bundle_type=bundle,
                n_recent_distractors=n_recent,
                n_alarms=2,
                n_neutrals=2,
                load_bearing_recent=lb_recent,
            )
        )

    return tuple(templates)


#: Frozen v2 template list (calibration + confirmatory).
TEMPLATES: Final[tuple[_TemplateSpec, ...]] = _build_templates()


#: Public template-id list in the canonical order that :data:`TEMPLATES`
#: iterates. Downstream Wave 1b receipts print these ids verbatim.
TEMPLATE_IDS: Final[tuple[str, ...]] = tuple(t.template_id for t in TEMPLATES)


def _templates_by_bucket(bucket: TemplateBucket) -> tuple[_TemplateSpec, ...]:
    return tuple(t for t in TEMPLATES if t.bucket is bucket)


def calibration_template_ids() -> tuple[str, ...]:
    """Return the ordered tuple of calibration template ids."""
    return tuple(
        t.template_id
        for t in TEMPLATES
        if t.bucket is TemplateBucket.CALIBRATION
    )


def confirmatory_template_ids() -> tuple[str, ...]:
    """Return the ordered tuple of confirmatory template ids."""
    return tuple(
        t.template_id
        for t in TEMPLATES
        if t.bucket is TemplateBucket.CONFIRMATION
    )


def paraphrase_family_of(template_id: str) -> str:
    """Return the paraphrase family for a registered template id."""
    for template in TEMPLATES:
        if template.template_id == template_id:
            return template.paraphrase_family
    raise KeyError(
        f"unknown delayed_commitments_v2 template id: {template_id!r}"
    )


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
                "calibration seed must be in "
                f"[{CALIBRATION_SEED_MIN}, {CALIBRATION_SEED_MAX}]; "
                f"got {seed}"
            )
    else:
        if not (CONFIRMATION_SEED_MIN <= seed <= CONFIRMATION_SEED_MAX):
            raise ValueError(
                "confirmatory seed must be in "
                f"[{CONFIRMATION_SEED_MIN}, {CONFIRMATION_SEED_MAX}]; "
                f"got {seed}"
            )


def _classify_holdout(holdout: str | None) -> tuple[str | None, str | None]:
    """Split a holdout string into ``(paraphrase_family, template_id)``.

    Same shape as Wave 0's ``delayed_commitments._classify_holdout``.
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
    """Pick one template deterministically for ``(seed, bucket, holdout)``."""
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
            "no delayed_commitments_v2 templates remain after applying "
            f"holdout {holdout!r} to bucket {bucket.value!r}"
        )
    key = (
        f"cogr-e2-wave1b::{FAMILY_NAME}_v2::{bucket.value}::{seed}::"
        f"{holdout or ''}"
    ).encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    index = int(digest[:16], 16) % len(pool)
    return pool[index]


# --------------------------------------------------------------------------- #
# Node id and layout
# --------------------------------------------------------------------------- #


def _node_name(seed: int, index: int) -> str:
    """Return the withheld-graph-aligned node id for ``(seed, index)``."""
    return f"{FAMILY_NAME}_s{seed:06d}_n{index:03d}"


def _rng(seed: int, template_id: str, salt: str) -> random.Random:
    return random.Random(
        f"cogr-e2-wave1b::{FAMILY_NAME}_v2::{template_id}::{salt}::{seed}"
    )


# Graph-index zones. Non-overlapping ranges covering the full
# ``GRAPH_SIZE = 64`` node id space. The context zone hosts the
# busy-day active-context items; the alarm zone hosts the nodes the
# wrong prior brightens; the mid zone hosts the load-bearing memory,
# the semantic decoy, the bundle plants, and the recent-distractor
# candidates; the neutral zone hosts filler.
_CONTEXT_ZONE: Final[tuple[int, ...]] = tuple(range(0, 6))       # 6 slots
_ALARM_ZONE: Final[tuple[int, ...]] = tuple(range(6, 11))        # 5 slots
_MID_ZONE: Final[tuple[int, ...]] = tuple(range(11, 52))         # 41 slots
_NEUTRAL_ZONE: Final[tuple[int, ...]] = tuple(range(52, 64))     # 12 slots


@dataclass(frozen=True)
class _RoleLayout:
    """Per-episode role-to-graph-index binding and stream-position map."""

    load_bearing_idx: int
    load_bearing_stream_pos: int
    alarm_idxs: tuple[int, ...]
    recent_distractor_idxs: tuple[int, ...]
    contradictory_idxs: tuple[int, int] | None
    complementary_idxs: tuple[int, int] | None
    dangerous_idxs: tuple[int, int, int] | None
    isolation_distractor_idx: int | None
    semantic_decoy_idx: int
    neutral_idxs: tuple[int, ...]
    context_item_idxs: tuple[int, ...]
    #: candidate_index -> stream_position (0 == most recent). Length
    #: equals the candidate cardinality.
    stream_positions: Mapping[int, int]


#: The positions Wave 0's ``info_matched_recency`` weights above chance
#: under its ``1 / (1 + i)`` scoring — i.e., positions 0, 1, 2 dominate
#: recency-based rankings. Anti-recency = load-bearing must NOT sit at
#: one of these positions on at least 50% of episodes (in practice, the
#: v2 layout keeps it below 30%).
RECENT_POSITIONS: Final[tuple[int, ...]] = (0, 1, 2)


def _pick_layout(template: _TemplateSpec, seed: int) -> _RoleLayout:
    """Bind roles to distinct graph indices and stream positions.

    * Context items come from :data:`_CONTEXT_ZONE`.
    * Alarms come from :data:`_ALARM_ZONE`.
    * Neutral filler comes from :data:`_NEUTRAL_ZONE`.
    * Load-bearing memory, semantic decoy, recent distractors, and
      bundle plants come from :data:`_MID_ZONE`. The mid zone is drawn
      as a shuffled iterator so every plant gets a distinct index.
    * Stream positions: the recent distractors occupy the first
      ``n_recent_distractors`` positions (positions ``0`` .. ``n_recent
      - 1``). The load-bearing memory sits at a random position at or
      beyond position ``n_recent_distractors`` unless the template's
      ``load_bearing_recent`` flag is set, in which case it sits at a
      random position inside :data:`RECENT_POSITIONS` (and one recent
      distractor is displaced to a later position so the position
      cardinality is preserved).
    """
    rng = _rng(seed, template.template_id, "layout")

    context_item_idxs = tuple(rng.sample(list(_CONTEXT_ZONE), k=2))
    alarm_idxs = tuple(rng.sample(list(_ALARM_ZONE), k=template.n_alarms))
    neutral_idxs = tuple(rng.sample(list(_NEUTRAL_ZONE), k=template.n_neutrals))

    mid_shuffled = list(_MID_ZONE)
    rng.shuffle(mid_shuffled)
    mid_iter = iter(mid_shuffled)

    def _take() -> int:
        return next(mid_iter)

    recent_distractor_idxs = tuple(
        _take() for _ in range(template.n_recent_distractors)
    )
    load_bearing_idx = _take()
    semantic_decoy_idx = _take()

    contradictory_idxs: tuple[int, int] | None = None
    complementary_idxs: tuple[int, int] | None = None
    dangerous_idxs: tuple[int, int, int] | None = None
    isolation_distractor_idx: int | None = None

    if template.primary_bundle_type == BUNDLE_CONTRADICTORY_PAIR:
        contradictory_idxs = (_take(), _take())
    elif template.primary_bundle_type == BUNDLE_COMPLEMENTARY_PAIR:
        complementary_idxs = (_take(), _take())
    elif template.primary_bundle_type == BUNDLE_DANGEROUS_CONJUNCTION:
        dangerous_idxs = (_take(), _take(), _take())
    elif template.primary_bundle_type == BUNDLE_ISOLATION_DISTRACTOR:
        isolation_distractor_idx = _take()
    # BUNDLE_USEFUL_SINGLETON: no additional plant beyond load-bearing.

    # Assemble the ordered list of candidate indices so we can assign
    # stream positions.
    candidate_idxs: list[int] = []
    candidate_idxs.append(load_bearing_idx)
    candidate_idxs.extend(alarm_idxs)
    candidate_idxs.extend(recent_distractor_idxs)
    if contradictory_idxs is not None:
        candidate_idxs.extend(contradictory_idxs)
    if complementary_idxs is not None:
        candidate_idxs.extend(complementary_idxs)
    if dangerous_idxs is not None:
        candidate_idxs.extend(dangerous_idxs)
    if isolation_distractor_idx is not None:
        candidate_idxs.append(isolation_distractor_idx)
    candidate_idxs.append(semantic_decoy_idx)
    candidate_idxs.extend(neutral_idxs)

    n_candidates = len(candidate_idxs)
    stream_positions: dict[int, int] = {}

    # Recent distractors occupy the first n_recent stream positions.
    for i, idx in enumerate(recent_distractor_idxs):
        stream_positions[idx] = i

    # Load-bearing stream position.
    if template.load_bearing_recent:
        # Place inside the recent window; displace whichever recent
        # distractor currently sits at that position to a later slot so
        # the position cardinality stays intact.
        recent_slot = rng.randint(0, min(2, template.n_recent_distractors - 1))
        for displaced_idx, pos in list(stream_positions.items()):
            if pos == recent_slot and displaced_idx != load_bearing_idx:
                # Move the displaced distractor to the first slot after
                # the recent window.
                stream_positions[displaced_idx] = template.n_recent_distractors
                break
        stream_positions[load_bearing_idx] = recent_slot
    else:
        # Pick a non-recent stream position at or beyond n_recent.
        # A minimum of position 3 is enforced so the wave0
        # info_matched_recency baseline's top-3 slice never touches
        # load-bearing on non-recent-variant templates.
        floor = max(template.n_recent_distractors, len(RECENT_POSITIONS))
        used_positions = set(stream_positions.values())
        available = [p for p in range(floor, n_candidates) if p not in used_positions]
        if not available:
            # Extremely narrow template — fall back to the highest
            # available position.
            available = [
                p for p in range(n_candidates) if p not in used_positions
            ]
            available = [p for p in available if p >= template.n_recent_distractors]
        stream_positions[load_bearing_idx] = available[
            rng.randrange(len(available))
        ]

    # Fill remaining positions.
    used_positions = set(stream_positions.values())
    available = [p for p in range(n_candidates) if p not in used_positions]
    rng.shuffle(available)
    for idx in candidate_idxs:
        if idx in stream_positions:
            continue
        stream_positions[idx] = available.pop()

    return _RoleLayout(
        load_bearing_idx=load_bearing_idx,
        load_bearing_stream_pos=stream_positions[load_bearing_idx],
        alarm_idxs=alarm_idxs,
        recent_distractor_idxs=recent_distractor_idxs,
        contradictory_idxs=contradictory_idxs,
        complementary_idxs=complementary_idxs,
        dangerous_idxs=dangerous_idxs,
        isolation_distractor_idx=isolation_distractor_idx,
        semantic_decoy_idx=semantic_decoy_idx,
        neutral_idxs=neutral_idxs,
        context_item_idxs=context_item_idxs,
        stream_positions=MappingProxyType(stream_positions),
    )


# --------------------------------------------------------------------------- #
# Wrong-prior, role, utility, candidate assemblers
# --------------------------------------------------------------------------- #


def _wrong_prior(
    nodes: tuple[str, ...],
    layout: _RoleLayout,
    seed: int,
) -> Mapping[str, float]:
    """Build the Wave 0 adversarial-misspecification prior over ``nodes``."""
    load_bearing = _node_name(seed, layout.load_bearing_idx)
    prior: dict[str, float] = {node: W_UNIFORM_INIT for node in nodes}
    for idx in layout.alarm_idxs:
        prior[_node_name(seed, idx)] = W_ALARM_INIT
    prior[load_bearing] = W_COMMIT_INIT
    return MappingProxyType(prior)


def _sealed_role_map(layout: _RoleLayout, seed: int) -> Mapping[str, str]:
    role: dict[str, str] = {}
    for idx in layout.context_item_idxs:
        role[_node_name(seed, idx)] = ROLE_CONTEXT_ITEM
    role[_node_name(seed, layout.load_bearing_idx)] = ROLE_LOAD_BEARING
    for idx in layout.alarm_idxs:
        role[_node_name(seed, idx)] = ROLE_ALARM
    for idx in layout.recent_distractor_idxs:
        role[_node_name(seed, idx)] = ROLE_RECENT_DISTRACTOR
    role[_node_name(seed, layout.semantic_decoy_idx)] = ROLE_SEMANTIC_DECOY
    if layout.contradictory_idxs is not None:
        for idx in layout.contradictory_idxs:
            role[_node_name(seed, idx)] = ROLE_CONTRADICTORY
    if layout.complementary_idxs is not None:
        for idx in layout.complementary_idxs:
            role[_node_name(seed, idx)] = ROLE_COMPLEMENTARY
    if layout.dangerous_idxs is not None:
        for idx in layout.dangerous_idxs:
            role[_node_name(seed, idx)] = ROLE_DANGEROUS
    if layout.isolation_distractor_idx is not None:
        role[_node_name(seed, layout.isolation_distractor_idx)] = ROLE_ISOLATION
    for idx in layout.neutral_idxs:
        role[_node_name(seed, idx)] = ROLE_NEUTRAL
    return role


def _sealed_utility_map(
    layout: _RoleLayout, seed: int, template: _TemplateSpec
) -> Mapping[str, float]:
    """Per-node sealed utility with the non-ceiling clamp applied.

    The utility scored by wave0 ``SealedEnvironment._score`` is
    per-node additive; the load-bearing memory is the sole answer-key
    node, so ``hit_reward = utility[load_bearing]`` on a correct
    retrieval and every other selected candidate contributes a
    ``0.25 * max(u, 0)`` miss penalty. Bundle interactions
    (super-additive complementary pairs, sub-additive contradictory
    pairs, constraint-violating dangerous conjunctions) are recovered
    by the Wave 1b ``utility.py`` / ``bundle_oracle.py`` modules from
    the :class:`BundleManifest`; they are not encoded inside the
    additive sealed scorer here.
    """
    rng = _rng(seed, template.template_id, "utility")
    utility: dict[str, float] = {}

    load_bearing_node = _node_name(seed, layout.load_bearing_idx)
    utility[load_bearing_node] = U_LOAD_BEARING + rng.uniform(-0.02, 0.02)

    for idx in layout.alarm_idxs:
        utility[_node_name(seed, idx)] = U_ALARM + rng.uniform(-0.02, 0.02)
    for idx in layout.recent_distractor_idxs:
        utility[_node_name(seed, idx)] = (
            U_RECENT_DISTRACTOR + rng.uniform(-0.02, 0.02)
        )
    utility[_node_name(seed, layout.semantic_decoy_idx)] = (
        U_SEMANTIC_DECOY + rng.uniform(-0.02, 0.02)
    )
    if layout.contradictory_idxs is not None:
        for idx in layout.contradictory_idxs:
            utility[_node_name(seed, idx)] = (
                U_CONTRADICTORY_MEMBER + rng.uniform(-0.02, 0.02)
            )
    if layout.complementary_idxs is not None:
        for idx in layout.complementary_idxs:
            utility[_node_name(seed, idx)] = (
                U_COMPLEMENTARY_MEMBER + rng.uniform(-0.01, 0.01)
            )
    if layout.dangerous_idxs is not None:
        for idx in layout.dangerous_idxs:
            utility[_node_name(seed, idx)] = (
                U_DANGEROUS_MEMBER + rng.uniform(-0.02, 0.02)
            )
    if layout.isolation_distractor_idx is not None:
        utility[_node_name(seed, layout.isolation_distractor_idx)] = (
            U_ISOLATION_DISTRACTOR + rng.uniform(-0.02, 0.02)
        )
    for idx in layout.neutral_idxs:
        utility[_node_name(seed, idx)] = U_NEUTRAL + rng.uniform(-0.01, 0.01)

    # Non-ceiling clamp.
    distractor_ceiling = max(
        (u for node, u in utility.items() if node != load_bearing_node),
        default=0.0,
    )
    max_allowed = distractor_ceiling + MAX_UTILITY_DIFF
    if utility[load_bearing_node] > max_allowed:
        utility[load_bearing_node] = max_allowed

    return utility


def _candidate_nodes_in_stream_order(
    layout: _RoleLayout, seed: int
) -> tuple[str, ...]:
    """Return the candidate tuple ordered by ascending stream position.

    ``candidate_nodes[0]`` is the most recent event (Wave 0
    ``info_matched_recency`` convention: ``score = 1 / (1 + i)``).
    """
    ordered = sorted(
        layout.stream_positions.items(),
        key=lambda kv: kv[1],
    )
    return tuple(_node_name(seed, idx) for idx, _pos in ordered)


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
    """Return one sealed :class:`EpisodeSpec` for delayed_commitments_v2.

    Parameters
    ----------
    seed:
        Row-level seed. Must lie in
        ``[CALIBRATION_SEED_MIN, CALIBRATION_SEED_MAX]`` for calibration
        buckets or ``[CONFIRMATION_SEED_MIN, CONFIRMATION_SEED_MAX]``
        for the confirmatory bucket.
    bucket:
        :class:`~experiments.concern_gated_retrieval_e2.wave0.template_split.TemplateBucket`
        selecting the calibration or confirmatory template pool.
    holdout:
        Optional paraphrase-family or template-id holdout tag; see
        :func:`_classify_holdout`.

    Returns
    -------
    EpisodeSpec
        A sealed episode carrying policy-visible context, care anchors,
        candidate set, and budget, plus role labels, per-candidate
        utility, and the load-bearing answer key inside the sealed
        fields. The evaluator-only :class:`BundleManifest` for the
        episode is registered in the module-level manifest registry and
        may be retrieved via :func:`bundle_manifest`.
    """
    _validate_bucket(bucket)
    _validate_seed(seed, bucket)
    _classify_holdout(holdout)

    template = _select_template(seed, bucket, holdout)
    layout = _pick_layout(template, seed)

    graph: WeightedGraph = build_withheld_graph(
        seed=seed, size=GRAPH_SIZE, family=FAMILY_NAME
    )
    nodes = graph.nodes

    context_nodes = _context_nodes(layout, seed)
    candidate_nodes = _candidate_nodes_in_stream_order(layout, seed)
    care_anchors = _wrong_prior(nodes, layout, seed)
    role = _sealed_role_map(layout, seed)
    utility = _sealed_utility_map(layout, seed, template)
    load_bearing_node = _node_name(seed, layout.load_bearing_idx)
    answer_key: tuple[str, ...] = (load_bearing_node,)

    stable_id = stable_template_id(FAMILY_NAME, seed, bucket)
    episode_id = f"{template.template_id}::{stable_id}"
    if holdout is not None:
        episode_id = f"{episode_id}::h-{holdout}"

    manifest = BundleManifest(
        episode_id=episode_id,
        seed=seed,
        primary_bundle_type=template.primary_bundle_type,
        useful_singleton=load_bearing_node,
        contradictory_pair=(
            (
                _node_name(seed, layout.contradictory_idxs[0]),
                _node_name(seed, layout.contradictory_idxs[1]),
            )
            if layout.contradictory_idxs is not None
            else None
        ),
        complementary_pair=(
            (
                _node_name(seed, layout.complementary_idxs[0]),
                _node_name(seed, layout.complementary_idxs[1]),
            )
            if layout.complementary_idxs is not None
            else None
        ),
        dangerous_conjunction=(
            (
                _node_name(seed, layout.dangerous_idxs[0]),
                _node_name(seed, layout.dangerous_idxs[1]),
                _node_name(seed, layout.dangerous_idxs[2]),
            )
            if layout.dangerous_idxs is not None
            else None
        ),
        isolation_distractor=(
            _node_name(seed, layout.isolation_distractor_idx)
            if layout.isolation_distractor_idx is not None
            else None
        ),
        semantic_decoy=_node_name(seed, layout.semantic_decoy_idx),
        stream_positions={
            _node_name(seed, idx): pos
            for idx, pos in layout.stream_positions.items()
        },
        load_bearing_position=layout.load_bearing_stream_pos,
        recent_positions=RECENT_POSITIONS,
    )
    _MANIFEST_REGISTRY[episode_id] = manifest

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


def bundle_manifest(episode: EpisodeSpec) -> BundleManifest:
    """Return the planted :class:`BundleManifest` for a sealed episode.

    **Evaluator-only.** This function is deliberately unreachable from
    any policy path:

    * The type contract requires an :class:`EpisodeSpec` (the sealed
      evaluator-side record). Passing an
      :class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeContext`
      raises :class:`LeakageError`, because the policy-visible view is
      typed differently and stripping the sealed fields is the whole
      point of the sealed environment.
    * The body dereferences ``episode._answer_key`` — a member of
      :data:`IntegrityAudit.FORBIDDEN_ATTRS` — so
      :meth:`IntegrityAudit.assert_clean` flags every policy callable
      that even parses a reference to this function's return value.

    Raises
    ------
    LeakageError
        If ``episode`` is not an :class:`EpisodeSpec` instance (e.g. a
        policy attempted to pass its :class:`EpisodeContext`).
    KeyError
        If the episode was never registered by :func:`generate_episode`.
    """
    if not isinstance(episode, EpisodeSpec):
        raise LeakageError(
            "bundle_manifest requires the sealed EpisodeSpec; the "
            "policy-visible EpisodeContext cannot access planted bundle "
            "labels. See wave1b/PREREGISTRATION.md §4."
        )
    # Explicit sealed-field dereference so IntegrityAudit.assert_clean
    # fires on any policy callable whose source references this helper's
    # return value (see FORBIDDEN_ATTRS in wave0.sealed_env).
    _sealed_answer_probe = episode._answer_key
    del _sealed_answer_probe
    manifest = _MANIFEST_REGISTRY.get(episode.episode_id)
    if manifest is None:
        raise KeyError(
            f"no bundle manifest registered for episode {episode.episode_id!r}"
        )
    return manifest


def recency_load_bearing_correlation(seeds: Sequence[int]) -> float:
    """Return the recency vs. load-bearing correlation on the given seeds.

    The pre-run assertion the Wave 1b preregistration §4 requires is
    that this quantity is strictly below ``0.5`` on every family.

    We define the correlation operationally as the fraction of episodes
    whose load-bearing memory sits at a stream position that Wave 0's
    :func:`~experiments.concern_gated_retrieval_e2.wave0.baselines.info_matched_recency`
    baseline weights above chance — namely positions in
    :data:`RECENT_POSITIONS` (``0``, ``1``, ``2`` under Wave 0's
    ``1 / (1 + i)`` weighting). A fraction of ``0.5`` would mean the
    baseline retrieves the load-bearing memory in its top-3 slot half
    the time; a v2 family that satisfies the anti-recency contract sits
    well below that.

    ``seeds`` may include ineligible values (out of the calibration
    range); those are skipped silently so the caller can pass e.g. a
    contiguous ``range()`` without pre-filtering. If every seed is
    skipped, the function returns ``0.0``.

    **Evaluator-only.** The body reads ``episode._answer_key`` and is
    therefore refused by :meth:`IntegrityAudit.assert_clean` on any
    policy path.
    """
    hits = 0
    total = 0
    recent_set = frozenset(RECENT_POSITIONS)
    for seed in seeds:
        try:
            episode = generate_episode(
                seed=seed, bucket=TemplateBucket.CALIBRATION
            )
        except (ValueError, TypeError):
            continue
        # Access the sealed answer to identify the load-bearing node.
        answer_key_node = episode._answer_key[0]
        try:
            position = episode.candidate_nodes.index(answer_key_node)
        except ValueError:
            # Load-bearing node missing from candidates would be a
            # generator bug; skip rather than crash the assertion.
            total += 1
            continue
        if position in recent_set:
            hits += 1
        total += 1
    if total == 0:
        return 0.0
    return hits / total


# --------------------------------------------------------------------------- #
# Pre-run assertion helper (evaluator-only)
# --------------------------------------------------------------------------- #


def oracle_recall_at_k_for_baseline(
    baseline_rank: Callable[..., Sequence[str]],
    seeds: Sequence[int],
    *,
    k: int = DEFAULT_BUDGET,
    bucket: TemplateBucket = TemplateBucket.CALIBRATION,
) -> float:
    """Return the fraction of seeds where ``baseline_rank``'s top-k
    intersects the sealed load-bearing answer set.

    This is the pre-run assertion helper Wave 1b uses to verify no
    generic-signal baseline reaches ``oracle_recall_at_k >= 0.8`` on
    the v2 family. The helper is deliberately in this module so the
    tests can call it without a bundle-oracle dependency.

    **Evaluator-only.** Reads ``episode._answer_key`` to compute recall.
    """
    from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
        SealedEnvironment,
    )

    hits = 0
    total = 0
    for seed in seeds:
        try:
            episode = generate_episode(seed=seed, bucket=bucket)
        except (ValueError, TypeError):
            continue
        env = SealedEnvironment(episode)
        context = env.observe(seed=seed)
        selected = tuple(baseline_rank(context, k))
        answer_set = frozenset(episode._answer_key)
        if answer_set & frozenset(selected):
            hits += 1
        total += 1
    if total == 0:
        return 0.0
    return hits / total


__all__ = [
    "BUNDLE_COMPLEMENTARY_PAIR",
    "BUNDLE_CONTRADICTORY_PAIR",
    "BUNDLE_DANGEROUS_CONJUNCTION",
    "BUNDLE_ISOLATION_DISTRACTOR",
    "BUNDLE_TYPES",
    "BUNDLE_USEFUL_SINGLETON",
    "BundleManifest",
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
    "RECENT_POSITIONS",
    "ROLE_ALARM",
    "ROLE_COMPLEMENTARY",
    "ROLE_CONTEXT_ITEM",
    "ROLE_CONTRADICTORY",
    "ROLE_DANGEROUS",
    "ROLE_ISOLATION",
    "ROLE_LOAD_BEARING",
    "ROLE_NEUTRAL",
    "ROLE_RECENT_DISTRACTOR",
    "ROLE_SEMANTIC_DECOY",
    "TEMPLATE_IDS",
    "TEMPLATES",
    "U_ALARM",
    "U_COMPLEMENTARY_MEMBER",
    "U_CONTRADICTORY_MEMBER",
    "U_DANGEROUS_MEMBER",
    "U_ISOLATION_DISTRACTOR",
    "U_LOAD_BEARING",
    "U_NEUTRAL",
    "U_RECENT_DISTRACTOR",
    "U_SEMANTIC_DECOY",
    "W_ALARM_INIT",
    "W_COMMIT_INIT",
    "W_UNIFORM_INIT",
    "bundle_manifest",
    "calibration_template_ids",
    "clear_manifests",
    "confirmatory_template_ids",
    "generate_episode",
    "oracle_recall_at_k_for_baseline",
    "paraphrase_family_of",
    "recency_load_bearing_correlation",
]
