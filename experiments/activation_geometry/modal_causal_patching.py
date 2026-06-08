#!/usr/bin/env python3
"""Modal entrypoint for final-token causal patching diagnostics."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


DEFAULT_MODEL_ID = "EleutherAI/pythia-70m-deduped"
DEFAULT_OPTION_ORDERS = "std,tds,dst"
DEFAULT_PATCH_MODES = "target,distractor,random,source_noop"
IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-causal-patching")


def pair_id(left: str, right: str) -> str:
    return f"{left}->{right}"


def option_order_key(order: tuple[str, str, str]) -> str:
    initials = {
        "source": "s",
        "target": "t",
        "distractor": "d",
    }
    return "".join(initials[role] for role in order)


def calibration_prompt(
    *,
    source_text: str,
    labels_by_role: dict[str, str],
    option_order: tuple[str, str, str],
) -> str:
    lines = [
        source_text,
        "",
        "Choose the closest related concept.",
    ]
    for slot, role in zip(("A", "B", "C"), option_order, strict=True):
        lines.append(f"{slot}. {labels_by_role[role]}")
    lines.append("Answer:")
    return "\n".join(lines)


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_delta(
    *,
    baseline_scores: dict[str, float],
    patched_scores: dict[str, float],
) -> dict[str, Any]:
    baseline_margin = target_margin(baseline_scores)
    patched_margin = target_margin(patched_scores)
    return {
        "baseline_target_margin": baseline_margin,
        "patched_target_margin": patched_margin,
        "target_margin_delta": patched_margin - baseline_margin,
        "target_minus_source_delta": (
            (patched_scores["target"] - patched_scores["source"])
            - (baseline_scores["target"] - baseline_scores["source"])
        ),
        "target_minus_distractor_delta": (
            (patched_scores["target"] - patched_scores["distractor"])
            - (baseline_scores["target"] - baseline_scores["distractor"])
        ),
    }


def final_token_pool(hidden_states: Any, attention_mask: Any) -> Any:
    token_counts = attention_mask.to(hidden_states.device).sum(dim=1).clamp(min=1)
    final_indices = token_counts.long() - 1
    gather_indices = final_indices.view(-1, 1, 1).expand(
        -1,
        1,
        hidden_states.shape[-1],
    )
    return hidden_states.gather(dim=1, index=gather_indices).squeeze(1)


def transformer_blocks(model: Any) -> Any:
    if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        return model.transformer.h
    if hasattr(model, "gpt_neox") and hasattr(model.gpt_neox, "layers"):
        return model.gpt_neox.layers
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return model.model.layers
    raise ValueError("Unsupported model architecture: cannot locate transformer blocks")


def block_for_hidden_state_layer(model: Any, layer: int) -> Any:
    if layer < 1:
        raise ValueError("Patch layer must be a transformer block output, not layer 0")
    blocks = transformer_blocks(model)
    block_index = layer - 1
    if not 0 <= block_index < len(blocks):
        raise ValueError(
            f"Layer {layer} maps to block {block_index}, outside block range 0..{len(blocks) - 1}"
        )
    return blocks[block_index]


def slot_token_ids(tokenizer: Any) -> dict[str, int]:
    tokens = {}
    for slot in ("A", "B", "C"):
        ids = tokenizer.encode(f" {slot}", add_special_tokens=False)
        if not ids:
            raise ValueError(f"Could not encode option token {slot!r}")
        tokens[slot] = int(ids[0])
    return tokens


def role_token_ids(
    option_order: tuple[str, str, str],
    token_ids_by_slot: dict[str, int],
) -> dict[str, int]:
    return {
        role: token_ids_by_slot[slot]
        for slot, role in zip(("A", "B", "C"), option_order, strict=True)
    }


def option_logprobs(torch: Any, logits: Any, token_ids: dict[str, int]) -> dict[str, float]:
    logprobs = torch.nn.functional.log_softmax(logits, dim=-1)
    return {name: float(logprobs[token_id].item()) for name, token_id in token_ids.items()}


def add_final_token_patch_hook(
    *,
    torch: Any,
    model: Any,
    layer: int,
    attention_mask: Any,
    patch_vector: Any,
    patch_alpha: float,
) -> Any:
    block = block_for_hidden_state_layer(model, layer)
    final_indices = attention_mask.to(patch_vector.device).sum(dim=1).long() - 1

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        adjusted = hidden_states.clone()
        batch_indices = torch.arange(adjusted.shape[0], device=adjusted.device)
        current = adjusted[batch_indices, final_indices]
        replacement = patch_vector.to(device=adjusted.device, dtype=adjusted.dtype)
        adjusted[batch_indices, final_indices] = (
            (1.0 - patch_alpha) * current + patch_alpha * replacement
        )
        if isinstance(output, tuple):
            return (adjusted, *output[1:])
        return adjusted

    return block.register_forward_hook(hook)


def run_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    patch_vector: Any | None,
    patch_alpha: float,
    max_length: int,
    token_ids: dict[str, int],
) -> dict[str, float]:
    encoded = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )
    device = next(model.parameters()).device
    encoded = {name: value.to(device) for name, value in encoded.items()}
    handle = None
    if patch_vector is not None:
        handle = add_final_token_patch_hook(
            torch=torch,
            model=model,
            layer=layer,
            attention_mask=encoded["attention_mask"],
            patch_vector=patch_vector,
            patch_alpha=patch_alpha,
        )
    try:
        with torch.inference_mode():
            outputs = model(**encoded, use_cache=False)
    finally:
        if handle is not None:
            handle.remove()
    logits = outputs.logits[0, -1].float()
    return option_logprobs(torch, logits, token_ids)


def collect_final_token_activations(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    records: list[dict[str, Any]],
    layers: list[int],
    batch_size: int,
    max_length: int,
) -> dict[str, dict[str, Any]]:
    activations: dict[str, dict[str, Any]] = {str(layer): {} for layer in layers}
    device = next(model.parameters()).device
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        encoded = tokenizer(
            [str(record["text"]) for record in batch],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        encoded = {name: value.to(device) for name, value in encoded.items()}
        with torch.inference_mode():
            outputs = model(**encoded, output_hidden_states=True, use_cache=False)
        for layer in layers:
            if not -len(outputs.hidden_states) <= layer < len(outputs.hidden_states):
                raise ValueError(
                    f"Layer {layer} is outside hidden-state range "
                    f"[-{len(outputs.hidden_states)}, {len(outputs.hidden_states) - 1}]"
                )
            pooled = final_token_pool(outputs.hidden_states[layer], encoded["attention_mask"])
            for record, vector in zip(batch, pooled, strict=True):
                activations[str(layer)][str(record["id"])] = vector.float().cpu()
    return activations


def activation_for_concept(
    records: list[dict[str, Any]],
    activations_by_record: dict[str, Any],
    *,
    concept_id: str,
    variant_index: int,
) -> Any:
    matches = [
        activations_by_record[str(record["id"])]
        for record in records
        if str(record["concept_id"]) == concept_id
        and int(record["variant_index"]) == variant_index
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one activation for {concept_id} variant {variant_index}; "
            f"found {len(matches)}"
        )
    return matches[0]


def heldout_source_text(
    records: list[dict[str, Any]],
    *,
    concept_id: str,
    holdout_variant_index: int,
) -> str:
    matches = [
        str(record["text"])
        for record in records
        if str(record["concept_id"]) == concept_id
        and int(record["variant_index"]) == holdout_variant_index
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one holdout text for {concept_id} variant {holdout_variant_index}; "
            f"found {len(matches)}"
        )
    return matches[0]


def patch_concept_for_mode(pair: dict[str, Any], mode: str) -> str:
    if mode == "target":
        return str(pair["right"])
    if mode == "distractor":
        return str(pair["distractor"])
    if mode == "random":
        return str(pair["random_patch"])
    if mode == "source_noop":
        return str(pair["left"])
    raise ValueError(f"Unknown patch mode: {mode}")


@app.function(image=IMAGE, timeout=2400)
def run_causal_patching_remote(
    concepts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    layer_roles: dict[str, int],
    patch_modes: list[str],
    option_orders: list[list[str]],
    holdout_variant_index: int,
    patch_variant_index: int,
    patch_alpha: float,
    batch_size: int,
    max_length: int,
) -> dict[str, Any]:
    torch = importlib.import_module("torch")
    transformers = importlib.import_module("transformers")

    token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN") or None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.bfloat16 if device.type == "cuda" else torch.float32,
        token=token,
    )
    model.to(device)
    model.eval()
    token_ids_by_slot = slot_token_ids(tokenizer)

    layers = list(dict.fromkeys(layer_roles.values()))
    layer_activations = collect_final_token_activations(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        records=records,
        layers=layers,
        batch_size=batch_size,
        max_length=max_length,
    )
    concept_lookup = {str(concept["id"]): concept for concept in concepts}

    rows = []
    for role, layer in layer_roles.items():
        activations_by_record = layer_activations[str(layer)]
        for pair in pair_specs:
            left = str(pair["left"])
            right = str(pair["right"])
            distractor = str(pair["distractor"])
            source_text = heldout_source_text(
                records,
                concept_id=left,
                holdout_variant_index=holdout_variant_index,
            )
            labels_by_role = {
                "source": str(concept_lookup[left]["label"]),
                "target": str(concept_lookup[right]["label"]),
                "distractor": str(concept_lookup[distractor]["label"]),
            }
            for order_row in option_orders:
                if len(order_row) != 3:
                    raise ValueError(f"Option order must contain three roles: {order_row}")
                option_order = (
                    str(order_row[0]),
                    str(order_row[1]),
                    str(order_row[2]),
                )
                prompt = calibration_prompt(
                    source_text=source_text,
                    labels_by_role=labels_by_role,
                    option_order=option_order,
                )
                token_ids = role_token_ids(option_order, token_ids_by_slot)
                baseline_scores = run_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    prompt=prompt,
                    layer=layer,
                    patch_vector=None,
                    patch_alpha=patch_alpha,
                    max_length=max_length,
                    token_ids=token_ids,
                )
                for mode in patch_modes:
                    patch_concept_id = patch_concept_for_mode(pair, mode)
                    patch_vector = activation_for_concept(
                        records,
                        activations_by_record,
                        concept_id=patch_concept_id,
                        variant_index=patch_variant_index,
                    ).to(device)
                    patched_scores = run_prompt(
                        torch=torch,
                        tokenizer=tokenizer,
                        model=model,
                        prompt=prompt,
                        layer=layer,
                        patch_vector=patch_vector,
                        patch_alpha=patch_alpha,
                        max_length=max_length,
                        token_ids=token_ids,
                    )
                    rows.append(
                        {
                            "pair": pair_id(left, right),
                            "left": left,
                            "right": right,
                            "kind": str(pair["kind"]),
                            "distractor": distractor,
                            "random_patch": str(pair["random_patch"]),
                            "random_patch_scope": str(pair["random_patch_scope"]),
                            "role": role,
                            "layer": layer,
                            "patch_mode": mode,
                            "patch_concept": patch_concept_id,
                            "patch_concept_label": str(concept_lookup[patch_concept_id]["label"]),
                            "patch_variant_index": patch_variant_index,
                            "patch_alpha": patch_alpha,
                            "option_order": option_order_key(option_order),
                            "prompt": prompt,
                            "scores": {
                                "baseline": baseline_scores,
                                "patched": patched_scores,
                            },
                            "summary": summarize_delta(
                                baseline_scores=baseline_scores,
                                patched_scores=patched_scores,
                            ),
                        }
                    )
    return {
        "rows": rows,
        "slot_token_ids": token_ids_by_slot,
    }


@app.local_entrypoint()
def main(
    concepts: str = "experiments/concept_geometry/concept_set.json",
    paraphrases: str = "experiments/concept_geometry/concept_paraphrases.json",
    model_id: str = DEFAULT_MODEL_ID,
    primary_layer: int = 5,
    backup_layer: int = 6,
    control_layer: int = 1,
    batch_size: int = 8,
    max_length: int = 128,
    holdout_variant: int = 2,
    patch_variant: int = 2,
    patch_alpha: float = 1.0,
    patch_modes: str = DEFAULT_PATCH_MODES,
    option_orders: str = DEFAULT_OPTION_ORDERS,
    seed: int = 20260608,
    out: str = "artifacts/activation_geometry/modal_causal_patching.json",
) -> None:
    resolved_path = Path(__file__).resolve()
    repo_root = resolved_path.parents[2] if len(resolved_path.parents) > 2 else Path.cwd()
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    from experiments.activation_geometry.activation_geometry_probe import (
        activation_records,
        load_concepts,
    )
    from experiments.activation_geometry.causal_patching_diagnostic import (
        aggregate_rows,
        attach_random_patch_concepts,
        gate_summaries,
        parse_patch_modes,
        public_summary,
        specificity_rows,
        write_payload,
    )
    from experiments.activation_geometry.final_token_steering_pilot import (
        default_pair_specs,
        serializable_pair_specs,
    )
    from experiments.activation_geometry.steering_calibration_diagnostic import (
        parse_option_orders,
    )

    concept_rows = load_concepts(Path(concepts))
    records = activation_records(concept_rows, Path(paraphrases))
    serializable_concepts = [concept.__dict__ for concept in concept_rows]
    serializable_records = [
        {
            "id": record.id,
            "concept_id": record.concept_id,
            "label": record.label,
            "category": record.category,
            "variant_index": record.variant_index,
            "text": record.text,
        }
        for record in records
    ]
    layer_roles = {
        "primary": primary_layer,
        "backup": backup_layer,
        "control": control_layer,
    }
    parsed_patch_modes = parse_patch_modes(patch_modes)
    parsed_option_orders = parse_option_orders(option_orders)
    pair_specs = attach_random_patch_concepts(
        serializable_concepts,
        serializable_pair_specs(default_pair_specs(concept_rows)),
        seed=seed,
    )
    remote_payload = run_causal_patching_remote.remote(
        serializable_concepts,
        serializable_records,
        pair_specs,
        model_id,
        layer_roles,
        parsed_patch_modes,
        [list(order) for order in parsed_option_orders],
        holdout_variant,
        patch_variant,
        patch_alpha,
        batch_size,
        max_length,
    )
    aggregates = aggregate_rows(remote_payload["rows"])
    specificity = specificity_rows(aggregates)
    payload = {
        "manifest": {
            "model_id": model_id,
            "concept_source": concepts,
            "paraphrase_source": paraphrases,
            "pooling": "final-token",
            "layer_roles": layer_roles,
            "holdout_variant_index": holdout_variant,
            "patch_variant_index": patch_variant,
            "patch_alpha": patch_alpha,
            "patch_modes": parsed_patch_modes,
            "option_orders": [
                "".join(role[0] for role in order)
                for order in parsed_option_orders
            ],
            "batch_size": batch_size,
            "max_length": max_length,
            "seed": seed,
            "pairs": pair_specs,
            "slot_token_ids": remote_payload["slot_token_ids"],
        },
        "rows": remote_payload["rows"],
        "aggregate_rows": aggregates,
        "specificity_rows": specificity,
        "gate_summaries": gate_summaries(specificity),
    }
    if out and out.lower() != "none":
        write_payload(Path(out), payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    print(
        "Run with: modal run experiments/activation_geometry/modal_causal_patching.py",
        file=sys.stderr,
    )
