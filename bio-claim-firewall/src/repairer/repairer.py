"""`Repairer`: attempts to fix one REJECTED claim, or abstains.

Shape adapted from MIDAS `verification_orchestrator.py:171-293`'s
`_attempt_reasoning_repair` (build feedback from the failed attempt +
verifier result, call the model, parse its response through the same
strict contract parser as the original proposal, return `None` on any
contract violation rather than propagating a half-repaired result). Rewritten
fresh for the biology domain: no reasoning-step feedback text, no LaTeX;
feedback is the raw `verdict` dict (`fault_code`, `reasons`) plus the cited
`evidence_records`, and the model's response contract is the closed
two-shape union `{"repaired_claim": {...}}` | `{"abstain": true, "reason":
"..."}` rather than free-form repair prose.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import RepairerError
from .types import RepairResult

try:  # pragma: no cover - exercised once Phase 4a lands `src/model_manager`
    from model_manager import ChatRequest, ChatResponse, ModelManager
except ImportError:  # pragma: no cover - fallback path, exercised today
    from dataclasses import dataclass
    from typing import Protocol, runtime_checkable

    @dataclass(frozen=True)
    class ChatResponse:  # type: ignore[no-redef]
        content: str
        provider: str
        model: str
        prompt_ref: str
        prompt_version: str
        latency_ms: int
        tokens_prompt: int
        tokens_completion: int

    ChatRequest = Any  # type: ignore[assignment,misc]

    @runtime_checkable
    class ModelManager(Protocol):  # type: ignore[no-redef]
        def call(
            self,
            task: str,
            user_msg: str,
            *,
            system_msg: str | None = None,
            max_tokens: int | None = None,
            temperature: float | None = None,
            timeout_s: float | None = None,
            prompt_ref: str | None = None,
        ) -> ChatResponse: ...


_SPEC_DIR = Path(__file__).resolve().parents[2] / "spec"


def _load_required_top_level_fields() -> tuple[str, ...]:
    schema = json.loads((_SPEC_DIR / "claim.schema.json").read_text(encoding="utf-8"))
    return tuple(schema["required"])


_SYSTEM_MSG = (
    "A biological claim you or a peer proposer emitted was rejected by the "
    "deterministic checker. You are given the failed claim, the checker's "
    "verdict, and the evidence records available. Respond with a single "
    "JSON object: either {\"repaired_claim\": <schema-valid claim>} if you "
    "can produce a claim the evidence actually supports, or "
    "{\"abstain\": true, \"reason\": \"<why no repair is possible>\"} "
    "otherwise. Emit no prose outside that JSON object."
)


class Repairer:
    """Calls the untrusted repair model and parses its response into a
    `RepairResult`. Never lets model output reach the verifier as anything
    other than a plain `dict` -- no `exec`, no `eval`, no dynamic dispatch
    on any string in the response.
    """

    def __init__(self, mm: ModelManager, prompt_ref: str = "repairer/claim_repair@v1") -> None:
        self.mm = mm
        self.prompt_ref = prompt_ref
        self._required_fields = _load_required_top_level_fields()

    def repair(self, failed_claim: dict, verdict: dict, evidence_records: list[dict]) -> RepairResult:
        user_msg = self._build_user_msg(failed_claim, verdict, evidence_records)
        response = self.mm.call(
            task="repairer",
            user_msg=user_msg,
            system_msg=_SYSTEM_MSG,
            prompt_ref=self.prompt_ref,
        )

        claim, abstained, reason = self._parse_response(response.content)

        return RepairResult(
            claim=claim,
            abstained=abstained,
            reason=reason,
            prompt_ref=response.prompt_ref,
            prompt_version=response.prompt_version,
            provider=response.provider,
            model=response.model,
            tokens_prompt=response.tokens_prompt,
            tokens_completion=response.tokens_completion,
            latency_ms=response.latency_ms,
        )

    # -- internal -----------------------------------------------------

    def _build_user_msg(self, failed_claim: dict, verdict: dict, evidence_records: list[dict]) -> str:
        payload = {
            "failed_claim": failed_claim,
            "verdict": verdict,
            "evidence_records": evidence_records,
        }
        return json.dumps(payload, sort_keys=True)

    def _parse_response(self, content: str) -> tuple[dict | None, bool, str]:
        try:
            parsed = json.loads(content.strip())
        except json.JSONDecodeError as exc:
            raise RepairerError(
                "contract_violated",
                f"repairer response is not valid JSON: {exc}",
                raw_response=content,
            ) from exc

        if not isinstance(parsed, dict):
            raise RepairerError(
                "contract_violated",
                f"repairer response must be a single JSON object (got {type(parsed).__name__})",
                raw_response=content,
            )

        has_repaired = "repaired_claim" in parsed
        has_abstain = "abstain" in parsed

        if has_repaired and has_abstain:
            raise RepairerError(
                "contract_violated",
                "repairer response must contain exactly one of "
                "'repaired_claim' or 'abstain', got both",
                raw_response=content,
            )

        if has_abstain:
            if parsed.get("abstain") is not True:
                raise RepairerError(
                    "contract_violated",
                    f"repairer response 'abstain' must be literal true, got {parsed.get('abstain')!r}",
                    raw_response=content,
                )
            reason = parsed.get("reason")
            if not isinstance(reason, str) or not reason:
                raise RepairerError(
                    "contract_violated",
                    "repairer abstain response is missing a non-empty 'reason'",
                    raw_response=content,
                )
            return None, True, reason

        if has_repaired:
            repaired_claim = parsed["repaired_claim"]
            if not isinstance(repaired_claim, dict):
                raise RepairerError(
                    "contract_violated",
                    f"'repaired_claim' must be a JSON object (got {type(repaired_claim).__name__})",
                    raw_response=content,
                )
            missing = [f for f in self._required_fields if f not in repaired_claim]
            if missing:
                raise RepairerError(
                    "contract_violated",
                    f"repaired_claim is missing required field(s): {', '.join(missing)}",
                    raw_response=content,
                    missing_fields=missing,
                )
            return repaired_claim, False, str(parsed.get("reason", ""))

        raise RepairerError(
            "contract_violated",
            "repairer response must contain either 'repaired_claim' or 'abstain'",
            raw_response=content,
        )
