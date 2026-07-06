import json
from typing import Optional

import pytest

from experiments.long_horizon_bottleneck.core import (
    alias_argument_id,
    alias_argument_vocab_size,
    build_cells,
    build_horizon_cells,
    estimate_modal_cost,
    generated_json_call_token_ids,
    generated_json_noop_token_ids,
    generated_json_sequence_length,
    generated_json_vocab_size,
    multifield_call_tokens,
    multifield_malformed_tokens,
    multifield_noop_tokens,
    multifield_vocab_sizes,
    parse_prompt_json_action,
    parse_generated_json_tokens,
    parse_multifield_action,
    parse_text_argument,
    parse_alias_argument,
    parse_structured_action,
    PROMPT_JSON_LOCALIZATION_POSITIONS,
    render_text_argument,
    render_generated_json_tokens,
    render_multifield_action,
    render_structured_action,
    structured_action_vocab_size,
    structured_call_action_id,
    structured_malformed_action_id,
    structured_noop_action_id,
    summarize_rows,
    summarize_recovery_rows,
    summarize_multifield_rows,
    summarize_prompt_causal_patch_rows,
    summarize_prompt_family_causal_patch_rows,
    summarize_prompt_localization_rows,
    summarize_prompt_transfer_rows,
    summarize_structured_rows,
    summarize_stochastic_rows,
    summarize_tool_rows,
    text_argument_id,
    text_argument_vocab_size,
)
from experiments.long_horizon_bottleneck.api_blackbox import (
    API_BLACKBOX_CONDITIONS,
    ProviderResult,
    build_api_benchmark_cases,
    evaluate_api_cases,
    make_provider_call,
    summarize_api_blackbox_rows,
    total_request_count,
)
from experiments.long_horizon_bottleneck.api_dispatch_characterization import (
    DISPATCH_CHARACTERIZATION_CASE_TYPES,
    build_dispatch_characterization_cases,
    evaluate_dispatch_characterization_cases,
    render_dispatch_characterization_markdown,
    summarize_dispatch_characterization_rows,
    summarize_dispatch_robustness,
    total_request_count as total_dispatch_characterization_request_count,
)
from experiments.long_horizon_bottleneck.api_blackbox_report import (
    aggregate_api_blackbox_summaries,
    render_api_blackbox_markdown,
)
from experiments.long_horizon_bottleneck.prompt_json_tasks import API_PROMPT_FAMILIES, prompt_family_user_prompt


def test_budget_guard_keeps_default_l4_sweep_well_under_1000():
    est = estimate_modal_cost(
        cells=128,
        gpu="L4",
        timeout_seconds=900,
        budget_usd=1000,
    )

    assert est.within_budget
    assert est.conservative_cost_usd < 40


def test_prompt_hidden_localization_default_budget_stays_under_25():
    est = estimate_modal_cost(
        cells=3,
        gpu="L4",
        timeout_seconds=7200,
        budget_usd=25,
    )

    assert est.within_budget
    assert est.conservative_cost_usd < 10


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


def test_text_argument_surface_renders_and_parses_phrase_variants():
    n_slots = 4
    variants_per_slot = 3

    assert text_argument_vocab_size(n_slots, variants_per_slot) == 14
    phrase_ids = [
        text_argument_id(slot=1, variant_index=variant, n_slots=n_slots, variants_per_slot=variants_per_slot)
        for variant in range(variants_per_slot)
    ]
    phrases = [render_text_argument(argument_id, n_slots, variants_per_slot) for argument_id in phrase_ids]

    assert phrases == ["clue_1", "second clue", "memory slot 1"]
    for variant, phrase in enumerate(phrases):
        parsed = parse_text_argument(phrase, n_slots, variants_per_slot)
        assert parsed["slot"] == 1
        assert parsed["variant_index"] == variant
        assert parsed["valid"]
        assert not parsed["missing"]

    assert parse_text_argument("none", n_slots, variants_per_slot) == {
        "slot": None,
        "variant_index": None,
        "valid": True,
        "missing": True,
        "reason": None,
    }
    malformed = parse_text_argument("clue-nonesuch", n_slots, variants_per_slot)
    assert malformed == {
        "slot": None,
        "variant_index": None,
        "valid": False,
        "missing": False,
        "reason": "unparsed_text_argument",
    }
    with pytest.raises(ValueError, match="argument_id"):
        render_text_argument(text_argument_vocab_size(n_slots, variants_per_slot), n_slots, variants_per_slot)


def test_generated_json_surface_renders_and_parses_token_sequences():
    n_slots = 4
    variants_per_slot = 3

    assert generated_json_sequence_length() == 13
    assert generated_json_vocab_size(n_slots, variants_per_slot) == 13 + text_argument_vocab_size(
        n_slots,
        variants_per_slot,
    )

    call_tokens = generated_json_call_token_ids(
        slot=1,
        variant_index=1,
        value=0,
        n_slots=n_slots,
        variants_per_slot=variants_per_slot,
    )
    rendered_call = render_generated_json_tokens(call_tokens, n_slots, variants_per_slot)
    parsed_call = parse_generated_json_tokens(call_tokens, n_slots, variants_per_slot)

    assert "second clue" in rendered_call
    assert parsed_call == {
        "opcode": "call",
        "slot": 1,
        "variant_index": 1,
        "value": 0,
        "valid": True,
        "executable": True,
        "reason": None,
        "text": rendered_call,
    }

    noop_tokens = generated_json_noop_token_ids(n_slots, variants_per_slot)
    parsed_noop = parse_generated_json_tokens(noop_tokens, n_slots, variants_per_slot)
    assert parsed_noop["opcode"] == "noop"
    assert parsed_noop["valid"] and not parsed_noop["executable"]

    malformed_tokens = list(call_tokens)
    malformed_tokens[3] = generated_json_noop_token_ids(n_slots, variants_per_slot)[3]
    parsed_malformed = parse_generated_json_tokens(malformed_tokens, n_slots, variants_per_slot)
    assert parsed_malformed["opcode"] == "malformed"
    assert not parsed_malformed["valid"]
    assert parsed_malformed["reason"] == "malformed_order"


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


def test_summarize_stochastic_rows_supports_text_argument_conditions():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "text_stochastic_bottleneck",
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
                "condition": "text_visible_control",
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

    assert summary["groups"]["text_stochastic_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["text_visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_text_stochastic_bottleneck"]["gate"]["pass"]


def test_summarize_stochastic_rows_supports_generated_json_conditions():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "generated_json_bottleneck",
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
                "condition": "generated_json_visible_control",
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

    assert summary["groups"]["generated_json_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["generated_json_visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_generated_json_bottleneck"]["gate"]["pass"]


def test_summarize_stochastic_rows_supports_autoregressive_json_conditions():
    rows = []
    for seed in range(8):
        rows.append(
            {
                "condition": "autoregressive_json_bottleneck",
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
                "condition": "autoregressive_json_visible_control",
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

    assert summary["groups"]["autoregressive_json_bottleneck/transformer"]["gate"]["pass"]
    assert summary["groups"]["autoregressive_json_visible_control/transformer"]["gate"]["pass"]
    assert summary["pooled_autoregressive_json_bottleneck"]["gate"]["pass"]


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


def test_parse_prompt_json_action_accepts_embedded_tool_call():
    parsed = parse_prompt_json_action(
        'Action: {"tool": "read_slot", "slot": "second clue", "value": "0"}',
        n_slots=4,
        variants_per_slot=3,
    )
    underscore = parse_prompt_json_action(
        '{"tool": "read_slot", "slot": "second_clue", "value": 0}',
        n_slots=4,
        variants_per_slot=3,
    )

    assert parsed["opcode"] == "call"
    assert parsed["slot"] == 1
    assert parsed["variant_index"] == 1
    assert parsed["value"] == 0
    assert parsed["valid"]
    assert parsed["executable"]
    assert underscore["slot"] == 1
    assert underscore["valid"]


def test_parse_prompt_json_action_accepts_noop_and_rejects_malformed_text():
    noop = parse_prompt_json_action(
        '```json\n{"tool": "noop"}\n```',
        n_slots=4,
        variants_per_slot=3,
    )
    malformed = parse_prompt_json_action(
        "I will inspect the clue without JSON.",
        n_slots=4,
        variants_per_slot=3,
    )

    assert noop["opcode"] == "noop"
    assert noop["valid"]
    assert not noop["executable"]
    assert malformed["opcode"] == "malformed"
    assert not malformed["valid"]
    assert malformed["reason"] == "missing_json_object"


def test_prompt_family_user_prompt_supports_public_api_families():
    bits = [0, 1, 0, 1]

    prompts = [
        prompt_family_user_prompt(family, bits, critical_slot=1, n_slots=4, slot_gap=4, variants_per_slot=3)
        for family in API_PROMPT_FAMILIES
    ]

    assert all("Allowed slot phrases" in prompt for prompt in prompts)
    assert any("API dispatch" in prompt for prompt in prompts)
    with pytest.raises(ValueError, match="Unknown prompt family"):
        prompt_family_user_prompt("unknown", bits, critical_slot=1, n_slots=4, slot_gap=4, variants_per_slot=3)


def test_build_api_benchmark_cases_tracks_request_count_with_repairs():
    cases = build_api_benchmark_cases(
        suite="prompt_family",
        prompt_families=["standard", "compact"],
        conditions=list(API_BLACKBOX_CONDITIONS),
        seeds=1,
        episodes_per_cell=1,
        critical_slots=[0, 1, 2, 3],
        n_slots_values=[4],
        slot_gap_values=[8],
        variants_per_slot=3,
        base_seed=20261050,
    )

    assert len(cases) == 2 * len(API_BLACKBOX_CONDITIONS) * 4
    assert total_request_count(cases) == 2 * 4 * 6
    assert {case.prompt_family for case in cases} == {"standard", "compact"}


def test_summarize_api_blackbox_rows_classifies_fixture_positive():
    cases = build_api_benchmark_cases(
        suite="prompt_family",
        prompt_families=["standard"],
        conditions=list(API_BLACKBOX_CONDITIONS),
        seeds=1,
        episodes_per_cell=2,
        critical_slots=[0],
        n_slots_values=[4],
        slot_gap_values=[8],
        variants_per_slot=3,
        base_seed=20261050,
    )
    provider = make_provider_call(provider="fixture", model="fixture-perfect")

    rows = evaluate_api_cases(
        cases,
        model="fixture-perfect",
        provider_name="fixture",
        provider_call=provider,
        include_prompts=False,
    )
    summary = summarize_api_blackbox_rows(rows)

    assert summary["outcome"] == "positive"
    assert summary["decision"]["controls_pass"]
    assert summary["decision"]["bottleneck_pass"]


def test_summarize_api_blackbox_rows_classifies_controlled_strong_negative():
    cases = build_api_benchmark_cases(
        suite="prompt_family",
        prompt_families=["standard"],
        conditions=list(API_BLACKBOX_CONDITIONS),
        seeds=1,
        episodes_per_cell=2,
        critical_slots=[1],
        n_slots_values=[4],
        slot_gap_values=[8],
        variants_per_slot=3,
        base_seed=20261050,
    )
    provider = make_provider_call(provider="fixture_wrong_bottleneck", model="fixture-wrong")

    rows = evaluate_api_cases(
        cases,
        model="fixture-wrong",
        provider_name="fixture_wrong_bottleneck",
        provider_call=provider,
        include_prompts=False,
    )
    summary = summarize_api_blackbox_rows(rows)

    assert summary["outcome"] == "strong_negative"
    assert summary["decision"]["controls_pass"]
    assert not summary["decision"]["bottleneck_pass"]


def test_aggregate_api_blackbox_summaries_preserves_failed_cells(tmp_path):
    positive_path = tmp_path / "positive.json"
    negative_path = tmp_path / "negative.json"
    positive_path.write_text(
        json.dumps(_api_summary_payload(suite="prompt_family", outcome="positive")),
        encoding="utf-8",
    )
    negative_path.write_text(
        json.dumps(_api_summary_payload(suite="external_stress", outcome="strong_negative", failed=True)),
        encoding="utf-8",
    )

    aggregate = aggregate_api_blackbox_summaries([positive_path, negative_path])
    markdown = render_api_blackbox_markdown(aggregate, report_date="2026-07-06")

    assert aggregate["n_summaries"] == 2
    assert aggregate["total_rows"] == 8
    assert aggregate["total_request_budget"] == 12
    assert aggregate["suite_outcomes"]["prompt_family"]["all_positive"]
    assert aggregate["suite_outcomes"]["external_stress"]["any_strong_negative"]
    assert aggregate["failed_cells"][0]["prompt_family"] == "dispatch"
    assert aggregate["failed_cells"][0]["controls_pass"]
    assert not aggregate["failed_cells"][0]["bottleneck_pass"]
    assert "mixed with controlled strong negative" in markdown
    assert "dispatch" in markdown


def test_build_dispatch_characterization_cases_targets_failed_seed_blocks():
    cases = build_dispatch_characterization_cases(
        stress_cases=["4slot_gap8", "8slot_gap16"],
        case_types=list(DISPATCH_CHARACTERIZATION_CASE_TYPES),
        seeds=1,
        episodes_per_cell=1,
        critical_slot=0,
        n_slots_values=[4, 8],
        slot_gap_values=[8, 16],
        variants_per_slot=3,
        base_seed=20261050,
    )

    original_seeds = {
        (case.stress_case, case.seed) for case in cases if case.case_type == "dispatch_original"
    }

    assert len(cases) == 2 * len(DISPATCH_CHARACTERIZATION_CASE_TYPES)
    assert total_dispatch_characterization_request_count(cases) == 30
    assert original_seeds == {
        ("4slot_gap8", 50661050),
        ("8slot_gap16", 53661050),
    }


def test_dispatch_characterization_summary_localizes_reproduced_failure():
    cases = build_dispatch_characterization_cases(
        stress_cases=["4slot_gap8"],
        case_types=list(DISPATCH_CHARACTERIZATION_CASE_TYPES),
        seeds=1,
        episodes_per_cell=1,
        critical_slot=0,
        n_slots_values=[4],
        slot_gap_values=[8],
        variants_per_slot=3,
        base_seed=20261050,
    )

    def provider(
        _messages: list[dict[str, str]],
        case,
        phase: str,
    ) -> ProviderResult:
        if phase == "repair_success" or case.condition in {
            "prompt_json_format_control",
            "prompt_json_visible_control",
        }:
            return ProviderResult(text='{"tool":"noop"}', usage={"fixture": True})
        value = 1 - case.expected_value if case.case_type == "dispatch_original" else case.expected_value
        text = f'{{"tool":"read_slot","slot":"clue_{case.critical_slot}","value":{value}}}'
        return ProviderResult(text=text, usage={"fixture": True})

    rows = evaluate_dispatch_characterization_cases(
        cases,
        model="fixture-dispatch",
        provider_name="fixture",
        provider_call=provider,
        include_prompts=False,
    )
    summary = summarize_dispatch_characterization_rows(rows)
    markdown = render_dispatch_characterization_markdown(
        {"manifest": {"n_requests": total_dispatch_characterization_request_count(cases)}, "summary": summary}
    )
    cell = next(iter(summary["cells"].values()))

    assert summary["outcome"] == "localized"
    assert summary["decision"]["controls_pass"]
    assert summary["decision"]["original_failure_reproduced"]
    assert summary["decision"]["not_reproduced_cells"] == 0
    assert not cell["original_pass"]
    assert cell["wording_neutral_pass"]
    assert cell["copy_assisted_pass"]
    assert cell["repair_hinted_pass"]
    assert "dispatch wording/surface" in cell["diagnosis"]
    assert "value-copy pressure" in cell["diagnosis"]
    assert "repair-memory pressure" in cell["diagnosis"]
    assert "Diagnostic Matrix" in markdown


def test_dispatch_characterization_summary_keeps_critical_slots_separate():
    cases = []
    for critical_slot in [0, 1]:
        cases.extend(
            build_dispatch_characterization_cases(
                stress_cases=["4slot_gap8"],
                case_types=list(DISPATCH_CHARACTERIZATION_CASE_TYPES),
                seeds=1,
                episodes_per_cell=1,
                critical_slot=critical_slot,
                n_slots_values=[4],
                slot_gap_values=[8],
                variants_per_slot=3,
                base_seed=20261050,
            )
        )

    def provider(
        _messages: list[dict[str, str]],
        case,
        phase: str,
    ) -> ProviderResult:
        if phase == "repair_success" or case.condition in {
            "prompt_json_format_control",
            "prompt_json_visible_control",
        }:
            return ProviderResult(text='{"tool":"noop"}', usage={"fixture": True})
        value = (
            1 - case.expected_value
            if case.case_type == "dispatch_original" and case.critical_slot == 0
            else case.expected_value
        )
        text = f'{{"tool":"read_slot","slot":"clue_{case.critical_slot}","value":{value}}}'
        return ProviderResult(text=text, usage={"fixture": True})

    rows = evaluate_dispatch_characterization_cases(
        cases,
        model="fixture-dispatch",
        provider_name="fixture",
        provider_call=provider,
        include_prompts=False,
    )
    summary = summarize_dispatch_characterization_rows(rows)

    assert len(summary["cells"]) == 2
    robustness = summarize_dispatch_robustness(summary)

    assert robustness["outcome"] == "broad_reproduced_localized"
    assert robustness["original_failure_cells"] == 1
    assert robustness["controls_passing_cells"] == 2
    assert summary["decision"]["localized_cells"] == 1
    assert summary["decision"]["not_reproduced_cells"] == 1
    assert {cell["critical_slot"] for cell in summary["cells"].values()} == {0, 1}


def _api_summary_payload(*, suite: str, outcome: str, failed: bool = False) -> dict:
    cell_key = f"{suite}/4slot_gap8/test-provider/test-model/dispatch/4slot/gap8"
    return {
        "manifest": {
            "suite": suite,
            "provider": "test-provider",
            "models": ["test-model"],
            "n_requests": 6,
            "prompt_families": ["dispatch"],
            "stress_cases": ["4slot_gap8"],
        },
        "summary": {
            "outcome": outcome,
            "n_rows": 4,
            "cells": {
                cell_key: {
                    "suite": suite,
                    "stress_case": "4slot_gap8",
                    "provider": "test-provider",
                    "model": "test-model",
                    "prompt_family": "dispatch",
                    "n_slots": 4,
                    "slot_gap": 8,
                    "complete": True,
                    "controls_pass": True,
                    "bottleneck_pass": not failed,
                    "pass": not failed,
                    "condition_gates": {
                        "prompt_json_format_control": True,
                        "prompt_json_visible_control": True,
                        "prompt_json_short_horizon_control": True,
                        "prompt_json_bottleneck": not failed,
                    },
                }
            },
        },
    }


def test_summarize_prompt_transfer_rows_classifies_positive_outcome():
    rows = _prompt_transfer_rows(
        bottleneck={
            "closed_loop_final_accuracy": 0.9,
            "first_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 0.9,
            "first_parsed_value_accuracy": 0.9,
            "repair_failed_schema_validity": 1.0,
            "repair_failed_parsed_slot_accuracy": 0.9,
            "repair_failed_parsed_value_accuracy": 0.9,
            "repair_success_noop_field_accuracy": 0.9,
            "repair_success_schema_validity": 1.0,
            "memory_specificity_z": 1.25,
            "memory_rank_percentile": 0.75,
        },
        visible={
            "closed_loop_final_accuracy": 1.0,
            "first_schema_validity": 1.0,
            "first_noop_field_accuracy": 1.0,
            "memory_specificity_z": 0.0,
        },
        format_control={"schema_validity": 1.0},
        short_control={
            "closed_loop_final_accuracy": 1.0,
            "first_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 1.0,
            "first_parsed_value_accuracy": 1.0,
        },
    )

    summary = summarize_prompt_transfer_rows(rows, n_boot=200)

    assert summary["outcome"] == "positive"
    assert summary["decision"]["positive"]
    assert summary["groups"]["prompt_json_bottleneck/qwen2.5-0.5b"]["gate"]["pass"]


def test_summarize_prompt_transfer_rows_classifies_controlled_strong_negative():
    rows = _prompt_transfer_rows(
        bottleneck={
            "closed_loop_final_accuracy": 0.2,
            "first_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 0.2,
            "first_parsed_value_accuracy": 0.2,
            "repair_failed_schema_validity": 1.0,
            "repair_failed_parsed_slot_accuracy": 0.2,
            "repair_failed_parsed_value_accuracy": 0.2,
            "repair_success_noop_field_accuracy": 0.9,
            "repair_success_schema_validity": 1.0,
            "memory_specificity_z": 0.0,
            "memory_rank_percentile": 0.25,
        },
        visible={
            "closed_loop_final_accuracy": 1.0,
            "first_schema_validity": 1.0,
            "first_noop_field_accuracy": 1.0,
            "memory_specificity_z": 0.0,
        },
        format_control={"schema_validity": 1.0},
        short_control={
            "closed_loop_final_accuracy": 1.0,
            "first_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 1.0,
            "first_parsed_value_accuracy": 1.0,
        },
    )

    summary = summarize_prompt_transfer_rows(rows, n_boot=200)

    assert summary["outcome"] == "strong_negative"
    assert summary["decision"]["controls_pass"]
    assert not summary["decision"]["positive"]


def test_summarize_prompt_localization_rows_classifies_positive_site():
    rows = _prompt_localization_rows(
        localization={
            "memory_specificity_z": 1.1,
            "memory_rank_percentile": 0.75,
        }
    )

    summary = summarize_prompt_localization_rows(rows, n_boot=200)
    transfer_summary = summarize_prompt_transfer_rows(rows, n_boot=200)

    assert summary["outcome"] == "positive"
    assert summary["decision"]["controls_pass"]
    assert summary["decision"]["behavior_bottleneck_pass"]
    assert summary["decision"]["localization_pass"]
    assert summary["localization_groups"]["qwen2.5-0.5b/generated_first/mid"]["gate"]["pass"]
    assert transfer_summary["n_rows"] == 40


def test_prompt_localization_positions_include_fixed_action_counterfactual_sites():
    assert {"fixed_noop_first", "fixed_noop_final", "fixed_read_first", "fixed_read_final"}.issubset(
        set(PROMPT_JSON_LOCALIZATION_POSITIONS)
    )

    rows = _prompt_localization_rows(
        localization={
            "memory_specificity_z": 1.1,
            "memory_rank_percentile": 0.75,
        },
        hidden_position="fixed_noop_final",
    )

    summary = summarize_prompt_localization_rows(rows, n_boot=200)

    assert summary["outcome"] == "positive"
    assert summary["localization_groups"]["qwen2.5-0.5b/fixed_noop_final/mid"]["gate"]["pass"]


def test_summarize_prompt_causal_patch_rows_classifies_positive_patch_site():
    rows = _prompt_causal_patch_rows(patch_effect=1.2, patch_direction_success=1.0)

    summary = summarize_prompt_causal_patch_rows(rows, n_boot=200)

    assert summary["outcome"] == "positive"
    assert summary["decision"]["causal_ready"]
    assert summary["decision"]["patch_pass"]
    assert summary["groups"]["qwen2.5-0.5b/value_prefix_final/final"]["gate"]["pass"]


def test_summarize_prompt_causal_patch_rows_classifies_strong_negative_patch_site():
    rows = _prompt_causal_patch_rows(patch_effect=0.0, patch_direction_success=0.0)

    summary = summarize_prompt_causal_patch_rows(rows, n_boot=200)

    assert summary["outcome"] == "strong_negative"
    assert summary["decision"]["causal_ready"]
    assert not summary["decision"]["patch_pass"]
    assert not summary["decision"]["positive"]


def test_summarize_prompt_family_causal_patch_rows_requires_each_family_model_pair():
    rows = [
        *_prompt_causal_patch_rows(patch_effect=1.2, patch_direction_success=1.0, prompt_family="standard"),
        *_prompt_causal_patch_rows(patch_effect=1.1, patch_direction_success=1.0, prompt_family="compact"),
    ]

    summary = summarize_prompt_family_causal_patch_rows(rows, n_boot=200)

    assert summary["outcome"] == "positive"
    assert summary["decision"]["all_family_models_causal_ready"]
    assert summary["decision"]["all_family_models_patch_pass"]
    assert summary["family_model"]["standard/qwen2.5-0.5b"]["patch_pass"]
    assert summary["family_model"]["compact/qwen2.5-0.5b"]["patch_pass"]


def test_summarize_prompt_family_causal_patch_rows_fails_when_one_family_model_misses_patch():
    rows = [
        *_prompt_causal_patch_rows(patch_effect=1.2, patch_direction_success=1.0, prompt_family="standard"),
        *_prompt_causal_patch_rows(patch_effect=0.0, patch_direction_success=0.0, prompt_family="ledger"),
    ]

    summary = summarize_prompt_family_causal_patch_rows(rows, n_boot=200)

    assert summary["outcome"] == "strong_negative"
    assert summary["decision"]["all_family_models_causal_ready"]
    assert not summary["decision"]["all_family_models_patch_pass"]
    assert not summary["family_model"]["ledger/qwen2.5-0.5b"]["patch_pass"]


def test_summarize_prompt_localization_rows_classifies_hidden_strong_negative():
    rows = _prompt_localization_rows(
        localization={
            "memory_specificity_z": 0.0,
            "memory_rank_percentile": 0.5,
        }
    )

    summary = summarize_prompt_localization_rows(rows, n_boot=200)

    assert summary["outcome"] == "strong_negative"
    assert summary["decision"]["controls_pass"]
    assert summary["decision"]["behavior_bottleneck_pass"]
    assert not summary["decision"]["localization_pass"]
    assert not summary["decision"]["positive"]


def test_summarize_prompt_localization_rows_is_inconclusive_when_controls_fail():
    rows = _prompt_localization_rows(
        localization={
            "memory_specificity_z": 1.1,
            "memory_rank_percentile": 0.75,
        },
        format_control={"schema_validity": 0.0},
    )

    summary = summarize_prompt_localization_rows(rows, n_boot=200)

    assert summary["outcome"] == "inconclusive"
    assert not summary["decision"]["controls_pass"]
    assert not summary["decision"]["positive"]


def _prompt_localization_rows(
    *,
    localization: dict[str, float],
    format_control: Optional[dict[str, float]] = None,
    hidden_position: str = "generated_first",
) -> list[dict[str, object]]:
    rows = _prompt_transfer_rows(
        bottleneck={
            "closed_loop_final_accuracy": 0.9,
            "first_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 0.9,
            "first_parsed_value_accuracy": 0.9,
            "repair_failed_schema_validity": 1.0,
            "repair_failed_parsed_slot_accuracy": 0.9,
            "repair_failed_parsed_value_accuracy": 0.9,
            "repair_success_noop_field_accuracy": 0.9,
            "repair_success_schema_validity": 1.0,
        },
        visible={
            "closed_loop_final_accuracy": 1.0,
            "first_schema_validity": 1.0,
            "first_noop_field_accuracy": 1.0,
            "memory_specificity_z": 0.0,
        },
        format_control=format_control or {"schema_validity": 1.0},
        short_control={
            "closed_loop_final_accuracy": 1.0,
            "first_schema_validity": 1.0,
            "first_parsed_slot_accuracy": 1.0,
            "first_parsed_value_accuracy": 1.0,
        },
    )
    for seed in range(10):
        rows.append(
            {
                "row_kind": "hidden_localization",
                "condition": "prompt_json_bottleneck",
                "architecture": "qwen2.5-0.5b",
                "model": "qwen2.5-0.5b",
                "critical_slot": seed % 4,
                "seed": seed,
                "hidden_position": hidden_position,
                "hidden_layer": "mid",
                "hidden_layer_index": 12,
                "memory_specificity_z": localization["memory_specificity_z"],
                "memory_rank_percentile": localization["memory_rank_percentile"],
            }
        )
    return rows


def _prompt_causal_patch_rows(
    *,
    patch_effect: float,
    patch_direction_success: float,
    prompt_family: str = "standard",
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in range(12):
        rows.append(
            {
                "row_kind": "causal_patch",
                "architecture": "qwen2.5-0.5b",
                "model": "qwen2.5-0.5b",
                "prompt_family": prompt_family,
                "critical_slot": seed % 4,
                "seed": seed,
                "patch_position": "value_prefix_final",
                "patch_layer": "final",
                "patch_layer_index": 24,
                "clean_margin": 1.0,
                "corrupted_margin": -1.0,
                "patched_margin": -1.0 + patch_effect,
                "patch_effect": patch_effect,
                "patch_recovery": patch_effect / 2.0,
                "patch_direction_success": patch_direction_success,
            }
        )
    return rows


def _prompt_transfer_rows(
    *,
    bottleneck: dict[str, float],
    visible: dict[str, float],
    format_control: dict[str, float],
    short_control: dict[str, float],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seed in range(10):
        base = {
            "architecture": "qwen2.5-0.5b",
            "critical_slot": seed % 4,
            "seed": seed,
            "schema_validity": float("nan"),
            "sampled_failure_rate": 0.5,
            "tool_value_specificity_z": 0.0,
        }
        rows.append({**base, "condition": "prompt_json_bottleneck", **bottleneck})
        rows.append({**base, "condition": "prompt_json_visible_control", **visible})
        rows.append({**base, "condition": "prompt_json_format_control", **format_control})
        rows.append({**base, "condition": "prompt_json_short_horizon_control", **short_control})
    return rows
