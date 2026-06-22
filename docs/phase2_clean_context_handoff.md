# Phase 2 Clean Context Handoff

Date: 2026-06-22
Repo: `jawauntb/research-derived-experiments`
Start point: freshly fetched `origin/main`
Reference state when this handoff was refreshed: branch
`codex/phase2-semantic-profile-discovery`
External paper folder: `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2`

Use this note to start the next agent session from a clean context window.

For historical context on the semantic-profile branch that removed the
supplied table, see `docs/phase2_semantic_profile_discovery_handoff.md`.
For the current integrated internal/external frontier, start with
`docs/phase2_next_phase_research_handoff.md`.

## Current State

Phase 2A and 2B now share a Modal-confirmed `2A-v2` rich-program contract:

```text
2A-v2-pixels-rich_programs
  + searched finite rich-program recipes
  + held-out role/parse transfer repair
  + supervised learned slot semantics
  + label-free role-token calibration
  + transfer-consuming executable module bodies
  + discovered semantic-profile induction
  + learned object slots for discovered-profile transfer
  + searched executable-module bodies over the label-free transfer gate
  + searched executable-module bodies over the learned-object-slot contract
```

Do not summarize this as "2A is done" or "2B is done." The honest claim is:

- `2A-v2` is done as a provided finite rich-program grammar with searched
  recipes, transfer repair, supervised learned slot semantics, and label-free
  role-token calibration plus discovered semantic-profile induction inside the
  synthetic connected-component world, plus a learned object-slot bridge in
  the synthetic fixed-slot world.
- It is not done as open-ended motor/apparatus discovery, fully unsupervised
  open-world semantics, natural-image object discovery, full slot attention,
  or full neural architecture search.
- `2B-v2` has compact motif/body validation, transfer-consuming executable
  bodies, and bounded searched executable-module contracts over the label-free
  transfer gate and the learned-object-slot/discovered-profile transfer gate,
  but not full neural module or architecture search.

## Recent Merged PRs

- PR #139: `2A-v2` held-out transfer repair plus transfer-consuming executable
  module body gate.
- PR #140: supervised learned slot-semantics repair.
- PR #141: searched finite rich-program recipe gate.
- PR #142: label-free slot-semantics transfer gate.
- PR #147: searched executable-module bodies against the label-free `2A-v2`
  transfer gate.
- PR #148: semantic-profile-discovery handoff.
- PR #151: discovered semantic-profile induction against the same held-out
  `2A-v2` transfer gate.
- PR #158: learned object-slot perception for the discovered-profile held-out
  transfer gate.
- Current branch: 2B consumption of the learned-object-slot plus
  discovered-profile held-out transfer contract.

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

### Discovered Semantic Profiles

Report:
`experiments/concerned_syntax/results/discovered_semantic_profiles_modal_2026_06_22.md`

Positive:
`discovered_semantic_world_model`

Metrics:
profile cluster purity/family/pair/action-template `1.000`, transfer gate
`1.000`, family/target/useful/rich high `1.000`, low-program `0.000`, regret
`0.004`, gate PASS across five Modal seeds at 3,000 train / 1,200 test / 90
epochs.

Rejected controls:

- `learned_rich_program_composer`: fails transfer.
- `discovered_semantic_family_only`: family `1.000`, but target/useful
  `0.214`.
- `discovered_semantic_target_only`: target `1.000`, but family/useful
  `0.143` and low-program `0.714`.
- `discovered_semantic_rich_without_concern`: family/target/useful/rich
  `1.000`, but low-program `0.714`.

Boundary:
this removes the supplied kind/profile table from the accepted agent, but the
world is still synthetic, connected-component perception is still algorithmic,
and feedback is still contract-shaped. Call it semantic-profile induction
inside the synthetic 2A-v2 world, not natural-image object discovery or fully
open-ended semantics.

### Learned Object Slots For Discovered Profiles

Report:
`experiments/concerned_syntax/results/learned_object_slots_modal_2026_06_22.md`

Positive:
`learned_object_slot_discovered_world_model`

Metrics:
slot recovery/scene recovery `1.000`, profile cluster
purity/family/pair/action-template `1.000`, transfer gate `1.000`,
family/target/useful/rich high `1.000`, low-program `0.000`, gate PASS across
five Modal seeds at 3,000 train / 1,200 test / 90 policy epochs plus 1,200
extractor-calibration images and 45 extractor epochs per seed.

Rejected controls:

- `learned_rich_program_composer`: fails held-out transfer.
- `learned_object_slot_family_only`: has family but not target/useful program.
- `learned_object_slot_target_only`: has target but not family/rich program
  and overuses low-concern programs.
- `learned_object_slot_rich_without_concern`: has family/target/useful/rich
  structure but fails low-concern discipline.

Boundary:
this removes algorithmic connected components from the accepted perception
path. It is still synthetic RGB, fixed six-slot layout, slot-local center
search, and contract-shaped feedback. Call it a learned object-slot bridge for
the synthetic 2A-v2 world, not natural-image vision or full slot attention.

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

### 2B Searched Executable Modules

Report:
`experiments/viable_computational_bodies/results/searched_executable_modules_modal_2026_06_22.md`

Positive:
`viability_guided`

Best searched body:
`component_slot_encoder+concern_gate+formal_guard+label_free_slot_inducer+program_family_router+reward_head+rich_program_composer+semantic_profile_grounder+target_binder+world_model`

Metrics:
body gate `1.000`, transfer gate `1.000`, formal validity `1.000`,
semantic kind/pair `1.000`, module coverage `1.000`,
family/target/useful/rich high `1.000`, low-program `0.000`, resource cost
`18`, gate PASS across five Modal seeds.

Rejected controls:

- `reward_only`: shortcut learned-composer body, transfer `0.000`, module
  coverage `0.111`.
- `family_proxy`: semantic/family `1.000`, but target/useful `0.214` and
  module coverage `0.444`.
- `target_proxy`: target `1.000`, but family/useful/rich `0.143` and
  low-program `0.714`.
- `ungated_rich_proxy`: family/target/useful/rich `1.000`, but transfer
  `0.000` and low-program `0.714`.

Boundary:
bounded executable-module contract search, not trainable neural architecture
search; still uses connected-component slots, a supplied semantic profile
table, and synthetic rich-program feedback.

### 2B Object-Slot Executable Modules

Report:
`experiments/viable_computational_bodies/results/object_slot_executable_modules_modal_2026_06_22.md`

Positive:
`viability_guided`

Best searched body:
`concern_gate+discovered_profile_inducer+formal_guard+learned_foreground_extractor+object_slot_centerer+profile_action_template+profile_memory+program_family_router+reward_head+rich_program_composer+target_binder+world_model`

Metrics:
object-slot body gate `1.000`, transfer gate `1.000`, formal validity
`1.000`, slot/scene recovery `1.000`, profile purity/semantic pair/action
template `1.000`, module coverage `1.000`, family/target/useful/rich high
`1.000`, low-program `0.000`, resource cost `21`, gate PASS across five Modal
seeds.

Rejected controls:

- `reward_only`: legacy shortcut body, transfer `0.000`, module coverage
  `0.000`.
- `family_proxy`: profile/family `1.000`, but target/useful `0.214` and
  module coverage `0.400`.
- `target_proxy`: target `1.000`, but family/useful/rich `0.143`,
  low-program `0.714`, and module coverage `0.500`.
- `ungated_rich_proxy`: family/target/useful/rich `1.000`, but transfer
  `0.000`, low-program `0.714`, and module coverage `0.800`.

Boundary:
bounded executable-module contract search over learned foreground slots and
discovered profiles, not trainable neural architecture search, natural-image
vision, or full slot attention.

## Most Important Files

- Main paper:
  `papers/concerned_syntax/paper.md`
- Rendered paper:
  `papers/concerned_syntax/paper.pdf`
- Public external PDF:
  `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/concerned_syntax.pdf`
- Public external 2B PDF:
  `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/2B_Viable_Computational_Bodies_2026_06_22.pdf`
- 2B paper:
  `papers/viable_computational_bodies/paper.md`
- 2B rendered paper:
  `papers/viable_computational_bodies/paper.pdf`
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
  `experiments/concerned_syntax/discovered_semantic_profiles.py`
  `experiments/concerned_syntax/learned_object_slots.py`
- 2B implementation:
  `experiments/viable_computational_bodies/learned_executable_modules.py`
  `experiments/viable_computational_bodies/searched_executable_modules.py`
  `experiments/viable_computational_bodies/modal_searched_executable_modules.py`
  `experiments/viable_computational_bodies/object_slot_executable_modules.py`
  `experiments/viable_computational_bodies/modal_object_slot_executable_modules.py`

## Next Best Move

Start from a fresh fetch/pull of `main` in a new worktree.

Recommended external branch:

```text
codex/external-contact-p1-lora-tier-b
```

Best next experiment:

Run the non-degenerate external P1 Tier-B follow-up with LoRA or full
fine-tuning on Pythia modular arithmetic. Do not repeat the frozen linear-
probe configuration that produced all-zero OOD accuracy.

Alternative strong 2B branch:

```text
codex/phase2-neural-module-search
```

Goal:
replace bounded searched executable contracts with trainable neural object-slot,
graph-binding, routed-head, and program-composition modules. Keep the
learned-object-slot/discovered-profile transfer verifier and controls; do not
call motif/contract search full neural architecture search.

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

Continue Phase 2 from freshly fetched `origin/main`. Start with
`docs/phase2_next_phase_research_handoff.md`. The internal object-slot 2B
consumption branch is now complete at bounded contract-search scale. The next
best external move is `codex/external-contact-p1-lora-tier-b`: rerun P1 on
Pythia with LoRA or full fine-tuning, not the degenerate frozen-linear probe.
The next best internal move is `codex/phase2-neural-module-search`: replace
bounded searched executable contracts with trainable neural object-slot,
graph-binding, routed-head, and program-composition modules. Keep claims
honest, use Modal for full evidence, avoid heavy local sweeps, update
paper/audit/handoff/PDFs, run checks, commit, push, PR, and merge when clean.
```
