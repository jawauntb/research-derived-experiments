from __future__ import annotations

import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import gen_provenance


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

    def test_committed_outputs_are_current(self) -> None:
        self.assertEqual(gen_provenance.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
