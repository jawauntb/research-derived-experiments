#!/usr/bin/env python3
"""Modal direction-subspace diagnostic for behavior-aligned gradients."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-behavior-direction-subspace")


def pair_id(left: str, right: str) -> str:
    return f"{left}->{right}"


def tensor_mean(torch: Any, vectors: list[Any]) -> Any:
    if not vectors:
        raise ValueError("Cannot average an empty vector list")
    return torch.stack(vectors, dim=0).mean(dim=0)


def normalize_rows(torch: Any, matrix: Any) -> Any:
    norms = torch.linalg.vector_norm(matrix.float(), dim=1, keepdim=True).clamp(min=1e-12)
    return matrix.float() / norms


def singular_summary(torch: Any, matrix: Any) -> dict[str, Any]:
    normalized = normalize_rows(torch, matrix)
    singular_values = torch.linalg.svdvals(normalized).float()
    energy = singular_values.square()
    total = energy.sum().clamp(min=1e-12)
    ratios = energy / total
    entropy = -(ratios * torch.log(ratios.clamp(min=1e-12))).sum()
    return {
        "singular_values": [float(value.item()) for value in singular_values],
        "explained_variance_ratio": [float(value.item()) for value in ratios],
        "cumulative_explained_variance": [
            float(value.item()) for value in torch.cumsum(ratios, dim=0)
        ],
        "effective_rank": float(torch.exp(entropy).item()),
    }


def mean_or_nan(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


SINGLE_LABEL_SCORING_REGIMES = ("canonical", "alias", "alias_0", "alias_1", "alias_2")


def label_scoring_regime_parts(
    regime: str,
    *,
    allow_groups: bool,
) -> list[str]:
    parts = [part.strip() for part in regime.split("+") if part.strip()]
    if not parts:
        raise ValueError("Label scoring regime cannot be empty")
    if len(parts) > 1 and not allow_groups:
        raise ValueError(f"Grouped label scoring regime is not allowed here: {regime}")
    invalid = sorted(set(parts) - set(SINGLE_LABEL_SCORING_REGIMES))
    if invalid:
        options = ", ".join(SINGLE_LABEL_SCORING_REGIMES)
        raise ValueError(f"Label scoring regime parts must be chosen from: {options}")
    return parts


def labels_by_role_for_regime(
    *,
    concept_lookup: dict[str, dict[str, Any]],
    aliases_by_concept: dict[str, list[str]],
    left: str,
    right: str,
    distractor: str,
    label_scoring_regime: str,
) -> dict[str, str]:
    concept_by_role = {
        "source": left,
        "target": right,
        "distractor": distractor,
    }
    if label_scoring_regime == "canonical":
        return {
            role: str(concept_lookup[concept_id]["label"])
            for role, concept_id in concept_by_role.items()
        }
    if label_scoring_regime == "alias" or label_scoring_regime.startswith("alias_"):
        alias_index = 0
        if label_scoring_regime.startswith("alias_"):
            alias_index = int(label_scoring_regime.rsplit("_", maxsplit=1)[1])
        missing = sorted(
            concept_id
            for concept_id in concept_by_role.values()
            if len(aliases_by_concept.get(concept_id, [])) <= alias_index
        )
        if missing:
            raise ValueError(
                f"Missing alias index {alias_index} for concepts: {missing}"
            )
        return {
            role: aliases_by_concept[concept_id][alias_index]
            for role, concept_id in concept_by_role.items()
        }
    raise ValueError(f"Unknown label scoring regime: {label_scoring_regime}")


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


def full_label_prompt(*, source_text: str, prompt_frame: str) -> str:
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


def objective_margin(logprobs: Any, token_ids: dict[str, int], role: str) -> Any:
    roles = ("source", "target", "distractor")
    if role not in roles:
        raise ValueError(f"Unknown objective role: {role}")
    others = [name for name in roles if name != role]
    return logprobs[token_ids[role]] - 0.5 * sum(
        logprobs[token_ids[name]] for name in others
    )


def label_token_ids(tokenizer: Any, labels_by_role: dict[str, str]) -> dict[str, list[int]]:
    token_ids = {}
    for role, label in labels_by_role.items():
        ids = tokenizer.encode(f" {label}", add_special_tokens=False)
        if not ids:
            raise ValueError(f"Could not encode label for {role!r}: {label!r}")
        token_ids[role] = [int(token_id) for token_id in ids]
    return token_ids


def continuation_score(
    *,
    torch: Any,
    logits: Any,
    prompt_length: int,
    continuation_ids: list[int],
    label_score_normalization: str,
) -> Any:
    token_logprobs = []
    for offset, token_id in enumerate(continuation_ids):
        prediction_index = prompt_length - 1 + offset
        logprobs = torch.nn.functional.log_softmax(
            logits[0, prediction_index].float(),
            dim=-1,
        )
        token_logprobs.append(logprobs[token_id])
    if label_score_normalization == "sum":
        return sum(token_logprobs)
    if label_score_normalization == "mean":
        return sum(token_logprobs) / len(token_logprobs)
    raise ValueError(f"Unknown label score normalization: {label_score_normalization}")


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


def full_label_score_gradient_for_role(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    max_length: int,
    continuation_ids: list[int],
    label_score_normalization: str,
) -> Any:
    prompt_max_length = max(1, max_length - len(continuation_ids))
    prompt_ids = tokenizer.encode(
        prompt,
        add_special_tokens=False,
        truncation=True,
        max_length=prompt_max_length,
    )
    if not prompt_ids:
        raise ValueError("Prompt encoded to zero tokens")

    device = next(model.parameters()).device
    input_ids = torch.tensor(
        [prompt_ids + continuation_ids],
        dtype=torch.long,
        device=device,
    )
    attention_mask = torch.ones_like(input_ids)
    block = block_for_hidden_state_layer(model, layer)
    token_indices = torch.tensor([len(prompt_ids) - 1], device=device)
    captured: dict[str, Any] = {}

    def capture_hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        batch_indices = torch.arange(hidden_states.shape[0], device=hidden_states.device)
        selected = hidden_states[batch_indices, token_indices].detach().clone()
        selected.requires_grad_(True)
        adjusted = hidden_states.clone()
        adjusted[batch_indices, token_indices] = selected
        captured["selected"] = selected
        if isinstance(output, tuple):
            return (adjusted, *output[1:])
        return adjusted

    model.zero_grad(set_to_none=True)
    handle = block.register_forward_hook(capture_hook)
    try:
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            use_cache=False,
        )
        score = continuation_score(
            torch=torch,
            logits=outputs.logits,
            prompt_length=len(prompt_ids),
            continuation_ids=continuation_ids,
            label_score_normalization=label_score_normalization,
        )
        score.backward()
        selected = captured.get("selected")
        if selected is None or selected.grad is None:
            raise RuntimeError("Could not capture full-label activation gradient")
        return selected.grad[0].detach().float().cpu()
    finally:
        handle.remove()
        model.zero_grad(set_to_none=True)


def full_label_gradient_direction_for_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    max_length: int,
    labels_by_role: dict[str, str],
    objective_role: str,
    label_score_normalization: str,
) -> Any:
    continuation_ids_by_role = label_token_ids(tokenizer, labels_by_role)
    gradients_by_role = {
        role: full_label_score_gradient_for_role(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            layer=layer,
            max_length=max_length,
            continuation_ids=continuation_ids,
            label_score_normalization=label_score_normalization,
        )
        for role, continuation_ids in continuation_ids_by_role.items()
    }
    others = [role for role in ("source", "target", "distractor") if role != objective_role]
    return gradients_by_role[objective_role] - 0.5 * sum(
        gradients_by_role[role] for role in others
    )


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
    scoring_surface: str,
    prompt_frame: str,
    label_score_normalization: str,
) -> Any:
    gradients = []
    for _variant_index, source_text in source_texts:
        if scoring_surface == "option_token":
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
            continue
        if scoring_surface == "full_label":
            prompt = full_label_prompt(
                source_text=source_text,
                prompt_frame=prompt_frame,
            )
            gradients.append(
                full_label_gradient_direction_for_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    prompt=prompt,
                    layer=layer,
                    max_length=max_length,
                    labels_by_role=labels_by_role,
                    objective_role=objective_role,
                    label_score_normalization=label_score_normalization,
                )
            )
            continue
        raise ValueError(f"Unknown scoring surface: {scoring_surface}")
    return tensor_mean(torch, gradients)


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


def cosine_rows(torch: Any, records: list[dict[str, Any]], matrix: Any) -> list[dict[str, Any]]:
    normalized = normalize_rows(torch, matrix)
    gram = normalized @ normalized.T
    rows = []
    for left_index, left in enumerate(records):
        for right_index, right in enumerate(records):
            if left_index >= right_index:
                continue
            if left["kind"] == right["kind"]:
                group = f"within_{left['kind']}"
            else:
                group = "positive_control_cross"
            rows.append(
                {
                    "left_pair": left["pair"],
                    "left_kind": left["kind"],
                    "right_pair": right["pair"],
                    "right_kind": right["kind"],
                    "group": group,
                    "cosine": float(gram[left_index, right_index].item()),
                    "abs_cosine": abs(float(gram[left_index, right_index].item())),
                }
            )
    return rows


def cosine_group_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = sorted({str(row["group"]) for row in rows})
    summaries = []
    for group in groups:
        selected = [row for row in rows if row["group"] == group]
        summaries.append(
            {
                "group": group,
                "count": len(selected),
                "mean_cosine": mean_or_nan([float(row["cosine"]) for row in selected]),
                "mean_abs_cosine": mean_or_nan(
                    [float(row["abs_cosine"]) for row in selected]
                ),
                "max_abs_cosine": max(float(row["abs_cosine"]) for row in selected),
            }
        )
    return summaries


def control_subspace_capture(
    torch: Any,
    records: list[dict[str, Any]],
    matrix: Any,
) -> list[dict[str, Any]]:
    normalized = normalize_rows(torch, matrix)
    control_indices = [
        index for index, record in enumerate(records) if str(record["kind"]) == "control"
    ]
    if not control_indices:
        return []
    control_matrix = normalized[control_indices]
    _u, _s, vh = torch.linalg.svd(control_matrix, full_matrices=False)
    rows = []
    max_rank = min(len(control_indices), vh.shape[0])
    for rank in range(1, max_rank + 1):
        basis = vh[:rank].T
        captures = (normalized @ basis).square().sum(dim=1)
        positive_values = [
            float(captures[index].item())
            for index, record in enumerate(records)
            if str(record["kind"]) == "positive"
        ]
        control_values = [
            float(captures[index].item())
            for index, record in enumerate(records)
            if str(record["kind"]) == "control"
        ]
        rows.append(
            {
                "rank": rank,
                "positive_mean_capture": mean_or_nan(positive_values),
                "positive_min_capture": min(positive_values),
                "positive_max_capture": max(positive_values),
                "control_mean_capture": mean_or_nan(control_values),
                "control_min_capture": min(control_values),
                "control_max_capture": max(control_values),
            }
        )
    return rows


@app.function(image=IMAGE, timeout=1800)
def run_direction_subspace_remote(
    concepts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    aliases_by_concept: dict[str, list[str]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    layer: int,
    train_variant_indices: list[int],
    max_length: int,
    scoring_surface: str,
    prompt_frame: str,
    objective_label_scoring_regime: str,
    label_score_normalization: str,
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
    train_variants = set(train_variant_indices)
    token_ids_by_slot = slot_token_ids(tokenizer)
    option_orders = [
        ("source", "target", "distractor"),
        ("target", "distractor", "source"),
        ("distractor", "source", "target"),
    ]
    objective_regime_parts = label_scoring_regime_parts(
        objective_label_scoring_regime,
        allow_groups=True,
    )

    direction_records = []
    direction_vectors = []
    for pair in pair_specs:
        left = str(pair["left"])
        right = str(pair["right"])
        distractor = str(pair["distractor"])
        source_texts = train_source_texts(
            records,
            concept_id=left,
            train_variant_indices=train_variants,
        )
        regime_directions = []
        labels_by_regime = {}
        for regime_part in objective_regime_parts:
            labels_by_role = labels_by_role_for_regime(
                concept_lookup=concept_lookup,
                aliases_by_concept=aliases_by_concept,
                left=left,
                right=right,
                distractor=distractor,
                label_scoring_regime=regime_part,
            )
            labels_by_regime[regime_part] = labels_by_role
            regime_directions.append(
                learned_gradient_direction(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    source_texts=source_texts,
                    labels_by_role=labels_by_role,
                    option_orders=option_orders,
                    token_ids_by_slot=token_ids_by_slot,
                    layer=layer,
                    max_length=max_length,
                    objective_role="target",
                    scoring_surface=scoring_surface,
                    prompt_frame=prompt_frame,
                    label_score_normalization=label_score_normalization,
                ).to(device)
            )
        direction = tensor_mean(torch, regime_directions).float()
        direction_vectors.append(direction.detach().cpu())
        direction_records.append(
            {
                "pair": pair_id(left, right),
                "left": left,
                "right": right,
                "kind": str(pair["kind"]),
                "distractor": distractor,
                "direction_norm": float(torch.linalg.vector_norm(direction).item()),
                "objective_labels_by_regime": labels_by_regime,
            }
        )

    matrix = torch.stack(direction_vectors, dim=0)
    pairwise_rows = cosine_rows(torch, direction_records, matrix)
    positive_matrix = matrix[
        [index for index, row in enumerate(direction_records) if row["kind"] == "positive"]
    ]
    control_matrix = matrix[
        [index for index, row in enumerate(direction_records) if row["kind"] == "control"]
    ]
    return {
        "direction_records": direction_records,
        "singular_summary": {
            "all": singular_summary(torch, matrix),
            "positive": singular_summary(torch, positive_matrix),
            "control": singular_summary(torch, control_matrix),
        },
        "cosine_rows": pairwise_rows,
        "cosine_group_summary": cosine_group_summary(pairwise_rows),
        "control_subspace_capture": control_subspace_capture(
            torch,
            direction_records,
            matrix,
        ),
    }


@app.local_entrypoint()
def main(
    concepts: str = "experiments/concept_geometry/concept_set.json",
    paraphrases: str = "experiments/concept_geometry/concept_paraphrases.json",
    aliases: str = "experiments/concept_geometry/concept_aliases.json",
    model_id: str = "EleutherAI/pythia-70m-deduped",
    layer: int = 5,
    train_variants: str = "0,1",
    max_length: int = 180,
    scoring_surface: str = "full_label",
    prompt_frame: str = "source_passage",
    objective_label_scoring_regime: str = "alias_0+alias_1",
    label_score_normalization: str = "mean",
    pair_set: str = "expanded",
    out: str = "artifacts/activation_geometry/modal_behavior_direction_subspace.json",
) -> None:
    resolved_path = Path(__file__).resolve()
    repo_root = resolved_path.parents[2] if len(resolved_path.parents) > 2 else Path.cwd()
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    from experiments.activation_geometry.activation_geometry_probe import (
        activation_records,
        load_concepts,
        parse_layers,
        write_payload,
    )
    from experiments.activation_geometry.final_token_steering_pilot import (
        pair_specs_for_set,
        serializable_pair_specs,
    )
    from experiments.activation_geometry.modal_behavior_aligned_direction import (
        load_aliases,
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
    aliases_by_concept = load_aliases(Path(aliases))
    pair_specs = pair_specs_for_set(concept_rows, pair_set=pair_set)
    parsed_train_variants = parse_layers(train_variants)

    remote_payload = run_direction_subspace_remote.remote(
        [concept.__dict__ for concept in concept_rows],
        serializable_records,
        aliases_by_concept,
        serializable_pair_specs(pair_specs),
        model_id,
        layer,
        parsed_train_variants,
        max_length,
        scoring_surface,
        prompt_frame,
        objective_label_scoring_regime,
        label_score_normalization,
    )
    payload = {
        "manifest": {
            "model_id": model_id,
            "concept_source": concepts,
            "paraphrase_source": paraphrases,
            "alias_source": aliases,
            "pair_set": pair_set,
            "layer": layer,
            "train_variant_indices": parsed_train_variants,
            "max_length": max_length,
            "scoring_surface": scoring_surface,
            "prompt_frame": prompt_frame,
            "objective_label_scoring_regime": objective_label_scoring_regime,
            "label_score_normalization": label_score_normalization,
            "pairs": serializable_pair_specs(pair_specs),
        },
        **remote_payload,
    }
    if out and out.lower() != "none":
        write_payload(Path(out), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    print(
        "Run with: modal run experiments/activation_geometry/modal_behavior_direction_subspace.py",
        file=sys.stderr,
    )
