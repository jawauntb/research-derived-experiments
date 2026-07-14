from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

from experiments.mathematical_claims.core import bounded_transport_loss, evaluate_all


ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "experiments" / "mathematical_claims"


class MathematicalClaimTests(unittest.TestCase):
    def test_every_assumption_has_a_satisfying_example_and_failure_case(self) -> None:
        results = evaluate_all()
        self.assertEqual(len(results), 7)
        self.assertTrue(all(result["example_satisfies_assumption"] for result in results))
        self.assertTrue(all(result["failure_case_detected"] for result in results))

    def test_matrix_and_committed_result_cover_the_same_theorems(self) -> None:
        matrix = json.loads((PACKAGE / "theorem_assumption_matrix.json").read_text())
        summary = json.loads((PACKAGE / "results" / "mathematical_claims_summary.json").read_text())
        expected = {item["theorem_id"] for item in matrix["assumptions"]}
        observed = {item["theorem_id"] for item in summary["results"]}
        self.assertEqual(observed, expected)
        self.assertEqual(summary["status"], "pass")

    def test_transport_bounds_require_one_delta_per_step(self) -> None:
        with self.assertRaisesRegex(ValueError, "one bound per transport step"):
            bounded_transport_loss([3.0, 2.0, 1.0], [1.0])

    def test_failure_cases_expose_each_registered_predicate_failure(self) -> None:
        by_id = {result["theorem_id"]: result for result in evaluate_all()}
        overlap = by_id["M201_BLOCK_DISJOINTNESS"]["failure_case"]
        self.assertLess(cast(float, overlap["union_size"]), cast(float, overlap["sum_sizes"]))
        unequal = by_id["M201_EQUAL_MASS"]["failure_case"]
        self.assertNotEqual(unequal["count_winners"], unequal["weighted_winners"])
        coverage = by_id["M201_COMPLETE_BLOCK_COVERAGE"]["failure_case"]
        self.assertLess(
            cast(float, coverage["actual_mass"]), cast(float, coverage["claimed_mass"])
        )
        self.assertIs(
            by_id["M201_COHERENT_OUTPUT_ACTION"]["failure_case"]["involution_ok"], False
        )
        self.assertIs(by_id["M201_BOUNDED_TRANSPORT_LOSS"]["failure_case"]["bounded"], False)
        self.assertIs(by_id["M201_GAUGE_SEPARATION"]["failure_case"]["gauge_fixed"], False)
        self.assertEqual(
            by_id["M201_NONZERO_COMMITMENT_EFFECT"]["failure_case"]["effect"], 0.0
        )

    def test_c2_satisfying_example_is_closed_on_the_declared_outputs(self) -> None:
        by_id = {result["theorem_id"]: result for result in evaluate_all()}
        example = by_id["M201_COHERENT_OUTPUT_ACTION"]["satisfying_example"]
        self.assertIs(example["closure_ok"], True)
        self.assertIs(example["coherent"], True)

    def test_runner_writes_the_exact_registered_results(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "summary.json"
            completed = subprocess.run(
                [sys.executable, str(PACKAGE / "experiment.py"), "--output", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                json.loads(completed.stdout),
                {"n_assumptions": 7, "status": "pass"},
            )
            self.assertEqual(json.loads(output.read_text())["results"], evaluate_all())


if __name__ == "__main__":
    unittest.main()
