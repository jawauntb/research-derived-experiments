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
PENALTY_DIRECTION_MODES = {
    "target_penalty_hard_1_0": ("hard_control", 1.0),
    "target_penalty_hard_2_0": ("hard_control", 2.0),
    "target_penalty_control_mean_1_0": ("control_mean", 1.0),
    "target_penalty_controls_0_5": ("control_set", 0.5),
    "target_penalty_controls_1_0": ("control_set", 1.0),
    "target_penalty_controls_2_0": ("control_set", 2.0),
}
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


def objective_role_for_mode(mode: str) -> str:
    if mode in {
        "target_learned",
        "target_resid_sd",
        "target_resid_control",
        "target_resid_all",
        "caa_target_contrast",
        "caa_target_minus_source",
        "caa_target_minus_distractor",
    } or mode in PENALTY_DIRECTION_MODES:
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


def run_scoring_prompt(
    *,
    torch: Any,
    tokenizer: Any,
    model: Any,
    prompt: str,
    layer: int,
    delta: Any | None,
    max_length: int,
    scoring_surface: str,
    token_ids: dict[str, int] | None,
    labels_by_role: dict[str, str],
    generation_labels_by_role: dict[str, list[str]] | None,
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
    patch_indices = token_indices.to(delta.device).long()

    def hook(_module: Any, _inputs: tuple[Any, ...], output: Any) -> Any:
        hidden_states = output[0] if isinstance(output, tuple) else output
        adjusted = hidden_states.clone()
        batch_indices = torch.arange(adjusted.shape[0], device=adjusted.device)
        adjusted[batch_indices, patch_indices] = (
            adjusted[batch_indices, patch_indices]
            + delta.to(device=adjusted.device, dtype=adjusted.dtype)
        )
        if isinstance(output, tuple):
            return (adjusted, *output[1:])
        return adjusted

    return block.register_forward_hook(hook)


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
        if scoring_surface in {"full_label", "generation_match"}:
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
    control_target_direction: Any | None,
    control_target_directions: list[Any],
    hard_control_target_direction: Any | None,
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
                        if scoring_surface == "generation_match"
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
                norms = {
                    objective_role: float(torch.linalg.vector_norm(direction).item())
                    for objective_role, direction in learned_directions.items()
                }
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
                    "norms": norms,
                    "activation_norms": activation_norms,
                    "activation_prompt_frame": activation_prompt_frame,
                    "learned_alignment": learned_alignment,
                }

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
                norms = record["norms"]
                activation_norms = record["activation_norms"]
                activation_prompt_frame = str(record["activation_prompt_frame"])
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
                for eval_label_scoring_regime in eval_label_scoring_regimes:
                    eval_labels_by_role = labels_by_role_for_regime(
                        concept_lookup=concept_lookup,
                        aliases_by_concept=aliases_by_concept,
                        left=left,
                        right=right,
                        distractor=distractor,
                        label_scoring_regime=eval_label_scoring_regime,
                    )
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
                            }
                        )
                    elif scoring_surface == "generation_match":
                        prompt_specs.append(
                            {
                                "prompt": full_label_prompt(
                                    source_text=heldout_text,
                                    prompt_frame=prompt_frame,
                                ),
                                "option_order": "generation_match",
                                "token_ids": None,
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
                            layer=layer,
                            delta=None,
                            max_length=max_length,
                            scoring_surface=scoring_surface,
                            token_ids=prompt_spec["token_ids"],
                            labels_by_role=eval_labels_by_role,
                            generation_labels_by_role=generation_labels,
                            label_score_normalization=label_score_normalization,
                        )
                        for scale_index, scale in enumerate(scales):
                            for mode_index, mode in enumerate(direction_modes):
                                direction = direction_for_mode(
                                    torch=torch,
                                    learned_directions=learned_directions,
                                    activation_directions=activation_directions,
                                    control_target_direction=control_target_direction,
                                    control_target_directions=control_directions,
                                    hard_control_target_direction=(
                                        hard_control_target_direction
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
                                direction_norm = float(
                                    torch.linalg.vector_norm(direction).item()
                                )
                                delta = direction * float(scale)
                                steered_scores = run_scoring_prompt(
                                    torch=torch,
                                    tokenizer=tokenizer,
                                    model=model,
                                    prompt=prompt,
                                    layer=layer,
                                    delta=delta,
                                    max_length=max_length,
                                    scoring_surface=scoring_surface,
                                    token_ids=prompt_spec["token_ids"],
                                    labels_by_role=eval_labels_by_role,
                                    generation_labels_by_role=generation_labels,
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
    }
    if out and out.lower() != "none":
        write_payload(Path(out), payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    print(
        "Run with: modal run experiments/activation_geometry/modal_behavior_aligned_direction.py",
        file=sys.stderr,
    )
