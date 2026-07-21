"""Live planner that produces prose plans for CT tasks.

Env-gated: requires ``LBPT_LIVE=1`` plus the shared CT live environment
(``GROUNDED_HARNESS_LIVE=1``, ``GROUNDED_HARNESS_PROVIDER``,
``GROUNDED_HARNESS_MODEL``, ``GROUNDED_HARNESS_API_KEY_ENV``). The
planner uses ``LiveExecutor.complete_messages`` — the same low-level
provider path the CT executor uses — so no new adapter is introduced.

The planner returns *prose* only. Extraction and ablation happen
downstream via the existing package modules. The system prompt asks
for plan text with obligation-shaped sentences (must / should /
required to / not allowed to) so the deterministic rule-based
extractor can atomize them; a live extractor may be swapped in later.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any


LBPT_LIVE_OPT_IN_ENV = "LBPT_LIVE"


def _system_prompt() -> str:
    # The CT LiveExecutor's low-level `complete_messages` always parses the
    # response as an action JSON, so we ship the plan inside the "text"
    # field of that schema. Downstream we ignore action/claimed_complete/
    # artifact_created/capability_used and only read text.
    return (
        "You are a plan writer. Given a task with a required artifact "
        "and a set of allowed and forbidden capabilities, write a short "
        "prose plan the executor will follow. "
        "The plan MUST be 3 to 6 sentences. "
        "Every sentence should either state an obligation using a modal "
        "verb (must, should, will, is required to, is not allowed to, "
        "must not) or state task context (no obligation). "
        "Refer to the required artifact path and any forbidden "
        "capabilities by name where relevant. "
        "Return ONLY a JSON object of this exact shape (no markdown): "
        '{"action":"return_plan","claimed_complete":false,'
        '"artifact_created":false,"capability_used":[],'
        '"text":"<the plan prose here>"}. '
        "The plan prose goes inside the text field. Do not include "
        "newlines inside the JSON literal; use a single string."
    )


def _user_prompt(
    *,
    task_id: str,
    family: str,
    title: str,
    instruction: str,
    required_artifact: str | None,
    required_capabilities: tuple[str, ...],
    forbidden_capabilities: tuple[str, ...],
) -> str:
    lines = [
        f"Task id: {task_id}",
        f"Task family: {family}",
        f"Title: {title}",
        f"Instruction: {instruction}",
    ]
    if required_artifact:
        lines.append(f"Required artifact path: {required_artifact}")
    if required_capabilities:
        lines.append(
            "Required capabilities: " + ", ".join(required_capabilities)
        )
    if forbidden_capabilities:
        lines.append(
            "Forbidden capabilities: " + ", ".join(forbidden_capabilities)
        )
    lines.append("")
    lines.append("Return the plan prose now.")
    return "\n".join(lines)


@dataclass(frozen=True)
class PlannedPlan:
    """A live-generated plan for one CT task."""

    task_id: str
    family: str
    plan_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "family": self.family,
            "plan_text": self.plan_text,
        }


class LivePlanner:
    """Env-gated live planner. Construction requires ``LBPT_LIVE=1``."""

    def __init__(self) -> None:
        if os.environ.get(LBPT_LIVE_OPT_IN_ENV, "").strip() != "1":
            raise RuntimeError(
                f"live planner requires {LBPT_LIVE_OPT_IN_ENV}=1"
            )
        from experiments.grounded_statecharts.adapters.live import LiveExecutor

        self._inner = LiveExecutor.from_env()

    def plan_for(
        self,
        *,
        task_id: str,
        family: str,
        title: str,
        instruction: str,
        required_artifact: str | None,
        required_capabilities: tuple[str, ...],
        forbidden_capabilities: tuple[str, ...],
    ) -> PlannedPlan:
        messages = [
            {"role": "system", "content": _system_prompt()},
            {
                "role": "user",
                "content": _user_prompt(
                    task_id=task_id,
                    family=family,
                    title=title,
                    instruction=instruction,
                    required_artifact=required_artifact,
                    required_capabilities=required_capabilities,
                    forbidden_capabilities=forbidden_capabilities,
                ),
            },
        ]
        response = self._inner.complete_messages(messages)
        text = _sanitize_plan_text(response.text)
        if not text.strip():
            raise RuntimeError(
                f"live planner returned empty text for task {task_id}"
            )
        return PlannedPlan(task_id=task_id, family=family, plan_text=text)


def _sanitize_plan_text(text: str) -> str:
    """Strip common wrapping artifacts (code fences, leading headings)."""

    stripped = text.strip()
    if stripped.startswith("```"):
        # Drop a leading ``` or ```lang line, and any trailing ```.
        lines = stripped.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    # Collapse trailing whitespace and ensure a final newline.
    stripped = re.sub(r"[ \t]+\n", "\n", stripped)
    return stripped.rstrip() + "\n"
