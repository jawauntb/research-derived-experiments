#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Prompt JSON hidden-localization replication sweep on cheap Modal L4 workers.

This follow-up directly probes the limiting gate from the prompt JSON transfer
run: final-prompt-token hidden specificity did not replicate, despite passing
prompt-level behavior. The sweep preserves format, visible, short-horizon, and
behavioral moved-bottleneck gates, then measures hidden sensitivity at multiple
token positions and layers.

The runner also supports fixed-action counterfactual positions. These
teacher-force a constant assistant JSON action under the base and slot-flipped
prompts, then measure whether hidden localization survives without varying the
generated answer tokens.

Recommended dry run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_prompt_json_hidden_localization_sweep.py \\
        --dry-run-budget --budget-usd 25

Recommended confirmatory run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_prompt_json_hidden_localization_sweep.py \\
        --models Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct \\
        --seeds 4 --episodes-per-cell 8 --hidden-metric-episodes 2 \\
        --critical-slots 0,1,2,3 --budget-usd 25 \\
        --out artifacts/long_horizon_bottleneck/prompt_json_hidden_localization_l4.json

Recommended fixed-action counterfactual run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_prompt_json_hidden_localization_sweep.py \\
        --models Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct \\
        --seeds 4 --episodes-per-cell 8 --hidden-metric-episodes 2 \\
        --critical-slots 0,1,2,3 \\
        --hidden-positions prompt_final,fixed_noop_first,fixed_noop_final,fixed_read_first,fixed_read_final \\
        --budget-usd 25 --base-seed 20260900 \\
        --out artifacts/long_horizon_bottleneck/prompt_json_fixed_action_localization_l4.json
"""

from __future__ import annotations

import importlib
import json
import math
import random
import time
from pathlib import Path
from typing import Any

from experiments.long_horizon_bottleneck.prompt_json_tasks import (
    bottleneck_user_prompt,
    call_correct,
    compact_parsed,
    encode_messages,
    episode_bits,
    failure_flags,
    format_user_prompt,
    generate_action,
    mean,
    messages,
    repair_messages,
    short_user_prompt,
    slot_phrase,
    visible_user_prompt,
)

modal = importlib.import_module("modal")

GPU = "L4"
MAX_CONTAINERS = 3
TIMEOUT_SECONDS = 7200
HF_CACHE_DIR = "/cache/huggingface"

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.47,<4.55",
    "accelerate>=0.33,<1.0",
    "sentencepiece>=0.2,<0.3",
    "safetensors>=0.4,<0.6",
).add_local_python_source("experiments")
HF_CACHE = modal.Volume.from_name("research-derived-hf-cache", create_if_missing=True)
app = modal.App(name="research-derived-prompt-json-hidden-localization")


def _resolve_layer_specs(layer_names: list[str], n_layers: int) -> list[dict[str, int | str]]:
    if n_layers <= 0:
        raise ValueError(f"n_layers must be positive, got {n_layers}")
    aliases = {
        "early": max(1, n_layers // 4),
        "mid": max(1, n_layers // 2),
        "late": max(1, (3 * n_layers) // 4),
        "final": n_layers,
    }
    specs: list[dict[str, int | str]] = []
    seen: set[tuple[str, int]] = set()
    for raw_name in layer_names:
        name = raw_name.strip()
        if not name:
            continue
        lowered = name.lower()
        if lowered in aliases:
            label = lowered
            index = aliases[lowered]
        elif lowered.startswith("layer_") and lowered.removeprefix("layer_").lstrip("-").isdigit():
            index = int(lowered.removeprefix("layer_"))
            label = f"layer_{index}"
        elif lowered.lstrip("-").isdigit():
            index = int(lowered)
            label = f"layer_{index}"
        else:
            known = ", ".join(sorted(aliases))
            raise ValueError(f"Unknown hidden layer spec {name!r}. Use {known} or an integer index.")
        if index < 0:
            index = n_layers + 1 + index
            label = f"layer_{index}"
        if not 0 <= index <= n_layers:
            raise ValueError(f"Hidden layer index {index} outside hidden_states range 0..{n_layers}")
        key = (label, index)
        if key not in seen:
            specs.append({"label": label, "index": index})
            seen.add(key)
    if not specs:
        raise ValueError("At least one hidden layer spec is required")
    return specs


def _fixed_action_texts(critical_slot: int, variants_per_slot: int) -> dict[str, str]:
    phrase = slot_phrase(critical_slot, variants_per_slot)
    return {
        "fixed_noop": '{"tool":"noop"}',
        "fixed_read": f'{{"tool":"read_slot","slot":"{phrase}","value":0}}',
    }


def _manual_chat_text(message_list: list[dict[str, str]], *, add_generation_prompt: bool) -> str:
    text = "\n\n".join(f"{message['role'].title()}: {message['content']}" for message in message_list)
    if add_generation_prompt:
        text += "\n\nAssistant:"
    return text


def _chat_text(tokenizer: Any, message_list: list[dict[str, str]], *, add_generation_prompt: bool) -> str:
    if getattr(tokenizer, "chat_template", None):
        return str(
            tokenizer.apply_chat_template(
                message_list,
                add_generation_prompt=add_generation_prompt,
                tokenize=False,
            )
        )
    return _manual_chat_text(message_list, add_generation_prompt=add_generation_prompt)


def _fixed_action_encoding_and_indices(
    tokenizer: Any,
    message_list: list[dict[str, str]],
    action_text: str,
    device: Any,
) -> tuple[dict[str, Any], list[int]]:
    import torch

    prompt_text = _chat_text(tokenizer, message_list, add_generation_prompt=True)
    if getattr(tokenizer, "chat_template", None):
        full_text = _chat_text(
            tokenizer,
            [*message_list, {"role": "assistant", "content": action_text}],
            add_generation_prompt=False,
        )
    else:
        full_text = f"{prompt_text}{action_text}"

    action_start = full_text.find(action_text, max(0, len(prompt_text) - 16))
    if action_start < 0:
        action_start = full_text.rfind(action_text)
    if action_start < 0:
        raise ValueError("Could not locate fixed assistant action text in rendered chat template")
    action_end = action_start + len(action_text)

    try:
        encoded = tokenizer(
            full_text,
            return_tensors="pt",
            return_offsets_mapping=True,
            add_special_tokens=False,
        )
        offsets = encoded.pop("offset_mapping")[0].tolist()
        action_indices = [
            index
            for index, (start, end) in enumerate(offsets)
            if end > action_start and start < action_end
        ]
        if not action_indices:
            raise ValueError("offset mapping did not identify fixed action tokens")
    except Exception:
        encoded = tokenizer(full_text, return_tensors="pt", add_special_tokens=False)
        prefix_encoded = tokenizer(full_text[:action_start], return_tensors="pt", add_special_tokens=False)
        action_encoded = tokenizer(action_text, return_tensors="pt", add_special_tokens=False)
        start_index = int(prefix_encoded["input_ids"].shape[-1])
        action_length = max(1, int(action_encoded["input_ids"].shape[-1]))
        end_index = min(start_index + action_length, int(encoded["input_ids"].shape[-1]))
        action_indices = list(range(start_index, end_index))
    if not action_indices:
        action_indices = [int(encoded["input_ids"].shape[-1]) - 1]

    model_inputs = {
        key: value.to(device)
        for key, value in encoded.items()
        if key != "offset_mapping"
    }
    if "attention_mask" not in model_inputs:
        model_inputs["attention_mask"] = torch.ones_like(model_inputs["input_ids"])
    return model_inputs, action_indices


def _fixed_action_hidden_vectors_by_site(
    model: Any,
    tokenizer: Any,
    message_list: list[dict[str, str]],
    *,
    action_prefix: str,
    action_text: str,
    positions: list[str],
    layer_specs: list[dict[str, int | str]],
) -> dict[tuple[str, str, int], Any]:
    import torch

    encoded, action_indices = _fixed_action_encoding_and_indices(tokenizer, message_list, action_text, model.device)
    position_indices = {
        f"{action_prefix}_first": action_indices[0],
        f"{action_prefix}_final": action_indices[-1],
    }
    with torch.inference_mode():
        outputs = model(
            input_ids=encoded["input_ids"],
            attention_mask=encoded["attention_mask"],
            output_hidden_states=True,
            use_cache=False,
        )

    vectors: dict[tuple[str, str, int], Any] = {}
    for position in positions:
        if position not in position_indices:
            known = ", ".join(sorted(position_indices))
            raise ValueError(f"Unknown fixed-action position {position!r}. Known positions: {known}")
        token_index = position_indices[position]
        for layer_spec in layer_specs:
            label = str(layer_spec["label"])
            layer_index = int(layer_spec["index"])
            vector = outputs.hidden_states[layer_index][0, token_index].detach().float().cpu()
            vectors[(position, label, layer_index)] = vector
    return vectors


def _hidden_vectors_by_site(
    model: Any,
    tokenizer: Any,
    message_list: list[dict[str, str]],
    *,
    critical_slot: int,
    variants_per_slot: int,
    positions: list[str],
    layer_specs: list[dict[str, int | str]],
    max_new_tokens: int,
) -> dict[tuple[str, str, int], Any]:
    import torch

    token_positions = [
        position
        for position in positions
        if position in {"prompt_final", "generated_first", "generated_final"}
    ]
    vectors: dict[tuple[str, str, int], Any] = {}
    if token_positions:
        encoded = encode_messages(tokenizer, message_list, model.device)
        input_len = int(encoded["input_ids"].shape[-1])
        needs_generation = any(position != "prompt_final" for position in token_positions)
        if needs_generation:
            with torch.inference_mode():
                input_ids = model.generate(
                    **encoded,
                    do_sample=False,
                    max_new_tokens=max_new_tokens,
                    pad_token_id=tokenizer.eos_token_id,
                )
            attention_mask = torch.ones_like(input_ids)
        else:
            input_ids = encoded["input_ids"]
            attention_mask = encoded["attention_mask"]

        generated_len = int(input_ids.shape[-1] - input_len)
        position_indices: dict[str, int] = {
            "prompt_final": input_len - 1,
            "generated_first": input_len if generated_len > 0 else input_len - 1,
            "generated_final": int(input_ids.shape[-1] - 1),
        }

        with torch.inference_mode():
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
                use_cache=False,
            )

        for position in token_positions:
            if position not in position_indices:
                known = ", ".join(sorted(position_indices))
                raise ValueError(f"Unknown hidden position {position!r}. Known positions: {known}")
            token_index = position_indices[position]
            for layer_spec in layer_specs:
                label = str(layer_spec["label"])
                layer_index = int(layer_spec["index"])
                vector = outputs.hidden_states[layer_index][0, token_index].detach().float().cpu()
                vectors[(position, label, layer_index)] = vector

    fixed_actions = _fixed_action_texts(critical_slot, variants_per_slot)
    for action_prefix, action_text in fixed_actions.items():
        fixed_positions = [
            position
            for position in positions
            if position in {f"{action_prefix}_first", f"{action_prefix}_final"}
        ]
        if fixed_positions:
            vectors.update(
                _fixed_action_hidden_vectors_by_site(
                    model,
                    tokenizer,
                    message_list,
                    action_prefix=action_prefix,
                    action_text=action_text,
                    positions=fixed_positions,
                    layer_specs=layer_specs,
                )
            )

    missing_positions = [
        position
        for position in positions
        if all(key[0] != position for key in vectors)
    ]
    if missing_positions:
        known = (
            "prompt_final, generated_first, generated_final, "
            "fixed_noop_first, fixed_noop_final, fixed_read_first, fixed_read_final"
        )
        raise ValueError(f"Unknown hidden positions {missing_positions}. Known positions: {known}")
    return vectors


def _hidden_localization_sensitivity(
    model: Any,
    tokenizer: Any,
    rng: random.Random,
    critical_slot: int,
    *,
    n_slots: int,
    slot_gap: int,
    variants_per_slot: int,
    episodes: int,
    positions: list[str],
    layer_specs: list[dict[str, int | str]],
    max_new_tokens: int,
) -> list[dict[str, Any]]:
    import torch

    specificity_values: dict[tuple[str, str, int], list[float]] = {}
    rank_values: dict[tuple[str, str, int], list[float]] = {}
    site_keys = [
        (position, str(layer_spec["label"]), int(layer_spec["index"]))
        for position in positions
        for layer_spec in layer_specs
    ]
    for key in site_keys:
        specificity_values[key] = []
        rank_values[key] = []

    for _ in range(episodes):
        bits = episode_bits(rng, n_slots)
        base_prompt = bottleneck_user_prompt(bits, critical_slot, n_slots, slot_gap, variants_per_slot)
        base_vectors = _hidden_vectors_by_site(
            model,
            tokenizer,
            messages(base_prompt),
            critical_slot=critical_slot,
            variants_per_slot=variants_per_slot,
            positions=positions,
            layer_specs=layer_specs,
            max_new_tokens=max_new_tokens,
        )
        distances: dict[tuple[str, str, int], list[float]] = {key: [] for key in site_keys}
        for slot in range(n_slots):
            flipped = list(bits)
            flipped[slot] = 1 - flipped[slot]
            flipped_prompt = bottleneck_user_prompt(flipped, critical_slot, n_slots, slot_gap, variants_per_slot)
            flipped_vectors = _hidden_vectors_by_site(
                model,
                tokenizer,
                messages(flipped_prompt),
                critical_slot=critical_slot,
                variants_per_slot=variants_per_slot,
                positions=positions,
                layer_specs=layer_specs,
                max_new_tokens=max_new_tokens,
            )
            for key in site_keys:
                distance = torch.linalg.vector_norm(base_vectors[key] - flipped_vectors[key])
                distances[key].append(float(distance.item()))

        for key in site_keys:
            critical_distance = distances[key][critical_slot]
            other_distances = [value for slot, value in enumerate(distances[key]) if slot != critical_slot]
            if other_distances:
                other_mean = sum(other_distances) / len(other_distances)
                other_var = sum((value - other_mean) ** 2 for value in other_distances) / len(other_distances)
                specificity_values[key].append((critical_distance - other_mean) / math.sqrt(other_var + 1e-8))
            rank_values[key].append(sum(value <= critical_distance for value in distances[key]) / len(distances[key]))

    return [
        {
            "hidden_position": position,
            "hidden_layer": layer_label,
            "hidden_layer_index": layer_index,
            "memory_specificity_z": mean(specificity_values[(position, layer_label, layer_index)]),
            "memory_rank_percentile": mean(rank_values[(position, layer_label, layer_index)]),
        }
        for position, layer_label, layer_index in site_keys
    ]


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=4,
    memory=24576,
    max_containers=MAX_CONTAINERS,
    volumes={"/cache": HF_CACHE},
    retries=0,
)
def run_prompt_hidden_localization_model(arg: dict[str, Any]) -> list[dict[str, Any]]:
    import os

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers.utils import logging as hf_logging

    os.environ.setdefault("HF_HOME", HF_CACHE_DIR)
    os.environ.setdefault("TRANSFORMERS_CACHE", HF_CACHE_DIR)
    hf_logging.set_verbosity_error()

    model_id = str(arg["model_id"])
    n_slots = int(arg["n_slots"])
    slot_gap = int(arg["slot_gap"])
    variants_per_slot = int(arg["variants_per_slot"])
    episodes_per_cell = int(arg["episodes_per_cell"])
    hidden_metric_episodes = int(arg["hidden_metric_episodes"])
    max_new_tokens = int(arg["max_new_tokens"])
    failure_probability = float(arg["failure_probability"])
    base_seed = int(arg["base_seed"])
    seeds = [int(seed) for seed in arg["seeds"]]
    critical_slots = [int(slot) for slot in arg["critical_slots"]]
    conditions = [str(condition) for condition in arg["conditions"]]
    hidden_positions = [str(position) for position in arg["hidden_positions"]]
    hidden_layers = [str(layer) for layer in arg["hidden_layers"]]

    tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=HF_CACHE_DIR)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        cache_dir=HF_CACHE_DIR,
        torch_dtype=dtype,
        device_map="auto",
    )
    model.eval()

    n_layers_raw = getattr(model.config, "num_hidden_layers", None)
    if n_layers_raw is None:
        n_layers_raw = getattr(model.config, "n_layer", None)
    if n_layers_raw is None:
        raise ValueError(f"Could not infer number of hidden layers for {model_id}")
    n_layers = int(n_layers_raw)
    layer_specs = _resolve_layer_specs(hidden_layers, n_layers)

    rows: list[dict[str, Any]] = []
    started_at = time.time()
    for condition_index, condition in enumerate(conditions):
        for critical_slot in critical_slots:
            if not 0 <= critical_slot < n_slots:
                raise ValueError(f"critical_slot={critical_slot} outside n_slots={n_slots}")
            for seed in seeds:
                row_seed = base_seed + seed + 1000 * critical_slot + 100_000 * condition_index
                rng = random.Random(row_seed)
                final_acc: list[float] = []
                schema_validity: list[float] = []
                first_schema: list[float] = []
                first_field_acc: list[float] = []
                first_noop_acc: list[float] = []
                first_slot_acc: list[float] = []
                first_value_acc: list[float] = []
                repair_failed_schema: list[float] = []
                repair_failed_field: list[float] = []
                repair_failed_slot: list[float] = []
                repair_failed_value: list[float] = []
                repair_success_schema: list[float] = []
                repair_success_noop: list[float] = []
                sampled_failure_flags = failure_flags(rng, episodes_per_cell, failure_probability)
                failure_modes: dict[str, int] = {}
                examples: list[dict[str, Any]] = []

                for episode in range(episodes_per_cell):
                    bits = episode_bits(rng, n_slots)
                    value = bits[critical_slot]
                    if condition == "prompt_json_format_control":
                        text, parsed = generate_action(
                            model,
                            tokenizer,
                            messages(format_user_prompt()),
                            max_new_tokens,
                            n_slots,
                            variants_per_slot,
                        )
                        schema_validity.append(float(parsed["valid"]))
                        first_schema.append(float(parsed["valid"]))
                        first_noop_acc.append(float(parsed["valid"] and parsed["opcode"] == "noop"))
                        first_field_acc.append(first_noop_acc[-1])
                        if not parsed["valid"] or parsed["opcode"] != "noop":
                            reason = str(parsed["reason"] or parsed["opcode"])
                            failure_modes[reason] = failure_modes.get(reason, 0) + 1
                        if len(examples) < 2:
                            examples.append({"episode": episode, "text": text, "parsed": compact_parsed(parsed)})
                        continue

                    if condition == "prompt_json_visible_control":
                        text, parsed = generate_action(
                            model,
                            tokenizer,
                            messages(visible_user_prompt(bits, critical_slot, variants_per_slot)),
                            max_new_tokens,
                            n_slots,
                            variants_per_slot,
                        )
                        is_noop = parsed["valid"] and parsed["opcode"] == "noop"
                        final_acc.append(float(is_noop))
                        first_schema.append(float(parsed["valid"]))
                        first_noop_acc.append(float(is_noop))
                        first_field_acc.append(float(is_noop))
                        if not is_noop:
                            reason = str(parsed["reason"] or parsed["opcode"])
                            failure_modes[reason] = failure_modes.get(reason, 0) + 1
                        if len(examples) < 2:
                            examples.append({"episode": episode, "text": text, "parsed": compact_parsed(parsed)})
                        continue

                    if condition == "prompt_json_short_horizon_control":
                        text, parsed = generate_action(
                            model,
                            tokenizer,
                            messages(short_user_prompt(bits, critical_slot, variants_per_slot)),
                            max_new_tokens,
                            n_slots,
                            variants_per_slot,
                        )
                        correct = call_correct(parsed, critical_slot, value)
                        final_acc.append(float(correct))
                        first_schema.append(float(parsed["valid"]))
                        first_field_acc.append(float(correct))
                        first_slot_acc.append(float(parsed["valid"] and parsed["slot"] == critical_slot))
                        first_value_acc.append(float(parsed["valid"] and parsed["value"] == value))
                        if not correct:
                            reason = str(parsed["reason"] or parsed["opcode"])
                            failure_modes[reason] = failure_modes.get(reason, 0) + 1
                        if len(examples) < 2:
                            examples.append(
                                {
                                    "episode": episode,
                                    "target_value": value,
                                    "text": text,
                                    "parsed": compact_parsed(parsed),
                                }
                            )
                        continue

                    if condition != "prompt_json_bottleneck":
                        raise ValueError(f"Unknown prompt transfer condition {condition!r}")

                    user_prompt = bottleneck_user_prompt(bits, critical_slot, n_slots, slot_gap, variants_per_slot)
                    first_text, first_parsed = generate_action(
                        model,
                        tokenizer,
                        messages(user_prompt),
                        max_new_tokens,
                        n_slots,
                        variants_per_slot,
                    )
                    first_correct = call_correct(first_parsed, critical_slot, value)
                    first_schema.append(float(first_parsed["valid"]))
                    first_field_acc.append(float(first_correct))
                    first_slot_acc.append(float(first_parsed["valid"] and first_parsed["slot"] == critical_slot))
                    first_value_acc.append(float(first_parsed["valid"] and first_parsed["value"] == value))

                    failed = sampled_failure_flags[episode]
                    repair_text, repair_parsed = generate_action(
                        model,
                        tokenizer,
                        repair_messages(user_prompt, first_text, failed),
                        max_new_tokens,
                        n_slots,
                        variants_per_slot,
                    )
                    if failed:
                        repair_correct = call_correct(repair_parsed, critical_slot, value)
                        final_acc.append(float(repair_correct))
                        repair_failed_schema.append(float(repair_parsed["valid"]))
                        repair_failed_field.append(float(repair_correct))
                        repair_failed_slot.append(
                            float(repair_parsed["valid"] and repair_parsed["slot"] == critical_slot)
                        )
                        repair_failed_value.append(float(repair_parsed["valid"] and repair_parsed["value"] == value))
                        if not repair_correct:
                            reason = f"failed_repair:{repair_parsed['reason'] or repair_parsed['opcode']}"
                            failure_modes[reason] = failure_modes.get(reason, 0) + 1
                    else:
                        is_noop = repair_parsed["valid"] and repair_parsed["opcode"] == "noop"
                        final_acc.append(float(first_correct and is_noop))
                        repair_success_schema.append(float(repair_parsed["valid"]))
                        repair_success_noop.append(float(is_noop))
                        if not is_noop:
                            reason = f"success_repair:{repair_parsed['reason'] or repair_parsed['opcode']}"
                            failure_modes[reason] = failure_modes.get(reason, 0) + 1
                    if len(examples) < 2:
                        examples.append(
                            {
                                "episode": episode,
                                "target_value": value,
                                "first_text": first_text,
                                "first_parsed": compact_parsed(first_parsed),
                                "failed": failed,
                                "repair_text": repair_text,
                                "repair_parsed": compact_parsed(repair_parsed),
                            }
                        )

                rows.append(
                    {
                        "row_kind": "behavior",
                        "condition": condition,
                        "model": model_id,
                        "architecture": model_id,
                        "critical_slot": critical_slot,
                        "seed": row_seed,
                        "episodes": episodes_per_cell,
                        "closed_loop_final_accuracy": mean(final_acc),
                        "schema_validity": mean(schema_validity),
                        "first_field_accuracy": mean(first_field_acc),
                        "first_noop_field_accuracy": mean(first_noop_acc),
                        "first_schema_validity": mean(first_schema),
                        "first_parsed_slot_accuracy": mean(first_slot_acc),
                        "first_parsed_value_accuracy": mean(first_value_acc),
                        "repair_failed_field_accuracy": mean(repair_failed_field),
                        "repair_failed_schema_validity": mean(repair_failed_schema),
                        "repair_failed_parsed_slot_accuracy": mean(repair_failed_slot),
                        "repair_failed_parsed_value_accuracy": mean(repair_failed_value),
                        "repair_success_noop_field_accuracy": mean(repair_success_noop),
                        "repair_success_schema_validity": mean(repair_success_schema),
                        "sampled_failure_rate": mean([float(flag) for flag in sampled_failure_flags])
                        if condition == "prompt_json_bottleneck"
                        else float("nan"),
                        "memory_specificity_z": float("nan"),
                        "memory_rank_percentile": float("nan"),
                        "tool_value_specificity_z": float("nan"),
                        "failure_modes": failure_modes,
                        "examples": examples,
                    }
                )

                if condition == "prompt_json_bottleneck" and hidden_metric_episodes > 0:
                    metric_rng = random.Random(row_seed + 777)
                    for hidden_row in _hidden_localization_sensitivity(
                        model,
                        tokenizer,
                        metric_rng,
                        critical_slot,
                        n_slots=n_slots,
                        slot_gap=slot_gap,
                        variants_per_slot=variants_per_slot,
                        episodes=hidden_metric_episodes,
                        positions=hidden_positions,
                        layer_specs=layer_specs,
                        max_new_tokens=max_new_tokens,
                    ):
                        rows.append(
                            {
                                "row_kind": "hidden_localization",
                                "condition": condition,
                                "model": model_id,
                                "architecture": model_id,
                                "critical_slot": critical_slot,
                                "seed": row_seed,
                                "episodes": hidden_metric_episodes,
                                **hidden_row,
                            }
                        )

    print(f"[prompt-json-hidden-localization] {model_id} produced {len(rows)} rows in {time.time() - started_at:.1f}s")
    return rows


@app.local_entrypoint()
def main(
    models: str = "Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct",
    seeds: int = 4,
    episodes_per_cell: int = 8,
    hidden_metric_episodes: int = 2,
    n_slots: int = 4,
    slot_gap: int = 8,
    variants_per_slot: int = 3,
    conditions: str = (
        "prompt_json_format_control,prompt_json_visible_control,"
        "prompt_json_short_horizon_control,prompt_json_bottleneck"
    ),
    critical_slots: str = "0,1,2,3",
    hidden_positions: str = "prompt_final,generated_first,generated_final",
    hidden_layers: str = "early,mid,late,final",
    base_seed: int = 20260850,
    failure_probability: float = 0.5,
    max_new_tokens: int = 80,
    budget_usd: float = 25.0,
    dry_run_budget: bool = False,
    out: str = "artifacts/long_horizon_bottleneck/prompt_json_hidden_localization_l4.json",
):
    from experiments.long_horizon_bottleneck.core import (
        PROMPT_JSON_LOCALIZATION_LAYERS,
        PROMPT_JSON_LOCALIZATION_POSITIONS,
        estimate_modal_cost,
        parse_csv,
        parse_int_csv,
        summarize_prompt_localization_rows,
    )

    model_list = parse_csv(models)
    condition_list = parse_csv(conditions)
    critical_slot_list = parse_int_csv(critical_slots)
    position_list = parse_csv(hidden_positions)
    layer_list = parse_csv(hidden_layers)
    uses_fixed_actions = any(position.startswith("fixed_") for position in position_list)
    prompt_contract = (
        "papers/long_horizon_bottleneck/prompt_json_fixed_action_localization_preregistration.md"
        if uses_fixed_actions
        else "papers/long_horizon_bottleneck/prompt_json_hidden_localization_preregistration.md"
    )
    seed_values = list(range(seeds))
    if not model_list:
        raise SystemExit("At least one model is required")
    if episodes_per_cell <= 0:
        raise SystemExit("episodes_per_cell must be positive")
    if hidden_metric_episodes < 0:
        raise SystemExit("hidden_metric_episodes must be non-negative")
    if variants_per_slot <= 0:
        raise SystemExit("variants_per_slot must be positive")
    if not 0.0 <= failure_probability <= 1.0:
        raise SystemExit("failure_probability must be between 0 and 1")
    unknown_positions = sorted(set(position_list) - set(PROMPT_JSON_LOCALIZATION_POSITIONS))
    if unknown_positions:
        known = ", ".join(PROMPT_JSON_LOCALIZATION_POSITIONS)
        raise SystemExit(f"Unknown hidden positions {unknown_positions}. Known positions: {known}")
    unknown_layers = []
    for layer in sorted(set(layer_list) - set(PROMPT_JSON_LOCALIZATION_LAYERS)):
        lowered = layer.lower()
        is_integer = lowered.lstrip("-").isdigit()
        is_layer_integer = lowered.startswith("layer_") and lowered.removeprefix("layer_").lstrip("-").isdigit()
        if not is_integer and not is_layer_integer:
            unknown_layers.append(layer)
    if unknown_layers:
        known = ", ".join(PROMPT_JSON_LOCALIZATION_LAYERS)
        raise SystemExit(f"Unknown hidden layers {unknown_layers}. Known layers: {known} or integer indices")

    behavior_cells = len(model_list) * len(condition_list) * len(critical_slot_list) * len(seed_values)
    hidden_sites = len(position_list) * len(layer_list)
    estimate = estimate_modal_cost(
        cells=len(model_list),
        gpu=GPU,
        timeout_seconds=TIMEOUT_SECONDS,
        budget_usd=budget_usd,
    )
    manifest = {
        "models": model_list,
        "gpu": GPU,
        "timeout_seconds": TIMEOUT_SECONDS,
        "max_containers": MAX_CONTAINERS,
        "remote_model_jobs": len(model_list),
        "logical_behavior_cells": behavior_cells,
        "hidden_sites_per_bottleneck_cell": hidden_sites,
        "seeds": seed_values,
        "base_seed": base_seed,
        "episodes_per_cell": episodes_per_cell,
        "hidden_metric_episodes": hidden_metric_episodes,
        "conditions": condition_list,
        "critical_slots": critical_slot_list,
        "n_slots": n_slots,
        "slot_gap": slot_gap,
        "variants_per_slot": variants_per_slot,
        "failure_probability": failure_probability,
        "max_new_tokens": max_new_tokens,
        "hidden_positions": position_list,
        "hidden_layers": layer_list,
        "fixed_action_templates": {
            "fixed_noop": '{"tool":"noop"}',
            "fixed_read": '{"tool":"read_slot","slot":"<critical slot phrase>","value":0}',
        }
        if uses_fixed_actions
        else {},
        "budget_estimate": estimate.__dict__,
        "thresholds": {
            "format_schema_validity": 0.95,
            "prompt_action_accuracy": 0.85,
            "localization_specificity_ci_low": 0.0,
            "localization_rank_chance": 0.5,
        },
        "prompt_contract": prompt_contract,
        "model_sources": [f"https://huggingface.co/{model_id}" for model_id in model_list],
    }
    print(
        "[prompt-json-hidden-localization] "
        f"models={len(model_list)} behavior_cells={behavior_cells} hidden_sites={hidden_sites} "
        f"gpu={GPU} max_containers={MAX_CONTAINERS} timeout={TIMEOUT_SECONDS}s "
        f"conservative_cost=${estimate.conservative_cost_usd:.2f} budget=${budget_usd:.2f}"
    )
    if not estimate.within_budget:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate.conservative_cost_usd:.2f} exceeds budget ${budget_usd:.2f}."
        )
    if dry_run_budget:
        dry_run_kind = "prompt JSON fixed-action localization dry run" if uses_fixed_actions else (
            "prompt JSON hidden-localization dry run"
        )
        print(json.dumps({"kind": dry_run_kind, "manifest": manifest}, indent=2))
        return

    model_args = [
        {
            "model_id": model_id,
            "seeds": seed_values,
            "episodes_per_cell": episodes_per_cell,
            "hidden_metric_episodes": hidden_metric_episodes,
            "n_slots": n_slots,
            "slot_gap": slot_gap,
            "variants_per_slot": variants_per_slot,
            "conditions": condition_list,
            "critical_slots": critical_slot_list,
            "base_seed": base_seed,
            "failure_probability": failure_probability,
            "max_new_tokens": max_new_tokens,
            "hidden_positions": position_list,
            "hidden_layers": layer_list,
        }
        for model_id in model_list
    ]
    model_row_groups = list(run_prompt_hidden_localization_model.map(model_args))
    rows = [row for row_group in model_row_groups for row in row_group]
    summary = summarize_prompt_localization_rows(rows)
    payload = {
        "kind": "prompt JSON fixed-action localization moved-bottleneck sweep"
        if uses_fixed_actions
        else "prompt JSON hidden-localization moved-bottleneck sweep",
        "manifest": manifest,
        "summary": summary,
        "rows": rows,
    }
    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[prompt-json-hidden-localization] wrote {output_path}")
    print(f"[prompt-json-hidden-localization] outcome={summary['outcome']}")

    def fmt(stat: dict[str, Any]) -> str:
        value = float(stat["mean"])
        return f"{value:.3f}" if math.isfinite(value) else "n/a"

    for key, item in summary["behavior"]["groups"].items():
        print(
            f"  behavior {key:82s} "
            f"final={fmt(item['final_accuracy'])} "
            f"schema={fmt(item['schema_validity'])} "
            f"first_slot={fmt(item['first_parsed_slot_accuracy'])} "
            f"first_value={fmt(item['first_parsed_value_accuracy'])} "
            f"pass={item['gate']['pass']}"
        )

    passing_sites = [
        (key, item)
        for key, item in summary["localization_groups"].items()
        if item["gate"]["pass"]
    ]
    if passing_sites:
        print("[prompt-json-hidden-localization] passing hidden sites:")
        for key, item in passing_sites:
            print(
                f"  {key} "
                f"spec={fmt(item['memory_specificity_z'])} "
                f"rank={fmt(item['memory_rank_percentile'])}"
            )
    else:
        print("[prompt-json-hidden-localization] no preregistered hidden site passed")
