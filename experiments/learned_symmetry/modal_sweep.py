#!/usr/bin/env python3
"""Modal entrypoint for the learned-symmetry sweep.

Parallelizes across N shards. Each shard trains M models on the partial-orbit
rotated-stroke task, scores weakness under (i) oracle Z_n, (ii) data-inferred
group, (iii) random-group control, and returns artefacts.

Run:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/learned_symmetry/modal_sweep.py \\
        --n-shards 8 --models-per-shard 32 --epochs 250 \\
        --base-seed 20260609 \\
        --out artifacts/learned_symmetry/modal_sweep_v1.json
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

app = modal.App(name="research-derived-learned-symmetry")


@app.function(image=IMAGE, timeout=3600, cpu=4)
def shard_sweep(arg: dict[str, Any]) -> dict[str, Any]:
    models_per_shard = arg["models_per_shard"]
    n_rotations = arg["n_rotations"]
    train_per_class = arg["train_per_class"]
    base_seed = arg["base_seed"]
    epochs = arg["epochs"]
    candidates = arg["candidates"]
    threshold = arg["threshold"]
    shard_id = arg["shard_id"]

    import math
    import random

    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from scipy.ndimage import rotate as scipy_rotate

    # ----- dataset -----
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

    def render(label: int) -> np.ndarray:
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

    def rotate_img(img: np.ndarray, deg: float) -> np.ndarray:
        rotated = scipy_rotate(img, angle=deg, reshape=False, order=1, mode="constant", cval=0.0)
        return np.clip(rotated, 0.0, 1.0).astype(np.float32)

    def make_split(rng: random.Random):
        train, ood = {}, {}
        for label in range(N_CLASSES):
            rots = list(range(n_rotations))
            rng.shuffle(rots)
            train[label] = tuple(sorted(rots[:train_per_class]))
            ood[label] = tuple(sorted(rots[train_per_class:]))
        return train, ood

    def materialize(train_dict, ood_dict, *, spcr: int, seed: int):
        rng_np = np.random.RandomState(seed)
        train_x, train_y, train_r = [], [], []
        ood_x, ood_y = [], []
        for label, rots in train_dict.items():
            base = render(label)
            for r in rots:
                deg = r * (360.0 / n_rotations)
                rotated = rotate_img(base, deg)
                for _ in range(spcr):
                    noisy = np.clip(rotated + rng_np.normal(0, 0.05, rotated.shape).astype(np.float32), 0, 1)
                    train_x.append(noisy)
                    train_y.append(label)
                    train_r.append(r)
        for label, rots in ood_dict.items():
            base = render(label)
            for r in rots:
                deg = r * (360.0 / n_rotations)
                rotated = rotate_img(base, deg)
                for _ in range(spcr):
                    noisy = np.clip(rotated + rng_np.normal(0, 0.05, rotated.shape).astype(np.float32), 0, 1)
                    ood_x.append(noisy)
                    ood_y.append(label)
        tx = torch.from_numpy(np.stack(train_x)).unsqueeze(1)
        ty = torch.tensor(train_y, dtype=torch.long)
        ox = torch.from_numpy(np.stack(ood_x)).unsqueeze(1)
        oy = torch.tensor(ood_y, dtype=torch.long)
        return tx, ty, ox, oy

    def rotate_batch(images: torch.Tensor, deg: float) -> torch.Tensor:
        if deg == 0.0:
            return images
        out = torch.zeros_like(images)
        for i in range(images.shape[0]):
            r = rotate_img(images[i, 0].cpu().numpy(), deg)
            out[i, 0] = torch.from_numpy(r)
        return out

    def augment(images, labels, aug, strength, n_rot, rng):
        if aug == "full_rotation":
            chunks_x = [images]
            chunks_y = [labels]
            for k in range(1, n_rot):
                deg = k * (360.0 / n_rot)
                chunks_x.append(rotate_batch(images, deg))
                chunks_y.append(labels)
            return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)
        if aug == "none" or strength == 0:
            return images, labels
        if aug == "partial_rotation":
            angles = [k * (360.0 / n_rot) for k in range(1, n_rot)]
            chosen = rng.sample(angles, min(strength, len(angles)))
            chunks_x = [images]
            chunks_y = [labels]
            for deg in chosen:
                chunks_x.append(rotate_batch(images, deg))
                chunks_y.append(labels)
            return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)
        if aug == "wrong_permute":
            chunks_x = [images]
            chunks_y = [labels]
            for _ in range(strength):
                perm = torch.randperm(GRID * GRID)
                flat = images.flatten(start_dim=2)
                shuffled = flat[:, :, perm].reshape_as(images)
                chunks_x.append(shuffled)
                chunks_y.append(labels)
            return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)
        raise ValueError(aug)

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
        else:
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

    def accuracy(model, x, y):
        model.eval()
        with torch.no_grad():
            preds = model(x).argmax(dim=-1)
        return float((preds == y).float().mean().item())

    def group_invariance(model, eval_x, angles):
        model.eval()
        with torch.no_grad():
            base = model(eval_x).argmax(dim=-1)
        agree = 0
        total = 0
        for deg in angles:
            if deg == 0.0:
                continue
            r = rotate_batch(eval_x, deg)
            with torch.no_grad():
                rp = model(r).argmax(dim=-1)
            agree += int((rp == base).sum().item())
            total += int(rp.shape[0])
        return agree / max(1, total) if total > 0 else 0.0

    def infer_group(train_x, train_y, n_candidates, threshold):
        B = train_x.shape[0]
        feats = [train_x[i].cpu().numpy().reshape(-1).astype(np.float32) for i in range(B)]
        labels = train_y.tolist()

        def cos(a, b):
            na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
            if na == 0 or nb == 0:
                return 0.0
            return float(np.dot(a, b) / (na * nb))

        cand_angles = [k * (360.0 / n_candidates) for k in range(n_candidates)]
        scores = []
        for theta in cand_angles:
            match = []
            for i in range(B):
                rot = rotate_img(train_x[i, 0].cpu().numpy(), theta).reshape(-1).astype(np.float32)
                same = [j for j in range(B) if labels[j] == labels[i]]
                if not same:
                    match.append(0.0)
                    continue
                match.append(max(cos(rot, feats[j]) for j in same))
            scores.append(float(np.mean(match)))
        kept = [(cand_angles[i], scores[i]) for i in range(n_candidates) if scores[i] >= threshold]
        kept_angles = [a for a, _ in kept]
        if 0.0 not in kept_angles:
            kept_angles = [0.0] + kept_angles
        return kept_angles, scores

    def random_group(target_size, n_candidates, rng_np):
        cands = list(range(1, n_candidates))
        rng_np.shuffle(cands)
        chosen = [0] + cands[: max(0, target_size - 1)]
        return [k * (360.0 / n_candidates) for k in chosen]

    def sharpness(model, x, y):
        model.eval()
        params = [p for p in model.parameters() if p.requires_grad]
        v = [torch.randint(0, 2, p.shape).float() * 2 - 1 for p in params]
        model.zero_grad()
        loss = F.cross_entropy(model(x), y)
        grads = torch.autograd.grad(loss, params, create_graph=True)
        gv = sum((g * vi).sum() for g, vi in zip(grads, v))
        hv = torch.autograd.grad(gv, params, retain_graph=False)
        return float(sum((h * vi).sum().item() for h, vi in zip(hv, v)))

    def angle_match(a, b, tol=7.5):
        d = abs(a - b)
        d = min(d, 360.0 - d)
        return d < tol

    # ----- sweep -----
    rng = random.Random(base_seed + shard_id * 9999)
    out = []
    for _ in range(models_per_shard):
        arch = rng.choice(["cnn", "mlp"])
        aug = rng.choice(["none", "partial_rotation", "full_rotation", "wrong_permute"])
        strength = 0 if aug in ("none", "full_rotation") else rng.choice([2, 4, 6])
        cfg = dict(
            seed=rng.randrange(0, 2**31 - 1),
            architecture=arch,
            hidden_width=rng.choice([16, 32, 64]),
            depth=rng.choice([1, 2]),
            init_scale=rng.choice([0.5, 1.0, 1.5]),
            learning_rate=rng.choice([1e-3, 3e-3, 1e-2]),
            weight_decay=rng.choice([0.0, 1e-4]),
            optimizer=rng.choice(["adam", "sgd"]),
            augmentation=aug,
            augmentation_strength=strength,
        )
        seed = int(cfg["seed"])
        torch.manual_seed(seed)
        np.random.seed(seed)

        split_seed = rng.randrange(0, 2**31 - 1)
        train_d, ood_d = make_split(random.Random(split_seed))
        tx, ty, ox, oy = materialize(train_d, ood_d, spcr=8, seed=seed)

        ax, ay = augment(
            tx, ty, cfg["augmentation"], cfg["augmentation_strength"],
            n_rotations, random.Random(seed)
        )

        model = make_model(cfg["architecture"], cfg["hidden_width"], cfg["depth"], cfg["init_scale"])
        opt = (
            torch.optim.Adam(model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"])
            if cfg["optimizer"] == "adam"
            else torch.optim.SGD(model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"], momentum=0.9)
        )
        final_loss = math.inf
        for _ in range(epochs):
            model.train()
            opt.zero_grad()
            loss = F.cross_entropy(model(ax), ay)
            loss.backward()
            opt.step()
            final_loss = float(loss.item())

        train_acc = accuracy(model, tx, ty)
        ood_acc = accuracy(model, ox, oy)
        oracle_angles = [k * (360.0 / n_rotations) for k in range(n_rotations)]
        w_oracle = group_invariance(model, ox, oracle_angles)
        learned_angles, _ = infer_group(tx, ty, candidates, threshold)
        w_learned = group_invariance(model, ox, learned_angles)
        rng_np = np.random.RandomState(seed)
        rand_angles = random_group(len(learned_angles), candidates, rng_np)
        w_random = group_invariance(model, ox, rand_angles)
        param_l2 = math.sqrt(sum(float((p.detach() ** 2).sum().item()) for p in model.parameters()))
        sharp = sharpness(model, ax, ay)

        oracle_set = set(oracle_angles)
        tp = sum(1 for o in oracle_set if any(angle_match(o, learned) for learned in learned_angles))
        recall = tp / max(1, len(oracle_set))
        denom = len(learned_angles)
        tp_p = sum(1 for learned in learned_angles if any(angle_match(o, learned) for o in oracle_set))
        precision = (tp_p / denom) if denom > 0 else 0.0

        out.append(dict(
            config=cfg,
            ood_accuracy=float(ood_acc),
            train_accuracy=float(train_acc),
            parameter_l2=param_l2,
            sharpness_proxy=float(sharp),
            final_train_loss=final_loss,
            weakness_oracle=float(w_oracle),
            weakness_learned=float(w_learned),
            weakness_random=float(w_random),
            learned_group_size=len(learned_angles),
            learned_group_recall=float(recall),
            learned_group_precision=float(precision),
        ))
    return {"shard_id": shard_id, "artifacts": out}


@app.local_entrypoint()
def main(
    n_shards: int = 8,
    models_per_shard: int = 32,
    n_rotations: int = 8,
    train_per_class: int = 3,
    epochs: int = 250,
    candidates: int = 24,
    threshold: float = 0.5,
    base_seed: int = 20260609,
    out: str = "artifacts/learned_symmetry/modal_sweep_v1.json",
) -> None:
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        dict(
            models_per_shard=models_per_shard,
            n_rotations=n_rotations,
            train_per_class=train_per_class,
            base_seed=base_seed,
            epochs=epochs,
            candidates=candidates,
            threshold=threshold,
            shard_id=i,
        )
        for i in range(n_shards)
    ]
    results = list(shard_sweep.map(args))
    arts = []
    for r in results:
        arts.extend(r["artifacts"])
    payload = {
        "manifest": dict(
            n_shards=n_shards,
            models_per_shard=models_per_shard,
            n_rotations=n_rotations,
            train_per_class=train_per_class,
            epochs=epochs,
            candidates=candidates,
            threshold=threshold,
            base_seed=base_seed,
            total_models=len(arts),
        ),
        "artifacts": arts,
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Wrote {len(arts)} artifacts to {out_path}")
