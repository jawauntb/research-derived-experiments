# BBBD attentive/distracted label protocol

Spec for `label_getter(t0_seconds, t1_seconds) -> int | None`.
Sources actually read: the per-experiment `README.md` files inside the BBBD BIDS trees on the `bbbd-cache` Modal volume (experiments 2, 3, 4, 5), a sample `events.tsv` + `events.json` from `experiment4/sub-08/ses-01/eeg/` and `experiment4/sub-08/ses-02/eeg/`, and a WebSearch snippet of the Scientific Data abstract. **The paper full text was not directly readable** (Nature IDP redirect, biorxiv/researchgate 403). The dataset READMEs are consistent and match the abstract, so this spec is treated as authoritative rather than PROVISIONAL.

## 1. Per-experiment task summary

- **Experiment 1** — eyetrack/behavioral only. No EEG `events.tsv` under `experiment1/**/eeg/`. **Skip.**
- **Experiment 2** — 31 subjects, **incidental** learning: subjects watched 5 educational videos not knowing they would be quizzed. Two sessions: ses-01 attentive (then answered questions), ses-02 distracted (silent count-backwards by 7 from a random prime 800-1000).
- **Experiment 3** — 29 subjects, **intentional** learning: subjects were told upfront they would be quizzed. Same two-session structure (ses-01 attentive, ses-02 distracted, count-back-by-7).
- **Experiment 4** — 43 subjects, 6 videos split into two groups of 3. Same two-session structure (ses-01 attentive, ses-02 distracted, count-back-by-7). Adds head-position and respiration modalities.
- **Experiment 5** — 48 subjects, 3 videos. Two sessions BUT **not attentive-vs-distracted**: ses-01 attentive baseline, ses-02 "intervention" = same videos re-watched with monetary incentive per correct answer and questions revealed beforehand. Both sessions are attentive; ses-02 manipulates **motivation**, not distraction. *(The exp-5 README's "Sessions:" block is copy-pasted from exp 2-4 and incorrectly says "distracted / counting backwards"; the Summary and Experiment Setup blocks both give the correct "intervention" description — trust those.)*

## 2. Concrete label mapping

`events.tsv` in this dataset has only recording start/end markers — **there is no per-trial `trial_type` column**. The attention condition is a **per-recording constant** derived from the BIDS session id:

| experiment | ses-01 label | ses-02 label |
|------------|--------------|--------------|
| exp2       | `1` attentive | `0` distracted |
| exp3       | `1` attentive | `0` distracted |
| exp4       | `1` attentive | `0` distracted |
| exp5       | `None` (skip) | `None` (skip) — motivation manipulation, not distraction |
| exp1       | n/a (no EEG events.tsv) | n/a |

So per-epoch label = per-recording label, provided the epoch falls inside the valid recording window (§3).

## 3. Time alignment

`events.tsv` schema (from `events.json`): three columns — `onset` (seconds), `duration` (seconds), `event` (string ∈ {`start`, `end`}). Two rows per file:

- `start` row: `onset` = 0.0, `duration` ≈ 0.0078 s.
- `end` row: `onset` = recording length in seconds (e.g. 142.945 s for stim-04, 184.797 s for stim-01), `duration` ≈ 0.0078 s.

`t0_seconds` / `t1_seconds` are relative to recording start (i.e. relative to the `start` row's onset, which is 0). An epoch is inside the recording iff `start_onset <= t0 and t1 <= end_onset`. Reject anything outside this window (return `None`).

## 4. Which experiments actually support the binary label

- **Yes:** exp2, exp3, exp4 — clean session-level attentive vs distracted.
- **No:** exp5 — both sessions attentive; ses-02 is an incentive intervention, not a distraction. The decoder should **skip** exp5 recordings entirely.
- **No:** exp1 — eyetrack-only, no EEG events file.

Because the label is *per-recording* and not per-trial, epoch-level "attention" here is really "was this subject counting backwards during this recording, yes/no." That's coarser than a fluctuating within-recording state estimate — flag this to anyone doing state-space claims.

## 5. Edge cases the labeler must handle

1. **Path parsing.** `label_getter` must know which experiment and session it's in. Either take `(experiment, session)` as constructor args, or parse them from the `events.tsv` path (BIDS: `.../experimentN/sub-XX/ses-YY/eeg/...`).
2. **Exp5 / exp1 → `None`.** Return `None` for every epoch when experiment is 1 or 5.
3. **Malformed `events.tsv`.** If start or end row is missing, return `None`. (Two subjects in the abstract's ~110 h corpus have partial signals.)
4. **Epoch out of bounds.** `t0 < 0` or `t1 > end_onset` → `None`. Do not clip.
5. **Zero/negative epoch length.** `t1 <= t0` → `None`.
6. **Session-boundary artifacts.** Optionally drop the first and last ~1 s of every recording (settling / stop-button motor artifacts) by shrinking the valid window to `[start_onset + pad, end_onset - pad]`. Default `pad = 0`; make it a knob.
7. **No per-trial "excluded trials" flag.** The authors' technical validation lives in `derivatives/` and questionnaire correctness lives in `phenotype/stimuli_questionnaire.tsv`. Neither reaches into `events.tsv`. Do **not** invent a per-epoch attentive-good vs attentive-bad split from post-hoc quiz accuracy — the quiz is per-video, not per-epoch.
