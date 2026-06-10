# Binary Yes-Bias Controls - 2026-06-09

## Question

The direct binary-relation gate produced the first nonzero behavior movement:
`target_learned` passed `4/7` positives and `3/10` random relation nulls. This
diagnostic asks whether that movement is relation-specific or a broad Yes-bias
direction.

```text
If the binary relation signal is semantic, target candidates should move more
than blank, generic, source, distractor, shuffled-target, and always-false
carrier controls.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payload:

```text
artifacts/activation_geometry/modal_pythia_70m_binary_yes_bias_controls_seed20260609.json
```

The run repeats the binary-relation behavior gate and adds control scores to
each baseline and steered row:

- `blank`: empty candidate
- `generic`: `a related concept`
- `source`: held-out source label
- `distractor`: held-out distractor label
- `shuffled_target`: target label from the next pair in the deterministic pair
  list
- `always_true`: identity carrier over the target candidate
- `always_false`: false identity carrier over the target candidate

Each control is scored by its `Yes - No` continuation margin.

## Main Gate

The main binary pass table is unchanged from the first binary-relation run.

| Direction | Target-positive passes | Random-null passes | Mean positive delta | Mean control delta | Specificity |
| --- | ---: | ---: | ---: | ---: | ---: |
| `target_learned` | 4/7 | 3/10 | 0.075 | -0.043 | 0.118 |
| `caa_target_minus_source` | 0/7 | 0/10 | 0.007 | 0.016 | -0.009 |
| `random_same_norm` | 0/7 | 0/10 | 0.023 | 0.001 | 0.023 |

## Yes-Bias Diagnostic

The target-learned direction increases Yes-No margins for every candidate type
and carrier control. All steered means are positive.

| Slice | Candidate/control | Mean delta | Steered mean | Steered positive count |
| --- | --- | ---: | ---: | ---: |
| positives | target | 4.508 | 2.206 | 7/7 |
| positives | source | 4.436 | 2.424 | 7/7 |
| positives | distractor | 4.430 | 2.073 | 7/7 |
| positives | blank | 4.498 | 2.620 | 7/7 |
| positives | generic | 4.410 | 2.204 | 7/7 |
| positives | shuffled target | 4.472 | 2.183 | 7/7 |
| positives | always false | 4.130 | 2.399 | 7/7 |
| positives | always true | 4.298 | 2.782 | 7/7 |
| random nulls | target | 4.357 | 1.862 | 10/10 |
| random nulls | source | 4.364 | 1.792 | 10/10 |
| random nulls | distractor | 4.435 | 1.582 | 10/10 |
| random nulls | blank | 4.336 | 2.057 | 10/10 |
| random nulls | generic | 4.191 | 1.507 | 10/10 |
| random nulls | shuffled target | 4.287 | 1.758 | 10/10 |
| random nulls | always false | 3.804 | 2.330 | 10/10 |
| random nulls | always true | 3.934 | 2.688 | 10/10 |

The passing rows make the confound visible. For example,
`attractor->attractor_network` steers the target candidate to `2.896`, but also
steers the blank candidate to `2.271`, source to `2.210`, distractor to `2.004`,
and the always-false carrier to `2.875`.

## Diagnosis

Accepted:

```text
The binary-relation surface is intervention-sensitive and exposes a real
behavioral degree of freedom in Pythia-70M.
```

Rejected:

```text
The current target-learned binary direction is semantically relation-specific.
```

Withheld:

```text
Any paper claim that the 4/7 binary positive passes show semantic bridge
steering. They are better explained as broad Yes-bias or candidate affirmation.
```

Best current interpretation:

```text
The binary surface is valuable because it finally makes behavior move, but the
learned direction mostly controls an answer-polarity axis. It increases Yes
margins for target, source, distractor, blank, generic, shuffled, and
always-false prompts alike.
```

## Next Move

- Learn a contrastive binary direction that maximizes target Yes while
  explicitly penalizing blank, generic, source, distractor, shuffled-target, and
  always-false Yes margins.
- Add the same controls to the robust-pass rule before treating any binary
  relation result as semantic specificity.
- Replicate only after a contrastive direction keeps target movement while
  suppressing the Yes-bias controls.

## Discovery-Regime Audit

Question: is the nonzero binary-relation behavior signal relation-specific, or
is it broad Yes-bias?

Current regime:

- Artifact types: binary-relation payloads, candidate-control margins,
  carrier-control margins, random-null specificity reports.
- Operations: held-out binary relation scoring, extra control-candidate scoring,
  always-true/false carrier scoring, target/source/distractor role-margin
  comparison.
- Gates/verifiers: target movement must exceed blank/generic/shuffled/source/
  distractor/false-carrier movement before semantic specificity can be claimed.
- Known limitations: one model, one seed, one layer, one scale; controls are
  diagnostic only and not yet part of robust-pass aggregation.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds the missing control artifact type needed to distinguish
  relation behavior from answer-polarity behavior.

Experiment:

- Manifest/report paths: this report; local ignored payload
  `artifacts/activation_geometry/modal_pythia_70m_binary_yes_bias_controls_seed20260609.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten random relation null pairs plus candidate/carrier
  yes-bias controls.
- Stress tests: blank, generic, source, distractor, shuffled-target,
  always-true, and always-false controls under `target_learned`.

Gate:

- Acceptance rule: semantic-specific binary steering requires target movement
  larger than yes-bias controls, with controls not ending broadly positive.
- Withheld/rejected rule: reject the candidate mechanism if yes-bias controls
  move with the target.

Results:

- Accepted artifacts: yes-bias control fields inside binary-relation payloads.
- Rejected or withheld artifacts: the current `target_learned` binary direction
  as relation-specific steering.
- Key metrics: all target/source/distractor/control/carrier Yes-No margins end
  positive in `17/17` target-learned rows.
- Variance or ablation: positives and random nulls show the same broad pattern.

Residual content:

- Explained by old regime: behavior can move on a direct binary surface.
- New content outside old regime: the movement is mainly answer-polarity
  control, not relation-specific transport.
- Retractions or supersessions: supersede "binary relation gives a promising
  semantic pocket" with "binary relation gives a useful behavior surface whose
  first direction is dominated by Yes-bias."

Next move: build contrastive binary directions and make yes-bias controls part
of the acceptance rule.
