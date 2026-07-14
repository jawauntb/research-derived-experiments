# S-022 Seed and Bootstrap Calibration

Status: **complete**

## Preregistered setup

- Configuration SHA-256: `86b0e3ced8aff410f3c0ad4a9780d8d66a073e873f5e4b976d05699c3dcfcf04`
- Seed counts: `(3, 5, 8, 10, 16, 64)`
- Monte Carlo repetitions per cell: `200`
- Bootstrap repetitions per interval: `300`
- Independent resampling unit: seed; paired episode differences remain grouped.

## Gates

- `all_preregistered_cells_reported`: **PASS**
- `hierarchical_undercoverage_detected`: **PASS**
- `promotion_bars_undercoverage`: **PASS**
- `promotion_meets_precision`: **PASS**
- `largest_seed_null_fpr_controlled`: **PASS**
- `negative_regime_preserved`: **PASS**

## Method comparison

| Regime | Seeds | Method | Coverage | Width | Power | FPR | Sign stability |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| null_iid | 3 | `naive_row_percentile` | 0.900 | 1.064 | — | 0.100 | — |
| null_iid | 3 | `paired_seed_cluster_percentile` | 0.785 | 0.830 | — | 0.215 | — |
| null_iid | 5 | `naive_row_percentile` | 0.940 | 0.822 | — | 0.060 | — |
| null_iid | 5 | `paired_seed_cluster_percentile` | 0.850 | 0.697 | — | 0.150 | — |
| null_iid | 8 | `naive_row_percentile` | 0.945 | 0.668 | — | 0.055 | — |
| null_iid | 8 | `paired_seed_cluster_percentile` | 0.895 | 0.603 | — | 0.105 | — |
| null_iid | 10 | `naive_row_percentile` | 0.965 | 0.611 | — | 0.035 | — |
| null_iid | 10 | `paired_seed_cluster_percentile` | 0.940 | 0.591 | — | 0.060 | — |
| null_iid | 16 | `naive_row_percentile` | 0.940 | 0.474 | — | 0.060 | — |
| null_iid | 16 | `paired_seed_cluster_percentile` | 0.915 | 0.456 | — | 0.085 | — |
| null_iid | 64 | `naive_row_percentile` | 0.945 | 0.240 | — | 0.055 | — |
| null_iid | 64 | `paired_seed_cluster_percentile` | 0.935 | 0.237 | — | 0.065 | — |
| moderate_iid | 3 | `naive_row_percentile` | 0.865 | 1.042 | 0.495 | — | 0.935 |
| moderate_iid | 3 | `paired_seed_cluster_percentile` | 0.640 | 0.757 | 0.660 | — | 0.935 |
| moderate_iid | 5 | `naive_row_percentile` | 0.885 | 0.829 | 0.675 | — | 0.980 |
| moderate_iid | 5 | `paired_seed_cluster_percentile` | 0.810 | 0.722 | 0.725 | — | 0.980 |
| moderate_iid | 8 | `naive_row_percentile` | 0.925 | 0.676 | 0.820 | — | 1.000 |
| moderate_iid | 8 | `paired_seed_cluster_percentile` | 0.875 | 0.636 | 0.835 | — | 1.000 |
| moderate_iid | 10 | `naive_row_percentile` | 0.925 | 0.601 | 0.900 | — | 1.000 |
| moderate_iid | 10 | `paired_seed_cluster_percentile` | 0.915 | 0.558 | 0.910 | — | 1.000 |
| moderate_iid | 16 | `naive_row_percentile` | 0.950 | 0.481 | 0.985 | — | 1.000 |
| moderate_iid | 16 | `paired_seed_cluster_percentile` | 0.925 | 0.450 | 0.985 | — | 1.000 |
| moderate_iid | 64 | `naive_row_percentile` | 0.940 | 0.239 | 1.000 | — | 1.000 |
| moderate_iid | 64 | `paired_seed_cluster_percentile` | 0.910 | 0.239 | 1.000 | — | 1.000 |
| moderate_hierarchy | 3 | `naive_row_percentile` | 0.640 | 1.014 | 0.495 | — | 0.815 |
| moderate_hierarchy | 3 | `paired_seed_cluster_percentile` | 0.725 | 1.423 | 0.420 | — | 0.815 |
| moderate_hierarchy | 5 | `naive_row_percentile` | 0.705 | 0.833 | 0.625 | — | 0.865 |
| moderate_hierarchy | 5 | `paired_seed_cluster_percentile` | 0.885 | 1.272 | 0.400 | — | 0.865 |
| moderate_hierarchy | 8 | `naive_row_percentile` | 0.740 | 0.679 | 0.685 | — | 0.955 |
| moderate_hierarchy | 8 | `paired_seed_cluster_percentile` | 0.895 | 1.060 | 0.455 | — | 0.955 |
| moderate_hierarchy | 10 | `naive_row_percentile` | 0.730 | 0.625 | 0.710 | — | 0.965 |
| moderate_hierarchy | 10 | `paired_seed_cluster_percentile` | 0.865 | 0.994 | 0.480 | — | 0.965 |
| moderate_hierarchy | 16 | `naive_row_percentile` | 0.750 | 0.505 | 0.885 | — | 0.985 |
| moderate_hierarchy | 16 | `paired_seed_cluster_percentile` | 0.925 | 0.811 | 0.655 | — | 0.985 |
| moderate_hierarchy | 64 | `naive_row_percentile` | 0.750 | 0.253 | 1.000 | — | 1.000 |
| moderate_hierarchy | 64 | `paired_seed_cluster_percentile` | 0.975 | 0.414 | 1.000 | — | 1.000 |
| null_hierarchy | 3 | `naive_row_percentile` | 0.650 | 1.115 | — | 0.350 | — |
| null_hierarchy | 3 | `paired_seed_cluster_percentile` | 0.740 | 1.641 | — | 0.260 | — |
| null_hierarchy | 5 | `naive_row_percentile` | 0.685 | 0.919 | — | 0.315 | — |
| null_hierarchy | 5 | `paired_seed_cluster_percentile` | 0.880 | 1.470 | — | 0.120 | — |
| null_hierarchy | 8 | `naive_row_percentile` | 0.685 | 0.803 | — | 0.315 | — |
| null_hierarchy | 8 | `paired_seed_cluster_percentile` | 0.910 | 1.353 | — | 0.090 | — |
| null_hierarchy | 10 | `naive_row_percentile` | 0.730 | 0.700 | — | 0.270 | — |
| null_hierarchy | 10 | `paired_seed_cluster_percentile` | 0.920 | 1.170 | — | 0.080 | — |
| null_hierarchy | 16 | `naive_row_percentile` | 0.725 | 0.584 | — | 0.275 | — |
| null_hierarchy | 16 | `paired_seed_cluster_percentile` | 0.945 | 1.000 | — | 0.055 | — |
| null_hierarchy | 64 | `naive_row_percentile` | 0.755 | 0.293 | — | 0.245 | — |
| null_hierarchy | 64 | `paired_seed_cluster_percentile` | 0.925 | 0.505 | — | 0.075 | — |
| weak_high_noise_hierarchy | 3 | `naive_row_percentile` | 0.735 | 1.855 | 0.260 | — | 0.585 |
| weak_high_noise_hierarchy | 3 | `paired_seed_cluster_percentile` | 0.740 | 2.188 | 0.295 | — | 0.585 |
| weak_high_noise_hierarchy | 5 | `naive_row_percentile` | 0.660 | 1.533 | 0.305 | — | 0.565 |
| weak_high_noise_hierarchy | 5 | `paired_seed_cluster_percentile` | 0.810 | 2.032 | 0.220 | — | 0.565 |
| weak_high_noise_hierarchy | 8 | `naive_row_percentile` | 0.745 | 1.232 | 0.240 | — | 0.635 |
| weak_high_noise_hierarchy | 8 | `paired_seed_cluster_percentile` | 0.840 | 1.683 | 0.140 | — | 0.635 |
| weak_high_noise_hierarchy | 10 | `naive_row_percentile` | 0.820 | 1.139 | 0.185 | — | 0.595 |
| weak_high_noise_hierarchy | 10 | `paired_seed_cluster_percentile` | 0.910 | 1.607 | 0.085 | — | 0.595 |
| weak_high_noise_hierarchy | 16 | `naive_row_percentile` | 0.770 | 0.907 | 0.265 | — | 0.675 |
| weak_high_noise_hierarchy | 16 | `paired_seed_cluster_percentile` | 0.905 | 1.284 | 0.140 | — | 0.675 |
| weak_high_noise_hierarchy | 64 | `naive_row_percentile` | 0.825 | 0.459 | 0.450 | — | 0.900 |
| weak_high_noise_hierarchy | 64 | `paired_seed_cluster_percentile` | 0.935 | 0.671 | 0.260 | — | 0.900 |

## Decision table

| Regime | Seeds | Coverage | Width / target | Power | FPR | Sign | Recommendation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| null_iid | 3 | 0.785 | 0.830 / 0.500 | — | 0.215 | — | **insufficient** |
| null_iid | 5 | 0.850 | 0.697 / 0.500 | — | 0.150 | — | **pilot_only** |
| null_iid | 8 | 0.895 | 0.603 / 0.500 | — | 0.105 | — | **pilot_only** |
| null_iid | 10 | 0.940 | 0.591 / 0.500 | — | 0.060 | — | **pilot_only** |
| null_iid | 16 | 0.915 | 0.456 / 0.500 | — | 0.085 | — | **promotion_ready** |
| null_iid | 64 | 0.935 | 0.237 / 0.500 | — | 0.065 | — | **promotion_ready** |
| moderate_iid | 3 | 0.640 | 0.757 / 0.500 | 0.660 | — | 0.935 | **insufficient** |
| moderate_iid | 5 | 0.810 | 0.722 / 0.500 | 0.725 | — | 0.980 | **pilot_only** |
| moderate_iid | 8 | 0.875 | 0.636 / 0.500 | 0.835 | — | 1.000 | **pilot_only** |
| moderate_iid | 10 | 0.915 | 0.558 / 0.500 | 0.910 | — | 1.000 | **pilot_only** |
| moderate_iid | 16 | 0.925 | 0.450 / 0.500 | 0.985 | — | 1.000 | **promotion_ready** |
| moderate_iid | 64 | 0.910 | 0.239 / 0.500 | 1.000 | — | 1.000 | **promotion_ready** |
| moderate_hierarchy | 3 | 0.725 | 1.423 / 0.750 | 0.420 | — | 0.815 | **insufficient** |
| moderate_hierarchy | 5 | 0.885 | 1.272 / 0.750 | 0.400 | — | 0.865 | **pilot_only** |
| moderate_hierarchy | 8 | 0.895 | 1.060 / 0.750 | 0.455 | — | 0.955 | **pilot_only** |
| moderate_hierarchy | 10 | 0.865 | 0.994 / 0.750 | 0.480 | — | 0.965 | **pilot_only** |
| moderate_hierarchy | 16 | 0.925 | 0.811 / 0.750 | 0.655 | — | 0.985 | **pilot_only** |
| moderate_hierarchy | 64 | 0.975 | 0.414 / 0.750 | 1.000 | — | 1.000 | **promotion_ready** |
| null_hierarchy | 3 | 0.740 | 1.641 / 0.750 | — | 0.260 | — | **insufficient** |
| null_hierarchy | 5 | 0.880 | 1.470 / 0.750 | — | 0.120 | — | **pilot_only** |
| null_hierarchy | 8 | 0.910 | 1.353 / 0.750 | — | 0.090 | — | **pilot_only** |
| null_hierarchy | 10 | 0.920 | 1.170 / 0.750 | — | 0.080 | — | **pilot_only** |
| null_hierarchy | 16 | 0.945 | 1.000 / 0.750 | — | 0.055 | — | **pilot_only** |
| null_hierarchy | 64 | 0.925 | 0.505 / 0.750 | — | 0.075 | — | **promotion_ready** |
| weak_high_noise_hierarchy | 3 | 0.740 | 2.188 / 0.800 | 0.295 | — | 0.585 | **insufficient** |
| weak_high_noise_hierarchy | 5 | 0.810 | 2.032 / 0.800 | 0.220 | — | 0.565 | **insufficient** |
| weak_high_noise_hierarchy | 8 | 0.840 | 1.683 / 0.800 | 0.140 | — | 0.635 | **insufficient** |
| weak_high_noise_hierarchy | 10 | 0.910 | 1.607 / 0.800 | 0.085 | — | 0.595 | **insufficient** |
| weak_high_noise_hierarchy | 16 | 0.905 | 1.284 / 0.800 | 0.140 | — | 0.675 | **insufficient** |
| weak_high_noise_hierarchy | 64 | 0.935 | 0.671 / 0.800 | 0.260 | — | 0.900 | **pilot_only** |

## Interpretation boundary

Within the preregistered synthetic regimes, treating nested episode rows as independent can understate uncertainty; promotion decisions must use seed-cluster resampling and meet the reported gates.

Negative regimes are retained as primary outcomes; no cell was dropped or retuned after simulation.

This is a local synthetic calibration. It must be followed by calibration against representative public-safe empirical variance structures before a repository-wide policy is promoted.
