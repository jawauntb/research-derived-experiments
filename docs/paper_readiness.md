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
| More concepts | Expanded behavior gate now has seven positives, five mixed controls, six target-disjoint controls, and ten random relation nulls. | Add bootstrap confidence intervals over pairs and random-null draws once a verifier separates positives from nulls. |
| Held-out aliases/controls | Added third aliases and a train-on-`alias_0+alias_1` / test-on-`alias_2` gate. | Diagnose why held-out transfer moves controls as much as positives. |
| Baselines | Random, source/distractor, residual projection, hard/mean-control penalties. | Add CAA/CAV-style activation-vector baselines and, later, SAE/feature-guided baselines if feasible. |
| Statistical confidence | Single seed for most behavior runs. | Add seeds, bootstrap CIs over pairs, and random relation nulls. |
| Claim boundary | `docs/semantic_specificity.md` defines specificity as held-out target transfer minus independent control leakage under matched score surfaces. | Keep the claim boundary in the paper draft and do not promote runs with near-zero specificity. |
| Generation tests | Mostly label logprob scoring. | Add constrained free-generation or short-answer scoring after logprob gates pass. |
| Mechanistic analysis | Direction-subspace diagnostic shows leakage is not one low-rank control vector; high overlaps are pair/target-pocket specific. | Add target-disjoint random relation nulls and stratify controls by target/source overlap. |

## Current Phase

**Phase 1: verifier hardening.**  
Make the existing Pythia-70M result fail or survive under held-out aliases and independent controls.

Acceptance for moving to Phase 2:

- The best constrained direction keeps at least `6/7` positives under held-out `alias_2`.
- It suppresses independent controls enough to make specificity clearly positive against raw target and residual-projection baselines.
- It does not rely only on construction-zeroing of `valence->steering_vector`.

Current Phase 1 result:

- Raw target directions transfer to held-out `alias_1`, but valence controls still pass.
- Constrained directions suppress controls more than raw target directions, but held-out `alias_1` positives drop to `2/3`.
- The systematic held-out failure is `attractor->attractor_network`, whose second alias `recurrent memory network` is more mechanistically specific than the training alias `stable-state network`.
- Multi-alias training over `alias_0+alias_1` improves held-out `alias_2` transfer on an expanded pair set: target-learned directions move `6/7` positives in both prompt frames.
- The expanded gate still fails semantic specificity: controls pass `5/5`, and held-out `alias_2` specificity is only `0.034` in `source_passage` and `0.002` in `latent_choice`.
- Direction-subspace diagnosis points away from a simple shared low-rank control leak: control effective rank is about `4.2/5`, and the full control subspace captures only `0.159` to `0.194` positive energy on average.
- The strongest leaks are pair-specific target pockets, especially `conceptual_space->representation_manifold` overlapping with `homeostasis->representation_manifold`.
- Target-disjoint controls do not rescue specificity. Target-learned directions move `6/7` positives but also `6/6` target-disjoint controls in both prompt frames.
- Held-out `alias_2` specificity with target-disjoint controls is only `0.066` in `source_passage` and `0.007` in `latent_choice`; canonical specificity is negative.
- Random relation nulls make the failure decisive: target-learned directions move `6/7` positives but `10/10` random null controls in both prompt frames.
- Random-null held-out `alias_2` specificity is negative: `-0.101` in `source_passage` and `-0.137` in `latent_choice`; canonical specificity is also negative.
- Phase 1 is not passed yet. The current full-label logprob gate should be treated as a diagnostic failure mode. The next attempt should add CAA/CAV-style baselines and a non-logprob generation or learned behavior-readout gate before adding model scale.

## Phase 2 Preview

If Phase 1 survives, expand along three axes:

- Model replication: add GPT-2 and a larger open causal LM if Modal budget allows.
- Concept expansion: add more positive bridges and random relation nulls.
- Baselines: add CAA/CAV-style activation differences against the same held-out alias verifier.
- Verifier pivot: add generation or learned behavior-readout tests that can separate true relation behavior from broad target-label promotion.

## Paper Draft Gate

Start the manuscript when the repo contains:

- A stable specificity-frontier table across at least two models or two seeds.
- A held-out alias/control result that survives independent controls.
- A baseline table showing why raw target gradients, residual projections, and random directions are insufficient.
- A definition of semantic specificity precise enough to be falsified.
