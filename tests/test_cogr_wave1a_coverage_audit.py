"""Wave 1a coverage-audit regression tests.

Covers the two Wave 1a scaffold guarantees the sweep runner relies on:

1. A passing cell returns a :class:`CoverageVerdict` with ``passed=True``.
2. A cell whose propensity-weighted coverage falls below the preregistered
   floor raises :class:`CoverageAuditFailure`; the exception carries the
   numeric verdict on ``.verdict``.

No experiment logic is exercised — the tests build ``ProbeReceipt``
fixtures directly and check the audit contract in isolation.
"""

from __future__ import annotations

from typing import Literal

import pytest

from experiments.concern_gated_retrieval_e2.wave0.concern_update import ProbeReceipt
from experiments.concern_gated_retrieval_e2.wave1a.coverage_audit import (
    CoverageAuditFailure,
    CoverageVerdict,
    DEFAULT_COVERAGE_FLOOR,
    audit_coverage,
    propensity_weighted_coverage,
)


def _receipt(
    episode_id: str,
    candidate: str,
    propensity: float,
    *,
    split: Literal["calibration", "confirmatory"] = "confirmatory",
) -> ProbeReceipt:
    return ProbeReceipt(
        episode_id=episode_id,
        candidate=candidate,
        selection_propensity=propensity,
        source_id="trusted",
        template_family_split=split,
        exploratory=True,
    )


def test_propensity_weighted_coverage_reference_formula():
    """The coverage sum matches the closed-form ``PREREGISTRATION.md`` §5.1."""
    receipts = [
        _receipt("ep0", "in_region", 0.5),      # 1 / 0.5 = 2.0
        _receipt("ep1", "out_of_region", 0.5),  # 0.0
        _receipt("ep2", "in_region", 0.25),     # 1 / 0.25 = 4.0
    ]
    target = frozenset({"in_region"})
    # Numerator = 2.0 + 4.0 = 6.0; denominator = 3 receipts.
    assert propensity_weighted_coverage(receipts, target) == pytest.approx(6.0 / 3.0)


def test_audit_coverage_passes_returns_verdict():
    """A cell above the floor returns a ``CoverageVerdict``."""
    # 3 receipts, all inside the target region, low propensity → high coverage.
    receipts = [
        _receipt(f"ep{i}", "commitment", 0.05) for i in range(3)
    ]
    target = frozenset({"commitment"})
    verdict = audit_coverage(receipts, target, floor=DEFAULT_COVERAGE_FLOOR)
    assert isinstance(verdict, CoverageVerdict)
    assert verdict.passed is True
    assert verdict.floor == pytest.approx(DEFAULT_COVERAGE_FLOOR)
    assert verdict.n_receipts == 3
    assert verdict.n_hits == 3
    # ( 1/0.05 + 1/0.05 + 1/0.05 ) / 3 = 20.0
    assert verdict.coverage == pytest.approx(20.0)


def test_audit_coverage_raises_on_floor_breach():
    """A cell below the floor raises with the numeric verdict attached."""
    receipts = [
        _receipt(f"ep{i}", "distractor", 1.0) for i in range(4)
    ]
    target = frozenset({"commitment"})  # no receipt hits the target
    with pytest.raises(CoverageAuditFailure) as excinfo:
        audit_coverage(receipts, target, floor=DEFAULT_COVERAGE_FLOOR)
    exc = excinfo.value
    assert isinstance(exc.verdict, CoverageVerdict)
    assert exc.verdict.passed is False
    assert exc.verdict.n_hits == 0
    assert exc.verdict.n_receipts == 4
    assert exc.verdict.coverage == pytest.approx(0.0)
    assert exc.verdict.floor == pytest.approx(DEFAULT_COVERAGE_FLOOR)


def test_audit_coverage_empty_cell_is_treated_as_failure():
    """An empty cell is a fatal failure, not a silent pass."""
    with pytest.raises(CoverageAuditFailure) as excinfo:
        audit_coverage([], {"commitment"}, floor=DEFAULT_COVERAGE_FLOOR)
    assert excinfo.value.verdict.n_receipts == 0
    assert excinfo.value.verdict.passed is False


def test_audit_coverage_rejects_negative_floor():
    """A negative floor is a caller bug and is rejected early."""
    receipts = [_receipt("ep", "commitment", 0.5)]
    with pytest.raises(ValueError, match="floor"):
        audit_coverage(receipts, {"commitment"}, floor=-1.0)


def test_audit_coverage_rejects_non_receipt_inputs():
    """A non-``ProbeReceipt`` in the batch is caught early."""
    with pytest.raises(TypeError, match="ProbeReceipt"):
        audit_coverage(
            ["not-a-receipt"],  # ty: ignore[invalid-argument-type]
            {"commitment"},
            floor=DEFAULT_COVERAGE_FLOOR,
        )
