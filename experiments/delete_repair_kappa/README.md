# Paper F: write κ, then see what it is

Three maps, specified before the run:

- `κ_cheap` — Paper E five-field rule. Not a function
  (`bag`/`last_bit`/`parity`/`q_id` vs `pair_eq`/`q_id`).
- `κ_screen` — coarsest representing menu screen.
  Hits 11/11. Theorem 4 plus a total order.
- `κ_unique` — killed: `bag` has 5 representing screens;
  Path A/B disagree.

Verdict: `calculus_is_sic`.

```bash
python3 experiments/delete_repair_kappa/experiment.py
python3 -m unittest tests.test_delete_repair_kappa
```
