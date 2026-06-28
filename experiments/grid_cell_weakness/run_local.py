#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Local CPU sweep for Paper A -- a complete (slower) run when Modal is unavailable.

Trains real path-integration RNNs at emergence scale on CPU, computes the four
pre-registered metrics per net, aggregates Spearman correlations + gates, and
writes results incrementally (so a slow/interrupted run still yields real data).

Run:  python experiments/grid_cell_weakness/run_local.py \
          --steps 4000 --seeds 2 --conditions full_translation,none,wrong_group

Writes (gitignored raw + committed report is hand-written from this JSON):
  artifacts/grid_cell_weakness/local_sweep.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

import core


def spearman(xs, ys) -> float:
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    ok = np.isfinite(xs) & np.isfinite(ys)
    xs, ys = xs[ok], ys[ok]
    if len(xs) < 2:
        return 0.0
    rx = np.argsort(np.argsort(xs)).astype(float); ry = np.argsort(np.argsort(ys)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    den = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / den) if den else 0.0


def partial(r_wo, r_wt, r_ot) -> float:
    den = math.sqrt(max(1e-9, (1 - r_wt ** 2) * (1 - r_ot ** 2)))
    return (r_wo - r_wt * r_ot) / den


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", default="full_translation,none,wrong_group")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--Ng", type=int, default=128)
    ap.add_argument("--Np", type=int, default=100)
    ap.add_argument("--sigma", type=float, default=0.10)
    ap.add_argument("--T", type=int, default=20)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--activity-reg", type=float, default=2e-3)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
    ap.add_argument("--base-seed", type=int, default=20260628)
    ap.add_argument("--out", default="artifacts/grid_cell_weakness/local_sweep.json")
    args = ap.parse_args()

    conds = [c.strip() for c in args.conditions.split(",") if c.strip()]
    seeds = [args.base_seed + 100 * k for k in range(args.seeds)]
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)

    manifest = dict(conditions=conds, seeds=seeds, steps=args.steps, Ng=args.Ng,
                    Np=args.Np, sigma=args.sigma, T=args.T, batch=args.batch,
                    activity_reg=args.activity_reg, weight_decay=args.weight_decay,
                    backend="local-cpu")
    cells = []

    def flush():
        out.write_text(json.dumps(dict(kind="LOCAL CPU sweep (Paper A)",
                                        manifest=manifest, cells=cells), indent=2,
                                   sort_keys=True, default=float) + "\n")

    t0 = time.time()
    for cond in conds:
        for seed in seeds:
            tc = time.time()
            r = core.train_pi_rnn(seed, augment=cond, Ng=args.Ng, Np=args.Np,
                                  sigma=args.sigma, T=args.T, steps=args.steps,
                                  batch=args.batch, weight_decay=args.weight_decay,
                                  activity_reg=args.activity_reg)
            w = core.weakness_translation(r["population"], r["side"], rng=np.random.default_rng(seed))
            t = core.toroidal_score(r["population"], rng=np.random.default_rng(seed))
            f = core.fourier_participation_ratio(r["rate_maps"])
            cell = dict(
                augment=cond, seed=seed, final_loss=r["final_loss"],
                ood_accuracy=r["ood_accuracy"], ood_error=r["ood_error"],
                coverage=r["coverage"],
                weakness_translation=w["weakness_translation"],
                toroidal_score=t.get("toroidal_score", float("nan")),
                betti1_estimate=t.get("betti1_estimate", -1),
                betti_match_torus=t.get("betti_match_torus", False),
                h1_top2=t.get("h1_top2"), h2_top=t.get("h2_top"),
                fourier_pr=f.get("fourier_pr", float("nan")),
                seconds=round(time.time() - tc, 1),
            )
            cells.append(cell); flush()
            print(f"[local] {cond:18s} seed={seed} loss={cell['final_loss']:.3f} "
                  f"ood={cell['ood_accuracy']:.3f} weak={cell['weakness_translation']:.3f} "
                  f"topo={cell['toroidal_score']:.3f} b1={cell['betti1_estimate']} "
                  f"match={cell['betti_match_torus']} ({cell['seconds']}s)")

    # aggregate
    def col(key, where=None):
        return [c[key] for c in cells if (where is None or c["augment"] in where)]
    w, topo, ood, fpr = col("weakness_translation"), col("toroidal_score"), col("ood_accuracy"), col("fourier_pr")
    r_wt, r_wo, r_ot = spearman(w, topo), spearman(w, ood), spearman(topo, ood)
    mean = lambda xs: (sum(xs) / len(xs)) if xs else float("nan")
    ft = [c for c in cells if c["augment"] == "full_translation"]
    analysis = dict(
        n_cells=len(cells),
        rho_weakness_topology=r_wt, rho_weakness_ood=r_wo, rho_topology_ood=r_ot,
        rho_weakness_neg_fourier_pr=spearman(w, [-v for v in fpr]),
        partial_weakness_ood_given_topology=partial(r_wo, r_wt, r_ot),
        G1_full_translation_betti_match_rate=(sum(c["betti_match_torus"] for c in ft) / len(ft)) if ft else 0.0,
        G6_full_vs_none_topo=dict(full=mean(col("toroidal_score", {"full_translation"})),
                                  none=mean(col("toroidal_score", {"none"}))),
        elapsed_sec=round(time.time() - t0, 1),
    )
    manifest["analysis"] = analysis
    flush()
    print(f"[local] DONE {analysis['n_cells']} cells in {analysis['elapsed_sec']}s")
    print(f"[local] rho(weakness,topology)={r_wt:.3f} rho(weakness,OOD)={r_wo:.3f} "
          f"G1 full-transl betti-match={analysis['G1_full_translation_betti_match_rate']:.2f}")


if __name__ == "__main__":
    main()
