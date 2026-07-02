# Semantic Concern Geometry Sweep -- Modal Results (2026-07-02)

Pre-registration: [papers/semantic_concern_geometry/preregistration.md](../../../papers/semantic_concern_geometry/preregistration.md).

## Discovery-Regime Audit

Question: Does a non-spatial semantic loss-weight intervention move a learned representation-geometry deformation to the upweighted class in pretrained transformers?

Current regime:
- Artifact types: Modal sweep JSON, paired effect rows, bootstrap summary, result report, PDF paper.
- Operations: 20 Newsgroups sampling, pretrained transformer fine-tuning, JEPA-like predictive latent training, geometry probes.
- Gates/verifiers: preregistered 2% bootstrap-SE gate, semantic random-matched control, real-dataset requirement.
- Known limitations: four-topic text classification, small fine-tuned encoders, JEPA-like objective rather than official I-JEPA.

Action class:
- Search/discovery: search inside the Paper B metric-deformation schema, with a new non-spatial semantic artifact class.

## Manifest

- Models: sentence-transformers/all-MiniLM-L6-v2, distilbert-base-uncased
- Objectives: classifier, jepa
- Registered categories: sci.space, sci.med, rec.sport.hockey, comp.graphics
- Seeds per family: 256
- Steps per trained cell: 90
- Batch size: 32
- Concern weight: 8.0
- Target bootstrap SE: 0.02
- Dataset kinds observed: 20newsgroups
- Rows: 12288; paired concern effects: 4096
- Merged payloads: 2

Run command(s):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
    experiments/semantic_concern_geometry/modal_semantic_concern_sweep.py \
    --seeds 128 --base-seed 20260702 --steps 90 --batch-size 32 --target-se 0.02 \
    --out artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02.json

doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
    experiments/semantic_concern_geometry/modal_semantic_concern_sweep.py \
    --seeds 128 --base-seed 20260902 --steps 90 --batch-size 32 --target-se 0.02 \
    --out artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02_part2.json

```

## Gate Summary

| Family | lift vs uniform | lift vs random | specificity | rank | gate |
| --- | ---: | ---: | ---: | ---: | :--: |
| distilbert-base-uncased / classifier | -0.398 [-0.430, -0.367], SE 0.016 | -0.396 [-0.426, -0.366], SE 0.015 | -0.531 [-0.610, -0.448], SE 0.041 | 0.473 | FAIL |
| distilbert-base-uncased / JEPA-like | -0.358 [-0.389, -0.327], SE 0.015 | -0.360 [-0.388, -0.332], SE 0.014 | -0.477 [-0.557, -0.394], SE 0.041 | 0.485 | FAIL |
| all-MiniLM-L6-v2 / classifier | -0.508 [-0.534, -0.484], SE 0.013 | -0.505 [-0.531, -0.480], SE 0.013 | -0.678 [-0.763, -0.592], SE 0.044 | 0.450 | FAIL |
| all-MiniLM-L6-v2 / JEPA-like | -0.499 [-0.525, -0.474], SE 0.013 | -0.505 [-0.531, -0.480], SE 0.013 | -0.665 [-0.750, -0.580], SE 0.044 | 0.452 | FAIL |

Architecture-balanced pooled result:

- Lift vs uniform: -0.441 [-0.455, -0.427], SE 0.007
- Lift vs random matched: -0.441 [-0.455, -0.428], SE 0.007
- Specificity: -0.588 [-0.629, -0.546], SE 0.021
- Rank percentile: 0.465
- Pooled gate: FAIL

## Companion Metrics

| Family | centroid lift | kNN-purity lift | eff-rank lift | target-F1 lift | accuracy lift |
| --- | ---: | ---: | ---: | ---: | ---: |
| distilbert-base-uncased / classifier | +0.325 [+0.294, +0.356], SE 0.016 | +0.369 [+0.338, +0.400], SE 0.016 | +0.553 [+0.496, +0.611], SE 0.029 | -0.018 [-0.020, -0.017], SE 0.001 | -0.008 [-0.009, -0.007], SE 0.000 |
| distilbert-base-uncased / JEPA-like | +0.309 [+0.275, +0.343], SE 0.017 | +0.316 [+0.286, +0.345], SE 0.015 | +0.443 [+0.389, +0.498], SE 0.028 | -0.014 [-0.016, -0.013], SE 0.001 | -0.006 [-0.007, -0.006], SE 0.000 |
| all-MiniLM-L6-v2 / classifier | +0.542 [+0.514, +0.570], SE 0.014 | +0.456 [+0.431, +0.483], SE 0.013 | +0.104 [+0.040, +0.165], SE 0.032 | -0.019 [-0.020, -0.017], SE 0.001 | -0.010 [-0.011, -0.009], SE 0.000 |
| all-MiniLM-L6-v2 / JEPA-like | +0.545 [+0.517, +0.574], SE 0.015 | +0.441 [+0.416, +0.467], SE 0.013 | +0.125 [+0.062, +0.187], SE 0.032 | -0.017 [-0.019, -0.016], SE 0.001 | -0.009 [-0.010, -0.008], SE 0.000 |

## Target Audit

Per-target effects are retained so a single class cannot silently carry the claim.

### distilbert-base-uncased / classifier

| Target | n | lift vs uniform | lift vs random | specificity |
| --- | ---: | ---: | ---: | ---: |
| comp.graphics | 256 | -0.329 [-0.372, -0.287], SE 0.022 | -0.264 [-0.303, -0.225], SE 0.020 | -1.256 [-1.304, -1.207], SE 0.025 |
| rec.sport.hockey | 256 | -0.503 [-0.598, -0.414], SE 0.046 | -0.492 [-0.581, -0.409], SE 0.044 | +1.440 [+1.305, +1.567], SE 0.067 |
| sci.med | 256 | -0.380 [-0.429, -0.331], SE 0.025 | -0.393 [-0.443, -0.346], SE 0.025 | -0.991 [-1.046, -0.936], SE 0.028 |
| sci.space | 256 | -0.381 [-0.432, -0.333], SE 0.025 | -0.436 [-0.486, -0.388], SE 0.026 | -1.317 [-1.358, -1.276], SE 0.021 |

### distilbert-base-uncased / JEPA-like

| Target | n | lift vs uniform | lift vs random | specificity |
| --- | ---: | ---: | ---: | ---: |
| comp.graphics | 256 | -0.301 [-0.351, -0.255], SE 0.025 | -0.252 [-0.299, -0.208], SE 0.023 | -1.210 [-1.257, -1.161], SE 0.024 |
| rec.sport.hockey | 256 | -0.413 [-0.500, -0.333], SE 0.043 | -0.395 [-0.476, -0.319], SE 0.040 | +1.565 [+1.438, +1.684], SE 0.062 |
| sci.med | 256 | -0.343 [-0.396, -0.292], SE 0.026 | -0.379 [-0.429, -0.331], SE 0.025 | -0.976 [-1.032, -0.920], SE 0.029 |
| sci.space | 256 | -0.373 [-0.421, -0.329], SE 0.023 | -0.413 [-0.460, -0.367], SE 0.024 | -1.286 [-1.331, -1.240], SE 0.023 |

### all-MiniLM-L6-v2 / classifier

| Target | n | lift vs uniform | lift vs random | specificity |
| --- | ---: | ---: | ---: | ---: |
| comp.graphics | 256 | -0.503 [-0.540, -0.467], SE 0.019 | -0.454 [-0.490, -0.421], SE 0.018 | -1.410 [-1.452, -1.367], SE 0.022 |
| rec.sport.hockey | 256 | -0.442 [-0.515, -0.371], SE 0.037 | -0.437 [-0.512, -0.363], SE 0.038 | +1.502 [+1.384, +1.618], SE 0.059 |
| sci.med | 256 | -0.565 [-0.607, -0.522], SE 0.022 | -0.639 [-0.689, -0.591], SE 0.025 | -1.101 [-1.155, -1.048], SE 0.027 |
| sci.space | 256 | -0.524 [-0.563, -0.489], SE 0.019 | -0.490 [-0.524, -0.457], SE 0.017 | -1.701 [-1.734, -1.667], SE 0.017 |

### all-MiniLM-L6-v2 / JEPA-like

| Target | n | lift vs uniform | lift vs random | specificity |
| --- | ---: | ---: | ---: | ---: |
| comp.graphics | 256 | -0.508 [-0.546, -0.471], SE 0.019 | -0.456 [-0.491, -0.421], SE 0.017 | -1.395 [-1.440, -1.346], SE 0.024 |
| rec.sport.hockey | 256 | -0.431 [-0.502, -0.360], SE 0.037 | -0.428 [-0.500, -0.357], SE 0.036 | +1.510 [+1.390, +1.625], SE 0.060 |
| sci.med | 256 | -0.550 [-0.599, -0.502], SE 0.025 | -0.645 [-0.694, -0.599], SE 0.024 | -1.085 [-1.139, -1.030], SE 0.028 |
| sci.space | 256 | -0.506 [-0.546, -0.471], SE 0.019 | -0.492 [-0.524, -0.461], SE 0.016 | -1.691 [-1.726, -1.657], SE 0.017 |

## Interpretation Rules

- Passing families support the bounded claim: semantic loss weighting can causally and specifically deform a learned text-representation metric.
- Failed families remain failed; the pooled result must not hide a family-level failure.
- Behavioral gains alone do not count as metric deformation.
- Synthetic-fallback runs are smoke tests only and do not address the externality limitation.

