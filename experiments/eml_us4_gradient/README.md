# EML US-4′ (gradient recovery, lowest bound)

Does master-formula gradient descent, a *different* search process from
the Gibbs sampler, still rank the fat zero fiber above a same-min-size
singleton?

Registered before any blind count:

- Fat / zero: `eml(1,eml(eml(1,1),1))` (and `eml(x,eml(eml(x,1),1))`)
  — identically 0, two size-3 formulas, higher `Φ`.
- Thin / singleton: `eml(1,eml(1,eml(1,1)))` — `e-ln(e-1)`, one
  formula, lower `Φ`.
- Process: hand-derived GD on the size-3 master skeleton. Not Gibbs
  sampling of the census. Not Odrzywołek's neural bootstrap.
- Success: MSE `< 1e-6` on the registered six-point grid.
- Rule: zero `>` singleton by ≥1 of 8 inits ⇒ `Φ` holds here; equal ⇒
  reject `Φ`-predicts-GD (min-size still governs); singleton `>` zero
  ⇒ kill `Φ`-predicts-GD. Perturbed-correct failure withholds.

Registered run: perturbed-correct 8/8, zero blind **8/8**, singleton
blind **6/8**. Verdict `phi_holds`. The two singleton misses are
undefined (`MSE=1e6`), not near-threshold losses. Local analogue
only; margin is two seeds.

```bash
python3 experiments/eml_us4_gradient/experiment.py
python3 -m unittest tests.test_eml_us4_gradient
```
