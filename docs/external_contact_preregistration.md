# External Contact Pre-Registration

**Title (working):** Three Falsifiable Predictions About Systems The Lab Did Not Build

**Frozen:** 2026-06-18, before any external fetch, download, or sweep.

**Author:** Jawaun Brown (research-strategy branch)

---

## Why this document exists

The lab-director critique in `docs/phase2_breakthrough_trajectory.md` names the
program's defining weakness precisely: **every result lives on toy worlds the lab
built itself.** Homeostatic bandits, cyclic-symbol benchmarks, rotated strokes,
pixel-rendered parse trees — all simulator-defined. A hostile reviewer can say the
three theoretical pillars (weakness→OOD, the concern/identifiability ceiling,
cross-substrate concept geometry) are artifacts of self-built environments. There
is **no external contact**: no pre-committed, directional, falsifiable prediction
about a system the lab did not construct.

This document fixes that on paper. It pre-registers **three predictions**, one per
pillar, each about a **named, public, external system**. Each follows the Phase 2
process contract (`phase2_breakthrough_trajectory.md`): breakthrough question,
old-regime shortcut, kill criterion, transfer ladder, claim tier. Each mirrors the
gate/interpretation-matrix style of `papers/*/preregistration.md`.

The same falsification ethos applies as in the metric-stack synthesis (§17): we
list these so a reviewer can identify exactly which observation would retract or
weaken each claim.

### Hard environment constraints (frozen, honestly stated)

The test environment that will check these predictions has:

- **No OpenAI / Anthropic API keys.** No Doppler, no Modal locally.
- **Network egress blocked**, including `huggingface.co` (`host_not_allowed`,
  HTTP 403) and PyPI. Verified 2026-06-18.
- **`uvx` present but unable to resolve packages** within timeout (no PyPI route);
  no `torch`, `transformers`, `numpy`, `sklearn`, or `gensim` importable; **only
  Python 3.11 stdlib** (`json`, `math`, `random`, `statistics`, `itertools`) is
  guaranteed.
- No local HF cache, no GloVe/word2vec, no model weights in-repo.

Consequence: each prediction below ships in **two runnability tiers**, and a
prediction only counts as "externally contacted" if *at least one* tier is
realizable given the above.

- **Tier A — offline-now (stdlib only).** A self-contained test against a public
  artifact whose *numeric content is small enough to be transcribed/vendored* as a
  stdlib data file, or that is reconstructable from a published table. Runs today.
- **Tier B — fetch-when-unblocked.** A pre-registered numeric prediction checkable
  against a **public, fetchable result** (a model card, a leaderboard cell, an
  arXiv table, an open-weights eval) the moment network or `uvx` is restored. The
  prediction value is frozen *now*, so the check is honest.

No prediction relies on a private API. Where a pillar's strongest test needs a
neural model, the model is **open-weights and public** and the prediction is
written so the *numbers in the relevant paper/leaderboard already decide it* (Tier
B), with a degraded-but-real stdlib proxy as Tier A.

---

# Prediction 1 — WEAKNESS → OOD on an external model family

## External system (named, specific)

**The Pythia model suite** (EleutherAI; Biderman et al., 2023) — `pythia-70m`,
`pythia-160m`, `pythia-410m`, `pythia-1.4b` — evaluated on **two public,
distribution-shifted arithmetic / symbolic generalization benchmarks the lab did
not build**:

1. **The modular-addition / "grokking" task family** as reported in the public
   grokking literature (Power et al., 2022; Nanda et al., 2023 mech-interp release),
   where train covers a fraction `p` of `(a,b) mod n` pairs and OOD is the held-out
   complement.
2. **GSM8K-style symbolic shift** is *not* used (too entangled). Instead the
   external held-out target is the **`cycle_navigation` / `modular arithmetic`
   splits of the public BIG-bench-Lite tasks**, which have published per-model
   accuracy.

These are external: the suite, its checkpoints, and the benchmarks were built by
other groups.

## Breakthrough question

Does **symmetry-compatible-hypothesis weakness** — the equivariance count of a
*learned function* under the task's true group, generalized from the lab's
`weakness_oracle_norm` (weakness paper §2, §4) — predict OOD generalization on an
external model family **better than training/eval loss, parameter count, parameter
L₂, or a flatness/sharpness proxy**, the way it did at r ≈ +0.81 on the lab's own
256/1024-MLP sweeps?

## Theory-derived, directional, falsifiable prediction

For a fixed external pretrained model (e.g., `pythia-410m`) fine-tuned with
**partial-orbit supervision** on modular addition mod n (train shows a strict
subset of the `Z_n` translation orbit), and across the four Pythia sizes:

> **P1.** The Spearman rank correlation between **learned-function weakness under
> the true group `Z_n`** (`weakness_oracle_norm`, computed on the model's argmax
> function table over the input domain) and **held-out OOD accuracy** will be
> `ρ ≥ +0.5` and will **strictly exceed** the |ρ| of every classical predictor
> — final training loss, eval loss, parameter count, parameter L₂ norm, and a
> Hutchinson-style sharpness proxy — by a margin of **≥ 0.25 in |ρ|**.
>
> Directionally: higher weakness → higher OOD; the **wrong-group control**
> (weakness under a random permutation of equal size) will have `|ρ| ≤ 0.15`.

This is the lab's own headline (weakness paper §4.2: weakness r≈+0.81 vs loss
r≈−0.03, val r≈+0.10, L₂≤+0.27, sharpness≤+0.14, wrong-group ≈ −0.12) **transferred
to a model family the lab did not train.** The directional, margin, and
wrong-group-null clauses are all pre-committed.

## Kill criterion (retracts / weakens the claim)

- **Hard kill:** any classical predictor (loss, eval loss, param count, L₂,
  sharpness) reaches `|ρ|` within 0.10 of weakness's `ρ` across the sweep, OR
  weakness `ρ < +0.3`. Then "weakness beats classical heuristics" does **not**
  survive external contact — it was a property of the lab's hand-built MLP sweep.
- **Soft kill (regime narrowing):** the wrong-group control reaches `|ρ| > 0.25`
  ("any equivariance count works"), mirroring the lab's own §5 ablation logic —
  the result would then be volume-dominated, not symmetry-specific.
- **Honest-negative mirror of the paper's own LLM caveat (§10.2):** if the
  *latent* weakness signal exists but does not predict *behavioral* OOD accuracy
  (the exact failure the weakness paper reported at Pythia-70M, N=24), we record a
  partial result, not a pass.

## Strongest old-regime shortcut baseline (should almost work)

**Eval loss / negative log-likelihood on the OOD split's *inputs*** (no labels) —
the single most defensible classical model-selection signal, and the one a
reviewer will reach for first. Secondary shortcut: **parameter count** (bigger
Pythia ⇒ usually better OOD), which is a genuinely strong confound on a *suite*
that varies size. P1 is only interesting if weakness beats *both*. If parameter
count alone predicts OOD as well as weakness, the claim collapses to "scale helps."

## Test recipe (given the constraints)

- **Tier B (fetch-when-unblocked, strongest):** `uvx --python=3.12 --with
  torch --with transformers` to load each public Pythia checkpoint; fine-tune a
  linear/LoRA head on partial-orbit mod-n (n ∈ {13, 17, 23}, train window a strict
  orbit subset); extract the argmax function table over the full domain; compute
  `weakness_oracle_norm` exactly as `experiments/symbolic_weakness/selectors.py`
  does, plus loss, L₂, and a Hutchinson sharpness proxy (Rademacher
  `vᵀHv`); regress all against held-out OOD accuracy. This **reuses the lab's
  existing weakness code unchanged** — only the function table now comes from an
  external model. Frozen seed 20260618.
- **Tier A (offline-now, stdlib only — degraded but real external contact):**
  Skip the neural model entirely and treat the **published per-model OOD accuracy
  numbers** as the external observable. Vendor a small CSV transcribed from a
  public grokking/modular-arithmetic table (model size, train fraction, reported
  OOD accuracy) into `experiments/external_contact/p1_pythia_grok_public.csv`.
  Compute, in **pure stdlib**, a *proxy weakness* for each row = the published
  fraction of the symmetry orbit covered by training (a known monotone surrogate
  for learned weakness — the weakness paper §4.2 per-augmentation table shows mean
  weakness rises monotonically with orbit coverage: none 0.14 → partial 0.32 →
  full 0.95). Pre-register: proxy-weakness Spearman ρ with published OOD ≥ +0.6,
  strictly above param-count ρ. This is weaker (orbit-coverage is a *surrogate* for
  measured weakness) but it is a real, pre-committed test against numbers the lab
  did not generate, runnable today with zero dependencies.

## Claim tier a pass earns

**Field claim** — *if* Tier B passes (weakness, measured on an external model's
learned function, beats loss/scale/L₂/sharpness with the wrong-group null holding).
This is the cleanest "survives literature-nearest baselines on a system we did not
build" result in the program. **Tier A alone earns at most regime-transition /
diagnostic** (it confirms the directional law against external numbers but uses an
orbit-coverage surrogate, not measured neural weakness).

---

# Prediction 2 — CONCERN / IDENTIFIABILITY CEILING on an external active-learning system

## External system (named, specific)

**The public deep-ensemble / Bayesian active-learning uncertainty literature on a
standard benchmark the lab did not build** — concretely:

- **Deep Ensembles (Lakshminarayanan et al., 2017) on rotated/corrupted CIFAR-10
  (CIFAR-10-C; Hendrycks & Dietterich, 2019)** — public weights/benchmarks; and
- **BALD-style batch active learning on MNIST/FashionMNIST** as reported in the
  public active-learning benchmarks (Houlsby et al., 2011; Gal et al., 2017;
  Kirsch et al. BatchBALD, 2019).

Both are external systems with **published calibration and acquisition curves**.

## Breakthrough question

Two of the metric-stack's load-bearing corrections — **"uncertainty is not error"**
(Correction 4.3: same-architecture ensemble variance is uncorrelated with error at
the regime boundary, r≈0) and the **no-false-calm gate** (§2.5: a probe/acquisition
signal that falls without a matching fall in error is silencing, not resolving) —
were established only on the lab's homeostatic bandit. Do they **transfer to an
external uncertainty/active-learning system the lab did not build**?

## Theory-derived, directional, falsifiable predictions

> **P2a (uncertainty ≠ error / no-false-calm, transferred).** For deep ensembles
> of *identical architecture* on CIFAR-10-C, the per-sample correlation between
> **ensemble predictive variance** and **actual prediction error** will **collapse
> toward zero (Pearson |r| ≤ 0.2) precisely on the high-corruption-severity /
> distribution-shifted slices** where error is *highest* — even while it is
> positive on in-distribution data. The ensemble will exhibit **"false calm"**:
> regions of high error where variance fails to rise. This is the CIFAR-scale
> analog of the lab's E=0.5 regime-boundary finding (Paper 14b).
>
> **P2b (architectural ceiling on identifiability, transferred).** For BALD/
> BatchBALD active learning on MNIST/FashionMNIST, the published acquisition-vs-
> error curves will show the metric-stack's signature: **acquisition by current
> model uncertainty (BALD) underperforms an information-gain/expected-error-
> reduction oracle** (the lab's "current error ≠ value of probing", Correction
> 4.6, Paper 22's 5× finding), and **batch-naive BALD will redundantly sample
> near-duplicate points** — a *false-calm-adjacent* failure that BatchBALD's own
> paper documents and fixes. Directional: the gap between naive-uncertainty
> acquisition and value-of-information acquisition is **non-zero and in the
> predicted direction** on an external benchmark.

## Kill criterion (retracts / weakens the claim)

- **Kills P2a:** if external deep-ensemble variance stays well-correlated with
  error on the *shifted/high-corruption* slices (Pearson |r| ≥ 0.5 there), then
  "same-class uncertainty is not epistemic" was bandit-specific. This is the exact
  mirror of metric-stack falsification condition #6 ("anti-cheat / no-false-calm
  methodology fails to transfer").
- **Kills P2b:** if published BALD acquisition matches a value-of-information
  oracle within noise (no 4.6-style gap), then "current error ≠ value of probing"
  does not survive external contact.
- **Weakens both:** if the only external systems that show the pattern are
  themselves toy (MNIST is small), the transfer is partial — record as diagnostic,
  not field claim.

## Strongest old-regime shortcut baseline (should almost work)

**"Ensemble variance is a good epistemic uncertainty estimate."** This is the
*default* belief in the deployed-ML community and is true in-distribution — it
should almost work, which is exactly why P2a is a sharp test: the claim is that it
**breaks on the shifted slices**, the regime where it matters. For P2b the shortcut
is **"max-entropy / BALD single-point acquisition is near-optimal"** — strong on
i.i.d. pools, predicted to fail on batch / redundancy and on value-of-information.

## Test recipe (given the constraints)

- **Tier A (offline-now, stdlib only — primary, because the published curves
  already decide it):** This prediction is **checkable against published numbers**
  without running any model. Transcribe into
  `experiments/external_contact/p2_uncertainty_public.csv`:
  (i) CIFAR-10-C ensemble variance-vs-error correlation by corruption severity from
  the public deep-ensembles / corruption-robustness tables; (ii) BALD vs.
  BatchBALD vs. random acquisition accuracy-per-label-budget from the BatchBALD
  paper's published figures. Then compute, in stdlib, the pre-registered
  comparisons (|r| on shifted slices ≤ 0.2; BatchBALD > naive-BALD redundancy gap
  > 0). Because the numbers are frozen *now* from public sources, the only honest
  question is whether they fall on the predicted side — a genuine external check.
- **Tier B (fetch-when-unblocked, confirmatory):** `uvx --with torch --with
  torchvision` to load a public pretrained CIFAR-10 ensemble (or train 5 small
  CNNs), evaluate on CIFAR-10-C, and compute the variance-error correlation per
  severity directly, reusing the spirit of
  `experiments/ensemble_uncertainty/`. Frozen seed 20260618.

## Claim tier a pass earns

**Regime transition → field claim.** P2a/P2b transfer the metric-stack's two most
portable methodological corrections (uncertainty≠error; current-error≠value-of-
probing / no-false-calm) to an *external, widely-used* uncertainty stack. A clean
Tier-A pass against published curves is already a **field claim about
methodology** ("the lab's anti-cheat gates catch real failures in deployed active
learning"); Tier B strengthens it to mechanism on external weights.

---

# Prediction 3 — CONCEPT GEOMETRY CONVERGENCE on an external embedding family

## External system (named, specific)

**The public GloVe word-embedding family** (Pennington, Socher & Manning, 2014 —
`glove.6B`, 50/100/200/300-d, trained on Wikipedia+Gigaword by Stanford) and,
where fetchable, **fastText `crawl-300d`** (Bojanowski et al., 2017). These are
external, public, static embedding tables — the lab built neither. They are the
*purest* test of cross-substrate concept geometry because they are not LLMs, not
built by the lab, and not API-gated.

## Breakthrough question

The geometric-convergence synthesis (`notes/geometric_convergence_research_synthesis.md`)
and the concept-geometry track (`experiments/concept_geometry/`) claim that
independently named concepts occupy **related relational neighborhoods across
substrates**, and that this relational structure is **stable under paraphrase /
alias** and **convergent across independently trained models** (Platonic
Representation Hypothesis, Huh et al., 2024). The lab tested this only with
OpenAI embeddings (API-gated) and a partial Pythia-70M paraphrase probe (weakness
paper §10.2). Does the convergence claim hold on an **external, non-LLM,
independently-trained embedding family the lab did not build**?

## Theory-derived, directional, falsifiable prediction

Using the lab's own 24-concept set (`experiments/concept_geometry/concept_set.json`,
six categories: dynamics, cognition, semantics, ai_geometry, constraint, discovery,
agency) and its paraphrases (`concept_paraphrases.json`):

> **P3a (category-block geometry replicates externally).** In GloVe-300d, the mean
> within-category cosine similarity among the 24 concepts will **exceed the mean
> across-category cosine by a margin ≥ +0.10** (after the All-but-the-Top
> mean-centering correction the weakness paper §10.2 found necessary), i.e. the
> lab's hand-authored category structure is recovered in an embedding family it did
> not build. Block-structure NMI between agglomerative-clustering labels and the
> 6 authored categories ≥ 0.25.
>
> **P3b (paraphrase weakness > wrong-orbit control, externally).** Per-concept
> paraphrase weakness (mean pairwise cosine among a concept's alias/paraphrase
> variants) will exceed the wrong-orbit control (cosine to *other* concepts'
> variants) by **gap ≥ +0.15** after centering — the same directional signal the
> weakness paper found in centered Pythia-70M (§10.2 gap +0.44 to +0.79), now on a
> non-LLM external substrate.
>
> **P3c (cross-model convergence).** The concept×concept cosine *similarity
> matrices* of GloVe-100d and GloVe-300d (independently dimensioned models) will
> agree with **RSA/Spearman ρ ≥ +0.6** on their off-diagonal entries — a minimal
> Platonic-convergence signature across two external models.

## Kill criterion (retracts / weakens the claim)

- **Kills P3a:** within-vs-across-category margin < +0.05 after centering, or NMI <
  0.10 — the authored category geometry does **not** live in an external embedding
  space; it was an artifact of the curated prompt set or of OpenAI's embedder.
- **Kills P3b:** centered paraphrase-weakness gap ≤ +0.05, OR the *raw* (uncentered)
  gap is large but vanishes after the All-but-the-Top correction — the precise
  anisotropy confound the weakness paper flagged (§10.2). Recording this is a
  pre-committed honest-negative, not a silent drop.
- **Kills P3c:** cross-dimension RSA ρ < +0.3 — the two external models do *not*
  converge on relational geometry, weakening the convergence pillar.
- **Multi-word-concept confound:** several concepts are multi-word ("basin of
  attraction"). If results depend entirely on the word-vector pooling rule, we
  flag as method-sensitive (mirrors the paper's per-layer/pooling caveats).

## Strongest old-regime shortcut baseline (should almost work)

**Raw (uncentered) cosine similarity** — it will look *strongly* confirmatory
because GloVe (like all embeddings) is anisotropic and *everything* is positively
cosine-similar. This is the exact trap the weakness paper §10.2 documented
("wrong-orbit control is itself high ~0.86–0.99"). P3 only earns credit if the
signal **survives All-but-the-Top centering** — i.e., the shortcut that "almost
works" is designed to be defeated by the centering control. Secondary shortcut:
**lexical-frequency / string-length similarity** (do co-categorized concepts just
share surface tokens?) — pre-registered as a null control.

## Test recipe (given the constraints)

- **Tier A (offline-now, stdlib only — fully realizable):** This is the **one
  prediction wholly runnable today**, because GloVe vectors are plain text
  (`word value value ...` per line) and all math (mean-centering, cosine,
  agglomerative clustering, RSA Spearman) is implementable in **pure Python
  stdlib** — no numpy. Recipe: (1) when the lab's local GloVe text file is present
  at `references/embeddings/glove.6B.300d.txt` (or any subset vendored as
  `experiments/external_contact/p3_glove_subset.txt` containing only the ~80 word
  types our 24 concepts + paraphrases need — small enough to commit), (2) build
  per-concept vectors by mean-pooling constituent word vectors, (3) apply
  All-but-the-Top (subtract corpus mean, remove top-1 PC via stdlib power
  iteration), (4) compute the P3a/P3b/P3c statistics with the lab's existing
  metrics (RSA, mutual-NN, linear alignment per the synthesis §"Ten Research
  Areas" #1). Add this as a `--external-glove` mode to the existing
  `experiments/concept_geometry/paraphrase_stability_probe.py` so it reuses the
  committed concept/paraphrase JSONs and the audit-card output format. The
  **subset-vendoring** step keeps it fully offline: only the word types we name are
  shipped, raw full embeddings stay out of git (matching the track's
  README discipline: "Raw embeddings stay local").
- **Tier B (fetch-when-unblocked):** fetch the full `glove.6B` and `fastText
  crawl-300d` tables, repeat across both families, and add fastText as a third
  model in the P3c convergence RSA. Optionally `uvx --with sentence-transformers`
  for an open MiniLM sentence-embedder as a fourth external substrate.

## Claim tier a pass earns

**Mechanism → regime transition.** A Tier-A pass (authored category geometry +
paraphrase-weakness gap + cross-model RSA all survive centering on external GloVe)
shows the concept-geometry claim is **not** an artifact of the lab's OpenAI probe
— it lives in an independently-built embedding family. It is *not* a field claim
on its own (static word vectors are a limited substrate; P3c needs ≥ 3 model
families and the LLM-behavioral chain remains open per §10.2/§10.3 of the weakness
paper) — but it is the first concept-geometry result with genuine external contact.

---

## Cross-prediction summary

| # | Pillar | External system | Headline prediction | Hard kill | Strongest shortcut | Best runnable tier | Max claim tier |
|---|---|---|---|---|---|---|---|
| P1 | Weakness→OOD | Pythia suite + public grokking/mod-arith benchmarks | weakness ρ≥+0.5 with OOD, beats loss/scale/L₂/sharpness by ≥0.25 |G| | classical beats / weakness ρ<0.3 | eval loss; param count | A (surrogate) / B (full) | Field claim (Tier B) |
| P2 | Concern / identifiability ceiling | Deep ensembles on CIFAR-10-C; BALD/BatchBALD on MNIST | variance⊥error on shifted slices (|r|≤0.2); uncertainty-acq < value-of-info acq | variance tracks error on shift (|r|≥0.5) | "ensemble variance = epistemic"; "BALD≈optimal" | A (published curves) | Field claim (methodology) |
| P3 | Concept geometry convergence | GloVe `6B` (+ fastText) | category margin ≥+0.10, paraphrase gap ≥+0.15, cross-model RSA ≥+0.6, all post-centering | signal vanishes after All-but-the-Top | raw (anisotropic) cosine | A (full, stdlib) | Mechanism → regime transition |

## Shared anti-cheat discipline (frozen)

Mirroring `papers/*/preregistration.md`:

1. **No-false-calm carries over.** Any "pass" where a headline metric improves but
   its kill-criterion control is not also reported is treated as false calm and
   does not count (cf. metric-stack §2.5).
2. **Wrong-X controls are mandatory.** P1 wrong-group, P2 in-distribution-vs-shift
   split, P3 wrong-orbit + All-but-the-Top — each prediction is only "passed" with
   its control on the correct side.
3. **Frozen-now numbers.** All Tier-A external numbers are transcribed from public
   sources and committed *before* the comparison is computed, so the check cannot
   be retrofit.
4. **Honest-negative is a result.** Per the weakness paper §10.2/§10.3 precedent, a
   latent-signal-without-behavioral-transfer outcome (esp. plausible for P1/P3) is
   recorded as a partial result, never silently dropped.

## Pre-committed continuation

- If **P1 Tier B passes**: this becomes the program's first external field claim;
  promote to a standalone short paper ("Weakness predicts OOD on a model family we
  did not train").
- If **P2 Tier A passes**: write the methodological-transfer note ("the lab's
  anti-cheat gates catch deployed active-learning failures").
- If **P3 Tier A passes**: extend concept-geometry track to ≥3 external embedding
  families and re-open the LLM-behavioral chain that §10.2 left open.
- If any **hard-kills**: record which pillar fails to survive external contact —
  that is itself the most valuable possible finding given the director's critique,
  because it tells the lab exactly which claim was self-built-world-bound.
