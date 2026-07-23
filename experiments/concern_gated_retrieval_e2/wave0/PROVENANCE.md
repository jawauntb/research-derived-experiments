# Wave 0 Provenance — skeleton

This file is a **skeleton**. It is populated by the Wave 0 Modal calibration
step and is the sole channel through which `TBD` values in
[`PREREGISTRATION.md`](PREREGISTRATION.md) §8 and §11 become numeric.
Manual edits to numeric fields are forbidden.

## 1. Attribution

- **Human director:** Jawaun Brown
- **Wave:** 0 (calibration, freeze, premise-audit stub)
- **Package:** `experiments/concern_gated_retrieval_e2/wave0/`
- **Predecessor (imported, never edited):** `experiments/concern_gated_retrieval/`
- **Producing agent identity:** Claude Code (Opus 4.7) directed by human `Jawaun Brown`
- **Producing agent session ref:** `session_01XMVYi59Z5dSz2oTKd78A4b`

## 2. Preregistration binding

- **Preregistration path:** `experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md`
- **Preregistration digest (SHA-256, calibration-populated draft):** `9aebdcc258d900d07b8fd7bff60c8c715c99564522e2a194affa2d290873e513`
- **Promotion contract path:** `experiments/concern_gated_retrieval_e2/wave0/PROMOTION_CONTRACT.md`
- **Promotion contract digest (SHA-256):** `2c4edec8de4a72f22e770d57b8109c98c5f1c3d2698043a0e510934f17374264`
- **Signature status:** signed by calibration completion 2026-07-23. See PREREGISTRATION.md §1.

## 3. Calibration Modal run

- **Run kind:** `calibration`
- **Run label:** `cogr_e2_wave0_calibration_2026_07_23`
- **Modal app:** `research-derived-cogr-wave0-calibration`
- **Modal image digest (deployed before spawn):** `im-I8ERULtbIN07yKPnxWYwxm`
- **Modal run URL:** https://modal.com/apps/generalintelligencecompany/main/ap-NoUhXlWmwVltucEJvEZcHd
- **GPU type:** L4 (H100 explicitly forbidden by Wave 0 operating rule)
- **Effective GPU-hour cost, USD upper bound:** `$8.00`
- **Effective cost relative to equivalent H100 rate:** `0.235` (target ≤ 0.35, PASS)
- **Doppler scope:** `/Users/jawaun/superoptimizers`
- **Run date (UTC):** 2026-07-23
- **Seed range used:** `100000..100999` (verified disjoint from reserved
  confirmatory range `200000..201999`)
- **Preset:** `calibration` (18 cells x 24 seeds/cell = 432 rows)
- **Reproduce command:** `bash scripts/deploy_and_run_cogr_wave0.sh`

## 4. Per-family variance receipt (mirror of PREREGISTRATION.md §8)

| Family | `mu_hat_multiplicative` | `sigma_hat_multiplicative` | `mu_hat_best_matched` | `sigma_hat_best_matched` | `headroom_to_ceiling` | `delta_thresh_L1` |
|---|---|---|---|---|---|---|
| `delayed_commitments` | 0.0553 | 0.2080 | 0.5314 | 0.0218 | 0.4845 | 0.0484 |
| `maintenance_fault` | 0.0480 | 0.1483 | 0.5029 | 0.0267 | 0.4548 | 0.0534 |
| `resource_constrained` | 0.1578 | 0.2905 | 0.5750 | 0.0250 | 0.4291 | 0.0500 |

**Observation.** The calibration multiplicative-PPR (`multiplicative_ppr`) sits
substantially *below* the best matched-budget baseline on every family under
the adversarial wrong prior. This is not a failure of Wave 0; it is Wave 0
doing its job. The L0 pilot's ceiling initialization masked how sensitive the
multiplicative fusion is to wrong-prior care weights. Wave 1 must beat these
`mu_hat_best_matched` rows using the online-learned concern update, not the
frozen wrong prior. Wave 0 does not adjudicate whether it can.

## 5. Gate receipts (G0-G6, mirror of PROMOTION_CONTRACT.md)

| Gate | Status | Receipt |
|---|---|---|
| G0_ANTI_LEAKAGE | PASS | `tests/test_cogr_wave0_sealed_env.py` + `test_cogr_wave0_template_split.py` green; IntegrityAudit invoked at baseline import |
| G1_WRONG_PRIOR | PASS | Every calibration row generated via the wrong-prior spec in `PREREGISTRATION.md` §5 |
| G2_NON_CEILING | PASS | Every family reports strictly positive `headroom_to_ceiling` (0.4291-0.4845); no promotable baseline saturates within 0.05 of the oracle |
| G3_FAMILY_ROBUSTNESS | PASS | Per-family variance receipt above; no cross-family collapse |
| G4_SEED_INDEPENDENCE | PASS | Seed range 100000-100999 verified disjoint from reserved 200000-201999 |
| G5_CODE_FREEZE | PASS | `WAVE0_ANALYSIS_HASH = 9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23` |
| G6_MODAL_BUDGET | PASS | L4 GPU only; realized cost ≤ $8.00; ratio 0.235 ≤ 0.35 target; image `im-I8ERULtbIN07yKPnxWYwxm` deployed before spawn |

## 6. Analysis-code freeze

- **`WAVE0_ANALYSIS_HASH`:** `9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23`
- **Files hashed:** every tracked file under
  `experiments/concern_gated_retrieval_e2/wave0/**` in sorted path order.
- **Mirror location:** `PREREGISTRATION.md` §11 (must match this value
  byte-for-byte).

## 7. Premise-audit stub

Wave 0 does **not** perform the premise audit against real, governed
long-horizon traces. The audit is documented in
[`docs/concern_gated_retrieval_research_program.md`](../../../docs/concern_gated_retrieval_research_program.md)
§ "Wave 0 — premise, safety, and calibration" as future work. No governed
data is ingested by Wave 0 code.

- **Premise-audit status:** future work — no data ingested.
- **Governance gates cleared:** none. See the roadmap's "Safety and
  data-governance entry gates" list; every item there is currently
  outstanding.
- **Non-evidence marker:** this stub is explicitly non-evidential. It is
  recorded here so that a future audit run does not silently reuse Wave 0
  provenance to claim clearance.

## 8. Artifact policy

- Raw calibration outputs (per-episode receipts, propensity logs) live
  under gitignored `artifacts/concern_gated_retrieval_e2/wave0/`.
- Only this file, the preregistration, and the promotion contract are
  committed under `experiments/`.
- No user PII, no secrets, no `.env` contents are committed under this
  subtree.

## 9. Change log

| Date (UTC) | Change |
|---|---|
| 2026-07-23 | Skeleton created. All numeric and hash fields TBD; to be filled by the Wave 0 Modal calibration step. |
| 2026-07-23 | Calibration Modal L4 run completed (app `research-derived-cogr-wave0-calibration`, image `im-I8ERULtbIN07yKPnxWYwxm`, 18 cells x 24 seeds). All seven gates G0-G6 PASS. Per-family variance rows populated; multiplicative_ppr underperforms best matched baseline under wrong prior (expected under §5 adversarial spec). `WAVE0_ANALYSIS_HASH` computed and mirrored. |
