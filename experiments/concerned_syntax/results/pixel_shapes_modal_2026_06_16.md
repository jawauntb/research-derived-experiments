# Pixel Concerned-Syntax Agents

Date: 2026-06-16

Question: does the concerned-syntax gate survive when the surface is rendered as pixels and object attributes must be extracted from connected components?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs, 48x48 RGB images.

## Gate Summary

| Agent | Parse high | Action | Subtree | Objects | Ambiguity | High probe | Low probe | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| concerned_pixel_probe | 1.000 | 1.000 | 0.805 | 1.000 | 1.000 | 1.000 | 0.195 | 0.004 | PASS |
| passive_pixel | 0.499 | 0.874 | 0.506 | 1.000 | 1.000 | 0.000 | 0.000 | 0.054 | fail |
| restless_pixel_probe | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |
| surface_pixel_shortcut | 0.499 | 0.880 | 0.506 | 1.000 | 1.000 | 0.000 | 0.000 | 0.054 | fail |

## Interpretation

The pixel surface is still hidden-parse invariant: rendering uses visible role appearance and position, not the true parse assignment. A connected-component extractor recovers object centroids, sizes, colors, and shape density before learning. The accepted agent must therefore combine perceptual object extraction with a concern-gated pair probe. Surface shortcuts keep some action prior but fail hidden binding. Passive perceptual inference fails because the same image admits multiple hidden parses. Restless probing recovers binding while violating the low-concern cap.

Raw JSON remains local under `artifacts/concerned_syntax/`.
