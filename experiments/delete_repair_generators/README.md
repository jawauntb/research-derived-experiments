# delete_repair_generators

Door 2's registered consolidation test: a second generator episode
through the same two ledgers.

Episodes:

| Episode | Grammar | Target | Min size (base vs ext) | Mass | Outside fact |
|---|---|---|---|---|---|
| `sq_x4` (replay anchor) | `{x, ×}` vs `{x, ×, sq}`, bound 7 | `x^4` | 7 vs 3 | 5 vs 14 | yes |
| `cube_x3` (new) | `{x, ×}` vs `{x, ×, cube}`, bound 5 | `x^3` | 5 vs 2 | 2 vs 3 | yes |

Both min sizes were predicted before enumeration (`2k−1` for mul-only
formulas; 2 for one macro application). Screens `q_den` / `q_size` /
`q_depth` are invariant on the shared universe in both episodes and
both round trips are the identity.

Verdict: `border_consolidated`. The door-2 fact is a border, not a
squaring quirk: generator-set motion carries access facts; screen
motion carries representability facts.

Run:

```bash
python3 experiments/delete_repair_generators/experiment.py
python3 -m unittest tests.test_delete_repair_generators
```

Paper: `papers/delete_repair_generators/paper.md`. Not Paper G.
