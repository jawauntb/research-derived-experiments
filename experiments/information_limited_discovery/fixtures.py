#!/usr/bin/env python3
"""Load the versioned finite discovery-task corpus."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.information_limited_discovery.core import DiscoveryProblem
from experiments.relative_identifiability.core import (
    FiniteExperimentSystem,
    FiniteTarget,
)


PACKAGE = Path(__file__).resolve().parent
DEFAULT_FIXTURE = PACKAGE / "fixtures" / "discovery_tasks.json"


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a nonempty string")
    return value


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{label} must be a list of strings")
        items.append(item)
    return tuple(items)


def load_problems(path: Path = DEFAULT_FIXTURE) -> tuple[DiscoveryProblem, ...]:
    """Parse and validate every public task."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise ValueError("unsupported fixture schema version")
    raw_tasks = payload.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError("tasks must be a nonempty list")

    problems: list[DiscoveryProblem] = []
    for raw_task in raw_tasks:
        if not isinstance(raw_task, dict):
            raise ValueError("each task must be an object")
        raw_system = raw_task.get("system")
        raw_target = raw_task.get("target")
        raw_costs = raw_task.get("experiment_costs")
        if not isinstance(raw_system, dict):
            raise ValueError("system must be an object")
        if not isinstance(raw_target, dict):
            raise ValueError("target must be an object")
        if not isinstance(raw_costs, dict):
            raise ValueError("experiment_costs must be an object")

        experiments = _string_tuple(
            raw_system.get("experiments"),
            "system.experiments",
        )
        raw_outcomes = raw_system.get("outcomes")
        if not isinstance(raw_outcomes, list) or any(
            not isinstance(row, list) for row in raw_outcomes
        ):
            raise ValueError("system.outcomes must be a list of lists")
        system = FiniteExperimentSystem(
            name=_require_string(raw_system, "name"),
            realizations=_string_tuple(
                raw_system.get("realizations"),
                "system.realizations",
            ),
            experiments=experiments,
            outcomes=tuple(tuple(row) for row in raw_outcomes),
        )
        target_values = raw_target.get("values")
        if not isinstance(target_values, list):
            raise ValueError("target.values must be a list")
        target = FiniteTarget(
            name=_require_string(raw_target, "name"),
            values=tuple(target_values),
        )
        costs: list[int] = []
        for experiment in experiments:
            cost = raw_costs.get(experiment)
            if isinstance(cost, bool) or not isinstance(cost, int):
                raise ValueError(
                    f"cost for experiment {experiment!r} must be an integer"
                )
            costs.append(cost)
        unknown_costs = set(raw_costs).difference(experiments)
        if unknown_costs:
            raise ValueError("experiment_costs contains unknown experiments")
        budget = raw_task.get("budget")
        if isinstance(budget, bool) or not isinstance(budget, int):
            raise ValueError("budget must be an integer")
        variant = raw_task.get("variant")
        if variant not in ("coarse", "rich"):
            raise ValueError("variant must be 'coarse' or 'rich'")
        problems.append(
            DiscoveryProblem(
                problem_id=_require_string(raw_task, "problem_id"),
                pair_id=_require_string(raw_task, "pair_id"),
                variant=variant,
                domain=_require_string(raw_task, "domain"),
                system=system,
                target=target,
                allowed_family=_string_tuple(
                    raw_task.get("allowed_family"),
                    "allowed_family",
                ),
                budget=budget,
                experiment_costs=tuple(costs),
            )
        )

    ids = tuple(problem.problem_id for problem in problems)
    if len(set(ids)) != len(ids):
        raise ValueError("problem_id values must be unique")
    grouped: dict[str, set[str]] = {}
    for problem in problems:
        grouped.setdefault(problem.pair_id, set()).add(problem.variant)
    if any(variants != {"coarse", "rich"} for variants in grouped.values()):
        raise ValueError("each pair_id must have one coarse and one rich task")
    return tuple(problems)
