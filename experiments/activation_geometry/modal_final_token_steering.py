#!/usr/bin/env python3
"""Modal entrypoint for final-token activation steering pilots."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


DEFAULT_MODEL_ID = "EleutherAI/pythia-70m-deduped"
DEFAULT_SCALES = "0.5,1.0"
IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-final-token-steering")


def pair_id(left: str, right: str) -> str:
    return f"{left}->{right}"


def steering_prompt(
    *,
    source_text: str,
    source_label: str,
    target_label: str,
    distractor_label: str,
) -> str:
    return (
        f"{source_text}\n\n"
        "Choose the closest related concept.\n"
        f"A. {source_label}\n"
        f"B. {target_label}\n"
        f"C. {distractor_label}\n"
        "Answer:"
    )


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def target_minus_source(scores: dict[str, float]) -> float:
    return scores["target"] - scores["source"]


def summarize_scale(
    *,
    baseline_scores: dict[str, float],
    forward_scores: dict[str, float],
    reverse_scores: dict[str, float],
) -> dict[str, Any]:
    baseline_margin = target_margin(baseline_scores)
    forward_margin = target_margin(forward_scores)
    reverse_margin = target_margin(reverse_scores)
    baseline_target_minus_source = target_minus_source(baseline_scores)
    forward_target_minus_source = target_minus_source(forward_scores)
    reverse_target_minus_source = target_minus_source(reverse_scores)
    forward_delta = forward_margin - baseline_margin
    reverse_delta = reverse_margin - baseline_margin
    return {
        "baseline_target_margin": baseline_margin,
        "forward_target_margin": forward_margin,
        "reverse_target_margin": reverse_margin,
        "forward_margin_delta": forward_delta,
        "reverse_margin_delta": reverse_delta,
        "signed_margin_effect": forward_delta - reverse_delta,
        "baseline_target_minus_source": baseline_target_minus_source,
        "forward_target_minus_source": forward_target_minus_source,
        "reverse_target_minus_source": reverse_target_minus_source,
        "forward_target_minus_source_delta": (
            forward_target_minus_source - baseline_target_minus_source
        ),
        "reverse_target_minus_source_delta": (
            reverse_target_minus_source - baseline_target_minus_source
        ),
        "passes_signed_margin_gate": forward_delta > 0 and reverse_delta < 0,
    }


def gate_summary(rows: list[dict[str, Any]], *, scale: float) -> dict[str, Any]:
    selected = [row for row in rows if row["scale"] == scale]
    primary_positive = [
        row for row in selected if row["role"] == "primary" and row["kind"] == "positive"
    ]
    backup_positive = [
        row for row in selected if row["role"] == "backup" and row["kind"] == "positive"
    ]
    control_positive = [
        row for row in selected if row["role"] == "control" and row["kind"] == "positive"
    ]
    primary_controls = [
        row for row in selected if row["role"] == "primary" and row["kind"] == "control"
    ]
    return {
        "scale": scale,
        "primary_positive_pass_count": sum(
            1 for row in primary_positive if row["summary"]["passes_signed_margin_gate"]
        ),
        "primary_positive_total": len(primary_positive),
        "backup_positive_pass_count": sum(
            1 for row in backup_positive if row["summary"]["passes_signed_margin_gate"]
        ),
        "backup_positive_total": len(backup_positive),
        "control_layer_positive_pass_count": sum(
            1 for row in control_positive if row["summary"]["passes_signed_margin_gate"]
        ),
        "control_layer_positive_total": len(control_positive),
        "primary_valence_control_pass_count": sum(
            1 for row in primary_controls if row["summary"]["passes_signed_margin_gate"]
        ),
        "primary_valence_control_total": len(primary_controls),
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
        raise ValueError("Steering layer must be a transformer block output, not layer 0")
    blocks = transformer_blocks(model)
    block_index = layer - 1
    if not 0 <= block_index < len(blocks):
        raise ValueError(
            f"Layer {layer} maps to block {block_index}, outside block range 0..{len(blocks) - 1}"
        )
    return blocks[block_index]


def mean_tensor(torch: Any, vectors: list[Any]) -> Any:
    return torch.stack(vectors, dim=0).mean(dim=0)


def option_token_ids(tokenizer: Any) -> dict[str, int]:
    tokens = {}
    for key, label in (("source", " A"), ("target", " B"), ("distractor", " C")):
        ids = tokenizer.encode(label, add_special_tokens=False)
        if not ids:
            raise ValueError(f"Could not encode option token {label!r}")
        tokens[key] = int(ids[0])
    return tokens


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
            adjusted[batch_indices, final_indices] + delta.to(adjusted.device)
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


def direction_for_pair(
    *,
    torch: Any,
    records: list[dict[str, Any]],
    activations_by_record: dict[str, Any],
    left: str,
    right: str,
    train_variant_indices: set[int],
) -> Any:
    source_vectors = [
        activations_by_record[str(record["id"])]
        for record in records
        if str(record["concept_id"]) == left
        and int(record["variant_index"]) in train_variant_indices
    ]
    target_vectors = [
        activations_by_record[str(record["id"])]
        for record in records
        if str(record["concept_id"]) == right
        and int(record["variant_index"]) in train_variant_indices
    ]
    if not source_vectors or not target_vectors:
        raise ValueError(f"Missing train activations for {left}->{right}")
    return mean_tensor(torch, target_vectors) - mean_tensor(torch, source_vectors)


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


@app.function(image=IMAGE, timeout=1800)
def run_final_token_steering_remote(
    concepts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    layer_roles: dict[str, int],
    scales: list[float],
    train_variant_indices: list[int],
    holdout_variant_index: int,
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
    token_ids = option_token_ids(tokenizer)

    layers = list(dict.fromkeys(layer_roles.values()))
    train_variants = set(train_variant_indices)
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
            direction = direction_for_pair(
                torch=torch,
                records=records,
                activations_by_record=activations_by_record,
                left=left,
                right=right,
                train_variant_indices=train_variants,
            ).to(device)
            direction_norm = float(torch.linalg.vector_norm(direction).item())
            source_text = heldout_source_text(
                records,
                concept_id=left,
                holdout_variant_index=holdout_variant_index,
            )
            prompt = steering_prompt(
                source_text=source_text,
                source_label=str(concept_lookup[left]["label"]),
                target_label=str(concept_lookup[right]["label"]),
                distractor_label=str(concept_lookup[distractor]["label"]),
            )
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
            for scale in scales:
                delta = direction * scale
                forward_scores = run_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    prompt=prompt,
                    layer=layer,
                    delta=delta,
                    max_length=max_length,
                    token_ids=token_ids,
                )
                reverse_scores = run_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    prompt=prompt,
                    layer=layer,
                    delta=-delta,
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
                        "scale": scale,
                        "direction_norm": direction_norm,
                        "prompt": prompt,
                        "scores": {
                            "baseline": baseline_scores,
                            "forward": forward_scores,
                            "reverse": reverse_scores,
                        },
                        "summary": summarize_scale(
                            baseline_scores=baseline_scores,
                            forward_scores=forward_scores,
                            reverse_scores=reverse_scores,
                        ),
                    }
                )
    return {
        "rows": rows,
        "gate_summaries": [
            gate_summary(rows, scale=scale)
            for scale in scales
        ],
        "option_token_ids": token_ids,
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
    train_variants: str = "0,1",
    holdout_variant: int = 2,
    scales: str = DEFAULT_SCALES,
    out: str = "artifacts/activation_geometry/modal_final_token_steering.json",
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
    from experiments.activation_geometry.final_token_steering_pilot import (
        default_pair_specs,
        parse_scales,
        public_summary,
        serializable_pair_specs,
        write_payload,
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
    parsed_scales = parse_scales(scales)
    train_variant_indices = parse_layers(train_variants)
    pair_specs = default_pair_specs(concept_rows)
    remote_payload = run_final_token_steering_remote.remote(
        [concept.__dict__ for concept in concept_rows],
        serializable_records,
        serializable_pair_specs(pair_specs),
        model_id,
        layer_roles,
        parsed_scales,
        train_variant_indices,
        holdout_variant,
        batch_size,
        max_length,
    )
    payload = {
        "manifest": {
            "model_id": model_id,
            "concept_source": concepts,
            "paraphrase_source": paraphrases,
            "pooling": "final-token",
            "layer_roles": layer_roles,
            "train_variant_indices": train_variant_indices,
            "holdout_variant_index": holdout_variant,
            "scales": parsed_scales,
            "batch_size": batch_size,
            "max_length": max_length,
            "pairs": serializable_pair_specs(pair_specs),
            "option_token_ids": remote_payload["option_token_ids"],
        },
        "rows": remote_payload["rows"],
        "gate_summaries": remote_payload["gate_summaries"],
    }
    if out and out.lower() != "none":
        write_payload(Path(out), payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    print(
        "Run with: modal run experiments/activation_geometry/modal_final_token_steering.py",
        file=sys.stderr,
    )
