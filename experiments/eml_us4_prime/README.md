# EML US-4′ (Gibbs access, lowest bound)

Does truncated fiber mass, not shortest depth, govern Gibbs access on
the leaf-labeled EML language `S → 1 | x | eml(S,S)` through `k=5`?

Yes at fixed min-size: the identically-zero function has two size-3
formulas, a typical size-3 constant has one, and `Φ` differs by 2.

No for the Sq-toy extra-shell story: extra shells add < 1% mass here.

Master-formula gradient recovery is withheld.

```bash
python3 experiments/eml_us4_prime/experiment.py
python3 -m unittest tests.test_eml_us4_prime
```
