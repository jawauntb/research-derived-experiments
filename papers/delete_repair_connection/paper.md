# Paper C: cell 3 is not idle Kirchhoff packaging

**Jawaun Brown** (human director) and **Cursor Grok 4.6** (agent, under review)
**Date:** August 17, 2026
**Status:** Cell 3 is **supported** as more than integer cycle-sum on
this harness. Not Lorentz. Not CG-2. Papers D–F stay unlicensed.

## Current frame

Paper A banked `cycle_integrates_iff_sum_zero` on `List Int`. That
is discrete Poincaré / Kirchhoff. Paper B showed opposite repairs
are not interchangeable. The leftover reading is that cell 3 is
just that Kirchhoff fact with a fancier name, so the taxonomy is
still only two arrows plus packaging.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| Every connection is integer cycle-sum | Ontology | high | Affine holonomy ≠ `(1, sum b)` |
| Additive cycles still obey Kirchhoff | Measurement | high | `a=1` control |
| Raw comparison is enough | Mechanism | high | Flat affine section |
| This is Lorentz / CG-2 | Ontology | high | Withhold |

## Anomaly map

If cell 3 is idle, `Aff(1, Z/3)` 4-cycles should still have
holonomy `(1, sum b)`. Paper A's integer walks are the `a=1`
slice of that group. A pass on that slice is the control, not
the claim.

## Candidate reframe

A connection is path-ordered composition in a group that need not
be `(Z, +)`. When a scale `a=2` appears, sum-of-shifts is the
wrong invariant. Cell 3 names that object. It is still not a
Lorentz boost and not concern holonomy.

## Discriminating predictions

| Predictor | Additive `a=1` cycles | Affine cycles with some `a=2` |
|---|---|---|
| Cell 3 is Kirchhoff | holonomy = `(1, sum b)` | same |
| Cell 3 is real | holonomy = `(1, sum b)` | at least one escape |
| Instrument broken | escape | anything |

## Severe experiment

Package: `experiments/delete_repair_connection/`.
Group: `Aff(1, Z/3)`, 6 elements, laws checked exhaustively.
Walks: 4-cycles.

| Cycle | `sum b` | Kirchhoff | Holonomy | Escape? |
|---|---|---|---|---|
| additive flat | 0 | `(1,0)` | `(1,0)` | no (control) |
| additive curved | 1 | `(1,1)` | `(1,1)` | no (control) |
| affine A | 0 | `(1,0)` | `(2,0)` | **yes** |
| affine B | 2 | `(1,2)` | `(1,0)` | **yes** |

Affine A: Kirchhoff predicts flat; the connection is not.
Affine B: Kirchhoff predicts curved; the connection is flat.
Composition does not commute: `(2,0)∘(1,1)=(2,2)` and
`(1,1)∘(2,0)=(2,1)`.

On the flat affine B section from value `0`, raw equality
disagrees with transported equality. Transported comparison
recovers the section.

Fatal instrument gates passed. A `cell3_idle` verdict would
still have passed CI.

## Claim boundary

**Supported.** On this harness, cell 3 is not idle Kirchhoff
packaging.

**Still prior art as a name.** Path-ordered products in a finite
affine group are undergraduate algebra. What is ours is the
discriminator against the Paper A control.

**Not licensed.** Lorentz geometry. Lamport clocks. Positional
encodings. CG-2. Paper D (the transfer that should fail). Paper
E. Paper F. A better LLM.

**What would change the conclusion.** Every later non-additive
example collapsing to a rewritten sum; a proof that `Aff(1, Z/3)`
is secretly `(Z/3, +)` after a coordinate change that also
preserves the registered cycles.

## Next best test

D–E are now banked. Do not start Paper F. Do not identify this
4-cycle with a boost.
