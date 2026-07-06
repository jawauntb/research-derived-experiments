# Phase 2: Inferred Transformations and Intervention

## Manifest

- **base_seed:** `20260706`
- **epochs:** `450`
- **gpu:** `L4`
- **max_containers:** `24`
- **n_configs:** `180`
- **regularization_values:** `[0.0, 0.05, 0.2]`
- **shards:** `6`
- **suite:** `phase2 inferred transformations and intervention`
- **budget:** 6 L4 cells, conservative $4.80 against $50.00

## Regime Transition

- Old regime: oracle transformation compatibility as a post-hoc OOD diagnostic.
- New operation: infer supported modular shifts from observed train-label overlaps, then optionally regularize predictions under that discovered family.
- Claim level: neural-validated intervention result for a finite structured domain; not a language/vision transformation-discovery theorem.

## Predictor Correlations

| Predictor | Pearson r | Spearman r | N |
| --- | ---: | ---: | ---: |
| `compatibility_true` | 0.862 | 0.394 | 540 |
| `negative_train_loss` | 0.454 | 0.266 | 540 |
| `compatibility_discovered` | 0.413 | 0.389 | 540 |
| `compatibility_inferred` | 0.413 | 0.389 | 540 |
| `id_validation_accuracy` | 0.379 | 0.162 | 540 |
| `train_accuracy` | 0.379 | 0.162 | 540 |
| `compatibility_wrong` | 0.097 | 0.096 | 540 |

## Intervention

| Compatibility regularization | N | Mean train | Mean OOD | Mean discovered compatibility | High-ID N | High-ID mean OOD |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.000 | 180 | 0.719 | 0.134 | 0.339 | 98 | 0.178 |
| 0.050 | 180 | 0.719 | 0.320 | 0.506 | 98 | 0.519 |
| 0.200 | 180 | 0.723 | 0.352 | 0.546 | 99 | 0.573 |

## Selection Without OOD Labels

| Predictor | Domains | Mean selected OOD |
| --- | ---: | ---: |
| `compatibility_discovered` | 1 | 1.000 |
| `compatibility_inferred` | 1 | 1.000 |
| `compatibility_true` | 1 | 1.000 |
| `compatibility_wrong` | 1 | 1.000 |
| `negative_parameter_l2` | 1 | 0.200 |
| `id_validation_accuracy` | 1 | 0.000 |
| `negative_abs_sharpness` | 1 | 0.000 |
| `negative_train_loss` | 1 | 0.000 |
| `train_accuracy` | 1 | 0.000 |

This selector table is a one-domain sanity check, not a cross-domain headline. The phase-two evidence-bearing result is the intervention table above: compatibility regularization improves OOD while keeping the comparison restricted to high-ID models.

## Residual Finding

Supported discovery is stricter than the phase-one inferred score: non-identity shifts must have observed overlap evidence. The regularizer tests whether that inferred family can control OOD behavior without OOD labels.
