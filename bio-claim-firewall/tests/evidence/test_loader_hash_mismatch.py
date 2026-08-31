"""Load-bearing for R-CITE-02 / the checker's fail-closed hash verification.

If the loader ever stops catching a manifest/file sha256 disagreement, a
tampered snapshot could be served as if it were the frozen, trusted one --
this is exactly the failure mode spec/fault_taxonomy.md's `CHECKER_ERROR`
bucket ("snapshot hash mismatch") exists to catch fail-closed.
"""

from __future__ import annotations

import json

import pytest

from src.evidence.errors import EvidenceError
from src.evidence.loader import load_bundle

from conftest import EVIDENCE_SOURCE


def _flip_one_hex_char(hex_str: str) -> str:
    flipped_char = "1" if hex_str[0] == "0" else "0"
    return flipped_char + hex_str[1:]


def test_loader_succeeds_on_untampered_data_root(data_root):
    bundle = load_bundle(data_root)
    assert bundle.ledger.count() == 2


def test_loader_raises_hash_mismatch_when_ontology_manifest_disagrees(data_root):
    target = data_root / "manifests" / "hgnc.test.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["sha256"] = _flip_one_hex_char(payload["sha256"])
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EvidenceError) as exc_info:
        load_bundle(data_root)

    assert exc_info.value.fault_code == "HASH_MISMATCH"


def test_loader_raises_hash_mismatch_when_evidence_manifest_disagrees(data_root):
    target = data_root / "manifests" / f"{EVIDENCE_SOURCE}.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["sha256"] = _flip_one_hex_char(payload["sha256"])
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EvidenceError) as exc_info:
        load_bundle(data_root)

    assert exc_info.value.fault_code == "HASH_MISMATCH"


def test_loader_raises_hash_mismatch_when_evidence_file_is_tampered_post_manifest(data_root):
    # The manifest is untouched and correct; the underlying records.jsonl
    # is edited after the fact -- the more realistic tamper scenario.
    records_path = data_root / "evidence_records" / EVIDENCE_SOURCE / "records.jsonl"
    records_path.write_text(records_path.read_text(encoding="utf-8") + '{"tampered": true}\n', encoding="utf-8")

    with pytest.raises(EvidenceError) as exc_info:
        load_bundle(data_root)

    assert exc_info.value.fault_code == "HASH_MISMATCH"


def test_loader_raises_hash_mismatch_never_silently_continues(data_root):
    # Fail-closed means the whole bundle refuses to load, not just the
    # tampered source -- assert the exception actually propagates out of
    # load_bundle rather than, say, being swallowed and yielding a bundle
    # missing just that source.
    target = data_root / "manifests" / "hgnc.test.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["sha256"] = _flip_one_hex_char(payload["sha256"])
    target.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(EvidenceError):
        load_bundle(data_root)
