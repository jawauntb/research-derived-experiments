# Causally Grounded Finite Agents Benchmark

Generated: 2026-07-06

## Charter

A finite agent is not grounded because it succeeds. It is grounded when the
variables that matter for future control are represented, attributed, queried,
and committed at the causal surfaces where action is selected.

This benchmark family evaluates whether an agent succeeds for the right causal
reason. Final task success is necessary, but it is never sufficient. A model
can answer correctly by shortcut, uniform storage, stale confidence, source
confusion, or local final-token cues. The benchmark therefore requires a
behavior score plus at least one structure-specific gate tied to the condition.

## Minimum Pass Rule

Do not call a model causally grounded on a suite unless it passes:

1. The task behavior gate.
2. The relevant causal-structure gate for that suite.
3. The suite's anti-cheat controls.

Examples:

- final answer plus moved-slot specificity;
- return plus action-conditioned consequence prediction;
- tool success plus repair commitment;
- attribution behavior plus self/world source accuracy;
- post-shift probe re-engagement plus recovery and no false calm;
- ID success plus structure-compatible OOD selection.

## Four Empirical Laws

### Law 1: Predictive Policy Closure

When an agent learns action-conditioned change in what it cares about, the
consequence model itself can become the policy by action argmax. This is the
planning-from-concern result: a Delta-E model can convert concern-shaped
representation into competence without optimal-action labels.

### Law 2: Reafferent Identifiability

Input factorization is not identification. A self head that sees action and a
world head that does not can still split the same total outcome arbitrarily.
Source attribution requires a gauge-breaking signal: source labels, null
intervention, temporal asymmetry, interventional contrast, or another source
pinning loss.

### Law 3: Re-Engagement Floor

Efficient inquiry is not adaptive inquiry. An agent can learn to probe
selectively, then stop probing after convergence and fail to restart after the
world changes. Quiet is not evidence of stability.

### Law 4: Commitment-Surface Memory

Memory becomes agent-relevant where it is coupled to a future commitment
surface: a later action, tool call, repair, emitted JSON value, or causal
readout. The moved-bottleneck diagnostic tests whether memory sensitivity
follows the moved future-critical variable rather than a matched distractor.

## Suite Inventory

| Suite | Existing evidence | Status | Behavior gate | Structure gate | Anti-cheat controls | Known boundary |
|---|---|---|---|---|---|---|
| A. Consequence-to-action | `papers/planning_from_concern/paper.md`; `experiments/planning_from_concern` | Strong | return and action accuracy | action-conditioned Delta-E model selects by argmax | random/sensory encoder controls; policy/distillation parity | distributed concern means no single privileged reward axis is sufficient |
| B. Reafferent attribution | `papers/first_order_self/paper.md`; `papers/null_intervention/paper.md`; `papers/world_responds/paper.md`; `experiments/world_responds` | Strong with ceiling | action competence or total prediction | self/world source MAE, gauge-breaker benefit, mediated/exogenous split | null intervention, shuffled source labels, oracle source labels, wrong-history controls | role-specific mediated effects hit a shared-head ceiling |
| C. Re-engagement under world change | `experiments/world_responds/BENCHMARK_CARD.md`; `papers/probe_value_reengagement/paper.md`; `papers/habituated_reengagement/paper.md`; `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md` | Packaged frontier: bounded positive with recovery gap | post-shift outcome recovery | post-shift probe density, decision-layer cooling, no-false-calm gate | cost-aware inquiry, surprise preserved, second-shift reopenability, signal-layer false-calm control | decision-layer cooling reopens inquiry and catches false calm; strict recovery and public JSONL runner remain partial |
| D. Long-horizon moved bottleneck | `papers/long_horizon_bottleneck/paper.md`; `experiments/long_horizon_bottleneck` | Strongest, hardened | delayed final accuracy | moved-slot memory specificity and rank | visible-control null, matched distractors, causal patch, fixed-action localization | black-box API runs are behavior-only, not hidden-state evidence |
| E. Tool commitment and repair | `experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`; prompt/API JSON suites | Strongest, hardened | parsed tool success, schema validity, repair/no-op behavior | critical variable survives tool argument, repair branch, generated action, or value-token readout | malformed schema controls, stochastic failure, alias/text argument surfaces, dispatch variants | OpenAI GPT-4.1 Nano dispatch failure is sparse: 1 of 16 robustness cells reproduced |
| F. Structure-compatible OOD | `papers/weakness_invariance_neurips/paper.md`; `papers/structure_compatible_generalization`; `experiments/structure_compatible_generalization` | Strong, needs unified packaging | ID success and OOD accuracy | compatibility with true or inferred deployment-generating transformations | wrong-group control, no-OOD-label selection, shortcut-compatible train split | parity and large symmetric groups remain degraded; topology mediation failed in one harness |

## Vector Score Axes

Report vectors, not a single leaderboard scalar.

| Axis | Question | Example metrics |
|---|---|---|
| Behavior | Does the agent succeed at the task? | final accuracy, return, tool success |
| Causal representation | Is the internal structure specific to the future-relevant variable? | moved-slot specificity, latent displacement, causal patch effect |
| Attribution | Does the agent assign outcomes to self versus world correctly? | source MAE, gauge-breaking improvement, oracle gap |
| Inquiry | Does the agent probe when information is valuable and re-engage after change? | probe efficiency, post-shift probe floor, no-false-calm |
| Commitment | Does the tracked variable survive the action interface? | parsed field correctness, repair correctness, schema validity |
| Generalization | Does the learned function preserve deployment-generating structure? | compatibility, wrong-group control, OOD-free selected OOD |

## Release Package Contract

Each suite release should include:

- a task generator with fixed seeds and declarative manifests;
- JSONL rows for each episode/model/condition/seed/provider;
- a scored summary JSON;
- a benchmark card with claims and non-claims;
- lower and upper baselines;
- anti-cheat controls;
- figure/table regeneration scripts or committed result reports;
- a public-safe source index that points to repo paths and archived PDF names.

The shared artifact contract is defined in
`docs/causally_grounded_agents_release_schema.md`, with a machine-readable
summary schema in `docs/causally_grounded_agents_release_schema.json`.

## Public Entry Points

Start here:

- umbrella benchmark: `docs/causally_grounded_agents_benchmark.md`;
- release schema: `docs/causally_grounded_agents_release_schema.md`;
- publication sharing map: `docs/publication_sharing_map.md`;
- Suite C frontier card: `experiments/world_responds/BENCHMARK_CARD.md`;
- Suite C status report: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`;
- Suite C remaining implementation gap: `docs/causally_grounded_agents_next_gap.md`;
- hardened Suite D/E card: `experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`;
- Paper 32 design note: `papers/causally_grounded_agents_benchmark/paper.md`;
- Paper 32 PDF: `papers/causally_grounded_agents_benchmark/paper.pdf`.

Run the public black-box fixture smoke test for Suite D/E:

```bash
python3 -m experiments.long_horizon_bottleneck.eval \
  --provider fixture \
  --models fixture \
  --suite prompt_family \
  --seeds 1 \
  --episodes-per-cell 1 \
  --out artifacts/long_horizon_bottleneck/fixture_public_smoke_summary.json \
  --jsonl artifacts/long_horizon_bottleneck/fixture_public_smoke_rows.jsonl
```

Run the full provider/API suites with the commands in
`experiments/long_horizon_bottleneck/README.md`.

## Regime Audit

- Old regime: separate papers and experiment cards, each with local gates and
  its own result language.
- Transition: suite-level benchmark packaging with shared score axes, schemas,
  anti-cheat controls, and minimum pass rule.
- Transported evidence: existing papers, result reports, provenance cards,
  black-box API evaluator, and long-horizon benchmark card.
- Rejected alternatives: a single scalar groundedness score; final behavior as
  sufficient evidence; source paths that only work on one local machine.
- Residual finding: Suite C is now packaged as a benchmark frontier. It has
  positive re-engagement, decision-layer cooling, and no-false-calm evidence,
  while strict recovery and public JSONL cost-normalized scoring remain partial.
- Readiness: Suite D/E is release-hardened; Suite A/B/F are strong but need
  packaging convergence; Suite C has a public card/status but still needs a
  first-class Paper 23B runner.
- Allowed claim: diagnostic benchmark release scaffold for finite agents, not
  a consciousness test, production reliability certificate, human behavioral
  result, or neural validation.
- Next operation: implement the reusable Suite C Paper 23B runner described in
  `docs/causally_grounded_agents_next_gap.md`.

## Non-Claims

This benchmark does not certify consciousness, full autonomy, production tool
reliability, broad OOD robustness, or human/neural validity. It gives controlled
finite evidence about whether success is tied to the causal surfaces that future
action depends on.
