"""Model adapters and the strict IDENT tool-use protocol."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from experiments.ident.schemas import IdentItem

SYSTEM_PROMPT = """You are evaluating an underdetermined scientific system. Do not assume the
mechanism is identifiable from the supplied evidence. You may choose exactly
one intervention from the menu or answer immediately.

RETURN JSON ONLY:
{
  "identifiable_now": true | false,
  "live_hypotheses": ["..."],
  "action": {"type": "intervene", "intervention_id": "..."}
            OR {"type": "answer", "answer": "..."},
  "confidence": 0.0 to 1.0,
  "brief_reason": "maximum 50 words"
}
"""

FINAL_SYSTEM_PROMPT = """You received the outcome of your single permitted intervention.
Return JSON ONLY:
{
  "answer": "...",
  "confidence": 0.0 to 1.0,
  "brief_reason": "maximum 50 words"
}
"""


def render_item_prompt(item: IdentItem) -> str:
    public = item.to_public_dict(reveal_truth=False)
    return (
        "Identify the hidden mechanism. Evidence may be underdetermined.\n\n"
        + json.dumps(public, indent=2, sort_keys=True)
    )


def render_intervention_followup(
    item: IdentItem, intervention_id: str, outcome: Any
) -> str:
    return json.dumps(
        {
            "item_id": item.item_id,
            "intervention_id": intervention_id,
            "outcome": outcome,
            "final_query": item.final_query,
            "hypotheses": item.hypotheses,
        },
        indent=2,
        sort_keys=True,
    )


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError("no JSON object found in model response")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("model response JSON must be an object")
    return value


class ChatModel(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...


@dataclass
class FixtureModel:
    """Deterministic fixture model for pipeline tests (oracle-like on separators)."""

    mode: str = "oracle"

    def complete(self, *, system: str, user: str) -> str:
        payload = json.loads(user) if user.lstrip().startswith("{") else None
        if "single permitted intervention" in system or (
            isinstance(payload, dict) and "outcome" in payload
        ):
            # Final answer stage — fixture cannot see truth here from user alone.
            # Runner supplies truth via a side channel for fixture; for generic
            # fixture, answer the first listed hypothesis.
            hyps = []
            if isinstance(payload, dict):
                hyps = list(payload.get("hypotheses") or [])
            answer = hyps[0] if hyps else "h_0"
            return json.dumps(
                {
                    "answer": answer,
                    "confidence": 0.5,
                    "brief_reason": "Fixture final answer.",
                }
            )

        # First-stage: parse the embedded public item JSON.
        # The prompt prefixes a sentence before JSON.
        data = extract_json_object(user)
        interventions = data.get("candidate_interventions") or []
        live = data.get("equivalence_class_before") or data.get("hypotheses") or []
        if self.mode == "answer_now":
            return json.dumps(
                {
                    "identifiable_now": True,
                    "live_hypotheses": live,
                    "action": {"type": "answer", "answer": live[0] if live else "h_0"},
                    "confidence": 0.9,
                    "brief_reason": "Fixture answers immediately.",
                }
            )
        # Default: pick cheapest intervention by stated cost.
        if not interventions:
            return json.dumps(
                {
                    "identifiable_now": False,
                    "live_hypotheses": live,
                    "action": {"type": "answer", "answer": live[0] if live else "h_0"},
                    "confidence": 0.5,
                    "brief_reason": "No interventions available.",
                }
            )
        best = min(interventions, key=lambda g: (float(g["cost"]), g["id"]))
        return json.dumps(
            {
                "identifiable_now": False,
                "live_hypotheses": live,
                "action": {"type": "intervene", "intervention_id": best["id"]},
                "confidence": 0.6,
                "brief_reason": "Fixture chooses lowest-cost intervention.",
            }
        )


@dataclass
class EchoTranscriptModel:
    """Replay a pre-recorded JSON response sequence (for offline scoring)."""

    responses: list[str]
    _i: int = 0

    def complete(self, *, system: str, user: str) -> str:
        if self._i >= len(self.responses):
            raise IndexError("no more recorded responses")
        text = self.responses[self._i]
        self._i += 1
        return text
