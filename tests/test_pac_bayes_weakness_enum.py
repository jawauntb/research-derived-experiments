from __future__ import annotations

import json
import unittest
from fractions import Fraction
from pathlib import Path

from experiments.pac_bayes_weakness_enum.core import (
    binary_kl,
    fixed_action_cyclic_count,
    invert_kl,
    iter_functions,
    mixture_mass,
    mixture_pi,
    weakness_cyclic,
    weakness_dihedral,
    weakness_symmetric,
    wave11_toy_masses,
)
from experiments.pac_bayes_weakness_enum.families import C7, D7, FAMILIES


ROOT = Path(__file__).resolve().parent.parent
SUMMARY = (
    ROOT
    / "experiments"
    / "pac_bayes_weakness_enum"
    / "results"
    / "pac_bayes_weakness_enum_summary.json"
)


class PacBayesWeaknessEnumTest(unittest.TestCase):
    def test_wave11_toy_masses_are_one_quarter_and_three_quarters(self) -> None:
        shortcut, invariant = wave11_toy_masses()
        self.assertEqual(shortcut, Fraction(1, 4))
        self.assertEqual(invariant, Fraction(3, 4))

    def test_mixture_masses_sum_to_one_on_n3_cyclic(self) -> None:
        n = 3
        cards = [0] * 4
        for f in iter_functions(n):
            cards_w = weakness_cyclic(f, n)
            for k in range(1, cards_w + 1):
                cards[k] += 1
        # Rebuild H≥k from W histogram.
        hist = [0] * 4
        for f in iter_functions(n):
            hist[weakness_cyclic(f, n)] += 1
        cards = [0] * 4
        running = 0
        for k in range(3, 0, -1):
            running += hist[k]
            cards[k] = running
        pi = mixture_pi(cards, "uniform")
        total = Fraction(0)
        for f in iter_functions(n):
            total += mixture_mass(weakness_cyclic(f, n), cards, pi)
        self.assertEqual(total, 1)
        self.assertEqual(sum(hist), 27)

    def test_fixed_action_count_on_c3_is_three(self) -> None:
        self.assertEqual(fixed_action_cyclic_count(3), 3)

    def test_truth_shifts_are_fully_cyclic_compatible(self) -> None:
        cyclic = next(spec for spec in FAMILIES if spec["family_id"] == "cyclic")
        self.assertEqual(weakness_cyclic(cyclic["truth"], 7), 7)
        dihedral = next(spec for spec in FAMILIES if spec["family_id"] == "dihedral")
        self.assertEqual(weakness_dihedral(dihedral["truth"], 7), 14)

    def test_symmetric_weakness_is_n_factorial_on_bijections(self) -> None:
        self.assertEqual(weakness_symmetric((1, 2, 3, 4, 5, 0)), 720)
        self.assertEqual(weakness_symmetric((0, 0, 0, 0, 0, 0)), 720)

    def test_kl_inversion_recovers_a_known_bound(self) -> None:
        rhs = binary_kl(0.0, 0.25)
        self.assertAlmostEqual(invert_kl(0.0, rhs), 0.25, places=9)

    def test_frozen_groups_contain_identity(self) -> None:
        self.assertEqual(C7[0], tuple(range(7)))
        self.assertEqual(D7[0], tuple(range(7)))
        for spec in FAMILIES:
            if spec["aligned_is_full_symmetric"]:
                continue
            self.assertEqual(spec["groups"]["aligned"][0], tuple(range(spec["n"])))

    def test_committed_summary_replays_registered_gates(self) -> None:
        self.assertTrue(SUMMARY.is_file(), "run experiment.py before asserting the receipt")
        payload = json.loads(SUMMARY.read_text())
        self.assertEqual(payload["experiment_id"], "pac_bayes_weakness_enum")
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["PB_ENUM_CARDINALITY"])
        self.assertTrue(payload["gates"]["PB_MASS_FORMULA"])
        self.assertTrue(payload["gates"]["PB_FIXED_ACTION"])
        self.assertTrue(payload["gates"]["PB_NEURAL_WITHHELD"])
        self.assertTrue(payload["gates"]["PB_CLAIM_BOUNDARY"])
        self.assertEqual(
            payload["ranking"]["verdict"],
            "finite_iid_holds_ood_or_weight_killed",
        )
        self.assertEqual(payload["ranking"]["ood_kill_families"], ["parity"])
        self.assertTrue(payload["gates"]["PB_IID_NONVACUOUS"])
        self.assertTrue(payload["gates"]["PB_WEIGHT_STABLE"])
        self.assertTrue(payload["gates"]["PB_HYPERPRIOR_ADDS_INFO"])
        self.assertFalse(payload["gates"]["PB_OOD_WRONG_GROUP"])
        self.assertFalse(payload["kills"]["class_count_contradiction"])
        self.assertFalse(payload["kills"]["iid_vacuous"])
        self.assertTrue(payload["kills"]["wrong_group_tight_ood_fail"])
        by_id = {row["family_id"]: row for row in payload["families"]}
        self.assertEqual(by_id["cyclic"]["ambient_card"], 7**7)
        self.assertEqual(by_id["dihedral"]["ambient_card"], 7**7)
        self.assertEqual(by_id["parity"]["ambient_card"], 6**6)
        self.assertEqual(by_id["color"]["ambient_card"], 6**6)
        self.assertEqual(by_id["cyclic"]["fixed_action_eq_count"], 7)
        self.assertEqual(by_id["cyclic"]["level_cards"]["aligned"]["7"], 49)
        self.assertEqual(by_id["parity"]["probes"]["truth"]["weakness"]["aligned"], 2)
        self.assertEqual(by_id["parity"]["probes"]["shortcut"]["weakness"]["aligned"], 2)
        self.assertEqual(payload["kills"]["neural_untransported"], True)
        self.assertIn("Langford–Seeger–Maurer", payload["withheld"][0])


if __name__ == "__main__":
    unittest.main()
