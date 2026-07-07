# Morning brief — 2026-07-07

## What changed while you slept

**Cleared the first GO of the session.** Eyetrack cross-subject-predicts
per-recording quiz score (video comprehension) at Spearman ρ = 0.277 on
held-out subjects. Pre-registered before touching data. Ablations clean.
Reporting-only secondary "distracted → attentive score" sits at chance,
which validates the direction (the signal comes from active attention,
not from subject-level personality).

## The one figure

| n_train_subjects | mean Spearman ρ | folds |
|---:|---:|---:|
| 8  | +0.194 | 10 |
| 16 | +0.289 | 10 |
| 24 | **+0.277** | 10 |
| — prior-only baseline: 0.000 | | |
| — distracted-predicts-attentive-score: -0.030 | | |

Every seed cleared the pre-registered 0.05 per-seed floor.
GO threshold: ρ ≥ 0.15. Passed by 12.7 pts.

## What that means, at three levels of ambition

- **Minimum honest read:** eyetrack features carry cross-subject
  information about how well someone will comprehend a video, even
  when trained on strangers' data. Effect is small but robust. This
  is a real biomarker.
- **Middle read:** on the same subjects, EEG was flat at chance and
  eyetrack binary attention was inconclusive on bits/sec. Only this
  regression target cleared its gate. So the productizable channel is
  eyetrack, and the productizable measurement is comprehension /
  cognitive engagement, not binary attention.
- **Full read:** the plan's "objective brain-state biomarker for CNS
  trials" thesis survives — narrowed from "wearable multi-modal
  decoder" to "eyetrack biomarker of engagement." All the reusable
  infra (Modal apps, Doppler secrets, Supabase schema, Railway site)
  still applies.

## What ran while you slept

1. `quiz-20260707-014453` — the load-bearing quiz-score regression.
   Verdict `GO`. Report at
   `phase0-results:/quiz-20260707-014453/report.md`.
2. LaBraM integration research agent (see
   `coherence-testbench/docs/labram_integration.md`) — confirmed
   MIT-licensed, weights public, ~4 h to first result.
3. LaBraM EEG rescue attempt (`phase0.eeg.labram.v1`, same task as the
   killed EEG bench, encoder swapped to a frozen LaBraM-Base). Wired
   up on Modal as `coherence-testbench-labram`. **Did NOT complete.**
   Modal image build repeatedly failed with `libcudart.so.13`
   linkage — braindecode's `filter` module imports torchaudio at
   load time, and torchaudio's CPU wheel via Modal's `run_commands`
   still resolved a CUDA-linked variant. Five variants tried:
   - CPU-tagged pip_install (`torch==2.7.1+cpu`) — libcudart
   - safetensors pin added — libcudart persisted
   - Manual `hf_hub_download` + `torch.load` bypassing braindecode's
     `from_pretrained` — libcudart persisted
   - `run_commands` explicit uninstall + torch 2.4.1 CPU install —
     image build failed
   - `run_commands` with torch 2.5.1 CPU install — image build failed
   The pre-registration `phase0.eeg.labram.v1` is on file, the code
   is in the repo, but no LaBraM verdict tonight. This is a Modal
   image-spec fight — a fresh look tomorrow, or a different foundation
   model (CBraMod, EEGPT), should unstick it in an hour or two.
   **Not load-bearing on the eyetrack GO.**

## What I did NOT do

- Did NOT start Phase 3 build. The freeze rule from POST_MORTEM.md
  says even after a GO, Phase 3 requires explicit user re-scoping.
- Did NOT take the site down.
- Did NOT change the pre-registered thresholds after the fact.
- Did NOT succeed in getting LaBraM running — five image-spec
  variants all failed on Modal (see attempts log in the LaBraM
  section above). The `phase0.eeg.labram.v1` pre-registration is
  on record but has no verdict. Not urgent — the quiz-score GO
  stands on its own without any EEG rescue.

## What's on file

Read in this order:
1. `MORNING_BRIEF.md` (this file)
2. `MODALITY_COMPARISON.md` — head-to-head with the new quiz-score
   section at the top
3. `config/kill_criterion_eyetrack_quiz.yaml` — the pre-registration
   the GO cleared
4. `POST_MORTEM.md` — earlier EEG KILL for context
5. `NEXT_STEPS.md` — the four future branches; now update-worthy in
   light of the eyetrack GO

## What to decide when you wake up

The pre-registration cleared its gate. That's the objective signal.
The subjective questions are yours:

1. **Do you buy the effect size?** ρ = 0.28 is real but small.
   Explains ~8% of variance in quiz scores. Enough to sell as an
   endpoint in a CNS trial, or do we want more before that
   conversation?
2. **Do you want to try to break the GO?** The pre-reg's confound
   list only had two runtime ablations (prior-only and structural).
   Adversarial runs — e.g. per-subject baseline demographic
   regressor, or a train-only bootstrap for CI — would strengthen the
   result. Not required by the pre-reg, but if you plan to show this
   to investors, worth an hour.
3. **Do you want to run this against a bigger corpus?** BBBD's 60
   labeled subjects across 3 experiments is thin. A confirmatory
   replication on an independent eyetrack corpus with any
   cognitive-outcome label would be the strongest possible next test.
4. **Do you want to revive the EEG bench with LaBraM?** The
   background research agent is working on the integration spec. If
   LaBraM turns out to be plug-and-play, running it against the same
   quiz-score task would tell us whether the earlier EEG KILL was
   architecture-limited or genuinely a modality-limitation.

If you want me to autonomously execute one of these, tell me which
and I'll pick up. Otherwise the state is stable and safe.
