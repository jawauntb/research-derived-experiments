# Phase 2 Clean Context Handoff

Date: 2026-06-22
Repo: `jawauntb/research-derived-experiments`
Start point: freshly fetched `origin/main`
Reference state when this handoff was prepared: `4398fc0`
(`Merge pull request #145 from jawauntb/codex/phase2-clean-context-handoff-sha`)
External paper folder: `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2`

Use this note to start the next agent session from a clean context window.

## Current State

Phase 2A and 2B now share a Modal-confirmed `2A-v2` rich-program contract:

```text
2A-v2-pixels-rich_programs
  + searched finite rich-program recipes
  + held-out role/parse transfer repair
  + supervised learned slot semantics
  + label-free role-token calibration
  + transfer-consuming executable module bodies
```

Do not summarize this as "2A is done" or "2B is done." The honest claim is:

- `2A-v2` is done as a provided finite rich-program grammar with searched
  recipes, transfer repair, supervised learned slot semantics, and label-free
  role-token calibration.
- It is not done as open-ended motor/apparatus discovery, fully unsupervised
  semantic-profile discovery, natural-image object discovery, or full neural
  architecture search.
- `2B-v2` has compact motif/body validation and executable-module bodies that
  consume the v2 transfer contract, but not full searched/evolved neural
  module discovery.

## Recent Merged PRs

- PR #139: `2A-v2` held-out transfer repair plus transfer-consuming executable
  module body gate.
- PR #140: supervised learned slot-semantics repair.
- PR #141: searched finite rich-program recipe gate.
- PR #142: label-free slot-semantics transfer gate.

## Accepted Evidence

### Rich Program Language

Report:
`experiments/concerned_syntax/results/rich_program_language_modal_2026_06_17.md`

Positive:
`concerned_program_composer`

Metrics:
parse/action/family/target/useful/rich high `1.000`, low-program `0.162`,
gate PASS across five Modal seeds.

Rejected controls:
`target_without_family`, `family_without_target`, `rich_without_concern`,
`surface_rich_shortcut`, and `random_rich_program`.

### Searched Rich Program Recipes

Report:
`experiments/concerned_syntax/results/searched_rich_program_policy_modal_2026_06_18.md`

Positive:
`concerned_rich_program_search`

Best recipe:
`concern_or_calibration+learned_family+slot_scores+bind_if_useful_program+bound_action`

Metrics:
parse/action/family/target/useful/rich high `1.000`, subtree `0.789`,
low-program `0.144`, regret `0.004`, gate PASS across five Modal seeds.

Rejected controls:

- `reward_only_rich_program_search`: chooses no useful program.
- `family_proxy_rich_program_search`: family `1.000`, but target/useful
  `0.076` and low-program `1.000`.
- `syntax_proxy_rich_program_search`: syntax/family/target/useful/rich
  `1.000`, but low-program `1.000`.

### Rich Transfer Repair

Report:
`experiments/concerned_syntax/results/rich_program_transfer_repair_modal_2026_06_18.md`

Positive:
`role_equivariant_rich_world_model`

Metrics:
transfer gate `1.000`, parse/action/family/target/useful/rich high `1.000`,
low-program `0.000`, regret `0.004`, gate PASS across five Modal seeds.

Boundary:
this uses an explicit role-equivariant decoder.

### Supervised Learned Slot Semantics

Report:
`experiments/concerned_syntax/results/learned_slot_semantics_modal_2026_06_18.md`

Positive:
`learned_slot_semantic_world_model`

Metrics:
semantic kind/pair `1.000`, transfer gate `1.000`,
family/target/useful/rich high `1.000`, low-program `0.000`, gate PASS across
five Modal seeds at 3,000 train / 1,200 test / 90 epochs.

Boundary:
role-token calibration is supervised and synthetic.

### Label-Free Slot Semantics

Report:
`experiments/concerned_syntax/results/unsupervised_slot_semantics_modal_2026_06_18.md`

Positive:
`unsupervised_slot_semantic_world_model`

Metrics:
semantic kind/family/pair `1.000`, transfer gate `1.000`,
family/target/useful/rich high `1.000`, low-program `0.000`, regret `0.004`,
gate PASS across five Modal seeds at 3,000 train / 1,200 test / 90 epochs.

Boundary:
this removes visible role-token labels, but still uses a supplied semantic
profile table plus synthetic rich-program feedback. Do not call it fully
unsupervised semantic discovery.

### 2B Transfer-Consuming Executable Bodies

Report:
`experiments/viable_computational_bodies/results/learned_executable_modules_modal_2026_06_18.md`

Positive:
`transfer_repaired_executable_body`

Metrics:
transfer gate `1.000`, executable-module coverage `1.000`,
family/target/useful/rich `1.000`, low-program `0.000`, resource cost `16`,
gate PASS across five Modal seeds.

Boundary:
compact explicit modules, not full searched/evolved neural architecture.

## Most Important Files

- Main paper:
  `papers/concerned_syntax/paper.md`
- Rendered paper:
  `papers/concerned_syntax/paper.pdf`
- Public external PDF:
  `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/concerned_syntax.pdf`
- Long handoff:
  `docs/phase2_next_breakthrough_handoff.md`
- Trajectory:
  `docs/phase2_breakthrough_trajectory.md`
- Audit ledger:
  `docs/discovery_regime_audit.md`
- 2A implementations:
  `experiments/concerned_syntax/rich_program_language.py`
  `experiments/concerned_syntax/searched_rich_program_policy.py`
  `experiments/concerned_syntax/rich_program_transfer_repair.py`
  `experiments/concerned_syntax/learned_slot_semantics.py`
  `experiments/concerned_syntax/unsupervised_slot_semantics.py`
- 2B implementation:
  `experiments/viable_computational_bodies/learned_executable_modules.py`

## Next Best Move

Start from a fresh fetch/pull of `main` in a new worktree.

Recommended branch:

```text
codex/phase2-searched-executable-modules
```

Best next experiment:

Make 2B search/evolve executable module bodies that consume the newest
label-free transfer contract. The current body gate has compact explicit
modules. The next breakthrough is to search/evolve those executable modules
under the same v2 transfer verifier.

Alternative strong 2A branch:

```text
codex/phase2-semantic-profile-discovery
```

Goal:
replace the supplied semantic profile table in
`unsupervised_slot_semantics.py` with a discovered profile mechanism. Keep the
same held-out transfer gate and controls. Be strict: if the profile table is
still supplied, do not claim fully unsupervised semantic discovery.

## Modal-First Rule

Do local smoke tests only. Heavy evidence must run on Modal, especially any
five-seed sweep, held-out slice grid, or search/evolution loop.

The user has a constrained local machine. Avoid cooking it.

## Required Finish Rhythm

For any follow-up branch:

1. Fresh fetch/pull of `main` and new worktree/branch.
2. Minimal local smoke test.
3. Modal full sweep for the scientific claim.
4. Update reports, audit ledger, trajectory, handoffs, paper, and PDFs.
5. Render affected PDFs and visually inspect PNG pages.
6. Run required checks:
   - `git diff --check`
   - lint/type checks
   - targeted tests if behavior changed
7. Commit, push, open PR, merge to `main` when clean.

## Copy-Paste Prompt For Next Agent

```text
Start from fresh `origin/main` in `jawauntb/research-derived-experiments`.
Read `docs/phase2_clean_context_handoff.md`,
`docs/phase2_next_breakthrough_handoff.md`, and
`docs/discovery_regime_audit.md`.

Continue Phase 2 from freshly fetched `origin/main`. The next best move is
`codex/phase2-searched-executable-modules`: search/evolve 2B executable module
bodies that consume the newest label-free `2A-v2` transfer contract. Keep the
claim honest, use Modal for full evidence, avoid heavy local sweeps, update the
paper/audit/handoff/PDFs, run checks, commit, push, PR, and merge when clean.
```
