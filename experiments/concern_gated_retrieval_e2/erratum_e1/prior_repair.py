"""Erratum E1 — the non-leaky wrong prior.

The frozen families implement Wave 0 PREREGISTRATION section 5 as::

    prior[load_bearing] = W_COMMIT_INIT      # 0.05, applied to exactly one node

Suppressing *exactly one* node, which is the answer, makes the suppressed
value a unique identifier for the target: sorting candidates by ascending
concern is a perfect oracle.

The preregistration's own words are ``suppress at least one true commitment
region``. The repair honours that text while removing the identifiability: it
suppresses a **set** of ``k`` candidates, of which the load-bearing node is
one and the rest are non-answer, non-alarm distractors. Ascending concern then
yields a ``1``-in-``k`` shortlist rather than the answer, so the expected
leaked hit@1 falls to ``1/k``.

The frozen ``wave0`` and ``wave1b`` packages are **not edited**. This module
returns a repaired copy of an episode, so the historical record and its
analysis hashes stay intact and the defect stays visible.
"""

from __future__ import annotations

import dataclasses
import random
from types import MappingProxyType
from typing import Final, Mapping

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import EpisodeSpec

__all__ = [
    "DEFAULT_SUPPRESSED_SET_SIZE",
    "repair_wrong_prior",
    "suppressed_set",
]


#: Cardinality of the suppressed set, including the load-bearing node. With
#: ``k = 4`` the inverted-signal shortcut degrades from 1.000 to about 0.25.
DEFAULT_SUPPRESSED_SET_SIZE: Final[int] = 4


def suppressed_set(
    episode: EpisodeSpec,
    *,
    k: int = DEFAULT_SUPPRESSED_SET_SIZE,
    seed: int | None = None,
) -> tuple[str, ...]:
    """Return the ``k`` candidates to suppress, load-bearing node included.

    EVALUATOR-side: reads ``_answer_key`` so it can guarantee the suppressed
    set contains non-answers. Deterministic given ``(episode.seed, k)``.
    """
    candidates: tuple[str, ...] = tuple(episode.candidate_nodes)
    answer = set(episode._answer_key)
    prior: Mapping[str, float] = episode.care_anchors

    load_bearing = [c for c in candidates if c in answer]
    # Never suppress the inflated alarm nodes: they carry the *other* half of
    # the adversarial specification and must stay at their inflated weight.
    alarm_weight = max(prior.values()) if prior else 0.0
    fillers = [
        c
        for c in candidates
        if c not in answer and prior.get(c, 0.0) < alarm_weight
    ]

    base_seed = int(seed if seed is not None else episode.seed)
    rng = random.Random(base_seed * 1000 + k)
    rng.shuffle(fillers)
    chosen = load_bearing + fillers[: max(0, k - len(load_bearing))]
    return tuple(sorted(chosen))


def repair_wrong_prior(
    episode: EpisodeSpec,
    *,
    k: int = DEFAULT_SUPPRESSED_SET_SIZE,
    seed: int | None = None,
) -> EpisodeSpec:
    """Return a copy of ``episode`` whose concern prior no longer identifies the answer.

    Every other field -- roles, utilities, answer key, geometry inputs -- is
    preserved exactly, so the repair changes the *prior* and nothing else.
    """
    prior = dict(episode.care_anchors)
    if not prior:
        return episode

    suppressed = suppressed_set(episode, k=k, seed=seed)
    if len(suppressed) < 2:
        # Degenerate episode: cannot build a non-identifying suppressed set.
        return episode

    floor = min(prior.values())
    for node in suppressed:
        prior[node] = floor

    return dataclasses.replace(episode, care_anchors=MappingProxyType(prior))
