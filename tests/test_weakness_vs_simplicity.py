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


if __name__ == "__main__":
    unittest.main()
