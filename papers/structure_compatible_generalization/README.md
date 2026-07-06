# Structure-Compatible Generalization Paper

This folder is generated from the Modal L4 suite payload.

Expected artifacts:

- `paper.md`
- `paper.pdf`
- `figures/fig1_domain_predictors.png`
- `figures/fig2_selection_without_ood.png`

Build flow:

```bash
python3 -m experiments.structure_compatible_generalization.summarize_suite \
  --in artifacts/structure_compatible_generalization/l4_suite.json

python3 scripts/build_structure_compatible_pdf.py \
  --in artifacts/structure_compatible_generalization/l4_suite.json
```

