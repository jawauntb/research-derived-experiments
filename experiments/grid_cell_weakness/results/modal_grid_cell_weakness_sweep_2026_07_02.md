# Grid-Cell Weakness — Modal Gate Sweep (2026-07-02)

Pre-registration: [papers/grid_cell_weakness/preregistration.md](../../../papers/grid_cell_weakness/preregistration.md).
Runner: `experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py`.
Backend: Modal H100 workers. Raw JSON is gitignored; combined artifact:
`artifacts/grid_cell_weakness/grid_cell_weakness_sweep_2026_07_02_seed32.json`.

Manifest: 5 conditions × 2 architectures × 32 seeds = **320 trained RNNs**; Ng=128,
Np=100, T=20, steps=4000, batch=200, activity_reg=1e-3, weight_decay=1e-4.
OOD geometry was decoded at arena scales `1.0, 1.25, 1.5, 2.0`; the preregistered
primary OOD metric is the largest held-out arena (`2.0`).

## Gate Verdicts

| Gate | Preregistered criterion | Modal result | Verdict |
| --- | --- | ---: | --- |
| G1 manifold recovered | full-translation torus match ≥ 0.60 | **0.734** | **pass** |
| G2 weakness↔topology | ρ ≥ 0.5 and ≥2× best classical baseline | ρ = **+0.197**; loss↔topology ρ = +0.431 | **fail** |
| G3 weakness↔OOD | ρ ≥ 0.5 and ≥2× best classical baseline | ρ = **+0.617**; loss↔OOD ρ = +0.652 | **fail** |
| G4 topology mediates | partial ρ drops ≥ 50% | partial ρ = **+0.623**; drop = −0.009 | **fail** |
| G5 spectral leg | ρ(weakness, −Fourier PR) ≥ 0.5 | **+0.635** | **pass** |
| G6 causal topology/OOD contrast | full-translation beats none/random-shift | topo 0.357 vs ~0.000; OOD 0.949 vs 0.484 | **pass** |
| wrong-group null | | ρ(wrong-group weakness, OOD) = **0.000** | **pass** |

The wrong-group null is reported with a corrected tie-aware Spearman rank. The first
Modal analysis used ordinal ranks without tie averaging, which assigned a fake
correlation to a constant wrong-group predictor. Raw cell measurements were unaffected;
only the summary rank calculation changed.

## Condition Means

| Condition | n | weakness | toroidal score | torus match | ID acc | OOD acc @2.0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| full_translation | 64 | **0.768** | **0.357** | **0.734** | 0.947 | **0.949** |
| partial_translation | 64 | 0.416 | 0.007 | 0.000 | 0.913 | 0.732 |
| random_shift | 64 | 0.400 | 0.000 | 0.000 | 0.976 | 0.615 |
| none | 64 | 0.446 | 0.000 | 0.000 | 0.984 | 0.484 |
| wrong_group | 64 | 0.048 | 0.009 | 0.000 | 0.985 | 0.489 |

## Larger-Arena OOD Curve

| Condition | 1.0 | 1.25 | 1.5 | 2.0 |
| --- | ---: | ---: | ---: | ---: |
| full_translation | 0.947 | 0.949 | 0.948 | **0.949** |
| partial_translation | 0.913 | 0.793 | 0.706 | **0.732** |
| random_shift | 0.976 | 0.910 | 0.778 | **0.615** |
| none | 0.984 | 0.805 | 0.655 | **0.484** |
| wrong_group | 0.985 | 0.808 | 0.659 | **0.489** |

## Reading

**Confirmed.** The harness robustly produces toroidal population codes under full
translation augmentation (G1), the spectral leg replicates at scale (G5), and the
causal condition contrast is large: full translation yields toroidal topology and
large-arena OOD generalization while unaugmented and wrong-group controls do not
(G6).

**Not confirmed.** The strongest confirmatory triangle claim fails as stated.
Weakness does predict OOD in the raw sense (ρ = +0.617), but it does **not** beat
the best classical baseline by the preregistered 2× margin, and it only weakly
tracks toroidal score (ρ = +0.197). Topology also does not mediate the
weakness→OOD relationship; the partial correlation does not drop.

The honest interpretation is therefore narrower than the registered Paper A
claim: translation augmentation causally induces toroidal topology and OOD
generalization, and weakness remains a useful spectral/OOD signal, but this
Modal sweep does **not** establish weakness as the scalar that governs toroidal
topology or topology as the mediator of generalization.
