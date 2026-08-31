"""Canonicalization of a schema-valid Claim / EvidenceRecord dict.

`normalize_claim` and `normalize_evidence` are the two public entry points.
Both assume the input already validated against its JSON Schema (schema
validation is the verifier's job, not this module's) but still do a
defensive shape check on the outermost fields, because this module must not
crash uncontrolled on a malformed dict — it must fail with a typed
`NormalizationError` so the rule engine can turn it into a `CHECKER_ERROR`
verdict rather than an unhandled exception.

Every CURIE-shaped field is canonicalized via `Snapshot.canonicalize()`.
`snapshot.canonicalize()` already raises `NormalizationError` with
`fault_code="UNKNOWN_ENTITY"` when a CURIE is unresolvable (per the `Snapshot`
Protocol contract); this module's job is to enrich that error with a `where`
path when the Snapshot implementation did not set one, not to invent new
failure modes.

Neither function mutates its input dict — every value is read via `.get()`.
"""

from __future__ import annotations

from typing import Any

from .errors import NormalizationError
from .snapshot import Snapshot
from .types import (
    CanonicalClaim,
    CanonicalEffect,
    CanonicalEvidence,
)

_ALLOWED_RELATIONS = frozenset(
    {"increases", "decreases", "binds", "expressed_in", "causes", "correlates_with"}
)
_ALLOWED_POLARITIES = frozenset({"positive", "negative", "none"})
_ALLOWED_CONFIDENCE_LANGUAGES = frozenset(
    {"observed", "supported", "suggestive", "causal"}
)
_ALLOWED_REQUESTED_STATUSES = frozenset({"hypothesis", "established"})

_ALLOWED_RECORD_TYPES = frozenset(
    {
        "perturbation_effect",
        "physical_interaction",
        "pathway_membership",
        "expression_observation",
        "ontology_annotation",
        "identifier_alias",
    }
)
_ALLOWED_OBSERVATION_TYPES = frozenset({"interventional", "observational"})
_ALLOWED_EFFECT_SIGNS = frozenset({"positive", "negative", "null"})

_UNSPECIFIED_CELL_TYPE = "unspecified"
_CL_PREFIX = "CL:"


# ---------------------------------------------------------------------------
# Defensive shape helpers (see module docstring: these are NOT UNKNOWN_ENTITY)
# ---------------------------------------------------------------------------


def _require_dict(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise NormalizationError(
            f"expected {where!r} to be an object, got {type(value).__name__}",
            where=where,
        )
    return value


def _require_str(value: Any, where: str) -> str:
    if not isinstance(value, str):
        raise NormalizationError(
            f"expected {where!r} to be a string, got {type(value).__name__}",
            where=where,
        )
    return value


def _require_optional_str(value: Any, where: str) -> str | None:
    if value is None:
        return None
    return _require_str(value, where)


def _require_number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NormalizationError(
            f"expected {where!r} to be a number, got {type(value).__name__}",
            where=where,
        )
    return float(value)


def _require_optional_number(value: Any, where: str) -> float | None:
    if value is None:
        return None
    return _require_number(value, where)


def _require_optional_int(value: Any, where: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise NormalizationError(
            f"expected {where!r} to be an integer or null, got {type(value).__name__}",
            where=where,
        )
    return value


def _require_enum(value: Any, allowed: frozenset[str], where: str) -> str:
    s = _require_str(value, where)
    if s not in allowed:
        raise NormalizationError(
            f"{where}={s!r} is not one of {sorted(allowed)}", where=where
        )
    return s


def _require_str_list(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise NormalizationError(
            f"expected {where!r} to be a list of strings", where=where
        )
    return tuple(value)


# ---------------------------------------------------------------------------
# CURIE canonicalization
# ---------------------------------------------------------------------------


def _canonicalize_curie(snapshot: Snapshot, curie: str, where: str) -> str:
    """Canonicalize one CURIE, tagging any failure with `where` for the caller.

    `Snapshot.canonicalize()` already raises `NormalizationError` with
    `fault_code="UNKNOWN_ENTITY"` on its own (per the Protocol contract), but
    a Snapshot implementation cannot know which claim/evidence field it was
    called for. This wrapper fills in `where` (and `curie`, defensively) when
    the raised error didn't already carry one, without changing fault_code.
    """
    try:
        return snapshot.canonicalize(curie)
    except NormalizationError as exc:
        raise NormalizationError(
            exc.args[0] if exc.args else f"{curie!r} does not resolve",
            fault_code=exc.fault_code or "UNKNOWN_ENTITY",
            curie=exc.curie or curie,
            where=exc.where or where,
        ) from exc


def _canonicalize_entity_ref(
    snapshot: Snapshot, ref: Any, where: str
) -> tuple[str, str]:
    ref = _require_dict(ref, where)
    curie = _require_str(ref.get("id"), f"{where}.id")
    label = _require_str(ref.get("label"), f"{where}.label")
    canonical_id = _canonicalize_curie(snapshot, curie, f"{where}.id")
    return canonical_id, label


def _canonicalize_optional_curie(
    snapshot: Snapshot, value: Any, where: str
) -> str | None:
    if value is None:
        return None
    curie = _require_str(value, where)
    return _canonicalize_curie(snapshot, curie, where)


def _canonicalize_cell_type(snapshot: Snapshot, value: Any, where: str) -> str:
    cell_type = _require_str(value, where)
    if cell_type == _UNSPECIFIED_CELL_TYPE:
        return cell_type
    return _canonicalize_curie(snapshot, cell_type, where)


def _cell_type_ancestors(snapshot: Snapshot, canonical_cell_type: str) -> tuple[str, ...]:
    """Ancestor closure for R-CTX-02 — only ever non-empty for a resolved CL CURIE."""
    if canonical_cell_type == _UNSPECIFIED_CELL_TYPE:
        return ()
    if not canonical_cell_type.startswith(_CL_PREFIX):
        # NORMALIZE-DECISION: a cell_type that resolved but isn't CL-prefixed
        # has no is_a ancestor closure defined (only Cell Ontology terms do
        # per inference_rules.md §1/§5); treat as empty rather than erroring,
        # least-authority default since R-CTX-02 only ever consults CL
        # closures.
        return ()
    # Defensive belt-and-suspenders: canonicalize()'s postcondition should
    # guarantee contains(canonical_cell_type), but we don't trust that of an
    # arbitrary Snapshot implementation blindly before calling ancestors().
    if not snapshot.contains(canonical_cell_type):
        return ()  # NORMALIZE-DECISION: see above — fail soft, not hard.
    return tuple(snapshot.ancestors(canonical_cell_type))


# ---------------------------------------------------------------------------
# Shared cell_context / assay_context handling
# ---------------------------------------------------------------------------


def _normalize_cell_context(
    snapshot: Snapshot, claim_or_record: dict[str, Any]
) -> tuple[str, str | None, str | None]:
    cell_context = _require_dict(claim_or_record.get("cell_context"), "cell_context")
    cell_type = _canonicalize_cell_type(
        snapshot, cell_context.get("cell_type"), "cell_context.cell_type"
    )
    cell_line = _canonicalize_optional_curie(
        snapshot, cell_context.get("cell_line"), "cell_context.cell_line"
    )
    state = _require_optional_str(cell_context.get("state"), "cell_context.state")
    return cell_type, cell_line, state


def _normalize_assay_context(claim_or_record: dict[str, Any]) -> tuple[str, str | None]:
    assay_context = _require_dict(claim_or_record.get("assay_context"), "assay_context")
    assay = _require_str(assay_context.get("assay"), "assay_context.assay")
    # NORMALIZE-DECISION: assay_context.perturbation (e.g. "CRISPRi:HGNC:1097")
    # is documented as a free-text label, not a CURIE on its own — it does not
    # match EntityRef.id's CURIE pattern as a whole string. R-CTX-06 only
    # requires exact string equality against the evidence record's
    # perturbation field, so it is left untouched rather than parsed and
    # partially canonicalized.
    perturbation = _require_optional_str(
        assay_context.get("perturbation"), "assay_context.perturbation"
    )
    return assay, perturbation


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_claim(claim: dict, snapshot: Snapshot) -> CanonicalClaim:
    """Canonicalize a schema-valid Claim dict. Never mutates `claim`."""
    claim = _require_dict(claim, "claim")

    schema_version = _require_str(claim.get("schema_version"), "schema_version")
    claim_id = _require_str(claim.get("claim_id"), "claim_id")
    relation = _require_enum(claim.get("relation"), _ALLOWED_RELATIONS, "relation")
    polarity = _require_enum(claim.get("polarity"), _ALLOWED_POLARITIES, "polarity")
    confidence_language = _require_enum(
        claim.get("confidence_language"), _ALLOWED_CONFIDENCE_LANGUAGES, "confidence_language"
    )
    requested_status = _require_enum(
        claim.get("requested_status"), _ALLOWED_REQUESTED_STATUSES, "requested_status"
    )

    subject_id, subject_label = _canonicalize_entity_ref(snapshot, claim.get("subject"), "subject")
    object_id, object_label = _canonicalize_entity_ref(snapshot, claim.get("object"), "object")

    species = _canonicalize_curie(
        snapshot, _require_str(claim.get("species"), "species"), "species"
    )

    cell_type, cell_line, state = _normalize_cell_context(snapshot, claim)
    cell_type_ancestors = _cell_type_ancestors(snapshot, cell_type)

    assay, perturbation = _normalize_assay_context(claim)

    # NORMALIZE-DECISION: evidence_ids are preserved untouched (not resolved
    # against the evidence ledger) per the task spec — resolving them is the
    # evidence loader's job, not this module's.
    evidence_ids = _require_str_list(claim.get("evidence_ids"), "evidence_ids")

    return CanonicalClaim(
        schema_version=schema_version,
        claim_id=claim_id,
        subject_id=subject_id,
        subject_label=subject_label,
        relation=relation,  # type: ignore[arg-type]
        object_id=object_id,
        object_label=object_label,
        polarity=polarity,  # type: ignore[arg-type]
        species=species,
        cell_type=cell_type,
        cell_type_ancestors=cell_type_ancestors,
        cell_line=cell_line,
        state=state,
        assay=assay,
        perturbation=perturbation,
        evidence_ids=evidence_ids,
        confidence_language=confidence_language,  # type: ignore[arg-type]
        requested_status=requested_status,  # type: ignore[arg-type]
    )


def _canonicalize_effect(effect: Any, where: str) -> CanonicalEffect | None:
    if effect is None:
        return None
    effect = _require_dict(effect, where)
    sign = _require_enum(effect.get("sign"), _ALLOWED_EFFECT_SIGNS, f"{where}.sign")
    magnitude = _require_number(effect.get("magnitude"), f"{where}.magnitude")
    significance = _require_optional_number(effect.get("significance"), f"{where}.significance")
    magnitude_scale = _require_optional_str(
        effect.get("magnitude_scale"), f"{where}.magnitude_scale"
    )
    n_replicates = _require_optional_int(effect.get("n_replicates"), f"{where}.n_replicates")
    return CanonicalEffect(
        sign=sign,  # type: ignore[arg-type]
        magnitude=magnitude,
        significance=significance,
        magnitude_scale=magnitude_scale,
        n_replicates=n_replicates,
    )


def normalize_evidence(record: dict, snapshot: Snapshot) -> CanonicalEvidence:
    """Canonicalize a schema-valid EvidenceRecord dict. Never mutates `record`."""
    record = _require_dict(record, "record")

    schema_version = _require_str(record.get("schema_version"), "schema_version")
    evidence_id = _require_str(record.get("evidence_id"), "evidence_id")
    source = _require_str(record.get("source"), "source")
    snapshot_hash = _require_str(record.get("snapshot_hash"), "snapshot_hash")
    record_type = _require_enum(record.get("record_type"), _ALLOWED_RECORD_TYPES, "record_type")
    observation_type = _require_enum(
        record.get("observation_type"), _ALLOWED_OBSERVATION_TYPES, "observation_type"
    )

    subject_id, subject_label = _canonicalize_entity_ref(snapshot, record.get("subject"), "subject")
    object_id, object_label = _canonicalize_entity_ref(snapshot, record.get("object"), "object")

    species = _canonicalize_curie(
        snapshot, _require_str(record.get("species"), "species"), "species"
    )

    cell_type, cell_line, state = _normalize_cell_context(snapshot, record)
    assay, perturbation = _normalize_assay_context(record)

    effect = _canonicalize_effect(record.get("effect"), "effect")

    # `contradicts` holds evidence_ids (ledger keys), not ontology CURIEs, so
    # it is not run through snapshot.canonicalize() — only shape-checked.
    contradicts = _require_str_list(record.get("contradicts", []), "contradicts")

    retrieved_at = _require_str(record.get("retrieved_at"), "retrieved_at")
    license_ = _require_str(record.get("license"), "license")
    source_citation = _require_optional_str(record.get("source_citation"), "source_citation")

    return CanonicalEvidence(
        schema_version=schema_version,
        evidence_id=evidence_id,
        source=source,
        snapshot_hash=snapshot_hash,
        record_type=record_type,  # type: ignore[arg-type]
        subject_id=subject_id,
        subject_label=subject_label,
        object_id=object_id,
        object_label=object_label,
        species=species,
        cell_type=cell_type,
        cell_line=cell_line,
        state=state,
        assay=assay,
        perturbation=perturbation,
        observation_type=observation_type,  # type: ignore[arg-type]
        effect=effect,
        contradicts=contradicts,
        retrieved_at=retrieved_at,
        license=license_,
        source_citation=source_citation,
    )
