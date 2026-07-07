# Quiz-score GO — adversarial verification

**Filed 2026-07-07 after the pre-registered `phase0.eyetrack.quiz.v1`
returned GO.** These analyses are post-hoc; the pre-registered gate had
already been cleared and this document is about *hardening* the finding,
not re-litigating it. Two of the findings materially shift the interpretation
even though the GO stands.

## 1. The GO stands after bootstrapping

Bootstrap 95% CI (20,000 resamples over 10 pooled n=24 folds):

- Pooled Spearman ρ at n_train=24: **+0.277 [+0.169, +0.388]**
- CI excludes 0: **yes**
- CI excludes the pre-registered GO threshold (0.15): **yes** (barely — lower bound is 0.169)
- Folds with ρ > 0: **10/10**

The gate is cleared with confidence.

## 2. But: exp4 was silently dropped due to a schema bug

The `read_quiz_scores` function was keying quiz labels by (subject, exp,
phenotype_stimulus_no). For exp4, the phenotype tsv uses
`stimulus_no ∈ {1, 2, 3}`, while the recording files are
`task-stim04/stim05/stim06`. My shard code parsed the recording side
(stim = 4, 5, 6) and looked up quiz scores at those keys, so exp4's
lookup returned None for every recording.

**The GO of ρ = 0.277 was computed on exp2 + exp3 only.**
Exp4 (43 subjects, the biggest experiment) contributed exactly zero
subjects to the pool.

Per-experiment breakdown at n=24 (from the shard_outputs.json):

| exp | subjects | mean ρ | bootstrap 95% CI       |
|----:|---------:|-------:|:-----------------------|
|  2  |    31    | +0.171 | [+0.093, +0.279]       |
|  3  |    29    | +0.382 | [+0.226, +0.512]       |
|  4  |     0    |   —    |    (missed by bug)     |

Exp3 is doing most of the heavy lifting. Exp2 barely clears the 0.15
GO threshold at the CI lower bound. The corrected exp4 run
(`quiz-20260707-021649-corrected`, fire-and-forget on Modal after the
fix) will tell us whether the third experiment strengthens, weakens, or
matches the pattern.

The bug is now fixed in `src/coherence/ingest/eyetrack.py`
(`stim_offset = {4: 3}`).

## 3. Demographics-only baseline explains almost half the effect

Cross-subject Ridge regression using only `Age` + `Sex` from
`participants.tsv` (no eyetrack, no per-recording features) predicts
quiz score at:

| exp | mean demo-only ρ at n=24 |
|----:|-------------------------:|
|  2  | −0.022                   |
|  3  | +0.207                   |
|  4  | +0.188                   |

Pooled across 15 folds (5 seeds × 3 experiments):
**demographic-only ρ = +0.124 [95% CI: +0.026, +0.229]**.

Interpretation:
- The **eyetrack effect above demographics is ρ ≈ 0.15**, not the raw
  0.28 headline. Roughly 44% of the observed signal is explained by
  Age + Sex alone.
- The eyetrack effect's 95% CI lower bound (0.169) *overlaps slightly*
  with the demographic-only CI upper bound (0.229). So the "eyetrack
  adds signal beyond demographics" claim is real but the magnitude is
  smaller than the raw ρ suggests.

This does NOT invalidate the GO. The pre-registered kill-criterion
compared cross-subject decoder performance to chance (ρ ≤ 0.05
KILL, ρ ≥ 0.15 GO); it did not require the decoder to beat a
demographic baseline. But if the intended interpretation is
"eyetrack captures cognitive-engagement signal beyond static
demographics," the effect size is more modest than the headline ρ.

## 4. What this means for the company narrative

The updated honest read:

- **Signal is real.** The GO threshold is cleared with a lower CI bound
  of 0.169 and 10/10 positive folds. The pre-registration is honored.
- **The eyetrack-specific effect is smaller than the raw headline.**
  ρ ≈ 0.15 attributable to eyetrack features above demographics.
  ~2.3% of variance in quiz score explained by eyetrack-specific signal.
- **The signal is heterogeneous across experiments.** Exp3 shows a large
  eyetrack-specific effect (ρ_eyetrack − ρ_demo ≈ 0.175); exp2 is
  smaller and marginal (~0.19). Cross-experiment stability is
  important to establish before over-claiming.
- **Exp4 is a genuine unknown until the corrected run finishes.**

## 5. What to do next

- Wait for `quiz-20260707-021649-corrected` (fire-and-forget from
  Modal). If exp4 shows similar signal to exp2/3, the pooled GO
  strengthens. If exp4 shows null, we know the effect is confined to
  the two smaller experiments and needs replication.
- **Do NOT lower the pre-registered threshold retroactively.** If the
  corrected run pushes the pooled ρ below 0.15, the honest verdict
  changes from GO to INCONCLUSIVE.
- Consider a proper *residualized* rerun: regress out
  demographic-predicted quiz score, then predict the *residual*
  from eyetrack. That's the correct control for a "eyetrack adds
  signal beyond demographics" claim. Should be added to
  `train_eyetrack_quiz.py` as an ablation for the next iteration.

## Artifacts

- Original run: `phase0-results:/quiz-20260707-014453/`
- Corrected run: `phase0-results:/quiz-20260707-021649-corrected/`
- This verification: `coherence-testbench/QUIZ_VERIFICATION.md`

## 6. Corrected run result (2026-07-07 02:35 EDT) — VERDICT REVERTS TO INCONCLUSIVE

The corrected run (`quiz-20260707-021649-corrected`) with exp4's stim
mapping fixed returned **INCONCLUSIVE, not GO**. Numbers:

| n_train | pooled ρ | notes |
|--------:|---------:|-------|
|       8 | +0.152   | at GO threshold |
|      16 | +0.216   | above GO |
|      24 | +0.223   | above GO |
|      32 | **+0.132**   | **below GO — max n is exp4 only** |

Per-seed at n=32: [−0.009, +0.615, +0.017, −0.161, +0.198] — one
seed at −0.161 fails the seed floor of 0.05. Per-seed stability check:
**FAIL**.

Per-experiment ρ at n=24:

| exp | subjects | records | ρ at n=24 |
|----:|---------:|--------:|----------:|
|  2  |    31    |   297   |   +0.171  |
|  3  |    29    |   323   |   +0.382  |
|  4  |    42    |   126   |   +0.114  |

The GO from the original run was a *subset* effect. Adding the missing
exp4 (which has weaker signal AND fewer records per subject, because
BBBD's exp4 splits stimuli across sessions) drags the pooled ρ down
at max n_train, and one bad seed at n=32 (exp4-only) fails the seed
floor.

### The strict pre-registered verdict is INCONCLUSIVE.

Any narrative that assumes GO must retract to INCONCLUSIVE. The
freeze rules apply as before: Phase 3 stays FROZEN. The site footer
gets rolled back to the pre-GO language (with a note about the
verification-driven retraction). The signal is still real (ρ=0.38 on
exp3), but per the pre-reg gate the aggregate result is INCONCLUSIVE.

### What the corrected run tells us that the original didn't

- **exp3 has genuinely strong cross-subject signal.** ρ = 0.38 is not
  an artifact.
- **exp2 has weaker but real signal.** ρ = 0.17-0.21.
- **exp4 has the weakest signal.** ρ = 0.11-0.13. Probably because
  BBBD's exp4 only has 3 attentive-session recordings per subject vs
  6 in exp2/3.
- **Pooling heterogeneous experiments hurts the aggregate.** A more
  sophisticated eval would report per-experiment ρ separately or
  weight by n_records.

### Followups

- Do NOT rerun with exp4 dropped. That's textbook goalpost movement
  after seeing the data.
- If we care about exp3-specific signal, register a separate
  pre-reg keyed to a single experiment's design and run it fresh
  (Branch-E-like).
- The residualized-eyetrack ablation (§5) is still worth doing but
  the pre-reg gate is what it is.
