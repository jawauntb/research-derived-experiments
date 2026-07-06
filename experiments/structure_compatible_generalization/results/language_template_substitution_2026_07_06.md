# Phase 4: Language/Template Substitution Generator

## Manifest

- **base_seed:** `20260706`
- **epochs:** `220`
- **gpu:** `L4`
- **max_containers:** `16`
- **max_transforms:** `24`
- **n_configs:** `64`
- **regularization_values:** `[0.0, 0.05, 0.2, 0.5]`
- **shards:** `4`
- **suite:** `language template substitution generator`
- **budget:** 4 L4 cells, conservative $3.20 against $30.00

## Discovery-Regime Audit

- Old regime: modular and vision generators tested finite transport families outside open-ended text.
- New operation: render finite addition examples as language-like templates and infer number-word/template substitutions from observed label-transport overlaps.
- Claim level: controlled language/template substitution, not broad natural-language paraphrase discovery.

## Predictor Correlations

| Domain | Predictor | Pearson r | Spearman r | N |
| --- | --- | ---: | ---: | ---: |
| `language_template_substitution` | `compatibility_discovered` | 0.858 | 0.596 | 256 |
| `language_template_substitution` | `compatibility_true` | 0.853 | 0.628 | 256 |
| `language_template_substitution` | `negative_train_loss` | 0.492 | 0.232 | 256 |
| `language_template_substitution` | `id_validation_accuracy` | 0.478 | 0.127 | 256 |
| `language_template_substitution` | `train_accuracy` | 0.478 | 0.127 | 256 |
| `language_template_substitution` | `compatibility_wrong` | -0.088 | 0.059 | 256 |
| `language_template_substitution` | `negative_abs_sharpness` | -0.111 | 0.063 | 256 |
| `language_template_substitution` | `negative_parameter_l2` | -0.476 | -0.189 | 256 |

## Regularization Intervention

| Regularization | N | Mean train | Mean ID | Mean OOD | Mean learned compatibility | High-ID N | High-ID OOD |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.000 | 64 | 0.554 | 0.554 | 0.147 | 0.082 | 29 | 0.224 |
| 0.050 | 64 | 0.553 | 0.553 | 0.234 | 0.124 | 29 | 0.415 |
| 0.200 | 64 | 0.555 | 0.555 | 0.255 | 0.141 | 29 | 0.463 |
| 0.500 | 64 | 0.558 | 0.558 | 0.277 | 0.201 | 29 | 0.512 |

## Augmentation Arm

| Augmentation | N | Mean train | Mean OOD | Mean learned compatibility |
| --- | ---: | ---: | ---: | ---: |
| `none` | 68 | 0.569 | 0.161 | 0.152 |
| `partial_a_substitution` | 96 | 0.643 | 0.421 | 0.259 |
| `wrong_substitution` | 92 | 0.454 | 0.076 | 0.000 |

## Interpretation

The language/template suite is the finite-text bridge requested by the SCG program: it asks whether learned substitution compatibility predicts held-out number-word transport when ordinary train and ID checks are tied.
