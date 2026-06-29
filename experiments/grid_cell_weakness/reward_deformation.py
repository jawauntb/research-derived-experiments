#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Experiment ①: does concern (reward) deform the representational metric?

The non-circular test. A reward is an INJECTED, independent variable; we ask
whether the learned code's induced metric — how fast the population vector moves
per unit physical space, i.e. local resolution — and its local weakness deform
*specifically at the reward location* and *track the reward when it moves*, with a
no-reward control. Reward location and weakness/metric are independent, so a
positive result cannot be tautological.

Mechanism (in-house): a globally translation-invariant (high-weakness) code
cannot have extra resolution at one location — invariance forbids privileging a
point. To buy local resolution it must break the symmetry locally → local
weakness drops AT the reward while staying high elsewhere, and the induced metric
(resolution) rises there. This is the metric-tensor warp that valence_tapestry
could not show in a bandit, on the substrate where it is measurable. It mirrors
reward-warping of the biological grid code (Miolane; Boccara/Butler/Hardcastle).

Folds in Experiment ③: decoding accuracy in a larger, never-seen arena (true OOD
geometry), so the OOD leg is tested without Modal.

Run:  python experiments/grid_cell_weakness/reward_deformation.py \
          --seeds 2 --steps 2500
Writes: artifacts/grid_cell_weakness/reward_deformation.json  (gitignored)
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

import core  # build_place_cells, place_code, gen_trajectories, weakness_translation, ...


# --------------------------------------------------------------------------- #
# Metric-deformation observables
# --------------------------------------------------------------------------- #

def metric_density(pop: np.ndarray, side: int) -> np.ndarray:
    """Induced-metric magnitude: mean ||Δr|| / ||Δx|| over 4-neighbours, per bin.

    High = the population code moves fast per unit space = fine local resolution
    = the manifold is locally stretched (the Riemannian-metric-warp signature).
    """
    grid = pop.reshape(side, side, -1)
    dx = 1.0 / (side - 1)
    dens = np.zeros((side, side))
    for i in range(side):
        for j in range(side):
            diffs = []
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < side and 0 <= nj < side:
                    diffs.append(np.linalg.norm(grid[ni, nj] - grid[i, j]) / dx)
            dens[i, j] = float(np.mean(diffs)) if diffs else 0.0
    return dens


def local_weakness(pop: np.ndarray, side: int, center_ij: tuple[int, int],
                   radius: int = 4, seed: int = 0) -> float:
    """Weakness (mean R² of a single wrapped-translation operator) restricted to a
    spatial window around `center_ij`. Lower = translation symmetry more broken
    locally."""
    rng = np.random.default_rng(seed)
    grid = pop.reshape(side, side, -1)
    ci, cj = center_ij
    win = [(i, j) for i in range(side) for j in range(side)
           if abs(i - ci) <= radius and abs(j - cj) <= radius]
    if len(win) < 8:
        return float("nan")
    idx = np.array([i * side + j for i, j in win])
    flat = grid.reshape(side * side, -1)
    shifts = [(1, 0), (0, 1), (1, 1)]
    rng.shuffle(idx)
    cut = max(4, int(0.5 * len(idx)))
    tr, te = idx[:cut], idx[cut:]
    if len(te) < 2:
        return float("nan")
    r2s = []
    for di, dj in shifts:
        shifted = np.roll(np.roll(grid, -di, axis=0), -dj, axis=1).reshape(side * side, -1)
        T, *_ = np.linalg.lstsq(flat[tr], shifted[tr], rcond=None)
        pred = flat[te] @ T
        ss_res = float(((shifted[te] - pred) ** 2).sum())
        ss_tot = float(((shifted[te] - shifted[te].mean(0)) ** 2).sum()) or 1.0
        r2s.append(max(0.0, min(1.0, 1.0 - ss_res / ss_tot)))
    return float(np.mean(r2s))


def region_mean(field: np.ndarray, center_ij, radius: int = 2) -> float:
    ci, cj = center_ij
    side = field.shape[0]
    vals = [field[i, j] for i in range(side) for j in range(side)
            if abs(i - ci) <= radius and abs(j - cj) <= radius]
    return float(np.mean(vals)) if vals else float("nan")


# --------------------------------------------------------------------------- #
# Training with a reward-reweighted objective
# --------------------------------------------------------------------------- #

def train(seed, *, reward_xy=None, reward_strength=6.0, reward_width=0.12,
          Ng=96, Np=100, sigma=0.10, T=20, steps=2500, batch=128, lr=1e-3,
          weight_decay=1e-4, activity_reg=2e-3, decode_arenas=(1.0, 1.25)):
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    side = int(round(math.sqrt(Np)))
    centers = core.build_place_cells(side)
    dev = "cpu"

    class PIRNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Linear(Np, Ng)
            self.rnn = nn.RNNCell(2, Ng, nonlinearity="relu")
            self.dec = nn.Linear(Ng, Np)

        def forward(self, vel, p0):
            h = self.enc(p0); gs = []
            for t in range(vel.shape[1]):
                h = self.rnn(vel[:, t], h); gs.append(h)
            G = torch.stack(gs, 1)
            return self.dec(G), G

    model = PIRNN().to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    def batch_data(box=1.0):
        vels, poss = core.gen_trajectories(batch, T, rng, box=box)
        p0 = poss[:, 0] - vels[:, 0]
        tgt = core.place_code(poss.reshape(-1, 2), centers, sigma).reshape(batch, T, Np)
        p0c = core.place_code(p0, centers, sigma)
        # reward weighting on each timestep by proximity to the reward location
        if reward_xy is not None:
            d2 = ((poss.reshape(-1, 2) - np.array(reward_xy)) ** 2).sum(1)
            w = 1.0 + reward_strength * np.exp(-d2 / (2 * reward_width ** 2))
        else:
            w = np.ones(batch * T)
        w = w / w.mean()
        return (torch.tensor(vels, dtype=torch.float32),
                torch.tensor(p0c, dtype=torch.float32),
                torch.tensor(tgt, dtype=torch.float32),
                torch.tensor(w, dtype=torch.float32))

    final_loss = math.inf
    for _ in range(steps):
        vel, p0c, tgt, w = batch_data()
        logits, G = model(vel, p0c)
        logp = torch.log_softmax(logits, -1).reshape(-1, Np)
        # per-sample weighted KL
        kl = (tgt.reshape(-1, Np) * (torch.log(tgt.reshape(-1, Np) + 1e-9) - logp)).sum(-1)
        loss = (w * kl).mean() + activity_reg * (G ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
        final_loss = float(loss.item())

    model.eval()
    with torch.no_grad():
        step = 1.0 / (side - 1)

        def decode_err_field(box=1.0):
            vels, poss = core.gen_trajectories(400, T, rng, box=box)
            p0 = poss[:, 0] - vels[:, 0]; p0c = core.place_code(p0, centers, sigma)
            lg, _ = model(torch.tensor(vels, dtype=torch.float32),
                          torch.tensor(p0c, dtype=torch.float32))
            pidx = lg.reshape(-1, Np).argmax(-1).numpy()
            tpos = poss.reshape(-1, 2)
            err = np.sqrt(((centers[pidx] - tpos) ** 2).sum(1))
            acc = float((err <= step + 1e-6).mean())
            return tpos, err, acc

        ood = {}
        for box in decode_arenas:
            _, _, acc = decode_err_field(box)
            ood[f"{box:g}"] = acc
        tpos, err, _ = decode_err_field(1.0)

        # population manifold
        vels, poss = core.gen_trajectories(512, T, rng)
        p0 = poss[:, 0] - vels[:, 0]; p0c = core.place_code(p0, centers, sigma)
        _, G = model(torch.tensor(vels, dtype=torch.float32),
                     torch.tensor(p0c, dtype=torch.float32))
        G = G.reshape(-1, Ng).numpy(); flat = poss.reshape(-1, 2)

    ms = side
    b = np.clip((flat * ms).astype(int), 0, ms - 1); bid = b[:, 0] * ms + b[:, 1]
    pop = np.zeros((ms * ms, Ng)); cnt = np.zeros(ms * ms)
    for k, g in zip(bid, G):
        pop[k] += g; cnt[k] += 1
    ne = cnt > 0; pop[ne] /= cnt[ne, None]; pop[~ne] = pop[ne].mean(0) if ne.any() else 0.0

    dens = metric_density(pop, ms)
    # local decode error near a point (resolution proxy from behavior)
    eb = np.clip((tpos * ms).astype(int), 0, ms - 1)
    errfield = np.full((ms, ms), np.nan)
    for (i, j), e in zip(eb, err):
        errfield[i, j] = e if np.isnan(errfield[i, j]) else 0.5 * (errfield[i, j] + e)

    return dict(seed=seed, reward_xy=reward_xy, final_loss=final_loss, ood=ood,
                pop=pop, side=ms, density=dens, errfield=errfield)


def reward_bin(xy, side):
    return (int(round(xy[0] * (side - 1))), int(round(xy[1] * (side - 1))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--steps", type=int, default=2500)
    ap.add_argument("--base-seed", type=int, default=20260629)
    ap.add_argument("--out", default="artifacts/grid_cell_weakness/reward_deformation.json")
    args = ap.parse_args()

    A, B = (0.3, 0.3), (0.7, 0.7)
    conditions = [("control", None), ("reward_A", A), ("reward_B", B)]
    seeds = [args.base_seed + 100 * k for k in range(args.seeds)]
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    cells = []

    def flush():
        out.write_text(json.dumps(dict(kind="reward-deformation (Experiment 1+3)",
                                        reward_A=A, reward_B=B, cells=cells),
                                   indent=2, sort_keys=True, default=float) + "\n")

    t0 = time.time()
    for name, rxy in conditions:
        for s in seeds:
            tc = time.time()
            r = train(s, reward_xy=rxy, steps=args.steps)
            side = r["side"]
            binA, binB = reward_bin(A, side), reward_bin(B, side)
            dens = r["density"]; dz = (dens - dens.mean()) / (dens.std() + 1e-9)
            cell = dict(
                condition=name, seed=s, final_loss=r["final_loss"], ood=r["ood"],
                # induced-metric density z-score at A and B (deformation localisation)
                density_z_at_A=float(dz[binA]), density_z_at_B=float(dz[binB]),
                density_raw_at_A=region_mean(dens, binA), density_raw_at_B=region_mean(dens, binB),
                density_mean=float(dens.mean()),
                # local weakness near A vs B (symmetry spent locally)
                local_weakness_A=local_weakness(r["pop"], side, binA, seed=s),
                local_weakness_B=local_weakness(r["pop"], side, binB, seed=s),
                global_weakness=core.weakness_translation(r["pop"], side,
                                                          rng=np.random.default_rng(s))["weakness_translation"],
                # decode error near A vs B (resolution from behaviour)
                err_at_A=region_mean(np.nan_to_num(r["errfield"], nan=float(np.nanmean(r["errfield"]))), binA),
                err_at_B=region_mean(np.nan_to_num(r["errfield"], nan=float(np.nanmean(r["errfield"]))), binB),
                seconds=round(time.time() - tc, 1),
            )
            cells.append(cell); flush()
            print(f"[reward] {name:8s} seed={s} loss={cell['final_loss']:.3f} "
                  f"dz@A={cell['density_z_at_A']:+.2f} dz@B={cell['density_z_at_B']:+.2f} "
                  f"lwA={cell['local_weakness_A']:.2f} lwB={cell['local_weakness_B']:.2f} "
                  f"ood={r['ood']} ({cell['seconds']}s)")

    # directional tests (means over seeds per condition)
    def cond(name):
        return [c for c in cells if c["condition"] == name]

    def mean(xs):
        xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
        return float(np.mean(xs)) if xs else float("nan")

    analysis = {}
    for name in ("control", "reward_A", "reward_B"):
        cs = cond(name)
        analysis[name] = dict(
            density_z_at_A=mean([c["density_z_at_A"] for c in cs]),
            density_z_at_B=mean([c["density_z_at_B"] for c in cs]),
            local_weakness_A=mean([c["local_weakness_A"] for c in cs]),
            local_weakness_B=mean([c["local_weakness_B"] for c in cs]),
            err_at_A=mean([c["err_at_A"] for c in cs]),
            err_at_B=mean([c["err_at_B"] for c in cs]),
            ood_large=mean([c["ood"].get("1.25", float("nan")) for c in cs]),
        )
    # Control-subtracted deformation (removes positional baseline asymmetry):
    # the reward effect is (reward-condition − control) at the SAME location.
    cA = analysis["control"]
    dz = lambda name, where: analysis[name][f"density_z_at_{where}"]
    analysis["control_subtracted"] = dict(
        # reward at A should raise density at A vs control, and do so MORE at A than at B
        deform_at_reward_A=dz("reward_A", "A") - cA["density_z_at_A"],
        deform_at_reward_B=dz("reward_B", "B") - cA["density_z_at_B"],
        specificity_A=(dz("reward_A", "A") - cA["density_z_at_A"]) - (dz("reward_A", "B") - cA["density_z_at_B"]),
        specificity_B=(dz("reward_B", "B") - cA["density_z_at_B"]) - (dz("reward_B", "A") - cA["density_z_at_A"]),
    )
    # the cross-over test: reward_A should raise density at A relative to B (and vice-versa),
    # while control is flat. Summaries:
    analysis["tests"] = dict(
        # H2 cross-over: (density_z@A - density_z@B) is positive for reward_A, negative for reward_B,
        # ~0 for control.
        crossover_A=analysis["reward_A"]["density_z_at_A"] - analysis["reward_A"]["density_z_at_B"],
        crossover_B=analysis["reward_B"]["density_z_at_A"] - analysis["reward_B"]["density_z_at_B"],
        crossover_control=analysis["control"]["density_z_at_A"] - analysis["control"]["density_z_at_B"],
        # H4 local weakness traded: reward_A local weakness@A < @B (symmetry spent at A)
        weakness_trade_A=analysis["reward_A"]["local_weakness_A"] - analysis["reward_A"]["local_weakness_B"],
        weakness_trade_B=analysis["reward_B"]["local_weakness_A"] - analysis["reward_B"]["local_weakness_B"],
        weakness_trade_control=analysis["control"]["local_weakness_A"] - analysis["control"]["local_weakness_B"],
    )
    payload = json.loads(out.read_text()); payload["analysis"] = analysis
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n")
    print(f"[reward] DONE in {round(time.time()-t0,1)}s")
    print(f"[reward] crossover (A,B,ctrl)="
          f"{analysis['tests']['crossover_A']:+.2f},{analysis['tests']['crossover_B']:+.2f},"
          f"{analysis['tests']['crossover_control']:+.2f}")
    print(f"[reward] weakness-trade (A,B,ctrl)="
          f"{analysis['tests']['weakness_trade_A']:+.2f},{analysis['tests']['weakness_trade_B']:+.2f},"
          f"{analysis['tests']['weakness_trade_control']:+.2f}")


if __name__ == "__main__":
    main()
