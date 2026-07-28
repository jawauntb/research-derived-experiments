# IDENT Preregistration / Discovery-Regime Audit

## Discovery-Regime Audit

Question:
What is the smallest environment where passive prediction and mechanism identification provably diverge, and do modern models request the weakest separating intervention?

Current regime:
- Artifact types: finite hypothesis sets, response tables, equivalence classes, minimum-cost identifying separators, JSONL items, baseline/model transcripts, gate verdicts.
- Operations: exhaustive equivalence/separator computation, deterministic generators (boolean / DFA / small programs), baseline suite, one-shot JSON tool protocol.
- Gates/verifiers: G1–G7 (see below); validators reject leaking or non-identifying items.
- Known limitations: v1 is one-step and symbolic; NL wrappers and multi-step adaptive ID are out of scope.

Action class:
- Retrieval/search/discovery: **discovery** — adds a new benchmark artifact type (experiment-relative underdetermination with exact separators) and a fatal passive-bound gate.
- Why: prior VOI / intervention packages score probe value, but do not ship a held-out family where passive impossibility is exact and the weakest separator is annotated.

Experiment:
- Manifest/report paths: `experiments/ident/experiment_manifest.json`, `experiments/ident/results/baseline_summary.json`
- Positive targets: oracle ≥99% identification; every item live-class ≥2 with ≥1 identifying separator.
- Negative controls: wasteful more-of-same interventions; answer-now baseline bounded by chance.
- Stress tests: hypothesis label shuffle; cost gap; k∈{2,3,4}; three formal domains.

Gate:
- Acceptance rule: G1∧G2∧G3∧G4 on the fixed test split; G6 recorded; G5/G7 deferred to model eval.
- Withheld/rejected rule: items failing validation are never written; failed model runs preserved under `artifacts/ident/`.

Results:
- Accepted artifacts: `splits/{train,dev,test}.jsonl` (1000 items); `results/baseline_summary.{json,md}` with G1–G4 and G6 PASS; `results/model_summary.{json,md}` with G5/G7 PASS on OpenRouter slice.
- Rejected/withheld: raw model transcripts under `artifacts/ident/` only.
- Transported evidence: Bayesian VOI / online identifying interventions motivate cost-aware probes; IDENT isolates underdetermination recognition.
- Residual content: models intervene often (low false certainty) but remain far below oracle on final ID; Claude can match separator accuracy while still failing update-after-intervention (~0.55 final). EIG already separates well, so do not claim a new IG principle.
- Retractions: none.

Next move:
- Keep symbolic IDENT for the first paper; focus analysis on post-separator update failures and weakness regret. Expand surface (FSM depth / NL wrappers) only if a stronger model closes the final-ID gap on the symbolic menu.

## Target object and decision

- Target: IDENT v1 symbolic benchmark + passive impossibility note.
- Decision after baselines: ship if G1–G4 pass; expand surface only if models already match oracle.

## Material assumptions

1. Mechanisms are finite and fully specified in the generator.
2. Uniform prior over the live class for chance bounds and EIG.
3. One intervention budget in v1.
4. Hypothesis descriptions are faithful and non-leaking.

## Fatal gates (noncompensatory)

- G1 Formal ambiguity
- G2 Separability / active sufficiency
- G3 Passive bound
- G4 Oracle solvability

## Evidence / provenance paths

- Theory: `theory/definitions.md`, `theory/impossibility_theorem.md`
- Data: `splits/{train,dev,test}.jsonl`
- Results: `results/baseline_summary.json`
- Raw transcripts: `artifacts/ident/` (gitignored)
