# Result Tables for the ICML-Style Package

This file is the human-readable result ledger behind `paper.tex` and
`appendix.tex`. It preserves source paths and claim boundaries so the paper can
be audited without rereading every sparse result memo.

## Phase 1: Cross-Domain Structure-Compatible Generalization

Source:
`experiments/structure_compatible_generalization/results/structure_compatible_l4_2026_07_06.md`

Manifest: base seed `20260706`; domains `symbolic`, `vision`, `modular`;
symbolic models `128`; vision models `96`; modular neural models `128`;
budget estimate `$9.59` against `$50.00`.

| Domain | Rows | Mean train | Mean ID | Mean OOD | Top predictor | Top Pearson r | ID Pearson r |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `modular_exact` | 2 | 1.000 | 1.000 | 0.545 | `compatibility_inferred` | 1.000 | 0.000 |
| `modular_neural` | 128 | 0.732 | 0.732 | 0.165 | `compatibility_true` | 0.649 | 0.188 |
| `symbolic_cyclic` | 128 | 0.973 | 0.984 | 0.394 | `compatibility_true` | 0.763 | 0.099 |
| `vision_rotation` | 96 | 0.773 | 0.773 | 0.380 | `compatibility_true` | 0.451 | 0.445 |

Selection without OOD labels:

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

Claim boundary: finite underspecified tasks with known deployment
transformations; not full OOD certification.

## Phase 2: Inferred Transformations and Intervention

Source:
`experiments/structure_compatible_generalization/results/phase2_transformations_2026_07_06.md`

Manifest: base seed `20260706`; `180` configs; regularization values
`[0.0, 0.05, 0.2]`; budget estimate `$4.80` against `$50.00`.

| Regularization | N | Mean train | Mean OOD | Mean discovered compatibility | High-ID N | High-ID mean OOD |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.000 | 180 | 0.719 | 0.134 | 0.339 | 98 | 0.178 |
| 0.050 | 180 | 0.719 | 0.320 | 0.506 | 98 | 0.519 |
| 0.200 | 180 | 0.723 | 0.352 | 0.546 | 99 | 0.573 |

Claim boundary: neural-validated finite intervention; not a general
transformation-discovery theorem.

## Phase 3: Learned Generators and Transfer

Source:
`experiments/structure_compatible_generalization/results/phase3_learned_generators_2026_07_06.md`

Manifest: base seed `20260706`; modular configs `90`; vision base `36`;
regularization values `[0.0, 0.05, 0.2]`; budget estimate `$4.80` against
`$50.00`.

Predictor correlations:

| Domain | Predictor | Pearson r | Spearman r | N |
| --- | --- | ---: | ---: | ---: |
| `modular_learned_generator` | `compatibility_true` | 0.812 | 0.367 | 270 |
| `modular_learned_generator` | `compatibility_discovered` | 0.787 | 0.474 | 270 |
| `modular_learned_generator` | `id_validation_accuracy` | 0.398 | 0.120 | 270 |
| `modular_learned_generator` | `compatibility_wrong` | -0.085 | 0.049 | 270 |
| `vision_rotation_learned_generator` | `compatibility_true` | 0.678 | 0.591 | 144 |
| `vision_rotation_learned_generator` | `compatibility_discovered` | 0.599 | 0.502 | 144 |
| `vision_rotation_learned_generator` | `id_validation_accuracy` | 0.661 | 0.632 | 144 |

Vision transfer:

| Regime | N | Mean train | Mean OOD | Mean learned compatibility |
| --- | ---: | ---: | ---: | ---: |
| `learned_aug` | 36 | 0.707 | 0.644 | 0.793 |
| `none` | 36 | 0.815 | 0.258 | 0.486 |
| `oracle_aug` | 36 | 0.709 | 0.693 | 0.801 |
| `random_aug` | 36 | 0.679 | 0.610 | 0.760 |

Claim boundary: finite generator-transfer diagnostic; random augmentation is a
serious control in the vision arm and must be discussed.

## Phase 4: Language/Template Substitution Generator

Source:
`experiments/structure_compatible_generalization/results/language_template_substitution_2026_07_06.md`

Manifest: base seed `20260706`; `64` configs; regularization values
`[0.0, 0.05, 0.2, 0.5]`; budget estimate `$3.20` against `$30.00`.

| Predictor | Pearson r | Spearman r | N |
| --- | ---: | ---: | ---: |
| `compatibility_discovered` | 0.858 | 0.596 | 256 |
| `compatibility_true` | 0.853 | 0.628 | 256 |
| `negative_train_loss` | 0.492 | 0.232 | 256 |
| `id_validation_accuracy` | 0.478 | 0.127 | 256 |
| `train_accuracy` | 0.478 | 0.127 | 256 |
| `compatibility_wrong` | -0.088 | 0.059 | 256 |

Regularization intervention:

| Regularization | N | Mean train | Mean ID | Mean OOD | High-ID N | High-ID OOD |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.000 | 64 | 0.554 | 0.554 | 0.147 | 29 | 0.224 |
| 0.050 | 64 | 0.553 | 0.553 | 0.234 | 29 | 0.415 |
| 0.200 | 64 | 0.555 | 0.555 | 0.255 | 29 | 0.463 |
| 0.500 | 64 | 0.558 | 0.558 | 0.277 | 29 | 0.512 |

Claim boundary: finite text-like substitutions; not broad natural-language
paraphrase discovery.

## Phase 5: Semantic Retrieval Transfer

Source:
`experiments/structure_compatible_generalization/results/semantic_retrieval_transfer_2026_07_06.md`

Manifest: base seed `20260706`; encoders `all_minilm_l6_v2` and
`bge_small_en_v1_5`; `32` configs; budget estimate `$0.80` against `$30.00`.

| Predictor | Pearson r | Spearman r | N |
| --- | ---: | ---: | ---: |
| `compatibility_true` | 0.940 | 0.915 | 64 |
| `compatibility_discovered` | 0.861 | 0.863 | 64 |
| `train_accuracy` | 0.772 | 0.628 | 64 |
| `id_validation_accuracy` | 0.709 | 0.488 | 64 |
| `compatibility_wrong` | -0.872 | -0.919 | 64 |

Claim boundary: frozen-encoder semantic transfer; not arbitrary open-world
paraphrase certification.

## Phase 6: Semantic Selection Control

Source:
`experiments/structure_compatible_generalization/results/semantic_selection_control_2026_07_06.md`

Bootstrap source:
`experiments/structure_compatible_generalization/results/semantic_selection_bootstrap_2026_07_06.md`

Manifest: base seed `20260706`; encoders `all_minilm_l6_v2` and
`bge_small_en_v1_5`; `12` zoos; `12` configs per zoo; thresholds
`[0.5, 0.56, 0.62, 0.68, 0.74]`; budget estimate `$0.80` against `$30.00`.

Gate status: all registered gates passed.

| Selector | Zoos | Mean candidates | Selected OOD | Regret | Lift vs random |
| --- | ---: | ---: | ---: | ---: | ---: |
| `random_candidate` | 120 | 8.617 | 0.919 | 0.073 | 0.000 |
| `id_validation_accuracy` | 120 | 8.617 | 0.919 | 0.073 | 0.000 |
| `train_accuracy` | 120 | 8.617 | 0.919 | 0.073 | 0.000 |
| `compatibility_wrong` | 120 | 8.617 | 0.751 | 0.242 | -0.168 |
| `compatibility_discovered` | 120 | 8.617 | 0.978 | 0.014 | 0.059 |
| `compatibility_true` | 120 | 8.617 | 0.993 | 0.000 | 0.073 |
| `ood_oracle` | 120 | 8.617 | 0.993 | 0.000 | 0.073 |

Zoo-level bootstrap intervals, 1,000 reps:

| Metric | Point | 95% CI |
| --- | ---: | ---: |
| `learned_selected_ood` | 0.978 | [0.973, 0.983] |
| `random_selected_ood` | 0.919 | [0.915, 0.924] |
| `id_selected_ood` | 0.919 | [0.915, 0.924] |
| `wrong_selected_ood` | 0.751 | [0.750, 0.753] |
| `learned_regret` | 0.014 | [0.011, 0.018] |
| `learned_lift_vs_random` | 0.059 | [0.052, 0.065] |
| `learned_lift_vs_id` | 0.059 | [0.052, 0.065] |
| `learned_lift_vs_wrong` | 0.227 | [0.221, 0.233] |

Claim boundary: finite semantic retrieval model selection; not universal
semantic/OOD certification.

## Companion Benchmark Results

The causally grounded finite-agent benchmark is a companion appendix, not the
main ICML claim.

### Suite C: Re-Engagement

Sources:

- `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`
- `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.md`

Hand-policy headline `burst_then_refractory`: final affected MAE `0.112`;
first-shift selectivity `16.927`; second-shift reopenability `16.667`; probes
`22.6`; all C1-C6 gates pass.

Learned probe head: final affected MAE `0.112`; first-shift selectivity
`16.667`; second-shift reopenability `17.448`; probes `23.1`; all C1-C6 gates
plus learned signal controls pass.

### Suite D/E: Long-Horizon Commitment

Source:
`experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`

Main lesson: future-critical variables must survive the surfaces where they
control action: hidden states, generated JSON, tool calls, repair branches, and
value-token causal patches.
