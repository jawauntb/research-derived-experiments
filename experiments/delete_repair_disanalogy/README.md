# Paper D: shared-diagram disanalogy

Possibility 6 says Lorentz, Lamport, and positional encodings are
one object. This package runs the transfer that should fail.

On a `{0,1,2,3}²` integer Minkowski grid, 43,680 injections, **196**
diamond embeddings. The Lamport task (concurrency of `{e1,e2}`) is
constant. The Lorentz task `s²(e1,e2)` takes **four** values:
`-1` (128), `-3` (32), `-4` (32), `-8` (4). The poset does not
determine the metric.

The PE cell is the Paper A/B fact: `q_perm` does not represent
`first_bit`. Disclosed as already-enumerated.

Verdict: `disanalogy_holds`. Not a functor. Not real Lorentz physics.

```bash
python3 experiments/delete_repair_disanalogy/experiment.py
python3 -m unittest tests.test_delete_repair_disanalogy
```
