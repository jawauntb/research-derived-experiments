# Critical Review: Vector First-Order Self

Date: 2026-07-06

## Verdict

Mixed result, high value. The paper proves that vector self/world attribution and
zero-shot priority reweighting can compose, while showing that autonomous probe
selection fails when raw uncertainty channels are not comparable.

## Main Issues

1. **Make the negative result constructive.** The scale-asymmetric calibration
   failure is not just a failed gate; it is a diagnostic for multi-concern agent
   architectures.
2. **Name the law.** A vector self needs comparable uncertainty channels before a
   shared intervention gate combines them.
3. **Separate behavior from inquiry.** The agent can behave vectorially while its
   inquiry policy is still dominated by one scalar residual scale.
4. **Clarify the reafference connection.** Reafferent attribution works per
   dimension only when the system can identify which dimension still needs a
   boundary-checking intervention.
5. **Reframe the next move.** Paper 21A is not an arbitrary calibration patch; it
   is the minimal architecture correction implied by this failure.

## Rewrite Applied

- Added an abstract-level architecture-law paragraph.
- Added Section 5.6, "Architecture law: comparable concern channels."
- Reframed the result as a warning for long-horizon agents that mix objectives,
  safety, tool reliability, uncertainty, and future optionality in one action
  gate.

## Contribution Opportunity

The major contribution is the "scalar concern wearing vector clothes" diagnostic:

> A system can have vector heads and vector behavior while its inquiry policy is
> still captured by the largest raw uncertainty scale.

This matters for machine agency because planning over many objectives requires
calibrated channels before any shared action or probe decision.
