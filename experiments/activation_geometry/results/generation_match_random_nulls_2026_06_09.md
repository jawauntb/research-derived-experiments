# Generation-Match Random Null Gate - 2026-06-09

## Question

Full-label logprob gates showed broad target-label transport: positives moved,
but random relation nulls moved as much or more. This run asks whether a
non-logprob short-generation verifier preserves any semantically specific
behavior effect.

```text
If the intervention is semantically specific, steering should make the model
generate held-out target aliases for true bridge pairs more often than for
random relation null controls.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_generation_match_random_nulls_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_generation_match_random_nulls_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Pair set: `expanded_random_nulls`, with 7 positives and 10 random relation
  null controls
- Direction-learning objective: full-label `alias_0+alias_1`
- Generation-match eval labels: canonical label plus aliases, with held-out
  `alias_2` used by the manifest-level eval regime
- Prompt frames: `source_passage`, `latent_choice`
- Layer: primary `5`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scale: `1.0`
- Directions: `target_learned`, `caa_target_minus_source`, `random_same_norm`
- Seed: `20260609`

The directions are still learned with the differentiable full-label objective;
the verifier is different. For each prompt, the runner greedily generates 8 new
tokens with and without the steering vector and classifies the generated text by
exact normalized phrase matches against source, target, and distractor label
sets.

The gate was tightened after inspection: a generation row only counts as a
behavior pass when the steered continuation actually matches a target label.
Merely dropping the source label no longer counts, even if the target margin
improves.

## Scale 1 Primary-Layer Results

The strict target-match gate rejects all tested directions.

| Prompt | Direction | Target-positive passes | Random-null passes | Mean positive delta | Mean control delta | Specificity |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| source_passage | caa_target_minus_source | 0/7 | 0/10 | 0.143 | 0.000 | 0.143 |
| source_passage | random_same_norm | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| source_passage | target_learned | 0/7 | 0/10 | 0.143 | 0.050 | 0.093 |
| latent_choice | caa_target_minus_source | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| latent_choice | random_same_norm | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |
| latent_choice | target_learned | 0/7 | 0/10 | 0.000 | 0.000 | 0.000 |

The nonzero source-passage mean deltas are not target hits. They come from
source-label suppression in two positive rows:

| Prompt | Direction | Pair | Baseline roles/text | Steered roles/text |
| --- | --- | --- | --- | --- |
| source_passage | caa_target_minus_source | `phase_space->conceptual_space` | source: `phase space: a geometric state space where` | none: `the concept of the concept of the concept` |
| source_passage | caa_target_minus_source | `validity_gate->weak_constraint` | source: `validity gate: a criterion that blocks hypotheses` | none: `a criterion that blocks hypotheses whose apparent success` |
| source_passage | target_learned | `phase_space->conceptual_space` | source: `phase space: a geometric state space where` | none: `the concept of the concept of the concept` |
| source_passage | target_learned | `validity_gate->weak_constraint` | source: `validity gate: a criterion that blocks hypotheses` | none: `the criteria that blocks hypotheses whose apparent success` |

The latent-choice prompt is more uniform: both baseline and steered generations
mostly collapse to the same generic continuation, `the "normal" state. The
model`, and never match the target label set.

## Diagnosis

Accepted:

```text
The repo now has a non-logprob generation-match verifier with held-out aliases,
random relation nulls, CAA baseline support, and a regression test preventing
source-label suppression from being counted as target behavior.
```

Rejected:

```text
The current Pythia-70M target-gradient and CAA-style directions produce
paper-ready semantic steering behavior under short generation.
```

Withheld:

```text
Any claim that the full-label logprob specificity frontier has transported to
free/generated behavior.
```

Best current interpretation:

```text
The generation verifier is doing its job as a stricter behavioral falsifier. The
current interventions can move label scores, and sometimes suppress source
phrases, but they do not make Pythia-70M generate held-out target names for the
intended bridges. The next positive path should improve the behavior interface
or learn a behavior-readout verifier, not scale the same failed generation gate.
```

## Next Move

- Build a learned behavior-readout gate over generated continuations or hidden
  states, trained on aliases but evaluated on held-out aliases and random
  relation nulls.
- Try a constrained short-answer interface only if the output space still
  requires generation, and keep the stricter target-match requirement.
- Delay larger-model replication for the generation gate until a verifier shows
  nonzero target hits on the current model.

## Discovery-Regime Audit

Question: does a non-logprob short-generation verifier preserve semantically
specific behavior effects from alias-trained directions?

Current regime:

- Artifact types: alias-indexed behavior-direction manifests, CAA-style
  direction vectors, random-relation null pair sets, generated-text examples,
  target-match generation gates.
- Operations: full-label alias-gradient construction, CAA activation
  differencing, greedy continuation with steering hooks, normalized phrase
  matching over canonical and alias labels.
- Gates/verifiers: positives must generate target labels; random relation nulls
  must not; source-label suppression alone is not a pass.
- Known limitations: one small model, one seed, greedy 8-token continuation,
  exact phrase matcher rather than learned semantic evaluator.

Action class:

- Retrieval/search/discovery: verifier transition with a rejected candidate.
- Why: this adds a non-logprob behavior verifier and changes what counts as an
  accepted behavioral artifact.

Experiment:

- Manifest/report paths: this report; local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_generation_match_random_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: `source_passage` and `latent_choice`; target-gradient, CAA, and
  random same-norm directions.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  steered generations actually match held-out target labels for positives more
  often than for random-null controls.
- Withheld/rejected rule: withhold behavioral semantic steering if target hits
  are zero or if gains come from source/distractor suppression.

Results:

- Accepted artifacts: generation-match scoring surface; generation example
  renderer; target-match-only robust-pass gate.
- Rejected or withheld artifacts: current target-gradient and CAA directions as
  behavior-level semantic steering mechanisms.
- Key metrics: strict target-positive passes are `0/7` for target-gradient, CAA,
  and random directions in both prompt frames; random-null passes are `0/10`.
- Variance or ablation: source-passage has two source-suppression rows but no
  target hits; latent-choice has no target hits and generic repeated
  continuations.

Residual content:

- Explained by old regime: label-logprob movement does not imply generated
  target behavior.
- New content outside old regime: a stricter verifier reveals source-suppression
  artifacts that margin scoring alone would overcount.
- Retractions or supersessions: supersede "nonzero generation margin delta may
  indicate behavior" with "generation behavior requires an explicit steered
  target-label match under this verifier."

Next move: build a learned behavior-readout gate or redesign the short-answer
generation interface before running larger models.
