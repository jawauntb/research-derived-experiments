# Phase 3: Learned Generators and Transfer

## Manifest

- **base_seed:** `20260706`
- **candidates:** `24`
- **gpu:** `L4`
- **max_containers:** `24`
- **max_transports:** `16`
- **modular_configs:** `90`
- **modular_epochs:** `350`
- **modular_shards:** `3`
- **n_rotations:** `8`
- **regularization_values:** `[0.0, 0.05, 0.2]`
- **suite:** `phase3 learned generators and transfer`
- **threshold:** `0.5`
- **train_per_class:** `3`
- **vision_base:** `36`
- **vision_epochs:** `220`
- **vision_shards:** `3`
- **budget:** 6 L4 cells, conservative $4.80 against $50.00

## Discovery-Regime Audit

- Old regime: supported modular shifts supplied the transformation parameterization.
- New operation: learn candidate input/label transports from observed overlap evidence, then transfer the same compatibility/intervention logic to data-inferred vision rotations.
- Claim level: finite generator-transfer diagnostic, not open-ended transformation discovery.

## Predictor Correlations

| Domain | Predictor | Pearson r | Spearman r | N |
| --- | --- | ---: | ---: | ---: |
| `modular_learned_generator` | `compatibility_true` | 0.812 | 0.367 | 270 |
| `modular_learned_generator` | `compatibility_discovered` | 0.787 | 0.474 | 270 |
| `modular_learned_generator` | `negative_train_loss` | 0.432 | 0.250 | 270 |
| `modular_learned_generator` | `id_validation_accuracy` | 0.398 | 0.120 | 270 |
| `modular_learned_generator` | `train_accuracy` | 0.398 | 0.120 | 270 |
| `modular_learned_generator` | `negative_abs_sharpness` | 0.050 | 0.224 | 270 |
| `modular_learned_generator` | `compatibility_wrong` | -0.085 | 0.049 | 270 |
| `modular_learned_generator` | `negative_parameter_l2` | -0.448 | -0.230 | 270 |
| `vision_rotation_learned_generator` | `compatibility_true` | 0.678 | 0.591 | 144 |
| `vision_rotation_learned_generator` | `id_validation_accuracy` | 0.661 | 0.632 | 144 |
| `vision_rotation_learned_generator` | `train_accuracy` | 0.661 | 0.632 | 144 |
| `vision_rotation_learned_generator` | `negative_train_loss` | 0.659 | 0.514 | 144 |
| `vision_rotation_learned_generator` | `compatibility_discovered` | 0.599 | 0.502 | 144 |
| `vision_rotation_learned_generator` | `compatibility_wrong` | 0.457 | 0.341 | 144 |
| `vision_rotation_learned_generator` | `negative_parameter_l2` | -0.770 | -0.581 | 144 |

## Modular Intervention

| Regularization | N | Mean train | Mean OOD | Mean learned compatibility | High-ID N | High-ID OOD |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.000 | 90 | 0.652 | 0.168 | 0.047 | 45 | 0.256 |
| 0.050 | 90 | 0.653 | 0.253 | 0.152 | 45 | 0.425 |
| 0.200 | 90 | 0.656 | 0.290 | 0.185 | 45 | 0.502 |

## Vision Transfer

| Regime | N | Mean train | Mean OOD | Mean learned compatibility |
| --- | ---: | ---: | ---: | ---: |
| `learned_aug` | 36 | 0.707 | 0.644 | 0.793 |
| `none` | 36 | 0.815 | 0.258 | 0.486 |
| `oracle_aug` | 36 | 0.709 | 0.693 | 0.801 |
| `random_aug` | 36 | 0.679 | 0.610 | 0.760 |

| Regime | Paired N | Mean OOD delta vs none |
| --- | ---: | ---: |
| `learned_aug` | 14 | 0.391 |
| `oracle_aug` | 14 | 0.440 |
| `random_aug` | 14 | 0.363 |

## Residual Finding

The phase-three residual is whether learned generators can both predict and control OOD outside the hand-specified modular shift schema. The vision arm is the first transfer test; language/template substitution remains the next unclaimed step.
