# Release Checklist

## Main Paper Scope

- [x] Main paper centers Suite C and Suite D/E.
- [x] Suites A/B/F are appendix/background only.
- [x] Minimum pass rule is explicit.
- [x] Claim boundary excludes consciousness, production reliability, and human
  or biological validation.
- [x] Related work covers agent mechanisms, agent benchmarks, reward hacking,
  and goal misgeneralization.

## Public Benchmark Package

- [ ] Public JSONL rows for Suite C finite gate.
- [x] Public Suite C summary JSON.
- [x] Public Suite C learned-transfer summary JSON.
- [x] Suite C benchmark card.
- [ ] Public fixture JSONL rows for Suite D/E API benchmark.
- [x] Suite D/E benchmark card.
- [x] Shared release schema document.
- [x] Shared machine-readable release schema.
- [ ] Generated minimum-pass-rule vector figure.
- [ ] Quantitative Suite D/E hidden-state and API figures.

## Submission Risks

- Suite C now has a positive finite teacher-free reward/CEM layer, but it still
  uses a privileged source-identity feature and remains a finite-harness result.
- Suite D/E API results are behavior-only for closed models.
- Raw local Modal artifacts should not be published without curation.
- The package is better suited to a benchmark/workshop/dataset venue unless
  public fixtures and one-command reproduction are tightened.

## Validation Run

Completed on 2026-07-06:

- `tectonic paper.tex` passed and generated `paper.pdf`.
- Shared repo checks passed: `uvx ruff check .` and `ty check scripts experiments tests`.
- Targeted dependent-suite tests passed: 104 passed, 3 skipped across
  structure-compatible generalization, Suite C, Suite C neural transfer, and
  long-horizon bottleneck.
