#!/usr/bin/env python3
"""Modal entrypoint for answer-surface basin patching diagnostics."""

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
DEFAULT_LABEL_REGIMES = "canonical,alias,symbol"
DEFAULT_PATCH_TEXT_REGIMES = "definition,neutral"
OPTION_ROLES = ("source", "target", "distractor")
PROMPT_FRAMES = {
    "dynamics": "Choose the concept most directly linked to stable-state dynamics.",
}
ALIAS_LABELS = {
    "attractor": "stable-state basin",
    "attractor_network": "recurrent stable-state network",
    "basin_of_attraction": "convergence region",
    "conceptual_space": "geometric meaning space",
    "prototype": "central example pattern",
    "schema": "structured expectation pattern",
}
SYMBOL_LABELS = {
    "attractor": "signal alpha",
    "attractor_network": "signal beta",
    "basin_of_attraction": "signal gamma",
    "conceptual_space": "signal delta",
    "prototype": "signal epsilon",
    "schema": "signal zeta",
}
IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-answer-surface-basin")


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


def option_order_key(order: tuple[str, str, str]) -> str:
    initials = {
        "source": "s",
        "target": "t",
        "distractor": "d",
    }
    return "".join(initials[role] for role in order)


def prompt_instruction(frame: str) -> str:
    if frame not in PROMPT_FRAMES:
        options = ", ".join(sorted(PROMPT_FRAMES))
        raise ValueError(f"Prompt frame must be one of: {options}")
    return PROMPT_FRAMES[frame]


def concept_label(
    *,
    concept_id: str,
    canonical_label: str,
    label_regime: str,
) -> str:
    if label_regime == "canonical":
        return canonical_label
    if label_regime == "alias":
        return ALIAS_LABELS.get(concept_id, canonical_label)
    if label_regime == "symbol":
        return SYMBOL_LABELS.get(concept_id, f"signal {concept_id.replace('_', '-')}")
    raise ValueError(f"Unknown label regime: {label_regime}")


def neutral_carrier_text(*, label: str) -> str:
    return f"Concept label: {label}."


def source_text_for_regime(
    *,
    definition_text: str,
    label: str,
    patch_text_regime: str,
) -> str:
    if patch_text_regime == "definition":
        return definition_text
    if patch_text_regime == "neutral":
        return neutral_carrier_text(label=label)
    raise ValueError(f"Unknown patch text regime: {patch_text_regime}")


def calibration_prompt(
    *,
    source_text: str,
    labels_by_role: dict[str, str],
    option_order: tuple[str, str, str],
    prompt_frame: str,
) -> str:
    invalid_roles = sorted(set(option_order) - set(OPTION_ROLES))
    if invalid_roles:
        raise ValueError(f"Unknown option roles: {', '.join(invalid_roles)}")
    lines = [
        source_text,
        "",
        prompt_instruction(prompt_frame),
    ]
    for slot, role in zip(("A", "B", "C"), option_order, strict=True):
        lines.append(f"{slot}. {labels_by_role[role]}")
    lines.append("Answer:")
    return "\n".join(lines)


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


def prompt_final_token_activation(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    max_length: int,
) -> Any:
    encoded = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )
    device = next(model.parameters()).device
    encoded = {name: value.to(device) for name, value in encoded.items()}
    block = block_for_hidden_state_layer(model, layer)
    final_indices = encoded["attention_mask"].to(device).sum(dim=1).long() - 1
    captured: dict[str, Any] = {}

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        batch_indices = torch.arange(hidden_states.shape[0], device=hidden_states.device)
        captured["activation"] = (
            hidden_states[batch_indices, final_indices].detach().float().cpu()
        )
        return output

    handle = block.register_forward_hook(hook)
    with torch.inference_mode():
        try:
            model(**encoded, use_cache=False)
        finally:
            handle.remove()
    if "activation" not in captured:
        raise ValueError(f"Failed to capture activation at layer {layer}")
    return captured["activation"][0]


def heldout_source_text(
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
            f"Expected one text for {concept_id} variant {variant_index}; found {len(matches)}"
        )
    return matches[0]


@app.function(image=IMAGE, timeout=2400)
def run_answer_surface_basin_remote(
    concepts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    layer_roles: dict[str, int],
    patch_modes: list[str],
    option_orders: list[list[str]],
    label_regimes: list[str],
    patch_text_regimes: list[str],
    context_variant_index: int,
    patch_alpha: float,
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
    concept_lookup = {str(concept["id"]): concept for concept in concepts}

    rows = []
    for role, layer in layer_roles.items():
        for pair in pair_specs:
            left = str(pair["left"])
            right = str(pair["right"])
            distractor = str(pair["distractor"])
            random_patch = str(pair["random_patch"])
            concept_ids = sorted({left, right, distractor, random_patch})
            definition_text_by_concept = {
                concept_id: heldout_source_text(
                    records,
                    concept_id=concept_id,
                    variant_index=context_variant_index,
                )
                for concept_id in concept_ids
            }
            for label_regime in label_regimes:
                label_by_concept = {
                    concept_id: concept_label(
                        concept_id=concept_id,
                        canonical_label=str(concept_lookup[concept_id]["label"]),
                        label_regime=label_regime,
                    )
                    for concept_id in concept_ids
                }
                labels_by_role = {
                    "source": label_by_concept[left],
                    "target": label_by_concept[right],
                    "distractor": label_by_concept[distractor],
                }
                for patch_text_regime in patch_text_regimes:
                    patch_source_text_by_concept = {
                        concept_id: source_text_for_regime(
                            definition_text=definition_text_by_concept[concept_id],
                            label=label_by_concept[concept_id],
                            patch_text_regime=patch_text_regime,
                        )
                        for concept_id in concept_ids
                    }
                    for order_row in option_orders:
                        if len(order_row) != 3:
                            raise ValueError(
                                f"Option order must contain three roles: {order_row}"
                            )
                        option_order = (
                            str(order_row[0]),
                            str(order_row[1]),
                            str(order_row[2]),
                        )
                        source_prompt = calibration_prompt(
                            source_text=definition_text_by_concept[left],
                            labels_by_role=labels_by_role,
                            option_order=option_order,
                            prompt_frame=str(pair["prompt_frame"]),
                        )
                        token_ids = role_token_ids(option_order, token_ids_by_slot)
                        baseline_scores = run_prompt(
                            torch=torch,
                            tokenizer=tokenizer,
                            model=model,
                            prompt=source_prompt,
                            layer=layer,
                            patch_vector=None,
                            patch_alpha=patch_alpha,
                            max_length=max_length,
                            token_ids=token_ids,
                        )
                        for mode in patch_modes:
                            patch_concept = patch_concept_for_mode(pair, mode)
                            patch_prompt = calibration_prompt(
                                source_text=patch_source_text_by_concept[patch_concept],
                                labels_by_role=labels_by_role,
                                option_order=option_order,
                                prompt_frame=str(pair["prompt_frame"]),
                            )
                            patch_vector = prompt_final_token_activation(
                                torch=torch,
                                tokenizer=tokenizer,
                                model=model,
                                prompt=patch_prompt,
                                layer=layer,
                                max_length=max_length,
                            ).to(device)
                            patched_scores = run_prompt(
                                torch=torch,
                                tokenizer=tokenizer,
                                model=model,
                                prompt=source_prompt,
                                layer=layer,
                                patch_vector=patch_vector,
                                patch_alpha=patch_alpha,
                                max_length=max_length,
                                token_ids=token_ids,
                            )
                            rows.append(
                                {
                                    "pair": str(pair["id"]),
                                    "left": left,
                                    "right": right,
                                    "kind": str(pair["kind"]),
                                    "distractor": distractor,
                                    "random_patch": random_patch,
                                    "random_patch_scope": str(
                                        pair["random_patch_scope"]
                                    ),
                                    "prompt_frame": str(pair["prompt_frame"]),
                                    "role": role,
                                    "layer": layer,
                                    "label_regime": label_regime,
                                    "patch_text_regime": patch_text_regime,
                                    "patch_mode": mode,
                                    "patch_concept": patch_concept,
                                    "patch_concept_label": label_by_concept.get(
                                        patch_concept,
                                        str(concept_lookup[patch_concept]["label"]),
                                    ),
                                    "patch_context": "answer_surface_basin",
                                    "context_variant_index": context_variant_index,
                                    "patch_alpha": patch_alpha,
                                    "option_order": option_order_key(option_order),
                                    "prompt": source_prompt,
                                    "patch_prompt": patch_prompt,
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
    control_layer: int = 6,
    max_length: int = 128,
    context_variant: int = 0,
    patch_alpha: float = 1.0,
    patch_modes: str = DEFAULT_PATCH_MODES,
    option_orders: str = DEFAULT_OPTION_ORDERS,
    label_regimes: str = DEFAULT_LABEL_REGIMES,
    patch_text_regimes: str = DEFAULT_PATCH_TEXT_REGIMES,
    seed: int = 20260608,
    out: str = "artifacts/activation_geometry/modal_answer_surface_basin.json",
) -> None:
    resolved_path = Path(__file__).resolve()
    repo_root = resolved_path.parents[2] if len(resolved_path.parents) > 2 else Path.cwd()
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    from experiments.activation_geometry.activation_geometry_probe import (
        activation_records,
        load_concepts,
    )
    from experiments.activation_geometry.answer_surface_basin_diagnostic import (
        LABEL_REGIMES,
        PATCH_TEXT_REGIMES,
        aggregate_rows,
        answer_surface_pair_specs,
        gate_summaries,
        public_summary,
        serializable_pair_specs,
        specificity_rows,
    )
    from experiments.activation_geometry.causal_patching_diagnostic import (
        PATCH_MODES,
        attach_random_patch_concepts,
        write_payload,
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
        "control": control_layer,
    }
    parsed_patch_modes = parse_values(
        patch_modes,
        allowed=PATCH_MODES,
        name="Patch modes",
    )
    parsed_option_orders = parse_option_orders(option_orders)
    parsed_label_regimes = parse_values(
        label_regimes,
        allowed=LABEL_REGIMES,
        name="Label regimes",
    )
    parsed_patch_text_regimes = parse_values(
        patch_text_regimes,
        allowed=PATCH_TEXT_REGIMES,
        name="Patch text regimes",
    )
    pair_specs = attach_random_patch_concepts(
        serializable_concepts,
        serializable_pair_specs(answer_surface_pair_specs()),
        seed=seed,
    )
    remote_payload = run_answer_surface_basin_remote.remote(
        serializable_concepts,
        serializable_records,
        pair_specs,
        model_id,
        layer_roles,
        parsed_patch_modes,
        [list(order) for order in parsed_option_orders],
        parsed_label_regimes,
        parsed_patch_text_regimes,
        context_variant,
        patch_alpha,
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
            "patch_context": "answer_surface_basin",
            "layer_roles": layer_roles,
            "context_variant_index": context_variant,
            "patch_alpha": patch_alpha,
            "patch_modes": parsed_patch_modes,
            "option_orders": [
                "".join(role[0] for role in order)
                for order in parsed_option_orders
            ],
            "label_regimes": parsed_label_regimes,
            "patch_text_regimes": parsed_patch_text_regimes,
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
        "Run with: modal run experiments/activation_geometry/modal_answer_surface_basin.py",
        file=sys.stderr,
    )
