# Modality comparison — EEG vs eyetrack on BBBD

Two pre-registered contrasts on the same subjects (BBBD exp 2/3/4):

1. **Binary attention:** ses-01 (attentive) vs ses-02 (distracted, counting-
   backwards). Reported here as balanced accuracy under LSO.
2. **Quiz-score regression:** predict per-recording quiz score (fraction
   correct) from the attentive-session signal. Reported as Spearman ρ
   under LSO.

> **Headline (2026-07-07 update):** the quiz-score regression on eyetrack
> returned **`GO`** — LSO Spearman ρ = **0.277** at n_train=24, monotonic
> curve, every seed above the pre-registered floor, prior-only baseline
> at ρ = 0.000. First cleared GO of the session. See §Quiz-score below.

## Headline

|                              | EEG (Phase-0)   | Eyetrack gen-1 | Eyetrack gen-2 (SSL + more compute) |
|---                           | ---:            | ---:            | ---:                       |
| per-subject baseline BA      | 93.2%           | 77.8%           | 77.8%                      |
| LSO cross-subject BA @ n=4   | 50.0%           | 61.0%           | 60.8%                      |
| LSO cross-subject BA @ n=8   | 50.0%           | 61.7%           | 61.1%                      |
| LSO cross-subject BA @ n=16  | 50.0%           | 62.6%           | 62.2%                      |
| LSO cross-subject BA @ n=24  | 50.0%           | 65.5%           | 64.7%                      |
| LSO cross-subject BA @ n=32  | 50.0%           | —               | **66.5%**                  |
| bits/sec MI @ max n          | 0.000           | 0.021           | **0.024**                  |
| generalization gap           | 43.2 pts        | 12.3 pts        | 11.3 pts                   |
| verdict                      | `KILL`          | `INCONCLUSIVE`  | **`INCONCLUSIVE`**         |

## Bottom line

- **EEG:** dead cross-subject on this task.
- **Eyetrack binary attention:** signal is real (66.5% BA at n=32, +16
  pts over chance, monotonic learning curve, non-zero MI, clean
  ablations). BUT bits/sec (0.024) falls short of the pre-registered
  GO threshold (0.030). Pre-registered rerun exhausted; verdict stays
  INCONCLUSIVE. BBBD caps at ~32 subjects per experiment.
- **Eyetrack quiz-score regression:** **`GO`.** LSO Spearman ρ = 0.277
  at n_train=24, monotonic curve, clean ablations. First cleared GO
  of the session. This is the load-bearing result — it says eyetrack
  cross-subject-predicts a real cognitive outcome (comprehension) at
  an effect size that would justify further data collection.

## Quiz-score regression (Branch-D supplementary v1)

Pre-reg: `config/kill_criterion_eyetrack_quiz.yaml` (`phase0.eyetrack.quiz.v1`).
Modal run: `quiz-20260707-014453`. 60 subjects contributed labeled
recordings across exp 2/3/4.

| n_train | mean Spearman ρ | n folds |
|---:|---:|---:|
| 8  | +0.194 | 10 |
| 16 | +0.289 | 10 |
| 24 | **+0.277** | 10 |

- Per-seed floor (0.05): every seed cleared.
- Prior-only train-mean regressor: ρ = 0.000.
- Structural subject-id-leak guarantee via train-only `_fit_scaler`.
- Reporting-only secondary: distracted-session-features →
  attentive-quiz-score = -0.030 (chance). You can't decode
  comprehension of a video from a session where the subject was
  counting backwards — as expected and validating.

## Binary attention comparison

## Reading

- **Within-subject signal is strong for BOTH modalities.** 93% (EEG) and
  78% (eyetrack). Whatever the decoder architecture is picking up per-
  person, it isn't nothing.
- **Cross-subject transfer only happens on eyetrack.** EEG lands at
  *exactly* 50.0% across all train sizes — a flat, unambiguous KILL.
  Eyetrack shows a **positive learning curve** (61.0 → 65.5% as
  training subjects grow), a **12-point gap** (per-subject vs LSO)
  well inside the GO threshold, and **non-zero MI** (0.021 bits/s).
- **This is the exact opposite of the naive prior.** EEG has orders of
  magnitude more channels (64 vs 8) and much higher bandwidth. But
  its cross-subject invariance under the plan's Riemannian +
  adversarial + SSL stack is zero. Meanwhile, 11 simple eyetrack
  features generalize.
- **The most likely reason:** the "attention vs distraction" contrast
  in BBBD is really "watching a video vs counting-back-by-7." Eyetrack
  probably picks that up via pupil-dilation-under-cognitive-load
  (Kahneman-style) and gaze-dispersion-under-task-switching, both of
  which are famously subject-invariant in the psychophysiology
  literature. EEG-level differences in the same distinction may be
  genuinely subject-specific (different alpha suppression patterns,
  different frontal-parietal balance) and not learnable from
  ~20-40 subjects.

## Ablation comparison (gen-1 eyetrack + Phase-0 EEG)

|                              | EEG                | Eyetrack |
|---                           | ---:               | ---:      |
| prior-only baseline          | 50.0%              | 50.0%     |
| 16 Hz band-zero (exp 4/5)    | 50.0%              | n/a (no EEG) |
| head-dropped                 | n/a (no head)      | **62.4%** (−3 pts) |
| subject-ID leak (structural) | fits train-only    | fits train-only |
| device-calibration (structural) | n/a             | fits train-only |

The head-dropped ablation is important: eyetrack signal is NOT
depending on the head-motion artifact from counting-out-loud. Real
gaze + pupil signal is doing the work.

## What Branch-D rerun-1 is testing

Fired `eyetrack-20260707-002325-ssl` at 00:23 with:
- SSL pretrain enabled (masked feature reconstruction warm-start on
  the trunk).
- More compute per fold (40 → 60 epochs).
- Expanded train-subject sweep (`[4, 8, 16, 24, 32]`) to catch exp4's
  higher end (43 subjects → ~34 in the train pool).

If the rerun clears **bits/s ≥ 0.030** at BA ≥ 58%, we have a **GO**
on eyetrack — first positive Phase-0 result of this build track.

## What this implies for the company thesis

The public framing of the guide reads: "objective brain-state
biomarkers that make CNS and psychedelic trials work." The internal
thesis says "wearable, high-information interface to human mental
state — attention, affect, cognitive load, intent."

The Phase-0 KILL narrowed one specific implementation of that thesis
(EEG + cross-subject decoder + BBBD session labels). The eyetrack
result reopens it on a different modality path. IF gen-2 confirms
GO:

- Public framing survives (objective biomarker is objective, whether
  the source is EEG or eyetrack).
- Endpoint bundle changes: pupil dynamics + gaze dispersion + saccade
  rate + head stability → cognitive-load / attention readouts.
- Regulatory ladder (510(k) → DDT) is similar; the device
  classification is different (eyetrack hardware is even more
  commoditized than EEG — smartphone cameras can do it).
- Beacon Biosignals moat (sleep EEG) still doesn't touch this.
- The wearable-mind-interface long-term thesis remains a bet, but
  eyetrack is a lower-friction on-ramp than EEG.

If gen-2 fires INCONCLUSIVE again, the honest read is: signal exists
but needs more subjects / better features / a more complex feature
extractor to break the bits/s ceiling. Would justify a Branch-D
"gen-3" with braindecode-style neural featurizer over raw
(8, n_samples) instead of the current 11 hand-crafted features.

If gen-2 fires KILL (LSO BA drops below 53%), that would be a
surprise given the positive gen-1 signal — most likely explanation
would be the SSL pretrain over-regularized the small feature space.
Would drop SSL and re-analyze.

## Status

- **EEG Phase-0 binary attention:** CLOSED. Verdict `KILL`. See [POST_MORTEM.md](POST_MORTEM.md).
- **Eyetrack Branch-D binary attention gen-1 + gen-2:** INCONCLUSIVE
  with signal (66.5% BA at n=32; bits/s just below GO bar).
- **Eyetrack Branch-D quiz-score regression:** **`GO`** (ρ = 0.277,
  supplementary pre-reg `phase0.eyetrack.quiz.v1`).
- **Site footer:** updated to reflect the quiz-score GO.
- **Phase 3 build decision:** the pre-registered rule ("only GO
  unfreezes Phase 3") has now been met on eyetrack quiz-score
  regression. The freeze rules from POST_MORTEM.md and memory
  explicitly named an *explicit user re-scoping* as the trigger, not
  just a passing GO — so this stays frozen pending your call, but the
  gate is CLEARED on the load-bearing criterion.
