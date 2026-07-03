#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Prompt-level JSON transfer sweep on one cheap Modal L4 worker.

This is the first transfer target after the synthetic JSON regimes. A prompted
open model must emit parser-facing JSON actions:

    {"tool": "read_slot", "slot": "second clue", "value": 0}
    {"tool": "noop"}

The runner loads the model once, evaluates all conditions inside one L4
container, and summarizes the result as positive, controlled strong negative, or
inconclusive.

Recommended dry run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_prompt_json_transfer_sweep.py \\
        --dry-run-budget --budget-usd 25

Recommended confirmatory run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_prompt_json_transfer_sweep.py \\
        --model-id Qwen/Qwen2.5-0.5B-Instruct --seeds 4 \\
        --episodes-per-cell 8 --hidden-metric-episodes 2 \\
        --critical-slots 0,1,2,3 --budget-usd 25 \\
        --out artifacts/long_horizon_bottleneck/prompt_json_transfer_l4.json
"""

from __future__ import annotations

import importlib
import json
import math
import random
import time
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 3600
HF_CACHE_DIR = "/cache/huggingface"

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.47,<4.55",
    "accelerate>=0.33,<1.0",
    "sentencepiece>=0.2,<0.3",
    "safetensors>=0.4,<0.6",
)
HF_CACHE = modal.Volume.from_name("research-derived-hf-cache", create_if_missing=True)
app = modal.App(name="research-derived-prompt-json-transfer")

SYSTEM_PROMPT = """You are a tool-planning model. Reply with exactly one JSON object and no prose.

Valid JSON actions:
{"tool":"read_slot","slot":"<exact slot phrase>","value":0}
{"tool":"read_slot","slot":"<exact slot phrase>","value":1}
{"tool":"noop"}

The slot field must be one of the allowed slot phrases named in the user prompt.
"""


def _text_argument_phrase(slot: int, variant_index: int) -> str:
    ordinals = (
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "eighth",
        "ninth",
        "tenth",
        "eleventh",
        "twelfth",
    )
    if variant_index == 0:
        return f"clue_{slot}"
    if variant_index == 1:
        ordinal = ordinals[slot] if slot < len(ordinals) else f"slot {slot}"
        return f"{ordinal} clue"
    if variant_index == 2:
        return f"memory slot {slot}"
    return f"slot {slot} phrase {variant_index}"


def _slot_phrase(slot: int, variants_per_slot: int) -> str:
    return _text_argument_phrase(slot, slot % variants_per_slot)


def _parse_text_argument(text: str, n_slots: int, variants_per_slot: int) -> dict[str, Any]:
    normalized = _normalize_text_argument(text)
    if normalized in {"none", "missing", "null", "noop"}:
        return {"slot": None, "variant_index": None, "valid": True, "missing": True, "reason": None}
    for slot in range(n_slots):
        for variant_index in range(variants_per_slot):
            if normalized == _normalize_text_argument(_text_argument_phrase(slot, variant_index)):
                return {
                    "slot": slot,
                    "variant_index": variant_index,
                    "valid": True,
                    "missing": False,
                    "reason": None,
                }
    return {"slot": None, "variant_index": None, "valid": False, "missing": False, "reason": "unparsed_text_argument"}


def _normalize_text_argument(text: str) -> str:
    normalized = text.strip().lower().replace("_", " ").replace("-", " ")
    return " ".join(normalized.split())


def _extract_json_object(text: str) -> tuple[dict[str, Any] | None, str | None]:
    decoder = json.JSONDecoder()
    for start, char in enumerate(text):
        if char != "{":
            continue
        try:
            parsed, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed, text[start : start + end]
    return None, None


def _malformed(text: str, reason: str, json_text: str | None = None) -> dict[str, Any]:
    return {
        "opcode": "malformed",
        "slot": None,
        "variant_index": None,
        "value": None,
        "valid": False,
        "executable": False,
        "reason": reason,
        "text": text,
        "json_text": json_text,
    }


def _parse_action(text: str, n_slots: int, variants_per_slot: int) -> dict[str, Any]:
    action, json_text = _extract_json_object(text)
    if action is None:
        return _malformed(text, "missing_json_object")
    tool = action.get("tool")
    if not isinstance(tool, str):
        return _malformed(text, "missing_tool", json_text)
    normalized_tool = tool.strip().lower()
    if normalized_tool == "noop":
        return {
            "opcode": "noop",
            "slot": None,
            "variant_index": None,
            "value": None,
            "valid": True,
            "executable": False,
            "reason": None,
            "text": text,
            "json_text": json_text,
        }
    if normalized_tool != "read_slot":
        return _malformed(text, "unknown_tool", json_text)

    slot_argument = action.get("slot")
    if isinstance(slot_argument, int) and not isinstance(slot_argument, bool):
        if not 0 <= slot_argument < n_slots:
            return _malformed(text, "slot_out_of_range", json_text)
        parsed_argument = {
            "slot": slot_argument,
            "variant_index": None,
            "valid": True,
            "missing": False,
            "reason": None,
        }
    elif isinstance(slot_argument, str):
        parsed_argument = _parse_text_argument(slot_argument, n_slots, variants_per_slot)
    else:
        return _malformed(text, "missing_slot", json_text)
    if parsed_argument["missing"]:
        return _malformed(text, "missing_slot", json_text)
    if not parsed_argument["valid"]:
        return _malformed(text, str(parsed_argument["reason"]), json_text)

    raw_value = action.get("value")
    if isinstance(raw_value, bool):
        value = int(raw_value)
    elif isinstance(raw_value, int) and raw_value in (0, 1):
        value = raw_value
    elif isinstance(raw_value, str) and raw_value.strip().lower() in {"0", "1", "false", "true"}:
        value = 1 if raw_value.strip().lower() in {"1", "true"} else 0
    else:
        return _malformed(text, "bad_value", json_text)

    return {
        "opcode": "call",
        "slot": parsed_argument["slot"],
        "variant_index": parsed_argument["variant_index"],
        "value": value,
        "valid": True,
        "executable": True,
        "reason": None,
        "text": text,
        "json_text": json_text,
    }


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else float("nan")


def _episode_bits(rng: random.Random, n_slots: int) -> list[int]:
    return [rng.randrange(2) for _ in range(n_slots)]


def _context_lines(bits: list[int], n_slots: int, slot_gap: int, variants_per_slot: int) -> list[str]:
    slot_lines = {slot_gap + slot * slot_gap: slot for slot in range(n_slots)}
    total_lines = slot_gap * (n_slots + 1)
    lines: list[str] = []
    for line_index in range(total_lines):
        if line_index in slot_lines:
            slot = slot_lines[line_index]
            lines.append(f"Memory record {line_index:02d}: {_slot_phrase(slot, variants_per_slot)} = {bits[slot]}.")
        else:
            marker = (line_index * 37 + sum(bits) * 11) % 997
            lines.append(f"Trace filler {line_index:02d}: ignore marker {marker:03d}.")
    return lines


def _bottleneck_user_prompt(
    bits: list[int],
    critical_slot: int,
    n_slots: int,
    slot_gap: int,
    variants_per_slot: int,
) -> str:
    phrase = _slot_phrase(critical_slot, variants_per_slot)
    allowed = ", ".join(f'"{_slot_phrase(slot, variants_per_slot)}"' for slot in range(n_slots))
    lines = _context_lines(bits, n_slots, slot_gap, variants_per_slot)
    return "\n".join(
        [
            "Long-horizon moved-bottleneck task.",
            "Read the records, find the requested slot phrase, and emit one JSON action.",
            f"Allowed slot phrases: {allowed}.",
            *lines,
            f"Requested slot phrase: {phrase}",
            f"Emit the read_slot JSON for {phrase} with its recorded value.",
        ]
    )


def _visible_user_prompt(bits: list[int], critical_slot: int, variants_per_slot: int) -> str:
    phrase = _slot_phrase(critical_slot, variants_per_slot)
    value = bits[critical_slot]
    return "\n".join(
        [
            "Visible-control task.",
            f"The requested slot phrase is {phrase}, and the value is already visible: {value}.",
            "The environment already has the answer. Emit only the no-op JSON action.",
        ]
    )


def _short_user_prompt(bits: list[int], critical_slot: int, variants_per_slot: int) -> str:
    phrase = _slot_phrase(critical_slot, variants_per_slot)
    value = bits[critical_slot]
    return "\n".join(
        [
            f"Allowed slot phrases: \"{phrase}\".",
            f"Record: {phrase} = {value}.",
            f"Requested slot phrase: {phrase}.",
            f"Emit the read_slot JSON for {phrase} with its value.",
        ]
    )


def _format_user_prompt() -> str:
    return "Format-control task. Emit exactly this action as JSON: {\"tool\":\"noop\"}"


def _messages(user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _repair_messages(user_prompt: str, assistant_text: str, failed: bool) -> list[dict[str, str]]:
    if failed:
        repair_text = (
            "Tool result: ERROR. The previous action failed before recording any value. "
            "Repair by emitting the same read_slot JSON action again."
        )
    else:
        repair_text = (
            "Tool result: SUCCESS. The value was recorded already. "
            "Emit only the no-op JSON action."
        )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": assistant_text},
        {"role": "user", "content": repair_text},
    ]


def _failure_flags(rng: random.Random, episodes: int, failure_probability: float) -> list[bool]:
    flags = [rng.random() < failure_probability for _ in range(episodes)]
    if 0.0 < failure_probability < 1.0 and episodes >= 2:
        if not any(flags):
            flags[0] = True
        if all(flags):
            flags[-1] = False
    return flags


def _call_correct(parsed: dict[str, Any], critical_slot: int, value: int) -> bool:
    return (
        parsed["valid"]
        and parsed["opcode"] == "call"
        and parsed["slot"] == critical_slot
        and parsed["value"] == value
    )


def _compact_parsed(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "opcode": parsed["opcode"],
        "slot": parsed["slot"],
        "variant_index": parsed["variant_index"],
        "value": parsed["value"],
        "valid": parsed["valid"],
        "executable": parsed["executable"],
        "reason": parsed["reason"],
        "json_text": parsed["json_text"],
    }


def _encode_messages(tokenizer: Any, messages: list[dict[str, str]], device: Any) -> dict[str, Any]:
    import torch

    if getattr(tokenizer, "chat_template", None):
        input_ids = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(device)
        return {"input_ids": input_ids, "attention_mask": torch.ones_like(input_ids)}
    prompt = "\n\n".join(f"{message['role'].title()}: {message['content']}" for message in messages)
    prompt += "\n\nAssistant:"
    encoded = tokenizer(prompt, return_tensors="pt")
    return {key: value.to(device) for key, value in encoded.items()}


def _generate_action(
    model: Any,
    tokenizer: Any,
    messages: list[dict[str, str]],
    max_new_tokens: int,
    n_slots: int,
    variants_per_slot: int,
) -> tuple[str, dict[str, Any]]:
    import torch

    encoded = _encode_messages(tokenizer, messages, model.device)
    with torch.inference_mode():
        output = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output[0, encoded["input_ids"].shape[-1] :]
    text = tokenizer.decode(generated, skip_special_tokens=True).strip()
    return text, _parse_action(text, n_slots, variants_per_slot)


def _last_hidden_vector(model: Any, tokenizer: Any, messages: list[dict[str, str]]) -> Any:
    import torch

    encoded = _encode_messages(tokenizer, messages, model.device)
    with torch.inference_mode():
        outputs = model(**encoded, output_hidden_states=True, use_cache=False)
    return outputs.hidden_states[-1][0, -1].detach().float().cpu()


def _hidden_sensitivity(
    model: Any,
    tokenizer: Any,
    rng: random.Random,
    critical_slot: int,
    *,
    n_slots: int,
    slot_gap: int,
    variants_per_slot: int,
    episodes: int,
) -> tuple[float, float]:
    import torch

    specificity_values: list[float] = []
    rank_values: list[float] = []
    for _ in range(episodes):
        bits = _episode_bits(rng, n_slots)
        base_messages = _messages(_bottleneck_user_prompt(bits, critical_slot, n_slots, slot_gap, variants_per_slot))
        base_hidden = _last_hidden_vector(model, tokenizer, base_messages)
        distances: list[float] = []
        for slot in range(n_slots):
            flipped = list(bits)
            flipped[slot] = 1 - flipped[slot]
            flipped_messages = _messages(
                _bottleneck_user_prompt(flipped, critical_slot, n_slots, slot_gap, variants_per_slot)
            )
            distance = torch.linalg.vector_norm(base_hidden - _last_hidden_vector(model, tokenizer, flipped_messages))
            distances.append(float(distance.item()))
        critical_distance = distances[critical_slot]
        other_distances = [value for slot, value in enumerate(distances) if slot != critical_slot]
        if other_distances:
            other_mean = sum(other_distances) / len(other_distances)
            other_var = sum((value - other_mean) ** 2 for value in other_distances) / len(other_distances)
            specificity_values.append((critical_distance - other_mean) / math.sqrt(other_var + 1e-8))
        rank_values.append(sum(value <= critical_distance for value in distances) / len(distances))
    return _mean(specificity_values), _mean(rank_values)


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=4,
    memory=16384,
    max_containers=1,
    volumes={"/cache": HF_CACHE},
    retries=0,
)
def run_prompt_transfer_sweep(arg: dict[str, Any]) -> list[dict[str, Any]]:
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
                failure_flags = _failure_flags(rng, episodes_per_cell, failure_probability)
                failure_modes: dict[str, int] = {}
                examples: list[dict[str, Any]] = []

                for episode in range(episodes_per_cell):
                    bits = _episode_bits(rng, n_slots)
                    value = bits[critical_slot]
                    if condition == "prompt_json_format_control":
                        text, parsed = _generate_action(
                            model,
                            tokenizer,
                            _messages(_format_user_prompt()),
                            max_new_tokens,
                            n_slots,
                            variants_per_slot,
                        )
                        schema_validity.append(float(parsed["valid"]))
                        first_schema.append(float(parsed["valid"]))
                        first_noop_acc.append(float(parsed["valid"] and parsed["opcode"] == "noop"))
                        first_field_acc.append(first_noop_acc[-1])
                        if not parsed["valid"] or parsed["opcode"] != "noop":
                            failure_modes[str(parsed["reason"] or parsed["opcode"])] = (
                                failure_modes.get(str(parsed["reason"] or parsed["opcode"]), 0) + 1
                            )
                        if len(examples) < 2:
                            examples.append({"episode": episode, "text": text, "parsed": _compact_parsed(parsed)})
                        continue

                    if condition == "prompt_json_visible_control":
                        text, parsed = _generate_action(
                            model,
                            tokenizer,
                            _messages(_visible_user_prompt(bits, critical_slot, variants_per_slot)),
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
                            failure_modes[str(parsed["reason"] or parsed["opcode"])] = (
                                failure_modes.get(str(parsed["reason"] or parsed["opcode"]), 0) + 1
                            )
                        if len(examples) < 2:
                            examples.append({"episode": episode, "text": text, "parsed": _compact_parsed(parsed)})
                        continue

                    if condition == "prompt_json_short_horizon_control":
                        text, parsed = _generate_action(
                            model,
                            tokenizer,
                            _messages(_short_user_prompt(bits, critical_slot, variants_per_slot)),
                            max_new_tokens,
                            n_slots,
                            variants_per_slot,
                        )
                        call_correct = _call_correct(parsed, critical_slot, value)
                        final_acc.append(float(call_correct))
                        first_schema.append(float(parsed["valid"]))
                        first_field_acc.append(float(call_correct))
                        first_slot_acc.append(float(parsed["valid"] and parsed["slot"] == critical_slot))
                        first_value_acc.append(float(parsed["valid"] and parsed["value"] == value))
                        if not call_correct:
                            failure_modes[str(parsed["reason"] or parsed["opcode"])] = (
                                failure_modes.get(str(parsed["reason"] or parsed["opcode"]), 0) + 1
                            )
                        if len(examples) < 2:
                            examples.append(
                                {
                                    "episode": episode,
                                    "target_value": value,
                                    "text": text,
                                    "parsed": _compact_parsed(parsed),
                                }
                            )
                        continue

                    if condition != "prompt_json_bottleneck":
                        raise ValueError(f"Unknown prompt transfer condition {condition!r}")

                    user_prompt = _bottleneck_user_prompt(bits, critical_slot, n_slots, slot_gap, variants_per_slot)
                    first_text, first_parsed = _generate_action(
                        model,
                        tokenizer,
                        _messages(user_prompt),
                        max_new_tokens,
                        n_slots,
                        variants_per_slot,
                    )
                    first_correct = _call_correct(first_parsed, critical_slot, value)
                    first_schema.append(float(first_parsed["valid"]))
                    first_field_acc.append(float(first_correct))
                    first_slot_acc.append(float(first_parsed["valid"] and first_parsed["slot"] == critical_slot))
                    first_value_acc.append(float(first_parsed["valid"] and first_parsed["value"] == value))

                    failed = failure_flags[episode]
                    repair_text, repair_parsed = _generate_action(
                        model,
                        tokenizer,
                        _repair_messages(user_prompt, first_text, failed),
                        max_new_tokens,
                        n_slots,
                        variants_per_slot,
                    )
                    if failed:
                        repair_correct = _call_correct(repair_parsed, critical_slot, value)
                        final_acc.append(float(repair_correct))
                        repair_failed_schema.append(float(repair_parsed["valid"]))
                        repair_failed_field.append(float(repair_correct))
                        repair_failed_slot.append(
                            float(repair_parsed["valid"] and repair_parsed["slot"] == critical_slot)
                        )
                        repair_failed_value.append(float(repair_parsed["valid"] and repair_parsed["value"] == value))
                        if not repair_correct:
                            failure_modes[f"failed_repair:{repair_parsed['reason'] or repair_parsed['opcode']}"] = (
                                failure_modes.get(
                                    f"failed_repair:{repair_parsed['reason'] or repair_parsed['opcode']}",
                                    0,
                                )
                                + 1
                            )
                    else:
                        is_noop = repair_parsed["valid"] and repair_parsed["opcode"] == "noop"
                        final_acc.append(float(first_correct and is_noop))
                        repair_success_schema.append(float(repair_parsed["valid"]))
                        repair_success_noop.append(float(is_noop))
                        if not is_noop:
                            failure_modes[f"success_repair:{repair_parsed['reason'] or repair_parsed['opcode']}"] = (
                                failure_modes.get(
                                    f"success_repair:{repair_parsed['reason'] or repair_parsed['opcode']}",
                                    0,
                                )
                                + 1
                            )
                    if len(examples) < 2:
                        examples.append(
                            {
                                "episode": episode,
                                "target_value": value,
                                "first_text": first_text,
                                "first_parsed": _compact_parsed(first_parsed),
                                "failed": failed,
                                "repair_text": repair_text,
                                "repair_parsed": _compact_parsed(repair_parsed),
                            }
                        )

                memory_specificity_z = float("nan")
                memory_rank_percentile = float("nan")
                if condition == "prompt_json_bottleneck" and hidden_metric_episodes > 0:
                    metric_rng = random.Random(row_seed + 777)
                    memory_specificity_z, memory_rank_percentile = _hidden_sensitivity(
                        model,
                        tokenizer,
                        metric_rng,
                        critical_slot,
                        n_slots=n_slots,
                        slot_gap=slot_gap,
                        variants_per_slot=variants_per_slot,
                        episodes=hidden_metric_episodes,
                    )

                rows.append(
                    {
                        "condition": condition,
                        "model": model_id,
                        "architecture": model_id,
                        "critical_slot": critical_slot,
                        "seed": row_seed,
                        "episodes": episodes_per_cell,
                        "closed_loop_final_accuracy": _mean(final_acc),
                        "schema_validity": _mean(schema_validity),
                        "first_field_accuracy": _mean(first_field_acc),
                        "first_noop_field_accuracy": _mean(first_noop_acc),
                        "first_schema_validity": _mean(first_schema),
                        "first_parsed_slot_accuracy": _mean(first_slot_acc),
                        "first_parsed_value_accuracy": _mean(first_value_acc),
                        "repair_failed_field_accuracy": _mean(repair_failed_field),
                        "repair_failed_schema_validity": _mean(repair_failed_schema),
                        "repair_failed_parsed_slot_accuracy": _mean(repair_failed_slot),
                        "repair_failed_parsed_value_accuracy": _mean(repair_failed_value),
                        "repair_success_noop_field_accuracy": _mean(repair_success_noop),
                        "repair_success_schema_validity": _mean(repair_success_schema),
                        "sampled_failure_rate": _mean([float(flag) for flag in failure_flags])
                        if condition == "prompt_json_bottleneck"
                        else float("nan"),
                        "memory_specificity_z": memory_specificity_z,
                        "memory_rank_percentile": memory_rank_percentile,
                        "tool_value_specificity_z": float("nan"),
                        "failure_modes": failure_modes,
                        "examples": examples,
                    }
                )

    print(f"[prompt-json-transfer] produced {len(rows)} rows in {time.time() - started_at:.1f}s")
    return rows


@app.local_entrypoint()
def main(
    model_id: str = "Qwen/Qwen2.5-0.5B-Instruct",
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
    base_seed: int = 20260705,
    failure_probability: float = 0.5,
    max_new_tokens: int = 80,
    budget_usd: float = 25.0,
    dry_run_budget: bool = False,
    out: str = "artifacts/long_horizon_bottleneck/prompt_json_transfer_l4.json",
):
    from experiments.long_horizon_bottleneck.core import (
        estimate_modal_cost,
        parse_csv,
        parse_int_csv,
        summarize_prompt_transfer_rows,
    )

    condition_list = parse_csv(conditions)
    critical_slot_list = parse_int_csv(critical_slots)
    seed_values = list(range(seeds))
    if episodes_per_cell <= 0:
        raise SystemExit("episodes_per_cell must be positive")
    if hidden_metric_episodes < 0:
        raise SystemExit("hidden_metric_episodes must be non-negative")
    if variants_per_slot <= 0:
        raise SystemExit("variants_per_slot must be positive")
    if not 0.0 <= failure_probability <= 1.0:
        raise SystemExit("failure_probability must be between 0 and 1")

    logical_cells = len(condition_list) * len(critical_slot_list) * len(seed_values)
    estimate = estimate_modal_cost(
        cells=1,
        gpu=GPU,
        timeout_seconds=TIMEOUT_SECONDS,
        budget_usd=budget_usd,
    )
    manifest = {
        "model_id": model_id,
        "gpu": GPU,
        "timeout_seconds": TIMEOUT_SECONDS,
        "remote_containers": 1,
        "logical_cells": logical_cells,
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
        "budget_estimate": estimate.__dict__,
        "thresholds": {
            "format_schema_validity": 0.95,
            "prompt_action_accuracy": 0.85,
        },
        "prompt_contract": "papers/long_horizon_bottleneck/prompt_json_transfer_preregistration.md",
    }
    print(
        "[prompt-json-transfer] "
        f"logical_cells={logical_cells} remote_containers=1 gpu={GPU} timeout={TIMEOUT_SECONDS}s "
        f"conservative_cost=${estimate.conservative_cost_usd:.2f} budget=${budget_usd:.2f}"
    )
    if not estimate.within_budget:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate.conservative_cost_usd:.2f} exceeds budget ${budget_usd:.2f}."
        )
    if dry_run_budget:
        print(json.dumps({"kind": "prompt JSON transfer dry run", "manifest": manifest}, indent=2))
        return

    rows = run_prompt_transfer_sweep.remote(
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
        }
    )
    summary = summarize_prompt_transfer_rows(rows)
    payload = {
        "kind": "prompt JSON transfer moved-bottleneck sweep",
        "manifest": manifest,
        "summary": summary,
        "rows": rows,
    }
    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[prompt-json-transfer] wrote {output_path}")
    print(f"[prompt-json-transfer] outcome={summary['outcome']}")

    def fmt(stat: dict[str, Any]) -> str:
        value = float(stat["mean"])
        return f"{value:.3f}" if math.isfinite(value) else "n/a"

    for key, item in summary["groups"].items():
        print(
            f"  {key:70s} "
            f"final={fmt(item['final_accuracy'])} "
            f"schema={fmt(item['schema_validity'])} "
            f"first_slot={fmt(item['first_parsed_slot_accuracy'])} "
            f"first_value={fmt(item['first_parsed_value_accuracy'])} "
            f"failed_slot={fmt(item['repair_failed_parsed_slot_accuracy'])} "
            f"failed_value={fmt(item['repair_failed_parsed_value_accuracy'])} "
            f"success_noop={fmt(item['repair_success_noop_field_accuracy'])} "
            f"memory_spec={fmt(item['memory_specificity_z'])} "
            f"rank={fmt(item['memory_rank_percentile'])} "
            f"pass={item['gate']['pass']}"
        )
