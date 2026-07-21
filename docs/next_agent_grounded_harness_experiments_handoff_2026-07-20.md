---
title: Grounded Harness Build and Experiment Handoff
type: feat
date: 2026-07-20
artifact_contract: ce-handoff/v1
artifact_readiness: implementation-ready
execution: code-and-experiments
repository: jawauntb/research-derived-experiments
audited_base: abc535f7c3b5226ed33efa0c104d3b830ae014c1
resume_focus: D2 live-agent pilot and public replay
---

# Grounded Harness Build and Experiment Handoff

> Start every tranche from a fresh fetch of `origin/main` and an isolated
> worktree. Do not edit the primary checkout or work directly on `main`.
>
> Audited baseline: `main` at `abc535f7`, after PRs #378–#382 merged on
> 2026-07-20. There were no open pull requests at the audit.
>
> Human director: Jawaun Brown. Agent-generated code, results, and papers remain
> under his direction and review.

## Mission

Move the grounded-harness portfolio from deterministic mechanism fixtures to
the first credible live-agent pilot, while producing a commercially legible
demo and the data substrate required for publishable causal attribution.

The immediate target is not all four confirmatory papers. It is one shared D2
evidence slice:

1. two real task families with machine-checkable outcomes;
2. a declared live model behind a provider-neutral adapter;
3. Grounded Statechart and Constraint Transport comparisons at matched budgets;
4. repeated stochastic runs, no-op replay characterization, row-level data,
   and 95% confidence intervals;
5. one two-minute failure replay that distinguishes observed events from
   inferred causal credit; and
6. sealed failures that can become the first non-synthetic Counterfactual
   Harness Search dataset.

This order delivers the fastest useful artifact first and makes the flagship
research possible without manufacturing a disconnected benchmark.

## Audited State

| Surface | What is on `main` | Honest boundary |
|---|---|---|
| Shared runtime | Typed append-only events, serialized pre-verification checkpoint, exact no-op replay, and one-component replay enforcement | Deterministic only |
| Grounded Statecharts | G0 self-report versus G3 artifact-digest guard; false completion is repaired before commit | One missing-artifact fixture; GS1–GS6 open |
| Constraint Transport | Two machine-checkable families, depths 1–4, hash-linked typed lineage, capability narrowing, tamper controls, and external effect/commit guards | Controlled summary-loss diagnostic; CT1–CT6 open |
| Counterfactual Harness Search | Six injected single-surface faults, isolated repair/placebo replays, exact attribution, and equal seven-evaluation trace baseline | Synthetic-identifiable; CHS1–CHS6 open |
| Harness Unlearning | Descendant-aware causal-use gate, quarantine/retirement, shift recovery, recurrence, and reactivation | One deterministic tool-schema shift; HU1–HU7 open |
| Public explanation | Four static HTML replays and compact committed result bundles | No unified two-minute live failure replay |
| Live evaluation | None | No population, stochastic, provider, OOD, or commercial claim |

The deterministic foundation is therefore complete enough to stop adding
toy-only breadth. The next unresolved question is whether the mechanisms help
real agents without merely increasing refusal, cost, or benchmark leakage.

## Discovery-Regime Audit

### Current regime

The repository can prove mechanism identity: restore a checkpoint, change one
declared harness component, enforce typed constraints, and observe the expected
path change on controlled fixtures.

### Proposed transition

Demonstrate that the same typed interventions produce stable, useful effects
over stochastic live-agent episodes and held-out tasks. The new artifact is not
another fixture; it is a paired empirical distribution with replay-integrity,
budget, uncertainty, and provenance receipts.

### Search versus discovery

- Prompt, threshold, and graph tuning on the existing fixtures is search within
  the current regime.
- Adding a model adapter or viewer is enabling infrastructure, not a scientific
  result.
- A transition occurs only if independent guards or typed transport improve a
  held-out behavioral outcome at matched budget and survive the relevant nulls.
- Counterfactual Harness Search becomes a causal result only when sealed fault
  labels and matched placebo interventions support attribution beyond a strong
  non-interventional baseline.

### Smallest breaking experiment

Run two task families, 12 held-out tasks per family, three stochastic repeats,
and the frozen core conditions below on one declared model. This is a D2 pilot,
not a powered confirmatory study. Use results only to estimate variance, reject
broken mechanisms, and design the D3 sample size.

Task families:

1. **Artifact completion:** produce or modify a local artifact subject to fresh
   executable checks. The tempting failure is reporting completion from stale,
   partial, or irrelevant evidence.
2. **Recursive constrained tool use:** delegate a task while preserving an
   approval, evidence, or capability constraint. A compliant non-refusal path
   must exist and be machine-checkable.

Core conditions:

1. direct agent loop with final self-report;
2. explicit statechart with G0 self-guard;
3. statechart with the relevant G3 executable guard;
4. typed constraint envelope without external effect guard;
5. typed constraint envelope with external delegation and commit guards;
6. matched wrong-edge or wrong-evidence guard.

Add exact no-op, matched-cost random intervention, and passive-log controls to
the episodes where they apply. Hold the base model, task, tool snapshot, call
ceiling, and primary token/tool budget fixed within each paired comparison.

### Pilot pass gate

The D2 slice passes only when all of the following hold:

- every row validates against the public schema and has resolvable manifest,
  task, checkpoint, artifact, and result hashes;
- deterministic fixture parity remains byte-stable;
- no-op replay differences remain inside a pre-registered stochastic tolerance,
  or the analysis explicitly models the observed replay variance;
- G3 guards directionally reduce false completion without more than a frozen
  10 percentage-point loss in raw task success;
- typed envelopes plus external guards directionally improve zero-violation
  joint success over both prose and envelope-only controls;
- the wrong-edge/wrong-evidence and matched-cost controls do not receive the
  candidate mechanism's credit;
- task-level paired effects and 95% intervals are published, with repeats nested
  under tasks rather than counted as independent samples;
- all integrity gates pass before any scientific metric is interpreted.

If no-op replay is too unstable for paired attribution, stop CHS escalation and
publish a replay-variance characterization. If guards improve safety only by
blocking valid tasks, stop the product claim and investigate useful autonomy.

## Dependency-Ordered Work

### Tranche 1 — Shared live-evaluation contract

Build this first because every later experiment consumes it.

Required outcome:

- a provider-neutral executor interface with a deterministic fixture adapter
  and one opt-in live adapter;
- no provider import, API key, network call, or unrestricted raw transcript in
  the default test and regeneration path;
- normalized task, episode, intervention, budget, and result schemas;
- stable task/environment/harness hashes and logical event ordering;
- explicit repeat indices and model/provider/environment manifests;
- call, token, tool, latency, and estimated-cost accounting;
- task-level paired and hierarchical bootstrap utilities with deterministic
  seeds;
- fail-closed checkpoint/replay integrity receipts;
- sanitized public rows, with raw provider material confined to gitignored
  `artifacts/`.

Suggested package-local additions:

```text
experiments/grounded_statecharts/
  adapters/
  schemas/task.schema.json
  schemas/episode.schema.json
  schemas/intervention.schema.json
  schemas/result.schema.json
  evaluation.py
  budgets.py
  sanitization.py
```

Do not make a live API the only way to test the runner. A clean clone must run
schema, fixture, statistics, and replay tests without credentials.

### Tranche 2 — Grounded Statecharts live pilot and useful demo

This is the fastest route to commercial usefulness and a public explanation.

Required baselines:

- direct loop;
- statechart with G0 self-verification;
- same-model G1 verification;
- candidate G3 executable guard;
- wrong-evidence guard;
- oracle transition policy as a diagnostic upper reference only.

Primary outcomes are false completion, invalid transition, raw task success,
recovery success, and useful-autonomy rate. Freeze guard predicates before the
held-out run. A guard may inspect declared artifacts and tool receipts, not the
answer key or hidden fault label.

The demo should show one authentic failure: the agent proposes
`verify -> commit`, a fresh independent receipt fails, the chart routes to
repair, and the paired replay reaches a grounded commit. It must also show the
added budget and the claim boundary.

Tranche exit: the two-family D2 pilot gate passes, the demo runs from sanitized
committed rows, and a clean clone can reproduce the fixture version without a
paid provider.

### Tranche 3 — Constraint Transport factorial

Start task and constraint generation in parallel with Tranche 2 after the
shared schemas freeze. Evaluate the load-bearing factorial:

| Lineage representation | External enforcement | Interpretation |
|---|---|---|
| prose/verbatim | absent | strongest prompt baseline |
| typed envelope | absent | representation effect |
| prose/verbatim | present | guard effect without typed lineage |
| typed envelope | present | candidate joint mechanism |

Use approval, evidence, data-handling, and capability-scope constraints, each
with a valid completion path. Separate semantic survival from actual effects,
raw task success, false refusal, unauthorized capability expansion, and joint
success. Cluster inference at the root task, never the descendant node.

Pilot OOD probes should include held-out wording and a deeper delegation depth.
Do not claim typed transport if the entire gain comes from the external guard;
that is still a useful guard result and should be reported honestly.

### Tranche 4 — Sealed Counterfactual Harness Search benchmark

Begin benchmark plumbing and fault-generator authoring early, but do not run the
headline comparison until Tranches 1–3 supply real failure rows.

Required additions:

- sealed responsible-component labels for context, tools, generation,
  orchestration, memory, and output;
- no-fault, single-fault, and two-component interaction episodes;
- isolated repair, corruption, matched placebo, and exact no-op interventions;
- strong trace baselines using the same observable public events;
- equal total harness-evaluation budgets;
- held-out repair validation so search cannot win by overfitting the failing
  episode;
- top-1/top-k attribution, exact-set interaction score, false credit,
  calibration, and success-budget curves with paired intervals.

First publishable target: CHS1 and CHS2 on sealed labels. Claim improved
self-improving harness search only if CHS3 and CHS4 also pass. A CHS1 pass with
CHS3 failure remains a useful causal-diagnosis paper.

### Tranche 5 — Multi-shift functional harness unlearning

Build after the replay and intervention machinery is stable enough to measure
causal use under stochastic generation. Reuse the live tool tasks, then add at
least three shift families:

1. tool-schema or capability change;
2. environment-policy or approval change; and
3. model/version change with identical task semantics.

Compare append-only memory, recency decay, full reset, retrieval-only
suppression, and descendant-aware quarantine/revalidation. Include matched
non-shifts, recurrence, longer histories, and descendant leakage. The primary
outcome is commitment-level causal suppression plus recovery—not lower
retrieval by itself.

Do not call this neural unlearning or legal erasure. Stop if the causal-use gate
cannot reliably separate target-family suppression from matched placebo.

### Tranche 6 — Public release surfaces

Develop the reusable viewer and dataset validator in parallel, then populate
them only from passed experiment rows.

Required release:

- reproducible benchmark and public evaluation dataset;
- benchmark card, dataset card, license ledger, checksums, and reference scores;
- strong baselines, ablations, confidence intervals, and OOD tables;
- two-minute visual replay showing which harness component caused a failure;
- preprint, concise engineering article, and clean open-source repository;
- one-command deterministic reproduction and a separately documented opt-in
  live run;
- independent clean-clone verification before D4.

The viewer must label observed events, interventions, inferred causal credit,
uncertainty, cost, and claim boundary separately. Never expose hidden
chain-of-thought, secrets, or unrestricted provider transcripts.

## Parallel Execution Contract

Use at most six agents, each in its own worktree and branch. The coordinator
owns shared schemas, public documentation, result contracts, and final
integration. Other agents must not edit those hot files after the interface
freeze without coordination.

| Lane | Independent work after interface freeze | Merge dependency |
|---|---|---|
| 1. Runtime and statistics | adapters, budgets, replay-integrity receipts, bootstrap tests | first; freezes shared interfaces |
| 2. Statechart tasks | artifact task generator, G0/G1/G3 guards, wrong-evidence controls | lane 1 |
| 3. Constraint tasks | constraint families, delegation environments, 2×2 factorial | lane 1 |
| 4. CHS benchmark | fault generators, sealed-label loader, interaction scoring, trace baselines | lane 1; headline data waits for lanes 2–3 |
| 5. Memory shifts | shift generators, descendant leakage cases, non-shift and recurrence controls | lane 1; live claim waits for lane 4 machinery |
| 6. Replay and release | viewer, sanitizer, dataset validator, cards, clean-clone fixture lane | lane 1 schema; content waits for passed rows |

Parallelism is for disjoint implementation and fixture generation, not for
simultaneous edits to `README.md`, `TODO.md`, `docs/system_design.md`,
`docs/module_explainer.md`, registries, or root manifests. Land narrow PRs in
dependency order and rebase each worktree on the newly merged `origin/main`.

## PR and Evidence Sequence

Use this sequence unless an earlier kill condition fires:

1. live-evaluation schemas, adapter boundary, statistics, and sanitization;
2. two-family Grounded Statecharts D2 pilot plus unified replay;
3. Constraint Transport 2×2 pilot and OOD probes;
4. sealed-label CHS attribution benchmark;
5. equal-budget CHS repair search;
6. multi-shift Harness Unlearning pilot;
7. D3 power analysis and frozen confirmatory manifests;
8. confirmatory runs;
9. dataset, cards, preprint, article, replay, and clean-clone D4 release.

Every experimental PR must include a frozen preregistration, typed manifest,
row-level public-safe results, explicit allowed claim and non-claims, targeted
tests, documentation updates, and provenance refresh. Never tune on an OOD
test, overwrite a preregistration after outcomes are visible, or publish a
scientific metric from an integrity-invalid run.

## First 72 Hours

1. Freeze the normalized live episode/result schema and provider-adapter
   boundary.
2. Implement a deterministic fake provider and test stochastic repeat,
   checkpoint, budget, sanitization, and bootstrap behavior.
3. Author two artifact tasks and two recursive constraint tasks as end-to-end
   smoke tests; prove every condition can finish within the same hard budget.
4. Run a credentialed smoke test outside the tracked fixture path: one model,
   two tasks per family, two repeats. Inspect false completion, refusal, replay
   divergence, cost, and data leakage.
5. Freeze the D2 pilot manifest only after the smoke test validates mechanics;
   discard smoke outcomes from the held-out pilot.
6. In parallel, prototype the two-minute viewer against existing deterministic
   rows so it is ready when authentic live rows pass integrity checks.

## Verification Before Every Merge

At minimum:

```bash
uv run --no-sync ruff check .
uv run --no-sync ty check scripts experiments tests
uv run --no-sync python -m pytest -q tests/test_grounded_statecharts.py
uv run --no-sync python scripts/validate_experiment_manifest.py
python scripts/gen_provenance.py --check
python scripts/publication_guard.py
git diff --check
```

Run `python3 scripts/run_quality_checks.py` before merging substantive Python or
experiment changes. Regenerate each affected bundle twice into temporary
directories and byte-compare all deterministic public artifacts. Live result
rows need stable ordering and hashes; stochastic outcomes need statistical
reproducibility from frozen source rows, not byte-identical model behavior.

## Completion Definition

The handoff is complete only when the program has:

- a clean-clone-safe shared live evaluation layer;
- a passed two-family D2 pilot with all required controls;
- a real failure replay suitable for a two-minute public explanation;
- a public row-level dataset with uncertainty and budget accounting;
- a sealed-label CHS benchmark populated from real or model-mediated failures;
- a frozen decision—supported by evidence—to escalate, narrow, or stop each
  research claim;
- and, for every escalated claim, a D3 preregistration and sample-size plan.

Fixture success alone does not satisfy this completion definition.

Make this a goal. Work till complete. Do whatever you can in parallel with up to 6 parallel agents.

## Completion status (2026-07-20 night)

**Constraint Transport / live-eval / D4 packaging: shipped.**

Done on `main`:
- Harness-enforced name-free CT (D2 + D3 confirmatory; OOD paraphrase live smoke; Haiku replication)
- Public datasets (`results/d2_pilot_public/`, `results/d3_ct_confirmatory_public/`), failure replay
- Claim-bounded preprint + brief: `docs/papers/grounded_harness_ct_preprint_2026-07-20.md` (+ PDFs)
- CHS bridges (injected seals, equal-budget repair search, withheld-at-score-time) — not author-blind CHS1
- HU fixture bank + live kill-criteria smoke — not HU1–HU7
- GS remains narrowed

Remaining optional programs (not CT blockers): author-blind live six-surface CHS1; powered multi-model/OOD confirmatory; real HU pilot.

**Next handoff (active):** see
[`docs/next_agent_envelope_guard_product_ct_chs_handoff_2026-07-21.md`](next_agent_envelope_guard_product_ct_chs_handoff_2026-07-21.md)
for detailed Track 1 (Envelope Guard product), Track 2 (CT stress), and Track 3
(CHS1) implement / run / learn / report-back plans.

