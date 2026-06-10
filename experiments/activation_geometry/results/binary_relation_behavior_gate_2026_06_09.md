# Binary-Relation Behavior Gate - 2026-06-09

## Question

After exact generation, learned generation-readout, and short-answer gates all
returned zero target behavior, this run asks whether a direct yes/no relation
classification interface can reveal behavior-level movement.

```text
If current directions are behavior-inactive only because generation is too hard,
then a direct relation classifier should show target-positive movement while
random relation nulls remain weaker.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payload:

```text
artifacts/activation_geometry/modal_pythia_70m_binary_relation_random_nulls_source_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Pair set: `expanded_random_nulls`, with 7 positives and 10 random relation
  null controls
- Direction-learning objective: binary relation yes/no margin over
  `alias_0+alias_1`
- Eval label regime metadata: held-out `alias_2`
- Prompt frame: `source_passage`
- Layer: primary `5`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scale: `1.0`
- Directions: `target_learned`, `caa_target_minus_source`, `random_same_norm`
- Seed: `20260609`

For each source passage and candidate concept, the prompt asks:

```text
Answer Yes only if the candidate names the closest related concept,
not merely the concept described in the passage.
```

Each source, target, and distractor candidate is scored by its `Yes - No`
continuation margin. A pass requires:

```text
target margin improves
target Yes-No margin increases
steered target Yes-No margin is positive
```

## Scale 1 Primary-Layer Results

This is the first nonzero behavior-level result in the recent verifier sequence,
but it is not yet semantically specific enough for a paper claim.

| Direction | Target-positive passes | Random-null passes | Mean positive delta | Mean control delta | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: |
| `target_learned` | 4/7 | 3/10 | 0.075 | -0.043 | 0.118 |
| `caa_target_minus_source` | 0/7 | 0/10 | 0.007 | 0.016 | -0.009 |
| `random_same_norm` | 0/7 | 0/10 | 0.023 | 0.001 | 0.023 |

Passing `target_learned` positives:

| Pair | Margin delta | Target Yes-No delta |
| --- | ---: | ---: |
| `attractor->attractor_network` | 0.280 | 4.833 |
| `fixed_point->prototype` | 0.230 | 4.367 |
| `phase_space->conceptual_space` | 0.159 | 4.521 |
| `validity_gate->weak_constraint` | 0.147 | 4.387 |

Passing `target_learned` random relation nulls:

| Pair | Margin delta | Target Yes-No delta |
| --- | ---: | ---: |
| `regime_transition->activation_vector` | 0.114 | 4.479 |
| `residual_content->self_boundary` | 0.144 | 4.398 |
| `valence->steering_vector` | 0.391 | 4.706 |

## Diagnosis

Accepted:

```text
The repo now has a direct binary-relation behavior surface that does not ask the
model to generate a concept label or choose among visible A/B/C labels.
```

Rejected:

```text
The current binary-relation result is a publishable semantic-specific steering
claim. Controls still pass, and the strongest control pass is the adversarial
`valence->steering_vector` pair.
```

Withheld:

```text
Any claim that target-learned binary directions are relation-specific rather
than broad candidate-affirmation directions.
```

Key issue:

```text
The binary target direction strongly increases the target Yes-No score on nearly
every row. Many rows fail only because source and distractor Yes-No margins also
increase. The learned target/source/distractor direction cosines are very high
across pairs, usually around 0.97 to 0.99, which suggests a broad Yes-bias or
candidate-affirmation axis rather than clean relation semantics.
```

Best current interpretation:

```text
Generation was too strict to show behavior, but the binary classifier reveals a
real intervention-sensitive behavior surface. The signal is not yet specific:
it appears to be a mixture of target-relation movement and broad Yes-bias.
```

## Next Move

- Add a yes-bias diagnostic: blank candidate, source candidate, distractor
  candidate, shuffled-pair candidate, and always-true/always-false carrier
  controls.
- Add relation-specific contrast directions that optimize target Yes while
  penalizing source/distractor/control Yes margins.
- Replicate this binary surface across seed, scale, and layer only after the
  yes-bias diagnostic separates relation movement from candidate affirmation.

## Discovery-Regime Audit

Question: can a direct yes/no relation-classification interface reveal behavior
that generation and short-answer gates miss?

Current regime:

- Artifact types: binary-relation payloads, random-null specificity reports,
  yes/no continuation-margin tables, direction-alignment diagnostics.
- Operations: train-alias binary yes/no gradient construction, held-out-alias
  binary relation scoring, random-null control comparison, CAA/random baselines.
- Gates/verifiers: positives must increase target Yes-No margin and become
  target-positive more often than random relation nulls.
- Known limitations: one small model, one seed, one layer, one scale, no
  explicit yes-bias controls yet.

Action class:

- Retrieval/search/discovery: verifier transition with residual content.
- Why: this adds a new behavior artifact class that is neither label generation
  nor visible option-token choice, and it produces the first nonzero behavior
  target passes after the stricter generation gates failed.

Experiment:

- Manifest/report paths: this report; local ignored payload
  `artifacts/activation_geometry/modal_pythia_70m_binary_relation_random_nulls_source_seed20260609.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: target-gradient, CAA, and random same-norm directions under
  held-out `alias_2`.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if
  positives beat random-null controls and the effect cannot be explained by a
  broad Yes-bias direction.
- Withheld/rejected rule: withhold semantic-specific claims if controls pass or
  target/source/distractor gradients are too collinear to separate.

Results:

- Accepted artifacts: `binary_relation` scoring surface and direct yes/no
  behavior gate.
- Rejected or withheld artifacts: binary relation result as a final semantic
  specificity claim.
- Key metrics: `target_learned` passes `4/7` positives and `3/10` random nulls;
  CAA and random pass `0/7` positives and `0/10` random nulls.
- Variance or ablation: role-gradient cosines are very high, suggesting broad
  candidate affirmation as a confound.

Residual content:

- Explained by old regime: full-label directions can move text-conditioned
  label surfaces.
- New content outside old regime: direct yes/no relation behavior is
  intervention-sensitive even when generation behavior is zero.
- Retractions or supersessions: supersede "all behavior gates are zero" with
  "generation behavior is zero, but direct binary relation behavior has a
  nonzero, confounded signal."

Next move: separate relation movement from yes-bias with explicit binary
controls before scaling.
