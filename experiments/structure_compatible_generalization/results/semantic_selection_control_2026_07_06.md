# Phase 6: Semantic Selection Control

## Manifest

- **base_seed:** `20260706`
- **configs_per_zoo:** `12`
- **encoder_keys:** `['all_minilm_l6_v2', 'bge_small_en_v1_5']`
- **gpu:** `L4`
- **max_containers:** `8`
- **n_zoos:** `12`
- **suite:** `semantic selection control`
- **thresholds:** `[0.5, 0.56, 0.62, 0.68, 0.74]`
- **budget:** 2 L4 cells, conservative $0.80 against $30.00

## Discovery-Regime Audit

- Current regime: frozen-encoder semantic retrieval rows with learned candidate transformation pairs.
- New operation: OOD-free model-zoo selection inside high train/ID candidate sets.
- Gate: learned compatibility must beat train/ID selectors and random selection, while wrong compatibility fails.
- Claim level: finite semantic retrieval model selection, not universal paraphrase certification.

## Gate Status

| Gate | Passed |
| --- | ---: |
| `min_zoo_count` | `True` |
| `beats_id_validation` | `True` |
| `beats_train_accuracy` | `True` |
| `beats_random_candidate` | `True` |
| `wrong_control_fails` | `True` |
| `accepted` | `True` |

## Selector Results

| Selector | Zoos | Mean candidates | Selected OOD | Regret | Lift vs random | Mean ties |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `random_candidate` | 120 | 8.617 | 0.919 | 0.073 | 0.000 | 8.617 |
| `id_validation_accuracy` | 120 | 8.617 | 0.919 | 0.073 | 0.000 | 8.617 |
| `train_accuracy` | 120 | 8.617 | 0.919 | 0.073 | 0.000 | 8.617 |
| `compatibility_wrong` | 120 | 8.617 | 0.751 | 0.242 | -0.168 | 1.967 |
| `compatibility_discovered` | 120 | 8.617 | 0.978 | 0.014 | 0.059 | 3.917 |
| `compatibility_true` | 120 | 8.617 | 0.993 | 0.000 | 0.073 | 3.617 |
| `ood_oracle` | 120 | 8.617 | 0.993 | 0.000 | 0.073 | 3.617 |

## Threshold Stress Test

| Threshold | Selector | Zoos | Selected OOD | Lift vs random |
| ---: | --- | ---: | ---: | ---: |
| 0.50 | `compatibility_discovered` | 24 | 0.992 | 0.075 |
| 0.50 | `compatibility_wrong` | 24 | 0.750 | -0.167 |
| 0.50 | `id_validation_accuracy` | 24 | 0.917 | 0.000 |
| 0.56 | `compatibility_discovered` | 24 | 0.984 | 0.068 |
| 0.56 | `compatibility_wrong` | 24 | 0.755 | -0.161 |
| 0.56 | `id_validation_accuracy` | 24 | 0.917 | 0.000 |
| 0.62 | `compatibility_discovered` | 24 | 0.984 | 0.061 |
| 0.62 | `compatibility_wrong` | 24 | 0.750 | -0.173 |
| 0.62 | `id_validation_accuracy` | 24 | 0.923 | 0.000 |
| 0.68 | `compatibility_discovered` | 24 | 0.969 | 0.052 |
| 0.68 | `compatibility_wrong` | 24 | 0.750 | -0.167 |
| 0.68 | `id_validation_accuracy` | 24 | 0.917 | 0.000 |
| 0.74 | `compatibility_discovered` | 24 | 0.961 | 0.038 |
| 0.74 | `compatibility_wrong` | 24 | 0.750 | -0.173 |
| 0.74 | `id_validation_accuracy` | 24 | 0.923 | 0.000 |

## Interpretation

This phase tests the deployable version of the semantic retrieval claim: when train and ID validation are insufficient to choose among candidates, learned compatibility is used as the selector before OOD labels are inspected.
