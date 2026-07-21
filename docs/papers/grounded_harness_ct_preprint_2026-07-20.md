# Harness-Enforced Constraint Transport Under Name-Free Evaluation

**Status:** research preprint (internal), claim-bounded  
**Date:** 2026-07-20  
**Package:** `experiments/grounded_statecharts`  
**Model (live slices):** `openai` / `gpt-4.1-mini`  
**Public datasets:** `experiments/grounded_statecharts/results/d2_pilot_public/`,  
`experiments/grounded_statecharts/results/d3_ct_confirmatory_public/`

## Abstract

Recursive agent systems often lose constraints at delegation boundaries: a parent
understands an obligation or prohibition, yet a child acts under a widened or
incomplete contract. We evaluate Constraint Transport (CT) and Grounded
Statecharts (GS) inside a shared live harness with matched budgets, task-clustered
uncertainty, and fail-closed public rows. An early labeled-prompt D2 slice
suggested large CT and modest GS effects, but a weak-prompt ablation that removed
condition-name labels collapsed both contrasts to zero—evidence that the labeled
effects were prompt/scaffold artifacts. We redesigned the evaluation contract:
prompts are name-free by default; `condition_policy.py` enforces G3 artifact
repair and external envelope capability narrowing in code; outcomes are scored
from applied evidence rather than condition-name membership. Under that
harness-enforced, name-free contract, CT joint-success again separates perfectly
on a name-free ablation (δ = +1.0), a held-out harness-v2 D2 matrix (144 episodes;
δ = +1.0, CI [1.0, 1.0]), and a D3 CT confirmatory slice (120 episodes; 5 nested
repeats; δ = +1.0, CI [1.0, 1.0]). The allowed claim is narrow: external guards
recover joint success after capability widenings under name-free prompts via
harness enforcement—not model-side constraint learning. GS remains narrowed; CHS
has paired-contrast orchestration seals only; Harness Unlearning remains fixture
scaffolding.

## 1. Introduction

Modern agent stacks compose planners, workers, and tools. Constraints that are
salient at the root—approval requirements, evidence obligations, capability
bounds—can decay as tasks are summarized, delegated, or re-authorized. The
grounded-harness program treats this as a *transport* problem rather than only a
prompt-following problem: whether child-effective constraints preserve the
load-bearing parts of the parent contract through recursion.

Four related surfaces share one package, `experiments/grounded_statecharts`:

1. **Grounded Statecharts (GS)** — independent transition guards that block false
   completion before commit.
2. **Constraint Transport (CT)** — typed envelopes, lineage, capability
   narrowing, and external effect/commit guards through recursive delegation.
3. **Counterfactual Harness Search (CHS)** — paired repair/placebo attribution
   over harness surfaces.
4. **Harness Unlearning (HU)** — descendant-aware causal-use gates for stale
   tool-pattern memory.

This preprint reports the live name-free evaluation program that separates
*harness-enforced* CT recovery from prompt-label scaffolding. The scientific
target is not a general claim that language models “learn constraints,” but a
severe test of whether external guards change machine-checkable joint success
when condition identity is withheld from the prompt.

## 2. Methods

### 2.1 Task families and model

Held-out D2 tasks freeze two machine-checkable families (12 tasks each):

- **Artifact completion:** produce a required local artifact under fresh
  verification; the tempting failure is false completion from stale or missing
  evidence.
- **Recursive constrained tool use:** delegate while preserving approval,
  evidence, or capability constraints; a compliant non-refusal path exists and
  is machine-checkable.

Live slices use `gpt-4.1-mini` behind the package’s opt-in live adapter. Smoke
rows are discarded from held-out analysis. Budgets are matched within paired
comparisons (`DEFAULT_PILOT_BUDGET`).

### 2.2 Conditions and primary contrasts

Core CT contrast (primary):

- `envelope_only` versus `envelope_external_guards` on **joint success**
  (task success with zero constraint violation).

Core GS contrast (secondary / narrowed):

- `statechart_g0` versus `statechart_g3` on **false completion**.

Wrong-edge / wrong-evidence and matched soft/self-report cells remain controls
or baselines; they do not receive candidate-mechanism credit when they fail the
registered gate.

### 2.3 Prompt and scoring contract (harness-v2)

After the labeled-prompt artifact was exposed, the evaluation contract was
frozen as follows:

1. **Name-free prompts by default.** Condition names and treatment labels are
   not injected into the live instruction text used for escalation gates.
2. **Harness enforcement in `condition_policy.py`.** After the provider returns
   an action:
   - `statechart_g3` repairs missing artifacts before commit scoring;
   - `envelope_external_guards` (and constrained `statechart_g3`) strips
     forbidden capabilities and forces a constrained delegate action;
   - self-report / `envelope_only` leave model claims unchanged.
3. **Score from evidence.** `score_from_evidence` computes false completion,
   task success, and joint success from applied workspace/capability evidence,
   not from condition-name membership.
4. **Labeled prompts are diagnostic-only**
   (`GROUNDED_HARNESS_LABELED_PROMPT=1`) and must not gate escalation.

### 2.4 Statistics and integrity

Primary uncertainty uses task-clustered bootstrap with nested repeats under
tasks (not treated as independent samples). Integrity requirements include
publishable public-schema rows, resolvable hashes, zero provider failures on the
reported slices, and separation of raw provider material into gitignored
`artifacts/`. Public exports live under:

- `results/d2_pilot_public/` (held-out harness-v2 D2)
- `results/d3_ct_confirmatory_public/` (CT confirmatory)

### 2.5 Escalation sequence

| Slice | Role |
|---|---|
| Labeled-prompt D2 | Diagnostic only; variance under the old contract |
| Weak-prompt ablation (pre-harness) | Kill test for labeled scaffolding |
| Harness-v2 name-free ablation | Redesigned gate before held-out spend |
| Held-out harness-v2 D2 (144 eps) | Planning / public D2 matrix |
| D3 CT confirmatory (120 eps, 5 nested repeats) | Confirmatory CT cells only |

Kill criteria (registered): pre-harness weak-prompt CT δ = 0.0 kills labeled
escalation; harness-v2 name-free CT δ = +1.0 with ≥4 tasks passes the redesigned
gate; GS improvement remains killed at ablation δ = 0.0.

## 3. Results

All figures below are taken from the package decision freeze and public
summaries; no additional statistics are invented here.

### 3.1 Labeled-prompt D2 looked strong—and was fragile

Under labeled prompts, directional task-clustered contrasts were:

| Contrast | Labeled prompt |
|---|---|
| CT joint_success: external − envelope_only | **+1.000** |
| GS false_completion: G3 − G0 | **−0.167** |

A weak-prompt ablation that removed condition labels **collapsed both contrasts
to 0.0**. That result is the program’s central negative finding: the labeled D2
effects were prompt/scaffold artifacts under the old contract, not evidence of
stable model-side transport or GS improvement.

### 3.2 Harness-v2 name-free redesign restores CT, not GS

After moving condition identity into harness code:

| Contrast | Harness-v2 name-free ablation |
|---|---|
| CT joint_success δ | **+1.000** |
| GS false_completion δ | **0.0** |

CT therefore re-passes the redesigned escalation gate as a *harness-enforcement*
effect. GS does not: under name-free prompts plus harness repair in the
ablation, the model rarely false-completes, so G3 shows no improvement delta.

### 3.3 Held-out harness-v2 D2 (144 episodes)

Public held-out matrix (`results/d2_pilot_public/`; 144/144 publishable;
`gpt-4.1-mini`):

| Contrast | Point estimate | Bootstrap CI |
|---|---|---|
| CT joint_success: external − envelope_only | **+1.000** | **[1.0, 1.0]** |
| GS false_completion: G3 − G0 | **−0.083** | **[−0.25, 0.0]** |

Task-level CT separation on this slice is complete under the name-free contract:
`envelope_only` joint success is 0/12 tasks and `envelope_external_guards` is
12/12 after harness enforcement. Artifact false completion shows only a small
G3 edge (−0.083) with no raw task-success loss on the registered G3−G0
task-success contrast (0.0).

### 3.4 D3 CT confirmatory (120 episodes)

Confirmatory CT-only slice (`results/d3_ct_confirmatory_public/`; 120/120
publishable; 5 nested repeats; same harness-enforced name-free contract):

| Contrast | Point estimate | Bootstrap CI |
|---|---|---|
| CT joint_success: external − envelope_only | **+1.000** | **[1.0, 1.0]** |

The confirmatory result matches the held-out D2 planning estimate under the same
contract.

### 3.5 Portfolio status outside CT

- **GS:** remains narrowed; do not escalate on the current null / small edge.
- **CHS:** paired-contrast seals from public CT contrasts are allowed for
  orchestration/output surfaces only; full six-surface CHS1 on sealed real
  failures remains open.
- **HU:** fixture scaffolding and draft multi-shift smokes only; no HU1–HU7
  live claim.

## 4. Discussion

### 4.1 Claim boundary (authoritative)

**Allowed claim.** External guards recover joint success after capability
widenings under name-free prompts through harness enforcement
(`condition_policy.py`), with task-clustered uncertainty reported on public
sanitized rows.

**Not allowed from these slices.** Model-side constraint learning; GS product
readiness; CHS1 attribution on sealed real failures; HU1–HU7 unlearning; general
production safety certificates; claims that typed envelopes alone (without
external guards) suffice under the live name-free contract.

This boundary is the scientific payload of the redesign. The first D2 success
was easy to over-read as “the model transported constraints when labeled.” The
weak-prompt collapse forced a gauge fix: condition identity must live in the
harness, and scoring must read evidence.

### 4.2 Surprises

1. **Labeled scaffolding was sufficient to manufacture both CT and GS deltas.**
   Removing names zeroed both effects before harness enforcement existed.
2. **CT’s +1.0 returned under name-free prompts once external enforcement was
   real**—so the mechanism of interest is recovery after widening, not verbal
   compliance with a condition label.
3. **GS did not return.** The same redesign that revived CT left GS at ablation
   δ = 0.0 and only a small held-out false-completion edge (−0.083), consistent
   with low base-rate false completion under the name-free live path.
4. **Perfect task-level CT separation** (0/12 vs 12/12 on held-out D2) yields a
   bootstrap CI pinned at [1.0, 1.0]. That is informative about this frozen bank
   and contract; it is not a license to extrapolate to arbitrary models, depths,
   or OOD wording without further tests.

### 4.3 Frame diagnosis

**Current frame (rejected for escalation):** labeled condition prompts reveal
latent model constraint competence.

**Working frame (supported for CT only):** under name-free prompts, external
capability/effect guards change the child-effective contract after the model
acts, recovering joint success when widenings would otherwise fail scoring.

**Discriminating prediction that already landed:** if labels were load-bearing,
harness-v2 name-free CT should collapse; it did not. If GS improvement were
label-independent, ablation GS δ should remain negative; it went to 0.0.

## 5. Limitations

- Single declared model (`gpt-4.1-mini`) for the reported live slices.
- Frozen 12+12 held-out bank; OOD wording and deeper-depth probes are planned
  but not primary confirmatory evidence in the public D3 CT export.
- CT contrast is specifically external guards versus envelope-only under the
  harness-enforced contract; it is not a full published 2×2 of prose×guard with
  live crossed cells in this preprint.
- Perfect separation can reflect a strong, machine-checkable failure mode of
  widening under `envelope_only` rather than graded real-world difficulty.
- GS, CHS, and HU claims remain intentionally incomplete.
- Public rows exclude prompts, transcripts, and sealed labels; independent
  re-analysis of raw provider material is outside the public contract.

## 6. Next steps

1. Keep labeled prompts banned for gates; treat any reappearance of label-driven
   deltas as contamination.
2. Run registered OOD probes (held-out paraphrase wording; deeper delegation
   depth) without expanding the primary CT claim until those probes pass their
   kill criteria.
3. Expand CHS seals beyond orchestration/output with injected surface coverage
   toward CHS1; do not score CHS from heuristic harvest alone.
4. Replace HU replicated fixture replays with independently generated corpora
   before any live HU claim.
5. Revisit GS only if a name-free design produces a non-null false-completion
   contrast without raw-success collapse beyond the frozen ≤10pp loss gate.

## References (internal)

- `experiments/grounded_statecharts/README.md` — package contract and runners
- `experiments/grounded_statecharts/D2_PILOT_DECISION.md` — decision freeze and
  directional table
- `experiments/grounded_statecharts/D3_SAMPLE_SIZE_PLAN.md` — confirmatory plan
  and claim boundary
- `experiments/grounded_statecharts/condition_policy.py` — harness enforcement
  and evidence scoring
- `experiments/grounded_statecharts/results/d2_pilot_public/` — public held-out
  D2 dataset
- `experiments/grounded_statecharts/results/d3_ct_confirmatory_public/` — public
  D3 CT confirmatory dataset
- `docs/harness_research/constraint_transport.md` — design thesis and non-claims
- `docs/next_agent_grounded_harness_experiments_handoff_2026-07-20.md` — program
  handoff and D2 gate
- `experiments/grounded_statecharts/CONSTRAINT_TRANSPORT_D2_PREREGISTRATION.md`
  — bridge assumptions and kill criteria
