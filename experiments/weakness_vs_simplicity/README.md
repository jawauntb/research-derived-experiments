# Weakness vs. Simplicity

Hypothesis: when a reusable weak constraint is available, a selector that prefers the largest compatible extension should generalize better than one that prefers the shortest available form. Short forms can be misleading when the vocabulary contains cheap memorization-like hypotheses.

This is a toy benchmark, not a proof. It creates Boolean worlds, samples positive and negative observations from a target one-feature rule, and compares:

- `weakness`: choose the consistent candidate accepting the most possible worlds;
- `simplicity`: choose the consistent candidate with the shortest form length;
- `random`: choose a consistent candidate uniformly.

The memorizer candidate is intentionally short and narrow. It is the toy analogue of an overfit explanation that looks simple in the current representation but fails to preserve compatible futures.

Run:

```bash
python3 experiments/weakness_vs_simplicity/experiment.py --trials 500 --seed 7 --out artifacts/weakness_vs_simplicity/pilot.json
```

