# Short-Answer Behavior Gate - 2026-06-09

## Question

The exact generation-match and learned generation-readout gates both rejected
the current behavior directions on open-ended continuations. This run asks
whether a more constrained short-answer interface reveals target behavior that
the earlier prompts failed to elicit.

```text
If the previous negative generation results were mostly an interface problem,
then forcing a short related-concept answer should produce nonzero target hits
or target-readout passes for positives without doing the same for random nulls.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_short_answer_generation_match_random_nulls_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_short_answer_generation_match_random_nulls_latent_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_short_answer_generation_readout_random_nulls_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_short_answer_generation_readout_random_nulls_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Pair set: `expanded_random_nulls`, with 7 positives and 10 random relation
  null controls
- Direction-learning objective: full-label `alias_0+alias_1`
- Eval label regime metadata: held-out `alias_2`
- Prompt frames: `source_short_answer`, `latent_short_answer`
- Layer: primary `5`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scale: `1.0`
- Directions: `target_learned`, `caa_target_minus_source`, `random_same_norm`
- Seed: `20260609`

The `source_short_answer` frame asks for one short related concept phrase after
a source passage. The `latent_short_answer` frame asks for one short concept
phrase without a source passage. Both are evaluated under two non-logprob
behavior surfaces:

- `generation_match`: the steered text must match a target canonical or alias
  phrase.
- `generation_readout`: the steered continuation must improve target margin,
  increase target score, and have `best_role == target` under the learned
  generation readout.

## Scale 1 Primary-Layer Results

The short-answer interface does not rescue behavior. All strict target-positive
passes remain zero.

| Surface | Prompt | Direction | Target-positive passes | Random-null passes | Mean positive delta | Mean control delta | Specificity |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| generation_match | source_short_answer | caa_target_minus_source | 0/7 | 0/10 | 0.000 | 0.050 | -0.050 |
| generation_match | source_short_answer | random_same_norm | 0/7 | 0/10 | 0.000 | 0.100 | -0.100 |
| generation_match | source_short_answer | target_learned | 0/7 | 0/10 | 0.071 | 0.150 | -0.079 |
| generation_match | latent_short_answer | caa_target_minus_source | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| generation_match | latent_short_answer | random_same_norm | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| generation_match | latent_short_answer | target_learned | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| generation_readout | source_short_answer | caa_target_minus_source | 0/7 | 0/10 | 0.000 | 0.003 | -0.003 |
| generation_readout | source_short_answer | random_same_norm | 0/7 | 0/10 | 0.000 | 0.002 | -0.002 |
| generation_readout | source_short_answer | target_learned | 0/7 | 0/10 | -0.001 | 0.005 | -0.006 |
| generation_readout | latent_short_answer | caa_target_minus_source | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| generation_readout | latent_short_answer | random_same_norm | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| generation_readout | latent_short_answer | target_learned | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |

## Examples

The source-conditioned prompt mostly repeats the source passage rather than
answering with the target concept:

| Surface | Direction | Pair | Baseline | Steered |
| --- | --- | --- | --- | --- |
| generation_match | target_learned | `autopoiesis->homeostasis` | `self-maintaining organization in which a` | `the system is a system of the same` |
| generation_readout | caa_target_minus_source | `attractor->attractor_network` | source `0.975`: `attractor: a persistent destination pattern in` | source `0.975`: `attractor: a persistent destination pattern in` |
| generation_readout | caa_target_minus_source | `basin_of_attraction->schema` | target `0.964`: `the attractor  Related concept:` | target `0.964`: `the attractor  Related concept:` |

The source-free latent prompt collapses to a generic continuation and steering
does not change it:

```text
The term "word" is
```

The learned readout sometimes assigns that generic string to source, target, or
distractor depending on the pair, but the steered text and best role do not move.

## Diagnosis

Accepted:

```text
The repo now has two constrained short-answer prompt frames wired into both
strict non-logprob behavior gates.
```

Rejected:

```text
The claim that current Pythia-70M target-gradient or CAA-style directions have
behavior-level target semantics that were hidden only by an overly open-ended
generation prompt.
```

Withheld:

```text
Any paper claim that the current intervention stack performs semantic steering
in generated behavior. The full-label logprob effects are still useful as a
diagnostic of label-surface transport, but they do not yet imply behavior.
```

Best current interpretation:

```text
The bottleneck is not just the evaluator and not just the wording of the
generation prompt. The current intervention changes label scores under
teacher-forced scoring surfaces, but it does not robustly cause the model to
emit or internally read out the target concept in short generated answers.
```

## Next Move

- Move to a direct behavior-classification/intervention task where the output
  behavior is explicitly separable from label completion.
- Treat larger-model repeats as premature until at least one non-logprob
  behavior task has nonzero target movement.
- Keep the short-answer prompt frames as regression tests for future
  intervention methods.

## Discovery-Regime Audit

Question: does a constrained short-answer interface reveal target behavior that
open-ended generation gates miss?

Current regime:

- Artifact types: generation-match payloads, generation-readout payloads,
  prompt-frame manifests, random-null specificity reports, generated-text
  examples.
- Operations: full-label alias-gradient construction, CAA activation
  differencing, short-answer greedy generation with steering hooks, exact target
  phrase matching, learned continuation readout scoring.
- Gates/verifiers: positives must produce target matches or target-readout
  classifications more often than random relation null controls.
- Known limitations: one small model, one seed, greedy short continuation, no
  larger-model replication because the small non-logprob gate is zero.

Action class:

- Retrieval/search/discovery: verifier search with a rejected interface.
- Why: this changes the prompting interface inside the existing non-logprob
  behavior-verifier schema and tests whether the negative result was caused by
  prompt openness.

Experiment:

- Manifest/report paths: this report; local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_short_answer_*_random_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: source-conditioned and source-free short-answer frames;
  exact-match and learned-readout behavior surfaces; target-gradient, CAA, and
  random same-norm directions.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  short-answer target behavior is nonzero for positives and exceeds random-null
  controls.
- Withheld/rejected rule: reject if target-positive passes are zero or if
  nonzero deltas come from source suppression, generic completions, or unchanged
  readout roles.

Results:

- Accepted artifacts: `source_short_answer` and `latent_short_answer` prompt
  frames.
- Rejected or withheld artifacts: the short-answer interface as a rescue for
  current target-gradient and CAA directions.
- Key metrics: all four surface/prompt combinations show `0/7` target-positive
  passes and `0/10` random-null passes for target-gradient, CAA, and random
  directions.
- Variance or ablation: source-conditioned prompts repeat source text; latent
  prompts collapse to generic text; learned readout agrees with exact matching.

Residual content:

- Explained by old regime: label-score steering does not automatically
  transport into generated target behavior.
- New content outside old regime: the short-answer interface is not sufficient
  to bridge teacher-forced label movement and behavior.
- Retractions or supersessions: supersede "short-answer prompting may recover
  the target behavior" with "current directions remain behavior-inactive under
  short-answer generation."

Next move: build a direct behavior-classification/intervention gate before
adding model scale.
