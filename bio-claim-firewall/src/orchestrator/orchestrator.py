"""`Orchestrator`: the propose -> verify -> repair -> re-verify loop.

# MIDAS ATTRIBUTION: adapted from MIDAS `src/pipeline/verification/
# verification_orchestrator.py:89-169` (`VerificationOrchestrator.
# verify_with_repair`) -- the overall shape (start a trajectory, loop up to
# `max_repair_attempts + 1` times calling verify-then-repair, log every
# iteration, close the trajectory in a way that always fires even on an
# early break) is preserved. Everything problem-domain-specific is
# rewritten: MIDAS repairs one `ReasoningOutput` against a single pass/fail
# verification result; this orchestrator verifies a whole `ClaimBundle`
# (each claim independently) against a `verdict.schema.json`-shaped
# four-way verdict (`ACCEPTED_CONDITIONALLY` / `REJECTED` / `INCONCLUSIVE`
# / `CHECKER_ERROR`), and repair is only ever attempted for `REJECTED`
# claims -- see the PHASE4B-DECISION docstrings below for `INCONCLUSIVE`
# and `CHECKER_ERROR` handling, both of which have no MIDAS analogue.
#
# PHASE4B-DECISION (fault-split invariant, propose-contract failures):
# PHASE_4_PLAN.md's fault-split table requires a proposer-side pipeline
# failure to never be confused with `CHECKER_ERROR`. Since
# `OrchestratorResult.status` is a closed four-value enum with no fifth
# slot for "the proposer never produced a claim at all", a
# `proposer.ProposerError` from `Proposer.propose()` is NOT folded into any
# of the four status values -- it propagates out of `run()` as an
# `OrchestratorError` (after the trajectory is still durably closed; see
# the `try/finally` below). Callers that want a non-raising API wrap
# `run()` themselves.
"""

from __future__ import annotations

from typing import Any

from repairer import Repairer, RepairerError
from proposer import Proposer, ProposerError
from trajectory import AttemptRecord, TrajectoryLogger
from verifier import VerifierConfig, verify

from .errors import OrchestratorError
from .types import OrchestratorConfig, OrchestratorResult, Status

_REPAIRABLE_VERDICTS = frozenset({"REJECTED"})


def _entity_id(entity: Any) -> str | None:
    return entity.get("id") if isinstance(entity, dict) else None


class Orchestrator:
    """Runs the full propose/verify/repair loop for one question and logs
    every attempt to a `TrajectoryLogger`, if configured.
    """

    def __init__(
        self,
        proposer: Proposer,
        repairer: Repairer,
        verifier_config: VerifierConfig,
        snapshot: Any,
        config: OrchestratorConfig,
    ) -> None:
        self.proposer = proposer
        self.repairer = repairer
        self.verifier_config = verifier_config
        self.snapshot = snapshot
        self.config = config

    def run(
        self,
        question: str,
        evidence_records: list[dict],
        context_hints: dict | None = None,
    ) -> OrchestratorResult:
        logger = TrajectoryLogger(self.config.trajectory_path) if self.config.trajectory_path else None
        trajectory_id = logger.start_trajectory(question) if logger else _fresh_trajectory_id()

        attempts = 0  # counts verify() calls only -- see OrchestratorResult.attempts
        log_seq = 0  # counts every logged record -- preserves strict call order
        final_verdicts: list[dict] = []
        status: str = "pending"

        try:
            try:
                bundle = self.proposer.propose(question, evidence_records, context_hints)
            except ProposerError as exc:
                log_seq += 1
                if logger:
                    logger.log_attempt(
                        trajectory_id,
                        AttemptRecord(attempt_number=log_seq, stage="propose_error", note=str(exc)),
                    )
                status = "propose_error"
                raise OrchestratorError(
                    "propose_failed", str(exc), trajectory_id=trajectory_id
                ) from exc

            claim_statuses: list[str] = []

            for claim in bundle.claims:
                log_seq += 1
                if logger:
                    logger.log_attempt(trajectory_id, self._propose_record(log_seq, claim, bundle))

                attempts += 1
                verdict = verify(claim, self.snapshot, self.verifier_config)
                log_seq += 1
                if logger:
                    logger.log_attempt(trajectory_id, self._verify_record(log_seq, claim, verdict))

                claim_status: Status
                final_verdict = verdict

                if verdict["verdict"] == "ACCEPTED_CONDITIONALLY":
                    claim_status = "accepted"
                elif verdict["verdict"] == "CHECKER_ERROR":
                    claim_status = "checker_error"
                elif verdict["verdict"] == "REJECTED":
                    claim_status, final_verdict, attempts, log_seq = self._repair_loop(
                        claim, verdict, evidence_records, logger, trajectory_id, attempts, log_seq
                    )
                else:
                    # PHASE4B-DECISION: INCONCLUSIVE carries no fault_code
                    # -- per spec/fault_taxonomy.md it is a distinct
                    # terminal state ("no rule applies but no violation"),
                    # not a claim-side contract violation, so it is never
                    # sent to the repairer (nothing about it is
                    # "repairable"). It folds into the `rejected_exhausted`
                    # bucket for this coarse status summary ONLY -- the
                    # verdict recorded in `final_verdicts` is the
                    # untouched INCONCLUSIVE verdict `verify()` returned,
                    # never rewritten to REJECTED or ACCEPTED_CONDITIONALLY
                    # (spec/non_goals.md's second Prohibited move).
                    claim_status = "rejected_exhausted"

                final_verdicts.append(final_verdict)
                claim_statuses.append(claim_status)

                if claim_status == "checker_error" and self.config.abort_on_checker_error:
                    status = "checker_error"
                    return OrchestratorResult(
                        final_verdicts=tuple(final_verdicts),
                        trajectory_id=trajectory_id,
                        attempts=attempts,
                        status=status,
                    )
                # abort_on_checker_error=False: fall through and move on
                # to the next claim in the bundle ("skip claim").

            status = _aggregate_status(claim_statuses)
            return OrchestratorResult(
                final_verdicts=tuple(final_verdicts),
                trajectory_id=trajectory_id,
                attempts=attempts,
                status=status,
            )
        finally:
            # Always fires -- on every `return` above, on the
            # `OrchestratorError` raise, and defensively on any other
            # exception this loop did not anticipate (test_close_always_
            # called.py). `status` holds whatever was last assigned
            # ("pending" if nothing else ran at all).
            if logger:
                logger.close_trajectory(trajectory_id, final_status=status)

    # -- the per-claim repair->re-verify cycle -------------------------

    def _repair_loop(
        self,
        claim: dict,
        verdict: dict,
        evidence_records: list[dict],
        logger: TrajectoryLogger | None,
        trajectory_id: str,
        attempts: int,
        log_seq: int,
    ) -> tuple[Status, dict, int, int]:
        current_claim = claim
        current_verdict = verdict

        for _ in range(self.config.max_repair_attempts):
            try:
                result = self.repairer.repair(current_claim, current_verdict, evidence_records)
            except RepairerError as exc:
                # MIDAS-equivalent: `_attempt_reasoning_repair` catching
                # `ReasoningContractError` and halting the repair loop
                # rather than retrying against a model that just violated
                # its own contract.
                log_seq += 1
                if logger:
                    logger.log_attempt(
                        trajectory_id,
                        AttemptRecord(
                            attempt_number=log_seq,
                            stage="repair_error",
                            claim_id=current_claim.get("claim_id"),
                            note=str(exc),
                        ),
                    )
                return "rejected_exhausted", current_verdict, attempts, log_seq

            log_seq += 1
            if result.abstained:
                if logger:
                    logger.log_attempt(trajectory_id, self._repair_abstain_record(log_seq, current_claim, result))
                return "abstained", current_verdict, attempts, log_seq

            repaired_claim = result.claim
            assert repaired_claim is not None  # RepairResult.__post_init__ guarantees this
            if logger:
                logger.log_attempt(trajectory_id, self._repair_record(log_seq, repaired_claim, result))

            attempts += 1
            new_verdict = verify(repaired_claim, self.snapshot, self.verifier_config)
            log_seq += 1
            if logger:
                logger.log_attempt(trajectory_id, self._verify_record(log_seq, repaired_claim, new_verdict))

            current_claim = repaired_claim
            current_verdict = new_verdict

            if new_verdict["verdict"] == "ACCEPTED_CONDITIONALLY":
                return "accepted", current_verdict, attempts, log_seq
            if new_verdict["verdict"] == "CHECKER_ERROR":
                return "checker_error", current_verdict, attempts, log_seq
            if new_verdict["verdict"] == "INCONCLUSIVE":
                return "rejected_exhausted", current_verdict, attempts, log_seq
            # REJECTED -> loop again if attempts remain

        return "rejected_exhausted", current_verdict, attempts, log_seq

    # -- trajectory record builders -------------------------------------

    def _propose_record(self, seq: int, claim: dict, bundle: Any) -> AttemptRecord:
        return AttemptRecord(
            attempt_number=seq,
            stage="propose",
            proposed_claim=claim,
            claim_id=claim.get("claim_id"),
            subject_id=_entity_id(claim.get("subject")),
            relation=claim.get("relation"),
            object_id=_entity_id(claim.get("object")),
            evidence_ids=list(claim.get("evidence_ids") or []),
            provider=bundle.provider,
            model=bundle.model,
            prompt_ref=bundle.prompt_ref,
            prompt_version=bundle.prompt_version,
            tokens_prompt=bundle.tokens_prompt,
            tokens_completion=bundle.tokens_completion,
            latency_ms=bundle.latency_ms,
        )

    def _verify_record(self, seq: int, claim: dict, verdict: dict) -> AttemptRecord:
        return AttemptRecord(
            attempt_number=seq,
            stage="verify",
            proposed_claim=claim,
            claim_id=claim.get("claim_id"),
            subject_id=_entity_id(claim.get("subject")),
            relation=claim.get("relation"),
            object_id=_entity_id(claim.get("object")),
            evidence_ids=list(claim.get("evidence_ids") or []),
            verdict=verdict.get("verdict"),
            fault_code=verdict.get("fault_code"),
            reasons=list(verdict.get("reasons") or []),
        )

    def _repair_record(self, seq: int, repaired_claim: dict, result: Any) -> AttemptRecord:
        return AttemptRecord(
            attempt_number=seq,
            stage="repair",
            proposed_claim=repaired_claim,
            claim_id=repaired_claim.get("claim_id"),
            subject_id=_entity_id(repaired_claim.get("subject")),
            relation=repaired_claim.get("relation"),
            object_id=_entity_id(repaired_claim.get("object")),
            evidence_ids=list(repaired_claim.get("evidence_ids") or []),
            provider=result.provider,
            model=result.model,
            prompt_ref=result.prompt_ref,
            prompt_version=result.prompt_version,
            tokens_prompt=result.tokens_prompt,
            tokens_completion=result.tokens_completion,
            latency_ms=result.latency_ms,
            note=result.reason or None,
        )

    def _repair_abstain_record(self, seq: int, failed_claim: dict, result: Any) -> AttemptRecord:
        return AttemptRecord(
            attempt_number=seq,
            stage="repair_abstain",
            claim_id=failed_claim.get("claim_id"),
            provider=result.provider,
            model=result.model,
            prompt_ref=result.prompt_ref,
            prompt_version=result.prompt_version,
            tokens_prompt=result.tokens_prompt,
            tokens_completion=result.tokens_completion,
            latency_ms=result.latency_ms,
            note=result.reason,
        )


def _aggregate_status(claim_statuses: list[str]) -> Status:
    """Fold one status per claim into the run-level summary.

    # PHASE4B-DECISION: neither the task brief nor spec/non_goals.md
    # defines multi-claim aggregation (every listed test scenario is a
    # single-claim bundle). Priority order chosen: any `checker_error`
    # dominates (fail-closed); else any `abstained` dominates (the
    # repairer explicitly declined on at least one claim); else
    # `accepted` only if every claim in the bundle was accepted;
    # otherwise `rejected_exhausted`.
    """
    if not claim_statuses:
        return "rejected_exhausted"
    if "checker_error" in claim_statuses:
        return "checker_error"
    if "abstained" in claim_statuses:
        return "abstained"
    if all(s == "accepted" for s in claim_statuses):
        return "accepted"
    return "rejected_exhausted"


def _fresh_trajectory_id() -> str:
    import uuid

    return str(uuid.uuid4())
