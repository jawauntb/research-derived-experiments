import pytest

from experiments.long_horizon_bottleneck.core import (
    alias_argument_id,
    alias_argument_vocab_size,
    build_cells,
    build_horizon_cells,
    estimate_modal_cost,
    multifield_call_tokens,
    multifield_malformed_tokens,
    multifield_noop_tokens,
    multifield_vocab_sizes,
    parse_multifield_action,
    parse_alias_argument,
    parse_structured_action,
    render_multifield_action,
    render_structured_action,
    structured_action_vocab_size,
    structured_call_action_id,
    structured_malformed_action_id,
    structured_noop_action_id,
    summarize_rows,
    summarize_recovery_rows,
    summarize_multifield_rows,
    summarize_structured_rows,
    summarize_stochastic_rows,
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


def test_structured_action_vocab_roundtrips_and_parses_schema():
    n_slots = 4
    assert structured_action_vocab_size(n_slots) == 2 * n_slots + 5

    # Every executable call round-trips through parse with matching slot/value.
    for slot in range(n_slots):
        for value in (0, 1):
            token = structured_call_action_id(slot, value, n_slots)
            parsed = parse_structured_action(token, n_slots)
            assert parsed["opcode"] == "call"
            assert parsed["executable"] and parsed["valid"]
            assert parsed["slot"] == slot and parsed["value"] == value

    noop = parse_structured_action(structured_noop_action_id(n_slots), n_slots)
    assert noop["opcode"] == "noop"
    assert noop["valid"] and not noop["executable"]

    bad = parse_structured_action(structured_malformed_action_id("bad_slot", n_slots), n_slots)
    assert bad["opcode"] == "malformed"
    assert bad["reason"] == "bad_slot"
    assert not bad["valid"] and not bad["executable"]


def test_structured_action_ids_are_unique_and_dense():
    n_slots = 3
    size = structured_action_vocab_size(n_slots)
    ids = set()
    for slot in range(n_slots):
        for value in (0, 1):
            ids.add(structured_call_action_id(slot, value, n_slots))
    ids.add(structured_noop_action_id(n_slots))
    for reason in ("missing_slot", "bad_slot", "bad_value", "malformed_order"):
        ids.add(structured_malformed_action_id(reason, n_slots))
    assert ids == set(range(size))


def test_render_structured_action_emits_json_like_strings():
    n_slots = 4
    call = parse_structured_action(structured_call_action_id(2, 1, n_slots), n_slots)
    assert render_structured_action(call) == '{"tool": "read_slot", "slot": 2, "value": 1}'
    noop = parse_structured_action(structured_noop_action_id(n_slots), n_slots)
    assert render_structured_action(noop) == '{"tool": "noop"}'
    malformed = parse_structured_action(structured_malformed_action_id("bad_value", n_slots), n_slots)
    assert render_structured_action(malformed) == '{"error": "bad_value"}'


def test_parse_structured_action_rejects_out_of_range_tokens():
    with pytest.raises(ValueError, match="outside structured vocab"):
        parse_structured_action(structured_action_vocab_size(4), 4)


def test_summarize_structured_rows_requires_repair_call_and_visible_null():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "structured_direct_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_action_token_accuracy": 1.0,
                "first_action_schema_validity": 1.0,
                "first_parsed_slot_accuracy": 1.0,
                "first_parsed_value_accuracy": 1.0,
                "repair_action_token_accuracy": 1.0,
                "repair_action_schema_validity": 0.0,
                "repair_parsed_slot_accuracy": float("nan"),
                "repair_parsed_value_accuracy": float("nan"),
                "memory_specificity_z": 1.4,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.1,
            }
        )
        rows.append(
            {
                "condition": "structured_repair_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_action_token_accuracy": 1.0,
                "first_action_schema_validity": 1.0,
                "first_parsed_slot_accuracy": 1.0,
                "first_parsed_value_accuracy": 1.0,
                "repair_action_token_accuracy": 1.0,
                "repair_action_schema_validity": 1.0,
                "repair_parsed_slot_accuracy": 1.0,
                "repair_parsed_value_accuracy": 1.0,
                "memory_specificity_z": 1.5,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.2,
            }
        )
        rows.append(
            {
                "condition": "structured_visible_control",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_action_token_accuracy": 1.0,
                "first_action_schema_validity": 0.0,
                "first_parsed_slot_accuracy": float("nan"),
                "first_parsed_value_accuracy": float("nan"),
                "repair_action_token_accuracy": 1.0,
                "repair_action_schema_validity": 0.0,
                "repair_parsed_slot_accuracy": float("nan"),
                "repair_parsed_value_accuracy": float("nan"),
                "memory_specificity_z": 0.0,
                "memory_rank_percentile": 0.5,
                "tool_value_specificity_z": 0.0,
            }
        )

    summary = summarize_structured_rows(rows, n_boot=200)

    assert summary["groups"]["structured_direct_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["structured_repair_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["structured_visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_structured_direct_bottleneck"]["gate"]["pass"]
    assert summary["pooled_structured_repair_bottleneck"]["gate"]["pass"]


def test_summarize_structured_rows_fails_repair_when_schema_invalid():
    rows = [
        {
            "condition": "structured_repair_bottleneck",
            "architecture": "transformer",
            "critical_slot": seed % 4,
            "closed_loop_final_accuracy": 1.0,
            "teacher_forced_final_accuracy": 1.0,
            "first_action_token_accuracy": 1.0,
            "first_action_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 1.0,
            "first_parsed_value_accuracy": 1.0,
            "repair_action_token_accuracy": 1.0,
            "repair_action_schema_validity": 0.4,
            "repair_parsed_slot_accuracy": 1.0,
            "repair_parsed_value_accuracy": 1.0,
            "memory_specificity_z": 1.5,
            "memory_rank_percentile": 0.875,
            "tool_value_specificity_z": 1.2,
        }
        for seed in range(8)
    ]

    summary = summarize_structured_rows(rows, n_boot=200)
    group = summary["groups"]["structured_repair_bottleneck/transformer"]

    assert not group["gate"]["repair_action_schema_valid_ge_0_90"]
    assert not group["gate"]["pass"]


def test_multifield_action_schema_parses_calls_noops_and_malformed_arguments():
    n_slots = 4
    assert multifield_vocab_sizes(n_slots) == {"opcode": 3, "slot": 6, "value": 4}

    call = parse_multifield_action(*multifield_call_tokens(2, 1, n_slots), n_slots)
    assert call["opcode"] == "call"
    assert call["valid"] and call["executable"]
    assert call["slot"] == 2 and call["value"] == 1
    assert render_multifield_action(call) == '{"tool": "read_slot", "slot": 2, "value": 1}'

    noop = parse_multifield_action(*multifield_noop_tokens(n_slots), n_slots)
    assert noop["opcode"] == "noop"
    assert noop["valid"] and not noop["executable"]
    assert render_multifield_action(noop) == '{"tool": "noop"}'

    bad_slot = parse_multifield_action(*multifield_malformed_tokens("bad_slot", n_slots), n_slots)
    assert bad_slot["reason"] == "bad_slot"
    assert not bad_slot["valid"] and not bad_slot["executable"]
    assert render_multifield_action(bad_slot) == '{"error": "bad_slot"}'


def test_parse_multifield_action_rejects_out_of_range_fields():
    with pytest.raises(ValueError, match="opcode_id"):
        parse_multifield_action(3, 0, 0, 4)
    with pytest.raises(ValueError, match="slot_id"):
        parse_multifield_action(0, 6, 0, 4)
    with pytest.raises(ValueError, match="value_id"):
        parse_multifield_action(0, 0, 4, 4)


def test_alias_argument_surface_maps_synonyms_to_canonical_slots():
    n_slots = 4
    aliases_per_slot = 3

    assert alias_argument_vocab_size(n_slots, aliases_per_slot) == 14
    alias_ids = [
        alias_argument_id(slot=2, alias_index=alias, n_slots=n_slots, aliases_per_slot=aliases_per_slot)
        for alias in range(aliases_per_slot)
    ]

    for alias, argument_id in enumerate(alias_ids):
        parsed = parse_alias_argument(argument_id, n_slots, aliases_per_slot)
        assert parsed["slot"] == 2
        assert parsed["alias_index"] == alias
        assert parsed["valid"]
        assert not parsed["missing"]

    missing = parse_alias_argument(n_slots * aliases_per_slot, n_slots, aliases_per_slot)
    assert missing == {"slot": None, "alias_index": None, "valid": True, "missing": True, "reason": None}
    malformed = parse_alias_argument(n_slots * aliases_per_slot + 1, n_slots, aliases_per_slot)
    assert malformed == {
        "slot": None,
        "alias_index": None,
        "valid": False,
        "missing": False,
        "reason": "bad_alias",
    }
    with pytest.raises(ValueError, match="argument_id"):
        parse_alias_argument(alias_argument_vocab_size(n_slots, aliases_per_slot), n_slots, aliases_per_slot)


def test_summarize_multifield_rows_requires_composed_schema_and_repair_fields():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "multifield_direct_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_field_accuracy": 1.0,
                "first_schema_validity": 1.0,
                "first_parsed_slot_accuracy": 1.0,
                "first_parsed_value_accuracy": 1.0,
                "repair_field_accuracy": float("nan"),
                "repair_schema_validity": float("nan"),
                "repair_parsed_slot_accuracy": float("nan"),
                "repair_parsed_value_accuracy": float("nan"),
                "memory_specificity_z": 1.4,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.1,
            }
        )
        rows.append(
            {
                "condition": "multifield_repair_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_field_accuracy": 1.0,
                "first_schema_validity": 1.0,
                "first_parsed_slot_accuracy": 1.0,
                "first_parsed_value_accuracy": 1.0,
                "repair_field_accuracy": 1.0,
                "repair_schema_validity": 1.0,
                "repair_parsed_slot_accuracy": 1.0,
                "repair_parsed_value_accuracy": 1.0,
                "memory_specificity_z": 1.5,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.2,
            }
        )
        rows.append(
            {
                "condition": "multifield_visible_control",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_field_accuracy": 1.0,
                "first_schema_validity": 1.0,
                "first_parsed_slot_accuracy": float("nan"),
                "first_parsed_value_accuracy": float("nan"),
                "repair_field_accuracy": 1.0,
                "repair_schema_validity": 1.0,
                "repair_parsed_slot_accuracy": float("nan"),
                "repair_parsed_value_accuracy": float("nan"),
                "memory_specificity_z": 0.0,
                "memory_rank_percentile": 0.5,
                "tool_value_specificity_z": 0.0,
            }
        )

    summary = summarize_multifield_rows(rows, n_boot=200)

    assert summary["groups"]["multifield_direct_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["multifield_repair_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["multifield_visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_multifield_direct_bottleneck"]["gate"]["pass"]
    assert summary["pooled_multifield_repair_bottleneck"]["gate"]["pass"]


def test_summarize_multifield_rows_fails_repair_when_a_field_breaks_schema():
    rows = [
        {
            "condition": "multifield_repair_bottleneck",
            "architecture": "transformer",
            "critical_slot": seed % 4,
            "closed_loop_final_accuracy": 1.0,
            "teacher_forced_final_accuracy": 1.0,
            "first_field_accuracy": 1.0,
            "first_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 1.0,
            "first_parsed_value_accuracy": 1.0,
            "repair_field_accuracy": 1.0,
            "repair_schema_validity": 0.4,
            "repair_parsed_slot_accuracy": 1.0,
            "repair_parsed_value_accuracy": 1.0,
            "memory_specificity_z": 1.5,
            "memory_rank_percentile": 0.875,
            "tool_value_specificity_z": 1.2,
        }
        for seed in range(8)
    ]

    summary = summarize_multifield_rows(rows, n_boot=200)
    group = summary["groups"]["multifield_repair_bottleneck/transformer"]

    assert not group["gate"]["repair_schema_valid_ge_0_90"]
    assert not group["gate"]["pass"]


def test_summarize_stochastic_rows_requires_failed_repair_and_success_noop():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "stochastic_failure_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_field_accuracy": 1.0,
                "first_schema_validity": 1.0,
                "first_parsed_slot_accuracy": 1.0,
                "first_parsed_value_accuracy": 1.0,
                "repair_field_accuracy": 1.0,
                "repair_schema_validity": 1.0,
                "repair_failed_field_accuracy": 1.0,
                "repair_failed_schema_validity": 1.0,
                "repair_failed_parsed_slot_accuracy": 1.0,
                "repair_failed_parsed_value_accuracy": 1.0,
                "repair_success_noop_field_accuracy": 1.0,
                "repair_success_schema_validity": 1.0,
                "sampled_failure_rate": 0.5,
                "memory_specificity_z": 1.5,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.2,
            }
        )
        rows.append(
            {
                "condition": "stochastic_visible_control",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_field_accuracy": 1.0,
                "first_schema_validity": 1.0,
                "first_parsed_slot_accuracy": float("nan"),
                "first_parsed_value_accuracy": float("nan"),
                "repair_field_accuracy": 1.0,
                "repair_schema_validity": 1.0,
                "repair_failed_field_accuracy": float("nan"),
                "repair_failed_schema_validity": float("nan"),
                "repair_failed_parsed_slot_accuracy": float("nan"),
                "repair_failed_parsed_value_accuracy": float("nan"),
                "repair_success_noop_field_accuracy": 1.0,
                "repair_success_schema_validity": 1.0,
                "sampled_failure_rate": 0.5,
                "memory_specificity_z": 0.0,
                "memory_rank_percentile": 0.5,
                "tool_value_specificity_z": 0.0,
            }
        )

    summary = summarize_stochastic_rows(rows, n_boot=200)

    assert summary["groups"]["stochastic_failure_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["stochastic_visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_stochastic_failure_bottleneck"]["gate"]["pass"]


def test_summarize_stochastic_rows_supports_alias_argument_conditions():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "alias_stochastic_bottleneck",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_field_accuracy": 1.0,
                "first_schema_validity": 1.0,
                "first_parsed_slot_accuracy": 1.0,
                "first_parsed_value_accuracy": 1.0,
                "repair_field_accuracy": 1.0,
                "repair_schema_validity": 1.0,
                "repair_failed_field_accuracy": 1.0,
                "repair_failed_schema_validity": 1.0,
                "repair_failed_parsed_slot_accuracy": 1.0,
                "repair_failed_parsed_value_accuracy": 1.0,
                "repair_success_noop_field_accuracy": 1.0,
                "repair_success_schema_validity": 1.0,
                "sampled_failure_rate": 0.5,
                "memory_specificity_z": 1.5,
                "memory_rank_percentile": 0.875,
                "tool_value_specificity_z": 1.2,
            }
        )
        rows.append(
            {
                "condition": "alias_visible_control",
                "architecture": "transformer",
                "critical_slot": seed % 4,
                "closed_loop_final_accuracy": 1.0,
                "teacher_forced_final_accuracy": 1.0,
                "first_field_accuracy": 1.0,
                "first_schema_validity": 1.0,
                "first_parsed_slot_accuracy": float("nan"),
                "first_parsed_value_accuracy": float("nan"),
                "repair_field_accuracy": 1.0,
                "repair_schema_validity": 1.0,
                "repair_failed_field_accuracy": float("nan"),
                "repair_failed_schema_validity": float("nan"),
                "repair_failed_parsed_slot_accuracy": float("nan"),
                "repair_failed_parsed_value_accuracy": float("nan"),
                "repair_success_noop_field_accuracy": 1.0,
                "repair_success_schema_validity": 1.0,
                "sampled_failure_rate": 0.5,
                "memory_specificity_z": 0.0,
                "memory_rank_percentile": 0.5,
                "tool_value_specificity_z": 0.0,
            }
        )

    summary = summarize_stochastic_rows(rows, n_boot=200)

    assert summary["groups"]["alias_stochastic_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["alias_visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_alias_stochastic_bottleneck"]["gate"]["pass"]


def test_summarize_stochastic_rows_fails_when_success_repair_is_not_noop():
    rows = [
        {
            "condition": "stochastic_failure_bottleneck",
            "architecture": "transformer",
            "critical_slot": seed % 4,
            "closed_loop_final_accuracy": 1.0,
            "teacher_forced_final_accuracy": 1.0,
            "first_field_accuracy": 1.0,
            "first_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 1.0,
            "first_parsed_value_accuracy": 1.0,
            "repair_field_accuracy": 1.0,
            "repair_schema_validity": 1.0,
            "repair_failed_field_accuracy": 1.0,
            "repair_failed_schema_validity": 1.0,
            "repair_failed_parsed_slot_accuracy": 1.0,
            "repair_failed_parsed_value_accuracy": 1.0,
            "repair_success_noop_field_accuracy": 0.4,
            "repair_success_schema_validity": 1.0,
            "sampled_failure_rate": 0.5,
            "memory_specificity_z": 1.5,
            "memory_rank_percentile": 0.875,
            "tool_value_specificity_z": 1.2,
        }
        for seed in range(8)
    ]

    summary = summarize_stochastic_rows(rows, n_boot=200)
    group = summary["groups"]["stochastic_failure_bottleneck/transformer"]

    assert not group["gate"]["repair_success_noop_field_acc_ge_0_90"]
    assert not group["gate"]["pass"]
