#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal moved-location replication for Paper B ("concern deforms the metric").

This is the direct scale-up of `reward_deformation.py`, not the exponent-only
Newton sweep. It asks whether moving an injected concern/reward field moves the
induced metric deformation, and it repeats the measurement across three model
families:

  - rnn: the original recurrent path-integration harness
  - transformer: a causal Transformer sequence model over velocities
  - jepa: a JEPA-style predictive latent dynamics model

Primary pre-registered metrics are defined in
`papers/grid_cell_weakness/preregistration.md`.

Smoke:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal --with numpy modal run \\
            experiments/grid_cell_weakness/modal_reward_location_sweep.py \\
            --seeds 1 --steps 400 --archs rnn,transformer,jepa \\
            --locations 0.3:0.3 --out artifacts/grid_cell_weakness/reward_location_smoke.json

Scale:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal --with numpy modal run \\
            experiments/grid_cell_weakness/modal_reward_location_sweep.py \\
            --seeds 128 --steps 4000 --ng 256 --np 256 \\
            --archs rnn,transformer,jepa \\
            --out artifacts/grid_cell_weakness/reward_location_sweep_2026_07_02.json
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
)

app = modal.App(name="research-derived-reward-location")


def _place_cells(side: int):
    import numpy as np

    xs = np.linspace(0.0, 1.0, side)
    x, y = np.meshgrid(xs, xs, indexing="ij")
    return np.stack([x.ravel(), y.ravel()], axis=1)


def _place_code(pos, centers, sigma: float):
    import numpy as np

    d2 = ((pos[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
    logits = -d2 / (2 * sigma**2)
    logits = logits - logits.max(1, keepdims=True)
    e = np.exp(logits)
    return e / e.sum(1, keepdims=True)


def _trajectories(batch: int, steps: int, rng, speed: float = 0.06):
    import numpy as np

    pos = rng.uniform(0.1, 0.9, size=(batch, 2))
    vels = np.zeros((batch, steps, 2))
    poss = np.zeros((batch, steps, 2))
    heading = rng.uniform(0, 2 * math.pi, size=batch)
    for t in range(steps):
        heading = heading + rng.normal(0, 0.4, size=batch)
        vel = speed * np.stack([np.cos(heading), np.sin(heading)], axis=1)
        npos = pos + vel
        for dim in range(2):
            lo = npos[:, dim] < 0.0
            hi = npos[:, dim] > 1.0
            npos[lo, dim] = -npos[lo, dim]
            npos[hi, dim] = 2.0 - npos[hi, dim]
            heading[lo | hi] = heading[lo | hi] + math.pi
        vel = npos - pos
        vels[:, t] = vel
        poss[:, t] = npos
        pos = npos
    return vels, poss


def _reward_field(side: int, xy: list[float], strength: float, width: float):
    import numpy as np

    xs = np.linspace(0.0, 1.0, side)
    x, y = np.meshgrid(xs, xs, indexing="ij")
    d2 = (x - xy[0]) ** 2 + (y - xy[1]) ** 2
    return 1.0 + strength * np.exp(-d2 / (2 * width**2))


def _reward_weights(pos, xy: list[float] | None, strength: float, width: float):
    import numpy as np

    if xy is None:
        return np.ones(pos.shape[0])
    d2 = ((pos - np.array(xy)) ** 2).sum(1)
    return 1.0 + strength * np.exp(-d2 / (2 * width**2))


def _area_density(pop, side: int):
    import numpy as np

    grid = pop.reshape(side, side, -1)
    dx = 1.0 / (side - 1)
    area = np.full((side, side), np.nan)
    stretch = np.full((side, side), np.nan)
    for i in range(1, side - 1):
        for j in range(1, side - 1):
            du = (grid[i + 1, j] - grid[i - 1, j]) / (2 * dx)
            dv = (grid[i, j + 1] - grid[i, j - 1]) / (2 * dx)
            g00 = float(du @ du)
            g11 = float(dv @ dv)
            g01 = float(du @ dv)
            area[i, j] = math.sqrt(max(0.0, g00 * g11 - g01 * g01))
            stretch[i, j] = 0.5 * (math.sqrt(max(0.0, g00)) + math.sqrt(max(0.0, g11)))
    return area, stretch


def _xy_to_bin(xy: list[float], side: int) -> tuple[int, int]:
    return (int(round(xy[0] * (side - 1))), int(round(xy[1] * (side - 1))))


def _region_mean(field, xy: list[float], radius: int = 2) -> float:
    import numpy as np

    side = field.shape[0]
    ci, cj = _xy_to_bin(xy, side)
    vals = []
    for i in range(max(1, ci - radius), min(side - 1, ci + radius + 1)):
        for j in range(max(1, cj - radius), min(side - 1, cj + radius + 1)):
            val = field[i, j]
            if np.isfinite(val):
                vals.append(float(val))
    return float(np.mean(vals)) if vals else float("nan")


def _rank_percentile(field, xy: list[float], radius: int = 2) -> float:
    import numpy as np

    reward_val = _region_mean(field, xy, radius)
    vals = field[np.isfinite(field)]
    if vals.size == 0 or not np.isfinite(reward_val):
        return float("nan")
    return float((vals <= reward_val).mean())


def _peak_error(field, xy: list[float]) -> float:
    import numpy as np

    mask = np.isfinite(field)
    if not mask.any():
        return float("nan")
    idx = int(np.nanargmax(np.where(mask, field, np.nan)))
    side = field.shape[0]
    i, j = divmod(idx, side)
    peak = np.array([i / (side - 1), j / (side - 1)])
    return float(np.sqrt(((peak - np.array(xy)) ** 2).sum()))


def _top_com_error(field, xy: list[float], quantile: float = 0.9) -> float:
    import numpy as np

    vals = field[np.isfinite(field)]
    if vals.size == 0:
        return float("nan")
    cutoff = float(np.quantile(vals, quantile))
    weights = np.where(np.isfinite(field) & (field >= cutoff), np.maximum(field - cutoff, 0.0), 0.0)
    if float(weights.sum()) <= 0:
        return float("nan")
    side = field.shape[0]
    xs = np.linspace(0.0, 1.0, side)
    x, y = np.meshgrid(xs, xs, indexing="ij")
    com = np.array([(x * weights).sum() / weights.sum(), (y * weights).sum() / weights.sum()])
    return float(np.sqrt(((com - np.array(xy)) ** 2).sum()))


def _pearson(a, b) -> float:
    import numpy as np

    av = np.asarray(a, dtype=float).ravel()
    bv = np.asarray(b, dtype=float).ravel()
    m = np.isfinite(av) & np.isfinite(bv)
    if int(m.sum()) < 4:
        return float("nan")
    av = av[m] - av[m].mean()
    bv = bv[m] - bv[m].mean()
    den = float(np.sqrt((av @ av) * (bv @ bv)))
    return float((av @ bv) / den) if den > 0 else float("nan")


def _metric_observables(pop, side: int, xy: list[float], locations: list[list[float]],
                        strength: float, width: float) -> dict[str, float]:
    import numpy as np

    area, stretch = _area_density(pop, side)
    reward = _reward_field(side, xy, strength, width)

    def field_metrics(field, prefix: str) -> dict[str, float]:
        log_field = np.log(field + 1e-12)
        finite = np.isfinite(log_field)
        mu = float(np.nanmean(log_field[finite])) if finite.any() else 0.0
        sd = float(np.nanstd(log_field[finite])) if finite.any() else 1.0
        z_field = (log_field - mu) / (sd + 1e-9)
        reward_z = _region_mean(z_field, xy, radius=2)
        wrong = [_region_mean(z_field, loc, radius=2) for loc in locations
                 if math.dist(loc, xy) > 1e-6]
        wrong = [x for x in wrong if math.isfinite(x)]
        wrong_z = float(np.mean(wrong)) if wrong else float("nan")
        return {
            f"{prefix}reward_z": reward_z,
            f"{prefix}wrong_z_mean": wrong_z,
            f"{prefix}specificity_z": reward_z - wrong_z if math.isfinite(wrong_z) else float("nan"),
            f"{prefix}reward_rank_percentile": _rank_percentile(log_field, xy, radius=2),
            f"{prefix}peak_error": _peak_error(log_field, xy),
            f"{prefix}top10_com_error": _top_com_error(log_field, xy),
            f"{prefix}spatial_corr_reward_log_metric": _pearson(reward, log_field),
        }

    primary = field_metrics(stretch, "")
    companion = field_metrics(area, "area_")
    return {
        **primary,
        **companion,
        "mean_area": float(np.nanmean(area)),
        "mean_stretch": float(np.nanmean(stretch)),
    }


@app.function(
    image=IMAGE,
    gpu="H100",
    timeout=7200,
    memory=32768,
    max_containers=256,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> list[dict[str, Any]]:
    import numpy as np
    import torch
    import torch.nn as nn

    torch.set_float32_matmul_precision("high")

    arch = arg["arch"]
    condition = arg["condition"]
    seed = int(arg["seed"])
    xy = arg.get("xy")
    locations = arg["locations"]
    ng = int(arg["Ng"])
    np_cells = int(arg["Np"])
    sig_pc = float(arg["sig_pc"])
    reward_strength = float(arg["reward_strength"])
    reward_width = float(arg["reward_width"])
    T = int(arg["T"])
    train_steps = int(arg["steps"])
    batch = int(arg["batch"])
    noise_std = float(arg["noise_std"])

    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    side = int(round(math.sqrt(np_cells)))
    centers = _place_cells(side)
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    class RNNModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Linear(np_cells, ng)
            self.rnn = nn.RNNCell(2, ng, nonlinearity="relu")
            self.dec = nn.Linear(ng, np_cells)

        def forward(self, vel, p0, target=None):
            h = self.enc(p0)
            states = []
            for t in range(vel.shape[1]):
                h = self.rnn(vel[:, t], h)
                h = h / (h.norm(dim=-1, keepdim=True) + 1e-6)
                states.append(h)
            G = torch.stack(states, 1)
            return self.dec(G + noise_std * torch.randn_like(G)), G, None

    class TransformerModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.p0 = nn.Linear(np_cells, ng)
            self.vel = nn.Linear(2, ng)
            self.pos = nn.Parameter(torch.randn(1, 64, ng) * 0.02)
            layer = nn.TransformerEncoderLayer(
                d_model=ng,
                nhead=4,
                dim_feedforward=4 * ng,
                dropout=0.0,
                activation="gelu",
                batch_first=True,
                norm_first=True,
            )
            self.tr = nn.TransformerEncoder(layer, num_layers=2)
            self.dec = nn.Linear(ng, np_cells)

        def forward(self, vel, p0, target=None):
            steps = vel.shape[1]
            tok = self.vel(vel) + self.p0(p0).unsqueeze(1) + self.pos[:, :steps]
            mask = torch.triu(torch.full((steps, steps), float("-inf"), device=vel.device), diagonal=1)
            G = self.tr(tok, mask=mask)
            G = G / (G.norm(dim=-1, keepdim=True) + 1e-6)
            return self.dec(G + noise_std * torch.randn_like(G)), G, None

    class JEPAModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Sequential(nn.Linear(np_cells, ng), nn.GELU(), nn.Linear(ng, ng))
            self.pred = nn.Sequential(nn.Linear(ng + 2, 2 * ng), nn.GELU(), nn.Linear(2 * ng, ng))
            self.dec = nn.Linear(ng, np_cells)

        def encode(self, place):
            z = self.enc(place)
            return z / (z.norm(dim=-1, keepdim=True) + 1e-6)

        def forward(self, vel, p0, target=None):
            z = self.encode(p0)
            states = []
            for t in range(vel.shape[1]):
                z = self.pred(torch.cat([z, vel[:, t]], dim=-1))
                z = z / (z.norm(dim=-1, keepdim=True) + 1e-6)
                states.append(z)
            G = torch.stack(states, 1)
            aux = None
            if target is not None:
                with torch.no_grad():
                    target_z = self.encode(target.reshape(-1, np_cells)).reshape(target.shape[0], target.shape[1], ng)
                aux = ((G - target_z) ** 2).mean(-1).reshape(-1)
            return self.dec(G + noise_std * torch.randn_like(G)), G, aux

    if arch == "transformer":
        model = TransformerModel().to(dev)
    elif arch == "jepa":
        model = JEPAModel().to(dev)
    else:
        model = RNNModel().to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    def batch_data():
        vels, poss = _trajectories(batch, T, rng)
        p0 = poss[:, 0] - vels[:, 0]
        tgt = _place_code(poss.reshape(-1, 2), centers, sig_pc).reshape(batch, T, np_cells)
        p0c = _place_code(p0, centers, sig_pc)
        weight_xy = xy if condition == "reward" else None
        weights = _reward_weights(poss.reshape(-1, 2), weight_xy, reward_strength, reward_width)
        weights = weights / weights.mean()
        return (
            torch.tensor(vels, dtype=torch.float32, device=dev),
            torch.tensor(p0c, dtype=torch.float32, device=dev),
            torch.tensor(tgt, dtype=torch.float32, device=dev),
            torch.tensor(weights, dtype=torch.float32, device=dev),
        )

    final_loss = math.inf
    for _ in range(train_steps):
        vel, p0c, target, weights = batch_data()
        logits, _, aux = model(vel, p0c, target)
        logp = torch.log_softmax(logits, -1).reshape(-1, np_cells)
        kl = (target.reshape(-1, np_cells) * (torch.log(target.reshape(-1, np_cells) + 1e-9) - logp)).sum(-1)
        loss = (weights * kl).mean()
        if aux is not None:
            loss = loss + 0.5 * (weights * aux).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        final_loss = float(loss.item())

    model.eval()
    with torch.no_grad():
        vels, poss = _trajectories(int(arg["eval_batch"]), T, rng)
        p0 = poss[:, 0] - vels[:, 0]
        p0c = _place_code(p0, centers, sig_pc)
        _, G, _ = model(
            torch.tensor(vels, dtype=torch.float32, device=dev),
            torch.tensor(p0c, dtype=torch.float32, device=dev),
            None,
        )
        hidden = G.reshape(-1, ng).cpu().numpy()
        flat_pos = poss.reshape(-1, 2)

    bins = np.clip((flat_pos * side).astype(int), 0, side - 1)
    ids = bins[:, 0] * side + bins[:, 1]
    pop = np.zeros((side * side, ng))
    count = np.zeros(side * side)
    for idx, h in zip(ids, hidden):
        pop[idx] += h
        count[idx] += 1
    nonempty = count > 0
    pop[nonempty] /= count[nonempty, None]
    pop[~nonempty] = pop[nonempty].mean(0) if nonempty.any() else 0.0

    eval_locs = locations if condition == "control" else [xy]
    rows = []
    for loc in eval_locs:
        metrics = _metric_observables(pop, side, loc, locations, reward_strength, reward_width)
        rows.append({
            "arch": arch,
            "condition": condition,
            "seed": seed,
            "reward_xy": loc,
            "final_loss": final_loss,
            "coverage": float(nonempty.mean()),
            "side": side,
            "Ng": ng,
            **metrics,
        })
    return rows


def _boot_stat(vals, n_boot: int = 5000) -> dict[str, float]:
    import numpy as np

    arr = np.array([v for v in vals if np.isfinite(v)], dtype=float)
    if arr.size == 0:
        return {"mean": float("nan"), "se": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    if arr.size == 1:
        val = float(arr[0])
        return {"mean": val, "se": float("nan"), "ci95": [val, val], "n": 1}
    rng = np.random.default_rng(0)
    boot = np.empty(n_boot)
    for i in range(n_boot):
        boot[i] = arr[rng.integers(0, arr.size, arr.size)].mean()
    return {
        "mean": float(arr.mean()),
        "se": float(boot.std(ddof=1)),
        "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "n": int(arr.size),
    }


def _balanced_arch_stat(groups: dict[str, list[float]], n_boot: int = 5000) -> dict[str, float]:
    import numpy as np

    clean = {k: np.array([v for v in vals if np.isfinite(v)], dtype=float)
             for k, vals in groups.items()}
    clean = {k: v for k, v in clean.items() if v.size > 0}
    if not clean:
        return {"mean": float("nan"), "se": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    means = [float(v.mean()) for v in clean.values()]
    rng = np.random.default_rng(1)
    boot = np.empty(n_boot)
    keys = sorted(clean)
    for i in range(n_boot):
        arch_means = []
        for key in keys:
            vals = clean[key]
            arch_means.append(float(vals[rng.integers(0, vals.size, vals.size)].mean()))
        boot[i] = float(np.mean(arch_means))
    return {
        "mean": float(np.mean(means)),
        "se": float(boot.std(ddof=1)),
        "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "n": int(sum(v.size for v in clean.values())),
    }


def _loc_key(xy: list[float]) -> str:
    return f"{xy[0]:.3f},{xy[1]:.3f}"


def _summarize(rows: list[dict[str, Any]], target_se: float) -> dict[str, Any]:
    controls = {
        (r["arch"], r["seed"], _loc_key(r["reward_xy"])): r
        for r in rows
        if r["condition"] == "control"
    }
    reward_rows = [dict(r) for r in rows if r["condition"] == "reward"]
    for row in reward_rows:
        ctrl = controls.get((row["arch"], row["seed"], _loc_key(row["reward_xy"])))
        row["control_reward_z"] = ctrl["reward_z"] if ctrl else float("nan")
        row["control_subtracted_lift_z"] = row["reward_z"] - row["control_reward_z"]

    archs = sorted({r["arch"] for r in reward_rows})
    summary: dict[str, Any] = {
        "target_bootstrap_se": target_se,
        "architectures": {},
        "pooled_architecture_balanced": {},
        "rows_reward": len(reward_rows),
        "rows_control": len(rows) - len(reward_rows),
    }
    primary_by_arch: dict[str, list[float]] = {}
    spec_by_arch: dict[str, list[float]] = {}
    for arch in archs:
        ars = [r for r in reward_rows if r["arch"] == arch]
        lift = [r["control_subtracted_lift_z"] for r in ars]
        spec = [r["specificity_z"] for r in ars]
        primary_by_arch[arch] = lift
        spec_by_arch[arch] = spec
        arch_summary = {
            "control_subtracted_lift_z": _boot_stat(lift),
            "specificity_z": _boot_stat(spec),
            "reward_rank_percentile": _boot_stat([r["reward_rank_percentile"] for r in ars]),
            "spatial_corr_reward_log_metric": _boot_stat([r["spatial_corr_reward_log_metric"] for r in ars]),
            "peak_error": _boot_stat([r["peak_error"] for r in ars]),
            "top10_com_error": _boot_stat([r["top10_com_error"] for r in ars]),
            "area_control_subtracted_lift_z": _boot_stat([
                r["area_reward_z"] - controls.get(
                    (r["arch"], r["seed"], _loc_key(r["reward_xy"])), {}
                ).get("area_reward_z", float("nan"))
                for r in ars
            ]),
            "area_specificity_z": _boot_stat([r["area_specificity_z"] for r in ars]),
            "area_reward_rank_percentile": _boot_stat([r["area_reward_rank_percentile"] for r in ars]),
            "area_spatial_corr_reward_log_metric": _boot_stat([r["area_spatial_corr_reward_log_metric"] for r in ars]),
            "final_loss": _boot_stat([r["final_loss"] for r in ars]),
            "coverage": _boot_stat([r["coverage"] for r in ars]),
            "locations": {},
        }
        lift_stat = arch_summary["control_subtracted_lift_z"]
        spec_stat = arch_summary["specificity_z"]
        rank_stat = arch_summary["reward_rank_percentile"]
        arch_summary["gate"] = {
            "lift_positive": lift_stat["ci95"][0] > 0,
            "specificity_positive": spec_stat["ci95"][0] > 0,
            "lift_se_le_target": lift_stat["se"] <= target_se,
            "specificity_se_le_target": spec_stat["se"] <= target_se,
            "rank_above_chance": rank_stat["mean"] > 0.5,
        }
        arch_summary["gate"]["pass"] = all(arch_summary["gate"].values())
        for loc in sorted({_loc_key(r["reward_xy"]) for r in ars}):
            lrs = [r for r in ars if _loc_key(r["reward_xy"]) == loc]
            arch_summary["locations"][loc] = {
                "control_subtracted_lift_z": _boot_stat([r["control_subtracted_lift_z"] for r in lrs]),
                "specificity_z": _boot_stat([r["specificity_z"] for r in lrs]),
                "reward_rank_percentile": _boot_stat([r["reward_rank_percentile"] for r in lrs]),
                "peak_error": _boot_stat([r["peak_error"] for r in lrs]),
            }
        summary["architectures"][arch] = arch_summary

    summary["pooled_architecture_balanced"]["control_subtracted_lift_z"] = _balanced_arch_stat(primary_by_arch)
    summary["pooled_architecture_balanced"]["specificity_z"] = _balanced_arch_stat(spec_by_arch)
    pooled_lift = summary["pooled_architecture_balanced"]["control_subtracted_lift_z"]
    pooled_spec = summary["pooled_architecture_balanced"]["specificity_z"]
    summary["pooled_architecture_balanced"]["gate"] = {
        "lift_positive": pooled_lift["ci95"][0] > 0,
        "specificity_positive": pooled_spec["ci95"][0] > 0,
        "lift_se_le_target": pooled_lift["se"] <= target_se,
        "specificity_se_le_target": pooled_spec["se"] <= target_se,
    }
    summary["pooled_architecture_balanced"]["gate"]["pass"] = all(
        summary["pooled_architecture_balanced"]["gate"].values()
    )
    return summary


def _parse_locations(spec: str) -> list[list[float]]:
    if not spec.strip():
        vals = [0.25, 0.50, 0.75]
        return [[x, y] for x in vals for y in vals]
    locs = []
    for part in spec.split(";"):
        if not part.strip():
            continue
        a, b = part.split(":")
        locs.append([float(a), float(b)])
    return locs


@app.local_entrypoint()
def main(seeds: int = 64, steps: int = 4000, ng: int = 256, np: int = 256,
         sig_pc: float = 0.09, t: int = 20, batch: int = 128, eval_batch: int = 1024,
         noise_std: float = 0.15, reward_strength: float = 6.0, reward_width: float = 0.12,
         archs: str = "rnn,transformer,jepa", locations: str = "", base_seed: int = 20260702,
         target_se: float = 0.01,
         out: str = "artifacts/grid_cell_weakness/reward_location_sweep_2026_07_02.json"):
    arch_list = [a.strip() for a in archs.split(",") if a.strip()]
    loc_list = _parse_locations(locations)
    cells: list[dict[str, Any]] = []
    for arch in arch_list:
        for k in range(seeds):
            seed = base_seed + 100 * k
            cells.append({
                "arch": arch,
                "condition": "control",
                "seed": seed,
                "xy": None,
                "locations": loc_list,
                "Ng": ng,
                "Np": np,
                "sig_pc": sig_pc,
                "T": t,
                "steps": steps,
                "batch": batch,
                "eval_batch": eval_batch,
                "noise_std": noise_std,
                "reward_strength": reward_strength,
                "reward_width": reward_width,
            })
            for loc in loc_list:
                cells.append({
                    "arch": arch,
                    "condition": "reward",
                    "seed": seed,
                    "xy": loc,
                    "locations": loc_list,
                    "Ng": ng,
                    "Np": np,
                    "sig_pc": sig_pc,
                    "T": t,
                    "steps": steps,
                    "batch": batch,
                    "eval_batch": eval_batch,
                    "noise_std": noise_std,
                    "reward_strength": reward_strength,
                    "reward_width": reward_width,
                })

    print(
        f"[reward-location] dispatching {len(cells)} cells: archs={arch_list} "
        f"locations={len(loc_list)} seeds={seeds} Ng={ng} Np={np} steps={steps}"
    )
    chunks = [chunk for chunk in run_cell.map(cells) if chunk]
    rows = [row for chunk in chunks for row in chunk]
    summary = _summarize(rows, target_se)
    payload = {
        "kind": "moved-location reward-deformation sweep",
        "manifest": {
            "architectures": arch_list,
            "locations": loc_list,
            "seeds": seeds,
            "base_seed": base_seed,
            "steps": steps,
            "Ng": ng,
            "Np": np,
            "T": t,
            "batch": batch,
            "eval_batch": eval_batch,
            "noise_std": noise_std,
            "reward_strength": reward_strength,
            "reward_width": reward_width,
            "target_bootstrap_se": target_se,
        },
        "summary": summary,
        "rows": rows,
    }
    op = Path(out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[reward-location] wrote {op}")
    for arch, item in summary["architectures"].items():
        lift = item["control_subtracted_lift_z"]
        spec = item["specificity_z"]
        rank = item["reward_rank_percentile"]
        print(
            f"  {arch:12s} lift={lift['mean']:+.4f} SE={lift['se']:.4f} "
            f"CI[{lift['ci95'][0]:+.4f},{lift['ci95'][1]:+.4f}] ; "
            f"spec={spec['mean']:+.4f} SE={spec['se']:.4f} "
            f"CI[{spec['ci95'][0]:+.4f},{spec['ci95'][1]:+.4f}] ; "
            f"rank={rank['mean']:.3f} pass={item['gate']['pass']}"
        )
    pooled = summary["pooled_architecture_balanced"]
    print(
        "[reward-location] pooled "
        f"lift={pooled['control_subtracted_lift_z']['mean']:+.4f} "
        f"SE={pooled['control_subtracted_lift_z']['se']:.4f}; "
        f"spec={pooled['specificity_z']['mean']:+.4f} "
        f"SE={pooled['specificity_z']['se']:.4f}; pass={pooled['gate']['pass']}"
    )
