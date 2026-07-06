# Figure Manifest

This manifest names the figure set for the ICML-style package and keeps source
paths auditable.

## Main Paper Figures

1. **Semantic selector headline**
   - Source: `papers/structure_compatible_generalization/figures/fig11_semantic_selection_ood.png`
   - Main-paper role: closest deployment analogue; choose among high train/ID
     semantic candidates before seeing OOD labels.
   - Caption: "Semantic selector performance. Learned compatibility improves
     OOD-free selection over train, ID, and random selectors, while wrong
     compatibility is anti-useful."

2. **Cross-domain predictor rankings**
   - Source: `papers/structure_compatible_generalization/figures/fig1_domain_predictors.png`
   - Main-paper role: broad evidence that compatibility is a useful OOD
     predictor across symbolic, modular, and vision domains.
   - Caption: "Predictor correlations by domain. Compatibility is strongest in
     symbolic and modular settings; vision is a mixed case and is reported as
     such."

3. **Selection without OOD**
   - Source: `papers/structure_compatible_generalization/figures/fig2_selection_without_ood.png`
   - Main-paper role: phase-one selector comparison.
   - Caption: "OOD-free selection in the phase-one finite domains."

## Appendix Figures

4. **Discovered vs oracle transformations**
   - Source: `papers/structure_compatible_generalization/figures/fig3_discovered_vs_oracle.png`
   - Use: support the transition from oracle to inferred/discovered families.

5. **Regularization intervention**
   - Source: `papers/structure_compatible_generalization/figures/fig4_regularization_intervention.png`
   - Use: show compatibility as a control signal, not only a diagnostic.

6. **Learned generator predictors**
   - Source: `papers/structure_compatible_generalization/figures/fig5_learned_generator_predictors.png`
   - Use: phase-three learned generator evidence.

7. **Learned generator interventions**
   - Source: `papers/structure_compatible_generalization/figures/fig6_learned_generator_interventions.png`
   - Use: augmentation/regularization details.

8. **Language-template predictors**
   - Source: `papers/structure_compatible_generalization/figures/fig7_language_template_predictors.png`
   - Use: finite text bridge.

9. **Language-template intervention**
   - Source: `papers/structure_compatible_generalization/figures/fig8_language_template_intervention.png`
   - Use: regularization and augmentation controls in the finite-text phase.

10. **Semantic retrieval predictors**
    - Source: `papers/structure_compatible_generalization/figures/fig9_semantic_retrieval_predictors.png`
    - Use: frozen-encoder transfer.

11. **Semantic retrieval breakdowns**
    - Source: `papers/structure_compatible_generalization/figures/fig10_semantic_retrieval_breakdowns.png`
    - Use: encoder and selector-family breakdowns.

12. **Semantic selection regret**
    - Source: `papers/structure_compatible_generalization/figures/fig12_semantic_selection_regret.png`
    - Use: selector regret and threshold stress.

13. **Semantic selection bootstrap intervals**
    - Source: `papers/structure_compatible_generalization/figures/fig13_semantic_selection_bootstrap_ci.png`
    - Use: Phase 6 zoo-bootstrap 95% CIs for selected OOD accuracy.

## Companion Benchmark Appendix Figures

14. **Suite C gate status**
    - Source: `papers/habituated_reengagement/figures/suite_c_fig1_gate_status.png`
    - Use: finite-agent companion appendix.

15. **Suite C no-false-calm control**
    - Source: `papers/habituated_reengagement/figures/suite_c_fig4_no_false_calm.png`
    - Use: central anti-cheat control for re-engagement.

16. **Suite C learned transfer controls**
    - Source: `papers/habituated_reengagement/figures/suite_c_neural_fig4_control_failures.png`
    - Use: stale/wrong/suppressed-signal controls.

17. **Long-horizon commitment ladder**
    - Source: `papers/long_horizon_bottleneck/figures/fig1_commitment_surface_ladder.png`
    - Use: Suite D/E companion benchmark framing.

## Missing Figures Before Submission

- A single new schematic for the paper's main method:
  "ID-equivalent model zoo -> compatibility audit -> OOD-free selector."
- A compact negative-control figure comparing true/discovered/wrong
  compatibility across all six phases.
