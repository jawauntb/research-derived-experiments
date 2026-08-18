# Gate 1 at the kernel: intelligence pays only on slack

**Jawaun Brown** (human director) and **Claude Fable 5** (agent, under review)
**Date:** August 18, 2026
**Status:** Gate 1 of the essay "Intention Is All You Need" — the
dividend gate — run at the kernel as an exact instrument. Verdict
`dividend_confirmed`. Dividends exactly 0 / 0 / 7 / 73/11 / 0 across
the five registered tasks, every gain curve weakly increasing with
endpoint exactly the dividend.

## Current frame

The essay "Intention Is All You Need" prices what a compiler's
choice is worth before any capability claim is credited. Its D12
defines the choice dividend of a task — the exact gap between the
best compliant value and the uniform compiler's expected value over
the compliant region — and its P11 / Theorem-B framing says the
dividend is positive exactly where compliance leaves value-varying
slack: intelligence pays only on slack. This package is that
arithmetic as a registered instrument on the sixteen worlds {0,1}^4,
with the zero cases pinned from both sides (no slack by arity, no
slack by constancy) and the positive cases computed exactly.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| Capability is worth paying for on every task | Ontology | high | Singleton and flat tasks: dividend exactly 0 |
| A wide compliant region suffices for choice to pay | Mechanism | high | The flat task is wide (8 worlds) and pays 0 |
| The sweep endpoint could overshoot or miss the dividend | Method | high | gain(size) = dividend exactly on all five tasks |
| Early capability is monotonically useful | Method | medium | gain(1) < 0 on both wide-varying tasks, recorded |

## Severe experiment

Package: `experiments/choice_dividend/`. Worlds {0,1}^4 encoded
0..15; a task is a registered compliant region in ascending order
plus a registered value rule into `Fraction`s. Dividend per D12:
max U over the region minus the uniform expectation. Capability
sweep: best-of-k under the registered ascending scan, gain(k) =
prefix-max minus the uniform expectation. The task table and the
expected dividends (0, 0, 7, 73/11, 0) were registered before the
run.

Observed, all exact and all predicted before the run:

| Task | Region (size) | E_uniform[U] | max U | Dividend | gain(1) | gain(size) |
|---|---|---|---|---|---|---|
| `singleton_5` | {5} (1) | 5 | 5 | **0** | 0 | 0 |
| `singleton_12` | {12} (1) | 12 | 12 | **0** | 0 | 0 |
| `even_worlds` | evens (8) | 7 | 14 | **7** | −7 | 7 |
| `popcount_ge2` | popcount ≥ 2 (11) | 103/11 | 16 | **73/11** | −15/11 | 73/11 |
| `odd_flat` | odds (8) | 5 | 5 | **0** | 0 | 0 |

The `even_worlds` gain curve is (−7, −5, −3, −1, 1, 3, 5, 7); the
`popcount_ge2` curve is (−15/11 ×3, 18/11 ×7, 73/11); both weakly
increasing with endpoint exactly the dividend. The two singletons
and the flat task never move off 0: with one compliant outcome, or
eight equally good ones, there is nothing for capability to buy —
the essay's "everything compliant equally good" case pays zero
through a wide-open region.

The negative first gains are the honest edge of the registered
scan: best-of-1 is deterministic first-element, and the first
element of an ascending scan sits below the mean whenever the value
rises along it. The registered claim was always the curve's
endpoint and monotonicity, not gain(1) ≥ 0 — capability buys its
way from below the uniform baseline up to exactly the dividend, and
no further.

## What this is

The smallest true statement: **the dividend, not the region width
and not the capability, is what choice is worth.** Zero slack pays
zero whether the region is a point or eight-wide and flat; varying
slack pays exactly max − mean, and a full-capability sweep collects
exactly that, never more. This fixes the kernel endpoint against
which the learner half of Gate 1 — where a real model's best-of-k
must climb a real task's curve — can later be measured.

## Lean status

The dividend arithmetic is kernel-checkable by construction (finite
exact rationals). A Lean core for this package has not landed;
claims here are labeled **python-enumerated** per the repo's
two-state rule until a SafeVerify receipt exists.

## Claim boundary

**Supported.** On the five registered tasks over {0,1}^4: dividends
exactly 0, 0, 7, 73/11, 0; every best-of-k gain curve weakly
increasing under the registered ascending scan; gain(region size)
equal to the dividend exactly on all five tasks; negative first
gains −7 and −15/11 recorded on the wide-varying tasks.

**Not supported.** This is the kernel arithmetic of P11/D12 only —
not the learner experiment. No claim about real capability sweeps
on real models (that half of Gate 1 is explicitly not run and stays
open). No claim off this task table, this uniform baseline, or this
registered scan order. No LLM, no valence.

**What would change the conclusion.** A zero-case with a positive
dividend, or a wide curve missing its dividend
(`dividend_refuted`) — none observed. Non-monotone gain curves or
unregistered dividend values (`inconclusive`) — none observed.

## Next best test

The learner half of Gate 1: a registered best-of-k sweep where the
selector is a real model's sampled attempts on a task with a
registered dividend, so the observed curve can be laid against this
kernel endpoint. Separately, the Gate 2 silence instrument
(`silent_substitution`) already banks the record side: together the
gates say when capability claims are priced (dividend > 0) and when
records can even carry the news. Both stay registered-first, as
this one was.

## Provenance

`python3 experiments/choice_dividend/experiment.py`;
`python3 -m unittest tests.test_choice_dividend`.
Human director: Jawaun Brown. Agent: Claude Fable 5 (Cursor agent,
under J. Brown direction), session
`4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`, run
`choice_dividend_2026_08_18`, under review.
