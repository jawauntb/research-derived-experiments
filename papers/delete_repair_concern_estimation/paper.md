# Registered estimation: counting is enough at this bound

**Jawaun Brown** (human director) and **Claude Fable 5** (agent, under review)
**Date:** August 18, 2026
**Status:** Door 3's licensed follow-up — the registered plug-in
estimator instrument — run and confirmed. Verdict
`estimation_works`. Frequency counting recovers the oracle concern
choice at exactly the registered prefixes 1 / 2 / 6, with a
misspecification gap of exactly 4. Not Paper G.

## Current frame

Door 3 opened the third job — care which matter — with concern as a
**given** registered weight vector: κ_concern picks the screen worth
holding, exactly. Its paper closed with one licensed next step:
learned concern stays out until a registered instrument exists for
estimated concern. This letter is that instrument. Nothing about the
menu, the cost rule, or the tie-break changes; the only new object is
the estimator, and the estimator is frequency counting and nothing
else.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| Concern must be given, not estimated | Ontology | high | A registered estimator that recovers the oracle choice |
| Counting alone cannot find the choice | Mechanism | high | Convergence on all three registered sequences |
| Convergence timing is a fit parameter | Method | high | Steps 1/2/6 registered before the run, then confirmed minimal |
| Holding the wrong screen is harmless | Mechanism | medium | The exact cross-sequence cost gap |

## Severe experiment

Package: `experiments/delete_repair_concern_estimation/`. Three
registered literal 24-draw task sequences; the plug-in weights after
n draws are the empirical frequencies (exact `Fraction`s); the
plug-in choice at n is door 3's κ_concern on the unchanged menu and
cost rule. The convergence steps were registered before the run and
the run could only confirm or refute them — the instrument confirms,
it does not fit.

Observed, all exact and all predicted before the run:

| Sequence | Oracle concern | Oracle choice | Registered step | Observed step |
|---|---|---|---:|---:|
| `SEQ_BAG` = ("bag",)×24 | δ_bag | `q_perm` | 1 | **1** |
| `SEQ_MIX` = ("bag","first_bit")×12 | uniform{bag, first_bit} | `q_stab0` | 2 | **2** |
| `SEQ_PAIR` = ("bag","pair_eq")×12 | uniform{bag, pair_eq} | `q_id` | 6 | **6** |

The `SEQ_PAIR` step is door 3's exact boundary doing the work: the
odd-prefix `pair_eq` frequency k/(2k+1) sits below 11/27 through
n = 5 (2/5) and above it from n = 7 (3/7), while even prefixes sit at
1/2, so the plug-in choice locks to `q_id` exactly at n = 6. The full
24-row choice trace per sequence is recorded.

Misspecification control: on `SEQ_PAIR`'s true concern, holding
`SEQ_MIX`'s oracle screen `q_stab0` has expected cost **20** against
`q_id`'s **16** — exact gap **4**. Estimating the wrong sequence's
concern is not free, and the price is a recorded rational.

## What this is

The smallest true statement: **at this bound, estimated concern needs
no machinery beyond counting.** The plug-in weights after n draws are
the empirical frequencies; κ_concern of those frequencies equals the
oracle choice from the registered prefix on, and the prefix itself is
a theorem of door 3's exact geometry (the 11/27 boundary), not a fit.
Estimation enters the third job with zero new degrees of freedom.

## Claim boundary

**Supported.** On door 3's menu and cost rule, with these three
registered 24-draw sequences, registered frequency counting recovers
the oracle concern choice for all prefixes n ≥ the registered minimal
steps 1 / 2 / 6 and stays through n = 24; the misspecification gap is
exactly 4.

**Not supported.** Frequency counting is the entire estimator — not
SGD, not valence, not learned representations, not an inferred prior.
The menu and cost are fixed as door 3 registered; nothing off this
menu, this cost rule, or these sequences. No stochastic-convergence
claim (the sequences are literal, not sampled). No LLM. No new
master object. Not Paper G.

**What would change the conclusion.** Any final-prefix choice off
oracle (`estimation_fails`) — none observed. Convergence at
unregistered steps (`inconclusive`) — none observed; the mismatch
witnesses at n = 1 (`SEQ_MIX`) and n = 5 (`SEQ_PAIR`) confirm the
registered steps are minimal.

## Next best test

Sampled draws under a registered seed and a registered
concentration-style bound on the step — estimation under noise rather
than on literal sequences. Separately, a registered instrument for
concern *drift* (the true weights change mid-sequence) would test
whether counting with a registered window keeps the choice. Both stay
out until registered, as this one did.

## Provenance

`python3 experiments/delete_repair_concern_estimation/experiment.py`;
`python3 -m unittest tests.test_delete_repair_concern_estimation`.
Human director: Jawaun Brown. Agent: Claude Fable 5 (Cursor agent,
under J. Brown direction), session
`4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`, run
`delete_repair_concern_estimation_2026_08_18`, under review.
