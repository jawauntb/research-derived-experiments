#!/usr/bin/env python3
"""Cluttered rotated-MNIST sweep over resolution × background noise.

Tests the regime where pixel cosine should *finally* fail. We sweep:

  resolution ∈ {16, 28}  (downsampled vs full MNIST)
  noise σ ∈ {0.0, 0.10, 0.20, 0.30}  (Gaussian background added to each pixel)

For each combination, run the v1 pixel-cosine baseline, Approach 2
(encoder invariance), and Approach 3 (encoder enumerative). The
hypothesis: as noise grows, pixel cosine's recall should drop sharply
because rotating a digit slightly mis-aligns the (noisy) background,
while the encoder methods — trained to be class-invariant — should be
robust to background variation.

Run:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/neural_group_generator/modal_cluttered_mnist.py
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

app = modal.App(name="research-derived-cluttered-mnist")


@app.function(image=IMAGE, timeout=3600, cpu=4)
def run_single(arg: dict[str, Any]) -> dict[str, Any]:
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
    encoder_epochs = arg["encoder_epochs"]
    seed = arg["seed"]
    grid_size = arg["grid_size"]
    noise_sigma = arg["noise_sigma"]

    py_rng = random.Random(seed)
    rng_np = np.random.RandomState(seed)
    torch.manual_seed(seed)

    ds = load_dataset("ylecun/mnist", split="train")
    label_to_imgs: dict[int, list[np.ndarray]] = {i: [] for i in range(10)}
    for row in ds:
        img = row["image"]
        if not isinstance(img, Image.Image):
            img = Image.fromarray(np.array(img).astype(np.uint8))
        if grid_size != 28:
            img = img.resize((grid_size, grid_size), Image.BILINEAR)
        arr = np.array(img).astype(np.float32) / 255.0
        label_to_imgs[int(row["label"])].append(arr)

    n_needed_per_class = n_rotations * samples_per_cell
    for c in range(10):
        py_rng.shuffle(label_to_imgs[c])
        label_to_imgs[c] = label_to_imgs[c][: n_needed_per_class * 2]

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

    def add_noise(img: np.ndarray) -> np.ndarray:
        if noise_sigma <= 0:
            return img
        noise = rng_np.normal(0, noise_sigma, img.shape).astype(np.float32)
        return np.clip(img + noise, 0, 1).astype(np.float32)

    train_x, train_y, ood_x, ood_y = [], [], [], []
    for c in range(10):
        imgs = label_to_imgs[c]
        cursor = 0
        for r in train_rots[c]:
            deg = r * (360.0 / n_rotations)
            for _ in range(samples_per_cell):
                rotated = rot_arr(imgs[cursor], deg)
                rotated = add_noise(rotated)
                train_x.append(rotated)
                train_y.append(c)
                cursor += 1
        for r in ood_rots[c]:
            deg = r * (360.0 / n_rotations)
            for _ in range(samples_per_cell):
                if cursor >= len(imgs):
                    break
                rotated = rot_arr(imgs[cursor], deg)
                rotated = add_noise(rotated)
                ood_x.append(rotated)
                ood_y.append(c)
                cursor += 1

    tx = torch.from_numpy(np.stack(train_x)).unsqueeze(1)
    ty = torch.tensor(train_y, dtype=torch.long)

    B = tx.shape[0]
    candidate_angles = [k * (360.0 / n_candidates) for k in range(n_candidates)]
    oracle_set = set(k * (360.0 / n_rotations) for k in range(n_rotations))

    def angle_match(a: float, b: float, tol: float = 7.5) -> bool:
        d = abs(a - b)
        d = min(d, 360 - d)
        return d < tol

    def cos(a: np.ndarray, b: np.ndarray) -> float:
        na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        return 0.0 if na == 0 or nb == 0 else float(np.dot(a, b) / (na * nb))

    # --- Approach 1: pixel cosine ---
    train_feats_pixel = [tx[i, 0].cpu().numpy().reshape(-1) for i in range(B)]
    train_labels = ty.tolist()
    pixel_scores: dict[float, float] = {}
    for theta in candidate_angles:
        sims = []
        for i in range(B):
            r = rot_arr(tx[i, 0].cpu().numpy(), theta).reshape(-1)
            same = [j for j in range(B) if train_labels[j] == train_labels[i]]
            sims.append(max(cos(r, train_feats_pixel[j]) for j in same))
        pixel_scores[theta] = float(np.mean(sims))

    # --- Encoder ---
    class Encoder(nn.Module):
        def __init__(self):
            super().__init__()
            if grid_size >= 28:
                hidden_grid = 7
                self.body = nn.Sequential(
                    nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                    nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                    nn.Flatten(),
                )
            else:
                hidden_grid = grid_size // 4
                self.body = nn.Sequential(
                    nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                    nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
                    nn.Flatten(),
                )
            d = 32 * hidden_grid * hidden_grid
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
        exp_logits = torch.exp(logits) * (1 - torch.eye(B))
        log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True).clamp(min=1e-9))
        denom = mask_same.sum(dim=1).clamp(min=1)
        loss = -((mask_same * log_prob).sum(dim=1) / denom).mean()
        loss.backward(); opt.step()

    encoder.eval()

    # --- Approach 2: encoder invariance ---
    with torch.no_grad():
        z_base = encoder(tx)
    inv_scores = {}
    for theta in candidate_angles:
        rotated_imgs = torch.zeros_like(tx)
        for i in range(B):
            rotated_imgs[i, 0] = torch.from_numpy(rot_arr(tx[i, 0].cpu().numpy(), theta))
        with torch.no_grad():
            z_rot = encoder(rotated_imgs)
        inv_scores[theta] = float((z_base * z_rot).sum(dim=-1).mean().item())

    # --- Approach 3: encoder enumerative ---
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

    def best_metrics(scores: dict[float, float]) -> tuple[float, float, float, float]:
        """Return (best_threshold, kept, recall, precision) maximizing F1
        over a fine threshold grid."""
        thr_grid = [round(0.05 * k, 2) for k in range(1, 20)]
        best = (-1.0, 0.0, 0.0, 0.0, -1.0)  # (thr, kept_size, recall, precision, F1)
        for thr in thr_grid:
            kept = [a for a, s in scores.items() if s >= thr]
            if 0.0 not in kept:
                kept = [0.0] + kept
            tp_r = sum(1 for o in oracle_set if any(angle_match(o, k) for k in kept))
            tp_p = sum(1 for k in kept if any(angle_match(o, k) for o in oracle_set))
            r = tp_r / len(oracle_set)
            p = tp_p / max(1, len(kept))
            f1 = 2 * r * p / max(1e-9, r + p)
            if f1 > best[4]:
                best = (thr, len(kept), r, p, f1)
        return best

    return {
        "manifest": dict(
            grid_size=grid_size,
            noise_sigma=noise_sigma,
            n_train=B,
            train_per_class=train_per_class,
            samples_per_cell=samples_per_cell,
            n_candidates=n_candidates,
            encoder_epochs=encoder_epochs,
        ),
        "v1_pixel_cosine": {
            "best": best_metrics(pixel_scores),
            "scores": pixel_scores,
        },
        "approach2_encoder_invariance": {
            "best": best_metrics(inv_scores),
            "scores": inv_scores,
        },
        "approach3_encoder_enumerative": {
            "best": best_metrics(enc_scores),
            "scores": enc_scores,
        },
    }


@app.local_entrypoint()
def main(
    n_rotations: int = 8,
    train_per_class: int = 3,
    samples_per_cell: int = 24,
    n_candidates: int = 24,
    encoder_epochs: int = 500,
    seed: int = 20260609,
    out: str = "artifacts/neural_group_generator/cluttered_mnist_v1.json",
) -> None:
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sweep: list[dict[str, Any]] = []
    for grid_size in [16, 28]:
        for noise_sigma in [0.0, 0.10, 0.20, 0.30]:
            sweep.append(dict(
                n_rotations=n_rotations,
                train_per_class=train_per_class,
                samples_per_cell=samples_per_cell,
                n_candidates=n_candidates,
                encoder_epochs=encoder_epochs,
                seed=seed,
                grid_size=grid_size,
                noise_sigma=noise_sigma,
            ))

    results = list(run_single.map(sweep))

    out_path.write_text(json.dumps({
        "manifest": dict(
            n_rotations=n_rotations,
            train_per_class=train_per_class,
            samples_per_cell=samples_per_cell,
            n_candidates=n_candidates,
            encoder_epochs=encoder_epochs,
            seed=seed,
        ),
        "results": results,
    }, indent=2, sort_keys=True))

    print(f"\nCluttered MNIST sweep done ({len(results)} cells)")
    print(f"{'grid':>4} {'σ':>5} | {'pixel R':>8} {'pixel P':>8} | {'enc-inv R':>10} {'enc-inv P':>10} | {'enc-enum R':>11} {'enc-enum P':>11}")
    for r in results:
        m = r["manifest"]
        p = r["v1_pixel_cosine"]["best"]
        a2 = r["approach2_encoder_invariance"]["best"]
        a3 = r["approach3_encoder_enumerative"]["best"]
        print(f"{m['grid_size']:>4} {m['noise_sigma']:>5.2f} | {p[2]:>8.3f} {p[3]:>8.3f} | {a2[2]:>10.3f} {a2[3]:>10.3f} | {a3[2]:>11.3f} {a3[3]:>11.3f}")
