"""SnapshotBundle satisfies the Snapshot protocol needed by src/normalize and src/rules.

The protocol lives in ``src/normalize/snapshot.py`` and is the canonical
contract (a ``runtime_checkable`` Protocol). These tests exercise the
protocol's methods on a real ``SnapshotBundle`` built by ``load_bundle`` and
also assert structural conformance via ``isinstance``.
"""

from __future__ import annotations

import pytest

from evidence.loader import load_bundle
from evidence.snapshot import SnapshotBundle
from normalize.errors import NormalizationError
from normalize.snapshot import Snapshot

from conftest import (
    CELL_TYPE_CHILD,
    CELL_TYPE_OTHER,
    CELL_TYPE_PARENT,
    CELL_TYPE_ROOT,
    GENE_1,
    GENE_1_DEPRECATED,
    SPECIES_ID,
)


def test_snapshot_bundle_is_a_runtime_checkable_snapshot(data_root):
    bundle = load_bundle(data_root)

    assert isinstance(bundle, SnapshotBundle)
    assert isinstance(bundle, Snapshot)


def test_contains_true_for_every_loaded_curie_class(data_root):
    bundle = load_bundle(data_root)

    assert bundle.contains(GENE_1) is True
    assert bundle.contains(SPECIES_ID) is True
    assert bundle.contains(CELL_TYPE_CHILD) is True
    assert bundle.contains(CELL_TYPE_OTHER) is True


def test_contains_false_for_unknown_curie(data_root):
    bundle = load_bundle(data_root)
    assert bundle.contains("HGNC:9999999") is False


def test_contains_false_for_deprecated_alias(data_root):
    # normalize.Snapshot.contains is an as-is membership check, NOT a
    # resolvability check. R-ENT-02's "deprecated alias resolves" semantics
    # are the responsibility of ``canonicalize`` (which does the forward-hop);
    # callers who want the resolvability check compose
    # ``contains(canonicalize(x))``.
    bundle = load_bundle(data_root)
    assert bundle.contains(GENE_1_DEPRECATED) is False


def test_canonicalize_resolves_deprecated_alias(data_root):
    bundle = load_bundle(data_root)
    assert bundle.canonicalize(GENE_1_DEPRECATED) == GENE_1


def test_canonicalize_identity_for_already_canonical(data_root):
    bundle = load_bundle(data_root)
    assert bundle.canonicalize(GENE_1) == GENE_1


def test_canonicalize_raises_unknown_entity_for_unresolvable_curie(data_root):
    bundle = load_bundle(data_root)
    with pytest.raises(NormalizationError) as exc_info:
        bundle.canonicalize("HGNC:9999999")
    assert exc_info.value.fault_code == "UNKNOWN_ENTITY"
    assert exc_info.value.curie == "HGNC:9999999"


def test_ancestors_returns_recorded_closure_for_known_cell_type(data_root):
    bundle = load_bundle(data_root)

    assert bundle.ancestors(CELL_TYPE_CHILD) == (CELL_TYPE_PARENT, CELL_TYPE_ROOT)
    assert bundle.ancestors(CELL_TYPE_OTHER) == (CELL_TYPE_PARENT, CELL_TYPE_ROOT)


def test_ancestors_empty_tuple_for_unknown_curie(data_root):
    bundle = load_bundle(data_root)
    assert bundle.ancestors("CL:0000000000") == ()


def test_aliases_returns_deprecated_forwarding_onto_canonical(data_root):
    bundle = load_bundle(data_root)
    assert bundle.aliases(GENE_1) == (GENE_1_DEPRECATED,)


def test_aliases_returns_empty_tuple_for_curie_with_no_deprecated_forms(data_root):
    bundle = load_bundle(data_root)
    assert bundle.aliases(SPECIES_ID) == ()


def test_ledger_is_reachable_from_the_bundle(data_root):
    bundle = load_bundle(data_root)
    assert bundle.ledger.count() == 2
