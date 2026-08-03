from __future__ import annotations

import unittest

from experiments.symbolic_causation.core import (
    EXPECTED_CLASS,
    base_environment,
    classify,
    evaluate_benchmark,
    evaluate_intervention,
    terminal_distribution,
    trajectory_distribution,
)
from experiments.symbolic_causation.core import (
    default_interventions as interventions,
)


class SymbolicCausationTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_taxonomy_matches_expected(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["classifications"], EXPECTED_CLASS)

    def test_trajectory_distribution_normalized(self) -> None:
        dist = trajectory_distribution(base_environment())
        self.assertAlmostEqual(sum(dist.values()), 1.0, places=12)
        terminal = terminal_distribution(base_environment())
        self.assertAlmostEqual(sum(terminal.values()), 1.0, places=12)

    def test_noise_signal_moves_distribution_without_control(self) -> None:
        row = next(
            evaluate_intervention(m)
            for m in interventions()
            if m.name == "noise_signal"
        )
        self.assertGreater(row["delta_kl"], 0.0)
        self.assertLess(abs(row["true_goal_effect"]), 1e-3)

    def test_false_credit_is_uncaused(self) -> None:
        row = next(
            evaluate_intervention(m) for m in interventions() if m.name == "false_credit"
        )
        self.assertGreater(row["observed_goal_gain"], 1e-3)
        self.assertLess(abs(row["true_goal_effect"]), 1e-3)
        self.assertGreater(row["calibration_error"], 1e-3)
        self.assertEqual(classify(row), "false_credit")

    def test_agent_transfers_brittle_does_not(self) -> None:
        rows = {m.name: evaluate_intervention(m) for m in interventions()}
        self.assertGreater(rows["agent"]["transfer"], 1e-3)
        self.assertLessEqual(rows["brittle_controller"]["transfer"], 1e-3)


if __name__ == "__main__":
    unittest.main()
