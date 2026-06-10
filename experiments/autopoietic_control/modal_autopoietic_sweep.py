#!/usr/bin/env python3
"""Paper 5b — Autopoietic Control sweep.

For each cell (model x seed x los_variant), runs:

  Phase 0: passive measurement (post-hoc linear probe on epoch-0 features)
  Phase 1: fine-tune for 60 epochs, save snapshots at epochs
           [1, 2, 4, 8, 16, 32, 60]
  Phase 2: at every snapshot, measure
           - cluster gap (same - diff centered cosine)
           - paraphrase-specific drop (= paraphrase-axis ablate
             - random-axis ablate, max over alpha)
           - wrong-direction robustness (push to other concept centroid)
           - held-out paraphrase accuracy (= viability buffer)
  Phase 3 (final snapshot only): repair test
           - perturb classifier head weights with Gaussian noise (sigma sweep)
           - measure immediate accuracy drop on held-out paraphrases
           - run K in-context test-time updates on held-out paraphrases
             (K ∈ [0, 1, 5, 10, 20])
           - measure recovery curve

Hold-out: per concept, variant index 2 is reserved for held-out
evaluation; train on variants 0 and 1.

LoS variants:
  - `full_ft`     : standard end-to-end fine-tune
  - `frozen_early`: freeze first half of encoder layers
  - `frozen_encoder`: freeze entire encoder, train head only

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/autopoietic_control/modal_autopoietic_sweep.py
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

app = modal.App(name="research-derived-autopoietic-5b")

SNAPSHOT_EPOCHS = [1, 2, 4, 8, 16, 32, 60]
REPAIR_SIGMAS = [0.05, 0.1, 0.2, 0.4]
REPAIR_K_STEPS = [0, 1, 5, 10, 20]
INTERVENTION_STRENGTHS = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]


@app.function(image=IMAGE, timeout=3600, cpu=8, memory=8192)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import copy
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
    seed: int = arg["seed"]
    los_variant: str = arg["los_variant"]

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
        m.to(device)
        return m

    # Train (variants 0, 1) vs held-out (variant 2)
    concepts = [e["id"] for e in paraphrases]
    label_idx_of = {c: i for i, c in enumerate(concepts)}
    n_concepts = len(concepts)

    train_flat = []
    heldout_flat = []
    for entry in paraphrases:
        cid = entry["id"]
        lbl = label_idx_of[cid]
        for i, v in enumerate(entry["variants"]):
            tup = (cid, i, v, lbl)
            if i < 2:
                train_flat.append(tup)
            else:
                heldout_flat.append(tup)

    train_texts = [t for _, _, t, _ in train_flat]
    train_labels = np.array([lbl for _, _, _, lbl in train_flat])
    heldout_texts = [t for _, _, t, _ in heldout_flat]
    heldout_labels = np.array([lbl for _, _, _, lbl in heldout_flat])

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
        mask = (attn.float() if attn is not None
                else torch.ones_like(e["input_ids"]).float()).unsqueeze(-1)
        pooled = (hs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return pooled.cpu().numpy()

    def hidden_pool_grad(model, t):
        e = encode_batch(t)
        o = model(**e, output_hidden_states=True)
        hs = o.hidden_states[sim_layer].float()
        attn = e.get("attention_mask")
        mask = (attn.float() if attn is not None
                else torch.ones_like(e["input_ids"]).float()).unsqueeze(-1)
        return (hs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)

    def cluster_metrics(centered, labels_):
        norms = np.linalg.norm(centered, axis=1, keepdims=True)
        unit = centered / np.clip(norms, 1e-9, None)
        sim = unit @ unit.T
        same = labels_[:, None] == labels_[None, :]
        diff = ~same
        np.fill_diagonal(same, False)
        return float(sim[same].mean()), float(sim[diff].mean())

    def per_concept_dirs(centered, labels_):
        D = centered.shape[1]
        dirs = np.zeros((n_concepts, D), dtype=np.float32)
        for ci in range(n_concepts):
            m = labels_ == ci
            if m.any():
                dirs[ci] = centered[m].mean(axis=0)
        norms = np.linalg.norm(dirs, axis=1, keepdims=True)
        return dirs / np.clip(norms, 1e-9, None)

    def intervention(features, head_module, unit_per_concept,
                     labels_arr, mode, seed_for_wrong):
        f = torch.from_numpy(features).float().to(device)
        l = torch.from_numpy(labels_arr).long().to(device)
        with torch.no_grad():
            base_acc = (head_module(f).argmax(-1) == l).float().mean().item()
        dir_per = unit_per_concept[labels_arr]
        d = torch.from_numpy(dir_per).float().to(device)
        if mode == "wrong_dir":
            rng_local = np.random.RandomState(seed_for_wrong)
            wrong_idx = np.array([
                rng_local.choice([c for c in range(n_concepts) if c != lbl])
                for lbl in labels_arr
            ])
            d = torch.from_numpy(unit_per_concept[wrong_idx]).float().to(device)

        drops = []
        for alpha in INTERVENTION_STRENGTHS:
            if mode == "ablate":
                proj = (f * d).sum(dim=-1, keepdim=True) * d
                perturbed = f - alpha * proj
            else:
                perturbed = f + alpha * d
            with torch.no_grad():
                acc = (head_module(perturbed).argmax(-1) == l).float().mean().item()
            drops.append(float(base_acc - acc))
        return float(base_acc), drops

    def fit_post_hoc_head(features, labels_arr):
        head = nn.Linear(features.shape[1], n_concepts).to(device)
        f = torch.from_numpy(features).float().to(device)
        l = torch.from_numpy(labels_arr).long().to(device)
        opt = torch.optim.Adam(head.parameters(), lr=1e-2, weight_decay=1e-3)
        for _ in range(400):
            opt.zero_grad()
            loss = F.cross_entropy(head(f), l)
            loss.backward()
            opt.step()
        with torch.no_grad():
            acc = (head(f).argmax(-1) == l).float().mean().item()
        return head, float(acc)

    def measure_snapshot(model, head, label_for):
        """All measurements at one checkpoint.

        label_for == 'passive' uses the post-hoc head from the epoch-0
        features; 'active' uses the trained head.
        """
        with torch.no_grad():
            train_pool = hidden_pool_eval(model, train_texts)
            heldout_pool = hidden_pool_eval(model, heldout_texts)

        mean_t = train_pool.mean(axis=0, keepdims=True)
        centered_t = train_pool - mean_t
        # held-outs are centered with the train mean — it's the same encoder
        centered_h = heldout_pool - mean_t

        same, diff = cluster_metrics(centered_t, train_labels)
        para_dir = per_concept_dirs(centered_t, train_labels)
        rng = np.random.RandomState(seed + 13 + hash(label_for) % 2**16)
        shuffled = train_labels.copy()
        rng.shuffle(shuffled)
        rand_dir = per_concept_dirs(centered_t, shuffled)

        base_train, para_ablate = intervention(
            train_pool, head, para_dir, train_labels, "ablate", seed + 17)
        _, para_wrong = intervention(
            train_pool, head, para_dir, train_labels, "wrong_dir", seed + 19)
        _, rand_ablate = intervention(
            train_pool, head, rand_dir, train_labels, "ablate", seed + 23)

        # Buffer = held-out paraphrase accuracy on TRAIN-direction-centered
        # features (encoder is the same, but the held-outs were never seen).
        h = torch.from_numpy(heldout_pool).float().to(device)
        lh = torch.from_numpy(heldout_labels).long().to(device)
        with torch.no_grad():
            heldout_acc = (head(h).argmax(-1) == lh).float().mean().item()

        return dict(
            cluster_same=same,
            cluster_diff=diff,
            cluster_gap=same - diff,
            train_acc=base_train,
            heldout_buffer_acc=float(heldout_acc),
            max_para_ablate=max(para_ablate),
            max_para_wrong=max(para_wrong),
            max_rand_ablate=max(rand_ablate),
            specific_at_max=max(para_ablate) - max(rand_ablate),
            para_ablate_curve=para_ablate,
            para_wrong_curve=para_wrong,
            rand_ablate_curve=rand_ablate,
        )

    # ============ Phase 0: passive ============
    model = fresh_lm()
    model.eval()
    pooled_passive = hidden_pool_eval(model, train_texts)
    head_passive, train_acc_p = fit_post_hoc_head(pooled_passive, train_labels)
    passive = measure_snapshot(model, head_passive, "passive")
    passive["epoch"] = 0
    passive["train_acc_posthoc"] = train_acc_p

    # ============ Phase 1: active fine-tune with snapshots ============
    model = fresh_lm()
    hidden_size = model.config.hidden_size
    classifier = nn.Linear(hidden_size, n_concepts).to(device)

    # Apply LoS variant — freeze layers
    if los_variant == "frozen_encoder":
        for p in model.parameters():
            p.requires_grad = False
    elif los_variant == "frozen_early":
        # Freeze the first half of transformer layers
        try:
            blocks = (
                model.gpt_neox.layers if hasattr(model, "gpt_neox")
                else model.transformer.h
            )
            n_blocks = len(blocks)
            for i in range(n_blocks // 2):
                for p in blocks[i].parameters():
                    p.requires_grad = False
            # also freeze embeddings
            try:
                model.get_input_embeddings().weight.requires_grad = False
            except Exception:
                pass
        except Exception as e:
            return dict(error=f"frozen_early not supported: {e}")
    # full_ft = nothing frozen

    trainable_params = (
        [p for p in model.parameters() if p.requires_grad]
        + list(classifier.parameters())
    )
    opt = torch.optim.AdamW(trainable_params, lr=ft_lr, weight_decay=1e-4)
    label_t = torch.tensor(
        [lbl for _, _, _, lbl in train_flat], dtype=torch.long, device=device)
    bs = 24
    n_examples = len(train_flat)
    trajectory = []
    repair_snapshot = None
    for epoch in range(1, ft_epochs + 1):
        model.train()
        order = list(range(n_examples))
        random.shuffle(order)
        for s in range(0, n_examples, bs):
            b = order[s:s + bs]
            opt.zero_grad()
            pooled = hidden_pool_grad(model, [train_texts[i] for i in b])
            logits = classifier(pooled)
            loss = F.cross_entropy(logits, label_t[b])
            loss.backward()
            opt.step()
        if epoch in SNAPSHOT_EPOCHS:
            model.eval()
            snap = measure_snapshot(model, classifier, "active")
            snap["epoch"] = epoch
            trajectory.append(snap)

    # Save final classifier state for repair (always — independent of
    # whether ft_epochs happens to be in SNAPSHOT_EPOCHS).
    model.eval()
    repair_snapshot = dict(
        classifier_state=copy.deepcopy(classifier.state_dict()),
    )

    # ============ Phase 3: repair test ============
    # Take final model + classifier. Add Gaussian noise to classifier head,
    # then run K test-time gradient steps on HELDOUT paraphrases (variant 2)
    # — these are the "viability inputs" the system uses to recover.
    model.eval()
    heldout_t = tokenizer(
        heldout_texts, return_tensors="pt", truncation=True,
        max_length=max_length, padding=True
    )
    heldout_t = {k: v.to(device) for k, v in heldout_t.items()}
    heldout_label_t = torch.tensor(heldout_labels, dtype=torch.long, device=device)

    def eval_head(head, feats=None):
        if feats is None:
            with torch.no_grad():
                o = model(**heldout_t, output_hidden_states=True)
            hs = o.hidden_states[sim_layer].float()
            attn = heldout_t.get("attention_mask")
            mask = (attn.float() if attn is not None
                    else torch.ones_like(heldout_t["input_ids"]).float()
                    ).unsqueeze(-1)
            feats = (hs * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        with torch.no_grad():
            return (head(feats).argmax(-1) == heldout_label_t).float().mean().item(), feats

    # Pre-extract held-out features once (encoder is frozen during repair —
    # we only update the classifier head, which is the analogue of allostatic
    # control acting on a single layer).
    base_acc, heldout_feats = eval_head(classifier)

    repair_results = []
    for sigma in REPAIR_SIGMAS:
        for K in REPAIR_K_STEPS:
            torch.manual_seed(seed + int(sigma * 1000) + K * 7)
            np.random.seed(seed + int(sigma * 1000) + K * 7)
            # Re-load clean head, then perturb
            head_perturbed = nn.Linear(hidden_size, n_concepts).to(device)
            head_perturbed.load_state_dict(repair_snapshot["classifier_state"])
            with torch.no_grad():
                for p in head_perturbed.parameters():
                    p.add_(torch.randn_like(p) * sigma)
            # Immediate acc after perturbation
            acc_immediate, _ = eval_head(head_perturbed, heldout_feats)
            # Run K test-time update steps on held-outs
            if K > 0:
                opt2 = torch.optim.Adam(head_perturbed.parameters(),
                                        lr=1e-2)
                for _ in range(K):
                    opt2.zero_grad()
                    logits = head_perturbed(heldout_feats)
                    loss = F.cross_entropy(logits, heldout_label_t)
                    loss.backward()
                    opt2.step()
            acc_after, _ = eval_head(head_perturbed, heldout_feats)
            repair_results.append(dict(
                sigma=sigma, K=K,
                acc_immediate=float(acc_immediate),
                acc_after=float(acc_after),
                acc_baseline=float(base_acc),
                drop_immediate=float(base_acc - acc_immediate),
                recovery=float(acc_after - acc_immediate),
                residual_loss=float(base_acc - acc_after),
            ))

    return dict(
        model_id=model_id,
        seed=seed,
        los_variant=los_variant,
        sim_layer=sim_layer,
        passive=passive,
        trajectory=trajectory,
        repair=repair_results,
        snapshot_epochs=SNAPSHOT_EPOCHS,
        repair_sigmas=REPAIR_SIGMAS,
        repair_K_steps=REPAIR_K_STEPS,
    )


MODEL_CONFIGS = [
    ("EleutherAI/pythia-70m-deduped", 5),
    ("openai-community/gpt2", 6),
]
LOS_VARIANTS = ["full_ft", "frozen_early", "frozen_encoder"]


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    paraphrases_path: str = "experiments/concept_geometry/concept_paraphrases.json",
    max_length: int = 96,
    ft_epochs: int = 60,
    ft_lr: float = 5e-4,
    out: str = "artifacts/autopoietic_control/sweep_v1.json",
) -> None:
    paraphrases = json.loads(Path(paraphrases_path).read_text())
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]

    cell_args = []
    for model_id, sim_layer in MODEL_CONFIGS:
        for sd in seed_list:
            for los in LOS_VARIANTS:
                cell_args.append(dict(
                    model_id=model_id, paraphrases=paraphrases,
                    sim_layer=sim_layer, max_length=max_length,
                    ft_epochs=ft_epochs, ft_lr=ft_lr, seed=sd,
                    los_variant=los,
                ))

    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Quick summary table
    summary_rows = []
    for r in results:
        if "error" in r:
            continue
        final = r["trajectory"][-1] if r["trajectory"] else None
        if final is None:
            continue
        summary_rows.append(dict(
            model=r["model_id"].split("/")[-1],
            seed=r["seed"],
            los=r["los_variant"],
            passive_specific=r["passive"]["specific_at_max"],
            active_specific=final["specific_at_max"],
            passive_buffer=r["passive"]["heldout_buffer_acc"],
            active_buffer=final["heldout_buffer_acc"],
            passive_cluster_gap=r["passive"]["cluster_gap"],
            active_cluster_gap=final["cluster_gap"],
        ))

    out_path.write_text(json.dumps({
        "manifest": {
            "seeds": seed_list,
            "models": [m[0] for m in MODEL_CONFIGS],
            "los_variants": LOS_VARIANTS,
            "ft_epochs": ft_epochs,
            "ft_lr": ft_lr,
            "snapshot_epochs": SNAPSHOT_EPOCHS,
            "intervention_strengths": INTERVENTION_STRENGTHS,
            "repair_sigmas": REPAIR_SIGMAS,
            "repair_K_steps": REPAIR_K_STEPS,
        },
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nfinal-snapshot summary ({len(summary_rows)} cells):")
    print(f"{'model':<22} {'seed':>8} {'los':<15} | "
          f"{'p_spec':>8} {'a_spec':>8} {'p_buf':>6} {'a_buf':>6}")
    for r in summary_rows:
        print(f"  {r['model']:<20} {r['seed']:>8} {r['los']:<15} | "
              f"{r['passive_specific']:>+.4f} {r['active_specific']:>+.4f} "
              f"{r['passive_buffer']:>.3f} {r['active_buffer']:>.3f}")
