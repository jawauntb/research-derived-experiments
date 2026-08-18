from __future__ import annotations

import unittest
from fractions import Fraction

from experiments.silent_substitution.core import (
    COMPLIANCE_RECORD,
    EXPECTED_LIMIT_MASS,
    LIMIT_MASS_FLOOR,
    PRINCIPAL_VALUE,
    REGISTERED_ARMS,
    REWARD_ALIGNED,
    REWARD_MISALIGNED,
    TRAJECTORY,
    argmax_reward_mass,
    ecology_weights,
    evaluate_benchmark,
    expectation,
)


class SilentSubstitutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_for_any_recorded_verdict(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["SIL_RECORD_CONSTANT"])
        self.assertTrue(payload["gates"]["SIL_MISALIGNED_R_RISES"])
        self.assertTrue(payload["gates"]["SIL_MISALIGNED_U_FALLS"])
        self.assertTrue(payload["gates"]["SIL_LIMIT_CONCENTRATES"])
        self.assertTrue(payload["gates"]["SIL_ALIGNED_CONTROL"])
        self.assertTrue(payload["gates"]["SIL_EXACT_ARITHMETIC"])
        self.assertTrue(payload["gates"]["SIL_CLAIM_BOUNDARY"])
        self.assertIn(
            payload["ranking"]["verdict"],
            {"substitution_silent", "substitution_visible", "inconclusive"},
        )
        self.assertIn("Valence", payload["withheld"][0])

    def test_value_tables_are_registered_literals(self) -> None:
        self.assertEqual(PRINCIPAL_VALUE, tuple(Fraction(7 - x) for x in range(8)))
        self.assertEqual(REWARD_MISALIGNED, tuple(Fraction(x) for x in range(8)))
        self.assertEqual(REWARD_ALIGNED, PRINCIPAL_VALUE)
        self.assertEqual(TRAJECTORY, tuple(range(13)))
        self.assertEqual(len(REGISTERED_ARMS), 2)
        self.assertEqual(
            [spec["arm_id"] for spec in REGISTERED_ARMS],
            ["misaligned", "aligned"],
        )

    def test_uniform_start_has_expected_principal_7_2(self) -> None:
        for row in self.payload["arms"]:
            self.assertEqual(Fraction(row["uniform_principal"]), Fraction(7, 2))
            self.assertTrue(row["uniform_anchor_ok"])
        self.assertEqual(
            expectation(ecology_weights(REWARD_MISALIGNED, 0), PRINCIPAL_VALUE),
            Fraction(7, 2),
        )

    def test_record_is_the_constant_compliance_symbol(self) -> None:
        self.assertEqual(len(self.payload["trace"]), 26)
        for entry in self.payload["trace"]:
            self.assertEqual(entry["record"], COMPLIANCE_RECORD)
        for row in self.payload["arms"]:
            self.assertTrue(row["record_constant"])
            self.assertEqual(row["records"], [COMPLIANCE_RECORD] * 13)
        self.assertTrue(self.payload["ranking"]["record_constant_both_arms"])

    def test_misaligned_reward_rises_while_principal_falls(self) -> None:
        rows = {
            entry["t"]: entry
            for entry in self.payload["trace"]
            if entry["arm_id"] == "misaligned"
        }
        self.assertEqual(sorted(rows), list(range(13)))
        rewards = [Fraction(rows[t]["expected_reward"]) for t in range(13)]
        principals = [Fraction(rows[t]["expected_principal"]) for t in range(13)]
        for earlier, later in zip(rewards, rewards[1:]):
            self.assertGreater(later, earlier)
        for earlier, later in zip(principals, principals[1:]):
            self.assertLess(later, earlier)
        self.assertEqual(rewards[0], Fraction(7, 2))
        self.assertEqual(rewards[1], Fraction(14, 3))
        self.assertEqual(principals[1], Fraction(7, 3))
        self.assertEqual(rewards[12], Fraction(47999661097, 7083249971))
        self.assertEqual(principals[12], Fraction(1583088700, 7083249971))
        for t in range(13):
            self.assertEqual(
                Fraction(rows[t]["expected_principal"]),
                7 - Fraction(rows[t]["expected_reward"]),
            )

    def test_limit_mass_is_the_exact_registered_fraction(self) -> None:
        rows = {
            entry["t"]: entry
            for entry in self.payload["trace"]
            if entry["arm_id"] == "misaligned"
        }
        masses = [Fraction(rows[t]["argmax_reward_mass"]) for t in range(13)]
        for earlier, later in zip(masses, masses[1:]):
            self.assertGreater(later, earlier)
        self.assertEqual(masses[0], Fraction(1, 8))
        self.assertEqual(masses[12], EXPECTED_LIMIT_MASS)
        self.assertEqual(
            masses[12], Fraction(17179869184, 21249749913)
        )
        self.assertGreater(masses[12], LIMIT_MASS_FLOOR)
        self.assertEqual(
            self.payload["ranking"]["limit_mass"], "17179869184/21249749913"
        )
        self.assertEqual(
            argmax_reward_mass(
                ecology_weights(REWARD_MISALIGNED, 12), REWARD_MISALIGNED
            ),
            EXPECTED_LIMIT_MASS,
        )

    def test_aligned_control_rises_through_the_same_channel(self) -> None:
        rows = {
            entry["t"]: entry
            for entry in self.payload["trace"]
            if entry["arm_id"] == "aligned"
        }
        principals = [Fraction(rows[t]["expected_principal"]) for t in range(13)]
        for earlier, later in zip(principals, principals[1:]):
            self.assertGreater(later, earlier)
        self.assertEqual(principals[0], Fraction(7, 2))
        # Mirror symmetry x -> 7 - x: the aligned arm's E_t[U] equals the
        # misaligned arm's E_t[R_MIS].
        self.assertEqual(principals[12], Fraction(47999661097, 7083249971))
        for entry in rows.values():
            self.assertEqual(entry["expected_reward"], entry["expected_principal"])

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        if not ranking["record_constant_both_arms"]:
            self.assertEqual(ranking["verdict"], "substitution_visible")
        elif (
            ranking["misaligned_reward_rises"]
            and ranking["misaligned_principal_falls"]
            and ranking["aligned_principal_rises"]
        ):
            self.assertEqual(ranking["verdict"], "substitution_silent")
        else:
            self.assertEqual(ranking["verdict"], "inconclusive")

    def test_deterministic_replay(self) -> None:
        second = evaluate_benchmark()
        self.assertEqual(self.payload["ranking"], second["ranking"])
        self.assertEqual(self.payload["arms"], second["arms"])
        self.assertEqual(self.payload["trace"], second["trace"])
