# Gauge-Fixed Concern Transport Experiment Audit

## Regime Transition

### Old Regime

- **Artifact types:** proof-focused paper, literature review, diagrams, PDF.
- **Operations:** mathematical derivation, theorem ladder, cross-field conceptual demos.
- **Verifiers/gates:** PDF build, visual render, source links, reference count, lint/type checks for builder.
- **Claim level:** scaffold plus proof paper; no empirical validation.

### New Regime

- **Added artifact type/operation/verifier/gate:** Modal L4 synthetic experiment suite with raw payload, summary gates, figures, report, rewritten empirical paper, and direct PDF rebuild check.
- **Preserved artifacts:** bridge theorem, concern-weighted weakness definitions, gauge-fixing theorem, cross-field literature spine, original PDF builder pattern.
- **Preserved gates rerun:** lint, type checks, targeted tests, direct PDF build, visual PDF inspection, budget guard.

### Rejected Alternatives

- **Alternative:** Run only diagrams and application templates.
  - **Why rejected:** The user requested actual experiments; templates remain future-work-only evidence.
- **Alternative:** Use large public datasets or foundation models first.
  - **Why rejected:** Fragile downloads and external variability would obscure the theorem-premise gates; synthetic ground truth is the correct first empirical regime.
- **Alternative:** Treat probe accuracy as sufficient mechanistic evidence.
  - **Why rejected:** The bridge theorem predicts probe/commitment divergence; the experiment must include patch-style commitment effects.
- **Alternative:** Run all cells locally.
  - **Why rejected:** The user explicitly requested Modal L4 execution, and the repo already has L4 budget-guard patterns.

### Residual Finding

- **What appeared beyond the old regime:** The empirical suite showed that each theorem premise survives a controlled experiment rather than remaining only a proof obligation.
- **What bottleneck remains:** Passing synthetic gates still does not prove human, neural, biological, or foundation-model generality.

### Readiness

| Gate | Status | Evidence |
| --- | --- | --- |
| Plan | Pass | `docs/plans/2026-07-07-002-feat-gfc-modal-experiments-plan.md` |
| Theory artifact | Pass | `papers/gauge_fixed_concern_transport/paper.md` |
| Local smoke | Pass | `experiments/gauge_fixed_concern_transport/results/gfc_smoke_suite_2026_07_07.md` |
| Modal dry-run budget | Pass | Modal app `ap-aJ3jMVo96u3f5XMyxeTceu`; `$63.94 / $250.00` conservative timeout estimate |
| Modal full L4 run | Pass | Modal app `ap-GFeFvaDvcvaKGOjWyeciX8`; 320 rows; visible GPU `NVIDIA L4` |
| Paper rewrite | Pass | `papers/gauge_fixed_concern_transport/paper.pdf` and `papers/pdf/gauge_fixed_concern_transport.pdf` |

### Allowed Claim

The allowed claim is now `synthetic Modal L4 empirical validation result`.

### Next Operation

Export the same gates to foundation-model, biological, robotic, and human-subject
settings before making wider generality claims.
