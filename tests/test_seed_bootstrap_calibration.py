from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from experiments.seed_bootstrap_calibration.simulation import (
    DEFAULT_CONFIG,
    CalibrationConfig,
    Regime,
    bootstrap_interval,
    build_public_summary,
    render_markdown,
    run_calibration,
)


class SeedBootstrapCalibrationTest(unittest.TestCase):
    def test_default_grid_keeps_the_preregistered_seed_floors(self) -> None:
        self.assertEqual(DEFAULT_CONFIG.seed_counts, (3, 5, 8, 10, 16, 64))
        self.assertEqual(
            DEFAULT_CONFIG.methods,
            ("naive_row_percentile", "paired_seed_cluster_percentile"),
        )

    def test_bootstrap_is_deterministic_and_cluster_interval_is_wider(self) -> None:
        paired_differences = np.array(
            [
                [-3.2, -3.1, -3.0, -2.9],
                [-1.2, -1.1, -1.0, -0.9],
                [0.9, 1.0, 1.1, 1.2],
                [2.9, 3.0, 3.1, 3.2],
            ]
        )

        naive = bootstrap_interval(
            paired_differences,
            method="naive_row_percentile",
            bootstrap_reps=400,
            confidence=0.95,
            seed=17,
        )
        repeated = bootstrap_interval(
            paired_differences,
            method="naive_row_percentile",
            bootstrap_reps=400,
            confidence=0.95,
            seed=17,
        )
        clustered = bootstrap_interval(
            paired_differences,
            method="paired_seed_cluster_percentile",
            bootstrap_reps=400,
            confidence=0.95,
            seed=17,
        )

        self.assertEqual(naive, repeated)
        self.assertGreater(clustered[1] - clustered[0], naive[1] - naive[0])

    def test_run_is_deterministic_and_preserves_every_cell(self) -> None:
        config = CalibrationConfig(
            seed_counts=(3, 8),
            episodes_per_seed=4,
            monte_carlo_reps=12,
            bootstrap_reps=50,
            confidence=0.95,
            simulation_seed=1234,
            regimes=(
                Regime(
                    name="moderate_hierarchy",
                    claim_type="directional_effect",
                    effect=0.5,
                    noise_sd=0.7,
                    hierarchy_sd=0.8,
                    target_width=1.0,
                ),
                Regime(
                    name="weak_high_noise_hierarchy",
                    claim_type="directional_effect",
                    effect=0.2,
                    noise_sd=1.5,
                    hierarchy_sd=1.2,
                    target_width=0.8,
                ),
            ),
        )

        first = run_calibration(config)
        second = run_calibration(config)

        self.assertEqual(first, second)
        self.assertEqual(len(first["cells"]), 8)
        observed = {
            (cell["regime"], cell["seed_count"], cell["method"])
            for cell in first["cells"]
        }
        expected = {
            (regime.name, seed_count, method)
            for regime in config.regimes
            for seed_count in config.seed_counts
            for method in config.methods
        }
        self.assertEqual(observed, expected)
        self.assertEqual(len(first["decision_table"]), 4)
        weak_rows = [
            row
            for row in first["decision_table"]
            if row["regime"] == "weak_high_noise_hierarchy"
        ]
        self.assertTrue(
            all(row["recommendation"] != "promotion_ready" for row in weak_rows)
        )

    def test_public_summary_is_aggregate_only_and_renders_decisions(self) -> None:
        config = CalibrationConfig(
            seed_counts=(3,),
            episodes_per_seed=3,
            monte_carlo_reps=8,
            bootstrap_reps=30,
            confidence=0.95,
            simulation_seed=9,
            regimes=(
                Regime(
                    name="weak_high_noise_hierarchy",
                    claim_type="directional_effect",
                    effect=0.2,
                    noise_sd=1.5,
                    hierarchy_sd=1.2,
                    target_width=0.8,
                ),
            ),
        )
        result = run_calibration(config)
        summary = build_public_summary(result)
        encoded = json.dumps(summary)
        markdown = render_markdown(summary)

        self.assertNotIn("paired_differences", encoded)
        self.assertNotIn("replicate_rows", encoded)
        self.assertIn("weak_high_noise_hierarchy", encoded)
        self.assertIn("Decision table", markdown)
        self.assertIn("Negative regimes are retained", markdown)

    def test_committed_summary_exactly_matches_default_deterministic_run(self) -> None:
        committed = json.loads(
            Path(
                "experiments/seed_bootstrap_calibration/results/summary.json"
            ).read_text(encoding="utf-8")
        )
        regenerated = json.loads(
            json.dumps(build_public_summary(run_calibration(DEFAULT_CONFIG)))
        )

        self.assertEqual(committed, regenerated)


if __name__ == "__main__":
    unittest.main()
