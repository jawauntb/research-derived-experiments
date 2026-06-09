# Full-Label Alias Gate - 2026-06-08

## Question

The carrier-control run showed that full-label behavior transfer is label-anchored and definition-context boosted. This gate asks whether the same canonical-label patch vectors also move non-identical aliases for the target concept.

If aliases survive, the result starts looking like concept-level behavior transfer. If aliases collapse while canonical labels replicate, the current effect is mostly exact-label behavior with only scattered synonym pockets.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_full_label_alias_latent_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_full_label_alias_source_seed20260608.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Patch-vector surface: `hook_output`
- Injection layers: `5,6`
- Patch alpha: `1.0`
- Pair set: `combined`
- Baseline pairs: 8 sampled ordered concept pairs
- Total pairs: 15
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Prompt frames: `latent_choice`, `source_passage`
- Scoring surface: `full_label`
- Label score normalization: mean logprob per label token
- Label scoring regimes: `canonical`, `alias`
- Patch-text regimes: `definition`, `neutral`, `label_only`, `blank_carrier`, `shuffled_label`
- Eval variant: `2`
- Seed: `20260608`

Alias labels come from `experiments/concept_geometry/concept_aliases.json`. Patch vectors still come from canonical-label concept texts, so alias scoring tests transfer from a canonical definition carrier to a different target phrase.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_behavior_gate.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 5,6 --max-length 180 --eval-variant 2 --patch-alphas 1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral,label_only,blank_carrier,shuffled_label --patch-vector-surface hook_output --prompt-frame latent_choice --scoring-surface full_label --label-score-normalization mean --label-scoring-regimes canonical,alias --aliases experiments/concept_geometry/concept_aliases.json --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_full_label_alias_latent_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_behavior_gate.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 5,6 --max-length 180 --eval-variant 2 --patch-alphas 1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral,label_only,blank_carrier,shuffled_label --patch-vector-surface hook_output --prompt-frame source_passage --scoring-surface full_label --label-score-normalization mean --label-scoring-regimes canonical,alias --aliases experiments/concept_geometry/concept_aliases.json --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_full_label_alias_source_seed20260608.json
```

## Results

### Definition Patch Specificity

| Prompt frame | Layer | Canonical passes | Canonical mean advantage | Alias passes | Alias mean advantage |
| --- | ---: | ---: | ---: | ---: | ---: |
| latent_choice | 5 | 9/15 | 0.622 | 6/15 | -0.140 |
| latent_choice | 6 | 9/15 | 0.881 | 6/15 | -0.196 |
| source_passage | 5 | 12/15 | 0.646 | 5/15 | -0.094 |
| source_passage | 6 | 10/15 | 0.881 | 4/15 | -0.196 |

Canonical scoring reproduces the previous carrier-control result. Alias scoring keeps positive raw target-margin movement, but target patches no longer beat distractor/random/source-noop controls on average.

### Alias Carrier Controls

| Prompt frame | Regime | Layer 5 passes | Layer 5 advantage | Layer 6 passes | Layer 6 advantage |
| --- | --- | ---: | ---: | ---: | ---: |
| latent_choice | definition | 6/15 | -0.140 | 6/15 | -0.196 |
| latent_choice | neutral | 2/15 | -0.079 | 2/15 | -0.113 |
| latent_choice | label_only | 5/15 | -0.129 | 4/15 | -0.162 |
| latent_choice | blank_carrier | 0/15 | 0.000 | 0/15 | 0.000 |
| latent_choice | shuffled_label | 5/15 | -0.196 | 3/15 | -0.235 |
| source_passage | definition | 5/15 | -0.094 | 4/15 | -0.196 |
| source_passage | neutral | 2/15 | -0.080 | 2/15 | -0.113 |
| source_passage | label_only | 5/15 | -0.121 | 4/15 | -0.162 |
| source_passage | blank_carrier | 0/15 | 0.000 | 0/15 | 0.000 |
| source_passage | shuffled_label | 4/15 | -0.193 | 2/15 | -0.235 |

The alias surface is not blank-carrier movement, but it is also not a clean definition-specific transfer surface. Label-only and shuffled-label alias controls can match a meaningful fraction of the alias pass count, and every alias regime has negative mean target-over-control advantage except blank, where controls and target are tied by construction.

### Alias Survivor Pockets

Combined across both prompt frames and both layers, a few alias-definition rows survive:

| Pair | Kind | Definition passes | Mean advantage | Main caveat |
| --- | --- | ---: | ---: | --- |
| `weak_constraint->family_resemblance/d=semantic_distance` | baseline_cross_category | 4/4 | 0.443 | Cleanest alias survivor, but not an intended focus bridge. |
| `semantic_distance->conceptual_space/d=family_resemblance` | baseline_same_category | 3/4 | 0.729 | Plausibly lexical-semantic near-neighbor structure. |
| `phase_space->basin_of_attraction/d=attractor` | baseline_same_category | 3/4 | 0.432 | Same-family dynamical vocabulary may be helping. |
| `representation_manifold->weak_constraint/d=simplicity_bias` | baseline_cross_category | 4/4 | 1.177 | Label-only also passes 4/4, so this is label-surface confounded. |
| `valence->activation_vector/d=steering_vector` | generic_control | 4/4 | 0.359 | Shuffled-label also passes 4/4, so this is not clean. |

The survivor pockets are interesting but not yet the publishable claim. They point to a follow-up diagnostic: multiple aliases per concept, alias shuffling, and alias-specific semantic-neighbor baselines.

## Diagnosis

This is a strong boundary result.

Accepted:

```text
The exact canonical-label full-label behavior effect replicates under the alias-gate runner.
```

Accepted:

```text
Canonical definition patch vectors cause some alias-label target movement, but the alias movement is not globally target-specific against distractor/random/source-noop controls.
```

Withheld:

```text
The current behavior transfer is concept-level in a label-invariant sense.
```

Best current interpretation:

```text
The behavior-visible transfer is primarily canonical-label anchored. Alias labels expose weak, pair-specific pockets rather than a broad label-invariant concept transfer surface.
```

This makes the research more revealing, not less. We now know the current mechanism crosses from representation readouts into behavior only through a fragile language surface. That gives us a sharper next target: find an intervention or scoring interface that survives alias/periphrase labels, or prove that the model's concept behavior is mostly mediated by label-specific output geometry.

## Next Move

- Run a multiple-alias gate using both aliases per concept, scored separately.
- Add alias-shuffled controls: score the target alias while patching a different concept whose alias is semantically close.
- Learn behavior-aligned directions against alias labels directly, then test whether those directions still preserve canonical-label movement.
- Diagnose the cleanest alias survivor pockets before broad replication.

## Discovery-Regime Audit

Question: does canonical full-label behavior transfer survive non-identical alias scoring?

Current regime:

- Artifact types: alias-label manifests, full-label behavior payloads, canonical-vs-alias specificity rows, alias survivor pocket tables.
- Operations: hook-output state capture from canonical carriers, full-label continuation scoring over canonical and alias labels, target-vs-control specificity aggregation.
- Gates/verifiers: canonical definition patches should reproduce the carrier-control result; alias patches must beat distractor/random/source-noop controls to count as label-invariant concept transfer.
- Known limitations: one seed, one model, one alias per concept, aliases are hand-authored, no alias-trained behavior direction yet.

Action class:

- Retrieval/search/discovery: verifier refinement with a boundary result.
- Why: this run does not simply repeat the exact-label behavior gate; it changes the scored lexical surface and tests whether behavior transfer is label-invariant.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_alias_*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: alias scoring against distractor/random/source-noop patch modes, `blank_carrier`, `shuffled_label`, `neutral`, `label_only`.
- Stress tests: prompt frames `latent_choice` and `source_passage`; layers `5,6`; canonical vs alias scoring.

Gate:

- Acceptance rule: accept label-invariant behavior transfer only if alias-scored definition target patches pass robustly and have positive target-over-control advantage.
- Withheld/rejected rule: withhold concept-level behavior transfer if alias target movement is matched or exceeded by controls.

Results:

- Accepted artifacts: alias label manifest, alias scoring support in the behavior gate, this report.
- Rejected or withheld artifacts: broad label-invariant behavior transfer claim remains withheld.
- Key metrics: canonical definitions pass `9/15` to `12/15` with mean advantage `0.622` to `0.881`; alias definitions pass only `4/15` to `6/15` and have negative mean advantage from `-0.094` to `-0.196`.
- Variance or ablation: both prompt frames agree: canonical effect replicates; alias specificity collapses globally; a few pair-specific alias pockets remain.

Residual content:

- Explained by old regime: exact canonical labels dominate the behavior-visible effect.
- New content outside old regime: alias scoring reveals weak, pair-specific synonym pockets that may mark either true concept transfer or alias-surface confounds.
- Retractions or supersessions: supersede "full-label behavior transfer may be concept-level" with "full-label behavior transfer is currently canonical-label anchored, with only local alias pockets."

Next move: run multiple-alias and alias-shuffle diagnostics, then try alias-trained behavior-aligned directions.
