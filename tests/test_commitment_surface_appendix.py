from __future__ import annotations

import json
import unittest

from scripts.export_commitment_surface_e4_appendix import build_public_artifact


class CommitmentSurfaceAppendixTests(unittest.TestCase):
    def test_e4_export_keeps_metrics_and_omits_raw_tables(self) -> None:
        raw = {
            "config": {
                "sizes": ["70m"],
                "ns": [13],
                "seeds": [7],
                "arms": ["A"],
                "train_frac": 0.5,
                "epochs": 2,
                "lora_rank": 8,
            },
            "analysis": {"n_cells": 1, "per_arm": {}},
            "cells": [{
                "arm": "A",
                "size": "70m",
                "n": 13,
                "seed": 7,
                "ood_accuracy": 0.25,
                "patch_ce_delta": 0.5,
                "weakness_oracle_norm": 0.1,
                "function_table": [1, 2, 3],
                "train_inputs": [0, 1],
            }],
        }

        exported = build_public_artifact(json.dumps(raw).encode())

        self.assertEqual(exported["coverage"]["exported_cells"], 1)
        self.assertTrue(exported["coverage"]["complete"])
        self.assertEqual(exported["cells"][0]["ood_accuracy"], 0.25)
        self.assertNotIn("function_table", exported["cells"][0])
        self.assertNotIn("train_inputs", exported["cells"][0])
        self.assertIn("function_table", exported["coverage"]["omitted_raw_fields"])


if __name__ == "__main__":
    unittest.main()
