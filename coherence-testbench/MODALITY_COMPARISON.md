# Modality comparison — EEG vs eyetrack on the same BBBD task

Same 87 unique subject-experiments across BBBD exp 2/3/4. Same
session-level attentive-vs-distracted contrast (ses-01 vs ses-02).
Same LSO evaluation. Only the input signal differs.

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
- **Eyetrack:** signal is real (66.5% BA at n=32, +16 pts over chance,
  monotonic learning curve, non-zero MI, clean ablations).
- **BUT** bits/sec (0.024) falls short of the pre-registered GO threshold
  (0.030) by ~20%. The pre-registration's allowed rerun (SSL + more
  compute) executed and the verdict remained INCONCLUSIVE.
- **BBBD caps the data at ~32 subjects per experiment.** Based on the
  learning-curve slope (61 → 66.5% over 4 → 32 subjects), reaching
  the 0.030 bits/s bar would need roughly another ~50-60 subjects.
  Not available on BBBD alone.

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

- **EEG Phase-0:** CLOSED. Verdict `KILL`. See [POST_MORTEM.md](POST_MORTEM.md).
- **Eyetrack Branch-D gen-1:** INCONCLUSIVE. Signal present, bits/s short.
- **Eyetrack Branch-D gen-2 (SSL + more compute):** INCONCLUSIVE.
  Signal continues to strengthen (66.5% BA at n=32) but bits/s still
  falls 20% below the GO threshold. Pre-registered rerun exhausted.
- **Site:** footer updated to reflect the mixed EEG-KILL / eyetrack-
  INCONCLUSIVE result.
- **Phase 3 build:** still FROZEN. Signal present but no GO cleared.
  Unfreeze requires either (a) a new pre-registration on a corpus with
  more subjects, (b) a richer eyetrack featurizer that beats 66.5% BA,
  or (c) an explicit user decision to accept the sub-threshold signal
  as sufficient evidence.
