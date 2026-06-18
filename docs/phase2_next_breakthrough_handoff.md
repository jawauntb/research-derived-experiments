# Phase 2 Next Breakthrough Handoff

Date: 2026-06-16
Repo: `jawauntb/research-derived-experiments`
Current fresh branch for this note: `codex/phase2-next-handoff`
Current `origin/main`: `8a93813` (`Merge pull request #128 from jawauntb/codex/phase2-program-body-search`)
External paper artifact folder: `/Users/jawaun/Metaphysics of Intelligence/Phase_Arc_2`

This is the start-here note for the next agent session. The user is not asking
for PR churn. The user wants Phase 2 to compound toward paper-worthy,
field-facing scientific results at least as substantive as the Phase I Metric
Stack of Concern result. Treat code, papers, citations, figures, and PRs as the
delivery machinery for the science, not the goal.

## 1. The Current Breakthrough

The current real breakthrough is not "another sweep." It is the first coupled
Arc 2A/2B contract:

```text
2A-v1-pixels-observe_pair
```

Arc 2A now has a minimal intervention-invention result: from pixel-rendered
object features, an agent learns when to intervene and which `observe_pair(a,b)`
target makes the viability-relevant hidden binding observable.

Arc 2B now consumes that empirical 2A-v1 contract: a program-body search finds a
resource-bounded motif stack that expresses the 2A concerned-program-inventor
gate while reward-only and syntax-proxy controls fail.

Do not phrase this as "2A is done" or "2B is done." Phrase it this way:

- `2A-v1` is done as a frozen minimal contract, not as the final concerned
  syntax result.
- `2B-v1` is done as a first coupled body-search result, not as full neural
  architecture search.
- 2A and 2B are already combined through the frozen empirical contract.
- The next combination is Haskell-in-the-loop body search, then `2A-v2` with a
  richer intervention language consumed by 2B.

Current accepted 2A result:

```text
report: experiments/concerned_syntax/results/intervention_invention_modal_2026_06_16.md
positive: concerned_program_inventor
parse-high: 1.000
action: 1.000
target-high: 1.000
useful-high: 1.000
low-probe: 0.156
gate: PASS across 5 Modal seeds
```

Important rejected controls:

- `target_without_concern`: target-high `1.000`, but low-probe `1.000`.
- `concern_without_target`: low-probe `0.156`, but target-high `0.088`.
- `random_program_probe`: spends budget and asks mostly wrong questions.
- `surface_program_shortcut`: keeps action prior but fails hidden binding.

Current accepted 2B result:

```text
report: experiments/viable_computational_bodies/results/program_body_search_modal_2026_06_16.md
positive: viability_guided
body gate: 1.000
empirical 2A gate: 1.000
formal valid: 1.000
target-high: 1.000
useful-high: 1.000
low-probe: 0.156
gate: PASS across 5 Modal seeds
```

Accepted searched body:

```text
calibration_guard
causal_binding_head
concern_policy
formal_guard
intervention_planner
reward_head
vector_surface_encoder
world_model
```

Important rejected controls:

- `reward_only`: shortcut body, body gate `0.000`.
- `syntax_proxy`: target/useful `1.000`, but low-probe `0.830` and body gate
  `0.000`.

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

### Milestone A: Haskell-in-Loop Program-Body Search

Suggested branch: `codex/phase2-haskell-program-body-gate`

This is the highest-leverage immediate move because it closes the biggest open
gap in the current coupled result. Python can already consume Haskell verdicts
for named learned/vector body summaries, and `ontology-check --motifs` exists,
but `program_body_search` still uses a Python/static body contract inside the
search loop.

Definition of done:

- `experiments/viable_computational_bodies/program_body_search.py` asks the
  Haskell checker for motif verdicts, or consumes cached Haskell verdicts with
  provenance.
- Modal body search records `formal_source`, `formal_valid`, `resource_cost`,
  and `formal_violations` from Haskell where available.
- The fallback path is explicit and cannot silently convert Haskell failure
  into a passing body.
- `viability_guided` still passes, and `reward_only` / `syntax_proxy` still
  fail for distinct reasons.
- The 2B paper updates its limitation from "Haskell motif verdicts are not yet
  inside the program-body search loop" to the actual result.

Allowed claim if it passes:

```text
The empirical 2A-v1 gate and an external typed motif admissibility checker are
now coupled inside the body-search loop.
```

Do not claim proof-assistant-level verification.

### Milestone B: 2A-v2 Rich Intervention Language

Suggested branch: `codex/phase2-rich-program-language`

The current `observe_pair(a,b)` result is minimal intervention invention. The
next 2A result should require composing or choosing among richer interventions:

```text
observe_pair(a,b)
move(anchor)
ablate(role)
compose(two steps)
null
```

Definition of done:

- The agent chooses a program that makes the hidden binding identifiable under
  cost.
- Low-concern probe/program use remains capped.
- Controls separate target knowledge, concern gating, random composition, and
  passive reward shortcuts.
- The report includes a mechanism trace: visible state, selected program,
  observation, belief update or parse decision, and final action.
- Modal, not the local laptop, runs the multi-seed training/sweep.

Allowed claim if it passes:

```text
The agent composes concern-gated interventions beyond pair observation, but not
yet open-ended motor programs or apparatus discovery.
```

### Milestone C: Held-Out Transfer Gates

Suggested branch: `codex/phase2-transfer-gates`

Seed stability is not enough. Turn transfer into a required gate:

- held-out role pairs,
- held-out parse families,
- held-out colors/textures/positions,
- held-out program tokens if `2A-v2` exists.

There is already a role-transfer hook in the program-body work. Treat it as a
starting point, not settled evidence. Any old local diagnostic should be treated
as a hint only; run the required stress on Modal and report failures honestly.

Definition of done:

- A transfer manifest is pre-registered.
- Main and transfer metrics are reported side by side.
- Passing i.i.d. while failing transfer weakens the claim instead of being
  hidden.
- The body search either consumes the transfer gate or explicitly freezes it as
  the next contract.

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

Start with `codex/phase2-haskell-program-body-gate`.

Reason: it turns the current best result from "2B search uses an empirical 2A
gate plus Python/static body formalism" into "2B search uses an empirical 2A
gate plus an external typed Haskell motif verifier." That is a clean,
paper-relevant regime consolidation, and it prepares the body search to consume
`2A-v2` once richer intervention programs exist.

Then run `2A-v2` and transfer gates in parallel if there are available agents or
clean Modal shards. 2B does not need to wait for 2A-v2; it can consolidate
against frozen 2A-v1 while 2A-v2 is being invented. The integration checkpoint
is when 2A-v2 has passed enough controls to become the next frozen empirical
contract.

The working rhythm:

```text
regime question -> anti-cheat gate -> minimal code -> Modal sweep
-> audit card -> gate-margin figure -> paper/PDF -> checks -> PR
-> fresh branch -> next experiment
```

Keep going until the result changes what the paper can honestly claim.
