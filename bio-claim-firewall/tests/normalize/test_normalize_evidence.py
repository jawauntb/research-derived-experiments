from __future__ import annotations

import copy
import dataclasses

import pytest

from normalize import CanonicalEffect, CanonicalEvidence, NormalizationError, normalize_evidence


def _base_record(**overrides):
    record = {
        "schema_version": "0.1.0",
        "evidence_id": "perturbseq.replogle_2022:aaaaaaaaaaaaaaaa",
        "source": "perturbseq.replogle_2022",
        "snapshot_hash": "a" * 64,
        "record_type": "perturbation_effect",
        "subject": {"id": "HGNC:1097", "label": "BRAF"},
        "object": {"id": "HGNC:6407", "label": "KRAS"},
        "species": "NCBITaxon:9606",
        "cell_context": {"cell_type": "CL:0000236", "cell_line": None, "state": None},
        "assay_context": {"assay": "CRISPRi_screen", "perturbation": "CRISPRi:HGNC:1097"},
        "observation_type": "interventional",
        "effect": {
            "sign": "positive",
            "magnitude": 1.5,
            "magnitude_scale": "log2fc",
            "significance": 0.01,
            "n_replicates": 3,
        },
        "contradicts": [],
        "retrieved_at": "2026-01-01T00:00:00Z",
        "license": "CC0",
        "source_citation": None,
    }
    record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# Required coverage (analogous to test_normalize_claim.py)
# ---------------------------------------------------------------------------


def test_happy_path_resolves_aliases(snapshot):
    record = _base_record(subject={"id": "HGNC:OLD1", "label": "BRAF (deprecated symbol)"})

    result = normalize_evidence(record, snapshot)

    assert isinstance(result, CanonicalEvidence)
    assert result.subject_id == "HGNC:1097"
    assert result.subject_label == "BRAF (deprecated symbol)"
    assert result.object_id == "HGNC:6407"
    assert result.species == "NCBITaxon:9606"
    assert result.record_type == "perturbation_effect"
    assert result.observation_type == "interventional"


def test_unknown_entity_on_bad_curie_prefix(snapshot):
    record = _base_record(subject={"id": "FOO:123", "label": "Not a real prefix"})

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    err = exc_info.value
    assert err.fault_code == "UNKNOWN_ENTITY"
    assert err.curie == "FOO:123"
    assert err.where == "subject.id"


def test_unknown_entity_on_well_formed_but_unresolvable_id(snapshot):
    record = _base_record(object={"id": "HGNC:9999999", "label": "MADEUPKINASE"})

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    err = exc_info.value
    assert err.fault_code == "UNKNOWN_ENTITY"
    assert err.curie == "HGNC:9999999"
    assert err.where == "object.id"


def test_unspecified_cell_type_skips_canonicalization(snapshot):
    # Evidence records don't officially carry the claim-only "unspecified"
    # escape hatch, but normalize_evidence handles it the same defensive way
    # as normalize_claim for symmetry, rather than trying to resolve the
    # literal string as a CURIE.
    record = _base_record(cell_context={"cell_type": "unspecified", "cell_line": None, "state": None})

    result = normalize_evidence(record, snapshot)

    assert result.cell_type == "unspecified"


def test_cl_cell_type_is_canonicalized(snapshot):
    record = _base_record(cell_context={"cell_type": "CL:0000988", "cell_line": None, "state": None})

    result = normalize_evidence(record, snapshot)

    assert result.cell_type == "CL:0000988"


def test_input_dict_not_mutated(snapshot):
    record = _base_record(subject={"id": "HGNC:OLD1", "label": "BRAF (deprecated symbol)"})
    original = copy.deepcopy(record)

    normalize_evidence(record, snapshot)

    assert record == original


def test_canonical_evidence_is_frozen(snapshot):
    record = _base_record()
    result = normalize_evidence(record, snapshot)

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.subject_id = "HGNC:6407"  # type: ignore[misc]


def test_canonical_effect_is_frozen(snapshot):
    record = _base_record()
    result = normalize_evidence(record, snapshot)

    assert result.effect is not None
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.effect.sign = "negative"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# effect sub-object preservation
# ---------------------------------------------------------------------------


def test_effect_subobject_is_preserved(snapshot):
    record = _base_record(
        effect={
            "sign": "negative",
            "magnitude": -2.25,
            "magnitude_scale": "pearson_r",
            "significance": 0.049,
            "n_replicates": 4,
        }
    )

    result = normalize_evidence(record, snapshot)

    assert result.effect == CanonicalEffect(
        sign="negative",
        magnitude=-2.25,
        significance=0.049,
        magnitude_scale="pearson_r",
        n_replicates=4,
    )


def test_effect_null_is_preserved_for_non_perturbation_records(snapshot):
    record = _base_record(
        record_type="physical_interaction",
        observation_type="observational",
        effect=None,
    )

    result = normalize_evidence(record, snapshot)

    assert result.effect is None


def test_effect_with_only_required_fields(snapshot):
    record = _base_record(
        effect={"sign": "null", "magnitude": 0.0, "significance": None}
    )

    result = normalize_evidence(record, snapshot)

    assert result.effect == CanonicalEffect(
        sign="null", magnitude=0.0, significance=None, magnitude_scale=None, n_replicates=None
    )


def test_effect_not_a_dict_raises_normalization_error(snapshot):
    record = _base_record(effect="positive")  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "effect"


def test_effect_bad_sign_enum_raises_normalization_error(snapshot):
    record = _base_record(effect={"sign": "up", "magnitude": 1.0, "significance": None})

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.where == "effect.sign"


def test_effect_bad_magnitude_type_raises_normalization_error(snapshot):
    record = _base_record(effect={"sign": "positive", "magnitude": "big", "significance": None})

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.where == "effect.magnitude"


def test_effect_bad_significance_type_raises_normalization_error(snapshot):
    record = _base_record(effect={"sign": "positive", "magnitude": 1.0, "significance": "low"})

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.where == "effect.significance"


def test_effect_bad_n_replicates_type_raises_normalization_error(snapshot):
    record = _base_record(
        effect={
            "sign": "positive",
            "magnitude": 1.0,
            "significance": None,
            "n_replicates": "three",
        }
    )

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.where == "effect.n_replicates"


# ---------------------------------------------------------------------------
# Additional branch coverage
# ---------------------------------------------------------------------------


def test_unknown_entity_species(snapshot):
    record = _base_record(species="NCBITaxon:0000000")

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.fault_code == "UNKNOWN_ENTITY"
    assert exc_info.value.where == "species"


def test_unknown_entity_cell_line(snapshot):
    record = _base_record(
        cell_context={"cell_type": "CL:0000236", "cell_line": "CLO:9999999", "state": None}
    )

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.fault_code == "UNKNOWN_ENTITY"
    assert exc_info.value.where == "cell_context.cell_line"


def test_contradicts_list_is_preserved_untouched(snapshot):
    record = _base_record(
        contradicts=["reactome.v88:bbbbbbbbbbbbbbbb", "go.2026-06-01:cccccccccccccccc"]
    )

    result = normalize_evidence(record, snapshot)

    assert result.contradicts == (
        "reactome.v88:bbbbbbbbbbbbbbbb",
        "go.2026-06-01:cccccccccccccccc",
    )


def test_contradicts_defaults_to_empty_tuple_when_absent(snapshot):
    record = _base_record()
    del record["contradicts"]

    result = normalize_evidence(record, snapshot)

    assert result.contradicts == ()


def test_contradicts_not_a_list_raises_normalization_error(snapshot):
    record = _base_record(contradicts="reactome.v88:bbbbbbbbbbbbbbbb")  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.where == "contradicts"


def test_source_citation_none_passes_through(snapshot):
    record = _base_record(source_citation=None)

    result = normalize_evidence(record, snapshot)

    assert result.source_citation is None


def test_source_citation_string_passes_through(snapshot):
    record = _base_record(source_citation="PMID:12345678")

    result = normalize_evidence(record, snapshot)

    assert result.source_citation == "PMID:12345678"


def test_non_dict_record_raises_normalization_error(snapshot):
    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence("not a dict", snapshot)  # type: ignore[arg-type]

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "record"


def test_invalid_record_type_enum_raises_normalization_error(snapshot):
    record = _base_record(record_type="made_up_type")

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "record_type"


def test_invalid_observation_type_enum_raises_normalization_error(snapshot):
    record = _base_record(observation_type="hypothetical")

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.where == "observation_type"


def test_wrong_type_scalar_field_raises_normalization_error(snapshot):
    record = _base_record(evidence_id=12345)  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_evidence(record, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "evidence_id"
