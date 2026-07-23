# Wave 0 figures — placeholder notice

**Status:** placeholder assets pending the calibration Modal run

The PNGs currently committed under
`papers/concern_gated_retrieval_wave0/figures/` are **placeholder** figures
rendered by `build_figures.py`. They are intentionally checked in so the paper
draft has visual scaffolding, but they are **not** the confirmatory record of
the Wave 0 calibration.

## What is real vs placeholder

| Figure | Structural content | Numeric content |
|---|---|---|
| `fig1_pipeline` | Real — the six-stage pipeline is fixed by §3–§7 of `PREREGISTRATION.md`. | N/A — no numbers depicted. |
| `fig2_wrong_prior` | Real — the adversarial shape is fixed by §5 of `PREREGISTRATION.md` (alarm inflated, at least one commitment suppressed). | Illustrative weights only; the actual per-family alarm and suppressed-commitment identifiers are evaluator-only. |
| `fig3_family_matrix` | Real — three families x six properties come from §4 and §6 of `PREREGISTRATION.md`. | Intensity is a calibration-scaffolding label, not a metric. |
| `fig4_baseline_slate` | Real — twelve baseline categories mirror §7 of `PREREGISTRATION.md`. | The "matched-budget dimensions" axis is a scaffolding count, not a performance number. "`[scored]`" annotations reflect whichever baselines the calibration summary already recorded. |
| `fig5_leakage_barriers` | Real — evaluator-only field list comes from §4.1 of `PREREGISTRATION.md`. | N/A — no numbers depicted. |
| `fig6_calibration_grid` | Real when `calibration_summary.json` is present; placeholder otherwise. | Numbers come directly from `experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json` when it exists. When absent, the figure carries a "placeholder — replaced by Modal run" watermark. |

## Aesthetic

The figures emulate the [Dither Kit](https://www.tripwire.sh/dither-kit)
retro-chart look — an ordered categorical palette, hatch-fill overlays as a
matplotlib approximation of ordered dither, monospace typography, and
letter-spaced UPPERCASE titles. Dither Kit itself is a React library and is
not a runtime dependency; the aesthetic is re-implemented in matplotlib so
the same asset renders in both light and dark mode without a JS runtime.

## How to regenerate

```bash
cd papers/concern_gated_retrieval_wave0/figures
python build_figures.py
```

The script writes `figN_<name>_dark.png` and `figN_<name>_light.png` for
`N ∈ {1, 2, 3, 4, 5, 6}` into this directory. It is deterministic and
idempotent. When
`experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json`
is present, `fig6` uses the real per-family variance rows; otherwise it
stamps the placeholder watermark.

## When does the placeholder notice come down

The placeholder watermark on `fig6` disappears automatically once the
calibration Modal run has populated `calibration_summary.json`. This notice
should stay in place until:

1. The Modal calibration run has completed and the summary JSON is committed.
2. The preregistration signature block in `PREREGISTRATION.md` has been
   filled with the calibration manifest hash.
3. `PROVENANCE.md` records the Modal deploy hash and the calibration seed
   range receipt.

None of the figures make a mechanism claim. Wave 0 remains a calibration
scaffolding + wrong-prior initialization step; the figures depict that
scaffolding and nothing more.
