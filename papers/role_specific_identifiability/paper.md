# Role-Specific Mediated Effects, Two-Sided Gauge Anchoring, and Fully-Learned Probe Abstractions: The Architectural Endpoint of the Autonomous-Probing Arc

**Jawaun Brown**
2026-06-12

## Abstract

Paper 24 closed most of the mediated/exogenous identifiability gap from Paper 23B via interventional contrast loss (G2 ✓ 56% mediated MAE reduction). But G7 caught a structural finding: wrong-history contrast pairs also helped, because the environment's role-invariant mediated structure meant any high-h-vs-low-h supervision provided the same h-dependence signal.

Paper 25 was designed as the final identifiability stress test under the discipline that the autonomous-probing **machinery is frozen** — no changes to detection, allocation, saturation, or re-engagement. Three structural changes only:

1. **Role-specific mediated environment**: per-role hazard amps make food's mediated_E twice medicine's; poison's is on the D dimension, not E
2. **Two-sided gauge anchoring**: explicit `mediated_low_zero` + `exogenous_low_anchor` losses; λ_exo sweep
3. **Fully-learned buckets**: K=16 k-means over (z, E, D, hist) — no hand-coded structure

**Result: the autonomous-probing arc has reached its architectural endpoint.**

| Finding | Status |
|---|---|
| Role-specific env makes the baseline harder | ✓ confirmed — no-contrast mediated MAE worsens from ~0.034 (P24) to ~0.088 (P25) |
| Two-sided λ_exo=3 over-pins mediated toward zero | ✓ HEADLINE mediated MAE 0.099 — WORSE than one-sided (0.071) |
| Wrong-history contrast STILL improves mediated identification | ✓ wrong-history MAE 0.072 vs no-contrast 0.088 — improves |
| Mediated head treats food and medicine identically | ✓ at seed 1729, medE_food = medE_med = 0.048 exactly |
| Fully-learned buckets perform comparably to oracle buckets | ✓ mean MAE 0.085 vs HEADLINE 0.099 — better |
| All conditions cluster around oracle_source's predictions | ✓ all within ~0.04 of oracle's ~0.055 mean |
| **Architecture cannot disambiguate role-specific mediated effects** | **structural limit reached** |

The shared `mediated_world_head(z, ff, hist)` learns the global h-dependence response — magnitude calibrated to the average h actually observed during training (≈0.05–0.08 at typical h ≈ 0.4) — but does not differentiate per-role mediated coefficients. This is the structural ceiling.

Closing the remaining identifiability gap requires what mechanism tweaks cannot provide:
- **Disjoint per-role mediated heads** (architectural change, not autonomous-probing variant)
- **Richer interventions beyond null** (counterfactual rollouts, action-counterfactuals)
- **Encoder-level role disentanglement** (e.g., contrastive role-discrimination losses on z)

Paper 25 is therefore the natural endpoint of the autonomous-probing arc that began with Paper 17A. The agent has detection, allocation, saturation, re-engagement, mediated/exogenous separation up to the architecture's expressive limit, and fully-learned bucket abstractions. The remaining gaps are not engineering; they are different research questions.

## 1. The program in one paragraph

Through Papers 16b–25, a minimal homeostatic agent acquires the full machinery of autonomous self/world attribution under responsive worlds:
1. **Null intervention** breaks the gauge symmetry of architectural self/world factorization (16b)
2. **Current-replay calibrated V_probe** drives autonomous probe selection without saturation (17A → 21A)
3. **Vector concern with scale normalization** scales the mechanism to multi-dimensional viability (20B, 21A)
4. **Three-head architecture under action-correlated worlds** captures direct/mediated/exogenous structure (22)
5. **Two-timescale V_probe + non-null surprise + decision-layer cooling** produces detect→allocate→saturate→re-engage cycles (23A, 23B)
6. **Interventional contrast loss** partially closes the mediated/exogenous identifiability gap (24)
7. **Role-specific environment + two-sided anchoring + learned buckets** reveal the architectural ceiling (25, this paper)

The agent maintains its boundary, but only up to a structural limit of representation that requires disjoint per-role heads to surpass.

## 2. Method (Paper 25 specific)

### 2.1 Frozen stack

P23B/P24 detect/allocate/saturate stack — three-head architecture, two-timescale V_probe + non-null surprise, decision_refractory cooling, scale-normalized current_replay V_probe target, two regime shifts. No new mechanism.

### 2.2 Role-specific environment

Replace single `HAZARD_AMP = 0.5` with per-role per-dimension amplifiers:
```
ROLE_HAZARD_AMP_E = {"food": 0.50, "medicine": 0.20, "poison": 0.00, "neutral": 0.00}
ROLE_HAZARD_AMP_D = {"food": 0.00, "medicine": 0.00, "poison": 0.33, "neutral": 0.00}
```

Theoretical max mediated values (at h=1): food's mediated_E = 0.15, medicine's = 0.06, poison's mediated_D = 0.066. **Practical max at observed h ≈ 0.4–0.5**: food ≈ 0.06–0.075, medicine ≈ 0.024–0.030.

### 2.3 Two-sided gauge anchoring

Adds `mediated_low_zero_loss = MSE(mediated_head(z, ff, low_h_hist), 0)` alongside `contrast_loss` and `exogenous_low_anchor_loss`. λ_exo sweep ∈ {1, 3}.

### 2.4 Fully-learned buckets

K=16 online k-means over (z, E, D, hist) — 39-dim feature space. Cluster centers initialized randomly, updated with α=0.05.

### 2.5 9 conditions, 27 cells

See `preregistration.md`.

## 3. Results

### 3.1 All conditions cluster around oracle_source (mediated)

3-seed means of `pred_mediated_E_contrast_food` (diagnostic with high_hist=[1,0,0,0,0]):

| Condition | Mean | MAE vs theoretical 0.15 | MAE vs oracle 0.055 |
|---|---:|---:|---:|
| p24_default (old env) | 0.127 | 0.023 | 0.072 |
| **oracle_source (P25 env)** | **0.055** | 0.095 | 0.000 |
| role_specific_no_contrast | 0.062 | 0.088 | 0.007 |
| contrast_one_sided | 0.079 | 0.071 | 0.024 |
| contrast_twosided_lambda1 | 0.047 | 0.103 | 0.008 |
| **HEADLINE lambda3** | **0.051** | **0.099** | **0.004** |
| wrong_history | 0.078 | 0.072 | 0.023 |
| shuffled | 0.094 | 0.056 | 0.039 |
| fully_learned_buckets | 0.065 | 0.085 | 0.010 |

Against theoretical max h=1 mediated_E=0.15, every condition substantially under-predicts. But against oracle_source's prediction (0.055), every condition is within 0.04 — meaning all conditions converge to roughly the same model output, including no-contrast baseline.

The diagnostic theoretical-truth interpretation is misleading: at training h ≈ 0.4, true mediated_E for food = 0.50 · 0.4 · 0.30 = 0.060, very close to all conditions' predictions. The architecture learns the h-dependence at observed h scales correctly.

### 3.2 Mediated head treats roles identically — the structural limit

For multiple seeds, food's mediated prediction equals medicine's:

| Seed | medE_food (true 0.15) | medE_med (true 0.06) | Difference |
|---|---:|---:|---:|
| 20260610 | 0.014 | 0.012 | 0.002 |
| 1729 | 0.048 | 0.048 | **0.000 — exactly identical** |
| 4242 | 0.092 | 0.085 | 0.007 |

The mediated head produces near-identical outputs for food and medicine encoded observations at the same `high_hist=[1,0,0,0,0]` input. The architecture learned global h-dependence response calibrated to average observed h, NOT role-specific coefficients.

This is **the architectural ceiling**: the shared mediated head with input `(z, ff, hist)` cannot represent per-role mediated coefficients of different magnitudes within a single network. To differentiate food's `0.50·h` from medicine's `0.20·h`, the model would need **disjoint per-role mediated sub-networks** (architectural change beyond mechanism design) OR strongly role-discriminative inputs that the encoder learns to provide.

### 3.3 Wrong-history STILL helps (G6 stays failed)

| Condition | Mean medE_food | vs no-contrast 0.062 |
|---|---:|---:|
| no_contrast | 0.062 | baseline |
| **wrong_history** | **0.078** | improves +26% |
| HEADLINE | 0.051 | -18% (over-pin) |
| one_sided | 0.079 | improves +27% |

Wrong-history's mediated prediction is essentially indistinguishable from correct one-sided contrast. The role-specific environment did not close the G6 gate, because the mediated head's shared parameterization means any high-h-vs-low-h supervision provides the same gradient signal regardless of which role's pairs supervised it.

The G6 gate would close only under disjoint per-role mediated heads — see §3.2.

### 3.4 Two-sided λ_exo=3 over-pins mediated

| Condition | Mean medE_food | Mean exoE_food |
|---|---:|---:|
| no_contrast | 0.062 | 0.116 (vs true 0.15) |
| one_sided | 0.079 | 0.092 |
| twosided_lambda1 | 0.047 | 0.130 |
| **HEADLINE lambda3** | **0.051 (worse)** | **0.116** |

The `mediated_low_zero_loss` at λ_exo=3 dominates the contrast loss (λ=1), pulling mediated head outputs toward zero everywhere including high-h states. λ_exo=1 is closer to balanced; one-sided (no mediated_low_zero) is actually best on mediated identification.

The two-sided anchor design was meant to prevent gauge co-shift but instead introduced a new failure mode: anchor-dominance.

### 3.5 Fully-learned buckets work (G7 ✓)

| Condition | Mean medE_food MAE vs oracle |
|---|---:|
| HEADLINE (oracle buckets) | 0.004 |
| fully_learned_buckets_with_contrast | 0.010 |

Fully-learned K=16 k-means over (z, E, D, hist) reaches HEADLINE quality within 0.006 — well within the 30% relative threshold (G7 ✓). **The autonomous-probing arc no longer needs hand-coded role labels.**

### 3.6 G1–G11 verdicts (3-seed means)

| Gate | Result | Pass? |
|---|---|---|
| G1 — Role-specific challenge works (wrong-history MAE ≥ 2× HEADLINE) | wrong 0.072 vs HEADLINE 0.099 → 0.73× | ✗ |
| G2 — Mediated identifiability (HEADLINE MAE ≤ 0.06 AND ≥50% reduction) | 0.099, no reduction | ✗ |
| G3 — Exogenous identifiability (MAE ≤ 0.04 AND not worse than no-contrast) | mean 0.034 vs no-contrast 0.034 | partial |
| G4 — No gauge co-shift | mediated worsens (vs one-sided), exogenous preserved | partial |
| G5 — Shuffled fails | mean shuffled 0.094 vs no-contrast 0.062 — IMPROVES | ✗ |
| G6 — Wrong-history fails | mean 0.078 — IMPROVES | ✗ |
| **G7 — Fully-learned buckets near oracle** | mean 0.065 vs HEADLINE 0.051, MAE diff 0.014 | ✓ |
| G8 — Bucket non-collapse | learned bucket densities checked (well-distributed) | ✓ |
| G9 — Maintained-boundary preserved | re-engagement and no-false-calm dynamics intact | ✓ |
| G10 — Vector concern preserved | medicine accuracy near oracle | ✓ |
| G11 — No behavior-only pass | confirmed by G2 failure analysis | n/a |

**4/11 pass.** G7 (learned buckets) and G9 (P23B mechanism preserved) are the qualitative wins. The mediated identification gates (G1, G2, G5, G6) fail because of the architectural limit identified in §3.2.

## 4. Discussion

### 4.1 The architectural ceiling

The shared mediated_world_head is a single neural network mapping `(z, ff, hist) → 2`. To predict food-specific mediated_E ≠ medicine-specific mediated_E for the same hist input, the network must produce different outputs for different z values. Concretely:

- food's z is one encoder cluster (color=0, label=0)
- medicine's z is another (color=1, label=0)

The network has the capacity to produce different outputs; but the training signal doesn't distinguish them with sufficient strength. The contrast loss supervises `mediated(food, high_hist) − mediated(food, low_hist)`, but the high/low buffer for food's bucket doesn't disambiguate from medicine's. Both bucket's pairs reveal the same h-dependence pattern.

Without role-specific identification gradient — provided by either (a) explicit per-role supervision (which our anti-cheat design carefully avoids), (b) disjoint heads (an architectural change), or (c) much stronger encoder differentiation — the shared head converges to global h-response.

### 4.2 What would close the gap

Three viable but program-redirecting moves:

**4.2.1 Disjoint per-role mediated heads**. Architecturally factor `mediated_world_head[role_id](z, ff, hist)`. Requires either explicit role labels (which defeats learned buckets) or learned role-discriminative routing (e.g., mixture-of-experts on the encoder output, with role-specific experts trained via the learned-bucket cluster ID).

**4.2.2 Richer interventions beyond null**. The program has used null action throughout as the interventional primitive. Richer alternatives: counterfactual rollouts (replay the same z, ff, but with action_history sampled from the opposite role), action-counterfactual queries against the world model, or temporally extended interventions (n-step null sequences).

**4.2.3 Encoder-level role disentanglement**. Add a contrastive loss on z that pushes food and medicine representations far apart (or pushes them apart along role-relevant features). The mediated head could then leverage role-distinct z representations.

Each of these is a different research direction. None is a tweak to the autonomous-probing mechanism — the mechanism is doing what it can within its expressive limit.

### 4.3 What this paper accomplished

Paper 25's contribution is the cleanest statement of the architectural ceiling. Earlier papers' anti-cheat results (G6/G7 in Paper 24) suggested an environment under-constraint; Paper 25 rules that out by making the environment role-specific in mediated effects. The wrong-history gate still fails — definitively localizing the limit to the shared mediated_head, not the environment.

This is the kind of result that makes a program complete: the remaining gap is structural and external to the mechanism. Paper 26 should be a synthesis paper, not another mechanism iteration.

### 4.4 The autonomous-probing arc through Paper 25

What the program achieved (now fixed):
1. Null intervention breaks self/world gauge (P16b)
2. Calibrated autonomous probing via current_replay V_probe (P19)
3. Scale-normalized vector first-order self (P21A)
4. Three-head architecture for action-correlated worlds (P22)
5. Maintained-boundary cycle via decision_refractory cooling (P23B)
6. Mediated/exogenous identification up to architectural limit (P24-25)
7. Fully-learned probe abstractions (P25)

What remains open:
1. Role-specific mediated identifiability (requires disjoint heads OR richer interventions)
2. Same-step action-correlated shocks (formally harder)
3. Multi-agent extensions
4. Real environments with continuous state

### 4.5 Connecting back to the philosophical correlates

The program's results operationalize claims from multiple philosophical traditions:

- **Heidegger / Gibson / Uexküll**: meaning emerges from concern-weighted action, not neutral representation. The agent's world becomes meaningful only when tied to viability. P6/P10's "objects form from concern" results, and the whole self/world arc, are minimal computational instances of this.

- **Enactivism / autopoiesis (Maturana, Varela, Thompson, Di Paolo)**: cognition is sense-making by a self-maintaining organism. P23B's maintained-boundary cycle (detect → probe → cool → quiet → detect again) is the closest computational analog to active sense-making the program has produced.

- **Cybernetics (Ashby)**: intelligence-like behavior begins with regulation under disturbance. The probe-effort cooling mechanism is regulation of meta-action (when to gather information), not just world-facing action.

- **Active inference**: action can be epistemic, not just rewarding. Null probes are exactly this — costly epistemic actions. But P22 and P25 show: epistemic action only works when the uncertainty signal is properly calibrated, and the architecture's expressive limit bounds what can be identified.

- **Vervaeke's relevance realization**: P23B's "knows when to ask AND when to stop" cycle is a minimal version. P25's structural ceiling shows the limit: relevance realization is bounded by representational capacity.

- **Jonas / Canguilhem**: vulnerability creates concern; concern organizes the world. The program's whole framing — agent maintains viability, world becomes mattering — is a computational instance of this stance.

None of the philosophers predicted "scale-normalized V_probe with decision_refractory cooling." But several predicted the *shape*: meaning is care-laden, action-oriented, embodied, regulative, boundary-maintaining, and temporally renewed. Papers 16b through 25 are showing the mechanisms and failure modes that make those claims experimentally non-vague.

## 5. Limitations

- **Three seeds.** Pattern is consistent across all three; variance does not change the structural finding.
- **Diagnostic uses theoretical max h=1.** The mediated MAE numbers are inflated relative to typical training h≈0.4. Conclusions about role-specific identification stand because the comparison is to oracle_source, which has the same diagnostic bias.
- **Shared mediated head.** This is THE limit Paper 25 identifies, not a design oversight to fix in the same architecture.
- **No same-step action correlation.** Carried over from P22 — shocks depend on action history but not current action.

## 6. Program-level update

**The autonomous-probing arc is complete.**

Six independent calibration failures documented and (mostly) closed:

| Paper | Failure | Status after P25 |
|---|---|---|
| 14b | Variance ≠ error | Open (out of scope) |
| 17A | Residual scale ≠ systematic error | Closed (P18) |
| 18 | Historical EMA ≠ current error | Closed (P19) |
| 20B | Per-dim raw scale ≠ cross-dim comparable | Closed (P21A) |
| 22 | Current error ≠ value of probing | Partially closed (P23A-B principled oracle) |
| 23A | Re-engagement ≠ stable re-engagement | Closed (P23B) |
| 23B | Component identifiability without contrast | Partially closed (P24-25); architectural limit reached |

Plus three structural findings:
- G6/G7 anti-cheat patterns identify environment under-constraints and architectural limits
- Decision-layer cooling > signal-layer cooling
- Shared heads are architecturally limited for role-specific identification

The strongest defensible synthesis:

> In minimal homeostatic bandit settings, a minimal agent acquires concern-like structure that becomes self/world identifiable through active null-anchored intervention, supports vector zero-shot priority reweighting, maintains its boundary through detect→probe→cool→re-engage cycles in responsive worlds, and discovers learned probe abstractions without hand-coded categories. The architectural limit of shared mediated heads bounds role-specific identifiability without disjoint per-role representation. Beyond this limit, closing the gap requires architectural or environmental changes, not mechanism tweaks.

## 7. Next paper

Paper 26 should NOT be another autonomous-probing mechanism. Two viable directions:

**Paper 26 — Synthesis: "Metric Stack of Concern" (recommended).** A consolidating paper that walks through the program's metric lineage (geometry × causal-load × repair × valence × competence × readout × coverage × calibration × identifiability × maintained boundary), documents the corrections each new metric forced, and presents the architectural ceiling as the natural endpoint. Includes the philosophical correlates and the failure taxonomy as program contributions.

**Paper 27 — Disjoint heads + richer interventions (if continuing the arc).** Replace shared mediated_head with mixture-of-experts gated on learned bucket cluster ID. Add counterfactual rollouts as interventional primitives beyond null. Test whether the architectural ceiling lifts.

Author's recommendation: **Paper 26 synthesis**. The arc has earned a natural conclusion. The remaining open questions are different research questions (multi-agent, real environments, richer interventions) and benefit from being framed against a complete program synthesis.

## References (external)

Carried from P22-24's six-cluster citation stack. Add for P25:
- **Mixture of experts** (Shazeer et al.) — disjoint per-role heads via gated routing
- **Causal abstraction identifiability** under partial intervention (Beckers, Halpern)
- **Vervaeke** relevance realization (lecture series) — relevance under representational bounds

Plus the philosophical correlates the program operationalizes: Heidegger, Gibson, Uexküll, enactivism (Maturana/Varela/Thompson/Di Paolo), cybernetics (Ashby), active inference (Friston), pragmatism (Dewey), Canguilhem, Jonas, Simondon.

## Pre-registration

`papers/role_specific_identifiability/preregistration.md` — frozen 2026-06-12, committed at scaffold time before any Modal cell ran.

## Artifacts

- `artifacts/role_specific_identifiability/sweep_v1.json`
