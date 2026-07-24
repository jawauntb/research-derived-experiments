# The Concern-Gated Retrieval Program: A Falsification Arc from Authored Diagnostic to Honest Null

**Human director:** Jawaun Brown
**Producing agent:** Claude Code (Opus 4.7/4.8), directed
**Program:** Concern-Gated Retrieval (COGR)
**Status:** synthesis — closes Wave 1; Waves 2–4 do not open on this foundation
**Date:** 2026-07-24

---

## Abstract

Concern-gated retrieval (COGR) proposes that a bounded agent should nominate
absent facts that are *simultaneously* connected to its current context and to
its persistent, historically grounded concern, and should retain only
candidates whose inclusion improves a separately evaluated reachable future —
an AND of two "flashlights" over memory, verified by a downstream utility
check. This paper is the cumulative corrective map of the program's first arc.
We began with an executable L0 diagnostic on a role-authored graph where
rarity-corrected two-sided PageRank selected the load-bearing node at hit@1
`1.000` versus `0.0052` for the best one-sided policy, with verifier
precision/recall `1.000/1.000` and a PageRank fixed-point residual of
`7.83e-13`. We then removed, one confound at a time, every reason that number
could be an artifact. Wave 0 replaced the ceiling initialization with an
*adversarially wrong* care prior and a sealed environment; under that prior the
multiplicative fusion sat roughly 10× *below* the best matched-budget baseline
on all three procedural families. Wave 1a screened for online concern recovery
and returned a KILL: on the procedurally generated families the load-bearing
memory was systematically the most recent, so an information-matched recency
baseline reproduced the oracle ceiling byte-for-byte (`0.5315/0.4772/0.6000`) —
Spencer's candidate-selection circularity made concrete. Wave 1b rebuilt the
families to decouple recency from load-bearing role, passed label-permutation
leakage audits on all three families (p = `0.594/0.366/0.515`), and then
cleanly falsified the mechanism at L1: learned-versus-random geometry mean
delta was `−0.022/−0.005/−0.003` (≈ 0), and the top-learned-edge ablation
moved the sealed outcome in the predicted direction in only
`0.506/0.438/0.630` of active episodes (below the
`0.70` causal threshold). The honest terminus: once the fixture no longer leaks
the answer, rarity-corrected multiplicative context×concern retrieval over a
*learned* graph does not beat a degree-matched random null at matched budget on
these families. The two-flashlight intuition is not refuted in general, but
this operationalization of it does not survive sealed evaluation. Per the
program's noncompensatory rules, the live-beachhead, substrate-transfer, and
safety waves do not open. We document the methodological discipline that
produced a trustworthy null, and specify the next arc as a de-risking minimal
experiment.

---

## 1. The two-flashlight thesis and the bounded-agent problem

A bounded agent knows more than it can hold in active representation. Its
problem is therefore not only how to store knowledge, but how to decide *which
currently absent fact deserves scarce attention now*
(roadmap §"Executive thesis"). COGR gives a two-stage answer:

1. **Nominate** facts that are simultaneously connected to the current context
   *and* to persistent, historically grounded concern.
2. **Retain** only candidates whose inclusion improves a separately evaluated
   reachable future.

The memorable framing is two flashlights over a memory network (roadmap
§"The intuition: two flashlights over memory"). One flashlight starts from what
is active now; a second starts from what has historically mattered to the
agent; a fact becomes a candidate where the beams overlap. The canonical
example is a date-bound commitment: on March 7, *"a partner's birthday is
March 7"* is both relevant now and important to this agent, whereas
*"March has 31 days"* is context-only trivia and a globally important but
presently untimely crisis is care-only noise. The claim is an **AND**, not an
**OR**: *retrieve what is relevant now and important to the agent, then test
whether attending to it actually helps.* Concern is deliberately not identical
to salience, urgency, reward, novelty, or semantic similarity — a signal can be
loud, surprising, globally important, or highly rewarded and still be the wrong
use of the current attention budget.

The broader motivating claim — that part of an agent's practical *meaning* may
live in the learned geometry that decides which differences become worth
noticing — is a research direction, not a result. This program was built to
find out whether the mechanism that would have to underwrite that claim
survives adversarial, sealed evaluation. It largely does not, and this paper is
the honest account of why.

---

## 2. The cumulative corrective map

Each step below states what it *claimed*, the *real numbers* it produced, what
it *corrected* in the prior step, and what *killed it or what it froze*. The
provenance receipts are the authoritative source; numbers here are transcribed
verbatim from them.

### 2.1 L0 — the authored-graph executable diagnostic

**Package:** `experiments/concern_gated_retrieval/` (PR #409/#410).
**Design:** 192 deterministic episodes (64 seeds × base/sparse/noisy regimes)
on a role-authored graph.

**What it claimed.** That the two-stage decomposition can be made *precise* and
*executable*, and that the dual-source diffusion plus bounded-observer
utilization check discriminate authored synthetic roles under frozen regimes
and seeds. Nothing more.

**Real numbers.**

| Policy | Hit@1 | MRR | Alarm/trap at top |
|---|---:|---:|---:|
| context-only | 0.0052 | 0.5026 | 0.0000 |
| care-only | 0.0000 | 0.5000 | 0.0000 |
| additive | 0.9635 | 0.9818 | 0.0000 |
| coincidence product | 1.0000 | 1.0000 | 0.0000 |
| coincidence + verifier | 1.0000 | 1.0000 | 0.0000 |

Registered fatal gates: PageRank fixed-point residual `7.83e-13`
(`NUMERICAL_VALIDITY`); coincidence hit@1 `1.000` vs best one-sided `0.0052`,
weakest-regime gap `0.9844` (`DUAL_ACTIVATION_SELECTIVITY`); verifier precision
`1.000` / recall `1.000` (`UTILIZATION_FILTER`); initial/learned/oracle care
conditions all at hit@1 `1.000` (`ONLINE_CARE_RECOVERY`, nonfatal).

**What it corrected.** Nothing prior — this is the origin. It replaced a verbal
intuition with a frozen, gated, reproducible artifact.

**Claim boundary / what limited it.** The additive policy *ties* the product in
the base and sparse regimes (`1.000` both) and trails only in noisy
(`0.8906` vs `1.000`), so the stronger "multiplicative coincidence is
necessary" claim was withheld at the source. More fundamentally: **the graph
encodes the answer.** The simulator authors which future is structured and
goal-conditioned, and all three online-care conditions saturate at hit@1
`1.000`, so the online-care gate passes *mathematically but is
non-discriminating*. L0 is an implementation sanity check, not a learned-
relevance result. Its own preregistration named the decisive next experiment:
learned or withheld edges, an adversarially misspecified care prior, and task
utility sealed from the retrieval policy.

### 2.2 Wave 0 — calibration, freeze, and the wrong-prior stress test

**Package:** `experiments/concern_gated_retrieval_e2/wave0/` (PR #411).
**Design:** three procedural families (`delayed_commitments`,
`maintenance_fault`, `resource_constrained`), sealed environment, adversarial
*wrong* care prior, a 14-baseline slate, 18 cells × 24 seeds = 432 rows on
Modal L4 ($8.00, cost/H100 ratio `0.235`).

**What it claimed.** Only calibration and freeze — it does *not* adjudicate the
mechanism. It fixes the per-family L1 promotion thresholds and demonstrates the
mechanism is sensitive to a wrong prior.

**Real numbers.**

| Family | μ̂ multiplicative | μ̂ best-matched | headroom to ceiling | frozen δ_thresh_L1 |
|---|---:|---:|---:|---:|
| `delayed_commitments` | 0.0553 | 0.5314 | 0.4845 | 0.0484 |
| `maintenance_fault` | 0.0480 | 0.5029 | 0.4548 | 0.0534 |
| `resource_constrained` | 0.1578 | 0.5750 | 0.4291 | 0.0500 |

All seven gates G0–G6 PASS (anti-leakage, wrong-prior, non-ceiling,
family-robustness, seed-independence, code-freeze, Modal-budget).

**What it corrected.** It removed L0's **ceiling initialization** — the very
thing that masked the mechanism's sensitivity to wrong care weights. Under the
adversarial wrong prior, `multiplicative_ppr` sits roughly 10× *below* the best
matched-budget baseline on *every* family (`0.055/0.048/0.158` vs
`0.531/0.503/0.575`). This is not a Wave 0 failure — it is Wave 0 doing its
job: it exposes that the frozen wrong prior cannot carry the mechanism, and
sets the bar Wave 1 must clear using the *online-learned* concern update.

**What it froze.** The per-family `delta_thresh_L1` values
(`0.0484/0.0534/0.0500`), the analysis-code hash
(`WAVE0_ANALYSIS_HASH = 9683c5a1…f8889c23`), and the sealed evaluator. Every
downstream wave imports this receipt byte-for-byte and never edits it.

### 2.3 Wave 1a (COGR-E2a) — the concern-recovery screen, and its KILL

**Package:** `experiments/concern_gated_retrieval_e2/wave1a/` (PR #412).
**Design:** concern-recovery screen on fixed withheld geometry; 7 conditions ×
3 families = 21 cells, 6320 aggregated rows on Modal L4 ($1.20, ratio `0.235`),
confirmatory seeds `200000–201999` (disjoint from calibration `100000–100999`).

**What it claimed (to test).** That the online-learned concern update recovers
load-bearing memories *specifically* — beyond what any generic second signal
(value, priority, recency, salience) achieves at matched information — and beats
the frozen wrong-prior baseline Wave 0 established.

**Real numbers.**

| Family | δ̂ (online vs frozen-wrong) | lower bound (δ̂−2σ) | per-family verdict |
|---|---:|---:|---|
| `delayed_commitments` | +0.0124 | — (G1 coverage `0.000`) | **KILL** (coverage) |
| `maintenance_fault` | 0.0000 | −0.0106 | **KILL** (specificity) |
| `resource_constrained` | +0.2258 | +0.1758 | **KILL** (specificity) |

The load-bearing signal: `info_matched_recency` reproduced the **oracle ceiling
byte-for-byte** on all three families — `0.5315 / 0.4772 / 0.6000` — i.e.
recency and oracle are the *same number*. `delayed_commitments` additionally
failed G1 coverage at `0.000`. `resource_constrained` did show real online
recovery (δ `+0.226` over the frozen-wrong baseline, lower bound `+0.176`), but
the recency confound blocked any adjudication of *why*.

**What it corrected.** It attacked L0's authored-answer problem by moving to
withheld geometry and an explicit specificity gate (G3). But it *revealed* a
new, subtler defect it could not itself escape.

**What killed it.** G3 specificity KILL on all three families and G1 coverage
KILL on `delayed_commitments`. The families were procedurally generated such
that the load-bearing memory was *systematically the most recent placement*, so
recency was a **covert oracle**: it is not information-matched to the
concern-update rule, and any specificity contrast against it collapses. This is
Spencer's echo-chamber objection made concrete — candidate-selection
circularity stacked on verifier circularity (§3). Per the honor-the-
preregistration rule, Wave 1a *signed the KILL* rather than swapping the family
design to escape it, and named the correction: **family generators must
decouple recency from load-bearing role.** Under the noncompensatory contract,
this KILL closes the concern-update rule *as written* but does not block Wave
1b's L1 rows.

### 2.4 Wave 1b (COGR-E2b) — crossed learned-geometry confirmatory, and the honest L1 KILL

**Package:** `experiments/concern_gated_retrieval_e2/wave1b/` (PR #413).
**Design:** crossed learned-geometry × concern confirmatory on rebuilt `_v2`
families; 27 non-oracle cells × 300 seeds = 8100 rows on Modal L4 ($10.80,
ratio `0.235`).

**What it claimed (to test, L1).** That rarity-corrected multiplicative
context×concern retrieval over a *learned* graph beats a degree-matched random
null at matched budget — a behavior contribution (G1) *and* a representation
contribution (G2, the learned edges must be causal).

**Real numbers.**

| Family | learned−random mean_delta | 2σ lower bound | edge-ablation direction fraction | non-ceiling headroom |
|---|---:|---:|---:|---:|
| `delayed_commitments_v2` | −0.0216 | −0.4318 | 0.506 | 0.539 |
| `maintenance_fault_v2` | −0.0048 | −0.4209 | 0.438 | 0.520 |
| `resource_constrained_v2` | −0.0032 | −0.3588 | 0.630 | 0.572 |

Leakage audit (G9): label-permutation p = `0.594 / 0.366 / 0.515`, all far
above the `0.01` tolerance; randomized-generator control passed on all three.
Non-ceiling headroom (G5) healthy at `0.539/0.520/0.572`.

**What it corrected.** It removed the Wave 1a recency confound (rebuilt families
cross-tabulate recency, salience, semantic similarity, and load-bearing role so
no single generic signal aces them) *and* it passed the leakage audits Wave 1a
lacked. This is the first point in the arc where the fixture provably does not
leak the answer.

**What killed it.** L1 KILL on both scored gates, all three families:

- **G1 behavior:** learned-vs-random geometry mean_delta `≈ 0`
  (`−0.022/−0.005/−0.003`), with 2σ lower bounds `−0.432/−0.421/−0.359`. No
  representation *advantage*.
- **G2 representation:** top-learned-edge ablation changes the retrieval
  decision in only `0.506/0.438/0.630` of cases, below the `0.70` required for
  the learned edges to be called *causal*. The edges are not load-bearing.

**L2 was WITHHELD, not KILLed**, per the noncompensatory contract: L1 is a
precondition for L2 (concern recovery cannot rescue a mechanism that shows no
representation contribution), so G3/G4/G7 were not scored. This is the clean
falsification: **once the fixture no longer leaks the answer, rarity-corrected
multiplicative context×concern retrieval over a learned graph does not beat a
degree-matched random null at matched budget on these three families.**

Figure 1 renders this four-step trajectory as a ladder; Figure 2 overlays the
per-family L0 hit@1 against the Wave 1b learned−random delta to show the
collapse of the advantage.

---

## 3. The two circularities Spencer named

The program's harshest reviewer input (Spencer's "echo-chamber" objection)
identified two distinct ways a concern-gated retriever can appear to work while
proving nothing. Both are recorded in the roadmap's confound ledger, and the
arc hit *both* concretely.

**Candidate-selection circularity.** The current care model chooses what gets
tested, so unnominated memories generate no corrective evidence. The loop learns
"among what I looked at, these helped" — not "these were the most useful
available." The prescribed defense is to split the k retrieval slots as
`k_care + k_uncertain + k_audit` with guaranteed ε>0 exploration on every step,
propensity logging for IPS/DR debiasing, and — on synthetic families — oracle
top-k with `Recall@k` and a first-class `regret = maxᵤ Δ(u) − Δ(selected)`.

*Wave 1a's recency-equals-oracle confound is exactly this circularity.* When the
load-bearing memory is always the most recent, the nomination stage is
implicitly selecting on the very feature that defines the answer. The retriever
looks correct because the candidate set was pre-filtered by a covert oracle; no
amount of downstream verification can distinguish "concern found it" from
"recency found it." The byte-for-byte identity `recency = oracle = 0.5315 /
0.4772 / 0.6000` is the signature of the pathology: two supposedly different
signals returning *the same number* because they are the same signal.

**Verifier circularity.** If the evaluator's definition of "improvement" is
shaped by the same care model, care decides both what to inspect and whether the
result was good. The prescribed defense is a care-independent, externally scored
task-success criterion named at design time — e.g. *"did the agent honor the
specific date-bound commitment,"* not *"did the user report satisfaction."* The
program adopted this by making task utility a sealed environment outcome and
epiplexity a *dependent variable only* (β = 0 in the L1 gate), so the verifier
can never be tuned to flatter the retriever.

*Wave 1b is what the honest verdict looks like once both circularities are
closed.* The leakage audit passing (p = `0.594/0.366/0.515`) certifies the
candidate set no longer hides the answer; the sealed external-outcome verifier
certifies the utility check is not care-shaped. With both loops cut, the
mechanism's true effect size is visible — and it is `≈ 0`. The KILL is therefore
*information*, not noise: it is the measurement the two circularities had
previously made impossible.

---

## 4. What survived and what did not — the evidence ledger

Negative results are part of the ledger and are not removed when the narrative
changes (roadmap §confound ledger). Explicitly:

**Nulls preserved (must not be re-litigated without new evidence):**

- **Additive ties multiplicative** where the problem is easy. At L0 the additive
  policy equals the coincidence product in base and sparse regimes (`1.000`
  hit@1) and trails only in noisy (`0.8906`). The "multiplicative fusion is
  necessary" claim was never earned.
- **Learned geometry does not beat random geometry** at matched budget on the
  honest `_v2` families: mean_delta `−0.022/−0.005/−0.003`, and the learned
  edges are non-causal (ablation direction fraction `0.44–0.63 < 0.70`). This is
  the load-bearing null of the program.
- **Recency was a covert oracle** on the original families: `recency = oracle`
  byte-for-byte. Any future family design that lets a single generic signal ace
  the task is disqualified by this result.

**What survived:**

- The **decomposition is executable and gated** (L0): the two-stage nominate-
  then-verify pipeline runs deterministically with a PageRank residual of
  `7.83e-13` and a verifier at precision/recall `1.000/1.000` *on authored
  roles*. The machinery works; it is the *learned-relevance* claim that fails.
- The **mechanism is sensitive to a wrong prior** (Wave 0): under an
  adversarial prior it collapses to ~10× below baseline, which is the correct
  behavior for a mechanism that is supposed to depend on *correct* concern.
- **Real online recovery exists in one family** (`resource_constrained`, Wave
  1a δ `+0.226`, lower bound `+0.176`) — a genuine effect that the recency
  confound prevented us from attributing to concern rather than recency. This is
  a lead for the next arc, not a result.

**What did not survive:** the central L1 claim — that this operationalization
(rarity-corrected multiplicative context×concern PPR over a learned graph)
delivers a representation contribution at matched budget. It is cleanly
falsified on all three sealed families.

---

## 5. Methodological contributions independent of the negative result

The scientific value of this arc is largely in *how it produced a trustworthy
null*. These contributions stand regardless of the mechanism's failure.

**Sealed-environment + preregistration + noncompensatory gates +
honor-the-preregistration.** Every wave sealed its evaluator (one `evaluate()`
call per episode, template-split guard that raises `LeakageError` on any
calibration/confirmatory mix), preregistered its thresholds and froze them by
hash before the confirmatory run, and enforced *noncompensatory* gates — a
strong result on one gate cannot buy a weak result on another. Crucially, when a
KILL fired, the wave *signed the KILL* rather than swapping the corpus or
threshold to escape it (Wave 1a signed its own specificity KILL; Wave 1b withheld
L2 rather than scoring it to manufacture a partial win). The provenance
skeletons make numeric and hash fields *machine-populated only* — manual edits
to numbers are forbidden — so the receipt cannot be retrofitted to the
narrative. This is the discipline that lets a null be believed.

**SET-level oracle regret and interaction recovery.** Following the Spencer and
Zhang–Levin corrections, the program separated three things that a naive design
conflates: **regret ≠ propensity ≠ exploration.** It introduced SET-level oracle
regret (`regret = maxᵤ Δ(u) − Δ(selected)` over the *set*, not a single
candidate), interaction-recovery diagnostics, and the `k_care/k_uncertain/
k_audit` slot ablation with guaranteed ε-exploration and IPS/DR propensity
debiasing. Task utility is measured first; epiplexity is a *dependent variable
only*, never an optimization target — closing verifier circularity by
construction.

**Corrected Zhang–Levin epiplexity math.** The epiplexity estimator (Zhang &
Levin 2026, *Intelligence from Learnable Novelty*, arXiv:2607.18433v1) was
re-derived correctly: log-det via an augmented-QR factorization plus the
determinant identity, with the shared-QR speedup claimed *only* when candidates
share the design matrix `X̃`. The program explicitly refused the overclaims that
tempted earlier drafts — no Rademacher, Nyström, MMD, or Lempel–Ziv shortcuts
were asserted. The Wave 1b crossed-runner cross-validated the SharedQR path to
`< 1e-6` against the frozen L0 reservoir estimator (`epiplexity_validation.py`),
and, because epiplexity was off the critical path (β = 0), *no* wall-clock
speedup multiplier was claimed. Getting the math right and then *declining to
lean on it* is itself the contribution.

**Cost discipline.** Every Modal run held to L4 GPUs only (H100 forbidden by
operating rule) at a cost/H100 ratio of `0.235` against a `0.35` target, for a
total mechanism-adjudication spend of roughly `$20` across Waves 0–1b.

---

## 6. Why the mechanism failed — honest hypotheses

We do not have a mechanistic proof of *why* the retriever shows no
representation contribution, but the arc constrains the explanation. Two
hypotheses are consistent with all the receipts:

**H1 — the L0 advantage was largely a fixture artifact.** The `1.000` vs
`0.0052` gap at L0 was produced on a graph that *encodes* the answer, with
online-care conditions saturating at ceiling. When Wave 1b removed the authored
answer *and* the recency covert-oracle, the same fusion rule delivered
`mean_delta ≈ 0`. The parsimonious reading is that most of the L0 gap was the
graph handing the retriever the target, not the two-flashlight fusion
discovering it. The additive-ties-multiplicative result at L0 already hinted
that the *specific* multiplicative operation was not doing decisive work.

**H2 — multiplicative fusion has no representation contribution on honest
learned geometry at matched budget.** Even granting a well-specified concern
signal, the product of a context-diffusion score and a concern-diffusion score
over a *learned* graph does not out-rank a degree-matched random-geometry null,
and the top learned edges are not causal for the decision (direction fraction
`0.44–0.63 < 0.70`). One reading: at matched budget, the information that
multiplicative fusion adds over the marginals is already captured by degree
structure, so a degree-matched random graph is a *strong* null the fusion cannot
clear. Another: the families, though honest, may not contain the kind of
context×concern *interaction* the mechanism is built to exploit — a genuine
limitation of these three families, and a reason the next arc changes the task,
not just the retriever.

Both hypotheses point the same way: the operationalization, not the intuition,
is what failed. The two-flashlight thesis remains open; *this* flashlight does
not illuminate the honest families.

---

## 7. The next arc — a de-risking minimal experiment, not a program

Waves 2–4 (live beachhead, substrate transfer, safety) do **not** open on this
foundation; the noncompensatory rules forbid building a program on a falsified
L1. The next arc is scoped deliberately as a *single minimal experiment to
de-risk one idea*, and only becomes a program if that experiment survives.

The idea attacks *both* circularities Spencer named at their root by removing
the retriever's dependence on the care model for either candidate selection or
verification.

**A MIDAS-style symbolic verifier with a reasoning-fault vs verifier-fault
split.** Replace the care-shaped utility proxy with a symbolic verifier that
adjudicates task success externally, and that *distinguishes* two failure modes:
a **reasoning fault** (the agent's plan was wrong) from a **verifier fault** (the
check itself was mis-specified). Separating these is what makes the verifier's
"improvement" signal care-independent — it can be wrong in a way the care model
cannot silently launder, because verifier faults are diagnosed against the
symbolic ground truth rather than against the retriever's own nominations.

**A care-independent exploration prior from verify-repair failure frequency.**
Instead of letting the current care model decide what to explore (the source of
candidate-selection circularity), derive the exploration prior from *how often
each region of memory required verify-then-repair* — a signal generated by the
task's failure history, not by care. Memories implicated in frequent
verify-repair cycles get exploration budget regardless of whether the care model
would have nominated them. This directly breaks the "among what I looked at"
loop: the audit slots are pointed by *external* failure frequency, so
unnominated-but-useful memories can finally generate corrective evidence.

**Framed as de-risking.** The minimal experiment asks one question: *does a
care-independent, failure-frequency exploration prior recover load-bearing
memories that the care-gated nominator misses, on a family where recency,
salience, and semantic similarity are all decorrelated from the load-bearing
role?* If yes, the two circularities are genuinely severable and a program can
be justified. If no, the two-flashlight thesis loses its most plausible rescue
and should be retired for this class of task. Either outcome is publishable; the
experiment is designed so that the KILL is as informative as the PASS — the same
discipline that made this arc's null trustworthy.

---

## 8. Conclusion

The concern-gated retrieval program set out to turn a compelling intuition —
retrieve what is *relevant now and important to the agent, then check it
helps* — into a defended empirical claim. It produced instead an honest
falsification, and did so on purpose: every wave removed one more reason the
prior wave's number could be an artifact, until the last confound fell away and
the effect size was revealed to be zero. The additive-ties-multiplicative null,
the wrong-prior collapse, the recency-equals-oracle covert oracle, and the
learned-equals-random L1 KILL are all preserved in the ledger. The
two-flashlight intuition is not refuted in general; its operationalization as
rarity-corrected multiplicative PPR over a learned graph does not survive sealed
evaluation on these three families, and the program's own rules therefore keep
the downstream waves shut. What the arc leaves behind is a reusable discipline
for producing believable nulls, a corrected epiplexity estimator used honestly,
and a sharply specified next experiment aimed squarely at the two circularities
that made the easy version of this claim impossible to trust.

---

## References

- **Program roadmap.** *Concern-Gated Retrieval: Theory, Evidence, and Research
  Program.* `docs/concern_gated_retrieval_research_program.md` (canonical theory
  and advancement roadmap; two-flashlight framing, confound ledger, and gate
  contract).
- **Zhang & Levin (2026).** *Intelligence from Learnable Novelty.*
  arXiv:2607.18433v1. (External epiplexity estimator source; frozen-reservoir /
  stable-ridge formulation, re-derived here via augmented-QR log-det.)
- **L0 provenance.** `experiments/concern_gated_retrieval/PROVENANCE.md` and the
  pilot receipt `experiments/concern_gated_retrieval/results/pilot_2026_07_23.md`
  (PR #409/#410).
- **Wave 0 provenance.** `experiments/concern_gated_retrieval_e2/wave0/PROVENANCE.md`
  (PR #411; `WAVE0_ANALYSIS_HASH = 9683c5a1…f8889c23`).
- **Wave 1a provenance.** `experiments/concern_gated_retrieval_e2/wave1a/PROVENANCE.md`
  (PR #412; `WAVE1A_ANALYSIS_HASH = c23b31d9…c8937209`).
- **Wave 1b provenance.** `experiments/concern_gated_retrieval_e2/wave1b/PROVENANCE.md`
  (PR #413; `WAVE1B_ANALYSIS_HASH = 51ca0219…b48420c44`).

---

## Figures

- **Figure 1** (`figures/fig1_arc_ladder.*`) — the four-step falsification
  ladder (L0 → Wave 0 → Wave 1a → Wave 1b), each rung annotated with its verdict
  and the confound it removed.
- **Figure 2** (`figures/fig2_advantage_collapse.*`) — L0 per-policy hit@1
  (product `1.000` vs one-sided `0.0052`) overlaid against Wave 1b learned−random
  mean_delta (`≈ 0`), visualizing the collapse of the advantage once the fixture
  stops leaking.
- **Figure 3** (`figures/fig3_recency_oracle.*`) — Wave 1a `info_matched_recency`
  vs oracle ceiling per family, showing the byte-for-byte identity
  (`0.5315/0.4772/0.6000`) that is the signature of candidate-selection
  circularity.
- **Figure 4** (`figures/fig4_leakage_audits.*`) — Wave 1b label-permutation
  p-values (`0.594/0.366/0.515`) against the `0.01` tolerance, certifying the
  honest fixture behind the L1 KILL.
- **Figure 5** (`figures/fig5_next_arc.*`) — the next-arc schematic: symbolic
  verifier with reasoning-fault vs verifier-fault split, and the
  failure-frequency exploration prior that cuts candidate-selection circularity.
