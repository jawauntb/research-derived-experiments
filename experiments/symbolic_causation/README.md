# Symbolic Causation & Agency Benchmark

Instrument 3 of the Structural Observatory (see
[`notes/structural_intelligence_conjecture.md`](../../notes/structural_intelligence_conjecture.md)).

Hypothesis: a symbolic structure becomes causally effective only through
instantiation, but "changes behaviour" is not one quantity. Treating a symbolic
model/intervention `m` as an operation on a system's distribution over future
trajectories `P(γ | s)`, four distinct quantities dissociate:

- **signal** — `delta_kl = KL(P(γ|m) ‖ P(γ|baseline))`: does `m` move the
  trajectory distribution at all?
- **control / navigability** — `goal_gain`, `viability_gain`: does `m` raise the
  probability of reaching the target / avoiding failure?
- **knowledge** — `predictive_accuracy`: does `m` predict outcomes without
  necessarily changing them?
- **agency** — control **plus** correct causal self-attribution
  (`calibration_error` small: claimed effect ≈ true do-effect) **plus**
  `transfer` (the effect survives an environment perturbation `m` did not choose).

Method: an exact finite-state world with target and failure regions; futures are
enumerated to the horizon, so every quantity is computed in closed form (no
sampling). Seven hand-built conditions (baseline, noise_signal, control,
knowledge_only, false_credit, agent, brittle_controller) each realize a distinct
metric signature.

Pre-registered gates:

- `signal_dissociates_from_control`: `noise_signal` moves the distribution
  (`delta_kl > 0`) but does not raise `goal_gain`.
- `knowledge_dissociates_from_signal`: `knowledge_only` predicts perfectly with
  `delta_kl = 0`.
- `false_credit_is_uncaused_and_miscalibrated`: the outcome improves while the
  true do-effect is zero and calibration error is large (the agent miscredits an
  exogenous environmental enrichment).
- `agency_transfers` / `brittle_control_does_not_transfer`: the agent's effect
  survives a perturbation; the brittle controller's does not.
- `taxonomy_recovered`: a fixed threshold classifier assigns each condition its
  intended label, so no single scalar identifies agency.

This connects to the repo's causal-use and causally-grounded-agents lines
(`experiments/common/causal_use.py`, `experiments/world_responds`): it is a
minimal, exactly-computable statement of why final-outcome influence is
proxy-vulnerable.

Run:

```bash
python3 experiments/symbolic_causation/experiment.py --output experiments/symbolic_causation/results/symbolic_causation_summary.json
```
