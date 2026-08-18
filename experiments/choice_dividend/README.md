# choice_dividend

Gate 1 of the essay "Intention Is All You Need" — the dividend gate —
run at the kernel as an exact instrument. On the sixteen worlds
{0,1}^4 a task is a compliant region plus a value function
U: worlds → `Fraction`. The choice dividend (the essay's D12) is the
exact gap between the best compliant value and the uniform compiler's
expectation over the region; per P11 / Theorem B, intelligence pays
only on slack.

Registered task table, three families:

| Task | Region (size) | U | Dividend |
|---|---|---|---|
| `singleton_5` | {5} (1) | U(x) = x | **0** |
| `singleton_12` | {12} (1) | U(x) = x | **0** |
| `even_worlds` | even worlds (8) | U(x) = x | **7** |
| `popcount_ge2` | popcount ≥ 2 (11) | U(x) = popcount(x)·4 − (x % 3) | **73/11** |
| `odd_flat` | odd worlds (8) | U(x) = 5 | **0** |

Capability sweep: best-of-k over each region in registered ascending
order; gain(k) = prefix-max U minus the uniform expectation. gain(1)
is deterministic first-element and can be negative (−7 on
`even_worlds`, −15/11 on `popcount_ge2`) — recorded; the registered
claim is the curve's weak monotonicity and its endpoint
gain(|region|) = dividend, which both hold exactly on every task.

Verdict: `dividend_confirmed`.

Kernel arithmetic of P11/D12 only. The learner half of Gate 1 —
real capability sweeps on real models — is explicitly NOT run here
and stays open. No LLM, no valence, no RNG.

Run:

```bash
python3 experiments/choice_dividend/experiment.py
python3 -m unittest tests.test_choice_dividend
```

Paper: `papers/choice_dividend/paper.md`.
