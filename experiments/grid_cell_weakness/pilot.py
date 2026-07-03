#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Local design pilot for Paper A (papers/grid_cell_weakness/preregistration.md).

Two jobs, in order of importance:

  (1) METRIC DISCRIMINATION (the headline pilot check): on synthetic manifolds
      with known topology (torus / plane / sphere), confirm the harness's
      topology + weakness measurements actually separate a toroidal code from a
      plane or sphere. If the metrics cannot tell a torus from a plane, no
      amount of Modal compute matters. This is cheap and decisive.

  (2) END-TO-END SMOKE: train a few tiny path-integration RNNs on CPU across
      augmentation conditions and confirm the full per-network pipeline
      (train -> weakness -> topology -> fourier -> OOD) runs and produces sane,
      finite numbers. Pilot-scale nets are NOT expected to pass the
      pre-registered gates (grid-cell emergence needs the Modal sweep); the
      pilot only validates the harness end to end.

Run (local, CPU):  python experiments/grid_cell_weakness/pilot.py
Writes:  artifacts/grid_cell_weakness/pilot.json
         experiments/grid_cell_weakness/results/pilot_<date>.md  (hand-committed)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

import core  # local module (run from this directory or with repo root on path)


def metric_discrimination(rng: np.random.Generator) -> dict:
    n = 256
    out = {}
    for name, sampler in [("torus", core.sample_torus),
                          ("plane", core.sample_plane),
                          ("sphere", core.sample_sphere)]:
        m = sampler(n, rng, noise=0.02)
        w = core.weakness_translation(m["points"], m["side"], rng=np.random.default_rng(0))
        t = core.toroidal_score(m["points"], rng=np.random.default_rng(0))
        out[name] = dict(weakness=w, topology=t)
    # the discriminating claim: torus scores highest on toroidal_score and is
    # the only one with a betti-2-loop + void match
    scores = {k: out[k]["topology"].get("toroidal_score", float("nan")) for k in out}
    betti = {k: out[k]["topology"].get("betti_match_torus", False) for k in out}
    discriminates = (
        out["torus"]["topology"].get("available", False)
        and scores["torus"] == max(scores.values())
        and betti["torus"] and not betti["plane"] and not betti["sphere"]
    )
    return dict(per_manifold=out, toroidal_scores=scores, betti_match=betti,
                DISCRIMINATES=bool(discriminates))


def spearman(xs, ys) -> float:
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    if len(xs) < 2:
        return 0.0

    def rank(vals):
        order = np.argsort(vals)
        ranks = np.empty(len(vals), dtype=float)
        i = 0
        while i < len(vals):
            j = i
            while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            ranks[order[i:j + 1]] = (i + j) / 2.0
            i = j + 1
        return ranks

    rx = rank(xs)
    ry = rank(ys)
    rx -= rx.mean(); ry -= ry.mean()
    den = math.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / den) if den else 0.0


def end_to_end_smoke() -> dict:
    conditions = ["full_translation", "none", "wrong_group"]
    seeds = [20260628, 20260629]
    nets = []
    for aug in conditions:
        for seed in seeds:
            r = core.train_pi_rnn(seed, augment=aug, steps=200, T=18, batch=64)
            w = core.weakness_translation(r["population"], r["side"],
                                          rng=np.random.default_rng(seed))
            t = core.toroidal_score(r["population"], rng=np.random.default_rng(seed))
            f = core.fourier_participation_ratio(r["rate_maps"])
            nets.append(dict(
                augment=aug, seed=seed, final_loss=r["final_loss"],
                ood_accuracy=r["ood_accuracy"], ood_error=r["ood_error"],
                coverage=r["coverage"],
                weakness_translation=w["weakness_translation"],
                toroidal_score=t.get("toroidal_score", float("nan")),
                betti1_estimate=t.get("betti1_estimate", -1),
                fourier_pr=f.get("fourier_pr", float("nan")),
            ))
    w = [float(x["weakness_translation"]) for x in nets]
    topo = [float(x["toroidal_score"]) for x in nets]
    ood = [float(x["ood_accuracy"]) for x in nets]
    fpr = [float(x["fourier_pr"]) for x in nets]
    corr = dict(
        rho_weakness_topology=spearman(w, topo),
        rho_weakness_ood=spearman(w, ood),
        rho_weakness_neg_fourier_pr=spearman(w, [-float(v) for v in fpr]),
        n_nets=len(nets),
        note="pilot-scale; correlations are directional sanity only, not gate evidence",
    )
    return dict(nets=nets, correlations=corr)


def main() -> None:
    rng = np.random.default_rng(0)
    print("[pilot] (1) metric discrimination on synthetic manifolds ...")
    disc = metric_discrimination(rng)
    print(f"[pilot]   toroidal_scores = "
          f"{ {k: round(v,3) for k,v in disc['toroidal_scores'].items()} }")
    print(f"[pilot]   DISCRIMINATES torus vs plane/sphere = {disc['DISCRIMINATES']}")

    print("[pilot] (2) end-to-end RNN smoke across augmentation conditions ...")
    smoke = end_to_end_smoke()
    print(f"[pilot]   trained {smoke['correlations']['n_nets']} nets; "
          f"rho(weakness,topology)={smoke['correlations']['rho_weakness_topology']:.2f}, "
          f"rho(weakness,OOD)={smoke['correlations']['rho_weakness_ood']:.2f}")

    payload = dict(
        kind="LOCAL design pilot (CPU) -- harness validation only",
        preregistration="papers/grid_cell_weakness/preregistration.md",
        metric_discrimination=disc,
        end_to_end_smoke=smoke,
    )
    out = Path("artifacts/grid_cell_weakness/pilot.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n")
    print(f"[pilot] wrote {out}")


if __name__ == "__main__":
    main()
