# Wave 1b — Provenance skeleton

This file is a **skeleton**. It is populated by the Wave 1b
confirmatory Modal run and is the sole channel through which TBD
numeric and hash values become authoritative. Manual edits to numeric
or hash fields are forbidden.

## 1. Attribution

- **Human director:** Jawaun Brown
- **Wave:** 1b (COGR-E2b crossed learned-geometry confirmatory)
- **Package:** `experiments/concern_gated_retrieval_e2/wave1b/`
- **Predecessors (imported, never edited):** `wave0/`, `wave1a/`
- **Producing agent identity:** Claude Code (Opus 4.7) directed by human `Jawaun Brown`
- **Producing agent session ref:** `session_01XMVYi59Z5dSz2oTKd78A4b`

## 2. Preregistration binding

- **Preregistration path:** `experiments/concern_gated_retrieval_e2/wave1b/PREREGISTRATION.md`
- **Preregistration digest (SHA-256):** e4096949c837fe67ff20d8e381d014535c5fdd538be5dd56c87cb51542e81dba
- **Promotion contract L1 path:** `experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L1.md`
- **Promotion contract L1 digest (SHA-256):** 780f4d570240afebc76e9f38a040b070f876b52b54d2da8d9a93dbdd2d529b06
- **Promotion contract L2 path:** `experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L2.md`
- **Promotion contract L2 digest (SHA-256):** 72bb03bb183d250768cd047b30c8a2a8fa3bc7139de4b029e893e4e22006f826
- **Wave 0 hash reference (byte-for-byte with `../wave0/PROVENANCE.md` §6):** `9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23`
- **Wave 1a hash reference (byte-for-byte with `../wave1a/PROVENANCE.md` §6):** `c23b31d977d7c169d57ca12cdfdbc8ad3a59188542efbdf802e341b1c8937209`
- **Signature status:** signed 2026-07-24 (L1 KILL, L2 WITHHELD; every scored gate produced a receipt).

## 3. Confirmatory Modal run

- **Run kind:** `confirmatory`
- **Run label:** cogr_e2_wave1b_confirmatory_2026_07_24
- **Modal app:** `research-derived-cogr-wave1b-e2b`
- **Modal image digest:** built fresh 2026-07-24 (research-derived-cogr-wave1b-e2b)
- **Modal run URL:** https://modal.com/apps/generalintelligencecompany/main/
- **GPU type:** L4 only
- **`max_containers`:** 64 (human director authorized scaling)
- **Effective GPU-hour cost, USD upper bound:** $10.80
- **Effective cost relative to H100:** 0.235 (target ≤ 0.35, PASS)
- **Doppler scope:** `/Users/jawaun/superoptimizers`
- **Run date (UTC):** 2026-07-24
- **Seed range used:** `200000..201999`
- **Preset:** `confirmatory` (27 non-oracle cells × 300 seeds = 8100 rows)
- **Reproduce command:** `bash scripts/deploy_and_run_cogr_wave1b.sh`

## 4. Pre-run assertion receipts (per family)

| Family | `recency_load_bearing_corr` | `oracle_recall(recency)` | `oracle_recall(embedding_sim)` | `oracle_recall(care_only)` | `interaction_recovery(recency)` | PASS/KILL |
|---|---|---|---|---|---|---|
| `delayed_commitments_v2` | 0.150 | 0.120 | 0.220 | 0.160 | < 0.5 | PASS |
| `maintenance_fault_v2`   | 0.200 | 0.150 | 0.230 | 0.180 | < 0.5 | PASS |
| `resource_constrained_v2`| construction-guaranteed | < 0.8 | < 0.8 | < 0.8 | < 0.5 | PASS |

Confirmed at confirmatory time by the G9 leakage audit passing on all
three families (§5, G9 row).

## 5. Gate receipts (G0–G9)

| Gate | Status | Receipt |
|---|---|---|
| G0 integrity | PASS | IntegrityAudit clean; sealed evaluator one-call-per-episode; template-split guard clean on all 3 families |
| G1 L1_behavior | **KILL** (all 3) | learned−random mean_delta = −0.0216 / −0.0048 / −0.0032; paired 2σ lower bound −0.4318 / −0.4209 / −0.3588 ≪ delta_thresh_L1 |
| G2 L1_representation | **KILL** (all 3) | edge-ablation direction fraction 0.506 / 0.438 / 0.630 < 0.70 required; learned edges not causal |
| G3 L2_recovery | WITHHELD | L1 precondition failed; diagnostic rows preserved in raw receipts only |
| G4 L2_specificity | WITHHELD | L1 precondition failed |
| G5 non_ceiling | PASS (all 3) | headroom 0.539 / 0.520 / 0.572 ≥ 0.05 |
| G6 bundle_awareness | not scored | L1 KILLed on G1/G2 before G6 became promotion-relevant; planted-bundle receipts retained in raw rows |
| G7 adversarial | WITHHELD | L2-only gate; L1 precondition failed |
| G8 robustness | PASS | no family-level reversal; all three families KILL consistently, none masked by aggregate |
| G9 leakage_audit | PASS (all 3) | label-permutation p = 0.594 / 0.366 / 0.515 (≫ 0.01 tolerance); randomized-generator passed on all three — families carry no covert oracle |

## 6. Analysis-code freeze

- **`WAVE1B_ANALYSIS_HASH`:** 51ca021926ac8e3c57fec1d35cd6a59014f105d1a9adf47ab5e6434b48420c44
- **Mirror location:** `PREREGISTRATION.md §13`.

## 7. Epiplexity implementation regime

- **Estimator class used by the crossed-runner:** epiplexity was a dependent-variable diagnostic only (β=0 in the L1 gate); the SharedQR path is cross-validated to <1e-6 against the frozen L0 reservoir estimator in epiplexity_validation.py.
- **Regime verification note:** not on the critical path this run; no shared-factorization speedup is claimed.
- **Measured per-cell epiplexity wall-time speedup vs frozen L0 reservoir estimator:** not measured (epiplexity off the critical path); no multiplier claimed.

## 8. Bundle-awareness receipts

| Family | Complementary pairs planted | Recovered | Dangerous conjunctions planted | Avoided |
|---|---|---|---|---|
| `delayed_commitments_v2` | planted | not scored (G6 not promotion-relevant after L1 KILL) | planted | not scored |
| `maintenance_fault_v2`   | planted | not scored | planted | not scored |
| `resource_constrained_v2`| planted | not scored | planted | not scored |

## 9. L1 verdict

- **L1 decision (PASS / KILL):** KILL (G1 behavior + G2 representation, all three families)
- **Passing families:** none

## 10. L2 verdict

- **L2 decision (PASS / KILL / WITHHELD):** WITHHELD (L1 precondition failed)
- **Passing families:** none

## 11. Replay ledger

| Replay # | Date (UTC) | Cell rejected | Knob touched | Replayable range used | Effect on gate receipt |
|---|---|---|---|---|---|

## 12. Premise-audit stub (unchanged from Wave 0)

Wave 1b does not perform the premise audit against real, governed
long-horizon traces. Documented in the roadmap. No governed data is
ingested by Wave 1b code.

## 13. Artifact policy

Raw confirmatory outputs live under gitignored
`artifacts/concern_gated_retrieval_e2/wave1b/`. Only this file, the
preregistration, the promotion contracts, and the `__init__.py` /
`README.md` are committed under `experiments/`.

## 14. Change log

| Date (UTC) | Change |
|---|---|
| 2026-07-24 | Skeleton created. All numeric, hash, and gate-receipt fields TBD. Wave 0 + Wave 1a hash references pinned. |
| 2026-07-24 | Confirmatory Modal L4 run completed (27 cells, 8100 rows, $10.80, ratio 0.235). **L1 KILL** (G1 behavior + G2 representation on all three families; learned-vs-random mean_delta ≈ 0; edge-ablation direction fraction 0.44–0.63 < 0.70). **L2 WITHHELD** (L1 precondition failed). Leakage audits PASS on all families (p=0.37–0.59), so the KILL is honest, not a fixture artifact. WAVE1B_ANALYSIS_HASH populated. |
