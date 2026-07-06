from __future__ import annotations

import unittest

import numpy as np

from experiments.virtual_governor_stress_signal.core import (
    CONDITIONS,
    DEFAULT_TARGET,
    OBS_DIM,
    TARGETS,
    apply_action,
    condition_observation,
    oracle_action,
    stress_norm,
    summarize_records,
)


class VirtualGovernorStressSignalTests(unittest.TestCase):
    def test_condition_observations_have_shared_shape(self) -> None:
        state = np.array([0.4, 0.5, 0.6], dtype=np.float32)
        target = TARGETS[0]
        history = [target - state]

        observations = [
            condition_observation(
                condition=condition,
                state=state,
                target=target,
                stress_history=history,
            )
            for condition in CONDITIONS
        ]

        self.assertTrue(all(obs.shape == (OBS_DIM,) for obs in observations))
        self.assertTrue(np.allclose(observations[0], 0.0))
        self.assertFalse(np.allclose(observations[-1], observations[1]))

    def test_oracle_action_reduces_or_preserves_stress(self) -> None:
        rng = np.random.default_rng(123)
        state = np.array([0.32, 0.72, 0.48], dtype=np.float32)
        target = DEFAULT_TARGET
        action = oracle_action(state, target)
        next_state = apply_action(state, action, rng, noise_scale=0.0)

        self.assertLessEqual(stress_norm(next_state, target), stress_norm(state, target))

    def test_summary_ranks_live_governor_when_scores_are_best(self) -> None:
        rows = []
        for condition, score in [
            ("reward_only", 0.25),
            ("local_state", 0.35),
            ("stale_governor", 0.45),
            ("wrong_governor", 0.10),
            ("virtual_governor", 0.80),
        ]:
            rows.append(
                {
                    "condition": condition,
                    "seed": 1,
                    "train_loss": 0.1,
                    "action_accuracy": score,
                    "mean_stress": 1.0 - score,
                    "post_shift_stress_auc": 1.0 - score,
                    "recovery_rate": score,
                    "mean_recovery_steps": 16.0 * (1.0 - score),
                    "final_stress": 1.0 - score,
                    "global_recovery_score": score,
                    "post_shift_curve": [1.0 - score, 0.9 - score / 2],
                }
            )

        summary = summarize_records(rows)

        self.assertEqual(summary["ranking"][0]["condition"], "virtual_governor")
        self.assertGreater(summary["headline_delta_recovery_score"], 0.5)


if __name__ == "__main__":
    unittest.main()
