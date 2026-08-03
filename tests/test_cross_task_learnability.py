from __future__ import annotations

import math
import unittest

from experiments.cross_task_learnability.core import (
    EPS,
    M,
    N_BITS,
    all_worlds,
    evaluate_benchmark,
    exact_recovery_probability,
    fibre_masses,
    latent_z,
    theorem_bound,
)


class CrossTaskLearnabilityTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_theorem_bound_matches_formula(self) -> None:
        # N >= c * M * ln(M / eps), rounded up.
        self.assertEqual(theorem_bound(m=4, c=1.0, eps=0.05), math.ceil(4 * math.log(80)))
        self.assertEqual(theorem_bound(m=4, c=2.0, eps=0.05), math.ceil(8 * math.log(80)))

    def test_recovery_is_zero_below_M(self) -> None:
        masses = (0.25, 0.25, 0.25, 0.25)
        for n in range(M):
            self.assertEqual(exact_recovery_probability(masses, n), 0.0)

    def test_recovery_is_monotone_and_reaches_one(self) -> None:
        masses = (0.25, 0.25, 0.25, 0.25)
        prev = 0.0
        for n in range(0, 60):
            current = exact_recovery_probability(masses, n)
            self.assertGreaterEqual(current + 1e-12, prev)
            prev = current
        self.assertGreater(exact_recovery_probability(masses, 60), 1 - 1e-6)

    def test_uniform_fibre_masses_are_balanced(self) -> None:
        worlds = all_worlds(N_BITS)
        entries = fibre_masses(worlds, "uniform")
        masses = [mass for _z, mass in entries]
        for m in masses:
            self.assertAlmostEqual(m, 0.25, places=12)
        self.assertAlmostEqual(sum(masses), 1.0, places=12)

    def test_skewed_fibre_masses_have_p_min_one_eighth(self) -> None:
        worlds = all_worlds(N_BITS)
        entries = fibre_masses(worlds, "skewed")
        masses = [mass for _z, mass in entries]
        self.assertAlmostEqual(min(masses), 0.125, places=12)
        self.assertAlmostEqual(sum(masses), 1.0, places=12)

    def test_shared_task_family_separates_latent_Z(self) -> None:
        # Sanity: the shared family from instrument 4 injects Z into (Y1, Y2, Y3).
        seen: set[tuple[int, int, int]] = set()
        for x in all_worlds(N_BITS):
            profile = (
                x[0] ^ x[1],
                x[2] ^ x[3],
                x[0] ^ x[1] ^ x[2] ^ x[3],
            )
            seen.add(profile)
        # Group by latent Z: each Z-class must have exactly one profile.
        z_to_profile: dict[tuple[int, int], set[tuple[int, int, int]]] = {}
        for x in all_worlds(N_BITS):
            profile = (
                x[0] ^ x[1],
                x[2] ^ x[3],
                x[0] ^ x[1] ^ x[2] ^ x[3],
            )
            z_to_profile.setdefault(latent_z(x), set()).add(profile)
        for profiles in z_to_profile.values():
            self.assertEqual(len(profiles), 1)
        # Distinct Z values yield distinct profiles.
        collected = {next(iter(v)) for v in z_to_profile.values()}
        self.assertEqual(len(collected), len(z_to_profile))

    def test_exact_recovery_at_theorem_bound_meets_target(self) -> None:
        # Uniform: at N = ceil(c M ln(M/eps)) with c=1 the recovery >= 1 - eps.
        worlds = all_worlds(N_BITS)
        entries = fibre_masses(worlds, "uniform")
        masses = tuple(mass for _z, mass in entries)
        n = theorem_bound(m=M, c=1.0, eps=EPS)
        self.assertGreaterEqual(exact_recovery_probability(masses, n), 1.0 - EPS)
        # Skewed with c=2 same story at N = ceil(2 M ln(M/eps)).
        entries_skewed = fibre_masses(worlds, "skewed")
        masses_skewed = tuple(mass for _z, mass in entries_skewed)
        n2 = theorem_bound(m=M, c=2.0, eps=EPS)
        self.assertGreaterEqual(
            exact_recovery_probability(masses_skewed, n2), 1.0 - EPS
        )


if __name__ == "__main__":
    unittest.main()
