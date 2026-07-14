from __future__ import annotations

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from experiments.bayesian_voi.core import (
    classification_error,
    evaluate_benchmark,
    exact_evsi,
    mutual_information,
    posterior,
)


ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "experiments" / "bayesian_voi" / "results" / "bayesian_voi_summary.json"


class BayesianValueOfInformationTests(unittest.TestCase):
    def test_all_preregistered_gates_pass(self) -> None:
        payload = evaluate_benchmark()
        self.assertTrue(all(payload["gates"].values()))

    def test_current_error_heuristic_cannot_rank_probes(self) -> None:
        payload = evaluate_benchmark()
        learnable = {row["scenario"]: row for row in payload["scenarios"]}[
            "learnable_uncertainty"
        ]
        rows = learnable["probes"]
        self.assertEqual(len({row["current_error"] for row in rows}), 1)
        self.assertEqual(len({row["error_squared_over_k_plus_one"] for row in rows}), 1)
        self.assertEqual(learnable["top_by_metric"]["oracle_evsi"], ["signal"])

    def test_misspecification_preserves_information_value_divergence(self) -> None:
        payload = evaluate_benchmark()
        by_name = {row["scenario"]: row for row in payload["scenarios"]}
        misspecified = by_name["model_misspecification"]
        self.assertEqual(misspecified["top_by_metric"]["mutual_information"], ["misleading_signal"])
        self.assertEqual(misspecified["top_by_metric"]["oracle_evsi"], ["robust_weak_signal"])

        irreducible = by_name["irreducible_noise"]
        self.assertTrue(all(row["oracle_evsi"] == 0.0 for row in irreducible["probes"]))
        self.assertTrue(all(row["mutual_information"] == 0.0 for row in irreducible["probes"]))

    def test_exact_calculations_match_hand_values(self) -> None:
        prior = {"A": 0.6, "B": 0.4}
        signal = {"A": 0.9, "B": 0.1}
        posterior_signal = posterior(prior, signal, 1)
        self.assertTrue(math.isclose(posterior_signal["A"], 0.9310344827586207, rel_tol=1e-12))
        self.assertTrue(math.isclose(posterior_signal["B"], 0.06896551724137931, rel_tol=1e-12))
        self.assertTrue(math.isclose(classification_error(prior), 0.4, rel_tol=1e-12))
        self.assertTrue(math.isclose(exact_evsi(prior, signal), 0.3, rel_tol=1e-12))
        self.assertTrue(
            math.isclose(mutual_information(prior, {"A": 0.5, "B": 0.5}), 0.0, abs_tol=1e-12)
        )

    def test_runner_is_deterministic_and_public_safe(self) -> None:
        package = ROOT / "experiments" / "bayesian_voi"
        with TemporaryDirectory() as directory:
            outputs = [Path(directory) / "a.json", Path(directory) / "b.json"]
            for output in outputs:
                completed = subprocess.run(
                    [sys.executable, str(package / "experiment.py"), "--output", str(output)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(json.loads(completed.stdout), {"scenarios": 3, "status": "pass"})
            self.assertEqual(outputs[0].read_bytes(), outputs[1].read_bytes())
            text = outputs[0].read_text()
            self.assertNotIn("timestamp", text.lower())
            self.assertNotIn("/Users/", text)

    def test_committed_summary_is_exactly_regenerated(self) -> None:
        self.assertEqual(json.loads(SUMMARY.read_text()), evaluate_benchmark())


if __name__ == "__main__":
    unittest.main()
