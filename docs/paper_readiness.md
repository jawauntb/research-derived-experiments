# Paper Readiness Tracker

## Target Claim

The paper is not "activation steering works." The paper-worthy claim must be narrower:

```text
Semantic-specific activation steering requires separating concept transport from
label-surface control. Held-out aliases and independent adversarial controls expose
that distinction, and constrained control penalties trace a specificity frontier.
```

## Missing Evidence

| Requirement | Current state | Next gate |
| --- | --- | --- |
| More models | Pythia-70M only for alias/constrained runs. | Replicate best frontier on at least one larger open model and one small control model. |
| More concepts | Three promoted positives, two valence controls. | Expand positives and controls with same-category, cross-category, and random relation nulls. |
| Held-out aliases/controls | Added `alias_0`/`alias_1` regimes and leave-one-out control bases in the current branch. | Require positive transfer to `alias_1` while independent controls remain suppressed. |
| Baselines | Random, source/distractor, residual projection, hard/mean-control penalties. | Add CAA/CAV-style activation-vector baselines and, later, SAE/feature-guided baselines if feasible. |
| Statistical confidence | Single seed for most behavior runs. | Add seeds, bootstrap CIs over pairs, and random relation nulls. |
| Claim boundary | Informal "semantic specificity" language. | Define specificity as held-out target transfer minus independent control leakage under matched score surfaces. |
| Generation tests | Mostly label logprob scoring. | Add constrained free-generation or short-answer scoring after logprob gates pass. |
| Mechanistic analysis | Direction cosines and layer controls only. | Estimate control-channel rank/subspace structure and pair-specific residuals. |

## Current Phase

**Phase 1: verifier hardening.**  
Make the existing Pythia-70M result fail or survive under held-out aliases and independent controls.

Acceptance for moving to Phase 2:

- The best constrained direction keeps at least `2/3` positives under held-out `alias_1`.
- It suppresses independent valence controls better than raw target and residual-projection baselines.
- It does not rely only on construction-zeroing of `valence->steering_vector`.

Current Phase 1 result:

- Raw target directions transfer to held-out `alias_1`, but valence controls still pass.
- Constrained directions suppress controls more than raw target directions, but held-out `alias_1` positives drop to `2/3`.
- The systematic held-out failure is `attractor->attractor_network`, whose second alias `recurrent memory network` is more mechanistically specific than the training alias `stable-state network`.
- Phase 1 is not passed yet; the next attempt should train over multiple aliases jointly before adding model scale.

## Phase 2 Preview

If Phase 1 survives, expand along three axes:

- Model replication: add GPT-2 and a larger open causal LM if Modal budget allows.
- Concept expansion: add more positive bridges and random relation nulls.
- Baselines: add CAA/CAV-style activation differences against the same held-out alias verifier.

## Paper Draft Gate

Start the manuscript when the repo contains:

- A stable specificity-frontier table across at least two models or two seeds.
- A held-out alias/control result that survives independent controls.
- A baseline table showing why raw target gradients, residual projections, and random directions are insufficient.
- A definition of semantic specificity precise enough to be falsified.
