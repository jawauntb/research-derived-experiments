"""Tests for the deterministic ablation transforms."""

from __future__ import annotations

import pytest

from experiments.load_bearing_prose_test.ablation import (
    ablate_bundle,
    delete_claim,
    negate_claim,
    paraphrase_claim,
)
from experiments.load_bearing_prose_test.claims import AblationKind
from experiments.load_bearing_prose_test.extraction import RuleBasedExtractor


PLAN = (
    "The executor must commit. "
    "The executor will not deploy. "
    "The executor is required to attach evidence.\n"
)


def _bundle():
    extractor = RuleBasedExtractor()
    return extractor.extract(plan_id="p_abl", plan_text=PLAN)


def test_negate_is_not_a_round_trip_for_will_not() -> None:
    """Regression: sequential rule application used to invert ``will not`` twice."""

    bundle = _bundle()
    will_not_claim = next(
        c for c in bundle.claims if "will not" in c.text
    )
    ablation = negate_claim(bundle, PLAN, will_not_claim)
    assert ablation.kind is AblationKind.NEGATE
    assert ablation.modified_plan != PLAN
    assert "will deploy" in ablation.modified_plan
    assert "will not deploy" not in ablation.modified_plan


def test_negate_inverts_every_modal_kind() -> None:
    bundle = _bundle()
    for claim in bundle.claims:
        ablation = negate_claim(bundle, PLAN, claim)
        assert ablation.modified_plan != PLAN
        assert ablation.kind is AblationKind.NEGATE


def test_paraphrase_changes_text_but_preserves_content_words() -> None:
    bundle = _bundle()
    for claim in bundle.claims:
        ablation = paraphrase_claim(bundle, PLAN, claim)
        assert ablation.modified_plan != PLAN
        # Content words in the claim should still be present in the modified plan.
        for word in ("commit", "deploy", "evidence"):
            if word in claim.text.lower():
                assert word in ablation.modified_plan.lower()


def test_delete_removes_the_claim_span() -> None:
    bundle = _bundle()
    for claim in bundle.claims:
        ablation = delete_claim(bundle, PLAN, claim)
        assert ablation.kind is AblationKind.DELETE
        # The claim text must no longer appear verbatim.
        assert claim.text not in ablation.modified_plan


def test_ablate_bundle_produces_three_ablations_per_claim() -> None:
    bundle = _bundle()
    aset = ablate_bundle(bundle, PLAN)
    assert len(aset.ablations) == 3 * len(bundle.claims)
    for claim in bundle.claims:
        by_kind = aset.for_claim(claim.claim_id)
        assert set(by_kind.keys()) == {
            AblationKind.DELETE,
            AblationKind.NEGATE,
            AblationKind.PARAPHRASE,
        }


def test_transform_raises_when_offsets_do_not_match_plan() -> None:
    """Guardrail: bundle/plan mismatch is a fail-loud error."""

    bundle = _bundle()
    claim = bundle.claims[0]
    with pytest.raises(ValueError):
        negate_claim(bundle, "unrelated plan text", claim)


def test_ablation_digests_differ_across_kinds_for_same_claim() -> None:
    bundle = _bundle()
    aset = ablate_bundle(bundle, PLAN)
    for claim in bundle.claims:
        by_kind = aset.for_claim(claim.claim_id)
        digests = {ablation.modified_digest for ablation in by_kind.values()}
        assert len(digests) == len(by_kind)
