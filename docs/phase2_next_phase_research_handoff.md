# Phase 2 Next-Phase Research Handoff

Date: 2026-06-22
Repo: `jawauntb/research-derived-experiments`
Internal branch prepared from fresh `origin/main`:
`codex/phase2-object-slot-2b-consumption`

External-contact synthesis note:
commit `79206fa` was fetched from
`origin/claude/geometric-research-review-58ztl1`, not from `origin/main`, at
the time this handoff was written. Its paper is
`papers/external_contact_synthesis/paper.md` on that branch.

## The Short Version

The research program is not stuck. It is in the harder, better phase where
previous broad claims are being forced through external contact and scaffold
removal. Some claims now pass cleanly, some narrow sharply, and some fail as
tooling rather than science. That is progress.

The current internal Phase 2 lane has been turning the Concerned Shape Grammar
from a hand-coded diagnostic into a stacked transfer contract:

```text
pixels -> object slots -> causal pair -> program family -> intervention
-> bound/unbound parse evidence -> concern-gated action
```

The newest internal step in this branch is 2B consumption of the learned
object-slot + discovered-profile transfer contract. It makes bounded
executable body search track the latest 2A scaffold-removal path rather than
the older label-free supplied-profile abstraction, while keeping the synthetic
renderer, fixed six-slot layout, slot-local center search, bounded module
grammar, and contract-shaped feedback as explicit scaffolds.

The newest external-contact step is the synthesis paper at commit `79206fa`.
It says the program has one clean external pillar, one narrowed but real
uncertainty/corruption claim, one substrate-sensitive concept-geometry result
with a cross-family falsification, and one P1 tooling block that still needs
LoRA.

## What Just Changed Internally

The learned-object-slot dependency adds:

```text
experiments/concerned_syntax/learned_object_slots.py
experiments/concerned_syntax/modal_learned_object_slots_sweep.py
experiments/concerned_syntax/results/learned_object_slots_local_2026_06_22.md
experiments/concerned_syntax/results/learned_object_slots_modal_2026_06_22.md
```

This branch then adds:

```text
experiments/viable_computational_bodies/object_slot_executable_modules.py
experiments/viable_computational_bodies/modal_object_slot_executable_modules.py
experiments/viable_computational_bodies/results/object_slot_executable_modules_local_2026_06_22.md
experiments/viable_computational_bodies/results/object_slot_executable_modules_modal_2026_06_22.md
```

The accepted path is:

1. Generate RGB pixel examples without running connected components.
2. Train one learned foreground pixel classifier per seed.
3. Use fixed slot-local center search to produce six learned object slots.
4. Induce anonymous semantic profiles from learned slots using candidate-family
   success, bound/unbound utility gaps, and action templates.
5. Run the same held-out role-kind and true-parse transfer verifier used by
   the discovered semantic-profile result.

The accepted path does not call the algorithmic connected-component extractor.

Local smoke evidence:

```text
report: experiments/concerned_syntax/results/learned_object_slots_local_2026_06_22.md
train/test: 90/40 per held-out slice
profile induction: 500 calibration examples
extractor calibration: 500 images
extractor epochs: 10
policy epochs: 10
slot recovery: 1.000
scene recovery: 1.000
profile purity/family/pair/action-template: 1.000
accepted agent: learned_object_slot_discovered_world_model
transfer gate: PASS
family/target/useful/rich high: 1.000
low-concern program rate: 0.000
```

Modal evidence:

```text
modal run experiments/concerned_syntax/modal_learned_object_slots_sweep.py
seeds: 20260622, 1729, 4242, 8675309, 314159
train/test: 3000/1200 per held-out slice/seed
profile induction: 1200 calibration examples/seed
extractor calibration: 1200 images/seed
extractor epochs: 45
policy epochs: 90
report: experiments/concerned_syntax/results/learned_object_slots_modal_2026_06_22.md
slot recovery: 1.000
scene recovery: 1.000
profile purity/family/pair/action-template: 1.000
accepted agent: learned_object_slot_discovered_world_model
transfer gate: 1.000
family/target/useful/rich high: 1.000
low-concern program rate: 0.000
mean regret: 0.004
```

Interpret the result carefully:

- The allowed claim is that discovered semantic profiles no longer depend on
  algorithmic connected-component features in the synthetic fixed-slot 2A-v2
  world.
- Do not call this natural-image object discovery.
- Do not call this full slot attention.
- Do not call this open-ended semantics.
- The fixed six-slot layout, synthetic renderer, and contract-shaped feedback
  remain scaffolds.

2B consumption evidence:

```text
modal run experiments/viable_computational_bodies/modal_object_slot_executable_modules.py
seeds: 20260622, 1729, 4242, 8675309, 314159
generations/population: 18/18
train/test: 3000/1200 per held-out slice/seed
profile induction: 1200 calibration examples/seed
extractor calibration: 1200 images/seed
extractor epochs: 45
policy epochs: 90
report: experiments/viable_computational_bodies/results/object_slot_executable_modules_modal_2026_06_22.md
accepted strategy: viability_guided
accepted body: concern_gate+discovered_profile_inducer+formal_guard+learned_foreground_extractor+object_slot_centerer+profile_action_template+profile_memory+program_family_router+reward_head+rich_program_composer+target_binder+world_model
object-slot body gate: 1.000
transfer gate: 1.000
slot/scene recovery: 1.000
profile purity/semantic pair/action-template: 1.000
module coverage/formal validity: 1.000
family/target/useful/rich high: 1.000
low-concern program rate: 0.000
```

Interpret the 2B result carefully:

- The allowed claim is that bounded executable body search can consume the
  learned-object-slot + discovered-profile 2A-v2 contract in the synthetic
  fixed-slot world.
- Do not call this trainable neural architecture search.
- Do not call this natural-image perception or full slot attention.
- The synthetic renderer, fixed slot layout, slot-local center search, finite
  module grammar, and contract-shaped feedback remain scaffolds.

## Current Internal Phase 2 Ledger

### 2A: Concerned Syntax And Intervention Programs

The strongest internal 2A chain is now:

```text
rich_program_language_modal_2026_06_17.md
searched_rich_program_policy_modal_2026_06_18.md
rich_program_transfer_repair_modal_2026_06_18.md
learned_slot_semantics_modal_2026_06_18.md
unsupervised_slot_semantics_modal_2026_06_18.md
discovered_semantic_profiles_modal_2026_06_22.md
learned_object_slots_modal_2026_06_22.md
```

What this supports:

- A finite rich intervention-program grammar can be learned/searched well
  enough to pass the transfer gate.
- Held-out role-kind and parse-family transfer are explicit.
- Explicit role decoding is not required once supervised learned slot
  semantics are added.
- Visible role-token labels are not required once label-free slot calibration
  is added.
- A supplied semantic profile table is not required once profiles are induced
  from intervention/outcome/action traces.
- Algorithmic connected components are not required for the learned object-slot
  discovered-profile transfer gate.

What this does not support:

- Natural-image perception.
- Open-ended motor or apparatus invention.
- Open-world semantic discovery.
- Full neural architecture search.
- A claim that "2A is done."

### 2B: Viable Computational Bodies

The current 2B chain is:

```text
program_body_search_modal_2026_06_16.md
rich_program_body_search_modal_2026_06_18.md
learned_executable_modules_modal_2026_06_18.md
searched_executable_modules_modal_2026_06_22.md
object_slot_executable_modules_modal_2026_06_22.md
```

What this supports:

- Body/motif search can consume the empirical 2A-v1 and 2A-v2 contracts.
- Bounded executable module contracts can pass formal validity, module
  coverage, transfer, family, target, useful-program, rich-program, and
  low-concern discipline gates.
- 2B body search can consume the newest learned-object-slot +
  discovered-profile 2A contract at bounded contract-search scale.
- Reward-only, family-proxy, target-proxy, and ungated-rich bodies fail in
  diagnostic ways.

What remains open:

- Replace compact searched module contracts with trainable neural modules.
- Open-ended motor/apparatus discovery beyond the finite rich-program DSL.

## Current External-Contact Ledger

The external synthesis paper at `79206fa` organizes the first serious contact
with public systems the lab did not build. Treat this as a separate branch
until it lands on `main`.

### P2b: Clean External Pass

Report:

```text
experiments/external_contact/results/p2_uncertainty_2026_06_22.md
```

Claim:

```text
current error != value of probing
```

External basis:

- Kirsch 2019 BatchBALD vs naive/top-k BALD.
- 5 of 5 published comparisons land on the predicted side.
- This is the cleanest external field-claim-class result in the program.

Allowed claim:

```text
The methodological correction transfers externally: acquisition value is not
captured by current error alone.
```

### P2a Tier-B: Narrowed But Real

Report:

```text
experiments/external_contact/results/p2_tier_b_2026_06_22.md
```

Original broad claim:

```text
uncertainty decouples from error under shift
```

Result:

- Predictive entropy stays correlated with error at about +0.39 to +0.44 even
  under severe shift. Literal P2a is refuted for entropy.
- Ensemble variance collapses on heavy defocus blur.
- `var_pred_class` reaches the textbook false-calm signature at severity 4
  defocus blur, with Pearson r = -0.017 while accuracy drops to 0.340.
- Variance does not collapse on brightness or gaussian noise.

Sharper allowed claim:

```text
Ensemble variance, not predictive entropy, decouples from error on blur-class
shift, not on noise/brightness shift.
```

### P3: Within-Family Pass, Cross-Family Falsification

Reports:

```text
experiments/external_contact/results/p3_glove_2026_06_22.md
experiments/external_contact/results/p3_three_family_2026_06_22.md
```

GloVe within-family passes:

```text
margin: 0.106
NMI: 0.531
paraphrase gap: 0.252
GloVe-300d vs GloVe-100d RSA: 0.747
```

Three-family result:

```text
GloVe-300d vs GloVe-100d RSA: 0.747
GloVe-300d vs fastText-300d RSA: 0.543
GloVe-100d vs fastText-300d RSA: 0.346
min pairwise RSA: 0.346
threshold: 0.600
verdict: FAIL
```

Allowed claim:

```text
The lab's concept geometry survives inside one external embedding family and
partially in a second, but the substrate-independent Platonic-convergence
reading is not supported by the three-family panel.
```

### P1: Linear-Probe Tier-B Degenerated

Report:

```text
experiments/external_contact/results/p1_pythia_2026_06_22.md
```

Result:

- 27 of 27 cells have OOD accuracy 0.0.
- The frozen Pythia hidden-state plus linear-head setup memorizes train pairs
  and does not extrapolate modular arithmetic.
- The P1 weakness-to-OOD threshold is not meaningfully evaluable in this
  linear-probe configuration.

Allowed claim:

```text
P1 is unsettled. Linear probing on frozen Pythia is a degenerate
operationalization; the next real test is LoRA or full fine-tuning.
```

## Are We Stuck?

No. The program is leaving the "everything passes in our toy world" phase and
entering the "which parts survive contact, transfer, and scaffold removal"
phase.

What feels like stuckness is actually three useful pressures:

1. Internal scaffolds are being removed one by one, and the remaining scaffolds
   are finally visible enough to name.
2. External results are narrowing claims instead of merely confirming them.
3. The next steps require choosing between synthesis, stronger external field
   claims, or deeper internal mechanism work.

The right mental model is:

```text
not: "we need one more positive table"
but: "we need the next result to change the allowed claim boundary"
```

## Best Next Moves

### 1. Land The Stacked Internal Branches

Do this first if PR #158 and this stacked 2B branch are still open. Together
they close learned object-slot perception for discovered profiles and 2B
consumption of that newest 2A contract at bounded contract-search scale.

Definition of done:

- Modal report is written.
- Audit card is updated.
- Concerned Syntax and 2B papers state the new claim boundaries.
- PDFs are rendered and visually checked.
- Clean-context and next-breakthrough handoffs point to this note.
- Checks pass, commit, push, PR, merge if clean.

### 2. External P1 LoRA Tier-B

Suggested branch:

```text
codex/external-contact-p1-lora-tier-b
```

Question:

```text
Does weakness predict OOD generalization when Pythia is allowed to actually
learn the modular-shift task through LoRA?
```

Why this is the highest-ceiling external follow-up:

- P2b is already clean.
- P2a is already narrowed.
- P3 has a useful falsification.
- P1 remains the big unresolved external field-claim candidate.

Guardrails:

- Do not rerun the linear-probe setup and expect new science.
- Use LoRA or full fine-tuning.
- Preserve wrong-group controls and classical predictors.
- Treat degeneration or all-zero OOD as a tooling result, not a claim
  falsification.

### 3. Internal Neural Module Search

Suggested branch:

```text
codex/phase2-neural-module-search
```

Question:

```text
Can 2B replace bounded searched executable contracts with trainable neural
object-slot, graph-binding, routed-head, and program-composition modules while
preserving the same held-out transfer and control gates?
```

Why this is good:

- It attacks the main remaining internal 2B scaffold.
- It can reuse the object-slot/discovered-profile transfer gate from this
  branch.

Guardrails:

- Do not call bounded contract search neural architecture search.
- Preserve reward-only, family-only, target-only, and ungated-rich controls.
- Keep formal/module coverage explicit even when modules become trainable.

### 4. P2 Tier-B Corruption Extension

Suggested branch:

```text
codex/external-contact-p2-corruption-extension
```

Question:

```text
Does the variance/error decoupling generalize across blur corruptions, or is
defocus blur special?
```

Why this is good:

- It turns the sharpened P2a claim into a taxonomy.
- It is cheaper than P1 LoRA.
- It could harden the publishable sub-claim around blur-class shift.

### 5. Discovery-EWS v2

Suggested branch:

```text
codex/discovery-ews-v2-structured-provenance
```

Question:

```text
Can the audit metric stop scoring honest "rejected/refuted" prose as a
failure signal?
```

Why this matters:

- The v1 regex is now repeatedly misfiring on positive-discipline language.
- Do not patch the regex to make the current result look better.
- Emit structured JSON sidecars for gate verdicts and claim tier, then score
  from those records.

## Claim Boundaries For The Next Agent

Use these phrasings:

- "Semantic-profile induction inside a synthetic fixed-slot world."
- "Learned object-slot bridge for 2A-v2, not natural-image vision."
- "2B bounded executable-module search now consumes the learned-object-slot +
  discovered-profile transfer contract."
- "External P2b is a clean methodological correction."
- "P2a narrows to ensemble variance plus blur-class shift."
- "P3 is substrate-sensitive; cross-family Platonic convergence is not
  supported."
- "P1 linear-probe degenerated; LoRA remains the real test."

Avoid these phrasings:

- "2A is solved."
- "2B is solved."
- "Fully unsupervised semantic discovery."
- "Natural-image object discovery."
- "Substrate-independent concept convergence."
- "Uncertainty generally fails under shift."
- "P1 was falsified."

## Copy-Paste Kickoff Prompt

Use this if starting a new agent after this branch lands:

```text
Start from fresh `origin/main` in `jawauntb/research-derived-experiments`.
Read:
- `docs/phase2_next_phase_research_handoff.md`
- `docs/phase2_clean_context_handoff.md`
- `docs/phase2_next_breakthrough_handoff.md`
- `docs/discovery_regime_audit.md`

First verify whether PR #158 and the object-slot 2B branch landed. If they did,
read:
- `experiments/concerned_syntax/results/learned_object_slots_modal_2026_06_22.md`
- `experiments/viable_computational_bodies/results/object_slot_executable_modules_modal_2026_06_22.md`
- `experiments/concerned_syntax/learned_object_slots.py`
- `experiments/viable_computational_bodies/object_slot_executable_modules.py`

Then choose one next move:

1. External route:
   create `codex/external-contact-p1-lora-tier-b` and rerun P1 on Pythia with
   LoRA or full fine-tuning, not the degenerate frozen-linear setup. Preserve
   wrong-group controls, classical predictors, and the pre-registered
   weakness/OOD thresholds.

2. Internal 2B route:
   create `codex/phase2-neural-module-search` and replace bounded searched
   executable contracts with trainable neural object-slot, graph-binding,
   routed-head, and program-composition modules. Preserve the object-slot
   transfer gate and reward/family/target/ungated controls.

3. External P2 route:
   create `codex/external-contact-p2-corruption-extension` and extend P2
   Tier-B to the full Hendrycks corruption set, especially blur families, to
   test whether the variance/blur finding generalizes.

Use local work only for smoke tests. Run full evidence on Modal. Update the
audit ledger, relevant papers, rendered PDFs, and handoffs. Run `git diff
--check`, publication guard, ruff, ty, and targeted tests before commit. Push,
open a PR, and merge only when clean.
```
