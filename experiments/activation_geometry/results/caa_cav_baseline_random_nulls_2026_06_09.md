# CAA/CAV Baseline Random Nulls - 2026-06-09

## Question

Random relation nulls showed that target-gradient behavior directions are not
semantically specific under the full-label logprob gate. This run asks whether
simple CAA/CAV-style activation-difference directions avoid that failure.

```text
If the failure is specific to target-gradient construction, activation
difference baselines should move held-out positive aliases while leaving random
relation null controls mostly unmoved.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_caa_baseline_random_nulls_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_caa_baseline_random_nulls_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Pair set: `expanded_random_nulls`, with 7 positives and 10 random relation null controls
- Objective labels: `alias_0+alias_1`
- Eval labels: held-out `alias_2` and `canonical`
- Prompt frames: `source_passage`, `latent_choice`
- CAA construction frame: `source_passage`
- Layers: primary `5`, backup `6`, control `1`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scale: `1.0`
- Directions: target-learned, `caa_target_contrast`,
  `caa_target_minus_source`, `caa_target_minus_distractor`, random same-norm
- Seed: `20260609`

The CAA-style modes use mean hidden-state activation differences:

```text
caa_target_contrast = target_mean - 0.5 * (source_mean + distractor_mean)
caa_target_minus_source = target_mean - source_mean
caa_target_minus_distractor = target_mean - distractor_mean
```

All CAA vectors are norm-matched to the learned target-gradient vector for the
same pair, layer, and objective regime before evaluation.

## Scale 1 Primary-Layer Results

Specificity is:

```text
specificity_score = heldout_positive_mean_delta - independent_control_mean_delta
```

CAA-style baselines are active and sometimes improve mean specificity relative
to the target-gradient direction, especially in the `source_passage` held-out
alias gate. They do not pass the semantic-specificity gate. Controls still pass
broadly: at best `7/10` random null controls pass in `source_passage`, and all
`10/10` random null controls pass for every CAA mode in `latent_choice`.

| Prompt | Eval | Direction | Positive passes | Positive mean | Control passes | Control mean | Specificity |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| source_passage | alias_2 | caa_target_contrast | 7/7 | 0.144 | 9/10 | 0.098 | 0.046 |
| source_passage | alias_2 | caa_target_minus_distractor | 5/7 | 0.090 | 9/10 | 0.072 | 0.018 |
| source_passage | alias_2 | caa_target_minus_source | 7/7 | 0.160 | 7/10 | 0.095 | 0.066 |
| source_passage | alias_2 | random_same_norm | 2/7 | -0.013 | 7/10 | 0.031 | -0.044 |
| source_passage | alias_2 | target_learned | 6/7 | 0.326 | 10/10 | 0.427 | -0.101 |
| source_passage | canonical | caa_target_contrast | 7/7 | 0.790 | 10/10 | 0.938 | -0.148 |
| source_passage | canonical | caa_target_minus_distractor | 7/7 | 0.728 | 10/10 | 0.904 | -0.176 |
| source_passage | canonical | caa_target_minus_source | 6/7 | 0.605 | 10/10 | 0.699 | -0.094 |
| source_passage | canonical | random_same_norm | 1/7 | -0.039 | 5/10 | -0.019 | -0.021 |
| source_passage | canonical | target_learned | 6/7 | 0.342 | 10/10 | 0.516 | -0.174 |
| latent_choice | alias_2 | caa_target_contrast | 7/7 | 0.130 | 10/10 | 0.115 | 0.015 |
| latent_choice | alias_2 | caa_target_minus_distractor | 6/7 | 0.076 | 10/10 | 0.090 | -0.014 |
| latent_choice | alias_2 | caa_target_minus_source | 7/7 | 0.149 | 10/10 | 0.106 | 0.043 |
| latent_choice | alias_2 | random_same_norm | 4/7 | 0.014 | 7/10 | 0.043 | -0.029 |
| latent_choice | alias_2 | target_learned | 6/7 | 0.324 | 10/10 | 0.461 | -0.137 |
| latent_choice | canonical | caa_target_contrast | 7/7 | 0.722 | 10/10 | 1.048 | -0.326 |
| latent_choice | canonical | caa_target_minus_distractor | 7/7 | 0.684 | 10/10 | 0.976 | -0.292 |
| latent_choice | canonical | caa_target_minus_source | 6/7 | 0.535 | 10/10 | 0.819 | -0.284 |
| latent_choice | canonical | random_same_norm | 3/7 | -0.009 | 4/10 | -0.025 | 0.016 |
| latent_choice | canonical | target_learned | 6/7 | 0.382 | 10/10 | 0.585 | -0.203 |

## Diagnosis

Accepted:

```text
The CAA/CAV-style activation-difference baseline is implemented and active under
the same held-out alias/random-null verifier as the target-gradient directions.
```

Accepted:

```text
CAA-style directions reduce some random-null mean movement relative to raw
target-gradient directions, especially in source-passage held-out alias scoring.
```

Rejected:

```text
CAA/CAV-style activation-difference directions rescue semantic specificity under
the current full-label logprob verifier.
```

Withheld:

```text
Any claim that positive held-out alias movement alone is enough evidence for
semantic concept transport.
```

Best current interpretation:

```text
The failure is not just target-gradient overfitting. Activation-difference
baselines also transport broad answer-label evidence to random relation nulls.
The current logprob gate is useful as a falsifier, but a paper-level positive
claim now needs a non-logprob generation/readout verifier or a stronger
behavior-aligned objective that can beat CAA and random-null controls.
```

## Next Move

- Build a non-logprob generation or learned behavior-readout gate for the same
  positive and random-null pairs.
- Add bootstrap confidence intervals over pairs and random-null draws only after
  a verifier separates positives from nulls.
- Treat larger-model replication as premature for this exact full-label logprob
  objective.

## Discovery-Regime Audit

Question: do CAA/CAV-style activation-difference directions avoid the random
relation null failure that invalidated target-gradient behavior directions?

Current regime:

- Artifact types: alias-indexed behavior-direction manifests, activation-mean
  CAA/CAV direction vectors, random-relation null pair sets, specificity tables,
  result reports.
- Operations: source-passage activation extraction, mean activation
  differencing, norm matching to target-gradient directions, held-out alias
  scoring.
- Gates/verifiers: positives must beat random relation nulls under the same
  score surface; controls should not broadly pass; canonical controls should not
  be stronger than positives.
- Known limitations: one model, one seed, CAA vectors use simple mean
  differences, no generation/readout scoring yet.

Action class:

- Retrieval/search/discovery: baseline hardening with a rejected rescue.
- Why: this adds a CAA/CAV-style baseline operation and tests whether the
  failure was construction-specific rather than verifier-specific.

Experiment:

- Manifest/report paths: this report; local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_caa_baseline_random_nulls_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: ten seeded random relation null controls.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`;
  canonical labels; random same-norm baseline.

Gate:

- Acceptance rule: continue toward paper-level semantic specificity only if a
  CAA/CAV baseline keeps high held-out positive transfer while suppressing
  random-null controls enough to make specificity clearly positive.
- Withheld/rejected rule: reject the CAA/CAV rescue if random null controls
  still broadly pass or canonical specificity is negative.

Results:

- Accepted artifacts: CAA/CAV direction modes and this report.
- Rejected or withheld artifacts: CAA/CAV as a semantically specific mechanism
  under the current full-label logprob verifier.
- Key metrics: best source-passage held-out alias CAA row is
  `caa_target_minus_source`, with `7/7` positives, `7/10` controls, and
  specificity `0.066`; best latent held-out alias CAA row is
  `caa_target_minus_source`, with `7/7` positives, `10/10` controls, and
  specificity `0.043`.
- Variance or ablation: source and latent prompt frames agree that CAA moves
  positives but does not suppress random nulls; canonical specificity is
  negative for all CAA modes.

Residual content:

- Explained by old regime: both gradient and CAA directions can move held-out
  target labels.
- New content outside old regime: a standard activation-difference baseline also
  fails the random-null specificity gate, strengthening the case that the
  verifier/objective, not only the direction-construction method, is the current
  bottleneck.
- Retractions or supersessions: supersede "CAA may rescue this verifier" with
  "CAA is a useful baseline but fails the same independent-control gate."

Next move: create a non-logprob generation or learned behavior-readout gate for
semantic specificity.
