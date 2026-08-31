"""Self-consistency guardrail for the tests/fixtures/ pack itself.

This is not a test of the (not-yet-built, Phase 3) verifier. It is a test
that the *fixture pack* -- the synthetic frozen world, the per-fault-code
claim library, and expectations.jsonl -- is internally coherent, so the
Phase 5 mechanical verifier suite can be built against it with confidence.

Run:
    cd bio-claim-firewall && uv run --no-sync python -m pytest tests/fixtures/ -q
    # or, if the above environment lacks third-party packages:
    cd bio-claim-firewall && python3 -m pytest tests/fixtures/ -q
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent          # .../bio-claim-firewall/tests/fixtures
SYNTH_DIR = FIXTURES_DIR / "synthetic_world"
CLAIMS_DIR = FIXTURES_DIR / "claims"
SPEC_DIR = FIXTURES_DIR.parent.parent / "spec"           # .../bio-claim-firewall/spec
EXPECTATIONS_PATH = FIXTURES_DIR / "expectations.jsonl"

MANIFESTS_DIR = SYNTH_DIR / "manifests"
PERTURBSEQ_DIR = SYNTH_DIR / "evidence_records" / "perturbseq_v_test"
RECORDS_PATH = PERTURBSEQ_DIR / "records.jsonl"
RAW_SOURCE_PATH = PERTURBSEQ_DIR / "raw_source.jsonl"


def _load_json(path: Path):
    return json.loads(path.read_text())


CLAIM_SCHEMA = _load_json(SPEC_DIR / "claim.schema.json")
EVIDENCE_SCHEMA_RAW = _load_json(SPEC_DIR / "evidence.schema.json")
VERDICT_SCHEMA = _load_json(SPEC_DIR / "verdict.schema.json")


def _inline_local_refs(node, defs_source):
    """Replace {"$ref": "claim.schema.json#/$defs/X"} with the actual
    definition, so we never need a multi-file $ref resolver (works
    identically whether we validate with `jsonschema` or the minimal
    fallback below)."""
    if isinstance(node, dict):
        if set(node.keys()) == {"$ref"} and isinstance(node["$ref"], str) \
                and node["$ref"].startswith("claim.schema.json#/$defs/"):
            def_name = node["$ref"].rsplit("/", 1)[-1]
            return copy.deepcopy(defs_source["$defs"][def_name])
        return {k: _inline_local_refs(v, defs_source) for k, v in node.items()}
    if isinstance(node, list):
        return [_inline_local_refs(v, defs_source) for v in node]
    return node


EVIDENCE_SCHEMA = _inline_local_refs(copy.deepcopy(EVIDENCE_SCHEMA_RAW), CLAIM_SCHEMA)

# ---------------------------------------------------------------------------
# Schema validator: real `jsonschema` when importable, else a minimal
# hand-rolled structural validator.
#
# FIXTURES-DECISION: `uv run --no-sync python3 -m pytest ...` (the primary
# command this file's module docstring documents) runs in an environment
# where `jsonschema` is NOT importable (verified: `ModuleNotFoundError`
# under `uv run --no-sync`, but importable under plain `python3`). Per the
# task instructions, pyproject.toml/uv.lock are not to be touched to add
# it. So this file tries `import jsonschema` and falls back to a minimal
# validator covering exactly the JSON Schema keywords claim.schema.json /
# evidence.schema.json actually use (type incl. union types, enum, const,
# pattern, required, additionalProperties, items/minItems/uniqueItems,
# minLength, format for "uuid"/"date-time"). It does not implement
# oneOf/allOf/if-then (verdict.schema.json uses allOf/if-then, but this
# file never needs to validate a Verdict instance -- only claim and
# evidence instances, which don't use those keywords).
# ---------------------------------------------------------------------------
try:
    import jsonschema  # type: ignore
    _HAVE_JSONSCHEMA = True
except ImportError:
    _HAVE_JSONSCHEMA = False


_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

_PY_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def _instance_matches_type(instance, type_name: str) -> bool:
    if type_name == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if type_name == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if type_name == "boolean":
        return isinstance(instance, bool)
    py_t = _PY_TYPES.get(type_name)
    if py_t is None:
        raise AssertionError(f"minimal validator: unhandled type {type_name!r}")
    if type_name in ("object", "array", "null"):
        return isinstance(instance, py_t)
    if type_name == "string":
        return isinstance(instance, str)
    return isinstance(instance, py_t)


def _minimal_validate(instance, schema, path: str = "$") -> None:
    if "const" in schema:
        assert instance == schema["const"], f"{path}: expected const {schema['const']!r}, got {instance!r}"
    if "enum" in schema:
        assert instance in schema["enum"], f"{path}: {instance!r} not in enum {schema['enum']!r}"
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        assert any(_instance_matches_type(instance, t) for t in types), (
            f"{path}: {instance!r} does not match type(s) {types}"
        )
    if "pattern" in schema and isinstance(instance, str):
        assert re.search(schema["pattern"], instance), (
            f"{path}: {instance!r} does not match pattern {schema['pattern']!r}"
        )
    if "minLength" in schema and isinstance(instance, str):
        assert len(instance) >= schema["minLength"], f"{path}: shorter than minLength"
    if "format" in schema and isinstance(instance, str):
        fmt = schema["format"]
        if fmt == "uuid":
            assert _UUID_RE.match(instance), f"{path}: {instance!r} is not a uuid"
        elif fmt == "date-time":
            assert _DATETIME_RE.match(instance), f"{path}: {instance!r} is not a date-time"
    if isinstance(instance, dict) and ("properties" in schema or schema.get("type") == "object"):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            assert req in instance, f"{path}: missing required property {req!r}"
        if schema.get("additionalProperties") is False:
            extra = set(instance.keys()) - set(props.keys())
            assert not extra, f"{path}: additional properties not allowed: {sorted(extra)}"
        for k, v in instance.items():
            if k in props:
                _minimal_validate(v, props[k], f"{path}.{k}")
    if isinstance(instance, list) and schema.get("type") == "array":
        if "minItems" in schema:
            assert len(instance) >= schema["minItems"], f"{path}: fewer than minItems"
        if schema.get("uniqueItems"):
            seen = [json.dumps(x, sort_keys=True) for x in instance]
            assert len(seen) == len(set(seen)), f"{path}: items not unique"
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(instance):
                _minimal_validate(item, items_schema, f"{path}[{i}]")


def validate_instance(instance, schema) -> None:
    """Raises an AssertionError (minimal) or jsonschema.ValidationError
    (real) if `instance` does not conform to `schema`."""
    if _HAVE_JSONSCHEMA:
        jsonschema.validate(instance=instance, schema=schema)
    else:
        _minimal_validate(instance, schema)


def is_schema_valid(instance, schema) -> bool:
    try:
        validate_instance(instance, schema)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Import recompute_hashes.py as a module (pure stdlib, side-effect-free on
# import -- `main()` only runs under `if __name__ == "__main__"`) so the
# hash/id derivation logic is exercised from a single source of truth
# rather than re-implemented here and risking drift.
# ---------------------------------------------------------------------------
_spec = importlib.util.spec_from_file_location(
    "synthetic_world_recompute_hashes", SYNTH_DIR / "recompute_hashes.py"
)
recompute_hashes = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = recompute_hashes
_spec.loader.exec_module(recompute_hashes)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Fixture data loading
# ---------------------------------------------------------------------------

MANIFEST_LINE_RE = re.compile(r'^([a-zA-Z0-9_]+):\s*(.*)$')


def _parse_flat_manifest(path: Path) -> dict:
    """Parses the flat `key: value` manifest format written by this fixture
    pack (see synthetic_world/manifests/*.yaml). Strips surrounding quotes
    from scalar values. Not a general YAML parser -- these manifests are
    deliberately flat so both this test and recompute_hashes.py can avoid
    a PyYAML dependency."""
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = MANIFEST_LINE_RE.match(line)
        assert m, f"{path}: could not parse manifest line: {line!r}"
        key, value = m.group(1), m.group(2).strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        out[key] = value
    return out


REQUIRED_MANIFEST_FIELDS = {
    "source", "source_url", "retrieved_at", "license", "sha256",
    "row_count", "preprocessing_cmd", "schema_version",
}


def _all_manifests() -> dict[str, dict]:
    return {p.name: _parse_flat_manifest(p) for p in sorted(MANIFESTS_DIR.glob("*.yaml"))}


def _all_claim_files() -> list[Path]:
    return sorted(CLAIMS_DIR.glob("*.json"))


def _load_evidence_records() -> list[dict]:
    records = []
    for line in RECORDS_PATH.read_text().splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _load_expectations() -> list[dict]:
    entries = []
    for line in EXPECTATIONS_PATH.read_text().splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


CLOSED_FAULT_CODES = sorted(
    c for c in VERDICT_SCHEMA["properties"]["fault_code"]["enum"] if c is not None
)

# The one claim fixture that is intentionally NOT valid Claim JSON --
# see INVALID_RELATION__invalid.json and its note in expectations.jsonl.
# Documented here (not just there) so this is the single source of truth
# a reader checks when a "why does this fail schema validation" question
# comes up.
KNOWN_SCHEMA_INVALID_CLAIMS = {"INVALID_RELATION__invalid.json"}

# The one claim fixture whose evidence_ids are EXPECTED not to resolve.
KNOWN_BAD_CITATION_CLAIMS = {"BAD_CITATION__invalid.json"}


# ---------------------------------------------------------------------------
# 1. Claim files are schema-valid (except the documented exception).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("claim_path", _all_claim_files(), ids=lambda p: p.name)
def test_claim_files_schema_valid(claim_path: Path):
    if claim_path.name in KNOWN_SCHEMA_INVALID_CLAIMS:
        pytest.skip(f"{claim_path.name} is a documented KNOWN_SCHEMA_INVALID fixture "
                    f"(see test_known_schema_invalid_claims_are_actually_invalid)")
    instance = _load_json(claim_path)
    validate_instance(instance, CLAIM_SCHEMA)


def test_known_schema_invalid_claims_are_actually_invalid():
    """Guards against KNOWN_SCHEMA_INVALID_CLAIMS silently going stale
    (e.g. someone "fixes" the file so it becomes schema-valid without
    updating the documented exception set)."""
    assert KNOWN_SCHEMA_INVALID_CLAIMS, "expected at least one documented schema-invalid claim"
    for name in KNOWN_SCHEMA_INVALID_CLAIMS:
        path = CLAIMS_DIR / name
        assert path.is_file(), f"{name} listed as schema-invalid but file does not exist"
        instance = _load_json(path)
        assert not is_schema_valid(instance, CLAIM_SCHEMA), (
            f"{name} was expected to FAIL claim.schema.json validation (that's its whole "
            f"point -- it demonstrates INVALID_RELATION firing at the schema/parse layer) "
            f"but it validated successfully. Either the file was fixed and should be moved "
            f"out of KNOWN_SCHEMA_INVALID_CLAIMS, or the schema changed."
        )


# ---------------------------------------------------------------------------
# 2. Evidence records are schema-valid.
# ---------------------------------------------------------------------------

def test_evidence_records_schema_valid():
    records = _load_evidence_records()
    assert len(records) == 6, f"expected exactly 6 perturbseq_v_test records, found {len(records)}"
    for i, record in enumerate(records):
        validate_instance(record, EVIDENCE_SCHEMA)


# ---------------------------------------------------------------------------
# 3. Every manifest's sha256 equals the sha256 of the file it references.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("manifest_path", sorted(MANIFESTS_DIR.glob("*.yaml")), ids=lambda p: p.name)
def test_manifest_has_required_fields(manifest_path: Path):
    fields = _parse_flat_manifest(manifest_path)
    missing = REQUIRED_MANIFEST_FIELDS - set(fields.keys())
    assert not missing, f"{manifest_path.name}: missing required manifest fields {missing}"
    assert fields["sha256"] != "TBD", f"{manifest_path.name}: sha256 was never computed"
    assert re.match(r"^[0-9a-f]{64}$", fields["sha256"]), f"{manifest_path.name}: sha256 is not 64 hex chars"


@pytest.mark.parametrize("manifest_path", sorted(MANIFESTS_DIR.glob("*.yaml")), ids=lambda p: p.name)
def test_manifest_sha256_matches_referenced_file(manifest_path: Path):
    fields = _parse_flat_manifest(manifest_path)
    snapshot_path = SYNTH_DIR / fields["snapshot_file"]
    assert snapshot_path.is_file(), f"{manifest_path.name}: snapshot_file {fields['snapshot_file']} does not exist"
    actual = recompute_hashes.sha256_file(snapshot_path)
    assert actual == fields["sha256"], (
        f"{manifest_path.name}: manifest sha256 {fields['sha256']} does not match actual "
        f"sha256 of {fields['snapshot_file']} ({actual}). Run "
        f"synthetic_world/recompute_hashes.py to fix."
    )


# ---------------------------------------------------------------------------
# 4. Every evidence record's snapshot_hash matches its manifest's sha256,
#    and records.jsonl is byte-for-byte what recompute_hashes.py would
#    regenerate from raw_source.jsonl (catches any hand-edit drift).
# ---------------------------------------------------------------------------

def test_evidence_snapshot_hash_matches_manifest():
    manifests = _all_manifests()
    perturbseq_sha256 = manifests["perturbseq_v_test.yaml"]["sha256"]
    for record in _load_evidence_records():
        assert record["snapshot_hash"] == perturbseq_sha256, (
            f"{record['evidence_id']}: snapshot_hash {record['snapshot_hash']} != "
            f"manifests/perturbseq_v_test.yaml sha256 {perturbseq_sha256}"
        )


def test_records_jsonl_matches_recomputation_from_raw_source():
    manifests = _all_manifests()
    raw_sha256 = manifests["perturbseq_v_test.yaml"]["sha256"]
    assert raw_sha256 == recompute_hashes.sha256_file(RAW_SOURCE_PATH), (
        "manifest sha256 does not match current raw_source.jsonl -- run recompute_hashes.py"
    )
    rebuilt = [record for _label, record in recompute_hashes.build_perturbseq_records(raw_sha256)]
    on_disk = _load_evidence_records()
    assert rebuilt == on_disk, (
        "records.jsonl does not match what recompute_hashes.py derives from raw_source.jsonl "
        "-- someone hand-edited one without the other, or without re-running the script."
    )
    # And every evidence_id really is source:sha256(...)[:16] of the record minus its own id.
    for record in on_disk:
        without_id = {k: v for k, v in record.items() if k != "evidence_id"}
        expected_hash = recompute_hashes.canonical_json(without_id)
        import hashlib
        expected_id = f"{record['source']}:{hashlib.sha256(expected_hash.encode()).hexdigest()[:16]}"
        assert record["evidence_id"] == expected_id, (
            f"evidence_id {record['evidence_id']} is not sha256(canonical record minus id)[:16] "
            f"-- got {expected_id} instead. Hashes must be REAL, not hardcoded."
        )


# ---------------------------------------------------------------------------
# 5. Every evidence_ids reference in a claim resolves to a real record,
#    except BAD_CITATION__invalid.json, which must NOT resolve.
# ---------------------------------------------------------------------------

def _real_evidence_ids() -> set[str]:
    return {r["evidence_id"] for r in _load_evidence_records()}


@pytest.mark.parametrize("claim_path", _all_claim_files(), ids=lambda p: p.name)
def test_claim_evidence_ids_resolve_or_are_known_bad(claim_path: Path):
    instance = _load_json(claim_path)
    real_ids = _real_evidence_ids()
    cited = instance["evidence_ids"]
    assert cited, f"{claim_path.name}: evidence_ids must be non-empty"

    if claim_path.name in KNOWN_BAD_CITATION_CLAIMS:
        unresolved = [e for e in cited if e not in real_ids]
        assert unresolved, (
            f"{claim_path.name} is documented as a BAD_CITATION fixture (a fabricated "
            f"evidence_id) but every cited id actually resolves -- this defeats the "
            f"fixture's purpose."
        )
    else:
        unresolved = [e for e in cited if e not in real_ids]
        assert not unresolved, (
            f"{claim_path.name}: evidence_ids {unresolved} do not resolve to any record "
            f"in records.jsonl. If this is deliberate (a new BAD_CITATION-style fixture), "
            f"add it to KNOWN_BAD_CITATION_CLAIMS."
        )


# ---------------------------------------------------------------------------
# 6. expectations.jsonl covers every fault code plus INCONCLUSIVE and
#    ACCEPTED_CONDITIONALLY, and stays in sync with claims/.
# ---------------------------------------------------------------------------

def test_expectations_reference_existing_claim_files():
    for entry in _load_expectations():
        claim_path = FIXTURES_DIR / entry["claim_path"]
        assert claim_path.is_file(), f"expectations.jsonl references missing file {entry['claim_path']}"


def test_every_claim_file_has_an_expectations_entry():
    expected_paths = {entry["claim_path"] for entry in _load_expectations()}
    for claim_path in _all_claim_files():
        rel = f"claims/{claim_path.name}"
        assert rel in expected_paths, f"{rel} has no corresponding entry in expectations.jsonl"


def test_expectations_cover_every_fault_code():
    entries = _load_expectations()
    covered_codes = {e["expected_fault_code"] for e in entries if e.get("expected_fault_code")}
    missing = set(CLOSED_FAULT_CODES) - covered_codes
    assert not missing, (
        f"expectations.jsonl is missing REJECTED coverage for fault code(s): {sorted(missing)}. "
        f"Every fault code in verdict.schema.json's closed enum needs at least one "
        f"REJECTED expectation."
    )


def test_expectations_cover_inconclusive_and_accepted_conditionally():
    entries = _load_expectations()
    verdicts_present = {e["expected_verdict"] for e in entries}
    assert "INCONCLUSIVE" in verdicts_present, "expectations.jsonl has no INCONCLUSIVE entry"
    assert "ACCEPTED_CONDITIONALLY" in verdicts_present, (
        "expectations.jsonl has no ACCEPTED_CONDITIONALLY entry"
    )


def test_rejected_expectations_have_fault_code_and_valid_verdict_enum():
    entries = _load_expectations()
    verdict_enum = set(VERDICT_SCHEMA["properties"]["verdict"]["enum"])
    for entry in entries:
        assert entry["expected_verdict"] in verdict_enum, (
            f"{entry['claim_path']}: expected_verdict {entry['expected_verdict']!r} not in "
            f"verdict.schema.json's verdict enum"
        )
        if entry["expected_verdict"] == "REJECTED":
            assert entry.get("expected_fault_code") in CLOSED_FAULT_CODES, (
                f"{entry['claim_path']}: REJECTED entry must carry a valid expected_fault_code"
            )


# ---------------------------------------------------------------------------
# 7. Every fault code in the taxonomy has at least one adversarial
#    (<code>__invalid.json) fixture on disk -- the guardrail against
#    silently forgetting to test a code.
# ---------------------------------------------------------------------------

def test_every_fault_code_has_an_adversarial_fixture():
    existing = {p.name for p in _all_claim_files()}
    missing = []
    for code in CLOSED_FAULT_CODES:
        if f"{code}__invalid.json" not in existing:
            missing.append(code)
    assert not missing, f"No <code>__invalid.json fixture for fault code(s): {missing}"


def test_every_fault_code_has_a_positive_control_fixture():
    existing = {p.name for p in _all_claim_files()}
    missing = []
    for code in CLOSED_FAULT_CODES:
        if f"{code}__valid.json" not in existing:
            missing.append(code)
    assert not missing, f"No <code>__valid.json positive control for fault code(s): {missing}"


def test_inconclusive_and_accepted_conditionally_examples_exist():
    existing = {p.name for p in _all_claim_files()}
    assert "INCONCLUSIVE__example.json" in existing
    assert "ACCEPTED_CONDITIONALLY__example.json" in existing


# ---------------------------------------------------------------------------
# 8. Sanity: claim_id values are unique across the whole fixture pack, and
#    entity CURIEs used by claims that are NOT UNKNOWN_ENTITY-style
#    fixtures actually resolve in the frozen ontology snapshots (a
#    tighter check than schema validation, which only checks CURIE shape).
# ---------------------------------------------------------------------------

def test_claim_ids_are_unique():
    seen = {}
    for claim_path in _all_claim_files():
        instance = _load_json(claim_path)
        cid = instance["claim_id"]
        assert cid not in seen, f"claim_id {cid} reused by both {seen[cid]} and {claim_path.name}"
        seen[cid] = claim_path.name


def _known_hgnc_ids() -> set[str]:
    lines = (SYNTH_DIR / "ontology_snapshots" / "hgnc_v_test" / "curies.txt").read_text().splitlines()
    return {line.split("\t")[0] for line in lines if line.strip()}


def test_non_unknown_entity_claims_use_resolvable_hgnc_ids():
    known = _known_hgnc_ids()
    for claim_path in _all_claim_files():
        if claim_path.name == "UNKNOWN_ENTITY__invalid.json":
            continue  # deliberately cites an unresolvable HGNC id
        if claim_path.name in KNOWN_SCHEMA_INVALID_CLAIMS:
            continue
        instance = _load_json(claim_path)
        for role in ("subject", "object"):
            entity = instance[role]
            if entity["id"].startswith("HGNC:"):
                assert entity["id"] in known, (
                    f"{claim_path.name}: {role}.id {entity['id']!r} is not in the frozen "
                    f"hgnc_v_test snapshot (and this isn't the UNKNOWN_ENTITY fixture)"
                )
