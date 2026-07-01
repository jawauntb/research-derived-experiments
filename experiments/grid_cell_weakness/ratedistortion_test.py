#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Test the parameter-free prediction of the Reward-Deformation Law.

notes/reward_deformation_ratedistortion.md derives, from value-weighted
rate-distortion under a capacity constraint, that the induced metric obeys

    rho(x) = sqrt(det g(x)) ∝ w(x)^{d/(d+2)},

so in the d=2 arena the **area density** exponent is 1/2 and the per-axis
stretch exponent is 1/4. This script trains a reward-conditioned path-integration
RNN, extracts the population code r(x) on a spatial grid, computes the local 2-D
Jacobian metric, and regresses log(metric) on log(w) to measure the exponent —
the program's first *out-of-sample* geometric prediction (Kepler -> Newton).

Run:  python experiments/grid_cell_weakness/ratedistortion_test.py --seeds 2 --steps 2000
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import core
import reward_deformation as rd


def area_density_and_stretch(pop: np.ndarray, side: int):
    """Return per-bin (sqrt(det g), per-axis stretch) via a 2-D finite-difference Jacobian."""
    grid = pop.reshape(side, side, -1)
    dx = 1.0 / (side - 1)
    area = np.full((side, side), np.nan)
    stretch = np.full((side, side), np.nan)
    for i in range(1, side - 1):
        for j in range(1, side - 1):
            du = (grid[i + 1, j] - grid[i - 1, j]) / (2 * dx)   # dr/dx1  (N,)
            dv = (grid[i, j + 1] - grid[i, j - 1]) / (2 * dx)   # dr/dx2  (N,)
            J = np.stack([du, dv], axis=1)                      # (N,2)
            g = J.T @ J                                         # (2,2)
            det = max(0.0, float(g[0, 0] * g[1, 1] - g[0, 1] * g[1, 0]))
            area[i, j] = math.sqrt(det)
            stretch[i, j] = 0.5 * (np.linalg.norm(du) + np.linalg.norm(dv))
    return area, stretch


def reward_field(side: int, xy, A: float, sigma: float) -> np.ndarray:
    xs = np.linspace(0, 1, side)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    d2 = (X - xy[0]) ** 2 + (Y - xy[1]) ** 2
    return 1.0 + A * np.exp(-d2 / (2 * sigma ** 2))


def loglog_slope(w, rho):
    m = np.isfinite(w) & np.isfinite(rho) & (w > 0) & (rho > 0)
    lw, lr = np.log(w[m]), np.log(rho[m])
    if lw.size < 8 or lw.std() < 1e-6:
        return float("nan"), float("nan"), int(m.sum())
    A = np.vstack([lw, np.ones_like(lw)]).T
    slope, intercept = np.linalg.lstsq(A, lr, rcond=None)[0]
    pred = A @ [slope, intercept]
    ss_res = ((lr - pred) ** 2).sum()
    ss_tot = ((lr - lr.mean()) ** 2).sum() or 1.0
    return float(slope), float(1 - ss_res / ss_tot), int(m.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--A", type=float, default=6.0)
    ap.add_argument("--sigma", type=float, default=0.12)
    ap.add_argument("--reward-xy", type=float, nargs=2, default=[0.5, 0.5])
    ap.add_argument("--base-seed", type=int, default=20260701)
    ap.add_argument("--out", default="artifacts/grid_cell_weakness/ratedistortion.json")
    args = ap.parse_args()

    predicted_area, predicted_stretch = 0.5, 0.25  # d/(d+2), 1/(d+2) for d=2
    rows = []
    for k in range(args.seeds):
        seed = args.base_seed + 100 * k
        r = rd.train(seed, reward_xy=tuple(args.reward_xy), reward_strength=args.A,
                     reward_width=args.sigma, steps=args.steps)
        side = r["side"]
        area, stretch = area_density_and_stretch(r["pop"], side)
        w = reward_field(side, args.reward_xy, args.A, args.sigma)
        a_slope, a_r2, n = loglog_slope(w.ravel(), area.ravel())
        s_slope, s_r2, _ = loglog_slope(w.ravel(), stretch.ravel())
        rows.append(dict(seed=seed, area_exponent=a_slope, area_r2=a_r2,
                         stretch_exponent=s_slope, stretch_r2=s_r2, n_bins=n))
        print(f"[rd-test] seed={seed}  area alpha={a_slope:+.3f} (R2={a_r2:.2f}) "
              f"stretch alpha={s_slope:+.3f} (R2={s_r2:.2f})  n={n}")

    def mean(key):
        vals = [x[key] for x in rows if np.isfinite(x[key])]
        return float(np.mean(vals)) if vals else float("nan")

    summary = dict(
        predicted_area_exponent=predicted_area,
        predicted_stretch_exponent=predicted_stretch,
        measured_area_exponent=mean("area_exponent"),
        measured_stretch_exponent=mean("stretch_exponent"),
        mean_area_r2=mean("area_r2"),
        mean_stretch_r2=mean("stretch_r2"),
    )
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(kind="reward-deformation rate-distortion exponent test",
                                    predicted={"area": predicted_area, "stretch": predicted_stretch},
                                    summary=summary, rows=rows), indent=2, default=float) + "\n")
    print(f"\n[rd-test] PREDICTED area exponent 1/2 = 0.500 ; MEASURED = {summary['measured_area_exponent']:+.3f}")
    print(f"[rd-test] PREDICTED stretch exponent 1/4 = 0.250 ; MEASURED = {summary['measured_stretch_exponent']:+.3f}")
    print(f"[rd-test] wrote {out}")


if __name__ == "__main__":
    main()
