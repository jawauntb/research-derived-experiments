from __future__ import annotations

import contextlib
import copy
import io
import json
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.research_contracts import LEGACY_ADJUDICATION_STATEMENT
from scripts.validate_experiment_manifest import (
    MANIFEST_NAME,
    frozen_legacy_digest,
    main,
    validate_contract_registry,
)
from tests.test_experiment_manifest import valid_manifest


ROOT = Path(__file__).resolve().parent.parent
CUTOFF = "ab" * 20
AS_OF = date(2026, 8, 1)


def legacy_exception() -> dict:
    return {
        "owner": "Jawaun Brown",
        "reason_code": "pre_manifest_publication",
        "explanation": "Committed runs predate the manifest contract.",
        "next_action": "Author a package-root manifest bound to an exact run.",
        "granted_on": "2026-07-14",
        "review_date": "2026-09-12",
        "expiry_date": "2026-10-12",
        "legacy_cutoff_commit": CUTOFF,
        "adjudication": LEGACY_ADJUDICATION_STATEMENT,
    }


def structured_record(name: str) -> dict:
    manifest_path = f"experiments/{name}/{MANIFEST_NAME}"
    return {
        "package": name,
        "coverage_mode": "structured_manifest",
        "manifest_path": manifest_path,
        "primary_run_id": name,
        "run_coverage": "complete",
        "runs": [
            {
                "run_id": name,
                "publication_package": name,
                "runtime_package": name,
                "provenance_mode": "structured_manifest",
                "integrity_state": "not_assessed",
                "manifest_path": manifest_path,
                "report_paths": [f"experiments/{name}/results/summary.json"],
                "claim_ids": [],
                "evidence_ids": [],
                "gate_verdict_paths": [],
            }
        ],
    }


def legacy_record(name: str) -> dict:
    return {
        "package": name,
        "coverage_mode": "legacy_exception",
        "exception": legacy_exception(),
    }


class RegistryFixture:
    """A disposable experiments tree plus registry under one temporary root."""

    def __init__(self, directory: str) -> None:
        self.root = Path(directory)
        (self.root / "docs").mkdir()

    def add_package(self, name: str, *, manifest: bool = False, nested: bool = False) -> None:
        package = self.root / "experiments" / name
        (package / "results").mkdir(parents=True, exist_ok=True)
        (package / "results" / "summary.json").write_text("{}")
        if manifest:
            (package / MANIFEST_NAME).write_text(json.dumps(valid_manifest()))
        if nested:
            run_dir = package / "manifests" / "run1"
            run_dir.mkdir(parents=True)
            (run_dir / MANIFEST_NAME).write_text(json.dumps(valid_manifest()))

    def registry(
        self,
        structured: list[str],
        legacy: list[str],
        *,
        frozen: list[str] | None = None,
    ) -> dict:
        frozen_names = sorted(frozen if frozen is not None else legacy)
        return {
            "schema_version": "1.0",
            "kind": "experiment contract registry",
            "excluded_packages": ["common"],
            "frozen_legacy": {
                "cutoff_commit": CUTOFF,
                "frozen_on": "2026-07-14",
                "packages": frozen_names,
                "sha256": frozen_legacy_digest(frozen_names),
            },
            "packages": sorted(
                [structured_record(name) for name in structured]
                + [legacy_record(name) for name in legacy],
                key=lambda record: record["package"],
            ),
        }

    def write(self, registry: dict) -> None:
        path = self.root / "docs" / "experiment_contract_registry.json"
        path.write_text(json.dumps(registry))

    def validate(self, as_of: date = AS_OF) -> tuple[dict[str, int], list[str]]:
        return validate_contract_registry(self.root, as_of=as_of)


def standard_fixture(directory: str) -> tuple[RegistryFixture, dict]:
    fixture = RegistryFixture(directory)
    fixture.add_package("alpha_family", manifest=True)
    fixture.add_package("beta_family")
    fixture.add_package("gamma_family")
    registry = fixture.registry(["alpha_family"], ["beta_family", "gamma_family"])
    return fixture, registry


class ContractRegistryFixtureTests(unittest.TestCase):
    def test_valid_partition_passes_and_reports_counts(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            fixture.write(registry)
            counts, warnings = fixture.validate()
        self.assertEqual(counts, {"structured_manifest": 1, "legacy_exception": 2})
        self.assertEqual(warnings, [])

    def test_uncovered_new_package_fails_closed(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            fixture.add_package("new_family")
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "neither a registry record nor coverage: new_family"):
                fixture.validate()

    def test_new_package_cannot_pass_with_ungrounded_exception(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, _ = standard_fixture(directory)
            fixture.add_package("new_family")
            registry = fixture.registry(
                ["alpha_family"],
                ["beta_family", "gamma_family", "new_family"],
                frozen=["beta_family", "gamma_family"],
            )
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "not grounded in the frozen legacy set: new_family"):
                fixture.validate()

    def test_frozen_set_digest_mismatch_fails_closed(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, _ = standard_fixture(directory)
            fixture.add_package("new_family")
            registry = fixture.registry(
                ["alpha_family"], ["beta_family", "gamma_family", "new_family"]
            )
            registry["frozen_legacy"]["sha256"] = frozen_legacy_digest(
                ["beta_family", "gamma_family"]
            )
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "sha256 does not match"):
                fixture.validate()

    def test_expired_exception_fails_and_near_expiry_warns(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            fixture.write(registry)
            counts, warnings = fixture.validate(as_of=date(2026, 9, 20))
            self.assertEqual(counts["legacy_exception"], 2)
            self.assertEqual(len(warnings), 2)
            self.assertIn("expires on 2026-10-12", warnings[0])
            with self.assertRaisesRegex(ValueError, "expired on 2026-10-12"):
                fixture.validate(as_of=date(2026, 10, 12))

    def test_same_registry_is_wall_clock_independent(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            fixture.write(registry)
            counts, _ = fixture.validate(as_of=date(2026, 7, 20))
            self.assertEqual(counts["legacy_exception"], 2)
            with self.assertRaisesRegex(ValueError, "expired"):
                fixture.validate(as_of=date(2027, 3, 1))

    def test_renewal_horizon_beyond_180_days_fails(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            record = registry["packages"][1]
            self.assertEqual(record["package"], "beta_family")
            record["exception"]["expiry_date"] = "2027-02-01"
            record["exception"]["review_date"] = "2027-01-01"
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "horizon exceeds 180 days"):
                fixture.validate()

    def test_duplicate_package_record_fails(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            registry["packages"].insert(2, copy.deepcopy(registry["packages"][1]))
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "duplicate package record: beta_family"):
                fixture.validate()

    def test_orphaned_record_fails(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, _ = standard_fixture(directory)
            registry = fixture.registry(
                ["alpha_family"], ["beta_family", "gamma_family", "vanished_family"]
            )
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "orphaned: experiments/vanished_family"):
                fixture.validate()

    def test_blank_exception_field_fails(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            registry["packages"][1]["exception"]["next_action"] = "   "
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "next_action must be a non-empty string"):
                fixture.validate()

    def test_nested_only_manifest_fails(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            fixture.add_package("delta_family", nested=True)
            registry = fixture.registry(
                ["alpha_family"], ["beta_family", "delta_family", "gamma_family"]
            )
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "only nested manifests"):
                fixture.validate()

    def test_manifest_plus_exception_overlap_fails(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            (fixture.root / "experiments" / "beta_family" / MANIFEST_NAME).write_text(
                json.dumps(valid_manifest())
            )
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "overlaps a package-root manifest: beta_family"):
                fixture.validate()

    def test_forbidden_scientific_field_on_legacy_fails(self) -> None:
        for field, value in (("status", "accepted"), ("claim_ids", ["DEMO_CLAIM"])):
            with self.subTest(field=field), TemporaryDirectory() as directory:
                fixture, registry = standard_fixture(directory)
                registry["packages"][1]["exception"][field] = value
                fixture.write(registry)
                with self.assertRaisesRegex(
                    ValueError, f"must not carry scientific-status or run fields: {field}"
                ):
                    fixture.validate()

    def test_excluded_common_package_cannot_be_registered(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            fixture.add_package("common")
            fixture.write(registry)
            counts, _ = fixture.validate()
            self.assertEqual(sum(counts.values()), 3)

            registry["packages"].insert(0, legacy_record("common"))
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "must not register an excluded package"):
                fixture.validate()

    def test_unsorted_records_fail(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            registry["packages"].reverse()
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "must be sorted by package name"):
                fixture.validate()

    def test_structured_record_with_missing_manifest_fails(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, _ = standard_fixture(directory)
            registry = fixture.registry(
                ["alpha_family", "beta_family"], ["gamma_family"]
            )
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "experiments/beta_family/experiment_manifest.json is missing"):
                fixture.validate()

    def test_primary_run_id_must_name_a_registered_run(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            registry["packages"][0]["primary_run_id"] = "phantom_run"
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "does not name a registered run: phantom_run"):
                fixture.validate()

    def test_claim_bindings_require_the_canonical_registry(self) -> None:
        with TemporaryDirectory() as directory:
            fixture, registry = standard_fixture(directory)
            registry["packages"][0]["runs"][0]["claim_ids"] = ["DEMO_CLAIM"]
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "canonical registry is missing"):
                fixture.validate()

            (fixture.root / "docs" / "claim_registry.json").write_text(
                json.dumps({"claims": [{"claim_id": "DEMO_CLAIM"}]})
            )
            counts, _ = fixture.validate()
            self.assertEqual(counts["structured_manifest"], 1)

            registry["packages"][0]["runs"][0]["claim_ids"] = ["UNREGISTERED_CLAIM"]
            fixture.write(registry)
            with self.assertRaisesRegex(ValueError, "not a registered identifier: UNREGISTERED_CLAIM"):
                fixture.validate()


class CommittedRegistryTests(unittest.TestCase):
    def test_committed_registry_partitions_every_direct_package(self) -> None:
        counts, warnings = validate_contract_registry(ROOT, as_of=date(2026, 7, 15))
        self.assertEqual(
            counts, {"structured_manifest": 5, "legacy_exception": 49}
        )
        self.assertEqual(warnings, [])

    def test_cli_no_argument_mode_enforces_coverage(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main([]), 0)
        self.assertIn("[contract-registry] PASS: 5 structured + 49 legacy", stdout.getvalue())

    def test_cli_historical_inspection_is_clearly_labeled(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["--as-of", "2026-07-15"]), 0)
        self.assertIn("HISTORICAL INSPECTION as of 2026-07-15", stdout.getvalue())

    def test_cli_explicit_manifest_paths_skip_coverage(self) -> None:
        stdout = io.StringIO()
        manifest = str(ROOT / "experiments" / "bayesian_voi" / MANIFEST_NAME)
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main([manifest]), 0)
        self.assertNotIn("[contract-registry]", stdout.getvalue())

    def test_digest_helper_matches_committed_frozen_set(self) -> None:
        registry = json.loads(
            (ROOT / "docs" / "experiment_contract_registry.json").read_text()
        )
        frozen = registry["frozen_legacy"]
        self.assertEqual(len(frozen["packages"]), 49)
        self.assertEqual(frozen["sha256"], frozen_legacy_digest(frozen["packages"]))


if __name__ == "__main__":
    unittest.main()
