#!/usr/bin/env python3
"""Rotated MNIST partial-orbit extension to *When Pixels Beat Embeddings*.

Repeats the same four-method comparison (v1 pixel cosine, encoder cosine,
encoder invariance, direct rotation generator) but on **real digit
images** instead of synthetic strokes. The motivating question: does the
pixel-cosine advantage from the stroke benchmark survive natural-image
variation (writing style, stroke thickness, slant), or does the learned
encoder finally win?

Setup:

- 10 classes × Z_8 rotation group.
- For each class, sample 3 of 8 rotations for training and 5 for OOD.
- 30 images per (class, rotation) cell.
- Images downsampled from 28×28 to 16×16 to match the stroke pipeline.

Methods scored on recall/precision vs oracle Z_8.

Run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/neural_group_generator/modal_rotated_mnist.py
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
    "scipy>=1.11,<2.0",
    "datasets>=2.20,<4.0",
    "pillow>=10,<11",
)

app = modal.App(name="research-derived-rotated-mnist-extension")


@app.function(image=IMAGE, timeout=3600, cpu=4)
def run_rotated_mnist(arg: dict[str, Any]) -> dict[str, Any]:
    import math
    import random

    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from PIL import Image
    from datasets import load_dataset
    from scipy.ndimage import rotate as scipy_rotate

    n_rotations = arg["n_rotations"]
    train_per_class = arg["train_per_class"]
    samples_per_cell = arg["samples_per_cell"]
    n_candidates = arg["n_candidates"]
    threshold = arg["threshold"]
    encoder_epochs = arg["encoder_epochs"]
    seed = arg["seed"]
    grid_size = arg["grid_size"]

    rng = np.random.RandomState(seed)
    py_rng = random.Random(seed)
    torch.manual_seed(seed)

    # --- load MNIST ---
    ds = load_dataset("ylecun/mnist", split="train")
    label_to_imgs: dict[int, list[np.ndarray]] = {i: [] for i in range(10)}
    for row in ds:
        img = row["image"]  # PIL image, 28x28 L
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.array(img).astype(np.uint8))
        img_small = img.resize((grid_size, grid_size), Image.BILINEAR)
        arr = np.array(img_small).astype(np.float32) / 255.0
        label_to_imgs[int(row["label"])].append(arr)

    # subsample for efficiency
    n_needed_per_class = n_rotations * samples_per_cell
    for c in range(10):
        py_rng.shuffle(label_to_imgs[c])
        label_to_imgs[c] = label_to_imgs[c][:n_needed_per_class]

    # --- partial-orbit split ---
    train_rots = {}
    ood_rots = {}
    for c in range(10):
        rots = list(range(n_rotations))
        py_rng.shuffle(rots)
        train_rots[c] = sorted(rots[:train_per_class])
        ood_rots[c] = sorted(rots[train_per_class:])

    def rot_arr(img: np.ndarray, deg: float) -> np.ndarray:
        r = scipy_rotate(img, angle=deg, reshape=False, order=1,
                         mode="constant", cval=0.0)
        return np.clip(r, 0, 1).astype(np.float32)

    def build_split():
        train_x, train_y, ood_x, ood_y = [], [], [], []
        for c in range(10):
            imgs = label_to_imgs[c]
            assigned_train = imgs[: train_per_class * samples_per_cell]
            assigned_ood = imgs[train_per_class * samples_per_cell:]
            tidx = 0
            for r in train_rots[c]:
                deg = r * (360.0 / n_rotations)
                for _ in range(samples_per_cell):
                    rotated = rot_arr(assigned_train[tidx], deg)
                    train_x.append(rotated)
                    train_y.append(c)
                    tidx += 1
            oidx = 0
            for r in ood_rots[c]:
                deg = r * (360.0 / n_rotations)
                for _ in range(samples_per_cell):
                    if oidx >= len(assigned_ood):
                        break
                    rotated = rot_arr(assigned_ood[oidx], deg)
                    ood_x.append(rotated)
                    ood_y.append(c)
                    oidx += 1
        tx = torch.from_numpy(np.stack(train_x)).unsqueeze(1)
        ty = torch.tensor(train_y, dtype=torch.long)
        ox = torch.from_numpy(np.stack(ood_x)).unsqueeze(1)
        oy = torch.tensor(ood_y, dtype=torch.long)
        return tx, ty, ox, oy

    tx, ty, ox, oy = build_split()
    print(f"train shape {tx.shape}, ood shape {ox.shape}")

    B = tx.shape[0]
    candidate_angles = [k * (360.0 / n_candidates) for k in range(n_candidates)]
    oracle_angles = [k * (360.0 / n_rotations) for k in range(n_rotations)]
    oracle_set = set(oracle_angles)

    def angle_match(a: float, b: float, tol: float = 7.5) -> bool:
        d = abs(a - b)
        d = min(d, 360 - d)
        return d < tol

    def recall_precision(kept: list[float]) -> tuple[float, float]:
        tp_r = sum(1 for o in oracle_set if any(angle_match(o, k) for k in kept))
        tp_p = sum(1 for k in kept if any(angle_match(o, k) for o in oracle_set))
        return tp_r / len(oracle_set), tp_p / max(1, len(kept))

    def cos(a: np.ndarray, b: np.ndarray) -> float:
        na = float(np.linalg.norm(a))
        nb = float(np.linalg.norm(b))
        return 0.0 if na == 0 or nb == 0 else float(np.dot(a, b) / (na * nb))

    # ----- Approach 0 (v1 baseline): pixel cosine -----
    train_feats_pixel = [tx[i, 0].cpu().numpy().reshape(-1) for i in range(B)]
    train_labels = ty.tolist()
    pixel_scores = {}
    for theta in candidate_angles:
        sims = []
        for i in range(B):
            r = rot_arr(tx[i, 0].cpu().numpy(), theta).reshape(-1)
            same = [j for j in range(B) if train_labels[j] == train_labels[i]]
            sims.append(max(cos(r, train_feats_pixel[j]) for j in same))
        pixel_scores[theta] = float(np.mean(sims))
    pixel_kept = [a for a, s in pixel_scores.items() if s >= threshold]
    if 0.0 not in pixel_kept:
        pixel_kept = [0.0] + pixel_kept
    pixel_r, pixel_p = recall_precision(pixel_kept)

    # ----- Train SupCon encoder for Approaches 2, 3 -----
    class Encoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.body = nn.Sequential(
                nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                nn.Flatten(),
            )
            d = 32 * (grid_size // 4) ** 2
            self.head = nn.Sequential(
                nn.Linear(d, 64), nn.ReLU(), nn.Linear(64, 32)
            )

        def forward(self, x):
            return F.normalize(self.head(self.body(x)), dim=-1)

    encoder = Encoder()
    opt = torch.optim.Adam(encoder.parameters(), lr=3e-3, weight_decay=1e-4)
    for _ in range(encoder_epochs):
        encoder.train()
        opt.zero_grad()
        z = encoder(tx)
        sim = (z @ z.t()) / 0.1
        mask_same = (ty.unsqueeze(0) == ty.unsqueeze(1)).float()
        mask_same.fill_diagonal_(0)
        logits = sim - sim.max(dim=1, keepdim=True).values.detach()
        exp_logits = torch.exp(logits)
        exp_logits = exp_logits * (1 - torch.eye(B))
        log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True).clamp(min=1e-9))
        denom = mask_same.sum(dim=1).clamp(min=1)
        mlp = (mask_same * log_prob).sum(dim=1) / denom
        loss = -mlp.mean()
        loss.backward(); opt.step()

    # ----- Approach 2: encoder invariance scoring -----
    encoder.eval()
    with torch.no_grad():
        z_base = encoder(tx)
    inv_scores = {}
    for theta in candidate_angles:
        rotated_imgs = torch.zeros_like(tx)
        for i in range(B):
            rotated_imgs[i, 0] = torch.from_numpy(rot_arr(tx[i, 0].cpu().numpy(), theta))
        with torch.no_grad():
            z_rot = encoder(rotated_imgs)
        cosines = (z_base * z_rot).sum(dim=-1)
        inv_scores[theta] = float(cosines.mean().item())
    inv_kept = [a for a, s in inv_scores.items() if s >= threshold]
    if 0.0 not in inv_kept:
        inv_kept = [0.0] + inv_kept
    inv_r, inv_p = recall_precision(inv_kept)

    # ----- Approach 3: encoder-based enumerative -----
    with torch.no_grad():
        train_feats_enc = encoder(tx).cpu().numpy()
    enc_scores = {}
    for theta in candidate_angles:
        rotated_imgs = torch.zeros_like(tx)
        for i in range(B):
            rotated_imgs[i, 0] = torch.from_numpy(rot_arr(tx[i, 0].cpu().numpy(), theta))
        with torch.no_grad():
            rotated_feats = encoder(rotated_imgs).cpu().numpy()
        sims = []
        for i in range(B):
            same = [j for j in range(B) if train_labels[j] == train_labels[i]]
            sims.append(max(cos(rotated_feats[i], train_feats_enc[j]) for j in same))
        enc_scores[theta] = float(np.mean(sims))
    enc_kept = [a for a, s in enc_scores.items() if s >= threshold]
    if 0.0 not in enc_kept:
        enc_kept = [0.0] + enc_kept
    enc_r, enc_p = recall_precision(enc_kept)

    return {
        "manifest": dict(
            n_rotations=n_rotations,
            train_per_class=train_per_class,
            samples_per_cell=samples_per_cell,
            n_candidates=n_candidates,
            threshold=threshold,
            encoder_epochs=encoder_epochs,
            seed=seed,
            grid_size=grid_size,
            n_train=B,
            n_ood=ox.shape[0],
        ),
        "results": {
            "v1_pixel_cosine": {
                "scores": pixel_scores,
                "kept": pixel_kept,
                "recall": pixel_r,
                "precision": pixel_p,
            },
            "approach2_encoder_invariance": {
                "scores": inv_scores,
                "kept": inv_kept,
                "recall": inv_r,
                "precision": inv_p,
            },
            "approach3_encoder_enumerative": {
                "scores": enc_scores,
                "kept": enc_kept,
                "recall": enc_r,
                "precision": enc_p,
            },
        },
    }


@app.local_entrypoint()
def main(
    n_rotations: int = 8,
    train_per_class: int = 3,
    samples_per_cell: int = 30,
    n_candidates: int = 24,
    threshold: float = 0.5,
    encoder_epochs: int = 500,
    seed: int = 20260609,
    grid_size: int = 16,
    out: str = "artifacts/neural_group_generator/rotated_mnist_v1.json",
) -> None:
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = run_rotated_mnist.remote(dict(
        n_rotations=n_rotations,
        train_per_class=train_per_class,
        samples_per_cell=samples_per_cell,
        n_candidates=n_candidates,
        threshold=threshold,
        encoder_epochs=encoder_epochs,
        seed=seed,
        grid_size=grid_size,
    ))
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True))
    rs = result["results"]
    print(f"\nRotated MNIST result ({result['manifest']['n_train']} train, {result['manifest']['n_ood']} ood):")
    print(f"  v1 pixel cosine:           recall={rs['v1_pixel_cosine']['recall']:.3f}  precision={rs['v1_pixel_cosine']['precision']:.3f}  kept={len(rs['v1_pixel_cosine']['kept'])}")
    print(f"  Approach 2 enc invariance: recall={rs['approach2_encoder_invariance']['recall']:.3f}  precision={rs['approach2_encoder_invariance']['precision']:.3f}  kept={len(rs['approach2_encoder_invariance']['kept'])}")
    print(f"  Approach 3 enc enumerative: recall={rs['approach3_encoder_enumerative']['recall']:.3f}  precision={rs['approach3_encoder_enumerative']['precision']:.3f}  kept={len(rs['approach3_encoder_enumerative']['kept'])}")
