#!/usr/bin/env python3
"""Replication sweep for the passive→active geometry result.

Runs the same 3-phase probe across:

  - models ∈ {Pythia-70m-deduped, GPT-2 (124M)}
  - seeds  ∈ {20260610, 1729, 4242}

= 6 cells. For each cell, returns:
  - passive vs active cluster geometry
  - passive vs active causal interventions (ablate, wrong_dir, random_ablate)
  - the *paraphrase-specific* effect (paraphrase drop − random drop)
  - the passive→active ratio

Pre-registered acceptance gate:
  - ≥4 of 6 cells show ratio ≥3×
  - mean ratio across cells ≥4×
  - random-axis control stays approximately stable across phases (±0.3)

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/passive_to_active/modal_replication_sweep.py
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

app = modal.App(name="research-derived-p2a-replication")


@app.function(image=IMAGE, timeout=3600, cpu=8)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import os
    import random

    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import transformers

    model_id: str = arg["model_id"]
    paraphrases: list[dict[str, Any]] = arg["paraphrases"]
    sim_layer: int = arg["sim_layer"]
    max_length: int = arg["max_length"]
    ft_epochs: int = arg["ft_epochs"]
    ft_lr: float = arg["ft_lr"]
    intervention_max_norm: float = arg["intervention_max_norm"]
    n_intervention_strengths: int = arg["n_intervention_strengths"]
    seed: int = arg["seed"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN") or None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def fresh_lm():
        m = transformers.AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=torch.float32, token=token,
        )
        m.to(device); return m

    flat = []
    concepts = [e["id"] for e in paraphrases]
    label_idx_of = {c: i for i, c in enumerate(concepts)}
    for entry in paraphrases:
        for i, v in enumerate(entry["variants"]):
            flat.append((entry["id"], i, v, label_idx_of[entry["id"]]))
    n_concepts = len(concepts)
    n_examples = len(flat)
    texts = [t for _, _, t, _ in flat]
    labels = np.array([lbl for _, _, _, lbl in flat])

    def encode_batch(t):
        e = tokenizer(t, return_tensors="pt", truncation=True,
                     max_length=max_length, padding=True)
        return {k: v.to(device) for k, v in e.items()}

    def hidden_pool_eval(model, t):
        e = encode_batch(t)
        with torch.no_grad():
            o = model(**e, output_hidden_states=True)
        hs = o.hidden_states[sim_layer].float()
        attn = e.get("attention_mask")
        mask = (attn.float() if attn is not None else torch.ones_like(e["input_ids"]).float()).unsqueeze(-1)
        pooled = (hs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return pooled.cpu().numpy()

    def hidden_pool_grad(model, t):
        e = encode_batch(t)
        o = model(**e, output_hidden_states=True)
        hs = o.hidden_states[sim_layer].float()
        attn = e.get("attention_mask")
        mask = (attn.float() if attn is not None else torch.ones_like(e["input_ids"]).float()).unsqueeze(-1)
        return (hs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)

    # ----- Phase 1: passive measurement -----
    model = fresh_lm(); model.eval()
    pooled_passive = hidden_pool_eval(model, texts)
    mean_p = pooled_passive.mean(axis=0, keepdims=True)
    centered_p = pooled_passive - mean_p

    def cluster_metrics(centered, labels_):
        norms = np.linalg.norm(centered, axis=1, keepdims=True)
        unit = centered / np.clip(norms, 1e-9, None)
        sim = unit @ unit.T
        same = labels_[:, None] == labels_[None, :]
        diff = ~same
        np.fill_diagonal(same, False)
        return float(sim[same].mean()), float(sim[diff].mean())

    passive_same, passive_diff = cluster_metrics(centered_p, labels)

    def per_concept_dirs(centered, labels_):
        D = centered.shape[1]
        dirs = np.zeros((n_concepts, D), dtype=np.float32)
        for ci in range(n_concepts):
            m = labels_ == ci
            if m.any():
                dirs[ci] = centered[m].mean(axis=0)
        norms = np.linalg.norm(dirs, axis=1, keepdims=True)
        return dirs / np.clip(norms, 1e-9, None)

    para_unit_p = per_concept_dirs(centered_p, labels)
    rng_np = np.random.RandomState(seed)
    sh = labels.copy(); rng_np.shuffle(sh)
    rand_unit_p = per_concept_dirs(centered_p, sh)

    def fit_linear(features, labels_arr):
        head = nn.Linear(features.shape[1], n_concepts).to(device)
        f = torch.from_numpy(features).float().to(device)
        l = torch.from_numpy(labels_arr).long().to(device)
        opt = torch.optim.Adam(head.parameters(), lr=1e-2, weight_decay=1e-3)
        for _ in range(400):
            opt.zero_grad()
            loss = F.cross_entropy(head(f), l)
            loss.backward(); opt.step()
        with torch.no_grad():
            acc = (head(f).argmax(-1) == l).float().mean().item()
        return head, float(acc)

    head_p, acc_p = fit_linear(pooled_passive, labels)
    strengths = [intervention_max_norm * (i + 1) / n_intervention_strengths
                 for i in range(n_intervention_strengths)]

    def intervention(features, head_module, unit_per_concept, mode):
        f = torch.from_numpy(features).float().to(device)
        l = torch.from_numpy(labels).long().to(device)
        with torch.no_grad():
            base_acc = (head_module(f).argmax(-1) == l).float().mean().item()
        dir_per = unit_per_concept[labels]
        d = torch.from_numpy(dir_per).float().to(device)
        if mode == "wrong_dir":
            rng_local = np.random.RandomState(seed + 7)
            wrong_idx = np.array([
                rng_local.choice([c for c in range(n_concepts) if c != lbl])
                for lbl in labels
            ])
            d = torch.from_numpy(unit_per_concept[wrong_idx]).float().to(device)

        drops = []
        for alpha in strengths:
            if mode == "ablate":
                proj = (f * d).sum(dim=-1, keepdim=True) * d
                perturbed = f - alpha * proj
            else:
                perturbed = f + alpha * d
            with torch.no_grad():
                acc = (head_module(perturbed).argmax(-1) == l).float().mean().item()
            drops.append(float(base_acc - acc))
        return float(base_acc), drops

    passive_base, passive_para_ablate = intervention(pooled_passive, head_p, para_unit_p, "ablate")
    _, passive_para_wrong = intervention(pooled_passive, head_p, para_unit_p, "wrong_dir")
    _, passive_rand_ablate = intervention(pooled_passive, head_p, rand_unit_p, "ablate")

    # ----- Phase 2: active fine-tune -----
    model = fresh_lm(); model.train()
    classifier = nn.Linear(model.config.hidden_size, n_concepts).to(device)
    opt = torch.optim.AdamW(list(model.parameters()) + list(classifier.parameters()),
                            lr=ft_lr, weight_decay=1e-4)
    label_t = torch.tensor([lbl for _, _, _, lbl in flat], dtype=torch.long, device=device)
    ft_train_acc = 0.0
    for _ in range(ft_epochs):
        order = list(range(n_examples)); random.shuffle(order)
        bs = 24
        epoch_correct = 0
        for s in range(0, n_examples, bs):
            b = order[s:s + bs]
            opt.zero_grad()
            pooled = hidden_pool_grad(model, [texts[i] for i in b])
            logits = classifier(pooled)
            loss = F.cross_entropy(logits, label_t[b])
            loss.backward(); opt.step()
            epoch_correct += int((logits.argmax(-1) == label_t[b]).sum().item())
        ft_train_acc = epoch_correct / n_examples

    # ----- Phase 3: active measure -----
    model.eval()
    pooled_active = hidden_pool_eval(model, texts)
    mean_a = pooled_active.mean(axis=0, keepdims=True)
    centered_a = pooled_active - mean_a
    active_same, active_diff = cluster_metrics(centered_a, labels)

    para_unit_a = per_concept_dirs(centered_a, labels)
    rng_np2 = np.random.RandomState(seed + 1)
    sh2 = labels.copy(); rng_np2.shuffle(sh2)
    rand_unit_a = per_concept_dirs(centered_a, sh2)

    active_base, active_para_ablate = intervention(pooled_active, classifier, para_unit_a, "ablate")
    _, active_para_wrong = intervention(pooled_active, classifier, para_unit_a, "wrong_dir")
    _, active_rand_ablate = intervention(pooled_active, classifier, rand_unit_a, "ablate")

    return {
        "model_id": model_id,
        "seed": seed,
        "sim_layer": sim_layer,
        "passive": {
            "cluster_same": passive_same,
            "cluster_diff": passive_diff,
            "cluster_gap": passive_same - passive_diff,
            "linear_readout_acc": acc_p,
            "max_para_ablate": max(passive_para_ablate),
            "max_para_wrong": max(passive_para_wrong),
            "max_rand_ablate": max(passive_rand_ablate),
            "specific_at_max": max(passive_para_ablate) - max(passive_rand_ablate),
            "para_ablate_curve": passive_para_ablate,
            "para_wrong_curve": passive_para_wrong,
            "rand_ablate_curve": passive_rand_ablate,
        },
        "active": {
            "cluster_same": active_same,
            "cluster_diff": active_diff,
            "cluster_gap": active_same - active_diff,
            "ft_train_acc": float(ft_train_acc),
            "max_para_ablate": max(active_para_ablate),
            "max_para_wrong": max(active_para_wrong),
            "max_rand_ablate": max(active_rand_ablate),
            "specific_at_max": max(active_para_ablate) - max(active_rand_ablate),
            "para_ablate_curve": active_para_ablate,
            "para_wrong_curve": active_para_wrong,
            "rand_ablate_curve": active_rand_ablate,
        },
        "strengths": strengths,
    }


MODEL_CONFIGS = [
    ("EleutherAI/pythia-70m-deduped", 5),  # (model_id, sim_layer)
    ("openai-community/gpt2", 6),
]


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    paraphrases_path: str = "experiments/concept_geometry/concept_paraphrases.json",
    max_length: int = 96,
    ft_epochs: int = 60,
    ft_lr: float = 5e-4,
    n_intervention_strengths: int = 10,
    intervention_max_norm: float = 5.0,
    out: str = "artifacts/passive_to_active/replication_v1.json",
) -> None:
    paraphrases = json.loads(Path(paraphrases_path).read_text())
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]

    cell_args = []
    for model_id, sim_layer in MODEL_CONFIGS:
        for sd in seed_list:
            cell_args.append(dict(
                model_id=model_id,
                paraphrases=paraphrases,
                sim_layer=sim_layer,
                max_length=max_length,
                ft_epochs=ft_epochs,
                ft_lr=ft_lr,
                n_intervention_strengths=n_intervention_strengths,
                intervention_max_norm=intervention_max_norm,
                seed=sd,
            ))

    results = list(run_cell.map(cell_args))

    # Summarize
    cell_rows = []
    for r in results:
        p, a = r["passive"], r["active"]
        ratio = (a["specific_at_max"] / max(1e-6, p["specific_at_max"]))
        cell_rows.append(dict(
            model_id=r["model_id"], seed=r["seed"],
            passive_specific=p["specific_at_max"],
            active_specific=a["specific_at_max"],
            ratio=ratio,
            passive_para_ablate=p["max_para_ablate"],
            active_para_ablate=a["max_para_ablate"],
            passive_para_wrong=p["max_para_wrong"],
            active_para_wrong=a["max_para_wrong"],
            passive_rand_ablate=p["max_rand_ablate"],
            active_rand_ablate=a["max_rand_ablate"],
            passive_cluster_gap=p["cluster_gap"],
            active_cluster_gap=a["cluster_gap"],
        ))

    n_cells = len(cell_rows)
    n_meeting_3x = sum(1 for r in cell_rows if r["ratio"] >= 3.0)
    mean_ratio = sum(r["ratio"] for r in cell_rows) / max(1, n_cells)
    mean_passive_specific = sum(r["passive_specific"] for r in cell_rows) / max(1, n_cells)
    mean_active_specific = sum(r["active_specific"] for r in cell_rows) / max(1, n_cells)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "manifest": {
            "seeds": seed_list,
            "models": [m[0] for m in MODEL_CONFIGS],
            "ft_epochs": ft_epochs,
            "ft_lr": ft_lr,
            "intervention_max_norm": intervention_max_norm,
            "n_intervention_strengths": n_intervention_strengths,
        },
        "summary": {
            "n_cells": n_cells,
            "n_meeting_3x_gate": n_meeting_3x,
            "mean_ratio": mean_ratio,
            "mean_passive_specific": mean_passive_specific,
            "mean_active_specific": mean_active_specific,
        },
        "cells": cell_rows,
        "raw_results": results,
    }, indent=2, sort_keys=True))

    print(f"\nReplication sweep: {n_cells} cells")
    print(f"  n_meeting_3x_gate    : {n_meeting_3x}/{n_cells}")
    print(f"  mean ratio (active/passive specific) : {mean_ratio:.2f}x")
    print(f"  mean passive specific : {mean_passive_specific:+.4f}")
    print(f"  mean active specific  : {mean_active_specific:+.4f}")
    print(f"\nPer-cell breakdown:")
    print(f"{'model':<35} {'seed':>10} | {'p_spec':>8} {'a_spec':>8} {'ratio':>7}")
    for r in cell_rows:
        m = r['model_id'].split('/')[-1]
        print(f"  {m:<33} {r['seed']:>10} | {r['passive_specific']:>+.4f} {r['active_specific']:>+.4f} {r['ratio']:>6.2f}x")
