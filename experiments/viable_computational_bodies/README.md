# Viable Computational Bodies

Arc 2B asks which computational bodies can express the causal constituency
required by Arc 2A. This is not generic neural architecture search. The search
space is a typed symbolic architecture grammar, and candidates are selected by
viability, formal admissibility, anti-cheat gates, and their ability to pass
concerned-syntax tests.

Local smoke run:

```bash
python3 -m experiments.viable_computational_bodies.search \
  --seeds 12 --generations 18 --population 18 --base-seed 20260616 \
  --out artifacts/viable_computational_bodies/pilot.json \
  --report experiments/viable_computational_bodies/results/pilot_2026_06_16.md
```

Modal sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/viable_computational_bodies/modal_body_evolution_sweep.py
```

