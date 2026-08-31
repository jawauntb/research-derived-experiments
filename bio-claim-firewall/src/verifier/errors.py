"""VerifierError: the one exception type owned by src/verifier.

Reserved exclusively for internal invariant escalation inside this
package's own composition logic (e.g. a `RuleResult.verdict` value that
isn't one of the three the rules package documents -- structurally
unreachable given `rules.types.RuleResult.__post_init__`, but the
top-level composer never trusts "unreachable" as a substitute for a
handled branch). It is NEVER surfaced to a caller as a `REJECTED_*`
verdict, and it never even needs to leave `verify()` uncaught: `verify()`
wraps every stage (including any code that might raise `VerifierError`)
in `try / except Exception`, so raising this is just this package's own
vocabulary for "escalate to `CHECKER_ERROR`", exactly like any other
unexpected exception from a downstream module.
"""

from __future__ import annotations


class VerifierError(Exception):
    """Raised only for internal invariant violations inside src/verifier.

    Attributes:
        stage: which pipeline stage detected the violation (one of the
            `checker_error.stage` values in spec/verdict.schema.json --
            see `verify.py`'s VERIFIER-DECISION on stage-name mapping).
        message: human-readable detail.
        exception_class: the class name to attach to the resulting
            `checker_error.exception_class`, if this is standing in for
            (or wrapping) a lower-level exception. Defaults to this
            class's own name when not given.
    """

    def __init__(
        self, stage: str, message: str, exception_class: str | None = None
    ) -> None:
        self.stage = stage
        self.message = message
        self.exception_class = exception_class or type(self).__name__
        super().__init__(f"{stage}: {message}")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return (
            f"VerifierError(stage={self.stage!r}, message={self.message!r}, "
            f"exception_class={self.exception_class!r})"
        )
