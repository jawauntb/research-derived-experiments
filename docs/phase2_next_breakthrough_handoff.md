# Phase 2 Next Breakthrough Handoff

Date: 2026-06-22
Repo: `jawauntb/research-derived-experiments`
Start point: freshly fetched `origin/main`
Reference state when this handoff was prepared: `4398fc0`
(`Merge pull request #145 from jawauntb/codex/phase2-clean-context-handoff-sha`)
External paper artifact folder: `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2`

This is the start-here note for the next agent session. The user is not asking
for PR churn. The user wants Phase 2 to compound toward paper-worthy,
field-facing scientific results at least as substantive as the Phase I Metric
Stack of Concern result. Treat code, papers, citations, figures, and PRs as the
delivery machinery for the science, not the goal.

## 1. The Current Breakthrough

The current real breakthrough is not "another sweep." It is the first coupled
Arc 2A/2B rich-program contract, now with local transfer and executable-module
wrap gates:

```text
2A-v2-pixels-rich_programs
  + held-out role/parse transfer repair
  + executable module bodies consuming the transfer gate
```

Arc 2A now has a rich intervention-program result: from pixel-rendered object
features, an agent learns when to act, which object binding matters, and which
program family among `observe_pair`, `move_anchor`, `ablate_pair`, and
`compose_move_observe` exposes the hidden concern-relevant parse.

Arc 2B now consumes that empirical 2A-v2 contract: program-body search finds a
resource-bounded motif stack that expresses concern gating, target binding,
program-family routing, rich composition, and formal guard requirements while
reward-only and syntax-proxy controls fail.

The current branch adds the next publication-wrap gates: v2 held-out role/parse
transfer is repaired by an explicit role-equivariant rich world model across
five Modal seeds, and a compact executable-module body gate consumes that
transfer contract across five Modal seeds. That makes the result stronger, but
also sharpens the remaining boundary: these modules are explicit rather than
learned neural role semantics.

The current successor branch adds a narrower learned-semantics repair: a
supervised learned role-token prototype decoder replaces the explicit RGB role
decoder and preserves the same held-out role/parse transfer gate across five
Modal seeds with 3,000 train trials, 1,200 test trials, 1,200 semantic
calibration trials, and 90 epochs. This closes the supervised slot-semantics
boundary, but not unsupervised object discovery or open-ended program
invention.

The searched-rich successor branch then removes the named positive composer as
a supplied agent. A bounded recipe search over probe rule, program-family
selector, target selector, binding update, and action rule discovers the same
useful v2 policy across five Modal seeds. This closes finite DSL program-policy
search over the provided rich grammar, but not open-ended motor/apparatus
discovery.

The label-free slot-semantics successor branch then removes supervised
role-token calibration. It clusters connected components without visible role
labels and grounds active-cluster profiles through synthetic rich-program
feedback and action consistency. This closes label-free role-token calibration
under a supplied semantic profile table, but not fully unsupervised semantic-
profile discovery or natural-image object discovery.

Do not phrase this as "2A is done" or "2B is done." Phrase it this way:

- `2A-v2` is done as a provided-rich-grammar contract with Modal-confirmed
  searched recipes, transfer repair, supervised learned slot semantics, and
  label-free role-token calibration, not as open-ended motor/apparatus
  invention or fully unsupervised object/role semantic-profile discovery.
- `2B-v2` is done as motif search plus Modal-confirmed compact executable-
  module validation, not as full neural architecture search.
- 2A and 2B are already combined through the frozen empirical contract and the
  new transfer-consuming body gate.
- The next combination is learned object/role slots, searched/evolved
  executable module bodies, and program discovery beyond the finite DSL.

Current accepted 2A result:

```text
report: experiments/concerned_syntax/results/rich_program_language_modal_2026_06_17.md
positive: concerned_program_composer
parse-high: 1.000
action: 1.000
family-high: 1.000
target-high: 1.000
useful-program-high: 1.000
rich-program-high: 1.000
low-program: 0.162
gate: PASS across 5 Modal seeds
```

Important rejected controls:

- `target_without_family`: target-high `1.000`, but useful-high `0.000`.
- `family_without_target`: family-high `1.000`, but target-high `0.080`.
- `rich_without_concern`: rich-program high `1.000`, but low-program `1.000`.
- `surface_rich_shortcut`: avoids program use and fails hidden binding.

Current 2A transfer-wrap result:

```text
report: experiments/concerned_syntax/results/rich_program_transfer_repair_modal_2026_06_18.md
positive: role_equivariant_rich_world_model
transfer gate: 1.000
parse/action/family/target/useful/rich high: 1.000
low-program: 0.000
gate: PASS across 5 Modal seeds
```

Current learned slot-semantics result:

```text
report: experiments/concerned_syntax/results/learned_slot_semantics_modal_2026_06_18.md
positive: learned_slot_semantic_world_model
semantic kind/pair: 1.000
transfer gate: 1.000
family/target/useful/rich high: 1.000
low-program: 0.000
gate: PASS across 5 Modal seeds at 3000 train / 1200 test / 90 epochs
```

Important rejected controls:

- `learned_rich_program_composer`: transfer gate `0.000`; still fails held-out
  role/parse transfer.
- `learned_semantic_family_only`: family `1.000`, but target/useful `0.214`.
- `learned_semantic_target_only`: target `1.000`, but family/useful `0.143`
  and low-program `0.714`.
- `learned_semantic_rich_without_concern`: rich metrics `1.000`, but
  low-program `0.714`.

Current searched rich-program result:

```text
report: experiments/concerned_syntax/results/searched_rich_program_policy_modal_2026_06_18.md
positive: concerned_rich_program_search
best recipe: concern_or_calibration+learned_family+slot_scores+bind_if_useful_program+bound_action
parse/action/family/target/useful/rich high: 1.000
subtree: 0.789
low-program: 0.144
gate: PASS across 5 Modal seeds at 3000 train / 1200 test / 90 epochs
```

Important rejected controls:

- `reward_only_rich_program_search`: no programs, hidden syntax fail.
- `family_proxy_rich_program_search`: family `1.000`, but target/useful
  `0.076` and low-program `1.000`.
- `syntax_proxy_rich_program_search`: syntax/family/target/useful/rich
  `1.000`, but low-program `1.000`.

Current label-free slot-semantics result:

```text
report: experiments/concerned_syntax/results/unsupervised_slot_semantics_modal_2026_06_18.md
positive: unsupervised_slot_semantic_world_model
semantic kind/family/pair: 1.000
transfer gate: 1.000
family/target/useful/rich high: 1.000
low-program: 0.000
gate: PASS across 5 Modal seeds at 3000 train / 1200 test / 90 epochs
```

Important rejected controls:

- `learned_rich_program_composer`: transfer gate `0.000`; still fails held-out
  role/parse transfer.
- `unsupervised_semantic_family_only`: semantic kind/family/pair `1.000`, but
  target/useful `0.214`.
- `unsupervised_semantic_target_only`: semantic kind/family/pair `1.000`, but
  family/useful `0.143` and low-program `0.714`.
- `unsupervised_semantic_rich_without_concern`: semantic and rich metrics
  `1.000`, but low-program `0.714`.
- Boundary: this removes supervised role-token labels, but still uses a
  supplied semantic profile table and synthetic rich-program feedback.

Current accepted 2B result:

```text
report: experiments/viable_computational_bodies/results/rich_program_body_search_modal_2026_06_18.md
positive: viability_guided
body gate: 1.000
empirical 2A gate: 1.000
formal valid: 1.000
family/target/useful/rich high: 1.000
low-program: 0.168
gate: PASS across 5 Modal seeds
```

Accepted searched body:

```text
calibration_guard
causal_binding_head
concern_policy
formal_guard
intervention_planner
program_family_head
reward_head
rich_program_composer
vector_surface_encoder
world_model
```

Important rejected controls:

- `reward_only`: shortcut body, body gate `0.000`.
- `syntax_proxy`: family/target/useful/rich `1.000`, but formal validity
  `0.200`, low-program `0.670`, and body gate `0.000`.

Current executable-module body result:

```text
report: experiments/viable_computational_bodies/results/learned_executable_modules_modal_2026_06_18.md
positive: transfer_repaired_executable_body
transfer gate: 1.000
module coverage: 1.000
family/target/useful/rich high: 1.000
low-program: 0.000
gate: PASS across 5 Modal seeds
```

## 2. The North Star

The Phase I Metric Stack of Concern showed a measurable correction chain:

```text
viability prediction -> maintained concern -> self/world attribution
-> costly null probes -> correction -> re-engagement
```

Phase 2 should now show that maintained concern also organizes the grammar of
the world and the grammar of the agent's computational body:

```text
world syntax under concern:
  perception -> causal constituency -> intervention invention

body syntax under viability:
  motif grammar -> formal/resource admissibility -> empirical 2A competence

combined claim:
  concern selects what distinctions matter, which experiments expose them,
  and which body organizations can stably exploit them without becoming
  shortcut-driven or restless.
```

The audacious field-facing goal is not "our agent scores higher." It is:

```text
maintained concern is a discovery pressure that shapes representation,
experiment selection, and computational morphology under explicit anti-cheat
and formal gates.
```

## 3. Researcher-Lens Critique

Use this lens before coding:

- Hostile reviewer: what shortcut would make the headline score meaningless?
- Sutton/Silver: what improves with experience and scalable compute, rather
  than hand-designed examples?
- Pearl/Scholkopf/Bengio: did the agent choose interventions that distinguish
  mechanisms, or merely predict passively?
- Chollet/Lake: is there held-out composition, or only i.i.d. seed stability?
- CausaLab/AI-scientist: is there a faithful trajectory of hypothesis,
  program, observation, belief update, and action?
- Feynman/reviewer: can the strongest almost-working baseline be made to fail
  before the positive result is celebrated?

If an experiment cannot answer one of those critiques, it is probably only a
diagnostic improvement, not a breakthrough.

## 4. Best Next Milestones

### Milestone A: Modal-Visible Haskell Provenance

Suggested branch: `codex/phase2-modal-haskell-provenance`

The local Haskell-in-loop gap is closed for 2A-v1 motif search, and the Haskell
ontology has been extended for rich v2 motifs. The remaining provenance gap is
Modal: rich-program body search still records explicit `python_static`
provenance when Cabal is unavailable in the image.

Definition of done:

- Modal body search either includes Cabal/Haskell in its image or consumes a
  tracked Haskell verdict cache with a manifest.
- Modal body reports record `formal_source = "haskell"` for accepted bodies,
  not only local reports.
- The fallback path is explicit and cannot silently convert Haskell failure
  into a passing body.
- `viability_guided` still passes, and `reward_only` / `syntax_proxy` still
  fail for distinct reasons.

Allowed claim if it passes:

```text
The empirical 2A-v2 gate and an external typed motif admissibility checker are
coupled inside the Modal body-search loop with visible provenance.
```

Do not claim proof-assistant-level verification.

### Milestone B: Program Discovery Beyond the Provided Grammar

Suggested branch: `codex/phase2-open-program-search`

The provided rich grammar is now passed. The next 2A result should discover or
search program recipes rather than merely selecting among known families:

```text
observe_pair(a,b)
move_anchor(anchor)
ablate_pair(a,b)
compose_move_observe(anchor,a,b)
new searched or evolved recipes
null
```

Definition of done:

- The agent discovers, searches, or evolves a program recipe that makes the
  hidden binding identifiable under cost.
- Low-concern probe/program use remains capped.
- Controls separate memorized recipe selection, random composition, target
  knowledge, concern gating, and passive reward shortcuts.
- The report includes a mechanism trace: visible state, selected/generated
  program, observation, belief update or parse decision, and final action.
- Modal, not the local laptop, runs the multi-seed training/sweep.

Allowed claim if it passes:

```text
The agent searches concern-gated intervention programs beyond a fully provided
grammar, but not yet open-ended continuous motor control or apparatus discovery.
```

### Milestone C: Modal Confirmation of Transfer-Consuming Bodies

Suggested branch: `codex/phase2-wrap-gate-modal-confirmation`

Seed stability is not enough. The current branch adds Modal-confirmed v2
held-out role/parse transfer repair and a Modal-confirmed executable-module
body gate that consumes it. The next evidence upgrade is learned semantics and
searched modules:

- held-out role pairs,
- held-out parse families,
- held-out colors/textures/positions,
- transfer-consuming executable module bodies.

Treat local diagnostics as real gate-development evidence, not final paper
evidence. Run the required stress on Modal and report failures honestly.

Definition of done:

- A transfer manifest is pre-registered.
- Main and transfer metrics are reported side by side.
- Passing i.i.d. while failing transfer weakens the claim instead of being
  hidden.
- The body gate consumes the transfer gate, and partial bodies fail for
  interpretable missing-module reasons.

### Milestone D: Learned Object Slots

Suggested branch: `codex/phase2-learned-object-slots`

Connected components are a useful bridge, but not the final perception story.
The next perception step should replace algorithmic extraction with a learned
object-slot/CNN/slot-attention-style extractor, trained and swept on Modal.

Definition of done:

- The image renderer remains parse-invariant.
- The learned extractor has an object recovery metric and a downstream syntax
  metric.
- Surface and passive baselines still fail hidden binding.
- Do not claim natural-image vision. This is a learned object extraction gate
  on a synthetic rendered world.

### Milestone E: Figure Upgrade Pass

Suggested branch: `codex/phase2-paper-figures`

Do this whenever a scientific result stabilizes. A result is not paper-ready if
the chart only shows a happy positive bar. The figures must make the controls
fail visibly.

## 5. Modal-First Compute Rules

The user is doing other local work. Do not use the user's CPU or memory for
heavy science when Modal exists.

Local is allowed for:

- `rg`, `sed`, `git diff`, `git status`, small file reads;
- unit tests, lint, type checks, publication guard;
- tiny import or CLI smoke checks;
- Haskell compile/test when the task touches Haskell;
- figure generation and PDF rendering/inspection.

Local is not allowed for:

- multi-seed sweeps;
- neural training;
- CNN/object-slot experiments;
- architecture/body search;
- larger image/pixel experiments;
- "just to see" training runs when a Modal entrypoint exists or can be created.

Use this Modal pattern:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_intervention_invention_sweep.py \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

For 2B:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/viable_computational_bodies/modal_program_body_search.py \
  --generations 24 --population 24 \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

New Modal scripts should:

- use Python 3.12;
- mount the local `experiments` package with `add_local_python_source`;
- shard seeds/generations/training runs remotely;
- write raw JSON to ignored `artifacts/...`;
- write public summaries to `experiments/.../results/...md`;
- include enough manifest data to reproduce the sweep;
- make controls first-class, not afterthoughts.

Parallelization rule:

- Use `multi_tool_use.parallel` for independent local reads.
- Use Modal starmap/remote functions for seed shards and body-search shards.
- If multi-agent tools are available in a future session, split literature,
  method, anti-cheat, implementation, and paper/report streams. If they are not
  available, simulate those streams with separate notes and parallel reads.

## 6. Charts and Paper PDFs

The papers need publication-grade figures, not decorative screenshots.

Preferred figure type:

```text
gate-margin heatmap
```

Why: it shows how far each agent/control is above or below each acceptance
threshold, and it makes anti-cheat failures legible.

Figure rules:

- Show accepted model and negative controls in the same figure.
- Plot margin-to-threshold, not only raw scores.
- For metrics where lower is better, such as low-probe rate, invert the margin.
- Annotate raw values in cells or labels.
- Use consistent model/control names across report, chart, and paper.
- Keep the table first, figure second, prose third. The figure should explain
  the table, not replace it.
- Do not use a one-note color story that hides failures. The failed controls
  should be visually obvious.
- Add a caption that states what the control failure proves.

Local figure generation is acceptable because it is light:

```bash
uvx --python 3.12 --with matplotlib python scripts/make_phase2_step4_figures.py
```

If adding a new figure script, keep it deterministic and save under the paper's
`figures/` directory.

After paper markdown changes, render PDFs:

```bash
uvx --from markdown-pdf python scripts/render_paper_pdf.py \
  --in papers/concerned_syntax/paper.md \
  --out papers/concerned_syntax/paper.pdf \
  --title 'Constituency Tests for Concerned Representation in Minimal Agents' \
  --author 'Jawaun Brown'

uvx --from markdown-pdf python scripts/render_paper_pdf.py \
  --in papers/viable_computational_bodies/paper.md \
  --out papers/viable_computational_bodies/paper.pdf \
  --title 'Viability-Guided Evolution of Syntax-Bearing Computational Bodies' \
  --author 'Jawaun Brown'
```

Then visually inspect rendered pages. Do not trust markdown rendering alone:

```bash
mkdir -p /tmp/phase2_pdf_check
pdftoppm -png -r 160 papers/concerned_syntax/paper.pdf /tmp/phase2_pdf_check/2a
pdftoppm -png -r 160 papers/viable_computational_bodies/paper.pdf /tmp/phase2_pdf_check/2b
```

Finally copy public PDFs to:

```text
/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2/
```

## 7. Citation and Research Gathering

Before any new field-facing claim, browse or otherwise verify current primary
sources. Do not trust model memory for 2026 research context.

Use primary sources:

- arXiv abstract/PDF pages,
- OpenReview,
- DOI landing pages,
- official project pages,
- official docs for tools such as Modal.

Avoid secondary summaries unless they only help discover the primary source.

Update `references/SOURCES.md` only when a source changes one of:

- method design,
- baseline/control,
- anti-cheat warning,
- terminology,
- claim boundary,
- limitation wording.

Do not pad citations. Every cited source in a paper should be used in the
argument. Good citation locations:

- benchmark motivation,
- baseline/control definition,
- anti-cheat explanation,
- mechanism-trace motivation,
- limitation/claim boundary.

Existing literature bearings:

- Revencu, Pajot, and Dehaene for geometric shape syntax and constituency.
- Active Causal Experimentalist (ACE) for learned sequential intervention
  design.
- CausaLab for mechanism-trajectory fidelity.
- A-CBO and active causal-discovery critiques for why passive prediction is
  insufficient.
- Causal-JEPA and object-centric causal representation work for latent object
  intervention framing.
- Neural architecture search and neuro-symbolic reasoning for body-search
  contrasts.

Before writing "novel," search the nearest prior task and state the exact delta:

```text
Prior work: active causal discovery over interventions.
Delta here: concern-gated intervention selection under hidden syntactic
constituency, with a low-concern no-restless constraint and a body-search
contract.
```

## 8. Discovery-Regime Audit

Use `scientific-discovery-regime-audit` for every real experiment. Each result
should include:

- current regime,
- new artifact type or operation,
- positive target,
- negative controls,
- stress tests,
- acceptance gate,
- withheld/rejected artifacts,
- accepted artifacts,
- residual content,
- retractions or supersessions,
- next move.

Use `ce-compound` when a non-obvious process lesson emerges. Example lessons
worth compounding:

- Haskell should own typed admissibility while Python owns empirical sweeps and
  Modal reports.
- A body search is not meaningful unless it consumes the same empirical gate
  that the paper claims.
- Intervention availability is not intervention invention.

## 9. Claim Guardrails

Safe current claims:

- Arc 2A has symbolic, learned candidate-parse, vector, pixel, and minimal
  program-selection gates that separate concerned syntax from reward,
  passive prediction, random/restless probing, target-only selection, and
  concern-only probing.
- Arc 2B has body search that consumes the current empirical 2A-v1 program gate
  and rejects reward-only and syntax-proxy controls.
- Haskell typed ontology is operational and already consumable by Python in
  named body summaries, but not yet inside the program-body search loop.

Do not claim:

- human cognition evidence,
- neural evidence,
- natural-image vision,
- open-ended motor-program discovery,
- full neural architecture search,
- proof-assistant verification,
- that target selection alone equals concern,
- that concern gating alone equals intervention invention,
- that action accuracy equals syntax,
- that formal validity equals behavioral competence.

## 10. Fresh-Branch Workflow

The repo rule is strict:

```bash
git fetch origin main --prune
git switch -c codex/<task-name> origin/main
```

Always work from a fresh `origin/main` branch. Do not work on a stale local
branch. Run quality checks before committing.

General check:

```bash
python3 scripts/run_quality_checks.py
```

If touching Haskell:

```bash
(
  cd formal/ontology-hs && cabal test all && cabal run ontology-check
)
```

If touching papers:

- render the affected PDFs,
- inspect rendered PNG pages,
- copy public PDFs to the external Phase Arc 2 folder.

When done:

- commit,
- push,
- open a PR,
- merge if instructed or if the workflow expects it,
- continue the science from the new `main` rather than stopping at the PR.

## 11. Best Starting Move for the Next Agent

Start with a 2B searched/evolved module branch or a stricter semantic-profile
discovery branch.

Reason: the current branch lands Modal-confirmed label-free role-token
calibration under a supplied semantic profile table. The next scientific gap is
not another seed sweep; it is fully unsupervised semantic-profile discovery,
open-ended motor/apparatus discovery beyond the finite DSL, or searched/evolved
executable modules under 2B.

Then move to searched/evolved executable modules under 2B, keeping the
Modal-first rule and the same transfer gate as a required contract.

The working rhythm:

```text
regime question -> anti-cheat gate -> minimal code -> Modal sweep
-> audit card -> gate-margin figure -> paper/PDF -> checks -> PR
-> fresh branch -> next experiment
```

Keep going until the result changes what the paper can honestly claim.
