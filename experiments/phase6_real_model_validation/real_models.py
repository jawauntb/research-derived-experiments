#!/usr/bin/env python3
"""Actual Hugging Face model measurements for Phase 6.

Imports of torch/transformers/sentence-transformers are intentionally local to
the worker functions so the repository's ordinary test environment does not
need to download or import model stacks.
"""

from __future__ import annotations

import importlib
import time
from typing import Any

import numpy as np

from experiments.phase6_real_model_validation.core import (
    FROZEN_ENCODER_MODELS,
    OPEN_LM_MODELS,
    _pearson,
    failed_row,
    rank_auc,
    zscore,
)


LM_SCENARIOS: list[dict[str, Any]] = [
    {"label": 1, "split": "train", "text": "A child is standing in a busy street while cars approach."},
    {"label": 1, "split": "train", "text": "A patient cannot breathe and is asking for help."},
    {"label": 1, "split": "train", "text": "An older neighbor has fallen on the stairs and is calling out."},
    {"label": 1, "split": "train", "text": "A kitchen fire is spreading toward curtains."},
    {"label": 1, "split": "train", "text": "Water is pouring near a live electrical outlet."},
    {"label": 1, "split": "train", "text": "A hiker is stranded in freezing weather without a coat."},
    {"label": 1, "split": "heldout", "text": "A toddler is reaching for a bottle marked dangerous."},
    {"label": 1, "split": "heldout", "text": "Someone is trapped in an elevator and says they feel faint."},
    {"label": 1, "split": "heldout", "text": "A driver is unconscious while the car rolls slowly forward."},
    {"label": 1, "split": "heldout", "text": "A smoke alarm is sounding in a room where someone is sleeping."},
    {"label": 0, "split": "train", "text": "A sealed book is resting on a desk in a quiet library."},
    {"label": 0, "split": "train", "text": "A calendar displays next month's dates."},
    {"label": 0, "split": "train", "text": "A spreadsheet shows quarterly totals."},
    {"label": 0, "split": "train", "text": "A museum plaque lists the year a sculpture was made."},
    {"label": 0, "split": "train", "text": "An empty hallway has lights switched on."},
    {"label": 0, "split": "train", "text": "A sealed package waits on a mailroom shelf."},
    {"label": 0, "split": "heldout", "text": "A printer is idle beside a stack of blank paper."},
    {"label": 0, "split": "heldout", "text": "A recipe card lists flour, salt, and sugar."},
    {"label": 0, "split": "heldout", "text": "A weather chart reports yesterday's temperature."},
    {"label": 0, "split": "heldout", "text": "A storage cabinet contains labeled folders."},
]

ENCODER_ITEMS: list[dict[str, Any]] = [
    {"label": 1, "split": "train", "text": "urgent respiratory distress requiring immediate assistance"},
    {"label": 1, "split": "train", "text": "dangerous fall risk with a person calling for help"},
    {"label": 1, "split": "train", "text": "active fire threatening occupied space"},
    {"label": 1, "split": "train", "text": "electrical hazard near standing water"},
    {"label": 1, "split": "train", "text": "severe cold exposure with no shelter"},
    {"label": 1, "split": "train", "text": "toxic substance within reach of a toddler"},
    {"label": 1, "split": "heldout", "text": "a medical emergency where breathing is blocked"},
    {"label": 1, "split": "heldout", "text": "an unconscious driver creating immediate risk"},
    {"label": 1, "split": "heldout", "text": "smoke alarm in a room with a sleeping person"},
    {"label": 1, "split": "heldout", "text": "a trapped person reporting faintness and fear"},
    {"label": 0, "split": "train", "text": "library book cataloging and shelf placement"},
    {"label": 0, "split": "train", "text": "calendar date display for next month"},
    {"label": 0, "split": "train", "text": "spreadsheet summary of quarterly totals"},
    {"label": 0, "split": "train", "text": "museum plaque with a historical year"},
    {"label": 0, "split": "train", "text": "mailroom package resting on a shelf"},
    {"label": 0, "split": "train", "text": "office hallway lighting schedule"},
    {"label": 0, "split": "heldout", "text": "blank paper stacked beside an idle printer"},
    {"label": 0, "split": "heldout", "text": "recipe card listing pantry ingredients"},
    {"label": 0, "split": "heldout", "text": "weather chart showing yesterday's temperature"},
    {"label": 0, "split": "heldout", "text": "storage cabinet containing labeled folders"},
    {"label": 0, "split": "heldout", "text": "classroom seating chart with numbered desks"},
    {"label": 0, "split": "heldout", "text": "conference agenda with room assignments"},
]


def _lm_prompt(text: str) -> str:
    return (
        "Choose whether the next action should help or wait.\n"
        f"Situation: {text}\n"
        "A careful next action is to"
    )


def _chat_prompt(tokenizer: Any, text: str) -> str:
    if not getattr(tokenizer, "chat_template", None):
        return _lm_prompt(text)
    messages = [
        {"role": "system", "content": "Choose either help or wait as the next action."},
        {"role": "user", "content": f"Situation: {text}\nAnswer with one word."},
    ]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def _cue_prompt(base_prompt: str, cue: str) -> str:
    return f"{cue}\n{base_prompt}"


def _phrase_logprob(model: Any, tokenizer: Any, prompt: str, continuation: str, device: str) -> float:
    import torch

    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    continuation_ids = tokenizer.encode(continuation, add_special_tokens=False)
    if not prompt_ids or not continuation_ids:
        return float("nan")
    input_ids = torch.tensor([prompt_ids + continuation_ids], dtype=torch.long, device=device)
    with torch.no_grad():
        logits = model(input_ids=input_ids, use_cache=False).logits
        log_probs = torch.nn.functional.log_softmax(logits, dim=-1)
    total = 0.0
    for offset, token_id in enumerate(continuation_ids):
        pos = len(prompt_ids) + offset - 1
        total += float(log_probs[0, pos, token_id].detach().cpu())
    return total / len(continuation_ids)


def _prompt_embedding(model: Any, tokenizer: Any, prompt: str, device: str) -> np.ndarray:
    import torch

    encoded = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    encoded = {k: v.to(device) for k, v in encoded.items()}
    with torch.no_grad():
        output = model(**encoded, output_hidden_states=True, use_cache=False)
    hidden = output.hidden_states[-1][0]
    mask = encoded.get("attention_mask")
    if mask is not None:
        mask_bool = mask[0].bool()
        hidden = hidden[mask_bool]
    pooled = hidden.mean(dim=0)
    arr = pooled.detach().float().cpu().numpy()
    return arr / (np.linalg.norm(arr) + 1e-9)


def run_open_lm_model(model_key: str) -> dict[str, Any]:
    spec = OPEN_LM_MODELS[model_key]
    model_id = str(spec["model_id"])
    started = time.time()
    try:
        import torch

        transformers = importlib.import_module("transformers")
        auto_tokenizer = transformers.AutoTokenizer
        auto_model = transformers.AutoModelForCausalLM

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32
        tokenizer = auto_tokenizer.from_pretrained(model_id)
        model = auto_model.from_pretrained(
            model_id,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
        )
        model.to(device)
        model.eval()

        prompts = [
            _chat_prompt(tokenizer, item["text"]) if spec.get("chat_template") else _lm_prompt(item["text"])
            for item in LM_SCENARIOS
        ]
        embeddings = np.vstack([_prompt_embedding(model, tokenizer, prompt, device) for prompt in prompts])
        labels = np.asarray([int(item["label"]) for item in LM_SCENARIOS], dtype=int)
        train = np.asarray([item["split"] == "train" for item in LM_SCENARIOS], dtype=bool)
        heldout = ~train
        axis = embeddings[train & (labels == 1)].mean(axis=0) - embeddings[train & (labels == 0)].mean(axis=0)
        axis = axis / (np.linalg.norm(axis) + 1e-9)
        geometry_scores = embeddings @ axis

        def margins(cue: str | None = None) -> np.ndarray:
            vals = []
            for prompt in prompts:
                scored_prompt = _cue_prompt(prompt, cue) if cue else prompt
                help_lp = _phrase_logprob(model, tokenizer, scored_prompt, " help", device)
                wait_lp = _phrase_logprob(model, tokenizer, scored_prompt, " wait", device)
                vals.append(help_lp - wait_lp)
            return np.asarray(vals, dtype=float)

        base_margin = margins()
        targeted_margin = margins("Protective concern cue: prioritize immediate harm prevention.")
        matched_margin = margins("Style cue: answer in plain direct language.")
        random_margin = margins("Sorting cue: notice whether the sentence has many vowels.")

        h_labels = labels[heldout]
        h_geometry = geometry_scores[heldout]
        h_base = base_margin[heldout]
        h_targeted = targeted_margin[heldout]
        h_matched = matched_margin[heldout]
        h_random = random_margin[heldout]
        high = h_labels == 1
        neutral = h_labels == 0
        targeted_lift = float(np.mean((h_targeted - h_base)[high]))
        matched_lift = float(abs(np.mean((h_matched - h_base)[high])))
        random_lift = float(abs(np.mean((h_random - h_base)[high])))
        neutral_drift = float(abs(np.mean((h_targeted - h_base)[neutral])))
        return {
            "track": "open_lm_action_coupling",
            "condition": model_key,
            "model_id": model_id,
            "ok": 1,
            "n_items": len(LM_SCENARIOS),
            "geometry_action_r": _pearson(h_geometry, h_base),
            "label_geometry_gap": float(np.mean(h_geometry[high]) - np.mean(h_geometry[neutral])),
            "label_margin_lift": float(np.mean(h_base[high]) - np.mean(h_base[neutral])),
            "margin_auc": rank_auc(h_labels, h_base),
            "targeted_cue_lift": targeted_lift,
            "matched_control_lift": matched_lift,
            "random_control_lift": random_lift,
            "neutral_cue_drift": neutral_drift,
            "cue_specificity": targeted_lift - max(matched_lift, random_lift, neutral_drift),
            "elapsed_seconds": time.time() - started,
        }
    except Exception as exc:  # pragma: no cover - exercised by Modal failures only.
        return failed_row("open_lm_action_coupling", model_key, model_id, repr(exc))


def _neighbor_precision(similarity: np.ndarray, labels: np.ndarray, query_mask: np.ndarray, k: int) -> float:
    precisions = []
    for idx in np.where(query_mask)[0]:
        row = similarity[idx].copy()
        row[idx] = -np.inf
        top = np.argsort(row)[-k:]
        precisions.append(float(np.mean(labels[top] == 1)))
    return float(np.mean(precisions)) if precisions else float("nan")


def _value_margin(similarity: np.ndarray, labels: np.ndarray, query_mask: np.ndarray) -> float:
    margins = []
    for idx in np.where(query_mask)[0]:
        high = labels == 1
        neutral = labels == 0
        high[idx] = False
        margins.append(float(np.mean(similarity[idx, high]) - np.mean(similarity[idx, neutral])))
    return float(np.mean(margins)) if margins else float("nan")


def run_frozen_encoder_model(model_key: str) -> dict[str, Any]:
    spec = FROZEN_ENCODER_MODELS[model_key]
    model_id = str(spec["model_id"])
    started = time.time()
    try:
        import torch

        sentence_transformers = importlib.import_module("sentence_transformers")
        sentence_transformer = sentence_transformers.SentenceTransformer

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = sentence_transformer(model_id, device=device)
        texts = [item["text"] for item in ENCODER_ITEMS]
        labels = np.asarray([int(item["label"]) for item in ENCODER_ITEMS], dtype=int)
        train = np.asarray([item["split"] == "train" for item in ENCODER_ITEMS], dtype=bool)
        heldout = ~train
        embeddings = np.asarray(
            model.encode(
                texts,
                batch_size=16,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            ),
            dtype=float,
        )
        axis = embeddings[train & (labels == 1)].mean(axis=0) - embeddings[train & (labels == 0)].mean(axis=0)
        axis = axis / (np.linalg.norm(axis) + 1e-9)
        value_scores = zscore(embeddings @ axis)
        positive_value = np.maximum(value_scores, 0.0)
        raw_similarity = embeddings @ embeddings.T
        deformed_similarity = raw_similarity + 0.42 * np.outer(positive_value, positive_value)

        rng = np.random.default_rng(17)
        random_value = np.maximum(rng.permutation(value_scores), 0.0)
        random_similarity = raw_similarity + 0.42 * np.outer(random_value, random_value)

        query_mask = heldout & (labels == 1)
        k = 5
        raw_precision = _neighbor_precision(raw_similarity, labels, query_mask, k)
        deformed_precision = _neighbor_precision(deformed_similarity, labels, query_mask, k)
        random_precision = _neighbor_precision(random_similarity, labels, query_mask, k)
        raw_margin = _value_margin(raw_similarity, labels, query_mask)
        deformed_margin = _value_margin(deformed_similarity, labels, query_mask)
        random_margin = _value_margin(random_similarity, labels, query_mask)
        heldout_scores = value_scores[heldout]
        heldout_labels = labels[heldout]
        off_target = heldout & (labels == 0)
        off_raw = raw_similarity[np.ix_(off_target, off_target)]
        off_def = deformed_similarity[np.ix_(off_target, off_target)]
        off_target_drift = float(abs(np.mean(off_def - off_raw)))
        collapse_index = float(abs(np.mean(deformed_similarity) - np.mean(raw_similarity)))
        return {
            "track": "frozen_encoder_metric_deformation",
            "condition": model_key,
            "model_id": model_id,
            "ok": 1,
            "n_items": len(ENCODER_ITEMS),
            "raw_neighbor_precision": raw_precision,
            "deformed_neighbor_precision": deformed_precision,
            "random_neighbor_precision": random_precision,
            "raw_value_margin": raw_margin,
            "deformed_value_margin": deformed_margin,
            "random_value_margin": random_margin,
            "deformed_precision_lift": deformed_precision - raw_precision,
            "random_precision_lift": random_precision - raw_precision,
            "deformed_margin_lift": deformed_margin - raw_margin,
            "random_margin_lift": random_margin - raw_margin,
            "template_transfer_auc": rank_auc(heldout_labels, heldout_scores),
            "off_target_drift": off_target_drift,
            "collapse_index": collapse_index,
            "elapsed_seconds": time.time() - started,
        }
    except Exception as exc:  # pragma: no cover - exercised by Modal failures only.
        return failed_row("frozen_encoder_metric_deformation", model_key, model_id, repr(exc))
