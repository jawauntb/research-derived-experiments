# Paper C: connection beyond Kirchhoff

Cell 3 is idle if every connection is integer cycle-sum. This package
uses `Aff(1, Z/3)` on a 4-cycle.

- Additive cycles still match Kirchhoff.
- Affine Case A: `sum b = 0` but holonomy is `(2,0)`, not the identity.
- Affine Case B: `sum b = 2` but holonomy is the identity.
- Composition does not commute. Raw comparison fails on a flat
  affine section; transported comparison works.

Verdict: `cell3_holds`. Not Lorentz. Not CG-2. Not Paper D/E/F.

```bash
python3 experiments/delete_repair_connection/experiment.py
python3 -m unittest tests.test_delete_repair_connection
```
