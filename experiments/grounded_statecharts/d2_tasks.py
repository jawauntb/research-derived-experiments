"""Load and validate the frozen held-out D2 task bank.

The fixture contains task prompts and public evaluation contracts only.  It
does not contain hidden outcomes, fault labels, or answer keys; guards must
rely on the declared artifact or capability receipts at execution time.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.evaluation import CheckSpec, LiveTask, load_schema

PACKAGE_ROOT = Path(__file__).resolve().parent
D2_HELD_OUT_TASKS_PATH = PACKAGE_ROOT / "fixtures" / "d2_held_out_tasks.json"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _require_exact_keys(payload: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(payload) != expected:
        raise ValueError(f"{label} fields must be exactly {sorted(expected)}")


def live_task_from_payload(payload: Mapping[str, Any]) -> LiveTask:
    """Validate one schema-shaped fixture payload and construct its LiveTask."""

    schema = load_schema("task.schema.json")
    required = set(schema["required"])
    _require_exact_keys(payload, required, "task")
    check_spec_payload = payload["check_spec"]
    if not isinstance(check_spec_payload, Mapping):
        raise ValueError("check_spec must be an object")
    _require_exact_keys(
        check_spec_payload,
        set(schema["properties"]["check_spec"]["required"]),
        "check_spec",
    )
    if not all(isinstance(payload[name], str) and payload[name] for name in (
        "task_id",
        "family",
        "title",
        "instruction",
        "check_kind",
        "environment_digest",
        "task_digest",
    )):
        raise ValueError("task string fields must be non-empty strings")
    if payload["family"] not in schema["properties"]["family"]["enum"]:
        raise ValueError(f"unsupported family: {payload['family']}")
    if payload["check_kind"] not in schema["properties"]["check_kind"]["enum"]:
        raise ValueError(f"unsupported check_kind: {payload['check_kind']}")
    if not isinstance(payload["held_out"], bool):
        raise ValueError("held_out must be boolean")
    if not _SHA256.fullmatch(str(payload["environment_digest"])):
        raise ValueError("environment_digest must be a lowercase SHA-256 digest")
    if not _SHA256.fullmatch(str(payload["task_digest"])):
        raise ValueError("task_digest must be a lowercase SHA-256 digest")

    required_artifact = check_spec_payload["required_artifact"]
    required_capabilities = check_spec_payload["required_capabilities"]
    forbidden_capabilities = check_spec_payload["forbidden_capabilities"]
    if required_artifact is not None and (
        not isinstance(required_artifact, str) or not required_artifact
    ):
        raise ValueError("required_artifact must be null or a non-empty string")
    for values in (required_capabilities, forbidden_capabilities):
        if (
            not isinstance(values, list)
            or len(values) != len(set(values))
            or not all(isinstance(value, str) and value for value in values)
        ):
            raise ValueError("capability lists must contain unique non-empty strings")

    task = LiveTask(
        task_id=str(payload["task_id"]),
        family=str(payload["family"]),
        title=str(payload["title"]),
        instruction=str(payload["instruction"]),
        check_kind=str(payload["check_kind"]),
        check_spec=CheckSpec(
            required_artifact=required_artifact,
            required_capabilities=tuple(required_capabilities),
            forbidden_capabilities=tuple(forbidden_capabilities),
        ),
        environment_digest=str(payload["environment_digest"]),
        held_out=payload["held_out"],
    )
    if task.task_digest != payload["task_digest"]:
        raise ValueError(
            f"task digest mismatch for {task.task_id}: expected {task.task_digest}"
        )
    return task


def load_d2_held_out_tasks(path: Path = D2_HELD_OUT_TASKS_PATH) -> tuple[LiveTask, ...]:
    """Load the frozen D2 set and reject malformed, duplicate, or non-held-out rows."""

    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("D2 held-out task fixture must be a JSON list")
    tasks = tuple(live_task_from_payload(item) for item in raw if isinstance(item, Mapping))
    if len(tasks) != len(raw):
        raise ValueError("every D2 task must be a JSON object")
    if len({task.task_id for task in tasks}) != len(tasks):
        raise ValueError("D2 task IDs must be unique")
    if not all(task.held_out for task in tasks):
        raise ValueError("D2 task fixture may contain held-out tasks only")
    return tasks
