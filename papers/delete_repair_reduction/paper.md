# Door 2: the episode that moves the generators, not (q, K)

**Jawaun Brown** (human director) and **Claude Fable 5** (agent, under review)
**Date:** August 18, 2026
**Status:** A delete–repair fact outside (q, K) **exists at this
bound**, and it is the banked squaring episode wearing its own
clothes. Verdict `outside_fact_found`. Possibility 5's dynamics
reading is **bounded, not killed**. Not Paper G.

## Current frame

The close-out named its own death condition for Possibility 5: a
delete–repair fact that cannot be written as a movement of the screen
and kernel. It also, separately, banked that access is
process-relative. This instrument shows those two sentences meet: the
sharpest known outside fact was already in the record, filed under
access.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| Every delete–repair fact moves (q, K) | Ontology | high | A fact invariant under all registered screen motion |
| The squaring episode is (q, K) motion | Mechanism | high | Screen partitions before vs after |
| Access change implies screen change | Mechanism | high | The invariance table |
| The episode is the banked one | Measurement | high | Min sizes must equal US-2/US-3 |

## Severe experiment

Package: `experiments/delete_repair_reduction/`. Every tree to size 7
over `{x, ×}` (9 trees) and `{x, ×, sq}` (89 trees), exponent
semantics. The episode: delete `sq`, obstruction, re-adjoin.

Two ledgers, checked against each other:

| Ledger | Observable | Base | Ext |
|---|---|---|---|
| (q, K) | `q_den` / `q_size` / `q_depth` partitions on shared trees | identical | identical |
| Access | min size for `x^4` | 7 | **3** |
| Access | fibre mass for `x^4` at the bound | 5 | **14** |

The round trip (delete, then re-adjoin) is the identity on the access
table. So the same two-point argument that closed door 1 runs here in
the other direction: one (q, K) input, two required access outputs.
Min size is not a function of the registered (q, K) data. The episode
moves something, and that something is the generator set.

## What this does and does not do to Possibility 5

It does not touch the representability reading. Papers A–F facts —
which repairs represent, which screens are coarsest, where transport
is forced — are movements of (q, K), and stay that way.

It does bound the unrestricted slogan "delete–repair is motion of
(q, K)." Generator episodes are delete–repair loops in good standing
(delete, obstruction, repair, round-trip identity), and their
observable lives on the process coordinate. The honest statement of
Possibility 5 after this instrument: **delete–repair is typed motion
on SIC's frontier, where the frontier carries (q, K) for
representability facts and the generator set for access facts.** The
close-out's own three-job split (write / reach / care) already drew
this border; the instrument enumerates it.

## Claim boundary

**Supported.** At size bound 7, with screens `q_den`, `q_size`,
`q_depth`: the squaring episode changes access while all registered
(q, K) data is invariant and the round trip is the identity. The
banked US-2/US-3 numbers (7 vs 3) are reproduced, not assumed.

**Not supported.** A kill of Possibility 5's representability
reading. A new master object above SIC. A claim about screens beyond
the three registered ones. Continuum limits. An LLM. Paper G.

**What would change the conclusion.** A registered screen whose
partition differs across grammars on the shared universe and predicts
the access change — verdict flips to `all_reduce`. A (q, K)-motion
encoding of generator adjunction over the *fixed* shared universe that
reproduces min-size — none is on the table; producing one reopens the
unrestricted reading.

## Next best test

Door 2 is answered at this bound. If anyone wants it sharper, the
next severe test is a *second* generator episode (a different
definable macro) run through the same two ledgers; a second
outside fact of the same shape would consolidate the border, and an
episode whose access change tracks a screen would sharpen it the
other way. Door 3 (concern) is a separate instrument.

## Lean status

**Verified.** `GeneratorBorder.lean` (Wave 5): both episodes
enumerated in the kernel (9 vs 89 trees, min 7 vs 3, mass 5 vs 14),
`base_subset_ext7`, and the two-point separation
`min_size_not_shared_function` — several headlines depend on **no
axioms at all**; SafeVerify kernel replay passed
(`docs/lea/VERIFY_RECEIPT_2026-08-18.md`).

## Provenance

`python3 experiments/delete_repair_reduction/experiment.py`;
`python3 -m unittest tests.test_delete_repair_reduction`. Human
director: Jawaun Brown. Agent: Claude Fable 5, session
`4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`, under review.
