# Phase 2 Semantic Profile Discovery Handoff

Date: 2026-06-22
Repo: `jawauntb/research-derived-experiments`
Prepared from: freshly fetched `origin/main` after PR #147
Recommended branch: `codex/phase2-semantic-profile-discovery`

Use this note to start a clean agent session whose job is to attack the next
Phase 2C-adjacent bottleneck: removing the supplied semantic profile table from
the label-free slot-semantics gate while preserving the hard-won 2A/2B
evidence stack.

## Copy-Paste Kickoff Prompt

```text
Start from fresh `origin/main` in `jawauntb/research-derived-experiments`.
Read:
- `docs/phase2_semantic_profile_discovery_handoff.md`
- `docs/phase2_clean_context_handoff.md`
- `docs/phase2_next_breakthrough_handoff.md`
- `docs/discovery_regime_audit.md`

Create a new worktree/branch named `codex/phase2-semantic-profile-discovery`.

Goal: replace the supplied semantic profile table in
`experiments/concerned_syntax/unsupervised_slot_semantics.py` with a discovered
or inferred profile mechanism. Keep the existing label-free held-out transfer
gate and controls. Use local work only for smoke tests and development. Run
the real multi-seed evidence on Modal. Update reports, audit ledger,
trajectory, handoffs, paper/PDFs, run checks, commit, push, open a PR, and
merge when clean.

Do not overclaim. If the new mechanism still receives the kind/profile table
or just selects among supplied named profiles, call it profile selection or
calibration, not fully unsupervised semantic discovery.
```

## One-Line Summary

We already have label-free role-token calibration and searched executable
module bodies over the label-free transfer gate. The next real step is to make
the agent infer semantic profiles from component clusters, intervention
outcomes, and action consistency instead of receiving the profile table.

## Bigger Goal

The Phase I Metric Stack of Concern result showed a correction chain:

```text
viability prediction -> maintained concern -> self/world attribution
-> costly null probes -> correction -> re-engagement
```

Phase 2 is trying to show that maintained concern is not just another reward
or uncertainty scalar. It should organize:

```text
world syntax:
  perception -> causal constituency -> intervention/program choice

body syntax:
  motif grammar -> formal/resource admissibility -> empirical competence

combined claim:
  concern selects which distinctions matter, which experiments expose them,
  and which computational bodies can exploit them without shortcutting.
```

The field-facing claim to build toward is:

```text
Maintained concern is a discovery pressure that shapes representation,
experiment selection, and computational morphology under explicit anti-cheat
and formal gates.
```

This branch should not try to prove the full claim by itself. Its job is to
remove one remaining scaffold from the existing 2A-v2 contract.

## Current State On `main`

Phase 2A and 2B now share this Modal-confirmed contract:

```text
2A-v2-pixels-rich_programs
  + searched finite rich-program recipes
  + held-out role/parse transfer repair
  + supervised learned slot semantics
  + label-free role-token calibration
  + transfer-consuming executable module bodies
  + searched executable-module bodies over the label-free transfer gate
```

Recent relevant merged work:

- PR #139: held-out transfer repair plus transfer-consuming executable body.
- PR #140: supervised learned slot semantics.
- PR #141: searched finite rich-program recipes.
- PR #142: label-free slot-semantics transfer gate.
- PR #147: searched executable-module bodies over the label-free transfer gate.

Accepted label-free slot-semantics evidence:

```text
report: experiments/concerned_syntax/results/unsupervised_slot_semantics_modal_2026_06_18.md
positive: unsupervised_slot_semantic_world_model
semantic kind/family/pair: 1.000
transfer gate: 1.000
family/target/useful/rich high: 1.000
low-program: 0.000
gate: PASS across five Modal seeds
```

Accepted searched executable-module evidence:

```text
report: experiments/viable_computational_bodies/results/searched_executable_modules_modal_2026_06_22.md
positive: viability_guided
body gate: 1.000
transfer gate: 1.000
formal validity: 1.000
semantic kind/pair: 1.000
module coverage: 1.000
family/target/useful/rich high: 1.000
low-program: 0.000
resource cost: 18
gate: PASS across five Modal seeds
```

Do not summarize this as "2A is done" or "2B is done." The honest state is:

- `2A-v2` is strong as a provided-rich-grammar, label-free role-token,
  held-out-transfer contract.
- `2A-v2` is not yet fully unsupervised semantic-profile discovery, natural
  image object discovery, open-ended motor/apparatus invention, or a learned
  object-slot perception story.
- `2B-v2` is strong as bounded motif/body search and executable contract
  search over that 2A gate.
- `2B-v2` is not full neural architecture search or trainable neural module
  discovery.

## Why This Is The Next Bottleneck

The current implementation removes visible role-token labels, but it still
contains a supplied semantic profile table:

```text
experiments/concerned_syntax/unsupervised_slot_semantics.py
```

The file says the limitation in its docstring:

```text
The semantic profile table is still supplied; the result is label-free
role-token calibration, not fully unsupervised semantic discovery.
```

The key scaffold is `KIND_PROFILES`, which hands the inducer named semantic
profiles:

```text
shield_poison      -> compose_move_observe, concern_weight 1.4, roles shield/poison
repair_core        -> move_anchor,          concern_weight 1.2, roles repair/core
food_trap          -> ablate_pair,          concern_weight 1.0, roles food/trap
ornament_signal    -> observe_pair,         concern_weight 0.2, roles signal/ornament
```

The current `induce_unsupervised_slot_semantics` clusters connected components,
groups active cluster pairs, and scores candidate profiles through
`_kind_profile_score`. That is label-free role-token calibration, but the
candidate profile vocabulary is still externally provided.

The next branch should ask:

```text
Can profile structure be inferred from intervention/outcome evidence and
action consistency, rather than supplied as a named table?
```

## Target Transition

Old regime:

- Connected components are clustered without visible role labels.
- Active cluster pairs are grounded through synthetic rich-program feedback.
- Candidate semantic profiles are supplied by `KIND_PROFILES`.
- The accepted agent maps cluster pairs to those supplied profiles.

Desired new regime:

- Connected components are still clustered, to keep the first experiment
  narrow.
- Active cluster pairs are still grounded through rich-program feedback and
  action consistency.
- The accepted agent does not receive `KIND_PROFILES` or the kind-to-family /
  concern-weight / role-pair table.
- Profile hypotheses are induced, searched, or fit from observable intervention
  consequences.

Possible claim levels:

- If the agent invents profile records from outcome/action structure without a
  named candidate table: "semantic profile discovery" within the synthetic
  connected-component world.
- If the agent has a generic library of profile slots but must assign family,
  concern, and roles from feedback: "semantic profile induction."
- If the agent chooses among hidden supplied profile templates: "profile
  selection" or "calibration," not discovery.

Be precise. A failed or narrowed result is still useful if it identifies which
part of the profile remains scaffolded.

## Implementation Targets

Start with:

```text
experiments/concerned_syntax/unsupervised_slot_semantics.py
experiments/concerned_syntax/modal_unsupervised_slot_semantics_sweep.py
tests/test_concerned_syntax.py
```

Likely code areas:

- `InducedKindProfile`
- `KIND_PROFILES`
- `PROFILE_ORDER`
- `_kind_profile_score`
- `induce_unsupervised_slot_semantics`
- `summarize_inducer`
- `run_unsupervised_slot_semantics_experiment`
- report aggregation and Markdown output near the CLI entrypoint

The new code can either modify this file or add a sibling implementation such
as:

```text
experiments/concerned_syntax/discovered_semantic_profiles.py
experiments/concerned_syntax/modal_discovered_semantic_profiles_sweep.py
```

Prefer a sibling file if the change would make the old result harder to
compare or rerun. Preserve the current label-free result as a baseline.

## Suggested Approach

Keep the first attempt deliberately bounded:

1. Keep connected-component extraction and clustering unchanged.
2. For each active cluster pair, collect intervention traces:
   - observed active pair;
   - candidate program family tried;
   - whether the family exposed useful parse evidence;
   - selected target pair;
   - inferred parse;
   - resulting action;
   - utility/action regret under the trial feedback available to the benchmark.
3. Infer a profile record per cluster pair:
   - `family`: which program family reliably produces useful information;
   - `concern_weight` or concern band: whether action utility makes the pair
     high-concern or low-concern;
   - `role_pair`: local role names or anonymous slots derived from asymmetric
     intervention effects, not from `example.trial.roles`;
   - optional `kind`: generated from learned attributes, not read from the
     ground-truth kind label.
4. Keep the downstream world-model interface compatible enough that the old
   transfer gate can evaluate it.

Important: do not consume `example.trial.kind`, `example.trial.roles`, or a
handwritten mapping from kind to family/roles in the accepted agent. The
evaluator may use ground truth to score, but the inducer should not.

Good first variants to compare:

- `discovered_semantic_world_model`: learns family, concern band, and pair
  semantics from intervention/action feedback.
- `discovered_semantic_family_only`: gets family-like feedback but not target
  binding discipline.
- `discovered_semantic_target_only`: gets target binding but not family or
  concern discipline.
- `discovered_semantic_rich_without_concern`: can compose rich programs but
  lacks the concern gate.
- `learned_rich_program_composer`: existing baseline that should still fail
  held-out role/parse transfer.

## Gates And Controls

Preserve the old primary gate:

```text
held-out role-kind and true-parse transfer
```

The accepted positive should satisfy:

- transfer gate high across Modal seeds;
- semantic family and pair accuracy high;
- family/target/useful/rich high-concern rates high;
- low-concern program use capped;
- regret remains low;
- controls fail for distinct, diagnostic reasons.

Use the previous label-free thresholds as the starting contract:

```text
semantic kind/family/pair >= 0.95 where kind is still meaningful
transfer gate = 1.000 or report any miss explicitly
family/target/useful/rich high-concern >= 0.70
low-program <= 0.25
```

If the new mechanism no longer has a ground-truth `kind` prediction, replace
semantic kind accuracy with profile-cluster purity, family accuracy, pair
accuracy, and action-consistency metrics. State the metric change in the audit.

Controls should not merely score lower. They should fail differently:

- family-only: knows which program family is tempting, but misses target/useful
  binding.
- target-only: knows where to look, but misses family/rich composition and may
  over-probe low-concern cases.
- ungated-rich: can compose rich programs, but fails concern discipline.
- learned-composer baseline: still fails held-out transfer.

## Modal-First Rule

Local is for development only:

```bash
python3 -m experiments.concerned_syntax.unsupervised_slot_semantics \
  --train-trials 90 --test-trials 40 --seed 20260618 --epochs 10 \
  --induction-calibration-trials 500 \
  --out artifacts/concerned_syntax/unsupervised_slot_semantics_local.json \
  --report experiments/concerned_syntax/results/unsupervised_slot_semantics_local_2026_06_18.md
```

Once the new implementation has a smoke pass, add or update the Modal entrypoint
and run the real evidence there:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_discovered_semantic_profiles_sweep.py \
  --train-trials 3000 --test-trials 1200 --epochs 90 \
  --induction-calibration-trials 1200
```

If reusing the existing entrypoint instead, document that clearly and keep the
artifact/report names distinct from the old label-free result.

Do not run heavy multi-seed training or sweeps locally.

## Reports, Docs, And Paper Updates

Expected new artifacts:

```text
experiments/concerned_syntax/results/discovered_semantic_profiles_local_2026_06_22.md
experiments/concerned_syntax/results/discovered_semantic_profiles_modal_2026_06_22.md
```

Use a later date if the work happens later.

Update these files if the experiment lands:

```text
README.md
experiments/concerned_syntax/README.md
docs/discovery_regime_audit.md
docs/phase2_breakthrough_trajectory.md
docs/phase2_clean_context_handoff.md
docs/phase2_next_breakthrough_handoff.md
papers/concerned_syntax/paper.md
papers/concerned_syntax/paper.pdf
```

If the result affects 2B's current searched executable-module body, decide
whether `experiments/viable_computational_bodies/searched_executable_modules.py`
must consume the new profile-discovery contract. If that becomes too large,
record it as the next branch rather than silently broadening this one.

External PDF folder:

```text
/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2
```

Render and visually inspect updated PDF pages before finalizing.

## Coordination With The Other Active Agent

The user's other agent is working on the external validation/geometric research
review track, not this Phase 2C-adjacent implementation track.

As of the user's note, that other branch is focused on:

- P2 Tier-A and Tier-B uncertainty/value-of-information evidence;
- P3 GloVe/fastText cross-family RSA and possible contextual embedding follow-up;
- P1 Pythia weakness-to-OOD, where the linear-probe version degenerated and a
  LoRA Tier-B run may be the next informative test;
- an honest synthesis of which pillars survive outside the self-built world.

Do not duplicate that work in this branch. This branch should stay on the
internal Phase 2 semantic-profile bottleneck. The eventual synthesis should say
whether the external validation track strengthens or weakens the broader
program, but it should not block this implementation branch.

Message to send the other agent if coordination is needed:

```text
Proceed with the external validation track: P2 Tier-B, then decide P1 LoRA
versus synthesis. A separate branch will attack Phase 2 semantic-profile
discovery by removing the supplied profile table from label-free slot semantics.
Please avoid starting that semantic-profile-discovery branch unless we
coordinate first.
```

## Definition Of Done

Minimum:

- fresh worktree/branch from fetched `origin/main`;
- accepted agent does not consume the supplied semantic profile table;
- old label-free transfer gate is preserved or any gate change is explicit;
- controls fail for diagnostic reasons;
- local smoke report exists;
- Modal multi-seed report exists for the scientific claim;
- audit ledger records old regime, transition, transported evidence, rejected
  alternatives, residual finding, readiness, allowed claim, and next operation;
- paper and handoff docs state the limitation honestly;
- required checks pass;
- branch is committed, pushed, PR opened, and merged when clean.

Required checks before commit/PR:

```bash
git diff --check
python3 scripts/publication_guard.py
python3 -m unittest tests.test_concerned_syntax
uvx ruff check .
uvx ty check scripts experiments tests
```

If behavior changed outside the targeted file, run the broader quality script:

```bash
python3 scripts/run_quality_checks.py
```

## Final Claim Boundary

Good claim if it passes:

```text
Within the synthetic connected-component 2A-v2 world, the agent can infer
semantic profile structure from intervention/outcome and action-consistency
evidence without a supplied semantic profile table, while preserving held-out
role/parse transfer and rejecting shortcut controls.
```

Do not claim:

- natural-image object discovery;
- fully open-ended semantics;
- human or neural validation;
- open-ended motor/apparatus invention;
- full neural architecture search;
- that 2A or 2B is complete.

The most valuable failure would be a clean diagnosis of which part still needs
scaffolding: family, target binding, concern weight, asymmetric role identity,
or transfer repair.
