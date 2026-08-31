"""RuleResult's __post_init__ invariants raise RulesError when violated."""

from __future__ import annotations

import pytest

from rules import Reason, RulesError, RuleResult
from rules.types import AppliedRule


def test_rejected_requires_fault_code():
    with pytest.raises(RulesError):
        RuleResult("REJECTED", None, reasons=(Reason("R-CITE-01", "boom"),))


def test_rejected_requires_at_least_one_reason():
    with pytest.raises(RulesError):
        RuleResult("REJECTED", "BAD_CITATION", reasons=())


def test_accepted_requires_null_fault_code():
    with pytest.raises(RulesError):
        RuleResult(
            "ACCEPTED",
            "BAD_CITATION",
            applied_rules=(AppliedRule("R-EDGE-02", "e1"),),
            conditions=("only in cell_line=CLO:0009454 (K562)",),
        )


def test_accepted_requires_nonempty_applied_rules():
    with pytest.raises(RulesError):
        RuleResult(
            "ACCEPTED",
            None,
            applied_rules=(),
            conditions=("only in cell_line=CLO:0009454 (K562)",),
        )


def test_accepted_requires_nonempty_conditions():
    with pytest.raises(RulesError):
        RuleResult(
            "ACCEPTED",
            None,
            applied_rules=(AppliedRule("R-EDGE-02", "e1"),),
            conditions=(),
        )


def test_inconclusive_requires_null_fault_code():
    with pytest.raises(RulesError):
        RuleResult("INCONCLUSIVE", "BAD_CITATION")


def test_inconclusive_requires_empty_reasons():
    with pytest.raises(RulesError):
        RuleResult("INCONCLUSIVE", None, reasons=(Reason("R-CITE-01", "boom"),))


def test_valid_rejected_constructs_cleanly():
    result = RuleResult("REJECTED", "BAD_CITATION", reasons=(Reason("R-CITE-01", "boom"),))
    assert result.verdict == "REJECTED"
    assert result.fault_code == "BAD_CITATION"


def test_valid_accepted_constructs_cleanly():
    result = RuleResult(
        "ACCEPTED",
        None,
        applied_rules=(AppliedRule("R-EDGE-02", "e1"),),
        conditions=("only in cell_line=CLO:0009454 (K562)",),
    )
    assert result.verdict == "ACCEPTED"
    assert result.fault_code is None


def test_valid_inconclusive_constructs_cleanly():
    result = RuleResult("INCONCLUSIVE", None)
    assert result.verdict == "INCONCLUSIVE"
    assert result.reasons == ()
