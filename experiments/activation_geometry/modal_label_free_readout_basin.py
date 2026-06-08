#!/usr/bin/env python3
"""Modal entrypoint for label-free readout basin diagnostics."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


DEFAULT_MODEL_ID = "EleutherAI/pythia-70m-deduped"
DEFAULT_INJECTION_LAYER = 5
DEFAULT_READOUT_LAYER = 6
DEFAULT_PATCH_MODES = "target,distractor,random,source_noop"
DEFAULT_PATCH_TEXT_REGIMES = "definition,neutral"
DEFAULT_PATCH_VECTOR_SURFACE = "hook_output"
DEFAULT_READOUT_MODES = "centroid"
PATCH_MODES = ("target", "distractor", "random", "source_noop")
PATCH_TEXT_REGIMES = ("definition", "neutral")
PATCH_VECTOR_SURFACES = ("hidden_state", "hook_output")
READOUT_MODES = ("centroid", "ridge")
IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-label-free-readout-basin")


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


def vector_mean(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        raise ValueError("Cannot compute a mean over no vectors")
    dimensions = len(vectors[0])
    return [
        sum(vector[index] for vector in vectors) / len(vectors)
        for index in range(dimensions)
    ]


def subtract(left: list[float], right: list[float]) -> list[float]:
    return [left_value - right_value for left_value, right_value in zip(left, right)]


def normalize(vector: list[float]) -> list[float]:
    torch = importlib.import_module("torch")
    tensor = torch.tensor(vector, dtype=torch.float32)
    norm = torch.linalg.vector_norm(tensor)
    if float(norm.item()) == 0.0:
        return [0.0 for _ in vector]
    return (tensor / norm).tolist()


def cosine(left: list[float], right: list[float]) -> float:
    return sum(left_value * right_value for left_value, right_value in zip(left, right))


def centroid(vectors: list[list[float]]) -> list[float]:
    return normalize(vector_mean(vectors))


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_readout_delta(
    *,
    baseline_scores: dict[str, float],
    patched_scores: dict[str, float],
    patched_target_rank: int,
) -> dict[str, Any]:
    baseline_margin = target_margin(baseline_scores)
    patched_margin = target_margin(patched_scores)
    return {
        "baseline_target_margin": baseline_margin,
        "patched_target_margin": patched_margin,
        "target_margin_delta": patched_margin - baseline_margin,
        "target_score_delta": patched_scores["target"] - baseline_scores["target"],
        "source_score_delta": patched_scores["source"] - baseline_scores["source"],
        "distractor_score_delta": (
            patched_scores["distractor"] - baseline_scores["distractor"]
        ),
        "patched_target_rank": patched_target_rank,
        "patched_target_top3": patched_target_rank <= 3,
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


def final_token_vectors(
    *,
    torch: Any,
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
        torch=torch,
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


def patched_prompt_readout_vectors(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    source_prompt: str,
    injection_layer: int,
    patch_vector: list[float],
    readout_layers: list[int],
    patch_alpha: float,
    max_length: int,
) -> dict[int, list[float]]:
    encoded = tokenizer(
        source_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )
    device = next(model.parameters()).device
    encoded = {name: value.to(device) for name, value in encoded.items()}
    block = block_for_hidden_state_layer(model, injection_layer)
    final_indices = encoded["attention_mask"].to(device).sum(dim=1).long() - 1
    patch_tensor = torch.tensor(
        patch_vector,
        dtype=next(model.parameters()).dtype,
        device=device,
    )

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        adjusted = hidden_states.clone()
        batch_indices = torch.arange(adjusted.shape[0], device=adjusted.device)
        current = adjusted[batch_indices, final_indices]
        adjusted[batch_indices, final_indices] = (
            (1.0 - patch_alpha) * current + patch_alpha * patch_tensor
        )
        if isinstance(output, tuple):
            return (adjusted, *output[1:])
        return adjusted

    handle = block.register_forward_hook(hook)
    try:
        with torch.inference_mode():
            outputs = model(**encoded, output_hidden_states=True, use_cache=False)
    finally:
        handle.remove()
    return final_token_vectors(
        torch=torch,
        hidden_states=outputs.hidden_states,
        attention_mask=encoded["attention_mask"],
        layers=readout_layers,
    )


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
            f"Expected one text for {concept_id} variant {variant_index}; found {len(matches)}"
        )
    return matches[0]


def centered_normalized(
    vector: list[float],
    train_mean: list[float],
) -> list[float]:
    return normalize(subtract(vector, train_mean))


def readout_scores(
    vector: list[float],
    *,
    centroids_by_concept: dict[str, list[float]],
    left: str,
    right: str,
    distractor: str,
) -> dict[str, float]:
    return {
        "source": cosine(vector, centroids_by_concept[left]),
        "target": cosine(vector, centroids_by_concept[right]),
        "distractor": cosine(vector, centroids_by_concept[distractor]),
    }


def all_centroid_scores(
    vector: list[float],
    *,
    centroids_by_concept: dict[str, list[float]],
) -> dict[str, float]:
    return {
        concept_id: cosine(vector, centroid_vector)
        for concept_id, centroid_vector in centroids_by_concept.items()
    }


def target_rank(
    vector: list[float],
    *,
    centroids_by_concept: dict[str, list[float]],
    target: str,
) -> int:
    scored = sorted(
        all_centroid_scores(
            vector,
            centroids_by_concept=centroids_by_concept,
        ).items(),
        key=lambda row: row[1],
        reverse=True,
    )
    return [concept_id for concept_id, _score in scored].index(target) + 1


def build_centroid_readout(
    *,
    concept_ids: list[str],
    train_records: list[dict[str, Any]],
    train_vectors: dict[str, list[float]],
) -> tuple[list[float], dict[str, list[float]]]:
    train_mean = vector_mean(list(train_vectors.values()))
    by_concept: dict[str, list[list[float]]] = {concept_id: [] for concept_id in concept_ids}
    for record in train_records:
        concept_id = str(record["concept_id"])
        by_concept[concept_id].append(
            centered_normalized(train_vectors[str(record["id"])], train_mean)
        )
    return train_mean, {
        concept_id: centroid(vectors)
        for concept_id, vectors in by_concept.items()
        if vectors
    }


def build_ridge_readout(
    *,
    torch: Any,
    concept_ids: list[str],
    train_records: list[dict[str, Any]],
    train_vectors: dict[str, list[float]],
    ridge_lambda: float,
) -> dict[str, Any]:
    train_mean = vector_mean(list(train_vectors.values()))
    concept_index = {concept_id: index for index, concept_id in enumerate(concept_ids)}
    features = []
    labels = []
    for record in train_records:
        features.append(
            centered_normalized(
                train_vectors[str(record["id"])],
                train_mean,
            )
        )
        labels.append(concept_index[str(record["concept_id"])])
    x = torch.tensor(features, dtype=torch.float32)
    y = torch.zeros((len(labels), len(concept_ids)), dtype=torch.float32)
    y[torch.arange(len(labels)), torch.tensor(labels)] = 1.0
    kernel = x @ x.T
    regularized = kernel + ridge_lambda * torch.eye(kernel.shape[0])
    coefficients = torch.linalg.solve(regularized, y)
    weights = x.T @ coefficients
    return {
        "concept_ids": concept_ids,
        "train_mean": train_mean,
        "weights": weights.cpu().tolist(),
    }


def ridge_scores_all(
    vector: list[float],
    *,
    ridge_readout: dict[str, Any],
) -> dict[str, float]:
    torch = importlib.import_module("torch")
    centered = centered_normalized(
        vector,
        ridge_readout["train_mean"],
    )
    feature = torch.tensor(centered, dtype=torch.float32)
    weights = torch.tensor(ridge_readout["weights"], dtype=torch.float32)
    scores = feature @ weights
    return {
        concept_id: float(scores[index].item())
        for index, concept_id in enumerate(ridge_readout["concept_ids"])
    }


def scores_for_pair(
    scores_by_concept: dict[str, float],
    *,
    left: str,
    right: str,
    distractor: str,
) -> dict[str, float]:
    return {
        "source": scores_by_concept[left],
        "target": scores_by_concept[right],
        "distractor": scores_by_concept[distractor],
    }


def rank_from_scores(
    scores_by_concept: dict[str, float],
    *,
    target: str,
) -> int:
    scored = sorted(scores_by_concept.items(), key=lambda row: row[1], reverse=True)
    return [concept_id for concept_id, _score in scored].index(target) + 1


@app.function(image=IMAGE, timeout=2400)
def run_label_free_readout_remote(
    concepts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    injection_layers: list[int],
    readout_layers: list[int],
    patch_modes: list[str],
    patch_text_regimes: list[str],
    train_variant_indices: list[int],
    eval_variant_index: int,
    patch_alphas: list[float],
    patch_vector_surface: str,
    readout_modes: list[str],
    ridge_lambda: float,
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
    concept_ids = sorted(concept_lookup)
    readout_layers = sorted(set(readout_layers))
    injection_layers = sorted(set(injection_layers))

    train_records = [
        record
        for record in records
        if int(record["variant_index"]) in set(train_variant_indices)
    ]
    train_vectors_by_layer: dict[int, dict[str, list[float]]] = {
        layer: {} for layer in readout_layers
    }
    for record in train_records:
        vectors = prompt_layer_vectors(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=str(record["text"]),
            layers=readout_layers,
            max_length=max_length,
        )
        for layer, vector in vectors.items():
            train_vectors_by_layer[layer][str(record["id"])] = vector

    centroid_readouts: dict[int, tuple[list[float], dict[str, list[float]]]] = {}
    if "centroid" in readout_modes:
        centroid_readouts = {
            layer: build_centroid_readout(
                concept_ids=concept_ids,
                train_records=train_records,
                train_vectors=train_vectors_by_layer[layer],
            )
            for layer in readout_layers
        }
    ridge_readouts: dict[int, dict[str, Any]] = {}
    if "ridge" in readout_modes:
        ridge_readouts = {
            layer: build_ridge_readout(
                torch=torch,
                concept_ids=concept_ids,
                train_records=train_records,
                train_vectors=train_vectors_by_layer[layer],
                ridge_lambda=ridge_lambda,
            )
            for layer in readout_layers
        }

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
        definition_text_by_concept = {
            concept_id: heldout_text(
                records,
                concept_id=concept_id,
                variant_index=eval_variant_index,
            )
            for concept_id in sorted({left, right, distractor, random_patch})
        }
        labels_by_concept = {
            concept_id: str(concept_lookup[concept_id]["label"])
            for concept_id in definition_text_by_concept
        }
        baseline_vectors = prompt_layer_vectors(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=source_prompt,
            layers=readout_layers,
            max_length=max_length,
        )
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
                        patched_vectors = patched_prompt_readout_vectors(
                            torch=torch,
                            tokenizer=tokenizer,
                            model=model,
                            source_prompt=source_prompt,
                            injection_layer=injection_layer,
                            patch_vector=patch_vectors_by_concept[patch_concept],
                            readout_layers=readout_layers,
                            patch_alpha=patch_alpha,
                            max_length=max_length,
                        )
                        for readout_layer in readout_layers:
                            for readout_mode in readout_modes:
                                if readout_mode == "centroid":
                                    train_mean, centroids_by_concept = (
                                        centroid_readouts[readout_layer]
                                    )
                                    baseline_vector = centered_normalized(
                                        baseline_vectors[readout_layer],
                                        train_mean,
                                    )
                                    patched_vector = centered_normalized(
                                        patched_vectors[readout_layer],
                                        train_mean,
                                    )
                                    baseline_scores_by_concept = all_centroid_scores(
                                        baseline_vector,
                                        centroids_by_concept=centroids_by_concept,
                                    )
                                    patched_scores_by_concept = all_centroid_scores(
                                        patched_vector,
                                        centroids_by_concept=centroids_by_concept,
                                    )
                                elif readout_mode == "ridge":
                                    baseline_scores_by_concept = ridge_scores_all(
                                        baseline_vectors[readout_layer],
                                        ridge_readout=ridge_readouts[readout_layer],
                                    )
                                    patched_scores_by_concept = ridge_scores_all(
                                        patched_vectors[readout_layer],
                                        ridge_readout=ridge_readouts[readout_layer],
                                    )
                                else:
                                    raise ValueError(
                                        f"Unknown readout mode: {readout_mode}"
                                    )
                                baseline_scores = scores_for_pair(
                                    baseline_scores_by_concept,
                                    left=left,
                                    right=right,
                                    distractor=distractor,
                                )
                                patched_scores = scores_for_pair(
                                    patched_scores_by_concept,
                                    left=left,
                                    right=right,
                                    distractor=distractor,
                                )
                                rank = rank_from_scores(
                                    patched_scores_by_concept,
                                    target=right,
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
                                            pair["random_patch_scope"],
                                        ),
                                        "injection_layer": injection_layer,
                                        "readout_layer": readout_layer,
                                        "readout_mode": readout_mode,
                                        "patch_text_regime": patch_text_regime,
                                        "patch_mode": mode,
                                        "patch_concept": patch_concept,
                                        "patch_concept_label": labels_by_concept[
                                            patch_concept
                                        ],
                                        "patch_context": (
                                            "label_free_definition_readout"
                                        ),
                                        "train_variant_indices": train_variant_indices,
                                        "eval_variant_index": eval_variant_index,
                                        "patch_alpha": patch_alpha,
                                        "patch_vector_surface": patch_vector_surface,
                                        "source_prompt": source_prompt,
                                        "scores": {
                                            "baseline": baseline_scores,
                                            "patched": patched_scores,
                                        },
                                        "summary": summarize_readout_delta(
                                            baseline_scores=baseline_scores,
                                            patched_scores=patched_scores,
                                            patched_target_rank=rank,
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
    readout_layers: str = str(DEFAULT_READOUT_LAYER),
    max_length: int = 128,
    train_variants: str = "0,1",
    eval_variant: int = 2,
    patch_alpha: float = 1.0,
    patch_alphas: str = "",
    patch_vector_surface: str = DEFAULT_PATCH_VECTOR_SURFACE,
    readout_modes: str = DEFAULT_READOUT_MODES,
    ridge_lambda: float = 1.0,
    patch_modes: str = DEFAULT_PATCH_MODES,
    patch_text_regimes: str = DEFAULT_PATCH_TEXT_REGIMES,
    pair_set: str = "focus",
    baseline_sample_count: int = 56,
    seed: int = 20260608,
    out: str = "artifacts/activation_geometry/modal_label_free_readout_basin.json",
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
    from experiments.activation_geometry.label_free_readout_basin import (
        PATCH_TEXT_REGIMES,
        PATCH_VECTOR_SURFACES,
        READOUT_MODES,
        aggregate_rows,
        dose_response_summaries,
        gate_summaries,
        pair_specs_for_set,
        public_summary,
        serializable_pair_specs,
        specificity_rows,
        transfer_baseline_summaries,
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
    parsed_readout_layers = parse_ints(readout_layers, name="readout layer")
    parsed_train_variants = parse_ints(train_variants, name="train variant")
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
    parsed_readout_modes = parse_values(
        readout_modes,
        allowed=READOUT_MODES,
        name="Readout modes",
    )
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
    remote_payload = run_label_free_readout_remote.remote(
        serializable_concepts,
        serializable_records,
        pair_specs,
        model_id,
        parsed_injection_layers,
        parsed_readout_layers,
        parsed_patch_modes,
        parsed_patch_text_regimes,
        parsed_train_variants,
        eval_variant,
        parsed_patch_alphas,
        parsed_patch_vector_surface,
        parsed_readout_modes,
        ridge_lambda,
        max_length,
    )
    aggregates = aggregate_rows(remote_payload["rows"])
    specificity = specificity_rows(aggregates)
    payload = {
        "manifest": {
            "model_id": model_id,
            "concept_source": concepts,
            "paraphrase_source": paraphrases,
            "patch_context": "label_free_definition_readout",
            "injection_layers": parsed_injection_layers,
            "readout_layers": parsed_readout_layers,
            "train_variant_indices": parsed_train_variants,
            "eval_variant_index": eval_variant,
            "patch_alpha": parsed_patch_alphas[0] if len(parsed_patch_alphas) == 1 else None,
            "patch_alphas": parsed_patch_alphas,
            "patch_vector_surface": parsed_patch_vector_surface,
            "readout_modes": parsed_readout_modes,
            "ridge_lambda": ridge_lambda,
            "patch_modes": parsed_patch_modes,
            "patch_text_regimes": parsed_patch_text_regimes,
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
        "transfer_baseline_summaries": transfer_baseline_summaries(specificity),
        "dose_response_summaries": dose_response_summaries(specificity),
    }
    if out and out.lower() != "none":
        write_payload(Path(out), payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    print(
        "Run with: modal run experiments/activation_geometry/modal_label_free_readout_basin.py",
        file=sys.stderr,
    )
