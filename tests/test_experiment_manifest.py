from __future__ import annotations

import copy
import hashlib
import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from scripts.validate_experiment_manifest import (
    CLAIM_TIERS,
    STATUSES,
    contract_registry_digest,
    discover_manifests,
    main,
    validate,
    validate_contract_registry,
)


ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "experiment_manifest.schema.json"


def valid_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "experiment_id": "demo_experiment",
        "hypothesis": "The intervention improves the registered primary metric.",
        "claim_tier": "causal",
        "controls": [
            {
                "control_id": "matched_null",
                "description": "Matched run without the intervention.",
            }
        ],
        "seeds": [11, 23, 47],
        "runtime": {
            "execution_class": "local_cpu",
            "command": ["python", "experiments/demo/run.py"],
            "estimated_minutes": 5,
        },
        "dependencies": [
            {"name": "numpy", "version": ">=1.26,<2.2"},
        ],
        "gates": [
            {
                "gate_id": "PRIMARY_EFFECT",
                "criterion": "mean_delta >= 0.10",
            },
            {
                "gate_id": "NEGATIVE_CONTROL",
                "criterion": "abs(control_delta) <= 0.02",
            },
        ],
        "artifacts": [
            {
                "kind": "summary",
                "path": "experiments/demo/results/summary.json",
                "public": True,
            }
        ],
        "status": "planned",
    }


class ExperimentManifestTests(unittest.TestCase):
    def write_manifest(self, directory: str, payload: dict) -> Path:
        path = Path(directory) / "experiment_manifest.json"
        path.write_text(json.dumps(payload))
        return path

    def test_schema_and_validator_accept_the_same_valid_contract(self) -> None:
        schema = json.loads(SCHEMA.read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")
        self.assertEqual(set(schema["properties"]["claim_tier"]["enum"]), CLAIM_TIERS)
        self.assertEqual(set(schema["properties"]["status"]["enum"]), STATUSES)

        with TemporaryDirectory() as directory:
            payload = validate(self.write_manifest(directory, valid_manifest()))

        self.assertEqual(payload["experiment_id"], "demo_experiment")

    def test_committed_example_manifest_is_valid(self) -> None:
        payload = validate(ROOT / "templates" / "experiment" / "manifest.example.json")
        self.assertEqual(payload["status"], "planned")

    def test_all_contract_fields_are_required(self) -> None:
        required = {
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
        schema = json.loads(SCHEMA.read_text())
        self.assertTrue(required.issubset(schema["required"]))

        for field in sorted(required):
            with self.subTest(field=field), TemporaryDirectory() as directory:
                payload = valid_manifest()
                del payload[field]
                with self.assertRaisesRegex(ValueError, f"missing required field: {field}"):
                    validate(self.write_manifest(directory, payload))

    def test_unknown_status_fails_closed(self) -> None:
        payload = valid_manifest()
        payload["status"] = "done"
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "status is not canonical: done"):
                validate(self.write_manifest(directory, payload))

    def test_unknown_claim_tier_fails_closed(self) -> None:
        payload = valid_manifest()
        payload["claim_tier"] = "universal"
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "claim_tier is not canonical: universal"):
                validate(self.write_manifest(directory, payload))

    def test_duplicate_gate_ids_fail_closed(self) -> None:
        payload = valid_manifest()
        duplicate = copy.deepcopy(payload["gates"][0])
        duplicate["criterion"] = "a differently worded criterion"
        payload["gates"].append(duplicate)
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "duplicate gate_id: PRIMARY_EFFECT"):
                validate(self.write_manifest(directory, payload))

    def test_non_finite_runtime_numbers_fail_closed(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), TemporaryDirectory() as directory:
                payload = valid_manifest()
                payload["runtime"]["estimated_minutes"] = value
                with self.assertRaisesRegex(ValueError, "must be finite"):
                    validate(self.write_manifest(directory, payload))

    def test_discovery_finds_nested_canonical_manifests(self) -> None:
        with TemporaryDirectory() as directory:
            manifest_dir = Path(directory) / "experiments" / "demo"
            manifest_dir.mkdir(parents=True)
            path = self.write_manifest(str(manifest_dir), valid_manifest())
            self.assertEqual(discover_manifests(Path(directory)), [path])

    def test_cli_without_paths_discovers_repository_manifests(self) -> None:
        self.assertEqual(main([]), 0)

    def test_explicit_manifest_path_remains_independent_of_registry_coverage(self) -> None:
        with TemporaryDirectory() as directory:
            path = self.write_manifest(directory, valid_manifest())
            self.assertEqual(main([str(path)]), 0)


def legacy_digest(packages: list[str]) -> str:
    canonical = "\n".join(packages) + "\n"
    return hashlib.sha256(canonical.encode()).hexdigest()


class ExperimentContractRegistryTests(unittest.TestCase):
    AS_OF = date(2026, 7, 14)

    def write_manifest(self, root: Path, package: str, *, nested: bool = False) -> Path:
        directory = root / "experiments" / package
        if nested:
            directory = directory / "manifests" / "registered"
        directory.mkdir(parents=True, exist_ok=True)
        payload = valid_manifest()
        payload["experiment_id"] = package
        path = directory / "experiment_manifest.json"
        path.write_text(json.dumps(payload))
        return path

    def structured_record(
        self,
        package: str,
        *,
        manifest_path: str | None = None,
        run_manifest_path: str | None = None,
    ) -> dict:
        manifest_path = manifest_path or f"experiments/{package}/experiment_manifest.json"
        run_manifest_path = run_manifest_path or manifest_path
        run_id = f"{package}_registered"
        return {
            "package": package,
            "coverage_mode": "structured_manifest",
            "manifest_path": manifest_path,
            "run_coverage": "complete",
            "primary_run_id": run_id,
            "runs": [
                {
                    "run_id": run_id,
                    "publication_package": package,
                    "runtime_package": package,
                    "provenance_mode": "structured_manifest",
                    "integrity_state": "valid",
                    "manifest_path": run_manifest_path,
                    "report_paths": [],
                    "claim_ids": [],
                    "evidence_ids": [],
                    "gate_verdict_paths": [],
                }
            ],
        }

    def legacy_record(
        self,
        package: str,
        *,
        review_date: str = "2026-07-14",
        expiry_date: str = "2026-12-01",
    ) -> dict:
        return {
            "package": package,
            "coverage_mode": "legacy_exception",
            "legacy_exception": {
                "owner": "Jawaun Brown",
                "reason_code": "missing_package_manifest",
                "explanation": "The legacy package predates the structured contract.",
                "next_action": "Author a root manifest and bind the canonical run.",
                "review_date": review_date,
                "expiry_date": expiry_date,
                "frozen_legacy_cutoff": "2026-07-14",
                "adjudicates_claims": False,
            },
        }

    def registry_payload(
        self,
        records: list[dict],
        *,
        frozen_packages: list[str],
    ) -> dict:
        return {
            "schema_version": "1.0",
            "legacy_policy": {
                "frozen_package_cutoff": "2026-07-14",
                "warning_days": 30,
                "max_exception_horizon_days": 180,
                "frozen_legacy_packages": frozen_packages,
                "frozen_legacy_packages_sha256": legacy_digest(frozen_packages),
            },
            "packages": records,
        }

    def write_registry(self, root: Path, payload: dict) -> Path:
        path = root / "docs" / "experiment_contract_registry.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
        return path

    def validate_registry(
        self,
        path: Path,
        *,
        root: Path,
        as_of: date | None = None,
        expected_frozen_digest: str | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        payload = json.loads(path.read_text())
        frozen_packages = payload["legacy_policy"]["frozen_legacy_packages"]
        anchor = expected_frozen_digest or legacy_digest(frozen_packages)
        return validate_contract_registry(
            path,
            root=root,
            as_of=as_of or self.AS_OF,
            expected_frozen_digest=anchor,
        )

    def valid_fixture(self, root: Path) -> tuple[Path, dict]:
        self.write_manifest(root, "structured")
        (root / "experiments" / "legacy").mkdir(parents=True)
        payload = self.registry_payload(
            [self.structured_record("structured"), self.legacy_record("legacy")],
            frozen_packages=["legacy"],
        )
        return self.write_registry(root, payload), payload

    def test_committed_registry_covers_all_research_packages(self) -> None:
        registry, warnings = validate_contract_registry(
            ROOT / "docs" / "experiment_contract_registry.json",
            root=ROOT,
            as_of=self.AS_OF,
        )
        packages = cast(list[dict[str, object]], registry["packages"])
        modes = [record["coverage_mode"] for record in packages]

        self.assertEqual(len(modes), 54)
        self.assertEqual(modes.count("structured_manifest"), 5)
        self.assertEqual(modes.count("legacy_exception"), 49)
        self.assertEqual(warnings, [])

    def test_valid_registry_is_an_exact_structured_legacy_partition(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, _payload = self.valid_fixture(root)
            registry, warnings = self.validate_registry(
                path,
                root=root,
                as_of=self.AS_OF,
            )

        self.assertEqual(len(registry["packages"]), 2)
        self.assertEqual(warnings, [])

    def test_missing_package_fails_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, _payload = self.valid_fixture(root)
            (root / "experiments" / "new_family").mkdir()
            with self.assertRaisesRegex(ValueError, "uncovered package: new_family"):
                self.validate_registry(path, root=root)

    def test_new_package_cannot_self_authorize_a_legacy_exception(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            (root / "experiments" / "new_family").mkdir()
            payload["packages"].append(self.legacy_record("new_family"))
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "legacy exception is outside the frozen package set: new_family",
            ):
                self.validate_registry(path, root=root)

    def test_expired_exception_fails_and_near_expiry_warns(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][1]["legacy_exception"]["expiry_date"] = "2026-08-13"
            path.write_text(json.dumps(payload))

            _registry, warnings = self.validate_registry(
                path,
                root=root,
                as_of=date(2026, 7, 14),
            )
            self.assertEqual(len(warnings), 1)
            self.assertIn("legacy expires in 30 days", warnings[0])

            with self.assertRaisesRegex(ValueError, "legacy exception expired: legacy"):
                self.validate_registry(
                    path,
                    root=root,
                    as_of=date(2026, 8, 13),
                )

    def test_exception_horizon_is_capped_at_180_days(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][1]["legacy_exception"]["expiry_date"] = "2027-01-11"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "exception horizon exceeds 180 days: legacy"):
                self.validate_registry(path, root=root)

    def test_frozen_package_digest_is_verified_without_git_history(self) -> None:
        self.assertEqual(
            contract_registry_digest(["alpha", "beta"]),
            legacy_digest(["alpha", "beta"]),
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["legacy_policy"]["frozen_legacy_packages_sha256"] = "0" * 64
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "frozen legacy package digest mismatch"):
                self.validate_registry(path, root=root)

    def test_recomputed_adjacent_digest_cannot_expand_the_frozen_set(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            original_anchor = legacy_digest(["legacy"])
            (root / "experiments" / "new_family").mkdir()
            payload["packages"].append(self.legacy_record("new_family"))
            payload["legacy_policy"]["frozen_legacy_packages"] = ["legacy", "new_family"]
            payload["legacy_policy"]["frozen_legacy_packages_sha256"] = legacy_digest(
                ["legacy", "new_family"]
            )
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "frozen legacy package digest does not match the immutable anchor",
            ):
                self.validate_registry(
                    path,
                    root=root,
                    expected_frozen_digest=original_anchor,
                )

    def test_duplicate_and_orphaned_registry_packages_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"].append(copy.deepcopy(payload["packages"][1]))
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "duplicate package record: legacy"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][1] = self.legacy_record("orphan")
            payload["legacy_policy"]["frozen_legacy_packages"] = ["orphan"]
            payload["legacy_policy"]["frozen_legacy_packages_sha256"] = legacy_digest(["orphan"])
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "orphaned package record: orphan"):
                self.validate_registry(path, root=root)

    def test_blank_legacy_fields_and_verdict_fields_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][1]["legacy_exception"]["owner"] = " "
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "legacy_exception.owner must be a non-empty string"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][1]["legacy_exception"]["status"] = "rejected"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "legacy_exception contains unknown field: status",
            ):
                self.validate_registry(path, root=root)

    def test_nested_only_manifest_cannot_satisfy_structured_coverage(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            nested = self.write_manifest(root, "nested", nested=True)
            path = self.write_registry(
                root,
                self.registry_payload(
                    [
                        self.structured_record(
                            "nested",
                            manifest_path=str(nested.relative_to(root)),
                        )
                    ],
                    frozen_packages=[],
                ),
            )
            with self.assertRaisesRegex(
                ValueError,
                "structured manifest must be package-root: nested",
            ):
                self.validate_registry(path, root=root)

    def test_manifest_and_exception_overlap_fails_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, _payload = self.valid_fixture(root)
            self.write_manifest(root, "legacy")
            with self.assertRaisesRegex(
                ValueError,
                "package has both a root manifest and legacy exception: legacy",
            ):
                self.validate_registry(path, root=root)

    def test_common_is_excluded_from_coverage_and_cannot_be_registered(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, _payload = self.valid_fixture(root)
            (root / "experiments" / "common").mkdir()
            self.validate_registry(path, root=root)

            payload = json.loads(path.read_text())
            payload["packages"].append(self.legacy_record("common"))
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "excluded support package cannot be registered: common"):
                self.validate_registry(path, root=root)

    def test_frozen_list_rejects_unsorted_and_duplicate_entries(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["legacy_policy"]["frozen_legacy_packages"] = ["legacy", "alpha"]
            payload["legacy_policy"]["frozen_legacy_packages_sha256"] = legacy_digest(
                ["legacy", "alpha"]
            )
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "legacy_policy.frozen_legacy_packages must be sorted",
            ):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["legacy_policy"]["frozen_legacy_packages"] = ["legacy", "legacy"]
            payload["legacy_policy"]["frozen_legacy_packages_sha256"] = legacy_digest(
                ["legacy", "legacy"]
            )
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "legacy_policy.frozen_legacy_packages contains duplicate values",
            ):
                self.validate_registry(path, root=root)

    def test_tampered_warning_days_and_horizon_policy_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["legacy_policy"]["warning_days"] = 7
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "legacy_policy.warning_days must be 30"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["legacy_policy"]["max_exception_horizon_days"] = 365
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "legacy_policy.max_exception_horizon_days must be 180",
            ):
                self.validate_registry(path, root=root)

    def test_review_and_expiry_boundaries(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][1]["legacy_exception"]["review_date"] = "2026-07-15"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "legacy exception review date is in the future: legacy",
            ):
                self.validate_registry(path, root=root, as_of=date(2026, 7, 14))

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][1]["legacy_exception"]["expiry_date"] = "2026-07-14"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "legacy exception expiry must follow review date: legacy",
            ):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][1]["legacy_exception"]["expiry_date"] = "2026-08-14"
            path.write_text(json.dumps(payload))
            _registry, warnings = self.validate_registry(
                path,
                root=root,
                as_of=date(2026, 7, 14),
            )
            self.assertEqual(warnings, [])

    def test_unsafe_and_missing_structured_paths_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][0]["runs"][0]["report_paths"] = ["/tmp/escape.md"]
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "must be a safe repository-relative path"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][0]["runs"][0]["report_paths"] = ["../outside.md"]
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "must be a safe repository-relative path"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][0]["runs"][0]["report_paths"] = [
                "experiments/structured/missing_report.md"
            ]
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "does not exist"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            report = root / "experiments" / "structured" / "results.md"
            report.write_text("ok\n")
            payload["packages"][0]["runs"][0]["report_paths"] = [
                "experiments/structured/results.md",
                "experiments/structured/results.md",
            ]
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "report_paths contains duplicate values"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            path, payload = self.valid_fixture(root)
            outside = base / "outside.md"
            outside.write_text("secret\n")
            link = root / "experiments" / "structured" / "escape.md"
            link.symlink_to(outside)
            payload["packages"][0]["runs"][0]["report_paths"] = [
                "experiments/structured/escape.md"
            ]
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "escapes the repository"):
                self.validate_registry(path, root=root)

    def test_structured_run_identity_and_manifest_rules_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            (root / "experiments" / "structured" / "experiment_manifest.json").unlink()
            with self.assertRaisesRegex(ValueError, "does not exist"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            bad = root / "experiments" / "structured" / "experiment_manifest.json"
            bad.write_text("{")
            with self.assertRaisesRegex(ValueError, "cannot read"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            second = copy.deepcopy(payload["packages"][0]["runs"][0])
            payload["packages"][0]["runs"].append(second)
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "duplicate run_id in package structured"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][0]["primary_run_id"] = "missing_run"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "primary_run_id does not resolve in package structured",
            ):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][0]["runs"][0]["publication_package"] = "legacy"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "run publication_package must match owning package",
            ):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][0]["runs"][0]["runtime_package"] = "missing_runtime"
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "run runtime_package is not a direct package",
            ):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            del payload["packages"][0]["runs"][0]["manifest_path"]
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "structured run is missing manifest_path"):
                self.validate_registry(path, root=root)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = self.valid_fixture(root)
            payload["packages"][0]["runs"][0]["provenance_mode"] = "legacy_report"
            path.write_text(json.dumps(payload))
            # legacy_report may omit manifest_path; keep the existing path and ensure
            # the mode itself remains accepted while publication rules still hold.
            registry, warnings = self.validate_registry(path, root=root)
            self.assertEqual(len(registry["packages"]), 2)
            self.assertEqual(warnings, [])

    def test_run_manifest_path_must_name_experiment_manifest_json(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root, "structured")
            (root / "experiments" / "legacy").mkdir(parents=True)
            wrong = (
                root / "experiments" / "structured" / "manifests" / "m5" / "run.json"
            )
            wrong.parent.mkdir(parents=True)
            payload = valid_manifest()
            payload["experiment_id"] = "structured_m5_run"
            wrong.write_text(json.dumps(payload))
            registry = self.registry_payload(
                [
                    self.structured_record(
                        "structured",
                        run_manifest_path=str(wrong.relative_to(root)),
                    ),
                    self.legacy_record("legacy"),
                ],
                frozen_packages=["legacy"],
            )
            registry_path = self.write_registry(root, registry)
            with self.assertRaisesRegex(
                ValueError,
                r"manifest_path must name an experiment_manifest\.json file",
            ):
                self.validate_registry(registry_path, root=root)

    def test_run_manifest_path_must_live_inside_publication_package(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root, "structured")
            (root / "experiments" / "legacy").mkdir(parents=True)
            outside = (
                root
                / "experiments"
                / "legacy"
                / "manifests"
                / "m5"
                / "experiment_manifest.json"
            )
            outside.parent.mkdir(parents=True)
            payload = valid_manifest()
            payload["experiment_id"] = "legacy_m5_run"
            outside.write_text(json.dumps(payload))
            registry = self.registry_payload(
                [
                    self.structured_record(
                        "structured",
                        run_manifest_path=str(outside.relative_to(root)),
                    ),
                    self.legacy_record("legacy"),
                ],
                frozen_packages=["legacy"],
            )
            registry_path = self.write_registry(root, registry)
            with self.assertRaisesRegex(
                ValueError,
                r"manifest_path must live inside experiments/structured/",
            ):
                self.validate_registry(registry_path, root=root)

    def test_run_manifest_path_content_is_validated_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root, "structured")
            (root / "experiments" / "legacy").mkdir(parents=True)
            nested = (
                root
                / "experiments"
                / "structured"
                / "manifests"
                / "m5"
                / "experiment_manifest.json"
            )
            nested.parent.mkdir(parents=True)
            payload = valid_manifest()
            payload["experiment_id"] = "structured_m5_run"
            del payload["status"]
            nested.write_text(json.dumps(payload))
            registry = self.registry_payload(
                [
                    self.structured_record(
                        "structured",
                        run_manifest_path=str(nested.relative_to(root)),
                    ),
                    self.legacy_record("legacy"),
                ],
                frozen_packages=["legacy"],
            )
            registry_path = self.write_registry(root, registry)
            with self.assertRaisesRegex(ValueError, r"missing required field: status"):
                self.validate_registry(registry_path, root=root)

    def test_valid_nested_run_manifest_binding_passes(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_manifest(root, "structured")
            (root / "experiments" / "legacy").mkdir(parents=True)
            nested = (
                root
                / "experiments"
                / "structured"
                / "manifests"
                / "m5"
                / "experiment_manifest.json"
            )
            nested.parent.mkdir(parents=True)
            payload = valid_manifest()
            payload["experiment_id"] = "structured_m5_run"
            nested.write_text(json.dumps(payload))
            registry = self.registry_payload(
                [
                    self.structured_record(
                        "structured",
                        run_manifest_path=str(nested.relative_to(root)),
                    ),
                    self.legacy_record("legacy"),
                ],
                frozen_packages=["legacy"],
            )
            registry_path = self.write_registry(root, registry)
            registry_result, warnings = self.validate_registry(registry_path, root=root)
            self.assertEqual(len(registry_result["packages"]), 2)
            self.assertEqual(warnings, [])

    def test_historical_cli_flag_misuse_and_labeled_success(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.valid_fixture(root)
            # Explicit path mode must remain registry-independent even without a registry.
            manifest = root / "experiments" / "structured" / "experiment_manifest.json"
            self.assertEqual(main([str(manifest)]), 0)

        from io import StringIO
        from unittest.mock import patch

        with patch("sys.stderr", new_callable=StringIO) as stderr:
            with self.assertRaises(SystemExit):
                main(["--as-of", "2026-07-14"])
            self.assertIn("--as-of requires --historical-inspection", stderr.getvalue())

        with patch("sys.stderr", new_callable=StringIO) as stderr:
            with self.assertRaises(SystemExit):
                main(["--historical-inspection"])
            self.assertIn("--historical-inspection requires --as-of", stderr.getvalue())

        with patch.dict("os.environ", {"CI": "true"}, clear=False):
            with patch("sys.stderr", new_callable=StringIO) as stderr:
                with self.assertRaises(SystemExit):
                    main(["--historical-inspection", "--as-of", "2026-07-14"])
                self.assertIn("historical inspection is forbidden in CI", stderr.getvalue())

        with patch.dict("os.environ", {"CI": ""}, clear=False):
            with patch("sys.stdout", new_callable=StringIO) as stdout:
                self.assertEqual(
                    main(["--historical-inspection", "--as-of", "2026-07-14"]),
                    0,
                )
                self.assertIn(
                    "[experiment-contract] PASS historical-inspection",
                    stdout.getvalue(),
                )
                self.assertIn("54 packages at 2026-07-14", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
