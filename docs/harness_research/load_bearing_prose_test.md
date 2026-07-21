# Load-Bearing Prose Test

Status: plan and preregistration frozen 2026-07-21; scaffolding follows;
no empirical claim yet.

Portfolio role: shortest-path move to test whether the concern-transport
bridge theorem extends one substrate above the Constraint Transport (CT)
harness — from actions to the prose that authorizes actions.

## One-Sentence Thesis

Under a code-side commitment-surface oracle, atomic claims in
LLM-produced plans can be classified as *load-bearing* (deletion
changes the executor's committed action or evidence) or *available but
not load-bearing* (deletion leaves the commitment invariant), and the
load-bearing subset is stable under gauge-fixing paraphrase and
concordant with the κ set inherited from CT.

## Problem

The field's current default is that prose is only verifiable by
LLM-as-judge — a same-faculty check with correlated errors. That
default sits beside a paper this program already published
(`papers/commitment_surface/paper.md`) whose central thesis is that
mechanistic and interpretability work confuses *availability* of a
structure with *load-bearing* use of it. Both claims can be made
sharper by an empirical test on prose against a code-side oracle,
which the CT harness now provides.

The concern-transport bridge theorem
(`papers/gauge_fixed_concern_transport/paper.md`) states that a
concern-weighted distinction is load-bearing when it has positive
concern mass, survives a transport chain, is separable from
gauge-equivalent descriptions, and changes the commitment surface.
Prose has, in principle, all four surfaces exposed — planner-to-executor
prose passage as transport, paraphrase as gauge, executor evidence as
commitment surface, κ from the CT policy as concern. Whether the
theorem's discriminator returns a non-trivial answer on real
agent-produced prose is an open empirical question.

## Design

- Reuse the CT harness's two task families and κ set as ground truth
  concern.
- A planner LLM produces a prose plan for each task under a name-free
  contract.
- Claim extraction atomizes the plan into atomic predicate-shaped
  claims.
- Three ablation transforms — delete, negate, paraphrase — are applied
  per claim.
- The CT executor runs on the baseline plan and on each ablation
  variant.
- `score_from_evidence` from
  `experiments/grounded_statecharts/condition_policy.py` computes the
  commitment surface as the tuple `(action, capability_used_set,
  workspace_digest, false_completion, joint_success)`.
- A claim is *load-bearing* if delete or negate produces Δ ≠ 0 on the
  commitment surface.
- The gauge check requires load-bearing claims to be Δ = 0 under
  paraphrase.
- κ concordance measures agreement between "claim mentions a κ
  element" and "claim is load-bearing" with task-clustered
  bootstrap CI.

The primary published claim is bounded: it is a statement about *this*
substrate under *this* model with *these* task families. Publication
requires all three fatal gates in
[`load_bearing_prose_test/PREREGISTRATION.md`](load_bearing_prose_test/PREREGISTRATION.md)
to pass.

## Relation to Existing Work

- **Constraint Transport (CT).** Same κ substrate; same evidence
  oracle; same public-row discipline. This experiment is a one-level
  altitude increase from actions to authorizing prose.
- **Commitment Surface paper.** Provides the availability/load-bearing
  distinction that we operationalize here on prose.
- **Gauge-Fixed Concern Transport paper.** Provides the four-gate
  bridge theorem the experiment instantiates and audits.
- **Counterfactual Harness Search (CHS).** Injected-fault sealing is
  reused to validate the extraction/ablation/scoring pipeline before
  confirmatory spend.

## Non-Claims

- No claim of soundness in the automated-theorem-proving sense.
- No claim about arbitrary models, arbitrary prose, or arbitrary
  domains.
- No claim that inert claims are semantically empty — they may be
  load-bearing at horizons this substrate does not reach.
- No extension to long-horizon plan-coherence ledgers here (deferred).
- No κ inference from natural-language contracts here (deferred).

## Known Risks

- Planner prose may collapse to κ-verbatim quotes, converting the test
  into a verbatim-copying check. Mitigated by planner prompts that
  require justification and by a verbatim-similarity covariate.
- Executor may ignore plans, collapsing Δ to zero regardless of
  ablation. Mitigated by a plan-authority condition reported
  separately.
- Paraphrase transforms may leak ablation identity. Mitigated by a
  cosine-similarity floor and a rule-based paraphrase peer.
- The task family may be at ceiling and insensitive to plan content.
  Mitigated by a synthetic negative control (planner-injected
  forbidden capability) that the executor must refuse to commit.

## Success Would Look Like

A published bounded claim of the form: *under a name-free contract on
two CT task families with a declared model, load-bearing prose exists
at rate `L`; the load-bearing subset is paraphrase-stable at rate `P`;
κ concordance odds ratio is `K` with task-clustered CI excluding
chance.* Accompanied by a public sanitized dataset following the
CT public export discipline and a preprint that ties the empirical
protocol to the bridge theorem's four gates.

## Failure Would Look Like

Any fatal gate failing on the confirmatory slice. The bounded null
publishes with the same discipline: the substrate is not sensitive to
the theorem's discriminator at this scale, at this model, on these
families. The theoretical framework is unchanged; the substrate
requires a different instantiation.
