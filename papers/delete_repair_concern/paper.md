# Door 3: concern picks the screen, and it is not decoration

**Jawaun Brown** (human director) and **Claude Fable 5** (agent, under review)
**Date:** August 18, 2026
**Status:** The third job — care which matter — is **opened at the
lowest bound**. Verdict `concern_does_work`. Concern here is a
registered weight vector and nothing else. Not valence. Not Paper G.

## Current frame

The close-out split "discover all" into write / reach / care and did
not touch the third job. Paper F left the hook: `bag` has five
representing screens, and the winner was picked by a disclosed but
arbitrary total order (fewest fibres, then name). Door 1 then showed
that name tie-break is not even relabel-natural. So the choice among
representing screens is real, currently unmotivated, and sitting
exactly where a concern coordinate would act.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| The tie-break is harmless | Mechanism | high | A concern under which it is strictly costly |
| Concern is decoration on (q, K) | Ontology | high | Distinct concerns force distinct screens |
| Concern choice is coordinate-free | Mechanism | medium | Reversal on the mirrored concern pair |
| One number summarizes concern | Ontology | medium | A phase boundary, not a constant |

## Severe experiment

Package: `experiments/delete_repair_concern/`. The representing set
for `bag` is all five menu screens (fibres 5, 6, 8, 8, 16). Concern
is a registered rational weight vector over six tasks. The registered
cost is fibre count when the screen represents the task, `2·n_worlds`
= 32 when it does not. κ_concern is the exact expected-cost argmin
with Paper F's tie-break. All arithmetic is `Fraction`; no sampling.

Observed, all exact:

| Concern | Choice | Gap over the unweighted choice |
|---|---|---|
| all mass on `bag` | `q_perm` | 0 |
| `bag` + `first_bit` | **`q_stab0`** | 21/2 |
| `bag` + `last_bit` | **`q_stab_last`** | 21/2 |
| `bag` + `pair_eq` | **`q_id`** | 5/2 |
| `bag` + `parity` | `q_perm` | 0 |
| uniform over six | **`q_id`** | 7 |

Four distinct screens. The Paper F choice (`q_perm`) is strictly
suboptimal under four of six registered concerns, by exact rational
gaps. The mirrored pair is reversal-natural: swapping `first_bit` for
`last_bit` in the concern swaps `q_stab0` for `q_stab_last` — the
naturality the bare name tie-break failed in door 1, restored by
giving the choice a reason.

The concern axis is not a switch but a dial: on the family
`(1−ε)·bag + ε·pair_eq`, the choice is `q_perm` for ε ≤ 11/27 and
`q_id` above it, with the boundary computed exactly and confirmed by
a 55-point sweep. At the tie the disclosed order still breaks it.

## What this is

The smallest true statement: **on this menu, with this registered
cost, which screen you should hold is a function of what you expect
to be asked.** The screen is not concern-free. Theorem 4 says which
screens are sufficient; it is silent between them; concern is the
coordinate that decides. That is the third job opened, one finite
instrument wide.

## Claim boundary

**Supported.** Concern-relative choice on `bag`'s representing set
does real, exact, reversal-natural work at this bound; the
concern-free tie-break is strictly costly under registered concerns;
the `bag`/`pair_eq` phase boundary is 11/27.

**Not supported.** Valence, agency, phenomenology, consciousness.
Learned or inferred concern — the weights are registered inputs, not
estimates. Any claim off this menu or cost model. An LLM. A new
master object. Paper G.

**What would change the conclusion.** A cost model under which all
concerns collapse to one choice (concern_idle) — the registered rule
did not. A naturality failure on the mirrored pair — none observed.

## Lean status

**Verified.** `ConcernChoice.lean` (Wave 5): the six registered
choices, the sum-gap 21, and `boundary_base` exact at k = 22
(ε = 11/27) on the full grid — kernel `decide`, integer-scaled exact
arithmetic, SafeVerify passed
(`docs/lea/VERIFY_RECEIPT_2026-08-18.md`). The dial's tie point is
additionally pinned unique by `CrossingUnique.crossing_unique`,
proved by an autonomous Lea run and verified twice.

## Next best test

If this opens a program, the next severe test is concern *transport*:
move a concern across the reversal relabel and require the whole
choice function to commute, then across a menu extension (door 1's
`MENU_EXT`) and see whether the phase boundary is menu-stable.
Learned concern stays out until a registered instrument exists for it.

## Provenance

`python3 experiments/delete_repair_concern/experiment.py`;
`python3 -m unittest tests.test_delete_repair_concern`. Human
director: Jawaun Brown. Agent: Claude Fable 5, session
`4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`, under review.
