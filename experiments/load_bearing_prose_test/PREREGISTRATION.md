# Load-Bearing Prose Test — Preregistration

**Frozen design date.** 2026-07-21
**Package.** `experiments/load_bearing_prose_test/` (this file lives in
the package alongside the root manifest so the provenance tooling and
the registry `preregistration_path` both resolve to a single authority)
**Declared model (live slices).** `openai` / `gpt-4.1-mini`
**Parent theory.** `papers/gauge_fixed_concern_transport/paper.md`
(bridge theorem), `papers/commitment_surface/paper.md`
(availability vs load-bearing).
**Reused κ substrate.** `experiments/grounded_statecharts/condition_policy.py`.

## Question

Does prose produced by an LLM planner have commitment surfaces at the
executor boundary such that the concern-transport bridge theorem's four
conditions detect a non-trivial, gauge-stable, κ-aligned load-bearing
subset — or is prose at this substrate consistent with the field's
default position that it is only judgment-verifiable?

## Task families

Reused from `experiments/grounded_statecharts/` under matched budgets:

1. **artifact_completion** — produce a required local artifact under
   fresh verification.
2. **recursive_constrained_tool_use** — delegate while preserving
   approval, evidence, or capability constraints.

A CT-style planner produces a prose plan for each task; a separate
executor acts on that plan. The commitment-surface oracle is
`score_from_evidence` in `condition_policy.py`. Live provider paths are
opt-in and gated by the existing live adapter.

## Conditions and paired contrasts

For every extracted claim `c` in a plan `p`, we produce three ablations:

- `delete(c)`: remove `c` from `p`.
- `negate(c)`: replace `c` with its logical negation, preserving
  surrounding structure.
- `paraphrase(c)`: replace `c` with a neutral paraphrase (semantics
  preserved by construction; used for the gauge check).

For each ablation, we run the executor on the modified plan and record
`AppliedEvidence`. We compare to a baseline run on unmodified `p`.

## Primary metrics

- **Load-bearing rate `L`** — fraction of extracted claims for which
  `delete(c)` OR `negate(c)` produces Δ(commitment surface) ≠ 0, where Δ
  is computed on the tuple `(action, capability_used_set, workspace_digest,
  false_completion, joint_success)`.
- **Paraphrase invariance `P`** — among load-bearing claims, the fraction
  for which `paraphrase(c)` produces Δ = 0.
- **κ concordance `K`** — pointwise agreement between "claim mentions a κ
  element" and "claim is load-bearing", reported as odds ratio with
  task-clustered bootstrap CI.

Secondary: refusal-rate covariate, paraphrase-quality audit rate,
executor-plan-attention covariate (does the executor's action correlate
with the plan content at all in the baseline).

## Registered thresholds (fatal gates)

The primary claim ("prose has commitment surfaces at this substrate")
is *published* only if all three gates pass on the held-out
confirmatory slice:

1. **Load-bearing floor.** `L ≥ 0.15` with task-clustered bootstrap
   lower CI ≥ 0.05. Below this floor, we cannot separate signal from
   base-rate variance and the primary claim is killed.
2. **Paraphrase-invariance floor.** `P ≥ 0.80` on the load-bearing
   subset with a lower CI ≥ 0.70. Below this floor, the "load-bearing"
   signal is wording sensitivity, not concern; the primary claim is
   killed.
3. **κ concordance above chance.** Odds ratio bootstrap CI for `K`
   excludes 1.0 by at least 0.2 on the low side. At chance, the
   theorem does not predict what we measure and the primary claim
   is killed; the null publishes as a bounded null.

Fatal gates are noncompensatory. A failed or unknown gate cannot be
averaged away by strong sub-results.

## Sub-claims (independently gated)

- **Deletion vs negation asymmetry.** Report Δ separately for `delete`
  and `negate`. A published sub-claim requires the paired asymmetry to
  survive its own bootstrap CI.
- **Family split.** Report `L, P, K` per task family. A family-specific
  claim requires that family's own gates to pass.
- **κ-mentioning subset.** Report `L | κ-mention` and `L | not κ-mention`
  with paired uncertainty.

## Injected-fault sealing (CHS-style)

Before the confirmatory slice we run an injected-fault sweep with
known load-bearing (κ-decisive) and known inert (κ-irrelevant, syntax
only) claims planted in synthetic plans. The pipeline must recover
≥ 90% of planted load-bearing claims and ≤ 10% false positives on
planted inert claims. Failure to seal aborts confirmatory spend.

## Integrity requirements

- Public rows use the CT public schema; raw prompts, transcripts, and
  provider material stay in gitignored `artifacts/`.
- Byte-stable regeneration for `results/lbpt_public/summary.json` and
  `results/lbpt_public/rows.jsonl` at frozen seeds.
- Zero provider failures on reported slices; failing rows drop the
  entire task episode.
- Name-free contract: condition identity (which ablation, which κ
  element) lives in code; executor prompts do not reveal condition
  identity.

## Escalation sequence

| Slice | Role |
|---|---|
| Deterministic scaffold tests | Correctness of extraction/ablation/scoring |
| Injected-fault sealing | Pipeline validity (kill if seal fails) |
| Pilot (24 tasks, both families) | Base-rate `L` and gauge check |
| Held-out confirmatory (≥ 96 tasks, matched to D2 shape) | Fatal gates 1–3 |

Kill criteria are checked strictly at each slice. Post-hoc reassignment
of thresholds is forbidden; only knobs explicitly named as free
parameters here (paraphrase-quality audit rate cutoff and refusal
covariate windowing) may be adjusted, and only with a receipt in the
decision doc.

## Claim boundary

Passing all three fatal gates supports the narrow published claim:
*under name-free executor prompts on two CT task families with
`gpt-4.1-mini`, a non-trivial, paraphrase-stable, κ-aligned load-bearing
prose subset exists as detected by the concern-transport bridge theorem
protocol described in `docs/harness_research/load_bearing_prose_test.md`.*

Not supported by these slices: prose verification for arbitrary
domains or models; soundness in the ATP sense; a general claim about
plan coherence across long trajectories; that inert claims are
semantically empty (they may be load-bearing at horizons outside this
substrate).

## Related documents

- Plan: [`../../docs/plans/2026-07-21-001-feat-load-bearing-prose-test-plan.md`](../../docs/plans/2026-07-21-001-feat-load-bearing-prose-test-plan.md)
- Thesis: [`../../docs/harness_research/load_bearing_prose_test.md`](../../docs/harness_research/load_bearing_prose_test.md)
- κ source: `experiments/grounded_statecharts/condition_policy.py`
- Bridge theorem: `papers/gauge_fixed_concern_transport/paper.md`
- Availability/load-bearing framing: `papers/commitment_surface/paper.md`
- CT preprint (parent instance): `docs/papers/grounded_harness_ct_preprint_2026-07-20.md`
