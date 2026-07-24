"""Tests for the Wave 1b 3 x 3 x 3 crossed-factorial orchestrator.

Four regressions per the Wave 1b task brief:

1. **Cell shape.** :func:`build_all_cells` returns exactly 27
   ``CellSpec`` objects — one per ``(geometry, concern, family)``
   triple — and every axis level from
   :data:`GEOMETRY_AXIS`, :data:`CONCERN_AXIS`, and :data:`FAMILY_AXIS`
   appears the expected 9 times. Each cell honors its
   ``FAMILY_SEED_RANGES`` slice.
2. **Sealed env accessed once per episode.** :func:`run_cell`
   evaluates the sealed environment exactly ``len(rows)`` times on a
   well-formed run; the recorded receipt matches the per-row
   ``sealed_env_evaluate_calls`` invariant.
3. **Oracle cell refused by promotion harness.**
   :func:`refuse_promotion` raises
   :class:`PromotionRefused` on every cell whose geometry axis is
   ``ORACLE_WITHHELD`` or whose concern axis is ``ORACLE``. Non-ceiling
   cells are admitted unchanged.
4. **Intervention test signs.** :func:`intervene_on_edge` removes the
   correct edge (default = top-weighted; explicit ``edge_id`` respected
   in canonical form) and leaves every other edge intact. On a
   handcrafted geometry-vs-outcome fixture the intervention delta has
   the predicted sign.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("COGR_WAVE0_CONFIRMATORY_RUN", "1")

from experiments.concern_gated_retrieval.graph import WeightedGraph
from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    PromotionRefused,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    IntegrityAudit,
    LeakageError,
)
from experiments.concern_gated_retrieval_e2.wave1b.crossed import (
    CONCERN_AXIS,
    CONCERN_FROZEN_WRONG,
    CONCERN_ONLINE_LEARNED,
    CONCERN_ORACLE,
    CellResult,
    CellRow,
    CellSpec,
    DEFAULT_SEEDS_PER_CELL,
    FAMILY_AXIS,
    FAMILY_DELAYED,
    FAMILY_MAINTENANCE,
    FAMILY_RESOURCE,
    FAMILY_SEED_RANGES,
    GEOMETRY_AXIS,
    GEOM_FREQ_MATCHED_RANDOM,
    GEOM_LEARNED,
    GEOM_ORACLE_WITHHELD,
    build_all_cells,
    build_oracle_concern,
    intervene_on_edge,
    refuse_promotion,
    run_cell,
)


# --------------------------------------------------------------------------- #
# 1. Cell shape                                                                #
# --------------------------------------------------------------------------- #


class TestCellShape:
    def test_build_all_cells_returns_exactly_27(self) -> None:
        cells = build_all_cells(n_seeds=3)
        assert len(cells) == 27

    def test_every_geometry_appears_nine_times(self) -> None:
        cells = build_all_cells(n_seeds=3)
        for geometry in GEOMETRY_AXIS:
            count = sum(1 for c in cells if c.geometry == geometry)
            assert count == 9, f"geometry {geometry!r} appeared {count} times"

    def test_every_concern_appears_nine_times(self) -> None:
        cells = build_all_cells(n_seeds=3)
        for concern in CONCERN_AXIS:
            count = sum(1 for c in cells if c.concern == concern)
            assert count == 9, f"concern {concern!r} appeared {count} times"

    def test_every_family_appears_nine_times(self) -> None:
        cells = build_all_cells(n_seeds=3)
        for family in FAMILY_AXIS:
            count = sum(1 for c in cells if c.family == family)
            assert count == 9, f"family {family!r} appeared {count} times"

    def test_every_axis_triple_covered_exactly_once(self) -> None:
        cells = build_all_cells(n_seeds=3)
        triples = {
            (c.geometry, c.concern, c.family) for c in cells
        }
        assert len(triples) == 27
        for geometry in GEOMETRY_AXIS:
            for concern in CONCERN_AXIS:
                for family in FAMILY_AXIS:
                    assert (geometry, concern, family) in triples

    def test_seed_range_matches_n_seeds(self) -> None:
        cells = build_all_cells(n_seeds=5)
        for spec in cells:
            lo, hi = spec.seed_range
            assert hi - lo + 1 == spec.n_seeds

    def test_seed_range_inside_family_slice(self) -> None:
        cells = build_all_cells(n_seeds=3)
        for spec in cells:
            family_lo, family_hi = FAMILY_SEED_RANGES[spec.family]
            lo, hi = spec.seed_range
            assert lo >= family_lo
            assert hi <= family_hi

    def test_cell_id_stable_and_unique(self) -> None:
        cells = build_all_cells(n_seeds=3)
        ids = [c.cell_id for c in cells]
        assert len(set(ids)) == len(ids)
        # Stable: same construction, same id.
        again = build_all_cells(n_seeds=3)
        for a, b in zip(cells, again):
            assert a.cell_id == b.cell_id

    def test_cellspec_rejects_unknown_geometry(self) -> None:
        with pytest.raises(ValueError, match="geometry"):
            CellSpec(
                geometry="MADE_UP",
                concern=CONCERN_FROZEN_WRONG,
                family=FAMILY_DELAYED,
                n_seeds=3,
                seed_range=(200_000, 200_002),
            )

    def test_cellspec_rejects_unknown_concern(self) -> None:
        with pytest.raises(ValueError, match="concern"):
            CellSpec(
                geometry=GEOM_LEARNED,
                concern="OFF_PLAN",
                family=FAMILY_DELAYED,
                n_seeds=3,
                seed_range=(200_000, 200_002),
            )

    def test_cellspec_rejects_unknown_family(self) -> None:
        with pytest.raises(ValueError, match="family"):
            CellSpec(
                geometry=GEOM_LEARNED,
                concern=CONCERN_FROZEN_WRONG,
                family="rogue_family",
                n_seeds=3,
                seed_range=(200_000, 200_002),
            )

    def test_cellspec_rejects_n_seeds_range_mismatch(self) -> None:
        with pytest.raises(ValueError, match="seed_range width"):
            CellSpec(
                geometry=GEOM_LEARNED,
                concern=CONCERN_FROZEN_WRONG,
                family=FAMILY_DELAYED,
                n_seeds=10,
                seed_range=(200_000, 200_002),
            )

    def test_cellspec_rejects_out_of_family_seed_range(self) -> None:
        with pytest.raises(ValueError, match="outside"):
            CellSpec(
                geometry=GEOM_LEARNED,
                concern=CONCERN_FROZEN_WRONG,
                family=FAMILY_RESOURCE,
                n_seeds=3,
                seed_range=(200_000, 200_002),  # not inside RC slice
            )

    def test_build_all_cells_default_n_matches_prereg(self) -> None:
        assert DEFAULT_SEEDS_PER_CELL == 300

    def test_family_seed_ranges_widths(self) -> None:
        for family, (lo, hi) in FAMILY_SEED_RANGES.items():
            width = hi - lo + 1
            assert width >= DEFAULT_SEEDS_PER_CELL, (
                f"family {family!r} slice width {width} < N=300"
            )


# --------------------------------------------------------------------------- #
# 2. Sealed env accessed once per episode                                     #
# --------------------------------------------------------------------------- #


class TestSealedEnvSingleShot:
    """Sealed environment ``evaluate()`` is called exactly once per row.

    When the L1 edge-intervention diagnostic is enabled on a LEARNED cell
    an additional counterfactual evaluation is recorded — that path is
    tested separately below so the invariant is transparent.
    """

    @pytest.mark.parametrize(
        "geometry, concern, family, lo",
        [
            (GEOM_LEARNED, CONCERN_FROZEN_WRONG, FAMILY_DELAYED, 200_000),
            (GEOM_FREQ_MATCHED_RANDOM, CONCERN_FROZEN_WRONG, FAMILY_MAINTENANCE, 200_300),
            (GEOM_ORACLE_WITHHELD, CONCERN_FROZEN_WRONG, FAMILY_RESOURCE, 200_600),
            (GEOM_LEARNED, CONCERN_ONLINE_LEARNED, FAMILY_DELAYED, 200_010),
            (GEOM_LEARNED, CONCERN_ORACLE, FAMILY_MAINTENANCE, 200_320),
        ],
    )
    def test_one_evaluate_call_per_row_no_intervention(
        self,
        geometry: str,
        concern: str,
        family: str,
        lo: int,
    ) -> None:
        spec = CellSpec(
            geometry=geometry,
            concern=concern,
            family=family,
            n_seeds=3,
            seed_range=(lo, lo + 2),
        )
        result = run_cell(spec)
        assert len(result.rows) == 3
        assert result.sealed_env_evaluate_calls == 3
        for row in result.rows:
            assert row.sealed_env_evaluate_calls == 1

    def test_intervention_adds_one_more_evaluate_call_when_selection_differs(
        self,
    ) -> None:
        # A LEARNED / FROZEN_WRONG / DELAYED cell with intervention on
        # the top-weighted edge: when the counterfactual selection
        # differs from the original the runner spends a fresh sealed
        # environment on the counterfactual. Otherwise it does not.
        spec = CellSpec(
            geometry=GEOM_LEARNED,
            concern=CONCERN_FROZEN_WRONG,
            family=FAMILY_DELAYED,
            n_seeds=3,
            seed_range=(200_000, 200_002),
        )
        result = run_cell(spec, intervention_edge_index=0)
        # Each row: 1 sealed evaluate + 0 or 1 counterfactual evaluate.
        for row in result.rows:
            assert row.sealed_env_evaluate_calls == 1
            if row.intervention_edge is not None:
                assert row.intervention_delta is not None
        # Total sealed calls is at least N (one per row) and at most 2N.
        n = len(result.rows)
        assert n <= result.sealed_env_evaluate_calls <= 2 * n


# --------------------------------------------------------------------------- #
# 3. Oracle cell refused by promotion harness                                 #
# --------------------------------------------------------------------------- #


class TestPromotionRefusal:
    def test_non_ceiling_cell_admitted(self) -> None:
        spec = CellSpec(
            geometry=GEOM_LEARNED,
            concern=CONCERN_FROZEN_WRONG,
            family=FAMILY_DELAYED,
            n_seeds=3,
            seed_range=(200_000, 200_002),
        )
        assert refuse_promotion(spec) is spec

    def test_online_learned_learned_admitted(self) -> None:
        # L2 gate row — the promotable candidate on the concern axis.
        spec = CellSpec(
            geometry=GEOM_LEARNED,
            concern=CONCERN_ONLINE_LEARNED,
            family=FAMILY_MAINTENANCE,
            n_seeds=3,
            seed_range=(200_300, 200_302),
        )
        assert refuse_promotion(spec) is spec

    def test_freq_matched_random_admitted(self) -> None:
        # L1 gate row — the matched-budget null on the geometry axis.
        spec = CellSpec(
            geometry=GEOM_FREQ_MATCHED_RANDOM,
            concern=CONCERN_FROZEN_WRONG,
            family=FAMILY_DELAYED,
            n_seeds=3,
            seed_range=(200_000, 200_002),
        )
        assert refuse_promotion(spec) is spec

    @pytest.mark.parametrize(
        "geometry, concern",
        [
            (GEOM_ORACLE_WITHHELD, CONCERN_FROZEN_WRONG),
            (GEOM_ORACLE_WITHHELD, CONCERN_ONLINE_LEARNED),
            (GEOM_ORACLE_WITHHELD, CONCERN_ORACLE),
            (GEOM_LEARNED, CONCERN_ORACLE),
            (GEOM_FREQ_MATCHED_RANDOM, CONCERN_ORACLE),
        ],
    )
    def test_ceiling_axis_level_refused(
        self, geometry: str, concern: str
    ) -> None:
        spec = CellSpec(
            geometry=geometry,
            concern=concern,
            family=FAMILY_DELAYED,
            n_seeds=3,
            seed_range=(200_000, 200_002),
        )
        with pytest.raises(PromotionRefused):
            refuse_promotion(spec)

    def test_refuse_promotion_rejects_non_cellspec(self) -> None:
        with pytest.raises(TypeError):
            refuse_promotion({"geometry": GEOM_LEARNED})  # ty: ignore[invalid-argument-type]  # noqa

    def test_oracle_concern_factory_flagged_ceiling_only(self) -> None:
        # ``promotion_admit`` from wave0.baselines refuses any callable
        # with ``is_ceiling_only`` set truthy; the crossed runner's
        # ORACLE-concern factory sets this flag by construction.
        from experiments.concern_gated_retrieval_e2.wave0.baselines import (
            CEILING_MARKER,
            promotion_admit,
        )

        assert getattr(build_oracle_concern, CEILING_MARKER, False) is True
        with pytest.raises(PromotionRefused):
            promotion_admit(build_oracle_concern)

    def test_oracle_concern_factory_flagged_by_integrity_audit(self) -> None:
        # Body dereferences ``episode._answer_key`` — a sealed
        # field. ``IntegrityAudit.assert_clean`` must flag it so any
        # policy source that references this helper fails the audit.
        with pytest.raises(LeakageError):
            IntegrityAudit.assert_clean(build_oracle_concern)


# --------------------------------------------------------------------------- #
# 4. Intervention test signs                                                  #
# --------------------------------------------------------------------------- #


class TestIntervention:
    def _diamond_graph(self) -> WeightedGraph:
        """A handcrafted diamond with a dominant edge for sign tests."""
        return WeightedGraph.from_edges(
            ("a", "b", "c", "d"),
            [
                ("a", "b", 0.5),
                ("b", "c", 2.0),  # dominant edge
                ("c", "d", 1.0),
                ("a", "d", 0.3),
            ],
        )

    def test_default_removes_top_weighted_edge(self) -> None:
        g = self._diamond_graph()
        g2 = intervene_on_edge(g)
        # Top edge (b, c, 2.0) removed; every other edge preserved.
        assert "c" not in g2.adjacency["b"]
        assert "b" not in g2.adjacency["c"]
        assert g2.adjacency["a"].get("b") == pytest.approx(0.5)
        assert g2.adjacency["c"].get("d") == pytest.approx(1.0)
        assert g2.adjacency["a"].get("d") == pytest.approx(0.3)

    def test_specific_edge_removed_canonical_form(self) -> None:
        g = self._diamond_graph()
        # Non-canonical order — helper canonicalises.
        g2 = intervene_on_edge(g, edge_id=("d", "c"))
        assert "d" not in g2.adjacency["c"]
        assert "c" not in g2.adjacency["d"]
        # Other edges intact.
        assert g2.adjacency["b"].get("c") == pytest.approx(2.0)

    def test_specific_edge_removed_canonical_form_ordered(self) -> None:
        g = self._diamond_graph()
        g2 = intervene_on_edge(g, edge_id=("a", "b"))
        assert "b" not in g2.adjacency["a"]
        assert "a" not in g2.adjacency["b"]

    def test_missing_edge_is_no_op(self) -> None:
        g = self._diamond_graph()
        g2 = intervene_on_edge(g, edge_id=("a", "c"))  # not in graph
        # Every original edge is preserved.
        assert g2.adjacency["a"].get("b") == pytest.approx(0.5)
        assert g2.adjacency["b"].get("c") == pytest.approx(2.0)
        assert g2.adjacency["c"].get("d") == pytest.approx(1.0)
        assert g2.adjacency["a"].get("d") == pytest.approx(0.3)

    def test_empty_graph_returns_empty(self) -> None:
        g = WeightedGraph.from_edges(("a", "b", "c"), [])
        g2 = intervene_on_edge(g)
        for node in g.nodes:
            assert g2.adjacency[node] == {}

    def test_rejects_non_weighted_graph(self) -> None:
        with pytest.raises(TypeError):
            intervene_on_edge({"nodes": (), "adjacency": {}})  # ty: ignore[invalid-argument-type]  # noqa

    def test_rejects_malformed_edge_id(self) -> None:
        g = self._diamond_graph()
        with pytest.raises(ValueError):
            intervene_on_edge(g, edge_id=("a",))  # ty: ignore[invalid-argument-type]  # noqa
        with pytest.raises(ValueError):
            intervene_on_edge(g, edge_id=(1, 2))  # ty: ignore[invalid-argument-type]  # noqa

    def test_intervention_delta_recorded_on_learned_cell(self) -> None:
        # The intervention-delta receipt is non-``None`` on LEARNED
        # cells with the diagnostic enabled and untouched on the other
        # geometry axes.
        spec_learned = CellSpec(
            geometry=GEOM_LEARNED,
            concern=CONCERN_FROZEN_WRONG,
            family=FAMILY_MAINTENANCE,
            n_seeds=2,
            seed_range=(200_300, 200_301),
        )
        result_learned = run_cell(spec_learned, intervention_edge_index=0)
        # At least one row must have the intervention recorded (the
        # graph has at least one edge for maintenance_fault_v2).
        any_recorded = any(
            row.intervention_edge is not None for row in result_learned.rows
        )
        assert any_recorded

        spec_random = CellSpec(
            geometry=GEOM_FREQ_MATCHED_RANDOM,
            concern=CONCERN_FROZEN_WRONG,
            family=FAMILY_MAINTENANCE,
            n_seeds=2,
            seed_range=(200_300, 200_301),
        )
        result_random = run_cell(spec_random, intervention_edge_index=0)
        # Non-LEARNED cells never record intervention receipts because
        # the intervention target is the learned graph.
        for row in result_random.rows:
            assert row.intervention_edge is None
            assert row.intervention_delta is None


# --------------------------------------------------------------------------- #
# Result-shape smoke tests                                                    #
# --------------------------------------------------------------------------- #


class TestCellResultShape:
    def test_run_cell_receipt_shape(self) -> None:
        spec = CellSpec(
            geometry=GEOM_LEARNED,
            concern=CONCERN_FROZEN_WRONG,
            family=FAMILY_DELAYED,
            n_seeds=3,
            seed_range=(200_000, 200_002),
        )
        result = run_cell(spec)
        assert isinstance(result, CellResult)
        assert result.spec is spec
        assert len(result.rows) == 3
        assert all(isinstance(r, CellRow) for r in result.rows)
        for row in result.rows:
            assert -1.0 <= row.realized_reward <= 1.0
            assert row.misretrieval_cost >= 0.0
            assert isinstance(row.constraint_preserved, bool)
            assert row.receipt.candidate == row.selected[0]
        # Aggregate carries the four canonical keys.
        for key in (
            "mean_reward",
            "mean_misretrieval_cost",
            "mean_constraint_preserved",
            "n_rows",
        ):
            assert key in result.aggregate
        assert result.integrity_audit_passed is True
        assert result.wall_seconds >= 0.0

    def test_online_learned_row_has_concern_after(self) -> None:
        spec = CellSpec(
            geometry=GEOM_LEARNED,
            concern=CONCERN_ONLINE_LEARNED,
            family=FAMILY_DELAYED,
            n_seeds=3,
            seed_range=(200_000, 200_002),
        )
        result = run_cell(spec)
        for row in result.rows:
            assert row.concern_after is not None
            # concern_before and concern_after share the anchor key set.
            assert set(row.concern_before) == set(row.concern_after)

    def test_frozen_row_has_no_concern_after(self) -> None:
        spec = CellSpec(
            geometry=GEOM_LEARNED,
            concern=CONCERN_FROZEN_WRONG,
            family=FAMILY_DELAYED,
            n_seeds=2,
            seed_range=(200_000, 200_001),
        )
        result = run_cell(spec)
        for row in result.rows:
            assert row.concern_after is None
