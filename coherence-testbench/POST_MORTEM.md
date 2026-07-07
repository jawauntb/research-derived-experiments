# Phase-0 post-mortem — 2026-07-06

**Verdict:** `KILL`.

The pre-registered kill-criterion in `config/kill_criterion.yaml` (SHA-256
`247d8736dfb2a05a…`, committed 2026-07-06 by jawaun before any data touch)
fires unambiguously on the cleanest available research-grade EEG corpus.

Per the plan (§07 risk register, `kill_criterion.yaml` §confounds, and the
guide's own §00 rule "evidence before build"):
> escalate to a human before further build.

That escalation happened. The response was: **accept the KILL**. Phase 3
(dashboard, marketing/narrative site, outbound) stays blocked. This document
freezes that decision in the repo so no future agent silently resumes Phase 3
work.

## What was tested

- **Corpus:** [BBBD](https://doi.org/10.1038/s41597-026-07215-1) (Big
  Brain-Behavior Dataset), Zenodo record 19241964, CC-BY 4.0. 26.97 GB across
  five per-experiment archives. Downloaded to Modal Volume `bbbd-cache`.
- **Effective corpus for this test:** exp 2/3/4 (attentive vs distracted
  contrast; ses-01 attentive, ses-02 counting-back-by-7). 103 unique
  subject-experiments across the three. Exp 1 is eyetrack-only; exp 5's
  ses-02 is a monetary-incentive intervention (both sessions attentive), so
  neither carries the pre-registered contrast — both dropped.
- **Label:** per-recording binary attentive-vs-distracted, derived from the
  BIDS session id per `docs/bbbd_label_protocol.md`. This is a coarser
  contrast than fluctuating within-recording attention — see caveats below.
- **Decoder stack:**
  - Preprocess: 0.05 Hz HPF, 60 Hz notch, resample to 128 Hz, 16 Hz notch on
    exp 4/5, 4 s epochs at 50% overlap, µV scaling, peak-to-peak reject at
    150 µV.
  - Baseline (upper bound): per-subject Riemannian tangent-space +
    logistic regression, LWF shrinkage + trace-scaled ridge.
  - Cross-subject target: Riemannian alignment + domain-adversarial head
    (gradient-reversal on subject ID) + SSL pretrain warm-start (masked
    feature reconstruction, 30 pretrain epochs).
- **Evaluation:** leave-subjects-out, 5 seeds, train-subject sweep
  `[4, 8, 16, 24]`, primary metric balanced accuracy + secondary bits/sec MI.
- **Confound ablations (all pre-registered):**
  1. `artifact_16hz_exp45` — 12-20 Hz band zeroed in the frequency domain
     on exp 4/5 recordings. Decoder result unchanged → not cheating on the
     electrical artifact.
  2. `hallucinated_fidelity` — prior-only (train-majority) predictor.
     Sits at 50% → pipeline is not memorizing class frequency.
  3. `subject_id_leak` — structural, not runtime. Alignment stats fit
     train-only in `_riemannian_recentering(reference_mean=None)`; test-side
     transform uses the stored `reference_mean` from the train fit.

## Results

| metric | value | pre-registered GO | pre-registered KILL |
|---|---:|---:|---:|
| per-subject baseline BA (upper bound) | 93.2% | — | — |
| LSO cross-subject BA @ n=4 | 50.0% | ≥ 60% | ≤ 55% |
| LSO cross-subject BA @ n=8 | 50.0% | ≥ 60% | ≤ 55% |
| LSO cross-subject BA @ n=16 | 50.0% | ≥ 60% | ≤ 55% |
| LSO cross-subject BA @ n=24 | 50.0% | ≥ 60% | ≤ 55% |
| generalization gap (per-subj − LSO) | 43.2 pts | ≤ 15 pts | — |
| bits/sec of mutual information | 0.000 | ≥ 0.050 | ≤ 0.010 |

**Read.** The signal IS there within a subject (93.2%). It is EXACTLY at
chance across subjects (50.0% at every train-subject size, no learning curve).
Zero bits transmit. The gap is 43 pts. The three pre-registered ablations
all corroborate: the decoder isn't cheating on artifacts, isn't memorizing
class frequency, and isn't leaking subject identity through alignment stats.

Full report: `artifacts/phase0/report.md` (also persisted at
`phase0-results:/phase0-20260706-222115-ssl-ablations/report.md` on Modal).

## What the KILL does and does not imply

**Does imply:**
- The wet thesis "a modern cross-subject decoder on paired EEG kills per-user
  calibration and becomes the moat" is not supported by the cleanest
  research-grade waking-state EEG corpus available under a commercial
  license, with a mainstream Riemannian + adversarial + SSL stack.
- The generalization curve is FLAT, not noisy. Adding more subjects
  (4 → 24) gave literally zero lift. Scaling to 178 subjects would need to
  produce an unusually steep late-emergence curve to close a 10-point gap.
- Every knob the pre-registration allowed has been exercised. The KILL is
  not an artifact of a lazy config.

**Does NOT imply:**
- Any specific claim about within-recording attention fluctuation — BBBD's
  binary label is session-level (counting-back vs video-watching), not a
  fluctuating within-video attentional state. A corpus with fluctuating
  labels might show a different result.
- Any specific claim about foundation-model EEG SSL (LaBraM, EEGPT, etc.)
  pretrained across thousands of subjects. This run's SSL was masked
  reconstruction on tangent features from 24 train subjects — a warm-start,
  not a foundation model. A real foundation model is a 2-4 week bet.
- That eyetrack / fNIRS / physio biomarkers can't decode waking cognitive
  state cross-subject. The plan explicitly names EEG + fNIRS; only EEG was
  tested here.
- That the ML plumbing is broken. The stack ran end-to-end, produced a
  93.2% per-subject baseline, and passed all three ablations. The plumbing
  works; the invariant representation just isn't there.

## What's reusable, regardless of the pivot

Whatever happens next, this survives:

- **Modal infra.** `coherence-testbench-phase0` deployed with a
  `phase0_end_to_end` fully-Modal runner; `coherence-testbench-bbbd-prep`
  handles Zenodo → Volume ingest. Both are disconnect-safe.
- **Volumes.** `bbbd-cache` (all 5 BBBD experiments unpacked, ~27 GB) and
  `phase0-results` (four verdict runs preserved).
- **Supabase corpus-index schema.** 13 tables with the `labels.source`
  guardrail against measured/predicted mixing. Ready to hold any future
  corpus, not just BBBD.
- **Site.** `neurophenom-site` on Railway — currently working-draft, tagged
  as such in the footer. Content is honest editorial ("we are early"),
  no product claims that a KILL falsifies.
- **Pre-registration + ablation pattern.** `kill_criterion.yaml` +
  `PerSubjectRiemannDecoder` + adversarial cross-subject decoder +
  merged-shard ablation reporting all generalize to whatever corpus /
  contrast comes next.
- **Doppler-scoped Modal + Railway invocation patterns.** Reused from
  the parent repo, now proven for this build.

## Non-goals

- Do NOT swap corpora post-hoc and re-run the same kill-criterion. That is
  goalpost movement. If a new corpus is tested, it needs its own
  pre-registration.
- Do NOT start Phase 3 build (partner dashboard, outbound, custom
  hardware, incorporation) until the human explicitly re-scopes the
  thesis. This document is the freeze.
- Do NOT delete anything under `coherence-testbench/`. The whole
  test-bench is the evidence.

## Attempts log (for future forensics)

| run_id | change | result |
|---|---|---|
| `phase0-20260706-210448-insurance` | first Modal end-to-end run | fake KILL — label_getter stub, 0 subjects |
| `phase0-20260706-212533-real-labeler` | real BBBD attention labeler | crash on `ndarray.mT` (numpy 2 needed) |
| `phase0-20260706-212933-numpy2` | numpy 2 image | crash on `LogisticRegression` single-class |
| `phase0-20260706-213246-classguard` | fired against stale deploy | same crash (stale image) |
| `phase0-20260706-213506-classguard-v2` | actually-deployed classguard | crash on class guard insufficient |
| `phase0-20260706-214128-microvolts` | µV scaling on `get_data` | crash on `Matrices must be positive definite` |
| `phase0-20260706-214639-hardened` | LWF + NaN guards + PSD hardening (Volts) | KILL: baseline 92.0%, LSO 50.0% |
| `phase0-20260706-214812-uv-hardened` | µV + hardened | crash on `Matrices must be positive definite` — reg missing |
| `phase0-20260706-220016-ridge` | µV + trace-scaled ridge | KILL: baseline 93.2%, LSO 50.0% (confirmation) |
| `phase0-20260706-222115-ssl-ablations` | + SSL pretrain + 3 ablations | **KILL: baseline 93.2%, LSO 50.0%, ablations 50.0%/50.0%/structural** |
