#!/usr/bin/env python3
"""Modal entrypoint for the causal validation sweep.

Each shard runs N base configs × 4 augmentation regimes (none, oracle_aug,
learned_aug, random_aug) on the rotated-stroke partial-orbit task. Returns
per-(base, regime) OOD accuracy so we can compute paired per-model deltas.
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
)

app = modal.App(name="research-derived-causal-validation")


@app.function(image=IMAGE, timeout=3600, cpu=4)
def shard_sweep(arg: dict[str, Any]) -> dict[str, Any]:
    import math
    import random

    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from scipy.ndimage import rotate as scipy_rotate

    n_base = arg["n_base"]
    n_rotations = arg["n_rotations"]
    train_per_class = arg["train_per_class"]
    epochs = arg["epochs"]
    candidates = arg["candidates"]
    threshold = arg["threshold"]
    base_seed = arg["base_seed"]
    shard_id = arg["shard_id"]

    GRID = 16
    N_CLASSES = 8
    STROKES = [
        [(0.1, 0.5, 0.9, 0.5)],
        [(0.5, 0.1, 0.5, 0.9)],
        [(0.1, 0.1, 0.9, 0.9)],
        [(0.1, 0.9, 0.9, 0.1)],
        [(0.2, 0.5, 0.5, 0.2), (0.5, 0.2, 0.8, 0.5)],
        [(0.2, 0.5, 0.5, 0.8), (0.5, 0.8, 0.8, 0.5)],
        [(0.2, 0.2, 0.8, 0.2), (0.2, 0.2, 0.2, 0.8)],
        [(0.5, 0.2, 0.8, 0.5), (0.8, 0.5, 0.5, 0.8), (0.5, 0.8, 0.2, 0.5), (0.2, 0.5, 0.5, 0.2)],
    ]

    def render(label):
        img = np.zeros((GRID, GRID), dtype=np.float32)
        for x1, y1, x2, y2 in STROKES[label]:
            px1, py1 = int(round(x1 * (GRID - 1))), int(round(y1 * (GRID - 1)))
            px2, py2 = int(round(x2 * (GRID - 1))), int(round(y2 * (GRID - 1)))
            steps = max(abs(px2 - px1), abs(py2 - py1)) + 1
            for s in range(steps + 1):
                t = s / max(1, steps)
                x = int(round(px1 + t * (px2 - px1)))
                y = int(round(py1 + t * (py2 - py1)))
                if 0 <= x < GRID and 0 <= y < GRID:
                    img[y, x] = 1.0
        return img

    def rot(img, deg):
        r = scipy_rotate(img, angle=deg, reshape=False, order=1, mode="constant", cval=0.0)
        return np.clip(r, 0, 1).astype(np.float32)

    def make_split(rng):
        train, ood = {}, {}
        for label in range(N_CLASSES):
            rots = list(range(n_rotations))
            rng.shuffle(rots)
            train[label] = tuple(sorted(rots[:train_per_class]))
            ood[label] = tuple(sorted(rots[train_per_class:]))
        return train, ood

    def materialize(train_d, ood_d, *, spcr, seed):
        rng_np = np.random.RandomState(seed)
        tx, ty, ox, oy = [], [], [], []
        for label, rs in train_d.items():
            base = render(label)
            for r in rs:
                deg = r * (360.0 / n_rotations)
                rotated = rot(base, deg)
                for _ in range(spcr):
                    noisy = np.clip(rotated + rng_np.normal(0, 0.05, rotated.shape).astype(np.float32), 0, 1)
                    tx.append(noisy); ty.append(label)
        for label, rs in ood_d.items():
            base = render(label)
            for r in rs:
                deg = r * (360.0 / n_rotations)
                rotated = rot(base, deg)
                for _ in range(spcr):
                    noisy = np.clip(rotated + rng_np.normal(0, 0.05, rotated.shape).astype(np.float32), 0, 1)
                    ox.append(noisy); oy.append(label)
        return (
            torch.from_numpy(np.stack(tx)).unsqueeze(1),
            torch.tensor(ty, dtype=torch.long),
            torch.from_numpy(np.stack(ox)).unsqueeze(1),
            torch.tensor(oy, dtype=torch.long),
        )

    def rotate_batch(images, deg):
        if deg == 0.0:
            return images
        out = torch.zeros_like(images)
        for i in range(images.shape[0]):
            out[i, 0] = torch.from_numpy(rot(images[i, 0].cpu().numpy(), deg))
        return out

    def augment_with(images, labels, angles):
        chunks_x = [images]; chunks_y = [labels]
        for deg in angles:
            if deg == 0.0:
                continue
            chunks_x.append(rotate_batch(images, deg)); chunks_y.append(labels)
        return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)

    def make_model(arch, hidden, depth, init_scale):
        if arch == "cnn":
            layers = []
            in_ch = 1
            for _ in range(depth):
                conv = nn.Conv2d(in_ch, hidden, kernel_size=3, padding=1)
                with torch.no_grad():
                    conv.weight.mul_(init_scale)
                layers.extend([conv, nn.ReLU(), nn.MaxPool2d(2)])
                in_ch = hidden
            grid = max(1, GRID // (2 ** depth))
            head = nn.Linear(grid * grid * hidden, N_CLASSES)
            with torch.no_grad():
                head.weight.mul_(init_scale)
            return nn.Sequential(*layers, nn.Flatten(), head)
        layers = []
        in_dim = GRID * GRID
        for _ in range(depth):
            lin = nn.Linear(in_dim, hidden)
            with torch.no_grad():
                lin.weight.mul_(init_scale)
            layers.extend([lin, nn.ReLU()])
            in_dim = hidden
        head = nn.Linear(in_dim, N_CLASSES)
        with torch.no_grad():
            head.weight.mul_(init_scale)
        return nn.Sequential(nn.Flatten(), *layers, head)

    def infer_group(train_x, train_y, n_cand, thr):
        B = train_x.shape[0]
        feats = [train_x[i].cpu().numpy().reshape(-1).astype(np.float32) for i in range(B)]
        labels = train_y.tolist()

        def cos(a, b):
            na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
            if na == 0 or nb == 0: return 0.0
            return float(np.dot(a, b) / (na * nb))

        angles = [k * (360.0 / n_cand) for k in range(n_cand)]
        kept = [0.0]
        for theta in angles:
            if theta == 0.0:
                continue
            ms = []
            for i in range(B):
                r_im = rot(train_x[i, 0].cpu().numpy(), theta).reshape(-1).astype(np.float32)
                same = [j for j in range(B) if labels[j] == labels[i]]
                ms.append(max(cos(r_im, feats[j]) for j in same) if same else 0.0)
            if float(np.mean(ms)) >= thr:
                kept.append(theta)
        return kept

    rng = random.Random(base_seed + shard_id * 9999)
    out = []
    for _ in range(n_base):
        cfg = dict(
            seed=rng.randrange(0, 2**31 - 1),
            architecture=rng.choice(["cnn", "mlp"]),
            hidden_width=rng.choice([16, 32, 64]),
            depth=rng.choice([1, 2]),
            init_scale=rng.choice([0.5, 1.0, 1.5]),
            learning_rate=rng.choice([1e-3, 3e-3, 1e-2]),
            weight_decay=rng.choice([0.0, 1e-4]),
            optimizer=rng.choice(["adam", "sgd"]),
        )
        split_seed = rng.randrange(0, 2**31 - 1)
        train_d, ood_d = make_split(random.Random(split_seed))
        tx, ty, ox, oy = materialize(train_d, ood_d, spcr=8, seed=cfg["seed"])

        learned_angles = infer_group(tx, ty, candidates, threshold)
        oracle_angles = [k * (360.0 / n_rotations) for k in range(n_rotations)]
        rng_np = np.random.RandomState(cfg["seed"])
        rand_pool = list(range(1, candidates))
        rng_np.shuffle(rand_pool)
        random_angles = [0.0] + [k * (360.0 / candidates) for k in rand_pool[: max(0, len(learned_angles) - 1)]]

        regimes = {
            "none": [],
            "oracle_aug": [a for a in oracle_angles if a != 0.0],
            "learned_aug": [a for a in learned_angles if a != 0.0],
            "random_aug": [a for a in random_angles if a != 0.0],
        }

        for name, angles in regimes.items():
            ax, ay = augment_with(tx, ty, angles)
            torch.manual_seed(cfg["seed"])
            model = make_model(cfg["architecture"], cfg["hidden_width"], cfg["depth"], cfg["init_scale"])
            opt = (
                torch.optim.Adam(model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"])
                if cfg["optimizer"] == "adam"
                else torch.optim.SGD(model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"], momentum=0.9)
            )
            final_loss = math.inf
            for _ in range(epochs):
                model.train(); opt.zero_grad()
                loss = F.cross_entropy(model(ax), ay)
                loss.backward(); opt.step()
                final_loss = float(loss.item())

            with torch.no_grad():
                ta = float((model(tx).argmax(-1) == ty).float().mean().item())
                oa = float((model(ox).argmax(-1) == oy).float().mean().item())
            out.append(dict(
                base_seed=split_seed,
                config=cfg,
                regime=name,
                train_accuracy=ta,
                ood_accuracy=oa,
                final_train_loss=final_loss,
                learned_group_size=len(learned_angles),
            ))
    return {"shard_id": shard_id, "rows": out}


@app.local_entrypoint()
def main(
    n_shards: int = 8,
    n_base_per_shard: int = 12,
    n_rotations: int = 8,
    train_per_class: int = 3,
    epochs: int = 250,
    candidates: int = 24,
    threshold: float = 0.5,
    base_seed: int = 20260609,
    out: str = "artifacts/learned_symmetry/causal_v1.json",
) -> None:
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        dict(
            n_base=n_base_per_shard,
            n_rotations=n_rotations,
            train_per_class=train_per_class,
            epochs=epochs,
            candidates=candidates,
            threshold=threshold,
            base_seed=base_seed,
            shard_id=i,
        )
        for i in range(n_shards)
    ]
    results = list(shard_sweep.map(args))
    rows = []
    for r in results:
        rows.extend(r["rows"])
    out_path.write_text(json.dumps({
        "manifest": dict(
            n_shards=n_shards,
            n_base_per_shard=n_base_per_shard,
            n_rotations=n_rotations,
            train_per_class=train_per_class,
            epochs=epochs,
            candidates=candidates,
            threshold=threshold,
            base_seed=base_seed,
            total_units=len(rows) // 4,
        ),
        "rows": rows,
    }, indent=2, sort_keys=True))
    print(f"Wrote {len(rows)} rows ({len(rows) // 4} causal units × 4 regimes)")
