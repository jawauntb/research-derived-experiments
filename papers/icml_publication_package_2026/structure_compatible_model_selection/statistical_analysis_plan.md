# Statistical Analysis Plan

This plan records what can be claimed from the tracked artifacts and what must
be regenerated or restored before a main-conference submission.

## Current Evidence State

Tracked evidence for structure-compatible generalization consists of Markdown
summary reports, PDFs, figures, preregistrations, source code, the Phase 6
semantic-selection bootstrap report, a curated Phase 6 row-level release, and
smoke row ledgers for phases 1-5. The full regenerated Phase 6 payload was
produced locally at
`artifacts/structure_compatible_generalization/semantic_selection_control_regen_2026_07_06.json`;
its reviewer-facing row and selector records are now tracked as JSONL.

Consequence: the paper can now report Phase 6 zoo-level bootstrap intervals,
publish the Phase 6 row records, and report tie-break stress tests. The phases
1-5 ledgers are local regenerated smoke fixtures, not byte-identical restores
of the original Modal payloads, so they support reproducibility audits rather
than headline statistical intervals.

## Required Independent Units

Use the following units for uncertainty, not individual table cells unless the
raw row schema supports that interpretation:

- Phase 1: model rows clustered by domain and seed/config family.
- Phase 2: configs clustered by regularization condition and seed/config family.
- Phase 3: modular configs and paired vision settings; report learned-vs-random
  augmentation as a matched comparison.
- Phase 4: configs for regularization and augmentation; separate finite-template
  rows from augmentation rows.
- Phase 5: semantic orbits and encoder keys.
- Phase 6: selection zoos, with threshold and encoder as stratification
  variables.

## Primary Endpoint for the Unified Paper

Primary endpoint:

> In Phase 6 semantic model zoos, learned compatibility selects higher OOD
> accuracy than train accuracy, ID validation accuracy, and random eligible
> selection, while wrong compatibility selects lower OOD accuracy.

Current point estimates:

| Selector | Selected OOD | Regret | Lift vs random |
| --- | ---: | ---: | ---: |
| random candidate | 0.919 | 0.073 | 0.000 |
| ID validation | 0.919 | 0.073 | 0.000 |
| train accuracy | 0.919 | 0.073 | 0.000 |
| wrong compatibility | 0.751 | 0.242 | -0.168 |
| learned compatibility | 0.978 | 0.014 | 0.059 |
| true compatibility | 0.993 | 0.000 | 0.073 |
| OOD oracle | 0.993 | 0.000 | 0.073 |

## Completed Phase 6 Bootstrap

Completed on 2026-07-06:

```bash
uvx --python 3.12 --with numpy --with scipy --with torch --with sentence-transformers \
  python -m experiments.structure_compatible_generalization.semantic_selection_control \
  --n-zoos 12 --configs-per-zoo 12 --thresholds 0.50,0.56,0.62,0.68,0.74 \
  --out artifacts/structure_compatible_generalization/semantic_selection_control_regen_2026_07_06.json

uvx --python 3.12 --with numpy --with matplotlib \
  python -m experiments.structure_compatible_generalization.semantic_selection_bootstrap \
  artifacts/structure_compatible_generalization/semantic_selection_control_regen_2026_07_06.json \
  --out-root . --bootstrap-reps 1000
```

Tracked outputs:

- `experiments/structure_compatible_generalization/results/semantic_selection_bootstrap_2026_07_06.json`
- `experiments/structure_compatible_generalization/results/semantic_selection_bootstrap_2026_07_06.md`
- `experiments/structure_compatible_generalization/results/semantic_selection_rows_2026_07_06.jsonl`
- `experiments/structure_compatible_generalization/results/semantic_selection_records_2026_07_06.jsonl`
- `experiments/structure_compatible_generalization/results/semantic_selection_row_release_manifest_2026_07_06.json`
- `experiments/structure_compatible_generalization/results/semantic_selection_tiebreak_stress_2026_07_06.md`
- `papers/structure_compatible_generalization/figures/fig13_semantic_selection_bootstrap_ci.png`

Key intervals:

- learned selected OOD: 0.978, 95% CI [0.973, 0.983];
- learned minus random: 0.059, 95% CI [0.052, 0.065];
- learned minus ID: 0.059, 95% CI [0.052, 0.065];
- learned minus wrong: 0.227, 95% CI [0.221, 0.233];
- learned regret: 0.014, 95% CI [0.011, 0.018].
- tie-break stress: mean ties, worst tied candidate, and random-tie bootstrap
  all pass the registered selector gates.

## Phases 1-5 Row-Ledger Status

Tracked smoke row ledgers:

- `experiments/structure_compatible_generalization/results/phase_row_ledgers_2026_07_06.md`
- `experiments/structure_compatible_generalization/results/phase_row_ledgers_manifest_2026_07_06.json`
- `experiments/structure_compatible_generalization/results/row_ledgers/phase1_l4_rows_2026_07_06.jsonl`
- `experiments/structure_compatible_generalization/results/row_ledgers/phase2_transformations_rows_2026_07_06.jsonl`
- `experiments/structure_compatible_generalization/results/row_ledgers/phase3_learned_generators_rows_2026_07_06.jsonl`
- `experiments/structure_compatible_generalization/results/row_ledgers/phase4_language_templates_rows_2026_07_06.jsonl`
- `experiments/structure_compatible_generalization/results/row_ledgers/phase5_semantic_retrieval_rows_2026_07_06.jsonl`

These ledgers are explicitly labeled as local regenerated smoke fixtures. The
full Modal-scale row artifacts should still be restored or rerun if phases 1-5
return to the main quantitative claim.

## Remaining Bootstrap/Significance Before Submission

1. Restore or rerun full Modal-scale row-level payloads for phases 1-5 if they
   keep main-table quantitative space.
2. Add third-encoder or larger-zoo Phase 6 replication if a venue reviewer asks
   for scale beyond the current 120 zoos.
3. Add paired-difference presentation for the existing Phase 6 selector rows.

## Boundary Analyses

The paper should include these as reviewer-facing boundary analyses:

- Phase 3 vision: learned augmentation versus random augmentation under matched
  augmentation count. Current point estimates are close (`+0.391` vs `+0.363`
  paired OOD delta), so this may be a limitation rather than a win.
- Phase 1 modular exact: `N=2` is a sanity check, not statistical evidence.
- Semantic retrieval: report the finite corpus/orbit construction clearly and
  avoid broad semantic robustness language.

## Artifact Work Needed

Before a conference submission, optionally add full-scale public or redacted
artifacts:

```text
artifacts/structure_compatible_generalization/
  phase1_rows.jsonl
  phase2_rows.jsonl
  phase3_rows.jsonl
  phase4_rows.jsonl
  semantic_retrieval_rows.jsonl
  semantic_selection_records.jsonl
  semantic_selection_summary.json
```

If raw Modal payloads contain paths or provider-specific metadata, publish
curated row-level fixtures instead.
