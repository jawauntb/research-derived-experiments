# Activation Geometry Nightly Checkpoint: Pair-Optimized Intervention Pivot

Date: 2026-06-10

## Why this checkpoint exists

The current publication path is not blocked by code. It is blocked by evidence:
linear behavior directions keep collapsing into answer-surface or carrier
confirmation geometry. Tonight's key update is that the focused Pythia-160M
replication of the tiny Pythia-70M layer-3 pocket completed and failed, so the
next session should not spend its first energy rerunning larger PC-whitening
sweeps.

This note is the pause-safe handoff for the next work session.

## Latest Handoff: Positive-Family Frontier Replication

This section supersedes the earlier "pair-optimized intervention pivot" as the
next active work item. The pair-optimized vector was implemented and tested; it
was useful diagnostically, but it leaked structured controls. The current
frontier is the positive-family binary direction added in PR #73.

Current branch for the next checkpoint:

- Worktree:
  `/Users/jawaun/Research-Derived-Experiments-worktrees/positive-family-replication`
- Branch:
  `codex/positive-family-replication`
- Base:
  `2159042 feat: add positive-family binary direction probe (#73)`

What we know now:

- Pair-specific `target_binary_strict_opt_8` can move one strict positive, but
  it leaks structured controls under the stratified gate.
- Positive-family `target_binary_positive_family_opt_8` is the cleanest strict
  binary result so far:
  - Pythia-70M layer 3
  - objective labels `alias_0`
  - evaluation labels `alias_2`
  - train variant `0`, holdout variant `2`
  - pair set `layer3_strict_pocket_stratified_controls`
  - scale `1.0`
  - result: `1/2` strict positives and `0/12` stratified controls.
- The surviving positive is `attractor->attractor_network`.
- `fixed_point->prototype` fails at every tested positive-family scale.
- Scale tuning is narrow rather than solved:
  - `1.0` is clean.
  - `1.25` revives `1/12` target-sharing controls.
  - `1.5` fails the always-false carrier check on the surviving positive.

Main public report:

`experiments/activation_geometry/results/positive_family_binary_direction_2026_06_10.md`

Local ignored artifacts:

- `artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_alias0_seed20260610.json`
- `artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_scale_seed20260610.json`

## What Tomorrow Should Do First

Do not expand to more concepts yet. Run the smallest replication that can break
the positive-family frontier:

- Same model: `EleutherAI/pythia-70m-deduped`
- Same layer: `3`
- Same pair set: `layer3_strict_pocket_stratified_controls`
- Same strict binary verifier and held-out eval alias: `alias_2`
- Perturb the objective alias or train variant.

First command to run:

```bash
cd /Users/jawaun/Research-Derived-Experiments-worktrees/positive-family-replication
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-positive-family-opt8-alias1-strata experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_positive_family_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_alias1_seed20260610.json
```

Second command if the first does not immediately collapse the result:

```bash
cd /Users/jawaun/Research-Derived-Experiments-worktrees/positive-family-replication
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-positive-family-opt8-trainv1-strata experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_positive_family_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_trainv1_seed20260610.json
```

Recommended result report:

`experiments/activation_geometry/results/positive_family_replication_2026_06_10.md`

## Pre-Registered Replication Gate

Treat this as search unless it survives perturbation.

Acceptance rule:

- Alias or train-variant replication keeps at least `1/2` strict positives and
  `0/12` strict stratified controls.
- Stronger rule: the same positive-family operation eventually recovers `2/2`
  positives or survives a second model/layer with nonzero strict positives and
  no stratified controls.

Rejection rule:

- If objective `alias_1` or train variant `1` drops to `0/2` positives, the
  current frontier is alias/train-fragile.
- If controls revive, the positive-family vector is another structured
  answer-surface leak rather than a semantic-specific intervention.

Decision after those runs:

- If alias/train replication holds: test a second model/layer next.
- If it fails: pivot to a pair-conditioned nonlinear or readout-guided
  intervention under the same strict binary verifier.
- In either case, keep all failed artifacts and summarize them explicitly; the
  negative boundary is part of the paper.

## Earlier Checkpoint Git State (Superseded)

- Main includes PR #65:
  `32134cd Add Pythia-160M pocket replication (#65)`.
- Active worktree for the next step:
  `/Users/jawaun/Research-Derived-Experiments-worktrees/pair-optimized-binary-intervention`.
- Active branch:
  `codex/pair-optimized-binary-intervention`.
- The branch was created fresh after fetching and merging PR #65. At this
  checkpoint, it contains only the handoff update plus small cluttered-MNIST
  lint/type fixes needed to keep the latest `main` green.

## Accepted evidence so far

- Pythia-70M layer 5: top-PC residualization/whitening fails as a semantic
  steering route. The target binary gradients are almost collinear with the
  dominant control PC.
- Pythia-70M layer 3: PC1 whitening at scale `1.0` gives the cleanest strict
  pocket: `2/7` strict positives and `0/10` random-null controls.
- The stable strict positives around scale `1.0` are:
  - `attractor->attractor_network`
  - `fixed_point->prototype`
- Scale calibration is exhausted as the next big move: scale `1.25` adds one
  strict positive but revives one strict random-null control.
- Pythia-160M layer 3: the focused two-positive pocket does not replicate.
  `target_binary_pc1_whiten` gives `0/2` strict positives and `0/10` controls
  at every tested scale from `0.5` to `1.5`.

## Failed or withheld evidence

The first Pythia-160M full-pair replication attempt did not produce an artifact
and must not be treated as evidence.

Attempted command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-160m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set expanded_random_nulls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_160m_layer3_pc1_whiten_replication_seed20260610.json
```

Failure mode:

- Modal app URL:
  `https://modal.com/apps/generalintelligencecompany/main/ap-wAKzF1PvlJe76EOMTEQPaq`
- Local client failed with:
  `modal.exception.ConnectionError: [Errno 8] nodename nor servname provided, or not known`
- Modal stopped the app after the client disconnected.
- No local artifact exists at
  `artifacts/activation_geometry/modal_pythia_160m_layer3_pc1_whiten_replication_seed20260610.json`.

## Completed Since The Earlier Checkpoint

- Added durable Modal Volume result writing so long remote jobs can outlive
  local client hiccups.
- Added and used the focused pair set:

  - `layer3_strict_pocket_random_nulls`
  - Positives:
    - `attractor->attractor_network`
    - `fixed_point->prototype`
  - Controls:
    - all ten `RANDOM_RELATION_NULL_PAIRS`, including the hard adversarial
      `valence->steering_vector` row.

- Recorded the negative second-model result in
  `experiments/activation_geometry/results/binary_pythia160_pocket_replication_2026_06_10.md`.
- Updated the paper-readiness and discovery-regime ledgers to retract the
  cross-model pocket hypothesis.

## Modal Artifacts From The Negative Replication

- Local ignored payloads:
  - `artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_replication_seed20260610_raw.json`
  - `artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_replication_seed20260610.json`
  - `artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_scale_sweep_seed20260610_raw.json`
  - `artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_scale_sweep_seed20260610.json`
- Modal Volume payloads:
  - `rde-activation-results:activation_geometry/pythia160_layer3_pocket_seed20260610_raw.json`
  - `rde-activation-results:activation_geometry/pythia160_layer3_pocket_scale_sweep_seed20260610_raw.json`
- Modal call IDs:
  - `fc-01KTR5JE7VHVYA484GXC1AJM3B`
  - `fc-01KTRY77544CMWV4VFK7QXK3FH`

## Earlier Next Step (Completed By Later PRs)

Next move: keep the strict binary verifier, but change intervention class.
Implement a pair-focused optimized activation vector that is trained directly
against the strict binary objective and penalizes the strongest yes-bias
controls, then test it on the same focused pair set.

Suggested implementation target:

- Add a new direction mode such as `target_binary_strict_opt_16`.
- Optimize a per-pair injected final-token vector at the selected layer.
- Training positives: variants `0,1` with objective aliases `alias_0+alias_1`.
- Held-out test: variant `2` with `alias_2`.
- Penalize controls used by the strict binary verifier:
  blank, generic, source, distractor, shuffled target, always-false, and random
  relation nulls where feasible.
- Keep vector norms comparable to the existing binary target-gradient direction
  so scale does not become the explanation.
- Compare against:
  `target_binary_pc1_whiten`, `random_same_norm`, and ideally a raw target
  binary direction if the runner already exposes it.

Useful code hooks to inspect first:

- `experiments/activation_geometry/modal_behavior_aligned_direction.py`
  - `binary_yes_minus_no_gradient_for_prompt`
  - `binary_control_gradient_directions`
  - `learned_gradient_direction`
  - `binary_pc_adjusted_direction`
  - `direction_for_mode`
  - the evaluation loop that builds strict binary summaries
- `experiments/activation_geometry/behavior_aligned_direction.py`
  - direction-mode parsing and validation.

Starter inspection command:

```bash
cd /Users/jawaun/Research-Derived-Experiments-worktrees/pair-optimized-binary-intervention
rg "binary_yes_minus_no_gradient_for_prompt|binary_control_gradient_directions|learned_gradient_direction|binary_pc_adjusted_direction|direction_for_mode|strict" -n experiments/activation_geometry/modal_behavior_aligned_direction.py experiments/activation_geometry/behavior_aligned_direction.py
```

## Earlier Pair-Optimized Gate (Completed And Rejected)

Run the smallest experiment that can break the new intervention:

- Model/layer: start with Pythia-70M layer 3.
- Pair set: `layer3_strict_pocket_random_nulls`.
- Scoring: `binary_relation`.
- Prompt frame: `source_passage`.
- Acceptance rule: the optimized direction must preserve `2/2` strict positives
  and `0/10` strict random-null controls, and it must beat the strongest
  row-level yes-bias control on the held-out alias.
- Stronger acceptance rule: after the Pythia-70M focused test, repeat the same
  mode on Pythia-160M layer 3 and recover at least one strict positive with
  `0/10` strict controls.
- Rejection rule: if the optimized vector only raises broad Yes margins or
  carrier-confirmation controls, record it as another answer-surface failure.

## Earlier Discovery-Regime Status

This is still search, not discovery. The negative Pythia-160M result is useful
because it tightens the claim boundary: the two-pair Pythia-70M pocket is not a
robust semantic steering mechanism.

A discovery-level transition would require a new accepted operation or artifact
type: for example, a pair-optimized or feature-guided intervention that passes
the same strict binary gate and survives at least one model, layer, seed, or
alias perturbation beyond the original Pythia-70M pocket.
