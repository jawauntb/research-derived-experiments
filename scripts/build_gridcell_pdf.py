#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render Paper A from the 2026-07-02 Modal gate sweep.

The raw JSON remains gitignored. This builder uses the committed result report
numbers from experiments/grid_cell_weakness/results/modal_grid_cell_weakness_sweep_2026_07_02.md.

Run:  python scripts/build_gridcell_pdf.py
Out:  artifacts/papers/weakness_predicts_topology.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402

FIG = "artifacts/papers/figs_gridcell"
OUT = "artifacts/papers/weakness_predicts_topology.pdf"

CONDS = ["full_translation", "partial_translation", "random_shift", "none", "wrong_group"]
LABELS = ["full translation", "partial", "random shift", "none", "wrong group"]
WEAKNESS = [0.768, 0.416, 0.400, 0.446, 0.048]
TOPO = [0.357, 0.007, 0.000, 0.000, 0.009]
TORUS = [0.734, 0.000, 0.000, 0.000, 0.000]
OOD = [0.949, 0.732, 0.615, 0.484, 0.489]
OOD_CURVES = {
    "full translation": [0.947, 0.949, 0.948, 0.949],
    "partial": [0.913, 0.793, 0.706, 0.732],
    "random shift": [0.976, 0.910, 0.778, 0.615],
    "none": [0.984, 0.805, 0.655, 0.484],
    "wrong group": [0.985, 0.808, 0.659, 0.489],
}


def fig_gate_matrix(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    gates = ["G1 torus", "G2 W-topology", "G3 W-OOD", "G4 mediation", "G5 spectrum", "G6 causal", "null"]
    vals = np.array([[1, 0, 0, 0, 1, 1, 1]], dtype=float)
    fig, ax = plt.subplots(figsize=(6.6, 1.6))
    ax.imshow(vals, cmap=plt.matplotlib.colors.ListedColormap(["#c0392b", "#2f9e44"]), vmin=0, vmax=1)
    ax.set_xticks(range(len(gates)))
    ax.set_xticklabels(gates, rotation=25, ha="right")
    ax.set_yticks([0])
    ax.set_yticklabels(["Modal\n320 nets"])
    for j, v in enumerate(vals[0]):
        ax.text(j, 0, "pass" if v else "fail", ha="center", va="center", color="white", fontsize=8, weight="bold")
    ax.set_title("Pre-registered gate verdicts: the causal/spectral legs pass; mediation fails")
    ax.tick_params(length=0)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def fig_condition_bars(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(LABELS))
    width = 0.26
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    ax.bar(x - width, WEAKNESS, width, label="weakness", color="#2b6cb0")
    ax.bar(x, TOPO, width, label="toroidal score", color="#2f9e44")
    ax.bar(x + width, OOD, width, label="OOD @2.0", color="#e8a13a")
    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, rotation=20, ha="right")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("mean value")
    ax.set_title("Condition means across 320 Modal-trained path-integration RNNs")
    ax.legend(fontsize=8)
    ax.grid(axis="x", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def fig_ood_curves(path: str) -> str:
    import matplotlib.pyplot as plt

    xs = [1.0, 1.25, 1.5, 2.0]
    colors = ["#2b6cb0", "#2f9e44", "#8a63d2", "#9aa6b2", "#c0392b"]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for (name, vals), color in zip(OOD_CURVES.items(), colors):
        ax.plot(xs, vals, marker="o", lw=1.8, label=name, color=color)
    ax.set_xlabel("arena scale at decode time")
    ax.set_ylabel("decode accuracy")
    ax.set_ylim(0.35, 1.02)
    ax.set_title("Full translation preserves OOD path integration in larger arenas")
    ax.legend(fontsize=7.4, ncol=2)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def build() -> None:
    Path(FIG).mkdir(parents=True, exist_ok=True)
    f_gate = fig_gate_matrix(f"{FIG}/fig1_gate_matrix.png")
    f_cond = fig_condition_bars(f"{FIG}/fig2_condition_means.png")
    f_ood = fig_ood_curves(f"{FIG}/fig3_ood_curves.png")

    p = pk.Paper(OUT, FIG)
    p.title("Weakness, Toroidal Topology, and OOD Generalization in Path-Integration RNNs: A Modal Gate Sweep")
    p.authors("Jawaun Brown")
    p.authors("Research-Derived Experiments · Paper A")
    p.rule()
    p.abstract(
        "This paper tests a strong registered claim: that <b>weakness</b>, a scalar measuring how "
        "many translations a learned code remains compatible with, governs whether a path-integration "
        "RNN forms a toroidal population manifold and whether that topology mediates larger-arena "
        "generalization. A 320-network Modal H100 sweep gives a mixed, informative answer. Full "
        "translation augmentation reliably induces toroidal codes (G1 pass; torus match 0.734), "
        "spectral concentration tracks weakness (G5 pass; ρ=+0.635), and the causal condition "
        "contrast is large (G6 pass; OOD 0.949 vs 0.484 for no augmentation). But the central "
        "triangle claim fails: weakness only weakly predicts toroidal score (G2 fail; ρ=+0.197), "
        "weakness does not beat the best classical OOD baseline by the preregistered 2× margin "
        "(G3 fail; weakness ρ=+0.617, loss ρ=+0.652), and topology does not mediate the "
        "weakness→OOD relation (G4 fail). The honest conclusion is narrower and stronger for being "
        "bounded: translation augmentation causally produces a toroidal, OOD-generalizing spatial "
        "code, but this sweep does not establish weakness as the governing scalar of toroidal "
        "topology.")

    p.h1("1. Question")
    p.para(
        "Grid cells in mammalian entorhinal cortex form periodic spatial codes whose population "
        "activity lies on a torus. RNNs trained for path integration can rediscover similar codes. "
        "The preregistered question here is whether the program's substrate-general scalar, "
        "<b>weakness</b>, predicts that topological event. Weakness is the mean held-out R² with "
        "which one linear operator can transform a population code under wrapped translations: a "
        "high-weakness code behaves as though it has learned the translation group.")
    p.para(
        "The strong version predicted a triangle: high weakness, low Fourier participation ratio "
        "(few aligned irreducible representations), clean toroidal topology, and larger-arena OOD "
        "generalization should be measurements of one event. The sweep below tests that triangle "
        "without moving the goalposts.")

    p.h1("2. Method")
    p.para(
        "We trained 320 velocity-driven path-integration RNNs on Modal H100 workers: five training "
        "conditions, two recurrent architectures, and 32 seeds. Each network predicts a place-cell "
        "code from velocity sequences. Conditions vary the augmentation regime: full translations, "
        "partial translations, random shifts, no augmentation, and a wrong-group control. For each "
        "trained code we measure weakness, persistent-homology toroidal score, Fourier participation "
        "ratio, and decoding accuracy in held-out arenas of scale 1.0, 1.25, 1.5, and 2.0. The "
        "largest arena is the preregistered OOD metric.")
    p.figure(f_gate, "Figure 1. Gate verdicts from the preregistered Modal sweep. The causal and spectral legs pass; the topology-governing and mediation claims fail.", width_in=6.2)

    p.h1("3. Results")
    p.figure(f_cond, "Figure 2. Condition means. Full translation is the only condition that reliably forms a torus and preserves OOD decoding at arena scale 2.0.", width_in=6.3)
    p.figure(f_ood, "Figure 3. Larger-arena OOD curves. Full translation remains stable as the arena doubles; controls degrade sharply.", width_in=6.0)
    p.table(
        [["Gate", "Result", "Verdict"],
         ["G1 manifold recovered", "full-translation torus match = 0.734", "pass"],
         ["G2 weakness↔topology", "ρ = +0.197; loss↔topology ρ = +0.431", "fail"],
         ["G3 weakness↔OOD", "ρ = +0.617; loss↔OOD ρ = +0.652", "fail"],
         ["G4 topology mediates", "partial ρ = +0.623; drop = −0.009", "fail"],
         ["G5 spectral leg", "ρ(weakness, −Fourier PR) = +0.635", "pass"],
         ["G6 causal contrast", "topology 0.357 vs ~0; OOD 0.949 vs 0.484", "pass"],
         ["wrong-group null", "ρ = 0.000 with tie-aware Spearman", "pass"]],
        caption="Table 1. Pre-registered gate verdicts. The sweep confirms torus formation under the causal intervention but rejects the strongest mediation story.",
        col_widths=[155, 250, 55])

    p.h1("4. Interpretation")
    p.para(
        "The result should not be polished into a full confirmation. It is better than that: it "
        "tells us exactly which parts of the theory survive scale. Translation augmentation is a "
        "real causal intervention for toroidal topology and larger-arena generalization. Weakness "
        "is still a useful spectral and OOD-associated quantity. But toroidal topology is not the "
        "mediator of the weakness→OOD relationship in this harness, and weakness is not yet the "
        "single scalar that controls torus formation.")
    p.para(
        "A plausible reading is that the augmentation condition itself is the strongest causal "
        "variable: it directly supplies the group structure needed for both topology and OOD. "
        "Weakness measures part of that event, especially its spectral footprint, but it is not "
        "sufficiently specific to explain all topology variance after training loss and condition "
        "effects are present. Future work should test mediation within a narrower family of already "
        "well-trained toroidal codes and use tie-aware rank statistics from the outset.")

    p.h1("5. Limitations")
    p.para(
        "This remains an artificial RNN path-integration task, not a biological replication. The "
        "topology metric uses binned hidden activity and Vietoris-Rips persistent homology; both "
        "can be sensitive to sampling density. The wrong-group null in the first Modal summary was "
        "miscomputed by a rank helper that did not average ties; the corrected tie-aware Spearman "
        "is reported here and in the result report. The raw cell measurements did not change.")

    p.references([
        "Gardner, R. J. et al. Toroidal topology of population activity in grid cells. Nature 602 (2022).",
        "Sorscher, B., Mel, G. C., Ganguli, S., Ocko, S. A. A unified theory for the origin of grid cells through the lens of pattern formation. NeurIPS (2019).",
        "Cueva, C. J., Wei, X.-X. Emergence of grid-like representations by training recurrent neural networks to perform spatial localization. ICLR (2018).",
        "Banino, A. et al. Vector-based navigation using grid-like representations in artificial agents. Nature 557 (2018).",
        "Cohen, T., Welling, M. Group Equivariant Convolutional Networks. ICML (2016).",
        "Gruver, N., Finzi, M., Goldblum, M., Wilson, A. G. The Lie Derivative for Measuring Learned Equivariance. ICLR (2023).",
        "Bennett, M. T. How to Create Conscious Machines. arXiv:2403.00644 (2024).",
    ])
    out = p.build()
    print(f"[gridcell-pdf] wrote {out}")


if __name__ == "__main__":
    build()
