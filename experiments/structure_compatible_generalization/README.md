# Structure-Compatible Generalization

This experiment package turns the weakness/OOD result into a reusable
diagnostic suite for underspecified finite learning problems.

Core question:

> When train loss and ID checks cannot distinguish shortcut and rule-like
> solutions, does compatibility with the deployment-generating transformations
> predict which learned function generalizes OOD?

Domains:

- `symbolic_cyclic`: existing cyclic-prefix MLP weakness benchmark.
- `vision_rotation`: existing rotated-stroke vision benchmark.
- `modular_neural`: modular addition with local-prefix shortcut pressure.

Confirmatory execution is Modal L4-first:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/structure_compatible_generalization/modal_l4_suite.py \
  --shards-per-domain 4 --symbolic-models 128 --vision-models 96 \
  --modular-models 128 --budget-usd 50 \
  --out artifacts/structure_compatible_generalization/l4_suite.json
```

Quality gates can also run in Modal:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/structure_compatible_generalization/modal_l4_suite.py \
  --quality-only
```

After an L4 payload exists, generate report and paper artifacts:

```bash
python3 -m experiments.structure_compatible_generalization.summarize_suite \
  --in artifacts/structure_compatible_generalization/l4_suite.json

python3 scripts/build_structure_compatible_pdf.py \
  --in artifacts/structure_compatible_generalization/l4_suite.json
```

Export paper artifacts to the local Metaphysics archive:

```bash
python3 scripts/export_structure_compatible_artifacts.py
```

