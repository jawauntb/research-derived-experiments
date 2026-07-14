#!/usr/bin/env python3
"""Validate version 1.0 experiment manifests without third-party packages.

The JSON Schema is the portable contract.  This standard-library adapter gives
local tooling and CI a dependency-free validator, including the cross-item
duplicate gate-ID check that JSON Schema cannot express directly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Never, cast


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "experiment_manifest.schema.json"

SCHEMA_VERSION = "1.0"
CLAIM_TIERS = {
    "descriptive",
    "internal",
    "external",
    "causal",
    "theoretical",
}
STATUSES = {
    "planned",
    "running",
    "accepted",
    "rejected",
    "inconclusive",
    "superseded",
    "retired",
}
EXECUTION_CLASSES = {"local_cpu", "local_gpu", "modal_gpu", "external"}
ARTIFACT_KINDS = {
    "raw",
    "reduced",
    "summary",
    "figure",
    "paper",
    "provenance",
    "log",
    "model",
    "dataset",
    "other",
}

ROOT_FIELDS = {
    "schema_version",
    "experiment_id",
    "hypothesis",
    "claim_tier",
    "controls",
    "seeds",
    "runtime",
    "dependencies",
    "gates",
    "artifacts",
    "status",
}
EXPERIMENT_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
GATE_ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")


def fail(message: str) -> Never:
    raise ValueError(message)


def require_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return cast(dict[str, object], value)


def require_fields(
    value: dict[str, object],
    label: str,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    missing = required - set(value)
    if missing:
        name = sorted(missing)[0]
        if label == "manifest":
            fail(f"missing required field: {name}")
        fail(f"{label} is missing required field: {name}")
    unknown = set(value) - required - optional
    if unknown:
        fail(f"{label} contains unknown field: {sorted(unknown)[0]}")


def require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string")
    return value


def require_list(value: object, label: str, *, non_empty: bool = False) -> list[object]:
    if not isinstance(value, list):
        fail(f"{label} must be a list")
    if non_empty and not value:
        fail(f"{label} must not be empty")
    return cast(list[object], value)


def require_number(value: object, label: str, *, allow_zero: bool) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(f"{label} must be a number")
    if value < 0 or (not allow_zero and value == 0):
        qualifier = "non-negative" if allow_zero else "positive"
        fail(f"{label} must be {qualifier}")
    return value


def validate_controls(value: object) -> None:
    controls = require_list(value, "controls", non_empty=True)
    for index, item in enumerate(controls):
        label = f"controls[{index}]"
        control = require_object(item, label)
        require_fields(control, label, {"control_id", "description"})
        control_id = require_string(control["control_id"], f"{label}.control_id")
        if EXPERIMENT_ID.fullmatch(control_id) is None:
            fail(f"{label}.control_id has invalid format: {control_id}")
        require_string(control["description"], f"{label}.description")


def validate_seeds(value: object) -> None:
    seeds = require_list(value, "seeds", non_empty=True)
    if any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seeds):
        fail("seeds must contain only non-negative integers")
    if len(seeds) != len(set(seeds)):
        fail("seeds contains duplicate values")


def validate_runtime(value: object) -> None:
    runtime = require_object(value, "runtime")
    require_fields(
        runtime,
        "runtime",
        {"execution_class", "command"},
        {"estimated_minutes", "max_cost_usd"},
    )
    execution_class = require_string(runtime["execution_class"], "runtime.execution_class")
    if execution_class not in EXECUTION_CLASSES:
        fail(f"runtime.execution_class is not canonical: {execution_class}")
    command = require_list(runtime["command"], "runtime.command", non_empty=True)
    if any(not isinstance(part, str) or not part.strip() for part in command):
        fail("runtime.command must contain only non-empty strings")
    if "estimated_minutes" in runtime:
        require_number(runtime["estimated_minutes"], "runtime.estimated_minutes", allow_zero=False)
    if "max_cost_usd" in runtime:
        require_number(runtime["max_cost_usd"], "runtime.max_cost_usd", allow_zero=True)


def validate_dependencies(value: object) -> None:
    dependencies = require_list(value, "dependencies")
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(dependencies):
        label = f"dependencies[{index}]"
        dependency = require_object(item, label)
        require_fields(dependency, label, {"name", "version"})
        name = require_string(dependency["name"], f"{label}.name")
        version = require_string(dependency["version"], f"{label}.version")
        identity = (name, version)
        if identity in seen:
            fail(f"dependencies contains duplicate entry: {name} {version}")
        seen.add(identity)


def validate_gates(value: object) -> None:
    gates = require_list(value, "gates", non_empty=True)
    seen: set[str] = set()
    for index, item in enumerate(gates):
        label = f"gates[{index}]"
        gate = require_object(item, label)
        require_fields(gate, label, {"gate_id", "criterion"})
        gate_id = require_string(gate["gate_id"], f"{label}.gate_id")
        if GATE_ID.fullmatch(gate_id) is None:
            fail(f"{label}.gate_id has invalid format: {gate_id}")
        if gate_id in seen:
            fail(f"duplicate gate_id: {gate_id}")
        seen.add(gate_id)
        require_string(gate["criterion"], f"{label}.criterion")


def validate_artifacts(value: object) -> None:
    artifacts = require_list(value, "artifacts", non_empty=True)
    seen: set[tuple[str, str, bool]] = set()
    for index, item in enumerate(artifacts):
        label = f"artifacts[{index}]"
        artifact = require_object(item, label)
        require_fields(artifact, label, {"kind", "path", "public"})
        kind = require_string(artifact["kind"], f"{label}.kind")
        if kind not in ARTIFACT_KINDS:
            fail(f"{label}.kind is not canonical: {kind}")
        path = require_string(artifact["path"], f"{label}.path")
        public = artifact["public"]
        if not isinstance(public, bool):
            fail(f"{label}.public must be a boolean")
        identity = (kind, path, public)
        if identity in seen:
            fail(f"artifacts contains duplicate entry: {path}")
        seen.add(identity)


def validate(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")

    manifest = require_object(payload, "manifest")
    require_fields(manifest, "manifest", ROOT_FIELDS)

    if manifest["schema_version"] != SCHEMA_VERSION:
        fail(f"schema_version must be '{SCHEMA_VERSION}'")
    experiment_id = require_string(manifest["experiment_id"], "experiment_id")
    if EXPERIMENT_ID.fullmatch(experiment_id) is None:
        fail(f"experiment_id has invalid format: {experiment_id}")
    require_string(manifest["hypothesis"], "hypothesis")

    claim_tier = require_string(manifest["claim_tier"], "claim_tier")
    if claim_tier not in CLAIM_TIERS:
        fail(f"claim_tier is not canonical: {claim_tier}")
    status = require_string(manifest["status"], "status")
    if status not in STATUSES:
        fail(f"status is not canonical: {status}")

    validate_controls(manifest["controls"])
    validate_seeds(manifest["seeds"])
    validate_runtime(manifest["runtime"])
    validate_dependencies(manifest["dependencies"])
    validate_gates(manifest["gates"])
    validate_artifacts(manifest["artifacts"])
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="+", type=Path, help="experiment manifest JSON files")
    args = parser.parse_args(argv)

    for path in args.manifests:
        try:
            payload = validate(path)
        except ValueError as exc:
            print(f"[experiment-manifest] FAIL: {exc}", file=sys.stderr)
            return 1
        print(
            f"[experiment-manifest] PASS: {path} "
            f"({payload['experiment_id']}, schema={payload['schema_version']})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
