# E7 — Selective Load-Bearing Subspace Protection for Continual Learning

**Frozen: 2026-07-13 (UTC)**, before any E7 harness is written or run.

## Relationship to prior work

This prereg builds directly on the #344 result frozen in
`e2_e3_rank_normalized_patch_preregistration_2026-07-10.md`: a
compatibility-aligned activation subspace, fit from last-hidden-layer
activation means grouped by `(a + b) mod n`, taking the minimum SVD rank
explaining ≥50% of between-orbit spectral mass, with a validated,
width-stable, spectral-mass-normalized group-specific causal patch-CE and an
`a`-only wrong-subspace matched control. E7 does not reinterpret or relax any
#344 gate. It treats that identified subspace as a *protected object* and asks
a new, downstream question about continual learning. E7 inherits the E2/E3
modular-arithmetic MLP setup unchanged (widths `{96,128}`, depth 2, subspace
target mass 0.50, four seeds, OOD evaluation on a frozen strict-subset split).

## Question

Continual-learning stability methods (EWC-style Fisher-weighted anchoring; cf.
Dohare et al., *Loss of plasticity in deep continual learning*, Nature 2024,
arXiv:2404.00781, and the slowing-forgetting line arXiv:2411.06916) treat the
stability–plasticity dilemma as a **uniform** trade-off: every retained weight
is anchored, and plasticity is paid down uniformly to buy retention. The
commitment-surface framework predicts an asymmetry: forgetting a *load-bearing*
mechanism is catastrophic, forgetting a *footprint* is free. Does protecting
**only** the #344 transported causal compatibility subspace, across a sequence
of tasks, beat uniform EWC-style protection on the stability–plasticity
frontier **without** paying the uniform plasticity tax on footprint weights?

## Competing explanations

- **H_uniform (the trade-off is necessary):** retained OOD accuracy and
  load-bearing patch-CE on earlier tasks can only be preserved by anchoring in
  proportion to a global importance estimate (Fisher). Selectively protecting a
  low-rank causal subspace either fails to preserve earlier-task load-bearing
  structure (no better than naive fine-tuning) or, if it does preserve it,
  pays the same plasticity cost as EWC. The subspace carries no special leverage.
- **H_subspace (load-bearing protection escapes the trade-off):** the #344
  subspace concentrates the earlier-task causal mechanism into a small,
  transportable object. Freezing/penalizing motion *inside that subspace only*
  retains earlier-task load-bearing patch-CE and OOD accuracy comparably to or
  better than uniform EWC, while leaving the complementary (footprint) weight
  directions free, so new-task plasticity is not taxed. Protecting the `a`-only
  wrong subspace, being causally inert, does not reproduce the stability gain.

## Frozen design

### Task stream

- Base regime: modular-addition MLP, depth 2, widths `{96,128}`, exactly as
  E2/E3. A task is a modulus/orbit-shift configuration. Freeze **K = 4**
  sequential tasks as an ordered stream over moduli
  `T = [17, 19, 23, 29]` (T1..T4), each with train fraction `0.5` and a
  frozen strict-subset OOD complement. The task order is frozen and never
  permuted. Tasks are presented strictly sequentially; when training task
  `T_j`, only `T_j` data is available (standard continual-learning contract).
- 1,000 epochs per task (matching E2/E3 training budget), identical optimizer,
  identical initialization per (seed, width) across arms.

### Arms (matched parameter/compute budget)

All arms share architecture, epoch count, optimizer, batch schedule, and
per-(seed,width) initialization. They differ only in the per-task protection
regularizer applied while training `T_{j>1}`:

- **P_none** — naive sequential fine-tuning; no protection term. Forgetting
  floor.
- **P_ewc** — uniform EWC: diagonal-Fisher-weighted L2 anchor to the
  post-`T_{j-1}` parameters over *all* weights. Baseline uniform trade-off.
- **P_sub** — protect the #344 compatibility subspace only: after each task,
  re-fit the between-orbit subspace (min rank ≥50% between-orbit spectral mass)
  from that task's activations, and penalize the component of subsequent
  parameter updates that moves the model's realized activations inside that
  identified subspace (equivalently, anchor only the projection of the update
  onto the accumulated protected subspace). Complementary directions are free.
- **P_wrong** — matched control: identical machinery to P_sub but protecting
  the `a`-only wrong subspace from #344. Must **not** reproduce P_sub's
  stability advantage.

Protection strength (the single scalar coefficient λ shared by P_ewc / P_sub /
P_wrong) is fixed *once* on the CPU/dev pilot and frozen for the confirmatory
grid; it is never per-arm or per-cell retuned. The subspace target mass stays
0.50 (inherited, not re-selected). Compute is matched: P_ewc, P_sub, P_wrong
each pay one extra backward-projection per step; P_none omits it but runs the
same step count. Any per-arm wall-clock or step-count divergence >2% is a
harness bug, not a result.

### Per-task, per-arm metrics

After training each task `T_j`, for every earlier task `T_{i≤j}` and the
current task, record on the frozen OOD split:

1. **Stability:** retained OOD accuracy on each earlier task `T_{i<j}`.
2. **Plasticity:** new-task OOD accuracy on `T_j`.
3. **Load-bearing retention:** normalized compatibility-subspace patch-CE on
   each earlier task `T_{i<j}` (patch-CE divided by realized removed
   spectral-mass fraction, exactly the #344 normalization), plus the
   wrong-subspace control CE.
4. **Plasticity indicator:** last-hidden-layer effective rank (participation
   ratio of activation singular values) and dead-unit fraction (units with
   near-zero activation variance on OOD), per the loss-of-plasticity
   literature.

Record realized selected rank, realized removed mass, and per-matrix
protected-subspace projection norm for every cell.

### Seeds and cell count

- Frozen base seed: **`202607131200`**.
- Per-object seed: `SHA-256(base_seed ‖ task ‖ arm ‖ seed_index ‖ width)`,
  namespaced, collision-checked, taken mod 2³¹, exactly as E1/E5 derive RNG
  keys. No two cells share a derived seed.
- Four seeds per arm (`seed_index ∈ {0,1,2,3}`).
- Cell count: 4 arms × 2 widths × 4 seeds × 4 tasks = **128** trained
  checkpoints (32 task-streams: 4 arms × 2 widths × 4 seeds, each a 4-task
  sequence). Earlier-task retention metrics are evaluated at every task
  boundary, so stability rows number 4 arms × 2 widths × 4 seeds ×
  (0+1+2+3) = 192 (earlier-task, task-boundary) evaluations.

A **CPU/dev pilot** (one seed, width 96, K=2 tasks, all four arms) precedes any
larger spend. It fixes λ, validates the seed derivation and the exposure/budget
accounting, and confirms integrity checks pass. It cannot support a scientific
claim; only the full four-seed, two-width grid can.

## Frozen analysis

All numerical gates are macro means over matched valid cells; a cell is valid
only if the budget-match check holds and its realized protected-subspace
removed mass is within `±0.02` of 0.50 (inherited #344 tolerance). Report, per
width and per arm: mean retained earlier-task OOD accuracy, mean normalized
earlier-task patch-CE retention, mean final-task OOD accuracy, and mean
effective rank / dead-unit fraction, each with across-seed dispersion. Report
the joint (stability, plasticity) operating point per arm/width. Comparisons
use the frozen margins below; no margin may be moved after inspecting any cell.

## Gates & kill criteria

The claim that selective load-bearing subspace protection escapes the uniform
trade-off passes only if **all** gates hold.

- **G1 (stability):** P_sub retains earlier-task normalized compatibility
  patch-CE strictly better than P_none by ≥ **+0.05**, at **both** widths.
  (Selective protection actually preserves the load-bearing mechanism.)
- **G2 (plasticity, no uniform tax):** P_sub final-task OOD accuracy ≥ P_ewc
  final-task OOD accuracy − **0.02**, at **both** widths. (Selective protection
  does not pay the uniform plasticity tax; a frozen tolerance, not superiority,
  is required here.)
- **G3 (frontier dominance):** at both widths, P_sub's joint operating point
  dominates P_ewc — retained earlier-task OOD accuracy ≥ P_ewc's by ≥ **+0.03**
  **and** G2 holds — so P_sub is not merely trading one axis for the other.
- **G4 (specificity):** P_wrong does **not** reproduce P_sub's stability
  advantage: P_sub's earlier-task patch-CE retention exceeds P_wrong's by ≥
  **+0.05** at both widths. The causally inert subspace must not help.

Any failed gate is reported as a **strict failure**. No threshold may be
retuned from observed cells; failures stay failures. A G1/G3 failure rejects
H_subspace and is evidence for H_uniform in this regime. A G2 failure means
selective protection still pays the plasticity tax — the asymmetry claim dies
even if stability improves. A G4 failure means any observed stability gain is
not attributable to the identified load-bearing subspace (a machinery/anchoring
artifact), and P_sub's result cannot be interpreted causally regardless of
G1–G3. Integrity failures (budget mismatch >2%, removed-mass out of tolerance,
seed collision, held-task data leakage across the sequential contract) kill the
affected cell and trigger a rerun; they are never repaired by post-hoc
relabeling or by loosening λ.

## Claim boundary

A pass would establish, **only** within the small modular-arithmetic MLP regime
of E2/E3 and **only** for the specific #344 identified between-orbit
compatibility subspace, that protecting a transported causal subspace beats
uniform EWC-style anchoring on the stability–plasticity frontier without paying
the uniform plasticity tax. It is **not** a claim about transformers, LoRA
adapters, Pythia, language models, or foundation models; it is not a claim
about continual learning in general; and it does not assert that the subspace
identification method transfers to any non-group task stream. The result is
bounded to this toy where the load-bearing object is already validated.

## Rejected alternatives

- **Uniform EWC only (no P_sub arm):** cannot separate "protecting the
  right subspace" from "protecting more strongly"; it presupposes the uniform
  trade-off the experiment is meant to test.
- **Protecting raw top-k weights instead of the normalized subspace:** top-k by
  magnitude/Fisher conflates mechanism with parameter scale and rank, exactly
  the confound #344's spectral-mass normalization removed; rejected in favor of
  the mass-normalized between-orbit subspace.
- **Single width:** #344's central lesson is width stability; a one-width result
  cannot distinguish a load-bearing subspace from a width-specific artifact.
  Both `{96,128}` are required and gated independently.
- **Unmatched compute/parameter budget across arms:** any stability or
  plasticity gap could be bought with extra steps or capacity; the ≤2%
  budget-match check is mandatory and unmatched arms are invalid, not results.
- **Dropping P_wrong:** without the causally inert matched control, a stability
  gain cannot be attributed to the load-bearing subspace rather than to the
  anchoring machinery itself; G4 is non-optional.
