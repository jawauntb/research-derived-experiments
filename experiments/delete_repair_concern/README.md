# delete_repair_concern

Door 3 of the close-out (`papers/sic_dynamics/paper.md` §12): the
third job — care which matter — opened at the lowest bound.

Theorem 4 says which screens are sufficient for `bag` (all five, per
Paper F) and is silent between them. Paper F broke the tie by name;
door 1 showed that tie-break is not relabel-natural. Here concern is
a registered rational weight vector over six tasks, cost is a
registered two-case rule (fibre count on represent, 32 on miss), and
κ_concern is the exact expected-cost argmin.

Results, all exact:

- Six registered concerns select **four distinct screens**
  (`q_perm`, `q_stab0`, `q_stab_last`, `q_id`).
- The concern-free choice `q_perm` is strictly beaten under four
  concerns; max gap **21/2**.
- The mirrored concern pair is **reversal-natural** — the naturality
  the name tie-break failed, restored by giving the choice a reason.
- The `bag`/`pair_eq` dial has an exact phase boundary at
  **ε\* = 11/27**, confirmed by a 55-point sweep.

Verdict: `concern_does_work`.

Concern here is a weight vector and nothing else. Not valence, not
agency, not consciousness, not learned.

Run:

```bash
python3 experiments/delete_repair_concern/experiment.py
python3 -m unittest tests.test_delete_repair_concern
```

Paper: `papers/delete_repair_concern/paper.md`. Not Paper G.
