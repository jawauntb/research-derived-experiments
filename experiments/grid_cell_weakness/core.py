#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Core harness for Paper A: weakness -> toroidal topology -> OOD on a
self-contained path-integration RNN.

Pre-registration: papers/grid_cell_weakness/preregistration.md (frozen 2026-06-28).

This module is the canonical local implementation. The Modal worker
(modal_grid_cell_weakness_sweep.py) inlines a faithful copy so it stays
self-contained on the worker, matching the house pattern in
experiments/external_contact/modal_p1_pythia_weakness.py.

The four measured quantities (per network), all defined here:

  weakness_translation : fraction-of-variance R^2 with which a single linear
      operator T_d reproduces r(x (+) d) from r(x), averaged over a set of
      *wrapped* grid translations d. The wrap is the load-bearing choice: a
      periodic (toroidal) code stays equivariant under wrapped translation; a
      merely translation-equivariant plane code breaks at the wrap seam, so
      weakness separates the two. Normalized to [0, 1].
  toroidal_score : persistent-homology signature of the population point
      cloud. A 2-torus has Betti numbers (b0, b1, b2) = (1, 2, 1): one
      component, two independent loops, one void. Score combines the
      second-longest H1 bar with the longest H2 bar (both must be present).
  fourier_pr     : participation ratio of the 2-D spatial DFT of single-unit
      rate maps (DC removed). Low PR = spectrally concentrated = few aligned
      irreps = grid-like.
  ood_accuracy   : path-integration decoding accuracy on held-out trajectories
      (and, in the full sweep, a held-out larger arena).

Synthetic manifold samplers (torus / plane / sphere) are included so the
metric harness can be validated for *discriminativeness* before any training
run -- the pilot's headline check.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

_HOMOLOGY = None
try:  # prefer gudhi (manylinux wheels, no build); fall back to ripser.
    import gudhi as _gudhi  # noqa: F401
    _HOMOLOGY = "gudhi"
except Exception:  # pragma: no cover
    try:
        from ripser import ripser as _ripser  # noqa: F401
        _HOMOLOGY = "ripser"
    except Exception:
        _HOMOLOGY = None


def _persistence(P: np.ndarray, maxdim: int = 2) -> list[np.ndarray]:
    """Return finite persistence diagrams [H0, H1, ..., Hmaxdim] as (k,2) arrays."""
    if _HOMOLOGY == "ripser":
        return _ripser(P, maxdim=maxdim)["dgms"]
    # gudhi Rips up to (maxdim+1)-simplices; cap edge length to bound blow-up.
    from scipy.spatial.distance import pdist
    d = pdist(P)
    max_edge = float(np.percentile(d, 45)) if len(d) else 1.0
    rips = _gudhi.RipsComplex(points=P.tolist(), max_edge_length=max_edge)
    st = rips.create_simplex_tree(max_dimension=maxdim + 1)
    st.compute_persistence()
    dgms = []
    for dim in range(maxdim + 1):
        iv = st.persistence_intervals_in_dimension(dim)
        dgms.append(np.asarray(iv, dtype=float).reshape(-1, 2) if len(iv) else np.empty((0, 2)))
    return dgms


# --------------------------------------------------------------------------- #
# Synthetic manifolds (metric-validation unit test)
# --------------------------------------------------------------------------- #

def sample_torus(n: int, rng: np.random.Generator, noise: float = 0.0) -> dict[str, Any]:
    """Points on T^2 with their two angular coordinates on a regular grid."""
    side = int(round(math.sqrt(n)))
    th1 = np.linspace(0, 2 * math.pi, side, endpoint=False)
    th2 = np.linspace(0, 2 * math.pi, side, endpoint=False)
    A, B = np.meshgrid(th1, th2, indexing="ij")
    a, b = A.ravel(), B.ravel()
    pts = np.stack([np.cos(a), np.sin(a), np.cos(b), np.sin(b)], axis=1)
    if noise:
        pts = pts + rng.normal(0, noise, pts.shape)
    coords = np.stack([a, b], axis=1)  # toroidal coordinates in [0, 2pi)
    return dict(points=pts, coords=coords, side=side, kind="torus")


def sample_plane(n: int, rng: np.random.Generator, noise: float = 0.0) -> dict[str, Any]:
    side = int(round(math.sqrt(n)))
    xs = np.linspace(0, 1, side)
    ys = np.linspace(0, 1, side)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    x, y = X.ravel(), Y.ravel()
    pts = np.stack([x, y], axis=1)
    if noise:
        pts = pts + rng.normal(0, noise, pts.shape)
    coords = np.stack([x * 2 * math.pi, y * 2 * math.pi], axis=1)
    return dict(points=pts, coords=coords, side=side, kind="plane")


def sample_sphere(n: int, rng: np.random.Generator, noise: float = 0.0) -> dict[str, Any]:
    side = int(round(math.sqrt(n)))
    u = np.linspace(0.1, math.pi - 0.1, side)
    v = np.linspace(0, 2 * math.pi, side, endpoint=False)
    U, V = np.meshgrid(u, v, indexing="ij")
    uu, vv = U.ravel(), V.ravel()
    pts = np.stack([np.sin(uu) * np.cos(vv), np.sin(uu) * np.sin(vv), np.cos(uu)], axis=1)
    if noise:
        pts = pts + rng.normal(0, noise, pts.shape)
    coords = np.stack([vv, uu], axis=1)
    return dict(points=pts, coords=coords, side=side, kind="sphere")


# --------------------------------------------------------------------------- #
# Metric 1: weakness under wrapped grid translations
# --------------------------------------------------------------------------- #

def weakness_translation(
    points: np.ndarray,
    side: int,
    shifts: list[tuple[int, int]] | None = None,
    train_frac: float = 0.5,
    rng: np.random.Generator | None = None,
) -> dict[str, float]:
    """R^2 of a single linear operator reproducing r(x (+) d) from r(x).

    `points` are ordered as a `side x side` grid raveled row-major (index
    i*side + j <-> grid cell (i, j)). Translations act with wraparound
    (mod side) on the grid -- the periodic/toroidal group.
    """
    rng = rng or np.random.default_rng(0)
    P = np.asarray(points, dtype=np.float64)
    n = side * side
    assert P.shape[0] == n, f"expected {n} points, got {P.shape[0]}"
    grid = P.reshape(side, side, -1)

    if shifts is None:
        ks = [k for k in (1, 2, 3) if k < side]
        shifts = [(k, 0) for k in ks] + [(0, k) for k in ks] + [(k, k) for k in ks]

    # train/test split over grid cells, shared across shifts
    idx = np.arange(n)
    rng.shuffle(idx)
    cut = int(round(n * train_frac))
    train_mask = np.zeros(n, dtype=bool)
    train_mask[idx[:cut]] = True

    r2s = []
    for (di, dj) in shifts:
        src = grid.reshape(n, -1)
        shifted = np.roll(np.roll(grid, -di, axis=0), -dj, axis=1).reshape(n, -1)
        Xtr, Ytr = src[train_mask], shifted[train_mask]
        Xte, Yte = src[~train_mask], shifted[~train_mask]
        # least-squares linear operator T: Y ~ X T  (no bias -> strict "with-action")
        T, *_ = np.linalg.lstsq(Xtr, Ytr, rcond=None)
        pred = Xte @ T
        ss_res = float(((Yte - pred) ** 2).sum())
        ss_tot = float(((Yte - Yte.mean(axis=0)) ** 2).sum()) or 1.0
        r2 = 1.0 - ss_res / ss_tot
        r2s.append(max(0.0, min(1.0, r2)))

    arr = np.array(r2s)
    return dict(
        weakness_translation=float(arr.mean()),
        weakness_min=float(arr.min()),
        weakness_frac_above_0p8=float((arr >= 0.8).mean()),
        n_shifts=len(shifts),
    )


# --------------------------------------------------------------------------- #
# Metric 2: toroidal topology via persistent homology
# --------------------------------------------------------------------------- #

def toroidal_score(points: np.ndarray, max_points: int = 400,
                   rng: np.random.Generator | None = None) -> dict[str, Any]:
    """Persistent-homology toroidal signature; needs gudhi or ripser."""
    if _HOMOLOGY is None:
        return dict(available=False)
    rng = rng or np.random.default_rng(0)
    P = np.asarray(points, dtype=np.float64)
    if P.shape[0] > max_points:
        sel = rng.choice(P.shape[0], max_points, replace=False)
        P = P[sel]
    dgms = _persistence(P, maxdim=2)

    def lifetimes(dgm):
        if len(dgm) == 0:
            return np.array([])
        d = dgm[np.isfinite(dgm[:, 1])]
        return np.sort((d[:, 1] - d[:, 0]))[::-1] if len(d) else np.array([])

    h0, h1, h2 = lifetimes(dgms[0]), lifetimes(dgms[1]), lifetimes(dgms[2])
    h1_top2 = [float(h1[0]) if len(h1) > 0 else 0.0,
               float(h1[1]) if len(h1) > 1 else 0.0]
    h1_noise = float(h1[2]) if len(h1) > 2 else 0.0
    h2_top = float(h2[0]) if len(h2) > 0 else 0.0
    scale = float(np.linalg.norm(P.std(axis=0))) or 1.0

    # torus needs TWO loops well above the noise floor AND a void
    loop_gap = (h1_top2[1] - h1_noise) / scale
    score = max(0.0, min(loop_gap, h2_top / scale))
    betti1_est = int((h1 > (h1_top2[1] * 0.5 if h1_top2[1] > 0 else np.inf)).sum()) if len(h1) else 0
    return dict(
        available=True,
        toroidal_score=float(score),
        h1_top2=h1_top2, h1_noise=h1_noise, h2_top=h2_top,
        betti1_estimate=betti1_est,
        betti_match_torus=bool(betti1_est == 2 and h2_top > 0.2 * scale),
        scale=scale,
    )


# --------------------------------------------------------------------------- #
# Metric 3: Fourier participation ratio of single-unit rate maps
# --------------------------------------------------------------------------- #

def fourier_participation_ratio(rate_maps: np.ndarray) -> dict[str, float]:
    """rate_maps: (units, side, side). Low PR = few aligned spatial frequencies."""
    R = np.asarray(rate_maps, dtype=np.float64)
    prs = []
    for m in R:
        m = m - m.mean()
        if not np.any(m):
            continue
        power = np.abs(np.fft.fft2(m)) ** 2
        power[0, 0] = 0.0  # drop DC
        p = power.ravel()
        s = p.sum()
        if s <= 0:
            continue
        p = p / s
        pr = 1.0 / float((p ** 2).sum())  # participation ratio (# effective modes)
        prs.append(pr)
    if not prs:
        return dict(fourier_pr=float("nan"), n_units=0)
    return dict(fourier_pr=float(np.mean(prs)), fourier_pr_median=float(np.median(prs)),
                n_units=len(prs))


# --------------------------------------------------------------------------- #
# Path-integration task + RNN (torch)
# --------------------------------------------------------------------------- #

def build_place_cells(side: int) -> np.ndarray:
    xs = np.linspace(0.0, 1.0, side)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    return np.stack([X.ravel(), Y.ravel()], axis=1)  # (Np, 2)


def place_code(pos: np.ndarray, centers: np.ndarray, sigma: float) -> np.ndarray:
    d2 = ((pos[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
    logits = -d2 / (2 * sigma ** 2)
    logits = logits - logits.max(axis=1, keepdims=True)
    e = np.exp(logits)
    return e / e.sum(axis=1, keepdims=True)


def gen_trajectories(batch: int, T: int, rng: np.random.Generator,
                     speed: float = 0.06) -> tuple[np.ndarray, np.ndarray]:
    """Random-walk trajectories in the unit box with reflecting walls."""
    pos = rng.uniform(0.1, 0.9, size=(batch, 2))
    vels = np.zeros((batch, T, 2))
    poss = np.zeros((batch, T, 2))
    heading = rng.uniform(0, 2 * math.pi, size=batch)
    for t in range(T):
        heading = heading + rng.normal(0, 0.4, size=batch)
        v = speed * np.stack([np.cos(heading), np.sin(heading)], axis=1)
        npos = pos + v
        for d in range(2):
            lo, hi = npos[:, d] < 0.0, npos[:, d] > 1.0
            npos[lo, d] = -npos[lo, d]
            npos[hi, d] = 2.0 - npos[hi, d]
            heading[lo | hi] = heading[lo | hi] + math.pi
        v = npos - pos
        vels[:, t] = v
        poss[:, t] = npos
        pos = npos
    return vels, poss


def train_pi_rnn(seed: int, *, augment: str = "none", Ng: int = 64, Np: int = 64,
                 sigma: float = 0.12, T: int = 20, steps: int = 400, batch: int = 64,
                 lr: float = 1e-3, weight_decay: float = 1e-4, activity_reg: float = 0.0,
                 device: str = "cpu") -> dict[str, Any]:
    """Train a velocity-driven RNN to predict place-cell codes along a path.

    augment: 'none' | 'full_translation' | 'random_shift' | 'wrong_group'.
      Translation augmentation jitters each trajectory's start by a global
      offset (toroidal for 'full_translation'); 'wrong_group' permutes the two
      velocity channels (a matched, structure-destroying control).
    """
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    side = int(round(math.sqrt(Np)))
    centers = build_place_cells(side)
    centers_t = torch.tensor(centers, dtype=torch.float32, device=device)

    class PIRNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Linear(Np, Ng)          # initial place code -> hidden
            self.rnn = nn.RNNCell(2, Ng, nonlinearity="relu")  # nonneg-ish hidden
            self.dec = nn.Linear(Ng, Np)          # hidden -> place code logits

        def forward(self, vel, p0):
            h = self.enc(p0)
            gs = []
            for t in range(vel.shape[1]):
                h = self.rnn(vel[:, t], h)
                gs.append(h)
            G = torch.stack(gs, dim=1)             # (B, T, Ng)
            logits = self.dec(G)
            return logits, G

    model = PIRNN().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    lossfn = nn.KLDivLoss(reduction="batchmean")
    final_loss = math.inf

    def make_batch():
        vels, poss = gen_trajectories(batch, T, rng)
        p0 = poss[:, 0] - vels[:, 0]
        if augment == "full_translation":
            off = rng.uniform(0, 1, size=(batch, 2))
            poss = (poss + off[:, None, :]) % 1.0
            p0 = (p0 + off) % 1.0
        elif augment == "random_shift":
            off = rng.normal(0, 0.05, size=(batch, 2))
            poss = np.clip(poss + off[:, None, :], 0, 1)
            p0 = np.clip(p0 + off, 0, 1)
        elif augment == "wrong_group":
            vels = vels[:, :, ::-1].copy()  # swap vx/vy: a wrong "symmetry"
        tgt = place_code(poss.reshape(-1, 2), centers, sigma).reshape(batch, T, Np)
        p0c = place_code(p0, centers, sigma)
        return (torch.tensor(vels, dtype=torch.float32, device=device),
                torch.tensor(p0c, dtype=torch.float32, device=device),
                torch.tensor(tgt, dtype=torch.float32, device=device))

    for _ in range(steps):
        vel, p0c, tgt = make_batch()
        logits, G_tr = model(vel, p0c)
        logp = torch.log_softmax(logits, dim=-1)
        loss = lossfn(logp.reshape(-1, Np), tgt.reshape(-1, Np))
        if activity_reg:
            loss = loss + activity_reg * (G_tr ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
        final_loss = float(loss.item())

    # ---- OOD: held-out fresh trajectories (and a position-decode accuracy) ----
    model.eval()
    with torch.no_grad():
        vel, p0c, tgt = make_batch()
        logits, _ = model(vel, p0c)
        pred_idx = logits.reshape(-1, Np).argmax(-1).cpu().numpy()
        true_idx = tgt.reshape(-1, Np).argmax(-1).cpu().numpy()
        # decode accuracy = predicted-vs-true nearest place cell within 1 bin
        pc = centers[pred_idx]; tc = centers[true_idx]
        ood_err = float(np.sqrt(((pc - tc) ** 2).sum(1)).mean())
        ood_acc = float((np.sqrt(((pc - tc) ** 2).sum(1)) <= (1.0 / (side - 1) + 1e-6)).mean())

    # ---- population manifold: bin hidden activity by position ----
    with torch.no_grad():
        vels, poss = gen_trajectories(256, T, rng)
        p0 = poss[:, 0] - vels[:, 0]
        p0c = place_code(p0, centers, sigma)
        _, G = model(torch.tensor(vels, dtype=torch.float32, device=device),
                     torch.tensor(p0c, dtype=torch.float32, device=device))
        G = G.reshape(-1, Ng).cpu().numpy()
        flatpos = poss.reshape(-1, 2)

    mside = 16
    bins = np.clip((flatpos * mside).astype(int), 0, mside - 1)
    bin_id = bins[:, 0] * mside + bins[:, 1]
    pop = np.zeros((mside * mside, Ng)); cnt = np.zeros(mside * mside)
    for k, g in zip(bin_id, G):
        pop[k] += g; cnt[k] += 1
    nonempty = cnt > 0
    pop[nonempty] /= cnt[nonempty, None]
    # fill empty bins with global mean so the grid is complete
    pop[~nonempty] = pop[nonempty].mean(axis=0) if nonempty.any() else 0.0
    rate_maps = pop.reshape(mside, mside, Ng).transpose(2, 0, 1)  # (units, side, side)

    return dict(
        seed=seed, augment=augment, final_loss=final_loss,
        ood_accuracy=ood_acc, ood_error=ood_err,
        population=pop, side=mside, rate_maps=rate_maps,
        coverage=float(nonempty.mean()),
    )
