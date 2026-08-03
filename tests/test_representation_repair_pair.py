from __future__ import annotations

import unittest

from experiments.representation_repair_pair.core import (
    PAIR_AFFINE_TO_PROJECTIVE,
    PAIR_GLOBAL_NORM_TO_LOCALIZED_MEASURE,
    PAIR_NON_COMPOSING_TO_INTERFACE,
    PAIR_POINT_TO_ENSEMBLE,
    PAIR_QUOTIENT_TO_RESTORED_FIBER,
    PAIR_SCALAR_TO_OPERATOR,
    PAIR_STATIC_TO_PATH_SPACE,
    PAIR_SYMMETRY_TO_GAUGE_FIX,
    PAIRS,
    build_composite_broken,
    build_composite_lifted,
    evaluate_benchmark,
    evaluate_composition,
    invariant_captured,
    invariant_missed,
    lift_is_minimal,
)


class RepresentationRepairPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_exactly_eight_canonical_pairs(self) -> None:
        self.assertEqual(len(PAIRS), 8)
        keys = {p.key for p in PAIRS}
        self.assertEqual(
            keys,
            {
                "scalar_to_operator",
                "global_norm_to_localized_measure",
                "quotient_to_restored_fiber",
                "static_to_path_space",
                "affine_to_projective",
                "point_to_ensemble",
                "non_composing_to_interface",
                "symmetry_to_gauge_fix",
            },
        )

    def test_every_pair_broken_misses_invariant(self) -> None:
        for pair in PAIRS:
            with self.subTest(pair=pair.key):
                self.assertTrue(
                    invariant_missed(pair.states, pair.broken, pair.invariant),
                    f"{pair.key}: broken representation did NOT miss the invariant",
                )

    def test_every_pair_lifted_captures_invariant(self) -> None:
        for pair in PAIRS:
            with self.subTest(pair=pair.key):
                self.assertTrue(
                    invariant_captured(pair.states, pair.lifted, pair.invariant),
                    f"{pair.key}: lifted representation did NOT capture the invariant",
                )

    def test_every_pair_lift_is_minimal(self) -> None:
        for pair in PAIRS:
            with self.subTest(pair=pair.key):
                ok, records = lift_is_minimal(
                    pair.states, pair.broken, pair.lifted, pair.invariant
                )
                self.assertTrue(
                    ok,
                    f"{pair.key}: some strict enlargement of broken (below lifted)"
                    f" still captures I; records={records}",
                )

    def test_scalar_to_operator_bloch_shape(self) -> None:
        pair = PAIR_SCALAR_TO_OPERATOR
        self.assertEqual(pair.broken.names, ("z",))
        self.assertEqual(pair.lifted.names, ("z", "x", "y"))
        # |+> and |-> share Pauli-Z but differ on X
        self.assertNotEqual(
            pair.invariant("|+>"), pair.invariant("|->"),
        )
        self.assertEqual(
            pair.broken.evaluate("|+>"), pair.broken.evaluate("|->"),
        )
        self.assertNotEqual(
            pair.lifted.evaluate("|+>"), pair.lifted.evaluate("|->"),
        )

    def test_global_norm_lift_needs_every_cell(self) -> None:
        pair = PAIR_GLOBAL_NORM_TO_LOCALIZED_MEASURE
        # Sanity: two states with same support size but different profile exist.
        broken_values = [pair.broken.evaluate(s) for s in pair.states]
        # They should not all be distinct (broken must miss I).
        self.assertLess(len(set(broken_values)), len(broken_values))
        # And every cell drop breaks capture:
        ok, _ = lift_is_minimal(
            pair.states, pair.broken, pair.lifted, pair.invariant
        )
        self.assertTrue(ok)

    def test_quotient_to_restored_fiber_lifts_z_to_full_tuple(self) -> None:
        pair = PAIR_QUOTIENT_TO_RESTORED_FIBER
        self.assertEqual(pair.broken.names, ("z",))
        self.assertEqual(pair.lifted.names, ("z", "x", "y"))
        self.assertEqual(len(pair.states), 8)

    def test_static_to_path_space_lifts_current_to_trajectory(self) -> None:
        pair = PAIR_STATIC_TO_PATH_SPACE
        self.assertEqual(pair.broken.names, ("current",))
        self.assertEqual(pair.lifted.names, ("current", "t0", "t1"))

    def test_affine_to_projective_adds_c(self) -> None:
        pair = PAIR_AFFINE_TO_PROJECTIVE
        self.assertEqual(pair.broken.names, ("a", "b"))
        self.assertEqual(pair.lifted.names, ("a", "b", "c"))

    def test_point_to_ensemble_lifts_mean_to_moments(self) -> None:
        pair = PAIR_POINT_TO_ENSEMBLE
        self.assertEqual(pair.broken.names, ("mean",))
        self.assertEqual(pair.lifted.names, ("mean", "var", "skew"))

    def test_non_composing_to_interface_lifts_pair_to_protocol(self) -> None:
        pair = PAIR_NON_COMPOSING_TO_INTERFACE
        self.assertEqual(pair.broken.names, ("m1", "m2"))
        self.assertEqual(pair.lifted.names, ("m1", "m2", "family", "version"))

    def test_symmetry_to_gauge_fix_lifts_a_to_gauge_invariants(self) -> None:
        pair = PAIR_SYMMETRY_TO_GAUGE_FIX
        self.assertEqual(pair.broken.names, ("a",))
        self.assertEqual(pair.lifted.names, ("a", "a_minus_b", "a_minus_c"))

    def test_composition_captures_both_invariants(self) -> None:
        result = evaluate_composition()
        self.assertTrue(result["lifted_captures_scalar_operator_invariant"])
        self.assertTrue(result["lifted_captures_static_path_invariant"])
        self.assertTrue(result["lifted_captures_composite_invariant"])
        self.assertTrue(result["composite_lift_is_minimal"])
        self.assertTrue(
            result["lifts_commute_capture_agrees_across_orderings"]
        )
        self.assertEqual(result["product_world_size"], 6 * 8)

    def test_composite_broken_misses_composite_invariant(self) -> None:
        result = evaluate_composition()
        self.assertTrue(result["broken_misses_composite_invariant"])
        self.assertTrue(result["broken_misses_scalar_operator_invariant"])
        self.assertTrue(result["broken_misses_static_path_invariant"])

    def test_composite_broken_and_lifted_have_expected_shape(self) -> None:
        broken = build_composite_broken()
        lifted = build_composite_lifted()
        self.assertEqual(broken.names, ("z_a", "current_b"))
        self.assertEqual(
            lifted.names,
            ("z_a", "x_a", "y_a", "current_b", "t0_b", "t1_b"),
        )
        # Every broken feature is a lifted feature.
        self.assertTrue(set(broken.names).issubset(set(lifted.names)))


if __name__ == "__main__":
    unittest.main()
