# SIC-A Finite Derivation Pair (Theorem SIC-A witness, finite discrete positive-support case)

Companion instrument for [`papers/structural_intelligence_foundations/paper.md`](../../papers/structural_intelligence_foundations/paper.md)
and the Lean formalisation at
[`formal/structural-intelligence-mathlib/StructuralIntelligenceMathlib/SICA_FiniteExistence.lean`](../../formal/structural-intelligence-mathlib/StructuralIntelligenceMathlib/SICA_FiniteExistence.lean).

Hypothesis: on the 4-bit Boolean world `X = {0, 1}^4` (|X| = 16) with a
strictly-positive pmf family `P(theta, .)` indexed by `Theta = X`, the
**derived** master fibration `(q, K)` from the paper — where

- `q(x)` is the LR-vector against a fixed pivot `theta_0`,
- `K(z, x)` is uniform on the fibre `q^{-1}(z)`,

realises SIC-A pointwise on the world: four exact biconditional /
equality gates witness the three-step reduction (Theorem 1 gives `q`;
Proposition 3 side conditions concrete for `K`; CS-2 coarsestness
matches the reference MSS partition).

## Setup

- `X = {0, 1}^4`, uniform-base-measure over the 16 worlds.
- `Theta = X` (a 16-element parameter set; maximally expressive).
- `P_hat(theta, x)` proportional to `2^(-hamming(theta, x))` — an
  asymmetric task-natural family that separates parameters.
- `P_smoothed = (1 - 1/17) * P_hat + (1/17) * (1/16)` — Laplace
  smoothing to enforce strict positivity (`0 < P(theta, x)` for every
  `(theta, x)`), matching the T1 hypothesis.
- `theta_0 = (0, 0, 0, 0)` (canonical pivot).
- `q(x) := (theta |-> P(theta, x) / P(theta_0, x))` (LR-vector, from T1).
- `K(z, x) := 1 / |q^{-1}(z)|` if `q(x) = z`, else `0` (uniform-on-
  fibre kernel; the canonical fibre-supported, fibre-normalised
  compiler from Proposition 3 side conditions).

All arithmetic is done in Python's `fractions.Fraction` so every
comparison and every sum is bit-exact — no floating-point roundoff, no
tolerance windows.

## Pre-registered gates

- `t1_characterisation_biconditional`: for every world pair
  `(x, x')` in `X * X` (256 pairs), `q(x) = q(x')` iff the pmf
  cross-multiplication identity
  `P(theta, x) * P(theta', x') = P(theta, x') * P(theta', x)`
  holds for every `(theta, theta')` in `Theta * Theta` (256 sub-pairs
  per world pair). This is the Fisher–Neyman characterisation of
  Theorem 1.
- `fibration_structure_biconditional`: for every `(z, x)`, `K(z, x)`
  is positive iff `q(x) = z`. This is the Proposition 3 side
  condition (`FibreSupported`) made concrete.
- `fibre_normalisation_sums_to_one`: for every `z` in `image(q)`,
  `sum_x K(z, x) = 1` under exact rational arithmetic. This is the
  Proposition 3 side condition (`FibreNormalised`) made concrete.
- `lr_partition_equals_reference_mss_partition`: the fibre partition
  induced by the LR-vector equals the reference minimal sufficient
  statistic partition on `X`, bit-exact as a set of frozensets. This
  is the CS-2 minimality direction — no coarser statistic exists that
  is still sufficient.

## Result

All four gates pass exactly. The instrument is deterministic (no
seeds, no Monte Carlo, no sampling). The 4-bit world produces
`|image(q)|` fibres of specific sizes reported in the summary JSON.

## Two ways this could have failed and what they would have meant

1. **T1 characterisation biconditional fails.** Would mean either the
   LR-vector is not sufficient (contradicts T1) or the cross-
   multiplication identity does not correspond to the LR-vector fibre
   equality — implying a numerical bug in the paper's characterisation
   claim. Instrument would catch this on first run.
2. **Fibre normalisation drifts from 1.** Would mean the uniform-on-
   fibre kernel is not actually a probability distribution on the
   fibre — implying the Proposition 3 side condition
   (`FibreNormalised`) is misstated for this construction. Instrument
   catches any deviation to full rational precision (not just to
   `1e-12`).

Neither happens on this world under the smoothed pmf; both gates
report bit-exact equality.

## Run

```bash
python3 experiments/sica_finite_derivation_pair/experiment.py
python3 -m unittest tests.test_sica_finite_derivation_pair
```

## Cross-references

- Paper: `papers/structural_intelligence_foundations/paper.md`
- Lean theorem: `sic_a_finite_discrete` in
  `formal/structural-intelligence-mathlib/StructuralIntelligenceMathlib/SICA_FiniteExistence.lean`
  (axiom footprint: `[propext, Classical.choice, Quot.sound]` — no new
  project axioms)
- Coarsestness corollary: `sic_a_finite_discrete_coarsest` in the same
  file (inherits `HalmosSavage_minimality_h_extension` from Theorem 1).
