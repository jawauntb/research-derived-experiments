# delete_repair_concern_transport

Door 3's registered consolidation test: transport the concern
machinery across the reversal relabel and door 1's menu extension.

Results, all exact and predicted before the run:

| Fact | Base menu | Extended menu |
|---|---|---|
| `bag` representing set | 5 | 7 (both pair screens join, 12 fibres) |
| pure-`bag` choice | `q_perm` | `q_perm` (menu-stable anchor) |
| `bag`+`pair_eq` choice | `q_id` | `q_pair01` |
| phase boundary | 11/27 → `q_id` | 7/27 → `q_pair01` |
| mirrored-pair naturality | holds | holds |

The symmetry layer is coordinate-free; the boundary is menu-relative.
Doors 1 and 3 compose: what to hold is a joint function of the menu
and the expected questions.

Verdict: `transport_holds_boundary_moves`.

Run:

```bash
python3 experiments/delete_repair_concern_transport/experiment.py
python3 -m unittest tests.test_delete_repair_concern_transport
```

Paper: `papers/delete_repair_concern_transport/paper.md`. Not Paper G.
