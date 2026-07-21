"""Tests for the commitment-surface delta + verdict rules."""

from __future__ import annotations

from experiments.load_bearing_prose_test.claims import (
    AblationKind,
    Claim,
    Verdict,
)
from experiments.load_bearing_prose_test.scoring import (
    ClaimVerdictInputs,
    CommitmentSurface,
    aggregate_metrics,
    classify_claim,
    surface_delta,
)


def _surface(
    *,
    action: str = "delegate_with_envelope",
    caps: tuple[str, ...] = ("delegate",),
    artifact_created: bool = False,
    workspace_digest: str | None = None,
    false_completion: bool = False,
    joint_success: bool = True,
) -> CommitmentSurface:
    return CommitmentSurface(
        action=action,
        capability_used=frozenset(caps),
        artifact_created=artifact_created,
        workspace_digest=workspace_digest,
        false_completion=false_completion,
        joint_success=joint_success,
    )


def _claim(kappa: bool = True) -> Claim:
    return Claim(
        claim_id="p001::c001",
        text="The executor must delegate.",
        start_offset=0,
        end_offset=27,
        kappa_terms=("delegate",) if kappa else (),
    )


def test_surface_delta_is_false_for_identical_surfaces() -> None:
    a = _surface()
    b = _surface()
    assert surface_delta(a, b) is False


def test_surface_delta_flags_capability_widening() -> None:
    baseline = _surface(caps=("delegate",))
    widened = _surface(
        action="delegate_with_widened_capability",
        caps=("delegate", "publish"),
        joint_success=False,
    )
    assert surface_delta(baseline, widened) is True


def test_classify_claim_flags_load_bearing_on_delete_delta() -> None:
    baseline = _surface()
    widened = _surface(
        action="delegate_with_widened_capability",
        caps=("delegate", "publish"),
        joint_success=False,
    )
    inputs = ClaimVerdictInputs(
        claim=_claim(),
        baseline=baseline,
        surfaces={
            AblationKind.DELETE: widened,
            AblationKind.NEGATE: baseline,
            AblationKind.PARAPHRASE: baseline,
        },
    )
    verdict = classify_claim(inputs)
    assert verdict.is_load_bearing is True
    assert verdict.delete_delta is True
    assert verdict.negate_delta is False
    assert verdict.paraphrase_invariant is True


def test_classify_claim_marks_inert_when_no_delta() -> None:
    baseline = _surface()
    inputs = ClaimVerdictInputs(
        claim=_claim(kappa=False),
        baseline=baseline,
        surfaces={
            AblationKind.DELETE: baseline,
            AblationKind.NEGATE: baseline,
            AblationKind.PARAPHRASE: baseline,
        },
    )
    verdict = classify_claim(inputs)
    assert verdict.is_load_bearing is False
    assert verdict.paraphrase_invariant is False


def test_classify_claim_flags_paraphrase_leak_on_load_bearing_claim() -> None:
    baseline = _surface()
    widened = _surface(
        action="delegate_with_widened_capability",
        caps=("delegate", "publish"),
        joint_success=False,
    )
    inputs = ClaimVerdictInputs(
        claim=_claim(),
        baseline=baseline,
        surfaces={
            AblationKind.DELETE: widened,
            AblationKind.NEGATE: baseline,
            AblationKind.PARAPHRASE: widened,
        },
    )
    verdict = classify_claim(inputs)
    assert verdict.is_load_bearing is True
    assert verdict.paraphrase_delta is True
    assert verdict.paraphrase_invariant is False


def test_aggregate_metrics_matches_load_bearing_counts() -> None:
    verdicts = [
        Verdict(
            claim_id="c1",
            is_load_bearing=True,
            paraphrase_invariant=True,
            delete_delta=True,
            negate_delta=False,
            paraphrase_delta=False,
            kappa_mention=True,
        ),
        Verdict(
            claim_id="c2",
            is_load_bearing=False,
            paraphrase_invariant=False,
            delete_delta=False,
            negate_delta=False,
            paraphrase_delta=False,
            kappa_mention=False,
        ),
        Verdict(
            claim_id="c3",
            is_load_bearing=True,
            paraphrase_invariant=False,
            delete_delta=True,
            negate_delta=False,
            paraphrase_delta=True,
            kappa_mention=False,
        ),
    ]
    metrics = aggregate_metrics(verdicts)
    assert metrics.n_claims == 3
    assert metrics.n_load_bearing == 2
    assert metrics.n_paraphrase_invariant == 1
    assert metrics.load_bearing_rate == 2 / 3
    assert metrics.paraphrase_invariance_rate == 1 / 2
    assert metrics.kappa_odds_ratio is not None


def test_aggregate_metrics_handles_zero_load_bearing() -> None:
    verdict = Verdict(
        claim_id="c1",
        is_load_bearing=False,
        paraphrase_invariant=False,
        delete_delta=False,
        negate_delta=False,
        paraphrase_delta=False,
        kappa_mention=False,
    )
    metrics = aggregate_metrics([verdict])
    assert metrics.load_bearing_rate == 0.0
    assert metrics.paraphrase_invariance_rate == 0.0
