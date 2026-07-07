# NEXT_STEPS — thinking-menu after Phase-0 KILL

**Not a plan. A menu.** Phase-0 closed with a pre-registered KILL
(see [POST_MORTEM.md](POST_MORTEM.md)). Per the plan and the memory
entry, Phase 3 is FROZEN until you explicitly re-scope the thesis.
This document exists so the next time you sit down to think about
direction, you have an honest, ordered brief instead of a blank page.

## What the KILL actually told us

Rank-ordered by strength of evidence:

1. **On BBBD's session-level attention contrast**, with a Riemannian +
   domain-adversarial + SSL-warm-start decoder stack, the LSO
   cross-subject balanced accuracy is **exactly 50.0%** across
   n_train ∈ {4, 8, 16, 24}. Flat curve. Zero bits/s of MI.
2. **The within-subject signal is real** (93.2% baseline). The stack
   works; it just can't find a subject-invariant representation on
   this contrast.
3. **The KILL is not a lazy config.** Every knob the pre-registration
   allowed (SSL on, 16 Hz band-zero, prior-only control, subject-ID
   isolation) was exercised. All ablations at chance or structural.

## What the KILL did NOT tell us

Explicitly out of scope, so any branch that goes here is a NEW pre-reg:

- Whether cross-subject decoding works on **fluctuating within-video
  attention** (BBBD's label is session-level, not fluctuating).
- Whether a **foundation-model EEG encoder** pretrained on thousands
  of subjects (LaBraM, EEGPT, NeuroLM-style) would break the 50%
  ceiling. This run's SSL was masked-reconstruction on 24 train
  subjects — a warm-start, not a foundation model.
- Whether **fNIRS + EEG fusion** would rescue it (only EEG tested).
- Whether **eyetrack / pupil / physio biomarkers** decode
  cross-subject cognitive state at all (never tested).
- Whether **within-session state proxies** (Riemannian distance to
  reference posture, band-power volatility, HRV shifts) would give a
  usable per-session score even without epoch-level classification.
- Whether the **BBBD-alternate contrasts** (quiz-score regression,
  digit-span working-memory) — which were declared secondary in
  kill_criterion.yaml but never run — would have shown a different
  pattern.

Each of these is a separate falsifier for a variant thesis, not a
retry of the same one.

## Three branches to consider

Ordered by cost-to-explore (cheapest first), not by expected
value.

### Branch A — Accept and shelve (default)

**Cost:** none.
**Time:** 0 hours of new work.
**Plausibility of the underlying thesis:** unchanged from before
the Phase-0 test — you just have no positive evidence for it.

**What this looks like:**
- Site stays live as-is (footer already says "on pause").
- No new investor / partner conversations premised on the wearable
  mind-interface thesis.
- Modal + Railway costs continue at ~pennies/mo; nothing to tear down.
- If a compelling new angle appears (new corpus, new hire, new paper),
  reopen with a fresh pre-registration.

**Choose this if:** the KILL updated you materially and you'd rather
put the cycles elsewhere than chase a wounded thesis.

### Branch B — Test the fluctuating-attention hypothesis (medium bet)

**Cost:** medium. New pre-registration, new corpus, ~1-3 weeks of work.
**Plausibility of a positive result:** middling. The KILL is a
strong prior that cross-subject EEG is hard, but session-level labels
may have been the wrong task. A fluctuating attention corpus (e.g.
sustained attention response task with per-trial correctness) tests
a genuinely different claim.

**Concrete steps:**
1. Find a candidate corpus with per-trial (not per-session) attention
   labels under a commercial-compatible license. Candidates to
   evaluate: Sustained Attention Response Task (SART) datasets on
   OpenNeuro, DEAP's per-video valence/arousal (already in
   `references/text/`), or a driving-fatigue EEG corpus.
2. Write a NEW `config/kill_criterion.<branch-b>.yaml`. Same
   thresholds are fine, but the primary task and rationale change.
3. Reuse the existing preprocess + decoder stack unchanged. That
   gives us clean A/B comparison — if branch B beats chance,
   we've isolated "label granularity" as the variable.
4. Run once. Same KILL/GO/INCONCLUSIVE outcomes possible.

**Choose this if:** you believe the session-level label was the load-
bearing failure and want to test it head-on before writing off the
whole thesis.

### Branch C — Foundation-model EEG bet (expensive, longshot)

**Cost:** high. 2-4 weeks of engineering, non-trivial compute cost
(Modal GPUs for foundation-model pretraining), possibly hiring.
**Plausibility of a positive result:** modest. LaBraM / EEGPT get
5-10 point LSO lifts on standard BCI tasks — not the 15+ points we'd
need to move from 50.0 → 60.0 here. And they were pretrained on
2000+ subject-hours; we don't have that data.

**Concrete steps:**
1. Pick a public foundation model (LaBraM or NeuroLM) with a
   commercially-friendly weights license. Verify.
2. Wire it as an encoder in front of the current cross-subject head.
3. Rerun the same BBBD test. If it beats chance meaningfully,
   INCONCLUSIVE (rerun with the pre-registered ablations); if it
   doesn't, the KILL is even more bulletproof.
4. If it does beat chance, the follow-up question is: can we
   pretrain our OWN foundation model on more data? That IS the moat
   in an eventual company, but it's a real capex bet.

**Choose this if:** you specifically believe the missing ingredient
is foundation-model pretraining and want to prove or refute that
before shelving.

### Branch D — Pivot to eyetrack / fNIRS / physio (out-of-band)

**Cost:** low-to-medium. Reuses the same infra but different signal.
**Plausibility:** unknown — never tested. Cross-subject pupil
dynamics for cognitive load HAVE been shown to work in the psych
literature; whether it holds under commercial-quality noise and at
useful bandwidth is untested.

**Concrete steps:**
1. Repurpose `coherence-testbench/` to a `pupil-testbench/` or
   `nirs-testbench/`. The Modal + Doppler + Volume + Supabase infra
   all reuse cleanly. Only the signal ingest changes.
2. BBBD exp 1 IS eyetrack — already downloaded to `bbbd-cache`. Zero
   ingest cost to start.
3. New pre-registration for the new modality's kill-criterion. The
   thresholds are looser because pupil bandwidth is lower.

**Choose this if:** you're persuaded the EEG bet is dead but the
company thesis (objective waking-state biomarker for CNS trials) is
still alive on a different modality.

## Resource-cost check

Verified 2026-07-06 close-out:
- Modal deployed apps (`coherence-testbench-phase0`,
  `coherence-testbench-bbbd-prep`): 0 running containers. No compute
  cost while idle.
- Modal Volumes: `bbbd-cache` ~27 GB, `phase0-results` ~1 MB.
  Storage cost estimated < $5/mo.
- Railway `neurophenom-site`: static, negligible.
- Nothing bleeding money. Safe to leave as-is indefinitely.

## What NOT to do (freeze rules from POST_MORTEM.md)

- Do NOT swap corpora and re-run the SAME `kill_criterion.yaml`.
  That's post-hoc goalpost movement. New corpus → new pre-reg.
- Do NOT start Phase-3 build (partner dashboard, outbound, custom
  hardware) without explicit re-scoping.
- Do NOT delete `coherence-testbench/`. The whole test-bench is the
  evidence.
- Do NOT take the site down without asking. The "on pause" footer
  is more honest than a 404.
