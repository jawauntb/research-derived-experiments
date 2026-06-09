#!/usr/bin/env python3
"""Modal entrypoint for the paraphrase-weakness probe.

For each concept in `experiments/concept_geometry/concept_paraphrases.json`,
we extract the per-layer hidden state of each paraphrase variant from a
small open-source language model (Pythia-70M or GPT-2). We then compute,
per concept and per layer:

- *paraphrase weakness* (analogous to symmetry weakness in the symbolic
  benchmark): mean pairwise cosine similarity between hidden states of
  the same concept's variants.
- *control weakness*: mean pairwise cosine similarity between hidden
  states of variants drawn from *different* concepts (a wrong-orbit
  control).
- *behavioral consistency*: agreement of next-token argmax predictions
  across the three variants of one concept.

The headline question is whether per-concept layer-level weakness
predicts per-concept behavioral consistency, mirroring the symbolic
benchmark's question of whether learned-function weakness predicts OOD
generalization.

Run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/paraphrase_weakness/modal_paraphrase_probe.py \\
        --model-id EleutherAI/pythia-70m-deduped \\
        --out artifacts/paraphrase_weakness/pythia_70m.json
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

app = modal.App(name="research-derived-paraphrase-weakness")


@app.function(image=IMAGE, timeout=1800, gpu=None)
def run_probe(arg: dict[str, Any]) -> dict[str, Any]:
    import math
    import os

    import numpy as np
    import torch
    import transformers

    model_id: str = arg["model_id"]
    paraphrases: list[dict[str, Any]] = arg["paraphrases"]
    max_length: int = arg.get("max_length", 96)

    token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN") or None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        token=token,
        output_hidden_states=True,
    )
    model.to(device)
    model.eval()

    # Build a flat list of (concept_id, variant_index, text) entries.
    flat: list[tuple[str, int, str]] = []
    for entry in paraphrases:
        for i, v in enumerate(entry["variants"]):
            flat.append((entry["id"], i, v))

    # Encode all texts and gather per-layer mean-pooled hidden states.
    # We process one at a time for simplicity at this small scale.
    n_layers: int | None = None
    states_by_concept_variant: dict[tuple[str, int], list[np.ndarray]] = {}
    next_token_logits_by_concept_variant: dict[tuple[str, int], np.ndarray] = {}

    for concept_id, variant_idx, text in flat:
        enc = tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)
        input_ids = enc["input_ids"].to(device)
        attn = enc.get("attention_mask")
        if attn is not None:
            attn = attn.to(device)
        with torch.no_grad():
            out = model(
                input_ids=input_ids,
                attention_mask=attn,
                output_hidden_states=True,
            )
        hs = out.hidden_states  # tuple of [1, T, D]
        if n_layers is None:
            n_layers = len(hs)
        # Mean pool across tokens (excluding padding via attention mask).
        mask = (attn.float() if attn is not None else torch.ones_like(input_ids).float()).unsqueeze(-1)
        per_layer_pooled = []
        for layer_state in hs:
            ls = layer_state.float()
            pooled = (ls * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            per_layer_pooled.append(pooled.squeeze(0).cpu().numpy())
        states_by_concept_variant[(concept_id, variant_idx)] = per_layer_pooled

        # Final-token logits, used for behavioral consistency.
        logits = out.logits.float().cpu().numpy()[0]
        last_idx = int(attn.sum().item()) - 1 if attn is not None else logits.shape[0] - 1
        next_token_logits_by_concept_variant[(concept_id, variant_idx)] = logits[last_idx]

    assert n_layers is not None

    def cos(a: np.ndarray, b: np.ndarray) -> float:
        na = float(np.linalg.norm(a))
        nb = float(np.linalg.norm(b))
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    # Per-concept, per-layer paraphrase weakness =
    # mean pairwise cosine of variants of the same concept.
    concepts = [e["id"] for e in paraphrases]
    n_variants = {e["id"]: len(e["variants"]) for e in paraphrases}

    # Build per-layer centered (anisotropy-corrected) hidden states.
    # LLM cosine similarities are dominated by an isotropic "common direction"
    # (Mu & Viswanath 2018, "All-but-the-Top"); subtracting the per-layer
    # mean recovers a cleaner concept-vs-control signal.
    centered_states: dict[tuple[str, int], list[np.ndarray]] = {}
    per_layer_mean: list[np.ndarray] = []
    for layer in range(n_layers):
        stack = np.stack(
            [states_by_concept_variant[k][layer] for k in states_by_concept_variant],
            axis=0,
        )
        mean = stack.mean(axis=0)
        per_layer_mean.append(mean)
    for k, layers_list in states_by_concept_variant.items():
        centered_states[k] = [
            layers_list[layer] - per_layer_mean[layer]
            for layer in range(n_layers)
        ]

    weakness_per_concept_layer: dict[str, list[float]] = {c: [] for c in concepts}
    control_per_concept_layer: dict[str, list[float]] = {c: [] for c in concepts}
    weakness_centered_per_concept_layer: dict[str, list[float]] = {c: [] for c in concepts}
    control_centered_per_concept_layer: dict[str, list[float]] = {c: [] for c in concepts}

    rng = np.random.RandomState(0)
    for layer in range(n_layers):
        for c in concepts:
            pairs: list[tuple[int, int]] = []
            for i in range(n_variants[c]):
                for j in range(i + 1, n_variants[c]):
                    pairs.append((i, j))
            if pairs:
                sims_raw = [
                    cos(
                        states_by_concept_variant[(c, i)][layer],
                        states_by_concept_variant[(c, j)][layer],
                    )
                    for i, j in pairs
                ]
                sims_cen = [
                    cos(
                        centered_states[(c, i)][layer],
                        centered_states[(c, j)][layer],
                    )
                    for i, j in pairs
                ]
                weakness_per_concept_layer[c].append(float(np.mean(sims_raw)))
                weakness_centered_per_concept_layer[c].append(float(np.mean(sims_cen)))
            else:
                weakness_per_concept_layer[c].append(0.0)
                weakness_centered_per_concept_layer[c].append(0.0)

            other_concepts = [oc for oc in concepts if oc != c]
            ctrl_raw = []
            ctrl_cen = []
            for _ in range(5):
                oc = rng.choice(other_concepts)
                ctrl_raw.append(
                    cos(
                        states_by_concept_variant[(c, 0)][layer],
                        states_by_concept_variant[(oc, 0)][layer],
                    )
                )
                ctrl_cen.append(
                    cos(
                        centered_states[(c, 0)][layer],
                        centered_states[(oc, 0)][layer],
                    )
                )
            control_per_concept_layer[c].append(float(np.mean(ctrl_raw)))
            control_centered_per_concept_layer[c].append(float(np.mean(ctrl_cen)))

    # Behavioral consistency: per concept, fraction of paraphrase pairs whose
    # next-token argmax predictions agree.
    behavior_per_concept: dict[str, float] = {}
    for c in concepts:
        n = n_variants[c]
        if n < 2:
            behavior_per_concept[c] = 1.0
            continue
        agree = 0
        total = 0
        for i in range(n):
            for j in range(i + 1, n):
                ai = int(np.argmax(next_token_logits_by_concept_variant[(c, i)]))
                aj = int(np.argmax(next_token_logits_by_concept_variant[(c, j)]))
                agree += int(ai == aj)
                total += 1
        behavior_per_concept[c] = agree / max(1, total)

    return {
        "model_id": model_id,
        "n_layers": n_layers,
        "concepts": concepts,
        "weakness_per_concept_layer": weakness_per_concept_layer,
        "control_per_concept_layer": control_per_concept_layer,
        "weakness_centered_per_concept_layer": weakness_centered_per_concept_layer,
        "control_centered_per_concept_layer": control_centered_per_concept_layer,
        "behavior_per_concept": behavior_per_concept,
        "device": str(device),
    }


@app.local_entrypoint()
def main(
    model_id: str = "EleutherAI/pythia-70m-deduped",
    paraphrases_path: str = "experiments/concept_geometry/concept_paraphrases.json",
    out: str = "artifacts/paraphrase_weakness/probe.json",
    max_length: int = 96,
) -> None:
    paraphrases = json.loads(Path(paraphrases_path).read_text())
    result = run_probe.remote(
        {
            "model_id": model_id,
            "paraphrases": paraphrases,
            "max_length": max_length,
        }
    )
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(
        f"Wrote {out_path}: model_id={result['model_id']} n_layers={result['n_layers']} "
        f"n_concepts={len(result['concepts'])}"
    )
