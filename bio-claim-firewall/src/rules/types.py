"""Frozen result types the rule cascade produces.

`Reason` and `AppliedRule` are cheap, order-preserving records of "what the
engine noticed." `RuleResult` is the engine's single typed answer for one
claim, with `__post_init__` invariants enforced eagerly (per the module
brief) so a malformed result can never silently leave `RuleEngine.run()` --
any construction that would violate them raises `RulesError`
(`code="BAD_RULE_RESULT"`), which is exactly the internal-invariant-only
signal `src/rules/errors.py` documents. That keeps the invariant check in
one place instead of re-validating at every call site that builds a
`RuleResult`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .errors import RulesError

Verdict = Literal["ACCEPTED", "REJECTED", "INCONCLUSIVE"]


@dataclass(frozen=True, slots=True)
class Reason:
    """One rule-cascade finding: which rule fired, and why."""

    rule_id: str
    message: str
    evidence_id: str | None = None


@dataclass(frozen=True, slots=True)
class AppliedRule:
    """One rule that participated in an ACCEPT decision (post-cascade licensing)."""

    rule_id: str
    evidence_id: str | None = None


@dataclass(frozen=True, slots=True)
class RuleResult:
    """The rule engine's single typed answer for one claim.

    Invariants (checked in `__post_init__`; violation raises
    `RulesError("BAD_RULE_RESULT", ...)`):

    - `verdict == "REJECTED"` requires `fault_code is not None` and at
      least one `Reason`.
    - `verdict == "ACCEPTED"` requires `fault_code is None`, a non-empty
      `applied_rules`, and a non-empty `conditions`.
    - `verdict == "INCONCLUSIVE"` requires `fault_code is None` and
      `reasons == ()`.
    """

    verdict: Verdict
    fault_code: str | None
    reasons: tuple[Reason, ...] = field(default_factory=tuple)
    applied_rules: tuple[AppliedRule, ...] = field(default_factory=tuple)
    conditions: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.verdict == "REJECTED":
            if self.fault_code is None:
                raise RulesError(
                    "BAD_RULE_RESULT",
                    reason="REJECTED requires a non-null fault_code",
                    verdict=self.verdict,
                )
            if not self.reasons:
                raise RulesError(
                    "BAD_RULE_RESULT",
                    reason="REJECTED requires at least one Reason",
                    verdict=self.verdict,
                )
        elif self.verdict == "ACCEPTED":
            if self.fault_code is not None:
                raise RulesError(
                    "BAD_RULE_RESULT",
                    reason="ACCEPTED requires fault_code is None",
                    verdict=self.verdict,
                    fault_code=self.fault_code,
                )
            if not self.applied_rules:
                raise RulesError(
                    "BAD_RULE_RESULT",
                    reason="ACCEPTED requires a non-empty applied_rules",
                    verdict=self.verdict,
                )
            if not self.conditions:
                raise RulesError(
                    "BAD_RULE_RESULT",
                    reason="ACCEPTED requires a non-empty conditions",
                    verdict=self.verdict,
                )
        elif self.verdict == "INCONCLUSIVE":
            if self.fault_code is not None:
                raise RulesError(
                    "BAD_RULE_RESULT",
                    reason="INCONCLUSIVE requires fault_code is None",
                    verdict=self.verdict,
                    fault_code=self.fault_code,
                )
            if self.reasons:
                raise RulesError(
                    "BAD_RULE_RESULT",
                    reason="INCONCLUSIVE requires reasons == ()",
                    verdict=self.verdict,
                )
        else:
            raise RulesError(
                "BAD_RULE_RESULT", reason="unknown verdict", verdict=self.verdict
            )
