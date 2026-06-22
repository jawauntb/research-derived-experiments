# External Contact P2 — Uncertainty != Error on Published Ensemble / BALD Curves

Date: 2026-06-22
Code: `experiments/external_contact/p2_uncertainty_check.py`
Pre-registration: `docs/external_contact_preregistration.md` (Prediction 2, frozen 2026-06-18)
Runbook: `docs/external_contact_runbook.md` (§P2)
Frozen CSV: `experiments/external_contact/p2_uncertainty_public.csv` (committed at `0579cdf` BEFORE the check ran)
Artifact: `artifacts/external_contact/p2_uncertainty.json` (gitignored)
Sources:

- Ovadia et al. 2019, "Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift." arXiv:1906.02530. Table G.1 — CIFAR-10 corrupted, quartile aggregates across 80 shifted variants × 7 uncertainty methods.
- Kirsch et al. 2019, "BatchBALD: Efficient and Diverse Batch Acquisition for Deep Bayesian Active Learning." arXiv:1906.08158. Table 1 (MNIST labels-to-target-accuracy) + Section 4 (CINIC-10 transfer).

## Question

Do two of the metric-stack's load-bearing methodological corrections — "uncertainty is not error" on the shifted regime (Correction 4.3) and the "current error != value of probing" / no-false-calm gate (Correction 4.6) — survive contact with **external uncertainty / active-learning systems the lab did not build**?

## Commands

```bash
# Math sanity (synthetic; NOT a result):
python3 -m experiments.external_contact.p2_uncertainty_check --self-test

# Real Tier-A external check (CSV was frozen and committed BEFORE this ran):
python3 -m experiments.external_contact.p2_uncertainty_check \
    --csv experiments/external_contact/p2_uncertainty_public.csv \
    --out artifacts/external_contact/p2_uncertainty.json
```

## Result

| Gate | Pre-registered threshold | Tier-A status | Verdict |
|---|---|---|---|
| **P2a literal** (per-sample Pearson \|r\| between ensemble variance and error on shifted CIFAR-10-C slices ≤ 0.2; positive in-distribution) | \|r\| ≤ 0.2 on shifted slices | **Not checkable against published tables** | UNDECIDED — Tier-B required |
| **P2a aggregate proxy** (added in this run, not a post-hoc threshold redefinition for the literal claim) | Ensemble ECE q75/q25 ≥ 2.0 AND q75 ≥ 0.05 across shifted CIFAR-10-C variants | Ensemble ECE q25/q50/q75 = 0.031 / 0.037 / **0.110**; ratio **3.55×** | PASS |
| **P2b** (BatchBALD strictly beats naive top-k BALD on label budget to target accuracy) | All transcribed comparisons | **5/5 comparisons**; BatchBALD wins by 20–40% labels on MNIST, 12% on CINIC-10 | PASS |

### P2a — aggregate ECE under shift (all 7 methods, Ovadia Table G.1)

| Method | ECE q25 | ECE q50 | ECE q75 | q75/q25 ratio |
|---|---:|---:|---:|---:|
| dropout | **0.021** | **0.034** | 0.174 | 8.29× |
| temp_scaling | 0.022 | 0.049 | 0.180 | 8.18× |
| svi | 0.029 | 0.064 | 0.187 | 6.45× |
| ensembles | 0.031 | 0.037 | **0.110** | **3.55×** |
| vanilla | 0.057 | 0.127 | 0.288 | 5.05× |
| ll_svi | 0.058 | 0.135 | 0.275 | 4.74× |
| ll_dropout | 0.069 | 0.136 | 0.292 | 4.23× |

Bolded cells mark the lowest-ECE method per column. Two honest observations:

1. **Every method's ECE rises sharply under shift.** Even the *best-calibrated method on shifted CIFAR-10-C* (deep ensembles at q75) has ECE ≈ 0.110, about 3.5× its near-in-distribution value (q25 = 0.031). Across all seven methods, the 75th-vs-25th percentile spread is 2.4–8.3× on Brier and 3.6–8.3× on ECE. This is the aggregate signature of "uncertainty stops tracking error under shift" the lab's metric-stack predicts.
2. **Ensembles are NOT uniformly the lowest-ECE method.** At q25 and q50, *MC dropout* has lower ECE than ensembles (0.021 vs 0.031; 0.034 vs 0.037). Ensembles dominate only at q75 (0.110 vs 0.174 for dropout, the next best). This is consistent with the lab's stronger claim that the *identity* of the best uncertainty estimator depends on the regime — a corollary of "same-class uncertainty is not epistemic in general" — but it is not a finding pre-registered in P2a.

### P2b — BatchBALD vs naive BALD on Kirsch Table 1

| Comparison | BatchBALD labels | Naive labels | Gap (labels) | Gap (fraction) | Verdict |
|---|---:|---:|---:|---:|---|
| MNIST 90% acc, vs BALD reimpl | 90 | 120 | 30 | 0.250 | BatchBALD wins |
| MNIST 90% acc, vs BALD (Gal 2017) | 90 | 145 | 55 | 0.379 | BatchBALD wins |
| MNIST 95% acc, vs BALD reimpl | 200 | 250 | 50 | 0.200 | BatchBALD wins |
| MNIST 95% acc, vs BALD (Gal 2017) | 200 | 335 | 135 | 0.403 | BatchBALD wins |
| CINIC-10 59% acc (transfer), vs BALD median | 1170 | 1330 | 160 | 0.120 | BatchBALD wins |

All five published comparisons fall on the predicted side. The 5×-style "current error != value of probing" effect Correction 4.6 named — diversity-aware acquisition strictly beats single-point uncertainty — reproduces on external curves the lab did not generate. Magnitude here is 12–40% label efficiency rather than 5× (a milder external regime than the lab's homeostatic bandit), but the direction is unambiguous.

## Honest constraint on P2a (NOT a quiet rewrite)

Ovadia Table G.1 reports quartile aggregates across all 80 shifted CIFAR-10-C variants (4 corruptions × 5 severities ≈ 20 corruption types × 5 severities × multiple seeds, condensed to 25th / 50th / 75th percentiles per uncertainty method × metric). It does **not** publish per-corruption-severity tables, and the per-sample Pearson r between variance and error per severity exists only in figure form in the paper, not in any transcribable table. The literal P2a threshold (`|r| ≤ 0.2 on shifted slices, > 0 in-distribution`) is therefore **undecided** by Tier-A transcription. Tier-B — running deep ensembles on CIFAR-10-C ourselves on Modal and computing per-sample Pearson r per severity — is required to evaluate it.

The aggregate-proxy threshold reported above was added in this run and is **declared as such**; it is not retro-fitted to the literal P2a phrasing. The 75th-vs-25th percentile ECE ratio captures only the *aggregate* "calibration collapses under shift" signature; a model whose uncertainty preserves rank-correlation with error while shifting in absolute level could pass the literal P2a and fail the aggregate proxy, or vice versa.

## Interpretation — Allowed claim

**Regime transition / methodology external load-bearing (partial).** Two consequences:

1. **P2b is a clean Tier-A external pass.** The methodological correction "uncertainty-based active acquisition underperforms diversity / value-of-information acquisition" replicates on external published Kirsch curves on a non-lab benchmark with a non-lab algorithm. This is the program's second external load-bearing episode (after P3 GloVe). The directional claim survives without invoking lab-internal data.
2. **P2a is split.** The aggregate-proxy half passes — published Ovadia numbers confirm calibration collapses under shift for every uncertainty method including deep ensembles, which is consistent with the lab's prediction. But the literal P2a (per-sample variance-error decorrelation) requires Tier-B to evaluate, and the aggregate ECE-collapse signal is also a *known published field finding* (the headline of Ovadia 2019). So the lab's methodological correction is *compatible with* the literature — it isn't a new external prediction we got right that the field hadn't already established. That's an honest weakening.

The published-finding overlap on P2a-aggregate matters for the claim ladder: P2b transports a directional prediction (the lab predicted it would replicate, and it did, on systems we didn't pick); P2a-aggregate restates a finding already canonical in the field. P2a-literal — the actually-novel-for-this-program piece — remains to be tested.

**This does NOT escalate to "field claim about methodology" as the pre-registration tentatively allowed.** The pre-reg's tier was conditioned on the comparisons being computable; with P2a-literal undecided, the honest tier is *regime transition*, not *field claim*. Promotion to field-claim methodology awaits Tier-B Modal runs.

## Discovery-Regime Audit

- **Old regime:** the lab's two methodological corrections (uncertainty ≠ error in the shifted regime; current-error != value-of-probing) had only lab-internal evidence — homeostatic-bandit Paper 14b (variance-error decoupling at E=0.5) and Paper 22's 5× value-of-information finding.
- **Transition:** the same frozen pre-registered directional claims were checked against published Ovadia 2019 (CIFAR-10-C ensemble calibration under shift) and Kirsch 2019 (BatchBALD vs naive BALD label efficiency) — two external systems, neither built by the lab.
- **Transported evidence:** P2a aggregate-proxy and P2b thresholds, all the per-row source citations + table references in the CSV, the anti-cheat ordering (CSV frozen and committed before the check ran, anti-cheat discipline #3).
- **Rejected alternatives:** "ensemble variance is a good epistemic uncertainty estimator on shifted data" is rejected by the ECE-q75 = 0.110 number for ensembles (calibration collapses under heavy shift). "BALD acquisition matches a value-of-information oracle within noise" is rejected by the 20–40% label-efficiency gap to BatchBALD on every transcribed comparison.
- **Residual finding:** P2b strict external replication; P2a aggregate-only confirmation, literal threshold undecided.
- **Honest weakness:** P2a-aggregate restates a known Ovadia headline rather than predicting it ahead of the data; P2a-literal awaits Tier-B; only one BALD paper transcribed (Kirsch) rather than ≥ 2 independent active-learning works.
- **Readiness:** P2b PASS, P2a aggregate PASS, P2a literal UNDECIDED.
- **Allowed claim:** **regime transition / methodology external load-bearing (partial)** — explicitly NOT the "field claim about methodology" tier the prereg conditionally allowed, because P2a-literal is not yet checked.
- **Next operation:** (1) Tier-B P2a — deep ensembles on CIFAR-10-C on **Modal**, computing per-sample Pearson r per severity; (2) optional: transcribe a second active-learning benchmark (e.g., Beluch et al. 2018 power of ensembles in active learning, or Gal+Islam+Ghahramani 2017) to broaden P2b beyond a single source.

## Note on the discovery_ews v1 verdict for this episode

Re-running `discovery_ews` after this report lands shifts the **external_contact** family verdict from `load_bearing` (with P3 only) to `self_sealing` (with P3 + P2). The mechanical cause: this report's "Rejected alternatives" audit-section header and "is rejected by …" passages contribute 3 hits to the v1 FAILURE regex (`\brejected\b`), and the P3 report contributes 2 hits ("Rejected alternatives", "did not pass"). With `failure_hits = 5 >= max(3, transfer_hits + gate_pass_hits) = max(3, 2 + 3) = 5`, v1 marks the family failure-dominated and the verdict falls through to `self_sealing`.

This is a **known v1 rubric limitation**, not a substantive failure: the "Rejected alternatives" section is the lab's *positive*-discipline audit convention (alternative hypotheses considered and ruled out by the data), and the lab's evaluator currently reads it as the *negative* "the result was rejected". The cloud agent already fixed v1's self-reference loop (commit `cade28d`); this "positive-rejected" false-positive is a separate manifestation of the same apophenia and is precisely what the proposed **v2 structured-provenance rewrite** (gates + claim tier emitted as JSON, scored from records rather than markdown regex) is designed to remove (cf. `docs/handoff_2026_06_22.md` §2 "Discovery-EWS v2"). Per the lab discipline ("do NOT over-fit metrics/rubrics to answers you already know"), the FAILURE regex is left alone for this run — retuning it to flip the verdict would be the exact metric-gaming the discovery-EWS exists to detect. Headline conversion rate after this episode: **0.115** (17/148 across the program; from 0.135 / 7/52 in the cloud agent's post-decontamination scan, with the additional rows from this PR contributing more episodes than load-bearing resolutions under the current rubric).
