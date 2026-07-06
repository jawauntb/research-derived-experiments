from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.phase5_external_validity.budget import estimate_modal_cost
from experiments.phase5_external_validity.core import (
    TRACKS,
    evaluate_gates,
    run_cell,
    run_suite,
    summarize_rows,
)
from experiments.phase5_external_validity.summarize import write_report


class Phase5ExternalValidityTests(unittest.TestCase):
    def test_smoke_suite_runs_all_tracks(self) -> None:
        payload = run_suite("smoke", seeds=1)
        self.assertGreater(payload["summary"]["n_rows"], 0)
        self.assertEqual(set(payload["summary"]["by_track"]), set(TRACKS))
        self.assertTrue(payload["summary"]["gates"]["all_pass"])

    def test_each_track_cell_is_deterministic(self) -> None:
        for track in TRACKS:
            first = run_cell(track, seed=2, preset="smoke")
            second = run_cell(track, seed=2, preset="smoke")
            self.assertEqual(first, second)

    def test_subset_track_runs_evaluate_only_present_gates(self) -> None:
        payload = run_suite("smoke", tracks=["language_action_transport"], seeds=1)
        self.assertEqual(set(payload["summary"]["gates"]), {"language_action_transport", "all_pass"})
        self.assertTrue(payload["summary"]["gates"]["all_pass"])

    def test_gate_thresholds_have_failure_coverage(self) -> None:
        summary = run_suite("smoke", seeds=1)["summary"]
        gates = summary["gates"]
        self.assertTrue(gates["all_pass"])
        for track in TRACKS:
            self.assertTrue(gates[track]["pass"], track)

        cases = {
            "language_action_transport": (
                ("language_action_transport", "instruction_tuned_transport", "intervention_ratio"),
                1.0,
            ),
            "foundation_semantic_metric": (
                ("foundation_semantic_metric", "value_weighted_adapter", "collapse_index"),
                0.5,
            ),
            "role_routed_world_model": (
                ("role_routed_world_model", "shared_head", "mediated_mae"),
                gates["role_routed_world_model"]["role_mae"],
            ),
            "topology_seam_causality": (
                ("topology_seam_causality", "both_fixed", "seam_only_lift"),
                0.1,
            ),
        }
        for track, (metric_path, bad_value) in cases.items():
            by_track = copy.deepcopy(summary["by_track"])
            track_name, condition, metric = metric_path
            by_track[track_name]["conditions"][condition]["metrics"][metric]["mean"] = bad_value
            self.assertFalse(evaluate_gates(by_track)[track]["pass"], track)

    def test_report_generation_includes_gate_summary(self) -> None:
        payload = run_suite("smoke", seeds=1)
        payload["manifest"]["budget_estimate"] = estimate_modal_cost(
            4,
            1000.0,
            gpu="L4",
            timeout_seconds=900,
            max_containers=64,
            gpu_rate_per_second=0.000222,
        )
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "phase5_report.md"
            write_report(payload, out)
            text = out.read_text()
        self.assertIn("# Phase 5 External Validity L4 Suite", text)
        self.assertIn("Overall: **PASS**", text)
        self.assertIn("`language_action_transport`", text)
        self.assertIn("budget estimate", text)

    def test_pdf_build_creates_nonempty_pdf_and_figure_when_dependencies_exist(self) -> None:
        for module in ["matplotlib", "PIL", "reportlab"]:
            if importlib.util.find_spec(module) is None:
                self.skipTest(f"{module} is not installed")
        from scripts.build_phase5_external_validity_pdf import build

        payload = run_suite("smoke", seeds=1)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload_path = root / "payload.json"
            pdf_path = root / "phase5.pdf"
            figure_dir = root / "figures"
            payload_path.write_text(json.dumps(payload))
            build(payload_path, pdf_path, figure_dir, copy_to_metaphysics=False)
            self.assertGreater(pdf_path.stat().st_size, 10_000)
            self.assertGreater((figure_dir / "fig1_phase5_gate_passes.png").stat().st_size, 1_000)

    def test_budget_estimate_refuses_over_budget_dispatch(self) -> None:
        estimate = estimate_modal_cost(
            256,
            1000.0,
            gpu="L4",
            timeout_seconds=900,
            max_containers=64,
            gpu_rate_per_second=0.000222,
        )
        self.assertAlmostEqual(estimate["conservative_cost_usd"], 51.1488)
        self.assertTrue(estimate["within_budget"])

        over_budget = estimate_modal_cost(
            256,
            10.0,
            gpu="L4",
            timeout_seconds=900,
            max_containers=64,
            gpu_rate_per_second=0.000222,
        )
        self.assertFalse(over_budget["within_budget"])


if __name__ == "__main__":
    unittest.main()
