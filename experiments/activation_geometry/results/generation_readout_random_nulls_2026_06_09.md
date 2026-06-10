# Generation-Readout Random Null Gate - 2026-06-09

## Question

The strict generation-match gate rejected current behavior directions because
the model did not generate held-out target labels. This run asks whether a
learned hidden-state readout can recover semantic target behavior from the
generated continuations without using output-label logprobs.

```text
If generated continuations carry latent target semantics that exact label
matching misses, a readout trained on train aliases and train paraphrases should
score steered positive continuations as target more often than random nulls.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_generation_readout_random_nulls_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_generation_readout_random_nulls_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Pair set: `expanded_random_nulls`, with 7 positives and 10 random relation
  null controls
- Direction-learning objective: full-label `alias_0+alias_1`
- Readout training data: train aliases plus train paraphrases for source,
  target, and distractor roles
- Eval label regime metadata: held-out `alias_2`
- Prompt frames: `source_passage`, `latent_choice`
- Layer: primary `5`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scale: `1.0`
- Directions: `target_learned`, `caa_target_minus_source`, `random_same_norm`
- Seed: `20260609`

For each generated continuation, the runner embeds a readout prompt at layer 5,
then scores cosine similarity to source, target, and distractor centroids. The
strict pass rule requires all of the following:

```text
target margin improves
target score increases
steered readout best_role == target
```

This prevents source suppression or tiny target-score increases from counting as
behavior when the readout still classifies the continuation as source or
distractor.

## Scale 1 Primary-Layer Results

The strict readout gate rejects all tested directions.

| Prompt | Direction | Target-positive passes | Random-null passes | Mean positive delta | Mean control delta | Specificity |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| source_passage | caa_target_minus_source | 0/7 | 0/10 | 0.001 | 0.000 | 0.001 |
| source_passage | random_same_norm | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| source_passage | target_learned | 0/7 | 0/10 | -0.000 | 0.000 | -0.000 |
| latent_choice | caa_target_minus_source | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| latent_choice | random_same_norm | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| latent_choice | target_learned | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |

The one nonzero source-passage CAA margin row is not accepted because the
readout still calls the steered continuation `source`, not `target`:

| Prompt | Direction | Pair | Baseline best/text | Steered best/text |
| --- | --- | --- | --- | --- |
| source_passage | caa_target_minus_source | `validity_gate->weak_constraint` | source `0.966`: `validity gate: a criterion that blocks hypotheses` | source `0.965`: `a criterion that blocks hypotheses whose apparent success` |

The latent-choice prompt again collapses to generic text:

```text
the "normal" state. The model
```

The learned readout often assigns this generic string to different roles across
pairs, but steering does not change the generated text or move the best role.

## Diagnosis

Accepted:

```text
The repo now has a learned generation-readout scoring surface trained on train
aliases and train paraphrases, plus a strict robust-pass rule requiring the
steered readout's best role to be target.
```

Rejected:

```text
The current Pythia-70M target-gradient and CAA-style directions produce hidden
semantic target behavior in generated continuations under this readout.
```

Withheld:

```text
Any claim that exact generation-match was merely too brittle and that a learned
readout recovers robust target behavior.
```

Best current interpretation:

```text
The current intervention stack is label-score-active but behavior-inactive. Both
non-logprob evaluators agree: exact generated target names are absent, and a
train-alias hidden-state readout does not classify steered continuations as
target. The bottleneck is now the behavior interface or the intervention, not
just the evaluator.
```

## Next Move

- Try a constrained short-answer interface that forces the model to complete a
  concept phrase rather than open-ended 8-token continuation.
- If that still fails, move from steering generated text to a direct
  behavior-readout intervention/classifier task where the target behavior is
  explicitly separable.
- Treat larger-model replication as premature until at least one non-logprob
  gate has nonzero target behavior.

## Discovery-Regime Audit

Question: can a learned hidden-state readout recover semantic target behavior
from generated continuations where exact generation matching fails?

Current regime:

- Artifact types: generation-match payloads, generation-readout payloads,
  train-alias role centroids, generated-text example tables, random-null
  specificity reports.
- Operations: full-label alias-gradient construction, CAA activation
  differencing, greedy generation with steering hooks, hidden-state centroid
  scoring of generated continuations.
- Gates/verifiers: positives must improve target margin, increase target score,
  and be classified as target by the steered readout; controls must remain below
  positives.
- Known limitations: one small model, one seed, greedy generation, simple
  centroid readout rather than a cross-validated classifier.

Action class:

- Retrieval/search/discovery: verifier transition with a rejected candidate.
- Why: this adds a learned non-logprob behavior readout and tests whether exact
  label matching was too brittle.

Experiment:

- Manifest/report paths: this report; local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_generation_readout_random_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: `source_passage` and `latent_choice`; target-gradient, CAA, and
  random same-norm directions.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  steered positive continuations are read out as target more often than random
  null controls.
- Withheld/rejected rule: reject if target hits are zero or if gains occur while
  the readout's best role remains source/distractor.

Results:

- Accepted artifacts: generation-readout scoring surface and strict
  best-target readout gate.
- Rejected or withheld artifacts: current target-gradient and CAA directions as
  hidden-readout behavior mechanisms over generated continuations.
- Key metrics: strict positive passes are `0/7` in both prompt frames for all
  tested directions; random-null passes are `0/10`.
- Variance or ablation: source-passage has one tiny CAA target-score increase,
  but the best role remains source; latent-choice is fully unchanged.

Residual content:

- Explained by old regime: label-score movement can fail to transport into
  generated behavior.
- New content outside old regime: exact-match and learned-readout non-logprob
  gates agree on the negative result.
- Retractions or supersessions: supersede "a learned readout may recover
  hidden target behavior from generated text" with "this readout does not
  recover target behavior from the current generations."

Next move: redesign the behavior interface before scaling models.
