from __future__ import annotations

import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import gen_provenance


def write_legacy_registry(root: Path, package: str) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "claim_registry.json").write_text(json.dumps({"schema_version": "1.0", "claims": []}))
    (docs / "experiment_contract_registry.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "legacy_policy": {
                    "frozen_package_cutoff": "2026-07-14",
                    "warning_days": 30,
                    "max_exception_horizon_days": 180,
                    "frozen_legacy_packages": [package],
                    "frozen_legacy_packages_sha256": "0" * 64,
                },
                "packages": [
                    {
                        "package": package,
                        "coverage_mode": "legacy_exception",
                        "legacy_exception": {
                            "owner": "Jawaun Brown",
                            "reason_code": "missing_package_manifest",
                            "explanation": "test fixture",
                            "next_action": "migrate",
                            "review_date": "2026-07-14",
                            "expiry_date": "2026-12-01",
                            "frozen_legacy_cutoff": "2026-07-14",
                            "adjudicates_claims": False,
                        },
                    }
                ],
            }
        )
    )


class ProvenanceGenerationTests(unittest.TestCase):
    def test_shared_support_packages_are_not_counted_as_experiments(self) -> None:
        names = {path.name for path in gen_provenance.experiment_dirs()}
        self.assertNotIn("common", names)

    def test_check_mode_is_non_mutating_and_detects_stale_output(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "generated.md"
            path.write_text("stale")
            with (
                patch.object(gen_provenance, "validate_evidence_registry"),
                patch.object(gen_provenance, "validate_claim_registry"),
                patch.object(
                    gen_provenance,
                    "generated_outputs",
                    return_value=({path: "expected"}, 1),
                ),
            ):
                self.assertEqual(gen_provenance.main(["--check"]), 1)
            self.assertEqual(path.read_text(), "stale")

    def test_collect_uses_manifest_declared_json_summary_and_preregistration(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            experiment = root / "experiments" / "manifested"
            results = experiment / "results"
            paper_root = root / "papers"
            results.mkdir(parents=True)
            paper_root.mkdir()
            write_legacy_registry(root, "manifested")
            summary = results / "summary.json"
            preregistration = experiment / "preregistration.json"
            summary.write_text('{"gates": {"registered_gate": true}}\n')
            preregistration.write_text('{"status": "registered"}\n')
            (experiment / "PREREGISTRATION.md").write_text("# Undeclared fallback\n")
            (experiment / "README.md").write_text(
                "Run with `python experiments/manifested/experiment.py`.\n"
            )
            (experiment / "experiment_manifest.json").write_text(
                json.dumps(
                    {
                        "artifacts": [
                            {
                                "kind": "summary",
                                "path": "experiments/manifested/results/summary.json",
                                "public": True,
                            },
                            {
                                "kind": "other",
                                "path": "experiments/manifested/preregistration.json",
                                "public": True,
                            },
                        ]
                    }
                )
            )

            with (
                patch.object(gen_provenance, "ROOT", root),
                patch.object(gen_provenance, "PAPERS", paper_root),
            ):
                record = gen_provenance.collect(experiment)

            self.assertEqual(record["status"], "results")
            self.assertEqual(
                record["result_reports"],
                ["experiments/manifested/results/summary.json"],
            )
            self.assertEqual(
                record["preregistration"],
                "experiments/manifested/preregistration.json",
            )

    def test_collect_discovers_package_local_json_result_and_markdown_preregistration(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            experiment = root / "experiments" / "local_artifacts"
            results = experiment / "results"
            paper_root = root / "papers"
            results.mkdir(parents=True)
            paper_root.mkdir()
            write_legacy_registry(root, "local_artifacts")
            (results / "registered_summary.json").write_text('{"status": "pass"}\n')
            (experiment / "PREREGISTRATION.md").write_text("# Frozen design\n")
            (experiment / "README.md").write_text("# Local artifacts\n")

            with (
                patch.object(gen_provenance, "ROOT", root),
                patch.object(gen_provenance, "PAPERS", paper_root),
            ):
                record = gen_provenance.collect(experiment)

            self.assertEqual(record["status"], "results")
            self.assertEqual(
                record["result_reports"],
                ["experiments/local_artifacts/results/registered_summary.json"],
            )
            self.assertEqual(
                record["preregistration"],
                "experiments/local_artifacts/PREREGISTRATION.md",
            )

    def test_commitment_surface_primary_uses_m5_manifest_not_e5(self) -> None:
        record = gen_provenance.collect(
            gen_provenance.ROOT / "experiments" / "commitment_surface"
        )
        self.assertEqual(record["run_id"], "commitment_surface_m5_2026_07_14")
        self.assertEqual(
            record["experiment_id"],
            "commitment_surface_m5_suite_c_reopen_reset_trigger",
        )
        self.assertEqual(record["manifest_status"], "rejected")
        self.assertEqual(record["integrity_state"], "valid")
        self.assertEqual(record["run_coverage"], "partial")
        self.assertEqual(record["publication_package"], "commitment_surface")
        self.assertEqual(record["runtime_package"], "world_responds")
        self.assertEqual(
            record["scientific_adjudications"],
            [{"status": "unadjudicated"}],
        )
        self.assertIn(
            "experiments.world_responds.suite_c_reopen_reset_trigger",
            record["run_command"],
        )
        self.assertNotIn("modal_e5_generator_vs_coverage.py", record["run_command"])
        self.assertEqual(
            record["result_reports"],
            [
                "experiments/commitment_surface/results/m5_suite_c_reopen_reset_trigger_2026_07_14.json",
                "experiments/commitment_surface/results/m5_suite_c_reopen_reset_trigger_2026_07_14.md",
            ],
        )

    def test_structured_run_uses_its_declared_producing_agent(self) -> None:
        record = gen_provenance.collect(
            gen_provenance.ROOT / "experiments" / "grounded_statecharts"
        )

        self.assertIn("OpenAI Codex", record["attribution"])
        self.assertIn("PR 378 Counterfactual Harness Search follow-up", record["attribution"])

    def test_malformed_bound_manifest_fails_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            experiment = root / "experiments" / "commitment_surface"
            nested = experiment / "manifests" / "m5"
            nested.mkdir(parents=True)
            (root / "docs").mkdir()
            (root / "papers").mkdir()
            (nested / "experiment_manifest.json").write_text("{")
            (experiment / "experiment_manifest.json").write_text(
                (gen_provenance.ROOT / "experiments/commitment_surface/experiment_manifest.json").read_text()
            )
            for rel in [
                "results/e5_generator_vs_coverage.json",
                "results/e5_generator_vs_coverage.md",
                "results/m5_suite_c_reopen_reset_trigger_2026_07_14.json",
                "results/m5_suite_c_reopen_reset_trigger_2026_07_14.md",
                "results/e6_smoke_readiness.json",
                "results/e6_smoke_readiness_2026_07_13.md",
                "results/e7_selective_subspace_2026_07_13.json",
                "results/e7_selective_subspace_2026_07_13.md",
                "results/gate_verdicts/e5_strict_coverage.json",
            ]:
                path = experiment / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x\n")
            (root / "docs" / "claim_registry.json").write_text(
                (gen_provenance.ROOT / "docs/claim_registry.json").read_text()
            )
            (root / "docs" / "experiment_contract_registry.json").write_text(
                (gen_provenance.ROOT / "docs/experiment_contract_registry.json").read_text()
            )
            with (
                patch.object(gen_provenance, "ROOT", root),
                patch.object(gen_provenance, "PAPERS", root / "papers"),
            ):
                with self.assertRaisesRegex(ValueError, "structured provenance binding failed"):
                    gen_provenance.collect(experiment)

    def test_committed_outputs_are_current(self) -> None:
        self.assertEqual(gen_provenance.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
