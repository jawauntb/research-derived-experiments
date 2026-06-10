#!/usr/bin/env python3
"""Paper 6 v1 — Valence-Induced Object Formation sweep.

Minimal bandit env. Each item has a 16-dim observation:
  obs[0:8]  = "color" channel (4-way one-hot + Gaussian noise σ=0.15)
  obs[8:16] = "label" channel (2-way one-hot + Gaussian noise σ=0.15)

Reward function maps (color, label) -> {-1, +1} via one of:
  - XOR             : reward = +1 iff (color in {0,1}) XOR (label == 0)
  - additive_thresh : reward = +1 iff (color + label_signed) > 0
                      where label_signed ∈ {-1, +1}

In both, neither color nor label alone fully determines reward.

Three training conditions (same encoder MLP 16 → 64 → 32):
  - reconstruct  : encoder -> decoder 32 → 16, MSE
  - sensory      : encoder -> head 32 → 4, predict color
  - valence_coupled : encoder -> head 32 → 2, predict OPTIMAL ACTION
                      (consume iff reward > 0)

Post-training, extract embeddings for a held-out test set of N items
sampled uniformly over (color, label). Measure cluster gap along three
axes:
  - color axis : same-color centered cosine - diff-color centered cosine
  - label axis : same-label - diff-label
  - reward axis : same-reward - diff-reward (the causal-valence axis)

PREDICTION: reconstruct/sensory cluster by color; valence_coupled
clusters by reward.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/valence_object_formation/modal_object_formation_sweep.py
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "numpy>=1.26,<2.0",
)

app = modal.App(name="research-derived-valence-objects")

N_COLORS = 4
N_LABELS = 2
ITEMS = [(c, l) for c in range(N_COLORS) for l in range(N_LABELS)]
EMBED_DIM = 32
OBS_NOISE = 0.15


@app.function(image=IMAGE, timeout=600, cpu=4, memory=4096)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    seed: int = arg["seed"]
    condition: str = arg["condition"]
    reward_structure: str = arg["reward_structure"]
    train_steps: int = arg["train_steps"]
    train_samples_per_step: int = arg["train_samples_per_step"]
    test_samples: int = arg["test_samples"]

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def reward_of(color: int, label: int) -> int:
        if reward_structure == "xor":
            return 1 if ((color in (0, 1)) ^ (label == 0)) else -1
        elif reward_structure == "additive_thresh":
            # color in {0..3}; signed_label in {-1, +1}; sum > 0 -> reward +1.
            # color in {0,1} (low) + label==0 (low signed -1) -> -1 or 0
            # arrange so each (color,label) pair has a clean reward
            return 1 if (color + (1 if label == 1 else -2)) > 0 else -1
        else:
            raise ValueError(reward_structure)

    def sample_obs(n: int, rng: np.random.RandomState):
        # Sample uniformly over (color, label), then encode
        idx = rng.randint(0, len(ITEMS), size=n)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        rewards = np.array([reward_of(c, l) for c, l in zip(colors, labels)])
        # Build 16-dim observation: 8 dims for color (4-way one-hot in dims 0-3,
        # noise in 4-7), 8 dims for label (2-way one-hot in dims 0-1 of label
        # channel, noise in 2-7).
        obs = np.zeros((n, 16), dtype=np.float32)
        # color: one-hot in first 4 dims
        obs[np.arange(n), colors] = 1.0
        # label: one-hot in dims 8 and 9
        obs[np.arange(n), 8 + labels] = 1.0
        # Add Gaussian noise to all 16 dims to make the encoder do work
        obs += rng.randn(n, 16).astype(np.float32) * OBS_NOISE
        # Permute the dimensions (not labels) so positional ordering does not
        # match feature semantics — this prevents trivial dim-1 = color
        # solutions.
        perm = rng.permutation(16)
        obs = obs[:, perm]
        return obs, colors, labels, rewards, perm

    rng_train = np.random.RandomState(seed)
    perm_train = None  # captured by sample_obs on first call (we use the same
                      # permutation for both train and test)

    # Build encoder
    encoder = nn.Sequential(
        nn.Linear(16, 64), nn.ReLU(),
        nn.Linear(64, EMBED_DIM),
    ).to(device)

    if condition == "reconstruct":
        decoder = nn.Sequential(
            nn.Linear(EMBED_DIM, 64), nn.ReLU(),
            nn.Linear(64, 16),
        ).to(device)
        head = None
        params = list(encoder.parameters()) + list(decoder.parameters())
    elif condition == "sensory":
        head = nn.Linear(EMBED_DIM, N_COLORS).to(device)
        decoder = None
        params = list(encoder.parameters()) + list(head.parameters())
    elif condition == "valence_coupled":
        head = nn.Linear(EMBED_DIM, 2).to(device)  # consume / skip
        decoder = None
        params = list(encoder.parameters()) + list(head.parameters())
    else:
        raise ValueError(condition)

    opt = torch.optim.Adam(params, lr=2e-3)

    # Sample a stable observation permutation once so train/test share it.
    obs_pre, _, _, _, perm_train = sample_obs(1, rng_train)
    # Use perm_train going forward by patching the sample_obs closure manually.
    # Simpler: re-implement train/test sampling that uses a fixed perm.
    def sample_with_perm(n: int, rng: np.random.RandomState, perm):
        idx = rng.randint(0, len(ITEMS), size=n)
        colors = np.array([ITEMS[i][0] for i in idx])
        labels = np.array([ITEMS[i][1] for i in idx])
        rewards = np.array([reward_of(c, l) for c, l in zip(colors, labels)])
        obs = np.zeros((n, 16), dtype=np.float32)
        obs[np.arange(n), colors] = 1.0
        obs[np.arange(n), 8 + labels] = 1.0
        obs += rng.randn(n, 16).astype(np.float32) * OBS_NOISE
        obs = obs[:, perm]
        return obs, colors, labels, rewards

    # Training loop
    losses = []
    for step in range(train_steps):
        obs, colors, labels, rewards = sample_with_perm(
            train_samples_per_step, rng_train, perm_train
        )
        x = torch.from_numpy(obs).to(device)
        z = encoder(x)
        if condition == "reconstruct":
            recon = decoder(z)
            loss = F.mse_loss(recon, x)
        elif condition == "sensory":
            logits = head(z)
            target = torch.from_numpy(colors).long().to(device)
            loss = F.cross_entropy(logits, target)
        else:  # valence_coupled
            logits = head(z)
            # optimal action = 1 (consume) iff reward > 0, else 0 (skip)
            optimal_action = (rewards > 0).astype(np.int64)
            target = torch.from_numpy(optimal_action).long().to(device)
            loss = F.cross_entropy(logits, target)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 50 == 0 or step == train_steps - 1:
            losses.append(dict(step=step, loss=float(loss.item())))

    # Held-out clustering
    rng_test = np.random.RandomState(seed + 9999)
    test_obs, test_colors, test_labels, test_rewards = sample_with_perm(
        test_samples, rng_test, perm_train
    )
    with torch.no_grad():
        test_z = encoder(torch.from_numpy(test_obs).to(device)).cpu().numpy()

    # Center and unit-normalize for cosine
    mean = test_z.mean(axis=0, keepdims=True)
    centered = test_z - mean
    norms = np.linalg.norm(centered, axis=1, keepdims=True)
    unit = centered / np.clip(norms, 1e-9, None)
    sim = unit @ unit.T

    def cluster_gap(labels_arr):
        same = labels_arr[:, None] == labels_arr[None, :]
        diff = ~same
        np.fill_diagonal(same, False)
        return float(sim[same].mean() - sim[diff].mean()), \
               float(sim[same].mean()), float(sim[diff].mean())

    color_gap, color_same, color_diff = cluster_gap(test_colors)
    label_gap, label_same, label_diff = cluster_gap(test_labels)
    reward_gap, reward_same, reward_diff = cluster_gap(test_rewards)

    # Held-out task accuracy (if applicable)
    task_acc = None
    if condition == "sensory":
        with torch.no_grad():
            logits = head(torch.from_numpy(test_z).to(device))
            target = torch.from_numpy(test_colors).long().to(device)
            task_acc = float((logits.argmax(-1) == target).float().mean().item())
    elif condition == "valence_coupled":
        with torch.no_grad():
            logits = head(torch.from_numpy(test_z).to(device))
            optimal = (test_rewards > 0).astype(np.int64)
            target = torch.from_numpy(optimal).long().to(device)
            task_acc = float((logits.argmax(-1) == target).float().mean().item())

    return dict(
        seed=seed,
        condition=condition,
        reward_structure=reward_structure,
        train_steps=train_steps,
        losses=losses,
        color_gap=color_gap, color_same=color_same, color_diff=color_diff,
        label_gap=label_gap, label_same=label_same, label_diff=label_diff,
        reward_gap=reward_gap, reward_same=reward_same, reward_diff=reward_diff,
        task_acc=task_acc,
        # save the test embedding for 2D projection figure
        test_embeddings=test_z.tolist(),
        test_colors=test_colors.tolist(),
        test_labels=test_labels.tolist(),
        test_rewards=test_rewards.tolist(),
    )


@app.local_entrypoint()
def main(
    seeds: str = "20260610,1729,4242",
    train_steps: int = 1500,
    train_samples_per_step: int = 64,
    test_samples: int = 512,
    out: str = "artifacts/valence_object_formation/sweep_v1.json",
) -> None:
    seed_list = [int(s.strip()) for s in seeds.split(",") if s.strip()]
    conditions = ["reconstruct", "sensory", "valence_coupled"]
    reward_structures = ["xor", "additive_thresh"]

    cell_args = []
    for sd in seed_list:
        for cond in conditions:
            for rs in reward_structures:
                cell_args.append(dict(
                    seed=sd, condition=cond, reward_structure=rs,
                    train_steps=train_steps,
                    train_samples_per_step=train_samples_per_step,
                    test_samples=test_samples,
                ))

    print(f"running {len(cell_args)} cells in parallel...")
    results = list(run_cell.map(cell_args))

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for r in results:
        summary_rows.append(dict(
            seed=r["seed"], condition=r["condition"],
            reward_structure=r["reward_structure"],
            color_gap=r["color_gap"], label_gap=r["label_gap"],
            reward_gap=r["reward_gap"], task_acc=r["task_acc"],
        ))

    out_path.write_text(json.dumps({
        "manifest": dict(
            seeds=seed_list,
            conditions=conditions,
            reward_structures=reward_structures,
            train_steps=train_steps,
            train_samples_per_step=train_samples_per_step,
            test_samples=test_samples,
            obs_noise=OBS_NOISE,
            n_colors=N_COLORS, n_labels=N_LABELS,
        ),
        "summary": summary_rows,
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nfinal cluster gaps ({len(summary_rows)} cells):")
    print(f"{'cond':<18} {'rs':<18} {'seed':>10} | "
          f"{'color':>8} {'label':>8} {'reward':>8} {'task_acc':>9}")
    for r in summary_rows:
        ta = f"{r['task_acc']:.3f}" if r['task_acc'] is not None else "  --   "
        print(f"  {r['condition']:<16} {r['reward_structure']:<16} {r['seed']:>10} | "
              f"{r['color_gap']:>+.4f} {r['label_gap']:>+.4f} "
              f"{r['reward_gap']:>+.4f}  {ta}")
