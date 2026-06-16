---
title: Pixel-rendered concerned-syntax gates should transport controls
date: 2026-06-16
category: docs/solutions/architecture-patterns
module: concerned_syntax
problem_type: architecture_pattern
component: testing_framework
severity: medium
applies_when:
  - "A research branch claims a regime transition from symbolic or vector observations to pixels"
  - "The old gate already has meaningful positive and negative controls"
  - "A new perceptual surface could accidentally leak the hidden variable"
tags: [concerned-syntax, pixel-gate, object-extraction, anti-cheat, research-method]
---

# Pixel-rendered concerned-syntax gates should transport controls

## Context

Arc 2A needed to move beyond candidate parses and vector parts without losing
the diagnostic structure that made the earlier result meaningful. The risk was
to treat "pixels" as a cosmetic rendering step, then accidentally let the
image, feature extractor, or labels leak the hidden parse.

## Guidance

When changing the observation surface in a mechanism paper, change exactly one
regime component at first and transport the old gate intact. For the pixel
concerned-syntax branch, the structural change was:

```text
vector parts -> RGB image -> connected-component object attributes
```

The transported controls stayed the same:

- `surface_pixel_shortcut`: action prior without probing.
- `passive_pixel`: extracted object attributes without intervention.
- `restless_pixel_probe`: syntax recovery with no low-concern discipline.
- `concerned_pixel_probe`: object extraction plus concern-gated intervention.

The positive result is only accepted if the new surface also passes leakage
checks:

- Hidden true/alternate parse swap leaves the rendered image unchanged.
- Object extraction recovers the intended visible parts.
- Passive object features remain near chance on hidden binding.
- Restless probing recovers syntax but fails the low-concern cap.

## Why This Matters

A new artifact type is not automatically a scientific advance. It becomes
useful when the old explanation is transported and the residual content is
made explicit. Here the residual content is not "pixels improve accuracy"; it
is that the concerned-syntax gate survives a pixel-to-object operation while
passive object extraction remains insufficient.

This creates a cleaner next target: replace the algorithmic connected-component
extractor with a learned object-slot encoder, while preserving the same
hidden-parse invariance and no-restless controls.

## When to Apply

- Use this pattern before claiming a regime transition in Arc 2A or Arc 2B.
- Use it when moving from symbolic to vector, vector to pixel, pixel to learned
  slots, or hand-specified probes to invented interventions.
- Do not use it to justify broad claims about human vision, natural images, or
  full formal verification unless those gates were actually added.

## Examples

The pixel gate accepted:

```text
concerned_pixel_probe:
  parse-high: 0.996
  action:     0.999
  subtree:    0.786
  objects:    1.000
  low-probe:  0.187
  gate:       PASS
```

The controls preserved the failure taxonomy:

```text
passive_pixel:
  parse-high: 0.503
  subtree:    0.497
  gate:       fail

restless_pixel_probe:
  parse-high: 1.000
  low-probe:  1.000
  gate:       fail
```

## Related

- `experiments/concerned_syntax/pixel_shapes.py`
- `experiments/concerned_syntax/results/pixel_shapes_local_2026_06_16.md`
- `docs/discovery_regime_audit.md`
- `papers/concerned_syntax/paper.md`
