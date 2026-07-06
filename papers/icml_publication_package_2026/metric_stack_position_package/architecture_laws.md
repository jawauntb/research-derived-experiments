# Architecture Laws for Concern-Mediated Finite Agents

These laws summarize the broad metric-stack arc in a reviewer-safe form.

## Law 1: Behavior Is Not Load-Bearing Structure

Do not accept return, final accuracy, or tool success alone. Add a gate showing
that the intended variable or decomposition actually controls the behavior.

## Law 2: Preserve Vector-Valued Concern Until Decision Time

Premature scalar rewards hide priority shifts. Vector concern supports
zero-shot reweighting and exposes which dimension matters.

## Law 3: Attribution Needs Identifying Interventions

Passive factorization does not break self/world gauge symmetry. Use source
labels, null interventions, temporal asymmetry, or contrastive interventions.

## Law 4: Uncertainty Must Be Calibrated Against Current Evidence

Historical residual scale and ensemble variance can fail when the model is
systematically wrong. Recompute error against recent raw evidence.

## Law 5: Quiet Is Not Stability

An agent that stops probing after convergence may fail after world change.
Re-engagement and no-false-calm gates are required.

## Law 6: Cool The Decision, Not The Signal

Healthy habituation lowers unnecessary probes while preserving surprise as
information. Signal suppression creates false calm.

## Law 7: Memory Matters At Commitment Surfaces

Memory becomes agent-relevant when a future-critical variable reaches an action,
tool, schema, repair, emitted value, or causal readout surface.

## Law 8: Generalization Requires Deployment-Compatible Structure

When ID evidence underdetermines shortcut and rule, select or train for
compatibility with the transformations deployment will require.

## Law 9: Every Capability Needs A Proxy Search

For each proposed capability, ask what proxy can make behavior pass without the
intended structure. Then add the smallest gate or architecture change that makes
the intended structure load-bearing.

