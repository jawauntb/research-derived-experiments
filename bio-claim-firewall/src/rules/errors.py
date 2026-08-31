"""The one exception type owned by src/rules.

`RulesError` is reserved exclusively for internal invariant violations
inside the rule engine itself (a malformed cascade, a section returning a
shape the engine doesn't understand, a `RuleResult` that would violate its
own postconditions). It is NEVER raised to signal a claim-level
`REJECTED_<FAULT_CODE>` -- those are always communicated as a `Reason`
inside a `RuleResult`, never as a Python exception. Per src/INTERFACES.md
and spec/fault_taxonomy.md, an uncaught exception out of the rule engine is
exactly the signal the top-level `verifier.verify()` uses to render
`CHECKER_ERROR` (fail-closed), so raising `RulesError` here is how a rules
bug escalates instead of silently mis-rendering a verdict.
"""

from __future__ import annotations


class RulesError(Exception):
    """Raised only for internal invariant violations inside src/rules.

    Attributes:
        code: a short machine-readable tag for the invariant that was
            violated (e.g. ``"BAD_RULE_RESULT"``, ``"UNKNOWN_SECTION"``).
            Not a member of spec/fault_taxonomy.md's closed fault-code
            enum -- this is checker-side, not claim-side.
        details: arbitrary keyword context for logging/debugging.
    """

    def __init__(self, code: str, **details: object) -> None:
        self.code = code
        self.details = details
        detail_str = ", ".join(f"{key}={value!r}" for key, value in details.items())
        message = code if not detail_str else f"{code} ({detail_str})"
        super().__init__(message)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"RulesError({self.code!r}, **{self.details!r})"
