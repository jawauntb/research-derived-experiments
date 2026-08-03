from __future__ import annotations

import unittest

from experiments.alignment_governance_pair.core import (
    ACTIONS,
    BETA,
    NUMERIC_TOLERANCE,
    T_HORIZONS,
    UNVIABLE_STATES,
    V_STATES,
    Z_STATES,
    action_kernel,
    evaluate_benchmark,
    submatrix_on,
    survival_probability,
    theorem_lower_bound,
    uniform_policy_kernel,
)


class AlignmentGovernancePairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_kernel_rows_sum_to_one(self) -> None:
        matrix = uniform_policy_kernel()
        for row in matrix:
            self.assertAlmostEqual(sum(row), 1.0, places=12)

    def test_state_three_is_absorbing(self) -> None:
        matrix = uniform_policy_kernel()
        three_idx = Z_STATES.index(3)
        self.assertAlmostEqual(matrix[three_idx][three_idx], 1.0, places=12)
        for j, z in enumerate(Z_STATES):
            if z != 3:
                self.assertAlmostEqual(matrix[three_idx][j], 0.0, places=12)

    def test_p_v_row_sums_equal_one_minus_beta(self) -> None:
        matrix = uniform_policy_kernel()
        sub = submatrix_on(matrix, V_STATES)
        for row in sub:
            self.assertAlmostEqual(sum(row), 1.0 - BETA, places=12)

    def test_ag1_bound_holds_and_is_tight_at_every_T(self) -> None:
        # Every row of P_V sums to 1-beta, so survival = (1-beta)^T exactly at every T.
        matrix = uniform_policy_kernel()
        for t in T_HORIZONS:
            exact = survival_probability(matrix, V_STATES, t)
            bound = theorem_lower_bound(t)
            self.assertGreaterEqual(exact + NUMERIC_TOLERANCE, bound)
            self.assertAlmostEqual(exact, bound, places=10)

    def test_ag2_extending_V_to_Z_makes_survival_one(self) -> None:
        matrix = uniform_policy_kernel()
        for t in T_HORIZONS:
            exact = survival_probability(matrix, Z_STATES, t)
            self.assertAlmostEqual(exact, 1.0, places=12)

    def test_survival_monotone_decreasing_in_T(self) -> None:
        matrix = uniform_policy_kernel()
        prev = float("inf")
        for t in T_HORIZONS:
            exact = survival_probability(matrix, V_STATES, t)
            self.assertLessEqual(exact, prev + NUMERIC_TOLERANCE)
            prev = exact

    def test_start_state_symmetry(self) -> None:
        # By the construction, survival is the same from any V-state at every T
        # (every row of P_V^T has the same row-sum by row-sum induction).
        matrix = uniform_policy_kernel()
        for t in T_HORIZONS:
            values = [survival_probability(matrix, V_STATES, t, start_state=z) for z in V_STATES]
            for value in values[1:]:
                self.assertAlmostEqual(value, values[0], places=10)

    def test_action_kernel_absorbing_at_state_three(self) -> None:
        for action in ACTIONS:
            row = action_kernel(3, action)
            self.assertEqual(row, {3: 1.0})

    def test_unviable_states_disjoint_from_V(self) -> None:
        self.assertEqual(set(V_STATES) & set(UNVIABLE_STATES), set())
        self.assertEqual(set(V_STATES) | set(UNVIABLE_STATES), set(Z_STATES))


if __name__ == "__main__":
    unittest.main()
