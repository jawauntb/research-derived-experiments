# Structure-Compatible Generalization Paper

This folder is generated from the Modal L4 suite payload.

Expected artifacts:

- `structure_compatible_generalization.md`
- `structure_compatible_generalization.pdf`
- `inferred_transformations_intervention.md`
- `inferred_transformations_intervention.pdf`
- `figures/fig1_domain_predictors.png`
- `figures/fig2_selection_without_ood.png`

Build flow:

```bash
python3 -m experiments.structure_compatible_generalization.summarize_suite \
  --in artifacts/structure_compatible_generalization/l4_suite.json

python3 scripts/build_structure_compatible_pdf.py \
  --in artifacts/structure_compatible_generalization/l4_suite.json

doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/structure_compatible_generalization/modal_phase2_transformations.py \
  --artifacts-only \
  --artifact-input artifacts/structure_compatible_generalization/phase2_transformations.json
```
