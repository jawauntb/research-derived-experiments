#!/usr/bin/env python3
"""Modal entrypoint for the passive→active geometry experiment.

Runs three phases on Pythia-70M:

  Phase 1 (passive): pretrained model. Extract per-variant layer-5
    centered mean-pool hidden states. Compute paraphrase clustering and
    a causal-intervention effect (perturb along the paraphrase direction
    and measure behavior change on a held-out classification task).

  Phase 2 (active): add a linear classification head over the layer-5
    mean pool. Supervised fine-tune the encoder + head on the
    paraphrase-invariant concept-id task. All variants of each concept
    share a label.

  Phase 3 (active measure): re-extract layer-5 centered mean-pool
    hidden states from the *fine-tuned* model. Recompute clustering and
    causal intervention. Compare to Phase 1.

Falsifiable hypothesis: the *causal intervention effect* on the
paraphrase direction should grow substantially (≥ 3×) after fine-tuning;
random-direction interventions should not.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/passive_to_active/modal_passive_to_active.py
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

app = modal.App(name="research-derived-passive-to-active")


@app.function(image=IMAGE, timeout=3600, cpu=8, gpu=None)
def run_passive_to_active(arg: dict[str, Any]) -> dict[str, Any]:
    import os
    import math
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
    n_intervention_strengths: int = arg["n_intervention_strengths"]
    intervention_max_norm: float = arg["intervention_max_norm"]
    seed: int = arg["seed"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN") or None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    config = transformers.AutoConfig.from_pretrained(model_id, token=token)
    config.output_hidden_states = True

    def fresh_lm():
        m = transformers.AutoModelForCausalLM.from_pretrained(
            model_id, torch_dtype=torch.float32, token=token,
        )
        m.to(device)
        return m

    # --- build flat dataset ---
    flat: list[tuple[str, int, str, int]] = []  # (concept_id, variant_idx, text, label_idx)
    concepts = [e["id"] for e in paraphrases]
    label_idx_of = {c: i for i, c in enumerate(concepts)}
    for entry in paraphrases:
        for i, v in enumerate(entry["variants"]):
            flat.append((entry["id"], i, v, label_idx_of[entry["id"]]))
    n_concepts = len(concepts)
    n_examples = len(flat)

    def encode_batch(texts):
        enc = tokenizer(
            texts, return_tensors="pt", truncation=True,
            max_length=max_length, padding=True,
        )
        return {k: v.to(device) for k, v in enc.items()}

    def hidden_pool(model, texts):
        enc = encode_batch(texts)
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True)
        hs = out.hidden_states[sim_layer].float()
        attn = enc.get("attention_mask")
        mask = (attn.float() if attn is not None else torch.ones_like(enc["input_ids"]).float()).unsqueeze(-1)
        pooled = (hs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return pooled.cpu().numpy()

    def hidden_pool_with_grad(model, texts):
        """Same as hidden_pool but with grad enabled for fine-tuning."""
        enc = encode_batch(texts)
        out = model(**enc, output_hidden_states=True)
        hs = out.hidden_states[sim_layer].float()
        attn = enc.get("attention_mask")
        mask = (attn.float() if attn is not None else torch.ones_like(enc["input_ids"]).float()).unsqueeze(-1)
        pooled = (hs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return pooled

    # --- Phase 1: passive measurement ---
    model = fresh_lm()
    model.eval()
    texts = [t for _, _, t, _ in flat]
    labels = np.array([lbl for _, _, _, lbl in flat])

    pooled_passive = hidden_pool(model, texts)  # [N, D]
    mean_vec_passive = pooled_passive.mean(axis=0, keepdims=True)
    centered_passive = pooled_passive - mean_vec_passive

    def cluster_metrics(centered, labels):
        """Mean within-orbit cosine, between-orbit cosine, gap."""
        N = centered.shape[0]
        norms = np.linalg.norm(centered, axis=1, keepdims=True)
        unit = centered / np.clip(norms, 1e-9, None)
        sim = unit @ unit.T
        same = labels[:, None] == labels[None, :]
        diff = ~same
        np.fill_diagonal(same, False)
        same_mean = float(sim[same].mean()) if same.any() else 0.0
        diff_mean = float(sim[diff].mean()) if diff.any() else 0.0
        return same_mean, diff_mean, same_mean - diff_mean

    passive_same, passive_diff, passive_gap = cluster_metrics(centered_passive, labels)

    # --- Causal intervention setup ---
    # The "paraphrase direction" per concept = within-concept mean
    # minus overall mean (in the centered space, just the within-concept
    # mean of centered_passive).
    paraphrase_dirs_passive = np.zeros((n_concepts, centered_passive.shape[1]), dtype=np.float32)
    for ci, c in enumerate(concepts):
        mask = labels == ci
        if mask.any():
            paraphrase_dirs_passive[ci] = centered_passive[mask].mean(axis=0)
    norms = np.linalg.norm(paraphrase_dirs_passive, axis=1, keepdims=True)
    paraphrase_unit_passive = paraphrase_dirs_passive / np.clip(norms, 1e-9, None)

    # Random direction control (same procedure with shuffled labels).
    rng_np = np.random.RandomState(seed)
    shuffled_labels = labels.copy()
    rng_np.shuffle(shuffled_labels)
    random_dirs_passive = np.zeros_like(paraphrase_dirs_passive)
    for ci in range(n_concepts):
        mask = shuffled_labels == ci
        if mask.any():
            random_dirs_passive[ci] = centered_passive[mask].mean(axis=0)
    norms = np.linalg.norm(random_dirs_passive, axis=1, keepdims=True)
    random_unit_passive = random_dirs_passive / np.clip(norms, 1e-9, None)

    # --- Passive "behavior": linear-readout test ---
    # Fit a logistic classifier on TOP of the frozen layer-5 pooled features.
    # This gives us a stand-in for "what the model could do without action
    # coupling." Intervention effect = drop in linear-readout accuracy when
    # we add a perturbation along the paraphrase direction.
    def fit_linear_classifier(features, labels_arr):
        head = nn.Linear(features.shape[1], n_concepts).to(device)
        feats_t = torch.from_numpy(features).float().to(device)
        labels_t = torch.from_numpy(labels_arr).long().to(device)
        opt = torch.optim.Adam(head.parameters(), lr=1e-2, weight_decay=1e-3)
        for _ in range(400):
            opt.zero_grad()
            logits = head(feats_t)
            loss = F.cross_entropy(logits, labels_t)
            loss.backward(); opt.step()
        with torch.no_grad():
            acc = (head(feats_t).argmax(-1) == labels_t).float().mean().item()
        return head, float(acc)

    head_passive, acc_passive = fit_linear_classifier(pooled_passive, labels)

    def intervention_effect(features, head_module, paraphrase_unit_per_concept,
                            strengths, labels_arr, *, mode: str):
        """Causal intervention on the paraphrase direction.

        Three intervention modes (the v1 design was buggy — adding the
        same-concept paraphrase direction just pushes embeddings deeper
        into the correct class):

          - "ablate":   subtract the projection of each example onto its
                        own paraphrase unit. Tests whether the paraphrase
                        axis is *load-bearing* for the classifier.
          - "wrong_dir":add the paraphrase unit of a DIFFERENT random
                        concept; pushes the example toward a wrong class.
                        Tests whether the classifier's decision actually
                        depends on the paraphrase axis.
          - "add_self": original buggy mode (kept for diagnostic); adds
                        the same-concept direction. Should produce zero
                        drop because it strengthens the right class.

        Returns per-α accuracy drops.
        """
        feats_t = torch.from_numpy(features).float().to(device)
        labels_t = torch.from_numpy(labels_arr).long().to(device)
        with torch.no_grad():
            base_logits = head_module(feats_t)
            base_acc = (base_logits.argmax(-1) == labels_t).float().mean().item()

        per_example_dir = paraphrase_unit_per_concept[labels_arr]
        per_example_dir_t = torch.from_numpy(per_example_dir).float().to(device)

        if mode == "wrong_dir":
            # For each example, pick a uniformly random different concept
            # and use ITS paraphrase direction. Seeded for reproducibility.
            rng_local = np.random.RandomState(seed + 7)
            wrong_idx = np.array([
                rng_local.choice([c for c in range(n_concepts) if c != lbl])
                for lbl in labels_arr
            ])
            per_example_dir_t = torch.from_numpy(
                paraphrase_unit_per_concept[wrong_idx]
            ).float().to(device)

        results = {"base_acc": float(base_acc), "mode": mode,
                   "strengths": [], "perturbed_acc": [], "drop": []}
        for alpha in strengths:
            if mode == "ablate":
                proj = (feats_t * per_example_dir_t).sum(dim=-1, keepdim=True) * per_example_dir_t
                perturbed = feats_t - alpha * proj
            else:
                perturbed = feats_t + alpha * per_example_dir_t
            with torch.no_grad():
                acc = (head_module(perturbed).argmax(-1) == labels_t).float().mean().item()
            results["strengths"].append(float(alpha))
            results["perturbed_acc"].append(float(acc))
            results["drop"].append(float(base_acc - acc))
        return results

    strengths = [
        intervention_max_norm * (i + 1) / n_intervention_strengths
        for i in range(n_intervention_strengths)
    ]
    passive_para_ablate = intervention_effect(
        pooled_passive, head_passive, paraphrase_unit_passive, strengths, labels, mode="ablate"
    )
    passive_para_wrong = intervention_effect(
        pooled_passive, head_passive, paraphrase_unit_passive, strengths, labels, mode="wrong_dir"
    )
    passive_rand_ablate = intervention_effect(
        pooled_passive, head_passive, random_unit_passive, strengths, labels, mode="ablate"
    )

    # --- Phase 2: active fine-tuning ---
    # Replace the LM head with a classification head over layer-5 pooled features.
    # Fine-tune the LM body + head end-to-end on the concept-id task.
    model = fresh_lm()
    model.train()
    classifier = nn.Linear(model.config.hidden_size, n_concepts).to(device)

    params = list(model.parameters()) + list(classifier.parameters())
    opt = torch.optim.AdamW(params, lr=ft_lr, weight_decay=1e-4)

    label_tensor = torch.tensor([lbl for _, _, _, lbl in flat], dtype=torch.long, device=device)
    losses = []
    for epoch in range(ft_epochs):
        # Mini-batch over the 72 examples; tiny dataset, batch of 24 is fine.
        order = list(range(n_examples))
        random.shuffle(order)
        bs = 24
        epoch_loss = 0.0
        epoch_correct = 0
        for start in range(0, n_examples, bs):
            batch = order[start:start + bs]
            batch_texts = [texts[i] for i in batch]
            batch_labels = label_tensor[batch]
            opt.zero_grad()
            pooled = hidden_pool_with_grad(model, batch_texts)
            logits = classifier(pooled)
            loss = F.cross_entropy(logits, batch_labels)
            loss.backward(); opt.step()
            epoch_loss += float(loss.item()) * len(batch)
            epoch_correct += int((logits.argmax(-1) == batch_labels).sum().item())
        losses.append(epoch_loss / n_examples)
    ft_train_acc = float(epoch_correct) / n_examples

    # --- Phase 3: active measurement ---
    model.eval()
    pooled_active = hidden_pool(model, texts)
    mean_vec_active = pooled_active.mean(axis=0, keepdims=True)
    centered_active = pooled_active - mean_vec_active

    active_same, active_diff, active_gap = cluster_metrics(centered_active, labels)

    paraphrase_dirs_active = np.zeros_like(centered_active[:n_concepts])
    paraphrase_dirs_active = np.zeros((n_concepts, centered_active.shape[1]), dtype=np.float32)
    for ci in range(n_concepts):
        mask = labels == ci
        if mask.any():
            paraphrase_dirs_active[ci] = centered_active[mask].mean(axis=0)
    norms = np.linalg.norm(paraphrase_dirs_active, axis=1, keepdims=True)
    paraphrase_unit_active = paraphrase_dirs_active / np.clip(norms, 1e-9, None)

    rng_np2 = np.random.RandomState(seed + 1)
    shuffled_labels2 = labels.copy()
    rng_np2.shuffle(shuffled_labels2)
    random_dirs_active = np.zeros_like(paraphrase_dirs_active)
    for ci in range(n_concepts):
        mask = shuffled_labels2 == ci
        if mask.any():
            random_dirs_active[ci] = centered_active[mask].mean(axis=0)
    norms = np.linalg.norm(random_dirs_active, axis=1, keepdims=True)
    random_unit_active = random_dirs_active / np.clip(norms, 1e-9, None)

    # Active behavior is the fine-tuned classifier itself.
    # We intervene on the SAME features the classifier sees.
    active_para_ablate = intervention_effect(
        pooled_active, classifier, paraphrase_unit_active, strengths, labels, mode="ablate"
    )
    active_para_wrong = intervention_effect(
        pooled_active, classifier, paraphrase_unit_active, strengths, labels, mode="wrong_dir"
    )
    active_rand_ablate = intervention_effect(
        pooled_active, classifier, random_unit_active, strengths, labels, mode="ablate"
    )

    return {
        "manifest": dict(
            model_id=model_id,
            sim_layer=sim_layer,
            ft_epochs=ft_epochs,
            ft_lr=ft_lr,
            n_examples=n_examples,
            n_concepts=n_concepts,
            ft_train_acc=ft_train_acc,
            seed=seed,
        ),
        "passive": {
            "cluster_same_mean": passive_same,
            "cluster_diff_mean": passive_diff,
            "cluster_gap": passive_gap,
            "linear_readout_acc": acc_passive,
            "paraphrase_ablate": passive_para_ablate,
            "paraphrase_wrong_dir": passive_para_wrong,
            "random_ablate": passive_rand_ablate,
        },
        "active": {
            "cluster_same_mean": active_same,
            "cluster_diff_mean": active_diff,
            "cluster_gap": active_gap,
            "ft_train_acc": ft_train_acc,
            "ft_losses": losses,
            "paraphrase_ablate": active_para_ablate,
            "paraphrase_wrong_dir": active_para_wrong,
            "random_ablate": active_rand_ablate,
        },
    }


@app.local_entrypoint()
def main(
    model_id: str = "EleutherAI/pythia-70m-deduped",
    paraphrases_path: str = "experiments/concept_geometry/concept_paraphrases.json",
    sim_layer: int = 5,
    max_length: int = 96,
    ft_epochs: int = 60,
    ft_lr: float = 5e-4,
    n_intervention_strengths: int = 10,
    intervention_max_norm: float = 5.0,
    seed: int = 20260610,
    out: str = "artifacts/passive_to_active/pythia_70m_v1.json",
) -> None:
    paraphrases = json.loads(Path(paraphrases_path).read_text())
    result = run_passive_to_active.remote(dict(
        model_id=model_id,
        paraphrases=paraphrases,
        sim_layer=sim_layer,
        max_length=max_length,
        ft_epochs=ft_epochs,
        ft_lr=ft_lr,
        n_intervention_strengths=n_intervention_strengths,
        intervention_max_norm=intervention_max_norm,
        seed=seed,
    ))
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True))

    p = result["passive"]
    a = result["active"]
    print(f"\nPassive→Active Geometry Result (model={result['manifest']['model_id']})")
    print(f"  fine-tuned to train_acc = {result['manifest']['ft_train_acc']:.3f} in {result['manifest']['ft_epochs']} epochs")
    print()
    print(f"  cluster gap (same-orbit cosine − wrong-orbit cosine):")
    print(f"    passive:  {p['cluster_gap']:+.4f} (same={p['cluster_same_mean']:.4f}, diff={p['cluster_diff_mean']:.4f})")
    print(f"    active:   {a['cluster_gap']:+.4f} (same={a['cluster_same_mean']:.4f}, diff={a['cluster_diff_mean']:.4f})")
    print()
    print(f"  linear-readout accuracy (with the classifier the interventions hit):")
    print(f"    passive (post-hoc linear probe): {p['linear_readout_acc']:.4f}")
    print(f"    active (fine-tuned head + body): {a['ft_train_acc']:.4f}")
    print()
    print(f"  causal intervention — max drop in accuracy across α:")
    print(f"    passive: ablate paraphrase axis ........ {max(p['paraphrase_ablate']['drop']):.4f}")
    print(f"    passive: push to wrong-concept direction {max(p['paraphrase_wrong_dir']['drop']):.4f}")
    print(f"    passive: ablate random axis (control) .. {max(p['random_ablate']['drop']):.4f}")
    print(f"    active:  ablate paraphrase axis ........ {max(a['paraphrase_ablate']['drop']):.4f}")
    print(f"    active:  push to wrong-concept direction {max(a['paraphrase_wrong_dir']['drop']):.4f}")
    print(f"    active:  ablate random axis (control) .. {max(a['random_ablate']['drop']):.4f}")
