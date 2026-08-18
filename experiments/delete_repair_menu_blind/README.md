# delete_repair_menu_blind

Door 1 of the close-out (`papers/sic_dynamics/paper.md` §12): can a
specified κ that does **not** look at the menu hit a larger held-out
family?

Answer at this bound: no, and not because five fields are too few.
Gold itself is menu-relative. The same case (`pair_eq` on `q_id`)
has gold `noop` under the Paper E menu and gold `quotient` once
`q_pair01` joins the menu. A menu-blind κ is a function of `(Y, q)`
and is constant across menus, so no width of signature fixes it.

Bonus findings, both registered before the run:

- The Paper E cheap collision is itself menu-relative: 1 mixed-gold
  bucket under the base menu (7 cases), 0 under the extended menu,
  where the frozen rule scores 17/17.
- The Paper F tie-break (fewest fibres, then name) is not
  relabel-natural on ties: `pair_eq` and `pair23` both choose
  `q_pair01`. Action-level naturality survives.

Run:

```bash
python3 experiments/delete_repair_menu_blind/experiment.py
python3 -m unittest tests.test_delete_repair_menu_blind
```

Verdict: `menu_blind_dead`. κ_screen (Theorem 4 plus the disclosed
total order, recomputed per menu) is exact on all 34 rows.

Paper: `papers/delete_repair_menu_blind/paper.md`. Not Paper G.
