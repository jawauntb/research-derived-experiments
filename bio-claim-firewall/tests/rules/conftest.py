"""Shared fixtures for tests/rules/.

`bundle` builds a hash-verified `evidence.SnapshotBundle` directly from
`tests/fixtures/synthetic_world` -- no repaired tmp copy needed. The
fixture pack under `tests/fixtures/synthetic_world/` is byte-format
compatible with `src/evidence/loader.py` (bare `curies.txt`, the loader's
own `aliases.jsonl`/`cell_ontology.jsonl` field names, manifest `sha256`s
that cover exactly what `load_bundle` hashes, and both `.yaml` and `.json`
manifest siblings so this loads even where `pyyaml` is not importable
under `uv run --no-sync`); see `tests/fixtures/synthetic_world/
recompute_hashes.py` and `tests/fixtures/test_fixtures_self_consistent.py`
for how that's kept true.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evidence import load_bundle
from evidence.snapshot import SnapshotBundle
from normalize import normalize_claim

from rules import RuleEngine

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SYNTH_SRC = FIXTURES / "synthetic_world"
CLAIMS_DIR = FIXTURES / "claims"


@pytest.fixture
def bundle() -> SnapshotBundle:
    """A hash-verified `SnapshotBundle` over `tests/fixtures/synthetic_world`.

    `load_bundle` itself picks whichever manifest suffix it can parse for
    each source (`.yaml`/`.yml` when `pyyaml` is importable, `.json`
    otherwise) -- no per-test branching needed here.
    """
    return load_bundle(SYNTH_SRC)


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
