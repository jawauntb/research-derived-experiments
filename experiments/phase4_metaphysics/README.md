# Phase 4 Metaphysics

Phase 4 converts the cross-paper open questions into seven cheap, parallel
diagnostic tracks:

1. `language_scale` - paraphrase geometry, behavior coupling, and intervention
   specificity across scale-like regimes.
2. `neural_symmetry` - non-enumerative transformation discovery with closure
   constraints.
3. `learned_regimes` - learned regime variables for state-dependent concern.
4. `probe_value` - marginal value-of-information probing instead of current
   error or ensemble variance.
5. `beyond_ceiling` - disjoint per-role and mixture-of-experts heads beyond the
   shared-head mediated-identifiability ceiling.
6. `semantic_metric` - value-weighted metric deformation in a semantic-style
   embedding harness.
7. `topology_mediation` - topology, seam consistency, and OOD mediation.

These are controlled diagnostic harnesses. They are designed to decide which
mechanisms deserve heavier foundation-model or richer-agent follow-up, not to
claim foundation-model generality by themselves.

## Local Smoke

```bash
python -m experiments.phase4_metaphysics.core \
  --preset smoke \
  --out artifacts/phase4_metaphysics/smoke_suite.json

python -m experiments.phase4_metaphysics.summarize \
  --in artifacts/phase4_metaphysics/smoke_suite.json \
  --out experiments/phase4_metaphysics/results/phase4_smoke_suite_2026_07_06.md
```

## L4 Full Suite

The Modal runner uses L4 GPUs, `max_containers=64`, and refuses to dispatch if
the conservative timeout-based cost estimate exceeds `--budget-usd`.

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/phase4_metaphysics/modal_l4_suite.py \
  --preset full \
  --budget-usd 1000 \
  --out artifacts/phase4_metaphysics/l4_full_suite.json
```

## Paper

```bash
python scripts/build_phase4_metaphysics_pdf.py \
  --in artifacts/phase4_metaphysics/l4_full_suite.json \
  --out papers/phase4_metaphysics/learning_missing_conditions.pdf
```
