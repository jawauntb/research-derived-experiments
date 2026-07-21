"""Claim extraction from prose plans.

Scaffold layer: a deterministic rule-based extractor for CI, plus a
``ClaimExtractor`` Protocol for the Week-2 live-model extractor to
implement. No live provider paths here.

The rule-based extractor recognizes obligation-shaped sentences
("must X", "should Y", "requires Z") because those are what the CT
task families in ``experiments/grounded_statecharts`` produce; a
richer extractor is out of scope for the scaffold.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable, Protocol

from experiments.load_bearing_prose_test.claims import Claim, ClaimBundle


class ClaimExtractor(Protocol):
    """Interface every extractor must satisfy."""

    def extract(self, *, plan_id: str, plan_text: str) -> ClaimBundle: ...


# Ordered so longer forms match first (avoids "must" swallowing "must not").
_MODAL_PATTERNS: tuple[str, ...] = (
    r"must not\b",
    r"must\b",
    r"shall not\b",
    r"shall\b",
    r"should not\b",
    r"should\b",
    r"will not\b",
    r"will\b",
    r"requires\b",
    r"required to\b",
    r"needs to\b",
    r"forbidden to\b",
    r"not allowed to\b",
    r"allowed to\b",
)

_MODAL_REGEX = re.compile("|".join(_MODAL_PATTERNS), re.IGNORECASE)

# Sentence splitter: split on `.`, `!`, `?` followed by whitespace/EOL, or
# on a bare newline. Newlines are preserved as separators so bullet-list
# plans extract cleanly.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


@dataclass(frozen=True)
class KappaVocabulary:
    """Terms whose presence in a claim marks it as κ-mentioning.

    ``capabilities`` and ``artifacts`` come from the CT task fixture
    (``forbidden_capabilities``, ``required_capabilities``,
    ``required_artifact``). ``keywords`` are the shared vocabulary of
    the harness contract (evidence, approval, commit, etc.).
    """

    capabilities: frozenset[str]
    artifacts: frozenset[str]
    keywords: frozenset[str]

    def matches(self, text: str) -> tuple[str, ...]:
        lower = text.lower()
        hits: list[str] = []
        for term in sorted(self.capabilities):
            if term.lower() in lower:
                hits.append(term)
        for term in sorted(self.artifacts):
            if term.lower() in lower:
                hits.append(term)
        for term in sorted(self.keywords):
            if term.lower() in lower:
                hits.append(term)
        seen: set[str] = set()
        deduped: list[str] = []
        for hit in hits:
            if hit not in seen:
                seen.add(hit)
                deduped.append(hit)
        return tuple(deduped)


DEFAULT_KAPPA_KEYWORDS: frozenset[str] = frozenset(
    {"approval", "approve", "evidence", "commit", "artifact", "delegate", "envelope"}
)


def default_kappa_vocabulary(
    *,
    capabilities: Iterable[str] = (),
    artifacts: Iterable[str] = (),
    keywords: Iterable[str] = DEFAULT_KAPPA_KEYWORDS,
) -> KappaVocabulary:
    return KappaVocabulary(
        capabilities=frozenset(capabilities),
        artifacts=frozenset(artifacts),
        keywords=frozenset(keywords),
    )


def _plan_digest(plan_text: str) -> str:
    return hashlib.sha256(plan_text.encode()).hexdigest()


def _iter_sentences(plan_text: str) -> Iterable[tuple[int, int, str]]:
    """Yield ``(start_offset, end_offset, sentence_text)`` for each sentence.

    Offsets are into the original ``plan_text`` so ablation transforms
    can slice deterministically.
    """

    cursor = 0
    for chunk in _SENTENCE_SPLIT.split(plan_text):
        if not chunk:
            # Preserve cursor progress across empty splits.
            cursor = plan_text.find("\n", cursor)
            if cursor == -1:
                return
            cursor += 1
            continue
        start = plan_text.find(chunk, cursor)
        if start == -1:
            # Fall back to appending sequentially; keeps offsets monotone.
            start = cursor
        end = start + len(chunk)
        cursor = end
        yield start, end, chunk


class RuleBasedExtractor:
    """Deterministic obligation-shape extractor used in CI and tests."""

    def __init__(self, *, kappa: KappaVocabulary | None = None) -> None:
        self._kappa = kappa or default_kappa_vocabulary()

    def extract(self, *, plan_id: str, plan_text: str) -> ClaimBundle:
        if not isinstance(plan_id, str) or not plan_id:
            raise ValueError("plan_id must be a non-empty string")
        if not isinstance(plan_text, str) or not plan_text:
            raise ValueError("plan_text must be a non-empty string")

        claims: list[Claim] = []
        for index, (start, end, sentence) in enumerate(_iter_sentences(plan_text)):
            stripped = sentence.strip()
            if not stripped:
                continue
            if _MODAL_REGEX.search(stripped) is None:
                continue
            kappa_terms = self._kappa.matches(stripped)
            claim_id = f"{plan_id}::c{index:03d}"
            claims.append(
                Claim(
                    claim_id=claim_id,
                    text=stripped,
                    start_offset=start,
                    end_offset=end,
                    kappa_terms=kappa_terms,
                )
            )

        return ClaimBundle(
            plan_id=plan_id,
            plan_digest=_plan_digest(plan_text),
            claims=tuple(claims),
        )


def rule_based_extractor(
    *,
    capabilities: Iterable[str] = (),
    artifacts: Iterable[str] = (),
    keywords: Iterable[str] = DEFAULT_KAPPA_KEYWORDS,
) -> ClaimExtractor:
    return RuleBasedExtractor(
        kappa=default_kappa_vocabulary(
            capabilities=capabilities, artifacts=artifacts, keywords=keywords
        )
    )
