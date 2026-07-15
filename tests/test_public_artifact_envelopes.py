from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

from scripts.export_commitment_surface_e5_results import (
    PUBLIC_CELL_FIELDS,
    build_public_artifact,
    write_envelope,
)
from scripts.validate_experiment_manifest import validate_artifacts
from scripts.validate_public_artifact_envelopes import (
    build_envelope_from_public_artifact,
    main,
    validate_envelope,
)


ROOT = Path(__file__).resolve().parent.parent
E5_PUBLIC = ROOT / "experiments/commitment_surface/results/e5_generator_vs_coverage.json"
E5_ENVELOPE = ROOT / (
    "experiments/commitment_surface/results/e5_generator_vs_coverage.json.envelope.json"
)
E5_MANIFEST = "experiments/commitment_surface/experiment_manifest.json"
M5_MANIFEST = "experiments/commitment_surface/manifests/m5/experiment_manifest.json"
E4_PUBLIC = ROOT / "experiments/commitment_surface/results/e4_pythia_lora_v2_appendix.json"
E4_ENVELOPE = ROOT / (
    "experiments/commitment_surface/results/e4_pythia_lora_v2_appendix.json.envelope.json"
)
E4_MANIFEST = "experiments/commitment_surface/manifests/e4/experiment_manifest.json"


def _raw_payload() -> bytes:
    arms = ("G-reg", "B-ref", "W-reg", "Cov", "A-ref")
    cells = [
        {
            "cell_id": f"{size}__n{n}__seed{seed}__{arm}",
            "size": size,
            "n": n,
            "seed": seed,
            "arm": arm,
            "canonical_ood_accuracy": 0.5,
            "paraphrase_ood_accuracy": 0.25,
            "novel_k_equivariance_accuracy": 0.5,
            "canonical_normalized_patch_ce": 0.1,
            "paraphrase_normalized_patch_ce": 0.05,
            "integrity_pass": True,
            "split": {"train_inputs": [0, 1]},
        }
        for size in ("70m", "160m", "410m")
        for n in (13, 17, 23)
        for seed in (1, 2, 3)
        for arm in arms
    ]
    return json.dumps(
        {
            "manifest": {
                "manifest_id": "manifest",
                "implementation_fingerprint": "fingerprint",
            },
            "config": {"sizes": ["70m", "160m", "410m"]},
            "cells": cells,
            "analysis": {
                "n_cells": len(cells),
                "per_arm": {
                    arm: {
                        "canonical_ood_accuracy": 0.5,
                        "paraphrase_ood_accuracy": 0.25,
                        "novel_k_equivariance_accuracy": 0.5,
                        "canonical_normalized_patch_ce": 0.1,
                        "paraphrase_normalized_patch_ce": 0.05,
                    }
                    for arm in arms
                },
                "confirmatory_ready": True,
                "grid_audit": {"grid_complete": True, "cell_data_complete": True},
                "verdict": "coverage",
                "generator_learning_gate": False,
                "coverage_gate": True,
                "mixed_gate": False,
                "group_specificity_gate": False,
                "transport_gate": False,
                "canonical_G_minus_A": 0.0,
                "canonical_G_minus_Cov": -0.5,
                "novel_k_G_minus_A": 0.0,
                "paraphrase_lift_retained": float("-inf"),
            },
        }
    ).encode()


class PublicArtifactEnvelopeTests(unittest.TestCase):
    def _stage_valid_pair(self, root: Path) -> tuple[Path, dict]:
        artifact_rel = "experiments/demo/results/public.json"
        manifest_rel = "experiments/demo/experiment_manifest.json"
        envelope_rel = "experiments/demo/results/public.json.envelope.json"
        artifact = root / artifact_rel
        manifest = root / manifest_rel
        envelope_path = root / envelope_rel
        artifact.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(E5_PUBLIC.read_bytes())
        manifest.write_text("{}")
        payload = json.loads(E5_ENVELOPE.read_text())
        payload["artifact_path"] = artifact_rel
        payload["producer_manifest_path"] = manifest_rel
        payload["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        payload["artifact_bytes"] = artifact.stat().st_size
        # Drop gate paths that are absent in the temp tree.
        payload["gate_verdict_paths"] = []
        # Keep adjudication bound via claims/evidence only for mismatch tests that
        # do not exercise gate path existence; switch to unadjudicated for local.
        payload["claim_ids"] = []
        payload["evidence_ids"] = []
        payload["adjudication"] = "unadjudicated"
        envelope_path.write_text(json.dumps(payload))
        return envelope_path, payload

    def test_committed_e5_envelope_validates_without_raw_input(self) -> None:
        envelope = validate_envelope(E5_ENVELOPE)
        self.assertEqual(envelope["producer_manifest_path"], E5_MANIFEST)
        self.assertEqual(envelope["expected_rows"], 135)
        self.assertEqual(envelope["adjudication"], "bound")
        self.assertNotEqual(envelope["producer_manifest_path"], M5_MANIFEST)
        self.assertEqual(main([]), 0)

    def test_committed_e4_envelope_is_unadjudicated_and_run_specific(self) -> None:
        envelope = validate_envelope(E4_ENVELOPE)
        self.assertEqual(envelope["producer_manifest_path"], E4_MANIFEST)
        self.assertEqual(envelope["expected_rows"], 108)
        self.assertEqual(envelope["adjudication"], "unadjudicated")
        self.assertEqual(envelope["claim_ids"], [])
        self.assertEqual(envelope["evidence_ids"], [])
        self.assertEqual(envelope["gate_verdict_paths"], [])
        self.assertNotEqual(envelope["producer_manifest_path"], E5_MANIFEST)
        self.assertNotEqual(envelope["producer_manifest_path"], M5_MANIFEST)
        self.assertEqual(main([]), 0)

    def test_e4_wrong_primary_producer_fails_closed(self) -> None:
        payload = json.loads(E4_ENVELOPE.read_text())
        with TemporaryDirectory() as directory:
            root = Path(directory)
            artifact_rel = "experiments/demo/results/public.json"
            manifest_rel = "experiments/demo/manifests/e4/experiment_manifest.json"
            envelope_rel = "experiments/demo/results/public.json.envelope.json"
            artifact = root / artifact_rel
            envelope_path = root / envelope_rel
            artifact.parent.mkdir(parents=True, exist_ok=True)
            (root / manifest_rel).parent.mkdir(parents=True, exist_ok=True)
            (root / manifest_rel).write_text("{}")
            (root / E5_MANIFEST).parent.mkdir(parents=True, exist_ok=True)
            (root / E5_MANIFEST).write_text("{}")
            artifact.write_bytes(E4_PUBLIC.read_bytes())
            payload["artifact_path"] = artifact_rel
            payload["producer_manifest_path"] = E5_MANIFEST
            payload["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            payload["artifact_bytes"] = artifact.stat().st_size
            envelope_path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(
                ValueError,
                "producer_manifest_path does not match declaring manifest",
            ):
                validate_envelope(
                    envelope_path,
                    root=root,
                    tracked={artifact_rel, E5_MANIFEST, envelope_rel},
                    expected_artifact_path=artifact_rel,
                    expected_producer_manifest=manifest_rel,
                )

    def test_m5_producer_is_rejected_for_e5_declaration(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            envelope_path, payload = self._stage_valid_pair(root)
            payload["producer_manifest_path"] = (
                "experiments/demo/manifests/m5/experiment_manifest.json"
            )
            (root / payload["producer_manifest_path"]).parent.mkdir(parents=True)
            (root / payload["producer_manifest_path"]).write_text("{}")
            envelope_path.write_text(json.dumps(payload))
            tracked = {
                payload["artifact_path"],
                payload["producer_manifest_path"],
                str(envelope_path.relative_to(root)),
            }
            with self.assertRaisesRegex(
                ValueError,
                "producer_manifest_path does not match declaring manifest",
            ):
                validate_envelope(
                    envelope_path,
                    root=root,
                    tracked=tracked,
                    expected_artifact_path=payload["artifact_path"],
                    expected_producer_manifest="experiments/demo/experiment_manifest.json",
                )

    def test_wrong_digest_and_receipt_mismatch_fail_closed(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            envelope_path, payload = self._stage_valid_pair(root)
            tracked = {
                payload["artifact_path"],
                payload["producer_manifest_path"],
                str(envelope_path.relative_to(root)),
            }

            bad = copy.deepcopy(payload)
            bad["artifact_sha256"] = "0" * 64
            envelope_path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, "artifact_sha256 does not match"):
                validate_envelope(
                    envelope_path,
                    root=root,
                    tracked=tracked,
                    expected_artifact_path=payload["artifact_path"],
                    expected_producer_manifest=payload["producer_manifest_path"],
                )

            bad = copy.deepcopy(payload)
            bad["raw_source_receipt"]["sha256"] = "1" * 64
            envelope_path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(
                ValueError,
                "raw_source_receipt.sha256 does not match embedded public source receipt",
            ):
                validate_envelope(
                    envelope_path,
                    root=root,
                    tracked=tracked,
                    expected_artifact_path=payload["artifact_path"],
                    expected_producer_manifest=payload["producer_manifest_path"],
                )

    def test_path_traversal_untracked_and_recursive_envelope_fail(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            envelope_path, payload = self._stage_valid_pair(root)
            tracked = {
                payload["artifact_path"],
                payload["producer_manifest_path"],
                str(envelope_path.relative_to(root)),
            }

            bad = copy.deepcopy(payload)
            bad["artifact_path"] = "../secret.json"
            envelope_path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, "safe repository-relative path"):
                validate_envelope(envelope_path, root=root, tracked=tracked)

            bad = copy.deepcopy(payload)
            envelope_path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, "not a tracked repository file"):
                validate_envelope(
                    envelope_path,
                    root=root,
                    tracked={payload["artifact_path"], payload["producer_manifest_path"]},
                    expected_artifact_path=payload["artifact_path"],
                    expected_producer_manifest=payload["producer_manifest_path"],
                )

        with self.assertRaisesRegex(ValueError, "recursively envelope"):
            validate_artifacts(
                [
                    {
                        "kind": "summary",
                        "path": "experiments/x/results/a.json.envelope.json",
                        "public": True,
                        "envelope_path": "experiments/x/results/b.json.envelope.json",
                    }
                ]
            )

    def test_missing_omission_list_and_incomplete_grid_fail(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            envelope_path, payload = self._stage_valid_pair(root)
            artifact = root / payload["artifact_path"]
            tracked = {
                payload["artifact_path"],
                payload["producer_manifest_path"],
                str(envelope_path.relative_to(root)),
            }

            public = json.loads(artifact.read_text())
            public["coverage"]["omitted_raw_fields"] = []
            artifact.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")
            bad = copy.deepcopy(payload)
            bad["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            bad["artifact_bytes"] = artifact.stat().st_size
            bad["omitted_fields"] = []
            envelope_path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, "omitted_fields must not be empty"):
                validate_envelope(
                    envelope_path,
                    root=root,
                    tracked=tracked,
                    expected_artifact_path=payload["artifact_path"],
                    expected_producer_manifest=payload["producer_manifest_path"],
                )

            public = json.loads(E5_PUBLIC.read_text())
            public["cells"] = public["cells"][:134]
            public["coverage"]["exported_cells"] = 134
            artifact.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")
            bad = copy.deepcopy(payload)
            bad["artifact_sha256"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            bad["artifact_bytes"] = artifact.stat().st_size
            bad["expected_rows"] = 135
            bad["exported_rows"] = 134
            bad["omitted_fields"] = public["coverage"]["omitted_raw_fields"]
            envelope_path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(
                ValueError, "expected_rows and exported_rows disagree"
            ):
                validate_envelope(
                    envelope_path,
                    root=root,
                    tracked=tracked,
                    expected_artifact_path=payload["artifact_path"],
                    expected_producer_manifest=payload["producer_manifest_path"],
                )

    def test_fixture_exporter_emits_envelope_sidecar(self) -> None:
        public = build_public_artifact(_raw_payload())
        public_text = json.dumps(public, indent=2, sort_keys=True) + "\n"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            envelope_path = root / "public.json.envelope.json"
            envelope = write_envelope(
                public_text.encode("utf-8"),
                envelope_path,
                artifact_path="public.json",
            )
            self.assertTrue(envelope_path.is_file())
            self.assertEqual(envelope["expected_rows"], 135)
            self.assertEqual(envelope["producer_manifest_path"], E5_MANIFEST)
            self.assertEqual(
                len(cast(list[object], envelope["included_fields"])),
                len(PUBLIC_CELL_FIELDS),
            )

            rebuilt = build_envelope_from_public_artifact(
                artifact_path="public.json",
                public_bytes=public_text.encode("utf-8"),
                producer_manifest_path=E5_MANIFEST,
                claim_ids=["COMMITMENT_GENERATOR_GENERALIZATION"],
                evidence_ids=["EVID-COMMITMENT-E5-COVERAGE"],
                gate_verdict_paths=[
                    "experiments/commitment_surface/results/gate_verdicts/"
                    "e5_strict_coverage.json"
                ],
                generator_version="commitment_surface.e5_public_export.v1",
                included_fields=list(PUBLIC_CELL_FIELDS),
                public_safety_notes="fixture",
            )
            self.assertEqual(rebuilt["artifact_sha256"], envelope["artifact_sha256"])


if __name__ == "__main__":
    unittest.main()
