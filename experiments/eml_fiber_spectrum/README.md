# EML fiber spectrum (constant grammar)

First census of Odrzywołek's homogeneous grammar `S → 1 | eml(S,S)`
with `eml(x,y) = exp(x) - ln(y)`. Every closed tree is a real constant
or undefined. There is no 1-D integer invariant like polynomial degree.

Banked:

- Catalan-complete enumeration through 6 internal nodes (197 trees).
- Exact same-size disagreement: `eml(1,eml(1,1)) = e-1` versus
  `eml(eml(1,1),1) = exp(e)`.
- Closed census: 145 finite values, 118 numerical fibers, 52 undefined.
- Five well-resolved exact cross-size identities (optional gate).
- Disclosure that rounded / finite-grid agreement is not function identity.

Withheld:

- US-4′ (fiber free energy predicts EML gradient recovery).
- Variable-leaf / free-`x` spectrum.
- Any claim that a numerical fiber id is an identity theorem.

Companion paper: [`papers/delete_the_absolute/`](../../papers/delete_the_absolute/).
The monomial toy with a degree invariant lives on the companion
squaring-separation branch, not here.

```bash
python3 experiments/eml_fiber_spectrum/experiment.py
python3 -m unittest tests.test_eml_fiber_spectrum
```

## Lean formalisation (Wave 7)

The census and witness headlines are kernel-checked mathlib-free in
`formal/structural-intelligence/StructuralIntelligence/EmlCatalan.lean`:
`emlFib_counts` (shell counts = Catalan C_0..C_6; 197 trees, axiom-free),
`catalan_values`, `emlFib_total`, and the size-2 split `eml_pair_diff`
(same size, distinct terms, denotations separated by a registered Nat
model of the ExpLn fragment; the carrier-general derivations are
`left_denotes` / `right_denotes`). Numerical fiber statistics stay
Python, as registered. Verification status:
`docs/lea/VERIFY_RECEIPT_2026-08-18.md`.
