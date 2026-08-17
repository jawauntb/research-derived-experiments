from __future__ import annotations

import unittest

from experiments.delete_repair_connection.core import (
    AFFINE_A,
    AFFINE_B,
    IDENTITY,
    KIRCHHOFF_CURVED,
    KIRCHHOFF_FLAT,
    compose,
    evaluate_benchmark,
    group_elements,
    group_laws_hold,
    kirchhoff_prediction,
    order_matters,
    path_map,
    section_from,
)


class DeleteRepairConnectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = evaluate_benchmark()

    def test_instrument_stays_valid_even_if_cell3_is_idle(self) -> None:
        payload = self.payload
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(payload["gates"]["CONN_GROUP_LAWS"])
        self.assertTrue(payload["gates"]["CONN_KIRCHHOFF_CONTROL"])
        self.assertTrue(payload["gates"]["CONN_ENUMERATION"])
        self.assertIn(payload["ranking"]["verdict"], {"cell3_holds", "cell3_idle"})
        self.assertIn("Not integer Kirchhoff", payload["process_disclosure"])
        self.assertIn("Lorentz geometry", payload["withheld"][0])

    def test_group_is_six_elements_and_a_group(self) -> None:
        self.assertEqual(len(group_elements()), 6)
        self.assertTrue(group_laws_hold())
        self.assertTrue(order_matters())
        self.assertEqual(compose((2, 0), (1, 1)), (2, 2))
        self.assertEqual(compose((1, 1), (2, 0)), (2, 1))

    def test_additive_cycles_remain_kirchhoff(self) -> None:
        self.assertEqual(path_map(KIRCHHOFF_FLAT), IDENTITY)
        self.assertEqual(path_map(KIRCHHOFF_FLAT), kirchhoff_prediction(KIRCHHOFF_FLAT))
        self.assertEqual(path_map(KIRCHHOFF_CURVED), (1, 1))
        self.assertEqual(path_map(KIRCHHOFF_CURVED), kirchhoff_prediction(KIRCHHOFF_CURVED))

    def test_affine_cycles_escape_kirchhoff(self) -> None:
        self.assertEqual(path_map(AFFINE_A), (2, 0))
        self.assertEqual(kirchhoff_prediction(AFFINE_A), IDENTITY)
        self.assertNotEqual(path_map(AFFINE_A), kirchhoff_prediction(AFFINE_A))
        self.assertEqual(path_map(AFFINE_B), IDENTITY)
        self.assertEqual(kirchhoff_prediction(AFFINE_B), (1, 2))
        self.assertNotEqual(path_map(AFFINE_B), kirchhoff_prediction(AFFINE_B))

    def test_ranking_follows_the_preregistered_rule(self) -> None:
        ranking = self.payload["ranking"]
        expected_hold = (
            ranking["kirchhoff_control_holds"]
            and ranking["affine_escapes_kirchhoff"]
            and ranking["order_matters"]
            and ranking["raw_comparison_fails"]
            and ranking["transport_comparison_works"]
        )
        if expected_hold:
            self.assertEqual(ranking["verdict"], "cell3_holds")
        else:
            self.assertEqual(ranking["verdict"], "cell3_idle")
        self.assertEqual(section_from(AFFINE_B, 0)[0], 0)

    def test_deterministic_replay(self) -> None:
        first = self.payload
        second = evaluate_benchmark()
        self.assertEqual(first["ranking"], second["ranking"])
        self.assertEqual(first["cycles"], second["cycles"])
