from __future__ import annotations

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from experiments.eml_fiber_spectrum.core import (
    CROSS_SIZE_WITNESSES,
    GRID_COLLISION_DISCLOSURE,
    MAX_INTERNAL,
    OPTIONAL_GATES,
    REQUIRED_GATES,
    SIZE_NOT_DENOTATION_LEFT,
    SIZE_NOT_DENOTATION_RIGHT,
    TEST_GRID,
    US4_PRIME_WITHHELD,
    WITNESS_POINT,
    catalan,
    eml,
    enumerate_trees,
    eval_closed,
    eval_probe,
    evaluate_benchmark,
    parse_eml,
)


PACKAGE = Path(__file__).resolve().parent.parent / "experiments" / "eml_fiber_spectrum"


class EmlFiberSpectrumTest(unittest.TestCase):
    def test_benchmark_passes_required_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(set(payload["gates"]), set(REQUIRED_GATES))
        self.assertTrue(all(payload["gates"].values()))
        self.assertEqual(set(payload["optional_gates"]), set(OPTIONAL_GATES))

    def test_enumeration_matches_catalan_through_registered_bound(self) -> None:
        by_size = enumerate_trees(MAX_INTERNAL)
        for n_internal in range(MAX_INTERNAL + 1):
            self.assertEqual(len(by_size[n_internal]), catalan(n_internal))
        self.assertEqual(catalan(0), 1)
        self.assertEqual(catalan(5), 42)
        self.assertEqual(catalan(6), 132)
        self.assertEqual(sum(len(trees) for trees in by_size.values()), 197)

    def test_closed_forms(self) -> None:
        self.assertEqual(eval_closed(parse_eml("1")), 1.0)
        self.assertAlmostEqual(eval_closed(parse_eml("eml(1,1)")), math.e, places=15)
        self.assertAlmostEqual(
            eval_closed(parse_eml("eml(1,eml(1,1))")), math.e - 1.0, places=15
        )
        self.assertAlmostEqual(
            eval_closed(parse_eml("eml(eml(1,1),1)")), math.exp(math.e), places=12
        )
        self.assertEqual(eval_closed(parse_eml("eml(1,eml(eml(1,1),1))")), 0.0)
        self.assertEqual(eval_closed(parse_eml("eml(1,eml(eml(1,eml(1,1)),1))")), 1.0)

    def test_operator_is_exp_minus_log_on_the_grid(self) -> None:
        for x_val, y_val in TEST_GRID:
            self.assertGreater(y_val, 0.0)
            self.assertEqual(eml(x_val, y_val), math.exp(x_val) - math.log(y_val))

    def test_eml_rejects_nonpositive_y(self) -> None:
        with self.assertRaises(ValueError):
            eml(1.0, 0.0)
        with self.assertRaises(ValueError):
            eml(1.0, -1.0)

    def test_size_two_trees_disagree_at_the_registered_point(self) -> None:
        left = parse_eml(SIZE_NOT_DENOTATION_LEFT)
        right = parse_eml(SIZE_NOT_DENOTATION_RIGHT)
        self.assertEqual(left.n_internal, 2)
        self.assertEqual(right.n_internal, 2)
        left_val = eval_closed(left)
        right_val = eval_closed(right)
        self.assertIsNotNone(left_val)
        self.assertIsNotNone(right_val)
        self.assertNotEqual(left_val, right_val)
        self.assertEqual(eval_probe(left, *WITNESS_POINT), left_val)
        self.assertEqual(eval_probe(right, *WITNESS_POINT), right_val)
        self.assertAlmostEqual(left_val, math.e - 1.0, places=15)
        self.assertAlmostEqual(right_val, math.exp(math.e), places=12)

    def test_probe_at_one_one_matches_closed(self) -> None:
        for trees in enumerate_trees(4).values():
            for tree in trees:
                self.assertEqual(eval_probe(tree, 1.0, 1.0), eval_closed(tree))

    def test_cross_size_identities_are_exact(self) -> None:
        for left_pretty, right_pretty, expected in CROSS_SIZE_WITNESSES:
            left = parse_eml(left_pretty)
            right = parse_eml(right_pretty)
            self.assertNotEqual(left.n_internal, right.n_internal)
            self.assertAlmostEqual(eval_closed(left), expected, places=12)
            self.assertAlmostEqual(eval_closed(right), expected, places=12)

    def test_grid_collision_and_us4_prime_are_disclosed(self) -> None:
        payload = evaluate_benchmark()
        self.assertTrue(payload["grid_collision_disclosed"])
        self.assertEqual(payload["grid_collision_disclosure"], GRID_COLLISION_DISCLOSURE)
        self.assertIn("not identity of functions", payload["grid_collision_disclosure"])
        self.assertIn("US-4_prime", payload["untested"])
        self.assertEqual(payload["untested"]["US-4_prime"], US4_PRIME_WITHHELD)
        self.assertTrue(payload["gates"]["EFS_GRID_COLLISION_DISCLOSED"])
        self.assertTrue(payload["gates"]["EFS_US4_PRIME_WITHHELD"])
        self.assertEqual(payload["claim_tier_spectrum"], "computational")

    def test_optional_cross_size_gate_is_pass_or_withheld(self) -> None:
        payload = evaluate_benchmark()
        optional = payload["optional_gates"]["EFS_CROSS_SIZE_COLLISION"]
        self.assertIn(optional["status"], {"pass", "withheld"})
        if optional["status"] == "pass":
            self.assertTrue(optional["observed"])
            self.assertGreater(optional["n_exact_witnesses"], 0)
        else:
            self.assertFalse(optional["observed"])

    def test_spectrum_counts_are_consistent(self) -> None:
        payload = evaluate_benchmark()
        closed = payload["closed_spectrum"]
        self.assertEqual(payload["n_trees"], 197)
        self.assertEqual(closed["n_finite"] + closed["n_undefined"], 197)
        self.assertGreater(closed["n_numerical_fibers"], 1)
        self.assertGreaterEqual(closed["max_fiber_size"], 1)
        self.assertFalse(closed["size_is_denotation_invariant"])
        self.assertEqual(
            payload["tree_counts_by_size"],
            {str(n): catalan(n) for n in range(MAX_INTERNAL + 1)},
        )

    def test_suspect_collisions_are_not_the_cross_size_witness(self) -> None:
        payload = evaluate_benchmark()
        exact_values = {0.0, 1.0, math.e, math.e - 1.0, math.exp(math.e)}
        suspects = payload["closed_spectrum"]["suspect_cross_size_fibers"]
        self.assertGreaterEqual(len(suspects), 1)
        for row in suspects:
            mean_value = float(row["mean_value"])
            self.assertFalse(
                any(math.isclose(mean_value, exact, rel_tol=1e-12, abs_tol=1e-15) for exact in exact_values)
            )
        witnesses = payload["cross_size_witnesses"]
        self.assertTrue(all(row["ok"] for row in witnesses))

    def test_pretty_roundtrip(self) -> None:
        pretty = "eml(1,eml(eml(1,eml(1,1)),1))"
        tree = parse_eml(pretty)
        self.assertEqual(tree.pretty(), pretty)
        self.assertEqual(tree.n_internal, 4)

    def test_runner_writes_the_registered_summary(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "summary.json"
            completed = subprocess.run(
                [sys.executable, str(PACKAGE / "experiment.py"), "--output", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            printed = json.loads(completed.stdout)
            written = json.loads(output.read_text())
            live = evaluate_benchmark()
            self.assertEqual(printed["status"], "pass")
            self.assertEqual(written["gates"], live["gates"])
            self.assertEqual(written["n_trees"], live["n_trees"])
            self.assertEqual(
                written["closed_spectrum"]["n_numerical_fibers"],
                live["closed_spectrum"]["n_numerical_fibers"],
            )


if __name__ == "__main__":
    unittest.main()
