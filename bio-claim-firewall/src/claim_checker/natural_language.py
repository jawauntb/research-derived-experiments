"""Constrain one natural-language K562 claim before deterministic checking.

The model at this boundary is an untrusted parser, never an evidence source or
verdict authority. It may only return an exact gene pair and one direction;
the frozen evidence ledger and deterministic verifier remain responsible for
every biological result returned to the caller.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from worlds import WORLD_REGISTRY, WorldRegistry, WorldRegistryError

from .service import (
    ClaimCheckInputError,
    ClaimCheckResult,
    _attach_receipt,
    check_claim,
    check_k562_claim,
)

_PARSER_TASK = "claim_parser"
_REQUIRED_KEYS = frozenset(("subject", "object", "direction"))
_MAX_QUESTION_CHARS = 2_000
_DIRECTIONAL_PREDICATE_PATTERN = (
    r"(?:increase|increases|increased|raise|raises|raised|"
    r"upregulate|upregulates|upregulated|elevate|elevates|elevated|"
    r"decrease|decreases|decreased|reduce|reduces|reduced|"
    r"lower|lowers|lowered|downregulate|downregulates|downregulated|"
    r"suppress|suppresses|suppressed)"
)
_DIRECTIONAL_PREDICATE = re.compile(
    rf"\b{_DIRECTIONAL_PREDICATE_PATTERN}\b", re.IGNORECASE
)
_INCREASE_PREDICATES = frozenset(
    {
        "increase",
        "increases",
        "increased",
        "raise",
        "raises",
        "raised",
        "upregulate",
        "upregulates",
        "upregulated",
        "elevate",
        "elevates",
        "elevated",
    }
)
_DECREASE_PREDICATES = frozenset(
    {
        "decrease",
        "decreases",
        "decreased",
        "reduce",
        "reduces",
        "reduced",
        "lower",
        "lowers",
        "lowered",
        "downregulate",
        "downregulates",
        "downregulated",
        "suppress",
        "suppresses",
        "suppressed",
    }
)
_KNOCKDOWN_TOKEN = re.compile(r"\bknockdown\b", re.IGNORECASE)
_GENE_SYMBOL_PATTERN = r"[A-Za-z][A-Za-z0-9-]*"
_SUPPORTED_K562_CLAUSES = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        rf"\A\s*Within\s+K562\s+cells?,\s*"
        rf"(?P<subject>{_GENE_SYMBOL_PATTERN})\s+knockdown\s+"
        rf"(?P<direction>{_DIRECTIONAL_PREDICATE_PATTERN})\s+"
        rf"(?P<object>{_GENE_SYMBOL_PATTERN})\s+expression[.?!]?\s*\Z",
        rf"\A\s*(?P<subject>{_GENE_SYMBOL_PATTERN})\s+knockdown\s+"
        rf"(?P<direction>{_DIRECTIONAL_PREDICATE_PATTERN})\s+"
        rf"(?P<object>{_GENE_SYMBOL_PATTERN})\s+expression\s+in\s+"
        rf"K562(?:\s+cells?)?[.?!]?\s*\Z",
        rf"\A\s*Does\s+(?P<subject>{_GENE_SYMBOL_PATTERN})\s+knockdown\s+"
        rf"(?P<direction>{_DIRECTIONAL_PREDICATE_PATTERN})\s+"
        rf"(?P<object>{_GENE_SYMBOL_PATTERN})\s+expression\s+in\s+"
        rf"K562(?:\s+cells?)?\?\s*\Z",
    )
)


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
    _validate_directional_predicate_count(question)
    input_claim = _validate_k562_input_scope(question)
    parsed, interpretation = _parse_question(question.strip(), manager)
    _validate_k562_question(question, parsed, bundle, input_claim)
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
        raise ClaimCheckInputError(
            "natural-language claim must be a non-empty sentence"
        )
    if len(question) > _MAX_QUESTION_CHARS:
        raise ClaimCheckInputError(
            f"natural-language claim exceeds {_MAX_QUESTION_CHARS:,} character limit"
        )
    if world.adapter == "k562":
        _validate_directional_predicate_count(question)
        input_claim = _validate_k562_input_scope(question)
    else:
        input_claim = None
    parsed, interpretation = _parse_world_question(
        question.strip(), manager, world.claim_fields, world.parser_schema
    )
    if world.adapter == "k562":
        assert input_claim is not None
        _validate_k562_question(question, parsed, bundle, input_claim)
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


def _validate_k562_question(
    question: str,
    parsed: Mapping[str, str],
    bundle: Any,
    input_claim: Mapping[str, str],
) -> None:
    """Bind the untrusted K562 parse to the words the caller submitted.

    A parser response is not allowed to introduce a second claim, change the
    direction, or cite entities absent from the input.  The final deterministic
    checker still owns entity resolution and evidence lookup; this helper only
    closes the parser trust boundary before its output is used.
    """
    predicates = _validate_directional_predicate_count(question)

    input_direction = _direction_family(predicates[0])
    parsed_direction = _direction_family(parsed.get("direction", ""))
    if input_direction is None or parsed_direction != input_direction:
        raise ClaimCheckInputError(
            "natural-language parser direction does not match the submitted claim"
        )

    if any(
        parsed.get(field, "").strip().casefold()
        != input_claim[field].strip().casefold()
        for field in ("subject", "object")
    ):
        raise ClaimCheckInputError(
            "natural-language parser gene roles do not match the supported claim"
        )

    parsed_entities = set()
    entity_spans: dict[str, tuple[tuple[int, int], ...]] = {}
    for field in ("subject", "object"):
        value = parsed.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ClaimCheckInputError(
                "natural-language parser must return non-empty subject and object"
            )
        value = value.strip()
        parsed_entities.add(value.casefold())
        spans = _whole_token_spans(question, value)
        entity_spans[field] = spans
        if len(spans) != 1:
            raise ClaimCheckInputError(
                f"natural-language parser {field} must occur exactly once in the "
                "submitted claim"
            )

    if len(parsed_entities) != 2:
        raise ClaimCheckInputError(
            "natural-language parser subject and object must be distinct"
        )

    predicate_match = next(_DIRECTIONAL_PREDICATE.finditer(question))
    knockdown_match = next(_KNOCKDOWN_TOKEN.finditer(question))
    subject_span = entity_spans["subject"][0]
    object_span = entity_spans["object"][0]
    supported_order = (
        subject_span[1] <= knockdown_match.start()
        and knockdown_match.end() <= predicate_match.start()
        and predicate_match.end() <= object_span[0]
    )
    if not supported_order:
        raise ClaimCheckInputError(
            "natural-language parser subject/object roles do not match the "
            "supported active-voice claim"
        )

    known_labels = _known_hgnc_labels(bundle)
    mentioned_labels = {
        label for label in known_labels if _contains_whole_token(question, label)
    }
    extras = sorted(mentioned_labels - parsed_entities)
    if extras:
        raise ClaimCheckInputError(
            "natural-language input mentions known HGNC entities outside the parsed "
            f"subject/object pair: {', '.join(extras)}"
        )


def _validate_k562_input_scope(question: str) -> dict[str, str]:
    """Parse only the complete positive grammar accepted by the K562 route."""
    for pattern in _SUPPORTED_K562_CLAUSES:
        match = pattern.fullmatch(question)
        if match is not None:
            return {key: value for key, value in match.groupdict().items()}
    raise ClaimCheckInputError(
        "natural-language K562 claim is outside the supported single-clause grammar"
    )


def _validate_directional_predicate_count(question: str) -> list[str]:
    predicates = _DIRECTIONAL_PREDICATE.findall(question)
    if len(predicates) != 1:
        raise ClaimCheckInputError(
            "natural-language input must contain exactly one directional claim"
        )
    return predicates


def _direction_family(value: str) -> str | None:
    normalized = value.strip().casefold()
    if normalized in _INCREASE_PREDICATES:
        return "increase"
    if normalized in _DECREASE_PREDICATES:
        return "decrease"
    return None


def _contains_whole_token(question: str, value: str) -> bool:
    return bool(_whole_token_spans(question, value))


def _whole_token_spans(question: str, value: str) -> tuple[tuple[int, int], ...]:
    pattern = r"(?<!\w)" + re.escape(value.strip()) + r"(?!\w)"
    return tuple(
        (match.start(), match.end())
        for match in re.finditer(pattern, question, re.IGNORECASE)
    )


def _known_hgnc_labels(bundle: Any) -> frozenset[str]:
    labels = getattr(bundle, "labels", None)
    if not isinstance(labels, Mapping):
        return frozenset()
    return frozenset(
        label.strip().casefold()
        for curie, label in labels.items()
        if isinstance(curie, str)
        and curie.startswith("HGNC:")
        and isinstance(label, str)
        and label.strip()
    )


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
        variables={
            "question": question,
            "schema": json.dumps(dict(parser_schema), sort_keys=True),
        },
    )
    content = getattr(response, "content", None)
    if not isinstance(content, str):
        raise ClaimCheckInputError(
            "natural-language parser did not return the selected world's claim JSON"
        )
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ClaimCheckInputError(
            "natural-language parser did not return the selected world's claim JSON"
        ) from exc
    required = frozenset(claim_fields)
    if not isinstance(parsed, dict) or set(parsed) != required:
        raise ClaimCheckInputError(
            "natural-language parser returned fields outside the selected world's claim schema"
        )
    if any(
        not isinstance(parsed[key], str) or not parsed[key].strip() for key in required
    ):
        raise ClaimCheckInputError(
            "natural-language parser returned an empty claim field"
        )
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
