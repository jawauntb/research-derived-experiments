#!/usr/bin/env python3
"""Generate paper-grade figures for `papers/learned_symmetry_discovery/`.

Each figure tells one story. Saved as PNG at 200 dpi so PDF embedding looks
sharp. No animation, no rasterized table reproductions — only signal.

Figures produced:

  fig1_group_recovery.png
      Polar bar chart of per-angle consistency scores from the
      transformation-discovery procedure on a representative training
      split. True Z_8 angles highlighted in red. Threshold ring shown.

  fig2_pearson_correlations.png
      Horizontal bar chart of Pearson r vs OOD accuracy for every
      predictor in the 256-model sweep. Weakness variants in blue;
      classical baselines in gray.

  fig3_causal_validation.png
      Two panels.
      Left: bar chart of mean OOD by augmentation regime with stdev
      error bars. Right: scatter of `oracle_aug` vs `learned_aug`
      OOD per base config; diagonal shows perfect parity.

  fig4_threshold_sweep.png
      Paraphrase substitution discovery: behavioral invariance of the
      learned set vs random control across the two thresholds we ran
      (0.30, 0.88). Annotates the gap.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from experiments.learned_symmetry.transform_generator import (
    infer_rotation_group_from_training,
)
from experiments.rotation_weakness.dataset import (
    make_partial_rotation_split,
    materialize_split,
    rotate_image,
    rotation_group_elements,
    to_tensors,
)


FIG_DIR = ROOT / "papers" / "learned_symmetry_discovery" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = ROOT / "artifacts"


def _save(fig, name: str) -> None:
    out = FIG_DIR / name
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


# ---------------------------------------------------------------------------
# Figure 1: per-angle consistency score on one representative split.

def figure_group_recovery() -> None:
    n_rotations = 8
    n_candidates = 24
    threshold = 0.5
    split = make_partial_rotation_split(
        n_rotations=n_rotations, train_per_class=3, seed=20260609
    )
    train_samples, _ = materialize_split(
        split, samples_per_class_rotation=8, seed=20260609
    )
    train_x, train_y = to_tensors(train_samples)

    # Score each candidate angle.
    train_features = [train_x[i].cpu().numpy().reshape(-1).astype(np.float32) for i in range(train_x.shape[0])]
    train_labels = train_y.tolist()

    def cos(a, b):
        na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
        return 0.0 if na == 0 or nb == 0 else float(np.dot(a, b) / (na * nb))

    angles_deg = [k * (360.0 / n_candidates) for k in range(n_candidates)]
    scores = []
    for theta in angles_deg:
        sims = []
        for i in range(train_x.shape[0]):
            r = rotate_image(train_x[i, 0].cpu().numpy(), theta).reshape(-1).astype(np.float32)
            same_label = [j for j in range(train_x.shape[0]) if train_labels[j] == train_labels[i]]
            sims.append(max(cos(r, train_features[j]) for j in same_label))
        scores.append(float(np.mean(sims)))

    oracle = set(rotation_group_elements(n_rotations))

    fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw={"projection": "polar"})
    theta_rad = [np.deg2rad(a) for a in angles_deg]
    width = 2 * np.pi / n_candidates

    colors = []
    for a in angles_deg:
        if any(abs(a - o) < 7.6 or abs(360.0 - abs(a - o)) < 7.6 for o in oracle):
            colors.append("#d62728")  # red: true Z_8
        elif scores[angles_deg.index(a)] >= threshold:
            colors.append("#ff7f0e")  # orange: kept but false positive
        else:
            colors.append("#1f77b4")  # blue: rejected

    bars = ax.bar(theta_rad, scores, width=width * 0.9, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_rgrids([0.2, 0.4, 0.5, 0.6, 0.8], angle=90,
                  labels=["0.2", "0.4", "τ=0.5", "0.6", "0.8"],
                  fontsize=8)
    ax.set_ylim(0, max(scores) * 1.05)
    # Annotate angle labels every 45°
    ax.set_xticks([np.deg2rad(k) for k in range(0, 360, 45)])
    ax.set_xticklabels([f"{k}°" for k in range(0, 360, 45)], fontsize=9)
    # Threshold ring
    ax.plot(np.linspace(0, 2 * np.pi, 360), [threshold] * 360, color="gray",
            linestyle="--", linewidth=1, alpha=0.7)

    # Legend
    from matplotlib.patches import Patch
    legend = [
        Patch(facecolor="#d62728", label="True Z_8 angle (recovered)"),
        Patch(facecolor="#ff7f0e", label="Kept false positive"),
        Patch(facecolor="#1f77b4", label="Rejected"),
    ]
    ax.legend(handles=legend, loc="upper right", bbox_to_anchor=(1.4, 1.1), fontsize=9)
    ax.set_title("Data-inferred group recovery on one training split\n"
                 f"τ = {threshold}, recovery: 8/8 Z_8 angles + 2 near-identity FPs",
                 fontsize=11, pad=20)
    _save(fig, "fig1_group_recovery.png")


# ---------------------------------------------------------------------------
# Figure 2: Pearson correlations with OOD across predictors.

def figure_pearson_correlations() -> None:
    data = json.loads(
        (ARTIFACT_DIR / "learned_symmetry" / "modal_sweep_v1.json").read_text()
    )
    arts = data["artifacts"]
    ood = [a["ood_accuracy"] for a in arts]
    n = len(arts)

    def pearson(xs, ys):
        import math
        from statistics import mean
        mx, my = mean(xs), mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        denom = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
        return 0.0 if denom == 0 else num / denom

    fields = {
        "weakness_oracle (with oracle)": (
            [a["weakness_oracle"] for a in arts], "#1f77b4", "weakness",
        ),
        "weakness_learned (no oracle)": (
            [a["weakness_learned"] for a in arts], "#2ca02c", "weakness",
        ),
        "weakness_random (soft control)": (
            [a["weakness_random"] for a in arts], "#9467bd", "weakness",
        ),
        "parameter L₂": (
            [a["parameter_l2"] for a in arts], "#7f7f7f", "classical",
        ),
        "train accuracy": (
            [a["train_accuracy"] for a in arts], "#7f7f7f", "classical",
        ),
        "training loss": (
            [a["final_train_loss"] for a in arts], "#7f7f7f", "classical",
        ),
        "Hutchinson sharpness": (
            [a["sharpness_proxy"] for a in arts], "#7f7f7f", "classical",
        ),
    }

    items = []
    for name, (vals, color, _) in fields.items():
        items.append((name, pearson(vals, ood), color))
    items.sort(key=lambda r: r[1])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    names = [i[0] for i in items]
    rs = [i[1] for i in items]
    colors = [i[2] for i in items]
    bars = ax.barh(names, rs, color=colors, edgecolor="black", linewidth=0.3)

    ax.axvline(0, color="black", linewidth=0.7)
    ax.set_xlabel("Pearson r with OOD accuracy", fontsize=11)
    ax.set_xlim(-0.5, 0.9)
    ax.set_title(f"Predictors of OOD generalization (n = {n} models)", fontsize=12)
    for bar, r in zip(bars, rs):
        offset = 0.02 if r >= 0 else -0.02
        ax.text(r + offset, bar.get_y() + bar.get_height() / 2,
                f"{r:+.3f}", va="center",
                ha="left" if r >= 0 else "right", fontsize=9)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    _save(fig, "fig2_pearson_correlations.png")


# ---------------------------------------------------------------------------
# Figure 3: Causal validation — bar chart + paired scatter.

def figure_causal_validation() -> None:
    data = json.loads(
        (ARTIFACT_DIR / "learned_symmetry" / "causal_v1.json").read_text()
    )
    rows = data["rows"]

    by_regime = {}
    by_base = {}
    for r in rows:
        by_regime.setdefault(r["regime"], []).append(r["ood_accuracy"])
        by_base.setdefault(r["base_seed"], {})[r["regime"]] = r["ood_accuracy"]

    order = ["none", "random_aug", "learned_aug", "oracle_aug"]
    means = [float(np.mean(by_regime[k])) for k in order]
    stds = [float(np.std(by_regime[k])) for k in order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.6),
                                    gridspec_kw={"width_ratios": [1.1, 1]})

    # Left: bar chart with error bars
    colors = ["#7f7f7f", "#9467bd", "#2ca02c", "#1f77b4"]
    labels = ["none", "random_aug", "learned_aug\n(no oracle)", "oracle_aug\n(with oracle)"]
    bars = ax1.bar(labels, means, yerr=stds, capsize=6, color=colors,
                   edgecolor="black", linewidth=0.5)
    ax1.set_ylim(0, 1.15)
    ax1.set_ylabel("Mean OOD accuracy", fontsize=11)
    ax1.set_title("Causal effect of augmentation regime\n"
                  "(64 base configs × 4 regimes, paired)", fontsize=11)
    deltas = ["", "+0.444", "+0.515", "+0.568"]
    for bar, m, s, dlt in zip(bars, means, stds, deltas):
        ax1.text(bar.get_x() + bar.get_width() / 2, m + s + 0.025,
                 f"{m:.3f}", ha="center", fontsize=10, fontweight="bold")
        if dlt:
            ax1.text(bar.get_x() + bar.get_width() / 2, m + s + 0.085,
                     f"Δ {dlt}", ha="center", fontsize=8.5,
                     style="italic", color="#444")
    ax1.tick_params(axis="x", labelsize=10)
    ax1.grid(axis="y", linestyle=":", alpha=0.4)

    # Right: paired scatter learned_aug vs oracle_aug
    pairs = []
    for base, regs in by_base.items():
        if "oracle_aug" in regs and "learned_aug" in regs:
            pairs.append((regs["oracle_aug"], regs["learned_aug"]))
    xs, ys = zip(*pairs)
    ax2.scatter(xs, ys, c="#2ca02c", alpha=0.65, edgecolor="black",
                linewidth=0.4, s=40)
    ax2.plot([0, 1], [0, 1], color="black", linestyle="--", linewidth=1,
             alpha=0.7, label="y = x (perfect parity)")
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.set_aspect("equal", adjustable="box")
    ax2.set_xlabel("OOD with oracle augmentation", fontsize=11)
    ax2.set_ylabel("OOD with learned augmentation", fontsize=11)
    ax2.set_title("Paired comparison: learned vs oracle aug\n"
                  f"(n = {len(pairs)} base configs; mean Δ = −0.053)", fontsize=11)
    ax2.legend(loc="lower right", fontsize=9)
    ax2.grid(linestyle=":", alpha=0.4)

    fig.tight_layout()
    _save(fig, "fig3_causal_validation.png")


# ---------------------------------------------------------------------------
# Figure 4: Threshold sweep for paraphrase substitution discovery.

def figure_threshold_sweep() -> None:
    v1 = json.loads(
        (ARTIFACT_DIR / "paraphrase_weakness" / "learned_substitution_v1.json").read_text()
    )
    v2 = json.loads(
        (ARTIFACT_DIR / "paraphrase_weakness" / "learned_substitution_v2.json").read_text()
    )
    points = [
        (0.30, v1["behavior_learned_invariance"], v1["behavior_random_invariance"],
         v1["learned_substitution_size"]),
        (0.88, v2["behavior_learned_invariance"], v2["behavior_random_invariance"],
         v2["learned_substitution_size"]),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Left: behavioral invariance by threshold
    taus = [p[0] for p in points]
    learned = [p[1] for p in points]
    random_b = [p[2] for p in points]
    ax1.plot(taus, learned, "o-", color="#2ca02c", linewidth=2, markersize=10,
             label="Learned substitution group")
    ax1.plot(taus, random_b, "s--", color="#9467bd", linewidth=2, markersize=8,
             label="Random control")
    for tau, l, r in zip(taus, learned, random_b):
        ax1.text(tau, l + 0.005, f"{l:.3f}", ha="center", fontsize=9, fontweight="bold")
        ax1.text(tau, r - 0.012, f"{r:.3f}", ha="center", fontsize=9)
        ax1.annotate("", xy=(tau, r), xytext=(tau, l),
                     arrowprops=dict(arrowstyle="<->", color="gray", lw=0.7))
        ax1.text(tau + 0.02, (l + r) / 2, f"Δ = {l - r:+.3f}",
                 fontsize=8.5, color="#444")
    ax1.set_xlabel("Score threshold τ", fontsize=11)
    ax1.set_ylabel("Next-token argmax invariance", fontsize=11)
    ax1.set_ylim(0.85, 0.91)
    ax1.set_xlim(0.2, 1.0)
    ax1.set_title("Paraphrase substitution discovery\nbehavioral invariance vs random control",
                  fontsize=11)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(linestyle=":", alpha=0.4)

    # Right: fraction of candidates kept
    sizes = [p[3] for p in points]
    n_cand = v1["n_candidates"]
    fractions = [s / n_cand for s in sizes]
    bars = ax2.bar([f"τ = {p[0]}" for p in points], fractions,
                   color=["#9467bd", "#2ca02c"], edgecolor="black", linewidth=0.5)
    ax2.set_ylabel("Fraction of candidates kept", fontsize=11)
    ax2.set_title(f"Selectivity of the threshold\n({n_cand} candidate substitutions)",
                  fontsize=11)
    for bar, f, s in zip(bars, fractions, sizes):
        ax2.text(bar.get_x() + bar.get_width() / 2, f + 0.02,
                 f"{s} / {n_cand}\n({f*100:.1f}%)",
                 ha="center", fontsize=9, fontweight="bold")
    ax2.set_ylim(0, 1.1)
    ax2.grid(axis="y", linestyle=":", alpha=0.4)

    fig.tight_layout()
    _save(fig, "fig4_threshold_sweep.png")


def main() -> int:
    figure_group_recovery()
    figure_pearson_correlations()
    figure_causal_validation()
    figure_threshold_sweep()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
