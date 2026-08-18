# EML variable-`x` spectrum

Leaf-labeled grammar `S → 1 | x | eml(S,S)` with
`eml(a,b) = exp(a) - ln(b)`. Every tree is a real function of `x>0`
or undefined. There is no 1-D integer invariant like polynomial degree.

Banked:

- Counts through 5 internal nodes equal `2^{k+1} C_k` (3238 trees).
- Exact same-size functional split: `eml(x,1)=exp(x)` versus
  `eml(1,x)=e-ln(x)` (they agree at `x=1` and disagree at `x=2`).
- All-ones fragment recovers the constant size-2 split `e-1` vs `exp(e)`.
- Computational census: 2789 numerical fibers; 14 cross-size fibers.

Withheld:

- US-4′ (fiber free energy predicts EML gradient recovery).
- Identity of functions from finite-grid agreement.
- Any 1-D complete invariant.

The constant-only census is a different package
(`eml_fiber_spectrum` on the delete-repair branch).

```bash
python3 experiments/eml_variable_spectrum/experiment.py
python3 -m unittest tests.test_eml_variable_spectrum
```

## Lean formalisation (Wave 7)

The labeled-count headline is kernel-checked mathlib-free in
`formal/structural-intelligence/StructuralIntelligence/EmlCatalan.lean`:
`emlVar_counts` (counts = 2^(k+1)*C_k = 2, 4, 16, 80, 448, 2688 for
k = 0..5 via a single-pass bucket fold over the 3238-tree shell) and
`emlVar_formula` / `emlVar_total`. Grid spectra stay Python, as
registered. Verification status:
`docs/lea/VERIFY_RECEIPT_2026-08-18.md`.
