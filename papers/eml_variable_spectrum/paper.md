# Variable-`x` EML has no degree key

**Jawaun Brown** (human director) and **Cursor Grok 4.6** (agent, under review)
**Date:** August 17, 2026
**Status:** Local-CPU census banked. US-4′ withheld.

## Claim

Odrzywołek's operator `eml(a,b)=exp(a)-ln(b)` with leaf alphabet `{1,x}`
gives the grammar `S → 1 | x | eml(S,S)`. Trees are real functions of
`x>0`, or undefined. There is no 1-D integer invariant like polynomial
degree, so the fiber of a numerical function-tuple cannot be
dynamic-programmed the way `x^(2^n)` can.

This note banks a registered exhaustive census through 5 internal nodes
and one exact same-size functional split. It does not test US-4′.

## Instrument

Package: `experiments/eml_variable_spectrum/`.
Bound: `k ≤ 5`. Count formula: `2^{k+1} C_k` (3238 trees).
Grid: `{0.25, 0.5, 1, 2, e, 4}`. Real `exp`/`log`; nonpositive
right-hand side and overflow are undefined.

Fatal gates (all passed):

| Gate | Fact |
|---|---|
| `EVS_ENUMERATION_COMPLETE` | counts = `2, 4, 16, 80, 448, 2688` |
| `EVS_SIZE_NOT_FUNCTION` | `eml(x,1)=exp(x)` and `eml(1,x)=e-ln(x)` agree at `x=1` and disagree at `x=2` |
| `EVS_CONSTANT_EMBEDDING` | all-ones size-2 pair recovers `e-1` vs `exp(e)` and is constant in `x` |
| `EVS_GRID_DISCLOSED` | finite-grid agreement is not function identity |
| `EVS_US4_PRIME_WITHHELD` | US-4′ flagged untested |

Census (computational): 2789 numerical fibers; max fiber 12; 280
all-undefined rows; 1438 partial-undefined rows; 14 cross-size fibers.
Size is not a function invariant: distinct fibers by `k` are
`2, 4, 16, 78, 412, 2293`.

## Honesty

- Leaf alphabet `{1,x}` is a registered choice so the constant grammar
  embeds. It is not a claim that this is Odrzywołek's only language.
- Rounded 6-point tuples are a clustering, not identity of functions.
- Cross-size fiber counts are computational. They are not an identity
  theorem and they are not US-4′.
- The companion constant-only census lives on
  `experiments/eml_fiber_spectrum/` (other PR). This note does not
  depend on that file being present.

## Claim boundary

**Supported.** Labeled Catalan counts through `k=5`. Size is not a
function invariant (`exp(x)` vs `e-ln(x)`). All-ones fragment recovers
the constant size-2 split.

**Withheld.** US-4′. A 1-D complete invariant. Function identity from
the grid. Fiber free energy as a recovery predictor. Any statement that
this census is the EML-native access law.

**Kill.** Any `k≤5` count other than `2^{k+1} C_k`; the size-1 pair
agreeing at `x=2`; the all-ones pair failing `e-1` / `exp(e)`.

**Next test.** Ask whether truncated fiber mass, not shortest depth,
predicts which variable-`x` terms are recovered under a Gibbs sampler.
That is the Gibbs half of US-4′ (`experiments/eml_us4_prime/`).
Master-formula gradient recovery remains open.
