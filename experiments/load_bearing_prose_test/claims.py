"""Typed claims, ablations, and verdicts for the load-bearing prose test.

Scoped intentionally narrow: dataclasses + canonical digests, no I/O,
no live-provider paths. The executor adapter and scoring rules land in
Week 2 under ``executor.py`` and ``scoring.py``.

Digest discipline mirrors ``experiments.grounded_statecharts.runtime``
so downstream harness receipts can compose without a second canonical
serializer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


def canonical_json(value: object) -> str:
    """Serialize records in the stable representation used for hashes."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: object) -> str:
    """SHA-256 hex digest of the canonical JSON encoding of ``value``."""

    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


class AblationKind(str, Enum):
    """Ablation transforms declared by the preregistration.

    - ``delete`` removes the claim from the prose plan.
    - ``negate`` replaces the claim with its logical negation.
    - ``paraphrase`` replaces the claim with a semantics-preserving
      rewrite used for the gauge check.
    """

    DELETE = "delete"
    NEGATE = "negate"
    PARAPHRASE = "paraphrase"


_CLAIM_ID_MIN_LEN = 3
_CLAIM_ID_MAX_LEN = 128


def _require_nonempty_str(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _require_claim_id(value: object, label: str) -> str:
    text = _require_nonempty_str(value, label)
    if not (_CLAIM_ID_MIN_LEN <= len(text) <= _CLAIM_ID_MAX_LEN):
        raise ValueError(
            f"{label} length must be within [{_CLAIM_ID_MIN_LEN}, {_CLAIM_ID_MAX_LEN}]"
        )
    if any(ch.isspace() for ch in text):
        raise ValueError(f"{label} must not contain whitespace")
    return text


@dataclass(frozen=True)
class Claim:
    """A single atomic predicate-shaped claim extracted from a plan.

    ``text`` is the surface form used for ablation transforms.
    ``kappa_terms`` records which κ elements (capability names,
    artifact paths, evidence/approval keywords) the claim mentions,
    for the κ concordance metric declared in the preregistration.
    """

    claim_id: str
    text: str
    start_offset: int
    end_offset: int
    kappa_terms: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_claim_id(self.claim_id, "Claim.claim_id")
        _require_nonempty_str(self.text, "Claim.text")
        if self.start_offset < 0:
            raise ValueError("Claim.start_offset must be non-negative")
        if self.end_offset <= self.start_offset:
            raise ValueError("Claim.end_offset must be greater than start_offset")
        for term in self.kappa_terms:
            _require_nonempty_str(term, "Claim.kappa_terms element")

    @property
    def mentions_kappa(self) -> bool:
        return bool(self.kappa_terms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "kappa_terms": list(self.kappa_terms),
        }


@dataclass(frozen=True)
class ClaimBundle:
    """The claims extracted from a single plan, with its source hash.

    ``plan_digest`` binds the bundle to the exact source plan so
    downstream ablation receipts cannot be silently reattached to a
    different plan.
    """

    plan_id: str
    plan_digest: str
    claims: tuple[Claim, ...]

    def __post_init__(self) -> None:
        _require_claim_id(self.plan_id, "ClaimBundle.plan_id")
        if len(self.plan_digest) != 64 or any(
            ch not in "0123456789abcdef" for ch in self.plan_digest
        ):
            raise ValueError("ClaimBundle.plan_digest must be a lowercase SHA-256")
        seen: set[str] = set()
        for claim in self.claims:
            if claim.claim_id in seen:
                raise ValueError(f"duplicate claim_id in bundle: {claim.claim_id}")
            seen.add(claim.claim_id)

    @property
    def bundle_digest(self) -> str:
        return digest(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "plan_digest": self.plan_digest,
            "claims": [claim.to_dict() for claim in self.claims],
        }


@dataclass(frozen=True)
class Ablation:
    """A single ablation applied to one claim in a plan.

    ``modified_plan`` is the full plan text after the transform is
    applied. Storing it explicitly (rather than as a diff) lets the
    Week-2 executor adapter run without re-executing the transform.
    """

    plan_id: str
    claim_id: str
    kind: AblationKind
    modified_plan: str

    def __post_init__(self) -> None:
        _require_claim_id(self.plan_id, "Ablation.plan_id")
        _require_claim_id(self.claim_id, "Ablation.claim_id")
        if not isinstance(self.kind, AblationKind):
            raise ValueError("Ablation.kind must be an AblationKind")
        _require_nonempty_str(self.modified_plan, "Ablation.modified_plan")

    @property
    def modified_digest(self) -> str:
        return hashlib.sha256(self.modified_plan.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "claim_id": self.claim_id,
            "kind": self.kind.value,
            "modified_plan_digest": self.modified_digest,
        }


@dataclass(frozen=True)
class AblationSet:
    """The full set of ablations produced for one claim bundle.

    Exactly one Ablation per (claim_id, kind) pair. The set carries the
    source bundle digest so a receipt cannot be silently reattached to
    a different bundle downstream.
    """

    bundle_digest: str
    ablations: tuple[Ablation, ...]

    def __post_init__(self) -> None:
        if len(self.bundle_digest) != 64 or any(
            ch not in "0123456789abcdef" for ch in self.bundle_digest
        ):
            raise ValueError("AblationSet.bundle_digest must be a lowercase SHA-256")
        seen: set[tuple[str, AblationKind]] = set()
        for ablation in self.ablations:
            key = (ablation.claim_id, ablation.kind)
            if key in seen:
                raise ValueError(
                    f"duplicate ablation for claim {ablation.claim_id} "
                    f"kind {ablation.kind.value}"
                )
            seen.add(key)

    def for_claim(self, claim_id: str) -> dict[AblationKind, Ablation]:
        return {
            ablation.kind: ablation
            for ablation in self.ablations
            if ablation.claim_id == claim_id
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_digest": self.bundle_digest,
            "ablations": [ablation.to_dict() for ablation in self.ablations],
        }


@dataclass(frozen=True)
class Verdict:
    """The load-bearing verdict for a single claim.

    Populated by Week-2 ``scoring.py`` once executor evidence for the
    baseline and each ablation is available. The scaffold defines the
    type so upstream tests can already round-trip receipts.
    """

    claim_id: str
    is_load_bearing: bool
    paraphrase_invariant: bool
    delete_delta: bool
    negate_delta: bool
    paraphrase_delta: bool
    kappa_mention: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "is_load_bearing": self.is_load_bearing,
            "paraphrase_invariant": self.paraphrase_invariant,
            "delete_delta": self.delete_delta,
            "negate_delta": self.negate_delta,
            "paraphrase_delta": self.paraphrase_delta,
            "kappa_mention": self.kappa_mention,
        }
