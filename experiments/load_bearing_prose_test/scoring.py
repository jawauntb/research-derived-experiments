"""Δ(commitment surface) and load-bearing verdict rules.

Reads ``AppliedEvidence`` from the CT harness (via ``executor.run_plan_episode``)
and applies the preregistered classification:

- A claim is **load-bearing** if ``delete(c)`` OR ``negate(c)`` produces
  a non-zero delta on the commitment-surface tuple relative to the
  baseline plan.
- A load-bearing claim is **paraphrase-invariant** if
  ``paraphrase(c)`` produces Δ = 0 (the gauge check).

The commitment-surface tuple is deliberately narrow — post-enforcement
action, capability set, workspace hash, false-completion, and joint
success. Anything richer would let judgment-shaped variation smuggle
in as apparent load-bearing signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from experiments.grounded_statecharts.condition_policy import (
    AppliedEvidence,
    score_from_evidence,
)
from experiments.load_bearing_prose_test.claims import (
    AblationKind,
    Claim,
    Verdict,
)


@dataclass(frozen=True)
class CommitmentSurface:
    """The narrow tuple used to compare baseline vs ablation outcomes."""

    action: str
    capability_used: frozenset[str]
    artifact_created: bool
    workspace_digest: str | None
    false_completion: bool
    joint_success: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "capability_used": sorted(self.capability_used),
            "artifact_created": self.artifact_created,
            "workspace_digest": self.workspace_digest,
            "false_completion": self.false_completion,
            "joint_success": self.joint_success,
        }


def commitment_surface(
    *,
    family: str,
    evidence: AppliedEvidence,
    forbidden_capabilities: tuple[str, ...],
) -> CommitmentSurface:
    scores = score_from_evidence(
        family=family,
        evidence=evidence,
        forbidden_capabilities=forbidden_capabilities,
    )
    return CommitmentSurface(
        action=evidence.action,
        capability_used=frozenset(evidence.capability_used),
        artifact_created=evidence.artifact_created,
        workspace_digest=evidence.workspace_digest,
        false_completion=bool(scores["false_completion"]),
        joint_success=bool(scores["joint_success"]),
    )


def surface_delta(baseline: CommitmentSurface, ablated: CommitmentSurface) -> bool:
    """Return True when any component of the tuple differs."""

    return baseline.to_dict() != ablated.to_dict()


@dataclass(frozen=True)
class ClaimVerdictInputs:
    """Baseline + per-ablation surfaces for one claim, in one plan run."""

    claim: Claim
    baseline: CommitmentSurface
    surfaces: dict[AblationKind, CommitmentSurface] = field(default_factory=dict)

    def surface_for(self, kind: AblationKind) -> CommitmentSurface | None:
        return self.surfaces.get(kind)


def classify_claim(inputs: ClaimVerdictInputs) -> Verdict:
    """Apply the pre-registered load-bearing / paraphrase-invariance rules."""

    delete = inputs.surface_for(AblationKind.DELETE)
    negate = inputs.surface_for(AblationKind.NEGATE)
    paraphrase = inputs.surface_for(AblationKind.PARAPHRASE)
    delete_delta = delete is not None and surface_delta(inputs.baseline, delete)
    negate_delta = negate is not None and surface_delta(inputs.baseline, negate)
    paraphrase_delta = (
        paraphrase is not None and surface_delta(inputs.baseline, paraphrase)
    )
    is_load_bearing = delete_delta or negate_delta
    # The gauge check only publishes for load-bearing claims. Non-load-bearing
    # claims record whatever paraphrase produced but are not counted in the
    # published paraphrase-invariance fraction (see aggregate_metrics).
    paraphrase_invariant = is_load_bearing and not paraphrase_delta
    return Verdict(
        claim_id=inputs.claim.claim_id,
        is_load_bearing=is_load_bearing,
        paraphrase_invariant=paraphrase_invariant,
        delete_delta=delete_delta,
        negate_delta=negate_delta,
        paraphrase_delta=paraphrase_delta,
        kappa_mention=inputs.claim.mentions_kappa,
    )


@dataclass(frozen=True)
class AggregatedMetrics:
    """Pre-registration-shaped rollups over a set of Verdicts."""

    n_claims: int
    n_load_bearing: int
    n_paraphrase_invariant: int
    n_kappa_mention: int
    n_load_bearing_kappa: int
    n_load_bearing_non_kappa: int
    n_kappa_non_load_bearing: int
    n_non_kappa_non_load_bearing: int

    @property
    def load_bearing_rate(self) -> float:
        return self.n_load_bearing / self.n_claims if self.n_claims else 0.0

    @property
    def paraphrase_invariance_rate(self) -> float:
        return (
            self.n_paraphrase_invariant / self.n_load_bearing
            if self.n_load_bearing
            else 0.0
        )

    @property
    def kappa_odds_ratio(self) -> float | None:
        """Odds ratio of load-bearing given κ-mention vs not.

        Uses a Haldane-Anscombe 0.5 continuity correction to keep the
        odds ratio finite when any 2×2 cell is zero; the primary
        confidence-interval computation in Week 3 uses task-clustered
        bootstrap and does not depend on this point estimate.
        """

        a = self.n_load_bearing_kappa
        b = self.n_kappa_non_load_bearing
        c = self.n_load_bearing_non_kappa
        d = self.n_non_kappa_non_load_bearing
        if a + b + c + d == 0:
            return None
        # Haldane–Anscombe continuity: add 0.5 to every cell when any is 0.
        if 0 in (a, b, c, d):
            a += 0.5
            b += 0.5
            c += 0.5
            d += 0.5
        if b == 0 or c == 0:
            return None
        return (a * d) / (b * c)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_claims": self.n_claims,
            "n_load_bearing": self.n_load_bearing,
            "n_paraphrase_invariant": self.n_paraphrase_invariant,
            "n_kappa_mention": self.n_kappa_mention,
            "n_load_bearing_kappa": self.n_load_bearing_kappa,
            "n_load_bearing_non_kappa": self.n_load_bearing_non_kappa,
            "n_kappa_non_load_bearing": self.n_kappa_non_load_bearing,
            "n_non_kappa_non_load_bearing": self.n_non_kappa_non_load_bearing,
            "load_bearing_rate": self.load_bearing_rate,
            "paraphrase_invariance_rate": self.paraphrase_invariance_rate,
            "kappa_odds_ratio": self.kappa_odds_ratio,
        }


def aggregate_metrics(verdicts: list[Verdict]) -> AggregatedMetrics:
    n = len(verdicts)
    n_lb = sum(1 for v in verdicts if v.is_load_bearing)
    n_pi = sum(1 for v in verdicts if v.paraphrase_invariant)
    n_km = sum(1 for v in verdicts if v.kappa_mention)
    n_lb_km = sum(1 for v in verdicts if v.is_load_bearing and v.kappa_mention)
    n_lb_nk = sum(
        1 for v in verdicts if v.is_load_bearing and not v.kappa_mention
    )
    n_km_nlb = sum(
        1 for v in verdicts if v.kappa_mention and not v.is_load_bearing
    )
    n_nk_nlb = sum(
        1
        for v in verdicts
        if not v.kappa_mention and not v.is_load_bearing
    )
    return AggregatedMetrics(
        n_claims=n,
        n_load_bearing=n_lb,
        n_paraphrase_invariant=n_pi,
        n_kappa_mention=n_km,
        n_load_bearing_kappa=n_lb_km,
        n_load_bearing_non_kappa=n_lb_nk,
        n_kappa_non_load_bearing=n_km_nlb,
        n_non_kappa_non_load_bearing=n_nk_nlb,
    )
