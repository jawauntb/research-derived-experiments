# Label-Free Transfer Dose Response - 2026-06-08

## Question

Is broad label-free target-state transfer just a late hidden-state overwrite, or can target definition states propagate from earlier layers into a downstream readout?

The broad baseline demoted the attractor-specific claim and promoted a broader mechanism: definition-derived concept states can move downstream hidden states toward target concepts under a label-free readout. This run tests whether that mechanism has a layer/alpha structure.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payload:

```text
artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_dose_response.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Injection layers: `2,3,4,5,6`
- Readout layer: `6`
- Patch alphas: `0.25,0.5,0.75,1.0`
- Pair set: `combined`
- Focus pairs: 7 previously tested rows
- Baseline pairs: 8 sampled ordered concept pairs, excluding the focus left-right pairs
- Patch text regimes: `definition`, `neutral`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Train variants: `0,1`
- Eval variant: `2`
- Seed: `20260608`

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 2,3,4,5,6 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alphas 0.25,0.5,0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_dose_response.json
```

Specificity gate:

- Target patch must increase target readout margin.
- Target class must be top-3 under the patched readout.
- Target patch must beat the best of distractor, random, and source-noop patch modes.

Sanity gate:

- Strict downstream cells (`injection_layer < readout_layer`) have max absolute `definition` source-noop aggregate delta `0.0`.
- Same-layer `6 -> 6` cells fail the source-noop gate, with max absolute `definition` source-noop aggregate delta `0.343`.
- Therefore, this report treats `6 -> 6` as a withheld hook/readout-surface diagnostic and interprets only strict downstream cells.

## All-Pair Definition Dose Response

Strict downstream cells only, `N = 15` pairs per cell.

| Injection -> readout | Alpha | Specific passes | Pass rate | Mean target delta | Mean advantage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2 -> 6 | 0.25 | 2/15 | 13.3% | 0.014 | -0.010 |
| 2 -> 6 | 0.50 | 2/15 | 13.3% | 0.042 | -0.017 |
| 2 -> 6 | 0.75 | 3/15 | 20.0% | 0.072 | -0.027 |
| 2 -> 6 | 1.00 | 3/15 | 20.0% | 0.087 | -0.038 |
| 3 -> 6 | 0.25 | 2/15 | 13.3% | 0.022 | 0.000 |
| 3 -> 6 | 0.50 | 2/15 | 13.3% | 0.061 | -0.000 |
| 3 -> 6 | 0.75 | 4/15 | 26.7% | 0.102 | -0.007 |
| 3 -> 6 | 1.00 | 6/15 | 40.0% | 0.133 | -0.008 |
| 4 -> 6 | 0.25 | 2/15 | 13.3% | 0.056 | 0.028 |
| 4 -> 6 | 0.50 | 7/15 | 46.7% | 0.145 | 0.067 |
| 4 -> 6 | 0.75 | 10/15 | 66.7% | 0.238 | 0.101 |
| 4 -> 6 | 1.00 | 10/15 | 66.7% | 0.306 | 0.118 |
| 5 -> 6 | 0.25 | 5/15 | 33.3% | 0.084 | 0.047 |
| 5 -> 6 | 0.50 | 9/15 | 60.0% | 0.206 | 0.110 |
| 5 -> 6 | 0.75 | 11/15 | 73.3% | 0.324 | 0.163 |
| 5 -> 6 | 1.00 | 11/15 | 73.3% | 0.394 | 0.183 |

## Neutral Carrier Comparison

Strict downstream cells only, `N = 15` pairs per cell.

| Injection -> readout | Alpha | Specific passes | Pass rate | Mean target delta | Mean advantage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2 -> 6 | 0.25 | 0/15 | 0.0% | 0.013 | -0.000 |
| 2 -> 6 | 0.50 | 0/15 | 0.0% | 0.068 | -0.019 |
| 2 -> 6 | 0.75 | 1/15 | 6.7% | 0.095 | -0.005 |
| 2 -> 6 | 1.00 | 2/15 | 13.3% | 0.096 | -0.009 |
| 3 -> 6 | 0.25 | 1/15 | 6.7% | 0.079 | -0.003 |
| 3 -> 6 | 0.50 | 0/15 | 0.0% | 0.085 | -0.012 |
| 3 -> 6 | 0.75 | 2/15 | 13.3% | 0.102 | -0.004 |
| 3 -> 6 | 1.00 | 2/15 | 13.3% | 0.101 | -0.006 |
| 4 -> 6 | 0.25 | 1/15 | 6.7% | 0.077 | -0.002 |
| 4 -> 6 | 0.50 | 0/15 | 0.0% | 0.092 | -0.008 |
| 4 -> 6 | 0.75 | 1/15 | 6.7% | 0.107 | -0.002 |
| 4 -> 6 | 1.00 | 2/15 | 13.3% | 0.105 | -0.006 |
| 5 -> 6 | 0.25 | 0/15 | 0.0% | 0.099 | -0.001 |
| 5 -> 6 | 0.50 | 0/15 | 0.0% | 0.109 | 0.000 |
| 5 -> 6 | 0.75 | 0/15 | 0.0% | 0.112 | -0.001 |
| 5 -> 6 | 1.00 | 1/15 | 6.7% | 0.127 | -0.000 |

Neutral carrier patches can increase raw target margin, but they do not usually beat controls. The specificity difference between definition and neutral carriers is strongest at layers `4` and `5`.

## Baseline-Only Definition Rows

Strict downstream cells only, `N = 8` sampled baseline rows per cell.

| Injection -> readout | Alpha | Specific passes | Pass rate | Mean target delta | Mean advantage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2 -> 6 | 0.25 | 0/8 | 0.0% | 0.003 | -0.022 |
| 2 -> 6 | 0.50 | 0/8 | 0.0% | 0.019 | -0.042 |
| 2 -> 6 | 0.75 | 1/8 | 12.5% | 0.049 | -0.063 |
| 2 -> 6 | 1.00 | 2/8 | 25.0% | 0.058 | -0.081 |
| 3 -> 6 | 0.25 | 0/8 | 0.0% | 0.014 | -0.006 |
| 3 -> 6 | 0.50 | 0/8 | 0.0% | 0.044 | -0.019 |
| 3 -> 6 | 0.75 | 2/8 | 25.0% | 0.080 | -0.046 |
| 3 -> 6 | 1.00 | 2/8 | 25.0% | 0.097 | -0.062 |
| 4 -> 6 | 0.25 | 1/8 | 12.5% | 0.051 | 0.024 |
| 4 -> 6 | 0.50 | 2/8 | 25.0% | 0.126 | 0.046 |
| 4 -> 6 | 0.75 | 3/8 | 37.5% | 0.201 | 0.055 |
| 4 -> 6 | 1.00 | 3/8 | 37.5% | 0.247 | 0.048 |
| 5 -> 6 | 0.25 | 2/8 | 25.0% | 0.066 | 0.032 |
| 5 -> 6 | 0.50 | 3/8 | 37.5% | 0.165 | 0.071 |
| 5 -> 6 | 0.75 | 4/8 | 50.0% | 0.264 | 0.108 |
| 5 -> 6 | 1.00 | 4/8 | 50.0% | 0.327 | 0.118 |

The broad-null rows show the same ridge, though with lower pass rates than the source-family focus rows.

## Interpretation

This is not just a final readout overwrite.

Definition-derived target-state transfer is weak and control-dominated when injected at layers `2` and `3`, but becomes specific and dose-responsive when injected at layers `4` and `5` and read out at layer `6`. At layer `4`, definition pass rate rises from `13.3%` at alpha `0.25` to `66.7%` at alpha `0.75` and `1.0`. At layer `5`, it rises from `33.3%` to `73.3%`.

The cleanest accepted result is:

```text
Pythia-70M-deduped has a downstream label-free target-state transfer ridge:
definition patches injected at layers 4-5 propagate to a layer-6 concept readout
with a dose-response in patch alpha.
```

The rejected or withheld claims are:

```text
The effect is not currently established as an attractor-specific basin.
The same-layer 6 -> 6 result is withheld because the source-noop sanity gate fails.
```

The layer structure is informative. Early-layer patches do move target margins upward, but controls move them too, so specificity does not emerge until mid/late layers. That suggests the mechanism is not merely "any perturbation increases target cosine"; it is a content-specific target-state insertion that becomes legible to the readout after the model has entered a later representational regime.

## Limitations

- One small causal LM checkpoint.
- One downstream readout layer.
- Only 8 broad-null baseline rows in the dose-response run.
- Same-layer hook/readout behavior needs its own diagnostic before interpreting `6 -> 6`.
- Nearest-centroid readout may overstate simple geometric movement compared with a trained classifier or behavior-level task.

## Next Move

Replicate the downstream ridge with a slightly broader but still focused grid:

- Injection layers `3,4,5`
- Readout layer `6`
- Patch alphas `0.5,0.75,1.0`
- Larger baseline sample, at least 24 rows
- Two seeds or a second checkpoint/model

In parallel, add a hook/readout-surface diagnostic for same-layer patching so we know whether `6 -> 6` failed because of hidden-state indexing, hook timing, or a genuine same-layer non-identity issue.

## Discovery-Regime Audit

Question: is broad label-free target-state transfer a late overwrite, or does it have a downstream layer/alpha regime?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, sampled baseline-pair rows, patch-alpha grid summaries.
- Operations: held-out centroid readout training, activation patching at selected injection layers, downstream layer-6 readout scoring, target-vs-control specificity aggregation.
- Gates/verifiers: strict downstream source-noop gate, target-over-control specificity gate, neutral-carrier stress test, alpha dose-response.
- Known limitations: one checkpoint, one readout layer, small baseline sample, unresolved same-layer hook/readout mismatch.

Action class:

- Retrieval/search/discovery: discovery-leaning verifier refinement.
- Why: the run adds alpha as a first-class grid dimension and exposes a missing artifact type for same-layer hook/readout-surface validity.

Experiment:

- Manifest/report paths: this report; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_dose_response.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: injection layers `2,3,4,5,6`; patch alphas `0.25,0.5,0.75,1.0`; strict downstream no-op filtering.

Gate:

- Acceptance rule: accept a downstream transfer ridge only if strict downstream source-noop is exact and definition patches show a layer/alpha increase that neutral carriers do not match.
- Withheld/rejected rule: withhold same-layer cells if source-noop is nonzero; reject a pure late-overwrite interpretation if earlier strict downstream layers show specific dose-responsive transfer.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: same-layer `6 -> 6` interpretation is withheld.
- Key metrics: strict downstream definition source-noop max delta `0.0`; layer `4 -> 6` definition pass rate reaches `10/15`; layer `5 -> 6` definition pass rate reaches `11/15`; neutral carrier pass rates remain at or below `2/15` in all strict downstream cells.
- Variance or ablation: baseline-only rows show the same layer/alpha ridge with lower pass rates; source-family rows are stronger but no longer the sole phenomenon.

Residual content:

- Explained by old regime: broad target-state transfer is a generic definition-derived phenomenon, not attractor-specific.
- New content outside old regime: the transfer has a mid/late downstream ridge and an alpha dose-response.
- Retractions or supersessions: supersede "maybe a late overwrite" with "strict downstream transfer is strongest from layers 4-5 into layer 6; same-layer cells are invalid under current hook/readout instrumentation."

Next move: replicate the downstream ridge with more baseline rows and a second seed/checkpoint, while separately diagnosing same-layer hook/readout validity.
