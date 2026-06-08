#!/usr/bin/env python3
"""Modal entrypoint for label-free behavior-level patching gates."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


DEFAULT_MODEL_ID = "EleutherAI/pythia-70m-deduped"
DEFAULT_INJECTION_LAYER = 6
DEFAULT_PATCH_MODES = "target,distractor,random,source_noop"
DEFAULT_PATCH_TEXT_REGIMES = "definition,neutral"
DEFAULT_PATCH_VECTOR_SURFACE = "hook_output"
DEFAULT_PROMPT_FRAME = "source_passage"
DEFAULT_SCORING_SURFACE = "option_token"
DEFAULT_LABEL_SCORE_NORMALIZATION = "mean"
DEFAULT_OPTION_ORDERS = (
    "source,target,distractor;"
    "target,distractor,source;"
    "distractor,source,target"
)
PATCH_MODES = ("target", "distractor", "random", "source_noop")
PATCH_TEXT_REGIMES = (
    "definition",
    "definition_without_label",
    "neutral",
    "label_only",
    "blank_carrier",
    "shuffled_label",
)
PATCH_VECTOR_SURFACES = ("hidden_state", "hook_output")
OPTION_ROLES = ("source", "target", "distractor")
PROMPT_FRAMES = ("source_passage", "latent_choice")
SCORING_SURFACES = ("option_token", "full_label")
LABEL_SCORE_NORMALIZATIONS = ("mean", "sum")
IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-label-free-behavior-gate")


def parse_csv(value: str) -> list[str]:
    values = [part.strip() for part in value.split(",") if part.strip()]
    if not values:
        raise ValueError("At least one value must be provided")
    return values


def parse_values(value: str, *, allowed: tuple[str, ...], name: str) -> list[str]:
    values = parse_csv(value)
    invalid = sorted(set(values) - set(allowed))
    if invalid:
        options = ", ".join(allowed)
        raise ValueError(f"{name} must be chosen from: {options}")
    return values


def parse_ints(value: str, *, name: str) -> list[int]:
    values = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not values:
        raise ValueError(f"At least one {name} value must be provided")
    return values


def parse_floats(value: str, *, name: str) -> list[float]:
    values = [float(part.strip()) for part in value.split(",") if part.strip()]
    if not values:
        raise ValueError(f"At least one {name} value must be provided")
    return values


def parse_option_orders(value: str) -> list[tuple[str, str, str]]:
    orders = []
    for order_text in value.split(";"):
        if not order_text.strip():
            continue
        roles = parse_values(order_text, allowed=OPTION_ROLES, name="Option role")
        if len(roles) != 3 or set(roles) != set(OPTION_ROLES):
            roles = ",".join(OPTION_ROLES)
            raise ValueError(f"Each option order must be a permutation of: {roles}")
        order = (roles[0], roles[1], roles[2])
        orders.append(order)
    if not orders:
        raise ValueError("At least one option order must be provided")
    return orders


def neutral_carrier_text(*, label: str) -> str:
    return f"Concept label: {label}."


def label_only_text(*, label: str) -> str:
    return label


def blank_carrier_text() -> str:
    return "Concept label: [omitted]."


def definition_without_label_text(*, definition_text: str, label: str) -> str:
    stripped = definition_text.strip()
    prefix = f"{label}:"
    if stripped.lower().startswith(prefix.lower()):
        return stripped[len(prefix) :].strip()
    return stripped


def source_text_for_regime(
    *,
    definition_text: str,
    label: str,
    patch_text_regime: str,
    shuffled_label: str | None = None,
) -> str:
    if patch_text_regime == "definition":
        return definition_text
    if patch_text_regime == "definition_without_label":
        return definition_without_label_text(
            definition_text=definition_text,
            label=label,
        )
    if patch_text_regime == "neutral":
        return neutral_carrier_text(label=label)
    if patch_text_regime == "label_only":
        return label_only_text(label=label)
    if patch_text_regime == "blank_carrier":
        return blank_carrier_text()
    if patch_text_regime == "shuffled_label":
        if shuffled_label is None:
            raise ValueError("Shuffled-label regime requires shuffled_label")
        return neutral_carrier_text(label=shuffled_label)
    raise ValueError(f"Unknown patch text regime: {patch_text_regime}")


def shuffled_labels_by_concept(labels_by_concept: dict[str, str]) -> dict[str, str]:
    concept_ids = sorted(labels_by_concept)
    if len(concept_ids) < 2:
        raise ValueError("Shuffled-label regime requires at least two concepts")
    return {
        concept_id: labels_by_concept[concept_ids[(index + 1) % len(concept_ids)]]
        for index, concept_id in enumerate(concept_ids)
    }


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


def behavior_prompt(
    *,
    source_text: str,
    labels_by_role: dict[str, str],
    option_order: tuple[str, str, str],
    prompt_frame: str,
) -> str:
    if prompt_frame == "source_passage":
        lines = [
            "Read the passage and choose the concept it points to. Answer with only the letter.",
            "",
            f"Passage: {source_text}",
            "",
            "Options:",
        ]
    elif prompt_frame == "latent_choice":
        lines = [
            "Choose the concept most likely indicated by the model's current internal state. Answer with only the letter.",
            "",
            "Options:",
        ]
    else:
        raise ValueError(f"Unknown prompt frame: {prompt_frame}")
    for slot, role in zip(("A", "B", "C"), option_order, strict=True):
        lines.append(f"{slot}. {labels_by_role[role]}")
    lines.append("")
    lines.append("Answer:")
    return "\n".join(lines)


def full_label_prompt(
    *,
    source_text: str,
    prompt_frame: str,
) -> str:
    if prompt_frame == "source_passage":
        return "\n".join(
            [
                "Read the passage and name the concept it points to.",
                "",
                f"Passage: {source_text}",
                "",
                "Concept:",
            ]
        )
    if prompt_frame == "latent_choice":
        return "The concept most likely indicated by the model's current internal state is"
    raise ValueError(f"Unknown prompt frame: {prompt_frame}")


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_behavior_delta(
    *,
    baseline_scores: dict[str, float],
    patched_scores: dict[str, float],
) -> dict[str, float]:
    baseline_margin = target_margin(baseline_scores)
    patched_margin = target_margin(patched_scores)
    return {
        "baseline_target_margin": baseline_margin,
        "patched_target_margin": patched_margin,
        "target_margin_delta": patched_margin - baseline_margin,
        "target_logprob_delta": patched_scores["target"] - baseline_scores["target"],
        "source_logprob_delta": patched_scores["source"] - baseline_scores["source"],
        "distractor_logprob_delta": (
            patched_scores["distractor"] - baseline_scores["distractor"]
        ),
        "target_minus_source_delta": (
            (patched_scores["target"] - patched_scores["source"])
            - (baseline_scores["target"] - baseline_scores["source"])
        ),
        "target_minus_distractor_delta": (
            (patched_scores["target"] - patched_scores["distractor"])
            - (baseline_scores["target"] - baseline_scores["distractor"])
        ),
    }


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
            f"Layer {layer} maps to block {block_index}, "
            f"outside block range 0..{len(blocks) - 1}"
        )
    return blocks[block_index]


def final_token_vectors(
    *,
    hidden_states: tuple[Any, ...],
    attention_mask: Any,
    layers: list[int],
) -> dict[int, list[float]]:
    token_counts = attention_mask.sum(dim=1).clamp(min=1)
    final_index = int(token_counts[0].item()) - 1
    vectors = {}
    for layer in layers:
        if not -len(hidden_states) <= layer < len(hidden_states):
            raise ValueError(
                f"Layer {layer} is outside hidden-state range "
                f"[-{len(hidden_states)}, {len(hidden_states) - 1}]"
            )
        vectors[layer] = hidden_states[layer][0, final_index].float().cpu().tolist()
    return vectors


def prompt_layer_vectors(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layers: list[int],
    max_length: int,
) -> dict[int, list[float]]:
    encoded = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )
    device = next(model.parameters()).device
    encoded = {name: value.to(device) for name, value in encoded.items()}
    with torch.inference_mode():
        outputs = model(**encoded, output_hidden_states=True, use_cache=False)
    return final_token_vectors(
        hidden_states=outputs.hidden_states,
        attention_mask=encoded["attention_mask"],
        layers=layers,
    )


def prompt_hook_output_vectors(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layers: list[int],
    max_length: int,
) -> dict[int, list[float]]:
    encoded = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )
    device = next(model.parameters()).device
    encoded = {name: value.to(device) for name, value in encoded.items()}
    final_indices = encoded["attention_mask"].to(device).sum(dim=1).long() - 1
    captured: dict[int, list[float]] = {}
    handles = []

    def make_hook(layer: int) -> Any:
        def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> None:
            hidden_states = output[0] if isinstance(output, tuple) else output
            vector = hidden_states[0, final_indices[0]].detach().float().cpu()
            captured[layer] = vector.tolist()

        return hook

    for layer in sorted(set(layers)):
        handles.append(
            block_for_hidden_state_layer(model, layer).register_forward_hook(
                make_hook(layer),
            )
        )
    try:
        with torch.inference_mode():
            model(**encoded, output_hidden_states=False, use_cache=False)
    finally:
        for handle in handles:
            handle.remove()

    missing_layers = sorted(set(layers) - set(captured))
    if missing_layers:
        raise ValueError(f"Missing hook outputs for layers: {missing_layers}")
    return captured


def prompt_vectors_for_surface(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layers: list[int],
    max_length: int,
    patch_vector_surface: str,
) -> dict[int, list[float]]:
    if patch_vector_surface == "hidden_state":
        return prompt_layer_vectors(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            layers=layers,
            max_length=max_length,
        )
    if patch_vector_surface == "hook_output":
        return prompt_hook_output_vectors(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            layers=layers,
            max_length=max_length,
        )
    raise ValueError(f"Unknown patch vector surface: {patch_vector_surface}")


def add_token_index_patch_hook(
    *,
    torch: Any,
    model: Any,
    layer: int,
    token_indices: Any,
    patch_vector: Any,
    patch_alpha: float,
) -> Any:
    block = block_for_hidden_state_layer(model, layer)
    patch_indices = token_indices.to(patch_vector.device).long()

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        adjusted = hidden_states.clone()
        batch_indices = torch.arange(adjusted.shape[0], device=adjusted.device)
        current = adjusted[batch_indices, patch_indices]
        replacement = patch_vector.to(device=adjusted.device, dtype=adjusted.dtype)
        adjusted[batch_indices, patch_indices] = (
            (1.0 - patch_alpha) * current + patch_alpha * replacement
        )
        if isinstance(output, tuple):
            return (adjusted, *output[1:])
        return adjusted

    return block.register_forward_hook(hook)


def add_final_token_patch_hook(
    *,
    torch: Any,
    model: Any,
    layer: int,
    attention_mask: Any,
    patch_vector: Any,
    patch_alpha: float,
) -> Any:
    final_indices = attention_mask.to(patch_vector.device).sum(dim=1).long() - 1
    return add_token_index_patch_hook(
        torch=torch,
        model=model,
        layer=layer,
        token_indices=final_indices,
        patch_vector=patch_vector,
        patch_alpha=patch_alpha,
    )


def option_token_ids(tokenizer: Any) -> dict[str, int]:
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


def run_behavior_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    injection_layer: int,
    patch_vector: list[float] | None,
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
        patch_tensor = torch.tensor(
            patch_vector,
            dtype=next(model.parameters()).dtype,
            device=device,
        )
        handle = add_final_token_patch_hook(
            torch=torch,
            model=model,
            layer=injection_layer,
            attention_mask=encoded["attention_mask"],
            patch_vector=patch_tensor,
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


def label_token_ids(tokenizer: Any, labels_by_role: dict[str, str]) -> dict[str, list[int]]:
    token_ids = {}
    for role, label in labels_by_role.items():
        ids = tokenizer.encode(f" {label}", add_special_tokens=False)
        if not ids:
            raise ValueError(f"Could not encode label for {role!r}: {label!r}")
        token_ids[role] = [int(token_id) for token_id in ids]
    return token_ids


def continuation_logprob(
    *,
    torch: Any,
    logits: Any,
    prompt_length: int,
    continuation_ids: list[int],
    label_score_normalization: str,
) -> float:
    token_logprobs = []
    for offset, token_id in enumerate(continuation_ids):
        prediction_index = prompt_length - 1 + offset
        logprobs = torch.nn.functional.log_softmax(
            logits[0, prediction_index].float(),
            dim=-1,
        )
        token_logprobs.append(float(logprobs[token_id].item()))
    if label_score_normalization == "sum":
        return sum(token_logprobs)
    if label_score_normalization == "mean":
        return sum(token_logprobs) / len(token_logprobs)
    raise ValueError(f"Unknown label score normalization: {label_score_normalization}")


def run_full_label_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    labels_by_role: dict[str, str],
    injection_layer: int,
    patch_vector: list[float] | None,
    patch_alpha: float,
    max_length: int,
    label_score_normalization: str,
) -> tuple[dict[str, float], dict[str, int]]:
    continuation_ids_by_role = label_token_ids(tokenizer, labels_by_role)
    max_continuation_tokens = max(len(ids) for ids in continuation_ids_by_role.values())
    prompt_max_length = max(1, max_length - max_continuation_tokens)
    prompt_ids = tokenizer.encode(
        prompt,
        add_special_tokens=False,
        truncation=True,
        max_length=prompt_max_length,
    )
    if not prompt_ids:
        raise ValueError("Prompt encoded to zero tokens")

    device = next(model.parameters()).device
    scores = {}
    token_counts = {}
    for role, continuation_ids in continuation_ids_by_role.items():
        input_ids = torch.tensor(
            [prompt_ids + continuation_ids],
            dtype=torch.long,
            device=device,
        )
        attention_mask = torch.ones_like(input_ids)
        handle = None
        if patch_vector is not None:
            patch_tensor = torch.tensor(
                patch_vector,
                dtype=next(model.parameters()).dtype,
                device=device,
            )
            token_indices = torch.tensor([len(prompt_ids) - 1], device=device)
            handle = add_token_index_patch_hook(
                torch=torch,
                model=model,
                layer=injection_layer,
                token_indices=token_indices,
                patch_vector=patch_tensor,
                patch_alpha=patch_alpha,
            )
        try:
            with torch.inference_mode():
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    use_cache=False,
                )
        finally:
            if handle is not None:
                handle.remove()
        scores[role] = continuation_logprob(
            torch=torch,
            logits=outputs.logits,
            prompt_length=len(prompt_ids),
            continuation_ids=continuation_ids,
            label_score_normalization=label_score_normalization,
        )
        token_counts[role] = len(continuation_ids)
    return scores, token_counts


def heldout_text(
    records: list[dict[str, Any]],
    *,
    concept_id: str,
    variant_index: int,
) -> str:
    matches = [
        str(record["text"])
        for record in records
        if str(record["concept_id"]) == concept_id
        and int(record["variant_index"]) == variant_index
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one text for {concept_id} variant {variant_index}; "
            f"found {len(matches)}"
        )
    return matches[0]


@app.function(image=IMAGE, timeout=2400)
def run_label_free_behavior_remote(
    concepts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    injection_layers: list[int],
    patch_modes: list[str],
    patch_text_regimes: list[str],
    eval_variant_index: int,
    patch_alphas: list[float],
    patch_vector_surface: str,
    prompt_frame: str,
    scoring_surface: str,
    label_score_normalization: str,
    option_orders: list[tuple[str, str, str]],
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

    concept_lookup = {str(concept["id"]): concept for concept in concepts}
    slot_token_ids = option_token_ids(tokenizer)
    rows = []
    for pair in pair_specs:
        left = str(pair["left"])
        right = str(pair["right"])
        distractor = str(pair["distractor"])
        random_patch = str(pair["random_patch"])
        source_prompt = heldout_text(
            records,
            concept_id=left,
            variant_index=eval_variant_index,
        )
        labels_by_concept = {
            concept_id: str(concept_lookup[concept_id]["label"])
            for concept_id in sorted({left, right, distractor, random_patch})
        }
        shuffled_labels = shuffled_labels_by_concept(labels_by_concept)
        labels_by_role = {
            "source": labels_by_concept[left],
            "target": labels_by_concept[right],
            "distractor": labels_by_concept[distractor],
        }
        definition_text_by_concept = {
            concept_id: heldout_text(
                records,
                concept_id=concept_id,
                variant_index=eval_variant_index,
            )
            for concept_id in sorted({left, right, distractor, random_patch})
        }
        patch_base_vectors = {
            concept_id: prompt_vectors_for_surface(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                prompt=definition_text,
                layers=injection_layers,
                max_length=max_length,
                patch_vector_surface=patch_vector_surface,
            )
            for concept_id, definition_text in definition_text_by_concept.items()
        }
        probe_specs = []
        if scoring_surface == "option_token":
            for option_order in option_orders:
                prompt = behavior_prompt(
                    source_text=source_prompt,
                    labels_by_role=labels_by_role,
                    option_order=option_order,
                    prompt_frame=prompt_frame,
                )
                token_ids = role_token_ids(option_order, slot_token_ids)
                baseline_scores = run_behavior_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    prompt=prompt,
                    injection_layer=injection_layers[0],
                    patch_vector=None,
                    patch_alpha=0.0,
                    max_length=max_length,
                    token_ids=token_ids,
                )
                probe_specs.append(
                    {
                        "prompt": prompt,
                        "option_order": option_order,
                        "token_ids": token_ids,
                        "baseline_scores": baseline_scores,
                        "label_token_counts": None,
                    }
                )
        elif scoring_surface == "full_label":
            prompt = full_label_prompt(
                source_text=source_prompt,
                prompt_frame=prompt_frame,
            )
            baseline_scores, label_counts = run_full_label_prompt(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                prompt=prompt,
                injection_layer=injection_layers[0],
                patch_vector=None,
                patch_alpha=0.0,
                max_length=max_length,
                labels_by_role=labels_by_role,
                label_score_normalization=label_score_normalization,
            )
            probe_specs.append(
                {
                    "prompt": prompt,
                    "option_order": None,
                    "token_ids": None,
                    "baseline_scores": baseline_scores,
                    "label_token_counts": label_counts,
                }
            )
        else:
            raise ValueError(f"Unknown scoring surface: {scoring_surface}")
        for injection_layer in injection_layers:
            for patch_text_regime in patch_text_regimes:
                patch_vectors_by_concept = {}
                for concept_id, definition_text in definition_text_by_concept.items():
                    if patch_text_regime == "definition":
                        patch_vectors_by_concept[concept_id] = patch_base_vectors[
                            concept_id
                        ][injection_layer]
                        continue
                    patch_prompt = source_text_for_regime(
                        definition_text=definition_text,
                        label=labels_by_concept[concept_id],
                        patch_text_regime=patch_text_regime,
                        shuffled_label=shuffled_labels[concept_id],
                    )
                    patch_vectors_by_concept[concept_id] = prompt_vectors_for_surface(
                        torch=torch,
                        tokenizer=tokenizer,
                        model=model,
                        prompt=patch_prompt,
                        layers=[injection_layer],
                        max_length=max_length,
                        patch_vector_surface=patch_vector_surface,
                    )[injection_layer]
                for mode in patch_modes:
                    patch_concept = patch_concept_for_mode(pair, mode)
                    for patch_alpha in patch_alphas:
                        for probe_spec in probe_specs:
                            prompt = str(probe_spec["prompt"])
                            baseline_scores = probe_spec["baseline_scores"]
                            if scoring_surface == "option_token":
                                patched_scores = run_behavior_prompt(
                                    torch=torch,
                                    tokenizer=tokenizer,
                                    model=model,
                                    prompt=prompt,
                                    injection_layer=injection_layer,
                                    patch_vector=patch_vectors_by_concept[
                                        patch_concept
                                    ],
                                    patch_alpha=patch_alpha,
                                    max_length=max_length,
                                    token_ids=probe_spec["token_ids"],
                                )
                                label_token_counts = None
                            else:
                                patched_scores, label_token_counts = (
                                    run_full_label_prompt(
                                        torch=torch,
                                        tokenizer=tokenizer,
                                        model=model,
                                        prompt=prompt,
                                        injection_layer=injection_layer,
                                        patch_vector=patch_vectors_by_concept[
                                            patch_concept
                                        ],
                                        patch_alpha=patch_alpha,
                                        max_length=max_length,
                                        labels_by_role=labels_by_role,
                                        label_score_normalization=(
                                            label_score_normalization
                                        ),
                                    )
                                )
                            option_order = probe_spec["option_order"]
                            rows.append(
                                {
                                    "pair": str(pair["id"]),
                                    "left": left,
                                    "right": right,
                                    "kind": str(pair["kind"]),
                                    "distractor": distractor,
                                    "random_patch": random_patch,
                                    "random_patch_scope": str(
                                        pair["random_patch_scope"],
                                    ),
                                    "injection_layer": injection_layer,
                                    "patch_text_regime": patch_text_regime,
                                    "patch_mode": mode,
                                    "patch_concept": patch_concept,
                                    "patch_concept_label": labels_by_concept[
                                        patch_concept
                                    ],
                                    "patch_concept_shuffled_label": shuffled_labels[
                                        patch_concept
                                    ],
                                    "patch_context": "label_free_behavior_gate",
                                    "prompt_frame": prompt_frame,
                                    "scoring_surface": scoring_surface,
                                    "label_score_normalization": (
                                        label_score_normalization
                                    ),
                                    "eval_variant_index": eval_variant_index,
                                    "patch_alpha": patch_alpha,
                                    "patch_vector_surface": patch_vector_surface,
                                    "source_prompt": source_prompt,
                                    "behavior_prompt": prompt,
                                    "option_order": (
                                        list(option_order)
                                        if option_order is not None
                                        else []
                                    ),
                                    "label_token_counts": label_token_counts,
                                    "scores": {
                                        "baseline": baseline_scores,
                                        "patched": patched_scores,
                                    },
                                    "summary": summarize_behavior_delta(
                                        baseline_scores=baseline_scores,
                                        patched_scores=patched_scores,
                                    ),
                                }
                            )
    return {"rows": rows}


@app.local_entrypoint()
def main(
    concepts: str = "experiments/concept_geometry/concept_set.json",
    paraphrases: str = "experiments/concept_geometry/concept_paraphrases.json",
    model_id: str = DEFAULT_MODEL_ID,
    injection_layers: str = str(DEFAULT_INJECTION_LAYER),
    max_length: int = 160,
    eval_variant: int = 2,
    patch_alpha: float = 1.0,
    patch_alphas: str = "",
    patch_vector_surface: str = DEFAULT_PATCH_VECTOR_SURFACE,
    prompt_frame: str = DEFAULT_PROMPT_FRAME,
    scoring_surface: str = DEFAULT_SCORING_SURFACE,
    label_score_normalization: str = DEFAULT_LABEL_SCORE_NORMALIZATION,
    patch_modes: str = DEFAULT_PATCH_MODES,
    patch_text_regimes: str = DEFAULT_PATCH_TEXT_REGIMES,
    option_orders: str = DEFAULT_OPTION_ORDERS,
    pair_set: str = "focus",
    baseline_sample_count: int = 8,
    seed: int = 20260608,
    out: str = "artifacts/activation_geometry/modal_label_free_behavior_gate.json",
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
        attach_random_patch_concepts,
        write_payload,
    )
    from experiments.activation_geometry.label_free_behavior_gate import (
        PATCH_TEXT_REGIMES,
        PATCH_VECTOR_SURFACES,
        PROMPT_FRAMES,
        SCORING_SURFACES,
        aggregate_rows,
        gate_summaries,
        public_summary,
        specificity_rows,
    )
    from experiments.activation_geometry.label_free_readout_basin import (
        pair_specs_for_set,
        serializable_pair_specs,
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
    parsed_injection_layers = parse_ints(injection_layers, name="injection layer")
    parsed_patch_alphas = (
        parse_floats(patch_alphas, name="patch alpha")
        if patch_alphas.strip()
        else [patch_alpha]
    )
    parsed_patch_modes = parse_values(
        patch_modes,
        allowed=PATCH_MODES,
        name="Patch modes",
    )
    parsed_patch_text_regimes = parse_values(
        patch_text_regimes,
        allowed=PATCH_TEXT_REGIMES,
        name="Patch text regimes",
    )
    parsed_patch_vector_surface = parse_values(
        patch_vector_surface,
        allowed=PATCH_VECTOR_SURFACES,
        name="Patch vector surface",
    )[0]
    parsed_prompt_frame = parse_values(
        prompt_frame,
        allowed=PROMPT_FRAMES,
        name="Prompt frame",
    )[0]
    parsed_scoring_surface = parse_values(
        scoring_surface,
        allowed=SCORING_SURFACES,
        name="Scoring surface",
    )[0]
    parsed_label_score_normalization = parse_values(
        label_score_normalization,
        allowed=LABEL_SCORE_NORMALIZATIONS,
        name="Label score normalization",
    )[0]
    parsed_option_orders = parse_option_orders(option_orders)
    pair_specs = attach_random_patch_concepts(
        serializable_concepts,
        serializable_pair_specs(
            pair_specs_for_set(
                serializable_concepts,
                pair_set=pair_set,
                sample_count=baseline_sample_count,
                seed=seed,
            )
        ),
        seed=seed,
    )
    remote_payload = run_label_free_behavior_remote.remote(
        serializable_concepts,
        serializable_records,
        pair_specs,
        model_id,
        parsed_injection_layers,
        parsed_patch_modes,
        parsed_patch_text_regimes,
        eval_variant,
        parsed_patch_alphas,
        parsed_patch_vector_surface,
        parsed_prompt_frame,
        parsed_scoring_surface,
        parsed_label_score_normalization,
        parsed_option_orders,
        max_length,
    )
    aggregates = aggregate_rows(remote_payload["rows"])
    specificity = specificity_rows(aggregates)
    payload = {
        "manifest": {
            "model_id": model_id,
            "concept_source": concepts,
            "paraphrase_source": paraphrases,
            "patch_context": "label_free_behavior_gate",
            "injection_layers": parsed_injection_layers,
            "eval_variant_index": eval_variant,
            "patch_alpha": (
                parsed_patch_alphas[0] if len(parsed_patch_alphas) == 1 else None
            ),
            "patch_alphas": parsed_patch_alphas,
            "patch_vector_surface": parsed_patch_vector_surface,
            "prompt_frame": parsed_prompt_frame,
            "scoring_surface": parsed_scoring_surface,
            "label_score_normalization": parsed_label_score_normalization,
            "patch_modes": parsed_patch_modes,
            "patch_text_regimes": parsed_patch_text_regimes,
            "option_orders": [list(order) for order in parsed_option_orders],
            "pair_set": pair_set,
            "baseline_sample_count": baseline_sample_count,
            "max_length": max_length,
            "seed": seed,
            "pairs": pair_specs,
        },
        "rows": remote_payload["rows"],
        "aggregate_rows": aggregates,
        "specificity_rows": specificity,
        "gate_summaries": gate_summaries(specificity),
    }
    if out and out.lower() != "none":
        write_payload(Path(out), payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))
