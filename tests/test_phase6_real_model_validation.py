from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.phase6_real_model_validation.budget import estimate_modal_cost
from experiments.phase6_real_model_validation.core import (
    TRACKS,
    evaluate_gates,
    failed_row,
    fixture_rows,
    rank_auc,
    run_suite,
    summarize_rows,
)
from experiments.phase6_real_model_validation.summarize import write_report


class Phase6RealModelValidationTests(unittest.TestCase):
    def test_fixture_suite_runs_all_tracks(self) -> None:
        payload = run_suite("smoke")
        self.assertGreater(payload["summary"]["n_rows"], 0)
        self.assertEqual(set(payload["summary"]["by_track"]), set(TRACKS))
        self.assertTrue(payload["summary"]["gates"]["all_pass"])

    def test_subset_track_runs_evaluate_only_present_gates(self) -> None:
        payload = run_suite("smoke", tracks=["frozen_encoder_metric_deformation"])
        self.assertEqual(set(payload["summary"]["gates"]), {"frozen_encoder_metric_deformation", "all_pass"})
        self.assertTrue(payload["summary"]["gates"]["all_pass"])

    def test_rank_auc_handles_ties(self) -> None:
        self.assertEqual(rank_auc([1, 0], [0.5, 0.5]), 0.5)
        self.assertEqual(rank_auc([1, 1, 0, 0], [0.8, 0.7, 0.2, 0.1]), 1.0)

    def test_failed_model_rows_do_not_pass_contact_gate(self) -> None:
        rows = [
            failed_row("open_lm_action_coupling", "bad_a", "fixture/bad-a", "download failed"),
            failed_row("open_lm_action_coupling", "bad_b", "fixture/bad-b", "download failed"),
        ]
        summary = summarize_rows(rows)
        self.assertFalse(summary["gates"]["open_lm_action_coupling"]["pass"])
        self.assertFalse(summary["gates"]["all_pass"])

    def test_gate_thresholds_have_failure_coverage(self) -> None:
        summary = summarize_rows(fixture_rows())
        self.assertTrue(summary["gates"]["all_pass"])

        cases = {
            "open_lm_action_coupling": {
                "geometry_action_r": 0.0,
                "label_geometry_gap": 0.0,
                "label_margin_lift": 0.0,
                "margin_auc": 0.50,
                "cue_specificity": 0.0,
            },
            "frozen_encoder_metric_deformation": {
                "deformed_margin_lift": 0.0,
                "template_transfer_auc": 0.50,
            },
        }
        for track, bad_metrics in cases.items():
            by_track = copy.deepcopy(summary["by_track"])
            for condition in by_track[track]["conditions"]:
                for metric, bad_value in bad_metrics.items():
                    by_track[track]["conditions"][condition]["metrics"][metric]["mean"] = bad_value
            self.assertFalse(evaluate_gates(by_track)[track]["pass"], track)

    def test_report_generation_includes_gate_summary(self) -> None:
        payload = run_suite("smoke")
        payload["manifest"]["budget_estimate"] = estimate_modal_cost(
            5,
            1000.0,
            gpu="L4",
            timeout_seconds=1800,
            max_containers=8,
            gpu_rate_per_second=0.000222,
        )
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "phase6_report.md"
            write_report(payload, out)
            text = out.read_text()
        self.assertIn("# Phase 6 Real-Model Validation L4 Suite", text)
        self.assertIn("Overall: **PASS**", text)
        self.assertIn("public open-model/frozen-encoder measurements", text)
        self.assertIn("budget estimate", text)

    def test_pdf_build_creates_nonempty_pdf_and_figure_when_dependencies_exist(self) -> None:
        for module in ["matplotlib", "PIL", "reportlab"]:
            if importlib.util.find_spec(module) is None:
                self.skipTest(f"{module} is not installed")
        from scripts.build_phase6_real_model_validation_pdf import build

        payload = run_suite("smoke")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload_path = root / "payload.json"
            pdf_path = root / "phase6.pdf"
            figure_dir = root / "figures"
            payload_path.write_text(json.dumps(payload))
            build(payload_path, pdf_path, figure_dir, copy_to_metaphysics=False)
            self.assertGreater(pdf_path.stat().st_size, 10_000)
            self.assertGreater((figure_dir / "fig1_phase6_gate_passes.png").stat().st_size, 1_000)

    def test_budget_estimate_refuses_over_budget_dispatch(self) -> None:
        estimate = estimate_modal_cost(
            5,
            1000.0,
            gpu="L4",
            timeout_seconds=1800,
            max_containers=8,
            gpu_rate_per_second=0.000222,
        )
        self.assertAlmostEqual(estimate["conservative_cost_usd"], 1.998)
        self.assertTrue(estimate["within_budget"])

        over_budget = estimate_modal_cost(
            5,
            1.0,
            gpu="L4",
            timeout_seconds=1800,
            max_containers=8,
            gpu_rate_per_second=0.000222,
        )
        self.assertFalse(over_budget["within_budget"])


if __name__ == "__main__":
    unittest.main()
