# Semantic Concern Geometry

This experiment is the non-spatial follow-up to Paper B. It asks whether moving
a semantic loss-weight field over real text classes moves the learned
representation-geometry deformation to the upweighted class.

The registered dataset is 20 Newsgroups with four semantic targets:

- `sci.space`
- `sci.med`
- `rec.sport.hockey`
- `comp.graphics`

Run the scaled Modal sweep from a Doppler/Modal-authenticated machine:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
    experiments/semantic_concern_geometry/modal_semantic_concern_sweep.py \
    --seeds 64 --steps 90 --batch-size 32 --target-se 0.02 \
    --out artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02.json
```

Summarize the raw Modal payload:

```bash
python scripts/summarize_semantic_concern_sweep.py \
  --input artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02.json \
  --summary-json artifacts/semantic_concern_geometry/semantic_concern_summary_2026_07_02.json \
  --report experiments/semantic_concern_geometry/results/semantic_concern_sweep_2026_07_02.md
```

The pre-registration is
`papers/semantic_concern_geometry/preregistration.md`.

