from __future__ import annotations

import json
from collections import Counter

from experiments.grounded_statecharts.d2_tasks import (
    D2_HELD_OUT_TASKS_PATH,
    load_d2_held_out_tasks,
)
from experiments.grounded_statecharts.evaluation import (
    LiveTask,
    load_schema,
    smoke_tasks,
    validate_required_shape,
)


def test_d2_task_bank_has_two_balanced_held_out_families() -> None:
    tasks = load_d2_held_out_tasks()

    assert len(tasks) == 24
    assert Counter(task.family for task in tasks) == {
        "artifact_completion": 12,
        "recursive_constrained_tool_use": 12,
    }
    assert all(task.held_out for task in tasks)


def test_d2_task_rows_construct_live_tasks_and_match_schema_shape() -> None:
    raw_tasks = json.loads(D2_HELD_OUT_TASKS_PATH.read_text())
    tasks = load_d2_held_out_tasks()
    schema = load_schema("task.schema.json")

    assert all(isinstance(task, LiveTask) for task in tasks)
    assert [task.to_dict() for task in tasks] == raw_tasks
    assert all(validate_required_shape(task.to_dict(), schema) for task in tasks)


def test_d2_task_digests_are_frozen_and_smoke_tasks_are_excluded() -> None:
    first = load_d2_held_out_tasks()
    second = load_d2_held_out_tasks()
    raw_tasks = json.loads(D2_HELD_OUT_TASKS_PATH.read_text())

    assert [task.task_digest for task in first] == [task.task_digest for task in second]
    assert [task.task_digest for task in first] == [
        task["task_digest"] for task in raw_tasks
    ]
    assert {task.task_id for task in first}.isdisjoint(
        task.task_id for task in smoke_tasks()
    )
    assert all(task.held_out is False for task in smoke_tasks())
