# Hook-Output Dose-Response Replication - 2026-06-08

## Question

Does the label-free target-state transfer ridge survive the hook-output surface fix, a broader baseline, and a second seed?

The earlier dose-response run found a downstream definition-transfer ridge from layers `4-5` into a layer-`6` readout, but withheld same-layer `6 -> 6` because the source-noop sanity gate failed. The same-layer diagnostic later showed this was a patch-vector surface mismatch: final hidden states were being injected into a pre-final-layernorm block-output hook. This run repeats the dose-response with `hook_output` patch vectors.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Patch-vector surface: `hook_output`
- Injection layers: `3,4,5,6`
- Readout layer: `6`
- Patch alphas: `0.5,0.75,1.0`
- Pair set: `combined`
- Focus pairs: 7 previous source-family rows
- Baseline pairs: 24 sampled ordered concept pairs per seed
- Patch text regimes: `definition`, `neutral`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Train variants: `0,1`
- Eval variant: `2`
- Seeds: `20260608`, `20260609`

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 3,4,5,6 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alphas 0.5,0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --patch-vector-surface hook_output --pair-set combined --baseline-sample-count 24 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 3,4,5,6 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alphas 0.5,0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --patch-vector-surface hook_output --pair-set combined --baseline-sample-count 24 --seed 20260609 --out artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed20260609.json
```

Analysis helper:

```bash
python3 scripts/summarize_label_free_dose_response.py artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed20260608.json artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed20260609.json
```

## Manifest Sanity

| Artifact | Model | Seed | Surface | Injection layers | Readout | Alphas | Regimes | Baseline N | Pairs |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: |
| seed 20260608 | EleutherAI/pythia-70m-deduped | 20260608 | hook_output | 3,4,5,6 | 6 | 0.5,0.75,1.0 | definition,neutral | 24 | 31 |
| seed 20260609 | EleutherAI/pythia-70m-deduped | 20260609 | hook_output | 3,4,5,6 | 6 | 0.5,0.75,1.0 | definition,neutral | 24 | 31 |

## Source-Noop Gate

The hook-output identity gate passed exactly.

Across both seeds, all `definition/source_noop` aggregate deltas were `0.0`:

| Seeds | Aggregate rows | Max abs source-noop delta | Mean abs source-noop delta |
| --- | ---: | ---: | ---: |
| 20260608, 20260609 | 744 | 0.000 | 0.000 |

This includes every same-layer `6 -> 6` cell. The old `hidden_state` same-layer withholding is therefore superseded for hook-output patch vectors.

## All-Pair Definition Dose Response

Combined across both seeds, `N = 62` pair rows per cell.

| Injection -> readout | Alpha | Specific passes | Pass rate | Mean target delta | Median target delta | Mean advantage | Median advantage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 -> 6 | 0.50 | 10/62 | 16.1% | 0.061 | 0.060 | 0.002 | 0.018 |
| 3 -> 6 | 0.75 | 15/62 | 24.2% | 0.103 | 0.102 | -0.004 | 0.031 |
| 3 -> 6 | 1.00 | 25/62 | 40.3% | 0.145 | 0.133 | 0.005 | 0.030 |
| 4 -> 6 | 0.50 | 28/62 | 45.2% | 0.141 | 0.151 | 0.057 | 0.076 |
| 4 -> 6 | 0.75 | 38/62 | 61.3% | 0.239 | 0.256 | 0.092 | 0.107 |
| 4 -> 6 | 1.00 | 38/62 | 61.3% | 0.312 | 0.319 | 0.117 | 0.148 |
| 5 -> 6 | 0.50 | 36/62 | 58.1% | 0.214 | 0.213 | 0.114 | 0.127 |
| 5 -> 6 | 0.75 | 46/62 | 74.2% | 0.337 | 0.348 | 0.169 | 0.174 |
| 5 -> 6 | 1.00 | 46/62 | 74.2% | 0.411 | 0.430 | 0.192 | 0.193 |
| 6 -> 6 | 0.50 | 44/62 | 71.0% | 0.281 | 0.279 | 0.168 | 0.158 |
| 6 -> 6 | 0.75 | 52/62 | 83.9% | 0.424 | 0.443 | 0.231 | 0.210 |
| 6 -> 6 | 1.00 | 54/62 | 87.1% | 0.494 | 0.501 | 0.246 | 0.217 |

The ridge is stable across seeds. Layers `4`, `5`, and now valid same-layer `6` show positive target-over-control advantage with alpha dose-response. Layer `3` increases raw target margin, but remains close to control parity.

## Neutral Carrier Comparison

Combined across both seeds, `N = 62` pair rows per cell.

| Injection -> readout | Alpha | Specific passes | Pass rate | Mean target delta | Median target delta | Mean advantage | Median advantage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 -> 6 | 0.50 | 1/62 | 1.6% | 0.105 | 0.103 | -0.011 | -0.009 |
| 3 -> 6 | 0.75 | 6/62 | 9.7% | 0.130 | 0.111 | -0.003 | -0.003 |
| 3 -> 6 | 1.00 | 7/62 | 11.3% | 0.127 | 0.113 | 0.001 | 0.002 |
| 4 -> 6 | 0.50 | 3/62 | 4.8% | 0.114 | 0.099 | -0.012 | -0.007 |
| 4 -> 6 | 0.75 | 6/62 | 9.7% | 0.137 | 0.136 | -0.002 | -0.002 |
| 4 -> 6 | 1.00 | 6/62 | 9.7% | 0.132 | 0.116 | 0.002 | 0.003 |
| 5 -> 6 | 0.50 | 1/62 | 1.6% | 0.141 | 0.144 | -0.000 | 0.000 |
| 5 -> 6 | 0.75 | 8/62 | 12.9% | 0.142 | 0.147 | 0.001 | 0.001 |
| 5 -> 6 | 1.00 | 7/62 | 11.3% | 0.151 | 0.140 | 0.005 | 0.006 |
| 6 -> 6 | 0.50 | 10/62 | 16.1% | 0.082 | 0.076 | 0.016 | 0.009 |
| 6 -> 6 | 0.75 | 13/62 | 21.0% | 0.147 | 0.151 | 0.020 | 0.011 |
| 6 -> 6 | 1.00 | 13/62 | 21.0% | 0.192 | 0.199 | 0.020 | 0.016 |

Neutral carrier patches can still nudge target margins, especially same-layer, but they do not match definition patches on specificity or target-over-control advantage. At `6 -> 6`, alpha `1.0`, definition reaches `54/62` passes and mean advantage `0.246`; neutral reaches only `13/62` and mean advantage `0.020`.

## Baseline-Only Definition Rows

Combined across both seeds, `N = 48` sampled baseline rows per cell.

| Injection -> readout | Alpha | Specific passes | Pass rate | Mean target delta | Mean advantage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 -> 6 | 0.50 | 6/48 | 12.5% | 0.055 | -0.003 |
| 3 -> 6 | 0.75 | 11/48 | 22.9% | 0.096 | -0.015 |
| 3 -> 6 | 1.00 | 17/48 | 35.4% | 0.136 | -0.009 |
| 4 -> 6 | 0.50 | 18/48 | 37.5% | 0.133 | 0.048 |
| 4 -> 6 | 0.75 | 24/48 | 50.0% | 0.227 | 0.076 |
| 4 -> 6 | 1.00 | 24/48 | 50.0% | 0.294 | 0.096 |
| 5 -> 6 | 0.50 | 24/48 | 50.0% | 0.202 | 0.103 |
| 5 -> 6 | 0.75 | 32/48 | 66.7% | 0.321 | 0.154 |
| 5 -> 6 | 1.00 | 32/48 | 66.7% | 0.394 | 0.175 |
| 6 -> 6 | 0.50 | 30/48 | 62.5% | 0.272 | 0.159 |
| 6 -> 6 | 0.75 | 38/48 | 79.2% | 0.413 | 0.221 |
| 6 -> 6 | 1.00 | 40/48 | 83.3% | 0.483 | 0.236 |

The broad baseline rows show the same layer and alpha structure. This is important: the phenomenon is not confined to the original attractor-family rows.

## Focus-vs-Baseline Percentiles

| Seed | Kind | Count | Specific passes | Pass rate | Mean target delta | Mean advantage | Mean advantage percentile | Max advantage percentile |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20260608 | baseline_distribution | 288 | 143/288 | 49.7% | 0.240 | 0.071 | n/a | n/a |
| 20260608 | positive | 12 | 12/12 | 100.0% | 0.205 | 0.190 | 70.5% | 79.2% |
| 20260608 | source_family | 48 | 36/48 | 75.0% | 0.329 | 0.166 | 67.0% | 97.2% |
| 20260608 | generic_control | 24 | 20/24 | 83.3% | 0.296 | 0.143 | 64.2% | 88.2% |
| 20260609 | baseline_distribution | 288 | 153/288 | 53.1% | 0.265 | 0.136 | n/a | n/a |
| 20260609 | positive | 12 | 12/12 | 100.0% | 0.205 | 0.190 | 65.6% | 75.3% |
| 20260609 | source_family | 48 | 36/48 | 75.0% | 0.329 | 0.166 | 61.1% | 94.8% |
| 20260609 | generic_control | 24 | 20/24 | 83.3% | 0.296 | 0.114 | 52.1% | 78.5% |

This does not revive the attractor-specific basin claim. Source-family rows pass, but their mean advantage is only around the `61-67%` baseline percentile, and generic controls pass at `83.3%`. Some individual source-family rows remain high-tail, but the family is not exceptional as a group.

## Interpretation

Accepted result:

```text
Pythia-70M-deduped has a stable label-free target-state transfer ridge:
definition-derived target states injected at hook-output layers 4, 5, and 6
move a held-out layer-6 concept readout toward the target, with alpha
dose-response and exact source-noop identity.
```

The key update over the earlier report is that same-layer `6 -> 6` is now valid under hook-output patch vectors. It is also the strongest cell in the grid: combined definition pass rate rises from `71.0%` at alpha `0.5` to `87.1%` at alpha `1.0`.

Rejected or still demoted claim:

```text
This is still not established as an attractor-specific basin.
The same layer/alpha ridge appears in broad baseline rows and generic controls.
```

Best current framing:

```text
The evidence supports a general definition-derived concept-state transport
mechanism in late Pythia-70M representations, not a special attractor-only basin.
```

The interesting residual has sharpened. We are no longer asking whether the effect exists. It does. The next question is what geometric operation makes a definition-state patch broadly legible to a held-out readout, and whether that operation predicts behavior or only readout-space movement.

## Limitations

- One model checkpoint.
- One readout layer.
- Baseline rows are broader than before but still sampled from the same concept set.
- The readout is nearest-centroid in activation space, not a trained probe or behavior-level metric.
- Same-layer `6 -> 6` is valid as a hook-surface intervention, but it may partly reflect direct replacement of the readout layer's own representation.

## Next Move

Move from readout-space movement to a stronger verifier:

- Train a linear held-out readout on hook-output vectors and compare it with the nearest-centroid readout.
- Add a behavior-level multiple-choice task using label-free concept prompts.
- Test whether the hook-output ridge transfers to a second checkpoint or model.
- Separate "direct readout replacement" from "downstream propagation" by comparing `4 -> 6`, `5 -> 6`, and `6 -> 6` under identical trained-readout and behavior gates.

## Discovery-Regime Audit

Question: does the label-free transfer ridge survive hook-output surface correction, a broader baseline, and a second seed?

Current regime:

- Artifact types: label-free patch payloads, hook-output patch-vector manifests, sampled baseline-pair rows, source-noop identity tables, dose-response summaries.
- Operations: hook-output activation capture, held-out centroid readout training, final-token activation patching at transformer-block outputs, target-vs-control specificity aggregation.
- Gates/verifiers: exact source-noop identity, definition-vs-neutral stress, alpha dose-response, baseline percentile comparison, two-seed replication.
- Known limitations: one checkpoint, one readout layer, nearest-centroid readout, no behavior-level task yet.

Action class:

- Retrieval/search/discovery: consolidation search with verifier refinement.
- Why: the run keeps the existing label-free patch schema but tests the ridge under a corrected surface, larger null, and second seed; the accepted same-layer cell revises a previously withheld artifact class.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed*.json`.
- Positive targets: focus rows plus 24 sampled baseline pairs per seed.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, broad baseline rows.
- Stress tests: injection layers `3,4,5,6`; alphas `0.5,0.75,1.0`; two seeds; same-layer hook-output identity.

Gate:

- Acceptance rule: accept the replicated ridge only if source-noop is exact, definition patches show a stable layer/alpha specificity ridge across seeds, and neutral carriers do not match it.
- Withheld/rejected rule: reject attractor-specific revival unless focus/source-family rows are clearly exceptional against baseline and generic controls.

Results:

- Accepted artifacts: this report; `scripts/summarize_label_free_dose_response.py`.
- Rejected or withheld artifacts: no hook-output same-layer cells are withheld; attractor-specific revival is rejected.
- Key metrics: source-noop max delta `0.0` across 744 aggregates; combined definition pass rates reach `38/62` at `4 -> 6`, `46/62` at `5 -> 6`, and `54/62` at `6 -> 6`; neutral at `6 -> 6`, alpha `1.0` reaches only `13/62`.
- Variance or ablation: two seeds agree on the layer/alpha ridge; baseline-only rows show the same ridge, with `40/48` passes at `6 -> 6`, alpha `1.0`.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic rather than attractor-specific.
- New content outside old regime: same-layer `6 -> 6` is now a valid hook-output artifact and is the strongest point on the ridge.
- Retractions or supersessions: supersede "same-layer cells are invalid/unknown" with "same-layer cells are valid under hook-output patch vectors, but not attractor-specific."

Next move: use trained readouts and behavior-level gates to distinguish representational transport from readout-only movement.
