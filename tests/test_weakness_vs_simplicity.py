from __future__ import annotations

import random
import unittest

from experiments.weakness_vs_simplicity.experiment import (
    add_broad_negative_excluder,
    add_memorizer,
    all_worlds,
    choose_simplicity,
    choose_weakness,
    consistent,
    run_trial,
    reusable_candidates,
)


class WeaknessVsSimplicityTest(unittest.TestCase):
    def test_memorizer_is_consistent_and_simplest(self) -> None:
        worlds = all_worlds(4)
        candidates = reusable_candidates(worlds, 4)
        target = next(candidate for candidate in candidates if candidate.name == "x0=1")
        positives = list(target.extension)[:2]
        negatives = [world for world in worlds if world not in target.extension][:2]

        consistent_candidates = consistent(add_memorizer(candidates, positives), positives, negatives)
        chosen = choose_simplicity(consistent_candidates, random.Random(1))

        self.assertEqual(chosen.name, "memorize_observed_positives")
        self.assertEqual(chosen.form_length, 1)

    def test_weakness_prefers_reusable_broad_rule(self) -> None:
        worlds = all_worlds(4)
        candidates = reusable_candidates(worlds, 4)
        target = next(candidate for candidate in candidates if candidate.name == "x0=1")
        positives = list(target.extension)[:3]
        negatives = [world for world in worlds if world not in target.extension][:3]

        consistent_candidates = consistent(add_memorizer(candidates, positives), positives, negatives)
        chosen = choose_weakness(consistent_candidates, random.Random(1))

        self.assertNotEqual(chosen.name, "memorize_observed_positives")
        self.assertGreater(chosen.weakness, len(positives))

    def test_without_memorizer_simplicity_uses_reusable_rule(self) -> None:
        worlds = all_worlds(4)
        candidates = reusable_candidates(worlds, 4)
        target = next(candidate for candidate in candidates if candidate.name == "x0=1")
        positives = list(target.extension)[:3]
        negatives = [world for world in worlds if world not in target.extension][:3]

        consistent_candidates = consistent(candidates, positives, negatives)
        chosen = choose_simplicity(consistent_candidates, random.Random(1))

        self.assertNotEqual(chosen.name, "memorize_observed_positives")
        self.assertEqual(chosen.form_length, 4)

    def test_broad_negative_excluder_breaks_pure_weakness(self) -> None:
        worlds = all_worlds(4)
        candidates = reusable_candidates(worlds, 4)
        target = next(candidate for candidate in candidates if candidate.name == "x0=1")
        positives = list(target.extension)[:3]
        negatives = [world for world in worlds if world not in target.extension][:3]

        with_broad_candidate = add_broad_negative_excluder(candidates, worlds, negatives)
        consistent_candidates = consistent(with_broad_candidate, positives, negatives)

        weakness_choice = choose_weakness(consistent_candidates, random.Random(1))
        simplicity_choice = choose_simplicity(consistent_candidates, random.Random(1))

        self.assertEqual(weakness_choice.name, "exclude_observed_negatives")
        self.assertEqual(simplicity_choice.form_length, 4)
        self.assertNotEqual(simplicity_choice.name, "exclude_observed_negatives")

    def test_validation_gate_recovers_from_broad_excluder(self) -> None:
        worlds = all_worlds(4)
        candidates = reusable_candidates(worlds, 4)
        results = run_trial(
            rng=random.Random(1),
            worlds=worlds,
            base_candidates=candidates,
            selectors={"weakness": choose_weakness},
            train_positives=2,
            train_negatives=2,
            validation_positives=0,
            validation_negatives=3,
            include_memorizer=False,
            include_broad_negative_excluder=True,
        )

        by_selector = {result.selector: result for result in results}

        self.assertEqual(by_selector["weakness"].chosen, "exclude_observed_negatives")
        self.assertNotEqual(by_selector["validated_weakness"].chosen, "exclude_observed_negatives")
        self.assertGreater(by_selector["validated_weakness"].jaccard, by_selector["weakness"].jaccard)


if __name__ == "__main__":
    unittest.main()
