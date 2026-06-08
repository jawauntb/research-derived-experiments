# Trained Readout Gate - 2026-06-08

## Question

Does the hook-output label-free transfer ridge survive a trained linear readout, or was the earlier effect an artifact of nearest-centroid scoring?

The previous hook-output dose-response run established a stable late-layer transfer ridge under a centroid readout. This run keeps the same label-free patching setup but adds a multiclass ridge readout trained on held-out concept variants. The gate is deliberately narrow: if the ridge disappears under the trained readout, the prior result should be treated as centroid-specific readout geometry rather than concept-state transport.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Patch-vector surface: `hook_output`
- Injection layers: `4,5,6`
- Readout layer: `6`
- Readout modes: `centroid,ridge`
- Ridge lambda: `1.0`
- Patch alphas: `0.75,1.0`
- Pair set: `combined`
- Baseline pairs: 24 sampled ordered concept pairs per seed
- Patch text regimes: `definition`, `neutral`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Train variants: `0,1`
- Eval variant: `2`
- Seeds: `20260608`, `20260609`

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 4,5,6 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alphas 0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --patch-vector-surface hook_output --readout-modes centroid,ridge --ridge-lambda 1.0 --pair-set combined --baseline-sample-count 24 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 4,5,6 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alphas 0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --patch-vector-surface hook_output --readout-modes centroid,ridge --ridge-lambda 1.0 --pair-set combined --baseline-sample-count 24 --seed 20260609 --out artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed20260609.json
```

Analysis helper:

```bash
python3 scripts/summarize_label_free_dose_response.py artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed20260608.json artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed20260609.json
```

## Manifest Sanity

| Artifact | Model | Seed | Surface | Readout modes | Injection layers | Readout | Alphas | Regimes | Baseline N | Pairs |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: |
| seed 20260608 | EleutherAI/pythia-70m-deduped | 20260608 | hook_output | centroid,ridge | 4,5,6 | 6 | 0.75,1.0 | definition,neutral | 24 | 31 |
| seed 20260609 | EleutherAI/pythia-70m-deduped | 20260609 | hook_output | centroid,ridge | 4,5,6 | 6 | 0.75,1.0 | definition,neutral | 24 | 31 |

## Source-Noop Gate

The definition/source-noop identity gate passed exactly for both readout modes.

| Readout | Aggregate rows | Max abs definition/source-noop delta | Mean abs definition/source-noop delta |
| --- | ---: | ---: | ---: |
| centroid | 372 | 0.000 | 0.000 |
| ridge | 372 | 0.000 | 0.000 |

This gate is specific to definition carriers, where the source-noop patch is an identity check against the same carrier family. Neutral source-noop rows are not used as identity checks because they inject a neutral-source activation into a definition-eval carrier; they are better interpreted as another neutral carrier control.

## All-Pair Definition Dose Response

Combined across both seeds, `N = 62` pair rows per cell.

| Readout | Injection -> readout | Alpha | Specific passes | Pass rate | Mean target delta | Median target delta | Mean advantage | Median advantage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| centroid | 4 -> 6 | 0.75 | 38/62 | 61.3% | 0.239 | 0.256 | 0.092 | 0.107 |
| centroid | 4 -> 6 | 1.00 | 38/62 | 61.3% | 0.312 | 0.319 | 0.117 | 0.148 |
| centroid | 5 -> 6 | 0.75 | 46/62 | 74.2% | 0.337 | 0.348 | 0.169 | 0.173 |
| centroid | 5 -> 6 | 1.00 | 46/62 | 74.2% | 0.411 | 0.430 | 0.192 | 0.192 |
| centroid | 6 -> 6 | 0.75 | 52/62 | 83.9% | 0.424 | 0.443 | 0.231 | 0.210 |
| centroid | 6 -> 6 | 1.00 | 54/62 | 87.1% | 0.494 | 0.501 | 0.246 | 0.217 |
| ridge | 4 -> 6 | 0.75 | 42/62 | 67.7% | 0.148 | 0.157 | 0.065 | 0.073 |
| ridge | 4 -> 6 | 1.00 | 43/62 | 69.4% | 0.192 | 0.202 | 0.082 | 0.087 |
| ridge | 5 -> 6 | 0.75 | 49/62 | 79.0% | 0.211 | 0.233 | 0.118 | 0.119 |
| ridge | 5 -> 6 | 1.00 | 53/62 | 85.5% | 0.259 | 0.277 | 0.134 | 0.138 |
| ridge | 6 -> 6 | 0.75 | 56/62 | 90.3% | 0.264 | 0.281 | 0.156 | 0.152 |
| ridge | 6 -> 6 | 1.00 | 57/62 | 91.9% | 0.308 | 0.310 | 0.166 | 0.156 |

The ridge readout preserves the late-layer pattern. Its raw margins are smaller than centroid margins, but its specificity pass rates are at least as strong in every definition cell. The strongest trained-readout cell is same-layer `6 -> 6`, alpha `1.0`, with `57/62` passes and mean target-over-control advantage `0.166`.

## Neutral Carrier Comparison

Combined across both seeds, `N = 62` pair rows per cell.

| Readout | Injection -> readout | Alpha | Specific passes | Pass rate | Mean target delta | Median target delta | Mean advantage | Median advantage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| centroid | 4 -> 6 | 0.75 | 6/62 | 9.7% | 0.137 | 0.136 | -0.002 | -0.002 |
| centroid | 4 -> 6 | 1.00 | 6/62 | 9.7% | 0.132 | 0.116 | 0.002 | 0.003 |
| centroid | 5 -> 6 | 0.75 | 8/62 | 12.9% | 0.142 | 0.147 | 0.001 | 0.001 |
| centroid | 5 -> 6 | 1.00 | 7/62 | 11.3% | 0.151 | 0.140 | 0.005 | 0.006 |
| centroid | 6 -> 6 | 0.75 | 13/62 | 21.0% | 0.147 | 0.151 | 0.020 | 0.011 |
| centroid | 6 -> 6 | 1.00 | 13/62 | 21.0% | 0.192 | 0.199 | 0.020 | 0.016 |
| ridge | 4 -> 6 | 0.75 | 4/62 | 6.5% | 0.086 | 0.085 | -0.001 | -0.001 |
| ridge | 4 -> 6 | 1.00 | 8/62 | 12.9% | 0.084 | 0.088 | 0.001 | 0.003 |
| ridge | 5 -> 6 | 0.75 | 6/62 | 9.7% | 0.090 | 0.084 | 0.001 | 0.001 |
| ridge | 5 -> 6 | 1.00 | 7/62 | 11.3% | 0.096 | 0.101 | 0.004 | 0.005 |
| ridge | 6 -> 6 | 0.75 | 15/62 | 24.2% | 0.093 | 0.097 | 0.013 | 0.006 |
| ridge | 6 -> 6 | 1.00 | 17/62 | 27.4% | 0.122 | 0.127 | 0.013 | 0.010 |

Neutral carriers still nudge margins, especially same-layer, but they do not match definition patches on specificity or target-over-control advantage. Under ridge scoring at `6 -> 6`, alpha `1.0`, definition reaches `57/62` passes and mean advantage `0.166`; neutral reaches `17/62` and mean advantage `0.013`.

## Focus-vs-Baseline Check

The trained readout does not revive an attractor-specific claim. Broad baseline rows remain strong, and focus/source-family rows are not exceptional as a group.

| Seed | Kind | Readout | Count | Specific passes | Pass rate | Mean target delta | Mean advantage | Mean advantage percentile | Max advantage percentile |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 20260608 | baseline_distribution | centroid | 144 | 89/144 | 61.8% | 0.338 | 0.123 | n/a | n/a |
| 20260608 | positive | centroid | 6 | 6/6 | 100.0% | 0.247 | 0.247 | 66.0% | 67.4% |
| 20260608 | source_family | centroid | 24 | 24/24 | 100.0% | 0.456 | 0.234 | 64.6% | 94.4% |
| 20260608 | generic_control | centroid | 12 | 12/12 | 100.0% | 0.426 | 0.220 | 63.2% | 79.2% |
| 20260608 | baseline_distribution | ridge | 144 | 99/144 | 68.8% | 0.217 | 0.093 | n/a | n/a |
| 20260608 | positive | ridge | 6 | 6/6 | 100.0% | 0.155 | 0.155 | 64.6% | 67.4% |
| 20260608 | source_family | ridge | 24 | 24/24 | 100.0% | 0.280 | 0.147 | 62.5% | 93.8% |
| 20260608 | generic_control | ridge | 12 | 12/12 | 100.0% | 0.262 | 0.136 | 58.3% | 75.0% |
| 20260609 | baseline_distribution | centroid | 144 | 101/144 | 70.1% | 0.373 | 0.196 | n/a | n/a |
| 20260609 | positive | centroid | 6 | 6/6 | 100.0% | 0.247 | 0.247 | 62.5% | 62.5% |
| 20260609 | source_family | centroid | 24 | 24/24 | 100.0% | 0.456 | 0.234 | 60.4% | 90.3% |
| 20260609 | generic_control | centroid | 12 | 12/12 | 100.0% | 0.426 | 0.176 | 51.4% | 65.3% |
| 20260609 | baseline_distribution | ridge | 144 | 117/144 | 81.2% | 0.228 | 0.132 | n/a | n/a |
| 20260609 | positive | ridge | 6 | 6/6 | 100.0% | 0.155 | 0.155 | 61.1% | 63.9% |
| 20260609 | source_family | ridge | 24 | 24/24 | 100.0% | 0.280 | 0.147 | 58.3% | 92.4% |
| 20260609 | generic_control | ridge | 12 | 12/12 | 100.0% | 0.262 | 0.145 | 58.3% | 69.4% |

The baseline distribution itself becomes stronger under the ridge readout, with definition pass rates of `68.8%` and `81.2%` across the two seeds. That makes the trained-readout result stronger as a transport verifier and weaker as an attractor-family specificity claim.

## Interpretation

Accepted result:

```text
The hook-output label-free transfer ridge is not a nearest-centroid artifact.
A trained multiclass ridge readout preserves the late-layer definition-transfer
pattern across two seeds, with exact definition/source-noop identity and a
definition-vs-neutral specificity gap.
```

Rejected or still demoted claim:

```text
This still does not establish an attractor-specific basin.
The same trained-readout ridge appears across broad baseline rows and generic
controls, so the effect is better described as broad definition-derived
concept-state transport.
```

Best current framing:

```text
Late Pythia-70M hook-output states support a general concept-state transport
operation that remains visible under both centroid and trained linear readouts.
The next hard question is whether this transported state changes behavior, or
only moves representations across readout surfaces.
```

## Limitations

- One model checkpoint.
- One readout layer.
- Ridge readout is linear and trained on the same concept inventory.
- Same-layer `6 -> 6` may partly reflect direct replacement of the readout layer's own representation.
- The behavior-level gate is still missing.

## Next Move

Move from readout-space verification to behavior-level verification:

- Add a multiple-choice or logprob behavior task using label-free concept prompts.
- Compare behavior deltas against centroid and ridge readout deltas at the same injection layers.
- Replicate the trained-readout ridge on a second checkpoint or open model.

## Discovery-Regime Audit

Question: does the hook-output label-free transfer ridge survive a trained readout?

Current regime:

- Artifact types: label-free patch payloads, hook-output patch-vector manifests, centroid/ridge readout summaries, source-noop identity tables, baseline percentile summaries.
- Operations: hook-output activation capture, held-out centroid readout scoring, one-vs-all multiclass ridge fitting, final-token activation patching at transformer-block outputs.
- Gates/verifiers: exact definition/source-noop identity, definition-vs-neutral stress, centroid-vs-ridge readout agreement, two-seed replication, baseline percentile comparison.
- Known limitations: one checkpoint, one readout layer, no behavior-level task yet.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: the run adds trained readout mode as a first-class verifier dimension and tests whether the existing ridge survives a different scoring surface.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed*.json`.
- Positive targets: focus rows plus 24 sampled baseline pairs per seed.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, broad baseline rows.
- Stress tests: readout modes `centroid,ridge`; injection layers `4,5,6`; alphas `0.75,1.0`; two seeds.

Gate:

- Acceptance rule: accept readout-mode robustness only if ridge readout preserves the definition transfer ridge, definition/source-noop is exact, and neutral carriers do not match definition specificity.
- Withheld/rejected rule: reject attractor-specific revival unless focus/source-family rows are clearly exceptional against baseline and generic controls.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/modal_label_free_readout_basin.py`; `experiments/activation_geometry/label_free_readout_basin.py`; `scripts/summarize_label_free_dose_response.py`.
- Rejected or withheld artifacts: attractor-specific revival remains rejected.
- Key metrics: definition/source-noop max delta `0.0`; ridge definition pass rates reach `42/62` at `4 -> 6`, `53/62` at `5 -> 6`, and `57/62` at `6 -> 6`; ridge neutral at `6 -> 6`, alpha `1.0` reaches `17/62`.
- Variance or ablation: both seeds show the same layer ordering; ridge margins shrink relative to centroid while pass rates stay strong or improve.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic rather than attractor-specific.
- New content outside old regime: the transfer ridge survives a trained linear readout and is not merely nearest-centroid geometry.
- Retractions or supersessions: supersede "centroid readout may be producing the ridge" with "centroid is not necessary for the ridge, though readout-space movement still needs behavior-level validation."

Next move: add a behavior-level gate that tests whether readout-space transport predicts answer/logprob changes.
