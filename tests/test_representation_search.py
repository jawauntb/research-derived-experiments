from __future__ import annotations

import unittest

from experiments.representation_search.core import (
    DEFAULT_TASKS,
    all_worlds,
    conditional_entropy,
    evaluate_benchmark,
    evaluate_task,
    parity,
    quotient_library,
    score_quotient,
)


class RepresentationSearchTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_minimal_sufficient_recovers_each_ground_truth(self) -> None:
        for task in DEFAULT_TASKS:
            report = evaluate_task(task)
            chosen = report["selections"]["minimal_sufficient"]["chosen"]
            self.assertEqual(chosen, report["ground_truth_quotient"])

    def test_mdl_only_is_never_sufficient(self) -> None:
        for task in DEFAULT_TASKS:
            report = evaluate_task(task)
            self.assertFalse(report["selections"]["mdl_only"]["sufficient"])

    def test_ground_truth_quotient_has_zero_conditional_entropy(self) -> None:
        task = DEFAULT_TASKS[0]
        worlds = all_worlds(task.n_bits)

        def target(world: tuple[int, ...]) -> int:
            value = parity(task.truth_coords)(world)
            assert isinstance(value, int)
            return value

        truth = next(
            q for q in quotient_library(task.n_bits) if q.coords == task.truth_coords
        )
        self.assertAlmostEqual(conditional_entropy(worlds, target, truth), 0.0, places=12)

    def test_identity_is_sufficient_but_uncompressed(self) -> None:
        task = DEFAULT_TASKS[0]
        worlds = all_worlds(task.n_bits)

        def target(world: tuple[int, ...]) -> int:
            value = parity(task.truth_coords)(world)
            assert isinstance(value, int)
            return value

        identity = next(q for q in quotient_library(task.n_bits) if q.name == "identity")
        score = score_quotient(worlds, target, identity)
        self.assertTrue(score.sufficient)
        self.assertEqual(score.image_size, 2**task.n_bits)


if __name__ == "__main__":
    unittest.main()
