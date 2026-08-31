"""Shared fixtures for tests/verifier/.

# VERIFIER-DECISION: the task brief instructed copying `_build_repaired_data_root`
# out of `tests/rules/conftest.py` (which built a repaired tmp copy of
# `tests/fixtures/synthetic_world` to work around fixture/loader format
# mismatches), since `tests/verifier/` can't import a sibling test
# package's `conftest.py` directly (pytest's default no-`__init__.py`
# import mode makes a bare `import conftest` ambiguous across sibling
# test directories -- see that file's own historical explanation in git
# blame). By the time this package was written, the underlying
# fixture/loader mismatch that helper worked around had already been
# fixed at the source (a concurrent, separate task) -- `tests/rules/
# conftest.py`'s current `bundle` fixture loads
# `tests/fixtures/synthetic_world` directly via `evidence.load_bundle`,
# no repair step needed. This file mirrors that CURRENT (simpler)
# pattern rather than the stale repaired-copy one, since matching the
# fixture pack's real, present-day format is what actually keeps this
# package correct.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evidence import load_bundle
from evidence.snapshot import SnapshotBundle

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SYNTH_SRC = FIXTURES / "synthetic_world"
CLAIMS_DIR = FIXTURES / "claims"
SPEC_DIR = FIXTURES.parent.parent / "spec"


@pytest.fixture
def bundle() -> SnapshotBundle:
    """A hash-verified `SnapshotBundle` over `tests/fixtures/synthetic_world`."""
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
def checker_version() -> str:
    return "0.1.0"


@pytest.fixture
def config(bundle: SnapshotBundle, checker_version: str):
    from verifier import VerifierConfig

    return VerifierConfig(checker_version=checker_version, schema_dir=SPEC_DIR)


@pytest.fixture
def verdict_schema() -> dict[str, Any]:
    return json.loads((SPEC_DIR / "verdict.schema.json").read_text(encoding="utf-8"))


@pytest.fixture
def assert_verdict_matches_schema(verdict_schema: dict[str, Any]):
    """Fixture factory: a self-check that a verdict dict conforms to
    spec/verdict.schema.json, including the `allOf`/`if`/`then`
    conditional-required blocks the minimal validator in `src/verifier`
    doesn't need to handle (it only ever validates *claims*, never
    verdicts). Hand-rolled here for the same reason
    `tests/fixtures/test_fixtures_self_consistent.py` hand-rolls one: this
    environment does not have `jsonschema` importable under
    `uv run --no-sync` (confirmed), and pyproject.toml/uv.lock are out of
    scope for this task to change.
    """
    import re

    uuid_re = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    hex32_re = re.compile(r"^[0-9a-f]{32}$")
    hex64_re = re.compile(r"^[0-9a-f]{64}$")
    semver_re = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
    rule_id_re = re.compile(r"^R-[A-Z]+-[0-9]{2}$")
    datetime_re = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    required_top = verdict_schema["required"]
    fault_code_enum = verdict_schema["properties"]["fault_code"]["enum"]
    verdict_enum = verdict_schema["properties"]["verdict"]["enum"]
    stage_enum = verdict_schema["properties"]["checker_error"]["properties"]["stage"]["enum"]

    def _check(verdict: dict[str, Any]) -> None:
        assert isinstance(verdict, dict), "verdict must be a JSON object"
        for key in verdict:
            assert key in verdict_schema["properties"], f"unexpected top-level key {key!r}"
        for req in required_top:
            assert req in verdict, f"missing required top-level key {req!r}"

        assert verdict["schema_version"] == "0.1.0"
        assert hex32_re.match(verdict["verdict_id"]), f"bad verdict_id {verdict['verdict_id']!r}"
        assert uuid_re.match(verdict["claim_id"]), f"bad claim_id {verdict['claim_id']!r}"
        assert verdict["verdict"] in verdict_enum
        assert semver_re.match(verdict["checker_version"])
        assert datetime_re.match(verdict["issued_at"])
        assert isinstance(verdict["snapshot_hashes"], dict)
        for v in verdict["snapshot_hashes"].values():
            assert hex64_re.match(v)

        if "fault_code" in verdict and verdict["fault_code"] is not None:
            assert verdict["fault_code"] in fault_code_enum

        if verdict["verdict"] == "REJECTED":
            assert "fault_code" in verdict and verdict["fault_code"] in fault_code_enum
            assert "reasons" in verdict and isinstance(verdict["reasons"], list) and verdict["reasons"]
            for reason in verdict["reasons"]:
                assert set(reason.keys()) <= {"rule_id", "message", "evidence_id"}
                assert "rule_id" in reason and "message" in reason
                assert rule_id_re.match(reason["rule_id"]), reason["rule_id"]

        if verdict["verdict"] == "ACCEPTED_CONDITIONALLY":
            assert "derivation" in verdict and isinstance(verdict["derivation"], dict)
            derivation = verdict["derivation"]
            assert set(derivation.keys()) == {"evidence_ids", "applied_rules", "conditions"}
            assert derivation["evidence_ids"]
            assert derivation["applied_rules"]
            for rid in derivation["applied_rules"]:
                assert rule_id_re.match(rid), rid

        if verdict["verdict"] == "CHECKER_ERROR":
            assert "checker_error" in verdict and isinstance(verdict["checker_error"], dict)
            checker_error = verdict["checker_error"]
            assert set(checker_error.keys()) <= {"stage", "message", "exception_class"}
            assert checker_error["stage"] in stage_enum
            assert "message" in checker_error

    return _check
