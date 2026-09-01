"""Constrain one natural-language K562 claim before deterministic checking.

The model at this boundary is an untrusted parser, never an evidence source or
verdict authority. It may only return an exact gene pair and one direction;
the frozen evidence ledger and deterministic verifier remain responsible for
every biological result returned to the caller.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .service import ClaimCheckInputError, ClaimCheckResult, check_k562_claim
from .service import _attach_receipt, check_claim
from worlds import WORLD_REGISTRY, WorldRegistry, WorldRegistryError


_PARSER_TASK = "claim_parser"
_REQUIRED_KEYS = frozenset(("subject", "object", "direction"))
_MAX_QUESTION_CHARS = 2_000


class ClaimParserManager(Protocol):
    """The narrow model-manager surface this boundary needs."""

    def call(self, *, task: str, variables: dict[str, str]) -> Any: ...


@dataclass(frozen=True, slots=True)
class NaturalLanguageClaimCheckResult:
    """A transparent untrusted interpretation paired with a verified result."""

    interpretation: dict[str, str]
    result: ClaimCheckResult

    def as_dict(self) -> dict[str, Any]:
        """Return the parser provenance and deterministic checker output."""
        return {"interpretation": self.interpretation, **self.result.as_dict()}


def check_natural_language_k562_claim(
    bundle: Any,
    question: str,
    manager: ClaimParserManager,
    *,
    checker_version: str = "0.1.0",
) -> NaturalLanguageClaimCheckResult:
    """Check a one-sentence K562 gene-effect claim through a strict parser.

    The parser may only reduce the user sentence to ``subject``, ``object``,
    and ``direction``. Any malformed or expanded response raises a local input
    error; model prose, citations, confidence, and verdicts never reach the
    deterministic checker.
    """
    if not isinstance(question, str) or not question.strip():
        raise ClaimCheckInputError(
            "natural-language claim must be a non-empty sentence"
        )
    if len(question) > _MAX_QUESTION_CHARS:
        raise ClaimCheckInputError(
            f"natural-language claim exceeds {_MAX_QUESTION_CHARS:,} character limit"
        )

    parsed, interpretation = _parse_question(question.strip(), manager)
    result = check_k562_claim(
        bundle,
        parsed["subject"],
        parsed["object"],
        parsed["direction"],
        checker_version=checker_version,
    )
    return NaturalLanguageClaimCheckResult(interpretation=interpretation, result=result)


def check_natural_language_claim(
    bundle: Any,
    world_id: str,
    world_version: str | None,
    question: str,
    manager: ClaimParserManager,
    *,
    checker_version: str = "0.1.0",
    registry: WorldRegistry = WORLD_REGISTRY,
) -> NaturalLanguageClaimCheckResult:
    """Parse a question only after explicit world selection.

    The model receives the caller's text and the selected world's closed
    parser schema. It never receives evidence, citations, receipts, or other
    worlds, and its output is passed through the same structured checker as a
    non-LLM call.
    """
    try:
        world = registry.resolve(world_id, world_version)
    except WorldRegistryError as exc:
        raise ClaimCheckInputError(str(exc)) from exc
    if not isinstance(question, str) or not question.strip():
        raise ClaimCheckInputError("natural-language claim must be a non-empty sentence")
    if len(question) > _MAX_QUESTION_CHARS:
        raise ClaimCheckInputError(f"natural-language claim exceeds {_MAX_QUESTION_CHARS:,} character limit")
    parsed, interpretation = _parse_world_question(question.strip(), manager, world.claim_fields, world.parser_schema)
    result = check_claim(
        bundle,
        world.world_id,
        world.version,
        parsed,
        checker_version=checker_version,
        registry=registry,
    )
    # Parser provenance is deliberately attached after receipt construction;
    # _attach_receipt excludes it from the canonical payload.
    result = _attach_receipt(
        result,
        world,
        bundle,
        checker_version=checker_version,
        parser_provenance=interpretation,
        strict_bundle=True,
    )
    return NaturalLanguageClaimCheckResult(interpretation=interpretation, result=result)


def _parse_question(
    question: str, manager: ClaimParserManager
) -> tuple[dict[str, str], dict[str, str]]:
    response = manager.call(task=_PARSER_TASK, variables={"question": question})
    content = getattr(response, "content", None)
    if not isinstance(content, str):
        raise ClaimCheckInputError(
            "natural-language parser did not return subject, object, and direction JSON"
        )

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ClaimCheckInputError(
            "natural-language parser did not return subject, object, and direction JSON"
        ) from exc

    if not isinstance(parsed, dict) or set(parsed) != _REQUIRED_KEYS:
        raise ClaimCheckInputError(
            "natural-language parser must return exactly subject, object, and direction"
        )
    if any(
        not isinstance(parsed[key], str) or not parsed[key].strip()
        for key in _REQUIRED_KEYS
    ):
        raise ClaimCheckInputError(
            "natural-language parser must return non-empty subject, object, and direction"
        )

    components = {key: parsed[key].strip() for key in _REQUIRED_KEYS}
    return components, _interpretation_metadata(response, question, components)


def _parse_world_question(
    question: str,
    manager: ClaimParserManager,
    claim_fields: tuple[str, ...],
    parser_schema: Mapping[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    response = manager.call(
        task=_PARSER_TASK,
        variables={"question": question, "schema": json.dumps(dict(parser_schema), sort_keys=True)},
    )
    content = getattr(response, "content", None)
    if not isinstance(content, str):
        raise ClaimCheckInputError("natural-language parser did not return the selected world's claim JSON")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ClaimCheckInputError("natural-language parser did not return the selected world's claim JSON") from exc
    required = frozenset(claim_fields)
    if not isinstance(parsed, dict) or set(parsed) != required:
        raise ClaimCheckInputError("natural-language parser returned fields outside the selected world's claim schema")
    if any(not isinstance(parsed[key], str) or not parsed[key].strip() for key in required):
        raise ClaimCheckInputError("natural-language parser returned an empty claim field")
    components = {key: parsed[key].strip() for key in claim_fields}
    return components, _interpretation_metadata(response, question, components)


def _interpretation_metadata(
    response: Any, question: str, components: dict[str, str]
) -> dict[str, str]:
    meta = getattr(response, "meta", {})
    metadata = meta if isinstance(meta, dict) else {}
    prompt_ref = getattr(response, "prompt_ref", None)
    return {
        "mode": "untrusted_llm",
        "question": question,
        **components,
        "provider": _metadata_string(metadata, "provider", "unknown"),
        "model": _metadata_string(metadata, "model", "unknown"),
        "prompt_ref": prompt_ref if isinstance(prompt_ref, str) else "unknown",
    }


def _metadata_string(metadata: dict[str, Any], key: str, fallback: str) -> str:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else fallback
