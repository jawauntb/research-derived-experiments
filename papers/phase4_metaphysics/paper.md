# Learning the Missing Conditions

Jawaun Brown

Research-Derived Experiments - Phase 4 diagnostic suite

## Abstract

Phase 3 identified several open bottlenecks in the Metric Stack of Concern:
language scale, non-enumerative symmetry discovery, learned regime variables,
probe value, architecture beyond the mediated-identifiability ceiling,
foundation-model-style metric deformation, and topology mediation. This paper
reports a controlled Phase 4 diagnostic suite that turns those bottlenecks into
seven cheap L4-parallel gates. The allowed claim is bounded: these experiments
resolve mechanism choices inside controlled harnesses and identify which claims
deserve heavier external validation.

## 1. Claim Boundary

The suite is not a proof of foundation-model or biological generality. It is a
diagnostic bridge between the Phase 3 papers and more expensive experiments:
each open question is translated into a falsifiable harness, negative controls,
and a predeclared gate. A mechanism is promoted only when it clears its own gate;
failed tracks stay visible as bounded negatives.

The full run used 336 Modal L4 cells and produced 1440 result rows. The runner
estimated a conservative timeout-bound cost of $67.13 against the $1000 cap, so
the result remained far below the budget requested for Phase 4.

## 2. Experiment Manifest

| Track | Question | Primary controls |
| --- | --- | --- |
| `language_scale` | Does hidden paraphrase geometry couple to action-like behavior under sharper log-prob metrics? | pre-action coupling, random prompt fraction |
| `neural_symmetry` | Can a neural transformation generator discover non-enumerative symmetries? | raw generator, pixel enumeration |
| `learned_regimes` | Can state-dependent concern learn explicit regime variables near singular boundaries? | smooth/state-blind baseline, oracle boundary |
| `probe_value` | Does probe value track marginal information gain rather than current error? | current error, ensemble variance, current replay, random |
| `beyond_ceiling` | Can architecture break the mediated-identifiability ceiling? | shared head, wrong-history head |
| `semantic_metric` | Can metric deformation transfer to semantic-style embeddings? | frozen encoder, random value field |
| `topology_mediation` | Does topology mediate OOD generalization, or does another variable carry the effect? | broken seam, forced topology, seam partials |

## 3. Gate Results

| Track | Status | Key result | Interpretation |
| --- | --- | --- | --- |
| `language_scale` | FAIL | post-logprob r = 0.670, intervention ratio = 2.360 | Hidden geometry predicts behavior, but causal controller strength did not reach the 3x threshold. |
| `neural_symmetry` | PASS | closure F1 = 0.945, raw F1 = 0.568 | Non-enumerative discovery works when the generator is closure constrained. |
| `learned_regimes` | PASS | learned return = 50.0, oracle return = 50.0, smooth boundary acc = 0.5 | Regime variables can be learned when hard partitions are in the hypothesis class. |
| `probe_value` | PASS | learned VOI reduction = 0.323, Spearman = 0.840 | Probe policy should estimate marginal information value, not current error. |
| `beyond_ceiling` | PASS | role MAE = 0.036, MoE MAE = 0.039, shared MAE = 0.205 | The Phase 3 ceiling is architectural in this harness. |
| `semantic_metric` | PASS | moved-location lift = 0.508, specificity = 0.504 | Value-weighted metric deformation works in a controlled semantic embedding harness. |
| `topology_mediation` | PASS | topology partial drops from 0.208 to 0.004 after seam control | Seam consistency carries the observed OOD topology mediation. |

Overall suite status is therefore mixed rather than a clean pass. Six tracks
resolve their controlled mechanism question; one track, language scale, becomes
a sharper open problem.

## 4. Main Findings

First, language geometry is real but not yet a controller. Larger model-like
settings show the expected paraphrase/log-prob correlation, but intervention
specificity only reaches 2.36x against the pre-action baseline. That is useful
evidence for hidden paraphrase geometry, not enough evidence for a strong
behavioral coupling claim.

Second, non-enumerative symmetry discovery needs structure. A raw neural
proposal is brittle, but closure-constrained generation recovers high F1 and
keeps the OOD lift associated with enumerative discovery.

Third, regime variables are learnable when the architecture can represent a
hard partition. Smooth approximators remain exactly the wrong tool at singular
boundaries; they can average over the boundary and lose the intervention.

Fourth, useful probes are value-of-information probes. Current error and
ensemble variance can miss reducible uncertainty. The learned VOI policy
selects points that change the model, not merely points where the current model
looks wrong or noisy.

Fifth, the mediated-identifiability ceiling is not only statistical. Shared
heads remain capped, while disjoint per-role and mixture-of-experts heads break
the ceiling under richer counterfactual variation.

Sixth, semantic metric deformation and topology mediation both remain bounded.
Value fields move metric density in the controlled semantic harness; topology
helps OOD only through seam consistency, so topology alone is not the causal
story.

## 5. Discovery-Regime Audit

Old regime: Phase 3 could measure concern-like structure in minimal agents, but
left several variables oracle-specified or architecturally capped.

Transition: Phase 4 adds learned regime gates, marginal probe-value targets,
role-routed mediated heads, semantic-style metric deformation, and seam-aware
topology mediation.

Transported evidence: the null-anchored, current-replay, habituation,
role-specific ceiling, and metric-deformation claims are preserved as baselines.

Rejected alternatives remain visible: raw neural symmetry proposal,
current-error probe value, smooth boundary heads, shared mediated heads, and
topology without seam consistency.

## 6. Next Operations

Expensive compute should now be spent only where this suite says the hypothesis
is live: larger real language models for paraphrase action coupling, learned
closure-constrained transformation generators, richer homeostatic environments
with learned regime variables, true VOI probes under distribution shift,
role-routed self/world heads, and foundation-model semantic metric deformation.

Failed or bounded tracks should be carried forward as controls, not erased.
