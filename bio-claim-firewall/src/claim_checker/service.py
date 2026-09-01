"""Build and verify narrow K562 perturbation-effect claims without an LLM.

This module is deliberately a retrieval-free local surface.  It resolves exact
HGNC identifiers or labels, selects one exact record from the frozen Replogle
2022 K562 CRISPRi ledger, and lets the existing deterministic verifier decide
whether the requested direction is supported.  Missing or ambiguous evidence
returns ``INCONCLUSIVE`` instead of manufacturing a claim.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from normalize.errors import NormalizationError
from rules.sections._shared import RELATION_CANONICAL_SIGN
from verifier import verify
from verifier.config import VerifierConfig


_K562_CELL_TYPE = "CL:0000988"
_K562_CELL_LINE = "CLO:0007059"
_K562_STATE = "resting"
_REPLOGLE_SOURCE = "perturbseq.replogle_2022"
_CLAIM_ID_NAMESPACE = uuid.UUID("e2105604-6e35-4b5a-a04d-7bc77f19a973")


class ClaimCheckInputError(ValueError):
    """The local checker cannot safely resolve the supplied input."""


@dataclass(frozen=True, slots=True)
class ClaimCheckResult:
    """A UI- and CLI-safe view of a deterministic checker outcome."""

    claim: dict[str, Any] | None
    evidence: dict[str, Any] | None
    verdict: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return only JSON-compatible values suitable for a local CLI."""
        return {
            "claim": self.claim,
            "evidence": self.evidence,
            "verdict": self.verdict,
        }


def check_k562_claim(
    bundle: Any,
    subject: str,
    object_: str,
    direction: str,
    *,
    checker_version: str = "0.1.0",
) -> ClaimCheckResult:
    """Check one exact K562 CRISPRi perturbation-effect statement.

    ``subject`` and ``object_`` may be HGNC CURIEs or exact frozen HGNC
    labels.  ``direction`` is deliberately limited to ``increases`` and
    ``decreases``.  The function never uses a label as biological evidence;
    labels only resolve user input to frozen CURIEs before a real ledger record
    is selected.
    """
    relation, polarity = _direction_contract(direction)
    label_index = (
        _hgnc_label_index(bundle)
        if _requires_label_resolution(subject) or _requires_label_resolution(object_)
        else None
    )
    subject_id = _resolve_hgnc(bundle, subject, label_index)
    object_id = _resolve_hgnc(bundle, object_, label_index)
    records = _scoped_records(bundle, subject_id, object_id)
    directional_records = [
        record
        for record in records
        if record.get("effect", {}).get("sign") in {"positive", "negative"}
    ]

    if not directional_records:
        if any(record.get("effect", {}).get("sign") == "null" for record in records):
            return _inconclusive(
                bundle,
                "The exact frozen Replogle 2022 K562 CRISPRi record for this gene "
                "pair records no directional effect.",
                checker_version=checker_version,
            )
        return _inconclusive(
            bundle,
            "No exact frozen Replogle 2022 K562 CRISPRi record matches this gene pair.",
            checker_version=checker_version,
        )
    if len(directional_records) != 1:
        return _inconclusive(
            bundle,
            "Multiple exact frozen Replogle 2022 K562 CRISPRi records match this gene pair.",
            checker_version=checker_version,
        )

    record = directional_records[0]
    claim = _claim_from_record(record, relation=relation, polarity=polarity)
    verdict = verify(claim, bundle, VerifierConfig(checker_version=checker_version))
    return ClaimCheckResult(
        claim=claim,
        evidence=_evidence_summary(record),
        verdict=verdict,
    )


def _direction_contract(direction: str) -> tuple[str, str]:
    normalized = direction.strip().casefold() if isinstance(direction, str) else ""
    try:
        return normalized, RELATION_CANONICAL_SIGN[normalized]
    except KeyError as exc:
        raise ClaimCheckInputError(
            "direction must be exactly increases or decreases"
        ) from exc


def _requires_label_resolution(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not value.casefold().startswith("hgnc:")
    )


def _resolve_hgnc(
    bundle: Any, value: str, label_index: dict[str, tuple[str, ...]] | None
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ClaimCheckInputError(
            "gene input must be a non-empty HGNC CURIE or symbol"
        )

    normalized = value.strip()
    if normalized.casefold().startswith("hgnc:"):
        curie = f"HGNC:{normalized.split(':', 1)[1]}"
        try:
            canonical = bundle.canonicalize(curie)
        except NormalizationError as exc:
            raise ClaimCheckInputError(
                f"gene {value!r} does not resolve in the frozen HGNC snapshot"
            ) from exc
        if not canonical.startswith("HGNC:"):
            raise ClaimCheckInputError(
                f"gene {value!r} does not resolve to an HGNC identifier"
            )
        return canonical

    matches = (label_index or _hgnc_label_index(bundle)).get(normalized.casefold(), ())
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ClaimCheckInputError(
            f"gene symbol {value!r} is ambiguous in the frozen HGNC snapshot; use an HGNC CURIE"
        )
    raise ClaimCheckInputError(
        f"gene symbol {value!r} does not resolve in the frozen HGNC snapshot"
    )


def _hgnc_label_index(bundle: Any) -> dict[str, tuple[str, ...]]:
    """Build one case-folded label lookup while preserving ambiguities."""
    mutable_index: dict[str, list[str]] = {}
    for curie, label in getattr(bundle, "labels", {}).items():
        if curie.startswith("HGNC:") and isinstance(label, str):
            mutable_index.setdefault(label.casefold(), []).append(curie)
    return {label: tuple(sorted(curies)) for label, curies in mutable_index.items()}


def _scoped_records(
    bundle: Any, subject_id: str, object_id: str
) -> list[dict[str, Any]]:
    records = bundle.ledger.list_by(
        subject_id,
        object_id,
        cell_type=_K562_CELL_TYPE,
        cell_line=_K562_CELL_LINE,
        state=_K562_STATE,
        assay="CRISPRi_screen",
    )
    matches: list[dict[str, Any]] = []
    for record in records:
        if (
            record.get("source") == _REPLOGLE_SOURCE
            and record.get("record_type") == "perturbation_effect"
            and record.get("species") == "NCBITaxon:9606"
            and record.get("assay_context", {}).get("perturbation")
            == f"CRISPRi:{subject_id}"
        ):
            matches.append(record)
    return matches


def _claim_from_record(
    record: Mapping[str, Any], *, relation: str, polarity: str
) -> dict[str, Any]:
    evidence_id = record["evidence_id"]
    subject = record["subject"]
    object_ = record["object"]
    canonical_key = "|".join(
        (str(evidence_id), str(subject["id"]), relation, str(object_["id"]), polarity)
    )
    return {
        "schema_version": "0.1.0",
        "claim_id": str(uuid.uuid5(_CLAIM_ID_NAMESPACE, canonical_key)),
        "subject": {"id": subject["id"], "label": subject.get("label", subject["id"])},
        "relation": relation,
        "object": {"id": object_["id"], "label": object_.get("label", object_["id"])},
        "polarity": polarity,
        "species": record["species"],
        "cell_context": dict(record["cell_context"]),
        "assay_context": dict(record["assay_context"]),
        "evidence_ids": [evidence_id],
        "confidence_language": "supported",
        "requested_status": "hypothesis",
    }


def _evidence_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    effect = record["effect"]
    return {
        "evidence_id": record["evidence_id"],
        "source": record["source"],
        "citation": record.get("source_citation"),
        "effect_sign": effect.get("sign"),
        "magnitude": effect.get("magnitude"),
        "magnitude_scale": effect.get("magnitude_scale"),
        "significance": effect.get("significance"),
        "scope": {
            "species": record["species"],
            "cell_type": record["cell_context"]["cell_type"],
            "cell_line": record["cell_context"]["cell_line"],
            "state": record["cell_context"]["state"],
            "assay": record["assay_context"]["assay"],
            "perturbation": record["assay_context"]["perturbation"],
        },
    }


def _inconclusive(
    bundle: Any, reason: str, *, checker_version: str
) -> ClaimCheckResult:
    """Return a traceable no-claim result without invoking the verifier."""
    return ClaimCheckResult(
        claim=None,
        evidence=None,
        verdict={
            "verdict": "INCONCLUSIVE",
            "reason": reason,
            "checker_version": checker_version,
            "snapshot_hashes": dict(bundle.ledger.snapshot_hashes()),
        },
    )
