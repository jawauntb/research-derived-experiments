#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Capacity-bottlenecked test of the Reward-Deformation Law.

The first exponent test (ratedistortion_test.py) failed because nothing enforced
a capacity budget, so the network had no pressure to *trade* resolution. Here we
add the derivation's load-bearing assumptions:

  1. HARD CAPACITY: the population state is projected onto a fixed-norm sphere
     each step (bounded manifold => finite total code length => finite integral of
     the metric; steepening the code near the reward must be paid for elsewhere).
  2. FINITE-SNR CHANNEL: fixed-variance Gaussian noise is added before decoding,
     so decoding error at x depends on local resolution (Fisher info) and
     resolution actually matters.

Under these, value-weighted rate-distortion predicts the induced metric obeys
sqrt(det g) ~ w^{d/(d+2)} -> area-density exponent 1/2 (d=2). We measure it.

Run:  python experiments/grid_cell_weakness/capacity_bottleneck.py --seeds 3 --steps 2500
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import core
from ratedistortion_test import area_density_and_stretch, reward_field, loglog_slope


def train_bottleneck(seed, *, reward_xy, A=6.0, sigma=0.12, noise_std=0.15,
                     Ng=96, Np=100, sig=0.10, T=20, steps=2500, batch=128,
                     lr=1e-3, weight_decay=1e-4):
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    side = int(round(math.sqrt(Np)))
    centers = core.build_place_cells(side)

    class Bottleneck(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Linear(Np, Ng)
            self.rnn = nn.RNNCell(2, Ng, nonlinearity="relu")
            self.dec = nn.Linear(Ng, Np)

        def forward(self, vel, p0, noise):
            h = self.enc(p0)
            gs = []
            for t in range(vel.shape[1]):
                h = self.rnn(vel[:, t], h)
                h = h / (h.norm(dim=-1, keepdim=True) + 1e-6)   # unit sphere: fixed capacity
                gs.append(h)
            G = torch.stack(gs, 1)                               # clean code (geometry)
            Gn = G + noise * torch.randn_like(G)                 # finite-SNR channel
            return self.dec(Gn), G

    model = Bottleneck()
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    def batch_data():
        vels, poss = core.gen_trajectories(batch, T, rng)
        p0 = poss[:, 0] - vels[:, 0]
        tgt = core.place_code(poss.reshape(-1, 2), centers, sig).reshape(batch, T, Np)
        p0c = core.place_code(p0, centers, sig)
        d2 = ((poss.reshape(-1, 2) - np.array(reward_xy)) ** 2).sum(1)
        w = 1.0 + A * np.exp(-d2 / (2 * sigma ** 2))
        w = w / w.mean()
        return (torch.tensor(vels, dtype=torch.float32),
                torch.tensor(p0c, dtype=torch.float32),
                torch.tensor(tgt, dtype=torch.float32),
                torch.tensor(w, dtype=torch.float32))

    for _ in range(steps):
        vel, p0c, tgt, wv = batch_data()
        logits, _ = model(vel, p0c, noise_std)
        logp = torch.log_softmax(logits, -1).reshape(-1, Np)
        kl = (tgt.reshape(-1, Np) * (torch.log(tgt.reshape(-1, Np) + 1e-9) - logp)).sum(-1)
        loss = (wv * kl).mean()
        opt.zero_grad(); loss.backward(); opt.step()

    # extract clean population code on a spatial grid
    model.eval()
    with torch.no_grad():
        vels, poss = core.gen_trajectories(512, T, rng)
        p0 = poss[:, 0] - vels[:, 0]; p0c = core.place_code(p0, centers, sig)
        _, G = model(torch.tensor(vels, dtype=torch.float32),
                     torch.tensor(p0c, dtype=torch.float32), 0.0)
        G = G.reshape(-1, Ng).numpy(); flat = poss.reshape(-1, 2)
    ms = side
    b = np.clip((flat * ms).astype(int), 0, ms - 1); bid = b[:, 0] * ms + b[:, 1]
    pop = np.zeros((ms * ms, Ng)); cnt = np.zeros(ms * ms)
    for k, g in zip(bid, G):
        pop[k] += g; cnt[k] += 1
    ne = cnt > 0; pop[ne] /= cnt[ne, None]; pop[~ne] = pop[ne].mean(0) if ne.any() else 0.0
    return pop, ms, float(ne.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--steps", type=int, default=2500)
    ap.add_argument("--A", type=float, default=6.0)
    ap.add_argument("--sigma", type=float, default=0.12)
    ap.add_argument("--noise-std", type=float, default=0.15)
    ap.add_argument("--reward-xy", type=float, nargs=2, default=[0.5, 0.5])
    ap.add_argument("--base-seed", type=int, default=20260701)
    ap.add_argument("--out", default="artifacts/grid_cell_weakness/capacity_bottleneck.json")
    args = ap.parse_args()

    predicted_area, predicted_stretch = 0.5, 0.25
    rows = []
    for k in range(args.seeds):
        seed = args.base_seed + 100 * k
        pop, side, cov = train_bottleneck(seed, reward_xy=tuple(args.reward_xy), A=args.A,
                                          sigma=args.sigma, noise_std=args.noise_std, steps=args.steps)
        area, stretch = area_density_and_stretch(pop, side)
        w = reward_field(side, args.reward_xy, args.A, args.sigma)
        a_slope, a_r2, n = loglog_slope(w.ravel(), area.ravel())
        s_slope, s_r2, _ = loglog_slope(w.ravel(), stretch.ravel())
        rows.append(dict(seed=seed, coverage=cov, area_exponent=a_slope, area_r2=a_r2,
                         stretch_exponent=s_slope, stretch_r2=s_r2, n_bins=n))
        print(f"[bottleneck] seed={seed} cov={cov:.2f}  area alpha={a_slope:+.3f} (R2={a_r2:.2f}) "
              f"stretch alpha={s_slope:+.3f} (R2={s_r2:.2f})")

    def mean(key):
        vals = [x[key] for x in rows if np.isfinite(x[key])]
        return float(np.mean(vals)) if vals else float("nan")

    summary = dict(
        predicted_area_exponent=predicted_area, predicted_stretch_exponent=predicted_stretch,
        measured_area_exponent=mean("area_exponent"), measured_stretch_exponent=mean("stretch_exponent"),
        mean_area_r2=mean("area_r2"), mean_stretch_r2=mean("stretch_r2"),
        noise_std=args.noise_std, capacity="unit-sphere projection",
    )
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(kind="capacity-bottlenecked reward-deformation exponent test",
                                    summary=summary, rows=rows), indent=2, default=float) + "\n")
    print(f"\n[bottleneck] PREDICTED area exponent 0.500 ; MEASURED = {summary['measured_area_exponent']:+.3f} "
          f"(R2={summary['mean_area_r2']:.2f})")
    print(f"[bottleneck] PREDICTED stretch exponent 0.250 ; MEASURED = {summary['measured_stretch_exponent']:+.3f}")
    print(f"[bottleneck] wrote {out}")


if __name__ == "__main__":
    main()
