from __future__ import annotations

import unittest

from experiments.abstraction_frontier_pair.core import (
    N_BITS,
    SHARED_FAMILY,
    TRUE_Z_NAME,
    all_worlds,
    coding_cost,
    conditional_entropy,
    evaluate_benchmark,
    is_antichain,
    latent_z,
    pareto_frontier,
    quotient_library,
    score_quotient,
    strictly_finer,
    task_sufficiency,
    weakly_dominates,
)


class AbstractionFrontierPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_pareto_frontier_has_exactly_two_members(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(
            set(payload["pareto_frontier"]),
            {"constant", TRUE_Z_NAME},
        )

    def test_true_Z_has_zero_task_sufficiency_on_shared_family(self) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        z = next(q for q in library if q.name == TRUE_Z_NAME)
        self.assertAlmostEqual(
            task_sufficiency(worlds, SHARED_FAMILY, z), 0.0, places=12
        )

    def test_identity_has_zero_task_sufficiency_but_higher_coding_cost(
        self,
    ) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        z = next(q for q in library if q.name == TRUE_Z_NAME)
        identity = next(q for q in library if q.name == "identity")
        z_axes = score_quotient(worlds, SHARED_FAMILY, z)
        id_axes = score_quotient(worlds, SHARED_FAMILY, identity)
        self.assertEqual(z_axes.task_sufficiency, 0.0)
        self.assertEqual(id_axes.task_sufficiency, 0.0)
        self.assertLess(z_axes.coding_cost, id_axes.coding_cost)
        self.assertTrue(weakly_dominates(z_axes, id_axes))

    def test_identity_is_strictly_finer_than_true_Z(self) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        z = next(q for q in library if q.name == TRUE_Z_NAME)
        identity = next(q for q in library if q.name == "identity")
        self.assertTrue(strictly_finer(identity, z, worlds))
        self.assertFalse(strictly_finer(z, identity, worlds))

    def test_frontier_is_antichain(self) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        scored = [score_quotient(worlds, SHARED_FAMILY, q) for q in library]
        self.assertTrue(is_antichain(pareto_frontier(scored)))

    def test_constant_map_has_worst_task_sufficiency_and_lowest_coding_cost(
        self,
    ) -> None:
        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        constant = next(q for q in library if q.name == "constant")
        axes = score_quotient(worlds, SHARED_FAMILY, constant)
        self.assertEqual(axes.coding_cost, 0.0)
        # Each shared task is a balanced Boolean, so H(Y_alpha) = 1 bit;
        # sufficiency under the constant map is the max residual = 1.
        self.assertAlmostEqual(axes.task_sufficiency, 1.0, places=12)

    def test_lattice_library_contains_expected_23_quotients(self) -> None:
        library = quotient_library(N_BITS)
        self.assertEqual(len(library), 23)
        names = {q.name for q in library}
        self.assertIn("constant", names)
        self.assertIn(TRUE_Z_NAME, names)
        self.assertIn("identity", names)

    def test_pareto_frontier_stable_under_lattice_refinement(self) -> None:
        worlds = all_worlds(N_BITS)
        base = quotient_library(N_BITS)
        # Adding the base library twice should not shrink the frontier: adding
        # duplicates or refinements of Q is only monotone non-decreasing
        # on the Pareto set (Theorem AF-1 monotonicity clause).
        extended = list(base) + list(base)
        base_scored = [score_quotient(worlds, SHARED_FAMILY, q) for q in base]
        extended_scored = [
            score_quotient(worlds, SHARED_FAMILY, q) for q in extended
        ]
        base_names = {r.quotient for r in pareto_frontier(base_scored)}
        ext_names = {r.quotient for r in pareto_frontier(extended_scored)}
        self.assertTrue(base_names.issubset(ext_names))

    def test_latent_z_matches_true_Z_quotient_conditional_entropy_zero(
        self,
    ) -> None:
        worlds = all_worlds(N_BITS)
        # Each shared task should have H(Y_alpha | latent_z(X)) = 0.
        for task in SHARED_FAMILY:
            library = quotient_library(N_BITS)
            z = next(q for q in library if q.name == TRUE_Z_NAME)
            self.assertAlmostEqual(
                conditional_entropy(worlds, task.fn, z), 0.0, places=12
            )
        # And latent_z is the joint of the two pair-parities.
        self.assertEqual(latent_z((1, 0, 1, 1)), (1 ^ 0, 1 ^ 1))

    def test_coding_cost_matches_log2_image_size(self) -> None:
        import math

        worlds = all_worlds(N_BITS)
        library = quotient_library(N_BITS)
        for q in library:
            self.assertAlmostEqual(
                coding_cost(worlds, q),
                math.log2(len(q.image(worlds))),
                places=12,
            )


if __name__ == "__main__":
    unittest.main()
