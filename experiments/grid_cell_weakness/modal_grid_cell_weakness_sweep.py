#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Paper A Modal sweep -- weakness predicts toroidal topology and OOD.

Pre-registration: papers/grid_cell_weakness/preregistration.md (frozen 2026-06-28).

Self-contained, single-file worker (matching the house pattern in
experiments/external_contact/modal_p1_pythia_weakness.py): all model, task, and
metric helpers are module-level in THIS file so the Modal worker needs no
cross-file import. The canonical, importable copy lives in core.py and is what
experiments/grid_cell_weakness/pilot.py validated locally; keep the two in sync.

Each (augment, arch, seed) cell trains one path-integration RNN to grid-cell
emergence, then measures the four pre-registered quantities:
  weakness_translation (wrapped grid translations), toroidal_score (gudhi
  persistent homology), fourier_pr (spatial DFT participation ratio),
  ood_accuracy (held-out trajectories + larger arena). A wrong-group weakness
  (permuted-bin "translations") is computed as the null-control predictor.

Run (laptop, dispatches to Modal):

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
            experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py \\
            --seeds 8 --steps 4000 \\
            --out artifacts/grid_cell_weakness/sweep.json

Smoke first:  --seeds 1 --steps 400 --conditions full_translation,none
"""

from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "numpy>=1.26,<2.2",
    "scipy>=1.11,<1.15",
    "gudhi>=3.9,<3.13",
)

app = modal.App(name="research-derived-grid-cell-weakness")

CONDITIONS = ["full_translation", "partial_translation", "none", "random_shift", "wrong_group"]


# --------------------------------------------------------------------------- #
# Task + model + metric helpers (module-level -> available on the worker)
# --------------------------------------------------------------------------- #

def _build_place_cells(side: int):
    import numpy as np
    xs = np.linspace(0.0, 1.0, side)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    return np.stack([X.ravel(), Y.ravel()], axis=1)


def _place_code(pos, centers, sigma):
    import numpy as np
    d2 = ((pos[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
    logits = -d2 / (2 * sigma ** 2)
    logits = logits - logits.max(axis=1, keepdims=True)
    e = np.exp(logits)
    return e / e.sum(axis=1, keepdims=True)


def _gen_trajectories(batch, T, rng, speed=0.06, box=1.0):
    import numpy as np
    pos = rng.uniform(0.1 * box, 0.9 * box, size=(batch, 2))
    vels = np.zeros((batch, T, 2)); poss = np.zeros((batch, T, 2))
    heading = rng.uniform(0, 2 * math.pi, size=batch)
    for t in range(T):
        heading = heading + rng.normal(0, 0.4, size=batch)
        v = speed * np.stack([np.cos(heading), np.sin(heading)], axis=1)
        npos = pos + v
        for d in range(2):
            lo, hi = npos[:, d] < 0.0, npos[:, d] > box
            npos[lo, d] = -npos[lo, d]
            npos[hi, d] = 2.0 * box - npos[hi, d]
            heading[lo | hi] = heading[lo | hi] + math.pi
        v = npos - pos
        vels[:, t] = v; poss[:, t] = npos; pos = npos
    return vels, poss


def _weakness(points, side, shifts=None, train_frac=0.5, seed=0, permute=False):
    import numpy as np
    rng = np.random.default_rng(seed)
    P = np.asarray(points, dtype=np.float64)
    n = side * side
    grid = P.reshape(side, side, -1)
    if shifts is None:
        ks = [k for k in (1, 2, 3) if k < side]
        shifts = [(k, 0) for k in ks] + [(0, k) for k in ks] + [(k, k) for k in ks]
    idx = np.arange(n); rng.shuffle(idx)
    cut = int(round(n * train_frac))
    tm = np.zeros(n, dtype=bool); tm[idx[:cut]] = True
    perm = rng.permutation(n) if permute else None
    r2s = []
    for (di, dj) in shifts:
        src = grid.reshape(n, -1)
        if permute:
            shifted = src[perm]  # wrong-group: a fixed random bijection, not a translation
        else:
            shifted = np.roll(np.roll(grid, -di, axis=0), -dj, axis=1).reshape(n, -1)
        Xtr, Ytr = src[tm], shifted[tm]
        Xte, Yte = src[~tm], shifted[~tm]
        T, *_ = np.linalg.lstsq(Xtr, Ytr, rcond=None)
        pred = Xte @ T
        ss_res = float(((Yte - pred) ** 2).sum())
        ss_tot = float(((Yte - Yte.mean(axis=0)) ** 2).sum()) or 1.0
        r2s.append(max(0.0, min(1.0, 1.0 - ss_res / ss_tot)))
    return float(np.mean(r2s))


def _toroidal_score(points, max_points=400, seed=0):
    import numpy as np
    import gudhi
    from scipy.spatial.distance import pdist
    rng = np.random.default_rng(seed)
    P = np.asarray(points, dtype=np.float64)
    if P.shape[0] > max_points:
        P = P[rng.choice(P.shape[0], max_points, replace=False)]
    d = pdist(P)
    max_edge = float(np.percentile(d, 45)) if len(d) else 1.0
    st = gudhi.RipsComplex(points=P.tolist(), max_edge_length=max_edge).create_simplex_tree(max_dimension=3)
    st.compute_persistence()

    def life(dim):
        iv = np.asarray(st.persistence_intervals_in_dimension(dim), float).reshape(-1, 2)
        iv = iv[np.isfinite(iv[:, 1])]
        return np.sort(iv[:, 1] - iv[:, 0])[::-1] if len(iv) else np.array([])

    h1, h2 = life(1), life(2)
    h1_top2 = [float(h1[0]) if len(h1) > 0 else 0.0, float(h1[1]) if len(h1) > 1 else 0.0]
    h1_noise = float(h1[2]) if len(h1) > 2 else 0.0
    h2_top = float(h2[0]) if len(h2) > 0 else 0.0
    scale = float(np.linalg.norm(P.std(axis=0))) or 1.0
    score = max(0.0, min((h1_top2[1] - h1_noise) / scale, h2_top / scale))
    betti1 = int((h1 > (h1_top2[1] * 0.5 if h1_top2[1] > 0 else np.inf)).sum()) if len(h1) else 0
    return dict(toroidal_score=float(score), betti1_estimate=betti1,
                betti_match_torus=bool(betti1 == 2 and h2_top > 0.2 * scale),
                h1_top2=h1_top2, h2_top=h2_top)


def _fourier_pr(rate_maps):
    import numpy as np
    prs = []
    for m in rate_maps:
        m = m - m.mean()
        if not np.any(m):
            continue
        power = np.abs(np.fft.fft2(m)) ** 2
        power[0, 0] = 0.0
        p = power.ravel(); s = p.sum()
        if s <= 0:
            continue
        p = p / s
        prs.append(1.0 / float((p ** 2).sum()))
    return float(np.mean(prs)) if prs else float("nan")


# --------------------------------------------------------------------------- #
# Modal worker: train one net, measure four quantities
# --------------------------------------------------------------------------- #

@app.function(image=IMAGE, gpu="A10G", timeout=3600, memory=16384)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    import torch.nn as nn

    aug = arg["augment"]; seed = arg["seed"]; arch = arg["arch"]
    Ng, Np = arg["Ng"], arg["Np"]
    sigma, T, steps, batch = arg["sigma"], arg["T"], arg["steps"], arg["batch"]
    lr, wd, act_reg = arg["lr"], arg["weight_decay"], arg["activity_reg"]

    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    side = int(round(math.sqrt(Np)))
    centers = _build_place_cells(side)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    class PIRNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Linear(Np, Ng)
            cell = {"rnn": nn.RNNCell, "gru": nn.GRUCell}[arch]
            self.rnn = cell(2, Ng) if arch == "gru" else nn.RNNCell(2, Ng, nonlinearity="relu")
            self.dec = nn.Linear(Ng, Np)

        def forward(self, vel, p0):
            h = self.enc(p0); gs = []
            for t in range(vel.shape[1]):
                h = self.rnn(vel[:, t], h)
                if arch == "gru":
                    h = torch.relu(h)
                gs.append(h)
            G = torch.stack(gs, 1)
            return self.dec(G), G

    model = PIRNN().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    kl = nn.KLDivLoss(reduction="batchmean")

    def make_batch(box=1.0):
        vels, poss = _gen_trajectories(batch, T, rng, box=box)
        p0 = poss[:, 0] - vels[:, 0]
        if aug == "full_translation":
            off = rng.uniform(0, 1, (batch, 2)); poss = (poss + off[:, None]) % 1.0; p0 = (p0 + off) % 1.0
        elif aug == "partial_translation":
            off = rng.uniform(0, 0.3, (batch, 2)); poss = (poss + off[:, None]) % 1.0; p0 = (p0 + off) % 1.0
        elif aug == "random_shift":
            off = rng.normal(0, 0.05, (batch, 2)); poss = np.clip(poss + off[:, None], 0, box); p0 = np.clip(p0 + off, 0, box)
        elif aug == "wrong_group":
            vels = vels[:, :, ::-1].copy()
        tgt = _place_code(poss.reshape(-1, 2), centers, sigma).reshape(batch, T, Np)
        p0c = _place_code(p0, centers, sigma)
        return (torch.tensor(vels, dtype=torch.float32, device=device),
                torch.tensor(p0c, dtype=torch.float32, device=device),
                torch.tensor(tgt, dtype=torch.float32, device=device))

    final_loss = math.inf
    for _ in range(steps):
        vel, p0c, tgt = make_batch()
        logits, G = model(vel, p0c)
        loss = kl(torch.log_softmax(logits, -1).reshape(-1, Np), tgt.reshape(-1, Np))
        loss = loss + act_reg * (G ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
        final_loss = float(loss.item())

    decode_arenas = list(arg.get("decode_arenas", [1.0, 1.25, 1.5]))
    model.eval()
    with torch.no_grad():
        step = 1.0 / (side - 1)

        def decode_acc(box):
            v, p, t = make_batch(box=box)
            lg, _ = model(v, p)
            pidx = lg.reshape(-1, Np).argmax(-1).cpu().numpy()
            tidx = t.reshape(-1, Np).argmax(-1).cpu().numpy()
            return float((np.sqrt(((centers[pidx] - centers[tidx]) ** 2).sum(1)) <= step + 1e-6).mean())

        # in-distribution: held-out fresh trajectories in the training arena (box=1.0)
        id_acc = decode_acc(1.0)
        # OOD geometry: a sweep over arena scales (>1.0 = larger, never-seen geometry)
        ood_by_arena = {f"{box:g}": decode_acc(box) for box in decode_arenas}
        ood_scales = [b for b in decode_arenas if b > 1.0] or [max(decode_arenas)]
        # primary OOD (gate metric) = hardest (largest) held-out arena, per prereg
        ood_acc = ood_by_arena[f"{max(ood_scales):g}"]

        # population manifold: bin hidden by position
        vels, poss = _gen_trajectories(512, T, rng)
        p0 = poss[:, 0] - vels[:, 0]; p0c = _place_code(p0, centers, sigma)
        _, G = model(torch.tensor(vels, dtype=torch.float32, device=device),
                     torch.tensor(p0c, dtype=torch.float32, device=device))
        G = G.reshape(-1, Ng).cpu().numpy(); flat = poss.reshape(-1, 2)

    ms = 16
    b = np.clip((flat * ms).astype(int), 0, ms - 1); bid = b[:, 0] * ms + b[:, 1]
    pop = np.zeros((ms * ms, Ng)); cnt = np.zeros(ms * ms)
    for k, g in zip(bid, G):
        pop[k] += g; cnt[k] += 1
    ne = cnt > 0; pop[ne] /= cnt[ne, None]
    pop[~ne] = pop[ne].mean(0) if ne.any() else 0.0
    rate_maps = pop.reshape(ms, ms, Ng).transpose(2, 0, 1)

    w = _weakness(pop, ms, seed=seed)
    w_wrong = _weakness(pop, ms, seed=seed, permute=True)
    topo = _toroidal_score(pop, seed=seed)
    fpr = _fourier_pr(rate_maps)

    # Hutchinson sharpness proxy on the decoder (classical baseline)
    return dict(
        augment=aug, arch=arch, seed=seed, final_loss=final_loss,
        ood_accuracy=ood_acc, id_accuracy=id_acc, ood_by_arena=ood_by_arena,
        weakness_translation=w, weakness_wrong_group=w_wrong,
        toroidal_score=topo["toroidal_score"], betti1_estimate=topo["betti1_estimate"],
        betti_match_torus=topo["betti_match_torus"], h1_top2=topo["h1_top2"], h2_top=topo["h2_top"],
        fourier_pr=fpr, coverage=float(ne.mean()),
    )


# --------------------------------------------------------------------------- #
# Analysis helpers + local entrypoint
# --------------------------------------------------------------------------- #

def _spearman(xs, ys) -> float:
    import numpy as np
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    ok = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[ok], ys[ok]
    if len(xs) < 2:
        return 0.0
    rx = np.argsort(np.argsort(xs)).astype(float); ry = np.argsort(np.argsort(ys)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    den = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / den) if den else 0.0


def _partial(r_wo, r_wt, r_ot) -> float:
    den = math.sqrt(max(1e-9, (1 - r_wt ** 2) * (1 - r_ot ** 2)))
    return (r_wo - r_wt * r_ot) / den


@app.local_entrypoint()
def main(
    conditions: str = ",".join(CONDITIONS),
    archs: str = "rnn,gru",
    seeds: int = 8,
    Ng: int = 128,
    Np: int = 100,
    sigma: float = 0.10,
    T: int = 20,
    steps: int = 4000,
    batch: int = 200,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    activity_reg: float = 1e-3,
    decode_arenas: str = "1.0,1.25,1.5",
    base_seed: int = 20260628,
    out: str = "artifacts/grid_cell_weakness/sweep.json",
) -> None:
    cond_list = [c.strip() for c in conditions.split(",") if c.strip()]
    arch_list = [a.strip() for a in archs.split(",") if a.strip()]
    seed_list = [base_seed + 100 * k for k in range(seeds)]
    arena_list = [float(x) for x in decode_arenas.split(",") if x.strip()]
    cells = [dict(augment=c, arch=a, seed=s, Ng=Ng, Np=Np, sigma=sigma, T=T,
                  steps=steps, batch=batch, lr=lr, weight_decay=weight_decay,
                  activity_reg=activity_reg, decode_arenas=arena_list)
             for c in cond_list for a in arch_list for s in seed_list]
    print(f"[gcw] dispatching {len(cells)} cells "
          f"(conditions={cond_list}, archs={arch_list}, seeds={len(seed_list)}, steps={steps})")
    results = [r for r in run_cell.map(cells) if r]

    def col(key, where=None):
        return [r[key] for r in results if (where is None or r["augment"] in where)]

    w, topo, ood, fpr = col("weakness_translation"), col("toroidal_score"), col("ood_accuracy"), col("fourier_pr")
    wrong, loss = col("weakness_wrong_group"), col("final_loss")

    r_wt = _spearman(w, topo); r_wo = _spearman(w, ood); r_ot = _spearman(topo, ood)
    analysis = dict(
        n_cells=len(results),
        rho_weakness_topology=r_wt,
        rho_weakness_ood=r_wo,
        rho_topology_ood=r_ot,
        rho_weakness_neg_fourier_pr=_spearman(w, [-v for v in fpr]),
        rho_wrong_group_ood=_spearman(wrong, ood),
        rho_loss_topology=_spearman(loss, topo),
        rho_loss_ood=_spearman(loss, ood),
        partial_weakness_ood_given_topology=_partial(r_wo, r_wt, r_ot),
    )
    # gates
    ft = [r for r in results if r["augment"] == "full_translation"]
    g1 = (sum(r["betti_match_torus"] for r in ft) / len(ft)) if ft else 0.0
    best_classical_topo = abs(analysis["rho_loss_topology"])
    best_classical_ood = abs(analysis["rho_loss_ood"])
    mean = lambda xs: (sum(xs) / len(xs)) if xs else float("nan")
    analysis["gates"] = dict(
        G1_manifold_recovered=dict(value=g1, pass_=g1 >= 0.6),
        G2_weakness_topology=dict(pass_=r_wt >= 0.5 and abs(r_wt) >= 2 * best_classical_topo),
        G3_weakness_ood=dict(pass_=r_wo >= 0.5 and abs(r_wo) >= 2 * best_classical_ood),
        G4_topology_mediates=dict(
            partial=analysis["partial_weakness_ood_given_topology"],
            drop=1 - abs(analysis["partial_weakness_ood_given_topology"]) / (abs(r_wo) or 1),
            pass_=(1 - abs(analysis["partial_weakness_ood_given_topology"]) / (abs(r_wo) or 1)) >= 0.5),
        G5_spectral=dict(pass_=analysis["rho_weakness_neg_fourier_pr"] >= 0.5),
        G6_causal=dict(
            full_topo=mean(col("toroidal_score", {"full_translation"})),
            none_topo=mean(col("toroidal_score", {"none"})),
            random_topo=mean(col("toroidal_score", {"random_shift"})),
            full_ood=mean(col("ood_accuracy", {"full_translation"})),
            none_ood=mean(col("ood_accuracy", {"none"})),
            pass_=(mean(col("toroidal_score", {"full_translation"})) > mean(col("toroidal_score", {"none"}))
                   and mean(col("toroidal_score", {"full_translation"})) > mean(col("toroidal_score", {"random_shift"})))),
        wrong_group_null_ok=abs(analysis["rho_wrong_group_ood"]) <= 0.15,
    )

    out_path = Path(out); out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(dict(
        kind="REAL Paper A grid-cell weakness sweep on Modal",
        manifest=dict(conditions=cond_list, archs=arch_list, seeds=seed_list, Ng=Ng, Np=Np,
                      steps=steps, batch=batch, lr=lr, weight_decay=weight_decay, activity_reg=activity_reg,
                      decode_arenas=arena_list),
        analysis=analysis, cells=results,
    ), indent=2, sort_keys=True, default=float) + "\n")
    print(f"[gcw] wrote {out_path}")
    print(f"[gcw] rho(weakness,topology)={r_wt:.3f}  rho(weakness,OOD)={r_wo:.3f}  "
          f"G4 partial={analysis['partial_weakness_ood_given_topology']:.3f}")
    print(f"[gcw] gates: { {k: v.get('pass_') for k, v in analysis['gates'].items() if isinstance(v, dict)} }")
