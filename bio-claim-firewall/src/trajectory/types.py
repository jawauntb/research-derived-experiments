"""`AttemptRecord`/`TrajectoryRecord`: the trajectory JSONL schema.

Adapted from MIDAS `src/pipeline/trajectory.py`'s `AttemptRecord` /
`TrajectoryRecord` dataclasses (see PHASE_4_PLAN.md's field-rename table):

- `reasoning_steps` -> `proposed_claim` (a claim is atomic, not a list of
  proof steps -- no math-step decomposition to carry).
- `verification_status` -> `verdict` (the literal `verdict.schema.json`
  `verdict` string: `ACCEPTED_CONDITIONALLY` / `REJECTED` / `INCONCLUSIVE`
  / `CHECKER_ERROR`, or `None` for a record that never reached `verify()`
  at all, e.g. a proposer contract failure or a repairer abstain).
- `generated_code` dropped entirely (nothing is ever executed here).
- new biology fields: `claim_id`, `subject_id`, `relation`, `object_id`,
  `fault_code`, `evidence_ids`.
- new provenance fields (this task's own rule -- "MODEL_VERSION,
  PROMPT_VERSION, provider, seed (if set) into every record"): `provider`,
  `model`, `prompt_ref`, `prompt_version`, `tokens_prompt`,
  `tokens_completion`, `latency_ms`, `seed`.

`steps_verified`/`steps_failed` (MIDAS's per-proof-step pass/fail tally) are
dropped rather than renamed: a `Claim` has no sub-steps to tally against,
so nothing in the biology domain maps onto that field. `verification_errors`
is replaced by `reasons`, carrying `verdict.schema.json`'s own
`reasons`/`checker_error` shape verbatim rather than a MIDAS-specific
`{error_type, message}` pair.

# PHASE4B-DECISION: one `AttemptRecord` is logged per meaningful event in
the orchestrator loop -- a `propose()` call, a `verify()` call, a
`repair()` call (whether it produces a repaired claim or an abstain), or a
contract-violation raised by either untrusted-model call. `stage`
distinguishes which kind of event produced the record; `attempt_number` is
a monotonically increasing counter across the *whole* trajectory (not
per-claim), so the JSONL record faithfully preserves call order end to end
-- exactly what `test_trajectory_log.py` checks for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Stage = Literal[
    "propose",
    "propose_error",
    "verify",
    "repair",
    "repair_abstain",
    "repair_error",
]


@dataclass
class AttemptRecord:
    attempt_number: int
    stage: Stage

    # -- the claim this record concerns, if any was produced ----------
    proposed_claim: dict | None = None
    claim_id: str | None = None
    subject_id: str | None = None
    relation: str | None = None
    object_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)

    # -- the checker's verdict for this attempt, if `verify()` ran -----
    verdict: str | None = None
    fault_code: str | None = None
    reasons: list[dict[str, Any]] = field(default_factory=list)

    # -- model-call provenance (populated for propose/repair* stages) --
    provider: str | None = None
    model: str | None = None
    prompt_ref: str | None = None
    prompt_version: str | None = None
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    latency_ms: int | None = None
    seed: int | None = None

    # -- free-text detail: abstain reason, or a contract-error message -
    note: str | None = None


@dataclass
class TrajectoryRecord:
    trajectory_id: str
    timestamp: str
    question: str
    attempts: list[AttemptRecord] = field(default_factory=list)
    final_status: str = "pending"
    attempt_count: int = 0
