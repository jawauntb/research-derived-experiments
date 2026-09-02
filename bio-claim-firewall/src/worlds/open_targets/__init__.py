"""Typed Open Targets release-bound target--disease association adapter."""

from .adapter import (
    FixtureCorruption,
    OpenTargetsAdapter,
    OpenTargetsClaim,
    OpenTargetsIntegrityError,
    OpenTargetsOutcome,
    OpenTargetsResult,
    OutcomeKind,
    check_open_targets_claim,
    load_fixture,
    validate_fixture,
)

__all__ = [
    "FixtureCorruption",
    "OpenTargetsAdapter",
    "OpenTargetsClaim",
    "OpenTargetsIntegrityError",
    "OpenTargetsOutcome",
    "OpenTargetsResult",
    "OutcomeKind",
    "check_open_targets_claim",
    "load_fixture",
    "validate_fixture",
]
