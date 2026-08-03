from __future__ import annotations

import unittest

from experiments.cross_task_sufficiency.core import (
    N_BITS,
    NOT_SHARED_FAMILY,
    SHARED_FAMILY,
    all_worlds,
    coarsest_common_sufficient_statistic,
    conditional_entropy,
    evaluate_benchmark,
    latent_z,
    minimal_sufficient_for_task,
    quotient_library,
    score_family,
)


class CrossTaskSufficiencyTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_shared_family_css_is_latent_Z(self) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        css = coarsest_common_sufficient_statistic(worlds, SHARED_FAMILY, library)
        self.assertEqual(css.quotient, "joint(parity{0,1},parity{2,3})")
        self.assertEqual(css.image_size, 4)

    def test_not_shared_family_css_is_identity(self) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        css = coarsest_common_sufficient_statistic(worlds, NOT_SHARED_FAMILY, library)
        self.assertEqual(css.quotient, "identity")
        self.assertEqual(css.image_size, 2**N_BITS)

    def test_family_css_finer_than_single_task_mss(self) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        css = coarsest_common_sufficient_statistic(worlds, SHARED_FAMILY, library)
        for task in SHARED_FAMILY:
            mss = minimal_sufficient_for_task(worlds, task, library)
            self.assertLessEqual(mss.image_size, css.image_size)

    def test_latent_Z_makes_every_shared_task_deterministic(self) -> None:
        worlds = all_worlds(N_BITS)
        for task in SHARED_FAMILY:
            groups: dict[tuple[int, int], set[int]] = {}
            for w in worlds:
                groups.setdefault(latent_z(w), set()).add(task.fn(w))
            for value_set in groups.values():
                self.assertEqual(len(value_set), 1)

    def test_latent_Z_is_sufficient_for_every_shared_task(self) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        z = next(q for q in library if q.name == "joint(parity{0,1},parity{2,3})")
        for task in SHARED_FAMILY:
            self.assertAlmostEqual(
                conditional_entropy(worlds, task.fn, z), 0.0, places=12
            )

    def test_individual_bit_reads_are_not_common_sufficient_for_shared_family(
        self,
    ) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        for name in ("parity{0,1}", "parity{2,3}", "parity{0}", "parity{1}"):
            q = next(q for q in library if q.name == name)
            family_score, _ = score_family(worlds, SHARED_FAMILY, q)
            self.assertFalse(family_score.common_sufficient)


if __name__ == "__main__":
    unittest.main()
