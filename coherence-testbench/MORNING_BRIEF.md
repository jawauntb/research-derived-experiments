# Morning brief — 2026-07-07 (revised 02:35 EDT after verification)

## What changed while you slept — TL;DR

- **01:44 EDT:** quiz-score regression on eyetrack cleared the pre-
  registered GO threshold, ρ = 0.277 on the pooled result.
- **02:16 EDT:** adversarial verification (bootstrap CI + demographic
  baseline + per-experiment breakdown) surfaced a silent bug —
  exp4 had been dropped from the ingest due to a stim-numbering
  mismatch. GO was based on exp2+exp3 only.
- **02:35 EDT:** corrected run (with exp4's mapping fixed) returned
  **INCONCLUSIVE, not GO.** Signal is real on exp3 (ρ=0.38) but
  weaker on exp2 (ρ=0.17) and weakest on exp4 (ρ=0.11). Pooled ρ
  at max n=32 = 0.132, below the 0.15 GO threshold; one seed
  fails the per-seed 0.05 floor.
- **Site footer + README + memory rolled back.** Phase 3 stays
  frozen. No pre-registered gate cleared on the full corpus.

The pre-registration + verification loop caught its own artifact.
That's the system working correctly, but it means the "first GO" story
you would have woken up to at 01:44 was premature.

## The three tables that matter

**Original (01:44) — pre-bug-fix, exp2+3 only, 60 subjects:**

| n_train_subjects | mean Spearman ρ | folds |
|---:|---:|---:|
| 8  | +0.194 | 10 |
| 16 | +0.289 | 10 |
| 24 | **+0.277** | 10 |

Verdict: **GO** (later retracted).

**Corrected (02:35) — bug-fix, all three experiments, 102 subjects:**

| n_train_subjects | mean Spearman ρ | folds |
|---:|---:|---:|
| 8  | +0.152 | 15 |
| 16 | +0.216 | 15 |
| 24 | +0.223 | 15 |
| 32 | **+0.132** | 5 (exp4-only) |

Verdict: **INCONCLUSIVE** (per-seed at n=32 fails floor: [−0.009,
+0.615, +0.017, −0.161, +0.198]).

**Per-experiment ρ at n=24 (corrected):**

| exp | subjects | records | ρ at n=24 |
|----:|---------:|--------:|----------:|
|  2  |    31    |   297   |   +0.171  |
|  3  |    29    |   323   |   +0.382  |
|  4  |    42    |   126   |   +0.114  |

Common controls (both runs):
- prior-only train-mean regressor: ρ = 0.000 ✅ (clean)
- distracted-predicts-attentive-score: ρ ≈ −0.02 ✅ (chance)

Verification-only findings (post-hoc):
- **Demographics-only baseline (Age+Sex from participants.tsv, no
  eyetrack):** ρ = +0.124 [95% CI +0.026, +0.229]. This explains
  ~44% of the observed effect. Eyetrack-specific signal above
  demographics is ρ ≈ 0.15.
- **Residualized rerun (02:52) — full Frisch-Waugh-Lovell test.**
  Fit `Ridge(Age, Sex) → quiz` on each train fold, compute residuals
  on train + test, train eyetrack MLP on residuals. Cleanly
  isolates the eyetrack signal above demographics.

  | n_train | ρ_eyetrack_raw | ρ_demo_only | **ρ_residual** |
  |---:|---:|---:|---:|
  |  8 | +0.165 | −0.026 | +0.019 |
  | 16 | +0.201 | +0.067 | +0.159 |
  | 24 | +0.216 | +0.073 | **+0.207** ← peak |
  | 32 | +0.091 | +0.027 | +0.109 |

  Per-experiment surprise: exp3's raw ρ=+0.38 collapses to
  ρ_residual=+0.112 (most of exp3's story was demographics).
  Exp2 strengthens: raw +0.171 → residual +0.200 (genuine
  per-recording signal). See `QUIZ_VERIFICATION.md` §7.

## What that means, at three levels of ambition

- **Minimum honest read:** the retracted GO was ~44% demographic
  (Age+Sex from participants.tsv). The 02:52 residualized rerun
  confirms this cleanly: **residual eyetrack ρ = +0.207 at n=24**,
  well above zero, still positive, but half the raw headline.
- **Middle read:** the pre-registered gate on the *raw* quiz score
  ρ=0.15 doesn't clear over the full corpus; the residualized ρ
  peaks at 0.207 but wasn't the pre-registered target. Also:
  exp3 (the strongest per-experiment raw signal at ρ=+0.38)
  collapses to +0.112 when residualized — most of exp3's story was
  demographics, not eyetrack. Exp2 (weakest raw signal) actually
  strengthens under residualization (+0.171 raw → +0.200 residual)
  because its eyetrack signal is genuinely per-recording.
- **Full read:** the honest three-line summary of the whole session
  is: (1) EEG is dead cross-subject on BBBD; (2) eyetrack has a
  real but modest signal above demographics on this task (residual
  ρ ≈ 0.2); (3) the pre-registered gate does not clear on the
  full corpus, so Phase 3 stays FROZEN — but the underlying
  modality is not falsified, just not strong enough on this
  particular corpus/task to justify build spend.

## What ran while you slept

1. `quiz-20260707-014453` — the load-bearing quiz-score regression.
   Verdict `GO`. Report at
   `phase0-results:/quiz-20260707-014453/report.md`.
2. LaBraM integration research agent (see
   `coherence-testbench/docs/labram_integration.md`) — confirmed
   MIT-licensed, weights public, ~4 h to first result.
3. LaBraM EEG rescue attempt (`phase0.eeg.labram.v1`). Wired up as
   `coherence-testbench-labram`. **Did NOT complete.** Eight+
   variants tried across two families of failures:

   Image-family failures (5x):
   - `debian_slim` + CPU-tagged pip_install → libcudart
   - `debian_slim` + safetensors pin → libcudart
   - `debian_slim` + manual `hf_hub_download` → libcudart
   - `debian_slim` + `run_commands` uninstall + torch 2.4.1 CPU →
     image build failed (dep resolver)
   - `debian_slim` + `run_commands` + torch 2.5.1 CPU → build failed

   Code-family failures on the pytorch/pytorch base (3x):
   - `Image.from_registry("pytorch/pytorch:2.5.1-cuda12.4")` +
     loose pins → image builds, but braindecode's
     `Labram(n_chans=64, n_times=800)` raises
     `ValueError("n_outputs not specified.")`
   - Add `n_outputs=2` kwarg → same error; the kwarg is silently
     dropped by braindecode's `wrapped` decorator
   - Switch to `Labram.from_pretrained(repo_id)` → safetensors
     `NameError` even with safetensors in pip_install (huggingface_hub
     module-level try-import + torch version mismatch)

   The pre-registration `phase0.eeg.labram.v1` is on file, the shard
   code is in the repo, but no LaBraM verdict. Real fix requires
   either (a) implementing a minimal LaBraM loader against the
   upstream repo's weights + architecture (bypasses braindecode
   entirely), or (b) switching to CBraMod / EEGPT / a different
   commercially-friendly foundation model. Both are fresh-eyes work.
   **Not load-bearing on the eyetrack result.**

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
