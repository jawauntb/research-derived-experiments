from __future__ import annotations

import copy
import dataclasses

import pytest

from normalize import CanonicalClaim, NormalizationError, normalize_claim


def _base_claim(**overrides):
    claim = {
        "schema_version": "0.1.0",
        "claim_id": "11111111-1111-4111-8111-111111111111",
        "subject": {"id": "HGNC:1097", "label": "BRAF"},
        "relation": "increases",
        "object": {"id": "HGNC:6407", "label": "KRAS"},
        "polarity": "positive",
        "species": "NCBITaxon:9606",
        "cell_context": {"cell_type": "CL:0000236", "cell_line": None, "state": None},
        "assay_context": {"assay": "CRISPRi_screen", "perturbation": "CRISPRi:HGNC:1097"},
        "evidence_ids": ["perturbseq.replogle_2022:aaaaaaaaaaaaaaaa"],
        "confidence_language": "supported",
        "requested_status": "hypothesis",
    }
    claim.update(overrides)
    return claim


# ---------------------------------------------------------------------------
# Required coverage
# ---------------------------------------------------------------------------


def test_happy_path_resolves_aliases(snapshot):
    claim = _base_claim(subject={"id": "HGNC:OLD1", "label": "BRAF (deprecated symbol)"})

    result = normalize_claim(claim, snapshot)

    assert isinstance(result, CanonicalClaim)
    assert result.subject_id == "HGNC:1097"
    assert result.subject_label == "BRAF (deprecated symbol)"
    assert result.object_id == "HGNC:6407"
    assert result.species == "NCBITaxon:9606"
    assert result.relation == "increases"
    assert result.polarity == "positive"
    assert result.evidence_ids == ("perturbseq.replogle_2022:aaaaaaaaaaaaaaaa",)


def test_unknown_entity_on_bad_curie_prefix(snapshot):
    claim = _base_claim(subject={"id": "FOO:123", "label": "Not a real prefix"})

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    err = exc_info.value
    assert err.fault_code == "UNKNOWN_ENTITY"
    assert err.curie == "FOO:123"
    assert err.where == "subject.id"


def test_unknown_entity_on_well_formed_but_unresolvable_id(snapshot):
    claim = _base_claim(object={"id": "HGNC:9999999", "label": "MADEUPKINASE"})

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    err = exc_info.value
    assert err.fault_code == "UNKNOWN_ENTITY"
    assert err.curie == "HGNC:9999999"
    assert err.where == "object.id"


def test_unspecified_cell_type_skips_ancestor_lookup(snapshot):
    claim = _base_claim(cell_context={"cell_type": "unspecified", "cell_line": None, "state": None})

    result = normalize_claim(claim, snapshot)

    assert result.cell_type == "unspecified"
    assert result.cell_type_ancestors == ()


def test_cl_cell_type_gets_correct_ancestor_tuple(snapshot):
    claim = _base_claim(cell_context={"cell_type": "CL:0000988", "cell_line": None, "state": None})

    result = normalize_claim(claim, snapshot)

    assert result.cell_type == "CL:0000988"
    assert result.cell_type_ancestors == ("CL:0000000",)

    # And the other fixture cell type, to be sure the mapping isn't hardcoded.
    claim2 = _base_claim(cell_context={"cell_type": "CL:0000236", "cell_line": None, "state": None})
    result2 = normalize_claim(claim2, snapshot)
    assert result2.cell_type_ancestors == ("CL:0000738", "CL:0000000")


def test_input_dict_not_mutated(snapshot):
    claim = _base_claim(subject={"id": "HGNC:OLD1", "label": "BRAF (deprecated symbol)"})
    original = copy.deepcopy(claim)

    normalize_claim(claim, snapshot)

    assert claim == original


def test_canonical_claim_is_frozen(snapshot):
    claim = _base_claim()
    result = normalize_claim(claim, snapshot)

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.subject_id = "HGNC:6407"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Additional branch coverage
# ---------------------------------------------------------------------------


def test_unknown_entity_species(snapshot):
    claim = _base_claim(species="NCBITaxon:0000000")

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code == "UNKNOWN_ENTITY"
    assert exc_info.value.where == "species"


def test_unknown_entity_cell_type(snapshot):
    claim = _base_claim(
        cell_context={"cell_type": "CL:9999999", "cell_line": None, "state": None}
    )

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code == "UNKNOWN_ENTITY"
    assert exc_info.value.where == "cell_context.cell_type"


def test_unknown_entity_cell_line(snapshot):
    claim = _base_claim(
        cell_context={"cell_type": "CL:0000236", "cell_line": "CLO:9999999", "state": None}
    )

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code == "UNKNOWN_ENTITY"
    assert exc_info.value.where == "cell_context.cell_line"


def test_cell_line_none_passes_through(snapshot):
    claim = _base_claim(
        cell_context={"cell_type": "CL:0000236", "cell_line": None, "state": "resting"}
    )

    result = normalize_claim(claim, snapshot)

    assert result.cell_line is None
    assert result.state == "resting"


def test_cell_line_curie_is_canonicalized(snapshot):
    # FakeSnapshot's fixed universe doesn't include a CLO cell-line entry, but
    # normalize.py treats cell_line generically as "any CURIE the Snapshot
    # knows about" -- reuse a fixture gene CURIE purely to exercise the
    # resolution code path, not for domain realism.
    claim = _base_claim(
        cell_context={"cell_type": "CL:0000236", "cell_line": "HGNC:OLD1", "state": None}
    )

    result = normalize_claim(claim, snapshot)

    assert result.cell_line == "HGNC:1097"


def test_perturbation_and_assay_pass_through_untouched(snapshot):
    claim = _base_claim(
        assay_context={"assay": "CRISPRi_screen", "perturbation": "CRISPRi:HGNC:1097"}
    )

    result = normalize_claim(claim, snapshot)

    assert result.assay == "CRISPRi_screen"
    assert result.perturbation == "CRISPRi:HGNC:1097"


def test_perturbation_null_passes_through(snapshot):
    claim = _base_claim(assay_context={"assay": "bulk-RNA-seq", "perturbation": None})

    result = normalize_claim(claim, snapshot)

    assert result.perturbation is None


def test_non_dict_claim_raises_normalization_error(snapshot):
    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim("not a dict", snapshot)  # type: ignore[arg-type]

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "claim"


def test_non_dict_subject_raises_normalization_error(snapshot):
    claim = _base_claim(subject="BRAF")  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "subject"


def test_non_dict_cell_context_raises_normalization_error(snapshot):
    claim = _base_claim(cell_context="CL:0000236")  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "cell_context"


def test_non_dict_assay_context_raises_normalization_error(snapshot):
    claim = _base_claim(assay_context="CRISPRi_screen")  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "assay_context"


def test_wrong_type_scalar_field_raises_normalization_error(snapshot):
    claim = _base_claim(claim_id=12345)  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "claim_id"


def test_invalid_relation_enum_raises_normalization_error(snapshot):
    claim = _base_claim(relation="regulates_epigenetically")

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "relation"


def test_invalid_polarity_enum_raises_normalization_error(snapshot):
    claim = _base_claim(polarity="sideways")

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "polarity"


def test_invalid_confidence_language_raises_normalization_error(snapshot):
    claim = _base_claim(confidence_language="definitely")

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.where == "confidence_language"


def test_invalid_requested_status_raises_normalization_error(snapshot):
    claim = _base_claim(requested_status="proven")

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.where == "requested_status"


def test_evidence_ids_not_a_list_raises_normalization_error(snapshot):
    claim = _base_claim(evidence_ids="perturbseq.replogle_2022:aaaaaaaaaaaaaaaa")  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.fault_code is None
    assert exc_info.value.where == "evidence_ids"


def test_evidence_ids_with_non_string_item_raises_normalization_error(snapshot):
    claim = _base_claim(evidence_ids=[123])  # type: ignore[arg-type]

    with pytest.raises(NormalizationError) as exc_info:
        normalize_claim(claim, snapshot)

    assert exc_info.value.where == "evidence_ids"


def test_evidence_ids_are_preserved_and_not_resolved(snapshot):
    claim = _base_claim(
        evidence_ids=["perturbseq.replogle_2022:aaaaaaaaaaaaaaaa", "does.not.exist:0000000000000000"]
    )

    result = normalize_claim(claim, snapshot)

    # Both ids survive untouched -- resolving them against the evidence
    # ledger is the evidence loader's job, not this module's.
    assert result.evidence_ids == (
        "perturbseq.replogle_2022:aaaaaaaaaaaaaaaa",
        "does.not.exist:0000000000000000",
    )


def test_resolved_but_non_cl_cell_type_has_empty_ancestors(snapshot):
    # A cell_type value that resolves but isn't CL-prefixed has no is_a
    # closure defined; normalize.py should fail soft to an empty tuple
    # rather than erroring.
    claim = _base_claim(
        cell_context={"cell_type": "HGNC:1097", "cell_line": None, "state": None}
    )

    result = normalize_claim(claim, snapshot)

    assert result.cell_type == "HGNC:1097"
    assert result.cell_type_ancestors == ()


def test_snapshot_reporting_contains_false_yields_empty_ancestors(snapshot):
    class _RogueSnapshot:
        """A deliberately misbehaving Snapshot: canonicalize() returns a
        CL curie that contains() then denies. Exercises normalize.py's
        defensive belt-and-suspenders guard around ancestors()."""

        def contains(self, curie: str) -> bool:
            return False

        def canonicalize(self, curie: str) -> str:
            return "CL:0000236"

        def ancestors(self, curie: str) -> tuple[str, ...]:  # pragma: no cover - must not be called
            raise AssertionError("ancestors() should not be called when contains() is False")

        def aliases(self, curie: str) -> tuple[str, ...]:
            return ()

    claim = _base_claim()
    result = normalize_claim(claim, _RogueSnapshot())

    assert result.cell_type_ancestors == ()
