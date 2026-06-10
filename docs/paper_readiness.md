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
| Baselines | Random, source/distractor, residual projection, hard/mean-control penalties, and CAA/CAV-style activation-difference baselines. | Add learned behavior-readout/generation baselines and, later, SAE/feature-guided baselines if feasible. |
| Statistical confidence | Single seed for most behavior runs. | Add seeds, bootstrap CIs over pairs, and random relation nulls. |
| Claim boundary | `docs/semantic_specificity.md` defines specificity as held-out target transfer minus independent control leakage under matched score surfaces. | Keep the claim boundary in the paper draft and do not promote runs with near-zero specificity. |
| Generation tests | Added strict short-generation match, learned generation-readout, constrained short-answer gates, a direct binary-relation behavior gate, binary yes-bias controls, and contrastive binary directions. Generation remains zero. Binary relation classification moves behavior, but yes-bias-aware gating rejects the apparent pocket. | Treat binary relation as a diagnostic verifier unless top-PC residualization preserves target movement. |
| Mechanistic analysis | Full-label alias leakage is not explained by one low-rank control vector, but the binary yes/no surface is strongly low-rank: target + control gradients have first-PC energy `0.895` and first-three-PC energy `0.930`. | Test whether removing/whitening the dominant binary axis preserves any target-specific movement. |

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
- CAA/CAV-style activation-difference baselines are active and sometimes improve mean specificity relative to target-gradient directions, but they still fail random-null specificity. The best source held-out alias CAA row is `7/7` positives, `7/10` controls, specificity `0.066`; the best latent row is `7/7` positives, `10/10` controls, specificity `0.043`.
- A strict non-logprob generation-match gate rejects the current behavior directions as generated semantic steering. After requiring the steered continuation to actually match the target label, source and latent prompt frames both show `0/7` target-positive passes and `0/10` random-null passes for target-gradient, CAA, and random directions.
- The only nonzero source-passage generation margin deltas come from source-label suppression, not target generation, so they are recorded as failures rather than passes.
- A learned generation-readout gate agrees with the exact-match gate. After requiring target-margin improvement, target-score increase, and steered `best_role == target`, source and latent prompt frames both show `0/7` positives and `0/10` random-null controls for target-gradient, CAA, and random directions.
- The only nonzero readout margin pocket is `validity_gate->weak_constraint` under source-passage CAA, but the steered best role remains `source`, so it is explicitly rejected.
- A constrained short-answer interface also fails to recover target behavior. Exact match and learned readout both show `0/7` positives and `0/10` random-null controls for target-gradient, CAA, and random directions in both `source_short_answer` and `latent_short_answer`.
- Source-conditioned short-answer prompts mostly repeat the source passage; source-free latent short-answer prompts collapse to generic continuations such as `The term "word" is`.
- A direct binary-relation classifier produces the first nonzero behavior movement: `target_learned` passes `4/7` positives and `3/10` random relation nulls, with mean specificity `0.118`; CAA and random remain `0/7` positives and `0/10` controls.
- The binary signal is confounded: target/source/distractor learned directions are highly collinear, usually around `0.97` to `0.99`, and the target direction increases target Yes-No margin on nearly every row. The next gate must separate relation movement from a broad Yes-bias or candidate-affirmation axis.
- Binary yes-bias controls explain the confound directly. Under `target_learned`, target/source/distractor, blank, generic, shuffled-target, always-true, and always-false Yes-No margins all end positive in `17/17` rows. Mean positive-slice deltas are all about `4.1` to `4.5`.
- Contrastive binary directions are now tested under a strict yes-bias-aware gate. All directions fail strict semantic specificity: `target_learned` has `4/7` loose positive passes but `0/7` strict passes; `target_binary_controls_0_5` has `4/7` loose positives but `0/7` strict; weights `1.0+` suppress controls by also collapsing or reversing target movement.
- Binary gradient geometry shows why: the target/control yes-no gradient field is highly low-rank, with target gradients first-PC energy `0.926`, control gradients first-PC energy `0.891`, and combined target-plus-control first-PC energy `0.895`.
- Phase 1 is not passed yet. The current full-label logprob gate should be treated as a diagnostic failure mode, generation gates are negative, and binary relation behavior is nonzero but dominated by answer-polarity control.

## Phase 2 Preview

If Phase 1 survives, expand along three axes:

- Model replication: add GPT-2 and a larger open causal LM if Modal budget allows.
- Concept expansion: add more positive bridges and random relation nulls.
- Baselines: compare generation/readout behavior against the existing target-gradient, residual, random, and CAA/CAV-style activation-difference baselines.
- Verifier pivot: add relation-specific contrast directions and promote yes-bias controls into the binary robust-pass rule.

## Paper Draft Gate

Start the manuscript when the repo contains:

- A stable specificity-frontier table across at least two models or two seeds.
- A held-out alias/control result that survives independent controls.
- A baseline table showing why raw target gradients, residual projections, and random directions are insufficient.
- A definition of semantic specificity precise enough to be falsified.
