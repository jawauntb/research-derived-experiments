"""`Proposer`: turns a question + evidence records into a `ClaimBundle`.

Adapted (schema-wrapper shape only, per PHASE_4_PLAN.md) from MIDAS
`src/pipeline/reasoning/reasoning.py`'s `ReasoningPipeline` -- in particular
the "call the model, then run its response through one strict, hand-written
contract parser that raises a typed contract-error class on any violation"
shape (MIDAS lines 22-39 the error class, 79-104 the call+parse pipeline,
106-201 the parse/validate logic, 294-323 the contract-error raise site).
Everything MIDAS-specific is rewritten fresh: no XML `<solution>` parsing,
no `<think>` stripping, no LaTeX `\\boxed{}` extraction -- this proposer is
JSON-schema-shaped from day one (PHASE_4_PLAN.md's "Coupling to strip").

# PHASE4B-DECISION (proposer-side contract scope): `spec/claim.schema.json`
# is the checker's full JSON-Schema contract (CURIE patterns, relation
# enum, evidence_ids non-empty, etc) -- re-validating all of that here
# would duplicate `src/verifier`'s own validator and blur the fault-split
# invariant ("that is a proposer problem, not a checker gap" per
# spec/fault_taxonomy.md's header). This module's own contract check is
# deliberately narrower: is the response parseable as a JSON array of
# objects, and does each object have every *top-level* required key from
# `claim.schema.json`? A claim that's syntactically complete but
# semantically wrong (bad CURIE prefix, wrong relation, empty
# evidence_ids, ...) is NOT a `ProposerError` -- it's a legitimate `Claim`
# dict that flows to `verify()` and comes back `REJECTED_<FAULT_CODE>`.
# Read live off `spec/claim.schema.json`'s own `"required"` array (never
# hardcoded) so a future schema-version bump never silently drifts out of
# sync with this check.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .errors import ProposerError
from .types import ClaimBundle

try:  # pragma: no cover - exercised by the bare-package adapter tests
    from model_manager import ModelManager, adapt_model_manager
except ImportError:
    try:  # pragma: no cover - exercised by the src-package adapter test
        from src.model_manager import ModelManager, adapt_model_manager
    except ImportError:  # pragma: no cover - lightweight fake fallback
        from typing import Protocol, runtime_checkable

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
            ) -> Any: ...

        def adapt_model_manager(manager: Any) -> Any:
            return manager


_SPEC_DIR = Path(__file__).resolve().parents[2] / "spec"

# Fixed namespace UUID for the deterministic client-side `claim_id` fill-in
# (uuid5(namespace, canonical_key)). Any fixed UUID constant works here --
# what matters is that it never changes across runs, so the same
# (question, subject, relation, object, evidence_ids) tuple always mints
# the same claim_id (see test_proposer_deterministic_uuid.py).
_CLAIM_ID_NAMESPACE = uuid.UUID("6f5e2b1a-6f1e-4b7a-9c1d-9d6a5f6b8c2a")

_UUID_HEX = frozenset("0123456789abcdefABCDEF-")


def _load_required_top_level_fields() -> tuple[str, ...]:
    schema = json.loads((_SPEC_DIR / "claim.schema.json").read_text(encoding="utf-8"))
    return tuple(schema["required"])


class Proposer:
    """Calls the untrusted proposer model and parses its response into a
    contract-checked `ClaimBundle`. Never lets model output reach the
    verifier as anything other than a plain `dict` -- no `exec`, no
    `eval`, no dynamic dispatch on any string in the response.
    """

    def __init__(self, mm: ModelManager, prompt_ref: str = "proposer/claim_bundle@v1") -> None:
        self.mm = adapt_model_manager(mm)
        self.prompt_ref = prompt_ref
        self._required_fields = _load_required_top_level_fields()

    def propose(
        self,
        question: str,
        evidence_records: list[dict],
        context_hints: dict | None = None,
    ) -> ClaimBundle:
        user_msg = self._build_user_msg(question, evidence_records, context_hints)
        response = self.mm.call(
            task="proposer",
            user_msg=user_msg,
            system_msg=_SYSTEM_MSG,
            prompt_ref=self.prompt_ref,
        )

        claims = self._parse_response(response.content, question=question)

        return ClaimBundle(
            claims=tuple(claims),
            prompt_ref=response.prompt_ref,
            prompt_version=response.prompt_version,
            provider=response.provider,
            model=response.model,
            tokens_prompt=response.tokens_prompt,
            tokens_completion=response.tokens_completion,
            latency_ms=response.latency_ms,
        )

    # -- internal -----------------------------------------------------

    def _build_user_msg(
        self,
        question: str,
        evidence_records: list[dict],
        context_hints: dict | None,
    ) -> str:
        # The Phase 4b-shaped interface takes one `user_msg` string. For
        # lightweight fakes, this deterministic envelope is the whole
        # request. For a real manager, ModelManagerAdapter validates and
        # expands the same envelope into the configured versioned prompt's
        # {question, evidence_records, context_hints} variables.
        payload = {
            "question": question,
            "evidence_records": evidence_records,
            "context_hints": context_hints or {},
        }
        return json.dumps(payload, sort_keys=True)

    def _parse_response(self, content: str, *, question: str) -> list[dict]:
        try:
            parsed = json.loads(content.strip())
        except json.JSONDecodeError as exc:
            raise ProposerError(
                "contract_violated",
                f"proposer response is not valid JSON: {exc}",
                raw_response=content,
            ) from exc

        if not isinstance(parsed, list):
            raise ProposerError(
                "contract_violated",
                "proposer response must be a single JSON array of claim objects "
                f"(got {type(parsed).__name__}); prose outside the array is not allowed",
                raw_response=content,
            )

        claims: list[dict] = []
        for index, item in enumerate(parsed):
            if not isinstance(item, dict):
                raise ProposerError(
                    "contract_violated",
                    f"claim at index {index} is not a JSON object (got {type(item).__name__})",
                    raw_response=content,
                    claim_index=index,
                )
            claims.append(self._check_and_fix_claim(item, index, question=question, raw_response=content))

        return claims

    def _check_and_fix_claim(
        self, claim: dict, index: int, *, question: str, raw_response: str
    ) -> dict:
        missing = [f for f in self._required_fields if f not in claim]
        if missing:
            raise ProposerError(
                "contract_violated",
                f"claim at index {index} is missing required field(s): {', '.join(missing)}",
                raw_response=raw_response,
                claim_index=index,
                missing_fields=missing,
            )

        claim_id = claim.get("claim_id")
        if not isinstance(claim_id, str) or not _looks_like_uuid(claim_id):
            claim = dict(claim)
            claim["claim_id"] = self._deterministic_claim_id(question, claim)

        return claim

    def _deterministic_claim_id(self, question: str, claim: dict) -> str:
        subject = claim.get("subject")
        object_ = claim.get("object")
        subject_id = subject.get("id", "") if isinstance(subject, dict) else ""
        object_id = object_.get("id", "") if isinstance(object_, dict) else ""
        relation = claim.get("relation", "")
        evidence_ids = claim.get("evidence_ids", [])
        if not isinstance(evidence_ids, list):
            evidence_ids = [evidence_ids]
        # PHASE4B-DECISION: the task spells the canonical key as
        # "question + subject.id + relation + object.id + evidence_ids
        # joined" -- joined with "|" separators here (rather than naive
        # string concatenation) so distinct field boundaries can never
        # collide (e.g. subject_id="AB", relation="C" vs subject_id="A",
        # relation="BC" would otherwise hash identically).
        canonical_key = "|".join(
            [question, str(subject_id), str(relation), str(object_id), ",".join(str(e) for e in evidence_ids)]
        )
        return str(uuid.uuid5(_CLAIM_ID_NAMESPACE, canonical_key))


def _looks_like_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return True


_SYSTEM_MSG = (
    "You propose biological claims for independent verification against a "
    "frozen evidence ledger. Respond with a single JSON array of claim "
    "objects conforming to the claim schema. Emit no prose outside the "
    "array."
)
