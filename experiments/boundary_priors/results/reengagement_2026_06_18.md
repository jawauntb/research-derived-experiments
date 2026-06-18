# Boundary Priors (Track 3) — Costly Probing & Selective Re-engagement

Date: 2026-06-18
Code: `experiments/boundary_priors/reengagement.py`
Pre-registration: `experiments/boundary_priors/preregistration.md` (mechanism gates M1–M4)
Artifact: `artifacts/boundary_priors/reengagement.json`
Seeds: 20260610, 1729, 4242

## Question

The diagnostic pilot showed a plastic boundary prior recovers after the boundary
moves. But that agent probed at a fixed rate. The mechanism-tier question (the
metric-stack's Paper 23B maintained-boundary signature): when probing **costs
viability** and is the *only* way to discover newly controllable channels, does
the agent **go quiet once the boundary is learned, re-engage after it moves, then
satiate** — and does that selective discipline beat constant probing?

## Setup changes vs. the pilot

- Probing costs viability (`probe_cost = 0.06` per probe step).
- Exploitation actuates **only** believed-self channels (no free exploration), so
  a newly controllable channel can be found *only* via an explicit probe.
- A forced 60-step warmup lets every condition learn the initial boundary.
- Positive agent `reengaging`: probe propensity = base + uncertainty + control-
  surprise − effort-cooling. Controls: `fixed_probe` (0.25), `restless` (0.60),
  `no_probe` (0.0 after warmup).

## Result: the re-engagement signature holds (3/3); net-reward dominance is 2/3

| Condition | probe pre | probe early-post | probe late-post | net reward (late) | boundary acc (late) |
|---|---:|---:|---:|---:|---:|
| `reengaging` | **0.064** | **0.158** | **0.072** | 0.678 | 0.975 |
| `fixed_probe` | 0.228 | 0.250 | 0.261 | 0.653 | 0.990 |
| `restless` | 0.617 | 0.617 | 0.658 | 0.617 | 0.943 |
| `no_probe` | 0.000 | 0.000 | 0.000 | 0.530 | **0.625** |

(3-seed means. "early-post" = 40 steps right after the shift; "late-post" = a
steady window 160+ steps after.)

- **M1 (selective re-engagement): PASS (3/3).** Probe rate is quiet pre-shift
  (0.058–0.067), spikes 2.2–2.6× right after the shift (0.150–0.175), per seed.
- **M2 (satiation): PASS (3/3).** Late-post probe rate (0.067–0.075) falls back
  below the post-shift spike — the agent cools once it has re-identified the
  controllable set.
- **M4 (no-false-calm): PASS (3/3).** Late boundary accuracy 0.926–0.999 — the
  probing fell because attribution resolved, not because the agent gave up.
- **Context: `no_probe` fails to recover (3/3).** Without probing, late boundary
  accuracy is 0.625 and net reward 0.530 — so probing is genuinely necessary.
  (This was the kill criterion the *first* design tripped, when an exploit
  fill-branch explored for free; restricting exploitation to believed-self fixed
  it.)
- **M3 (net-reward dominance under cost): PARTIAL (2/3).** `reengaging` beats both
  constant probers on seeds 1729 (0.698 vs 0.647/0.612) and 4242 (0.677 vs
  0.643/0.618), but is narrowly edged by `fixed_probe` on seed 20260610 (0.658 vs
  0.668).

## Interpretation (honest)

The **maintained-boundary signature is real and clean**: the agent detects the
boundary move via control-surprise, allocates a probe burst, then satiates —
without false calm, on every seed. This is the first mechanism-tier behavior in
Track 3 and the direct analog of the metric-stack's Paper 23B cycle, now applied
to the boundary *location* rather than the mediated/exogenous split.

The economic claim is weaker and honestly partial. `reengaging` is far more
**probe-efficient** — ~0.07 late probe rate vs. `fixed_probe`'s 0.26 (~3.6×
fewer probes) for comparable recovery (bacc 0.975 vs. 0.990). But this parsimony
costs a little completeness: on seed 20260610 it recovers to only 0.926 boundary
accuracy, and the always-on prober's fuller recovery (0.99) plus the modest probe
cost is enough to edge it out on net reward there. This is the parsimony-vs-
completeness tradeoff, and it is the *same 2/3-seed pattern* the metric-stack's
own winning `decision_refractory` mechanism showed (Paper 23B). We report it as a
partial economic result, not a pass.

**`probe_cost` transparency:** it was raised once (0.02 → 0.06) after an initial
run showed 0.02 was too small to make probing economically distinguishable. No
other gate parameter was tuned to results, and 0.06 still yields only 2/3 on M3 —
we did not keep pushing it to force a green gate.

## Claim tier

**Mechanism (signature), with a partial economic result.** M1+M2+M4 (the
re-engagement signature) pass on all seeds; M3 (net-reward dominance) passes on
2/3. `all_pass` is `False` by the pre-registered conjunction, and we leave it
that way rather than redefine the gate post hoc.

## Discovery-regime audit

- **Regime:** boundary-location attribution with *costly* epistemic action; the
  probe policy itself is now the object of interest.
- **Residual the regime cannot explain:** why one seed under-probes to incomplete
  recovery — is it initial-condition sensitivity of the surprise trigger, or a
  genuine coverage gap when newly-self channels are never randomly hit during the
  burst? A budget-aware probe target (probe the *least-recently-confirmed*
  channels rather than uniform random) is the obvious next refinement.

## Next

1. Replace uniform-random probing with a coverage-aware probe target; test
   whether M3 reaches 3/3 without raising `probe_cost`.
2. Let `num_self` change at the shift (lose effectors) — a harder boundary move.
3. Represent the boundary as a navigable embedding coordinate
   (Levin 2026 remapping/navigation; see `references/levin_recent_papers_2026_06.md`).
