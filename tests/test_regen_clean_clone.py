from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import regen


ROOT = Path(__file__).resolve().parent.parent


class RegenCleanCloneTests(unittest.TestCase):
    EXPECTED_ALLOWLIST = {
        "bayesian_voi",
        "mathematical_claims",
        "seed_bootstrap_calibration",
    }

    def test_allowlist_is_exactly_the_expected_deterministic_cpu_set(self) -> None:
        self.assertEqual(set(regen.CLEAN_CLONE_ALLOWLIST), self.EXPECTED_ALLOWLIST)

    def test_allowlist_recipes_are_local_cpu_argv(self) -> None:
        for package in sorted(self.EXPECTED_ALLOWLIST):
            with self.subTest(package=package):
                argv, output_rel = regen.load_structured_recipe(package)
                self.assertIsInstance(argv, list)
                self.assertTrue(all(isinstance(part, str) for part in argv))
                self.assertFalse(any("&&" in part or ";" in part for part in argv))
                self.assertTrue((ROOT / output_rel).is_file())
                self.assertIn(argv[0], {"python3", "uvx"})

    def test_unknown_or_non_allowlisted_package_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "not in the clean-clone allowlist"):
            regen.load_structured_recipe("commitment_surface")

    def test_modal_documented_command_is_inspect_only(self) -> None:
        with patch("builtins.print") as printed:
            regen.main(["external_contact"])
        text = "\n".join(str(call.args[0]) for call in printed.call_args_list if call.args)
        self.assertIn("does not launch Modal", text)
        self.assertIn("documented run command", text)

    def test_no_op_fails_when_output_must_be_newly_created(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            # Minimal fake package that "succeeds" without creating the output.
            package = "bayesian_voi"
            output_rel = regen.CLEAN_CLONE_ALLOWLIST[package]
            (root / "docs").mkdir()
            (root / "experiments" / package).mkdir(parents=True)
            manifest_path = root / "experiments" / package / "experiment_manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "experiment_id": package,
                        "hypothesis": "x",
                        "claim_tier": "theoretical",
                        "controls": [{"control_id": "c", "description": "d"}],
                        "seeds": [0],
                        "runtime": {
                            "execution_class": "local_cpu",
                            "command": ["python3", "-c", "pass"],
                            "estimated_minutes": 1,
                        },
                        "dependencies": [],
                        "gates": [{"gate_id": "G", "criterion": "c"}],
                        "artifacts": [
                            {"kind": "summary", "path": output_rel, "public": True}
                        ],
                        "status": "accepted",
                    }
                )
            )
            (root / "docs" / "experiment_contract_registry.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "legacy_policy": {
                            "frozen_package_cutoff": "2026-07-14",
                            "warning_days": 30,
                            "max_exception_horizon_days": 180,
                            "frozen_legacy_packages": [],
                            "frozen_legacy_packages_sha256": "0" * 64,
                        },
                        "packages": [
                            {
                                "package": package,
                                "coverage_mode": "structured_manifest",
                                "manifest_path": str(
                                    manifest_path.relative_to(root)
                                ),
                                "run_coverage": "complete",
                                "runs": [
                                    {
                                        "run_id": "bayesian_voi_test",
                                        "publication_package": package,
                                        "runtime_package": package,
                                        "provenance_mode": "structured_manifest",
                                        "integrity_state": "valid",
                                        "manifest_path": str(
                                            manifest_path.relative_to(root)
                                        ),
                                        "report_paths": [output_rel],
                                        "claim_ids": [],
                                        "evidence_ids": [],
                                        "gate_verdict_paths": [],
                                    }
                                ],
                            }
                        ],
                    }
                )
            )
            oracle = root / output_rel
            oracle.parent.mkdir(parents=True)
            oracle.write_text('{"ok": true}\n')

            with patch.object(regen, "materialize_clean_checkout") as materialize:

                def _materialize(_source: Path, dest: Path) -> None:
                    # Copy only the files needed for the recipe + pre-seeded output.
                    for relative in (
                        "docs/experiment_contract_registry.json",
                        str(manifest_path.relative_to(root)),
                        output_rel,
                    ):
                        target = dest / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes((root / relative).read_bytes())

                materialize.side_effect = _materialize
                with self.assertRaises(SystemExit) as raised:
                    regen.verify_clean_clone_package(package, root=root)
                self.assertIn("did not newly create output", str(raised.exception))

    def test_verify_clean_clone_allowlist_passes_on_repo(self) -> None:
        # Real isolated checkout against committed oracles.
        regen.verify_clean_clone_package("bayesian_voi")
        regen.verify_clean_clone_package("mathematical_claims")


if __name__ == "__main__":
    unittest.main()
