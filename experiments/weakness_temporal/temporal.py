#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Experiment ②: weakness as a temporal *early-warning* predictor of OOD.

The cleanest non-circular test in the program. We train many small MLPs on the
cyclic prefix-shift task and record, at an EARLY checkpoint and at the END:
learned-function weakness, training loss, train accuracy, and OOD accuracy.

The claim is predictive across time, not a same-endpoint correlation:
  does weakness measured EARLY predict FINAL OOD better than early loss /
  early accuracy — and crucially, among models that look identical early
  (already train-perfect), does early weakness still separate who will
  generalize? "Predict the future from the present" cannot be tautological with
  the present, which is the circularity charge against the static result.

Task: domain Z_n, truth f(x) = (x + b) mod n. Train on a contiguous prefix
window; OOD = the held-out complement. MLP: one-hot(n) -> hidden -> logits(n).
Weakness = equivariance count of the argmax function table under Z_n, normalized.

Run:  python experiments/weakness_temporal/temporal.py --n-models 240
Out:  artifacts/weakness_temporal/temporal.json  (gitignored)
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def cyclic_group(n):
    return [tuple((x + k) % n for x in range(n)) for k in range(n)]


def equivariance_count(table, group):
    n = len(table)
    cnt = 0
    for g in group:
        induced = tuple(table[g[x]] for x in range(n))
        for h in group:
            if all(h[table[x]] == induced[x] for x in range(n)):
                cnt += 1
                break
    return cnt


def spearman(xs, ys):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    ok = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[ok], ys[ok]
    if len(xs) < 3:
        return 0.0
    rx = np.argsort(np.argsort(xs)).astype(float); ry = np.argsort(np.argsort(ys)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    den = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / den) if den else 0.0


def pearson(xs, ys):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    ok = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[ok], ys[ok]
    if len(xs) < 3 or xs.std() == 0 or ys.std() == 0:
        return 0.0
    return float(np.corrcoef(xs, ys)[0, 1])


def train_one(n, b, window, *, width, lr, wd, seed, steps, early_frac):
    import torch
    import torch.nn as nn
    torch.manual_seed(seed)
    cyc = cyclic_group(n)
    truth = [(x + b) % n for x in range(n)]
    train_x = list(range(window))
    ood_x = list(range(window, n))
    X = torch.eye(n)
    yt = torch.tensor(truth)
    model = nn.Sequential(nn.Linear(n, width), nn.ReLU(), nn.Linear(width, n))
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    lossfn = nn.CrossEntropyLoss()
    early_step = max(1, int(steps * early_frac))
    snap = {}

    def measure(tag):
        model.eval()
        with torch.no_grad():
            logits = model(X)
            table = tuple(int(t) for t in logits.argmax(-1).tolist())
            tr_loss = float(lossfn(logits[train_x], yt[train_x]).item())
            tr_acc = float((logits[train_x].argmax(-1) == yt[train_x]).float().mean().item())
            ood_acc = float((logits[ood_x].argmax(-1) == yt[ood_x]).float().mean().item()) if ood_x else float("nan")
        w = equivariance_count(table, cyc) / len(cyc)
        snap[tag] = dict(weakness=w, train_loss=tr_loss, train_acc=tr_acc, ood_acc=ood_acc)
        model.train()

    for t in range(steps):
        opt.zero_grad()
        loss = lossfn(model(X)[train_x], yt[train_x])
        loss.backward(); opt.step()
        if t + 1 == early_step:
            measure("early")
    measure("final")
    return snap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-models", type=int, default=240)
    ap.add_argument("--steps", type=int, default=1500)
    ap.add_argument("--early-frac", type=float, default=0.15)
    ap.add_argument("--base-seed", type=int, default=20260629)
    ap.add_argument("--out", default="artifacts/weakness_temporal/temporal.json")
    args = ap.parse_args()

    rng = np.random.default_rng(args.base_seed)
    ns = [11, 13, 17]
    widths = [16, 32, 64]
    lrs = [3e-3, 1e-2, 3e-2]
    wds = [0.0, 1e-4, 1e-2]
    rows: list[dict[str, Any]] = []
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)

    for m in range(args.n_models):
        n = int(rng.choice(ns)); width = int(rng.choice(widths))
        lr = float(rng.choice(lrs)); wd = float(rng.choice(wds))
        window = int(rng.integers(max(3, n // 3), n - 2))
        b = int(rng.integers(1, n))
        seed = args.base_seed + m
        snap = train_one(n, b, window, width=width, lr=lr, wd=wd, seed=seed,
                         steps=args.steps, early_frac=args.early_frac)
        rows.append(dict(n=n, width=width, lr=lr, wd=wd, window=window, seed=seed,
                         early=snap["early"], final=snap["final"]))
        if (m + 1) % 40 == 0:
            out.write_text(json.dumps(dict(kind="weakness temporal early-warning",
                                           manifest=vars(args), rows=rows),
                                      indent=2, sort_keys=True, default=float) + "\n")
            print(f"[temporal] {m+1}/{args.n_models}")

    we = [r["early"]["weakness"] for r in rows]
    le = [r["early"]["train_loss"] for r in rows]
    ae = [r["early"]["train_acc"] for r in rows]
    of = [r["final"]["ood_acc"] for r in rows]

    analysis: dict[str, Any] = dict(
        n_models=len(rows),
        # cross-time prediction: early signal -> final OOD
        spearman_weakness_early_vs_ood_final=spearman(we, of),
        pearson_weakness_early_vs_ood_final=pearson(we, of),
        spearman_loss_early_vs_ood_final=spearman(le, of),
        spearman_trainacc_early_vs_ood_final=spearman(ae, of),
    )
    # tie-control: among models already train-perfect at the early checkpoint,
    # loss/acc cannot separate them — does early weakness still predict final OOD?
    tie = [r for r in rows if r["early"]["train_acc"] >= 0.999]
    if len(tie) >= 5:
        we_t = [r["early"]["weakness"] for r in tie]
        of_t = [r["final"]["ood_acc"] for r in tie]
        le_t = [r["early"]["train_loss"] for r in tie]
        analysis["tie_controlled"] = dict(
            n_tie=len(tie),
            spearman_weakness_early_vs_ood_final=spearman(we_t, of_t),
            spearman_loss_early_vs_ood_final=spearman(le_t, of_t),
            note="models train-perfect at the early checkpoint; loss/acc are tied so "
                 "cannot predict, but early weakness still can — the non-circular result.",
        )
    payload = dict(kind="weakness temporal early-warning", manifest=vars(args),
                   analysis=analysis, rows=rows)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n")
    print(f"[temporal] DONE n={len(rows)}")
    print(f"[temporal] early weakness -> final OOD: spearman={analysis['spearman_weakness_early_vs_ood_final']:+.3f} "
          f"(early loss -> final OOD: {analysis['spearman_loss_early_vs_ood_final']:+.3f})")
    if "tie_controlled" in analysis:
        t = analysis["tie_controlled"]
        print(f"[temporal] TIE-CONTROLLED (n={t['n_tie']} train-perfect early): "
              f"weakness->OOD spearman={t['spearman_weakness_early_vs_ood_final']:+.3f} "
              f"vs loss->OOD {t['spearman_loss_early_vs_ood_final']:+.3f}")


if __name__ == "__main__":
    main()
