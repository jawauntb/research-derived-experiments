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
commitment surface as a triple `(G_dep, C, T)` and show, under an explicit
prior and orbit-likelihood, that weakness is the optimal selector exactly
when the probe group matches the deployment generator, and only a footprint
otherwise (Prop. 2); (ii) show a strong within-lab discriminator on cyclic
modular addition where unweighted weakness and misspecified concern
selectors underperform well-specified concern-weighted selection by a
decisive margin; (iii) show that neural training with cyclic-orbit
augmentation dominates readout selection over trained-with-no-augmentation
seeds on OOD accuracy AND patch-cross-entropy, with a wrong-group-augmented
control at 0.167 OOD (collapse) and near-zero patch-CE Δ; and (iv) run a
non-degenerate external-contact sweep on Pythia 70m/160m/410m LoRA-fine-tuned
on modular addition, where the compatibility-augmented arm reaches 0.882
mean OOD while the readout arm sits at 0.113 mean OOD, substantially
narrowing the P1 external gap our prior work identified; ρ(patch-CE, OOD)
= 0.853 vs ρ(weakness, OOD) = 0.290 across 108 cells, consistent with
Prop. 1 (probe readout does not identify causal use) in the non-aligned
regime. Two pre-registered gates strictly failed and we report them as
failures: the E1 misspecification-equivalence band (−0.054 vs ±0.05) and
the E4 Arm-A ceiling (0.113 vs ≤ 0.10); E4 is directionally decisive but
its strict gate did not pass. One confound remains open and is
pre-registered for a follow-up: cyclic-orbit augmentation places correctly
labeled examples on held-out deployment support, so E4 does not yet
separate *generator learning* from *labeled orbit coverage* (Section 6.5).
We recover the old-frame positives — cyclic and dihedral
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
  under `T`; probe AUC does not identify or lower-bound CE — a
  non-identification theorem (Prop. 1).
- **C2.** A bridge from Bennett weakness (extension mass) to
  concern-weighted weakness (extension mass weighted by consequence) to
  commitment-pinned intervention (Prop. 2 + Corollary), with cyclic/dihedral
  results as the aligned-generator special case, not the general law. The
  optimality statement requires `G_probe = G_dep` (or weakness restricted
  to `G_dep`); a strict superset probe group does *not* suffice
  (Section 3.4).
- **C3.** Four severe experiments (Section 5). E1 shows within-lab that
  well-specified concern beats unweighted by +0.24; the misspecification
  arm lands at −0.054 vs unweighted, *outside* the pre-registered ±0.05
  equivalence band, so that sub-gate strictly fails (the direction —
  misspec is not helpful — still holds). E2/E3 show that a neural
  compatibility-augmented arm dominates a weakness-readout selector on
  OOD by a decisive gap, with patch-CE aligned. E4 (Modal L4) runs the
  non-degenerate external contact on Pythia 70m/160m/410m LoRA:
  directionally decisive, strict pre-registered gate narrowly failed
  (Arm A mean OOD 0.113 vs the required ≤ 0.10).
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
to reject that instantiation, but to bound it: under an explicit prior
and orbit-likelihood it is Bayes-optimal exactly when the probe group
equals the deployment generator, or weakness is restricted to it — a
strict superset probe group does not suffice (Prop. 2).
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
family) whose action generates the deployment shift; `C : X → R_≥0` be a
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

### 3.3 Proposition 1: probe AUC does not identify causal use

Let `p : X → [0,1]` be any probe on features of `f`. Then:

**Prop. 1 (non-identification).** Probe AUC does not identify, and does
not lower-bound, causal effect: for every attainable AUC value `a` and
every target gap `δ ∈ [0, ε]`, there exist admissible `f, f' ∈ M_α`
with `AUC(p · f) = AUC(p · f') = a` and
`CE(f | patch, C) − CE(f' | patch, C) = δ`. Consequently no function of
probe AUC alone can decide whether a hypothesis is load-bearing at Σ.

We deliberately do *not* state this as probabilistic independence
(`AUC ⊥ CE`): independence would require a distribution over admissible
hypotheses, and no canonical one exists. The theorem is a
*non-identification* result — equal probe evidence is consistent with any
causal-effect gap in `[0, ε]` — which is the property the availability-⇒-use
inference actually needs and lacks. Empirically, an ensemble of trained
models can still exhibit correlation between AUC and CE (E3 measures
exactly this in the aligned regime); Prop. 1 says such correlation is a
property of the training distribution, not of the probe evidence.

Sketch. Fix `f'` train-perfect. Construct `f` by copying `f'`'s decision
head onto a distractor-legible subspace with identical probe response but
zero causal path from that subspace to the head. Then
`AUC(p · f) = AUC(p · f')` by construction, and `CE(f | patch, C)` can be
made arbitrarily small by choosing the patch on the distractor subspace,
while `CE(f' | patch, C)` remains ≥ ε. Full construction in Appendix A.1.

Empirical anchor: our prior distractor-AUC-0.999 vs patch-CE-0.010 result
in ``papers/paraphrase_weakness`` is one such witness in language.

### 3.4 Proposition 2: weakness is diagnostic when aligned

Let `G_probe` be the probe group used to score compatibility. Say `f` is
*compatible with* `g` iff `∃ h ∈ G_probe, ∀x ∈ X, f(g·x) = h·f(x)`, and
let `W_G(f) = |{ g ∈ G : f is compatible with g }|` be the compatibility
(weakness) count over any group `G`. Fix the deployment model that makes
"Bayes-optimal" meaningful: a deployment slice is generated by drawing
`g ~ Uniform(G_dep)` and evaluating `f` on the `g`-translated support;
`f` scores 1 on that slice iff `f` is compatible with `g` (the
orbit-likelihood), and concern is uniform.

**Prop. 2 (alignment condition).** Under this prior and likelihood:

- **(i) Aligned case.** If `G_probe = G_dep` — or, more generally, if
  weakness is computed *restricted to* `G_dep`, i.e. the selector uses
  `W_{G_dep}` — then `argmax W_{G_dep}` maximizes expected deployment
  accuracy over admissible hypotheses, hence is Bayes-optimal among
  selectors that depend only on `f`.
- **(ii) Superset caveat.** `G_probe ⊃ G_dep` does *not* suffice: a
  candidate can be compatible with many elements of
  `G_probe \ G_dep` while compatible with few elements of `G_dep`, so
  `W_{G_probe}` can rank candidates in the opposite order of
  `W_{G_dep}` (explicit counterexample in Appendix A.1). Optimality is
  recovered from a superset probe group only under an
  *ordering-preservation assumption*: for the candidate set under
  comparison, `W_{G_probe}(f) > W_{G_probe}(f') ⇒ W_{G_dep}(f) ≥
  W_{G_dep}(f')`.
- **(iii) Non-aligned case.** If `G_dep ⊄ G_probe` (the probe group does not contain the deployment generator), `W_{G_probe}` is a
  *footprint* — its correlation with concern-weighted deployment accuracy
  over a candidate set can be zero or negative.

Empirical anchors: our cyclic/dihedral 100%-vs-0% wins instantiate (i)
(`G_probe = G_dep = C_n`); our Pythia LoRA P1 hard kill is the
non-aligned case (iii); our grid G2/G4 non-mediation is the partially
aligned case where the ordering-preservation assumption of (ii) fails.

### 3.5 Corollary: concern-weighted extension mass

Define the **concern-weighted extension** of an admissible hypothesis
`f` for deployment slice `U ⊂ X` as

  W_C(f, U) = Σ_{x ∈ U} C(x) · 1[ f(x) = truth(x) ].

**Corollary (order-equivalence).** Let `C_star` be the deployment
consequence measure. `C = C_star` up to positive scaling is *sufficient*
for the selector `argmax_f W_C(f, U)` to pick a `C_star`-optimal
candidate, but it is not *necessary*: over a finite candidate set
`F ⊂ M_α`, the selector is `C_star`-optimal iff `C` is
**order-equivalent to `C_star` on `F`** — i.e.
`W_C(f, U) > W_C(f', U) ⇔ W_{C_star}(f, U) > W_{C_star}(f', U)` for all
`f, f' ∈ F`. Distinct weightings can induce the same ranking and are
then equally optimal. A misspecified `C` drawn as a random assignment
with the same marginal reduces `W_C` to unweighted extension mass *in
expectation*; a well-specified `C` strictly dominates unweighted
extension mass when candidates vary in coverage of high-`C_star` blocks.

Empirical anchor: E1 (Section 5.1). Well-specified: 0.814; unweighted:
0.570; misspec: 0.516. Gap +0.24 (wellspec vs unweighted). The misspec
arm sits 0.054 *below* unweighted — directionally consistent with the
corollary (random weighting is not helpful), but note this is outside
the pre-registered ±0.05 equivalence band, so the strict E1 misspec
sub-gate fails (Section 5.1); the in-expectation reduction predicts
equality, and the realized misspec draw was mildly adversarial rather
than neutral.

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
the P1 hard kill. The result at 108 cells (Section 5.4) is
**directionally decisive, but the strict pre-registered gate failed**:
Arm B mean OOD 0.882 vs Arm A mean OOD 0.113, Arm B mean
patch-CE Δ +4.86 vs Arm A −0.74, and the anti-cheat Arm C sits at
0.071 OOD despite the same augmentation volume as B. Weakness ρ drops
to 0.29 across cells; patch-CE ρ holds at 0.85. The pre-registered
"A mean OOD ≤ 0.10" condition came in at 0.113 — a fail by the exact
standard this paper advocates, and we record E4 as a gate failure, not
a pass. The miss is attributable to 2 of the 27 Arm A cells that
stumbled into the true cyclic rule without augmentation (the
410m/n=17/seed=709 cell reaches OOD 1.000 and weakness 1.000, textbook
aligned-regime recovery); twenty-two of twenty-seven Arm A cells sit at
OOD ≤ 0.15 while **all twenty-seven Arm B cells** clear OOD ≥ 0.5.
That diagnosis is a post-hoc account of a pre-registered miss — it
explains the failure, it does not convert it into a pass. What the two
Arm A outliers do show is that Arm A can occasionally recover when a
training run happens to land in the aligned regime, and when it does,
weakness and patch-CE agree on the load-bearing signal at cell scale.
We retract the "weakness predicts OOD in general" reading of the prior
program in favor of "weakness predicts OOD when the probe group and
training regime jointly align with the deployment generator, and the
intervention is train-time."

### 6.3 Anti-Goodhart control loop as compression of the Correction Chain

Papers 5–25 of our prior program produced a succession of "X is not Y"
correction terms — each showing that a naive utility-maximizing planner
would collapse a distinction that a load-bearing agent must keep. The
sequence: behavior ≠ representation; uncertainty ≠ error; current-error
≠ value-of-probing; probing ≠ commitment; commitment ≠ identifiability;
total-effect ≠ identifiable-effect. Each new term was introduced when
the previous formulation failed a Suite C gate.

Under the commitment-surface reading, the Correction Chain compresses
into an **anti-Goodhart control loop**:

  detect → allocate → saturate → cool → reopen

with three of the five stages carrying the causal load:

- **allocate** — the probing budget is concern-weighted. Uncertainty-only
  planners (`uncertainty_only` in the Phase-2 gate table) over-probe
  low-concern ambiguity and fail the world-change gate; the concern-
  gated selector is the only one that passes at 1.000/5 seeds. This is
  the E1 corollary at the agent scale.
- **cool** — the decision layer refuses fresh proxy uptake once a
  commitment is made; without this, the shared-head planner collapses
  role attribution under regime shift (P23B G8 partial pass). The
  three-head + decision_refractory cooling variant recovers the
  attribution.
- **reopen** — an *intervention-pinned* residual, not any surprise
  spike, reopens the commitment. The scale-normalized current-replay
  ablation and the two-regime shift stress-test show that surprise
  alone triggers anxiety, not stable re-engagement — VoI ≠
  current-error is the load-bearing distinction.

**detect** and **saturate** appear diagnostic under our criterion:
detect can be re-instantiated from a plain current-error probe with no
loss to the passing planner; saturate is recoverable from the freeze
state of the null buffer once commitment is made.

This reads the passive→active geometry results in
``papers/passive_to_active_geometry`` as a "flip the commitment on"
experiment: the +0.069 → +0.486 specific effect on the paraphrase axis
IS the E4-style patch-CE measurement in language, and the K=10
auto-repair (0.45 → 0.965) IS decision-layer cooling under
intervention-pinned residual — the same loop, one deployment surface
higher.

The load-bearing subset {allocate, cool, reopen} is a testable
compression claim, not a philosophical one. Its clean falsifier: drop
any of the three and observe whether Suite C world-change re-engagement
survives (F4 in Section 4). The prior negative on `uncertainty_only`
and the P23B G8 partial pass are our best current evidence in favor of
the compression; a factorial ablation would upgrade it.

### 6.4 Limitations

- Modular addition is one commitment surface; language- and vision-scale
  commitment surfaces are gestured at (via passive→active and paraphrase
  weakness in prior work) but not run at Pythia-410m+.
- The patch-CE metric reported for E4 (LoRA-full-ablation) is a coarse
  approximation to true directional patching. The pending E5 harness adds
  per-matrix spectral-mass-normalized low-rank patching. Its one-seed smoke
  validates execution and integrity only, so it does not retroactively
  strengthen E4.
- The E2 patch-CE evidence for *localization* is weaker than the
  headline B − A gap suggests. Arm B's absolute patch-CE Δ is small
  (+0.024; Arm C +0.003; B − C only +0.021), and the large B − A gap
  (+0.758) is mostly produced by Arm A's *negative* patch score
  (−0.734: ablating "compatibility-aligned" units in a memorizing
  model *reduces* OOD CE). The E2 patch result therefore supports
  "B's mechanism differs from A's" strongly, but supports "B localizes
  a substantial mechanism in the top-k units" only weakly. The
  large-width sweep sharpens this concern rather than resolving it.
- The E2/E3 top-k-unit patch-CE metric loses absolute-magnitude
  discriminating power at larger widths: a robustness sweep at
  `n ∈ {17, 19, 23}`, hidden width 128, top_k 16
  (`results/e2_e3_neural_larger_n.md`) shows Arm B mean OOD 1.000 vs
  Arm A 0.089 (gap +0.911) — the OOD story holds decisively — but
  patch-CE Δ for B drops to +0.04 because the trained model spreads
  the load-bearing structure across more redundant units, so a fixed
  top-k ablation catches a smaller fraction of the mechanism. A
  fixed-width top-k patch loses power as width grows; until a
  rank-normalized or subspace-decomposition patch is run, the E2/E3
  localization claim should be read as preliminary. Fix left to
  future work: normalize patch-CE by hidden-width fraction, or
  rank-decompose the affected subspace.
- The anti-Goodhart reading of the correction chain is a compression
  hypothesis; the strong form of {allocate, cool, reopen} as the load-
  bearing subset is only partially tested (Suite C hand/learned/
  teacher-free re-engagement).
- Extension to non-group deployment generators (e.g., semantic
  distribution shifts with no clean group action) is open.
- The highest-priority methodological issue is the label-exposure
  confound of Section 6.5: cyclic-orbit augmentation places correctly
  labeled examples on the held-out deployment support, so E2/E4 do not
  yet separate *generator learning* from *labeled orbit coverage*.

### 6.5 Open confound: labeled orbit coverage vs generator learning

E4's compatibility augmentation generates, for each train pair
`(x, y = (x + offset) mod n)`, the pair `((x+k) mod n, (y+k) mod n)`
for random `k`. Because `(y+k) = ((x+k) + offset) mod n`, every
augmented pair is a *correctly labeled* example at input `(x+k) mod n`
— including inputs in the held-out deployment complement. The same
holds for E2's `((a+k) mod n, b) ↦ (a+b+k) mod n` augmentation. In
other words, the intervention arms were trained with direct labeled
exposure to the OOD support. The wrong-group Arm C matches augmentation
*volume* but places *incorrect* labels on held-out inputs
(`π(truth(x))` at input `π(x)` is generally not `truth(π(x))`), so the
B-vs-C contrast rules out generic augmentation volume — it does **not**
rule out target-support label exposure as the operative mechanism.
An earlier revision of Arm C that used correctly-labeled coverage
augmentation *did* produce OOD generalization (Appendix A.4, R2),
which keeps the coverage explanation live rather than hypothetical.

E4 is therefore consistent with two readings:

1. **Commitment-first (ours).** The model learns a transportable
   generator (cyclic equivariance) and uses it at commitment; the
   augmentation is how the generator is installed.
2. **Coverage (deflationary).** Aligned augmentation simply exposes the
   OOD orbit with correct labels; nothing transportable is learned
   beyond fitting the exposed points.

The timestamped, explicitly post-hoc E5 addendum to `PLAN.md` (frozen
2026-07-09 21:36 EDT, before any E5 result) preregisters the severe follow-up.
Train **without ever presenting labels from the held-out deployment orbit**,
and compare five arms:

1. aligned generator regularization using only train-support pairs
   (e.g., an equivariance-consistency loss `f((x+k) mod n)` vs
   `(f(x)+k) mod n` evaluated only where both points are in the train
   support, or where the target is the model's own prediction rather
   than a ground-truth label);
2. aligned augmentation that is allowed to enter held-out support
   (the current Arm B, as the coverage-exposed reference);
3. wrong-generator regularization (matched form of (1), wrong group);
4. ordinary coverage-matched augmentation (correct labels, no group
   structure, matched count of held-out-support exposures);
5. readout selection (current Arm A).

Evaluate on **new group elements not used by the intervention**, repeat the
commitment under task-preserving prompt paraphrases, and use
spectral-mass-normalized LoRA causal patching. The harness records support
exposure counts and invalidates any G-reg/W-reg cell that receives a held-out
truth label.

**Kill criteria (pre-registered).** The commitment-first interpretation
is materially weakened if any of:

- arm (1)'s gains disappear when augmentation cannot label
  deployment-support points (i.e., (1) ≈ (5) while (2) >> (5));
- coverage-matched augmentation (4) performs on par with aligned
  augmentation (2);
- patch-CE fails to predict transfer to a novel commitment surface.

Until this follow-up runs, the E4 claim should be read as: *train-time
aligned intervention recovers external OOD where readout selection does
not* — with the mechanism (transportable generator vs labeled coverage)
not yet isolated. **E5 status at this revision: the Pythia-70m/n=13/one-seed
20-epoch validation smoke passed its integrity gate.** G-reg recorded zero
held-out truth-label exposures, B-ref/Cov's precomputed ledgers matched at 27
held-out events over six unique inputs, novel shifts were disjoint, and the
50% spectral-mass patch tolerance passed. Descriptively, G-reg/Cov/A-ref
canonical OOD accuracies were 0.000/0.286/0.000; this undertrained one-seed
smoke omits B-ref and W-reg and is explicitly not confirmatory evidence.
The generator-vs-coverage mechanism therefore remains pending, and E4's claim
boundary is unchanged.

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

**Prop. 1 (non-identification of causal use by probe AUC).** Let `M_α`
be the set of admissible hypotheses. Fix a probe `p : X → [0,1]` and any
admissible baseline `f'` with a known load-bearing mechanism `M(f')`
such that `CE(f' | patch, C) ≥ ε` when the patch zeroes `M(f')`. We
construct `f` as follows: (i) duplicate `f'`'s decision head onto a
fresh subspace `S` orthogonal to `M(f')` in feature space; (ii) copy
`f'`'s decisions bit-for-bit onto `M(f') ⊕ S`; (iii) route the probe
input through `S` while keeping the downstream computation routed
through `M(f')`. By construction:

  Property (a). `AUC(p · f) = AUC(p · f')` on any input distribution,
  because `p` reads `S` and `S` was constructed to match `f'`'s probe
  response.
  Property (b). Zero-ablating `S` changes `p · f` but not the decision
  head's output, so `CE(f | patch(S), C) = 0`.
  Property (c). Zero-ablating `M(f')` changes both the decision output
  and the probe response, so `CE(f | patch(M(f')), C) = CE(f' | patch,
  C) ≥ ε`.

This exhibits two admissible hypotheses with identical probe AUC and
causal-effect gap `ε` under the respective identified-mechanism patches.
To realize an arbitrary intermediate gap `δ ∈ [0, ε]`, interpolate the
*routing*, not the functions: construct `f_λ` that routes a fraction
`λ` of the decision head's input mass through `M(f')` and `1 − λ`
through the (causally inert, probe-visible) copy on `S`, with the head
re-normalized so the input–output behavior — hence admissibility and
probe response — is unchanged. `AUC(p · f_λ)` is constant in `λ` while
`CE(f_λ | patch(S), C)` moves continuously from `0` (at `λ = 1`) toward
`ε` (at `λ = 0`), so every gap `δ ∈ [0, ε]` is attained at equal AUC.

Hence no function of probe AUC alone identifies, or lower-bounds,
`CE(· | patch, C)` on `M_α`. We emphasize the scope: this is a
*non-identification* theorem over the admissible class. It does **not**
assert probabilistic independence of AUC and CE — that would require a
distribution over `M_α`, and under particular training distributions
the two can correlate (E3 measures such a correlation in the aligned
regime). What fails is the inference from probe evidence to causal use
for any *individual* hypothesis. ∎

**Prop. 2 (weakness is diagnostic exactly when aligned).**
*Deployment model.* Both groups finite. A deployment slice is generated
by drawing `g ~ Uniform(G_dep)` (the prior) and evaluating the
candidate on the `g`-translated support; the candidate scores 1 on the
slice iff it is compatible with `g` (the orbit-likelihood), and concern
is uniform. Under this model the expected deployment accuracy of an
admissible `f` is

  E_g[acc(f)] = W_{G_dep}(f) / |G_dep|,

i.e. expected accuracy is *exactly* normalized deployment-restricted
weakness.

*(i) Aligned case.* If the selector scores candidates by `W_{G_dep}` —
either because `G_probe = G_dep`, or because weakness is explicitly
restricted (or concern-weighted) to `G_dep` — then
`argmax_f W_{G_dep}(f)` maximizes `E_g[acc(f)]` by the identity above.
Since the score is a deterministic function of `f` and the objective is
its own posterior expectation under the stated prior and likelihood,
the argmax selector is Bayes-optimal among selectors that depend only
on `f`. (Bayes-optimality here is *relative to this explicit prior and
likelihood*; no claim is made under other priors.)

*(ii) Superset counterexample.* `G_probe ⊃ G_dep` does not suffice.
Let `G_dep = {e, g}` and `G_probe = {e, g, h1, h2, h3}`. Take `f`
compatible with `{e, h1, h2, h3}` (so `W_{G_probe}(f) = 4`,
`W_{G_dep}(f) = 1`) and `f'` compatible with `{e, g}` (so
`W_{G_probe}(f') = 2`, `W_{G_dep}(f') = 2`). Then
`W_{G_probe}(f) > W_{G_probe}(f')` while
`E_g[acc(f)] = 1/2 < 1 = E_g[acc(f')]`: the superset-probe ranking is
inverted on deployment. Optimality from a superset probe group is
recovered only under an ordering-preservation assumption on the
candidate set: `W_{G_probe}(f) > W_{G_probe}(f') ⇒ W_{G_dep}(f) ≥
W_{G_dep}(f')`.

*(iii) Non-aligned case.* Suppose `G_dep ⊄ G_probe`. Let
`g' ∈ G_dep \ G_probe`. Then `W_{G_probe}(f)` does not measure
compatibility with `g'`. Construct `f, f'` admissible such that
`W_{G_probe}(f) > W_{G_probe}(f')` but `f'` is compatible with `g'`
and `f` is not; then `f'` has strictly higher expected deployment
accuracy on the `g'`-generated slice while `f` has higher
`W_{G_probe}` — a negative association between selector score and OOD
accuracy on that candidate pair. Hence `W_{G_probe}` is a footprint
whose sign of association with deployment accuracy is
generator-dependent. ∎

**Corollary (order-equivalence for concern-weighted extension mass).**
Let `C : U → R_≥0` be a concern measure on the deployment slice `U`,
`C_star` the true consequence measure, and `F ⊂ M_α` a finite candidate
set. *Sufficiency:* if `C = a·C_star` for some `a > 0`, then
`W_C = a·W_{C_star}` and `argmax_F W_C = argmax_F W_{C_star}`, so the
selector is `C_star`-optimal on `F`. *Exact condition:* the selector
`argmax_F W_C` picks a `C_star`-optimal candidate for every truth
assignment iff `C` is order-equivalent to `C_star` on `F`:

  `W_C(f, U) > W_C(f', U) ⇔ W_{C_star}(f, U) > W_{C_star}(f', U)`
  for all `f, f' ∈ F`.

Equality up to positive scale is *not necessary*: over a finite `F`,
distinct weightings that induce the same ranking of candidates are
equally optimal, so the earlier "iff `C = C_star` up to scaling"
phrasing was too strong and is retracted here in favor of the
order-equivalence condition. *Misspecification:* if `C` is a random
assignment with the same marginal distribution as `C_star`,
independent of candidate coverage, then
`E[W_C(f, U)] = E[C] · |{x ∈ U : f(x) = truth(x)}|` — proportional to
unweighted extension mass — so the misspecified selector reduces to
unweighted Bennett *in expectation* (any particular draw can be mildly
helpful or mildly adversarial; E1's realized draw was mildly
adversarial at −0.054). A strictly adversarial `C` (anti-correlated
with `C_star`) inverts the relation. ∎

### A.2 Per-cell tables

The PDF build renders complete per-cell tables directly from the committed
public-safe E1 and E2/E3 JSON summaries and the compact committed E4 appendix
artifact. The E2 and E3 analyses share one 216-cell population. E4 exports all
108 cells while intentionally omitting raw function tables, train/OOD input
lists, and parameter metadata; no requested appendix metric is unavailable.

<!-- APPENDIX_A2_TABLES -->

### A.3 External citation apparatus

**Mechanistic interpretability and causal intervention.**

- Meng, K., Bau, D., Andonian, A., Belinkov, Y. (2022). *Locating and
  Editing Factual Associations in GPT.* NeurIPS 2022.
- Wang, K., Variengien, A., Conmy, A., Shlegeris, B., Steinhardt, J.
  (2023). *Interpretability in the Wild: A Circuit for Indirect Object
  Identification in GPT-2 Small.* ICLR 2023.
- Conmy, A., Mavor-Parker, A., Lynch, A., Heimersheim, S., Garriga-
  Alonso, A. (2023). *Towards Automated Circuit Discovery for
  Mechanistic Interpretability.* NeurIPS 2023.
- Chan, L., Garriga-Alonso, A., Goldowsky-Dill, N., Greenblatt, R.,
  Nitishinskaya, J., Radhakrishnan, A., Shlegeris, B. (2022). *Causal
  Scrubbing: A Method for Rigorously Testing Interpretability
  Hypotheses.* Alignment Forum.
- Goldowsky-Dill, N., MacLeod, C., Sato, L., Arora, A. (2023).
  *Localizing Model Behavior with Path Patching.* arXiv:2304.05969.
- Ghandeharioun, A., Caciularu, A., Pearce, A., Dixon, L., Geva, M.
  (2024). *Patchscopes: A Unifying Framework for Inspecting Hidden
  Representations of Language Models.* ICML 2024.

**Causal abstraction and alignment.**

- Geiger, A., Wu, Z., Potts, C., Icard, T., Goodman, N. D. (2023).
  *Finding Alignments Between Interpretable Causal Variables and
  Distributed Neural Representations.* CLeaR 2023.
- Chalupka, K., Perona, P., Eberhardt, F. (2015). *Visual Causal
  Feature Learning.* UAI 2015.

**Weakness, simplicity, invariance.**

- Bennett, M. T. (2000, 2023). *The Weakest Hypothesis.* Compendium
  of information-theoretic learning arguments.
- Solomonoff, R. J. (1964). *A Formal Theory of Inductive Inference.*
  Information and Control 7.
- Hutter, M. (2005). *Universal Artificial Intelligence.* Springer.
- Ellis, K., Wong, C., Nye, M., Sable-Meyer, M., Cary, L.,
  Morales, L., Hewitt, L., Solar-Lezama, A., Tenenbaum, J. B. (2020).
  *DreamCoder: Growing Generalizable, Interpretable Knowledge with
  Wake-Sleep Bayesian Program Learning.* PLDI 2020.
- Gruver, N., Finzi, M., Stanton, S., Wilson, A. G. (2023). *The Lie
  Derivative for Measuring Learned Equivariance.* ICLR 2023.
- Cohen, T. S., Welling, M. (2016). *Group Equivariant Convolutional
  Networks.* ICML 2016.

**Grid cells, path integration, geometry.**

- Sorscher, B., Mel, G. C., Ganguli, S., Ocko, S. A. (2019, 2023). *A
  Unified Theory for the Origin of Grid Cells Through the Lens of
  Pattern Formation.* NeurIPS 2019 / expanded 2023 in J.
  Neuroscience.
- Whittington, J. C. R., Muller, T. H., Mark, S., Chen, G., Barry, C.,
  Burgess, N., Behrens, T. E. J. (2020). *The Tolman-Eichenbaum
  Machine: Unifying Space and Relational Memory Through Generalization
  in the Hippocampal Formation.* Cell 183.
- Gardner, R. J., Hermansen, E., Pachitariu, M., Burak, Y., Baas, N.
  A., Dunn, B. A., Moser, M.-B., Moser, E. I. (2022). *Toroidal
  Topology of Population Activity in Grid Cells.* Nature 602.
- Webb, T., Miolane, N., et al. (2024). *Geometry of Consciousness:
  A Riemannian Manifold Perspective.* (Community talk / preprint.)

**Active inference, empowerment, sense of agency.**

- Friston, K., FitzGerald, T., Rigoli, F., Schwartenbeck, P., Pezzulo,
  G. (2017). *Active Inference: A Process Theory.* Neural Computation
  29(1).
- Klyubin, A. S., Polani, D., Nehaniv, C. L. (2005). *Empowerment: A
  Universal Agent-Centric Measure of Control.* CEC 2005.
- Kirchhoff, M., Parr, T., Palacios, E., Friston, K., Kiverstein, J.
  (2018). *The Markov Blankets of Life: Autonomy, Active Inference and
  the Free Energy Principle.* J. R. Soc. Interface 15.
- Ryu, S., Kwon, S., Sung, W. (2022). *Sense of Agency in
  Reinforcement Learning: A Definition and its Applications.*
  ICLR 2022.

**Grokking and modular arithmetic (external evaluation targets).**

- Power, A., Burda, Y., Edwards, H., Babuschkin, I., Misra, V. (2022).
  *Grokking: Generalization Beyond Overfitting on Small Algorithmic
  Datasets.* arXiv:2201.02177.
- Nanda, N., Chan, L., Lieberum, T., Smith, J., Steinhardt, J.
  (2023). *Progress Measures for Grokking via Mechanistic
  Interpretability.* ICLR 2023.
- Biderman, S., Schoelkopf, H., Anthony, Q., Bradley, H., O'Brien, K.,
  Hallahan, E., Khan, M. A., Purohit, S., Prashanth, U. S., Raff,
  E., Skowron, A., Sutawika, L., van der Wal, O. (2023). *Pythia: A
  Suite for Analyzing Large Language Models Across Training and
  Scaling.* ICML 2023.
- Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S.,
  Wang, L., Chen, W. (2022). *LoRA: Low-Rank Adaptation of Large
  Language Models.* ICLR 2022.

**In-house prior program (this branch's dependencies).**

- Brown, J. (2026a). *Structure-Compatible Generalization: Weakness
  Predicts OOD Better Than Loss, Simplicity, Flatness, or Compression.*
  ``papers/weakness_invariance_neurips/paper.md``.
- Brown, J. (2026b). *Concern-Weighted Weakness: A Bridge Theorem.*
  ``papers/concern_weighted_weakness/paper.md``.
- Brown, J. (2026c). *Gauge-Fixed Concern Transport.*
  ``papers/gauge_fixed_concern_transport/paper.md``.
- Brown, J. (2026d). *Passive-to-Active Geometry.*
  ``papers/passive_to_active_geometry/paper.md``.
- Brown, J. (2026e). *External Contact Pre-Registration.*
  ``docs/external_contact_preregistration.md``.

### A.4 Reviewer response (pre-empt)

We anticipate three lines of criticism and answer here.

**R1. "Your cyclic modular addition is a synthetic world; the E4
external contact is still on modular addition, so this isn't external."**

Response. The E4 external is *not* another synthetic world. It uses a
public open-weights model family (Pythia 70m/160m/410m) trained on
The Pile, and asks whether a LoRA fine-tune with cyclic-orbit
augmentation produces load-bearing OOD generalization. The old-frame
reading of our own prior program predicted a yes on weakness readout;
our P1 hard-kill and E4 Arm A both said no. The commitment-first
reframe predicted that Arm B (train-time compat intervention) would
recover, and E4 does — at n=13 in smoke, at scale in the full grid.
This is exactly the kind of *pre-registered directional prediction on
a system the lab did not build* the prior program's critique
identified as missing. It is not the last word on external contact —
we say so in Section 6.4 — but it is a genuine one.

**R2. "Patch-CE is confounded with total LoRA effect; you're just
measuring that the model uses fine-tuning."**

Response. The wrong-group Arm C is the anti-cheat. Arm C has the same
*augmentation volume* as Arm B — same number of extra training pairs,
same LoRA capacity, same optimizer trajectory — but the augmented
pair `(x, y = truth(x))` is transformed by a random non-cyclic
permutation π to `(π(x), π(y))`, teaching the model the wrong
equivariance `f(π(x)) = π(f(x))` instead of the cyclic action
`f(x + k) = f(x) + k`. On any input that also appears in the base
training set with its true label, Arm C's augmentation is *inconsistent*
with the cyclic rule, so the model cannot fit both without choosing.
If patch-CE were only measuring "the LoRA update is used", Arms B and C
would have similar patch-CE and similar OOD. Empirically the anti-cheat
holds: LoRA is only load-bearing when the augmentation *group* matches
the deployment generator, not merely when augmentation *volume* is
present. However, Arm C controls volume, **not label exposure**: Arm B's
cyclic augmentation places correctly labeled examples on the held-out
deployment support, while Arm C places incorrectly labeled ones there.
An earlier revision of Arm C used the labeled coverage augmentation
`(π(x), b) → truth(π(x), b)`, which just extends training coverage
with correct labels and — as expected — also produced OOD
generalization. That result answers a different question ("does
adding correct-labeled coverage help?" — yes) and, importantly, keeps
the coverage explanation of Arm B live: the reviewer's confound is
real, not hypothetical. Section 6.5 states the confound explicitly and
pre-registers the severe follow-up (generator regularization confined
to train support, tested on a novel group element or modulus) with
kill criteria. Until it runs, R2's strongest defensible reading of E4
is "aligned train-time intervention recovers external OOD where
readout selection does not," with the mechanism not yet isolated.

**R3. "The anti-Goodhart control loop reads like a philosophical
compression, not an empirical result."**

Response. It is a compression *hypothesis* over the prior Correction
Chain, made testable by the load-bearing subset claim: {allocate,
cool, reopen} carry the causal load; {detect, saturate} are
diagnostic. The claim is falsifiable by a factorial ablation in Suite
C — drop any one of {allocate, cool, reopen} and check whether the
world-change re-engagement gate survives. We do not run that
factorial in this paper (F4 in Section 4 is honest about this), but
it is the concrete follow-up and we name it. The paper's headline
claims (C1–C3 and C5) do not depend on M4; M4 is a load-bearing
conjecture whose downstream test is designed but not yet completed.
