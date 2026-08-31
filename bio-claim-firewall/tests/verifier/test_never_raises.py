"""Feed verify() garbage. It must always return a schema-conformant
CHECKER_ERROR (or, incidentally, some other valid verdict) dict -- never
raise.
"""

from __future__ import annotations

import pytest

from verifier import verify


GARBAGE_CLAIMS = [
    {},
    None,
    "just a plain string",
    12345,
    3.14,
    [],
    [1, 2, 3],
    True,
    {"claim_id": None},
    {"claim_id": 12345},
    {"claim_id": "not-a-uuid"},
    {"claim_id": "11111111-1111-4111-8111-111111111111"},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "subject": None},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "subject": "not-a-dict"},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "subject": {"id": None, "label": None}},
    {"nested": {"a": {"b": {"c": {"d": [1, 2, {"e": "f"}]}}}}},
    {"claim_id": "x" * 100000},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "evidence_ids": "not-a-list"},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "evidence_ids": [1, 2, 3]},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "polarity": float("nan")},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "polarity": float("inf")},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "extra": {1, 2, 3}},
    {"claim_id": "11111111-1111-4111-8111-111111111111", "extra": object()},
    {i: i for i in range(500)},
]


def _make_deeply_nested(depth: int) -> dict:
    node: dict = {"leaf": True}
    for _ in range(depth):
        node = {"nested": node}
    return node


GARBAGE_CLAIMS.append(_make_deeply_nested(2000))


@pytest.mark.parametrize("garbage", GARBAGE_CLAIMS, ids=lambda g: repr(g)[:60])
def test_never_raises_on_garbage(bundle, config, garbage, assert_verdict_matches_schema):
    verdict = verify(garbage, bundle, config)
    assert isinstance(verdict, dict)
    assert_verdict_matches_schema(verdict)


def test_never_raises_on_huge_string_claim_id(bundle, config, assert_verdict_matches_schema):
    verdict = verify({"claim_id": "z" * 1_000_000}, bundle, config)
    assert isinstance(verdict, dict)
    assert_verdict_matches_schema(verdict)


def test_never_raises_when_snapshot_is_garbage(config, assert_verdict_matches_schema):
    verdict = verify({"claim_id": "11111111-1111-4111-8111-111111111111"}, object(), config)
    assert isinstance(verdict, dict)
    assert_verdict_matches_schema(verdict)


def test_never_raises_when_snapshot_is_none(config, assert_verdict_matches_schema):
    verdict = verify({"claim_id": "11111111-1111-4111-8111-111111111111"}, None, config)
    assert isinstance(verdict, dict)
    assert_verdict_matches_schema(verdict)
