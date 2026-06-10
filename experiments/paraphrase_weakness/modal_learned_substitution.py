#!/usr/bin/env python3
"""Learn the meaning-preserving substitution group from paraphrase data.

Translates the rotation-group discovery procedure to language:

- Domain: 24 concepts × 3 paraphrase variants from concept_paraphrases.json.
- Candidate transformations: word substitutions (w_a → w_b) for word pairs
  that appear in the paraphrase corpus. The candidate set is enumerated
  from the observed substitution-pairs across paraphrase variants of the
  same concept (positive support).
- Score per substitution: average across all training sentences of
  similarity (using Pythia-70M centered hidden state at a chosen layer)
  between the substituted sentence and the closest variant of the SAME
  concept.
- Keep substitutions with score >= threshold. That set is the learned
  substitution group.
- Evaluate: behavioral consistency under the learned group (next-token
  agreement after applying each learned substitution) vs. random
  substitutions (control).

This is the language-domain analog of `infer_rotation_group_from_training`.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
    "numpy>=1.26,<2.0",
)

app = modal.App(name="research-derived-learned-substitution")


@app.function(image=IMAGE, timeout=1800, cpu=4)
def run_probe(arg: dict[str, Any]) -> dict[str, Any]:
    import os

    import numpy as np
    import torch
    import transformers

    model_id: str = arg["model_id"]
    paraphrases: list[dict[str, Any]] = arg["paraphrases"]
    max_length: int = arg.get("max_length", 96)
    sim_layer: int = arg.get("sim_layer", 5)
    threshold: float = arg.get("threshold", 0.3)

    token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN") or None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id, torch_dtype=torch.float32, token=token, output_hidden_states=True
    )
    model.to(device)
    model.eval()

    def encode(text: str) -> dict[str, Any]:
        enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
        return {k: v.to(device) for k, v in enc.items()}

    def hidden_state(text: str, layer: int) -> np.ndarray:
        enc = encode(text)
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True)
        hs = out.hidden_states[layer].float()  # [1, T, D]
        attn = enc.get("attention_mask")
        mask = (attn.float() if attn is not None else torch.ones_like(enc["input_ids"]).float()).unsqueeze(-1)
        pooled = (hs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return pooled.squeeze(0).cpu().numpy()

    def next_token_argmax(text: str) -> int:
        enc = encode(text)
        with torch.no_grad():
            out = model(**enc)
        logits = out.logits.float().cpu().numpy()[0]
        attn_mask = enc.get("attention_mask")
        last_idx = int(attn_mask.sum().item()) - 1 if attn_mask is not None else logits.shape[0] - 1
        return int(np.argmax(logits[last_idx]))

    # --- collect texts and hidden states ---
    texts: dict[tuple[str, int], str] = {}
    states: dict[tuple[str, int], np.ndarray] = {}
    for entry in paraphrases:
        for i, v in enumerate(entry["variants"]):
            texts[(entry["id"], i)] = v
            states[(entry["id"], i)] = hidden_state(v, sim_layer)

    # --- center the embedding space (All-but-the-Top) ---
    all_states = np.stack(list(states.values()), axis=0)
    mean_vec = all_states.mean(axis=0)
    centered_states = {k: v - mean_vec for k, v in states.items()}

    def cos(a: np.ndarray, b: np.ndarray) -> float:
        na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        return 0.0 if na == 0 or nb == 0 else float(np.dot(a, b) / (na * nb))

    # --- enumerate candidate substitutions from variant word-deltas ---
    # For each pair of variants of the same concept, the set of
    # words that appear in only one of them is a candidate substitution
    # source/target. We extract one-word substitutions of the form
    # "word_a → word_b" where word_a appears in variant i and word_b in
    # variant j of the same concept.
    candidates: list[tuple[str, str]] = []
    candidate_set: set[tuple[str, str]] = set()
    for entry in paraphrases:
        variants = entry["variants"]
        for i in range(len(variants)):
            for j in range(len(variants)):
                if i == j:
                    continue
                ws_i = set(variants[i].lower().split())
                ws_j = set(variants[j].lower().split())
                only_i = list(ws_i - ws_j)
                only_j = list(ws_j - ws_i)
                # Single-word substitutions: pair every only_i with only_j.
                for wa in only_i:
                    for wb in only_j:
                        if (wa, wb) not in candidate_set and wa != wb:
                            candidate_set.add((wa, wb))
                            candidates.append((wa, wb))

    # --- score each candidate substitution on the FULL paraphrase set ---
    def apply_sub(text: str, wa: str, wb: str) -> str:
        toks = text.split()
        out = [wb if t.lower() == wa else t for t in toks]
        return " ".join(out)

    sub_scores: list[tuple[tuple[str, str], float]] = []
    for wa, wb in candidates:
        per_sentence_scores: list[float] = []
        for (cid, idx), text in texts.items():
            sub_text = apply_sub(text, wa, wb)
            if sub_text == text:
                continue
            sub_state = hidden_state(sub_text, sim_layer) - mean_vec
            same_concept_states = [
                centered_states[(cid, k)] for k in range(len(text.split())) if (cid, k) in centered_states and k != idx
            ]
            same_concept_states = [
                centered_states[(cid, k)] for k in range(3) if (cid, k) in centered_states and k != idx
            ]
            if not same_concept_states:
                continue
            best = max(cos(sub_state, s) for s in same_concept_states)
            per_sentence_scores.append(best)
        if per_sentence_scores:
            sub_scores.append(((wa, wb), float(np.mean(per_sentence_scores))))

    sub_scores.sort(key=lambda r: -r[1])
    learned_subs = [
        {"from": wa, "to": wb, "score": s}
        for (wa, wb), s in sub_scores if s >= threshold
    ]

    # --- behavioral consistency under learned substitutions ---
    # For each concept c with multiple variants, pick variant 0 as base.
    # Apply each learned substitution that is applicable (wa is in base).
    # Score: fraction of (base, substituted) pairs whose next-token argmax
    # agrees.
    behavior_learned_agree = 0
    behavior_learned_total = 0
    for entry in paraphrases:
        if not entry["variants"]:
            continue
        base = entry["variants"][0]
        base_argmax = next_token_argmax(base)
        for sub in learned_subs:
            wa, wb = sub["from"], sub["to"]
            new = apply_sub(base, wa, wb)
            if new == base:
                continue
            new_argmax = next_token_argmax(new)
            behavior_learned_total += 1
            behavior_learned_agree += int(new_argmax == base_argmax)

    # Random-substitution control: same size, random word pairs from
    # the candidate set.
    rng = np.random.RandomState(0)
    target_size = max(1, len(learned_subs))
    if len(candidates) > target_size:
        idx = rng.choice(len(candidates), size=target_size, replace=False)
        random_subs = [candidates[i] for i in idx]
    else:
        random_subs = candidates

    behavior_random_agree = 0
    behavior_random_total = 0
    for entry in paraphrases:
        if not entry["variants"]:
            continue
        base = entry["variants"][0]
        base_argmax = next_token_argmax(base)
        for wa, wb in random_subs:
            new = apply_sub(base, wa, wb)
            if new == base:
                continue
            new_argmax = next_token_argmax(new)
            behavior_random_total += 1
            behavior_random_agree += int(new_argmax == base_argmax)

    return {
        "model_id": model_id,
        "n_candidates": len(candidates),
        "learned_substitution_size": len(learned_subs),
        "top_learned": learned_subs[:20],
        "behavior_learned_invariance": (
            behavior_learned_agree / max(1, behavior_learned_total)
        ),
        "behavior_random_invariance": (
            behavior_random_agree / max(1, behavior_random_total)
        ),
        "n_learned_evals": behavior_learned_total,
        "n_random_evals": behavior_random_total,
    }


@app.local_entrypoint()
def main(
    model_id: str = "EleutherAI/pythia-70m-deduped",
    paraphrases_path: str = "experiments/concept_geometry/concept_paraphrases.json",
    out: str = "artifacts/paraphrase_weakness/learned_substitution_v1.json",
    sim_layer: int = 5,
    threshold: float = 0.3,
) -> None:
    paraphrases = json.loads(Path(paraphrases_path).read_text())
    result = run_probe.remote(dict(
        model_id=model_id,
        paraphrases=paraphrases,
        max_length=96,
        sim_layer=sim_layer,
        threshold=threshold,
    ))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(
        f"Wrote {out_path}: model={result['model_id']} "
        f"n_candidates={result['n_candidates']} "
        f"learned_sub_size={result['learned_substitution_size']} "
        f"learned_behavior={result['behavior_learned_invariance']:.4f} "
        f"random_behavior={result['behavior_random_invariance']:.4f}"
    )
