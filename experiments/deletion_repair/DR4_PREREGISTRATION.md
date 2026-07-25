# DR4 — DR3 With the Costly Toy's Base Rate Repaired

**Package:** `experiments/deletion_repair/` (DR4 modules)
**Predecessor:** DR3 (H1″/H2″/H3″ GO, H4″ NO_GO on an unachievable gate)
**Human director:** Jawaun Brown
**Date:** 2026-07-25

## 0. Freeze status

This document was written **before** `run_dr4.py` was executed, and the
calibration in §3 was measured **before** the gates in §5 were written. That is
the order DR3 failed to follow, and correcting it is half the point of DR4.

DR3 recorded two process slips against itself: gates frozen in code with the
document written afterwards, and a speedup threshold set without calibrating
the toy it would be applied to. Both are fixed here.

## 1. What DR4 changes, and why it is not a re-run-until-it-passes

DR3's H4″ required `speedup_vs_random ≥ 10` on both toys. But

```
speedup = expected_random / verifications_to_first_hit,   verifications ≥ 1
⇒ speedup ≤ expected_random
```

and `expected_random` is fixed by the toy's base rate alone. DR3's costly toy
had 191 load-bearing candidates of 1350 — a 14% base rate — so
`expected_random = 7.0` and **no nominator could have exceeded 7×**. The gate
was unsatisfiable the moment the toy was written.

DR4 therefore **repairs the instrument, not the criterion**. The 10× threshold
is carried over unchanged. What changes is the toy: the parent budget is
tightened so that *all three* costly commitments must be released together,
rather than any one of them sufficing.

That is a principled change, not a cosmetic one. A single 64-unit commitment
against an 8-unit budget meant every deletion containing it qualified. A
1-unit budget against commitments of 64, 4 and 2 means no proper subset
suffices — dropping the two largest still leaves 2 > 1. It also sharpens the
analogy: the real move is rarely "drop one thing," it is drop the constraint
*and* discharge what the constraint was silently providing, which is exactly
the entangled-triple structure the restrictive toy already has.

## 2. The two toys

**RK — Restrictive Kinematics.** Unchanged from DR3. All proposition costs are
zero, so cost attribution is identically silent. The load-bearing deletion is
the entangled facet triple.

**CT4 — Calibrated Costly Transduction.** Three costly propositions
(`sequential_schedule` 64, `checkpoint_every_step` 4, `sync_barrier` 2) against
a budget of 1. Each is **vacuous as a predicate** — satisfied by every
hypothesis — so deleting any of them leaves the extension identical and
`weakness_gain == 0` exactly. Only the commitment changes. Seventeen inert
nuisance propositions pad `R` to 20 deletable.

## 3. Calibration (measured before the gates below were written)

| toy | candidates | load-bearing | base rate | `E[random]` | 10× gate needs |
|---|---:|---:|---:|---:|---:|
| RK | 1350 | 1 | 0.07% | 675.5 | ≤ 67 verifications |
| CT4 | 1350 | 1 | 0.07% | 675.5 | ≤ 67 verifications |

Independence, also measured before freezing:

| toy | `cost>0, weakness=0` | `weakness>0, cost=0` |
|---|---:|---:|
| RK | 0 | 1 |
| CT4 | **517** | 0 |

The 10× gate is now reachable on both toys, which is the defect DR4 exists to
fix.

## 4. Nominators

Unchanged from DR3: `weakness`, `cost`, `max_disjunction`, `sum_disjunction`,
`minrank_disjunction`, and the `random` / `size_only` controls. Ties broken by
seeded shuffle, never by name.

## 5. Gates

- **H1‴ — independence.** At least one candidate on CT4 has `cost_relief > 0`
  and `weakness_gain == 0`.
- **H2‴ — complementarity.** The best single nominator differs between RK and
  CT4.
- **H3‴ — combiner.** At least one combiner attains
  `verifications_to_first_hit` no worse than the better single nominator on
  **both** toys.
- **H4‴ — speedup.** The best nominator achieves `speedup_vs_random ≥ 10` on
  **both** toys. Threshold carried over from DR3 unchanged; only the toy that
  made it unreachable has been repaired.

**Overall GO requires all four.** A GO opens the date-cut retrodiction, which
has been closed since DR1 and is conditioned on a clean sweep here.

## 6. What a GO would and would not mean

It would mean: on toy systems with authored propositions and a fixed
vocabulary, execution-free nomination finds the load-bearing deletion far
faster than exhaustive search, the two signals are genuinely complementary when
cost is defined off the extension, and a combiner exploits both.

It would **not** mean the framework works on real material. That is precisely
what the retrodiction is for, and why a GO opens it rather than concluding
anything. Nothing here bears on vocabulary extension — the known ceiling.

Single-shot. No replay knobs.
