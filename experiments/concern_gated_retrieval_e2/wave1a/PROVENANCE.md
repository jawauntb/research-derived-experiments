# Wave 1a Provenance — skeleton

This file is a **skeleton**. It is populated by the Wave 1a confirmatory
Modal run and is the sole channel through which `TBD` values in
[`PREREGISTRATION.md`](PREREGISTRATION.md) §8 become authoritative and
through which the screen decision receipt is published. Manual edits to
numeric or hash fields are forbidden.

## 1. Attribution

- **Human director:** Jawaun Brown
- **Wave:** 1a (COGR-E2a concern-recovery screen)
- **Package:** `experiments/concern_gated_retrieval_e2/wave1a/`
- **Predecessor (imported, never edited):**
  `experiments/concern_gated_retrieval_e2/wave0/`
- **Producing agent identity:** Claude Code (Opus 4.7) directed by human
  `Jawaun Brown`
- **Producing agent session ref:** `session_01XMVYi59Z5dSz2oTKd78A4b`

## 2. Preregistration binding

- **Preregistration path:**
  `experiments/concern_gated_retrieval_e2/wave1a/PREREGISTRATION.md`
- **Preregistration digest (SHA-256):** `6780ed27fde6214ec6cad239d2e2934e15463f79f0fbd7dd9dc7ff8231b79940`
- **Promotion contract path:**
  `experiments/concern_gated_retrieval_e2/wave1a/PROMOTION_CONTRACT.md`
- **Promotion contract digest (SHA-256):** `df403c9a3b609c54e0748416cf96fa407e23a7a4eaf0c7f57ca5eccf7b2279ba`
- **Referenced Wave 0 hash (must match `../wave0/PROVENANCE.md` §6
  byte-for-byte):**
  `9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23`
- **Signature status:** signed 2026-07-23 (KILL verdict; every gate produced a receipt).

## 3. Confirmatory Modal run

- **Run kind:** `confirmatory` (COGR_WAVE0_CONFIRMATORY_RUN=1)
- **Run label:** `cogr_e2_wave1a_confirmatory_2026_07_23`
- **Modal app:** `research-derived-cogr-wave1a-e2a`
- **Modal image digest (deployed before spawn):** cached from Wave 0 (`im-I8ERULtbIN07yKPnxWYwxm`)
- **Modal run URL:** https://modal.com/apps/generalintelligencecompany/main/ap-AbYIXed0497KixEABoyGdW
- **GPU type:** L4 (H100 explicitly forbidden by the wave-wide operating rule)
- **`max_containers`:** `32` (human director authorized scaling above the wave-wide default of 10)
- **Effective GPU-hour cost, USD upper bound:** `$1.20`
- **Effective cost relative to equivalent H100 rate:** `0.235` (target `<= 0.35`, PASS)
- **Doppler scope:** `/Users/jawaun/superoptimizers`
- **Run date (UTC):** 2026-07-23
- **Seed range used:** `200000..201999` (verified disjoint from calibration `100000..100999`)
- **Preset:** `confirmatory` (7 conditions × 3 families = 21 cells, 6320 rows aggregated)
- **Reproduce command:** `bash scripts/deploy_and_run_cogr_wave1a.sh`

## 4. Per-family screen receipt (mirror of PREREGISTRATION.md §6)

Populated once the paired-seed confirmatory rows are aggregated. The
per-family thresholds `delta_thresh_E2a_{f}` in
[`PREREGISTRATION.md`](PREREGISTRATION.md) §6.2 are frozen; only the
observed `delta_hat_{f,v}` and `sigma_delta_{f,v}` values below are
populated by the Modal run.

| Family | Variant | `delta_hat_{f,v}` | `sigma_delta_{f,v}` | Lower bound `delta_hat - 2σ` | `delta_thresh_E2a_{f}` (frozen) | Per-family PASS/KILL |
|---|---|---|---|---|---|---|
| `delayed_commitments` | `ips` | +0.0124 | (undefined — G1 coverage floor breach) | — | 0.04845 | **KILL** (G1 coverage 0.000 < 0.01) |
| `delayed_commitments` | `dr`  | +0.0124 | (undefined — G1 coverage floor breach) | — | 0.04845 | **KILL** (G1 coverage 0.000 < 0.01) |
| `maintenance_fault`   | `ips` | 0.0000 | small — see verdict.json | -0.0106 | 0.05340 | **KILL** (G3 specificity: recency=oracle=0.4772) |
| `maintenance_fault`   | `dr`  | 0.0000 | small — see verdict.json | -0.0106 | 0.05340 | **KILL** (G3 specificity: recency=oracle=0.4772) |
| `resource_constrained`| `ips` | +0.2258 | small — see verdict.json | +0.1758 | 0.05000 | **KILL** (G3 specificity: recency=oracle=0.6000) |
| `resource_constrained`| `dr`  | +0.2258 | small — see verdict.json | +0.1758 | 0.05000 | **KILL** (G3 specificity: recency=oracle=0.6000) |

Diagnostic (non-promotable) distance-to-oracle rows:

| Family | Variant | `mu_hat(oracle) - mu_hat(online_learned_v)` |
|---|---|---|
| `delayed_commitments` | `ips` | 0.5563 |
| `delayed_commitments` | `dr`  | 0.5563 |
| `maintenance_fault`   | `ips` | 0.4739 |
| `maintenance_fault`   | `dr`  | 0.4739 |
| `resource_constrained`| `ips` | 0.4242 |
| `resource_constrained`| `dr`  | 0.4242 |

## 5. Gate receipts (G0-G7, mirror of PROMOTION_CONTRACT.md)

| Gate | Status | Receipt |
|---|---|---|
| G0_ANTI_LEAKAGE | PASS | IntegrityAudit invoked at import; sealed environment evaluate() called exactly once per episode; template split guard raises LeakageError on calibration/confirmatory mix |
| G1_COVERAGE | **KILL** on delayed_commitments (`0.000 < 0.01`); PASS on maintenance_fault and resource_constrained. See §4 coverage row |
| G2_PROPENSITY_ACCOUNTING | PASS | ESS above floor on every non-collapsed cell; all receipts source_id="trusted"; single-source-influence bound holds |
| G3_SPECIFICITY | **KILL** on all three families | info_matched_recency = oracle ceiling byte-for-byte (0.5315 / 0.4772 / 0.6000); recency baseline is not information-matched to the update rule under the current family design |
| G4_PER_FAMILY_EFFECT | **KILL** | No family has a passing variant; see §4 lower-bound rows |
| G5_SEED_INDEPENDENCE | PASS | Confirmatory seeds 200000-201999 disjoint from 100000-100999; TemplateFamilySplit guard receipt clean |
| G6_CODE_FREEZE | PASS | `WAVE1A_ANALYSIS_HASH = c23b31d977d7c169d57ca12cdfdbc8ad3a59188542efbdf802e341b1c8937209`; Wave 0 hash mirrored byte-for-byte |
| G7_MODAL_BUDGET | PASS | L4 GPU only; realized cost ≤ $1.20; cost/H100 ratio 0.235 ≤ 0.35; `max_containers = 32`; image cached from Wave 0 (`im-I8ERULtbIN07yKPnxWYwxm`) |

## 6. Analysis-code freeze

- **`WAVE1A_ANALYSIS_HASH`:** `c23b31d977d7c169d57ca12cdfdbc8ad3a59188542efbdf802e341b1c8937209`
- **Files hashed:** every tracked file under
  `experiments/concern_gated_retrieval_e2/wave1a/**` in sorted path
  order.
- **Mirror location:** `PREREGISTRATION.md` §8 (must match this value
  byte-for-byte).
- **Wave 0 hash reference:**
  `9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23`
  (verified byte-for-byte against
  [`../wave0/PROVENANCE.md`](../wave0/PROVENANCE.md) §6 at signature
  time).

## 7. Screen decision

- **Screen decision (PASS / KILL):** **KILL**
- **Passing variant (if any):** `none`
- **KILL scope:** `coverage` (delayed_commitments), `specificity` (all three families via recency-ties-oracle family-design confound)
- **Downstream effect on Wave 1b:**
  - PASS: opens Wave 1b (COGR-E2b) crossed-geometry design. Wave 1a
    receipt is inherited by Wave 1b for the concern-update slot in the
    crossed matrix.
  - KILL: closes the concern-update rule as written. Wave 1b's L1 rows
    remain open; the E2a KILL withholds L2 but does not block L1
    (roadmap § "Wave 1 — staged mechanism identification").

## 8. Replay ledger

Every replay performed under the §7 replayable-knob rule is recorded
here with its rejected-cell trace, the replayable knob touched, and
the replay-seed subrange used. Empty at draft time; append-only.

| Replay # | Date (UTC) | Cell rejected | Knob touched | Replayable range used | Effect on gate receipt |
|---|---|---|---|---|---|

## 9. Premise-audit stub (unchanged from Wave 0)

Wave 1a does **not** perform the premise audit against real, governed
long-horizon traces. The audit is documented in
[`../../../docs/concern_gated_retrieval_research_program.md`](../../../docs/concern_gated_retrieval_research_program.md)
§ "Safety and data-governance entry gates" as future work. No governed
data is ingested by Wave 1a code.

- **Premise-audit status:** future work — no data ingested.
- **Governance gates cleared:** none. See the roadmap's "Safety and
  data-governance entry gates" list; every item there is currently
  outstanding.
- **Non-evidence marker:** this stub is explicitly non-evidential.

## 10. Artifact policy

- Raw confirmatory outputs (per-episode receipts, propensity logs,
  coverage tables) live under gitignored
  `artifacts/concern_gated_retrieval_e2/wave1a/`.
- Only this file, the preregistration, the promotion contract, and the
  `__init__.py` / `README.md` are committed under `experiments/`.
- No user PII, no secrets, no `.env` contents are committed under this
  subtree.

## 11. Change log

| Date (UTC) | Change |
|---|---|
| 2026-07-23 | Skeleton created. All numeric, hash, and gate-receipt fields TBD; to be filled by the Wave 1a confirmatory Modal run. Wave 0 hash reference pinned. |
| 2026-07-23 | Confirmatory Modal L4 run completed (app `research-derived-cogr-wave1a-e2a`, 21 cells, 6320 rows, cost ≤ $1.20, ratio 0.235). Aggregate screen decision **KILL**: G1 coverage on `delayed_commitments`; G3 specificity on all three families via a family-design confound where `info_matched_recency` reproduces the oracle ceiling byte-for-byte. Wave 1a signs the KILL per the honor-the-preregistration rule. `WAVE1A_ANALYSIS_HASH` populated. |
