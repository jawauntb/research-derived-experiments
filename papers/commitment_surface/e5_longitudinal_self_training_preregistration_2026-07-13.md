# E5-L — Longitudinal Generator-vs-Coverage Inside a Self-Training Loop

**Frozen: 2026-07-13 (UTC)**, before any E5-L cell is run. This preregistration
does not alter or reinterpret E5's frozen 2026-07-10 gates in `PLAN.md`; it
turns E5's single-shot generator/coverage separator into a per-round instrument.
**This preregistration authorizes no GPU run.** A dev calibration precedes any
confirmatory GPU spend, mirroring E5's `confirmatory_ready` discipline.

## Question

Self-training methods (STaR, V-STaR, ReST-MCTS* arXiv:2406.03816) cannot tell
whether an improvement round **learned the generator** (real, transportable
capability) or merely **expanded labeled coverage** that mimics generalization;
"Mirage of Mastery" (arXiv:2506.18998) shows models inflate self-knowledge by
memorization. E5 built a controlled causal separator (5 leakage-separated arms,
held-out support, novel-shift / paraphrase transport, W-reg sharing G-reg
exposure). E5-L asks: **does self-training collapse / plateau onset coincide
with a round where coverage-gain continues but generator-gain stalls or
reverses** — i.e. the model compounds memorized coverage, not capability?

## Competing explanations

- **H_capability-compounding.** Each accepted self-label teaches transportable
  rule structure. Generator-gain (G-reg vs A-ref on frozen novel-shift /
  paraphrase, with patch-CE) rises monotonically with OOD accuracy; there is no
  round where coverage-gain outruns generator-gain before onset.
- **H_coverage-compounding-then-collapse.** Self-acceptance mostly memorizes
  held-out labels. OOD rises while unaccepted transport structure is neither
  learned nor patch-causal; at plateau/collapse onset r*, coverage-gain > 0
  while generator-gain ≤ ε_gen (stalls or reverses).

## Frozen design

Reuse the E5 Pythia-LoRA modular-arithmetic harness and arms (`e5_core.py`:
G-reg, B-ref, W-reg, Cov, A-ref) unchanged, wrapped in a round index r = 1..R.

- **Frozen grid.** R = 6 rounds; sizes {70m, 160m, 410m}; moduli {13, 17, 23};
  seeds {20260709, 20260809, 20260909}; 5 arms; train_frac 0.5;
  train_shift_count 3; augmentation_multiplier 3; spectral_mass_fraction 0.5;
  lora_rank 8; **160 epochs per round** (E5 confirmatory value). All non-round
  fields equal `E5_CONFIRMATORY_PARAMETERS`; any drift is non-confirmatory.
- **Expected cell count = R × sizes × moduli × seeds × arms
  = 6 × 3 × 3 × 3 × 5 = 810.** A round is a *matched round set* over all 5 arms
  at fixed (size, modulus, seed); no arm may be dropped from a round.
- **One self-training round r.** (1) The self-trained model M_{r-1} generates M=5
  greedy+sampled candidates per held-out input on the frozen S_ood support.
  (2) STaR/ReST selection: accept an input's self-consistent answer as a new
  pseudo-label iff ≥ m=4 of M=5 generations agree (self-consistency; no ground
  truth on S_ood is ever consulted). Accepted labels — correct or wrong — enter
  the **coverage channel only** (B-ref / Cov). (3) M_r fine-tunes for 160 epochs.
  (4) The E5 separator re-derives all 5 arms at M_r's state and emits per round:
  generator-learning score (G-reg vs A-ref), coverage score (Cov / B-ref),
  group-specificity control (W-reg), normalized compatibility-subspace patch-CE
  (#344, canonical + paraphrase), and canonical + paraphrase OOD accuracy.
- **Anti-leakage contract, every round** (E5 `validate_exposure_plans`,
  reasserted at each r): no S_ood truth label enters G-reg or W-reg; the
  self-accepted pseudo-labels feed only B-ref / Cov, never G-reg / W-reg;
  Cov exactly matches B-ref held-out unique-input and event coverage that round;
  W-reg shares G-reg supervised exposure and its
  (source_input, intervention_id) consistency schedule; no k ∈ K_novel appears
  in any intervention pair. K_novel and the paraphrase split are frozen at r=1
  and are excluded from self-acceptance in every round (transport is never
  self-labeled).
- **Seeds.** Base seed **20260713**. Per-cell RNG is a SHA-256 namespaced
  derivation over `f"{20260713}|e5l-longitudinal-v1|r{r}|{size}|n{n}|s{seed}|{arm}"`
  (first 8 digest bytes → uint64), collision-free across the 810 cells.

## Frozen analysis

Per valid round r and matched (size, modulus, seed) cell:

- `gen_score(r)` = G-reg − A-ref canonical OOD accuracy (measured on frozen
  novel-shift ∧ paraphrase; A-ref = no-intervention baseline at M_r).
- `cov_score(r)` = Cov − A-ref canonical OOD accuracy (Cov matched to B-ref
  coverage that round).
- `gen_gain(r) = gen_score(r) − gen_score(r-1)`;
  `cov_gain(r) = cov_score(r) − cov_score(r-1)` (r ≥ 2).
- `O(r)` = self-trained model M_r held-out OOD accuracy, **min of canonical and
  paraphrase** (transport-enforced), the deployed self-training trajectory.

**A-priori onset detector (frozen, from `O(r)` only).** Onset round r* is the
first r ≥ 2 with either **plateau** — `O(r) − max_{s<r} O(s) < δ_plateau` (no new
best beyond tolerance) — or **collapse** — `O(r) − O(r-1) ≤ −δ_collapse`.
Freeze δ_plateau = 0.01, δ_collapse = 0.05. The detector never reads
gen/cov/patch. A trajectory with no onset by r=R contributes only to G1/G3/G4.

**Pre-committed G2 statistic.** For each cell with an onset r*, the joint event
`E = [cov_gain(r*) > 0] ∧ [gen_gain(r*) ≤ ε_gen]`, ε_gen = 0.02 (frozen).
Primary statistic: the fraction of onset-bearing cells with E true. Report per
size and per modulus; also report gen_gain(r*) and cov_gain(r*) distributions.

## Gates & kill criteria

Macro means over matched valid cells; no threshold may be retuned from observed
cells; any failed gate is a **strict failure**; failures stay failures.

- **G1 — separator integrity (per round).** E5 integrity gates 1–5 hold for
  every arm at that round (train/OOD disjoint; G-reg/W-reg zero held-out truth;
  Cov = B-ref coverage; no K_novel in interventions; normalized patch removes
  the configured spectral-mass fraction within ±0.02). Any failure **voids that
  round** for that cell (rerun; never repair by relabeling), and voids G2 if it
  falls on r* or r*−1.
- **G2 — predictive (primary).** Onset coincides with coverage-without-generator
  iff the G2 statistic ≥ 2/3 of onset-bearing cells satisfy E, with a Wilson
  95% lower bound > 0.5. Below that bound → **H_coverage-compounding-then-
  collapse not supported**; strict failure of the central hypothesis.
- **G3 — group-specificity.** At r*, generator-gain must be group-specific:
  G-reg exceeds W-reg by ≥ 0.10 on both canonical OOD and novel-k equivariance
  accuracy. Failure blocks any generator-specific reading of the gain even if
  G2 fires.
- **G4 — transport.** Every gen_score / gen_gain is measured on frozen
  novel-shift / paraphrase, never on train support; G-reg paraphrase OOD lift
  retains ≥ 75% of its canonical lift and G-reg normalized patch-CE ≥ 0.05
  (canonical and paraphrase) in the rounds entering G2. A gain that fails
  transport or patch-CE is not counted as generator-learning.
- **Confirmatory discipline.** A one-seed 70m / n=13 / R=6 smoke is harness
  validation only (arms complete, finite metrics, G1 passes every round); it
  **cannot** support a claim, and reading it as confirmatory is a protocol
  violation. Confirmatory requires the full 810-cell grid complete, every round
  G1-valid, finite gate metrics for all 5 arms
  (E5 `confirmatory_ready` semantics), before G2–G4 are interpreted.

## Claim boundary

Bounded to modular arithmetic on Pythia-70m/160m/410m LoRA under this frozen
self-training loop. A confirmed G2 shows onset **correlates** with
coverage-gain-without-generator-gain; it does **not** prove that memorized
coverage *causes* collapse — the causal claim would need an intervention that
suppresses the coverage channel and shifts onset, which is out of scope here.
No result licenses claims about language self-training, non-group tasks, other
selection rules, or R > 6.

## Rejected alternatives

- **Aggregate-only.** Reporting mean OOD per round without the per-round
  generator/coverage decomposition — cannot separate the two mechanisms and is
  the exact confound E5 was built to break; rejected.
- **Unpaired arms.** Comparing G-reg and Cov / W-reg across different
  (size, modulus, seed, round) rather than within a matched round set — breaks
  E5's exposure and schedule matching; rejected.
- **Post-hoc onset.** Defining r* after inspecting gen/cov trajectories, or
  tuning δ_plateau / δ_collapse / ε_gen to the observed onset — the onset
  detector reads `O(r)` only and all thresholds are frozen above; rejected.
- **Smoke as confirmatory.** Treating the single-seed smoke or a partial /
  round-voided grid as evidence for G2 — forbidden by the confirmatory gate.
