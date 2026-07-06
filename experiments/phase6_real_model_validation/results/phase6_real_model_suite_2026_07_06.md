# Phase 6 Real-Model Validation L4 Suite

## Discovery-Regime Audit

Question: Do the Phase 5 proxy transport signals survive contact with actual open LMs and frozen text encoders?

Current regime:
- Artifact types: JSON model payloads, gate summaries, markdown report, paper PDF, and archived copy.
- Operations: L4-parallel Hugging Face decoder-LM logprob/hidden-state cells and frozen-encoder metric cells.
- Gates/verifiers: predeclared signal thresholds, failed-model rows retained, budget guard, lint/type/test checks, PDF render inspection.
- Known limitations: LM logprob margins are model text behavior, not human action; frozen-encoder metric deformation is post-hoc, not finetuning.

Action class:
- Validation tier: replaces Phase 5 proxy weights with public open-model/frozen-encoder measurements.

Gate:
- Acceptance rule: actual models must run and clear weak positive transport thresholds with controls below the promoted effect.
- Withheld/rejected rule: failed downloads, weak LM coupling, random-label deformation, and cue leakage remain explicit rows.

## Manifest

- preset: `full`
- tracks: `['open_lm_action_coupling', 'frozen_encoder_metric_deformation']`
- models: `['distilgpt2', 'pythia_70m', 'qwen2_0_5b_instruct', 'all_minilm_l6_v2', 'bge_small_en_v1_5']`
- gpu: `L4`
- claim_level: `actual open-LM and frozen-encoder validation result`
- budget estimate: 5 L4 cells, conservative timeout cost $2.00 / $1000.00
- rows: `5`

## Gate Summary

| Track | Status | Criteria | Key metrics | Claim |
| --- | --- | --- | --- | --- |
| `frozen_encoder_metric_deformation` | PASS | two frozen encoders; value metric lifts held-out value margin, random labels stay low, transfer AUC positive, no collapse | collapse_index=0.095; deformed_margin_lift=0.409; deformed_neighbor_precision=1.000; deformed_precision_lift=0.000; off_target_drift=0.000; ok_models=2.000; random_margin_lift=0.008; raw_neighbor_precision=1.000; template_transfer_auc=1.000 | a value-weighted metric deformation transports across actual frozen text encoders |
| `open_lm_action_coupling` | PASS | at least two open LMs run; at least three signal tests clear weak positive thresholds | geometry_action_r=0.340; label_geometry_gap=0.061; label_margin_lift=1.064; margin_auc=0.688; max_cue_specificity=1.312; ok_models=3.000; signal_count=5.000 | actual open LMs show measured concern/action transport signals without proxy weights |

Overall: **PASS**

## Model Rows

### frozen_encoder_metric_deformation

| Condition | Model | Status | Primary metrics |
| --- | --- | --- | --- |
| `all_minilm_l6_v2` | `sentence-transformers/all-MiniLM-L6-v2` | ok | collapse_index=0.094; deformed_margin_lift=0.377; deformed_neighbor_precision=1.000; deformed_precision_lift=0.000; deformed_value_margin=0.694; elapsed_seconds=15.852; off_target_drift=0.000; random_margin_lift=0.006; random_precision_lift=-0.050; raw_neighbor_precision=1.000; raw_value_margin=0.316; template_transfer_auc=1.000 |
| `bge_small_en_v1_5` | `BAAI/bge-small-en-v1.5` | ok | collapse_index=0.097; deformed_margin_lift=0.441; deformed_neighbor_precision=1.000; deformed_precision_lift=0.000; deformed_value_margin=0.641; elapsed_seconds=17.086; off_target_drift=0.000; random_margin_lift=0.011; random_precision_lift=-0.050; raw_neighbor_precision=1.000; raw_value_margin=0.201; template_transfer_auc=1.000 |

### open_lm_action_coupling

| Condition | Model | Status | Primary metrics |
| --- | --- | --- | --- |
| `distilgpt2` | `distilgpt2` | ok | cue_specificity=-0.124; elapsed_seconds=21.210; geometry_action_r=0.454; label_geometry_gap=0.016; label_margin_lift=0.703; margin_auc=0.750 |
| `pythia_70m` | `EleutherAI/pythia-70m-deduped` | ok | cue_specificity=-3.250; elapsed_seconds=22.704; geometry_action_r=-0.035; label_geometry_gap=0.012; label_margin_lift=0.000; margin_auc=0.500 |
| `qwen2_0_5b_instruct` | `Qwen/Qwen2.5-0.5B-Instruct` | ok | cue_specificity=1.312; elapsed_seconds=32.232; geometry_action_r=0.602; label_geometry_gap=0.153; label_margin_lift=2.488; margin_auc=0.812 |
