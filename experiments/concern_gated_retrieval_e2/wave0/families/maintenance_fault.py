"""Maintenance and fault response procedural family (Wave 0).

Wave 0's second procedural family. It instantiates the abstract retrieval
problem "identify the off-context fact whose loading would improve the
sealed outcome" through a maintenance-log surface: an early, quiet
observation (a subtle sensor reading, a normally-ignored warning) becomes
load-bearing only after a later symptom appears in the active context.

Domain:

* **Active context.** A symptom that has just appeared plus a small
  amount of local operational chatter.
* **Off-context load-bearing fact.** An earlier observation buried in the
  maintenance history whose signature explains the current symptom.
* **Distractors.**

  - *Context-only sensor noise.* Recent noise that pattern-matches the
    symptom but has no causal relation to it.
  - *Care-only chronic alarm.* A loud, oft-repeated critical alert that
    the misspecified concern prior overweights, but that is unrelated to
    the present symptom.
  - *Neutral maintenance logs.* Routine boilerplate that neither
    explains the symptom nor is elevated by the concern prior.

Anti-leakage: the generator does not consult a policy view. It produces
role labels, per-node utilities, and the answer key inside the sealed
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.EpisodeSpec`
fields, which the sealed environment then strips before any policy sees
the episode.

Wrong prior (PREREGISTRATION.md §5): the ``care_anchors`` map places
``w_alarm_init = 1.0`` on the chronic critical-alert region and
``w_commit_init = 0.05`` on the load-bearing early observation region.
Neutral logs and context-noise distractors sit at a small positive
uniform baseline so no reasonable two-sided method starts at ceiling.

Non-ceiling (PREREGISTRATION.md §6): the bounded reward differential
between the load-bearing target and the best distractor is capped at
``0.6`` on every calibration seed.

Wave 0 style boundary: this module describes calibration data
scaffolding + wrong-prior initialization. It does not model learned
memory geometry, concern recovery, meaning, or selfhood.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Final, Literal

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import EpisodeSpec
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
    stable_template_id,
)


# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------


#: Wave 0 family name as declared by PREREGISTRATION.md §6.2.
FAMILY_NAME: Final[Literal["maintenance_fault"]] = "maintenance_fault"


#: Wave 0 wrong-prior weights (PREREGISTRATION.md §5). Do not tune these
#: after Wave 0 freeze; they are part of the adversarial-misspecification
#: contract that Wave 1 confirmatory rows will be evaluated against.
W_ALARM_INIT: Final[float] = 1.0
W_COMMIT_INIT: Final[float] = 0.05

#: Small positive uniform baseline for the non-alarm, non-commitment
#: regions. Kept strictly between :data:`W_COMMIT_INIT` and
#: :data:`W_ALARM_INIT` so the prior is adversarial rather than a total
#: inversion (PREREGISTRATION.md §5(3)).
W_UNIFORM_INIT: Final[float] = 0.20


#: Bounded reward differential ceiling (PREREGISTRATION.md §6). No
#: family generator may produce a calibration row whose load-bearing
#: target has an expected reward differential over the best distractor
#: greater than this value.
MAX_UTILITY_DIFF: Final[float] = 0.6


#: Calibration seed range (PREREGISTRATION.md §10). Seeds outside this
#: range are refused for :attr:`TemplateBucket.CALIBRATION` requests.
CALIBRATION_SEED_MIN: Final[int] = 100_000
CALIBRATION_SEED_MAX: Final[int] = 100_999

#: Confirmatory seed range (PREREGISTRATION.md §10). Seeds outside this
#: range are refused for :attr:`TemplateBucket.CONFIRMATION` requests.
CONFIRMATION_SEED_MIN: Final[int] = 200_000
CONFIRMATION_SEED_MAX: Final[int] = 201_999


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _TemplateSpec:
    """Static, deterministic per-template shape.

    A ``_TemplateSpec`` fixes the *macro* shape of an episode: how long
    the maintenance history is, how many distractors of each kind are
    injected, and how many wall-clock steps separate the buried early
    observation from the later symptom. The seed then perturbs the
    concrete signature strings and utility magnitudes within those
    slots, so every ``(template_id, seed)`` pair is a distinct row but
    every seed within a template shares the same abstract retrieval
    problem.

    Attributes
    ----------
    template_id:
        The Wave 0 template id declared by PREREGISTRATION.md §6.2.
    paraphrase_family:
        Surface-form family (log style). At least one paraphrase family
        per template is held out from calibration via the ``holdout``
        argument to :func:`generate_episode`.
    bucket:
        :attr:`TemplateBucket.CALIBRATION` for ``MF-C-*`` templates and
        :attr:`TemplateBucket.CONFIRMATION` for ``MF-X-*`` templates.
    history_len:
        Number of maintenance-history observations that precede the
        symptom. Includes the buried early observation, chronic alarms,
        and neutral log entries.
    delay:
        Number of history steps between the buried early observation
        and the moment the symptom appears in the active context.
    neutral_logs:
        Count of neutral routine boilerplate entries.
    chronic_alarms:
        Count of chronic critical-alert entries the wrong prior loves.
    context_noise:
        Count of recent noise entries that pattern-match the symptom
        but do not explain it.
    """

    template_id: str
    paraphrase_family: str
    bucket: TemplateBucket
    history_len: int
    delay: int
    neutral_logs: int
    chronic_alarms: int
    context_noise: int


#: Paraphrase families for the maintenance_fault surface. Each family
#: represents a different maintenance-log style (system log, sensor
#: telemetry stream, service warning ledger, diagnostic tape). The
#: paraphrase-family holdout is a Wave 0-required diversity axis
#: (PREREGISTRATION.md §6, "Holdout scheme").
PARAPHRASE_FAMILIES: Final[tuple[str, ...]] = (
    "system_logs",
    "sensor_stream",
    "warning_ledger",
    "diagnostic_tape",
)


def _build_templates() -> tuple[_TemplateSpec, ...]:
    """Return the frozen list of 48 maintenance_fault templates.

    16 calibration templates (``MF-C-01`` … ``MF-C-16``) and 32
    confirmatory templates (``MF-X-01`` … ``MF-X-32``) per
    PREREGISTRATION.md §6.2, distributed across the four paraphrase
    families with monotone but bounded structural variation. The
    structural knobs (``history_len``, ``delay``, ``neutral_logs``,
    ``chronic_alarms``, ``context_noise``) vary across templates so the
    Wave 0 variance estimate covers a realistic spread; every template
    still respects the non-ceiling utility differential in §6.
    """
    templates: list[_TemplateSpec] = []

    # 16 calibration templates.
    cal_shapes = [
        (14, 6, 4, 3, 2),
        (16, 8, 5, 3, 2),
        (18, 10, 6, 3, 3),
        (20, 12, 7, 4, 3),
        (15, 7, 4, 3, 3),
        (17, 9, 5, 4, 2),
        (19, 11, 6, 4, 3),
        (21, 13, 7, 5, 3),
        (14, 8, 3, 3, 3),
        (16, 10, 4, 4, 3),
        (18, 12, 5, 4, 4),
        (20, 14, 6, 5, 4),
        (15, 9, 3, 4, 3),
        (17, 11, 4, 5, 3),
        (19, 13, 5, 5, 4),
        (21, 15, 6, 6, 4),
    ]
    for i, (h, d, nl, ca, cn) in enumerate(cal_shapes, start=1):
        templates.append(
            _TemplateSpec(
                template_id=f"MF-C-{i:02d}",
                paraphrase_family=PARAPHRASE_FAMILIES[(i - 1) % len(PARAPHRASE_FAMILIES)],
                bucket=TemplateBucket.CALIBRATION,
                history_len=h,
                delay=d,
                neutral_logs=nl,
                chronic_alarms=ca,
                context_noise=cn,
            )
        )

    # 32 confirmatory templates. Held only for registry parity with
    # PREREGISTRATION.md §6.2; Wave 0 policy code never generates them.
    conf_shapes = [
        (14, 6, 4, 3, 2), (16, 8, 5, 3, 2), (18, 10, 6, 3, 3), (20, 12, 7, 4, 3),
        (15, 7, 4, 3, 3), (17, 9, 5, 4, 2), (19, 11, 6, 4, 3), (21, 13, 7, 5, 3),
        (14, 8, 3, 3, 3), (16, 10, 4, 4, 3), (18, 12, 5, 4, 4), (20, 14, 6, 5, 4),
        (15, 9, 3, 4, 3), (17, 11, 4, 5, 3), (19, 13, 5, 5, 4), (21, 15, 6, 6, 4),
        (14, 7, 3, 4, 2), (16, 9, 4, 4, 3), (18, 11, 5, 4, 3), (20, 13, 6, 5, 4),
        (15, 8, 4, 4, 2), (17, 10, 5, 5, 2), (19, 12, 6, 5, 3), (21, 14, 7, 6, 3),
        (14, 9, 3, 5, 2), (16, 11, 4, 5, 3), (18, 13, 5, 6, 3), (20, 15, 6, 6, 4),
        (15, 10, 3, 5, 3), (17, 12, 4, 6, 3), (19, 14, 5, 6, 4), (21, 16, 6, 7, 4),
    ]
    for i, (h, d, nl, ca, cn) in enumerate(conf_shapes, start=1):
        templates.append(
            _TemplateSpec(
                template_id=f"MF-X-{i:02d}",
                paraphrase_family=PARAPHRASE_FAMILIES[(i - 1) % len(PARAPHRASE_FAMILIES)],
                bucket=TemplateBucket.CONFIRMATION,
                history_len=h,
                delay=d,
                neutral_logs=nl,
                chronic_alarms=ca,
                context_noise=cn,
            )
        )

    return tuple(templates)


#: Frozen list of all maintenance_fault templates (calibration +
#: confirmatory). Wave 0 policy code only ever sees the calibration
#: subset; the confirmatory subset is registered here so the Wave 0
#: registry is authoritative and so seed-range validation can refuse a
#: confirmatory seed in a calibration call and vice versa.
TEMPLATES: Final[tuple[_TemplateSpec, ...]] = _build_templates()


def _templates_by_bucket(bucket: TemplateBucket) -> tuple[_TemplateSpec, ...]:
    return tuple(t for t in TEMPLATES if t.bucket is bucket)


# ---------------------------------------------------------------------------
# Seed / holdout validation
# ---------------------------------------------------------------------------


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
    elif bucket is TemplateBucket.CONFIRMATION:
        if not (CONFIRMATION_SEED_MIN <= seed <= CONFIRMATION_SEED_MAX):
            raise ValueError(
                f"confirmatory seed must be in "
                f"[{CONFIRMATION_SEED_MIN}, {CONFIRMATION_SEED_MAX}]; "
                f"got {seed}"
            )
    else:
        raise TypeError("bucket must be a TemplateBucket instance")


def _validate_holdout(holdout: str | None) -> None:
    if holdout is None:
        return
    if not isinstance(holdout, str):
        raise TypeError("holdout must be str or None")
    if holdout not in PARAPHRASE_FAMILIES:
        raise ValueError(
            f"holdout must be one of {list(PARAPHRASE_FAMILIES)} or None; "
            f"got {holdout!r}"
        )


def _select_template(
    seed: int,
    bucket: TemplateBucket,
    holdout: str | None,
) -> _TemplateSpec:
    """Pick one template deterministically for ``(seed, bucket, holdout)``.

    The selection uses SHA-256 over ``(bucket, seed, holdout)`` and is
    therefore process-stable. The candidate pool is the templates in
    ``bucket`` whose ``paraphrase_family`` is not ``holdout``; if
    ``holdout`` is ``None`` the pool is every template in ``bucket``.
    """
    pool = _templates_by_bucket(bucket)
    if holdout is not None:
        pool = tuple(t for t in pool if t.paraphrase_family != holdout)
    if not pool:
        raise ValueError(
            "no maintenance_fault templates remain after applying holdout "
            f"{holdout!r} to bucket {bucket.value!r}"
        )
    key = f"{FAMILY_NAME}::{bucket.value}::{seed}::{holdout or ''}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    index = int(digest[:16], 16) % len(pool)
    return pool[index]


# ---------------------------------------------------------------------------
# Node id and utility construction
# ---------------------------------------------------------------------------


def _prefix(template_id: str, seed: int) -> str:
    """Return the canonical maintenance_fault node-id prefix.

    All nodes emitted by :func:`generate_episode` start with this
    prefix so that the sealed environment's candidate-set check and the
    guard's "no cross-episode candidate ids" audit both have a single
    string to test against.
    """
    return f"mf::{template_id}::s{seed:06d}"


def _reward_load_bearing(rng: random.Random) -> float:
    return 0.50 + rng.uniform(-0.05, 0.05)


def _reward_context_noise(rng: random.Random) -> float:
    return -0.05 + rng.uniform(-0.05, 0.05)


def _reward_chronic_alarm(rng: random.Random) -> float:
    return -0.10 + rng.uniform(-0.05, 0.05)


def _reward_neutral(rng: random.Random) -> float:
    return 0.0 + rng.uniform(-0.02, 0.02)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_episode(
    seed: int,
    bucket: TemplateBucket,
    holdout: str | None = None,
) -> EpisodeSpec:
    """Return one sealed :class:`EpisodeSpec` for the maintenance_fault family.

    Parameters
    ----------
    seed:
        Row-level seed. In the calibration range ``100000..100999`` for
        :attr:`TemplateBucket.CALIBRATION` and ``200000..201999`` for
        :attr:`TemplateBucket.CONFIRMATION` (PREREGISTRATION.md §10). A
        seed outside its declared range raises :class:`ValueError`.
    bucket:
        The template family the caller is generating for. Confirmatory
        rows are only ever produced when the caller-side family-split
        guard has already unlocked confirmatory access (see
        :mod:`experiments.concern_gated_retrieval_e2.wave0.template_split`).
    holdout:
        Optional paraphrase-family id to hold out. When set, templates
        whose ``paraphrase_family`` equals ``holdout`` are removed from
        the selection pool. ``None`` (default) uses every template.

    Returns
    -------
    EpisodeSpec
        A frozen episode carrying policy-visible context, care anchors,
        candidate set, and budget, plus the sealed role labels,
        per-node utility, and answer key inside the evaluator-only
        fields. The sealed environment strips the sealed fields before
        any policy view is returned.

    Wave 0 style: the episode encodes calibration data plus a wrong
    prior. It is not a claim about learned memory, concern recovery,
    meaning, or selfhood.
    """
    _validate_seed(seed, bucket)
    _validate_holdout(holdout)

    template = _select_template(seed, bucket, holdout)
    rng = random.Random(
        f"cogr-e2-wave0::{FAMILY_NAME}::{template.template_id}::{seed}"
    )
    prefix = _prefix(template.template_id, seed)

    # ------------------------------------------------------------------
    # Node ids
    # ------------------------------------------------------------------
    # Load-bearing target: the buried early observation whose signature
    # explains the symptom now in the active context.
    load_bearing = f"{prefix}::early_obs"

    # Active-context nodes: the current symptom plus a small amount of
    # local operational chatter (unhelpful but present).
    ctx_symptom = f"{prefix}::current_symptom"
    ctx_op_chat_a = f"{prefix}::op_chat_a"
    ctx_op_chat_b = f"{prefix}::op_chat_b"

    # Distractors: pattern-matching sensor noise, chronic loud alarms,
    # neutral maintenance boilerplate.
    context_noise_nodes = tuple(
        f"{prefix}::ctx_noise_{i:02d}" for i in range(template.context_noise)
    )
    chronic_alarm_nodes = tuple(
        f"{prefix}::chronic_alarm_{i:02d}" for i in range(template.chronic_alarms)
    )
    neutral_log_nodes = tuple(
        f"{prefix}::neutral_log_{i:02d}" for i in range(template.neutral_logs)
    )

    # ------------------------------------------------------------------
    # Policy-visible fields
    # ------------------------------------------------------------------
    context_nodes: tuple[str, ...] = (ctx_symptom, ctx_op_chat_a, ctx_op_chat_b)

    # Candidate set: the load-bearing early observation, every
    # distractor category, and enough of the neutral maintenance log
    # entries to keep the budget selection non-trivial. The symptom
    # itself is context, not a candidate.
    candidate_nodes: tuple[str, ...] = (
        load_bearing,
        *context_noise_nodes,
        *chronic_alarm_nodes,
        *neutral_log_nodes,
    )

    # Care anchors implement PREREGISTRATION.md §5's wrong prior:
    # overweight the chronic alarm region, suppress the load-bearing
    # early observation region, and leave neutral/noise entries at a
    # small positive uniform baseline.
    care_anchors: dict[str, float] = {load_bearing: W_COMMIT_INIT}
    for node in chronic_alarm_nodes:
        care_anchors[node] = W_ALARM_INIT
    for node in context_noise_nodes:
        care_anchors[node] = W_UNIFORM_INIT
    for node in neutral_log_nodes:
        care_anchors[node] = W_UNIFORM_INIT

    # Budget: enough to load the load-bearing target and one supporting
    # neutral entry; too small to sweep every distractor. This keeps the
    # policy's decision the interesting one PREREGISTRATION.md §2
    # names as the target object.
    budget = 2

    # ------------------------------------------------------------------
    # Sealed fields (evaluator-only)
    # ------------------------------------------------------------------
    role: dict[str, str] = {load_bearing: "load_bearing"}
    for node in context_noise_nodes:
        role[node] = "context_noise_distractor"
    for node in chronic_alarm_nodes:
        role[node] = "chronic_alarm_distractor"
    for node in neutral_log_nodes:
        role[node] = "neutral_maintenance_log"

    utility: dict[str, float] = {load_bearing: _reward_load_bearing(rng)}
    for node in context_noise_nodes:
        utility[node] = _reward_context_noise(rng)
    for node in chronic_alarm_nodes:
        utility[node] = _reward_chronic_alarm(rng)
    for node in neutral_log_nodes:
        utility[node] = _reward_neutral(rng)

    # Non-ceiling clamp: bound the load-bearing target's expected
    # differential over the best distractor at ``MAX_UTILITY_DIFF``
    # (PREREGISTRATION.md §6). ``max(...)`` is taken over the distractor
    # utilities we just generated; the load-bearing utility is then
    # clipped to keep its differential inside the cap.
    distractor_util_ceiling = max(
        (utility[node] for node in candidate_nodes if node != load_bearing),
        default=0.0,
    )
    max_allowed = distractor_util_ceiling + MAX_UTILITY_DIFF
    if utility[load_bearing] > max_allowed:
        utility[load_bearing] = max_allowed

    answer_key: tuple[str, ...] = (load_bearing,)

    # ------------------------------------------------------------------
    # Assemble the sealed episode
    # ------------------------------------------------------------------
    template_family_split = (
        "calibration" if bucket is TemplateBucket.CALIBRATION else "confirmatory"
    )
    stable_id = stable_template_id(FAMILY_NAME, seed, bucket)
    episode_id = f"{template.template_id}::{stable_id}"

    return EpisodeSpec(
        episode_id=episode_id,
        template_family_split=template_family_split,  # type: ignore[arg-type]
        family=FAMILY_NAME,  # type: ignore[arg-type]
        seed=seed,
        context_nodes=context_nodes,
        care_anchors=care_anchors,
        candidate_nodes=candidate_nodes,
        budget=budget,
        role=role,
        utility=utility,
        _answer_key=answer_key,
    )


__all__ = [
    "CALIBRATION_SEED_MAX",
    "CALIBRATION_SEED_MIN",
    "CONFIRMATION_SEED_MAX",
    "CONFIRMATION_SEED_MIN",
    "FAMILY_NAME",
    "MAX_UTILITY_DIFF",
    "PARAPHRASE_FAMILIES",
    "TEMPLATES",
    "W_ALARM_INIT",
    "W_COMMIT_INIT",
    "W_UNIFORM_INIT",
    "generate_episode",
]
