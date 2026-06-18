# Boundary Priors (Track 3)

A minimal embodied agent acts through `K` channels, each secretly **SELF**
(action-controllable, persists, drifts off-target unless maintained) or
**WORLD** (exogenous, action ignored). Under a limited actuation budget the
agent must infer the self/world boundary to spend its budget on controllable
channels. At a regime shift the boundary moves (a disjoint tool swap), and the
question is whether adaptability needs a *plastic, removable* separation prior
or whether a correct *fixed* prior suffices.

Thesis under test: the self/world boundary is a **prior, not an evidentially
fixed fact** ("There Is No Self-Evidence"; Levin's TAME). This is the
synthesis's Track 3 and the metric-stack paper's §18 next direction (make the
boundary *location* the learned object).

Pre-registered gates and conditions: see `preregistration.md`.
Pilot result and honest caveats: see `results/pilot_2026_06_18.md`.

Run (pure standard library, deterministic, ~1s):

```bash
python3 -m experiments.boundary_priors.experiment \
    --out artifacts/boundary_priors/pilot.json
```

The run prints a JSON payload with `summary`, pre-registered `gates`, and
per-cell `results`. Headline (3-seed): all four gates pass at **diagnostic**
tier — a correct fixed prior collapses after the boundary moves (reward
0.680 → 0.498), the plastic prior holds (0.684 → 0.687) by re-tracking the
boundary in ~7 steps, and a shuffled-attribution control fails to recover
(showing the mechanism is genuine self/world credit assignment, not generic
plasticity).
