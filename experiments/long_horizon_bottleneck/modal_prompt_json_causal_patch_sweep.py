#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Prompt JSON fixed-prefix causal patch sweep on cheap Modal L4 workers.

The fixed-action localization run showed that hidden critical-slot specificity
survives when generated answer tokens are held fixed. This runner asks a more
causal question: if we patch a donor hidden state from the base prompt into a
critical-slot-flipped prompt, do the next-token logits before the JSON `value`
field move back toward the donor slot value?

Recommended dry run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_prompt_json_causal_patch_sweep.py \\
        --dry-run-budget --budget-usd 25

Recommended confirmatory run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_prompt_json_causal_patch_sweep.py \\
        --models Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct \\
        --seeds 4 --episodes-per-cell 8 --critical-slots 0,1,2,3 \\
        --patch-positions prompt_final,value_prefix_final \\
        --patch-layers late,final --budget-usd 25 --base-seed 20260950 \\
        --out artifacts/long_horizon_bottleneck/prompt_json_causal_patch_l4.json
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
    episode_bits,
    messages,
    slot_phrase,
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
app = modal.App(name="research-derived-prompt-json-causal-patch")


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
            raise ValueError(f"Unknown patch layer spec {name!r}. Use {known} or an integer index.")
        if index < 0:
            index = n_layers + 1 + index
            label = f"layer_{index}"
        if not 1 <= index <= n_layers:
            raise ValueError(f"Patch layer index {index} outside transformer block range 1..{n_layers}")
        key = (label, index)
        if key not in seen:
            specs.append({"label": label, "index": index})
            seen.add(key)
    if not specs:
        raise ValueError("At least one patch layer spec is required")
    return specs


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


def _value_action_prefix(critical_slot: int, variants_per_slot: int) -> str:
    phrase = slot_phrase(critical_slot, variants_per_slot)
    return f'{{"tool":"read_slot","slot":"{phrase}","value":'


def _encode_value_prefix(
    tokenizer: Any,
    message_list: list[dict[str, str]],
    action_prefix: str,
    device: Any,
) -> tuple[dict[str, Any], dict[str, int]]:
    import torch

    prompt_text = _chat_text(tokenizer, message_list, add_generation_prompt=True)
    full_text = f"{prompt_text}{action_prefix}"
    encoded = tokenizer(full_text, return_tensors="pt", add_special_tokens=False)
    prompt_encoded = tokenizer(prompt_text, return_tensors="pt", add_special_tokens=False)
    full_len = int(encoded["input_ids"].shape[-1])
    prompt_len = int(prompt_encoded["input_ids"].shape[-1])
    if full_len <= 0 or prompt_len <= 0:
        raise ValueError("Tokenized prompt/value prefix must be non-empty")
    model_inputs = {key: value.to(device) for key, value in encoded.items()}
    if "attention_mask" not in model_inputs:
        model_inputs["attention_mask"] = torch.ones_like(model_inputs["input_ids"])
    return model_inputs, {
        "prompt_final": min(prompt_len - 1, full_len - 1),
        "value_prefix_final": full_len - 1,
    }


def _decoder_layers(model: Any) -> Any:
    candidates = [
        getattr(model, "model", None),
        getattr(getattr(model, "model", None), "model", None),
        getattr(model, "transformer", None),
        model,
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if hasattr(candidate, "layers"):
            return candidate.layers
        if hasattr(candidate, "h"):
            return candidate.h
    raise ValueError(f"Could not locate decoder layers on {type(model).__name__}")


def _forward_logits_and_hidden(
    model: Any,
    encoded: dict[str, Any],
    *,
    output_hidden_states: bool,
    patch_layer_index: int | None = None,
    patch_position: int | None = None,
    patch_vector: Any | None = None,
) -> tuple[Any, tuple[Any, ...] | None]:
    import torch

    handle = None
    if patch_vector is not None:
        if patch_layer_index is None or patch_position is None:
            raise ValueError("patch_layer_index and patch_position are required when patch_vector is provided")
        layers = _decoder_layers(model)
        module = layers[patch_layer_index - 1]

        def patch_hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
            if isinstance(output, tuple):
                hidden = output[0].clone()
                hidden[:, patch_position, :] = patch_vector.to(device=hidden.device, dtype=hidden.dtype)
                return (hidden, *output[1:])
            hidden = output.clone()
            hidden[:, patch_position, :] = patch_vector.to(device=hidden.device, dtype=hidden.dtype)
            return hidden

        handle = module.register_forward_hook(patch_hook)

    try:
        with torch.inference_mode():
            outputs = model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"],
                output_hidden_states=output_hidden_states,
                use_cache=False,
            )
    finally:
        if handle is not None:
            handle.remove()
    return outputs.logits[0, -1].detach().float().cpu(), outputs.hidden_states if output_hidden_states else None


def _value_token_ids(tokenizer: Any) -> tuple[int, int]:
    zero_ids = tokenizer("0", add_special_tokens=False)["input_ids"]
    one_ids = tokenizer("1", add_special_tokens=False)["input_ids"]
    if not zero_ids or not one_ids:
        raise ValueError("Tokenizer did not produce token ids for JSON value tokens 0 and 1")
    return int(zero_ids[0]), int(one_ids[0])


def _margin(logits: Any, donor_value: int, donor_token_id: int, corrupted_token_id: int) -> float:
    if donor_value == 0:
        return float((logits[donor_token_id] - logits[corrupted_token_id]).item())
    return float((logits[corrupted_token_id] - logits[donor_token_id]).item())


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
def run_prompt_causal_patch_model(arg: dict[str, Any]) -> list[dict[str, Any]]:
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
    base_seed = int(arg["base_seed"])
    seeds = [int(seed) for seed in arg["seeds"]]
    critical_slots = [int(slot) for slot in arg["critical_slots"]]
    patch_positions = [str(position) for position in arg["patch_positions"]]
    patch_layers = [str(layer) for layer in arg["patch_layers"]]

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
    layer_specs = _resolve_layer_specs(patch_layers, int(n_layers_raw))
    zero_token_id, one_token_id = _value_token_ids(tokenizer)

    site_keys = [
        (position, str(layer_spec["label"]), int(layer_spec["index"]))
        for position in patch_positions
        for layer_spec in layer_specs
    ]
    rows: list[dict[str, Any]] = []
    started_at = time.time()
    for critical_slot in critical_slots:
        if not 0 <= critical_slot < n_slots:
            raise ValueError(f"critical_slot={critical_slot} outside n_slots={n_slots}")
        action_prefix = _value_action_prefix(critical_slot, variants_per_slot)
        for seed in seeds:
            row_seed = base_seed + seed + 1000 * critical_slot
            rng = random.Random(row_seed)
            for episode in range(episodes_per_cell):
                bits = episode_bits(rng, n_slots)
                donor_value = bits[critical_slot]
                corrupted_bits = list(bits)
                corrupted_bits[critical_slot] = 1 - corrupted_bits[critical_slot]

                clean_prompt = bottleneck_user_prompt(bits, critical_slot, n_slots, slot_gap, variants_per_slot)
                corrupted_prompt = bottleneck_user_prompt(
                    corrupted_bits,
                    critical_slot,
                    n_slots,
                    slot_gap,
                    variants_per_slot,
                )
                clean_encoded, clean_positions = _encode_value_prefix(
                    tokenizer,
                    messages(clean_prompt),
                    action_prefix,
                    model.device,
                )
                corrupted_encoded, corrupted_positions = _encode_value_prefix(
                    tokenizer,
                    messages(corrupted_prompt),
                    action_prefix,
                    model.device,
                )
                clean_logits, clean_hidden_states = _forward_logits_and_hidden(
                    model,
                    clean_encoded,
                    output_hidden_states=True,
                )
                if clean_hidden_states is None:
                    raise ValueError("Expected hidden states from clean forward pass")
                corrupted_logits, _ = _forward_logits_and_hidden(
                    model,
                    corrupted_encoded,
                    output_hidden_states=False,
                )
                clean_margin = _margin(clean_logits, donor_value, zero_token_id, one_token_id)
                corrupted_margin = _margin(corrupted_logits, donor_value, zero_token_id, one_token_id)

                for position, layer_label, layer_index in site_keys:
                    if position not in clean_positions or position not in corrupted_positions:
                        known = ", ".join(sorted(clean_positions))
                        raise ValueError(f"Unknown patch position {position!r}. Known positions: {known}")
                    donor_vector = clean_hidden_states[layer_index][0, clean_positions[position]].detach()
                    patched_logits, _ = _forward_logits_and_hidden(
                        model,
                        corrupted_encoded,
                        output_hidden_states=False,
                        patch_layer_index=layer_index,
                        patch_position=corrupted_positions[position],
                        patch_vector=donor_vector,
                    )
                    patched_margin = _margin(patched_logits, donor_value, zero_token_id, one_token_id)
                    patch_effect = patched_margin - corrupted_margin
                    denominator = clean_margin - corrupted_margin
                    patch_recovery = patch_effect / denominator if abs(denominator) > 1e-8 else float("nan")
                    rows.append(
                        {
                            "row_kind": "causal_patch",
                            "model": model_id,
                            "architecture": model_id,
                            "critical_slot": critical_slot,
                            "seed": row_seed,
                            "episode": episode,
                            "patch_position": position,
                            "patch_layer": layer_label,
                            "patch_layer_index": layer_index,
                            "donor_value": donor_value,
                            "corrupted_value": 1 - donor_value,
                            "clean_margin": clean_margin,
                            "corrupted_margin": corrupted_margin,
                            "patched_margin": patched_margin,
                            "patch_effect": patch_effect,
                            "patch_recovery": patch_recovery,
                            "patch_direction_success": float(patch_effect > 0.0),
                        }
                    )

    print(f"[prompt-json-causal-patch] {model_id} produced {len(rows)} rows in {time.time() - started_at:.1f}s")
    return rows


@app.local_entrypoint()
def main(
    models: str = "Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct",
    seeds: int = 4,
    episodes_per_cell: int = 8,
    n_slots: int = 4,
    slot_gap: int = 8,
    variants_per_slot: int = 3,
    critical_slots: str = "0,1,2,3",
    patch_positions: str = "prompt_final,value_prefix_final",
    patch_layers: str = "late,final",
    base_seed: int = 20260950,
    budget_usd: float = 25.0,
    dry_run_budget: bool = False,
    out: str = "artifacts/long_horizon_bottleneck/prompt_json_causal_patch_l4.json",
):
    from experiments.long_horizon_bottleneck.core import (
        PROMPT_JSON_CAUSAL_PATCH_POSITIONS,
        PROMPT_JSON_LOCALIZATION_LAYERS,
        estimate_modal_cost,
        parse_csv,
        parse_int_csv,
        summarize_prompt_causal_patch_rows,
    )

    model_list = parse_csv(models)
    critical_slot_list = parse_int_csv(critical_slots)
    position_list = parse_csv(patch_positions)
    layer_list = parse_csv(patch_layers)
    seed_values = list(range(seeds))
    if not model_list:
        raise SystemExit("At least one model is required")
    if episodes_per_cell <= 0:
        raise SystemExit("episodes_per_cell must be positive")
    if variants_per_slot <= 0:
        raise SystemExit("variants_per_slot must be positive")
    unknown_positions = sorted(set(position_list) - set(PROMPT_JSON_CAUSAL_PATCH_POSITIONS))
    if unknown_positions:
        known = ", ".join(PROMPT_JSON_CAUSAL_PATCH_POSITIONS)
        raise SystemExit(f"Unknown patch positions {unknown_positions}. Known positions: {known}")
    unknown_layers = []
    for layer in sorted(set(layer_list) - set(PROMPT_JSON_LOCALIZATION_LAYERS)):
        lowered = layer.lower()
        is_integer = lowered.lstrip("-").isdigit()
        is_layer_integer = lowered.startswith("layer_") and lowered.removeprefix("layer_").lstrip("-").isdigit()
        if not is_integer and not is_layer_integer:
            unknown_layers.append(layer)
    if unknown_layers:
        known = ", ".join(PROMPT_JSON_LOCALIZATION_LAYERS)
        raise SystemExit(f"Unknown patch layers {unknown_layers}. Known layers: {known} or integer indices")

    logical_cells = len(model_list) * len(critical_slot_list) * len(seed_values)
    patch_sites = len(position_list) * len(layer_list)
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
        "logical_cells": logical_cells,
        "patch_sites_per_cell": patch_sites,
        "seeds": seed_values,
        "base_seed": base_seed,
        "episodes_per_cell": episodes_per_cell,
        "critical_slots": critical_slot_list,
        "n_slots": n_slots,
        "slot_gap": slot_gap,
        "variants_per_slot": variants_per_slot,
        "patch_positions": position_list,
        "patch_layers": layer_list,
        "budget_estimate": estimate.__dict__,
        "thresholds": {
            "clean_margin_positive": 0.0,
            "corrupted_margin_negative": 0.0,
            "patch_effect_ci_low": 0.0,
            "patch_direction_chance": 0.5,
        },
        "prompt_contract": "papers/long_horizon_bottleneck/prompt_json_causal_patch_preregistration.md",
        "model_sources": [f"https://huggingface.co/{model_id}" for model_id in model_list],
    }
    print(
        "[prompt-json-causal-patch] "
        f"models={len(model_list)} logical_cells={logical_cells} patch_sites={patch_sites} "
        f"gpu={GPU} max_containers={MAX_CONTAINERS} timeout={TIMEOUT_SECONDS}s "
        f"conservative_cost=${estimate.conservative_cost_usd:.2f} budget=${budget_usd:.2f}"
    )
    if not estimate.within_budget:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate.conservative_cost_usd:.2f} exceeds budget ${budget_usd:.2f}."
        )
    if dry_run_budget:
        print(json.dumps({"kind": "prompt JSON fixed-prefix causal-patch dry run", "manifest": manifest}, indent=2))
        return

    model_args = [
        {
            "model_id": model_id,
            "seeds": seed_values,
            "episodes_per_cell": episodes_per_cell,
            "n_slots": n_slots,
            "slot_gap": slot_gap,
            "variants_per_slot": variants_per_slot,
            "critical_slots": critical_slot_list,
            "base_seed": base_seed,
            "patch_positions": position_list,
            "patch_layers": layer_list,
        }
        for model_id in model_list
    ]
    model_row_groups = list(run_prompt_causal_patch_model.map(model_args))
    rows = [row for row_group in model_row_groups for row in row_group]
    summary = summarize_prompt_causal_patch_rows(rows)
    payload = {
        "kind": "prompt JSON fixed-prefix causal-patch sweep",
        "manifest": manifest,
        "summary": summary,
        "rows": rows,
    }
    output_path = Path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[prompt-json-causal-patch] wrote {output_path}")
    print(f"[prompt-json-causal-patch] outcome={summary['outcome']}")

    def fmt(stat: dict[str, Any]) -> str:
        value = float(stat["mean"])
        return f"{value:.3f}" if math.isfinite(value) else "n/a"

    passing_groups = [
        (key, item)
        for key, item in summary["groups"].items()
        if item["gate"]["pass"]
    ]
    for key, item in summary["groups"].items():
        print(
            f"  group {key:82s} "
            f"clean={fmt(item['clean_margin'])} "
            f"corrupt={fmt(item['corrupted_margin'])} "
            f"effect={fmt(item['patch_effect'])} "
            f"dir={fmt(item['patch_direction_success'])} "
            f"pass={item['gate']['pass']}"
        )
    if passing_groups:
        print("[prompt-json-causal-patch] passing patch groups:")
        for key, item in passing_groups:
            print(
                f"  {key} "
                f"effect={fmt(item['patch_effect'])} "
                f"recovery={fmt(item['patch_recovery'])}"
            )
    else:
        print("[prompt-json-causal-patch] no preregistered patch group passed")
