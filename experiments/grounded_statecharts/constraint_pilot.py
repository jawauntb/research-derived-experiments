"""Compact deterministic bridge for the Constraint Transport D2 pilot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.constraint_transport import (
    ConstraintTransportBenchmark,
    TransportOutcome,
    TransportTask,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results" / "constraint_pilot"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def _factor_row(outcome: TransportOutcome) -> dict[str, object]:
    typed = outcome.condition == "typed_guarded"
    return {
        "episode_id": outcome.episode_id,
        "family": outcome.family,
        "delegation_depth": outcome.delegation_depth,
        "representation": "typed" if typed else "prose",
        "external_guard": "present" if typed else "absent",
        "constraint_survival": outcome.constraint_survival,
        "task_success": outcome.task_success,
        "critical_violation": outcome.critical_violation,
        "joint_success": outcome.joint_success,
        "lineage_valid": outcome.lineage_valid,
        "source_condition": outcome.condition,
    }


def _rate(rows: list[dict[str, object]], metric: str) -> float:
    return sum(bool(row[metric]) for row in rows) / len(rows)


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    """Reuse the committed transport benchmark without a provider call."""

    tasks = TransportTask.load_many(PACKAGE_ROOT / "fixtures" / "constraint_transport.json")
    outcomes = ConstraintTransportBenchmark(tasks).run_all()
    rows = [_factor_row(outcome) for outcome in outcomes]
    observed_cells = {
        (str(row["representation"]), str(row["external_guard"])) for row in rows
    }
    cells = {
        f"{representation}_guard_{guard}": {
            "representation": representation,
            "external_guard": guard,
            "observed": (representation, guard) in observed_cells,
        }
        for representation in ("prose", "typed")
        for guard in ("absent", "present")
    }
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "constraint_pilot_bridge_2026_07_20",
        "tier": "deterministic-bridge",
        "episodes": len(rows),
        "factorial_design": {
            "representation": ["prose", "typed"],
            "external_guard": ["absent", "present"],
            "cells": cells,
            "unobserved_cells": [
                name for name, cell in cells.items() if not bool(cell["observed"])
            ],
        },
        "observed_metrics": {
            condition: {
                "episodes": len(condition_rows),
                "constraint_survival": _rate(condition_rows, "constraint_survival"),
                "joint_success": _rate(condition_rows, "joint_success"),
                "critical_violation_rate": _rate(condition_rows, "critical_violation"),
            }
            for condition, condition_rows in {
                "prose_guard_absent": [
                    row
                    for row in rows
                    if row["representation"] == "prose"
                    and row["external_guard"] == "absent"
                ],
                "typed_guard_present": [
                    row
                    for row in rows
                    if row["representation"] == "typed"
                    and row["external_guard"] == "present"
                ],
            }.items()
        },
        "gates": {
            "two_fixture_families": len({row["family"] for row in rows}) == 2,
            "depths_one_through_four": {
                outcome.delegation_depth for outcome in outcomes
            }
            == {1, 2, 3, 4},
            "deterministic_source_reused": len(rows) == len(outcomes),
            "no_provider_calls": True,
        },
        "allowed_claim": (
            "This bridge republishes the committed deterministic diagonal comparison: "
            "lossy prose without an external guard versus typed lineage with its "
            "external guard. It does not estimate separate representation, guard, "
            "or interaction effects."
        ),
        "next_best_test": (
            "Register and run the two missing crossed cells using matched live or "
            "fixture mechanics before interpreting a 2x2 factorial effect."
        ),
    }
    if not all(summary["gates"].values()):
        raise RuntimeError("constraint pilot bridge gates failed")
    _write_json(output_dir / "summary.json", summary)
    _write_jsonl(output_dir / "rows.jsonl", rows)
    return summary
