# DR6g — Fully Domain-Blind Claude Verifier

**Package:** `experiments/dr6_code_correctness_corollary/`
**Predecessor:** DR6f (partial degradation with D-adjacent prompt)
**Date:** 2026-07-27
**Written:** BEFORE new verifiers spawned (retroactively formalised — the
setup was fixed in the prompt used for the subagent invocations).

## 0. Question

DR6f showed partial degradation when D was withheld but domain
framing preserved. Extrapolating: fully domain-blind prompt should
substantially return the wall.

## 1. Setup

Same 11 snippets as DR6d/DR6e/DR6f. Three sandboxed Claude subagents.
Prompt strips all domain framing:

> For each Python code snippet, score 0-10 how likely it is that the
> code makes ANY implicit assumption about how the world works — a
> fact about the runtime environment, external systems, data
> conventions, or user context — that is not explicit in its imports,
> types, or comments.

## 2. Gates

- **G1**: realisation median further below DR6f (9.0). GO if r_median < 9.
- **G2**: overlap gap further below DR6f (6). GO if gap < 6.
- **G3**: R6 score below DR6f's 8.
- **G4**: direct wall — min realisation ≤ max placebo.

Overall GO on the DR6g question (wall further returns) = G4 or (G1 and G2 and G3).

## 3. Prediction

Wall reappears substantially. R6 drops well below 8.

## 4. Single-shot

Three verifiers, one aggregation, one verdict. No replay.
