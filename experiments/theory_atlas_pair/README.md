# Theory-Atlas Pair (Theorems TA-1 & TA-2 witness)

Companion instrument for
[`papers/theory_atlas/paper.md`](../../papers/theory_atlas/paper.md).

Hypothesis: on the 4-bit Boolean world with three context subsets
`U_1 = {x_0 = 0}`, `U_2 = {x_1 = 0}`, `U_3 = {x_2 = 0}` and target label
space `T = Z/4`, the cocycle condition
`T_jk ∘ T_ij = T_ik` is *necessary and sufficient* for a presheaf of
theories `{M_i, T_ij}` to glue to a global theory `M` on the context
union — Theorem TA-1 — and its failure classifies the obstruction by
the rank / support of the discrepancy — Theorem TA-2.

Shared chart maps (identical between the good and bad families):

- `M_1(x) = g(x)` on `U_1`,
- `M_2(x) = (g(x) + 1) mod 4` on `U_2`,
- `M_3(x) = (g(x) + 2) mod 4` on `U_3`,

for the observable `g(x) = (2·x_2 + x_3) mod 4`.

Two chart families, differing only in the transitions:

- **Good** (`T_12 = +1`, `T_23 = +1`, `T_13 = +2`): cocycle satisfied on
  the single triple `(1, 2, 3)`; discrepancy is the identity
  permutation on `T` (rank 0); pivot-through-chart-1 gluing yields the
  global theory `M = g` (single-valued on the 14-world union).
- **Bad** (`T_12 = +1`, `T_23 = +1`, `T_13 = +3`): cocycle fails on
  `(1, 2, 3)`; discrepancy is shift-by-3 on `Z/4` (rank 4, no fixed
  points); gluing is inconsistent on 6 worlds; all three `T_ij` are
  non-identity, so the failure is **spread across all pairwise
  overlaps** — the *missing-latent* signature of Theorem TA-2.

A third **phase-boundary reference family** (`T_12 = +1`, `T_23 = id`,
`T_13 = id`) is evaluated alongside as a taxonomy control: same cocycle
failure regime (non-zero discrepancy) but with the non-identity
transition supported on a *single* overlap — the *phase-transition*
signature. The gate compares all three verdicts on identical machinery.

**Method.** Enumerate the 16-element world, the three contexts, the
three pairwise overlaps, and the triple overlap. Represent each `T_ij`
as an explicit permutation of the 4-element target alphabet. Compute
the cocycle discrepancy `T_13^{-1} ∘ T_23 ∘ T_12` as a permutation on
`T`; report its rank (number of moved elements) per triple. Attempt to
construct a global theory by fixing `ψ_1 = id`, setting `ψ_i = T_1i^{-1}`
for `i > 1`, and comparing the candidate values `ψ_i(M_i(x))` at every
world in every context; consistent iff all charts agree on every
overlap.

Pre-registered gates (all four pass exactly):

- `ta1_good_charts_satisfy_cocycle`: cocycle holds on every triple for
  the good family.
- `ta1_bad_charts_violate_cocycle`: cocycle fails on at least one
  triple for the bad family.
- `ta1_glue_iff_cocycle`: good family glues; bad family does not.
- `ta2_bad_discrepancy_matches_missing_latent_signature`: bad family is
  classified as `missing_latent`; phase-boundary reference is
  `phase_transition`; good family is `glue`.

Result: all four gates pass. Bad-family discrepancy rank is 4 (maximal
on `Z/4`); every pairwise transition is non-identity; gluing fails on
6 of the 14 union worlds. Phase-boundary reference has one
non-identity transition (`T_12`) and two identity transitions; its
verdict is `phase_transition`. The taxonomy separates cleanly on
identical machinery.

Run:

```bash
python3 experiments/theory_atlas_pair/experiment.py
```
