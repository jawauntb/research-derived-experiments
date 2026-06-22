# First External Contact: Three Pre-Registered Pillars, One Sharp Result, and the Self-Built-World Problem

**Jawaun Brown**
2026-06-22

## Abstract

The geometric-convergence research program had a defining weakness named explicitly in `docs/phase2_breakthrough_trajectory.md`: every prior result lived on toy worlds the lab built — homeostatic bandits, cyclic-symbol benchmarks, rotated strokes, pixel-rendered parse trees. Three theoretical pillars (weakness→OOD, the concern/identifiability ceiling, cross-substrate concept geometry) had only internal evidence. A hostile reviewer could say each was an artifact of self-built environments.

This paper records what survived the program's first **pre-committed external contact**. Pre-registration `docs/external_contact_preregistration.md` (frozen 2026-06-18) named three predictions about systems the lab did not build: **P1** weakness→OOD on the Pythia model suite; **P2** uncertainty≠error / no-false-calm on Ovadia 2019 + Kirsch 2019; **P3** concept-geometry convergence on the GloVe family. A 2026-06-22 cloud-agent handoff added the pre-registered **P3c-3way amendment** before fastText vectors were fetched — strictly tightening cross-substrate RSA to require the minimum pairwise RSA across three families.

Four frozen result reports cover all four pre-registered tests plus an unfinished P1 LoRA variant. The honest verdict:

- **P2b clean external pass** (5/5 published Kirsch comparisons). BatchBALD strictly beats naive (top-k) BALD on label budget to target accuracy on MNIST and on CINIC-10 transfer. The lab's "current error ≠ value of probing" methodological correction replicates on external curves we did not generate.
- **P3 within-family pass, cross-family partial falsification.** GloVe-300d satisfies all three pre-registered P3 gates (margin 0.106, NMI 0.531, paraphrase gap 0.252). When fastText (independent training corpus) is added, the 3-way minimum pairwise RSA drops to 0.346 — well below the 0.6 threshold. fastText alone fails P3a margin (0.073 < 0.10) but passes NMI and paraphrase gap. The cross-substrate Platonic-convergence reading is NOT warranted by this 3-family panel; the original P3 GloVe result is real but substrate-sensitive.
- **P2a Tier-B partial confirmation, signal- and corruption-dependent.** K=5 small CNNs on CIFAR-10 + 3 sampled Hendrycks corruptions (substrate-faithful via HF parquet + programmatic corruptions; declared deviation due to Modal egress blocks). Predictive entropy correlation with error stays at +0.39 across every shifted slice — entropy does NOT collapse under shift, refuting the literal P2a for entropy. Ensemble variance correlation drops to +0.049 only on heavy defocus_blur and is preserved on brightness + gaussian_noise. The variance of the predicted-class probability flips sign to −0.017 at sev4 defocus — the textbook false-calm signature, on exactly one (corruption, signal) pair. The literal P2a is signal- and corruption-dependent, not the general claim the pre-reg framed.
- **P1 Tier-B (linear-probe variant) degenerate**, not falsified. All 27 cells (3 sizes × 3 n's × 3 seeds) on frozen Pythia hidden states yielded ood_accuracy = 0.0. Linear probing cannot elicit modular-arithmetic generalization from Pythia at any size or n; the head memorizes the partial-orbit training pairs (head_train_acc = 1.0) without extrapolating. The literal P1 threshold is *unevaluable* in this configuration. Honest finding: the runbook's "linear / LoRA head" option needs to be taken with LoRA (or full fine-tune), not linear-only. P1 LoRA Tier-B remains the unfinished test.

**Where the program stands:** one clean external pillar (the methodological correction P2b), one substrate-sensitive within-family pass (P3 GloVe), one substrate-faithful signal- and corruption-dependent partial confirmation (P2a Tier-B variance + blur), one partial falsification of the cross-substrate convergence claim (P3c-3way), and one tooling block (P1 linear-probe). The lab has **escaped the self-built-world problem on exactly one pillar (P2b)** with cleanness comparable to published findings, and is in *partial and substrate-specific* contact with two more (P2a Tier-B; P3 within-family). The high-ceiling external field-claim candidate (P1) is unevaluated.

## 1. Background — the self-built-world problem, frozen on paper

The director-style critique in `docs/phase2_breakthrough_trajectory.md` names the program's defining weakness with no hedge: every prior result lives on simulator-defined toys. Homeostatic bandits, Concerned Shape Grammar, Viable Computational Bodies, rotated MNIST, GloVe-via-OpenAI-API — all environments where the lab chose the substrate AND chose what counted as success. A hostile reviewer can say the three theoretical pillars (weakness→OOD, uncertainty≠error / no-false-calm methodology, cross-substrate concept geometry) are *artifacts* of self-built worlds.

The pre-registration `docs/external_contact_preregistration.md` (frozen 2026-06-18, before any external fetch or compute) fixed this on paper. Three predictions, one per pillar, each about a **named, public, external system**:

| # | Pillar | External system | Headline prediction | Hard kill |
|---|---|---|---|---|
| P1 | Weakness→OOD | Pythia suite + grokking/mod-arith | weakness ρ≥+0.5 with OOD, beats classical predictors by ≥0.25 in |ρ| | classical beats / weakness ρ<0.3 |
| P2 | Uncertainty/identifiability | Deep ensembles on CIFAR-10-C; BALD/BatchBALD on MNIST | variance⊥error on shifted slices (|r|≤0.2); uncertainty-acq < value-of-info acq | variance tracks error on shift (|r|≥0.5) |
| P3 | Concept geometry convergence | GloVe `6B` (+ fastText) | category margin ≥+0.10, paraphrase gap ≥+0.15, cross-model RSA ≥+0.6, all post-centering | signal vanishes after All-but-the-Top |

Each prediction shipped in two runnability tiers — **Tier A** (offline-now stdlib check, frequently against published numbers transcribed before computing) and **Tier B** (fetch-when-unblocked external sweep on Modal). A 2026-06-22 cloud-agent handoff added the pre-registered **P3c-3way amendment**: require the *minimum* pairwise RSA across three external embedding families ≥ 0.6. This strictly tightens the original P3c, which only required GloVe-300d vs GloVe-100d RSA ≥ 0.6 (two dimensionalities of one family).

The shared anti-cheat discipline (frozen with the pre-reg):

1. **No-false-calm**: a "pass" without its kill-criterion control is treated as false calm.
2. **Wrong-X controls mandatory**: P1 wrong-group, P2 in-dist vs shift split, P3 wrong-orbit + All-but-the-Top centering.
3. **Frozen-now numbers**: every Tier-A transcribed public number committed *before* the comparison is computed, so the check cannot be retrofit.
4. **Honest-negative is a result**: latent-signal-without-behavioral-transfer is recorded, never silently dropped.

## 2. Method — four pre-registered tests run honestly

### 2.1 P3 GloVe (Tier A, stdlib, fully runnable)

`experiments/external_contact/p3_glove_probe.py` is a pure-stdlib harness. `--self-test` runs on synthetic vectors with planted block structure (math validation only; NOT a result). `--glove` runs the real external test against the public GloVe vectors. Mean-pool concept labels and paraphrases, apply All-but-the-Top centering (Mu et al. 2018 via stdlib power iteration), compute the within-vs-across-category cosine margin (P3a), agglomerative-clustering NMI vs authored categories (P3a), paraphrase-vs-wrong-orbit cosine gap (P3b), and cross-model Spearman RSA on the off-diagonal cosine matrices (P3c).

For the P3c-3way amendment, the harness was extended to accept `--glove3` and a `--label3` (3-family panel mode), computing all pairwise RSAs and applying the strict `min pairwise RSA ≥ 0.6` rule when ≥ 3 families are present. `scripts/fetch_fasttext_subset.py` mirrors the GloVe fetcher: downloads the `wiki-news-300d-1M` zip (~650 MB) and vendors only the ~400-word subset the 24-concept set + paraphrases need (raw embeddings stay local per the existing track policy).

### 2.2 P2 Tier A (transcription against published curves)

`experiments/external_contact/p2_uncertainty_public.csv` is a frozen-now transcribed CSV from two sources, committed before the check ran:

- **Ovadia et al. 2019, "Can You Trust Your Model's Uncertainty?" Table G.1** — Brier / NLL / ECE quartile aggregates across 80 shifted CIFAR-10 variants for 7 uncertainty methods.
- **Kirsch et al. 2019, "BatchBALD" Table 1 + §4** — MNIST labels-to-target-accuracy and CINIC-10 transfer for BatchBALD vs naive BALD vs Gal et al. 2017 BALD.

Each row carries source citation + table/figure reference. `experiments/external_contact/p2_uncertainty_check.py` consumes the CSV (stdlib, `csv` module) and computes (P2a-aggregate) ensemble ECE q75/q25 ratio per method, and (P2b) labels-to-target paired comparisons (BatchBALD vs naive).

The harness flags **up front** that the literal P2a (per-sample Pearson r between ensemble variance and 0/1 error on shifted CIFAR-10-C slices, |r|≤0.2) is *not checkable* against Ovadia Table G.1 — quartile aggregates across all corruption variants are published but per-corruption-severity per-sample correlations exist only in figures. Honest constraint, declared without rewriting the threshold.

### 2.3 P3c-3way (cross-family fastText addendum, locally)

`scripts/fetch_fasttext_subset.py --run` invokes the P3 harness with `--glove`, `--glove2`, `--glove3`. The 3-way amendment requires the minimum pairwise RSA across the GloVe-300d, GloVe-100d, fastText-300d panel ≥ 0.6 on the 23 concepts shared by all three families (fastText covers `autopoiesis` which GloVe missed; the 23-concept intersection is the strictest common substrate).

### 2.4 P2 Tier B (deep ensembles on CIFAR-10 + Hendrycks corruptions, Modal)

`experiments/external_contact/modal_p2_ensembles_cifar10c.py`. Single Modal A10G worker; K=5 small CNNs (~140k params each, identical architecture) trained on CIFAR-10 from different seeds (Adam lr=1e-3, 10 epochs; member train accuracies 0.644–0.657, under-trained on purpose — the lab's claim is about epistemic uncertainty at a regime boundary, not state-of-the-art accuracy). For each (corruption × severity), evaluate 2000 samples and compute three per-sample uncertainty signals: predictive entropy of the mean softmax, ensemble variance of the predicted-class probability, ensemble variance summed over classes — and Pearson r vs 0/1 error.

**Methodology deviation, declared up front**: the pre-reg named the Hendrycks Zenodo .npy CIFAR-10-C files. Modal egress to `www.cs.toronto.edu` and `zenodo.org` both sustain ~60 KB/s from inside Modal containers and at image-build time (verified twice: torchvision's CIFAR-10 downloader stuck at 25 % after 15+ min in the function; image-builder curl stuck on the same path with no progress for 30+ min). Rather than block on Modal networking, this run uses:

- **CIFAR-10** loaded from the HuggingFace `uoft-cs/cifar10` parquet mirror (~60 MB; same substrate as Hendrycks's base CIFAR-10), cached on a persistent Modal Volume.
- **Hendrycks corruption recipes** applied programmatically at runtime using the published severity parameters (Gaussian noise σ ∈ {0.04, 0.06, 0.08, 0.09, 0.10}; shot-noise Poisson λ ∈ {60, 25, 12, 5, 3}; brightness offset ∈ {0.05, 0.10, 0.15, 0.20, 0.30}; contrast scale ∈ {0.75, 0.5, 0.4, 0.3, 0.15}; defocus-blur Gaussian σ ∈ {0.3, 0.4, 0.5, 1.0, 1.5}). The corruption RECIPES are external (from Hendrycks's appendix B); only the application is reproduced here.

Substrate-faithful, not substrate-equivalent. A reviewer who insists on bit-identical CIFAR-10-C arrays can re-run on the Zenodo .npy once the egress path is fixed. The result report `p2_tier_b_2026_06_22.md` flags this in section 1.

### 2.5 P1 Tier B (Pythia weakness→OOD, linear-probe variant, Modal)

`experiments/external_contact/modal_p1_pythia_weakness.py`. Sharded by Pythia size (3 workers in parallel; pythia-70m / 160m / 410m). Each worker loads its model once and runs all (n ∈ {13, 17, 23}) × 3 seeds = 9 cells. Linear-probe head on the last-token hidden state of frozen Pythia, trained on a strict-subset partial orbit (train_frac = 0.5, 400 epochs). Extract argmax function table over the full domain; compute weakness_oracle_norm under Z_n (equivariance count, re-implementing `experiments/symbolic_weakness/selectors.py` inline for the self-contained Modal worker), wrong-group null, and the classical predictor stack (head train loss, eval NLL on OOD, Pythia param count, Pythia L₂, Hutchinson sharpness on the head loss).

This is the **runbook's "linear / LoRA head" option taken with the LINEAR variant**; the LoRA variant is the unfinished follow-up.

## 3. Results — what survived first contact, per pillar

### 3.1 P3 (concept-geometry convergence)

The two frozen P3 result reports — `p3_glove_2026_06_22.md` and `p3_three_family_2026_06_22.md` — together establish:

**P3 GloVe (within-family, 23/24 concepts; `autopoiesis` absent from GloVe):**

| Gate | Threshold | Centered | Raw | Verdict |
|---|---:|---:|---:|---|
| P3a within-across margin | ≥ 0.10 | **0.106** | 0.061 | PASS |
| P3a clustering NMI | ≥ 0.25 | **0.531** | — | PASS |
| P3b paraphrase gap | ≥ 0.15 | **0.252** | 0.072 | PASS |
| P3c-2way RSA (GloVe-300d vs GloVe-100d) | ≥ 0.60 | **0.747** | — | PASS |

The strongest old-regime shortcut (raw uncentered cosine) did NOT carry the result — raw margin 0.061 and raw gap 0.072 both fail. The signal *strengthens* after All-but-the-Top centering. The lab's authored category structure lives in an embedding family the lab did not build.

**P3c-3way (cross-family, with fastText added; pre-registered before vectors were fetched):**

| Pair | RSA | Notes |
|---|---:|---|
| GloVe-300d vs GloVe-100d | **0.747** | within-family, two dimensionalities |
| GloVe-300d vs fastText-300d | 0.543 | cross-family, same dim, different corpus |
| GloVe-100d vs fastText-300d | **0.346** | cross-family, different dim, different corpus |
| min pairwise RSA | **0.346** | P3c-3way pass threshold 0.60 → **FAIL** |

**fastText alone (P3a / P3b probe on all 24 concepts):**

| Gate | Threshold | Centered | Raw | Verdict |
|---|---:|---:|---:|---|
| P3a within-across margin | ≥ 0.10 | **0.073** | 0.041 | **FAIL** (below by 0.027) |
| P3a clustering NMI | ≥ 0.25 | 0.539 | — | PASS |
| P3b paraphrase gap | ≥ 0.15 | 0.260 | 0.042 | PASS |

**Reading.** The GloVe within-family P3 result is real. Within-family RSA across two GloVe dimensionalities (0.747) is high; that signal does NOT generalize to cross-family RSA against an independently-trained embedding family (0.346, 0.543). The cross-substrate Platonic-convergence reading suggested by the original P3 was largely a within-family effect.

What survived: the categorical block structure exists on a second non-lab family (fastText NMI 0.539, paraphrase gap 0.260). The per-pair within-across margin does not generalize to fastText (margin 0.073 < 0.10).

The pre-reg's allowed claim "mechanism → regime transition" narrows to **regime transition / partial external load-bearing, substrate-sensitive**. The clean version of the field claim — "the lab's authored concept geometry is a substrate-independent Platonic-convergent structure" — does NOT survive a third independent family.

### 3.2 P2 Tier A (transcription against Ovadia + Kirsch)

`p2_uncertainty_2026_06_22.md`:

**P2b — BatchBALD vs naive BALD (Kirsch 2019 Table 1 + §4):**

| Comparison | BatchBALD labels | Naive labels | Gap | Verdict |
|---|---:|---:|---:|---|
| MNIST 90 % acc, vs BALD reimpl | 90 | 120 | 30 (25 %) | PASS |
| MNIST 90 % acc, vs BALD (Gal 2017) | 90 | 145 | 55 (38 %) | PASS |
| MNIST 95 % acc, vs BALD reimpl | 200 | 250 | 50 (20 %) | PASS |
| MNIST 95 % acc, vs BALD (Gal 2017) | 200 | 335 | 135 (40 %) | PASS |
| CINIC-10 59 % acc transfer, vs BALD median | 1170 | 1330 | 160 (12 %) | PASS |

**5/5 published comparisons fall on the predicted side.** The lab's "current error ≠ value of probing" / no-false-calm correction (Paper 22's 5× value-of-information finding) replicates on external curves. Magnitude is milder on Kirsch's MNIST (20-40 % label efficiency) than on the lab's bandit (5×), but the direction is unambiguous.

**P2a aggregate (Ovadia Table G.1 ECE q75/q25 across 80 shifted CIFAR-10 variants × 7 methods):**

| Method | ECE q25 | ECE q50 | ECE q75 | q75/q25 |
|---|---:|---:|---:|---:|
| dropout | **0.021** | **0.034** | 0.174 | 8.29× |
| temp_scaling | 0.022 | 0.049 | 0.180 | 8.18× |
| svi | 0.029 | 0.064 | 0.187 | 6.45× |
| ensembles | 0.031 | 0.037 | **0.110** | 3.55× |
| vanilla | 0.057 | 0.127 | 0.288 | 5.05× |
| ll_svi | 0.058 | 0.135 | 0.275 | 4.74× |
| ll_dropout | 0.069 | 0.136 | 0.292 | 4.23× |

Every method's ECE rises sharply under shift; even the best-calibrated method on shifted CIFAR-10-C (deep ensembles at q75 = 0.110) is ~3.5× its near-in-dist value (q25 = 0.031). Aggregate signature of "uncertainty stops tracking error under shift" — published, consistent with the lab's prediction.

**P2a literal (per-sample Pearson r per severity)**: NOT checkable against published tables (per-severity per-sample correlations exist only in figures). Recorded as UNDECIDED; Tier B required.

Two honest observations the P2 Tier A report flags: (1) ensembles are NOT the lowest-ECE method at q25 / q50 — *MC dropout* is — ensembles only dominate at q75. (2) The aggregate ECE-collapse signature is a known published Ovadia headline, so P2a-aggregate *confirms* rather than *predicts* the lab's correction.

Allowed claim from Tier A: **regime transition / methodology external load-bearing (partial)** — NOT the field-claim-methodology tier the pre-reg conditionally allowed, because P2a literal is undecided.

### 3.3 P2 Tier B (this paper's deepest result)

`p2_tier_b_2026_06_22.md`. 15 slices: in-dist + 3 corruptions × 5 severities, 2000 samples each.

| slice | acc | pearson(ent, err) | pearson(var_pred_class, err) | pearson(var_total, err) |
|---|---:|---:|---:|---:|
| sev0_in_dist                | **0.679** | **+0.436** | **+0.190** | **+0.265** |
| sev1_brightness             | 0.680     | +0.428     | +0.173     | +0.248     |
| sev1_defocus_blur           | 0.679     | +0.435     | +0.192     | +0.267     |
| sev1_gaussian_noise         | 0.641     | +0.443     | +0.156     | +0.245     |
| sev2_brightness             | 0.672     | +0.429     | +0.161     | +0.239     |
| sev2_defocus_blur           | 0.671     | +0.438     | +0.172     | +0.257     |
| sev2_gaussian_noise         | 0.576     | +0.437     | +0.171     | +0.239     |
| sev3_brightness             | 0.652     | +0.431     | +0.179     | +0.261     |
| sev3_defocus_blur           | 0.620     | +0.439     | +0.097     | +0.206     |
| sev3_gaussian_noise         | 0.493     | +0.424     | +0.180     | +0.227     |
| sev4_brightness             | 0.627     | +0.428     | +0.188     | +0.271     |
| sev4_defocus_blur           | **0.340** | +0.384     | **−0.017** | **+0.049** |
| sev4_gaussian_noise         | 0.461     | +0.407     | +0.178     | +0.199     |
| sev5_brightness             | 0.565     | +0.398     | +0.117     | +0.203     |
| sev5_defocus_blur           | **0.273** | +0.351     | +0.053     | **+0.090** |
| sev5_gaussian_noise         | 0.418     | +0.378     | +0.205     | +0.228     |

Three findings, three sub-claim verdicts:

1. **Entropy is NOT a false-calm signal here.** Predictive entropy of the mean softmax stays at +0.40 ± 0.03 across every slice from in-dist to sev5. Entropy keeps tracking error even when accuracy halves. Literal P2a (|r| ≤ 0.2) is **refuted for entropy**.
2. **Ensemble variance DOES collapse — but only on blur-type shift.** `pearson(var_total, error)` drops from +0.265 in-dist to +0.049 at sev4 defocus_blur and +0.090 at sev5 defocus_blur, comfortably below the P2a threshold. But on brightness and gaussian_noise, variance-error correlation stays at +0.20-0.27 at *every* severity. Literal P2a **passes on (variance, defocus_blur), refuted on (variance, brightness) and (variance, gaussian_noise)**.
3. **The predicted-class variance flips sign on heavy defocus.** `pearson(var_pred_class, error)` at sev4 defocus_blur is **−0.017** — the textbook false-calm signature (variance anti-correlated with error: when wrong, confidently wrong). Accuracy on that slice drops to 0.340, half the in-dist 0.679. This is a clean, sharp instance of the lab's predicted regime — on exactly one (corruption, signal) pair.

**The lab's "uncertainty ≠ error" claim is signal-dependent and corruption-type-dependent.** The general claim does not transfer; a sharper version — *"ensemble variance (not entropy) decouples from error on blur-class shift (not noise/brightness)"* — does. This is a sharper refinement of P2a than the original P2a was itself.

### 3.4 P1 Tier B (linear-probe variant, degenerate)

`p1_pythia_2026_06_22.md`. 27 cells (3 sizes × 3 n's × 3 seeds) on frozen Pythia hidden states. Every cell yielded ood_accuracy = 0.0. The head trained to 100 % accuracy on its partial orbit and produced noise on OOD inputs. All Spearman ρ values collapsed mechanically to 0.0 because the dependent variable was constant.

Distribution of weakness_oracle_norm across cells: 9 × 0.077 (n=13), 9 × 0.059 (n=17), 9 × 0.043 (n=23) — equal to 1/n at each n (only the identity element of Z_n maps the function table to itself).

**This is not a falsification of weakness→OOD; it is methodology degeneration.** Frozen-Pythia + linear-probe is too constrained to elicit a learned modular-arithmetic function. The runbook offered linear OR LoRA; this run took linear. P1 LoRA remains the unfinished test — and is the program's strongest remaining external field-claim candidate.

The 27-cell pattern is informative in one direction: **scale alone does NOT help** (pythia-70m → 410m all 0.0 OOD), so the parameter-count baseline P1 had to beat is also dead in this configuration. But the literal P1 weakness claim cannot be evaluated here.

## 4. The sharpened claims

What the program can ship after this contact:

1. **The methodological correction "current error ≠ value of probing" transfers externally** (P2b clean, 5/5 published Kirsch comparisons). This is the program's first external load-bearing field claim and is comparable in cleanness to published findings.

2. **Ensemble variance, not predictive entropy, exhibits the lab's predicted false-calm signature — and only on blur-class shift** (P2a Tier B, sev4 defocus var_pred_class = −0.017 on accuracy 0.340). The original P2a's general claim does not transfer; this sharper sub-claim does.

3. **The lab's authored concept geometry survives external contact on one embedding family (GloVe)** and partially on a second (fastText preserves NMI 0.539 and paraphrase gap 0.260 but fails the per-pair margin 0.073 < 0.10). **Cross-substrate convergence across independent training corpora is not warranted** by the 3-family panel (min RSA 0.346).

4. **The aggregate "uncertainty calibration collapses under shift" is real and replicates** (Ovadia ECE q75/q25 = 3.55× even for the best uncertainty method) — but this is a published field finding, so it *confirms*, not *predicts*, the lab's correction.

## 5. What was falsified or narrowed

The honest negative list — the lab's program *does* not get to claim these any more, given the data in hand:

1. **"The lab's authored concept geometry is a substrate-independent Platonic-convergent structure across embedding families."** P3c-3way min RSA 0.346 falsifies the cross-substrate reading; fastText's P3a margin 0.073 falsifies the per-pair within-across signal on a second family.

2. **"Same-class uncertainty (general) is not a reliable epistemic signal at shifted regime boundaries."** Entropy correlation stays at +0.39 across all severities and corruption types; entropy *is* a reliable signal in this Tier-B configuration. The claim narrows to ensemble variance (not all uncertainty signals) and to blur-class shift (not general shift).

3. **"Pythia linear-probe arithmetic generalization is informative about weakness."** It is not — the setup degenerates uniformly at 0.0 OOD accuracy.

These are not painful retractions; they are *narrowing*. The lab is in stronger evidential standing for the sharper sub-claims that *did* survive than it was in for the broader claims before.

## 6. Discovery-EWS instrument issue

A meta-observation surfaced repeatedly across the four result reports: the v1 `discovery_ews` rubric (regex over markdown) consistently flips the `external_contact` family verdict from `load_bearing` to `self_sealing` after each new honest-result report lands, because the lab's *positive-discipline* audit convention ("Rejected alternatives:", "is rejected by …", "the claim narrows to …") trips the FAILURE regex's `\brejected\b` and the literal "fail" / "refuted" tokens used in honest sub-claim verdicts.

This has happened three times in three days (P2 Tier A, P3c-3way, P2 Tier B; the P1 inconclusive added it a fourth time). Per the same discipline that the EWS exists to enforce, **the rubric is left alone**; retuning the regex to flip the verdict after the fact would be exactly the metric-overfit the EWS exists to detect. The structured-provenance v2 rewrite — have experiments emit gate verdicts + claim tier as JSON, score resolution from those records — remains the correct fix and is in the program's TODO under `Discovery-EWS v2`.

The empirical conversion rate at this writing is 0.115 across 152 artifacts (17 of 152 → load-bearing under v1). This number is now load-bearing only as an audit-detector, not as a substantive program-health metric, until v2 lands.

## 7. Next operations

The cleanest follow-ups, ordered by ratio of expected value to required effort:

1. **P1 LoRA Tier B** (Modal, ~30-60 min, ~$3-5). Rank-8 LoRA on the attention + MLP projections of the last 2 Pythia layers, plus the Linear classification head over n classes. This is the only operationalization of the runbook §P1 that gives the model a chance to actually learn the modular-shift function and produce within-sweep OOD variance for the weakness statistic to correlate against. Highest remaining ceiling for an external field claim.

2. **P2 Tier B corruption-set extension** (Modal, ~20 min). Implement the remaining 10 Hendrycks corruption types beyond `defocus_blur` / `brightness` / `gaussian_noise` and the two sampled-but-unimplemented ones (`shot_noise`, `contrast`). Question: does the blur-pattern collapse generalize within all blur-class corruptions (`glass_blur`, `motion_blur`, `zoom_blur`)? If yes, the (variance, blur) sharper claim hardens; if no, defocus_blur is special.

3. **Discovery-EWS v2** (local, stdlib). Structured provenance: have each `papers/*/preregistration.md` and result `experiments/*/results/*.md` emit a JSON sidecar with gate verdicts + claim tier; score family resolution from those records, not regex over prose. This removes the regex apophenia and replaces the v1 conversion rate (currently mis-firing on positive-discipline language) with an auditable metric.

4. **P3 fourth-family extension** (local, ~10 min). Add a public open-weights sentence embedder (e.g. MiniLM-L6-v2 from HF) as a fourth external family. Question: does cross-substrate RSA recover when going from static word vectors to contextual / sentence embeddings, or does the fastText partial-falsification generalize? This sharpens the P3c-3way narrowing toward either "static word-vector substrates don't converge across corpora" (specific narrowing) or "the lab's concept geometry isn't substrate-independent at all" (broader narrowing).

5. **Re-run P2 Tier B on bit-identical Zenodo CIFAR-10-C** once the Modal egress path is fixed (Volume populated from outside Modal, or alternative mirror identified). Substrate-equivalent confirmation of the variance + defocus_blur false-calm signature.

## 8. References

External pre-registered systems referenced (none built by this lab):

- Pennington, Socher & Manning 2014, **GloVe**. Stanford `glove.6B` (Wikipedia + Gigaword). Used in P3.
- Bojanowski et al. 2017, **fastText**. `wiki-news-300d-1M` from `dl.fbaipublicfiles.com`. Used in P3c-3way.
- Lakshminarayanan et al. 2017, **Deep Ensembles**. Used in P2.
- Hendrycks & Dietterich 2019, **CIFAR-10-C** (arXiv:1903.12261). Corruption recipes used in P2 Tier B.
- Ovadia et al. 2019, **Can You Trust Your Model's Uncertainty?** (arXiv:1906.02530). Table G.1 transcribed for P2 Tier A.
- Kirsch et al. 2019, **BatchBALD** (arXiv:1906.08158). Table 1 + §4 transcribed for P2 Tier A.
- Biderman et al. 2023, **Pythia**. EleutherAI `pythia-70m` / `-160m` / `-410m` from HuggingFace. Used in P1.
- Mu et al. 2018, **All-but-the-Top**. Anisotropy correction used in P3.
- Huh et al. 2024, **Platonic Representation Hypothesis**. Pre-reg framing for P3c convergence claim.

Internal artifacts:

- `docs/external_contact_preregistration.md` — pre-registration frozen 2026-06-18.
- `docs/external_contact_runbook.md` — Tier-A / Tier-B recipes.
- `experiments/external_contact/results/p3_glove_2026_06_22.md` — P3 GloVe within-family pass.
- `experiments/external_contact/results/p3_three_family_2026_06_22.md` — P3c-3way partial falsification.
- `experiments/external_contact/results/p2_uncertainty_2026_06_22.md` — P2 Tier A partial pass.
- `experiments/external_contact/results/p2_tier_b_2026_06_22.md` — P2 Tier B signal- and corruption-dependent partial confirmation.
- `experiments/external_contact/results/p1_pythia_2026_06_22.md` — P1 linear-probe Tier B inconclusive.
