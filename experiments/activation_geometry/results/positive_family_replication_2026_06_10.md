# Positive-Family Binary Direction Replication

Date: 2026-06-10

## Question

Does the positive-family strict-binary frontier survive the smallest alias and
train-variant perturbations?

The prior frontier was:

- model: `EleutherAI/pythia-70m-deduped`
- layer: `3`
- pair set: `layer3_strict_pocket_stratified_controls`
- objective labels: `alias_0`
- evaluation labels: `alias_2`
- train variant: `0`
- scale: `1.0`
- result: `1/2` strict positives and `0/12` stratified controls.

This report tests whether that frontier is stable enough to justify moving to a
second model/layer.

## Gate

Acceptance rule:

- preserve at least `1/2` strict positives;
- keep `0/12` strict stratified controls;
- keep `random_same_norm` at `0/2` positives and `0/12` controls.

Rejection rule:

- `0/2` positives means the frontier is alias/train fragile;
- any revived structured control means the frontier is not semantically
  specific enough to promote.

## Objective-Alias Replication

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-positive-family-opt8-alias1-strata experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_positive_family_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_alias1_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_alias1_seed20260610.json`

Result:

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |
| `target_binary_positive_family_opt_8` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |

Positive rows:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | no | `2.613` | `-0.000` | `-0.297` | `0.449` | `-0.442` |
| `fixed_point->prototype` | no | `2.041` | `0.274` | `0.119` | `-0.211` | `-1.746` |

Optimization summary for `target_binary_positive_family_opt_8`:

- target prompts: `2`
- control prompts: `22`
- positive pairs: `2`
- control pairs: `12`
- target margin mean/min during optimization: `0.436` / `0.408`
- control margin mean/max during optimization: `-0.355` / `0.174`
- post-rescale norm: `2.573`

Interpretation:

Changing only the objective label regime from `alias_0` to `alias_1` removes
the surviving positive. The controls remain clean, but that is not evidence of
semantic specificity because the intervention no longer clears a positive row.

## Train-Variant Replication

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-positive-family-opt8-trainv1-strata experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_positive_family_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_trainv1_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_trainv1_seed20260610.json`

Result:

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |
| `target_binary_positive_family_opt_8` | `1/2` | `1/12` | `0/3` | `0/3` | `1/3` | `0/3` |

Strict pass rows:

| Kind | Class | Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| positive | - | `attractor->attractor_network` | `1.987` | `0.237` | `0.039` | `0.312` | `-0.529` |
| control | `source_sharing` | `attractor->semantic_distance` | `1.977` | `0.227` | `0.017` | `0.352` | `-0.376` |

Positive rows:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | yes | `1.987` | `0.237` | `0.039` | `0.312` | `-0.529` |
| `fixed_point->prototype` | no | `0.990` | `-0.446` | `-0.573` | `-1.198` | `-2.579` |

Optimization summary for `target_binary_positive_family_opt_8`:

- target prompts: `2`
- control prompts: `22`
- positive pairs: `2`
- control pairs: `12`
- target margin mean/min during optimization: `0.812` / `0.302`
- control margin mean/max during optimization: `-0.400` / `0.228`
- post-rescale norm: `2.219`

Interpretation:

The surviving positive reappears under train variant `1`, but the same movement
also revives the source-sharing control `attractor->semantic_distance`. This is
exactly the structured-overlap failure mode the stratified gate was designed to
catch.

## Conclusion

The positive-family frontier fails the pre-registered robustness gate.

The result is scientifically useful, but negative:

- `alias_1` objective training gives `0/2` positives and `0/12` controls;
- train variant `1` gives `1/2` positives but leaks `1/12` controls;
- `fixed_point->prototype` still fails in both perturbations;
- `random_same_norm` remains clean in both runs.

This rules out promoting the current positive-family single-vector operation as
a paper nucleus. It should be treated as a diagnostic frontier showing that the
strict binary gate can expose a narrow, alias-sensitive `attractor` pocket.

Next move: keep the stratified strict verifier, but pivot intervention class.
The most valuable next experiment is pair-conditioned nonlinear or
readout-guided steering, where the intervention is allowed to depend on the
source/target pair while being penalized against the same structured controls.
