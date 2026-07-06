# Phase 5 External Validity L4 Suite

## Discovery-Regime Audit

Question: Which Phase 4 mechanisms transport when the setup becomes model-like, semantic, or counterfactual?

Current regime:
- Artifact types: JSON suite payloads, gate summaries, result reports, paper PDFs.
- Operations: cheap L4-parallel transport cells across four external-validity proxy harnesses.
- Gates/verifiers: predeclared pass/fail criteria, controls that should fail, lint/type/test checks, PDF render inspection.
- Known limitations: proxy transport result; real open-model runs remain the next heavier validation tier.

Action class:
- Search/discovery: discovery only where a Phase 4 mechanism survives a harder transport gate and controls fail.

Gate:
- Acceptance rule: each transport track must clear its track-specific gate before the mechanism is promoted.
- Withheld/rejected rule: failed controls and bounded negatives remain in the report as future baselines.

## Manifest

- preset: `full`
- tracks: `['language_action_transport', 'foundation_semantic_metric', 'role_routed_world_model', 'topology_seam_causality']`
- seeds: `64`
- gpu: `L4`
- claim_level: `external-validity proxy result`
- budget estimate: 256 L4 cells, conservative timeout cost $51.15 / $1000.00
- rows: `1216`

## Gate Summary

| Track | Status | Criteria | Key metrics | Claim |
| --- | --- | --- | --- | --- |
| `foundation_semantic_metric` | PASS | value adapter lift/spec positive, cross-encoder transfer strong, random control low, no collapse | collapse_index=0.092; cross_encoder_transfer=1.425; moved_location_lift=0.228; random_specificity=0.001; specificity=0.166 | semantic metric deformation transports to a foundation-style frozen-encoder proxy |
| `language_action_transport` | PASS | instruction proxy r>=0.55, heldout r>=0.45, intervention ratio>=3, controls low | control_fraction=0.117; geometry_action_r=0.858; heldout_transfer_r=0.837; intervention_ratio=4.472; tiny_ratio=1.527 | language action coupling transports in the stronger open-model proxy, not in tiny controls |
| `role_routed_world_model` | PASS | role/MoE MAE low, shared and swap controls fail, counterfactual consistency high | moe_mae=0.040; moe_ood_return=100.000; role_counterfactual_consistency=0.966; role_mae=0.036; shared_mae=0.316; swap_mae=0.556 | the mediated-identifiability ceiling breaks in a richer role-routed world model |
| `topology_seam_causality` | PASS | seam effect strong, topology alone weak, joint topology-by-seam interaction present | both_fixed_ood=0.833; joint_interaction=0.089; seam_only_lift=0.400; seam_partial_with_topology=0.961; topology_only_lift=0.118; topology_only_ood=0.344; topology_partial_with_seam=0.747 | seam consistency is the causal carrier; topology alone remains insufficient |

Overall: **PASS**

## Condition Means

### foundation_semantic_metric

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `cross_encoder_transfer` | 64 | cross_encoder_transfer=1.425; moved_location_lift=0.236; specificity=0.173 |
| `frozen_encoder` | 64 | cross_encoder_transfer=0.000; moved_location_lift=0.009; specificity=0.001 |
| `random_value_adapter` | 64 | cross_encoder_transfer=-0.002; moved_location_lift=0.009; specificity=0.001 |
| `value_weighted_adapter` | 64 | cross_encoder_transfer=1.648; moved_location_lift=0.228; specificity=0.166 |

### language_action_transport

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `instruction_tuned_transport` | 64 | geometry_action_r=0.858; heldout_transfer_r=0.837; intervention_ratio=4.472 |
| `l4_open_lm_proxy` | 64 | geometry_action_r=0.762; heldout_transfer_r=0.713; intervention_ratio=3.596 |
| `shuffled_axis_control` | 64 | geometry_action_r=0.005; heldout_transfer_r=-0.004; intervention_ratio=1.088 |
| `small_open_lm_proxy` | 64 | geometry_action_r=0.403; heldout_transfer_r=0.344; intervention_ratio=2.404 |
| `tiny_lm_control` | 64 | geometry_action_r=0.087; heldout_transfer_r=0.069; intervention_ratio=1.527 |

### role_routed_world_model

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `confounded_shortcut` | 64 | counterfactual_consistency=0.000; mediated_mae=0.273; ood_return=0.000 |
| `counterfactual_swap_control` | 64 | counterfactual_consistency=0.000; mediated_mae=0.556; ood_return=0.000 |
| `mixture_of_experts` | 64 | counterfactual_consistency=0.965; mediated_mae=0.040; ood_return=100.000 |
| `role_routed_heads` | 64 | counterfactual_consistency=0.966; mediated_mae=0.036; ood_return=100.000 |
| `shared_head` | 64 | counterfactual_consistency=0.479; mediated_mae=0.316; ood_return=0.000 |

### topology_seam_causality

| Condition | n | Primary metrics |
| --- | ---: | --- |
| `both_broken` | 64 | joint_interaction=0.089; mean_ood=0.227; seam_only_lift=0.400; seam_partial_with_topology=0.961; topology_only_lift=0.118 |
| `both_fixed` | 64 | joint_interaction=0.089; mean_ood=0.833; seam_only_lift=0.400; seam_partial_with_topology=0.961; topology_only_lift=0.118 |
| `phase_randomized_control` | 64 | joint_interaction=0.089; mean_ood=0.481; seam_only_lift=0.400; seam_partial_with_topology=0.961; topology_only_lift=0.118 |
| `seam_only` | 64 | joint_interaction=0.089; mean_ood=0.626; seam_only_lift=0.400; seam_partial_with_topology=0.961; topology_only_lift=0.118 |
| `topology_only` | 64 | joint_interaction=0.089; mean_ood=0.344; seam_only_lift=0.400; seam_partial_with_topology=0.961; topology_only_lift=0.118 |
