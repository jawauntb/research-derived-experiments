"""Canonical (post-normalization) dataclasses for Claim and EvidenceRecord.

Fields mirror `spec/claim.schema.json` and `spec/evidence.schema.json`,
flattened one level (`EntityRef`, `cell_context`, `assay_context` all
inlined) so the rule engine can compare fields cheaply without re-navigating
nested dicts. Enum fields use `Literal[...]` matching each schema's enum
verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Relation = Literal[
    "increases",
    "decreases",
    "binds",
    "expressed_in",
    "causes",
    "correlates_with",
]
Polarity = Literal["positive", "negative", "none"]
ConfidenceLanguage = Literal["observed", "supported", "suggestive", "causal"]
RequestedStatus = Literal["hypothesis", "established"]

RecordType = Literal[
    "perturbation_effect",
    "physical_interaction",
    "pathway_membership",
    "expression_observation",
    "ontology_annotation",
    "identifier_alias",
]
ObservationType = Literal["interventional", "observational"]
# NORMALIZE-DECISION: evidence.schema.json's effect.sign enum is
# `["positive", "negative", "null"]` — the *string* "null", not JSON null —
# preserved verbatim rather than collapsed into Python None, since the schema
# treats it as a distinct sign value (measured-but-directionless), not
# "field absent".
EffectSign = Literal["positive", "negative", "null"]


@dataclass(frozen=True, slots=True)
class CanonicalEffect:
    """Canonical form of `EvidenceRecord.effect`."""

    sign: EffectSign
    magnitude: float
    significance: float | None
    magnitude_scale: str | None = None
    n_replicates: int | None = None


@dataclass(frozen=True, slots=True)
class CanonicalClaim:
    """Canonical form of a Claim (spec/claim.schema.json), ready for the rule engine."""

    schema_version: str
    claim_id: str
    subject_id: str
    subject_label: str
    relation: Relation
    object_id: str
    object_label: str
    polarity: Polarity
    species: str
    cell_type: str
    cell_type_ancestors: tuple[str, ...]
    cell_line: str | None
    state: str | None
    assay: str
    perturbation: str | None
    evidence_ids: tuple[str, ...]
    confidence_language: ConfidenceLanguage
    requested_status: RequestedStatus


@dataclass(frozen=True, slots=True)
class CanonicalEvidence:
    """Canonical form of an EvidenceRecord (spec/evidence.schema.json)."""

    schema_version: str
    evidence_id: str
    source: str
    snapshot_hash: str
    record_type: RecordType
    subject_id: str
    subject_label: str
    object_id: str
    object_label: str
    species: str
    cell_type: str
    cell_line: str | None
    state: str | None
    assay: str
    perturbation: str | None
    observation_type: ObservationType
    effect: CanonicalEffect | None
    contradicts: tuple[str, ...]
    retrieved_at: str
    license: str
    source_citation: str | None
