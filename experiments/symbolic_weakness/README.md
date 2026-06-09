# Symbolic Weakness Benchmark

This benchmark tests a narrower, publishable claim:

> Out-of-distribution generalization is better predicted by weak invariant structure
> than by training loss, short description length, or surface compression.

The first task family uses cyclic-symbol transformations. Training examples only cover
a biased prefix of the cyclic group, so several hypotheses fit the training data:

- a short local patch that applies the observed shift only on the training prefix;
- exact memorization of the observed examples;
- a global modular shift that preserves the cyclic symmetry.

All of these can reach perfect training accuracy. Only the global shift remains
equivariant under translations of the cyclic group, and only that rule generalizes
to the held-out symbols.

Run:

```bash
python3 experiments/symbolic_weakness/experiment.py --trials 300 --seed 11 --out artifacts/symbolic_weakness/prefix_shift_pilot.json
```

The report in `results/` records accepted and rejected claims from the pilot.

Current pilot report:

- [results/prefix_shift_pilot_2026_06_09.md](results/prefix_shift_pilot_2026_06_09.md)
