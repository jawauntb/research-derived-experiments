"""verdict_id stability: same inputs -> same id; different inputs -> different id."""

from __future__ import annotations

import copy

from verifier import VerifierConfig, verify


def test_same_claim_same_snapshot_same_checker_version_same_id(bundle, config, load_claim):
    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")

    v1 = verify(copy.deepcopy(claim), bundle, config)
    v2 = verify(copy.deepcopy(claim), bundle, config)

    assert v1["verdict_id"] == v2["verdict_id"]
    # issued_at is wall-clock and MUST NOT be part of the hashed tuple, so
    # it may legitimately differ between the two calls even though the id
    # doesn't.
    assert v1["verdict"] == v2["verdict"] == "ACCEPTED_CONDITIONALLY"


def test_different_checker_version_different_id(bundle, load_claim):
    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")

    config_a = VerifierConfig(checker_version="0.1.0", schema_dir=_spec_dir())
    config_b = VerifierConfig(checker_version="0.2.0", schema_dir=_spec_dir())

    v1 = verify(copy.deepcopy(claim), bundle, config_a)
    v2 = verify(copy.deepcopy(claim), bundle, config_b)

    assert v1["verdict_id"] != v2["verdict_id"]
    assert v1["checker_version"] != v2["checker_version"]


def test_different_claim_different_id(bundle, config, load_claim):
    claim_a = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    claim_b = load_claim("UNSUPPORTED_EDGE__valid.json")

    v1 = verify(claim_a, bundle, config)
    v2 = verify(claim_b, bundle, config)

    assert v1["verdict_id"] != v2["verdict_id"]


def _spec_dir():
    from pathlib import Path

    return Path(__file__).resolve().parents[2] / "spec"
