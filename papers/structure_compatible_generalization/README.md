# Structure-Compatible Generalization Paper

This folder is generated from the Modal L4 suite payload.

Expected artifacts:

- `structure_compatible_generalization.md`
- `structure_compatible_generalization.pdf`
- `inferred_transformations_intervention.md`
- `inferred_transformations_intervention.pdf`
- `phase3_learned_generators_preregistration.md`
- `learned_generators_transfer.md`
- `learned_generators_transfer.pdf`
- `docs/paper_reviews/structure_compatible_generalization_critical_review.md`
- `docs/paper_reviews/inferred_transformations_intervention_critical_review.md`
- `figures/fig1_domain_predictors.png`
- `figures/fig2_selection_without_ood.png`
- `figures/fig3_discovered_vs_oracle.png`
- `figures/fig4_regularization_intervention.png`
- `figures/fig5_learned_generator_predictors.png`
- `figures/fig6_learned_generator_interventions.png`

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

doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/structure_compatible_generalization/modal_phase3_learned_generators.py \
  --artifacts-only \
  --artifact-input artifacts/structure_compatible_generalization/phase3_learned_generators.json

python3 scripts/export_structure_compatible_artifacts.py --clean
```

The local Metaphysics export copies descriptive paper PDFs by default. Use
`--include-supporting` when markdown reports, reviews, and standalone figures
should be copied too.
