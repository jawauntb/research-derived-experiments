"""The deterministic rule cascade: CanonicalClaim + SnapshotBundle -> RuleResult.

Implements spec/inference_rules.md's fixed rule cascade over a
hash-verified `evidence.SnapshotBundle`. See src/INTERFACES.md's `rules`
contract for the public shape the top-level `verifier` module depends on.
"""

from __future__ import annotations

from .engine import RuleEngine
from .errors import RulesError
from .types import AppliedRule, Reason, RuleResult

__all__ = [
    "RuleEngine",
    "RuleResult",
    "Reason",
    "AppliedRule",
    "RulesError",
]
