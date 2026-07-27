#!/usr/bin/env python3
"""Loader and executor for MIDAS-facing relative-identifiability fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.relative_identifiability.core import (
    FiniteExperimentSystem,
    FiniteTarget,
    analyze_refinement,
    identify_target,
)


SCHEMA_VERSION = "relative-identifiability-regression/v1"


@dataclass(frozen=True)
class RegressionSystem:
    system: FiniteExperimentSystem
    targets: dict[str, FiniteTarget]


@dataclass(frozen=True)
class RegressionSuite:
    schema_version: str
    systems: dict[str, RegressionSystem]
    cases: tuple[dict[str, Any], ...]
    refinements: tuple[dict[str, Any], ...]

    def run(self) -> dict[str, Any]:
        case_receipts = tuple(self._run_case(case) for case in self.cases)
        refinement_receipts = tuple(
            self._run_refinement(refinement) for refinement in self.refinements
        )
        return {
            "schema_version": self.schema_version,
            "cases": list(case_receipts),
            "refinements": list(refinement_receipts),
            "all_passed": bool(case_receipts)
            and bool(refinement_receipts)
            and all(
                receipt["passed"] for receipt in (*case_receipts, *refinement_receipts)
            ),
        }

    def _run_case(self, case: dict[str, Any]) -> dict[str, Any]:
        registered = self.systems[case["system"]]
        target = registered.targets[case["target"]]
        result = identify_target(
            registered.system,
            target,
            tuple(case["family"]),
        )
        expected = case["expected"]
        observed = result.to_dict()
        passed = all(observed.get(key) == value for key, value in expected.items())
        return {
            "id": case["id"],
            "passed": passed,
            "expected": expected,
            "observed": observed,
        }

    def _run_refinement(self, case: dict[str, Any]) -> dict[str, Any]:
        registered = self.systems[case["system"]]
        result = analyze_refinement(
            registered.system,
            tuple(case["coarse_family"]),
            tuple(case["rich_family"]),
        )
        expected = case["expected"]
        observed = result.to_dict()
        passed = all(observed.get(key) == value for key, value in expected.items())
        return {
            "id": case["id"],
            "passed": passed,
            "expected": expected,
            "observed": observed,
        }


def _load_system(name: str, raw: dict[str, Any]) -> RegressionSystem:
    system = FiniteExperimentSystem(
        name=name,
        realizations=tuple(raw["realizations"]),
        experiments=tuple(raw["experiments"]),
        outcomes=tuple(tuple(row) for row in raw["outcomes"]),
    )
    targets = {
        target_name: FiniteTarget(target_name, tuple(values))
        for target_name, values in raw["targets"].items()
    }
    for target in targets.values():
        if len(target.values) != len(system.realizations):
            raise ValueError(
                f"target {target.name!r} must have one value per realization"
            )
    return RegressionSystem(system=system, targets=targets)


def load_regression_suite(path: Path) -> RegressionSuite:
    """Load and validate one versioned regression fixture bundle."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "systems", "cases", "refinements"}
    if set(raw) != required:
        raise ValueError("regression suite has unexpected top-level fields")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema version: {raw['schema_version']}")
    if not raw["systems"]:
        raise ValueError("regression suite must contain at least one system")
    if not raw["cases"]:
        raise ValueError("regression suite must contain at least one case")
    if not raw["refinements"]:
        raise ValueError("regression suite must contain at least one refinement")
    systems = {
        name: _load_system(name, system) for name, system in raw["systems"].items()
    }
    case_ids = tuple(case["id"] for case in raw["cases"])
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("regression case ids must be unique")
    for case in raw["cases"]:
        if case["system"] not in systems:
            raise ValueError(f"unknown fixture system: {case['system']}")
        if case["target"] not in systems[case["system"]].targets:
            raise ValueError(f"unknown fixture target: {case['target']}")
        status = case["expected"].get("status")
        required_expected = (
            {"status", "quotient_blocks", "block_targets"}
            if status == "identifiable"
            else {"status", "pair", "shared_transcript", "target_values"}
            if status == "obstructed"
            else set()
        )
        if set(case["expected"]) != required_expected:
            raise ValueError(
                f"case {case['id']!r} has invalid expected certificate fields"
            )
    refinement_ids = tuple(refinement["id"] for refinement in raw["refinements"])
    if len(set(refinement_ids)) != len(refinement_ids):
        raise ValueError("refinement ids must be unique")
    required_refinement_expected = {
        "is_refinement",
        "strict",
        "added_experiments",
        "split_blocks",
        "separating_experiments",
    }
    for refinement in raw["refinements"]:
        if refinement["system"] not in systems:
            raise ValueError(f"unknown fixture system: {refinement['system']}")
        if set(refinement["expected"]) != required_refinement_expected:
            raise ValueError(
                f"refinement {refinement['id']!r} has invalid expected fields"
            )
    return RegressionSuite(
        schema_version=raw["schema_version"],
        systems=systems,
        cases=tuple(raw["cases"]),
        refinements=tuple(raw["refinements"]),
    )
