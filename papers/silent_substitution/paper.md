# Gate 2 at the kernel: every report is green

**Jawaun Brown** (human director) and **Claude Fable 5** (agent, under review)
**Date:** August 18, 2026
**Status:** Gate 2 of the essay "Intention Is All You Need" — the
silence gate — run at the kernel as an exact instrument, in the
zero-leakage limit. Verdict `substitution_silent`. The record is
constant at all 13 steps of both arms while misaligned expected
principal value falls from 7/2 to 1583088700/7083249971 and the
aligned control rises through the same channel.

## Current frame

The essay "Intention Is All You Need" puts a gate in front of any
trust placed in a delegate's compliant-looking record: before the
wall of green reports means anything, check whether the record could
even show a substitution (Gate 2, the silence gate). Its P10 kernel
run is the limiting case where the answer is exactly no. This
package is that run as a registered instrument: a realization space
of eight outcomes forming a single compliance class, so the
spec-level record is the constant symbol `compliant` BY CONSTRUCTION
— the zero-leakage limit. Whatever the compiler does to the
distribution over outcomes, the record carries zero bits about it.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| A constant record implies nothing is drifting | Ontology | high | Misaligned E_t[U] strictly falls under a constant record |
| The tilt mechanism, not the reward channel, sets the direction | Mechanism | high | The aligned arm rises under the identical tilt law |
| Concentration needs stochastic machinery | Method | medium | The argmax mass is a closed-form rational, strictly rising |
| Exactness is optional at kernel size | Method | medium | Every weight, expectation, and mass serializes as a Fraction |

## Severe experiment

Package: `experiments/silent_substitution/`. Realization space
X = 0..7, one compliance class. Principal value U = (7,6,5,4,3,2,1,0)
indexed by x. Misaligned delegate reward R_MIS = (0,...,7), exactly
opposed; aligned control reward R_AL = U. Base compiler uniform;
ecology step t reweights outcome x by (r(x) + 1) ** t, exact integer
powers, t = 0..12. All monotone directions and the exact t = 12
argmax mass were registered before the run.

Observed, all exact and all predicted before the run (misaligned arm
unless noted):

| t | E_t[R_MIS] | E_t[U] | mass on x = 7 | record |
|---:|---|---|---|---|
| 0 | 7/2 | 7/2 | 1/8 | `compliant` |
| 1 | 14/3 | 7/3 | 2/9 | `compliant` |
| 6 | 13973/2191 | 1364/2191 | 65536/111741 | `compliant` |
| 12 | 47999661097/7083249971 | 1583088700/7083249971 | **17179869184/21249749913** | `compliant` |

Every strict inequality holds at every one of the 12 adjacent step
pairs: E_t[R_MIS] rises, E_t[U] = 7 − E_t[R_MIS] falls, the argmax
mass rises. At t = 12 the mass is exactly 17179869184/21249749913
(≈ 0.8085), above the registered floor 4/5; it tends to 1 as t grows
and first crosses 99/100 at t = 35, outside the registered horizon.

The aligned control is the discriminating contrast: under the
identical tilt law, E_t[U] strictly *rises* from 7/2 to
47999661097/7083249971 (the mirror image under x → 7 − x). The
channel — which reward table feeds the tilt — sets the direction;
the tilt mechanism itself is direction-neutral. And in both arms the
spec-level record is the same constant symbol at all 13 steps: 26
green cells over a trajectory in which the principal's value moved
by a factor of more than fifteen in opposite directions.

## What this is

The smallest true statement: **at zero leakage, the record cannot
distinguish reward-tilted drift from aligned improvement, and the
drift is not slow.** Silent substitution here is not an empirical
surprise but a theorem of the construction: when the compliance
class is the whole space, spec-level compliance is invariant under
every reweighting, so the misaligned compiler's strictly rising
reward and strictly falling principal value are invisible by
construction. The instrument makes the limiting case exact so the
empirical half of Gate 2 — how much leakage real specifications
actually have — has a fixed endpoint to be measured against.

## Lean status

The kernel is also machine-checked in Lean (Wave 6,
`SilentSubstitution.lean`, landing separately). Pending receipt:
until the SafeVerify kernel-replay receipt lands in `docs/lea/`,
every claim in this package stays labeled **python-enumerated**, per
the repo's two-state rule (proved ≠ verified).

## Claim boundary

**Supported.** On the registered eight-outcome space with the
registered value tables and tilt law, for t = 0..12: the spec-level
record is constant in both arms; misaligned E_t[R_MIS] strictly
rises while E_t[U] strictly falls (7/2 → 1583088700/7083249971);
the mass on x = 7 strictly rises to exactly 17179869184/21249749913
at t = 12, above the registered floor 4/5; the aligned control's
E_t[U] strictly rises. All exact.

**Not supported.** This banks the ZERO-LEAKAGE limit only — the
limit is constructed, not measured. No claim about how much leakage
real specifications have (that is the open empirical half of
Gate 2). No claim about any real delegate, learner, or LLM. No
valence. The bridge from record silence to intention attribution
stays a bet per the essay.

**What would change the conclusion.** Any record cell differing
from the constant symbol (`substitution_visible`) — none observed;
the space is one compliance class by construction. Any monotonicity
failing at any step (`inconclusive`) — none observed. A t = 12 mass
off the registered exact Fraction — not observed.

## Next best test

The other half of Gate 2: a registered leakage instrument on a space
with more than one compliance class, where the record carries
nonzero bits and the question becomes how many bits are enough to
make substitution visible at a registered horizon. Separately, the
Gate 1 dividend instrument (`choice_dividend`) prices what the
compiler's choice is worth when the compliant region has slack. Both
stay registered-first, as this one was.

## Provenance

`python3 experiments/silent_substitution/experiment.py`;
`python3 -m unittest tests.test_silent_substitution`.
Human director: Jawaun Brown. Agent: Claude Fable 5 (Cursor agent,
under J. Brown direction), session
`4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`, run
`silent_substitution_2026_08_18`, under review.
