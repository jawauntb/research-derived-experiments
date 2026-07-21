"""Deterministic type-invariant tests for load-bearing-prose-test claim scaffolding."""

from __future__ import annotations

import pytest

from experiments.load_bearing_prose_test.claims import (
    Ablation,
    AblationKind,
    AblationSet,
    Claim,
    ClaimBundle,
    canonical_json,
    digest,
)


def _valid_bundle() -> ClaimBundle:
    plan_text = "The executor must commit. The executor should verify.\n"
    return ClaimBundle(
        plan_id="pt001",
        plan_digest=digest({"plan_text": plan_text}),
        claims=(
            Claim(
                claim_id="pt001::c001",
                text="The executor must commit.",
                start_offset=0,
                end_offset=25,
                kappa_terms=("commit",),
            ),
            Claim(
                claim_id="pt001::c002",
                text="The executor should verify.",
                start_offset=26,
                end_offset=53,
            ),
        ),
    )


def test_canonical_json_is_stable_and_sorted() -> None:
    payload = {"b": 1, "a": [3, 2, 1]}
    encoded = canonical_json(payload)
    assert encoded == '{"a":[3,2,1],"b":1}'
    assert digest(payload) == digest(payload)


def test_claim_rejects_empty_text_and_bad_offsets() -> None:
    with pytest.raises(ValueError):
        Claim(claim_id="p::c1", text="", start_offset=0, end_offset=1)
    with pytest.raises(ValueError):
        Claim(claim_id="p::c1", text="x", start_offset=5, end_offset=5)
    with pytest.raises(ValueError):
        Claim(claim_id="", text="x", start_offset=0, end_offset=1)


def test_claim_mentions_kappa_reflects_terms() -> None:
    claim = Claim(
        claim_id="p::c1",
        text="commit the delegate",
        start_offset=0,
        end_offset=19,
        kappa_terms=("commit", "delegate"),
    )
    assert claim.mentions_kappa is True
    plain = Claim(
        claim_id="p::c2",
        text="observe the state",
        start_offset=20,
        end_offset=36,
    )
    assert plain.mentions_kappa is False


def test_claim_bundle_rejects_duplicate_ids_and_bad_digest() -> None:
    good_digest = "0" * 64
    dup = Claim(claim_id="p::c1", text="a", start_offset=0, end_offset=1)
    with pytest.raises(ValueError):
        ClaimBundle(plan_id="p001", plan_digest=good_digest, claims=(dup, dup))
    with pytest.raises(ValueError):
        ClaimBundle(plan_id="p001", plan_digest="not-a-digest", claims=(dup,))


def test_claim_bundle_digest_is_deterministic_and_reflects_claims() -> None:
    bundle = _valid_bundle()
    other = ClaimBundle(
        plan_id=bundle.plan_id,
        plan_digest=bundle.plan_digest,
        claims=bundle.claims,
    )
    assert bundle.bundle_digest == other.bundle_digest
    perturbed = ClaimBundle(
        plan_id=bundle.plan_id,
        plan_digest=bundle.plan_digest,
        claims=bundle.claims[:1],
    )
    assert perturbed.bundle_digest != bundle.bundle_digest


def test_ablation_rejects_wrong_kind_type() -> None:
    with pytest.raises(ValueError):
        Ablation(
            plan_id="p001",
            claim_id="p1::c1",
            kind="delete",  # type: ignore[arg-type]
            modified_plan="x",
        )


def test_ablation_set_rejects_duplicate_claim_kind() -> None:
    bundle = _valid_bundle()
    a = Ablation(
        plan_id="p001",
        claim_id="p1::c1",
        kind=AblationKind.DELETE,
        modified_plan="one",
    )
    with pytest.raises(ValueError):
        AblationSet(bundle_digest=bundle.bundle_digest, ablations=(a, a))


def test_ablation_set_for_claim_lookup_returns_by_kind() -> None:
    bundle = _valid_bundle()
    delete = Ablation(
        plan_id="p001",
        claim_id="p1::c1",
        kind=AblationKind.DELETE,
        modified_plan="deleted",
    )
    negate = Ablation(
        plan_id="p001",
        claim_id="p1::c1",
        kind=AblationKind.NEGATE,
        modified_plan="negated",
    )
    other_claim_paraphrase = Ablation(
        plan_id="p001",
        claim_id="p1::c2",
        kind=AblationKind.PARAPHRASE,
        modified_plan="para",
    )
    aset = AblationSet(
        bundle_digest=bundle.bundle_digest,
        ablations=(delete, negate, other_claim_paraphrase),
    )
    by_kind = aset.for_claim("p1::c1")
    assert set(by_kind.keys()) == {AblationKind.DELETE, AblationKind.NEGATE}
    assert by_kind[AblationKind.DELETE] is delete
    assert "p1::c1" not in aset.for_claim("p1::c2")
