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

Coupled 2A-v2 rich program-body sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/viable_computational_bodies/modal_rich_program_body_search.py \
  --generations 18 --population 18 \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

Learned executable module bodies against 2A-v2 transfer:

```bash
python3 -m experiments.viable_computational_bodies.learned_executable_modules \
  --train-trials 300 --test-trials 120 --seed 20260618 --epochs 25 \
  --out artifacts/viable_computational_bodies/learned_executable_modules_local.json \
  --report experiments/viable_computational_bodies/results/learned_executable_modules_local_2026_06_18.md

doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/viable_computational_bodies/modal_learned_executable_modules.py \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

Searched executable module bodies against the label-free 2A-v2 transfer gate:

```bash
python3 -m experiments.viable_computational_bodies.searched_executable_modules \
  --seeds 1 --generations 6 --population 8 \
  --train-trials 120 --test-trials 50 --epochs 12 \
  --induction-calibration-trials 80 \
  --out artifacts/viable_computational_bodies/searched_executable_modules_local.json \
  --report experiments/viable_computational_bodies/results/searched_executable_modules_local_2026_06_22.md

doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/viable_computational_bodies/modal_searched_executable_modules.py \
  --generations 18 --population 18 \
  --train-trials 3000 --test-trials 1200 --epochs 90 \
  --induction-calibration-trials 1200
```

Executable body validation is produced by the learned Arc 2A sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_learned_agents_sweep.py \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

Vector module validation is produced by the vector-observation Arc 2A sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/concerned_syntax/modal_vector_shapes_sweep.py \
  --train-trials 3000 --test-trials 1200 --epochs 90
```

Typed ontology gate prototype:

```bash
(
  cd formal/ontology-hs && cabal test all && cabal run ontology-check
)
```
