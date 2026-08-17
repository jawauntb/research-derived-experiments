# Paper B: swap-cell discriminator

Same `{0,1}^4` harness as `delete_the_absolute`. Opposite repairs on
opposite toys.

This is a discriminator *contract* on the Paper A matrix, not new
enumeration. Typed repairs work. The crossed over-repair fails.
The under-quotient is cheaper (5 vs 16 fibres). No single screen is
minimal-safe for both toys. Verdict: `taxonomy_holds`.

```bash
python3 experiments/delete_repair_swap/experiment.py
python3 -m unittest tests.test_delete_repair_swap
```
