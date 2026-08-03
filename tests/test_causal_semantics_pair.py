from __future__ import annotations

import unittest

from experiments.causal_semantics_pair.core import (
    CONTEXTS,
    EXPECTED_COOCCURRENCE_PARTITION,
    EXPECTED_PSI_PARTITION,
    FUTURE_STATES,
    MESSAGES,
    NUMERIC_TOLERANCE,
    cooccurrence_equivalent,
    cooccurrence_partition,
    evaluate_benchmark,
    has_shared_cell,
    is_reflexive,
    is_reflexive_symmetric_transitive,
    is_symmetric,
    is_transitive,
    kappa,
    psi,
    psi_constant_within_each_class,
    psi_equivalent,
    psi_partition,
    psi_row_sums_to_one,
    refines,
)


class CausalSemanticsPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_world_has_expected_sizes(self) -> None:
        self.assertEqual(len(MESSAGES), 6)
        self.assertEqual(len(CONTEXTS), 4)
        self.assertEqual(len(FUTURE_STATES), 4)

    def test_every_psi_row_is_a_probability_distribution(self) -> None:
        for m in MESSAGES:
            for c in CONTEXTS:
                row = psi(m, c)
                self.assertTrue(psi_row_sums_to_one(row), msg=(m, c, row))
                self.assertEqual(len(row), len(FUTURE_STATES))

    def test_psi_equivalent_within_each_expected_class(self) -> None:
        for cell in EXPECTED_PSI_PARTITION:
            cell_members = list(cell)
            for i, a in enumerate(cell_members):
                for b in cell_members[i:]:
                    self.assertTrue(psi_equivalent(a, b), msg=(a, b))

    def test_psi_not_equivalent_across_expected_classes(self) -> None:
        # Pick a representative from every expected class and verify all
        # pairwise inequivalences.
        representatives = ["m0", "m2", "m4", "m5"]
        for i, a in enumerate(representatives):
            for b in representatives[i + 1 :]:
                self.assertFalse(psi_equivalent(a, b), msg=(a, b))

    def test_cs1_psi_equivalence_is_reflexive_symmetric_transitive(self) -> None:
        self.assertTrue(is_reflexive(MESSAGES, psi_equivalent))
        self.assertTrue(is_symmetric(MESSAGES, psi_equivalent))
        self.assertTrue(is_transitive(MESSAGES, psi_equivalent))
        self.assertTrue(is_reflexive_symmetric_transitive(MESSAGES, psi_equivalent))

    def test_cs2_psi_quotient_matches_expected_four_classes(self) -> None:
        self.assertEqual(psi_partition(MESSAGES), EXPECTED_PSI_PARTITION)

    def test_cs2_psi_quotient_is_common_sufficient(self) -> None:
        self.assertTrue(
            psi_constant_within_each_class(
                EXPECTED_PSI_PARTITION, CONTEXTS, tolerance=NUMERIC_TOLERANCE
            )
        )

    def test_cooccurrence_partition_matches_expected_two_classes(self) -> None:
        self.assertEqual(
            cooccurrence_partition(MESSAGES), EXPECTED_COOCCURRENCE_PARTITION
        )

    def test_cooccurrence_partition_differs_from_psi_quotient(self) -> None:
        p_psi = psi_partition(MESSAGES)
        p_cooc = cooccurrence_partition(MESSAGES)
        self.assertNotEqual(p_psi, p_cooc)

    def test_neither_partition_refines_the_other(self) -> None:
        p_psi = psi_partition(MESSAGES)
        p_cooc = cooccurrence_partition(MESSAGES)
        self.assertFalse(refines(p_psi, p_cooc))
        self.assertFalse(refines(p_cooc, p_psi))

    def test_partitions_share_no_cell(self) -> None:
        p_psi = psi_partition(MESSAGES)
        p_cooc = cooccurrence_partition(MESSAGES)
        self.assertFalse(has_shared_cell(p_psi, p_cooc))

    def test_class_distributions_pairwise_distinct_at_c0(self) -> None:
        # Class representatives at c0 must be pairwise distinct probability
        # vectors: exhibits the four Psi-classes as genuinely different.
        classes_at_c0 = {
            "A": psi("m0", "c0"),
            "B": psi("m2", "c0"),
            "C": psi("m4", "c0"),
            "D": psi("m5", "c0"),
        }
        seen: list[tuple[float, ...]] = []
        for label, row in classes_at_c0.items():
            self.assertNotIn(tuple(row), seen, msg=label)
            seen.append(tuple(row))

    def test_cooccurrence_signatures_group_by_parity_of_index(self) -> None:
        even_signature = kappa("m0")
        odd_signature = kappa("m1")
        self.assertNotEqual(even_signature, odd_signature)
        for idx in (0, 2, 4):
            self.assertEqual(kappa(f"m{idx}"), even_signature)
        for idx in (1, 3, 5):
            self.assertEqual(kappa(f"m{idx}"), odd_signature)

    def test_cooccurrence_equivalent_matches_signature_equality(self) -> None:
        for m1 in MESSAGES:
            for m2 in MESSAGES:
                self.assertEqual(
                    cooccurrence_equivalent(m1, m2),
                    kappa(m1) == kappa(m2),
                )

    def test_diagnostic_flags_in_summary_match_partitions(self) -> None:
        payload = evaluate_benchmark()
        self.assertFalse(payload["psi_refines_cooccurrence"])
        self.assertFalse(payload["cooccurrence_refines_psi"])
        self.assertEqual(payload["shared_cells_between_partitions"], [])
        self.assertTrue(payload["all_rows_are_probability_distributions"])


if __name__ == "__main__":
    unittest.main()
