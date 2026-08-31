"""Shared fixtures for tests/rules/.

`bundle` builds a hash-verified `evidence.SnapshotBundle` from a
*repaired* tmp copy of `tests/fixtures/synthetic_world`.

# RULES-DECISION: `tests/fixtures/synthetic_world` is authored in a shape
# `src/evidence/loader.py` cannot ingest byte-for-byte, in ways this task
# is not allowed to fix at the source (only `bio-claim-firewall/src/
# rules/` and `bio-claim-firewall/tests/rules/` are in scope). Every gap
# below was independently confirmed against `src/evidence/*` before
# writing this file:
#
#   1. Manifests are `.yaml` only, and `pyyaml` is not importable under
#      `uv run --no-sync` (confirmed: `ModuleNotFoundError`). Per the task
#      brief ("add JSON siblings inside conftest.py's tmp-copy of the
#      fixture tree"), we regenerate them as JSON here.
#
#   2. Every manifest's `sha256`, as authored (and as
#      `tests/fixtures/test_fixtures_self_consistent.py` itself verifies),
#      covers exactly one upstream `snapshot_file` -- e.g.
#      `perturbseq_v_test.yaml`'s covers `raw_source.jsonl`, and each
#      ontology manifest's covers its own bare `curies.txt`. But
#      `evidence.loader._load_evidence_source` hashes `records.jsonl`
#      (`sha256_file`) for an evidence source, and
#      `evidence.loader._load_ontology_source` hashes the WHOLE ontology
#      directory (`sha256_dir`: every file inside it, framed and
#      concatenated) for an ontology source -- neither matches what the
#      fixture pack's `sha256` field records, so `load_bundle` would fail
#      closed (`EvidenceError("HASH_MISMATCH")`) on the fixture tree
#      as-is. We recompute every manifest's `sha256`, in this tmp copy,
#      from exactly what `load_bundle` will hash -- using
#      `evidence.hashing`'s own functions, so there is no drift between
#      "what we compute" and "what the loader checks".
#
#   3. Three per-source data files use field names the loader does not
#      recognize:
#        - `ontology_snapshots/*/curies.txt` is `"CURIE\tLabel"` per line;
#          `loader._load_ontology_source` adds the *whole stripped line*
#          to the curies set (it never splits on tab), so every CURIE
#          would silently fail `contains()`/`canonicalize()`. We strip to
#          the bare CURIE column.
#        - `ontology_snapshots/hgnc_v_test/aliases.jsonl` uses keys
#          `deprecated_id`/`current_id`; the loader requires
#          `deprecated`/`canonical` and raises
#          `EvidenceError("HASH_MISMATCH", reason="malformed_alias_row")`
#          otherwise. We rename the keys.
#        - `ontology_snapshots/cellontology_v_test/cell_ontology.jsonl`
#          uses keys `id`/`is_a`; the loader requires `curie`/`ancestors`
#          (same failure mode). We rename them -- the fixture's `is_a`
#          values are already the full transitive closure (see
#          `RECORD_ID_MAP.md`'s sibling data), so no closure computation
#          is needed, just a key rename.
#
# None of the above rewrites any evidence record's *content* (subject,
# object, effect, contradicts, context, etc.) -- only manifest framing and
# ontology-file field names, so every rule-relevant fact the fixture pack
# encodes is preserved exactly. See `src/rules/sections/citations.py`'s
# own RULES-DECISION for a fourth, evidence-record-level gap this repair
# cannot and does not paper over (R-CITE-02's snapshot_hash semantics).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from evidence import load_bundle
from evidence.hashing import sha256_dir, sha256_file
from evidence.snapshot import SnapshotBundle
from normalize import normalize_claim

from rules import RuleEngine

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SYNTH_SRC = FIXTURES / "synthetic_world"
CLAIMS_DIR = FIXTURES / "claims"


def _parse_flat_manifest(path: Path) -> dict[str, str]:
    """Parse the fixture pack's flat `key: value` manifest lines (no pyyaml)."""
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        out[key] = value
    return out


def _fix_curies_txt(path: Path) -> None:
    lines = [ln.strip() for ln in path.read_text().splitlines() if ln.strip()]
    curies = [ln.split("\t", 1)[0] for ln in lines]
    path.write_text("\n".join(curies) + "\n", encoding="utf-8")


def _fix_aliases_jsonl(path: Path) -> None:
    if not path.is_file():
        return
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        rows.append({"deprecated": row["deprecated_id"], "canonical": row["current_id"]})
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _fix_cell_ontology_jsonl(path: Path) -> None:
    if not path.is_file():
        return
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        rows.append({"curie": row["id"], "ancestors": row["is_a"]})
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def _build_repaired_data_root(tmp_path: Path) -> Path:
    root = tmp_path / "synthetic_world"
    shutil.copytree(SYNTH_SRC, root)

    onto_root = root / "ontology_snapshots"
    for source_dir in sorted(p for p in onto_root.iterdir() if p.is_dir()):
        curies_path = source_dir / "curies.txt"
        if curies_path.is_file():
            _fix_curies_txt(curies_path)
        _fix_aliases_jsonl(source_dir / "aliases.jsonl")
        _fix_cell_ontology_jsonl(source_dir / "cell_ontology.jsonl")

    manifests_dir = root / "manifests"
    for yaml_path in sorted(manifests_dir.glob("*.yaml")):
        fields = _parse_flat_manifest(yaml_path)
        source = fields["source"]
        onto_source_dir = onto_root / source
        evidence_file = root / "evidence_records" / source / "records.jsonl"

        if onto_source_dir.is_dir():
            sha256 = sha256_dir(onto_source_dir)
        elif evidence_file.is_file():
            sha256 = sha256_file(evidence_file)
        else:  # pragma: no cover - guards fixture-pack drift, not exercised today
            raise AssertionError(f"conftest repair: no ontology dir or evidence file for source {source!r}")

        manifest = {
            "source": source,
            "source_url": fields["source_url"],
            "retrieved_at": fields["retrieved_at"],
            "license": fields["license"],
            "sha256": sha256,
            "row_count": int(fields["row_count"]),
            "preprocessing_cmd": fields.get("preprocessing_cmd"),
            "schema_version": fields["schema_version"],
        }
        (manifests_dir / f"{source}.json").write_text(json.dumps(manifest), encoding="utf-8")
        yaml_path.unlink()

    return root


@pytest.fixture
def bundle(tmp_path: Path) -> SnapshotBundle:
    """A hash-verified `SnapshotBundle` over a repaired copy of the synthetic world."""
    data_root = _build_repaired_data_root(tmp_path)
    return load_bundle(data_root)


# RULES-DECISION: helpers below are exposed as pytest *fixtures* (factory
# functions returned from a fixture), not as plain module-level functions
# meant to be imported with `from conftest import ...`. This repo already
# has a top-level `bio-claim-firewall/conftest.py`; a second file also
# named `conftest.py` (this one) makes a bare `import conftest` /
# `from conftest import ...` from a test module ambiguous under pytest's
# default (no-`__init__.py`) import mode. Fixtures don't have that
# problem -- pytest resolves them by directory scope regardless of the
# file's module name -- so every test in this package requests these by
# fixture name instead.


@pytest.fixture
def load_claim():
    """Fixture factory: `load_claim("BAD_CITATION__invalid.json") -> dict`."""

    def _load(name: str) -> dict[str, Any]:
        return json.loads((CLAIMS_DIR / name).read_text(encoding="utf-8"))

    return _load


@pytest.fixture
def expectations() -> list[dict[str, Any]]:
    """Every entry of `tests/fixtures/expectations.jsonl`, in file order."""
    entries: list[dict[str, Any]] = []
    for line in (FIXTURES / "expectations.jsonl").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))
    return entries


@pytest.fixture
def run_claim(bundle: SnapshotBundle, load_claim):
    """Fixture factory: normalize + run one named claim fixture through `RuleEngine`.

    `run_claim("BAD_CITATION__invalid.json") -> RuleResult`. Raises
    `NormalizationError` uncaught for a claim whose own entities don't
    resolve (e.g. `UNKNOWN_ENTITY__invalid.json`) -- that failure happens
    before a `CanonicalClaim`/`RuleEngine.run()` call is even possible; see
    `test_r_ent.py` for how that specific fixture is exercised instead.
    """

    def _run(name: str, checker_version: str = "0.1.0"):
        claim_dict = load_claim(name)
        canonical = normalize_claim(claim_dict, bundle)
        engine = RuleEngine(bundle, checker_version=checker_version)
        return engine.run(canonical)

    return _run
