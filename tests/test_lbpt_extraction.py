"""Tests for the deterministic rule-based claim extractor."""

from __future__ import annotations

import pytest

from experiments.load_bearing_prose_test.extraction import (
    DEFAULT_KAPPA_KEYWORDS,
    KappaVocabulary,
    RuleBasedExtractor,
    default_kappa_vocabulary,
)


def test_extractor_selects_only_modal_sentences() -> None:
    extractor = RuleBasedExtractor()
    plan = (
        "Prepare the update. "
        "The executor must commit the artifact. "
        "This is a decorative statement. "
        "The executor should verify approval.\n"
    )
    bundle = extractor.extract(plan_id="p001", plan_text=plan)
    texts = [claim.text for claim in bundle.claims]
    assert texts == [
        "The executor must commit the artifact.",
        "The executor should verify approval.",
    ]


def test_extractor_marks_kappa_terms_from_vocabulary() -> None:
    extractor = RuleBasedExtractor(
        kappa=default_kappa_vocabulary(
            capabilities=("delegate",),
            artifacts=("reports/out.md",),
        )
    )
    plan = (
        "The executor must write reports/out.md. "
        "The executor should delegate the review. "
        "The executor will observe idle state.\n"
    )
    bundle = extractor.extract(plan_id="p002", plan_text=plan)
    kappa_hits = {claim.text: claim.kappa_terms for claim in bundle.claims}
    assert kappa_hits["The executor must write reports/out.md."] == ("reports/out.md",)
    assert set(kappa_hits["The executor should delegate the review."]) == {"delegate"}
    assert kappa_hits["The executor will observe idle state."] == ()


def test_extractor_is_deterministic() -> None:
    extractor = RuleBasedExtractor()
    plan = "The executor must commit. The executor should verify.\n"
    a = extractor.extract(plan_id="p003", plan_text=plan)
    b = extractor.extract(plan_id="p003", plan_text=plan)
    assert a.bundle_digest == b.bundle_digest


def test_extractor_offsets_slice_original_plan() -> None:
    extractor = RuleBasedExtractor()
    plan = "Intro. The executor must commit. Trailer.\n"
    bundle = extractor.extract(plan_id="p004", plan_text=plan)
    assert len(bundle.claims) == 1
    claim = bundle.claims[0]
    assert plan[claim.start_offset : claim.end_offset].strip() == claim.text.strip()


def test_extractor_rejects_empty_inputs() -> None:
    extractor = RuleBasedExtractor()
    with pytest.raises(ValueError):
        extractor.extract(plan_id="", plan_text="a modal must exist")
    with pytest.raises(ValueError):
        extractor.extract(plan_id="p005", plan_text="")


def test_default_kappa_keywords_cover_ct_vocabulary() -> None:
    vocab = default_kappa_vocabulary()
    assert isinstance(vocab, KappaVocabulary)
    assert "commit" in vocab.keywords
    assert "approval" in vocab.keywords
    assert vocab.keywords == DEFAULT_KAPPA_KEYWORDS
