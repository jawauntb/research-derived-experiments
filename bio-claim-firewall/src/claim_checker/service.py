"""Build and verify narrow K562 perturbation-effect claims without an LLM.

This module is deliberately a retrieval-free local surface.  It resolves exact
HGNC identifiers or labels, selects one exact record from the frozen Replogle
2022 K562 CRISPRi ledger, and lets the existing deterministic verifier decide
whether the requested direction is supported.  Missing or ambiguous evidence
returns ``INCONCLUSIVE`` instead of manufacturing a claim.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

from audit import canonicalize_for_hash
from normalize.errors import NormalizationError
from rules.sections._shared import RELATION_CANONICAL_SIGN
from verifier import verify
from verifier.config import VerifierConfig
from worlds import K562_WORLD, WORLD_REGISTRY, World, WorldRegistry, WorldRegistryError

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
    receipt: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return only JSON-compatible values suitable for a local CLI."""
        result = {
            "claim": self.claim,
            "evidence": self.evidence,
            "verdict": self.verdict,
        }
        if self.receipt is not None:
            result["receipt"] = self.receipt
        return result


def _checker_error(message: str, *, stage: str = "load_snapshot", claim: Any = None, checker_version: str = "0.1.0") -> ClaimCheckResult:
    return ClaimCheckResult(
        claim=claim if isinstance(claim, dict) else None,
        evidence=None,
        verdict={
            "verdict": "CHECKER_ERROR",
            "checker_error": {"stage": stage, "message": message, "exception_class": "WorldBindingError"},
            "checker_version": checker_version,
        },
    )


def _world_source_hashes(bundle: Any, world: World) -> dict[str, str]:
    manifests = getattr(bundle, "manifests", None)
    if not isinstance(manifests, Mapping):
        raise WorldRegistryError("bundle has no immutable manifest mapping")
    expected = {contract.source: contract for contract in world.source_contracts}
    actual = set(manifests)
    allowed = set(world.source_allowlist)
    if actual != allowed:
        raise WorldRegistryError(
            f"bundle sources do not exactly match {world.world_key}: "
            f"extra={sorted(actual - allowed)!r}, missing={sorted(allowed - actual)!r}"
        )
    hashes: dict[str, str] = {}
    for source in sorted(actual):
        manifest = manifests[source]
        digest = getattr(manifest, "sha256", None)
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise WorldRegistryError(f"source {source!r} has a partial or invalid digest")
        contract = expected.get(source)
        if contract is not None and contract.sha256 is not None and digest != contract.sha256:
            raise WorldRegistryError(f"source {source!r} digest does not match registered world")
        hashes[source] = digest
    if expected and set(expected) != actual:
        raise WorldRegistryError(f"world {world.world_key} has incomplete source contracts")
    return hashes


def _world_digest(world: World, source_hashes: Mapping[str, str]) -> str:
    # The registry digest is immutable; this second digest binds the concrete
    # loaded manifests as well and is what appears in a receipt.
    payload = {"registered_world_digest": world.digest, "sources": dict(sorted(source_hashes.items()))}
    return hashlib.sha256(canonicalize_for_hash(payload)).hexdigest()


def _issued_at() -> str:
    now = datetime.now(UTC)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _attach_receipt(
    result: ClaimCheckResult,
    world: World,
    bundle: Any,
    *,
    checker_version: str,
    parser_provenance: Mapping[str, Any] | None = None,
    strict_bundle: bool = False,
) -> ClaimCheckResult:
    try:
        source_hashes = _world_source_hashes(bundle, world) if strict_bundle else dict(
            sorted(getattr(getattr(bundle, "ledger", None), "snapshot_hashes", dict)().items())
        )
        world_digest = _world_digest(world, source_hashes)
    except Exception as exc:  # noqa: BLE001 - receipt construction must fail closed
        if strict_bundle:
            return _checker_error(str(exc), claim=result.claim)
        source_hashes = dict(sorted(getattr(getattr(bundle, "ledger", None), "snapshot_hashes", dict)().items()))
        world_digest = world.digest

    # Only deterministic content enters this payload.  ``issued_at``, parser
    # provenance, and the verifier's run-local id remain outside it.
    outcome = {key: value for key, value in result.verdict.items() if key not in {"issued_at", "verdict_id", "receipt_id", "receipt_version", "world_id", "world_version", "world_digest", "source_hashes", "canonical_payload"}}
    payload = {
        "receipt_version": "2",
        "world_id": world.world_id,
        "world_version": world.version,
        "world_digest": world_digest,
        "source_hashes": source_hashes,
        "claim": result.claim,
        "evidence": result.evidence,
        "outcome": outcome,
        "checker_version": checker_version,
        "schema_version": "0.1.0",
    }
    receipt_id = hashlib.sha256(canonicalize_for_hash(payload)).hexdigest()
    receipt = {
        "receipt_version": "2",
        "receipt_id": receipt_id,
        "issued_at": _issued_at(),
        "canonical_payload": payload,
    }
    if parser_provenance is not None:
        receipt["parser_provenance"] = dict(parser_provenance)
    verdict = dict(result.verdict)
    verdict.update(
        {
            "receipt_version": "2",
            "receipt_id": receipt_id,
            "world_id": world.world_id,
            "world_version": world.version,
            "world_digest": world_digest,
            "source_hashes": source_hashes,
            "canonical_payload": payload,
        }
    )
    return ClaimCheckResult(claim=result.claim, evidence=result.evidence, verdict=verdict, receipt=receipt)


def _run_k562_adapter(bundle: Any, claim: Mapping[str, Any], *, checker_version: str) -> ClaimCheckResult:
    if set(claim) != set(K562_WORLD.claim_fields):
        raise ClaimCheckInputError(
            "world claim must contain exactly subject, object, and direction"
        )
    return check_k562_claim(
        bundle,
        claim["subject"],
        claim["object"],
        claim["direction"],
        checker_version=checker_version,
        _internal=True,
    )


def _adapter_result_to_claim_check(result: Any, world: World) -> ClaimCheckResult:
    """Normalize a typed world adapter result to the generic checker surface.

    The adapter owns its receipt schema and verdict semantics.  This boundary
    only copies its JSON-compatible fields and verifies that the adapter's
    source hashes still equal the registered contract; it never turns an
    adapter error into an acceptance.
    """
    payload = result.as_dict()
    if not isinstance(payload, Mapping):
        raise WorldRegistryError(f"adapter {world.adapter!r} returned a non-object result")
    source_hashes = payload.get("source_hashes")
    if source_hashes is None:
        source_hashes = payload.get("snapshot_hashes")
    if not isinstance(source_hashes, Mapping):
        raise WorldRegistryError(f"adapter {world.adapter!r} returned no source hashes")
    actual = dict(source_hashes)
    expected = {
        contract.source: contract.sha256
        for contract in world.source_contracts
        if contract.sha256 is not None
    }
    if actual != expected:
        raise WorldRegistryError(
            f"adapter {world.adapter!r} source hashes do not match registered world"
        )

    verdict_name = payload.get("verdict")
    if not isinstance(verdict_name, str) or not verdict_name:
        raise WorldRegistryError(f"adapter {world.adapter!r} returned no verdict")
    verdict: dict[str, Any] = {"verdict": verdict_name}
    for key in (
        "outcome",
        "reason",
        "message",
        "reason_code",
        "winning_rule",
        "citations",
        "checker_version",
        "world_id",
        "world_version",
        "source_hashes",
        "snapshot_hashes",
    ):
        if key in payload:
            verdict[key] = payload[key]
    receipt = payload.get("receipt")
    if receipt is not None and not isinstance(receipt, Mapping):
        raise WorldRegistryError(f"adapter {world.adapter!r} returned an invalid receipt")
    return ClaimCheckResult(
        claim=dict(payload["claim"]) if isinstance(payload.get("claim"), Mapping) else None,
        evidence=dict(payload["evidence"]) if isinstance(payload.get("evidence"), Mapping) else None,
        verdict=verdict,
        receipt=dict(receipt) if isinstance(receipt, Mapping) else None,
    )


def _run_registered_adapter(
    world: World,
    fixture: Any,
    claim: Mapping[str, Any],
    *,
    checker_version: str,
) -> ClaimCheckResult:
    """Dispatch only to an explicitly registered adapter.

    K562 continues to use its ``SnapshotBundle`` protocol.  Other worlds use
    an explicit fixture path (Arc's directory, or an Open Targets/Clinical
    Trials JSON file) or an in-memory fixture mapping where the adapter
    supports it.  No directory walking, source lookup, or plugin discovery is
    performed here.
    """
    allowed = set(world.claim_fields)
    unknown = set(claim) - allowed
    if unknown:
        raise ClaimCheckInputError(
            f"claim contains fields outside {world.world_key}: {sorted(unknown)!r}"
        )
    if world.adapter == "k562":
        return _run_k562_adapter(fixture, claim, checker_version=checker_version)

    if world.adapter == "arc_vcc":
        from worlds.arc_vcc import ArcVCCAdapter

        if not isinstance(fixture, (str, Path)):
            raise ClaimCheckInputError(
                "Arc VCC requires an explicit fixture directory path"
            )
        adapter_result = ArcVCCAdapter.from_path(
            Path(fixture), checker_version=checker_version
        ).check(claim)
    elif world.adapter == "open_targets":
        from worlds.open_targets import OpenTargetsAdapter

        adapter_result = OpenTargetsAdapter(
            fixture, checker_version=checker_version
        ).check(claim, checker_version=checker_version)
    elif world.adapter == "clinical_trials":
        from worlds.clinical_trials import ClinicalTrialsAdapter

        adapter_result = ClinicalTrialsAdapter(
            fixture, checker_version=checker_version
        ).check(claim, checker_version=checker_version)
    else:
        raise WorldRegistryError(f"no adapter registered for world {world.world_key}")
    return _adapter_result_to_claim_check(adapter_result, world)


def check_claim(
    bundle: Any,
    world_id: str,
    world_version: str | None,
    claim: Mapping[str, Any] | None = None,
    *,
    checker_version: str = "0.1.0",
    registry: WorldRegistry = WORLD_REGISTRY,
    **claim_fields: Any,
) -> ClaimCheckResult:
    """Check a structured claim against one explicitly selected world.

    The generic boundary accepts only the registered adapter's closed fields;
    evidence ids, receipts, and world selectors cannot be supplied as claim
    content. A strict source set/digest check runs before any rule evaluation.
    """
    try:
        world = registry.resolve(world_id, world_version)
        if claim is not None and claim_fields:
            raise ClaimCheckInputError("provide either claim or world claim fields, not both")
        if claim is None and claim_fields:
            # Permit convenient keyword usage while keeping the closed field
            # set enforced by _run_k562_adapter (object_ is accepted as a
            # Python spelling convenience only at this API boundary).
            if "object_" in claim_fields and "object" not in claim_fields:
                claim_fields["object"] = claim_fields.pop("object_")
            claim = claim_fields
        if claim is None or not isinstance(claim, Mapping):
            raise ClaimCheckInputError("a structured world claim is required")
        if world.adapter == "k562":
            # Resolve and verify the exact world bundle before invoking any
            # adapter or rule. This is the fail-closed isolation gate for the
            # legacy SnapshotBundle protocol.
            _world_source_hashes(bundle, world)
        result = _run_registered_adapter(
            world, bundle, claim, checker_version=checker_version
        )
        if world.adapter == "k562":
            return _attach_receipt(
                result,
                world,
                bundle,
                checker_version=checker_version,
                strict_bundle=True,
            )
        return result
    except (WorldRegistryError, ClaimCheckInputError) as exc:
        return _checker_error(str(exc), claim=dict(claim) if isinstance(claim, Mapping) else None, checker_version=checker_version)
    except Exception as exc:  # noqa: BLE001 - fail closed at the world boundary
        return _checker_error(str(exc), claim=dict(claim) if isinstance(claim, Mapping) else None, stage="run_rules", checker_version=checker_version)


# Descriptive alias used by callers that prefer the protocol name.
check_world_claim = check_claim


def _check_k562_claim_impl(
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


def check_k562_claim(
    bundle: Any,
    subject: str,
    object_: str,
    direction: str,
    *,
    checker_version: str = "0.1.0",
    _internal: bool = False,
) -> ClaimCheckResult:
    """Compatibility wrapper that explicitly selects the registered K562 world."""
    try:
        # Keep the legacy surface bound to the same immutable world as the
        # generic protocol.  This check must precede label resolution and
        # rule evaluation so a same-shaped foreign bundle cannot participate.
        _world_source_hashes(bundle, K562_WORLD)
    except Exception as exc:  # noqa: BLE001 - compatibility boundary must fail closed
        return _checker_error(str(exc), checker_version=checker_version)
    result = _check_k562_claim_impl(
        bundle, subject, object_, direction, checker_version=checker_version
    )
    if _internal:
        return result
    return _attach_receipt(
        result,
        K562_WORLD,
        bundle,
        checker_version=checker_version,
        strict_bundle=True,
    )
