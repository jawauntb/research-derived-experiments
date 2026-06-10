#!/usr/bin/env python3
"""Top-K=8 ablation for the Learning the Group synthetic-stroke benchmark.

Re-runs the v1 enumerative `infer_rotation_group_from_training` procedure
across many random splits, this time recording per-angle scores so we can
score recall/precision under BOTH the threshold-based selection rule and
the top-K = 8 rule.

Question: was the 89.7% recall / 71.3% precision result on synthetic
strokes also a procedural artifact of threshold-based selection, or
does it survive under top-K=8?
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from statistics import mean

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from experiments.rotation_weakness.dataset import (
    make_partial_rotation_split,
    materialize_split,
    rotate_image,
    rotation_group_elements,
    to_tensors,
)


def angle_match(a, b, tol=7.5):
    d = abs(a - b)
    d = min(d, 360 - d)
    return d < tol


def cos(a, b):
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    return 0.0 if na == 0 or nb == 0 else float(np.dot(a, b) / (na * nb))


def score_angles(train_x, train_y, n_candidates):
    B = train_x.shape[0]
    train_feats = [train_x[i, 0].numpy().reshape(-1).astype(np.float32) for i in range(B)]
    labels = train_y.tolist()
    angles = [k * (360.0 / n_candidates) for k in range(n_candidates)]
    scores = {}
    for theta in angles:
        sims = []
        for i in range(B):
            r = rotate_image(train_x[i, 0].numpy(), theta).reshape(-1).astype(np.float32)
            same = [j for j in range(B) if labels[j] == labels[i]]
            sims.append(max(cos(r, train_feats[j]) for j in same))
        scores[theta] = float(np.mean(sims))
    return scores


def threshold_metrics(scores, oracle, thr=0.5):
    kept = [a for a, s in scores.items() if s >= thr]
    if 0.0 not in kept:
        kept = [0.0] + kept
    tp_r = sum(1 for o in oracle if any(angle_match(o, k) for k in kept))
    tp_p = sum(1 for k in kept if any(angle_match(o, k) for o in oracle))
    return len(kept), tp_r / len(oracle), tp_p / max(1, len(kept))


def topk_metrics(scores, oracle, K=8):
    sorted_a = sorted(scores.items(), key=lambda r: -r[1])
    kept = [a for a, _ in sorted_a[:K]]
    if 0.0 not in kept:
        kept = [0.0] + kept[: K - 1]
    tp_r = sum(1 for o in oracle if any(angle_match(o, k) for k in kept))
    tp_p = sum(1 for k in kept if any(angle_match(o, k) for o in oracle))
    return len(kept), tp_r / len(oracle), tp_p / max(1, len(kept))


def main() -> int:
    n_rotations = 8
    train_per_class = 3
    samples_per_class_rotation = 8
    n_candidates = 24
    n_trials = 64
    base_seed = 20260609

    rng = random.Random(base_seed)
    oracle = set(rotation_group_elements(n_rotations))

    rows = []
    for _ in range(n_trials):
        seed = rng.randrange(0, 2**31 - 1)
        split = make_partial_rotation_split(
            n_rotations=n_rotations, train_per_class=train_per_class, seed=seed
        )
        train, _ = materialize_split(
            split, samples_per_class_rotation=samples_per_class_rotation, seed=seed
        )
        tx, ty = to_tensors(train)
        scores = score_angles(tx, ty, n_candidates)
        thr_kept, thr_r, thr_p = threshold_metrics(scores, oracle, thr=0.5)
        topk_kept, topk_r, topk_p = topk_metrics(scores, oracle, K=8)
        rows.append({
            "seed": seed,
            "thr_kept": thr_kept, "thr_recall": thr_r, "thr_precision": thr_p,
            "topk_kept": topk_kept, "topk_recall": topk_r, "topk_precision": topk_p,
        })

    summary = {
        "n_trials": n_trials,
        "threshold_0.5": {
            "mean_kept": mean(r["thr_kept"] for r in rows),
            "mean_recall": mean(r["thr_recall"] for r in rows),
            "mean_precision": mean(r["thr_precision"] for r in rows),
        },
        "topk_8": {
            "mean_kept": mean(r["topk_kept"] for r in rows),
            "mean_recall": mean(r["topk_recall"] for r in rows),
            "mean_precision": mean(r["topk_precision"] for r in rows),
        },
    }
    out_path = ROOT / "artifacts" / "learned_symmetry" / "topk_stroke_ablation_v1.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, sort_keys=True))

    def f1(r, p):
        return 2 * r * p / max(1e-9, r + p)
    print(f"n_trials = {n_trials}, n_candidates = {n_candidates}, K_oracle = 8")
    print()
    print(f"{'selection':<15} {'kept':>6} {'recall':>8} {'precision':>10} {'F1':>6}")
    for name, key in [("threshold τ=0.5", "threshold_0.5"), ("top-K=8", "topk_8")]:
        s = summary[key]
        print(f"{name:<15} {s['mean_kept']:>6.2f} {s['mean_recall']:>8.4f} {s['mean_precision']:>10.4f} {f1(s['mean_recall'], s['mean_precision']):>6.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
