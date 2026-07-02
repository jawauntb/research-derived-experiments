# Grid-Cell Weakness Conference Evidence Appendix (2026-07-02)

Source raw JSON: `artifacts/grid_cell_weakness/grid_cell_weakness_sweep_2026_07_02_seed32.json`
SHA-256: `8a15d4702ed405ad6a5a9e867e01690180ecec900207122a1d2e873418596310`

Manifest: 320 cells; conditions=['full_translation', 'partial_translation', 'none', 'random_shift', 'wrong_group']; archs=['rnn', 'gru']; seeds=32; steps=4000; decode_arenas=[1.0, 1.25, 1.5, 2.0].

Bootstrap intervals are percentile intervals from resampling cells within condition. Continuous metrics use 5000 bootstrap resamples; torus-match intervals use Wilson 95% intervals for the Boolean `betti_match_torus` fraction.

## Condition Metrics With 95% Intervals

| Condition | n | weakness | toroidal score | Fourier PR | torus match |
| --- | --- | --- | --- | --- | --- |
| full_translation | 64 | 0.768 [0.723, 0.808] | 0.357 [0.317, 0.396] | 4.472 [4.188, 4.773] | 0.734 [0.615, 0.827] |
| partial_translation | 64 | 0.416 [0.363, 0.467] | 0.007 [0.006, 0.009] | 7.557 [7.094, 8.038] | 0.000 [0.000, 0.057] |
| random_shift | 64 | 0.400 [0.368, 0.433] | 0.000 [0.000, 0.000] | 8.778 [8.200, 9.354] | 0.000 [0.000, 0.057] |
| none | 64 | 0.446 [0.409, 0.481] | 0.000 [0.000, 0.000] | 8.324 [7.791, 8.899] | 0.000 [0.000, 0.057] |
| wrong_group | 64 | 0.048 [0.033, 0.064] | 0.009 [0.007, 0.011] | 14.634 [14.128, 15.180] | 0.000 [0.000, 0.057] |

## OOD Curve With 95% Intervals

| Condition | arena 1 | arena 1.25 | arena 1.5 | arena 2 |
| --- | --- | --- | --- | --- |
| full_translation | 0.947 [0.944, 0.949] | 0.949 [0.946, 0.952] | 0.948 [0.945, 0.951] | 0.949 [0.946, 0.953] |
| partial_translation | 0.913 [0.909, 0.918] | 0.793 [0.786, 0.800] | 0.706 [0.697, 0.715] | 0.732 [0.725, 0.738] |
| random_shift | 0.976 [0.958, 0.987] | 0.910 [0.890, 0.923] | 0.778 [0.756, 0.793] | 0.615 [0.597, 0.628] |
| none | 0.984 [0.980, 0.987] | 0.805 [0.794, 0.815] | 0.655 [0.645, 0.665] | 0.484 [0.473, 0.495] |
| wrong_group | 0.985 [0.983, 0.987] | 0.808 [0.797, 0.818] | 0.659 [0.650, 0.669] | 0.489 [0.479, 0.499] |

## Within-Toroidal Analysis

These correlations restrict to models that already satisfy the Boolean torus criterion. They ask whether weakness explains variation after the main topology-formation event has already occurred.

| Subset | n | comparison | rho | 95% CI |
| --- | --- | --- | --- | --- |
| all_conditions | 47 | rho_weakness_ood | -0.198 | [-0.518, 0.136] |
| all_conditions | 47 | rho_weakness_toroidal_score | -0.335 | [-0.577, -0.063] |
| all_conditions | 47 | rho_weakness_neg_fourier_pr | -0.356 | [-0.585, -0.071] |
| all_conditions | 47 | rho_loss_ood | -0.779 | [-0.874, -0.612] |
| full_translation | 47 | rho_weakness_ood | -0.198 | [-0.518, 0.136] |
| full_translation | 47 | rho_weakness_toroidal_score | -0.335 | [-0.577, -0.063] |
| full_translation | 47 | rho_weakness_neg_fourier_pr | -0.356 | [-0.585, -0.071] |
| full_translation | 47 | rho_loss_ood | -0.779 | [-0.874, -0.612] |

Insufficient already-toroidal cells: partial_translation (n=0), random_shift (n=0), none (n=0), wrong_group (n=0).

## Topology Robustness Status

The recovered 2026-07-02 raw JSON stores scalar per-cell metrics but not hidden-state populations or per-configuration topology sweeps. Robustness over bin counts, Vietoris-Rips edge caps, empty-bin handling, and sampling density therefore cannot be reconstructed from this artifact. The Modal runner now has a robustness export path for reruns.

## CSV Outputs

- `grid_cell_weakness_cells_2026_07_02.csv`: one row per trained Modal cell.
- `grid_cell_weakness_bootstrap_2026_07_02.csv`: condition-level means and intervals.
- `grid_cell_weakness_ood_bootstrap_2026_07_02.csv`: OOD curve means and intervals.
- `grid_cell_weakness_within_toroidal_2026_07_02.csv`: already-toroidal within-condition correlations.
- `grid_cell_weakness_topology_robustness_2026_07_02.csv`: robustness summaries when available, otherwise a status row.
