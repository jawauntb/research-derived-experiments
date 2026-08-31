from __future__ import annotations

import json

import pytest

from src.evidence.manifest import Manifest, load_manifest

_VALID_FIELDS = {
    "source": "hgnc.test",
    "source_url": "https://example.invalid/hgnc",
    "retrieved_at": "2026-01-01T00:00:00Z",
    "license": "CC0",
    "sha256": "0" * 64,
    "row_count": 3,
    "preprocessing_cmd": "scripts/build_hgnc.py",
    "schema_version": "0.1.0",
}


def test_load_manifest_json_happy_path(tmp_path):
    path = tmp_path / "hgnc.json"
    path.write_text(json.dumps(_VALID_FIELDS), encoding="utf-8")

    manifest = load_manifest(path)

    assert isinstance(manifest, Manifest)
    assert manifest.source == "hgnc.test"
    assert manifest.source_url == "https://example.invalid/hgnc"
    assert manifest.retrieved_at == "2026-01-01T00:00:00Z"
    assert manifest.license == "CC0"
    assert manifest.sha256 == "0" * 64
    assert manifest.row_count == 3
    assert manifest.preprocessing_cmd == "scripts/build_hgnc.py"
    assert manifest.schema_version == "0.1.0"


def test_load_manifest_json_preprocessing_cmd_may_be_null(tmp_path):
    fields = dict(_VALID_FIELDS)
    fields["preprocessing_cmd"] = None
    path = tmp_path / "hgnc.json"
    path.write_text(json.dumps(fields), encoding="utf-8")

    manifest = load_manifest(path)

    assert manifest.preprocessing_cmd is None


def test_load_manifest_yaml_happy_path(tmp_path):
    pytest.importorskip("yaml")
    # JSON is a subset of YAML, so a JSON body under a .yaml extension
    # exercises the yaml.safe_load code path without needing real YAML
    # syntax in the fixture.
    path = tmp_path / "hgnc.yaml"
    path.write_text(json.dumps(_VALID_FIELDS), encoding="utf-8")

    manifest = load_manifest(path)

    assert manifest.source == "hgnc.test"
    assert manifest.sha256 == "0" * 64


def test_load_manifest_missing_required_field_raises(tmp_path):
    fields = dict(_VALID_FIELDS)
    del fields["sha256"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(fields), encoding="utf-8")

    with pytest.raises(ValueError):
        load_manifest(path)


def test_load_manifest_wrong_type_raises(tmp_path):
    fields = dict(_VALID_FIELDS)
    fields["row_count"] = "not-an-int"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(fields), encoding="utf-8")

    with pytest.raises(ValueError):
        load_manifest(path)


def test_load_manifest_unsupported_extension_raises(tmp_path):
    path = tmp_path / "hgnc.txt"
    path.write_text(json.dumps(_VALID_FIELDS), encoding="utf-8")

    with pytest.raises(ValueError):
        load_manifest(path)


def test_load_manifest_yaml_without_pyyaml_raises_cleanly(tmp_path):
    import src.evidence.manifest as manifest_module

    if manifest_module._HAVE_YAML:
        pytest.skip("pyyaml is importable in this environment; nothing to exercise here")

    path = tmp_path / "hgnc.yaml"
    path.write_text("source: hgnc.test", encoding="utf-8")

    with pytest.raises(ValueError):
        load_manifest(path)
