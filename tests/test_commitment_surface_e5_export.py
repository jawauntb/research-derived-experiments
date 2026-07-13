from __future__ import annotations

import json
import unittest

from scripts.export_commitment_surface_e5_results import (
    build_public_artifact,
    render_markdown,
    update_paper,
)


def _raw_payload(*, ready: bool = True) -> bytes:
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
    per_arm = {
        arm: {
            "canonical_ood_accuracy": 0.5,
            "paraphrase_ood_accuracy": 0.25,
            "novel_k_equivariance_accuracy": 0.5,
            "canonical_normalized_patch_ce": 0.1,
            "paraphrase_normalized_patch_ce": 0.05,
        }
        for arm in arms
    }
    return json.dumps(
        {
            "run_manifest": {
                "manifest_id": "manifest",
                "implementation_fingerprint": "fingerprint",
            },
            "config": {"sizes": ["70m", "160m", "410m"]},
            "cells": cells,
            "analysis": {
                "n_cells": len(cells),
                "per_arm": per_arm,
                "confirmatory_ready": ready,
                "grid_audit": {
                    "grid_complete": True,
                    "cell_data_complete": True,
                },
                "verdict": "coverage",
                "generator_learning_gate": False,
                "coverage_gate": True,
                "mixed_gate": False,
                "group_specificity_gate": False,
                "transport_gate": False,
                "canonical_G_minus_A": 0.0,
                "canonical_G_minus_Cov": -0.5,
                "novel_k_G_minus_A": 0.0,
                "paraphrase_lift_retained": 0.0,
            },
        }
    ).encode()


class CommitmentSurfaceE5ExportTest(unittest.TestCase):
    def test_export_keeps_metrics_and_omits_support_lists(self) -> None:
        public = build_public_artifact(_raw_payload())

        self.assertEqual(public["coverage"]["exported_cells"], 135)
        self.assertTrue(public["coverage"]["complete"])
        self.assertNotIn("split", public["cells"][0])
        self.assertIn("split", public["coverage"]["omitted_raw_fields"])
        self.assertIn("Strict verdict: `coverage`", render_markdown(public))

    def test_export_rejects_nonconfirmatory_payload(self) -> None:
        with self.assertRaisesRegex(ValueError, "not confirmatory-ready"):
            build_public_artifact(_raw_payload(ready=False))

    def test_paper_update_replaces_only_marked_blocks(self) -> None:
        public = build_public_artifact(_raw_payload())
        paper = """Before
<!-- E5_ABSTRACT_START -->
pending abstract
<!-- E5_ABSTRACT_END -->
Middle
<!-- E5_CLAIM_UPDATE_START -->
pending claim
<!-- E5_CLAIM_UPDATE_END -->
After
"""

        updated = update_paper(public, paper)

        self.assertIn("strict verdict **coverage**", updated)
        self.assertIn("E5 confirmatory verdict: coverage", updated)
        self.assertNotIn("pending abstract", updated)
        self.assertTrue(updated.startswith("Before"))
        self.assertTrue(updated.endswith("After\n"))


if __name__ == "__main__":
    unittest.main()
