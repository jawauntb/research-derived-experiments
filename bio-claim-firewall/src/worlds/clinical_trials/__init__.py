"""Typed ClinicalTrials.gov/SEC disclosure-consistency world adapter.

The adapter checks a narrow proposition: a separately reviewed SEC exhibit
identity relationship is consistent with the ClinicalTrials.gov record
available at the asserted time.
It intentionally does not infer efficacy, regulatory status, or corporate
truth from the matching identifiers.
"""

from .adapter import (
    ClinicalTrialsAdapter,
    ClinicalTrialsClaim,
    ClinicalTrialsIntegrityError,
    ClinicalTrialsOutcome,
    ClinicalTrialsResult,
    FixtureCorruption,
    OutcomeKind,
    check_clinical_trials_claim,
    load_fixture,
    validate_fixture,
)

__all__ = [
    "ClinicalTrialsAdapter",
    "ClinicalTrialsClaim",
    "ClinicalTrialsIntegrityError",
    "ClinicalTrialsOutcome",
    "ClinicalTrialsResult",
    "FixtureCorruption",
    "OutcomeKind",
    "check_clinical_trials_claim",
    "load_fixture",
    "validate_fixture",
]
