# Instructions — SIC Dynamics

You are formalizing already-banked claims from the delete–obstruction–repair
program. You are not inventing a new calculus.

## Goal

Prove the ready nodes in `.lea/blueprint.md`. Prefer finite discrete objects.
Specify types, domains, and quantifiers before tactics.

## Hard rules

- Proved (elaborates, no `sorry`) is never the same as verified (SafeVerify).
- Do not import Mathlib into this repo's mathlib-free cores:
  `DeleteRepair.lean`, `EmlZeroIdentity.lean`, `Compiler/SquaringSeparation.lean`.
- Do not re-prove `repair_paths_disagree`, `pathA`, `pathB`, or
  `CommonSuffScreen` / Theorem 4. Cite them.
- Do not touch `Complex.log 0` or Paper 0.
- Do not treat empirical ratios (`Φ = 2.015625`, extras `43/28`, GD `8/8`) as
  theorems.
- Do not refit Paper E's cheap signature to erase `pair_eq`.
- Do not claim Lorentz, a better LLM, or a new master object named κ.
- If a node needs analysis, say so and put it in a Mathlib-using file, not in
  the mathlib-free cores.

## Style

- One lemma per file when agents run in parallel.
- Finite types (`Fin`, explicit lists, `Bool`) over `ℝ` unless the claim is
  analytic.
- Kernel `decide` only; `native_decide` is forbidden (SafeVerify rejects it).
  Raise `maxRecDepth` / `maxHeartbeats` instead.
- No `{ field := … }` structure literals inside theorem statements (the
  SafeVerify target splitter cuts at the first `:=`); assert projections.
- Quantify over explicit lists (`∀ x ∈ [...]`), not bare inductive types.
- After a successful `lean_check`, append what worked to `.lea/memory.md`.
- After a dead end, append what failed. Do not delete earlier bullets.

## Standing mandate (2026-08-18)

Every theorem-level claim in the research repo must eventually pass
through this pipeline: proved (lake, no `sorry`), then verified
(SafeVerify, axioms ⊆ {propext}), with a receipt. The backlog of
unproved claims lives at `docs/lea/theorem_backlog.md` in the research
repo. Work it oldest-load-bearing first. Empirical process results stay
Python and must not be dressed up as theorems.
