# Critical Review: Planning from Concern Paper

Date: 2026-07-06

## Verdict

Revise and strengthen. This paper contains one of the program's cleanest
architecture results: a learned action-conditioned viability model can become
the policy by direct argmax, eliminating the sparse policy-learning bottleneck.
The empirical result is strong; the paper should name the architecture law more
explicitly.

## Main Issues

1. **Name predictive policy closure.** The paper should say plainly that the
   predictive model closes the action loop. A separate policy head is not
   merely unnecessary here; it is an avoidable bottleneck.
2. **Connect the result to agent architecture.** This is the simple change the
   program can export: train on observed viability deltas, then act by querying
   the learned counterfactual action model.
3. **Keep the boundary honest.** The result is one-step, scalar-viability,
   stationary, and non-epistemic. It is a precursor agency result, not full
   selfhood or consciousness.
4. **Make the relationship to long-horizon tasks explicit.** Long-horizon
   agents need memory to reach commitment surfaces; this paper shows how a
   current predictive model can itself be a commitment surface.
5. **Frame the next architectural extension.** The obvious next move is
   predictive closure plus uncertainty, multi-step rollout, and epistemic
   value, not a return to opaque policy-head training.

## Rewrite Applied

- Added an abstract-level architecture lesson.
- Added Section 5, "Architecture Law: Predictive Policy Closure."
- Added Figure 6, a predictive-policy closure diagram.
- Renumbered downstream sections.

## Contribution Opportunity

The major contribution is a small but powerful architecture recipe:

> If the model learns action-conditioned change in what the agent cares about,
> first try planning by the model's own action argmax before training a separate
> policy.

That is a concrete bridge from concern-shaped representation to machine agency.
