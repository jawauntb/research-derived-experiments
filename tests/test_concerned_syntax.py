from __future__ import annotations

import random
import unittest

from experiments.concerned_syntax.benchmark import (
    Intervention,
    concern_gap,
    choose_intervention,
    information_gain,
    make_trial,
    outcome_for_parse,
    run_trials,
    summarize,
)


class ConcernedSyntaxTest(unittest.TestCase):
    def test_same_surface_can_have_different_concern_outcomes(self) -> None:
        rng = random.Random(1)
        trial = make_trial(0, rng)
        # Force until the sampled trial is high-concern enough for the test.
        for idx in range(1, 50):
            if concern_gap(trial) >= 0.10:
                break
            trial = make_trial(idx, rng)

        true_outcome = outcome_for_parse(trial, trial.true_parse)
        alt_outcome = outcome_for_parse(trial, trial.alternate_parse)

        self.assertNotEqual(true_outcome, alt_outcome)
        self.assertGreaterEqual(concern_gap(trial), 0.10)

    def test_pair_probe_reveals_parse_when_constituency_differs(self) -> None:
        trial = make_trial(0, random.Random(4))
        probe = Intervention("pair_probe", "pair_probe", 0.04, pair=trial.causal_pair)

        self.assertEqual(information_gain(trial, probe), 1.0)

    def test_concerned_selector_avoids_low_concern_restless_probe(self) -> None:
        rng = random.Random(7)
        low_trial = make_trial(0, rng)
        for idx in range(1, 100):
            if concern_gap(low_trial) < 0.10:
                break
            low_trial = make_trial(idx, rng)

        intervention = choose_intervention(low_trial, "concerned_syntax", random.Random(8))

        self.assertEqual(intervention.name, "null")

    def test_benchmark_summary_separates_concerned_syntax(self) -> None:
        rows = run_trials(trials=200, seed=20260616)
        summary = summarize(rows)

        self.assertTrue(summary["concerned_syntax"]["gate_pass"])
        self.assertFalse(summary["flat_valence"]["gate_pass"])
        self.assertLessEqual(
            summary["concerned_syntax"]["low_concern_probe_rate"],
            0.25,
        )


if __name__ == "__main__":
    unittest.main()

