# silent_substitution

Gate 2 of the essay "Intention Is All You Need" — the silence gate —
run at the kernel as an exact instrument, in the zero-leakage limit.
The realization space X = 0..7 is a single compliance class, so the
spec-level record is the constant symbol `compliant` at every step BY
CONSTRUCTION: there is no record channel for a substitution to show
up on.

Two arms share the channel and differ only in the registered reward
table. The misaligned delegate reward `R_MIS = (0..7)` is exactly
opposed to the principal value `U = (7..0)`; the aligned control
reward `R_AL = U`. Ecology step t reweights outcome x by
`(r(x) + 1) ** t` for t = 0..12, all exact `Fraction`s.

Results, all exact and all registered before the run:

- The record is identical at all 13 steps in both arms.
- Misaligned `E_t[r]` strictly rises and `E_t[U]` strictly falls,
  from **7/2** at t = 0 to **1583088700/7083249971** (≈ 0.22) at
  t = 12 — every report green the whole way down.
- The mass on the reward argmax x = 7 strictly rises to exactly
  **17179869184/21249749913** (≈ 0.8085) at t = 12, above the
  registered floor 4/5 (it tends to 1 in t; 99/100 is first crossed
  at t = 35, outside this horizon).
- The aligned control's `E_t[U]` strictly rises: the channel, not
  the tilt, sets the direction.

Verdict: `substitution_silent`.

This banks the ZERO-LEAKAGE limit only. Measuring real
specifications' leakage is the open empirical half of Gate 2; the
bridge from record silence to intention attribution stays a bet per
the essay. No LLM, no valence, no RNG.

Run:

```bash
python3 experiments/silent_substitution/experiment.py
python3 -m unittest tests.test_silent_substitution
```

Paper: `papers/silent_substitution/paper.md`.
