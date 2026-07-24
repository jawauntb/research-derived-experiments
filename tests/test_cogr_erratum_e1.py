"""Regression tests for erratum E1 — the inverted-oracle leak and its repair.

These pin the finding itself, so that a future fixture change which
reintroduces the leak fails loudly rather than silently restoring a perfect
one-line policy.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.template_split import TemplateBucket
from experiments.concern_gated_retrieval_e2.wave1b.families import (
    delayed_commitments_v2 as family,
)

from experiments.concern_gated_retrieval_e2.erratum_e1.inverted_signal_audit import (
    ORACLE_LEAK_THRESHOLD,
    audit_care_anchors,
    audit_signal,
    format_audit_table,
)
from experiments.concern_gated_retrieval_e2.erratum_e1.prior_repair import (
    repair_wrong_prior,
    suppressed_set,
)


SEEDS = range(100_000, 100_120)


def _episodes():
    return [
        family.generate_episode(seed=s, bucket=TemplateBucket.CALIBRATION)
        for s in SEEDS
    ]


def test_the_leak_is_real_and_inverted() -> None:
    """The defect this erratum records: ascending concern is a perfect oracle."""
    row = audit_care_anchors(_episodes())

    assert row.ascending_hit_at_1 == pytest.approx(1.0), (
        "ascending care_anchors should identify the answer in every episode; "
        f"got {row.ascending_hit_at_1}"
    )
    assert row.descending_hit_at_1 == pytest.approx(0.0)
    assert row.leaks
    assert "INVERTED" in row.direction


def test_repair_closes_the_leak() -> None:
    repaired = [repair_wrong_prior(e, k=4) for e in _episodes()]
    row = audit_care_anchors(repaired)

    assert not row.leaks, f"repaired prior still leaks: {row}"
    assert row.worst < ORACLE_LEAK_THRESHOLD


def test_repair_preserves_everything_except_the_prior() -> None:
    for episode in _episodes()[:20]:
        repaired = repair_wrong_prior(episode, k=4)
        assert repaired.episode_id == episode.episode_id
        assert repaired.candidate_nodes == episode.candidate_nodes
        assert repaired.context_nodes == episode.context_nodes
        assert repaired._answer_key == episode._answer_key
        assert dict(repaired.role) == dict(episode.role)
        assert dict(repaired.utility) == dict(episode.utility)
        assert dict(repaired.care_anchors) != dict(episode.care_anchors)


def test_suppressed_set_contains_the_answer_and_non_answers() -> None:
    for episode in _episodes()[:20]:
        chosen = suppressed_set(episode, k=4)
        answer = set(episode._answer_key)
        assert len(chosen) >= 2, "a single-element suppressed set is the defect"
        assert answer & set(chosen), "the load-bearing node must stay suppressed"
        assert set(chosen) - answer, "the set must also contain non-answers"


def test_suppressed_set_is_deterministic() -> None:
    episode = family.generate_episode(seed=100_000, bucket=TemplateBucket.CALIBRATION)
    assert suppressed_set(episode, k=4) == suppressed_set(episode, k=4)


def test_audit_detects_a_planted_forward_leak() -> None:
    """The gate must catch a non-inverted leak too, not just the inverted one."""
    episodes = _episodes()

    def oracle_signal(episode):
        answer = set(episode._answer_key)
        return {c: (1.0 if c in answer else 0.0) for c in episode.candidate_nodes}

    row = audit_signal(episodes, oracle_signal, name="planted_oracle")

    assert row.descending_hit_at_1 == pytest.approx(1.0)
    assert row.leaks
    assert row.direction == "descending"


def test_format_audit_table_renders_rows() -> None:
    text = format_audit_table([audit_care_anchors(_episodes())])
    assert "care_anchors" in text
    assert "LEAK" in text
