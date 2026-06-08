from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_label_free_dose_response.py"
)
SPEC = importlib.util.spec_from_file_location("dose_response_summary", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
dose_response_summary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dose_response_summary)


class SummarizeLabelFreeDoseResponseTest(unittest.TestCase):
    def test_source_noop_rows_group_by_seed_surface_and_grid_cell(self) -> None:
        payload = {
            "manifest": {
                "model_id": "test-model",
                "seed": 7,
                "patch_vector_surface": "hook_output",
                "injection_layers": [6],
                "readout_layers": [6],
                "patch_alphas": [1.0],
                "patch_text_regimes": ["definition"],
                "pair_set": "combined",
                "baseline_sample_count": 1,
                "pairs": [{"pair": "source->target"}],
            },
            "aggregate_rows": [
                {
                    "patch_text_regime": "definition",
                    "patch_mode": "source_noop",
                    "patch_vector_surface": "hook_output",
                    "injection_layer": 6,
                    "readout_layer": 6,
                    "patch_alpha": 1.0,
                    "mean_target_margin_delta": -0.0,
                },
                {
                    "patch_text_regime": "neutral",
                    "patch_mode": "source_noop",
                    "patch_vector_surface": "hook_output",
                    "injection_layer": 6,
                    "readout_layer": 6,
                    "patch_alpha": 1.0,
                    "mean_target_margin_delta": 0.5,
                },
            ],
            "specificity_rows": [],
            "dose_response_summaries": [],
            "transfer_baseline_summaries": [],
        }

        rows = dose_response_summary.source_noop_rows(
            [(Path("artifact_seed7.json"), payload)]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["artifact"], "seed 7")
        self.assertEqual(rows[0]["surface"], "hook_output")
        self.assertEqual(rows[0]["cell"], "6 -> 6")
        self.assertEqual(rows[0]["max_abs_delta"], 0.0)

    def test_render_manifest_reports_surface_and_pair_count(self) -> None:
        rows = [
            {
                "artifact": "seed 7",
                "model": "test-model",
                "seed": 7,
                "surface": "hook_output",
                "injection_layers": "3,4,5,6",
                "readout_layers": "6",
                "alphas": "0.5,0.75,1.0",
                "regimes": "definition,neutral",
                "pair_set": "combined",
                "baseline_n": 24,
                "pairs": 31,
            }
        ]

        markdown = dose_response_summary.render_manifest(rows)

        self.assertIn("hook_output", markdown)
        self.assertIn("31", markdown)


if __name__ == "__main__":
    unittest.main()
