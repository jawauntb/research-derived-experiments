# Critical Review: Long-Horizon Moved-Bottleneck Paper

Date: 2026-07-06

## Verdict

Revise and strengthen. The empirical ladder is unusually strong: synthetic
memory transport, tool commitment, repair, generated JSON, hidden localization,
causal patching, prompt-family robustness, and black-box API behavior all live
in one bounded diagnostic. The paper's weakness is not evidence; it is that the
architecture lesson is implicit.

## Main Issues

1. **The result needs a named architecture law.** The paper says future control
   moves memory, but it should state the stronger design lesson: memory becomes
   agent-relevant when it is bound to a future commitment surface.
2. **The evidence ladder needs a visual.** The current table is accurate but
   dense. A reviewer should see the progression from behavior to hidden state,
   commitment, repair, generated action tokens, causal patching, and API
   behavior at a glance.
3. **The prompt-final negative is a strength.** The paper should emphasize that
   value-prefix states pass while prompt-final sites fail. That boundary is what
   prevents a vague "memory is somewhere" claim.
4. **The agency/consciousness boundary should remain strict.** This is a
   diagnostic for commitment-sensitive memory and action surfaces. It is not a
   production-agent autonomy or consciousness claim.
5. **The connection to the Metric Stack should be explicit but bounded.** The
   long-horizon result is the temporal/action-surface complement to concern
   calibration: relevant variables matter when they become constraints on
   future action.

## Rewrite Applied

- Added an architecture-law sentence to the abstract.
- Added a new section, "Architecture Law: Commitment Surfaces," between
  Interpretation and Boundaries.
- Added Figure 1, a commitment-surface evidence ladder.
- Tightened the remaining-work close around benchmark-card publication.

## Contribution Opportunity

The major contribution is a reusable test surface for long-horizon machine
agency:

> Does the variable that will later govern action become specifically
> represented at the memory, commitment, generated-action, and causal-readout
> surfaces where that action is actually selected?

That is a stronger benchmark target than final-task success and a cleaner
interpretability target than generic memory probing.
