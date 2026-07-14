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
import re
import sys
from datetime import date
from pathlib import Path
from typing import Never, cast

try:
    from scripts.research_contracts import (
        CLAIM_ID,
        CLAIM_TIERS,
        COVERAGE_MODES,
        EVIDENCE_ID,
        EXCEPTION_REASON_CODES,
        EXPIRY_WARNING_DAYS,
        GIT_COMMIT,
        INTEGRITY_STATES,
        ISO_DATE,
        LEGACY_ADJUDICATION_STATEMENT,
        MAX_EXCEPTION_HORIZON_DAYS,
        PACKAGE_ID,
        PROVENANCE_MODES,
        RUN_COVERAGE_STATES,
        SCHEMA_VERSION,
    )
except ModuleNotFoundError:  # Direct execution: python scripts/validate_experiment_manifest.py
    from research_contracts import (
        CLAIM_ID,
        CLAIM_TIERS,
        COVERAGE_MODES,
        EVIDENCE_ID,
        EXCEPTION_REASON_CODES,
        EXPIRY_WARNING_DAYS,
        GIT_COMMIT,
        INTEGRITY_STATES,
        ISO_DATE,
        LEGACY_ADJUDICATION_STATEMENT,
        MAX_EXCEPTION_HORIZON_DAYS,
        PACKAGE_ID,
        PROVENANCE_MODES,
        RUN_COVERAGE_STATES,
        SCHEMA_VERSION,
    )


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "experiment_manifest.json"
REGISTRY_RELATIVE_PATH = Path("docs") / "experiment_contract_registry.json"
REGISTRY_KIND = "experiment contract registry"
EXCLUDED_PACKAGES = ("common",)

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


def discover_manifests(root: Path = ROOT) -> list[Path]:
    """Return every canonical experiment manifest in stable path order."""

    experiments = root / "experiments"
    if not experiments.exists():
        return []
    return sorted(experiments.rglob(MANIFEST_NAME))


# --- Experiment contract registry: package coverage + run bindings -----------
#
# The registry partitions every direct research package into exactly one of
# `structured_manifest` (package-root manifest exists and validates) or
# `legacy_exception` (time-bounded, reviewed migration debt).  Coverage
# validation fails closed: a new package cannot pass by adding an ungrounded
# exception because exceptions are only honoured for packages inside the
# committed frozen legacy set, whose SHA-256 digest is validated without
# consulting Git history (so shallow CI checkouts behave identically).


def frozen_legacy_digest(packages: list[str]) -> str:
    """Canonical digest of the frozen legacy set: sha256 over one name per line."""

    return hashlib.sha256(("\n".join(packages) + "\n").encode()).hexdigest()


def require_iso_date(value: object, label: str) -> date:
    text = require_string(value, label)
    # fromisoformat alone is laxer than the portable schema (it accepts
    # "20260714" and week dates); pin the exact YYYY-MM-DD form first.
    if ISO_DATE.fullmatch(text) is None:
        fail(f"{label} must be an ISO YYYY-MM-DD date: {text}")
    try:
        return date.fromisoformat(text)
    except ValueError:
        fail(f"{label} must be an ISO YYYY-MM-DD date: {text}")


def require_package_id(value: object, label: str) -> str:
    text = require_string(value, label)
    if PACKAGE_ID.fullmatch(text) is None:
        fail(f"{label} has invalid format: {text}")
    return text


def require_repo_path(value: object, label: str, root: Path, *, must_exist: bool = True) -> Path:
    text = require_string(value, label)
    # Reject any ".." substring, matching the portable schema's stricter
    # repo_relative_path pattern so both authorities accept the same registry.
    if text.startswith("/") or "\\" in text or ".." in text:
        fail(f"{label} must be a safe repo-relative path: {text}")
    path = root / text
    if must_exist and not path.is_file():
        fail(f"{label} does not exist in the repository: {text}")
    return path


def direct_packages(root: Path) -> list[str]:
    experiments = root / "experiments"
    if not experiments.is_dir():
        fail(f"experiments directory not found under {root}")
    return sorted(
        entry.name
        for entry in experiments.iterdir()
        if entry.is_dir()
        and entry.name not in EXCLUDED_PACKAGES
        # Hidden and bytecode directories can never be research packages and
        # could otherwise wedge CI with an unregisterable name.
        and not entry.name.startswith(".")
        and entry.name != "__pycache__"
    )


def load_registered_ids(root: Path, path: Path, list_key: str, id_key: str) -> set[str] | None:
    """Return canonical IDs from a committed registry, or None when absent."""

    registry_path = root / path
    if not registry_path.is_file():
        return None
    try:
        payload = json.loads(registry_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {registry_path}: {exc}")
    if not isinstance(payload, dict) or not isinstance(payload.get(list_key), list):
        fail(f"{registry_path} is malformed: expected a top-level {list_key} list")
    identifiers: set[str] = set()
    for record in cast(list[object], payload[list_key]):
        if isinstance(record, dict) and isinstance(record.get(id_key), str):
            identifiers.add(cast(str, record[id_key]))
    return identifiers


def validate_run_record(
    item: object,
    label: str,
    *,
    package: str,
    root: Path,
    packages: set[str],
    claim_ids: set[str] | None,
    evidence_ids: set[str] | None,
) -> str:
    run = require_object(item, label)
    require_fields(
        run,
        label,
        {
            "run_id",
            "publication_package",
            "runtime_package",
            "provenance_mode",
            "integrity_state",
            "report_paths",
            "claim_ids",
            "evidence_ids",
            "gate_verdict_paths",
        },
        {"manifest_path"},
    )
    run_id = require_package_id(run["run_id"], f"{label}.run_id")
    publication = require_package_id(run["publication_package"], f"{label}.publication_package")
    if publication != package:
        fail(f"{label}.publication_package must equal the record package: {publication}")
    runtime = require_package_id(run["runtime_package"], f"{label}.runtime_package")
    if runtime not in packages:
        fail(f"{label}.runtime_package is not a direct research package: {runtime}")
    provenance_mode = require_string(run["provenance_mode"], f"{label}.provenance_mode")
    if provenance_mode not in PROVENANCE_MODES:
        fail(f"{label}.provenance_mode is not canonical: {provenance_mode}")
    integrity_state = require_string(run["integrity_state"], f"{label}.integrity_state")
    if integrity_state not in INTEGRITY_STATES:
        fail(f"{label}.integrity_state is not canonical: {integrity_state}")
    if "manifest_path" in run:
        require_repo_path(run["manifest_path"], f"{label}.manifest_path", root)
    if provenance_mode == "structured_manifest" and "manifest_path" not in run:
        fail(f"{label} with provenance_mode structured_manifest requires manifest_path")

    reports = require_list(run["report_paths"], f"{label}.report_paths", non_empty=True)
    for index, report in enumerate(reports):
        require_repo_path(report, f"{label}.report_paths[{index}]", root)

    for key, pattern, registered in (
        ("claim_ids", CLAIM_ID, claim_ids),
        ("evidence_ids", EVIDENCE_ID, evidence_ids),
    ):
        values = require_list(run[key], f"{label}.{key}")
        if values and registered is None:
            fail(
                f"{label}.{key} cannot be verified: "
                "the canonical registry is missing from this checkout"
            )
        seen: set[str] = set()
        for index, value in enumerate(values):
            identifier = require_string(value, f"{label}.{key}[{index}]")
            if pattern.fullmatch(identifier) is None:
                fail(f"{label}.{key}[{index}] has invalid format: {identifier}")
            if identifier in seen:
                fail(f"{label}.{key} contains duplicate entry: {identifier}")
            seen.add(identifier)
            if registered is not None and identifier not in registered:
                fail(f"{label}.{key}[{index}] is not a registered identifier: {identifier}")

    verdicts = require_list(run["gate_verdict_paths"], f"{label}.gate_verdict_paths")
    for index, verdict in enumerate(verdicts):
        require_repo_path(verdict, f"{label}.gate_verdict_paths[{index}]", root)
    return run_id


LEGACY_FORBIDDEN_FIELDS = {
    "status",
    "verdict",
    "claim_tier",
    "claim_ids",
    "evidence_ids",
    "gate_verdict_paths",
    "scientific_status",
    "adjudications",
    "runs",
    "manifest_path",
    "primary_run_id",
    "run_coverage",
}


def validate_legacy_exception(
    record: dict[str, object],
    label: str,
    *,
    package: str,
    root: Path,
    frozen_packages: set[str],
    cutoff_commit: str,
    as_of: date,
    warnings: list[str],
) -> None:
    exception_value = record.get("exception")
    exception_keys = set(exception_value) if isinstance(exception_value, dict) else set()
    forbidden = (set(record) | exception_keys) & LEGACY_FORBIDDEN_FIELDS
    if forbidden:
        fail(
            f"{label} must not carry scientific-status or run fields: "
            f"{sorted(forbidden)[0]}"
        )
    require_fields(record, label, {"package", "coverage_mode", "exception"})
    if package not in frozen_packages:
        fail(
            f"{label} is not grounded in the frozen legacy set: {package} "
            "(new packages must ship a package-root manifest)"
        )
    if (root / "experiments" / package / MANIFEST_NAME).is_file():
        fail(f"{label} overlaps a package-root manifest: {package}")

    exception = require_object(record["exception"], f"{label}.exception")
    require_fields(
        exception,
        f"{label}.exception",
        {
            "owner",
            "reason_code",
            "explanation",
            "next_action",
            "granted_on",
            "review_date",
            "expiry_date",
            "legacy_cutoff_commit",
            "adjudication",
        },
    )
    require_string(exception["owner"], f"{label}.exception.owner")
    reason_code = require_string(exception["reason_code"], f"{label}.exception.reason_code")
    if reason_code not in EXCEPTION_REASON_CODES:
        fail(f"{label}.exception.reason_code is not canonical: {reason_code}")
    require_string(exception["explanation"], f"{label}.exception.explanation")
    require_string(exception["next_action"], f"{label}.exception.next_action")
    granted_on = require_iso_date(exception["granted_on"], f"{label}.exception.granted_on")
    review_date = require_iso_date(exception["review_date"], f"{label}.exception.review_date")
    expiry_date = require_iso_date(exception["expiry_date"], f"{label}.exception.expiry_date")
    if not granted_on <= review_date <= expiry_date:
        fail(f"{label}.exception dates must satisfy granted_on <= review_date <= expiry_date")
    horizon = (expiry_date - granted_on).days
    if horizon > MAX_EXCEPTION_HORIZON_DAYS:
        fail(
            f"{label}.exception horizon exceeds {MAX_EXCEPTION_HORIZON_DAYS} days: "
            f"{horizon} days"
        )
    legacy_cutoff = require_string(
        exception["legacy_cutoff_commit"], f"{label}.exception.legacy_cutoff_commit"
    )
    if legacy_cutoff != cutoff_commit:
        fail(f"{label}.exception.legacy_cutoff_commit does not match the frozen cutoff")
    adjudication = require_string(exception["adjudication"], f"{label}.exception.adjudication")
    if adjudication != LEGACY_ADJUDICATION_STATEMENT:
        fail(f"{label}.exception.adjudication must state the exact non-adjudication statement")

    if as_of >= expiry_date:
        fail(
            f"legacy exception for {package} expired on {expiry_date.isoformat()}: "
            "renew it in a reviewed PR or migrate the package"
        )
    if (expiry_date - as_of).days <= EXPIRY_WARNING_DAYS:
        warnings.append(
            f"legacy exception for {package} expires on {expiry_date.isoformat()} "
            f"(review due {review_date.isoformat()})"
        )


def validate_contract_registry(
    root: Path = ROOT,
    registry_path: Path | None = None,
    *,
    as_of: date | None = None,
) -> tuple[dict[str, int], list[str]]:
    """Validate the package-coverage partition; return (counts, warnings)."""

    as_of = as_of or date.today()
    registry_path = registry_path or (root / REGISTRY_RELATIVE_PATH)
    try:
        payload = json.loads(registry_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {registry_path}: {exc}")

    registry = require_object(payload, "registry")
    require_fields(
        registry,
        "registry",
        {"schema_version", "kind", "excluded_packages", "frozen_legacy", "packages"},
    )
    if registry["schema_version"] != SCHEMA_VERSION:
        fail(f"registry schema_version must be '{SCHEMA_VERSION}'")
    if registry["kind"] != REGISTRY_KIND:
        fail(f"registry kind must be '{REGISTRY_KIND}'")
    excluded = require_list(registry["excluded_packages"], "registry.excluded_packages")
    if excluded != list(EXCLUDED_PACKAGES):
        fail(f"registry.excluded_packages must be {list(EXCLUDED_PACKAGES)}")

    frozen = require_object(registry["frozen_legacy"], "registry.frozen_legacy")
    require_fields(
        frozen,
        "registry.frozen_legacy",
        {"cutoff_commit", "frozen_on", "packages", "sha256"},
    )
    cutoff_commit = require_string(frozen["cutoff_commit"], "registry.frozen_legacy.cutoff_commit")
    if GIT_COMMIT.fullmatch(cutoff_commit) is None:
        fail("registry.frozen_legacy.cutoff_commit must be a 40-hex commit SHA")
    require_iso_date(frozen["frozen_on"], "registry.frozen_legacy.frozen_on")
    frozen_list = require_list(frozen["packages"], "registry.frozen_legacy.packages", non_empty=True)
    frozen_names = [
        require_package_id(item, f"registry.frozen_legacy.packages[{index}]")
        for index, item in enumerate(frozen_list)
    ]
    if frozen_names != sorted(set(frozen_names)):
        fail("registry.frozen_legacy.packages must be sorted and unique")
    digest = require_string(frozen["sha256"], "registry.frozen_legacy.sha256")
    if digest != frozen_legacy_digest(frozen_names):
        fail(
            "registry.frozen_legacy.sha256 does not match the committed package list; "
            "the frozen legacy set must not drift"
        )

    packages = direct_packages(root)
    package_set = set(packages)
    claim_ids = load_registered_ids(root, Path("docs/claim_registry.json"), "claims", "claim_id")
    evidence_ids = load_registered_ids(
        root, Path("docs/program_evidence_registry.json"), "records", "evidence_id"
    )

    warnings: list[str] = []
    counts = {"structured_manifest": 0, "legacy_exception": 0}
    seen_packages: list[str] = []
    records = require_list(registry["packages"], "registry.packages", non_empty=True)
    for index, item in enumerate(records):
        record = require_object(item, f"registry.packages[{index}]")
        package = require_package_id(record.get("package"), f"registry.packages[{index}].package")
        label = f"registry.packages[{index}] ({package})"
        if package in EXCLUDED_PACKAGES:
            fail(f"{label} must not register an excluded package")
        if package in seen_packages:
            fail(f"registry contains duplicate package record: {package}")
        seen_packages.append(package)
        if package not in package_set:
            fail(f"{label} is orphaned: experiments/{package} does not exist")

        coverage_mode = require_string(record.get("coverage_mode"), f"{label}.coverage_mode")
        if coverage_mode not in COVERAGE_MODES:
            fail(f"{label}.coverage_mode is not canonical: {coverage_mode}")
        counts[coverage_mode] += 1

        root_manifest = root / "experiments" / package / MANIFEST_NAME
        if not root_manifest.is_file() and any(
            path != root_manifest
            for path in (root / "experiments" / package).rglob(MANIFEST_NAME)
        ):
            fail(
                f"{label} has only nested manifests; a nested manifest does not "
                "satisfy package-root coverage"
            )

        if coverage_mode == "structured_manifest":
            require_fields(
                record,
                label,
                {"package", "coverage_mode", "manifest_path", "run_coverage", "runs"},
                {"primary_run_id"},
            )
            manifest_path = require_string(record["manifest_path"], f"{label}.manifest_path")
            expected = f"experiments/{package}/{MANIFEST_NAME}"
            if manifest_path != expected:
                fail(f"{label}.manifest_path must be the package root manifest: {expected}")
            if not root_manifest.is_file():
                fail(f"{label} declares structured coverage but {expected} is missing")
            validate(root_manifest)
            run_coverage = require_string(record["run_coverage"], f"{label}.run_coverage")
            if run_coverage not in RUN_COVERAGE_STATES:
                fail(f"{label}.run_coverage is not canonical: {run_coverage}")
            runs = require_list(record["runs"], f"{label}.runs", non_empty=True)
            run_ids: list[str] = []
            for run_index, run_item in enumerate(runs):
                run_id = validate_run_record(
                    run_item,
                    f"{label}.runs[{run_index}]",
                    package=package,
                    root=root,
                    packages=package_set,
                    claim_ids=claim_ids,
                    evidence_ids=evidence_ids,
                )
                if run_id in run_ids:
                    fail(f"{label}.runs contains duplicate run_id: {run_id}")
                run_ids.append(run_id)
            if "primary_run_id" in record:
                primary = require_string(record["primary_run_id"], f"{label}.primary_run_id")
                if primary not in run_ids:
                    fail(f"{label}.primary_run_id does not name a registered run: {primary}")
        else:
            validate_legacy_exception(
                record,
                label,
                package=package,
                root=root,
                frozen_packages=set(frozen_names),
                cutoff_commit=cutoff_commit,
                as_of=as_of,
                warnings=warnings,
            )

    if seen_packages != sorted(seen_packages):
        fail("registry.packages must be sorted by package name")
    missing = sorted(package_set - set(seen_packages))
    if missing:
        fail(
            f"package has neither a registry record nor coverage: {missing[0]} "
            "(add a package-root manifest; new packages cannot use legacy exceptions)"
        )
    return counts, warnings


def main(argv: list[str] | None = None, *, today: date | None = None) -> int:
    """Validate manifests, then (in no-argument mode) the coverage partition.

    ``today`` exists so date-sensitive tests can inject a fixed date; the CLI
    never sets it, so normal CI always evaluates expiry against the wall clock.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifests",
        nargs="*",
        type=Path,
        help=f"experiment manifest JSON files (default: discover experiments/**/{MANIFEST_NAME})",
    )
    parser.add_argument(
        "--as-of",
        dest="as_of",
        default=None,
        metavar="YYYY-MM-DD",
        help=(
            "HISTORICAL INSPECTION ONLY: evaluate legacy-exception expiry as of this "
            "date instead of today; never use in CI"
        ),
    )
    args = parser.parse_args(argv)

    if args.as_of is not None and args.manifests:
        print(
            "[contract-registry] FAIL: --as-of applies to the registry coverage "
            "check, which only runs in no-argument mode; remove the manifest paths",
            file=sys.stderr,
        )
        return 1

    manifests = args.manifests or discover_manifests()
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

    if args.manifests:
        # Explicit manifest paths keep the historical single-file contract;
        # package coverage is only enforced in no-argument (CI) mode.
        return 0

    as_of: date | None = today
    if args.as_of is not None:
        try:
            as_of = date.fromisoformat(args.as_of)
        except ValueError:
            print(f"[contract-registry] FAIL: invalid --as-of date: {args.as_of}", file=sys.stderr)
            return 1
        print(
            f"[contract-registry] HISTORICAL INSPECTION as of {as_of.isoformat()}: "
            "results do not certify today's coverage"
        )
    try:
        counts, warnings = validate_contract_registry(as_of=as_of)
    except ValueError as exc:
        print(f"[contract-registry] FAIL: {exc}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"[contract-registry] WARN: {warning}")
    print(
        f"[contract-registry] PASS: {counts['structured_manifest']} structured + "
        f"{counts['legacy_exception']} legacy exceptions cover "
        f"{counts['structured_manifest'] + counts['legacy_exception']} packages"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
