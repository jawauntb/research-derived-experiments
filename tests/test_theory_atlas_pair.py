from __future__ import annotations

import unittest

from experiments.theory_atlas_pair.core import (
    CONTEXT_INDICES,
    N_BITS,
    TARGET,
    TARGET_SIZE,
    ChartFamily,
    all_triples,
    all_worlds,
    bad_family,
    chart_M,
    cocycle_discrepancy,
    cocycle_holds_all_triples,
    context_union,
    contexts,
    evaluate_benchmark,
    glue_attempt,
    good_family,
    identity_perm,
    observable_g,
    pairwise_overlap,
    phase_boundary_family,
    shift_perm,
    taxonomy_verdict,
    transition_support_report,
    triple_overlap,
)


class TheoryAtlasPairTest(unittest.TestCase):
    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))

    def test_permutation_composition_and_inverse_are_bijections(self) -> None:
        sigma = shift_perm(1)
        tau = shift_perm(2)
        composed = sigma.compose(tau)
        self.assertEqual(
            sorted(composed.table), list(range(TARGET_SIZE)),
            "composition must remain a permutation",
        )
        for a in TARGET:
            self.assertEqual(sigma.inverse().apply(sigma.apply(a)), a)
            self.assertEqual(sigma.apply(sigma.inverse().apply(a)), a)
        self.assertTrue(identity_perm().is_identity())
        self.assertEqual(identity_perm().rank(), 0)

    def test_context_geometry_matches_paper_setup(self) -> None:
        worlds = all_worlds()
        self.assertEqual(len(worlds), 2 ** N_BITS)
        ctxs = contexts(worlds)
        for i in CONTEXT_INDICES:
            self.assertEqual(len(ctxs[i]), 8)
        for i, j in ((1, 2), (1, 3), (2, 3)):
            self.assertEqual(len(pairwise_overlap(ctxs, i, j)), 4)
        self.assertEqual(len(triple_overlap(ctxs, 1, 2, 3)), 2)
        self.assertEqual(len(context_union(ctxs)), 14)

    def test_chart_maps_agree_with_observable_shift(self) -> None:
        worlds = all_worlds()
        for w in worlds:
            g = observable_g(w)
            self.assertEqual(chart_M(1, w), g)
            self.assertEqual(chart_M(2, w), (g + 1) % TARGET_SIZE)
            self.assertEqual(chart_M(3, w), (g + 2) % TARGET_SIZE)

    def test_good_family_satisfies_cocycle_on_every_triple(self) -> None:
        family = good_family()
        for triple in all_triples():
            disc = cocycle_discrepancy(family, *triple)
            self.assertTrue(disc.is_identity(),
                            f"good family discrepancy on {triple} must be identity, got {disc.table}")
        self.assertTrue(cocycle_holds_all_triples(family))

    def test_bad_family_violates_cocycle_with_missing_latent_signature(self) -> None:
        family = bad_family()
        self.assertFalse(cocycle_holds_all_triples(family))
        disc = cocycle_discrepancy(family, 1, 2, 3)
        # shift by 3 on Z/4 = shift by -1 mod 4; no fixed points.
        self.assertEqual(disc.rank(), TARGET_SIZE)
        support = transition_support_report(family)
        self.assertEqual(support["num_non_identity_edges"], support["num_edges"])
        self.assertEqual(taxonomy_verdict(family), "missing_latent")

    def test_phase_boundary_reference_is_localised(self) -> None:
        family = phase_boundary_family()
        self.assertFalse(cocycle_holds_all_triples(family))
        support = transition_support_report(family)
        # Exactly one non-identity edge (T_12), other two are identity.
        self.assertEqual(support["num_non_identity_edges"], 1)
        self.assertEqual(support["non_identity_edges"], ["T_12"])
        self.assertEqual(taxonomy_verdict(family), "phase_transition")

    def test_good_family_glues_to_global_theory_equal_to_g(self) -> None:
        worlds = all_worlds()
        glue = glue_attempt(good_family(), worlds)
        self.assertTrue(glue["consistent"])
        self.assertEqual(glue["inconsistent_worlds"], [])
        # The constructed M must equal g on every world in the union.
        ctxs = contexts(worlds)
        for w in context_union(ctxs):
            key = "".join(str(b) for b in w)
            self.assertEqual(glue["M"][key], observable_g(w))

    def test_bad_family_glue_attempt_is_inconsistent_on_overlaps(self) -> None:
        worlds = all_worlds()
        glue = glue_attempt(bad_family(), worlds)
        self.assertFalse(glue["consistent"])
        self.assertGreaterEqual(len(glue["inconsistent_worlds"]), 1)
        # Every inconsistent world lives in at least a pairwise overlap.
        ctxs = contexts(worlds)
        overlap_worlds: set[tuple[int, ...]] = set()
        for i, j in ((1, 2), (1, 3), (2, 3)):
            for w in pairwise_overlap(ctxs, i, j):
                overlap_worlds.add(w)
        for rec in glue["inconsistent_worlds"]:
            self.assertIn(tuple(rec["world"]), overlap_worlds)

    def test_taxonomy_verdict_matches_theorem_ta2_rule(self) -> None:
        # Constructive sweep: for every possible shift-triple in Z/4,
        # the verdict from taxonomy_verdict must match the cocycle-truth
        # + all-edges-non-identity rule of Theorem TA-2.
        for a in range(TARGET_SIZE):
            for b in range(TARGET_SIZE):
                for c in range(TARGET_SIZE):
                    family = ChartFamily(
                        name=f"trial_{a}{b}{c}",
                        chart_map=chart_M,
                        transitions={
                            (1, 2): shift_perm(a),
                            (2, 3): shift_perm(b),
                            (1, 3): shift_perm(c),
                        },
                    )
                    disc = cocycle_discrepancy(family, 1, 2, 3)
                    all_edges_non_id = all(
                        not sigma.is_identity()
                        for sigma in family.transitions.values()
                    )
                    verdict = taxonomy_verdict(family)
                    if disc.is_identity():
                        self.assertEqual(verdict, "glue")
                    elif all_edges_non_id:
                        self.assertEqual(verdict, "missing_latent")
                    else:
                        self.assertEqual(verdict, "phase_transition")


if __name__ == "__main__":
    unittest.main()
