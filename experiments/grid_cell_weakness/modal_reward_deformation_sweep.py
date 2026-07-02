#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal sweep for the Reward-Deformation "Newton" experiment (and Paper B big-n).

Derivation + CPU results: notes/reward_deformation_ratedistortion.md.
State: the capacity constraint is causally validated (exponent 0.07 -> 0.30 with a
bottleneck) but PLATEAUS at ~0.30 ~ 1/3 rather than the 2-D prediction 1/2. Open
question: is the reallocation effectively 1-D (d_eff ~ 1 -> 1/3) or 2-D
(d_eff ~ 2 -> 1/2)? This sweep resolves it at scale, on GPU, with the decisive
next tests from the result reports:

  1. REWARD GEOMETRY  {point (radial), stripe (genuine 1-D), aniso2d (genuine 2-D)}
     - the effective-1-D hypothesis predicts: stripe -> ~1/3, aniso2d -> ~1/2.
  2. IMPLIED d_eff  = 2*alpha/(1-alpha), read directly off the measured exponent.
  3. AMPLITUDE SWEEP  A in {...}: peak resolution ratio ~ (1+A)^{d/(d+2)}.
  4. Many seeds + finer grid + larger Ng + longer training (the smooth
     high-resolution regime the law assumes); bootstrap CIs.
  5. Paper B big-n: control-subtracted specificity across all seeds + sign test.

Self-contained worker (house pattern). Run from a Modal-authed machine:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal --with numpy modal run \\
            experiments/grid_cell_weakness/modal_reward_deformation_sweep.py \\
            --seeds 10 --steps 8000 --ng 256 --np 256 \\
            --geometries point,stripe,aniso2d --amps 3,6,12 \\
            --out artifacts/grid_cell_weakness/reward_deformation_sweep.json

Smoke: --seeds 1 --steps 800 --geometries point --amps 6
"""

from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8", "numpy>=1.26,<2.2")

app = modal.App(name="research-derived-reward-deformation")


# --------------------------------------------------------------------------- #
# self-contained helpers (mirrors core.py + capacity_bottleneck.py, proven on CPU)
# --------------------------------------------------------------------------- #

def _place_cells(side):
    import numpy as np
    xs = np.linspace(0.0, 1.0, side)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    return np.stack([X.ravel(), Y.ravel()], axis=1)


def _place_code(pos, centers, sigma):
    import numpy as np
    d2 = ((pos[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
    logits = -d2 / (2 * sigma ** 2)
    logits = logits - logits.max(1, keepdims=True)
    e = np.exp(logits)
    return e / e.sum(1, keepdims=True)


def _trajectories(batch, T, rng, speed=0.06):
    import numpy as np
    pos = rng.uniform(0.1, 0.9, size=(batch, 2))
    vels = np.zeros((batch, T, 2)); poss = np.zeros((batch, T, 2))
    heading = rng.uniform(0, 2 * math.pi, size=batch)
    for t in range(T):
        heading = heading + rng.normal(0, 0.4, size=batch)
        v = speed * np.stack([np.cos(heading), np.sin(heading)], 1)
        npos = pos + v
        for d in range(2):
            lo, hi = npos[:, d] < 0.0, npos[:, d] > 1.0
            npos[lo, d] = -npos[lo, d]; npos[hi, d] = 2.0 - npos[hi, d]
            heading[lo | hi] = heading[lo | hi] + math.pi
        v = npos - pos; vels[:, t] = v; poss[:, t] = npos; pos = npos
    return vels, poss


def _reward_weights(pos, geometry, xy, A, sigma):
    """Per-sample value weight w(x). point=radial 2-D; stripe=1-D (x1 only);
    aniso2d=anisotropic 2-D (forces reallocation in both axes)."""
    import numpy as np
    if geometry == "stripe":
        d2 = (pos[:, 0] - xy[0]) ** 2 / (2 * sigma ** 2)
    elif geometry == "aniso2d":
        d2 = (pos[:, 0] - xy[0]) ** 2 / (2 * sigma ** 2) + (pos[:, 1] - xy[1]) ** 2 / (2 * (sigma * 2.2) ** 2)
    else:  # point
        d2 = ((pos - np.array(xy)) ** 2).sum(1) / (2 * sigma ** 2)
    return 1.0 + A * np.exp(-d2)


def _reward_field(side, geometry, xy, A, sigma):
    import numpy as np
    xs = np.linspace(0, 1, side)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    if geometry == "stripe":
        d2 = (X - xy[0]) ** 2 / (2 * sigma ** 2)
    elif geometry == "aniso2d":
        d2 = (X - xy[0]) ** 2 / (2 * sigma ** 2) + (Y - xy[1]) ** 2 / (2 * (sigma * 2.2) ** 2)
    else:
        d2 = ((X - xy[0]) ** 2 + (Y - xy[1]) ** 2) / (2 * sigma ** 2)
    return 1.0 + A * np.exp(-d2)


def _area_and_stretch(pop, side):
    import numpy as np
    grid = pop.reshape(side, side, -1); dx = 1.0 / (side - 1)
    area = np.full((side, side), np.nan); stretch = np.full((side, side), np.nan)
    for i in range(1, side - 1):
        for j in range(1, side - 1):
            du = (grid[i + 1, j] - grid[i - 1, j]) / (2 * dx)
            dv = (grid[i, j + 1] - grid[i, j - 1]) / (2 * dx)
            g00 = du @ du; g11 = dv @ dv; g01 = du @ dv
            area[i, j] = math.sqrt(max(0.0, g00 * g11 - g01 * g01))
            stretch[i, j] = 0.5 * (math.sqrt(g00) + math.sqrt(g11))
    return area, stretch


def _loglog_slope(w, rho):
    import numpy as np
    m = np.isfinite(w) & np.isfinite(rho) & (w > 0) & (rho > 0)
    lw, lr = np.log(w[m]), np.log(rho[m])
    if lw.size < 8 or lw.std() < 1e-6:
        return float("nan"), float("nan"), int(m.sum())
    Amat = np.vstack([lw, np.ones_like(lw)]).T
    slope, intercept = np.linalg.lstsq(Amat, lr, rcond=None)[0]
    pred = Amat @ [slope, intercept]
    ss_res = ((lr - pred) ** 2).sum(); ss_tot = ((lr - lr.mean()) ** 2).sum() or 1.0
    return float(slope), float(1 - ss_res / ss_tot), int(m.sum())


@app.function(
    image=IMAGE,
    gpu="H100",
    timeout=7200,
    memory=32768,
    max_containers=192,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn

    seed = arg["seed"]; geometry = arg["geometry"]; A = arg["A"]
    Ng, Np, sigma = arg["Ng"], arg["Np"], arg["sigma"]
    T, steps, batch, noise_std = arg["T"], arg["steps"], arg["batch"], arg["noise_std"]
    xy = arg["xy"]; sig_pc = arg["sig_pc"]
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    side = int(round(math.sqrt(Np)))
    centers = _place_cells(side)
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    class Bottleneck(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Linear(Np, Ng); self.rnn = nn.RNNCell(2, Ng, nonlinearity="relu")
            self.dec = nn.Linear(Ng, Np)

        def forward(self, vel, p0, noise):
            h = self.enc(p0); gs = []
            for t in range(vel.shape[1]):
                h = self.rnn(vel[:, t], h)
                h = h / (h.norm(dim=-1, keepdim=True) + 1e-6)   # unit sphere -> hard capacity
                gs.append(h)
            G = torch.stack(gs, 1)
            return self.dec(G + noise * torch.randn_like(G)), G

    model = Bottleneck().to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)

    def batch_data():
        vels, poss = _trajectories(batch, T, rng)
        p0 = poss[:, 0] - vels[:, 0]
        tgt = _place_code(poss.reshape(-1, 2), centers, sig_pc).reshape(batch, T, Np)
        p0c = _place_code(p0, centers, sig_pc)
        w = _reward_weights(poss.reshape(-1, 2), geometry, xy, A, sigma)
        w = w / w.mean()
        return (torch.tensor(vels, dtype=torch.float32, device=dev),
                torch.tensor(p0c, dtype=torch.float32, device=dev),
                torch.tensor(tgt, dtype=torch.float32, device=dev),
                torch.tensor(w, dtype=torch.float32, device=dev))

    for _ in range(steps):
        vel, p0c, tgt, wv = batch_data()
        logits, _ = model(vel, p0c, noise_std)
        logp = torch.log_softmax(logits, -1).reshape(-1, Np)
        kl = (tgt.reshape(-1, Np) * (torch.log(tgt.reshape(-1, Np) + 1e-9) - logp)).sum(-1)
        loss = (wv * kl).mean()
        opt.zero_grad(); loss.backward(); opt.step()

    model.eval()
    with torch.no_grad():
        vels, poss = _trajectories(1024, T, rng)
        p0 = poss[:, 0] - vels[:, 0]; p0c = _place_code(p0, centers, sig_pc)
        _, G = model(torch.tensor(vels, dtype=torch.float32, device=dev),
                     torch.tensor(p0c, dtype=torch.float32, device=dev), 0.0)
        G = G.reshape(-1, Ng).cpu().numpy(); flat = poss.reshape(-1, 2)
    ms = side
    b = np.clip((flat * ms).astype(int), 0, ms - 1); bid = b[:, 0] * ms + b[:, 1]
    pop = np.zeros((ms * ms, Ng)); cnt = np.zeros(ms * ms)
    for k, g in zip(bid, G):
        pop[k] += g; cnt[k] += 1
    ne = cnt > 0; pop[ne] /= cnt[ne, None]; pop[~ne] = pop[ne].mean(0) if ne.any() else 0.0

    area, stretch = _area_and_stretch(pop, ms)
    w = _reward_field(ms, geometry, xy, A, sigma)
    a_slope, a_r2, n = _loglog_slope(w.ravel(), area.ravel())
    s_slope, s_r2, _ = _loglog_slope(w.ravel(), stretch.ravel())
    d_eff = (2 * a_slope / (1 - a_slope)) if (np.isfinite(a_slope) and a_slope < 0.999) else float("nan")
    # peak resolution ratio (amplitude-scaling test): area at reward vs arena median
    rb = tuple(int(round(c * (ms - 1))) for c in xy)
    peak_ratio = float(np.nanmax(area) / (np.nanmedian(area) + 1e-9))
    return dict(seed=seed, geometry=geometry, A=A, coverage=float(ne.mean()),
                area_exponent=a_slope, area_r2=a_r2, stretch_exponent=s_slope, stretch_r2=s_r2,
                implied_d_eff=d_eff, n_bins=n, peak_resolution_ratio=peak_ratio)


def _boot_ci(vals, n=2000):
    import numpy as np
    v = np.array([x for x in vals if np.isfinite(x)])
    if v.size < 2:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(0)
    means = [v[rng.integers(0, v.size, v.size)].mean() for _ in range(n)]
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


@app.local_entrypoint()
def main(seeds: int = 10, steps: int = 8000, ng: int = 256, np: int = 256,
         sigma: float = 0.12, sig_pc: float = 0.09, t: int = 20, batch: int = 128,
         noise_std: float = 0.15, geometries: str = "point,stripe,aniso2d",
         amps: str = "3,6,12", base_seed: int = 20260701,
         out: str = "artifacts/grid_cell_weakness/reward_deformation_sweep.json"):
    geos = [g.strip() for g in geometries.split(",") if g.strip()]
    As = [float(a) for a in amps.split(",") if a.strip()]
    cells = [dict(seed=base_seed + 100 * k, geometry=g, A=a, Ng=ng, Np=np, sigma=sigma,
                  sig_pc=sig_pc, T=t, steps=steps, batch=batch, noise_std=noise_std, xy=[0.5, 0.5])
             for g in geos for a in As for k in range(seeds)]
    print(f"[rd-sweep] dispatching {len(cells)} cells: geometries={geos} amps={As} seeds={seeds} "
          f"Ng={ng} Np={np} steps={steps}")
    rows = [r for r in run_cell.map(cells) if r]

    # aggregate exponent + implied d_eff per (geometry, A), and amplitude scaling
    groups = {}
    for r in rows:
        groups.setdefault((r["geometry"], r["A"]), []).append(r)
    summary = {}
    for (g, a), rs in sorted(groups.items()):
        alpha, lo, hi = _boot_ci([x["area_exponent"] for x in rs])
        deff, _, _ = _boot_ci([x["implied_d_eff"] for x in rs])
        r2 = sum(x["area_r2"] for x in rs if x["area_r2"] == x["area_r2"]) / max(1, len(rs))
        summary[f"{g}@A={a:g}"] = dict(area_exponent=alpha, ci95=[lo, hi], implied_d_eff=deff,
                                       mean_r2=r2, n_seeds=len(rs))
    payload = dict(
        kind="reward-deformation Newton sweep (exponent resolution + Paper B big-n)",
        predicted_area_exponent_2d=0.5, predicted_area_exponent_1d=1.0 / 3.0,
        note="stripe should approach 1/3, aniso2d should approach 1/2 if reallocation dimension "
             "drives the exponent; implied_d_eff = 2*alpha/(1-alpha).",
        summary=summary, rows=rows,
    )
    op = Path(out); op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[rd-sweep] wrote {op}")
    for k, s in summary.items():
        print(f"  {k:22s} alpha={s['area_exponent']:+.3f} CI[{s['ci95'][0]:+.3f},{s['ci95'][1]:+.3f}] "
              f"d_eff~{s['implied_d_eff']:.2f} R2={s['mean_r2']:.2f} n={s['n_seeds']}")
