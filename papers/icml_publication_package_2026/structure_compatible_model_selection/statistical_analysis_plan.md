# Statistical Analysis Plan

This plan records what can be claimed from the tracked artifacts and what must
be regenerated or restored before a main-conference submission.

## Current Evidence State

Tracked evidence for structure-compatible generalization consists of Markdown
summary reports, PDFs, figures, preregistrations, source code, and the new
Phase 6 semantic-selection bootstrap report. The regenerated raw Phase 6
payload was produced locally at
`artifacts/structure_compatible_generalization/semantic_selection_control_regen_2026_07_06.json`
and is intentionally outside git because `artifacts/` is ignored.

Consequence: the paper can now report Phase 6 zoo-level bootstrap intervals.
Full bootstrap intervals over seeds, model rows, and semantic orbits for phases
1-5 still require restoring the raw artifacts or rerunning those suites.

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
- `papers/structure_compatible_generalization/figures/fig13_semantic_selection_bootstrap_ci.png`

Key intervals:

- learned selected OOD: 0.978, 95% CI [0.973, 0.983];
- learned minus random: 0.059, 95% CI [0.052, 0.065];
- learned minus ID: 0.059, 95% CI [0.052, 0.065];
- learned minus wrong: 0.227, 95% CI [0.221, 0.233];
- learned regret: 0.014, 95% CI [0.011, 0.018].

## Remaining Bootstrap/Significance Before Submission

1. Restore or regenerate row-level payloads for phases 1-5.
2. Use paired differences within each zoo where selectors share the same
   candidate set.
3. Repeat Phase 6 with deterministic tie-break variants:
   - mean of ties, current summary behavior;
   - worst tied candidate;
   - random tied candidate with bootstrap over tie samples.

## Boundary Analyses

The paper should include these as reviewer-facing boundary analyses:

- Phase 3 vision: learned augmentation versus random augmentation under matched
  augmentation count. Current point estimates are close (`+0.391` vs `+0.363`
  paired OOD delta), so this may be a limitation rather than a win.
- Phase 1 modular exact: `N=2` is a sanity check, not statistical evidence.
- Semantic retrieval: report the finite corpus/orbit construction clearly and
  avoid broad semantic robustness language.

## Artifact Work Needed

Before a conference submission, add public or redacted artifacts:

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
