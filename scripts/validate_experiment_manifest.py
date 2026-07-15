#!/usr/bin/env python3
"""Validate version 1.0 experiment manifests without third-party packages.

The JSON Schema is the portable contract.  This standard-library adapter gives
local tooling and CI a dependency-free validator, including the cross-item
duplicate gate-ID check that JSON Schema cannot express directly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Never, cast

try:
    from scripts.research_contracts import (
        CLAIM_ID,
        CLAIM_TIERS,
        EVIDENCE_ID,
        SCHEMA_VERSION,
        SHA256,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/validate_experiment_manifest.py
    from research_contracts import CLAIM_ID, CLAIM_TIERS, EVIDENCE_ID, SCHEMA_VERSION, SHA256


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "experiment_manifest.json"
CONTRACT_REGISTRY = ROOT / "docs" / "experiment_contract_registry.json"
EXCLUDED_PACKAGES = {"common"}

# This digest independently anchors the 49 packages that existed without a
# root manifest at the 2026-07-14 cutoff. Keeping the digest in code (and as a
# schema const) prevents a new package from authorizing its own exception by
# editing an adjacent list and digest together.
FROZEN_LEGACY_PACKAGES_SHA256 = (
    "a7a41a68393e136f408e2b7f4e73ef49efdfe49cb3f39a3c1279fb3964382d91"
)
CONTRACT_COVERAGE_MODES = {"structured_manifest", "legacy_exception"}
RUN_COVERAGE_STATES = {"complete", "partial"}
PROVENANCE_MODES = {"structured_manifest", "legacy_report"}
INTEGRITY_STATES = {"valid", "invalid", "not_assessed"}
LEGACY_REASON_CODES = {
    "ambiguous_run_history",
    "missing_package_manifest",
    "multi_execution_contract_needed",
    "scheduled_manifest_migration",
}
WARNING_DAYS = 30
MAX_EXCEPTION_HORIZON_DAYS = 180

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
GATE_ID = CLAIM_ID
RUN_ID = EXPERIMENT_ID

CONTRACT_ROOT_FIELDS = {"schema_version", "legacy_policy", "packages"}
LEGACY_POLICY_FIELDS = {
    "frozen_package_cutoff",
    "warning_days",
    "max_exception_horizon_days",
    "frozen_legacy_packages",
    "frozen_legacy_packages_sha256",
}
STRUCTURED_PACKAGE_FIELDS = {
    "package",
    "coverage_mode",
    "manifest_path",
    "run_coverage",
    "runs",
}
LEGACY_PACKAGE_FIELDS = {"package", "coverage_mode", "legacy_exception"}
RUN_FIELDS = {
    "run_id",
    "publication_package",
    "runtime_package",
    "provenance_mode",
    "integrity_state",
    "report_paths",
    "claim_ids",
    "evidence_ids",
    "gate_verdict_paths",
}
LEGACY_EXCEPTION_FIELDS = {
    "owner",
    "reason_code",
    "explanation",
    "next_action",
    "review_date",
    "expiry_date",
    "frozen_legacy_cutoff",
    "adjudicates_claims",
}


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
    if not math.isfinite(value):
        fail(f"{label} must be finite")
    if value < 0 or (not allow_zero and value == 0):
        qualifier = "non-negative" if allow_zero else "positive"
        fail(f"{label} must be {qualifier}")
    return value


def require_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail(f"{label} must be an integer")
    return value


def require_string_list(value: object, label: str) -> list[str]:
    items = require_list(value, label)
    strings: list[str] = []
    for index, item in enumerate(items):
        strings.append(require_string(item, f"{label}[{index}]"))
    if len(strings) != len(set(strings)):
        fail(f"{label} contains duplicate values")
    return strings


def require_iso_date(value: object, label: str) -> date:
    raw = require_string(value, label)
    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        fail(f"{label} must be an ISO date (YYYY-MM-DD)")
    if parsed.isoformat() != raw:
        fail(f"{label} must be an ISO date (YYYY-MM-DD)")
    return parsed


def contract_registry_digest(packages: list[str]) -> str:
    """Return the history-independent digest of a sorted legacy package set."""

    canonical = "\n".join(packages) + "\n"
    return hashlib.sha256(canonical.encode()).hexdigest()


def discover_experiment_packages(root: Path = ROOT) -> list[str]:
    """Return direct research package names, excluding shared support code."""

    experiments = root / "experiments"
    if not experiments.exists():
        return []
    return sorted(
        path.name
        for path in experiments.iterdir()
        if path.is_dir() and path.name not in EXCLUDED_PACKAGES
    )


def _safe_repo_file(value: object, label: str, *, root: Path) -> tuple[str, Path]:
    relative = require_string(value, label)
    raw_path = Path(relative)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        fail(f"{label} must be a safe repository-relative path: {relative}")
    resolved_root = root.resolve()
    resolved = (root / raw_path).resolve()
    if not resolved.is_relative_to(resolved_root):
        fail(f"{label} escapes the repository: {relative}")
    if not resolved.is_file():
        fail(f"{label} does not exist: {relative}")
    return relative, resolved


def _validate_identifier_list(
    value: object,
    label: str,
    pattern: re.Pattern[str],
) -> list[str]:
    identifiers = require_string_list(value, label)
    for identifier in identifiers:
        if pattern.fullmatch(identifier) is None:
            fail(f"{label} contains an invalid identifier: {identifier}")
    return identifiers


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
        require_fields(artifact, label, {"kind", "path", "public"}, {"envelope_path"})
        kind = require_string(artifact["kind"], f"{label}.kind")
        if kind not in ARTIFACT_KINDS:
            fail(f"{label}.kind is not canonical: {kind}")
        path = require_string(artifact["path"], f"{label}.path")
        public = artifact["public"]
        if not isinstance(public, bool):
            fail(f"{label}.public must be a boolean")
        if "envelope_path" in artifact:
            if kind in {"provenance", "raw"}:
                fail(f"{label}.envelope_path is forbidden for kind={kind}")
            if path.endswith(".envelope.json"):
                fail(f"{label} cannot recursively envelope an envelope sidecar")
            envelope_path = require_string(artifact["envelope_path"], f"{label}.envelope_path")
            envelope = Path(envelope_path)
            if envelope.is_absolute() or ".." in envelope.parts:
                fail(f"{label}.envelope_path must be a safe repository-relative path")
            if not envelope_path.endswith(".envelope.json"):
                fail(f"{label}.envelope_path must end with .envelope.json")
            if envelope_path == path:
                fail(f"{label}.envelope_path cannot equal path")
            if not public:
                fail(f"{label}.envelope_path requires public=true")
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


def _validate_run_record(
    value: object,
    *,
    package: str,
    packages: set[str],
    root: Path,
    index: int,
) -> str:
    label = f"packages[{package}].runs[{index}]"
    run = require_object(value, label)
    require_fields(run, label, RUN_FIELDS, {"manifest_path"})

    run_id = require_string(run["run_id"], f"{label}.run_id")
    if RUN_ID.fullmatch(run_id) is None:
        fail(f"{label}.run_id has invalid format: {run_id}")

    publication_package = require_string(
        run["publication_package"], f"{label}.publication_package"
    )
    if publication_package != package:
        fail(f"run publication_package must match owning package: {run_id}")
    runtime_package = require_string(run["runtime_package"], f"{label}.runtime_package")
    if runtime_package not in packages:
        fail(f"run runtime_package is not a direct package: {runtime_package}")

    provenance_mode = require_string(run["provenance_mode"], f"{label}.provenance_mode")
    if provenance_mode not in PROVENANCE_MODES:
        fail(f"{label}.provenance_mode is not canonical: {provenance_mode}")
    integrity_state = require_string(run["integrity_state"], f"{label}.integrity_state")
    if integrity_state not in INTEGRITY_STATES:
        fail(f"{label}.integrity_state is not canonical: {integrity_state}")

    if provenance_mode == "structured_manifest" and "manifest_path" not in run:
        fail(f"structured run is missing manifest_path: {run_id}")
    if "manifest_path" in run:
        relative_manifest, resolved_manifest = _safe_repo_file(
            run["manifest_path"], f"{label}.manifest_path", root=root
        )
        if resolved_manifest.name != MANIFEST_NAME:
            fail(
                f"{label}.manifest_path must name an {MANIFEST_NAME} file: "
                f"{relative_manifest}"
            )
        package_prefix = f"experiments/{package}/"
        if not relative_manifest.startswith(package_prefix):
            fail(
                f"{label}.manifest_path must live inside {package_prefix}: "
                f"{relative_manifest}"
            )
        if provenance_mode == "structured_manifest":
            validate(resolved_manifest)

    for path_label in ("report_paths", "gate_verdict_paths"):
        paths = require_string_list(run[path_label], f"{label}.{path_label}")
        for path_index, path in enumerate(paths):
            _safe_repo_file(path, f"{label}.{path_label}[{path_index}]", root=root)
    _validate_identifier_list(run["claim_ids"], f"{label}.claim_ids", CLAIM_ID)
    _validate_identifier_list(run["evidence_ids"], f"{label}.evidence_ids", EVIDENCE_ID)
    return run_id


def _validate_structured_package(
    record: dict[str, object],
    *,
    package: str,
    packages: set[str],
    root: Path,
) -> None:
    require_fields(record, f"package record {package}", STRUCTURED_PACKAGE_FIELDS, {"primary_run_id"})
    expected_manifest = f"experiments/{package}/{MANIFEST_NAME}"
    manifest_path = require_string(record["manifest_path"], f"{package}.manifest_path")
    if manifest_path != expected_manifest:
        fail(f"structured manifest must be package-root: {package}")
    _, resolved_manifest = _safe_repo_file(
        manifest_path,
        f"{package}.manifest_path",
        root=root,
    )
    validate(resolved_manifest)

    run_coverage = require_string(record["run_coverage"], f"{package}.run_coverage")
    if run_coverage not in RUN_COVERAGE_STATES:
        fail(f"{package}.run_coverage is not canonical: {run_coverage}")
    runs = require_list(record["runs"], f"{package}.runs", non_empty=True)
    run_ids: list[str] = []
    for index, run in enumerate(runs):
        run_id = _validate_run_record(
            run,
            package=package,
            packages=packages,
            root=root,
            index=index,
        )
        if run_id in run_ids:
            fail(f"duplicate run_id in package {package}: {run_id}")
        run_ids.append(run_id)

    if "primary_run_id" in record:
        primary_run_id = require_string(record["primary_run_id"], f"{package}.primary_run_id")
        if primary_run_id not in run_ids:
            fail(f"primary_run_id does not resolve in package {package}: {primary_run_id}")


def _validate_legacy_package(
    record: dict[str, object],
    *,
    package: str,
    policy_cutoff: date,
    frozen_packages: set[str],
    as_of: date,
    warning_days: int,
    max_horizon_days: int,
) -> list[str]:
    require_fields(record, f"package record {package}", LEGACY_PACKAGE_FIELDS)
    if package not in frozen_packages:
        fail(f"legacy exception is outside the frozen package set: {package}")

    exception = require_object(record["legacy_exception"], "legacy_exception")
    require_fields(exception, "legacy_exception", LEGACY_EXCEPTION_FIELDS)
    for field in ("owner", "explanation", "next_action"):
        require_string(exception[field], f"legacy_exception.{field}")
    reason_code = require_string(exception["reason_code"], "legacy_exception.reason_code")
    if reason_code not in LEGACY_REASON_CODES:
        fail(f"legacy_exception.reason_code is not canonical: {reason_code}")
    if exception["adjudicates_claims"] is not False:
        fail("legacy_exception.adjudicates_claims must be false")

    cutoff = require_iso_date(
        exception["frozen_legacy_cutoff"],
        "legacy_exception.frozen_legacy_cutoff",
    )
    if cutoff != policy_cutoff:
        fail(f"legacy exception cutoff does not match policy: {package}")
    review_date = require_iso_date(exception["review_date"], "legacy_exception.review_date")
    expiry_date = require_iso_date(exception["expiry_date"], "legacy_exception.expiry_date")
    if review_date > as_of:
        fail(f"legacy exception review date is in the future: {package}")
    if expiry_date <= review_date:
        fail(f"legacy exception expiry must follow review date: {package}")
    if (expiry_date - review_date).days > max_horizon_days:
        fail(f"exception horizon exceeds {max_horizon_days} days: {package}")
    remaining_days = (expiry_date - as_of).days
    if remaining_days <= 0:
        fail(f"legacy exception expired: {package}")
    if remaining_days <= warning_days:
        return [f"{package} expires in {remaining_days} days ({expiry_date.isoformat()})"]
    return []


def validate_contract_registry(
    path: Path = CONTRACT_REGISTRY,
    *,
    root: Path = ROOT,
    as_of: date | None = None,
    expected_frozen_digest: str | None = None,
) -> tuple[dict[str, object], list[str]]:
    """Validate the exact package coverage partition without consulting Git history."""

    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")
    registry = require_object(payload, "contract registry")
    require_fields(registry, "contract registry", CONTRACT_ROOT_FIELDS)
    if registry["schema_version"] != SCHEMA_VERSION:
        fail(f"contract registry schema_version must be '{SCHEMA_VERSION}'")

    policy = require_object(registry["legacy_policy"], "legacy_policy")
    require_fields(policy, "legacy_policy", LEGACY_POLICY_FIELDS)
    policy_cutoff = require_iso_date(
        policy["frozen_package_cutoff"],
        "legacy_policy.frozen_package_cutoff",
    )
    warning_days = require_integer(policy["warning_days"], "legacy_policy.warning_days")
    if warning_days != WARNING_DAYS:
        fail(f"legacy_policy.warning_days must be {WARNING_DAYS}")
    max_horizon_days = require_integer(
        policy["max_exception_horizon_days"],
        "legacy_policy.max_exception_horizon_days",
    )
    if max_horizon_days != MAX_EXCEPTION_HORIZON_DAYS:
        fail(
            "legacy_policy.max_exception_horizon_days must be "
            f"{MAX_EXCEPTION_HORIZON_DAYS}"
        )

    frozen_packages = require_string_list(
        policy["frozen_legacy_packages"],
        "legacy_policy.frozen_legacy_packages",
    )
    if frozen_packages != sorted(frozen_packages):
        fail("legacy_policy.frozen_legacy_packages must be sorted")
    for package in frozen_packages:
        if EXPERIMENT_ID.fullmatch(package) is None:
            fail(f"frozen legacy package has invalid format: {package}")
        if package in EXCLUDED_PACKAGES:
            fail(f"excluded support package cannot be frozen: {package}")
    stored_digest = require_string(
        policy["frozen_legacy_packages_sha256"],
        "legacy_policy.frozen_legacy_packages_sha256",
    )
    if SHA256.fullmatch(stored_digest) is None:
        fail("legacy_policy.frozen_legacy_packages_sha256 must be a SHA-256 digest")
    computed_digest = contract_registry_digest(frozen_packages)
    if stored_digest != computed_digest:
        fail("frozen legacy package digest mismatch")
    anchored_digest = expected_frozen_digest or FROZEN_LEGACY_PACKAGES_SHA256
    if stored_digest != anchored_digest:
        fail("frozen legacy package digest does not match the immutable anchor")

    actual_packages = set(discover_experiment_packages(root))
    records = require_list(registry["packages"], "packages", non_empty=True)
    by_package: dict[str, tuple[str, dict[str, object]]] = {}
    for index, item in enumerate(records):
        label = f"packages[{index}]"
        record = require_object(item, label)
        require_fields(
            record,
            label,
            {"package", "coverage_mode"},
            {
                "manifest_path",
                "run_coverage",
                "primary_run_id",
                "runs",
                "legacy_exception",
            },
        )
        package = require_string(record["package"], f"{label}.package")
        if EXPERIMENT_ID.fullmatch(package) is None:
            fail(f"{label}.package has invalid format: {package}")
        if package in EXCLUDED_PACKAGES:
            fail(f"excluded support package cannot be registered: {package}")
        if package in by_package:
            fail(f"duplicate package record: {package}")
        mode = require_string(record["coverage_mode"], f"{label}.coverage_mode")
        if mode not in CONTRACT_COVERAGE_MODES:
            fail(f"{label}.coverage_mode is not canonical: {mode}")
        by_package[package] = (mode, record)

    registered_packages = set(by_package)
    orphaned = sorted(registered_packages - actual_packages)
    if orphaned:
        fail(f"orphaned package record: {orphaned[0]}")
    uncovered = sorted(actual_packages - registered_packages)
    if uncovered:
        fail(f"uncovered package: {uncovered[0]}")

    active_date = as_of or date.today()
    warnings: list[str] = []
    for package in sorted(by_package):
        mode, record = by_package[package]
        root_manifest = root / "experiments" / package / MANIFEST_NAME
        if mode == "structured_manifest":
            _validate_structured_package(
                record,
                package=package,
                packages=actual_packages,
                root=root,
            )
        else:
            if root_manifest.is_file():
                fail(f"package has both a root manifest and legacy exception: {package}")
            warnings.extend(
                _validate_legacy_package(
                    record,
                    package=package,
                    policy_cutoff=policy_cutoff,
                    frozen_packages=set(frozen_packages),
                    as_of=active_date,
                    warning_days=warning_days,
                    max_horizon_days=max_horizon_days,
                )
            )

    structured_packages = {
        package for package, (mode, _record) in by_package.items() if mode == "structured_manifest"
    }
    physical_root_packages = {
        path.parent.name
        for path in (root / "experiments").glob(f"*/{MANIFEST_NAME}")
        if path.parent.name not in EXCLUDED_PACKAGES
    }
    if physical_root_packages != structured_packages:
        missing_record = sorted(physical_root_packages - structured_packages)
        missing_manifest = sorted(structured_packages - physical_root_packages)
        if missing_record:
            fail(f"root manifest is not registered as structured: {missing_record[0]}")
        fail(f"structured package is missing its root manifest: {missing_manifest[0]}")

    return registry, warnings


def discover_manifests(root: Path = ROOT) -> list[Path]:
    """Return every canonical experiment manifest in stable path order."""

    experiments = root / "experiments"
    if not experiments.exists():
        return []
    return sorted(experiments.rglob(MANIFEST_NAME))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifests",
        nargs="*",
        type=Path,
        help=f"experiment manifest JSON files (default: discover experiments/**/{MANIFEST_NAME})",
    )
    parser.add_argument(
        "--historical-inspection",
        action="store_true",
        help=(
            "clearly labeled non-CI mode for inspecting registry validity at a historical "
            "date; requires --as-of"
        ),
    )
    parser.add_argument(
        "--as-of",
        type=str,
        help="historical inspection date in YYYY-MM-DD form (never used by normal CI)",
    )
    args = parser.parse_args(argv)

    if args.as_of and not args.historical_inspection:
        parser.error("--as-of requires --historical-inspection")
    if args.historical_inspection and not args.as_of:
        parser.error("--historical-inspection requires --as-of")
    if args.historical_inspection and args.manifests:
        parser.error("historical inspection validates repository coverage, not explicit paths")
    if args.historical_inspection and os.environ.get("CI") == "true":
        parser.error("historical inspection is forbidden in CI; use no-argument current-date validation")

    if args.manifests:
        manifests = args.manifests
    else:
        inspection_date = date.today()
        if args.as_of:
            try:
                inspection_date = date.fromisoformat(args.as_of)
            except ValueError:
                parser.error("--as-of must be an ISO date (YYYY-MM-DD)")
            if inspection_date.isoformat() != args.as_of:
                parser.error("--as-of must be an ISO date (YYYY-MM-DD)")
        try:
            registry, warnings = validate_contract_registry(as_of=inspection_date)
        except ValueError as exc:
            print(f"[experiment-contract] FAIL: {exc}", file=sys.stderr)
            return 1
        for warning in warnings:
            print(f"[experiment-contract] WARN: {warning}", file=sys.stderr)
        mode = " historical-inspection" if args.historical_inspection else ""
        print(
            f"[experiment-contract] PASS{mode}: {len(registry['packages'])} packages "
            f"at {inspection_date.isoformat()}"
        )
        manifests = discover_manifests()

    for path in manifests:
        try:
            payload = validate(path)
        except ValueError as exc:
            print(f"[experiment-manifest] FAIL: {exc}", file=sys.stderr)
            return 1
        print(
            f"[experiment-manifest] PASS: {path} "
            f"({payload['experiment_id']}, schema={payload['schema_version']})"
        )
    if not manifests:
        print(f"[experiment-manifest] PASS: no {MANIFEST_NAME} files discovered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
