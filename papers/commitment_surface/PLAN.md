# The Commitment Surface: Plan

Frozen: 2026-07-09.

## Thesis (reframe)

Old frame: **right geometry ⇒ load-bearing**. Weakness / concern geometry are
primitives; if a candidate representation carries the right invariance or the
right concern warping, it will do the OOD work.

New frame: **proxy-readable structure is the default; load-bearing structure is
what survives transport to a commitment surface under gauge-fixing anti-cheat.**
Weakness and concern geometry are *diagnostics* — powerful when they coincide
with the deployment-generating structure, footprints or anti-correlates
otherwise. Load-bearing structure is what participates in a train-time
compatibility intervention whose causal contribution at the commitment surface
survives patching, gauge-fix and change-of-commitment.

Compressed slogan (paper title candidate):

> **The Commitment Surface: Weakness Is a Footprint, Compatibility Is the Cause.**

## What the paper claims

C1. Availability ≠ load-bearing. High-AUC geometric readouts (probes,
weakness signatures) do not entail causal use. Load-bearing structure is
identified by *commitment-surface survival*: (i) train-time compatibility
intervention lifts OOD, (ii) causal patch/ablate produces a CE ≥ ε on the
target commitment, (iii) the effect survives gauge fixing and change of
commitment.

C2. Weakness / compatibility is a *diagnostic when aligned, footprint when
not.* In cyclic/dihedral toys the alignment holds; in Pythia LoRA modular
addition it does not, and readout-only selectors hard-kill. A train-time
compatibility intervention, however, recovers the OOD lift.

C3. Concern is instrument-indexed, not portable-scalar. A single scalar
`kappa` deforms metrics in the domain that generated it (spatial) but does
not transport by identity to a foreign one (semantic; margin lift −0.441).
Its role is a local anti-Goodhart weight over deployment futures — not a
substrate-independent universal.

C4. Agency = anti-Goodhart control loop. The passive→active correction chain
(Papers 5–25) is compressed by: *detect → allocate → saturate → cool →
reopen*. Sophisticated planners that optimize a proxy (uncertainty,
current-error) without decision-layer cooling regress; the load-bearing
signal is *commitment cooling under intervention-pinned residuals.*

C5. Boundary condition: benchmarks whose generator matches the geometry
prior (cyclic modular addition, low-n dihedral) recover old-frame
predictions as a special case. This localizes the geometry story instead of
retracting it.

## Falsifiers (pre-registered)

Commitment-first frame dies if any of:

F1. In an in-lab synthetic where a train-time compatibility-augmentation arm
(true group) and a weakness-readout selector both have access to the same
model family, the readout selector matches or beats the compatibility
arm on held-out OOD accuracy while the compatibility arm shows CE ≥ ε
under patching.

F2. On the Pythia LoRA v2 external contact, pure weakness readout (Arm A)
matches or exceeds compatibility-augmented training (Arm B) on OOD
accuracy at n ∈ {13,17,23}, and Arm B shows patch-CE < ε.

F3. Cross-domain identity transport of `kappa` recovers the semantic margin
lift the plain scalar failed to recover.

F4. The anti-Goodhart control loop (M4) can be dropped (no decision-layer
cooling; no intervention pinning) without regressing Suite C world-change
re-engagement.

Old geometry-first frame dies if any of:

G1. Weakness readout stays at floor (Arm A OOD ≤ 0.05) on Pythia LoRA v2
while compatibility-augmented training (Arm B) clears OOD ≥ 0.5 at the
same modulus + size.

G2. Concern-weighted weakness with true deployment weighting beats
unweighted weakness by ≥ 0.10 OOD accuracy in the unequal-consequence
synthetic when the weighting is well-specified, and misspecified weighting
(random weights) is not distinguishable from unweighted.

G3. On causal patching of the "high-readout" component, CE < ε in ≥ half of
cells where Arm A predicted high OOD.

## Experiment package (four severe tests)

### E1 — Unequal-Consequence Concern-Weighted Selector (synthetic, in-lab)

Domain: cyclic + dihedral toys from `weakness_invariance_neurips`. New knob:
OOD deployment blocks weighted unequally by `kappa`. Arms: (a) unweighted
weakness, (b) concern-weighted weakness (well-specified `kappa`),
(c) concern-weighted weakness (misspecified random `kappa`), (d) loss.
Prediction (new frame): (b) beats (a) iff weighting aligns with deployment
generator; (c) not distinguishable from (a). Falsifier: (b) matches (a)
under alignment, or (c) beats (a).

### E2 — Compatibility Augmentation vs Weakness Readout (synthetic, in-lab)

The core M3 discriminator. Same cyclic/dihedral toys. Arms:
(A) weakness-readout selector, (B) train-time compatibility augmentation
(true group), (C) train-time wrong-group augmentation, (D) loss selector.
Measurements: OOD accuracy AND patch-CE (ablate the compatibility-aligned
component and measure commitment shift). Prediction (new frame):
(B) > (A) with (B) exhibiting CE ≥ ε and (A) exhibiting CE < ε. Falsifier
= F1.

### E3 — Causal Patch as Commitment Predictor (synthetic + language)

Take the paraphrase-weakness / semantic setup and extend: for every claimed
"aligned" component, run a causal patch. Regress OOD lift onto (a) readout
AUC, (b) patch-CE. Prediction (new frame): only (b) predicts. Falsifier: AUC
regression coefficient exceeds patch-CE coefficient.

### E4 — Pythia LoRA v2 Commitment-Pinned External Contact (Modal L4)

Non-degenerate P1 repair with four arms — the definitive external test.

Task: modular addition `(a + b) mod n`, n ∈ {13, 17, 23}, strict-subset
splits at train_frac ∈ {0.5, 0.75}. External model family: Pythia
{70m, 160m, 410m}, LoRA rank 8.

Arms:
- **A (readout):** standard LoRA-LM training; post-hoc weakness selector.
- **B (compatibility-augmented):** LoRA-LM training + augmentation with
  cyclic-group orbit transforms of the training pairs
  `(a', b') = ((a+k) mod n, (b+k) mod n)` at controlled proportion.
- **C (wrong-group):** LoRA-LM training + augmentation with random
  non-cyclic permutations (control).
- **D (loss):** LoRA-LM training only, no augmentation, no selector — the
  ID baseline.

Metrics per cell:
1. OOD accuracy on held-out complement.
2. Patch-CE: cross-entropy shift when the LoRA update on identified
   cyclic-orbit-consistent components is zeroed at eval.
3. Wrong-group control CE (must not shift).
4. Weakness / compatibility scores of the learned function table (readout).
5. Classical baselines (train loss, sharpness proxy, param L2).

Kill (new-frame wins): B mean OOD ≥ 0.5 with patch-CE ≥ ε AND A OOD ≤ 0.10.
Kill (old-frame wins): A OOD ≥ 0.5 with weakness selector rho ≥ +0.5.
Draw: cluster analysis to identify boundary conditions.

Scale: 3 sizes × 3 moduli × 2 train_fracs × 4 arms × 3 seeds = 216 cells.
Modal L4 parallel workers, shard by (size, arm). Uses existing pattern in
`experiments/external_contact/modal_p1_pythia_lora.py`.

## Paper structure (NeurIPS / ICML format)

Length: not page-capped; ~14–18 pages main + appendix.

Sections:
1. **Abstract.** (~200 words) The commitment surface reframe; four severe
   tests; results; boundary condition on old-frame positives.
2. **Introduction.** Problem: probe-heavy interpretability confuses
   *availability* with *use*. Contribution list; theoretical claim; results
   headline; road-map.
3. **Related work.** Structured mechanistic interpretability (patchscopes,
   activation patching, IOI), calibrated active learning (BALD),
   epistemic uncertainty, causal representation learning,
   sense-of-agency + control theory, active inference, empowerment,
   grid-cell geometry (Webb–Miolane etc.), Bennett weakest hypothesis,
   simplicity vs invariance-based generalization. External citations from
   `references/program_literature.md` and the exhaustive literature audit.
4. **Theory: The commitment surface.** Formalize:
   - Definition 1 (commitment surface): a triple `(G_dep, C, T)` — a
     deployment generator, a concern weighting, and a transport (change of
     commitment).
   - Definition 2 (load-bearing): `f` is load-bearing at `(G_dep, C, T)` iff
     `CE(f | patch, C) ≥ ε` AND `CE(f | T · patch, C) ≥ ε` (survives
     transport).
   - Proposition 1 (readout ≠ use): probe AUC ⊥ CE without a commitment
     term.
   - Proposition 2 (weakness as diagnostic): when `G_probe ≡ G_dep`,
     weakness is Bayes-optimal among selectors; when they diverge,
     weakness reduces to a footprint.
   - Corollary (concern-weighted): unweighted extension mass is optimal iff
     `C` is uniform; misspecified `C` reduces the concern-weighted selector
     to unweighted.
5. **Method.** E1/E2/E3/E4 designs, pre-registered gates, controls.
6. **Results.** Tables + figures per experiment; boundary-condition
   analysis.
7. **Discussion.**
   - What the old-frame positives become (aligned-generator limiting case).
   - Reconciling the P1 hard kill with the cyclic/dihedral 100% wins.
   - Anti-Goodhart control loop as compression of the Correction Chain.
   - Limitations: reliance on modular-addition external contact; interior
     of concept-geometry in language remains open; Suite C still
     bandit-shaped.
8. **Conclusion.** Commitment-first as the discipline that makes
   representation science externally survivable.
9. **Appendix.**
   - Full derivations.
   - Per-cell tables for E1–E4.
   - Pre-registration verbatim.
   - External citation apparatus.
   - Reviewer-response section (pre-empt reviewer 2).

## Timeline

- Day 0 (now): plan, code E1/E2/E3, launch E4 on Modal L4.
- Day 0.5: E1/E2/E3 results committed; paper skeleton committed; first PR.
- Day 1: E4 first partial cells; figures generated for E1/E2/E3; theory
  section drafted.
- Day 1.5: E4 complete; unified results section; PDF built; second PR.
- Day 2: verification pass, external citation completeness pass, PR merged.

## Loop-exit criterion

The loop exits (paper is "groundbreaking-shaped") when *all* of:
- ≥ 3 of E1/E2/E3/E4 report a decisive verdict at pre-registered gates.
- The paper's headline claim is not retracted by any survivor experiment.
- External citations engage ≥ 8 outside-lab works with disagreement or
  synthesis, not just name-drops.
- The reviewer-response appendix has an answer to each of the
  paper-reviews.d/*.md critical review threads that touched this cluster.
