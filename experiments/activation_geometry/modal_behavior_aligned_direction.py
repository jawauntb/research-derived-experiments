#!/usr/bin/env python3
"""Modal entrypoint for learned behavior-aligned direction pilots."""

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
DEFAULT_DIRECTION_MODES = "target_learned,source_learned,distractor_learned,random_same_norm"
IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-behavior-aligned-direction")


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


def objective_role_for_mode(mode: str) -> str:
    if mode == "target_learned":
        return "target"
    if mode == "source_learned":
        return "source"
    if mode == "distractor_learned":
        return "distractor"
    if mode == "random_same_norm":
        return "target"
    raise ValueError(f"Unknown direction mode: {mode}")


def mean_tensor(torch: Any, vectors: list[Any]) -> Any:
    if not vectors:
        raise ValueError("Cannot average an empty vector list")
    return torch.stack(vectors, dim=0).mean(dim=0)


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
            f"Expected one heldout text for {concept_id} variant {holdout_variant_index}; "
            f"found {len(matches)}"
        )
    return matches[0]


def train_source_texts(
    records: list[dict[str, Any]],
    *,
    concept_id: str,
    train_variant_indices: set[int],
) -> list[tuple[int, str]]:
    rows = [
        (int(record["variant_index"]), str(record["text"]))
        for record in records
        if str(record["concept_id"]) == concept_id
        and int(record["variant_index"]) in train_variant_indices
    ]
    if not rows:
        variants = ",".join(str(index) for index in sorted(train_variant_indices))
        raise ValueError(f"Missing train texts for {concept_id} variants {variants}")
    return sorted(rows)


def objective_margin(logprobs: Any, token_ids: dict[str, int], role: str) -> Any:
    roles = ("source", "target", "distractor")
    if role not in roles:
        raise ValueError(f"Unknown objective role: {role}")
    others = [name for name in roles if name != role]
    return logprobs[token_ids[role]] - 0.5 * sum(logprobs[token_ids[name]] for name in others)


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_behavior_delta(
    *,
    baseline_scores: dict[str, float],
    steered_scores: dict[str, float],
) -> dict[str, Any]:
    baseline_margin = target_margin(baseline_scores)
    steered_margin = target_margin(steered_scores)
    return {
        "baseline_target_margin": baseline_margin,
        "steered_target_margin": steered_margin,
        "target_margin_delta": steered_margin - baseline_margin,
        "target_logprob_delta": steered_scores["target"] - baseline_scores["target"],
        "target_minus_source_delta": (
            (steered_scores["target"] - steered_scores["source"])
            - (baseline_scores["target"] - baseline_scores["source"])
        ),
        "target_minus_distractor_delta": (
            (steered_scores["target"] - steered_scores["distractor"])
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
        raise ValueError("Steering layer must be a transformer block output, not layer 0")
    blocks = transformer_blocks(model)
    block_index = layer - 1
    if not 0 <= block_index < len(blocks):
        raise ValueError(
            f"Layer {layer} maps to block {block_index}, "
            f"outside block range 0..{len(blocks) - 1}"
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


def add_final_token_hook(
    *,
    torch: Any,
    model: Any,
    layer: int,
    attention_mask: Any,
    delta: Any,
) -> Any:
    block = block_for_hidden_state_layer(model, layer)
    final_indices = attention_mask.to(delta.device).sum(dim=1).long() - 1

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        adjusted = hidden_states.clone()
        batch_indices = torch.arange(adjusted.shape[0], device=adjusted.device)
        adjusted[batch_indices, final_indices] = (
            adjusted[batch_indices, final_indices]
            + delta.to(device=adjusted.device, dtype=adjusted.dtype)
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
    delta: Any | None,
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
    if delta is not None:
        handle = add_final_token_hook(
            torch=torch,
            model=model,
            layer=layer,
            attention_mask=encoded["attention_mask"],
            delta=delta,
        )
    try:
        with torch.inference_mode():
            outputs = model(**encoded, use_cache=False)
    finally:
        if handle is not None:
            handle.remove()
    logits = outputs.logits[0, -1].float()
    return option_logprobs(torch, logits, token_ids)


def gradient_direction_for_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    max_length: int,
    token_ids: dict[str, int],
    objective_role: str,
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

    def capture_hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        batch_indices = torch.arange(hidden_states.shape[0], device=hidden_states.device)
        selected = hidden_states[batch_indices, final_indices].detach().clone()
        selected.requires_grad_(True)
        adjusted = hidden_states.clone()
        adjusted[batch_indices, final_indices] = selected
        captured["selected"] = selected
        if isinstance(output, tuple):
            return (adjusted, *output[1:])
        return adjusted

    model.zero_grad(set_to_none=True)
    handle = block.register_forward_hook(capture_hook)
    try:
        outputs = model(**encoded, use_cache=False)
        logits = outputs.logits[0, -1].float()
        logprobs = torch.nn.functional.log_softmax(logits, dim=-1)
        objective = objective_margin(logprobs, token_ids, objective_role)
        objective.backward()
        selected = captured.get("selected")
        if selected is None or selected.grad is None:
            raise RuntimeError("Could not capture final-token activation gradient")
        return selected.grad[0].detach().float().cpu()
    finally:
        handle.remove()
        model.zero_grad(set_to_none=True)


def learned_gradient_direction(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    source_texts: list[tuple[int, str]],
    labels_by_role: dict[str, str],
    option_orders: list[tuple[str, str, str]],
    token_ids_by_slot: dict[str, int],
    layer: int,
    max_length: int,
    objective_role: str,
) -> Any:
    gradients = []
    for _variant_index, source_text in source_texts:
        for option_order in option_orders:
            prompt = calibration_prompt(
                source_text=source_text,
                labels_by_role=labels_by_role,
                option_order=option_order,
            )
            gradients.append(
                gradient_direction_for_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    prompt=prompt,
                    layer=layer,
                    max_length=max_length,
                    token_ids=role_token_ids(option_order, token_ids_by_slot),
                    objective_role=objective_role,
                )
            )
    return mean_tensor(torch, gradients)


def random_same_norm(
    *,
    torch: Any,
    direction: Any,
    seed: int,
) -> Any:
    generator = torch.Generator(device=direction.device)
    generator.manual_seed(seed)
    random_vector = torch.randn(direction.shape, generator=generator, device=direction.device)
    random_norm = torch.linalg.vector_norm(random_vector).clamp(min=1e-12)
    direction_norm = torch.linalg.vector_norm(direction)
    return random_vector * (direction_norm / random_norm)


def cosine_or_none(torch: Any, left: Any | None, right: Any | None) -> float | None:
    if left is None or right is None:
        return None
    left_norm = torch.linalg.vector_norm(left)
    right_norm = torch.linalg.vector_norm(right)
    if float(left_norm.item()) == 0.0 or float(right_norm.item()) == 0.0:
        return None
    return float(torch.nn.functional.cosine_similarity(left.float(), right.float(), dim=0).item())


def direction_for_mode(
    *,
    torch: Any,
    learned_directions: dict[str, Any],
    mode: str,
    seed: int,
) -> Any:
    if mode == "random_same_norm":
        return random_same_norm(
            torch=torch,
            direction=learned_directions["target"],
            seed=seed,
        )
    return learned_directions[objective_role_for_mode(mode)]


def parse_remote_option_orders(rows: list[list[str]]) -> list[tuple[str, str, str]]:
    option_orders = []
    for row in rows:
        if len(row) != 3:
            raise ValueError(f"Option order must contain three roles: {row}")
        option_orders.append((str(row[0]), str(row[1]), str(row[2])))
    return option_orders


@app.function(image=IMAGE, timeout=3000)
def run_behavior_aligned_direction_remote(
    concepts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    layer_roles: dict[str, int],
    scales: list[float],
    direction_modes: list[str],
    option_orders: list[list[str]],
    train_variant_indices: list[int],
    holdout_variant_index: int,
    max_length: int,
    seed: int,
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
    parsed_orders = parse_remote_option_orders(option_orders)
    train_variants = set(train_variant_indices)
    concept_lookup = {str(concept["id"]): concept for concept in concepts}

    rows = []
    for role, layer in layer_roles.items():
        for pair_index, pair in enumerate(pair_specs):
            left = str(pair["left"])
            right = str(pair["right"])
            distractor = str(pair["distractor"])
            labels_by_role = {
                "source": str(concept_lookup[left]["label"]),
                "target": str(concept_lookup[right]["label"]),
                "distractor": str(concept_lookup[distractor]["label"]),
            }
            source_texts = train_source_texts(
                records,
                concept_id=left,
                train_variant_indices=train_variants,
            )
            learned_directions = {
                objective_role: learned_gradient_direction(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    source_texts=source_texts,
                    labels_by_role=labels_by_role,
                    option_orders=parsed_orders,
                    token_ids_by_slot=token_ids_by_slot,
                    layer=layer,
                    max_length=max_length,
                    objective_role=objective_role,
                ).to(device)
                for objective_role in ("target", "source", "distractor")
            }
            norms = {
                objective_role: float(torch.linalg.vector_norm(direction).item())
                for objective_role, direction in learned_directions.items()
            }
            learned_alignment = {
                "target_source_cosine": cosine_or_none(
                    torch,
                    learned_directions["target"],
                    learned_directions["source"],
                ),
                "target_distractor_cosine": cosine_or_none(
                    torch,
                    learned_directions["target"],
                    learned_directions["distractor"],
                ),
            }
            heldout_text = heldout_source_text(
                records,
                concept_id=left,
                holdout_variant_index=holdout_variant_index,
            )
            for order_index, option_order in enumerate(parsed_orders):
                prompt = calibration_prompt(
                    source_text=heldout_text,
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
                    delta=None,
                    max_length=max_length,
                    token_ids=token_ids,
                )
                for scale_index, scale in enumerate(scales):
                    for mode_index, mode in enumerate(direction_modes):
                        direction = direction_for_mode(
                            torch=torch,
                            learned_directions=learned_directions,
                            mode=mode,
                            seed=(
                                seed
                                + layer * 100_003
                                + pair_index * 1_009
                                + order_index * 97
                                + scale_index * 13
                                + mode_index
                            ),
                        )
                        delta = direction * float(scale)
                        steered_scores = run_prompt(
                            torch=torch,
                            tokenizer=tokenizer,
                            model=model,
                            prompt=prompt,
                            layer=layer,
                            delta=delta,
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
                                "role": role,
                                "layer": layer,
                                "scale": float(scale),
                                "direction_mode": mode,
                                "objective_role": objective_role_for_mode(mode),
                                "option_order": option_order_key(option_order),
                                "prompt": prompt,
                                "train_variant_indices": sorted(train_variants),
                                "holdout_variant_index": holdout_variant_index,
                                "norms": norms,
                                "learned_alignment": learned_alignment,
                                "scores": {
                                    "baseline": baseline_scores,
                                    "steered": steered_scores,
                                },
                                "summary": summarize_behavior_delta(
                                    baseline_scores=baseline_scores,
                                    steered_scores=steered_scores,
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
    max_length: int = 128,
    train_variants: str = "0,1",
    holdout_variant: int = 2,
    scales: str = "1.0",
    direction_modes: str = DEFAULT_DIRECTION_MODES,
    option_orders: str = DEFAULT_OPTION_ORDERS,
    seed: int = 20260608,
    out: str = "artifacts/activation_geometry/modal_behavior_aligned_direction.json",
) -> None:
    resolved_path = Path(__file__).resolve()
    repo_root = resolved_path.parents[2] if len(resolved_path.parents) > 2 else Path.cwd()
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    from experiments.activation_geometry.activation_geometry_probe import (
        activation_records,
        load_concepts,
        parse_layers,
    )
    from experiments.activation_geometry.behavior_aligned_direction import (
        aggregate_rows,
        alignment_summary,
        gate_summaries,
        parse_direction_modes,
        public_summary,
        write_payload,
    )
    from experiments.activation_geometry.final_token_steering_pilot import (
        default_pair_specs,
        parse_scales,
        serializable_pair_specs,
    )
    from experiments.activation_geometry.steering_calibration_diagnostic import (
        parse_option_orders,
    )

    concept_rows = load_concepts(Path(concepts))
    records = activation_records(concept_rows, Path(paraphrases))
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
    parsed_direction_modes = parse_direction_modes(direction_modes)
    parsed_option_orders = parse_option_orders(option_orders)
    parsed_train_variants = parse_layers(train_variants)
    parsed_scales = parse_scales(scales)
    pair_specs = default_pair_specs(concept_rows)
    remote_payload = run_behavior_aligned_direction_remote.remote(
        [concept.__dict__ for concept in concept_rows],
        serializable_records,
        serializable_pair_specs(pair_specs),
        model_id,
        layer_roles,
        parsed_scales,
        parsed_direction_modes,
        [list(order) for order in parsed_option_orders],
        parsed_train_variants,
        holdout_variant,
        max_length,
        seed,
    )
    aggregates = aggregate_rows(remote_payload["rows"])
    payload = {
        "manifest": {
            "model_id": model_id,
            "concept_source": concepts,
            "paraphrase_source": paraphrases,
            "pooling": "final-token",
            "layer_roles": layer_roles,
            "train_variant_indices": parsed_train_variants,
            "holdout_variant_index": holdout_variant,
            "scales": parsed_scales,
            "direction_modes": parsed_direction_modes,
            "option_orders": [
                "".join(role[0] for role in order)
                for order in parsed_option_orders
            ],
            "max_length": max_length,
            "seed": seed,
            "pairs": serializable_pair_specs(pair_specs),
            "slot_token_ids": remote_payload["slot_token_ids"],
        },
        "rows": remote_payload["rows"],
        "aggregate_rows": aggregates,
        "gate_summaries": gate_summaries(aggregates),
        "alignment_summary": alignment_summary(remote_payload["rows"]),
    }
    if out and out.lower() != "none":
        write_payload(Path(out), payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    print(
        "Run with: modal run experiments/activation_geometry/modal_behavior_aligned_direction.py",
        file=sys.stderr,
    )
