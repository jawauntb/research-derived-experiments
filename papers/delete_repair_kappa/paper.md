# Paper F: we wrote κ. It is SIC.

**Jawaun Brown** (human director) and **Cursor Grok 4.6** (agent, under review)
**Date:** August 17, 2026
**Status:** Possibility 1 as a *new* master object is **dead on
this harness**. The written function exists and is Theorem 4
plus a total order. Verdict `calculus_is_sic`.

## Current frame

Papers A–E banked a taxonomy, a swap cell, a non-Kirchhoff
connection, a failed shared-theorem transfer, and a dead
one-shot agent rule. Possibility 1 was the leftover upgrade:
a function κ from typed failure signatures to minimal repairs.
This paper writes the maps first, then runs them.

## The function, specified before the run

**κ_cheap.** Paper E `decide` on the five-field signature.
No menu search.

**κ_screen.** If Kirchhoff mismatches, `transport`. Else let
`R` be the representing menu screens. Let `r*` be the unique
coarsest member of `R` (fewest fibres, then name). Restore,
quotient, or noop from `r*` versus the current screen.

**κ_unique.** The representing set is a singleton.

## Severe experiment

Suite: the 11 Paper E cases. No new toys fitted after E.

Observed:

- κ_cheap is **not a function**. Collision: `bag`, `last_bit`,
  and `parity` on `q_id` share a cheap signature with
  `pair_eq` on `q_id` and split gold (`quotient` vs `noop`).
- κ_screen hits **11/11**, including the E grain (`pair_eq`
  → `q_id`, noop).
- Uniqueness fails: `bag` has **5** representing screens.
  Tie-break picks `q_perm`.
- Path A/B still disagree on `(0,1)` vs `(1,1)`.
- Relabel `0↔3` sends `first_bit`/`q_stab0` to
  `last_bit`/`q_stab_last`.

Verdict: `calculus_is_sic`.

## Claim boundary

**Supported.** A computable natural choice function exists on
this menu. It is SIC's screen plus a named total order. The
cheap signature is not that function. Uniqueness is false.

**Not supported.** A new master object. A signature that does
not look at the menu. An LLM. Paper 0. Valence.

## Lean status

**Verified.** `KappaCheap.lean`, `KappaScreen.lean` (kernel `decide`,
no `native_decide`), `KappaUnique.lean`, `KappaRelabel.lean`.
Python suite remains the empirical receipt.
Receipt: `docs/lea/VERIFY_RECEIPT_2026-08-17.md`.

## Next best test

Stop. Possibility 5 is the close. Do not fit a fancier cheap
signature to erase the collision. Do not reopen DR/DCR.
Do not start Paper G.
