# Memory — SIC Dynamics

Durable facts. Append. Do not rewrite history to make the narrative simpler.

## House claim

- Possibility 5 is the close: delete–repair is SIC's dynamics, not a second
  master object. Papers A–F are banked. Written κ is Theorem 4 plus a named
  total order (`calculus_is_sic`).
- Possibility 1 as a *new* cheap function is dead: κ_cheap collides.
- Possibility 3 (one ladder) is dead on the A/B harness.
- Possibility 4 (unique linear hierarchy) is dead: Path A/B disagree.
- Possibility 6 (Lorentz = Lamport = PE) is dead on the diamond fibre.

## Already Lean (cite, do not rebuild)

- `StructuralIntelligence.DeleteRepair.repair_paths_disagree`
- `StructuralIntelligence.DeleteRepair.cycle_integrates_iff_sum_zero`
- `StructuralIntelligence.CommonSuffScreen` (coarsest CSS / Theorem 4)
- `StructuralIntelligence.EmlZeroIdentity.eml_zero_identity`
- `StructuralIntelligence.Compiler.SquaringSeparation`

## Paper F collision (κ_cheap)

Same cheap 5-field signature, two golds:

- `bag_q_id`, `last_bit_q_id`, `parity_q_id` → gold `quotient`
- `pair_eq_q_id` → gold `noop`

κ_screen hits 11/11 and looks at the disclosed menu. `bag` has 5 representing
screens; uniqueness is dead. Relabel `0↔3` sends `first_bit`/`q_stab0` to
`last_bit`/`q_stab_last`.

## Paper E miss

- Held-out miss: `pair_eq` on `q_id`. Policy said `quotient`; gold is `noop`.
- Unused symmetry is not leftover privilege.
- Held-out Aff cycle C: `((1,0),(1,0),(2,1),(2,2))`, holonomy `(1,1)`,
  Kirchhoff `(1,0)`. An earlier Kirchhoff-flat C was a bug, not a result.

## Paper C / D

- Aff(1, Z/3) holonomy is not integer Kirchhoff. Not Lorentz.
- 196 diamonds; `s² ∈ {-1,-3,-4,-8}`. Poset does not determine the interval.

## Process-split (do not formalize the ratios)

- Gibbs feels `Φ` (2 vs 1 min-shell).
- Known-tree GD feels `Φ` (8/8 vs 6/8).
- Unknown-tree GD does not (7 vs 7).
- Frozen-leaf extras 43 vs 28 feel `Φ` but are not the Gibbs ratio 2.016.

## Wave 2 banked (2026-08-17)

Append. Files are on `main` under `formal/structural-intelligence/`.
Aggregator imports them. Label: **proved-not-verified**.

- `KappaCheap.kappa_cheap_not_function`
- `KappaScreen.kappa_screen_hits_suite`
- `KappaUnique.bag_not_unique`
- `KappaRelabel.kappa_relabel_natural`
- `Aff13.affine_escapes_kirchhoff`
- `DiamondInterval.poset_not_determine_interval`
- `SurgeryMiss.surgery_miss_pair_eq`

## Wave 2 SafeVerify (2026-08-17)

Append. Receipt: `docs/lea/VERIFY_RECEIPT_2026-08-17.md`.

- verified: `kappa_cheap_not_function`, `bag_not_unique`, `kappa_relabel_natural`, `affine_escapes_kirchhoff`, `poset_not_determine_interval`, `surgery_miss_pair_eq`
- later verified: `kappa_screen_hits_suite` (kernel `decide`, no `native_decide`)
- verified: `dta_n4_representable_iff`, `swap_typed_wins`

## Wave 5 (2026-08-18) — the three doors in Lean

Append. Kernel `decide` only, axioms ≤ {propext}; several
GeneratorBorder headlines use no axioms at all.

- `MenuBlind.gold_flip_pair_eq` / `gold_flip_pair23` — gold is
  menu-relative (noop → quotient).
- `MenuBlind.menu_blind_kappa_impossible` — two-point kill of every
  menu-blind κ.
- `MenuBlind.base_gold_consistent` — menu-parameterized gold equals
  Wave 2 gold on the base menu (30 combos).
- `GeneratorBorder.*` — sq episode (9 vs 89 trees, min 7 vs 3, mass
  5 vs 14) and cube episode (4 vs 17 trees, min 5 vs 2, mass 2 vs 3);
  base embeds in ext; `min_size_not_shared_function`.
- `ConcernChoice.*` — six concern choices (four distinct screens,
  mirrored duals), sum-gap 21 over the concern-free choice,
  `boundary_base` k = 22 (ε = 11/27), `boundary_ext` k = 14
  (ε = 7/27): the concern boundary is menu-relative.
- Lean caught a transcription error the Python tests never asserted:
  the cube-episode extended universe has **17** trees at bound 5, not
  9. Enumerate in the kernel; do not trust prose counts.

## Wave 6 (2026-08-18) — essay-driven files, all SafeVerify-passed

Append. Driven by "Intention Is All You Need" v3 and its review.

- `CrossingUnique.crossing_unique` — proved by an **autonomous Lea
  run** (52 s, decide + omega), verified via Lea `/verify` AND the
  4.29 replay. First fully Lea-proved node in the repo.
- `MeaningVsCompany.*` — meaning quotient vs co-occurrence quotient
  incomparable on the registered six-message world; instantiates
  `CausalSemantics.PsiEquiv`; three headlines axiom-free.
- `WeakestAdequate.*` — the essay's D13 "largest region" does not
  exist (kernel counterexample); repair = maximal region under a
  **disclosed completion order** (greedy is order-dependent — the
  κ_screen tie-break lesson recurring).
- `KleisliSection.*` — sections of a quotient are spec-level
  indistinguishable; section space closed under fiberwise swaps;
  2×2 witness has exactly 4 sections, one shadow.
- `DialZero.*` — level-set partition has zero task-distortion, every
  zero-distortion encoder refines it, no two-cell partition works on
  the witness. Theorem B's "cells coarsen" wording is withdrawn per
  review; safe claim = optimal rate falls.
- Lea ops: default `max_turns = 20` is too small for multi-theorem
  proof-engineering runs — raised to 80 in `config/lea.local.toml`.
  The adapter must run under launchd (`com.lea.adapter`), not under
  an agent shell; shells here reap child processes between commands.
- `SilentSubstitution` (Wave 6b): Lea proved `rearrange` +
  `tilt_pointwise` (generalize-products-then-omega beats blind AC
  rewriting; ac-normalization via
  `simp [Nat.mul_add, Nat.mul_comm, Nat.mul_left_comm, …]` closes
  product equalities); the list Chebyshev induction rides on
  `sumBy_mul_left/right` + `sumBy_add` + a pointwise cross lemma.
  All SafeVerify-passed; kernel axioms `propext, Quot.sound`
  (`omega` normalizes through `Int`).

## Runbook facts (2026-08-18)

- Adapter-only start beats `start-dev.sh`: the web UI's rollup
  optional-dep bug tears the adapter down with it.
- `config/lea.local.toml` gets deleted by cleanup scripts; restore
  from the example before assuming deeper breakage.
- SafeVerify target splitter cuts at the first `:=` — no structure
  literals in theorem statements; Relabel/Surgery needed the same
  workaround in Wave 2.

## Off-limits

- Paper 0 / `Complex.log 0`
- DR/DCR text nomination
- OpenAI 2026 as theorems
- Neural bootstrap

## Wave 7 banked and verified (2026-08-18, second session)

- `EmlCatalan.lean` (EML-fib-Ck / EML-var-Ck / EML-pair-diff),
  `RepairTable.lean` (RR-1), `ObstructionTaxonomy.lean` (TA-2 discrete)
  all SAFEVERIFY_PASSED in the 4.29 scratch; axioms <= {propext}.
- New replay fact: deep kernel folds (3238-tree census) overflow the
  4.29 default thread stack; `lean --tstack=262144` fixes it. The
  replay script is `/tmp/sv429/replay7.sh`.
- `Nat.choose` does not kernel-reduce; use a structural Pascal
  `binom` when a census needs `decide`.
- Kernel catch of the wave: drafted variable-census total 4306 was
  wrong; `decide` refuted it; correct is 3238 = sum 2^(k+1)C_k, k<=5.
- Lane model note: primary-model lanes died on usage limits; Composer
  lanes (#523, #524) built both files green on the first try.
