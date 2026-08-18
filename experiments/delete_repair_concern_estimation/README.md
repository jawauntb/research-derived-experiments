# delete_repair_concern_estimation

Door 3's licensed follow-up: the registered plug-in estimator
instrument for concern. Door 3 (`experiments/delete_repair_concern/`)
took concern as a given weight vector; its paper said learned concern
stays out until a registered instrument exists for it. This is that
instrument, at the smallest honest size.

Concern is estimated by registered frequency counting: on a fixed
literal sequence of task draws, the plug-in weights after n draws are
the empirical frequencies (exact Fractions), and the plug-in choice is
door 3's κ_concern on the unchanged menu and cost rule. Three
registered sequences, 24 draws each: `SEQ_BAG` (all `bag`), `SEQ_MIX`
(alternating `bag`/`first_bit`), `SEQ_PAIR` (alternating
`bag`/`pair_eq`).

Results, all exact and all registered before the run:

- `SEQ_BAG` converges to the oracle choice `q_perm` at step **1**.
- `SEQ_MIX` converges to `q_stab0` at step **2** (n = 1 is δ_bag).
- `SEQ_PAIR` converges to `q_id` at step **6**: the odd-prefix
  `pair_eq` frequency k/(2k+1) crosses door 3's exact **11/27**
  boundary between n = 5 (2/5) and n = 7 (3/7).
- Misspecification control: holding `SEQ_MIX`'s screen `q_stab0`
  under `SEQ_PAIR`'s true concern costs **20 vs 16** — exact gap
  **4**.

Verdict: `estimation_works`.

Frequency counting is the entire estimator. Not SGD, not valence,
not learned representations. Menu and cost fixed as door 3
registered.

Run:

```bash
python3 experiments/delete_repair_concern_estimation/experiment.py
python3 -m unittest tests.test_delete_repair_concern_estimation
```

Paper: `papers/delete_repair_concern_estimation/paper.md`. Not
Paper G.
