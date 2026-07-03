import pytest

from experiments.long_horizon_bottleneck.core import (
    build_cells,
    build_horizon_cells,
    estimate_modal_cost,
    summarize_rows,
    summarize_recovery_rows,
    summarize_tool_rows,
)


def test_budget_guard_keeps_default_l4_sweep_well_under_1000():
    est = estimate_modal_cost(
        cells=128,
        gpu="L4",
        timeout_seconds=900,
        budget_usd=1000,
    )

    assert est.within_budget
    assert est.conservative_cost_usd < 40


def test_build_cells_crosses_conditions_architectures_slots_and_seeds():
    cells = build_cells(
        seeds=[0, 1],
        architectures=["gru", "transformer"],
        conditions=["bottleneck", "visible_control"],
        critical_slots=[0, 1, 2, 3],
        n_slots=4,
        sequence_length=128,
        slot_gap=8,
        train_steps=100,
        batch_size=64,
        eval_batches=2,
        metric_batches=2,
        hidden_size=32,
        base_seed=20260702,
    )

    assert len(cells) == 2 * 2 * 2 * 4
    assert cells[0]["slot_positions"] == [8, 16, 24, 32]
    assert {c["critical_slot"] for c in cells} == {0, 1, 2, 3}


def test_build_cells_rejects_slot_positions_that_reach_terminal_query():
    with pytest.raises(ValueError, match="leave the final sequence element"):
        build_cells(
            seeds=[0],
            architectures=["transformer"],
            conditions=["bottleneck"],
            critical_slots=[0],
            n_slots=4,
            sequence_length=17,
            slot_gap=4,
            train_steps=100,
            batch_size=64,
            eval_batches=2,
            metric_batches=2,
            hidden_size=32,
            base_seed=20260702,
        )


def test_build_horizon_cells_crosses_sequence_lengths_with_distinct_seed_blocks():
    cells = build_horizon_cells(
        sequence_lengths=[128, 256],
        seeds=[0, 1],
        architectures=["transformer"],
        conditions=["bottleneck"],
        critical_slots=[0, 1],
        n_slots=4,
        slot_gap=8,
        train_steps=100,
        batch_size=64,
        eval_batches=2,
        metric_batches=2,
        hidden_size=32,
        base_seed=20260702,
    )

    assert len(cells) == 2 * 2 * 2
    assert {c["sequence_length"] for c in cells} == {128, 256}
    assert min(c["seed"] for c in cells if c["sequence_length"] == 256) >= 20360702


def test_summarize_rows_detects_transport_and_visible_control_null():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "bottleneck",
                "architecture": "gru",
                "critical_slot": seed % 4,
                "sequence_length": 128,
                "accuracy": 0.98,
                "memory_specificity_z": 1.2,
                "memory_rank_percentile": 1.0,
            }
        )
        rows.append(
            {
                "condition": "visible_control",
                "architecture": "gru",
                "critical_slot": seed % 4,
                "sequence_length": 128,
                "accuracy": 0.99,
                "memory_specificity_z": 0.05,
                "memory_rank_percentile": 0.5,
            }
        )

    summary = summarize_rows(rows, n_boot=200)

    assert summary["groups"]["bottleneck/gru"]["gate"]["pass"]
    assert summary["horizon_groups"]["bottleneck/gru/length_128"]["gate"]["pass"]
    assert summary["groups"]["visible_control/gru"]["gate"]["pass"]
    assert summary["pooled_bottleneck"]["gate"]["pass"]


def test_summarize_tool_rows_requires_commitment_and_visible_null():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "tool_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "final_accuracy": 1.0,
                "tool_slot_accuracy": 1.0,
                "tool_value_accuracy": 1.0,
                "memory_specificity_z": 1.4,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.1,
            }
        )
        rows.append(
            {
                "condition": "visible_control",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "final_accuracy": 1.0,
                "tool_slot_accuracy": 1.0,
                "tool_value_accuracy": float("nan"),
                "memory_specificity_z": 0.0,
                "memory_rank_percentile": 0.5,
                "tool_value_specificity_z": 0.0,
            }
        )

    summary = summarize_tool_rows(rows, n_boot=200)

    assert summary["groups"]["tool_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_tool_bottleneck"]["gate"]["pass"]


def test_summarize_tool_rows_prefers_closed_loop_final_accuracy_when_present():
    rows = [
        {
            "condition": "tool_bottleneck",
            "architecture": "transformer",
            "critical_slot": seed % 4,
            "final_accuracy": 1.0,
            "teacher_forced_final_accuracy": 1.0,
            "closed_loop_final_accuracy": 0.0,
            "tool_slot_accuracy": 1.0,
            "tool_value_accuracy": 1.0,
            "memory_specificity_z": 1.4,
            "memory_rank_percentile": 0.875,
            "tool_value_specificity_z": 1.1,
        }
        for seed in range(8)
    ]

    summary = summarize_tool_rows(rows, n_boot=200)
    group = summary["groups"]["tool_bottleneck/transformer"]

    assert group["final_metric"] == "closed_loop_final_accuracy"
    assert group["teacher_forced_final_accuracy"]["mean"] == 1.0
    assert not group["gate"]["closed_loop_final_accuracy_ge_0_90"]
    assert not group["gate"]["pass"]


def test_summarize_recovery_rows_requires_repair_commitment_and_visible_null():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "direct_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_tool_slot_accuracy": 1.0,
                "first_tool_value_accuracy": 1.0,
                "repair_tool_slot_accuracy": 0.0,
                "repair_tool_value_accuracy": float("nan"),
                "memory_specificity_z": 1.4,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.1,
            }
        )
        rows.append(
            {
                "condition": "repair_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_tool_slot_accuracy": 1.0,
                "first_tool_value_accuracy": 1.0,
                "repair_tool_slot_accuracy": 1.0,
                "repair_tool_value_accuracy": 1.0,
                "memory_specificity_z": 1.5,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.2,
            }
        )
        rows.append(
            {
                "condition": "visible_control",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_tool_slot_accuracy": 1.0,
                "first_tool_value_accuracy": float("nan"),
                "repair_tool_slot_accuracy": 1.0,
                "repair_tool_value_accuracy": float("nan"),
                "memory_specificity_z": 0.0,
                "memory_rank_percentile": 0.5,
                "tool_value_specificity_z": 0.0,
            }
        )

    summary = summarize_recovery_rows(rows, n_boot=200)

    assert summary["groups"]["direct_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["repair_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_direct_bottleneck"]["gate"]["pass"]
    assert summary["pooled_repair_bottleneck"]["gate"]["pass"]
