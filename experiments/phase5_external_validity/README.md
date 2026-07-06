# Phase 5 External Validity

Phase 5 turns the Phase 4 mechanism choices into four transport tracks:

1. `language_action_transport` - whether paraphrase geometry becomes an
   action-like controller under stronger open-model proxy conditions.
2. `foundation_semantic_metric` - whether value-weighted metric deformation
   survives a frozen foundation-style semantic encoder and cross-encoder proxy.
3. `role_routed_world_model` - whether disjoint role heads and mixture routing
   break the mediated-identifiability ceiling in a richer world model.
4. `topology_seam_causality` - whether seam consistency, topology, or their
   interaction carries OOD generalization in a factorial causal design.

These are external-validity proxy harnesses. They are designed to decide which
tracks deserve heavier real open-model validation, not to claim foundation-model
generality by themselves.

## Local Smoke

```bash
python -m experiments.phase5_external_validity.core \
  --preset smoke \
  --out artifacts/phase5_external_validity/smoke_suite.json

python -m experiments.phase5_external_validity.summarize \
  --in artifacts/phase5_external_validity/smoke_suite.json \
  --out experiments/phase5_external_validity/results/phase5_smoke_suite_2026_07_06.md
```

## L4 Full Suite

The Modal runner uses L4 GPUs, `max_containers=64`, and refuses to dispatch if
the conservative timeout-based cost estimate exceeds `--budget-usd`.

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/phase5_external_validity/modal_l4_suite.py \
  --preset full \
  --seeds 64 \
  --budget-usd 1000 \
  --out artifacts/phase5_external_validity/l4_full_suite.json
```

## Paper

```bash
python scripts/build_phase5_external_validity_pdf.py \
  --in artifacts/phase5_external_validity/l4_full_suite.json \
  --out papers/phase5_external_validity/from_controlled_concern_geometry_to_foundation_models.pdf
```
