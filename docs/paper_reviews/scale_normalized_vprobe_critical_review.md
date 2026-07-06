# Critical Review: Scale-Normalized V_probe

Date: 2026-07-06

## Verdict

Strong corrective result, but bounded. The paper closes the vector scale-collapse
failure from Paper 20B and gives a simple architecture rule: normalize uncertainty
channels before allocating scarce inquiry. It does not yet prove learned
selection beats matched-volume random probing in easy convergent settings.

## Main Issues

1. **Lead with the architecture change.** The core result is not "another
   factorial"; it is a small normalization layer that turns a vector inquiry
   failure into stable attribution.
2. **Keep selectivity honest.** The learned probe becomes quiet after
   convergence, so G14/G15 are not a victory. This is good epistemic behavior but
   a weak selectivity test.
3. **Tie the result back to Paper 20B.** The paper should read as the direct
   correction to comparable-channel failure.
4. **Connect to long-horizon agents.** Planner uncertainty, memory retrieval
   confidence, tool errors, and safety risk are all different units; raw gates
   will be captured by the largest scale.
5. **Point forward to nonstationarity.** The next contribution needs a world
   where uncertainty returns after apparent convergence.

## Rewrite Applied

- Added an abstract-level architecture-law paragraph.
- Added Section 5.7, "Architecture law: normalized inquiry budgets."
- Explicitly bounded the claim: scale normalization restores stable attribution,
  while re-engagement/selectivity requires harder nonstationary tests.

## Contribution Opportunity

The major contribution is a practical law for agent meta-control:

> Normalize uncertainty before using it to allocate attention, memory replay, or
> probe actions.

This is a simple architecture change with obvious relevance to long-horizon
planning systems and multi-objective agents.
