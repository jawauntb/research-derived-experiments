#!/usr/bin/env python3
"""Modal entrypoint for learned behavior-aligned direction pilots."""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


DEFAULT_MODEL_ID = "EleutherAI/pythia-70m-deduped"
DEFAULT_OPTION_ORDERS = "std,tds,dst"
DEFAULT_DIRECTION_MODES = "target_learned,source_learned,distractor_learned,random_same_norm"
DEFAULT_SCORING_SURFACE = "option_token"
DEFAULT_PROMPT_FRAME = "source_passage"
DEFAULT_OBJECTIVE_LABEL_SCORING_REGIMES = "canonical"
DEFAULT_EVAL_LABEL_SCORING_REGIMES = "canonical"
DEFAULT_LABEL_SCORE_NORMALIZATION = "mean"
GENERATION_MATCH_NEW_TOKENS = 8
RESULTS_VOLUME_NAME = "rde-activation-results"
RESULTS_VOLUME_MOUNT = Path("/results")
PENALTY_DIRECTION_MODES = {
    "target_penalty_hard_1_0": ("hard_control", 1.0),
    "target_penalty_hard_2_0": ("hard_control", 2.0),
    "target_penalty_control_mean_1_0": ("control_mean", 1.0),
    "target_penalty_controls_0_5": ("control_set", 0.5),
    "target_penalty_controls_1_0": ("control_set", 1.0),
    "target_penalty_controls_2_0": ("control_set", 2.0),
}
BINARY_CONTROL_DIRECTION_MODES = {
    "target_binary_controls_0_5": 0.5,
    "target_binary_controls_1_0": 1.0,
    "target_binary_controls_2_0": 2.0,
    "target_binary_controls_4_0": 4.0,
}
BINARY_PC_DIRECTION_MODES = {
    "target_binary_pc1_resid": ("residualize", 1),
    "target_binary_pc3_resid": ("residualize", 3),
    "target_binary_pc1_whiten": ("whiten", 1),
    "target_binary_pc3_whiten": ("whiten", 3),
}
BINARY_OPT_DIRECTION_MODES = {
    "target_binary_strict_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
    },
    "target_binary_strict_opt_16": {
        "steps": 16,
        "lr": 0.2,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
    },
    "target_binary_readout_span_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "basis": "readout_span",
    },
    "target_binary_feature_mask_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "parameterization": "feature_mask",
        "mask_fraction": 0.15,
        "mask_control_weight": 1.0,
    },
    "target_binary_state_gate_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "parameterization": "state_gate",
        "gate_temperature": 0.05,
    },
    "target_binary_relation_state_gate_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "parameterization": "state_gate",
        "gate_temperature": 0.05,
        "relation_control_prompts": True,
    },
    "target_binary_multiclass_state_gate_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "parameterization": "multiclass_state_gate",
        "gate_temperature": 0.05,
    },
    "target_binary_relation_multiclass_state_gate_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "parameterization": "multiclass_state_gate",
        "gate_temperature": 0.05,
        "relation_control_prompts": True,
    },
    "target_binary_relation_multiclass_holdout_source_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "parameterization": "multiclass_state_gate",
        "gate_temperature": 0.05,
        "relation_control_prompts": True,
        "exclude_relation_control_classes": ("source_sharing",),
    },
    "target_binary_relation_multiclass_holdout_target_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "parameterization": "multiclass_state_gate",
        "gate_temperature": 0.05,
        "relation_control_prompts": True,
        "exclude_relation_control_classes": ("target_sharing",),
    },
    "target_binary_relation_multiclass_holdout_overlap_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "pair",
        "parameterization": "multiclass_state_gate",
        "gate_temperature": 0.05,
        "relation_control_prompts": True,
        "exclude_relation_control_classes": ("source_sharing", "target_sharing"),
    },
    "target_binary_positive_family_opt_8": {
        "steps": 8,
        "lr": 0.25,
        "control_weight": 2.0,
        "temperature": 0.25,
        "scope": "positive_family",
    },
}
IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-behavior-aligned-direction")
RESULTS_VOLUME = modal.Volume.from_name(RESULTS_VOLUME_NAME, create_if_missing=True)


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
    if prompt_frame == "source_short_answer":
        return "\n".join(
            [
                "Answer with one short related concept phrase only.",
                "",
                f"Passage: {source_text}",
                "",
                "Related concept:",
            ]
        )
    if prompt_frame == "latent_choice":
        return "The concept most likely indicated by the model's current internal state is"
    if prompt_frame == "latent_short_answer":
        return "Answer with one short concept phrase only. Related concept:"
    raise ValueError(f"Unknown prompt frame: {prompt_frame}")


def binary_relation_prompt(
    *,
    source_text: str,
    candidate_label: str,
) -> str:
    return "\n".join(
        [
            "Read the passage and candidate concept.",
            "Answer Yes only if the candidate names the closest related concept,",
            "not merely the concept described in the passage.",
            "",
            f"Passage: {source_text}",
            f"Candidate: {candidate_label}",
            "Answer Yes or No:",
        ]
    )


def binary_carrier_prompt(
    *,
    carrier: str,
    candidate_label: str,
) -> str:
    if carrier == "always_true":
        return "\n".join(
            [
                "Answer the factual identity check.",
                f"Candidate: {candidate_label}",
                "Question: Is the candidate exactly the same concept as itself?",
                "Answer Yes or No:",
            ]
        )
    if carrier == "always_false":
        return "\n".join(
            [
                "Answer the factual identity check.",
                f"Candidate: {candidate_label}",
                "Question: Is the candidate exactly the phrase 'not the candidate'?",
                "Answer Yes or No:",
            ]
        )
    raise ValueError(f"Unknown binary carrier: {carrier}")


def load_aliases(path: Path) -> dict[str, list[str]]:
    rows = json.loads(path.read_text())
    aliases_by_concept: dict[str, list[str]] = {}
    for row in rows:
        concept_id = str(row["id"])
        aliases = [
            str(alias).strip()
            for alias in row.get("aliases", [])
            if str(alias).strip()
        ]
        if not aliases:
            raise ValueError(f"Concept {concept_id!r} has no aliases")
        aliases_by_concept[concept_id] = aliases
    return aliases_by_concept


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
        missing = sorted(
            concept_id
            for concept_id in concept_by_role.values()
            if not aliases_by_concept.get(concept_id)
        )
        if missing:
            raise ValueError(f"Missing aliases for concepts: {missing}")
        alias_index = 0
        if label_scoring_regime.startswith("alias_"):
            alias_index = int(label_scoring_regime.rsplit("_", maxsplit=1)[1])
        too_short = sorted(
            concept_id
            for concept_id in concept_by_role.values()
            if len(aliases_by_concept[concept_id]) <= alias_index
        )
        if too_short:
            raise ValueError(
                f"Missing alias index {alias_index} for concepts: {too_short}"
            )
        return {
            role: aliases_by_concept[concept_id][alias_index]
            for role, concept_id in concept_by_role.items()
        }
    raise ValueError(f"Unknown label scoring regime: {label_scoring_regime}")


def generation_match_labels_by_role(
    *,
    concept_lookup: dict[str, dict[str, Any]],
    aliases_by_concept: dict[str, list[str]],
    left: str,
    right: str,
    distractor: str,
) -> dict[str, list[str]]:
    concept_by_role = {
        "source": left,
        "target": right,
        "distractor": distractor,
    }
    labels_by_role = {}
    for role, concept_id in concept_by_role.items():
        labels = [str(concept_lookup[concept_id]["label"])]
        labels.extend(str(alias) for alias in aliases_by_concept.get(concept_id, []))
        deduped = []
        seen = set()
        for label in labels:
            normalized = normalize_generated_text(label)
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(label)
        labels_by_role[role] = deduped
    return labels_by_role


def normalize_generated_text(text: str) -> str:
    normalized = text.lower().replace("_", " ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def generated_text_matches_label(*, generated_text: str, label: str) -> bool:
    text = normalize_generated_text(generated_text)
    normalized_label = normalize_generated_text(label)
    if not text or not normalized_label:
        return False
    return re.search(rf"(?<!\w){re.escape(normalized_label)}(?!\w)", text) is not None


def generation_match_scores(
    *,
    generated_text: str,
    labels_by_role: dict[str, list[str]],
) -> dict[str, Any]:
    scores: dict[str, Any] = {
        role: 1.0
        if any(
            generated_text_matches_label(generated_text=generated_text, label=label)
            for label in labels
        )
        else 0.0
        for role, labels in labels_by_role.items()
    }
    scores["generated_text"] = generated_text
    scores["matched_roles"] = [
        role for role in ("source", "target", "distractor") if scores[role] > 0
    ]
    return scores


def readout_text_prompt(text: str) -> str:
    cleaned = text.strip() or "[blank]"
    return "\n".join(
        [
            "Represent the semantic concept expressed by this text.",
            f"Text: {cleaned}",
            "Concept state:",
        ]
    )


def dedupe_texts(texts: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for text in texts:
        cleaned = text.strip()
        normalized = normalize_generated_text(cleaned)
        if cleaned and normalized not in seen:
            seen.add(normalized)
            deduped.append(cleaned)
    return deduped


def objective_role_for_mode(mode: str) -> str:
    if mode in {
        "target_learned",
        "target_resid_sd",
        "target_resid_control",
        "target_resid_all",
        "caa_target_contrast",
        "caa_target_minus_source",
        "caa_target_minus_distractor",
    } or (
        mode in PENALTY_DIRECTION_MODES
        or mode in BINARY_CONTROL_DIRECTION_MODES
        or mode in BINARY_PC_DIRECTION_MODES
        or mode in BINARY_OPT_DIRECTION_MODES
    ):
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


def normalize_vector(torch: Any, vector: Any) -> Any:
    norm = torch.linalg.vector_norm(vector.float()).clamp(min=1e-12)
    return vector.float() / norm


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


def target_margin(scores: dict[str, Any]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_behavior_delta(
    *,
    baseline_scores: dict[str, Any],
    steered_scores: dict[str, Any],
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


def intervention_anchor_tensor(delta: Any) -> Any:
    if isinstance(delta, dict):
        if delta.get("kind") in {"state_gate", "multiclass_state_gate"}:
            return delta["delta"]
        raise ValueError(f"Unknown intervention dictionary: {delta.get('kind')}")
    return delta


def intervention_addition(torch: Any, selected_hidden: Any, delta: Any) -> Any:
    if isinstance(delta, dict):
        kind = delta.get("kind")
        base_delta = delta["delta"].to(
            device=selected_hidden.device,
            dtype=selected_hidden.dtype,
        )
        if kind == "multiclass_state_gate":
            selected_float = selected_hidden.float()
            selected_norm = torch.linalg.vector_norm(
                selected_float,
                dim=-1,
                keepdim=True,
            ).clamp(min=1e-12)
            selected_unit = selected_float / selected_norm
            target_centroid = delta["target_centroid"].to(
                device=selected_hidden.device,
                dtype=torch.float32,
            )
            target_centroid = target_centroid / torch.linalg.vector_norm(
                target_centroid,
            ).clamp(min=1e-12)
            control_centroids = delta["control_centroids"].to(
                device=selected_hidden.device,
                dtype=torch.float32,
            )
            control_centroids = control_centroids / torch.linalg.vector_norm(
                control_centroids,
                dim=-1,
                keepdim=True,
            ).clamp(min=1e-12)
            target_scores = (selected_unit * target_centroid).sum(dim=-1)
            control_scores = selected_unit @ control_centroids.T
            gate_margins = target_scores - control_scores.max(dim=-1).values
            gate_values = torch.sigmoid(
                (gate_margins - float(delta["gate_threshold"]))
                / max(float(delta["gate_temperature"]), 1e-6)
            ).to(dtype=selected_hidden.dtype)
            return gate_values.unsqueeze(-1) * base_delta
        if kind != "state_gate":
            raise ValueError(f"Unknown intervention dictionary: {kind}")
        gate_direction = delta["gate_direction"].to(
            device=selected_hidden.device,
            dtype=torch.float32,
        )
        selected_float = selected_hidden.float()
        gate_direction_norm = torch.linalg.vector_norm(gate_direction).clamp(
            min=1e-12,
        )
        selected_norm = torch.linalg.vector_norm(
            selected_float,
            dim=-1,
        ).clamp(min=1e-12)
        gate_scores = (selected_float * gate_direction).sum(dim=-1) / (
            selected_norm * gate_direction_norm
        )
        gate_values = torch.sigmoid(
            (gate_scores - float(delta["gate_threshold"]))
            / max(float(delta["gate_temperature"]), 1e-6)
        ).to(dtype=selected_hidden.dtype)
        return gate_values.unsqueeze(-1) * base_delta
    return delta.to(device=selected_hidden.device, dtype=selected_hidden.dtype)


def direction_norm_value(torch: Any, direction: Any) -> float:
    return float(torch.linalg.vector_norm(intervention_anchor_tensor(direction)).item())


def scale_direction(direction: Any, scale: float) -> Any:
    if isinstance(direction, dict):
        if direction.get("kind") not in {"state_gate", "multiclass_state_gate"}:
            raise ValueError(
                f"Unknown intervention dictionary: {direction.get('kind')}"
            )
        scaled = dict(direction)
        scaled["delta"] = direction["delta"] * float(scale)
        return scaled
    return direction * float(scale)


def move_direction_to_device(direction: Any, device: Any) -> Any:
    if isinstance(direction, dict):
        kind = direction.get("kind")
        if kind not in {"state_gate", "multiclass_state_gate"}:
            raise ValueError(
                f"Unknown intervention dictionary: {kind}"
            )
        moved = dict(direction)
        moved["delta"] = direction["delta"].to(device)
        if kind == "state_gate":
            moved["gate_direction"] = direction["gate_direction"].to(device)
        if kind == "multiclass_state_gate":
            moved["target_centroid"] = direction["target_centroid"].to(device)
            moved["control_centroids"] = direction["control_centroids"].to(device)
        return moved
    return direction.to(device)


def add_final_token_hook(
    *,
    torch: Any,
    model: Any,
    layer: int,
    attention_mask: Any,
    delta: Any,
) -> Any:
    block = block_for_hidden_state_layer(model, layer)
    anchor = intervention_anchor_tensor(delta)
    final_indices = attention_mask.to(anchor.device).sum(dim=1).long() - 1

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        adjusted = hidden_states.clone()
        batch_indices = torch.arange(adjusted.shape[0], device=adjusted.device)
        adjusted[batch_indices, final_indices] = (
            adjusted[batch_indices, final_indices]
            + intervention_addition(
                torch,
                adjusted[batch_indices, final_indices],
                delta,
            )
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


def run_full_label_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    delta: Any | None,
    max_length: int,
    labels_by_role: dict[str, str],
    label_score_normalization: str,
) -> dict[str, float]:
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
    for role, continuation_ids in continuation_ids_by_role.items():
        input_ids = torch.tensor(
            [prompt_ids + continuation_ids],
            dtype=torch.long,
            device=device,
        )
        attention_mask = torch.ones_like(input_ids)
        handle = None
        if delta is not None:
            token_indices = torch.tensor([len(prompt_ids) - 1], device=device)
            handle = add_token_index_hook(
                torch=torch,
                model=model,
                layer=layer,
                token_indices=token_indices,
                delta=delta,
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
        score = continuation_score(
            torch=torch,
            logits=outputs.logits,
            prompt_length=len(prompt_ids),
            continuation_ids=continuation_ids,
            label_score_normalization=label_score_normalization,
        )
        scores[role] = float(score.item())
    return scores


def run_binary_relation_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    source_text: str,
    layer: int,
    delta: Any | None,
    max_length: int,
    labels_by_role: dict[str, str],
    label_score_normalization: str,
    binary_control_labels: dict[str, str] | None = None,
) -> dict[str, Any]:
    answer_labels = {"yes": "Yes", "no": "No"}
    scores: dict[str, Any] = {}
    answer_scores: dict[str, dict[str, float]] = {}

    def score_prompt(prompt: str) -> dict[str, float]:
        role_answer_scores = run_full_label_prompt(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            layer=layer,
            delta=delta,
            max_length=max_length,
            labels_by_role=answer_labels,
            label_score_normalization=label_score_normalization,
        )
        return {
            "yes": role_answer_scores["yes"],
            "no": role_answer_scores["no"],
            "yes_minus_no": role_answer_scores["yes"] - role_answer_scores["no"],
        }

    for role, candidate_label in labels_by_role.items():
        prompt = binary_relation_prompt(
            source_text=source_text,
            candidate_label=candidate_label,
        )
        role_answer_scores = score_prompt(prompt)
        answer_scores[role] = role_answer_scores
        scores[role] = role_answer_scores["yes_minus_no"]
    scores["answer_scores_by_role"] = answer_scores
    if binary_control_labels:
        control_scores = {}
        for control_name, candidate_label in binary_control_labels.items():
            prompt = binary_relation_prompt(
                source_text=source_text,
                candidate_label=candidate_label,
            )
            control_scores[control_name] = score_prompt(prompt)
        scores["binary_control_answer_scores"] = control_scores
        scores["binary_control_margins"] = {
            name: values["yes_minus_no"]
            for name, values in control_scores.items()
        }
    carrier_scores = {}
    target_label = labels_by_role["target"]
    for carrier in ("always_true", "always_false"):
        carrier_scores[carrier] = score_prompt(
            binary_carrier_prompt(
                carrier=carrier,
                candidate_label=target_label,
            )
        )
    scores["binary_carrier_answer_scores"] = carrier_scores
    scores["binary_carrier_margins"] = {
        name: values["yes_minus_no"] for name, values in carrier_scores.items()
    }
    return scores


def binary_yes_minus_no_margins_for_prompts(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompts: list[str],
    layer: int,
    delta: Any,
    max_length: int,
) -> Any:
    if not prompts:
        raise ValueError("At least one binary prompt is required")
    answer_ids = label_token_ids(tokenizer, {"yes": "Yes", "no": "No"})
    if len(answer_ids["yes"]) != 1 or len(answer_ids["no"]) != 1:
        raise ValueError("Optimized binary directions require one-token Yes/No labels")
    encoded = tokenizer(
        prompts,
        return_tensors="pt",
        truncation=True,
        max_length=max(1, max_length - 1),
        padding=True,
    )
    device = next(model.parameters()).device
    encoded = {name: value.to(device) for name, value in encoded.items()}
    token_indices = encoded["attention_mask"].sum(dim=1).long() - 1
    handle = add_token_index_hook(
        torch=torch,
        model=model,
        layer=layer,
        token_indices=token_indices,
        delta=delta,
    )
    try:
        outputs = model(**encoded, use_cache=False)
    finally:
        handle.remove()
    batch_indices = torch.arange(token_indices.shape[0], device=device)
    logits = outputs.logits[batch_indices, token_indices].float()
    logprobs = torch.nn.functional.log_softmax(logits, dim=-1)
    return logprobs[:, answer_ids["yes"][0]] - logprobs[:, answer_ids["no"][0]]


def generate_continuation(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    delta: Any | None,
    max_length: int,
    max_new_tokens: int,
) -> str:
    prompt_max_length = max(1, max_length - max_new_tokens)
    prompt_ids = tokenizer.encode(
        prompt,
        add_special_tokens=False,
        truncation=True,
        max_length=prompt_max_length,
    )
    if not prompt_ids:
        raise ValueError("Prompt encoded to zero tokens")

    device = next(model.parameters()).device
    generated_ids: list[int] = []
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    patch_token_indices = torch.tensor([len(prompt_ids) - 1], device=device)
    eos_token_id = tokenizer.eos_token_id
    for _step in range(max_new_tokens):
        attention_mask = torch.ones_like(input_ids)
        handle = None
        if delta is not None:
            handle = add_token_index_hook(
                torch=torch,
                model=model,
                layer=layer,
                token_indices=patch_token_indices,
                delta=delta,
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
        next_logits = outputs.logits[0, -1].float().clone()
        for special_token_id in {eos_token_id, tokenizer.pad_token_id}:
            if special_token_id is not None:
                next_logits[int(special_token_id)] = -torch.inf
        next_token_id = int(next_logits.argmax(dim=-1).item())
        generated_ids.append(next_token_id)
        input_ids = torch.cat(
            [
                input_ids,
                torch.tensor([[next_token_id]], dtype=torch.long, device=device),
            ],
            dim=1,
        )
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def run_generation_match_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    delta: Any | None,
    max_length: int,
    generation_labels_by_role: dict[str, list[str]],
) -> dict[str, Any]:
    generated_text = generate_continuation(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        prompt=prompt,
        layer=layer,
        delta=delta,
        max_length=max_length,
        max_new_tokens=GENERATION_MATCH_NEW_TOKENS,
    )
    return generation_match_scores(
        generated_text=generated_text,
        labels_by_role=generation_labels_by_role,
    )


def run_generation_readout_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    delta: Any | None,
    max_length: int,
    readout_centroids: dict[str, Any],
) -> dict[str, Any]:
    generated_text = generate_continuation(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        prompt=prompt,
        layer=layer,
        delta=delta,
        max_length=max_length,
        max_new_tokens=GENERATION_MATCH_NEW_TOKENS,
    )
    return generation_readout_scores(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        generated_text=generated_text,
        layer=layer,
        max_length=max_length,
        readout_centroids=readout_centroids,
    )


def run_scoring_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    source_text: str | None,
    layer: int,
    delta: Any | None,
    max_length: int,
    scoring_surface: str,
    token_ids: dict[str, int] | None,
    labels_by_role: dict[str, str],
    generation_labels_by_role: dict[str, list[str]] | None,
    readout_centroids: dict[str, Any] | None,
    binary_control_labels: dict[str, str] | None,
    label_score_normalization: str,
) -> dict[str, Any]:
    if scoring_surface == "option_token":
        if token_ids is None:
            raise ValueError("Option-token scoring requires token_ids")
        return run_prompt(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            layer=layer,
            delta=delta,
            max_length=max_length,
            token_ids=token_ids,
        )
    if scoring_surface == "full_label":
        return run_full_label_prompt(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            layer=layer,
            delta=delta,
            max_length=max_length,
            labels_by_role=labels_by_role,
            label_score_normalization=label_score_normalization,
        )
    if scoring_surface == "binary_relation":
        if source_text is None:
            raise ValueError("Binary-relation scoring requires source_text")
        return run_binary_relation_prompt(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            source_text=source_text,
            layer=layer,
            delta=delta,
            max_length=max_length,
            labels_by_role=labels_by_role,
            label_score_normalization=label_score_normalization,
            binary_control_labels=binary_control_labels,
        )
    if scoring_surface == "generation_match":
        if generation_labels_by_role is None:
            raise ValueError("Generation-match scoring requires generation labels")
        return run_generation_match_prompt(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            layer=layer,
            delta=delta,
            max_length=max_length,
            generation_labels_by_role=generation_labels_by_role,
        )
    if scoring_surface == "generation_readout":
        if readout_centroids is None:
            raise ValueError("Generation-readout scoring requires readout centroids")
        return run_generation_readout_prompt(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=prompt,
            layer=layer,
            delta=delta,
            max_length=max_length,
            readout_centroids=readout_centroids,
        )
    raise ValueError(f"Unknown scoring surface: {scoring_surface}")


def add_token_index_hook(
    *,
    torch: Any,
    model: Any,
    layer: int,
    token_indices: Any,
    delta: Any,
) -> Any:
    block = block_for_hidden_state_layer(model, layer)
    anchor = intervention_anchor_tensor(delta)
    patch_indices = token_indices.to(anchor.device).long()

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        adjusted = hidden_states.clone()
        batch_indices = torch.arange(adjusted.shape[0], device=adjusted.device)
        adjusted[batch_indices, patch_indices] = (
            adjusted[batch_indices, patch_indices]
            + intervention_addition(
                torch,
                adjusted[batch_indices, patch_indices],
                delta,
            )
        )
        if isinstance(output, tuple):
            return (adjusted, *output[1:])
        return adjusted

    return block.register_forward_hook(hook)


def hidden_states_for_token_prompts(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompts: list[str],
    layer: int,
    max_length: int,
) -> Any:
    if not prompts:
        raise ValueError("At least one prompt is required")
    encoded = tokenizer(
        prompts,
        return_tensors="pt",
        truncation=True,
        max_length=max(1, max_length - 1),
        padding=True,
    )
    device = next(model.parameters()).device
    encoded = {name: value.to(device) for name, value in encoded.items()}
    token_indices = encoded["attention_mask"].sum(dim=1).long() - 1
    block = block_for_hidden_state_layer(model, layer)
    captured: dict[str, Any] = {}

    def capture_hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        batch_indices = torch.arange(hidden_states.shape[0], device=hidden_states.device)
        captured["selected"] = (
            hidden_states[batch_indices, token_indices].detach().clone().float()
        )
        return output

    handle = block.register_forward_hook(capture_hook)
    try:
        with torch.no_grad():
            model(**encoded, use_cache=False)
        selected = captured.get("selected")
        if selected is None:
            raise RuntimeError("Could not capture token hidden states")
        return selected
    finally:
        handle.remove()


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


def binary_relation_gradient_direction_for_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    source_text: str,
    layer: int,
    max_length: int,
    candidate_label: str,
    label_score_normalization: str,
) -> Any:
    prompt = binary_relation_prompt(
        source_text=source_text,
        candidate_label=candidate_label,
    )
    return binary_yes_minus_no_gradient_for_prompt(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        prompt=prompt,
        layer=layer,
        max_length=max_length,
        label_score_normalization=label_score_normalization,
    )


def binary_yes_minus_no_gradient_for_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    max_length: int,
    label_score_normalization: str,
) -> Any:
    yes_ids = label_token_ids(tokenizer, {"yes": "Yes"})["yes"]
    no_ids = label_token_ids(tokenizer, {"no": "No"})["no"]
    yes_gradient = full_label_score_gradient_for_role(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        prompt=prompt,
        layer=layer,
        max_length=max_length,
        continuation_ids=yes_ids,
        label_score_normalization=label_score_normalization,
    )
    no_gradient = full_label_score_gradient_for_role(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        prompt=prompt,
        layer=layer,
        max_length=max_length,
        continuation_ids=no_ids,
        label_score_normalization=label_score_normalization,
    )
    return yes_gradient - no_gradient


def binary_control_gradient_directions(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    source_texts: list[tuple[int, str]],
    labels_by_role: dict[str, str],
    shuffled_target_label: str,
    layer: int,
    max_length: int,
    label_score_normalization: str,
) -> dict[str, Any]:
    gradients_by_control: dict[str, list[Any]] = {
        "blank": [],
        "generic": [],
        "source": [],
        "distractor": [],
        "shuffled_target": [],
        "always_false": [],
    }
    relation_control_labels = {
        "blank": "",
        "generic": "a related concept",
        "source": labels_by_role["source"],
        "distractor": labels_by_role["distractor"],
        "shuffled_target": shuffled_target_label,
    }
    for _variant_index, source_text in source_texts:
        for control_name, candidate_label in relation_control_labels.items():
            gradients_by_control[control_name].append(
                binary_relation_gradient_direction_for_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    source_text=source_text,
                    layer=layer,
                    max_length=max_length,
                    candidate_label=candidate_label,
                    label_score_normalization=label_score_normalization,
                )
            )
        gradients_by_control["always_false"].append(
            binary_yes_minus_no_gradient_for_prompt(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                prompt=binary_carrier_prompt(
                    carrier="always_false",
                    candidate_label=labels_by_role["target"],
                ),
                layer=layer,
                max_length=max_length,
                label_score_normalization=label_score_normalization,
            )
        )
    return {
        control_name: mean_tensor(torch, gradients)
        for control_name, gradients in gradients_by_control.items()
    }


def optimized_binary_prompt_sets(
    *,
    source_texts: list[tuple[int, str]],
    objective_labels_by_regime: dict[str, dict[str, str]],
    shuffled_labels_by_regime: dict[str, dict[str, str]],
    extra_control_labels_by_regime: dict[str, list[str]],
    extra_control_prompts_by_regime: dict[str, list[tuple[str, str]]] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    target_prompts = []
    control_prompts = []
    control_names = []
    for regime_part, labels_by_role in objective_labels_by_regime.items():
        shuffled_target_label = shuffled_labels_by_regime[regime_part]["target"]
        relation_control_labels = {
            "blank": "",
            "generic": "a related concept",
            "source": labels_by_role["source"],
            "distractor": labels_by_role["distractor"],
            "shuffled_target": shuffled_target_label,
        }
        for _variant_index, source_text in source_texts:
            target_prompts.append(
                binary_relation_prompt(
                    source_text=source_text,
                    candidate_label=labels_by_role["target"],
                )
            )
            for control_name, candidate_label in relation_control_labels.items():
                control_names.append(control_name)
                control_prompts.append(
                    binary_relation_prompt(
                        source_text=source_text,
                        candidate_label=candidate_label,
                    )
                )
            for extra_index, candidate_label in enumerate(
                extra_control_labels_by_regime.get(regime_part, [])
            ):
                control_names.append(f"random_null_{extra_index}")
                control_prompts.append(
                    binary_relation_prompt(
                        source_text=source_text,
                        candidate_label=candidate_label,
                    )
                )
            control_names.append("always_false")
            control_prompts.append(
                binary_carrier_prompt(
                    carrier="always_false",
                    candidate_label=labels_by_role["target"],
                )
            )
        for control_name, control_prompt in (
            extra_control_prompts_by_regime or {}
        ).get(regime_part, []):
            control_names.append(control_name)
            control_prompts.append(control_prompt)
    return target_prompts, control_prompts, control_names


def relation_control_class_from_name(control_name: str) -> str | None:
    prefix = "relation_control:"
    if not control_name.startswith(prefix):
        return None
    parts = control_name.split(":")
    if len(parts) < 2 or not parts[1]:
        return None
    return parts[1]


def filter_relation_control_prompts(
    prompts_by_regime: dict[str, list[tuple[str, str]]],
    *,
    include_classes: tuple[str, ...] = (),
    exclude_classes: tuple[str, ...] = (),
) -> dict[str, list[tuple[str, str]]]:
    include_set = set(include_classes)
    exclude_set = set(exclude_classes)
    filtered: dict[str, list[tuple[str, str]]] = {}
    for regime, prompts in prompts_by_regime.items():
        kept = []
        for control_name, prompt in prompts:
            control_class = relation_control_class_from_name(control_name)
            if control_class is None:
                continue
            if include_set and control_class not in include_set:
                continue
            if control_class in exclude_set:
                continue
            kept.append((control_name, prompt))
        filtered[regime] = kept
    return filtered


def feature_selective_binary_mask(
    *,
    torch: Any,
    reference_direction: Any,
    control_directions: list[tuple[str, Any]],
    mask_fraction: float,
    control_weight: float,
) -> tuple[Any, dict[str, Any]]:
    reference = reference_direction.detach().float()
    reference_norm = torch.linalg.vector_norm(reference).clamp(min=1e-12)
    target_abs = reference.flatten().abs()
    control_abs_values = []
    control_names = []
    for control_name, control_direction in control_directions:
        candidate = control_direction.detach().float().to(reference.device)
        candidate_norm = torch.linalg.vector_norm(candidate)
        if float(candidate_norm.item()) <= 1e-12:
            continue
        norm_matched = candidate * (reference_norm / candidate_norm)
        control_abs_values.append(norm_matched.flatten().abs())
        control_names.append(control_name)
    if control_abs_values:
        control_max = torch.stack(control_abs_values, dim=0).max(dim=0).values
    else:
        control_max = torch.zeros_like(target_abs)
    scores = target_abs - float(control_weight) * control_max
    feature_count = max(
        1,
        min(
            int(scores.numel()),
            int(round(float(mask_fraction) * int(scores.numel()))),
        ),
    )
    selected_scores, selected_indices = torch.topk(scores, k=feature_count)
    mask_flat = torch.zeros_like(target_abs)
    mask_flat[selected_indices] = 1.0
    mask = mask_flat.reshape(reference.shape).to(reference.device)
    summary = {
        "feature_mask_control_names": control_names,
        "feature_mask_count": feature_count,
        "feature_mask_fraction": float(mask_fraction),
        "feature_mask_density": float(feature_count / int(scores.numel())),
        "feature_mask_control_weight": float(control_weight),
        "feature_mask_score_mean": float(scores.mean().item()),
        "feature_mask_score_max": float(scores.max().item()),
        "feature_mask_score_min": float(scores.min().item()),
        "feature_mask_selected_score_mean": float(selected_scores.mean().item()),
        "feature_mask_selected_score_min": float(selected_scores.min().item()),
        "feature_mask_positive_score_count": int((scores > 0).sum().item()),
    }
    return mask, summary


def state_gate_for_binary_prompts(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    target_prompts: list[str],
    control_prompts: list[str],
    layer: int,
    max_length: int,
    reference_direction: Any,
    gate_directions: list[tuple[str, Any]],
    gate_temperature: float,
) -> tuple[Any, dict[str, Any]]:
    nonzero_gate_directions = []
    gate_direction_names = []
    for gate_direction_name, gate_direction in gate_directions:
        candidate = gate_direction.detach().float().to(reference_direction.device)
        if float(torch.linalg.vector_norm(candidate).item()) <= 1e-12:
            continue
        nonzero_gate_directions.append(candidate)
        gate_direction_names.append(gate_direction_name)
    gate_direction = projection_residual(
        torch,
        reference_direction.detach().float(),
        nonzero_gate_directions,
    )
    gate_direction_norm = torch.linalg.vector_norm(gate_direction)
    if float(gate_direction_norm.item()) <= 1e-12:
        gate_direction = reference_direction.detach().float()
        gate_direction_norm = torch.linalg.vector_norm(gate_direction).clamp(min=1e-12)
    gate_direction = gate_direction / gate_direction_norm
    prompts = target_prompts + control_prompts
    hidden_states = hidden_states_for_token_prompts(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        prompts=prompts,
        layer=layer,
        max_length=max_length,
    ).to(reference_direction.device)
    hidden_norms = torch.linalg.vector_norm(hidden_states, dim=-1).clamp(min=1e-12)
    gate_scores = (hidden_states * gate_direction).sum(dim=-1) / hidden_norms
    target_scores = gate_scores[: len(target_prompts)]
    control_scores = gate_scores[len(target_prompts) :]
    target_mean = target_scores.mean()
    target_min = target_scores.min()
    control_mean = control_scores.mean()
    control_max = control_scores.max()
    threshold = (target_mean + control_max) / 2.0
    summary = {
        "state_gate_direction_names": gate_direction_names,
        "state_gate_direction_norm": float(gate_direction_norm.item()),
        "state_gate_threshold": float(threshold.item()),
        "state_gate_temperature": float(gate_temperature),
        "state_gate_target_score_mean": float(target_mean.item()),
        "state_gate_target_score_min": float(target_min.item()),
        "state_gate_control_score_mean": float(control_mean.item()),
        "state_gate_control_score_max": float(control_max.item()),
        "state_gate_target_over_control_max": float((target_mean - control_max).item()),
    }
    return gate_direction.detach(), summary


def multiclass_control_group_name(control_name: str) -> str:
    if control_name.startswith("relation_control:"):
        parts = control_name.split(":")
        if len(parts) >= 2:
            return f"relation_control:{parts[1]}"
    if control_name.startswith("random_null_"):
        return "random_null"
    return control_name


def unit_normalized_rows(torch: Any, values: Any) -> Any:
    return values / torch.linalg.vector_norm(values, dim=-1, keepdim=True).clamp(
        min=1e-12,
    )


def unit_centroid(torch: Any, values: Any) -> Any:
    centroid = values.mean(dim=0)
    return centroid / torch.linalg.vector_norm(centroid).clamp(min=1e-12)


def multiclass_state_gate_for_binary_prompts(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    target_prompts: list[str],
    control_prompts: list[str],
    control_names: list[str],
    layer: int,
    max_length: int,
    gate_temperature: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if len(control_prompts) != len(control_names):
        raise ValueError("Control prompts and names must have equal length")
    prompts = target_prompts + control_prompts
    hidden_states = hidden_states_for_token_prompts(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        prompts=prompts,
        layer=layer,
        max_length=max_length,
    )
    hidden_states = hidden_states.to(next(model.parameters()).device).float()
    hidden_units = unit_normalized_rows(torch, hidden_states)
    target_units = hidden_units[: len(target_prompts)]
    control_units = hidden_units[len(target_prompts) :]
    target_centroid = unit_centroid(torch, target_units)
    grouped_control_units: dict[str, list[Any]] = {}
    for control_name, control_unit in zip(control_names, control_units, strict=True):
        grouped_control_units.setdefault(
            multiclass_control_group_name(control_name),
            [],
        ).append(control_unit)
    control_group_names = sorted(grouped_control_units)
    control_centroids = torch.stack(
        [
            unit_centroid(torch, torch.stack(grouped_control_units[group_name], dim=0))
            for group_name in control_group_names
        ],
        dim=0,
    )
    target_scores = target_units @ target_centroid
    target_control_scores = target_units @ control_centroids.T
    target_gate_margins = target_scores - target_control_scores.max(dim=-1).values
    control_scores = control_units @ target_centroid
    control_control_scores = control_units @ control_centroids.T
    control_gate_margins = control_scores - control_control_scores.max(dim=-1).values
    target_mean = target_gate_margins.mean()
    target_min = target_gate_margins.min()
    control_mean = control_gate_margins.mean()
    control_max = control_gate_margins.max()
    threshold = (target_mean + control_max) / 2.0
    payload = {
        "target_centroid": target_centroid.detach(),
        "control_centroids": control_centroids.detach(),
        "gate_threshold": float(threshold.item()),
        "gate_temperature": float(gate_temperature),
    }
    summary = {
        "multiclass_gate_control_group_names": control_group_names,
        "multiclass_gate_control_group_count": len(control_group_names),
        "multiclass_gate_threshold": float(threshold.item()),
        "multiclass_gate_temperature": float(gate_temperature),
        "multiclass_gate_target_margin_mean": float(target_mean.item()),
        "multiclass_gate_target_margin_min": float(target_min.item()),
        "multiclass_gate_control_margin_mean": float(control_mean.item()),
        "multiclass_gate_control_margin_max": float(control_max.item()),
        "multiclass_gate_target_over_control_max": float(
            (target_mean - control_max).item(),
        ),
    }
    return payload, summary


def optimize_binary_delta_for_prompt_sets(
    *,
    torch: Any,
    model: Any,
    tokenizer: Any,
    target_prompts: list[str],
    control_prompts: list[str],
    control_names: list[str],
    layer: int,
    max_length: int,
    reference_direction: Any,
    mode: str,
    basis_directions: list[tuple[str, Any]] | None = None,
    feature_mask_directions: list[tuple[str, Any]] | None = None,
    state_gate_directions: list[tuple[str, Any]] | None = None,
) -> tuple[Any, dict[str, Any]]:
    config = BINARY_OPT_DIRECTION_MODES[mode]
    steps = int(config["steps"])
    lr = float(config["lr"])
    control_weight = float(config["control_weight"])
    temperature = float(config["temperature"])
    device = next(model.parameters()).device
    reference = reference_direction.detach().float().to(device)
    reference_norm = torch.linalg.vector_norm(reference).clamp(min=1e-12)
    basis_vectors: list[Any] = []
    basis_names: list[str] = []
    if basis_directions is not None:
        for basis_name, basis_direction in basis_directions:
            candidate = basis_direction.detach().float().to(device)
            for basis_vector in basis_vectors:
                coefficient = torch.dot(candidate.flatten(), basis_vector.flatten())
                candidate = candidate - coefficient * basis_vector
            candidate_norm = torch.linalg.vector_norm(candidate)
            if float(candidate_norm.item()) <= 1e-8:
                continue
            basis_vectors.append(candidate / candidate_norm)
            basis_names.append(basis_name)
        if not basis_vectors:
            raise ValueError(f"{mode} requires at least one nonzero basis vector")
    basis_stack = torch.stack(basis_vectors, dim=0) if basis_vectors else None
    feature_mask = None
    feature_mask_summary: dict[str, Any] = {}
    if feature_mask_directions is not None:
        feature_mask, feature_mask_summary = feature_selective_binary_mask(
            torch=torch,
            reference_direction=reference,
            control_directions=feature_mask_directions,
            mask_fraction=float(config.get("mask_fraction", 1.0)),
            control_weight=float(config.get("mask_control_weight", 1.0)),
        )
    prompts = target_prompts + control_prompts
    target_count = len(target_prompts)
    if target_count == 0 or not control_prompts:
        raise ValueError("Optimized binary direction requires target and control prompts")
    state_gate_direction = None
    state_gate_summary: dict[str, Any] = {}
    multiclass_state_gate_payload = None
    multiclass_state_gate_summary: dict[str, Any] = {}
    if state_gate_directions is not None:
        state_gate_direction, state_gate_summary = state_gate_for_binary_prompts(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            target_prompts=target_prompts,
            control_prompts=control_prompts,
            layer=layer,
            max_length=max_length,
            reference_direction=reference,
            gate_directions=state_gate_directions,
            gate_temperature=float(config.get("gate_temperature", 0.05)),
        )
    if str(config.get("parameterization", "")) == "multiclass_state_gate":
        multiclass_state_gate_payload, multiclass_state_gate_summary = (
            multiclass_state_gate_for_binary_prompts(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                target_prompts=target_prompts,
                control_prompts=control_prompts,
                control_names=control_names,
                layer=layer,
                max_length=max_length,
                gate_temperature=float(config.get("gate_temperature", 0.05)),
            )
        )

    parameters = list(model.parameters())
    parameter_requires_grad = [parameter.requires_grad for parameter in parameters]
    for parameter in parameters:
        parameter.requires_grad_(False)
    try:
        coefficients: Any | None = None

        def delta_from_coefficients(current_coefficients: Any) -> Any:
            if basis_stack is None:
                raise ValueError("Cannot construct coefficient delta without basis")
            view_shape = (current_coefficients.shape[0],) + tuple(
                1 for _dimension in reference.shape
            )
            return (current_coefficients.reshape(view_shape) * basis_stack).sum(dim=0)

        def active_delta(candidate_delta: Any) -> Any:
            if feature_mask is None:
                return candidate_delta
            return candidate_delta * feature_mask

        def scoring_intervention(candidate_delta: Any) -> Any:
            patch_delta = active_delta(candidate_delta)
            if multiclass_state_gate_payload is not None:
                return {
                    "kind": "multiclass_state_gate",
                    "delta": patch_delta,
                    **multiclass_state_gate_payload,
                }
            if state_gate_direction is None:
                return patch_delta
            return {
                "kind": "state_gate",
                "delta": patch_delta,
                "gate_direction": state_gate_direction,
                "gate_threshold": state_gate_summary["state_gate_threshold"],
                "gate_temperature": state_gate_summary["state_gate_temperature"],
            }

        if basis_stack is None:
            delta = torch.zeros_like(reference, device=device, dtype=torch.float32)
            delta.requires_grad_(True)
            trainable_parameters = [delta]
        else:
            initial_coefficients = [
                torch.dot(reference.flatten(), basis_vector.flatten()).detach()
                for basis_vector in basis_vectors
            ]
            basis_coefficients = torch.stack(initial_coefficients).to(device)
            basis_coefficients.requires_grad_(True)
            trainable_parameters = [basis_coefficients]

            delta = delta_from_coefficients(basis_coefficients)
            with torch.no_grad():
                delta_norm = torch.linalg.vector_norm(delta)
                if delta_norm > reference_norm:
                    basis_coefficients.mul_(reference_norm / delta_norm)
            coefficients = basis_coefficients
        optimizer = torch.optim.Adam(trainable_parameters, lr=lr)
        final_metrics: dict[str, float] = {}
        for _step in range(steps):
            optimizer.zero_grad(set_to_none=True)
            model.zero_grad(set_to_none=True)
            if basis_stack is not None:
                if coefficients is None:
                    raise ValueError("Basis optimization requires coefficients")
                delta = delta_from_coefficients(coefficients)
            margins = binary_yes_minus_no_margins_for_prompts(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                prompts=prompts,
                layer=layer,
                delta=scoring_intervention(delta),
                max_length=max_length,
            )
            target_margins = margins[:target_count]
            control_margins = margins[target_count:]
            target_mean = target_margins.mean()
            centered_smooth_max = temperature * (
                torch.logsumexp(control_margins / temperature, dim=0)
                - torch.log(
                    torch.tensor(
                        float(control_margins.numel()),
                        device=device,
                        dtype=control_margins.dtype,
                    )
                )
            )
            control_penalty = torch.nn.functional.softplus(centered_smooth_max)
            objective = target_mean - control_weight * control_penalty
            (-objective).backward()
            optimizer.step()
            with torch.no_grad():
                if basis_stack is not None:
                    if coefficients is None:
                        raise ValueError("Basis optimization requires coefficients")
                    delta = delta_from_coefficients(coefficients)
                if feature_mask is not None and basis_stack is None:
                    delta.mul_(feature_mask)
                delta_norm = torch.linalg.vector_norm(active_delta(delta))
                if delta_norm > reference_norm:
                    if basis_stack is None:
                        delta.mul_(reference_norm / delta_norm)
                    else:
                        if coefficients is None:
                            raise ValueError("Basis optimization requires coefficients")
                        coefficients.mul_(reference_norm / delta_norm)
            final_metrics = {
                "target_margin_mean": float(target_mean.detach().item()),
                "target_margin_min": float(target_margins.detach().min().item()),
                "control_margin_mean": float(control_margins.detach().mean().item()),
                "control_margin_max": float(control_margins.detach().max().item()),
                "control_smooth_max": float(centered_smooth_max.detach().item()),
                "control_penalty": float(control_penalty.detach().item()),
                "objective": float(objective.detach().item()),
            }

        with torch.no_grad():
            if basis_stack is not None:
                if coefficients is None:
                    raise ValueError("Basis optimization requires coefficients")
                final_delta = active_delta(delta_from_coefficients(coefficients)).detach()
            else:
                final_delta = active_delta(delta).detach()
            pre_rescale_norm = torch.linalg.vector_norm(final_delta)
            if float(pre_rescale_norm.item()) > 0.0:
                final_delta = final_delta * (reference_norm / pre_rescale_norm)
            if basis_stack is not None:
                parameterization = str(config.get("basis"))
            elif multiclass_state_gate_payload is not None:
                parameterization = "multiclass_state_gate"
            elif state_gate_direction is not None:
                parameterization = str(config.get("parameterization", "state_gate"))
            elif feature_mask is not None:
                parameterization = str(config.get("parameterization", "feature_mask"))
            else:
                parameterization = "free_delta"
            summary: dict[str, Any] = {
                "mode": mode,
                "steps": steps,
                "lr": lr,
                "control_weight": control_weight,
                "temperature": temperature,
                "scope": str(config.get("scope", "pair")),
                "target_prompt_count": target_count,
                "control_prompt_count": len(control_prompts),
                "control_names": sorted(set(control_names)),
                "parameterization": parameterization,
                "basis_count": len(basis_names),
                "basis_names": basis_names,
                "reference_norm": float(reference_norm.item()),
                "pre_rescale_norm": float(pre_rescale_norm.item()),
                "post_rescale_norm": float(torch.linalg.vector_norm(final_delta).item()),
            }
            summary.update(feature_mask_summary)
            summary.update(state_gate_summary)
            summary.update(multiclass_state_gate_summary)
            summary.update(final_metrics)
        if multiclass_state_gate_payload is not None:
            final_intervention = {
                "kind": "multiclass_state_gate",
                "delta": final_delta.to(device),
                **{
                    key: value.to(device) if hasattr(value, "to") else value
                    for key, value in multiclass_state_gate_payload.items()
                },
            }
            return final_intervention, summary
        if state_gate_direction is not None:
            final_intervention = {
                "kind": "state_gate",
                "delta": final_delta.to(device),
                "gate_direction": state_gate_direction.to(device),
                "gate_threshold": state_gate_summary["state_gate_threshold"],
                "gate_temperature": state_gate_summary["state_gate_temperature"],
            }
            return final_intervention, summary
        return final_delta.to(device), summary
    finally:
        for parameter, requires_grad in zip(
            parameters,
            parameter_requires_grad,
            strict=True,
        ):
            parameter.requires_grad_(requires_grad)
        model.zero_grad(set_to_none=True)


def pair_optimized_binary_direction(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    source_texts: list[tuple[int, str]],
    objective_labels_by_regime: dict[str, dict[str, str]],
    shuffled_labels_by_regime: dict[str, dict[str, str]],
    extra_control_labels_by_regime: dict[str, list[str]],
    extra_control_prompts_by_regime: dict[str, list[tuple[str, str]]] | None = None,
    layer: int,
    max_length: int,
    reference_direction: Any,
    mode: str,
    basis_directions: list[tuple[str, Any]] | None = None,
    feature_mask_directions: list[tuple[str, Any]] | None = None,
    state_gate_directions: list[tuple[str, Any]] | None = None,
    relation_control_include_classes: tuple[str, ...] = (),
    relation_control_exclude_classes: tuple[str, ...] = (),
) -> tuple[Any, dict[str, Any]]:
    if extra_control_prompts_by_regime is not None:
        extra_control_prompts_by_regime = filter_relation_control_prompts(
            extra_control_prompts_by_regime,
            include_classes=relation_control_include_classes,
            exclude_classes=relation_control_exclude_classes,
        )
    target_prompts, control_prompts, control_names = optimized_binary_prompt_sets(
        source_texts=source_texts,
        objective_labels_by_regime=objective_labels_by_regime,
        shuffled_labels_by_regime=shuffled_labels_by_regime,
        extra_control_labels_by_regime=extra_control_labels_by_regime,
        extra_control_prompts_by_regime=extra_control_prompts_by_regime,
    )
    direction, summary = optimize_binary_delta_for_prompt_sets(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        target_prompts=target_prompts,
        control_prompts=control_prompts,
        control_names=control_names,
        layer=layer,
        max_length=max_length,
        reference_direction=reference_direction,
        mode=mode,
        basis_directions=basis_directions,
        feature_mask_directions=feature_mask_directions,
        state_gate_directions=state_gate_directions,
    )
    summary["relation_control_include_classes"] = list(
        relation_control_include_classes
    )
    summary["relation_control_exclude_classes"] = list(
        relation_control_exclude_classes
    )
    return direction, summary


def positive_family_binary_direction(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    records: list[dict[str, Any]],
    pair_specs: list[dict[str, Any]],
    concept_lookup: dict[str, dict[str, Any]],
    aliases_by_concept: dict[str, list[str]],
    train_variants: set[int],
    objective_label_scoring_regime: str,
    layer: int,
    max_length: int,
    reference_direction: Any,
    mode: str,
) -> tuple[Any, dict[str, Any]]:
    target_prompts: list[str] = []
    control_prompts: list[str] = []
    control_names: list[str] = []
    regime_parts = label_scoring_regime_parts(
        objective_label_scoring_regime,
        allow_groups=True,
    )
    for pair in pair_specs:
        left = str(pair["left"])
        right = str(pair["right"])
        distractor = str(pair["distractor"])
        current_pair_id = pair_id(left, right)
        current_kind = str(pair["kind"])
        control_class = str(pair.get("control_class", "") or "positive")
        source_texts = train_source_texts(
            records,
            concept_id=left,
            train_variant_indices=train_variants,
        )
        for regime_part in regime_parts:
            labels_by_role = labels_by_role_for_regime(
                concept_lookup=concept_lookup,
                aliases_by_concept=aliases_by_concept,
                left=left,
                right=right,
                distractor=distractor,
                label_scoring_regime=regime_part,
            )
            for _variant_index, source_text in source_texts:
                target_prompt = binary_relation_prompt(
                    source_text=source_text,
                    candidate_label=labels_by_role["target"],
                )
                if current_kind == "positive":
                    target_prompts.append(target_prompt)
                    for control_name, candidate_label in {
                        "blank": "",
                        "generic": "a related concept",
                        "source": labels_by_role["source"],
                        "distractor": labels_by_role["distractor"],
                    }.items():
                        control_names.append(f"positive_{control_name}")
                        control_prompts.append(
                            binary_relation_prompt(
                                source_text=source_text,
                                candidate_label=candidate_label,
                            )
                        )
                    control_names.append("positive_always_false")
                    control_prompts.append(
                        binary_carrier_prompt(
                            carrier="always_false",
                            candidate_label=labels_by_role["target"],
                        )
                    )
                elif current_kind == "control":
                    control_names.append(f"{control_class}:{current_pair_id}")
                    control_prompts.append(target_prompt)
    optimized_direction, summary = optimize_binary_delta_for_prompt_sets(
        torch=torch,
        tokenizer=tokenizer,
        model=model,
        target_prompts=target_prompts,
        control_prompts=control_prompts,
        control_names=control_names,
        layer=layer,
        max_length=max_length,
        reference_direction=reference_direction,
        mode=mode,
    )
    summary["positive_pair_count"] = sum(
        1 for pair in pair_specs if str(pair["kind"]) == "positive"
    )
    summary["control_pair_count"] = sum(
        1 for pair in pair_specs if str(pair["kind"]) == "control"
    )
    return optimized_direction, summary


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
        if scoring_surface in {"full_label", "generation_match", "generation_readout"}:
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
        if scoring_surface == "binary_relation":
            gradients.append(
                binary_relation_gradient_direction_for_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    source_text=source_text,
                    layer=layer,
                    max_length=max_length,
                    candidate_label=labels_by_role[objective_role],
                    label_score_normalization=label_score_normalization,
                )
            )
            continue
        raise ValueError(f"Unknown scoring surface: {scoring_surface}")
    return mean_tensor(torch, gradients)


def hidden_state_for_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    max_length: int,
) -> Any:
    input_ids = tokenizer.encode(
        prompt,
        add_special_tokens=False,
        truncation=True,
        max_length=max_length,
    )
    if not input_ids:
        raise ValueError("Prompt encoded to zero tokens")

    device = next(model.parameters()).device
    input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
    attention_mask = torch.ones_like(input_tensor)
    block = block_for_hidden_state_layer(model, layer)
    token_indices = torch.tensor([len(input_ids) - 1], device=device)
    captured: dict[str, Any] = {}

    def capture_hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        batch_indices = torch.arange(hidden_states.shape[0], device=hidden_states.device)
        captured["selected"] = (
            hidden_states[batch_indices, token_indices].detach().clone()
        )
        return output

    handle = block.register_forward_hook(capture_hook)
    try:
        with torch.no_grad():
            model(
                input_ids=input_tensor,
                attention_mask=attention_mask,
                use_cache=False,
            )
        selected = captured.get("selected")
        if selected is None:
            raise RuntimeError("Could not capture hidden-state activation")
        return selected[0].float().cpu()
    finally:
        handle.remove()


def role_readout_training_texts(
    *,
    role: str,
    role_source_texts: dict[str, list[tuple[int, str]]],
    objective_labels_by_regime: dict[str, dict[str, str]],
) -> list[str]:
    texts = [
        labels_by_role[role]
        for labels_by_role in objective_labels_by_regime.values()
    ]
    texts.extend(source_text for _variant_index, source_text in role_source_texts[role])
    return dedupe_texts(texts)


def learned_readout_centroids(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    role_source_texts: dict[str, list[tuple[int, str]]],
    objective_labels_by_regime: dict[str, dict[str, str]],
    layer: int,
    max_length: int,
) -> tuple[dict[str, Any], dict[str, int]]:
    centroids = {}
    counts = {}
    for role in ("source", "target", "distractor"):
        training_texts = role_readout_training_texts(
            role=role,
            role_source_texts=role_source_texts,
            objective_labels_by_regime=objective_labels_by_regime,
        )
        vectors = [
            normalize_vector(
                torch,
                hidden_state_for_prompt(
                    torch=torch,
                    tokenizer=tokenizer,
                    model=model,
                    prompt=readout_text_prompt(text),
                    layer=layer,
                    max_length=max_length,
                ),
            )
            for text in training_texts
        ]
        centroid = normalize_vector(torch, mean_tensor(torch, vectors))
        centroids[role] = centroid
        counts[role] = len(training_texts)
    return centroids, counts


def generation_readout_scores(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    generated_text: str,
    layer: int,
    max_length: int,
    readout_centroids: dict[str, Any],
) -> dict[str, Any]:
    vector = normalize_vector(
        torch,
        hidden_state_for_prompt(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=readout_text_prompt(generated_text),
            layer=layer,
            max_length=max_length,
        ),
    )
    scores: dict[str, Any] = {
        role: float(torch.dot(vector, centroid.float()).item())
        for role, centroid in readout_centroids.items()
    }
    role_scores = {role: float(scores[role]) for role in ("source", "target", "distractor")}
    scores["generated_text"] = generated_text
    scores["best_role"] = max(role_scores, key=lambda role: role_scores[role])
    scores["best_role_score"] = role_scores[str(scores["best_role"])]
    return scores


def mean_activation_direction(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    source_texts: list[tuple[int, str]],
    layer: int,
    max_length: int,
    prompt_frame: str,
) -> Any:
    activations = [
        hidden_state_for_prompt(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            prompt=full_label_prompt(
                source_text=source_text,
                prompt_frame=prompt_frame,
            ),
            layer=layer,
            max_length=max_length,
        )
        for _variant_index, source_text in source_texts
    ]
    return mean_tensor(torch, activations)


def learned_activation_directions(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    role_source_texts: dict[str, list[tuple[int, str]]],
    layer: int,
    max_length: int,
    prompt_frame: str,
) -> dict[str, Any]:
    role_means = {
        role: mean_activation_direction(
            torch=torch,
            tokenizer=tokenizer,
            model=model,
            source_texts=source_texts,
            layer=layer,
            max_length=max_length,
            prompt_frame=prompt_frame,
        )
        for role, source_texts in role_source_texts.items()
    }
    return {
        "caa_target_contrast": role_means["target"]
        - 0.5 * (role_means["source"] + role_means["distractor"]),
        "caa_target_minus_source": role_means["target"] - role_means["source"],
        "caa_target_minus_distractor": (
            role_means["target"] - role_means["distractor"]
        ),
    }


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


def direction_geometry_summary(
    *,
    torch: Any,
    named_vectors: list[tuple[str, Any]],
) -> dict[str, Any]:
    if not named_vectors:
        return {
            "count": 0,
            "names": [],
            "singular_values": [],
            "energy_ratios": [],
            "first_component_energy": None,
            "first_three_component_energy": None,
            "mean_pairwise_cosine": None,
        }
    names = [name for name, _vector in named_vectors]
    matrix = torch.stack(
        [
            normalize_vector(torch, vector).float()
            for _name, vector in named_vectors
        ],
        dim=0,
    )
    gram = matrix @ matrix.T
    if matrix.shape[0] > 1:
        off_diag = gram[~torch.eye(matrix.shape[0], dtype=torch.bool, device=gram.device)]
        mean_pairwise_cosine = float(off_diag.mean().item())
    else:
        mean_pairwise_cosine = None
    singular_values = torch.linalg.svdvals(matrix)
    energy = singular_values.square()
    total_energy = energy.sum().clamp(min=1e-12)
    energy_ratios = energy / total_energy
    first_three_count = min(3, energy_ratios.shape[0])
    return {
        "count": len(named_vectors),
        "names": names,
        "singular_values": [
            float(value.item()) for value in singular_values[:10]
        ],
        "energy_ratios": [
            float(value.item()) for value in energy_ratios[:10]
        ],
        "first_component_energy": float(energy_ratios[0].item()),
        "first_three_component_energy": float(
            energy_ratios[:first_three_count].sum().item()
        ),
        "mean_pairwise_cosine": mean_pairwise_cosine,
    }


def control_pc_basis(
    *,
    torch: Any,
    named_vectors: list[tuple[str, Any]],
    max_components: int,
) -> dict[str, Any]:
    if not named_vectors:
        return {
            "names": [],
            "vectors": [],
            "singular_values": [],
        }
    matrix = torch.stack(
        [
            normalize_vector(torch, vector).float().flatten()
            for _name, vector in named_vectors
        ],
        dim=0,
    )
    _u, singular_values, vh = torch.linalg.svd(matrix, full_matrices=False)
    component_count = min(max_components, int(vh.shape[0]))
    example = named_vectors[0][1].float()
    return {
        "names": [name for name, _vector in named_vectors],
        "vectors": [
            vh[index].reshape_as(example).to(example.device)
            for index in range(component_count)
        ],
        "singular_values": [
            singular_values[index] for index in range(component_count)
        ],
    }


def binary_pc_adjusted_direction(
    *,
    torch: Any,
    target_direction: Any,
    pc_basis: dict[str, Any] | None,
    adjustment: str,
    component_count: int,
) -> Any:
    if not pc_basis or not pc_basis.get("vectors"):
        return target_direction
    vectors = pc_basis["vectors"][:component_count]
    singular_values = pc_basis.get("singular_values", [])[:component_count]
    if not vectors:
        return target_direction
    adjusted = target_direction.float()
    for index, basis in enumerate(vectors):
        basis_direction = normalize_vector(torch, basis).to(
            device=adjusted.device,
            dtype=adjusted.dtype,
        )
        coefficient = torch.dot(adjusted.flatten(), basis_direction.flatten())
        if adjustment == "residualize":
            adjusted = adjusted - coefficient * basis_direction
        elif adjustment == "whiten":
            singular_value = singular_values[index].to(
                device=adjusted.device,
                dtype=adjusted.dtype,
            )
            damped_coefficient = coefficient / singular_value.clamp(min=1e-12)
            adjusted = (
                adjusted
                - coefficient * basis_direction
                + damped_coefficient * basis_direction
            )
        else:
            raise ValueError(f"Unknown binary PC adjustment: {adjustment}")
    return rescale_to_reference_norm(torch, adjusted, target_direction)


def remove_projection(torch: Any, direction: Any, basis: Any | None) -> Any:
    if basis is None:
        return direction
    basis_norm_squared = torch.dot(basis.float(), basis.float())
    if float(basis_norm_squared.item()) == 0.0:
        return direction
    coefficient = torch.dot(direction.float(), basis.float()) / basis_norm_squared
    return direction - coefficient.to(direction.dtype) * basis


def projection_residual(torch: Any, direction: Any, basis_vectors: list[Any | None]) -> Any:
    residual = direction
    for basis in basis_vectors:
        residual = remove_projection(torch, residual, basis)
    return residual


def rescale_to_reference_norm(torch: Any, direction: Any, reference: Any) -> Any:
    direction_norm = torch.linalg.vector_norm(direction)
    if float(direction_norm.item()) == 0.0:
        return direction
    reference_norm = torch.linalg.vector_norm(reference)
    return direction * (reference_norm / direction_norm)


def penalty_direction(
    *,
    torch: Any,
    target_direction: Any,
    penalty_basis: Any | None,
    weight: float,
) -> Any:
    if penalty_basis is None:
        return target_direction
    norm_matched_penalty = rescale_to_reference_norm(
        torch,
        penalty_basis,
        target_direction,
    )
    return target_direction - float(weight) * norm_matched_penalty


def multi_control_penalty_direction(
    *,
    torch: Any,
    target_direction: Any,
    penalty_bases: list[Any],
    weight: float,
) -> Any:
    if not penalty_bases:
        return target_direction
    norm_matched_penalties = [
        rescale_to_reference_norm(torch, penalty_basis, target_direction)
        for penalty_basis in penalty_bases
    ]
    return target_direction - float(weight) * mean_tensor(torch, norm_matched_penalties)


def direction_for_mode(
    *,
    torch: Any,
    learned_directions: dict[str, Any],
    activation_directions: dict[str, Any],
    binary_optimized_directions: dict[str, Any],
    control_target_direction: Any | None,
    control_target_directions: list[Any],
    hard_control_target_direction: Any | None,
    binary_control_directions: dict[str, Any],
    binary_control_pc_basis: dict[str, Any] | None,
    mode: str,
    seed: int,
) -> Any:
    target_direction = learned_directions["target"]
    if mode == "random_same_norm":
        return random_same_norm(
            torch=torch,
            direction=target_direction,
            seed=seed,
        )
    if mode in activation_directions:
        return rescale_to_reference_norm(
            torch,
            activation_directions[mode],
            target_direction,
        )
    if mode in binary_optimized_directions:
        return binary_optimized_directions[mode]
    if mode in BINARY_OPT_DIRECTION_MODES:
        raise ValueError(
            f"{mode} requires optimized binary directions; use binary_relation scoring"
        )
    if mode == "target_resid_sd":
        return rescale_to_reference_norm(
            torch,
            projection_residual(
                torch,
                target_direction,
                [
                    learned_directions["source"],
                    learned_directions["distractor"],
                ],
            ),
            target_direction,
        )
    if mode == "target_resid_control":
        return rescale_to_reference_norm(
            torch,
            projection_residual(torch, target_direction, [control_target_direction]),
            target_direction,
        )
    if mode == "target_resid_all":
        return rescale_to_reference_norm(
            torch,
            projection_residual(
                torch,
                target_direction,
                [
                    control_target_direction,
                    learned_directions["source"],
                    learned_directions["distractor"],
                ],
            ),
            target_direction,
        )
    if mode in PENALTY_DIRECTION_MODES:
        penalty_kind, weight = PENALTY_DIRECTION_MODES[mode]
        if penalty_kind == "control_set":
            return multi_control_penalty_direction(
                torch=torch,
                target_direction=target_direction,
                penalty_bases=control_target_directions,
                weight=weight,
            )
        penalty_basis = (
            hard_control_target_direction
            if penalty_kind == "hard_control"
            else control_target_direction
        )
        return penalty_direction(
            torch=torch,
            target_direction=target_direction,
            penalty_basis=penalty_basis,
            weight=weight,
        )
    if mode in BINARY_CONTROL_DIRECTION_MODES:
        if not binary_control_directions:
            raise ValueError(
                f"{mode} requires binary control directions; use binary_relation scoring"
            )
        return multi_control_penalty_direction(
            torch=torch,
            target_direction=target_direction,
            penalty_bases=list(binary_control_directions.values()),
            weight=BINARY_CONTROL_DIRECTION_MODES[mode],
        )
    if mode in BINARY_PC_DIRECTION_MODES:
        if not binary_control_pc_basis:
            raise ValueError(
                f"{mode} requires a binary control PC basis; "
                "use binary_relation scoring"
            )
        adjustment, component_count = BINARY_PC_DIRECTION_MODES[mode]
        return binary_pc_adjusted_direction(
            torch=torch,
            target_direction=target_direction,
            pc_basis=binary_control_pc_basis,
            adjustment=adjustment,
            component_count=component_count,
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
    aliases_by_concept: dict[str, list[str]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    layer_roles: dict[str, int],
    scales: list[float],
    direction_modes: list[str],
    option_orders: list[list[str]],
    train_variant_indices: list[int],
    holdout_variant_index: int,
    max_length: int,
    scoring_surface: str,
    prompt_frame: str,
    objective_label_scoring_regimes: list[str],
    eval_label_scoring_regimes: list[str],
    label_score_normalization: str,
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
    binary_gradient_geometry = []
    for role, layer in layer_roles.items():
        learned_records: dict[tuple[str, str], dict[str, Any]] = {}
        for pair_index, pair in enumerate(pair_specs):
            left = str(pair["left"])
            right = str(pair["right"])
            distractor = str(pair["distractor"])
            current_pair_id = pair_id(left, right)
            role_source_texts = {
                "source": train_source_texts(
                    records,
                    concept_id=left,
                    train_variant_indices=train_variants,
                ),
                "target": train_source_texts(
                    records,
                    concept_id=right,
                    train_variant_indices=train_variants,
                ),
                "distractor": train_source_texts(
                    records,
                    concept_id=distractor,
                    train_variant_indices=train_variants,
                ),
            }
            source_texts = role_source_texts["source"]
            heldout_text = heldout_source_text(
                records,
                concept_id=left,
                holdout_variant_index=holdout_variant_index,
            )
            activation_prompt_frame = "source_passage"
            activation_directions = learned_activation_directions(
                torch=torch,
                tokenizer=tokenizer,
                model=model,
                role_source_texts=role_source_texts,
                layer=layer,
                max_length=max_length,
                prompt_frame=activation_prompt_frame,
            )
            for objective_label_scoring_regime in objective_label_scoring_regimes:
                objective_regime_parts = label_scoring_regime_parts(
                    objective_label_scoring_regime,
                    allow_groups=True,
                )
                objective_labels_by_regime = {
                    regime_part: labels_by_role_for_regime(
                        concept_lookup=concept_lookup,
                        aliases_by_concept=aliases_by_concept,
                        left=left,
                        right=right,
                        distractor=distractor,
                        label_scoring_regime=regime_part,
                    )
                    for regime_part in objective_regime_parts
                }
                learned_directions = {}
                for objective_role in ("target", "source", "distractor"):
                    regime_directions = [
                        learned_gradient_direction(
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
                            scoring_surface=(
                                "full_label"
                                if scoring_surface
                                in {"generation_match", "generation_readout"}
                                else scoring_surface
                            ),
                            prompt_frame=prompt_frame,
                            label_score_normalization=label_score_normalization,
                        ).to(device)
                        for labels_by_role in objective_labels_by_regime.values()
                    ]
                    learned_directions[objective_role] = mean_tensor(
                        torch,
                        regime_directions,
                    ).to(device)
                binary_control_directions: dict[str, Any] = {}
                binary_optimized_directions: dict[str, Any] = {}
                binary_optimized_direction_summaries: dict[str, Any] = {}
                if scoring_surface == "binary_relation":
                    control_direction_groups: dict[str, list[Any]] = {}
                    shuffled_pair = pair_specs[(pair_index + 1) % len(pair_specs)]
                    shuffled_labels_by_regime = {}
                    for regime_part, labels_by_role in objective_labels_by_regime.items():
                        shuffled_labels_by_role = labels_by_role_for_regime(
                            concept_lookup=concept_lookup,
                            aliases_by_concept=aliases_by_concept,
                            left=str(shuffled_pair["left"]),
                            right=str(shuffled_pair["right"]),
                            distractor=str(shuffled_pair["distractor"]),
                            label_scoring_regime=regime_part,
                        )
                        shuffled_labels_by_regime[regime_part] = shuffled_labels_by_role
                        control_directions_for_regime = binary_control_gradient_directions(
                            torch=torch,
                            tokenizer=tokenizer,
                            model=model,
                            source_texts=source_texts,
                            labels_by_role=labels_by_role,
                            shuffled_target_label=shuffled_labels_by_role["target"],
                            layer=layer,
                            max_length=max_length,
                            label_score_normalization=label_score_normalization,
                        )
                        for control_name, control_direction in (
                            control_directions_for_regime.items()
                        ):
                            control_direction_groups.setdefault(
                                control_name,
                                [],
                            ).append(control_direction.to(device))
                    binary_control_directions = {
                        control_name: mean_tensor(torch, directions).to(device)
                        for control_name, directions in control_direction_groups.items()
                    }
                    extra_control_labels_by_regime: dict[str, list[str]] = {}
                    for regime_part in objective_regime_parts:
                        extra_control_labels = []
                        seen_extra_control_labels = set()
                        for control_pair in pair_specs:
                            if str(control_pair["kind"]) != "control":
                                continue
                            control_pair_id = pair_id(
                                str(control_pair["left"]),
                                str(control_pair["right"]),
                            )
                            if control_pair_id == current_pair_id:
                                continue
                            control_labels_by_role = labels_by_role_for_regime(
                                concept_lookup=concept_lookup,
                                aliases_by_concept=aliases_by_concept,
                                left=str(control_pair["left"]),
                                right=str(control_pair["right"]),
                                distractor=str(control_pair["distractor"]),
                                label_scoring_regime=regime_part,
                            )
                            candidate_label = control_labels_by_role["target"]
                            normalized_label = normalize_generated_text(candidate_label)
                            if normalized_label in seen_extra_control_labels:
                                continue
                            seen_extra_control_labels.add(normalized_label)
                            extra_control_labels.append(candidate_label)
                        extra_control_labels_by_regime[regime_part] = (
                            extra_control_labels
                        )
                    relation_control_prompts_by_regime: dict[
                        str,
                        list[tuple[str, str]],
                    ] = {}
                    for regime_part in objective_regime_parts:
                        relation_control_prompts = []
                        seen_relation_control_prompts = set()
                        for control_pair in pair_specs:
                            if str(control_pair["kind"]) != "control":
                                continue
                            control_pair_id = pair_id(
                                str(control_pair["left"]),
                                str(control_pair["right"]),
                            )
                            if control_pair_id == current_pair_id:
                                continue
                            control_labels_by_role = labels_by_role_for_regime(
                                concept_lookup=concept_lookup,
                                aliases_by_concept=aliases_by_concept,
                                left=str(control_pair["left"]),
                                right=str(control_pair["right"]),
                                distractor=str(control_pair["distractor"]),
                                label_scoring_regime=regime_part,
                            )
                            control_source_texts = train_source_texts(
                                records,
                                concept_id=str(control_pair["left"]),
                                train_variant_indices=train_variants,
                            )
                            control_class = str(
                                control_pair.get("control_class", "control")
                            )
                            for variant_index, control_source_text in (
                                control_source_texts
                            ):
                                control_prompt = binary_relation_prompt(
                                    source_text=control_source_text,
                                    candidate_label=control_labels_by_role["target"],
                                )
                                prompt_key = normalize_generated_text(control_prompt)
                                if prompt_key in seen_relation_control_prompts:
                                    continue
                                seen_relation_control_prompts.add(prompt_key)
                                relation_control_prompts.append(
                                    (
                                        (
                                            "relation_control:"
                                            f"{control_class}:{control_pair_id}:"
                                            f"v{variant_index}"
                                        ),
                                        control_prompt,
                                    )
                                )
                        relation_control_prompts_by_regime[regime_part] = (
                            relation_control_prompts
                        )
                    for mode in direction_modes:
                        if mode not in BINARY_OPT_DIRECTION_MODES:
                            continue
                        if (
                            str(BINARY_OPT_DIRECTION_MODES[mode].get("scope", "pair"))
                            != "pair"
                        ):
                            continue
                        basis_directions = None
                        feature_mask_directions = None
                        state_gate_directions = None
                        if (
                            str(BINARY_OPT_DIRECTION_MODES[mode].get("basis", ""))
                            == "readout_span"
                        ):
                            basis_directions = [
                                ("target", learned_directions["target"]),
                                ("source", learned_directions["source"]),
                                ("distractor", learned_directions["distractor"]),
                            ]
                            basis_directions.extend(
                                (
                                    f"binary_control_{control_name}",
                                    control_direction,
                                )
                                for control_name, control_direction in (
                                    binary_control_directions.items()
                                )
                            )
                        if (
                            str(
                                BINARY_OPT_DIRECTION_MODES[mode].get(
                                    "parameterization",
                                    "",
                                )
                            )
                            == "feature_mask"
                        ):
                            feature_mask_directions = [
                                ("source", learned_directions["source"]),
                                ("distractor", learned_directions["distractor"]),
                            ]
                            feature_mask_directions.extend(
                                (
                                    f"binary_control_{control_name}",
                                    control_direction,
                                )
                                for control_name, control_direction in (
                                    binary_control_directions.items()
                                )
                            )
                        if (
                            str(
                                BINARY_OPT_DIRECTION_MODES[mode].get(
                                    "parameterization",
                                    "",
                                )
                            )
                            == "state_gate"
                        ):
                            state_gate_directions = [
                                ("source", learned_directions["source"]),
                                ("distractor", learned_directions["distractor"]),
                            ]
                            state_gate_directions.extend(
                                (
                                    f"binary_control_{control_name}",
                                    control_direction,
                                )
                                for control_name, control_direction in (
                                    binary_control_directions.items()
                                )
                            )
                        optimized_direction, optimized_summary = (
                            pair_optimized_binary_direction(
                                torch=torch,
                                tokenizer=tokenizer,
                                model=model,
                                source_texts=source_texts,
                                objective_labels_by_regime=(
                                    objective_labels_by_regime
                                ),
                                shuffled_labels_by_regime=shuffled_labels_by_regime,
                                extra_control_labels_by_regime=(
                                    extra_control_labels_by_regime
                                ),
                                extra_control_prompts_by_regime=(
                                    relation_control_prompts_by_regime
                                    if BINARY_OPT_DIRECTION_MODES[mode].get(
                                        "relation_control_prompts",
                                        False,
                                    )
                                    else None
                                ),
                                layer=layer,
                                max_length=max_length,
                                reference_direction=learned_directions["target"],
                                mode=mode,
                                basis_directions=basis_directions,
                                feature_mask_directions=feature_mask_directions,
                                state_gate_directions=state_gate_directions,
                                relation_control_include_classes=tuple(
                                    str(control_class)
                                    for control_class in (
                                        BINARY_OPT_DIRECTION_MODES[mode].get(
                                            "include_relation_control_classes",
                                            (),
                                        )
                                    )
                                ),
                                relation_control_exclude_classes=tuple(
                                    str(control_class)
                                    for control_class in (
                                        BINARY_OPT_DIRECTION_MODES[mode].get(
                                            "exclude_relation_control_classes",
                                            (),
                                        )
                                    )
                                ),
                            )
                        )
                        binary_optimized_directions[mode] = move_direction_to_device(
                            optimized_direction,
                            device
                        )
                        binary_optimized_direction_summaries[mode] = optimized_summary
                norms = {
                    objective_role: float(torch.linalg.vector_norm(direction).item())
                    for objective_role, direction in learned_directions.items()
                }
                binary_control_norms = {
                    control_name: float(torch.linalg.vector_norm(direction).item())
                    for control_name, direction in binary_control_directions.items()
                }
                binary_control_mean_direction = (
                    mean_tensor(
                        torch,
                        list(binary_control_directions.values()),
                    ).to(device)
                    if binary_control_directions
                    else None
                )
                activation_norms = {
                    activation_mode: float(torch.linalg.vector_norm(direction).item())
                    for activation_mode, direction in activation_directions.items()
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
                if binary_control_directions:
                    learned_alignment["target_binary_control_mean_cosine"] = (
                        cosine_or_none(
                            torch,
                            learned_directions["target"],
                            binary_control_mean_direction,
                        )
                    )
                    for control_name, control_direction in (
                        binary_control_directions.items()
                    ):
                        learned_alignment[
                            f"target_binary_control_{control_name}_cosine"
                        ] = cosine_or_none(
                            torch,
                            learned_directions["target"],
                            control_direction,
                        )
                readout_centroids = None
                readout_training_counts = None
                if scoring_surface == "generation_readout":
                    readout_centroids, readout_training_counts = (
                        learned_readout_centroids(
                            torch=torch,
                            tokenizer=tokenizer,
                            model=model,
                            role_source_texts=role_source_texts,
                            objective_labels_by_regime=objective_labels_by_regime,
                            layer=layer,
                            max_length=max_length,
                        )
                    )
                learned_records[(current_pair_id, objective_label_scoring_regime)] = {
                    "pair_index": pair_index,
                    "left": left,
                    "right": right,
                    "kind": str(pair["kind"]),
                    "distractor": distractor,
                    "heldout_text": heldout_text,
                    "objective_label_regime_parts": objective_regime_parts,
                    "objective_labels_by_regime": objective_labels_by_regime,
                    "objective_labels_by_role": (
                        next(iter(objective_labels_by_regime.values()))
                        if len(objective_labels_by_regime) == 1
                        else objective_labels_by_regime
                    ),
                    "learned_directions": learned_directions,
                    "activation_directions": activation_directions,
                    "binary_control_directions": binary_control_directions,
                    "binary_optimized_directions": binary_optimized_directions,
                    "binary_optimized_direction_summaries": (
                        binary_optimized_direction_summaries
                    ),
                    "norms": norms,
                    "binary_control_norms": binary_control_norms,
                    "activation_norms": activation_norms,
                    "activation_prompt_frame": activation_prompt_frame,
                    "learned_alignment": learned_alignment,
                    "readout_centroids": readout_centroids,
                    "readout_training_counts": readout_training_counts,
                }

        positive_family_modes = [
            mode
            for mode in direction_modes
            if mode in BINARY_OPT_DIRECTION_MODES
            and str(BINARY_OPT_DIRECTION_MODES[mode].get("scope", "pair"))
            == "positive_family"
        ]
        if scoring_surface == "binary_relation" and positive_family_modes:
            for objective_label_scoring_regime in objective_label_scoring_regimes:
                regime_records = [
                    learned_records[
                        (
                            pair_id(str(pair["left"]), str(pair["right"])),
                            objective_label_scoring_regime,
                        )
                    ]
                    for pair in pair_specs
                ]
                positive_reference_directions = [
                    record["learned_directions"]["target"]
                    for record in regime_records
                    if str(record["kind"]) == "positive"
                ]
                if not positive_reference_directions:
                    raise ValueError(
                        "Positive-family binary optimization requires positives"
                    )
                reference_direction = mean_tensor(
                    torch,
                    positive_reference_directions,
                ).to(device)
                for mode in positive_family_modes:
                    optimized_direction, optimized_summary = (
                        positive_family_binary_direction(
                            torch=torch,
                            tokenizer=tokenizer,
                            model=model,
                            records=records,
                            pair_specs=pair_specs,
                            concept_lookup=concept_lookup,
                            aliases_by_concept=aliases_by_concept,
                            train_variants=train_variants,
                            objective_label_scoring_regime=(
                                objective_label_scoring_regime
                            ),
                            layer=layer,
                            max_length=max_length,
                            reference_direction=reference_direction,
                            mode=mode,
                        )
                    )
                    for record in regime_records:
                        record["binary_optimized_directions"][mode] = (
                            optimized_direction.to(device)
                        )
                        record["binary_optimized_direction_summaries"][mode] = (
                            optimized_summary
                        )

        binary_pc_component_count = max(
            (
                component_count
                for mode in direction_modes
                if mode in BINARY_PC_DIRECTION_MODES
                for _adjustment, component_count in [BINARY_PC_DIRECTION_MODES[mode]]
            ),
            default=0,
        )
        binary_control_pc_bases_by_regime: dict[str, dict[str, Any]] = {}
        if scoring_surface == "binary_relation" and binary_pc_component_count > 0:
            for objective_label_scoring_regime in objective_label_scoring_regimes:
                regime_records = [
                    learned_records[
                        (
                            pair_id(str(pair["left"]), str(pair["right"])),
                            objective_label_scoring_regime,
                        )
                    ]
                    for pair in pair_specs
                ]
                control_vectors = [
                    (
                        (
                            f"{record['pair_index']}:{record['left']}->"
                            f"{record['right']}:{control_name}"
                        ),
                        control_direction,
                    )
                    for record in regime_records
                    for control_name, control_direction in (
                        record["binary_control_directions"].items()
                    )
                ]
                binary_control_pc_bases_by_regime[objective_label_scoring_regime] = (
                    control_pc_basis(
                        torch=torch,
                        named_vectors=control_vectors,
                        max_components=binary_pc_component_count,
                    )
                )

        control_pair_ids = [
            pair_id(str(pair["left"]), str(pair["right"]))
            for pair in pair_specs
            if str(pair["kind"]) == "control"
        ]
        hard_control_pair_ids = [
            pair_id(str(pair["left"]), str(pair["right"]))
            for pair in pair_specs
            if str(pair["kind"]) == "control"
            and str(pair["left"]) == "valence"
            and str(pair["right"]) == "steering_vector"
        ]
        if len(hard_control_pair_ids) != 1:
            raise ValueError(
                "Expected exactly one hard control pair: "
                f"valence->steering_vector; found {hard_control_pair_ids}"
            )
        hard_control_pair_id = hard_control_pair_ids[0]
        for pair in pair_specs:
            left = str(pair["left"])
            right = str(pair["right"])
            distractor = str(pair["distractor"])
            current_pair_id = pair_id(left, right)
            current_kind = str(pair["kind"])
            for objective_label_scoring_regime in objective_label_scoring_regimes:
                record = learned_records[(current_pair_id, objective_label_scoring_regime)]
                control_directions = [
                    learned_records[
                        (control_pair_id, objective_label_scoring_regime)
                    ]["learned_directions"]["target"]
                    for control_pair_id in control_pair_ids
                    if current_kind != "control" or control_pair_id != current_pair_id
                ]
                if not control_directions:
                    control_directions = [
                        learned_records[
                            (control_pair_id, objective_label_scoring_regime)
                        ]["learned_directions"]["target"]
                        for control_pair_id in control_pair_ids
                    ]
                control_basis_pair_ids = [
                    control_pair_id
                    for control_pair_id in control_pair_ids
                    if current_kind != "control" or control_pair_id != current_pair_id
                ]
                if not control_basis_pair_ids:
                    control_basis_pair_ids = list(control_pair_ids)
                control_target_direction = (
                    mean_tensor(torch, control_directions).to(device)
                    if control_directions
                    else None
                )
                control_target_direction_norm = (
                    float(torch.linalg.vector_norm(control_target_direction).item())
                    if control_target_direction is not None
                    else None
                )
                hard_control_target_direction = learned_records[
                    (hard_control_pair_id, objective_label_scoring_regime)
                ]["learned_directions"]["target"]
                hard_control_target_direction_norm = float(
                    torch.linalg.vector_norm(hard_control_target_direction).item()
                )
                objective_labels_by_role = record["objective_labels_by_role"]
                heldout_text = str(record["heldout_text"])
                learned_directions = record["learned_directions"]
                activation_directions = record["activation_directions"]
                binary_control_directions = record["binary_control_directions"]
                binary_optimized_directions = record["binary_optimized_directions"]
                binary_optimized_direction_summaries = record[
                    "binary_optimized_direction_summaries"
                ]
                binary_control_pc_basis = binary_control_pc_bases_by_regime.get(
                    objective_label_scoring_regime
                )
                binary_control_pc_singular_values = (
                    [
                        float(value.item())
                        for value in binary_control_pc_basis.get(
                            "singular_values",
                            [],
                        )
                    ]
                    if binary_control_pc_basis
                    else []
                )
                norms = record["norms"]
                binary_control_norms = record["binary_control_norms"]
                activation_norms = record["activation_norms"]
                activation_prompt_frame = str(record["activation_prompt_frame"])
                readout_centroids = record.get("readout_centroids")
                readout_training_counts = record.get("readout_training_counts")
                learned_alignment = dict(record["learned_alignment"])
                learned_alignment["target_control_cosine"] = cosine_or_none(
                    torch,
                    learned_directions["target"],
                    control_target_direction,
                )
                learned_alignment["target_hard_control_cosine"] = cosine_or_none(
                    torch,
                    learned_directions["target"],
                    hard_control_target_direction,
                )
                if binary_control_pc_basis:
                    for pc_index, pc_vector in enumerate(
                        binary_control_pc_basis.get("vectors", [])[:3],
                        start=1,
                    ):
                        learned_alignment[
                            f"target_binary_control_pc{pc_index}_cosine"
                        ] = cosine_or_none(
                            torch,
                            learned_directions["target"],
                            pc_vector,
                        )
                for eval_label_scoring_regime in eval_label_scoring_regimes:
                    eval_labels_by_role = labels_by_role_for_regime(
                        concept_lookup=concept_lookup,
                        aliases_by_concept=aliases_by_concept,
                        left=left,
                        right=right,
                        distractor=distractor,
                        label_scoring_regime=eval_label_scoring_regime,
                    )
                    shuffled_pair = pair_specs[(int(record["pair_index"]) + 1) % len(pair_specs)]
                    shuffled_labels_by_role = labels_by_role_for_regime(
                        concept_lookup=concept_lookup,
                        aliases_by_concept=aliases_by_concept,
                        left=str(shuffled_pair["left"]),
                        right=str(shuffled_pair["right"]),
                        distractor=str(shuffled_pair["distractor"]),
                        label_scoring_regime=eval_label_scoring_regime,
                    )
                    binary_control_labels = {
                        "blank": "",
                        "generic": "a related concept",
                        "source": eval_labels_by_role["source"],
                        "distractor": eval_labels_by_role["distractor"],
                        "shuffled_target": shuffled_labels_by_role["target"],
                    }
                    generation_labels = generation_match_labels_by_role(
                        concept_lookup=concept_lookup,
                        aliases_by_concept=aliases_by_concept,
                        left=left,
                        right=right,
                        distractor=distractor,
                    )
                    prompt_specs: list[dict[str, Any]] = []
                    if scoring_surface == "option_token":
                        for option_order in parsed_orders:
                            prompt_specs.append(
                                {
                                    "prompt": calibration_prompt(
                                        source_text=heldout_text,
                                        labels_by_role=eval_labels_by_role,
                                        option_order=option_order,
                                    ),
                                    "option_order": option_order_key(option_order),
                                    "token_ids": role_token_ids(
                                        option_order,
                                        token_ids_by_slot,
                                    ),
                                }
                            )
                    elif scoring_surface == "full_label":
                        prompt_specs.append(
                            {
                                "prompt": full_label_prompt(
                                    source_text=heldout_text,
                                    prompt_frame=prompt_frame,
                                ),
                                "option_order": "full_label",
                                "token_ids": None,
                                "source_text": None,
                                "binary_control_labels": None,
                            }
                        )
                    elif scoring_surface == "binary_relation":
                        prompt_specs.append(
                            {
                                "prompt": binary_relation_prompt(
                                    source_text=heldout_text,
                                    candidate_label=eval_labels_by_role["target"],
                                ),
                                "option_order": "binary_relation",
                                "token_ids": None,
                                "source_text": heldout_text,
                                "binary_control_labels": binary_control_labels,
                            }
                        )
                    elif scoring_surface in {"generation_match", "generation_readout"}:
                        prompt_specs.append(
                            {
                                "prompt": full_label_prompt(
                                    source_text=heldout_text,
                                    prompt_frame=prompt_frame,
                                ),
                                "option_order": scoring_surface,
                                "token_ids": None,
                                "source_text": None,
                                "binary_control_labels": None,
                            }
                        )
                    else:
                        raise ValueError(f"Unknown scoring surface: {scoring_surface}")
                    for order_index, prompt_spec in enumerate(prompt_specs):
                        prompt = str(prompt_spec["prompt"])
                        baseline_scores = run_scoring_prompt(
                            torch=torch,
                            tokenizer=tokenizer,
                            model=model,
                            prompt=prompt,
                            source_text=prompt_spec.get("source_text"),
                            layer=layer,
                            delta=None,
                            max_length=max_length,
                            scoring_surface=scoring_surface,
                            token_ids=prompt_spec["token_ids"],
                            labels_by_role=eval_labels_by_role,
                            generation_labels_by_role=generation_labels,
                            readout_centroids=readout_centroids,
                            binary_control_labels=prompt_spec.get(
                                "binary_control_labels"
                            ),
                            label_score_normalization=label_score_normalization,
                        )
                        for scale_index, scale in enumerate(scales):
                            for mode_index, mode in enumerate(direction_modes):
                                direction = direction_for_mode(
                                    torch=torch,
                                    learned_directions=learned_directions,
                                    activation_directions=activation_directions,
                                    binary_optimized_directions=(
                                        binary_optimized_directions
                                    ),
                                    control_target_direction=control_target_direction,
                                    control_target_directions=control_directions,
                                    hard_control_target_direction=(
                                        hard_control_target_direction
                                    ),
                                    binary_control_directions=(
                                        binary_control_directions
                                    ),
                                    binary_control_pc_basis=(
                                        binary_control_pc_basis
                                    ),
                                    mode=mode,
                                    seed=(
                                        seed
                                        + layer * 100_003
                                        + int(record["pair_index"]) * 1_009
                                        + order_index * 97
                                        + scale_index * 13
                                        + mode_index
                                    ),
                                )
                                direction_norm = direction_norm_value(
                                    torch,
                                    direction,
                                )
                                delta = scale_direction(direction, float(scale))
                                steered_scores = run_scoring_prompt(
                                    torch=torch,
                                    tokenizer=tokenizer,
                                    model=model,
                                    prompt=prompt,
                                    source_text=prompt_spec.get("source_text"),
                                    layer=layer,
                                    delta=delta,
                                    max_length=max_length,
                                    scoring_surface=scoring_surface,
                                    token_ids=prompt_spec["token_ids"],
                                    labels_by_role=eval_labels_by_role,
                                    generation_labels_by_role=generation_labels,
                                    readout_centroids=readout_centroids,
                                    binary_control_labels=prompt_spec.get(
                                        "binary_control_labels"
                                    ),
                                    label_score_normalization=(
                                        label_score_normalization
                                    ),
                                )
                                rows.append(
                                    {
                                        "pair": pair_id(left, right),
                                        "left": left,
                                        "right": right,
                                        "kind": current_kind,
                                        "distractor": distractor,
                                        "control_class": str(
                                            pair.get("control_class", "")
                                        ),
                                        "role": role,
                                        "layer": layer,
                                        "scale": float(scale),
                                        "direction_mode": mode,
                                        "objective_role": objective_role_for_mode(mode),
                                        "direction_norm": direction_norm,
                                        "control_target_direction_norm": (
                                            control_target_direction_norm
                                        ),
                                        "hard_control_target_direction_norm": (
                                            hard_control_target_direction_norm
                                        ),
                                        "binary_control_direction_norms": (
                                            binary_control_norms
                                        ),
                                        "binary_control_pc_singular_values": (
                                            binary_control_pc_singular_values
                                        ),
                                        "binary_optimized_direction_summaries": (
                                            binary_optimized_direction_summaries
                                        ),
                                        "control_basis_pair_count": len(
                                            control_directions
                                        ),
                                        "control_basis_pair_ids": (
                                            control_basis_pair_ids
                                        ),
                                        "hard_control_pair_id": hard_control_pair_id,
                                        "scoring_surface": scoring_surface,
                                        "prompt_frame": prompt_frame,
                                        "objective_label_scoring_regime": (
                                            objective_label_scoring_regime
                                        ),
                                        "eval_label_scoring_regime": (
                                            eval_label_scoring_regime
                                        ),
                                        "label_score_normalization": (
                                            label_score_normalization
                                        ),
                                        "option_order": prompt_spec["option_order"],
                                        "prompt": prompt,
                                        "objective_labels_by_role": (
                                            objective_labels_by_role
                                        ),
                                        "eval_labels_by_role": eval_labels_by_role,
                                        "generation_match_labels_by_role": (
                                            generation_labels
                                        ),
                                        "binary_control_labels": prompt_spec.get(
                                            "binary_control_labels"
                                        ),
                                        "train_variant_indices": sorted(
                                            train_variants
                                        ),
                                        "holdout_variant_index": (
                                            holdout_variant_index
                                        ),
                                        "norms": norms,
                                        "activation_norms": activation_norms,
                                        "activation_prompt_frame": (
                                            activation_prompt_frame
                                        ),
                                        "readout_training_counts": (
                                            readout_training_counts
                                        ),
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
        if scoring_surface == "binary_relation":
            for objective_label_scoring_regime in objective_label_scoring_regimes:
                regime_records = [
                    learned_records[(pair_id(str(pair["left"]), str(pair["right"])), objective_label_scoring_regime)]
                    for pair in pair_specs
                ]
                target_vectors = [
                    (
                        f"{record['pair_index']}:{record['left']}->{record['right']}:target",
                        record["learned_directions"]["target"],
                    )
                    for record in regime_records
                ]
                control_vectors = [
                    (
                        (
                            f"{record['pair_index']}:{record['left']}->{record['right']}:"
                            f"{control_name}"
                        ),
                        control_direction,
                    )
                    for record in regime_records
                    for control_name, control_direction in (
                        record["binary_control_directions"].items()
                    )
                ]
                always_false_vectors = [
                    (
                        (
                            f"{record['pair_index']}:{record['left']}->{record['right']}:"
                            "always_false"
                        ),
                        record["binary_control_directions"]["always_false"],
                    )
                    for record in regime_records
                    if "always_false" in record["binary_control_directions"]
                ]
                binary_gradient_geometry.append(
                    {
                        "role": role,
                        "layer": layer,
                        "objective_label_scoring_regime": (
                            objective_label_scoring_regime
                        ),
                        "target_directions": direction_geometry_summary(
                            torch=torch,
                            named_vectors=target_vectors,
                        ),
                        "control_directions": direction_geometry_summary(
                            torch=torch,
                            named_vectors=control_vectors,
                        ),
                        "target_plus_control_directions": (
                            direction_geometry_summary(
                                torch=torch,
                                named_vectors=target_vectors + control_vectors,
                            )
                        ),
                        "always_false_directions": direction_geometry_summary(
                            torch=torch,
                            named_vectors=always_false_vectors,
                        ),
                    }
                )
    return {
        "rows": rows,
        "binary_gradient_geometry": binary_gradient_geometry,
        "slot_token_ids": token_ids_by_slot,
    }


@app.function(
    image=IMAGE,
    timeout=3000,
    volumes={str(RESULTS_VOLUME_MOUNT): RESULTS_VOLUME},
)
def run_behavior_aligned_direction_raw_to_volume_remote(
    concepts: list[dict[str, Any]],
    records: list[dict[str, Any]],
    aliases_by_concept: dict[str, list[str]],
    pair_specs: list[dict[str, Any]],
    model_id: str,
    layer_roles: dict[str, int],
    scales: list[float],
    direction_modes: list[str],
    option_orders: list[list[str]],
    train_variant_indices: list[int],
    holdout_variant_index: int,
    max_length: int,
    scoring_surface: str,
    prompt_frame: str,
    objective_label_scoring_regimes: list[str],
    eval_label_scoring_regimes: list[str],
    label_score_normalization: str,
    seed: int,
    modal_volume_out: str,
) -> dict[str, Any]:
    requested_volume_out = modal_volume_out.strip()
    if not requested_volume_out:
        raise ValueError("modal_volume_out must be a non-empty relative path")
    relative_out = requested_volume_out.lstrip("/")
    if not relative_out or ".." in Path(relative_out).parts:
        raise ValueError(f"Unsafe modal_volume_out path: {modal_volume_out}")

    remote_payload = run_behavior_aligned_direction_remote.get_raw_f()(
        concepts,
        records,
        aliases_by_concept,
        pair_specs,
        model_id,
        layer_roles,
        scales,
        direction_modes,
        option_orders,
        train_variant_indices,
        holdout_variant_index,
        max_length,
        scoring_surface,
        prompt_frame,
        objective_label_scoring_regimes,
        eval_label_scoring_regimes,
        label_score_normalization,
        seed,
    )
    output_path = RESULTS_VOLUME_MOUNT / relative_out
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(remote_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    RESULTS_VOLUME.commit()
    return {
        "modal_volume": RESULTS_VOLUME_NAME,
        "modal_volume_out": relative_out,
        "row_count": len(remote_payload["rows"]),
        "binary_gradient_geometry_count": len(
            remote_payload.get("binary_gradient_geometry", [])
        ),
    }


@app.local_entrypoint()
def main(
    concepts: str = "experiments/concept_geometry/concept_set.json",
    paraphrases: str = "experiments/concept_geometry/concept_paraphrases.json",
    aliases: str = "experiments/concept_geometry/concept_aliases.json",
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
    scoring_surface: str = DEFAULT_SCORING_SURFACE,
    prompt_frame: str = DEFAULT_PROMPT_FRAME,
    objective_label_scoring_regimes: str = DEFAULT_OBJECTIVE_LABEL_SCORING_REGIMES,
    eval_label_scoring_regimes: str = DEFAULT_EVAL_LABEL_SCORING_REGIMES,
    label_score_normalization: str = DEFAULT_LABEL_SCORE_NORMALIZATION,
    pair_set: str = "promoted",
    seed: int = 20260608,
    out: str = "artifacts/activation_geometry/modal_behavior_aligned_direction.json",
    modal_volume_out: str = "",
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
        PROMPT_FRAMES,
        SCORING_SURFACES,
        aggregate_rows,
        alignment_summary,
        gate_summaries,
        label_scoring_regime_parts as public_label_scoring_regime_parts,
        parse_direction_modes,
        parse_label_scoring_regimes,
        parse_values,
        public_summary,
        write_payload,
    )
    from experiments.activation_geometry.final_token_steering_pilot import (
        pair_specs_for_set,
        parse_scales,
        serializable_pair_specs,
    )
    from experiments.activation_geometry.steering_calibration_diagnostic import (
        parse_option_orders,
    )

    concept_rows = load_concepts(Path(concepts))
    aliases_by_concept = load_aliases(Path(aliases))
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
    layer_roles = {"primary": primary_layer}
    if backup_layer >= 1:
        layer_roles["backup"] = backup_layer
    if control_layer >= 1:
        layer_roles["control"] = control_layer
    parsed_direction_modes = parse_direction_modes(direction_modes)
    parsed_option_orders = parse_option_orders(option_orders)
    parsed_train_variants = parse_layers(train_variants)
    parsed_scales = parse_scales(scales)
    parsed_scoring_surface = parse_values(
        scoring_surface,
        allowed=SCORING_SURFACES,
        name="Scoring surface",
    )[0]
    parsed_prompt_frame = parse_values(
        prompt_frame,
        allowed=PROMPT_FRAMES,
        name="Prompt frame",
    )[0]
    parsed_objective_label_scoring_regimes = parse_label_scoring_regimes(
        objective_label_scoring_regimes,
        name="Objective label scoring regimes",
        allow_groups=True,
    )
    parsed_eval_label_scoring_regimes = parse_label_scoring_regimes(
        eval_label_scoring_regimes,
        name="Eval label scoring regimes",
        allow_groups=False,
    )
    parsed_label_score_normalization = parse_values(
        label_score_normalization,
        allowed=("mean", "sum"),
        name="Label score normalization",
    )[0]
    if parsed_scoring_surface == "option_token" and (
        parsed_objective_label_scoring_regimes != ["canonical"]
        or parsed_eval_label_scoring_regimes != ["canonical"]
    ):
        raise ValueError("Alias label regimes require full-label scoring")
    parsed_label_regime_parts = [
        part
        for regime in (
            parsed_objective_label_scoring_regimes
            + parsed_eval_label_scoring_regimes
        )
        for part in public_label_scoring_regime_parts(regime, allow_groups=True)
    ]
    if any(part == "alias" or part.startswith("alias_") for part in parsed_label_regime_parts):
        missing_aliases = sorted(
            concept.id for concept in concept_rows if concept.id not in aliases_by_concept
        )
        if missing_aliases:
            raise ValueError(f"Missing aliases for concepts: {missing_aliases}")
    pair_specs = pair_specs_for_set(concept_rows, pair_set=pair_set)
    if modal_volume_out.strip():
        function_call = run_behavior_aligned_direction_raw_to_volume_remote.spawn(
            [concept.__dict__ for concept in concept_rows],
            serializable_records,
            aliases_by_concept,
            serializable_pair_specs(pair_specs),
            model_id,
            layer_roles,
            parsed_scales,
            parsed_direction_modes,
            [list(order) for order in parsed_option_orders],
            parsed_train_variants,
            holdout_variant,
            max_length,
            parsed_scoring_surface,
            parsed_prompt_frame,
            parsed_objective_label_scoring_regimes,
            parsed_eval_label_scoring_regimes,
            parsed_label_score_normalization,
            seed,
            modal_volume_out,
        )
        print(
            json.dumps(
                {
                    "modal_volume": RESULTS_VOLUME_NAME,
                    "modal_volume_out": modal_volume_out.strip().lstrip("/"),
                    "function_call_id": function_call.object_id,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    remote_payload = run_behavior_aligned_direction_remote.remote(
        [concept.__dict__ for concept in concept_rows],
        serializable_records,
        aliases_by_concept,
        serializable_pair_specs(pair_specs),
        model_id,
        layer_roles,
        parsed_scales,
        parsed_direction_modes,
        [list(order) for order in parsed_option_orders],
        parsed_train_variants,
        holdout_variant,
        max_length,
        parsed_scoring_surface,
        parsed_prompt_frame,
        parsed_objective_label_scoring_regimes,
        parsed_eval_label_scoring_regimes,
        parsed_label_score_normalization,
        seed,
    )
    aggregates = aggregate_rows(remote_payload["rows"])
    payload = {
        "manifest": {
            "model_id": model_id,
            "concept_source": concepts,
            "paraphrase_source": paraphrases,
            "alias_source": aliases,
            "pooling": "final-token",
            "layer_roles": layer_roles,
            "train_variant_indices": parsed_train_variants,
            "holdout_variant_index": holdout_variant,
            "scales": parsed_scales,
            "direction_modes": parsed_direction_modes,
            "scoring_surface": parsed_scoring_surface,
            "prompt_frame": parsed_prompt_frame,
            "objective_label_scoring_regimes": (
                parsed_objective_label_scoring_regimes
            ),
            "eval_label_scoring_regimes": parsed_eval_label_scoring_regimes,
            "label_score_normalization": parsed_label_score_normalization,
            "pair_set": pair_set,
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
        "binary_gradient_geometry": remote_payload.get("binary_gradient_geometry", []),
    }
    if out and out.lower() != "none":
        write_payload(Path(out), payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    print(
        "Run with: modal run experiments/activation_geometry/modal_behavior_aligned_direction.py",
        file=sys.stderr,
    )
