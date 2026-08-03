# Concern–Fisher Pair (Theorems CG-1 and CG-2 witness)

Companion instrument for [`papers/concern_as_fiber_geometry/paper.md`](../../papers/concern_as_fiber_geometry/paper.md).

Hypothesis: on the 4-bit Boolean world of Instrument 4, with the concern
sufficient statistic `T(x) = (2·x_0 − 1, 2·x_2 − 1)`,

- **Theorem CG-1 (Fisher on the fiber).** The empirical Fisher matrix
  `β² · Cov_{c,z}[T]` on every fiber equals the closed form
  `β² · diag(sech²(β c_1), sech²(β c_2))` — independent of `z`, diagonal,
  with entries in `(0, β²]`.
- **Theorem CG-2 (Holonomy = signed enclosed area × ε).** For the
  non-exact concern-1-form `α + ε · (−c_2 dc_1)`, the holonomy around a
  closed loop in `c`-space at fixed `z` equals `ε · (signed area enclosed)`
  by Green's theorem. The exact part `α = β·E_c[T] dc` integrates to zero
  around any closed loop by exactness.

Method: exact enumeration of the 16-element Boolean world; closed-form
Fisher matrix comparison at 4 concern values × 4 fibers = 16 grid points;
trapezoidal quadrature (500 steps per edge) of the holonomy line integral
along both a unit rectangle and a right triangle at `z = (1, 1)`.

Pre-registered gates:

- `cg1_empirical_fisher_matches_predicted`: max abs diff ≤ 1e-12 across
  the 4×4 grid.
- `cg1_fisher_is_diagonal_at_every_grid_point`: off-diagonal entries
  exactly zero (independence of `T_1 ⟂ T_2` under `K_c`).
- `cg2_rectangle_holonomy_matches_area_epsilon`: rectangle area = 1 →
  holonomy = ε = 0.3, matched to 1e-3.
- `cg2_triangle_holonomy_matches_half_epsilon`: triangle area = 0.5 →
  holonomy = 0.15, matched to 1e-3.

Result: all four gates pass exactly to the pre-registered tolerance.
Empirical Fisher matches closed form to machine precision; both
holonomies match Green's-theorem prediction to trapezoidal-quadrature
error (`< 5e-6` at 500 steps per edge).

**Two mistakes were caught by this instrument on first run** (worth
documenting because they illustrate the value of exact numerical witnesses
for informal derivations):

1. The paper's original concern statistic `T = (x_0 − x_1, x_2 − x_3)` is
   identically zero on the fibers where `x_0 = x_1` — half the world.
   Fisher information degenerates there. The instrument reported
   `cg1_empirical_fisher_matches_predicted: false` immediately; the
   corrected statistic `T = (2·x_0 − 1, 2·x_2 − 1)` reads a different bit
   that varies non-trivially on every fiber and satisfies the theorem.
2. The paper's original "non-exact" 1-form
   `ε · (z_2 dc_1 − z_1 dc_2)` (with `z` fixed) is trivially exact on `ℝ²`
   with potential `Φ = ε(z_2 c_1 − z_1 c_2)`, so its holonomy is zero on
   every loop — the exact opposite of the paper's claim. The instrument
   reported `cg2_triangle_holonomy_is_epsilon: false`. Corrected form
   `α + ε(−c_2 dc_1)` has curl `+ε` and satisfies Green's theorem:
   holonomy = ε × signed enclosed area, non-zero on all non-degenerate
   loops.

Run:

```bash
python3 experiments/concern_fisher_pair/experiment.py
```
