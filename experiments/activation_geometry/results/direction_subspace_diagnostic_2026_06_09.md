# Direction Subspace Diagnostic - 2026-06-09

## Question

The multi-alias expanded specificity gate found strong held-out alias transfer
but near-zero semantic specificity: positives moved, and controls moved too. This
diagnostic asks whether the leakage is a shared low-rank control channel or a
set of pair-specific overlaps.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_direction_subspace_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_direction_subspace_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Layer: `5`
- Pair set: `expanded`
- Objective labels: `alias_0+alias_1`
- Prompt frames: `source_passage`, `latent_choice`
- Scoring surface: `full_label`
- Train variants: `0,1`

The diagnostic computes target-gradient directions only. It returns:

- singular spectra for all directions, positive directions, and control directions;
- pairwise cosine summaries;
- fraction of each positive direction captured by the rank-`k` control subspace.

## Results

The control directions are not a one-vector leakage channel. In both prompt
frames, the control target directions have effective rank around `4.2` out of
five controls. The first control component explains about `0.42` of control
energy, and the top two explain only about `0.63` to `0.65`.

| Prompt frame | Group | Effective rank | Top-1 variance | Top-2 cumulative |
| --- | --- | ---: | ---: | ---: |
| source_passage | all | 9.441 | 0.194 | 0.379 |
| source_passage | positive | 6.226 | 0.269 | 0.473 |
| source_passage | control | 4.179 | 0.418 | 0.648 |
| latent_choice | all | 9.211 | 0.189 | 0.363 |
| latent_choice | positive | 6.287 | 0.262 | 0.458 |
| latent_choice | control | 4.201 | 0.415 | 0.630 |

The full five-dimensional control subspace captures only a modest fraction of
positive direction energy on average:

| Prompt frame | Control rank | Positive mean capture | Positive max capture | Control mean capture |
| --- | ---: | ---: | ---: | ---: |
| source_passage | 1 | 0.010 | 0.025 | 0.418 |
| source_passage | 2 | 0.067 | 0.198 | 0.648 |
| source_passage | 3 | 0.141 | 0.557 | 0.825 |
| source_passage | 5 | 0.159 | 0.581 | 1.000 |
| latent_choice | 1 | 0.009 | 0.024 | 0.415 |
| latent_choice | 2 | 0.079 | 0.239 | 0.630 |
| latent_choice | 3 | 0.177 | 0.662 | 0.820 |
| latent_choice | 5 | 0.194 | 0.676 | 1.000 |

This argues against a simple shared-control-subspace explanation. The average
positive direction is not mostly inside the control subspace.

However, there are large pair-specific overlaps. The strongest positive-control
overlap in both prompt frames is:

```text
conceptual_space->representation_manifold
homeostasis->representation_manifold
```

with cosine magnitude `0.746` in `source_passage` and `0.802` in
`latent_choice`. Other large overlaps are also target- or source-sharing pockets,
such as `validity_gate->weak_constraint` with
`semantic_distance->validity_gate`, and `autopoiesis->homeostasis` with
`homeostasis->representation_manifold`.

| Prompt frame | Group | Mean abs cosine | Max abs cosine |
| --- | --- | ---: | ---: |
| source_passage | positive-control cross | 0.113 | 0.746 |
| source_passage | within control | 0.211 | 0.659 |
| source_passage | within positive | 0.149 | 0.487 |
| latent_choice | positive-control cross | 0.120 | 0.802 |
| latent_choice | within control | 0.193 | 0.680 |
| latent_choice | within positive | 0.131 | 0.493 |

## Diagnosis

Accepted:

```text
The leakage is not well explained by one generic low-rank control direction.
```

Accepted:

```text
Some leakage is pair-specific and label-pocket-specific, especially when a
positive and a control share the same target label or adjacent source/target
concepts.
```

Rejected:

```text
A single shared control-subspace subtraction should solve the expanded
specificity failure.
```

Withheld:

```text
The current control set is sufficient. Some controls are too target-overlapping
to distinguish leakage from legitimate target-name transport.
```

Best current interpretation:

```text
The score-level leakage is broader than a single vector but not simply "all
positive directions live in the control subspace." The hard cases are relation
pockets where positives and controls share target labels or nearby role
structure. The next verifier needs random relation nulls and target-disjoint
controls, then a baseline table against CAA/CAV-style activation differences.
```

## Next Move

- Add random relation nulls with target-disjoint controls.
- Separate controls into target-sharing, source-sharing, and fully disjoint
  classes.
- Compare behavior-gradient directions against CAA/CAV-style activation
  difference baselines under the same held-out alias verifier.
- Only then rerun larger-model replication or generation tests.

## Discovery-Regime Audit

Question: is behavior-direction leakage low-rank or pair-specific?

Current regime:

- Artifact types: behavior target-gradient directions, pairwise cosine summaries,
  singular spectra, control-subspace capture tables.
- Operations: multi-alias target-gradient extraction, normalized direction SVD,
  control-subspace projection, pairwise cosine ranking.
- Gates/verifiers: low-rank leakage would show high control energy in one or two
  components and high positive capture by that control subspace; pair-specific
  leakage would show low average capture but high individual pair overlaps.
- Known limitations: one model, one layer, one seed; no random relation nulls yet.

Action class:

- Retrieval/search/discovery: mechanistic diagnostic.
- Why: this adds a direction-subspace artifact class that was missing from the
  previous score-only specificity gates.

Experiment:

- Manifest/report paths: this report; local ignored payloads under
  `artifacts/activation_geometry/modal_pythia_70m_direction_subspace_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: expanded control pairs.
- Stress tests: `source_passage` and `latent_choice`.

Gate:

- Acceptance rule: classify leakage as low-rank only if low-rank control
  components capture most positive direction energy on average.
- Withheld/rejected rule: withhold low-rank explanation if average positive
  capture stays low and high overlaps are pair-specific.

Results:

- Accepted artifacts: Modal subspace diagnostic and this report.
- Rejected or withheld artifacts: one-vector or simple low-rank shared leakage
  explanation.
- Key metrics: control effective rank `4.179`/`4.201`; rank-5 control subspace
  captures only `0.159`/`0.194` positive energy on average, but max pair capture
  reaches `0.581`/`0.676`.
- Variance or ablation: source and latent prompt frames agree.

Residual content:

- Explained by old regime: broad full-label gradients move many labels.
- New content outside old regime: leakage is localized in relation pockets, not
  captured by one shared control vector.
- Retractions or supersessions: supersede "subtract the control subspace" with
  "stratify controls and add target-disjoint random relation nulls."

Next move: add random relation nulls and target-disjoint controls.
