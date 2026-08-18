# Concern transport: the boundary moves with the menu

**Jawaun Brown** (human director) and **Claude Fable 5** (agent, under review)
**Date:** August 18, 2026
**Status:** Door 3's choice function **transports** across the
reversal relabel under both menus, and its phase boundary is
**menu-relative**: 11/27 on the Paper E menu, 7/27 once the pair
screens join. Verdict `transport_holds_boundary_moves`. Doors 1 and 3
compose. Not Paper G.

## Current frame

Door 3 showed concern does real work on `bag`'s representing set,
with an exact `bag`/`pair_eq` boundary at 11/27. Door 1 showed gold
is menu-relative. The registered next test: run the concern machinery
through door 1's two menus and see which parts are invariant.

## Severe experiment

Package: `experiments/delete_repair_concern_transport/`. Door 3's
registered cost rule (fibre count on represent, 32 on miss), door 1's
menus and extended screen/task tables, exact rational arithmetic,
Paper F's tie-break.

Observed, all exact and all predicted before the run:

| Fact | Base menu | Extended menu |
|---|---|---|
| `bag` representing set | 5 screens | 7 (adds both pair screens, 12 fibres) |
| all-mass-on-`bag` choice | `q_perm` | `q_perm` |
| `bag`+`pair_eq` choice | `q_id` | **`q_pair01`** |
| phase boundary | 11/27 (→ `q_id`) | **7/27 (→ `q_pair01`)** |
| mirrored pair naturality | holds | holds |

The transportable part transports: reversal naturality holds under
both menus (`q_stab0` ↔ `q_stab_last`), and the concern-free anchor
(`q_perm` on pure `bag`) is menu-stable. The menu-dependent part
moves exactly as doors 1 and 3 jointly require: enlarging the menu
makes `pair_eq` cheap to serve (12 instead of the 32 miss penalty),
so the dial tips earlier — 7/27 instead of 11/27 — and tips to a
different screen.

One sentence: **what you should hold is a joint function of what is
on the menu and what you expect to be asked, and only its symmetry
layer is coordinate-free.**

## Claim boundary

**Supported.** Reversal-natural concern choice under both registered
menus; exact boundaries 11/27 and 7/27 confirmed by 55-point sweeps;
the `bag`+`pair_eq` choice flips `q_id` → `q_pair01` with the menu;
the pure-`bag` anchor is menu-stable.

**Not supported.** Valence, learned concern, claims off these two
menus or this cost rule, an LLM, a new master object, Paper G.

**What would change the conclusion.** A naturality break under either
menu (`transport_fails`) — none observed. Equal boundaries
(`boundary_menu_stable`) — excluded by the exact arithmetic.

## Next best test

The runnable enumerations licensed by the close-out's three doors are
now exhausted. The remaining follow-ups are design work, not runs:
Lean banking of the door headlines through the Lea pipeline, and a
registered instrument for learned concern before any learning run.

## Provenance

`python3 experiments/delete_repair_concern_transport/experiment.py`;
`python3 -m unittest tests.test_delete_repair_concern_transport`.
Human director: Jawaun Brown. Agent: Claude Fable 5, session
`4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`, under review.
