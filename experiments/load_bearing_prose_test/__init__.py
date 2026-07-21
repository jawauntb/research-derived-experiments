"""Load-Bearing Prose Test scaffolding.

Deterministic types, extractors, and ablation transforms for the
concern-transport bridge-theorem test on LLM-produced prose. No live
provider paths in the scaffold; those arrive in Week 2 alongside the
CT executor adapter.

See ``docs/harness_research/load_bearing_prose_test/README.md`` for
scope and ``PREREGISTRATION.md`` for fatal gates.
"""

from experiments.load_bearing_prose_test.claims import (
    Ablation,
    AblationKind,
    AblationSet,
    Claim,
    ClaimBundle,
    Verdict,
    canonical_json,
    digest,
)

__all__ = [
    "Ablation",
    "AblationKind",
    "AblationSet",
    "Claim",
    "ClaimBundle",
    "Verdict",
    "canonical_json",
    "digest",
]
