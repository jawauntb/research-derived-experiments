# Same-Layer Hook-Surface Diagnostic - 2026-06-08

## Question

Why did the label-free dose-response run fail the source-noop sanity gate for same-layer `6 -> 6` patching?

The dose-response report withheld same-layer cells because `source_noop` was nonzero when injection and readout were both layer `6`. This diagnostic tests whether the failure was a real non-identity intervention or a mismatch between the patch-vector surface and the hook surface.

## Diagnosis

The failure was a hook/readout-surface mismatch.

For Pythia/GPT-NeoX, patching `injection_layer=6` hooks the raw output of the sixth transformer block. The existing patch-vector path used `outputs.hidden_states[6]`. For a 6-layer Pythia model, that hidden-state index is post-final-layernorm, while the hook edits the pre-final-layernorm block output. So the old same-layer source-noop path wrote a final-normalized vector into the raw block-output slot, and the model then applied final layernorm again.

The fix is to capture patch vectors at the exact hook surface. The runner now supports:

```text
--patch-vector-surface hook_output
--patch-vector-surface hidden_state
```

and defaults to `hook_output`.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_same_layer_hidden_state_surface.json
artifacts/activation_geometry/modal_pythia_70m_same_layer_hook_output_surface.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Injection layers: `5,6`
- Readout layer: `6`
- Patch alpha: `1.0`
- Pair set: `focus`
- Patch text regime: `definition`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Patch-vector surfaces: `hidden_state`, `hook_output`
- Seed: `20260608`

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 5,6 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alpha 1.0 --patch-vector-surface hidden_state --patch-modes target,distractor,random,source_noop --patch-text-regimes definition --pair-set focus --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_same_layer_hidden_state_surface.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 5,6 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alpha 1.0 --patch-vector-surface hook_output --patch-modes target,distractor,random,source_noop --patch-text-regimes definition --pair-set focus --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_same_layer_hook_output_surface.json
```

## Source-Noop Gate

| Patch-vector surface | Injection -> readout | Rows | Max abs source-noop delta | Mean abs source-noop delta |
| --- | --- | ---: | ---: | ---: |
| hidden_state | 5 -> 6 | 7 | 0.000 | 0.000 |
| hidden_state | 6 -> 6 | 7 | 0.247 | 0.119 |
| hook_output | 5 -> 6 | 7 | 0.000 | 0.000 |
| hook_output | 6 -> 6 | 7 | 0.000 | 0.000 |

This confirms the root cause. The old `hidden_state` patch vectors were valid for strict downstream `5 -> 6`, but invalid for same-layer final-block `6 -> 6`. Capturing vectors at the hook output surface restores the exact no-op in both cases.

## Specificity Summary

| Surface | Injection -> readout | Kind | Specific passes | Mean target delta | Mean advantage |
| --- | --- | --- | ---: | ---: | ---: |
| hidden_state | 5 -> 6 | positive | 1/1 | 0.259 | 0.259 |
| hidden_state | 5 -> 6 | source_family | 4/4 | 0.516 | 0.264 |
| hidden_state | 5 -> 6 | generic_control | 2/2 | 0.489 | 0.246 |
| hidden_state | 6 -> 6 | positive | 0/1 | -0.108 | 0.094 |
| hidden_state | 6 -> 6 | source_family | 4/4 | 0.240 | 0.102 |
| hidden_state | 6 -> 6 | generic_control | 2/2 | 0.389 | 0.099 |
| hook_output | 5 -> 6 | positive | 1/1 | 0.259 | 0.259 |
| hook_output | 5 -> 6 | source_family | 4/4 | 0.516 | 0.264 |
| hook_output | 5 -> 6 | generic_control | 2/2 | 0.489 | 0.246 |
| hook_output | 6 -> 6 | positive | 1/1 | 0.253 | 0.253 |
| hook_output | 6 -> 6 | source_family | 4/4 | 0.579 | 0.286 |
| hook_output | 6 -> 6 | generic_control | 2/2 | 0.569 | 0.307 |

The `hook_output` surface preserves the previous `5 -> 6` numbers and makes `6 -> 6` interpretable. The same-layer result is not a special attractor-only effect; generic controls also transfer strongly.

## Interpretation

The same-layer failure was an instrumentation bug, not evidence against same-layer transfer.

Accepted result:

```text
Patch vectors must be captured at the same surface where they are injected.
For Pythia-70M-deduped, hook-output patch vectors restore exact source-noop
identity for same-layer 6 -> 6 label-free patching.
```

Retraction:

```text
The PR #24 same-layer 6 -> 6 cells should remain withheld as reported, but the
reason is now known: the old hidden_state patch-vector surface was post-final-LN
while the hook surface was pre-final-LN.
```

Practical consequence:

```text
Future label-free patching runs should use hook_output patch vectors by default.
The hidden_state surface is retained only for backwards comparison.
```

## Next Move

Rerun the dose-response ridge with `hook_output` as the default surface:

- Injection layers `3,4,5,6`
- Readout layer `6`
- Patch alphas `0.5,0.75,1.0`
- Larger baseline sample, at least 24 rows
- Two seeds or a second checkpoint/model

Then treat same-layer `6 -> 6` as valid only when the source-noop gate is exact under `hook_output`.

## Discovery-Regime Audit

Question: did same-layer label-free patching fail because the intervention is non-identity, or because patch vectors were captured at the wrong surface?

Current regime:

- Artifact types: label-free patch payloads, patch-vector-surface summaries, source-noop sanity tables.
- Operations: hidden-state vector capture, hook-output vector capture, transformer-block final-token patching, downstream readout scoring.
- Gates/verifiers: source-noop max absolute delta by patch-vector surface and injection/readout pair.
- Known limitations: one model checkpoint, one patch alpha, focus pairs only.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: the run adds patch-vector surface as a first-class verifier dimension and fixes an invalid same-layer measurement.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_same_layer_*_surface.json`.
- Positive targets: focus rows from the label-free readout diagnostic.
- Negative controls: distractor/random/source-noop patch modes.
- Stress tests: compare `hidden_state` against `hook_output` for `5 -> 6` and `6 -> 6`.

Gate:

- Acceptance rule: same-layer cells become interpretable only if `source_noop` is exactly zero at the hook surface.
- Withheld/rejected rule: withhold any same-layer surface that fails source-noop identity.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/modal_label_free_readout_basin.py`; `experiments/activation_geometry/label_free_readout_basin.py`.
- Rejected or withheld artifacts: hidden-state same-layer `6 -> 6` remains rejected as an invalid surface.
- Key metrics: hidden_state `6 -> 6` max source-noop delta `0.247`; hook_output `6 -> 6` max source-noop delta `0.0`; hook_output preserves `5 -> 6` source-noop max delta `0.0`.
- Variance or ablation: `5 -> 6` is identical across surfaces; final-layer same-layer behavior changes only when surface alignment matters.

Residual content:

- Explained by old regime: PR #24's strict downstream ridge remains valid.
- New content outside old regime: patch-vector surface must be explicit for same-layer/final-layer patching.
- Retractions or supersessions: supersede "same-layer cells invalid/unknown" with "same-layer cells are valid under hook-output patch vectors and invalid under post-final-LN hidden-state patch vectors."

Next move: rerun the broader dose-response with `hook_output` and a larger baseline sample.
