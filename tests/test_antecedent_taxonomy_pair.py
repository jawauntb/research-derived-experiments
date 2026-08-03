from __future__ import annotations

import unittest

from experiments.antecedent_taxonomy_pair.core import (
    ANTECEDENTS,
    all_worlds,
    aux_ivae_antecedent,
    check_cross_u_coherence_equals_Z,
    check_local_separation,
    evaluate_benchmark,
    interventional_crl_antecedent,
    latent_z,
    linear_ica_antecedent,
    partition_intersection,
    partition_refines,
    partitions_equal,
    quotient_partition,
    sparse_linear_ica_antecedent,
    true_z_partition,
)


class AntecedentTaxonomyPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_true_Z_has_four_blocks_on_4bit_world(self) -> None:
        self.assertEqual(len(true_z_partition(all_worlds())), 4)

    def test_linear_ica_local_screen_equals_Z(self) -> None:
        worlds = all_worlds()
        screens = linear_ica_antecedent(worlds)
        self.assertEqual(len(screens), 1)
        self.assertTrue(partitions_equal(screens[0], true_z_partition(worlds)))

    def test_sparse_linear_ica_local_screen_equals_Z(self) -> None:
        worlds = all_worlds()
        screens = sparse_linear_ica_antecedent(worlds)
        self.assertTrue(partitions_equal(screens[0], true_z_partition(worlds)))

    def test_aux_ivae_two_screens_intersect_to_Z(self) -> None:
        worlds = all_worlds()
        screens = aux_ivae_antecedent(worlds)
        self.assertEqual(len(screens), 2)
        intersection = partition_intersection(screens, worlds)
        self.assertTrue(partitions_equal(intersection, true_z_partition(worlds)))

    def test_interventional_crl_three_screens_intersect_to_Z(self) -> None:
        worlds = all_worlds()
        screens = interventional_crl_antecedent(worlds)
        self.assertEqual(len(screens), 3)
        intersection = partition_intersection(screens, worlds)
        self.assertTrue(partitions_equal(intersection, true_z_partition(worlds)))

    def test_every_antecedent_has_local_separation(self) -> None:
        worlds = all_worlds()
        for name, constructor in ANTECEDENTS:
            with self.subTest(antecedent=name):
                screens = constructor(worlds)
                self.assertTrue(check_local_separation(screens, worlds))

    def test_every_antecedent_intersection_refines_Z(self) -> None:
        worlds = all_worlds()
        for name, constructor in ANTECEDENTS:
            with self.subTest(antecedent=name):
                screens = constructor(worlds)
                self.assertTrue(check_cross_u_coherence_equals_Z(screens, worlds))

    def test_partition_refines_identity_of_itself(self) -> None:
        worlds = all_worlds()
        z = true_z_partition(worlds)
        self.assertTrue(partition_refines(z, z))

    def test_singleton_partition_refines_any(self) -> None:
        worlds = all_worlds()
        singletons = tuple(frozenset({w}) for w in worlds)
        self.assertTrue(partition_refines(singletons, true_z_partition(worlds)))

    def test_quotient_partition_from_latent_matches_true_Z(self) -> None:
        worlds = all_worlds()
        p = quotient_partition(worlds, latent_z)
        self.assertTrue(partitions_equal(p, true_z_partition(worlds)))


if __name__ == "__main__":
    unittest.main()
