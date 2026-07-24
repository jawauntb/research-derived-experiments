"""MX1 Part B — the verifier-fault split.

Ported from MIDAS's ``VerificationStatus``, which separates
``FAILED_REASONING`` (the thing being checked is wrong) from
``FAILED_CODEGEN`` / ``FAILED_CONTRACT`` (the *check itself* is broken, so its
verdict carries no evidence about the thing being checked). MIDAS treats only
the first as grounds for repair; the second means "do not trust this run".

Our analogue is a **marginal** verifier: one that scores a candidate set as the
sum of its members' singleton values. That model is exactly wrong where the
family plants interaction structure. A complementary pair is super-additive —
each member scores about zero alone while the pair is valuable — so a marginal
verifier reports about zero and the pair is discarded as useless. That is the
operational form of Spencer's objection: a memory that looks useless in
isolation can be load-bearing in company.

The split verifier declines to answer on sets where the marginal model is out
of its competence, returning :data:`FaultKind.VERIFIER_FAULT` with no value
instead of a confidently wrong number.

Ground truth for "was this set genuinely useful" is
:func:`wave1b.sealed_env_ext.compute_set_delta` (the SET-level oracle). The
verifiers under test never call it; only the scorer does.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, Final, Iterable, Sequence

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import EpisodeSpec
from experiments.concern_gated_retrieval_e2.wave1b.sealed_env_ext import (
    compute_set_delta,
)


__all__ = [
    "FaultKind",
    "VerifierOutcome",
    "marginal_verifier",
    "split_verifier",
    "planted_interaction_members",
]


class FaultKind(enum.Enum):
    """Which of the two MIDAS fault classes an attempt fell into."""

    #: The check ran and the thing checked was (or was not) good. Evidence.
    REASONING_FAULT = "reasoning_fault"
    #: The check was out of its competence. Carries NO evidence about the set.
    VERIFIER_FAULT = "verifier_fault"


@dataclass(frozen=True)
class VerifierOutcome:
    """One verifier's verdict on one candidate set.

    ``value`` is ``None`` exactly when ``fault_kind`` is
    :attr:`FaultKind.VERIFIER_FAULT` — a declined answer, not a zero.
    """

    selected_set: tuple[str, ...]
    fault_kind: FaultKind
    value: float | None


#: Bundle fields on a family ``BundleManifest`` whose members interact
#: non-additively. A marginal verifier is out of competence on any set that
#: contains two or more members of one of these.
_INTERACTING_BUNDLE_FIELDS: Final[tuple[str, ...]] = (
    "complementary_pair",
    "dangerous_conjunction",
)


def planted_interaction_members(manifest: Any) -> tuple[frozenset[str], ...]:
    """Return each planted *interacting* bundle as a frozenset of members.

    EVALUATOR-side: reads the family's ``BundleManifest``. Policy code must
    never call this; it exists so the Part B scorer can ask whether a set
    straddles an interaction the marginal model cannot represent.
    """
    groups: list[frozenset[str]] = []
    for field in _INTERACTING_BUNDLE_FIELDS:
        members = getattr(manifest, field, None)
        if members:
            groups.append(frozenset(members))
    return tuple(groups)


def marginal_verifier(episode: EpisodeSpec, selected: Iterable[str]) -> VerifierOutcome:
    """Score ``selected`` as the additive sum of its members' singleton values.

    This is the naive verifier: it always answers, and it is confidently wrong
    on every planted interaction.
    """
    members = tuple(sorted(set(selected)))
    total = sum(compute_set_delta(episode, [m]).delta_task for m in members)
    return VerifierOutcome(
        selected_set=members,
        fault_kind=FaultKind.REASONING_FAULT,
        value=float(total),
    )


def split_verifier(
    episode: EpisodeSpec,
    selected: Iterable[str],
    interaction_groups: Sequence[frozenset[str]],
) -> VerifierOutcome:
    """Marginal verifier plus a competence check.

    Returns :attr:`FaultKind.VERIFIER_FAULT` with ``value=None`` when
    ``selected`` contains two or more members of any planted interacting
    bundle — the marginal model cannot represent that set, so it declines
    rather than reporting a wrong number. Otherwise it behaves exactly like
    :func:`marginal_verifier`.
    """
    members = tuple(sorted(set(selected)))
    member_set = set(members)
    for group in interaction_groups:
        if len(member_set & group) >= 2:
            return VerifierOutcome(
                selected_set=members,
                fault_kind=FaultKind.VERIFIER_FAULT,
                value=None,
            )
    return marginal_verifier(episode, members)
