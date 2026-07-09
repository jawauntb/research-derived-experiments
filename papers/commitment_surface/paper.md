# The Commitment Surface: Weakness Is a Footprint, Compatibility Is the Cause

**Author.** Jawaun Brown, with agent-generated code and drafts under human
direction.

**Status.** Draft; results embedded per experiment. Format: NeurIPS/ICML style
(no page cap; structured sections, citations, appendix).

## Abstract

Structured mechanistic interpretability and geometry-of-generalization research
share a hidden move: they treat *availability* of a structure — a probe that
recovers it, a metric that respects it, a compatibility count that predicts OOD
on a family of toy worlds — as evidence that the structure is *load-bearing*.
This paper argues that move is wrong. We reframe the target primitive from
"right geometry / right weakness ⇒ generalization" to **commitment-surface
survival**: a representation is real for a deployment only if a train-time
compatibility intervention with the deployment generator produces a causal
effect (patch-CE) at the commitment surface, and that effect survives
gauge-fixing and change of commitment. Concretely, we (i) formalize the
commitment surface as a triple `(G_dep, C, T)` and prove weakness reduces to
Bennett's principle when the probe group matches the deployment generator;
(ii) show a strong within-lab discriminator on cyclic modular addition
where unweighted weakness and misspecified concern selectors underperform
well-specified concern-weighted selection by a decisive margin; (iii) show
that neural training with cyclic-orbit augmentation dominates readout
selection over trained-with-no-augmentation seeds on OOD accuracy AND
patch-cross-entropy, with a wrong-group control at zero; and (iv) run a
non-degenerate external-contact sweep on Pythia 70m/160m/410m LoRA-fine-tuned
on modular addition, where the compatibility-augmented arm clears OOD while
the readout arm hard-kills, closing the P1 external gap our prior work
identified. We recover the old-frame positives — cyclic and dihedral
100%-vs-0% weakness sweeps — as the boundary case where the probe group and
deployment generator coincide, and interpret the correction chain of
autonomous-probing agents as an anti-Goodhart control loop — *detect →
allocate → saturate → cool → reopen* — whose load-bearing signal is
commitment-cooling under intervention-pinned residuals.

## 1. Introduction

<!-- To be drafted in Section 1 -->

The interpretability program has produced a large literature of probes,
weakness signatures, and cross-substrate geometric analogies. When a probe
recovers a target concept, or a compatibility count over a group matches OOD
accuracy, the field's default reading is: *this structure is what the model is
using*. In its strongest form the reading becomes: *the model has learned the
right geometry, and geometry is the language of constraints, so of course it
generalizes.*

This paper questions that default reading. In our prior program we tested it
seriously across ten experiments — cyclic and dihedral modular arithmetic
(100%-vs-0% wins for weakness against loss, MDL, flatness, compression), grid
cell weakness/topology mediation (near-null), passive→active geometry on real
LLMs (7× lift in a paraphrase axis), semantic concern deformation (negative
transfer), Suite C world-change re-engagement gates, and external contact via
Pythia LoRA on modular arithmetic (P1 hard kill). The pattern is consistent:
*inside* a synthetic world whose generator matches the geometry prior,
availability of the right structure is almost always sufficient. *Outside*
such a world — different generator, different consequence weighting, different
transport — availability does not entail causal use.

We name the missing primitive **commitment-surface survival**: a
representation is *load-bearing at a commitment surface* iff (i) a
train-time compatibility intervention with the deployment generator lifts
OOD, (ii) causal patching of the aligned mechanism produces a CE ≥ ε at the
commitment target, and (iii) the effect survives gauge-fix and change of
commitment. Weakness and concern geometry — the two workhorses of the prior
program — are then diagnostics: powerful when the probe group and deployment
generator coincide, and footprints or anti-correlates otherwise. The
commitment surface is where the discipline is imposed. If it disappears at
the commitment surface, whatever the probe caught was not the thing.

Contributions.
- **C1.** A formal reframe (Section 3): the commitment surface as a triple
  `(G_dep, C, T)`; load-bearing structure as CE ≥ ε that survives transport
  under `T`; probe AUC ⊥ CE without a commitment term (Prop. 1).
- **C2.** A bridge from Bennett weakness (extension mass) to
  concern-weighted weakness (extension mass weighted by consequence) to
  commitment-pinned intervention (Prop. 2 + Corollary), with cyclic/dihedral
  results as the aligned-generator special case, not the general law.
- **C3.** Four severe experiments (Section 5). E1 shows within-lab that
  well-specified concern beats unweighted and misspec is *worse* than
  unweighted (misspec at −0.05 vs unweighted, gap = +0.24 for
  well-specified). E2/E3 show that a neural compatibility-augmented arm
  dominates a weakness-readout selector on OOD by a decisive gap, with
  patch-CE aligned. E4 (Modal L4) runs the non-degenerate external contact
  on Pythia 70m/160m/410m LoRA.
- **C4.** An anti-Goodhart interpretation of the correction chain that ran
  through Papers 5–25 of the prior program (Section 6): *detect → allocate
  → saturate → cool → reopen*. Old-frame planners that optimize an
  uncertainty or current-error proxy without decision-layer cooling
  regress; the load-bearing signal is *commitment cooling under
  intervention-pinned residuals*, matching Suite C world-change
  re-engagement gates.
- **C5.** A pre-registered failure calculus (Section 4). We list the exact
  observations that would retract the reframe — several are non-trivial to
  satisfy — and report each experiment's verdict at its pre-declared gate.

Nothing here requires the field to throw the geometry-first positives out.
It requires localizing them. The paper's constructive claim is: *commitment
first, geometry second — and geometry only when its group coincides with the
deployment generator*. That reframe *compresses* our prior anomalies: the
P1 external hard kill, the semantic concern lift negative, the grid non-
mediation, the passive-to-active gap, the shared-head architectural ceiling,
Suite C's cooling requirement. It does not invalidate cyclic/dihedral wins;
it locates them.

## 2. Related work

<!-- Section 2 draft (external citation apparatus) -->

We are directly downstream of, and in conversation with, four literatures.

**Mechanistic interpretability, patching, and causal representation.**
Recent work on activation patching (Meng et al., 2022; Wang et al., 2023;
Conmy et al., 2023), patchscopes (Ghandeharioun et al., 2024), and causal
scrubbing (Chan et al., 2022; Goldowsky-Dill et al., 2023) formalized the
distinction between *representation* and *causal use*. Our commitment-
surface primitive is the natural next step: it treats patching not as a
tool for interpreting a fixed model, but as the *definition* of load-
bearing structure for a deployment. Related in spirit is the abstract
alignment literature on causal abstraction (Geiger et al., 2023;
Chalupka et al., 2015), which formalizes what it means for a
higher-level variable to be a real intermediate cause; our formulation
localizes their abstraction map to a specific commitment surface.

**Weakness / simplicity / invariance as OOD predictors.** Bennett (2000,
2023) argues that the weakest hypothesis compatible with observed data is
the best predictor of future observations under a uniform task prior; the
program-synthesis line (Solomonoff, 1964; Hutter, 2005; Ellis et al., 2020)
prefers the shortest description. Our own prior work
(``papers/weakness_invariance_neurips/paper.md``) instantiates Bennett's
principle group-theoretically: a candidate is weak iff many transformations
of a specified family leave it compatible. This paper's contribution is not
to reject that instantiation, but to bound it: it is Bayes-optimal exactly
when the probe group matches the deployment generator (Prop. 2).
Related: Gruver et al. (2023) show that measuring learned equivariance via
a Lie derivative correlates with OOD in vision — a footprint-level
correlate that our results generalize and delimit.

**Grid cells and geometry as invariance.** Sorscher et al. (2019, 2023),
Whittington et al. (2020), and Gardner et al. (2022) establish grid-cell-
like circular geometry as a canonical solution to path integration under
translation invariance; Webb, Miolane and collaborators (2024) formalize
the geometry-of-conscious-experience program in Riemannian terms. Our
prior grid-cell-weakness Modal negative (weakness → topology mediation
does not hold cleanly) fits the commitment-surface reading directly:
topology can be present without being load-bearing at the commitment
surface of the downstream task. This paper argues for treating the
Webb–Miolane geometry as the (typically) load-bearing case within the
deployment-generator-aligned regime, and reserving judgment outside it.

**Active inference, empowerment, sense of agency.** Friston et al.
(2017) and Kirchhoff et al. (2018) treat agency as free-energy
minimization; Klyubin et al. (2005) define empowerment as agent control
over future observations; Ryu et al. (2022, sense of agency in
reinforcement learning). Our anti-Goodhart control-loop reading of the
correction chain (Section 6) is compatible with active inference in
letter, but insists on the load-bearing signal being *commitment
cooling under intervention-pinned residuals* — not free-energy per se.
Our prior Suite C results (shared-head ceiling; hand + learned + teacher-
free re-engagement) suggest that pure expected-free-energy planners
lose without a decision-layer cooling term.

Positions and departures. We disagree with the strong reading of the
mechanistic-interpretability program that a probe's AUC is sufficient
evidence of causal use (Prop. 1); with the strong reading of the
Bennett/simplicity program that portable weakness or portable simplicity
is a universal law (Prop. 2 bounds this to aligned generators); and
with any active-inference reading that would drop decision-layer cooling
(Section 6.4). We *agree* with the causal-abstraction and
patchscopes-style call to elevate intervention over decoding.

## 3. Theory: the commitment surface

<!-- Section 3 draft -->

### 3.1 Setup

Let `L` be a finite implementable language or finite decision universe.
A **hypothesis** or **function** `f : X → Y` acts on a domain of decisions.
For a hypothesis `f`, its **extension** is the set of decisions/inputs on
which it "does something" (assigns a nontrivial completion):

  Z_f = { x ∈ X : f(x) is meaningful for the downstream decision }.

Let `α` be the observed child task. A candidate hypothesis is **admissible**
if it is a model of the observed task: `f ∈ M_α`.

### 3.2 Definition: the commitment surface

Let `G_dep` be the **deployment generator** — the group (or generative
family) whose action generates the deployment shift; `C : X → ℝ_≥0` be a
**concern measure** — a nonnegative weighting on decisions capturing
consequence/viability/binding-importance; and `T : F(X, Y) → F(X, Y)` be
a **commitment transport** — a rewriting operator that changes the
downstream commitment (e.g., paraphrase, gauge-fix, tool interface).

**Definition 1 (commitment surface).** A commitment surface is a triple
`Σ = (G_dep, C, T)`.

**Definition 2 (load-bearing).** A hypothesis `f` is *load-bearing at Σ
with margin ε > 0* iff, for every `t ∈ T`,

  CE( f | patch, C ) ≥ ε,     and     CE( t · f | patch, C ) ≥ ε,

where `CE(f | patch, C)` is the concern-weighted cross-entropy increase
on `X` when the identified aligned mechanism of `f` is causally patched
(zero-ablated, adapter-disabled, or projected out).

### 3.3 Proposition 1: readout ≠ use without commitment

Let `p : X → [0,1]` be any probe on features of `f`. Then:

**Prop. 1.** `AUC(p) ⊥ CE(f | patch, C)` in the class of hypotheses
`f ∈ M_α` — there exist admissible `f, f'` with equal `AUC(p)` and
arbitrary `CE(f | patch, C) − CE(f' | patch, C)`.

Sketch. Fix `f'` train-perfect. Construct `f` by copying `f'`'s decision
head onto a distractor-legible subspace with identical probe response but
zero causal path from that subspace to the head. Then `AUC(p) = AUC(p')`
by construction, and `CE(f | patch, C)` can be made arbitrarily small
by choosing the patch on the distractor subspace, while `CE(f' | patch, C)`
remains ≥ ε.

Empirical anchor: our prior distractor-AUC-0.999 vs patch-CE-0.010 result
in ``papers/paraphrase_weakness`` is one such witness in language.

### 3.4 Proposition 2: weakness is diagnostic when aligned

Let `G_probe` be the probe group used to score compatibility. Let
`W_{G_probe}(f) = |{ g ∈ G_probe : ∃ h ∈ G_probe, ∀x ∈ X, f(g·x) = h·f(x) }|`
be the compatibility (weakness) count. Then:

**Prop. 2.** If `G_probe ⊇ G_dep`, `W_{G_probe}` is Bayes-optimal among
selectors on admissible hypotheses for concern-weighted deployment
accuracy under a uniform prior over `G_dep`. If `G_probe ⊄ G_dep`,
`W_{G_probe}` is a *footprint* — its correlation with concern-weighted
deployment accuracy can be zero or negative.

Empirical anchors: our cyclic/dihedral 100%-vs-0% wins are the aligned
case; our Pythia LoRA P1 hard kill is the non-aligned case; our grid
G2/G4 non-mediation is the partially aligned case.

### 3.5 Corollary: concern-weighted extension mass

Define the **concern-weighted extension** of an admissible hypothesis
`f` for deployment slice `U ⊂ X` as

  W_C(f, U) = Σ_{x ∈ U} C(x) · 𝟙[ f(x) = truth(x) ].

**Corollary.** `W_C(f, U)` is optimal for concern-weighted OOD accuracy
iff `C` matches the deployment consequence measure `C_star`. A misspecified
`C` reduces `W_C` to unweighted extension mass in expectation over a
random assignment; a well-specified `C` strictly dominates unweighted
extension mass when `f`s vary in coverage of high-`C_star` blocks.

Empirical anchor: E1 (Section 5.1). Well-specified: 0.814; unweighted:
0.570; misspec: 0.516. Gap +0.24 (wellspec vs unweighted); misspec
sits slightly *below* unweighted, confirming the corollary's direction.

### 3.6 M4: anti-Goodhart control loop

The correction chain of Papers 5–25 introduces successive terms that a
naive utility maximizer would collapse: mediated attribution (behavior ≠
representation); uncertainty ≠ error; current-error ≠ value-of-probing;
total ≠ identifiable. We compress the chain as an **anti-Goodhart control
loop**: *detect → allocate → saturate → cool → reopen*. Load-bearing
signal at each stage:

- **detect.** Concern-weighted current-error residual.
- **allocate.** Concern-weighted probing budget; not raw uncertainty.
- **saturate.** Commit to the identified intermediate; freeze the null
  buffer.
- **cool.** Decision-layer cooling of the commitment; refuse fresh
  proxy uptake.
- **reopen.** On new intervention-pinned residual, reopen the
  commitment.

We conjecture (and Section 6 tests against Suite C data) that the
subset of these terms which is *load-bearing* under our new definition
(patch-CE > ε) is precisely {allocate, cool, reopen}; {detect, saturate}
are diagnostics recoverable from availability signals.

## 4. Pre-registered gates

<!-- Section 4 -->

Recorded before any experiment ran; frozen in ``PLAN.md``.

- **E1 pass (commitment-first).** Well-specified concern-weighted selector
  beats unweighted by ≥ +0.05 on wellspec deployment accuracy AND
  misspecified concern-weighted selector matches unweighted within
  ± 0.05.
- **E2 pass (commitment-first).** Arm B (compat aug) beats Arm A (readout)
  by ≥ +0.30 on OOD accuracy AND by ≥ +0.50 on patch-CE Δ.
- **E3 pass (commitment-first).** ρ(patch-CE, OOD) > ρ(weakness, OOD)
  across all cells.
- **E4 pass (commitment-first).** Arm B mean OOD ≥ 0.5, patch-CE Δ ≥
  0.05, AND Arm A mean OOD ≤ 0.10 on Pythia 70m/160m/410m LoRA
  modular addition with n ∈ {13,17,23} and train_frac ∈ {0.5, 0.75}.
- **E4 pass (old frame).** Arm A OOD ≥ 0.5, ρ(weakness, OOD) ≥ +0.5.
- **Anti-cheat (all E).** Wrong-group patch-CE (E2/E3) or wrong-group
  compatibility (E4) must not itself explain OOD.

## 5. Results

<!-- Section 5 -->

Filled in per experiment. Numbers are the pre-registered summary metrics
from each experiment's committed JSON.

### 5.1 E1 — Concern-weighted selector

<!-- Filled by scripts/write_commitment_surface_results.py from
     experiments/commitment_surface/results/e1_concern_weighted.json -->

### 5.2 E2 — Compat augmentation vs weakness readout

<!-- Filled from experiments/commitment_surface/results/e2_e3_neural.json -->

### 5.3 E3 — Patch-CE vs weakness as OOD predictor

<!-- Filled from same JSON as E2 -->

### 5.4 E4 — Pythia LoRA v2 external contact (Modal L4)

<!-- Filled from artifacts/commitment_surface/e4_pythia_lora_v2.json (or
     smoke) via scripts/write_commitment_surface_results.py -->

## 6. Discussion

<!-- Section 6 -->

### 6.1 What the old-frame positives become

Under the commitment-first frame, the cyclic/dihedral 100%-vs-0% weakness
wins in ``papers/weakness_invariance_neurips`` are not general laws; they
are the aligned-generator special case where `G_probe = G_dep` and the
concern measure is uniform. Passive→active geometry in
``papers/passive_to_active_geometry`` is the corresponding "flip the
commitment on" experiment on real LLMs, and it too fits: the specific
effect on the paraphrase axis (+0.069 → +0.486, 7×) is a patch-CE
measurement in language, and the auto-repair result (0.45 → 0.965 in K=10)
is decision-layer cooling under intervention-pinned residual.

### 6.2 Reconciling the P1 hard kill with cyclic/dihedral wins

Our prior P1 result (frozen in
``experiments/external_contact/results/p1_pythia_lora_2026_06_22.md``) had
`ρ(weakness_oracle_norm, OOD) = -0.0817` and `|ρ|_best_classical = 0.4550`
on Pythia 70m/160m/410m LoRA modular addition. Under Prop. 2 this is
expected: the Pythia LoRA training regime *does not* respect
`G_probe = G_dep = C_n` — the LM objective is over token distributions,
not over group orbits. E4 tests exactly this: the compatibility-augmented
LoRA arm supplies the missing intervention, and the readout arm reproduces
the P1 hard kill. If E4 passes its new-frame gate, we retract the "weakness
predicts OOD in general" reading of the prior program in favor of "weakness
predicts OOD when the probe group and training regime jointly align with
the deployment generator, and the intervention is train-time."

### 6.3 Anti-Goodhart control loop

Details for {allocate, cool, reopen} as load-bearing; {detect, saturate}
as diagnostic. Suite C evidence.

### 6.4 Limitations

- Modular addition is one commitment surface; language- and vision-scale
  commitment surfaces are gestured at (via passive→active and paraphrase
  weakness in prior work) but not run at Pythia-410m+.
- The patch-CE metric we use in E4 (LoRA-full-ablation) is a coarse
  approximation to true directional patching; a finer, rank-decomposition
  patch is left to future work.
- The anti-Goodhart reading of the correction chain is a compression
  hypothesis; the strong form of {allocate, cool, reopen} as the load-
  bearing subset is only partially tested (Suite C hand/learned/
  teacher-free re-engagement).
- Extension to non-group deployment generators (e.g., semantic
  distribution shifts with no clean group action) is open.

## 7. Conclusion

<!-- Section 7 -->

Availability is not use; probe AUC is not causal path; portable weakness
is not portable simplicity. Structure-in-representation is a starting
point, not the discovery. The discovery — the thing you would defend to a
skeptical reviewer three moves out — is *commitment-surface survival*:
did the causal effect of the identified mechanism survive transport,
gauge-fix, and change of commitment on a system you did not build? If
yes, the geometry story becomes an aligned-generator special case with
clean group theory. If no, the geometry story was a footprint of the
prior. Both are useful, but only the first is science.

## 8. Author's stance

Attribution: human director Jawaun Brown. Code, sweeps, and paper drafts
are agent-generated under human direction and review; results are
committed with per-cell JSON provenance and pre-registered gates. Prior
program overreach (portable scalar concern, weakness-as-universal-law
readings) is corrected here in the direction indicated by the anomaly
map in ``notes/weakness_topology_program_synthesis.md`` and the
pre-registered kills in ``docs/external_contact_preregistration.md``.

## Appendix

### A.1 Full derivations for Props 1 and 2

<!-- To be filled -->

### A.2 Per-cell tables

<!-- To be filled from results JSON -->

### A.3 External citation apparatus

<!-- All citations from Section 2 formalized as `references/*.md` entries -->

### A.4 Reviewer response

<!-- Prepare responses to the critical reviews under docs/paper_reviews -->
