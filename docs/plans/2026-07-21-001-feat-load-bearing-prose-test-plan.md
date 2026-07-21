---
title: Load-Bearing Prose Test - Plan
type: feat
date: 2026-07-21
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: concern-transport-bridge-theorem
execution: code
---

# Load-Bearing Prose Test - Plan

## Goal Capsule

- **Objective:** Empirically test whether prose produced by LLM agents has
  commitment surfaces the concern-transport bridge theorem can detect — i.e.,
  whether atomic claims in a plan or analysis can be classified as
  *load-bearing* (deleting them changes the downstream committed action) or
  *available but not load-bearing* (deleting them leaves commitment invariant),
  and whether the load-bearing subset is stable under gauge-fixing paraphrase.
- **Why now.** The Constraint Transport (CT) program has an empirical instance
  of the bridge theorem for typed capability envelopes at the delegation
  boundary. Extending the same discipline one substrate up — from *actions*
  to *prose that authorizes actions* — is the shortest reachable move that
  would refute the default field position that prose is irreducibly
  judgment-bound. If the load-bearing subset is non-trivial and gauge-stable,
  we have the first real oracle for prose. If it collapses, we have a
  bounded null result for a specific claim about the bridge theorem's reach.
- **Authority.** `docs/harness_research/load_bearing_prose_test.md` (thesis),
  `experiments/load_bearing_prose_test/PREREGISTRATION.md` (gates and kills; moved into the package during Week 1 alongside the root manifest so provenance tooling and the registry `preregistration_path` both resolve to one authority),
  `papers/commitment_surface/paper.md` (availability vs. load-bearing),
  `papers/gauge_fixed_concern_transport/paper.md` (bridge theorem),
  `experiments/grounded_statecharts/condition_policy.py` (κ substrate reused
  for scoring).
- **Execution profile.** Reuse the CT harness's task families
  (`artifact_completion`, `recursive_constrained_tool_use`), κ set
  (`required_capabilities`, `forbidden_capabilities`, `required_artifact`),
  and evidence-based scoring. Add a planner-executor split: a planner
  produces prose plans; an executor acts on plans (and on ablation variants);
  the CT commitment-surface oracle scores the executor.
- **Stop conditions.** Kill the primary claim if load-bearing fraction is
  below the pre-registered floor, if paraphrase-invariance rejects too much
  of the load-bearing set, or if κ concordance is at chance. Do not
  post-hoc rescue by relabeling claims or swapping ablation transforms.
- **Tail ownership.** Commit and push on a focused branch, open a PR with the
  green-CI merge rule, and ship a public sanitized dataset under
  `experiments/load_bearing_prose_test/results/lbpt_public/` following the
  `d2_pilot_public/` discipline (rows.jsonl, summary.json, checksums.json,
  DATASET.md) once week 4 completes.

---

## Product Contract

### Summary

Take a real prose plan produced by an LLM planner for a CT-harness task.
Extract atomic claims. For each claim, produce three ablation variants
(delete, negate, neutral paraphrase) and run the downstream executor agent
on each variant. Measure whether the committed action / evidence / capability
set changes. Classify claims as load-bearing or inert. Publish the
load-bearing fraction, its paraphrase invariance, and its concordance with
the ground-truth κ from `condition_policy.py`.

The deliverable is the measurement, not a product. The bridge-theorem audit
receipt travels with every reported load-bearing claim.

### Problem Frame

Two turns of the conversation and the `commitment_surface` paper agree:
mechanistic and interpretability work often confuses *availability* of a
structure (a probe recovers it; a claim is *in* the prose) with *load-bearing*
use of that structure (it causally alters a commitment). At the level of
LLM plans and analyses, no published test currently separates the two
substrates. The default assumption is that prose can only be judged by
another LLM, i.e., by a same-faculty judge with correlated errors.

The concern-transport bridge theorem gives a discriminator. A prose claim
that has positive concern mass in the parent contract, survives transport
to the executor, is separable from gauge-equivalent paraphrases, and
changes the commitment surface, is load-bearing. Otherwise it is available
decoration. This experiment operationalizes that discriminator on real
agent-produced prose over a CT-substrate task family with a code-side
oracle.

### Bridge-Theorem Instantiation

| Theorem term | Realization in this experiment |
|---|---|
| Contexts C | Planner prompt → planner prose plan → executor prompt → executor action + evidence |
| Transport map T | Planner-to-executor prose passage |
| Concern measure κ | `required_capabilities`, `forbidden_capabilities`, `required_artifact` from `condition_policy.py` |
| Candidate gauge freedom | Neutral paraphrase of a claim (semantics preserved by construction) |
| Commitment surface | Executor's committed action, `capability_used`, and workspace hash under `score_from_evidence` |
| Load-bearing verdict | Δ(commitment surface) ≠ 0 under deletion AND Δ = 0 under paraphrase |

### Scope and Non-Goals

- **In scope.** Two CT task families; single declared live model
  (`gpt-4.1-mini`) for parity with the CT preprint; deterministic ablation
  transforms with an LLM paraphrase step audited by cosine similarity to
  a rule-based paraphrase; frozen fixture matrix mirroring the D2 held-out
  bank shape; public sanitized dataset with checksums.
- **Out of scope for the primary claim.** Any claim about arbitrary domains,
  arbitrary models, or arbitrary prose. Any claim that this test is sound in
  the ATP sense. Any claim that inert claims are *actually* meaningless (they
  may be load-bearing at a horizon this substrate doesn't reach). Any
  extension to plan-step coherence across long trajectories (that is a
  follow-on ledger experiment, deliberately deferred).
- **Explicitly not-shipped in this plan.** κ-inference from arbitrary NL
  contracts, prose commitment ledger, symbolic-invariant distillation. Each
  is a separate future package; the primary result must land first with a
  narrow claim.

### Success Criteria (pre-registered; see PREREGISTRATION.md for exact numbers)

- Load-bearing fraction is non-trivially above zero on a held-out bank.
- Load-bearing claims are paraphrase-invariant above the registered floor.
- Concordance with κ (claims mentioning κ elements are more likely load-bearing) has a bootstrap CI excluding chance.

### Kill Criteria (pre-registered)

- Load-bearing fraction below the registered floor → prose has no exploitable
  commitment structure at this substrate at this scale → primary claim killed.
- Paraphrase invariance below the registered floor → the "load-bearing" signal
  is wording sensitivity, not concern → primary claim killed.
- κ concordance at chance → the theorem does not predict what this test
  measures → primary claim killed; the measurement stands as a null.

Any failed gate prevents publication of the primary claim. Sub-claims that
survive their own registered gates may still ship.

### Integrity Requirements

- Sanitized public rows only; raw provider material remains in gitignored
  `artifacts/`.
- Task-clustered bootstrap uncertainty; nested repeats treated as
  within-task variance, not independent samples.
- Ablations run on frozen fixture claims; live-run seeds are fixed and
  recorded.
- Name-free contract discipline inherited from CT: condition identity
  (which ablation, which κ element) lives in code, not in executor
  prompts.
- `scientific-discovery-regime-audit` skill run before the confirmatory
  slice per `AGENTS.md`.

---

## Execution Plan

### Week 1 — Deterministic scaffolding (this branch's follow-on)

Create the runtime package `experiments/load_bearing_prose_test/`
together with its root `experiment_manifest.json` and a
`structured_manifest` entry in `docs/experiment_contract_registry.json`
in the *same commit* — the package-coverage validator fails-loud on
any unregistered `experiments/` subdirectory, so the manifest and
registry edit are non-optional even for scaffolding.

- Scaffold contents:
  - `claims.py`: `Claim`, `ClaimBundle`, `Ablation`, `AblationSet`,
    `Verdict` dataclasses; deterministic digests for receipts.
  - `extraction.py`: interface for claim extractors; a deterministic
    rule-based extractor for regression tests and a live-model extractor
    stub (opt-in behind an env flag, off in CI).
  - `ablation.py`: `delete`, `negate`, `paraphrase` transforms with a
    deterministic paraphrase used in tests and an LLM paraphrase behind
    the same env-gated adapter.
  - `fixtures/`: 4–8 seed plans wired to the CT task families with
    hand-authored expected extractions.
  - `tests/test_lbpt_*.py`: deterministic tests covering extraction,
    ablation transforms, and the round-trip receipt.
- `run_lbpt_smoke.py`: CLI that emits a deterministic fixture receipt so
  CI covers the surface before any live spend.

### Week 2 — Ablation execution loop

- `executor.py`: adapter that takes a prose plan (or an ablated variant),
  runs the CT executor path with matched budgets, and returns
  `AppliedEvidence` from `condition_policy.py`.
- `scoring.py`: given an `Ablation` and paired executor outputs, compute
  Δ(commitment surface) and a load-bearing verdict per pre-registered
  rules.
- `run_lbpt_pilot.py`: pilot slice over the two CT families; matched
  budgets; task-clustered rows; smoke rows discarded from held-out
  analysis.

### Week 3 — Gauge check and κ concordance

- Paraphrase-invariance harness: for load-bearing claims, run additional
  paraphrase-only ablations; verify Δ = 0.
- κ concordance measurement: label each claim as κ-mentioning or not
  from `condition_policy.py` sets; measure joint distribution against
  the ablation-derived load-bearing set with task-clustered bootstrap.
- CHS-style injected-fault sealing: inject known load-bearing and known
  inert claims; verify the pipeline recovers them.

### Week 4 — Preprint and public dataset

- `results/lbpt_public/` with `rows.jsonl`, `summary.json`,
  `checksums.json`, `DATASET.md` following the CT public export
  discipline.
- `docs/papers/lbpt_preprint_YYYY-MM-DD.md` with claim boundary, kill
  criteria outcomes, and explicit link to
  `papers/commitment_surface/paper.md` and
  `papers/gauge_fixed_concern_transport/paper.md`.
- Update `docs/system_design.md` and `docs/module_explainer.md` for the
  live surface; refresh provenance via `scripts/gen_provenance.py`.

---

## Risk Register

- **Prose plans may collapse to κ-verbatim quotes.** If planners parrot
  the parent contract verbatim, the ablation loop measures verbatim
  copying, not prose transport. Mitigation: use planner prompts that
  require justification and multi-step planning; measure paraphrase
  distance from κ text as a covariate.
- **Executor may ignore the plan entirely.** If executors act only on
  the task, not the plan, Δ = 0 across all ablations and the primary
  claim gets rescued incorrectly. Mitigation: add a
  "planner-only-authority" condition where the executor is prompted to
  strictly follow the plan; report separately.
- **Paraphrase collapse.** LLM paraphrases may leak the ablation identity
  (add or drop content). Mitigation: audit paraphrases against a
  rule-based baseline and reject the round if leakage rate exceeds a
  registered threshold.
- **False null via base-rate low commitment change.** If the CT executor
  is already at ceiling regardless of plan, the ablation cannot separate.
  Mitigation: sanity-check with a synthetic negative control
  (planner-injected forbidden capability) which the executor must
  refuse to commit — if that fails, the substrate is not sensitive
  enough and the primary result is inconclusive, not passed.
- **Gauge check that is really a semantic check.** Neutral paraphrases
  may be non-neutral. Mitigation: cosine-similarity floor plus a
  rule-based paraphrase peer; disagreement flags the paraphrase for
  exclusion.

---

## Kill and Escalation Sequence

| Slice | Role |
|---|---|
| Week-1 deterministic tests | Kill test for scaffolding correctness |
| Week-2 pilot (~24 tasks) | Kill test for base-rate load-bearing fraction |
| Week-3 gauge + κ pilot | Kill test for paraphrase invariance and κ concordance |
| Week-4 held-out confirmatory | Publish primary claim only if all above pass |

---

## Publication Surface

- **Package (planned):** `experiments/load_bearing_prose_test/` (created in Week 1 with a root manifest and registry entry)
- **Preregistration:** `experiments/load_bearing_prose_test/PREREGISTRATION.md`
- **Public dataset target:** `experiments/load_bearing_prose_test/results/lbpt_public/`
- **Preprint target:** `docs/papers/lbpt_preprint_YYYY-MM-DD.md`
- **Thesis:** `docs/harness_research/load_bearing_prose_test.md`

---

## Related Work in This Repo

- `experiments/grounded_statecharts/CONSTRAINT_TRANSPORT_PREREGISTRATION.md`
- `experiments/grounded_statecharts/condition_policy.py`
- `experiments/grounded_statecharts/D2_PILOT_DECISION.md`
- `docs/papers/grounded_harness_ct_preprint_2026-07-20.md`
- `papers/commitment_surface/paper.md`
- `papers/gauge_fixed_concern_transport/paper.md`
- `docs/harness_research/constraint_transport.md`
