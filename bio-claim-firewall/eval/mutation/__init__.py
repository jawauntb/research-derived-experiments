"""Phase 5a mutation-test runner.

Deletes or inverts each `# MUTATION-POINT:` decision hinge in
`src/rules/sections/*.py` (in a throwaway tmp copy -- never the real
source tree) and confirms `tests/rules/` breaks. A mutant that survives
(no test fails) means the fault code it guards is unvalidated: fix by
adding a test, not by trusting the rule.

Public surface:

    from eval.mutation import MutationRunner, MutationPoint, MUTATION_KINDS
    from eval.mutation import MutationReport, to_markdown, to_json, write_report

See `eval/mutation/README.md` for how to run this and how to add a new
mutation site.
"""

from __future__ import annotations

from .report import MutationReport, summarize, surviving_sites, to_json, to_markdown, write_report
from .runner import MUTATION_KINDS, MutationError, MutationPoint, MutationRunner, discover_points

__all__ = [
    "MUTATION_KINDS",
    "MutationError",
    "MutationPoint",
    "MutationRunner",
    "MutationReport",
    "discover_points",
    "summarize",
    "surviving_sites",
    "to_json",
    "to_markdown",
    "write_report",
]
