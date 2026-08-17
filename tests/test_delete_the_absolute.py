from __future__ import annotations

import json
import unittest
from itertools import product

from experiments.delete_the_absolute.core import (
    ALL_MODEL_IDS,
    HOLONOMY_P0,
    HOLONOMY_Q0,
    MODEL_FNS,
    MODEL_GROUPS,
    N,
    NONZERO_SUM_CYCLE,
    TASK_FNS,
    TASK_IDS,
    ZERO_SUM_CYCLE,
    all_perms,
    all_worlds,
    apply_perm,
    cycle_closes,
    evaluate_benchmark,
    fiber_count,
    fibres_of,
    find_sequence_noncommute_witness,
    group_id,
    group_intersection,
    group_perm,
    group_rot,
    group_stab0,
    identity_perm,
    inclusion_matrix,
    is_exact_repair,
    is_representable,
    is_subset_group,
    mixed_fibers,
    orbit,
    orbit_canonical,
    path_a_pair,
    path_a_seq,
    path_b_pair,
    path_b_seq,
    popcount,
    potentials_differ_by_constant,
    prefix_potentials,
    q_id,
    q_perm,
    q_rot,
    q_stab0,
    repair_splits_disagreement,
    representability_matrix,
    rotate_left_perm,
    sum_int,
    symmetry_of,
    y_bag,
    y_constant_on_fibers,
    y_first_bit,
    y_identity,
    y_necklace,
)


class DeleteTheAbsoluteTest(unittest.TestCase):
    def test_world_is_the_sixteen_bit_strings(self) -> None:
        worlds = all_worlds()
        self.assertEqual(N, 4)
        self.assertEqual(len(worlds), 16)
        self.assertEqual(len(set(worlds)), 16)
        self.assertEqual(worlds[0], (0, 0, 0, 0))
        self.assertEqual(worlds[-1], (1, 1, 1, 1))
        self.assertEqual(set(worlds), set(product((0, 1), repeat=4)))

    def test_group_sizes(self) -> None:
        self.assertEqual(len(group_id()), 1)
        self.assertEqual(len(group_rot()), 4)
        self.assertEqual(len(group_perm()), 24)
        self.assertEqual(len(group_stab0()), 6)
        self.assertEqual(group_id(), (identity_perm(),))
        self.assertEqual(set(group_rot()), set(rotate_left_perm(k) for k in range(4)))
        self.assertTrue(is_subset_group(group_id(), group_rot()))
        self.assertTrue(is_subset_group(group_rot(), group_perm()))
        self.assertTrue(is_subset_group(group_stab0(), group_perm()))
        self.assertFalse(is_subset_group(group_rot(), group_stab0()))
        self.assertFalse(is_subset_group(group_perm(), group_stab0()))

    def test_rotate_left_action(self) -> None:
        x = (1, 0, 0, 0)
        self.assertEqual(apply_perm(rotate_left_perm(1), x), (0, 0, 0, 1))
        self.assertEqual(apply_perm(rotate_left_perm(2), x), (0, 0, 1, 0))
        self.assertEqual(apply_perm(rotate_left_perm(4), x), x)

    def test_orbit_canonical_maps(self) -> None:
        x = (1, 0, 0, 0)
        self.assertEqual(q_id(x), x)
        self.assertEqual(q_rot(x), (0, 0, 0, 1))
        self.assertEqual(q_perm(x), (0, 0, 0, 1))
        self.assertEqual(q_stab0(x), (1, 0, 0, 0))
        self.assertEqual(q_stab0((0, 1, 0, 1)), (0, 0, 1, 1))
        for world in all_worlds():
            self.assertEqual(q_id(world), orbit_canonical(world, group_id()))
            self.assertEqual(q_rot(world), orbit_canonical(world, group_rot()))
            self.assertEqual(q_perm(world), orbit_canonical(world, group_perm()))
            self.assertEqual(q_stab0(world), orbit_canonical(world, group_stab0()))

    def test_q_perm_fibres_equal_popcount_fibres(self) -> None:
        worlds = all_worlds()
        perm_cells = {frozenset(cell) for cell in fibres_of(worlds, q_perm).values()}
        pop_cells = {frozenset(cell) for cell in fibres_of(worlds, popcount).values()}
        self.assertEqual(perm_cells, pop_cells)
        self.assertEqual(fiber_count(worlds, q_perm), 5)
        self.assertEqual(fiber_count(worlds, q_id), 16)
        self.assertEqual(fiber_count(worlds, q_rot), 6)
        self.assertEqual(fiber_count(worlds, q_stab0), 8)

    def test_task_symmetries_by_enumeration(self) -> None:
        worlds = all_worlds()
        g_bag = symmetry_of(y_bag, worlds)
        g_necklace = symmetry_of(y_necklace, worlds)
        g_first = symmetry_of(y_first_bit, worlds)
        g_id_task = symmetry_of(y_identity, worlds)
        self.assertEqual(set(g_bag), set(all_perms()))
        self.assertTrue(is_subset_group(group_rot(), g_necklace))
        self.assertFalse(is_subset_group(group_perm(), g_necklace))
        self.assertEqual(set(g_first), set(group_stab0()))
        self.assertEqual(g_id_task, group_id())
        self.assertEqual(group_intersection(group_rot(), g_first), group_id())

    def test_representability_equals_inclusion(self) -> None:
        worlds = all_worlds()
        task_groups = {task_id: symmetry_of(TASK_FNS[task_id], worlds) for task_id in TASK_IDS}
        inclusions = inclusion_matrix(worlds, task_groups)
        for model_id in ALL_MODEL_IDS:
            for task_id in TASK_IDS:
                with self.subTest(model=model_id, task=task_id):
                    represented = is_representable(worlds, model_id, task_id)
                    contained = inclusions[model_id][task_id]
                    self.assertEqual(represented, contained)
                    self.assertEqual(
                        represented,
                        y_constant_on_fibers(
                            worlds, MODEL_FNS[model_id], TASK_FNS[task_id]
                        ),
                    )

    def test_published_representability_matrix(self) -> None:
        worlds = all_worlds()
        matrix = representability_matrix(worlds)
        expected = {
            "q_id": {
                "bag": True,
                "necklace": True,
                "first_bit": True,
                "identity": True,
            },
            "q_rot": {
                "bag": True,
                "necklace": True,
                "first_bit": False,
                "identity": False,
            },
            "q_perm": {
                "bag": True,
                "necklace": False,
                "first_bit": False,
                "identity": False,
            },
        }
        self.assertEqual(matrix, expected)

    def test_overrepair_leftover_privilege_on_popcount(self) -> None:
        worlds = all_worlds()
        self.assertTrue(is_representable(worlds, "q_id", "bag"))
        self.assertTrue(is_representable(worlds, "q_perm", "bag"))
        self.assertGreater(fiber_count(worlds, q_id), fiber_count(worlds, q_perm))
        self.assertEqual(fiber_count(worlds, q_id), 16)
        self.assertEqual(fiber_count(worlds, q_perm), 5)

    def test_minimal_safe_first_bit(self) -> None:
        worlds = all_worlds()
        self.assertTrue(is_representable(worlds, "q_stab0", "first_bit"))
        self.assertFalse(is_representable(worlds, "q_perm", "first_bit"))
        self.assertFalse(is_representable(worlds, "q_rot", "first_bit"))
        # A rotation moves the first bit of 1000 to another index.
        x = (1, 0, 0, 0)
        rotated = apply_perm(rotate_left_perm(1), x)
        self.assertEqual(q_rot(x), q_rot(rotated))
        self.assertNotEqual(y_first_bit(x), y_first_bit(rotated))

    def test_repair_debt_mixed_fiber_and_split(self) -> None:
        worlds = all_worlds()
        mixed = mixed_fibers(worlds, q_perm, y_first_bit)
        self.assertGreaterEqual(len(mixed), 1)
        pop1 = next(cell for cell in mixed if cell["q_value"] == (0, 0, 0, 1))
        members = set(pop1["members"])
        self.assertIn((1, 0, 0, 0), members)
        self.assertIn((0, 1, 0, 0), members)
        self.assertEqual(sorted(pop1["y_values"]), [0, 1])
        self.assertTrue(
            is_exact_repair(worlds, q_perm, y_first_bit, y_first_bit)
        )
        self.assertTrue(
            repair_splits_disagreement(worlds, q_perm, y_first_bit, y_first_bit)
        )
        self.assertFalse(
            is_exact_repair(worlds, q_perm, lambda _x: 0, y_first_bit)
        )

    def test_noncommute_sequence_and_lean_pair(self) -> None:
        worlds = all_worlds()
        witness = find_sequence_noncommute_witness(worlds)
        self.assertIsNotNone(witness)
        assert witness is not None
        x, xp = witness
        self.assertEqual(path_a_seq(x), path_a_seq(xp))
        self.assertNotEqual(path_b_seq(x), path_b_seq(xp))
        # Lean regression: (0,1) vs (1,1).
        self.assertEqual(path_a_pair((0, 1)), path_a_pair((1, 1)))
        self.assertEqual(path_a_pair((0, 1)), (0, 1))
        self.assertEqual(path_b_pair((0, 1)), 1)
        self.assertEqual(path_b_pair((1, 1)), 0)
        # Concrete sequence lift of that pair.
        a = (0, 1, 0, 0)
        b = (1, 1, 0, 0)
        self.assertEqual(path_a_seq(a), path_a_seq(b))
        self.assertEqual(path_a_seq(a), (0, 1, 0, 0))
        self.assertEqual(path_b_seq(a), 1)
        self.assertEqual(path_b_seq(b), 0)

    def test_positional_holonomy_zero_and_nonzero_cycles(self) -> None:
        self.assertEqual(sum_int(ZERO_SUM_CYCLE), 0)
        self.assertNotEqual(sum_int(NONZERO_SUM_CYCLE), 0)
        self.assertTrue(cycle_closes(ZERO_SUM_CYCLE))
        self.assertFalse(cycle_closes(NONZERO_SUM_CYCLE))
        self.assertEqual(
            prefix_potentials(ZERO_SUM_CYCLE, start=0)[-1],
            sum_int(ZERO_SUM_CYCLE),
        )
        self.assertEqual(
            prefix_potentials(NONZERO_SUM_CYCLE, start=0)[-1],
            sum_int(NONZERO_SUM_CYCLE),
        )
        ok, constant = potentials_differ_by_constant(
            ZERO_SUM_CYCLE, HOLONOMY_P0, HOLONOMY_Q0
        )
        self.assertTrue(ok)
        self.assertEqual(constant, HOLONOMY_P0 - HOLONOMY_Q0)
        ok_nz, constant_nz = potentials_differ_by_constant(
            NONZERO_SUM_CYCLE, HOLONOMY_P0, HOLONOMY_Q0
        )
        self.assertTrue(ok_nz)
        self.assertEqual(constant_nz, HOLONOMY_P0 - HOLONOMY_Q0)

    def test_orbit_fibres_match_group_orbits(self) -> None:
        worlds = all_worlds()
        for model_id, group_fn in MODEL_GROUPS.items():
            group = group_fn()
            q_fn = MODEL_FNS[model_id]
            for x in worlds:
                self.assertEqual(frozenset(fibres_of(worlds, q_fn)[q_fn(x)]), orbit(x, group))

    def test_benchmark_passes_all_gates(self) -> None:
        payload = evaluate_benchmark()
        self.assertEqual(payload["status"], "pass")
        self.assertTrue(all(payload["gates"].values()))
        self.assertEqual(
            set(payload["gates"]),
            {
                "DTA_NOGO",
                "DTA_SAFE",
                "DTA_OVERREPAIR_COST",
                "DTA_MINIMAL_SAFE",
                "DTA_REPAIR_DEBT",
                "DTA_NONCOMMUTE",
                "DTA_POSITIONAL_HOLONOMY",
            },
        )
        self.assertEqual(len(payload["gate_table"]), 7)
        self.assertTrue(all(row["passed"] for row in payload["gate_table"]))
        self.assertEqual(payload["run_id"], "delete_the_absolute_2026_08_17")
        self.assertEqual(payload["world_size"], 16)
        self.assertEqual(payload["fiber_counts"]["q_id"], 16)
        self.assertEqual(payload["fiber_counts"]["q_perm"], 5)
        self.assertEqual(
            payload["representability_matrix"]["q_perm"]["first_bit"], False
        )
        json.dumps(payload)

    def test_payload_is_json_serializable_and_has_no_floats(self) -> None:
        payload = evaluate_benchmark()
        encoded = json.dumps(payload, sort_keys=True)
        decoded = json.loads(encoded)

        def assert_no_float(value: object, path: str) -> None:
            if isinstance(value, bool) or value is None:
                return
            if isinstance(value, float):
                self.fail(f"float at {path}")
            if isinstance(value, dict):
                for key, item in value.items():
                    assert_no_float(item, f"{path}.{key}")
                return
            if isinstance(value, list):
                for index, item in enumerate(value):
                    assert_no_float(item, f"{path}[{index}]")

        assert_no_float(decoded, "payload")


if __name__ == "__main__":
    unittest.main()
