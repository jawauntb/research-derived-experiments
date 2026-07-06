# Phase 4 Metaphysics L4 Suite

## Discovery-Regime Audit

Question: Can the Metric Stack learn the missing conditions that Phase 3 had to hand-specify?

Current regime:
- Artifact types: JSON suite payloads, gate summaries, result reports, paper PDFs.
- Operations: cheap L4-parallel diagnostic cells across seven controlled harnesses.
- Gates/verifiers: predeclared pass/fail criteria per open question, negative controls, lint/type/test checks.
- Known limitations: controlled synthetic/diagnostic harnesses; not yet foundation-model or biological generality.

Action class:
- Search/discovery: search inside known program schema, with discovery claim only where a new mechanism survives controls.

Gate:
- Acceptance rule: each track-specific gate must pass for a Phase 4 mechanism claim.
- Withheld/rejected rule: any failed track remains a bounded negative and cannot be promoted into the synthesis claim.

## Manifest

- preset: `full`
- tracks: `['language_scale', 'neural_symmetry', 'learned_regimes', 'probe_value', 'beyond_ceiling', 'semantic_metric', 'topology_mediation']`
- seeds: `48`
- gpu: `L4`
- claim_level: `diagnostic controlled-harness result`
- budget estimate: 336 L4 cells, conservative timeout cost $67.13 / $1000.00
- rows: `1440`

## Gate Summary

| Track | Status | Criteria | Key metrics | Claim |
| --- | --- | --- | --- | --- |
| `beyond_ceiling` | PASS | role heads MAE<=0.04, MoE<=0.07, wrong-history fails, shared head worse | moe_mae=0.039; role_mae=0.036; shared_mae=0.205; wrong_history_mae=0.151 | the Phase 3 ceiling is architectural in this harness |
| `language_scale` | FAIL | large post-coupling r>=0.45, intervention ratio>=3, random control low | intervention_ratio=2.360; post_logprob_r=0.670; random_fraction=0.205 | language-scale diagnostic mechanism, not foundation-model generality |
| `learned_regimes` | PASS | learned gate within 5 return points of oracle, boundary acc>=0.95, smooth baseline fails | learned_boundary_accuracy=1.000; learned_return=50.000; oracle_return=50.000; smooth_boundary_accuracy=0.500 | regime variables can be learned when hard partition is in hypothesis class |
| `neural_symmetry` | PASS | closure generator F1>=0.80, beats raw by>=0.20, preserves OOD lift | closure_f1=0.945; closure_ood_lift=0.908; pixel_ood_lift=0.899; raw_f1=0.568 | non-enumerative discovery needs closure constraints |
| `probe_value` | PASS | learned VOI beats random by>=25%, Spearman>=0.50, and beats current-error | current_error_reduction=-0.110; learned_voi_reduction=0.323; learned_voi_spearman=0.840 | probe policy should learn marginal information value, not current error |
| `semantic_metric` | PASS | moved lift>=0.35, specificity>=0.25, transfer>=0.20, controls low | frozen_specificity=-0.000; lift=0.508; random_specificity=0.000; specificity=0.504; transfer_specificity=0.504 | semantic-style metric deformation works in a controlled embedding harness |
| `topology_mediation` | PASS | topology mediates before seam control (r>=0.20), vanishes with seam, seam remains causal | broken_seam_ood=0.346; forced_topology_ood=0.716; seam_partial_with_topology=0.921; topology_partial=0.208; topology_partial_with_seam=0.004 | topology needs seam consistency to mediate OOD in this harness |

Overall: **FAIL**

## Condition Means

### beyond_ceiling

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `disjoint_per_role_heads` | 48 | mediated_mae=0.036 |
| `mixture_of_experts` | 48 | mediated_mae=0.039 |
| `shared_mediated_head` | 48 | mediated_mae=0.205 |
| `wrong_history_control` | 48 | mediated_mae=0.151 |

### language_scale

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `large_post_action_coupling` | 48 | intervention_effect=0.066; specificity=0.053; weakness_logprob_r=0.670 |
| `large_pre_action_coupling` | 48 | intervention_effect=0.028; specificity=0.015; weakness_logprob_r=0.066 |
| `medium_post_action_coupling` | 48 | intervention_effect=0.045; specificity=0.031; weakness_logprob_r=0.483 |
| `medium_pre_action_coupling` | 48 | intervention_effect=0.028; specificity=0.014; weakness_logprob_r=0.049 |
| `small_post_action_coupling` | 48 | intervention_effect=0.034; specificity=0.020; weakness_logprob_r=0.283 |
| `small_pre_action_coupling` | 48 | intervention_effect=0.028; specificity=0.014; weakness_logprob_r=0.017 |

### learned_regimes

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `fourier_features` | 48 | boundary_accuracy=1.000; return_50=50.000 |
| `learned_hard_gate` | 48 | boundary_accuracy=1.000; return_50=50.000 |
| `oracle_boundary` | 48 | boundary_accuracy=1.000; return_50=50.000 |
| `smooth_mlp` | 48 | boundary_accuracy=0.500; return_50=25.000 |

### neural_symmetry

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `neural_generator_closure` | 48 | f1=0.945; ood_lift=0.908 |
| `neural_generator_raw` | 48 | f1=0.568; ood_lift=0.596 |
| `pixel_enumerative` | 48 | f1=0.987; ood_lift=0.899 |

### probe_value

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `current_error` | 48 | final_mae=0.555; mae_reduction_vs_random=-0.110; voi_spearman=-0.257 |
| `current_replay` | 48 | final_mae=0.350; mae_reduction_vs_random=0.299; voi_spearman=0.592 |
| `ensemble_variance` | 48 | final_mae=0.441; mae_reduction_vs_random=0.118; voi_spearman=0.228 |
| `learned_voi` | 48 | final_mae=0.338; mae_reduction_vs_random=0.323; voi_spearman=0.840 |
| `matched_random` | 48 | final_mae=0.501; mae_reduction_vs_random=0.000; voi_spearman=-0.009 |

### semantic_metric

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `frozen_encoder` | 48 | moved_location_lift=-0.000; specificity=-0.000 |
| `random_value` | 48 | moved_location_lift=0.033; specificity=0.000 |
| `value_weighted` | 48 | moved_location_lift=0.508; specificity=0.504 |

### topology_mediation

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `broken_seam` | 48 | mean_ood=0.346; seam_partial_with_topology=0.921; topology_partial_loss_weakness=0.208 |
| `forced_topology` | 48 | mean_ood=0.716; seam_partial_with_topology=0.921; topology_partial_loss_weakness=0.208 |
| `full_translation` | 48 | mean_ood=0.848; seam_partial_with_topology=0.921; topology_partial_loss_weakness=0.208 |
| `none` | 48 | mean_ood=0.333; seam_partial_with_topology=0.921; topology_partial_loss_weakness=0.208 |
| `partial_translation` | 48 | mean_ood=0.569; seam_partial_with_topology=0.921; topology_partial_loss_weakness=0.208 |
