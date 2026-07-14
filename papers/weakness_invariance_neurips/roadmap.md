# Weakness Invariance Paper Roadmap

Working title: Weak Invariant Structure Predicts Out-of-Distribution Generalization

## Central Claim

When multiple hypotheses fit the observed data, OOD generalization is predicted by weakness: the size or richness of the compatible transformation set under which the hypothesis remains valid. In the first symbolic regime, weakness beats training loss, simplicity, compression, a flatness proxy, and random selection.

## Current Evidence

The prefix-shift pilot creates a deliberately adversarial setting:

- The local patch, memorizer, and global shift all fit the training data.
- The local patch is shorter and more compressed than the global rule.
- The global rule is the only train-perfect candidate with high translation equivariance.
- Weakness selects the invariant rule in 300/300 trials and reaches 100% mean OOD accuracy.
- Train loss, simplicity, compression, and the current flatness proxy select the local patch in 300/300 trials and reach 0% mean OOD accuracy.

Public report:

- `experiments/symbolic_weakness/results/prefix_shift_pilot_2026_06_09.md`

## NeurIPS-Grade Experimental Program

1. Symbolic benchmark suite

   Add multiple task families where local shortcuts fit the training split but fail under held-out transformations:

   - cyclic shifts with varied moduli and train windows;
   - parity/coset rules with biased support;
   - color and symbol permutation invariants;
   - grammar-preserving relabelings;
   - compositional transformations with ambiguous local evidence.

2. Baseline selectors

   Compare weakness against:

   - train and validation loss;
   - shortest program or hand-coded description length;
   - compression and MDL-style penalties;
   - flatness/sharpness proxies;
   - random train-consistent selection;
   - LLM-proposed hypotheses scored by the same metrics.

3. Learned-model version

   Train small MLPs, transformers, and sequence models on the symbolic tasks. Evaluate whether representation-level weakness predicts OOD generalization:

   - latent equivariance under known transformations;
   - compatible transformation volume in hidden space;
   - invariance of logits or readouts under group actions;
   - learned rule probes from hidden states.

4. Transformation discovery

   Move beyond supplied groups:

   - infer candidate transformations from data augmentations;
   - learn transformations that preserve training constraints;
   - penalize transformations that also preserve adversarial wrong rules;
   - distinguish true invariance from accidental symmetries.

5. Mechanistic connection

   Connect the symbolic result to the broader thesis:

   - weakness is not mere simplicity;
   - weakness is constraint-compatible freedom;
   - OOD generalization appears when the learned object is stable under a larger admissible transformation set;
   - this gives a concrete bridge between attractors, conceptual spaces, activation geometry, and invariant rule formation.

## Reviewer Risks

- The first result is too toy-like.
  - Mitigation: add multiple symbolic task families and neural learners.

- The weakness metric uses oracle knowledge of the transformation group.
  - Mitigation: add wrong-group, incomplete-group, noisy-group, and learned-group experiments.

- Flatness and compression baselines are too weak.
  - Mitigation: the finite conditional KL bridge is now derived in
    `pac_bayes_weakness_sketch.md`; next run its exact aligned/wrong-group
    enumeration, then add neural PAC-Bayes perturbation sensitivity and
    executable MDL baselines only if that severe test survives.

- Weakness may collapse into group-invariant simplicity.
  - Mitigation: include cases where the invariant rule is longer than the local shortcut and cases where short symmetric but wrong rules exist.

## First Paper Skeleton

1. Introduction: why loss and simplicity cannot distinguish local shortcut from invariant rule.
2. Definition: weakness as compatible transformation volume.
3. Symbolic benchmark: task families, candidate classes, selectors, OOD splits.
4. Results: weakness predicts OOD across symbolic tasks.
5. Neural extension: latent weakness predicts OOD across trained models.
6. Ablations: wrong groups, noisy groups, flatness/compression controls.
7. Discussion: weakness as a concrete operational bridge for generative invariance.
