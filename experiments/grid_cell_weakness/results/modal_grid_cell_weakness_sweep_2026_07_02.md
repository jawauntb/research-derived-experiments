# Grid-Cell Weakness — Modal Gate Sweep (2026-07-02)

Pre-registration: [papers/grid_cell_weakness/preregistration.md](../../../papers/grid_cell_weakness/preregistration.md).
Runner: `experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py`.
Backend: Modal H100 workers. Raw JSON is gitignored and remains outside the repository;
the recovered local artifact used for the conference-evidence pass was
`artifacts/grid_cell_weakness/grid_cell_weakness_sweep_2026_07_02_seed32.json`
(SHA-256 `8a15d4702ed405ad6a5a9e867e01690180ecec900207122a1d2e873418596310`).
Committed exports derived from that artifact:
`grid_cell_weakness_cells_2026_07_02.csv`,
`grid_cell_weakness_bootstrap_2026_07_02.csv`,
`grid_cell_weakness_ood_bootstrap_2026_07_02.csv`, and
`grid_cell_weakness_within_toroidal_2026_07_02.csv`.

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

## Bootstrap Intervals and Per-Cell Exports

The raw 320-cell Modal JSON was recovered locally and exported with
`scripts/analyze_gridcell_conference_evidence.py`. Continuous intervals below
are percentile bootstrap 95% CIs from 5000 resamples within condition; torus
match uses Wilson 95% intervals for the Boolean `betti_match_torus` fraction.

| Condition | n | weakness | toroidal score | Fourier PR | torus match |
| --- | ---: | ---: | ---: | ---: | ---: |
| full_translation | 64 | 0.768 [0.723, 0.808] | 0.357 [0.317, 0.396] | 4.472 [4.188, 4.773] | 0.734 [0.615, 0.827] |
| partial_translation | 64 | 0.416 [0.363, 0.467] | 0.007 [0.006, 0.009] | 7.557 [7.094, 8.038] | 0.000 [0.000, 0.057] |
| random_shift | 64 | 0.400 [0.368, 0.433] | 0.000 [0.000, 0.000] | 8.778 [8.200, 9.354] | 0.000 [0.000, 0.057] |
| none | 64 | 0.446 [0.409, 0.481] | 0.000 [0.000, 0.000] | 8.324 [7.791, 8.899] | 0.000 [0.000, 0.057] |
| wrong_group | 64 | 0.048 [0.033, 0.064] | 0.009 [0.007, 0.011] | 14.634 [14.128, 15.180] | 0.000 [0.000, 0.057] |

## Larger-Arena OOD Curve

| Condition | 1.0 | 1.25 | 1.5 | 2.0 |
| --- | ---: | ---: | ---: | ---: |
| full_translation | 0.947 | 0.949 | 0.948 | **0.949** |
| partial_translation | 0.913 | 0.793 | 0.706 | **0.732** |
| random_shift | 0.976 | 0.910 | 0.778 | **0.615** |
| none | 0.984 | 0.805 | 0.655 | **0.484** |
| wrong_group | 0.985 | 0.808 | 0.659 | **0.489** |

Bootstrap 95% CIs for the OOD curve:

| Condition | arena 1.0 | arena 1.25 | arena 1.5 | arena 2.0 |
| --- | ---: | ---: | ---: | ---: |
| full_translation | 0.947 [0.944, 0.949] | 0.949 [0.946, 0.952] | 0.948 [0.945, 0.951] | 0.949 [0.946, 0.953] |
| partial_translation | 0.913 [0.909, 0.918] | 0.793 [0.786, 0.800] | 0.706 [0.697, 0.715] | 0.732 [0.725, 0.738] |
| random_shift | 0.976 [0.958, 0.987] | 0.910 [0.890, 0.923] | 0.778 [0.756, 0.793] | 0.615 [0.597, 0.628] |
| none | 0.984 [0.980, 0.987] | 0.805 [0.794, 0.815] | 0.655 [0.645, 0.665] | 0.484 [0.473, 0.495] |
| wrong_group | 0.985 [0.983, 0.987] | 0.808 [0.797, 0.818] | 0.659 [0.650, 0.669] | 0.489 [0.479, 0.499] |

## Within-Toroidal Analysis

Among the 47 already-toroidal full-translation models, weakness does not explain
additional OOD variation after torus formation. The within-toroidal
weakness-OOD Spearman correlation is -0.198 (95% bootstrap CI [-0.518, 0.136]).
Weakness also anticorrelates with continuous toroidal score within this subset
(-0.335, CI [-0.577, -0.063]) and with -Fourier PR (-0.356, CI [-0.585,
-0.071]). This supports the current interpretation: weakness tracks one
spectral aspect of the learned translation structure, but it is not the scalar
governing torus formation or post-formation OOD variation.

No control condition has enough already-toroidal models for a within-condition
toroidal subset analysis (`partial_translation`, `random_shift`, `none`, and
`wrong_group` all have n=0 torus matches).

## Topology Robustness Status

The recovered 2026-07-02 raw JSON stores scalar per-cell metrics but not the
hidden-state populations or per-configuration topology sweeps needed to
reconstruct robustness over bin counts, Vietoris-Rips edge caps, empty-bin
handling, or sampling density. The Modal runner now supports a robustness export
mode for reruns; the current committed robustness CSV therefore contains a
status row rather than reconstructed robustness results.

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
