from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from experiments.gauge_fixed_concern_transport.budget import estimate_modal_cost
from experiments.gauge_fixed_concern_transport.core import (
    TRACKS,
    evaluate_gates,
    run_suite,
    summarize_rows,
)
from experiments.gauge_fixed_concern_transport.summarize import write_report


class GaugeFixedConcernTransportExperimentTests(unittest.TestCase):
    def test_smoke_suite_runs_all_tracks_and_passes(self) -> None:
        payload = run_suite("smoke")
        self.assertEqual(set(payload["summary"]["tracks"]), set(TRACKS))
        self.assertEqual(payload["summary"]["n_rows"], len(TRACKS) * 4)
        self.assertTrue(payload["summary"]["gates"]["all_pass"])

    def test_subset_track_runs_only_requested_gate(self) -> None:
        payload = run_suite("smoke", tracks=["mechanistic_commitment"], seeds=2)
        self.assertEqual(payload["summary"]["tracks"], ["mechanistic_commitment"])
        self.assertTrue(payload["summary"]["gates"]["mechanistic_commitment"]["pass"])
        self.assertTrue(payload["summary"]["gates"]["all_pass"])

    def test_gate_failure_coverage(self) -> None:
        payload = run_suite("smoke")
        by_track = copy.deepcopy(payload["summary"]["by_track"])
        cases = {
            "concern_weighted_ood": {"weighted_error_gain": 0.0},
            "causal_gauge_fixing": {"alignment_lift": 0.0},
            "mechanistic_commitment": {"patch_effect_ratio": 1.0},
            "reafference_null": {"attribution_lift": 0.0},
            "moved_bottleneck": {"localized_active_bottleneck": 0.5},
        }
        for track, bad_metrics in cases.items():
            mutated = copy.deepcopy(by_track)
            for metric, value in bad_metrics.items():
                mutated[track]["metrics"][metric]["mean"] = value
            self.assertFalse(evaluate_gates(mutated)[track]["pass"], track)

    def test_summary_schema_is_json_stable(self) -> None:
        payload = run_suite("smoke", seeds=1)
        encoded = json.dumps(payload, sort_keys=True)
        decoded = json.loads(encoded)
        summary = summarize_rows(decoded["rows"])
        self.assertEqual(summary["n_rows"], len(TRACKS))
        self.assertIn("all_pass", summary["gates"])

    def test_budget_estimate_refuses_over_budget_dispatch(self) -> None:
        estimate = estimate_modal_cost(
            320,
            250.0,
            gpu="L4",
            timeout_seconds=900,
            max_containers=64,
            gpu_rate_per_second=0.000222,
        )
        self.assertAlmostEqual(estimate["conservative_cost_usd"], 63.936)
        self.assertTrue(estimate["within_budget"])
        over_budget = estimate_modal_cost(
            320,
            10.0,
            gpu="L4",
            timeout_seconds=900,
            max_containers=64,
            gpu_rate_per_second=0.000222,
        )
        self.assertFalse(over_budget["within_budget"])

    def test_report_generation_includes_audit_and_gate_table(self) -> None:
        payload = run_suite("smoke")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            write_report(payload, out)
            text = out.read_text()
        self.assertIn("# Gauge-Fixed Concern Transport L4 Suite", text)
        self.assertIn("Overall: **PASS**", text)
        self.assertIn("Discovery-Regime Audit", text)
        self.assertIn("synthetic L4 empirical validation", text)


if __name__ == "__main__":
    unittest.main()
