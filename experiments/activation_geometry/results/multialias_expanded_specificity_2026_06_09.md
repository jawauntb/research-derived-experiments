# Multi-Alias Expanded Specificity Gate - 2026-06-09

## Question

The previous held-out alias gate showed that single-alias constrained behavior
directions were not label-invariant. This run asks whether two changes repair
that failure:

```text
Train the direction objective jointly on alias_0 and alias_1, then evaluate on
held-out alias_2 across an expanded positive/control pair set.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_multialias_expanded_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_multialias_expanded_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Pair set: `expanded`, with 7 positives and 5 controls
- Objective labels: `alias_0+alias_1`
- Eval labels: `alias_0`, held-out `alias_2`, `canonical`
- Prompt frames: `source_passage`, `latent_choice`
- Layers: primary `5`, backup `6`, control `1`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scales: `0.5,1.0,2.0`
- Directions: raw target, residual-all, multi-control penalties, random same-norm
- Seed: `20260609`

This branch adds three verifier upgrades:

- A grouped objective syntax such as `alias_0+alias_1`, which averages gradients
  over multiple label surfaces before constructing the behavior direction.
- A third alias per concept, allowing a train-on-two / test-on-one alias split.
- An expanded behavior pair set with seven positives and five controls.

## Scale 1 Primary-Layer Results

Specificity is defined in `docs/semantic_specificity.md` as:

```text
specificity_score = heldout_positive_mean_delta - independent_control_mean_delta
```

The key result is that multi-alias training improves held-out alias transfer but
does not create semantic specificity. On held-out `alias_2`, raw target directions
move `6/7` positives in both prompt frames, but they also move `5/5` controls.
The specificity score is near zero. Multi-control penalties do not fix this;
they are zero or negative under the held-out alias gate.

| Prompt | Eval | Direction | Positive passes | Positive mean | Control passes | Control mean | Specificity |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| source_passage | alias_2 | target_learned | 6/7 | 0.326 | 5/5 | 0.292 | 0.034 |
| source_passage | alias_2 | target_resid_all | 6/7 | 0.267 | 5/5 | 0.272 | -0.005 |
| source_passage | alias_2 | target_penalty_controls_1_0 | 6/7 | 0.307 | 5/5 | 0.309 | -0.002 |
| source_passage | alias_2 | target_penalty_controls_2_0 | 6/7 | 0.291 | 5/5 | 0.331 | -0.040 |
| source_passage | canonical | target_learned | 6/7 | 0.343 | 5/5 | 0.647 | -0.305 |
| source_passage | canonical | target_resid_all | 6/7 | 0.334 | 5/5 | 0.433 | -0.099 |
| latent_choice | alias_2 | target_learned | 6/7 | 0.324 | 5/5 | 0.322 | 0.002 |
| latent_choice | alias_2 | target_resid_all | 6/7 | 0.272 | 4/5 | 0.285 | -0.013 |
| latent_choice | alias_2 | target_penalty_controls_1_0 | 6/7 | 0.321 | 5/5 | 0.344 | -0.022 |
| latent_choice | alias_2 | target_penalty_controls_2_0 | 6/7 | 0.318 | 5/5 | 0.365 | -0.047 |
| latent_choice | canonical | target_learned | 6/7 | 0.382 | 5/5 | 0.781 | -0.399 |
| latent_choice | canonical | target_resid_all | 6/7 | 0.336 | 5/5 | 0.577 | -0.240 |

The training alias surface itself is easier: `alias_0` gives `7/7` positives for
learned and constrained directions. But controls are also `5/5`, and control
means are larger than positive means. This is the opposite of a semantic-specific
intervention.

## Failure Pattern

The one positive that fails under held-out `alias_2` is consistent across prompt
frames and direction modes:

```text
phase_space -> conceptual_space
```

This suggests the expanded positive set contains at least one relation whose
label surfaces are not aligned enough for the current behavior-gradient objective.
That is useful, but it is secondary. The more important failure is that the five
controls pass nearly everywhere.

## Diagnosis

Accepted:

```text
Training over multiple alias surfaces improves held-out alias transfer relative
to random directions on the expanded set.
```

Rejected:

```text
Multi-alias behavior gradients plus multi-control penalties are sufficient for
semantic-specific steering.
```

Withheld:

```text
The current behavior-aligned directions isolate a concept relation rather than a
general full-label target-boosting channel.
```

Best current interpretation:

```text
The behavior objective has learned a broad label-surface transport direction. It
can move many held-out target names, but it also moves matched controls. The next
research step should diagnose the leakage channel as a subspace, not add more
penalty weight to the same objective.
```

## Next Move

- Add a low-rank leakage-channel diagnostic over target/control directions.
- Add random relation nulls so controls are not only hand-picked semantic pairs.
- Add CAA/CAV-style activation-difference baselines under the same held-out alias
  verifier.
- Only after leakage diagnosis should we spend compute on larger-model
  replication or generation tests.

## Discovery-Regime Audit

Question: does multi-alias objective training plus a larger pair set produce
semantic-specific behavior directions?

Current regime:

- Artifact types: alias-indexed label manifests, grouped objective regimes,
  full-label gradient directions, expanded pair manifests, specificity reports.
- Operations: multi-alias gradient averaging, held-out alias scoring,
  norm-matched multi-control penalties, specificity-score comparison.
- Gates/verifiers: held-out alias positives must transfer and independent
  controls must remain lower than positives under the same score surface.
- Known limitations: one model, one seed, no generation scoring yet, expanded
  controls are hand-picked rather than random-relation nulls.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this creates a stronger gate and falsifies the current multi-alias
  behavior objective as a paper-ready specificity mechanism.

Experiment:

- Manifest/report paths: this report; local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_multialias_expanded_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: expanded control pairs with leave-one-out control bases.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`;
  canonical labels; three scales.

Gate:

- Acceptance rule: pass if held-out `alias_2` positives remain high while
  controls are suppressed enough to make specificity clearly positive.
- Withheld/rejected rule: withhold if controls pass broadly or specificity is
  near zero/negative.

Results:

- Accepted artifacts: grouped objective regimes; third aliases; expanded pair
  set; this report.
- Rejected or withheld artifacts: multi-alias constrained behavior directions
  remain non-paper-ready.
- Key metrics: held-out `alias_2` target-learned reaches `6/7` positives in both
  prompt frames but controls pass `5/5`; specificity is `0.034` in
  `source_passage` and `0.002` in `latent_choice`.
- Variance or ablation: both prompt frames agree; constrained and residual modes
  do not improve specificity.

Residual content:

- Explained by old regime: behavior gradients can move many held-out target
  labels.
- New content outside old regime: the main obstacle is now identifiable as broad
  control leakage, not just single-alias fragility.
- Retractions or supersessions: supersede "multi-alias training may be enough"
  with "multi-alias training improves transfer but not specificity."

Next move: diagnose whether leakage is low-rank or pair-specific.
