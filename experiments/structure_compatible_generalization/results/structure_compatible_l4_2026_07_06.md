# Structure-Compatible Generalization L4 Suite

## Manifest

- **base_seed:** `20260706`
- **domains:** `['symbolic', 'vision', 'modular']`
- **gpu:** `L4`
- **max_containers:** `24`
- **modular_epochs:** `500`
- **modular_models:** `128`
- **shards_per_domain:** `4`
- **symbolic_epochs:** `1200`
- **symbolic_models:** `128`
- **vision_epochs:** `160`
- **vision_models:** `96`
- **budget:** 12 L4 cells, conservative $9.59 against $50.00

## Headline

The diagnostic suite evaluates whether compatibility with the deployment-generating transformation family predicts OOD accuracy among finite models whose train/ID evidence is similar.

## Domain Predictor Rankings

### modular_exact

- Rows: 2; mean train 1.000; mean ID 1.000; mean OOD 0.545

| Rank | Predictor | Pearson r | Spearman r | N |
| ---: | --- | ---: | ---: | ---: |
| 1 | `compatibility_inferred` | 1.000 | 1.000 | 2 |
| 2 | `compatibility_true` | 1.000 | 1.000 | 2 |
| 3 | `compatibility_wrong` | 0.000 | 0.000 | 2 |
| 4 | `id_validation_accuracy` | 0.000 | 0.000 | 2 |
| 5 | `train_accuracy` | 0.000 | 0.000 | 2 |

### modular_neural

- Rows: 128; mean train 0.732; mean ID 0.732; mean OOD 0.165

| Rank | Predictor | Pearson r | Spearman r | N |
| ---: | --- | ---: | ---: | ---: |
| 1 | `compatibility_true` | 0.649 | 0.257 | 128 |
| 2 | `id_validation_accuracy` | 0.188 | -0.143 | 128 |
| 3 | `train_accuracy` | 0.188 | -0.143 | 128 |
| 4 | `negative_train_loss` | 0.178 | -0.065 | 128 |
| 5 | `compatibility_wrong` | 0.107 | 0.232 | 128 |
| 6 | `compatibility_inferred` | 0.092 | 0.283 | 128 |
| 7 | `negative_abs_sharpness` | 0.002 | 0.069 | 128 |
| 8 | `negative_parameter_l2` | -0.266 | 0.017 | 128 |

### symbolic_cyclic

- Rows: 128; mean train 0.973; mean ID 0.984; mean OOD 0.394

| Rank | Predictor | Pearson r | Spearman r | N |
| ---: | --- | ---: | ---: | ---: |
| 1 | `compatibility_true` | 0.763 | 0.574 | 128 |
| 2 | `compatibility_inferred` | 0.751 | 0.565 | 128 |
| 3 | `train_accuracy` | 0.164 | 0.155 | 128 |
| 4 | `id_validation_accuracy` | 0.099 | 0.075 | 128 |
| 5 | `negative_train_loss` | 0.066 | -0.103 | 128 |
| 6 | `negative_abs_sharpness` | -0.018 | -0.087 | 128 |
| 7 | `compatibility_wrong` | -0.107 | 0.104 | 128 |
| 8 | `negative_parameter_l2` | -0.203 | -0.338 | 128 |

### vision_rotation

- Rows: 96; mean train 0.773; mean ID 0.773; mean OOD 0.380

| Rank | Predictor | Pearson r | Spearman r | N |
| ---: | --- | ---: | ---: | ---: |
| 1 | `compatibility_true` | 0.451 | 0.219 | 96 |
| 2 | `id_validation_accuracy` | 0.445 | 0.438 | 96 |
| 3 | `train_accuracy` | 0.445 | 0.438 | 96 |
| 4 | `negative_train_loss` | 0.414 | 0.380 | 96 |
| 5 | `negative_abs_sharpness` | -0.315 | -0.325 | 96 |
| 6 | `negative_parameter_l2` | -0.390 | -0.380 | 96 |
| 7 | `compatibility_wrong` | -0.454 | -0.557 | 96 |

## Selection Without OOD Labels

| Predictor | Domains | Mean selected OOD |
| --- | ---: | ---: |
| `compatibility_true` | 3 | 1.000 |
| `id_validation_accuracy` | 3 | 0.660 |
| `train_accuracy` | 3 | 0.660 |
| `compatibility_inferred` | 2 | 0.531 |
| `compatibility_wrong` | 3 | 0.458 |
| `negative_parameter_l2` | 3 | 0.426 |
| `negative_abs_sharpness` | 3 | 0.410 |
| `negative_train_loss` | 3 | 0.117 |

## Regime Audit

- Old regime: Paper 3's oracle-group symbolic/MLP/vision weakness diagnostics.
- Transition: one common cross-domain diagnostic schema plus an additional modular algorithmic domain.
- Residual finding: compare the top-ranked predictors and OOD-free selection behavior across domains; do not claim full certification.
- Allowed claim: structure-compatible diagnostics for finite underspecified tasks with known deployment transformations.

