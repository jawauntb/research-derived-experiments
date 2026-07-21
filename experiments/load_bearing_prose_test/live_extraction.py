"""Optional live-model claim extractor (env-gated, imported lazily).

Off by default and never touched by CI. When ``LBPT_LIVE=1`` is set,
:class:`LiveClaimExtractor` calls the CT live adapter via
``LiveExecutor.complete_messages`` to atomize a plan into atomic
predicate-shaped claims returned as strict JSON.

The rule-based extractor stays the default oracle. This module exists
so Week 3 paraphrase-quality and κ-inference work can slot in
without a separate live adapter.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import hashlib

from experiments.load_bearing_prose_test.claims import Claim, ClaimBundle
from experiments.load_bearing_prose_test.extraction import (
    KappaVocabulary,
    default_kappa_vocabulary,
)


LBPT_LIVE_OPT_IN_ENV = "LBPT_LIVE"


def _system_prompt() -> str:
    return (
        "You extract atomic obligation-shaped claims from an agent plan. "
        "Return ONLY a JSON object of the form "
        '{"claims":[{"text":"..."}, ...]}. '
        "Each claim must be a single obligation sentence that names a "
        "modal verb (must, should, will, requires, forbidden, allowed). "
        "Do not include decorative sentences or headings. "
        "Do not wrap the JSON in markdown."
    )


def _user_prompt(plan_text: str) -> str:
    return f"Plan text:\n{plan_text}\n\nReturn the JSON now."


def _parse_claims_json(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("live extractor returned empty text")
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match is None:
            raise ValueError("live extractor text is not JSON") from None
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("live extractor JSON must be an object")
    raw = payload.get("claims", [])
    if not isinstance(raw, list):
        raise ValueError("claims must be a list")
    out: list[str] = []
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            text = item["text"].strip()
        elif isinstance(item, str):
            text = item.strip()
        else:
            continue
        if text:
            out.append(text)
    return out


class LiveClaimExtractor:
    """Live claim extractor. Constructing it requires ``LBPT_LIVE=1``."""

    def __init__(self, *, kappa: KappaVocabulary | None = None) -> None:
        if os.environ.get(LBPT_LIVE_OPT_IN_ENV, "").strip() != "1":
            raise RuntimeError(
                f"live extractor requires {LBPT_LIVE_OPT_IN_ENV}=1"
            )
        # Lazy import so CI never resolves the CT live module.
        from experiments.grounded_statecharts.adapters.live import LiveExecutor

        self._inner = LiveExecutor.from_env()
        self._kappa = kappa or default_kappa_vocabulary()

    def extract(self, *, plan_id: str, plan_text: str) -> ClaimBundle:
        if not plan_id:
            raise ValueError("plan_id must be a non-empty string")
        if not plan_text:
            raise ValueError("plan_text must be a non-empty string")
        messages = [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": _user_prompt(plan_text)},
        ]
        response = self._inner.complete_messages(messages)
        texts = _parse_claims_json(response.text)
        claims: list[Claim] = []
        cursor = 0
        for index, sentence in enumerate(texts):
            start = plan_text.find(sentence, cursor)
            if start < 0:
                # Fall back to a synthetic span so the offset invariant holds
                # even when the live extractor returns a lightly rephrased
                # sentence. Downstream ablation transforms slice by offset,
                # so we snap to the search cursor.
                start = cursor
            end = start + len(sentence)
            cursor = max(cursor, end)
            claims.append(
                Claim(
                    claim_id=f"{plan_id}::c{index:03d}",
                    text=sentence,
                    start_offset=start,
                    end_offset=max(start + 1, end),
                    kappa_terms=self._kappa.matches(sentence),
                )
            )
        return ClaimBundle(
            plan_id=plan_id,
            plan_digest=hashlib.sha256(plan_text.encode()).hexdigest(),
            claims=tuple(claims),
        )


def build_live_or_rule_based_extractor(
    *,
    kappa: KappaVocabulary | None = None,
) -> Any:
    """Return the live extractor if ``LBPT_LIVE=1``; otherwise the rule-based one."""

    from experiments.load_bearing_prose_test.extraction import RuleBasedExtractor

    if os.environ.get(LBPT_LIVE_OPT_IN_ENV, "").strip() == "1":
        return LiveClaimExtractor(kappa=kappa)
    return RuleBasedExtractor(kappa=kappa or default_kappa_vocabulary())
