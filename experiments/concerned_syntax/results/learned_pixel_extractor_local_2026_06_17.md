# Learned Pixel Extractor Concerned Syntax

Date: 2026-06-17

Question: can a learned foreground/slot extractor replace the connected-component extractor while preserving the pixel-level concerned-syntax gate?

Manifest: 1200 train trials, 500 test trials, seed 20260617, 60 SGD epochs, 96 extractor samples/image, 48x48 RGB images.

## Extractor Summary

| Count | Slot recovery | Scene recovery | Center error |
|---:|---:|---:|---:|
| 1.000 | 1.000 | 1.000 | 0.018 |

## Gate Summary

| Agent | Parse high | Action | Subtree | Objects | High probe | Low probe | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| concerned_pixel_probe | 1.000 | 1.000 | 0.768 | 1.000 | 1.000 | 0.157 | 0.008 | PASS |
| passive_pixel | 0.544 | 0.878 | 0.492 | 1.000 | 0.000 | 0.000 | 0.058 | fail |
| restless_pixel_probe | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |
| surface_pixel_shortcut | 0.544 | 0.854 | 0.492 | 1.000 | 0.000 | 0.000 | 0.058 | fail |

## Interpretation

This is a learned extractor diagnostic, not a full CNN or unsupervised object-slot model. The extractor learns foreground pixels from RGB values, uses slot-local search to produce six slots, and then the existing pixel concerned-syntax agents consume those learned slots. Passing this gate shows that the 2A pixel result is not tied to direct connected-component features, while still leaving richer object-centric perception as future work.

Raw JSON remains local under `artifacts/concerned_syntax/`.
