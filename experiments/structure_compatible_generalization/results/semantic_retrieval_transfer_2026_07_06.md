# Phase 5: Semantic Retrieval Transfer

## Manifest

- **base_seed:** `20260706`
- **discovered_threshold:** `0.62`
- **encoder_keys:** `['all_minilm_l6_v2', 'bge_small_en_v1_5']`
- **gpu:** `L4`
- **max_containers:** `8`
- **n_configs:** `32`
- **suite:** `semantic retrieval transfer`
- **budget:** 2 L4 cells, conservative $0.80 against $30.00

## Discovery-Regime Audit

- Old regime: rendered templates supplied explicit substitution structure.
- New operation: infer semantic paraphrase/entity orbits from frozen-encoder neighborhoods and test retrieval OOD.
- Claim level: frozen-encoder semantic transfer, not arbitrary open-world paraphrase certification.

## Predictor Correlations

| Domain | Predictor | Pearson r | Spearman r | N |
| --- | --- | ---: | ---: | ---: |
| `semantic_retrieval_frozen_encoder` | `compatibility_true` | 0.940 | 0.915 | 64 |
| `semantic_retrieval_frozen_encoder` | `compatibility_discovered` | 0.861 | 0.863 | 64 |
| `semantic_retrieval_frozen_encoder` | `train_accuracy` | 0.772 | 0.628 | 64 |
| `semantic_retrieval_frozen_encoder` | `id_validation_accuracy` | 0.709 | 0.488 | 64 |
| `semantic_retrieval_frozen_encoder` | `compatibility_wrong` | -0.872 | -0.919 | 64 |

## Encoder Breakdown

| Encoder | N | Mean train | Mean ID | Mean OOD | Mean learned compatibility |
| --- | ---: | ---: | ---: | ---: | ---: |
| `all_minilm_l6_v2` | 32 | 0.939 | 0.912 | 0.860 | 0.940 |
| `bge_small_en_v1_5` | 32 | 0.955 | 0.920 | 0.863 | 0.907 |

## Selector Family Breakdown

| Family | N | Mean train | Mean ID | Mean OOD | Mean learned compatibility |
| --- | ---: | ---: | ---: | ---: | ---: |
| `centroid` | 13 | 1.000 | 1.000 | 0.988 | 0.985 |
| `hybrid` | 12 | 1.000 | 1.000 | 0.974 | 0.983 |
| `knn` | 12 | 0.969 | 0.911 | 0.971 | 0.966 |
| `lexical` | 13 | 1.000 | 1.000 | 0.750 | 0.870 |
| `projected_centroid` | 14 | 0.786 | 0.692 | 0.658 | 0.828 |

## Interpretation

The semantic retrieval phase asks whether learned compatibility remains useful when the transformation family is inferred from actual frozen text-encoder neighborhoods rather than supplied as a finite symbolic substitution.
