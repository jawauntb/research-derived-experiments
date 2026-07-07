# coherence-testbench

Phase-0 test-bench for the Neurophenom / Coherence build plan. The single load-bearing
task in the entire company: prove cross-subject decoding of waking cognitive state
generalizes on real EEG before spending anything on hardware, data collection, or
market entry.

## Status

- **Phase-0 EEG (binary attention):** `KILL` (2026-07-06). See [`POST_MORTEM.md`](POST_MORTEM.md).
  LSO cross-subject 50.0% flat, bits/sec 0.000. Dead cross-subject.
- **Branch-D eyetrack (binary attention):** `INCONCLUSIVE` (2026-07-07)
  after pre-registered rerun. 66.5% BA at n=32, positive learning curve,
  bits/sec just short of GO. See [`MODALITY_COMPARISON.md`](MODALITY_COMPARISON.md).
- **Branch-D eyetrack (quiz-score regression, supplementary pre-reg
  `phase0.eyetrack.quiz.v1`):** originally reported **GO** (ρ=0.28)
  on 2026-07-07 at 01:44, but the corrected rerun at 02:16 (with
  a fixed exp4 stim-numbering mapping) reverts to **`INCONCLUSIVE`**.
  Signal is real on exp3 (ρ=0.38), weaker on exp2 (ρ=0.17), weakest
  on exp4 (ρ=0.11). Full write-up:
  [`QUIZ_VERIFICATION.md`](QUIZ_VERIFICATION.md). No pre-registered
  gate has been cleared on the full corpus.
- **Phase 3 build:** still **FROZEN**. The 01:44 GO was retracted
  when the corrected run showed the original was a subset effect
  (exp4 dropped by a silent bug). No pre-registered gate has cleared
  on the full corpus. See [`NEXT_STEPS.md`](NEXT_STEPS.md).

## What this repo does

1. Pre-registers the GO/KILL threshold for cross-subject attention decoding in
   `config/kill_criterion.yaml`. Committed BEFORE any run.
2. Ingests the [BBBD](https://doi.org/10.1038/s41597-026-07215-1) dataset (64-ch
   EEG, 178 subjects, CC-BY 4.0) from Zenodo via BIDS.
3. Preprocesses per dataset methods: 0.05 Hz HPF, 60 Hz notch, resample to 128 Hz,
   flag/notch the 16 Hz electrical artifact in Exp 4-5 so no decoder cheats on it.
4. Trains two decoders:
   - **Baseline** — per-subject calibrated (upper bound).
   - **Target** — cross-subject: Riemannian alignment + domain-adversarial head,
     with a hook for SSL pretraining.
5. Evaluates leave-subjects-out. Primary metric: attention decoding accuracy.
   Secondary: quiz-score / digit-span regression. Reports accuracy AND bits/sec
   mutual information.
6. Ships an auto-generated `report.md` with generalization curve, cross- vs
   per-subject gap, MI, and an explicit call vs the pre-set threshold.

## Non-negotiables (from the evaluation-discipline note in the plan)

- **Leave-subjects-out CV only.** Within-subject numbers are never a headline.
- **Report bandwidth as bits/second of mutual information**, not just accuracy.
- **Separate measured signal from generative prior.** Any prior-heavy component
  gets a signal-vs-prior ablation.
- **License hygiene.** BBBD is CC-BY 4.0. Do NOT introduce CC-BY-NC corpora
  (e.g. TRIBE-style) into the product path.

## Environment

Reuses the parent repo's env conventions (Doppler-scoped Modal, no secrets in repo).

```bash
# Local, without Doppler
python3 scripts/env_probe.py

# Under Doppler (recommended)
doppler --scope /Users/jawaun/superoptimizers run -- python3 scripts/env_probe.py
```

Expected variables (see `.env.example`):

- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` (inherited; not used by this bench directly)
- `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET` (Modal compute)
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (metadata / labels / experiment tracking)
- `LOGFIRE_TOKEN` (pipeline traces)
- `BBBD_CACHE_DIR` (local BIDS root; large — keep off the repo tree)

## Run Phase 0

Local dry-run of the whole gate on synthetic data (fast; sanity):

```bash
python3 scripts/run_phase0.py --smoke
```

**Stage the dataset on Modal** (one-time; downloads any missing experiment
archives directly on Modal's egress, unzips in place, then removes the zips):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        modal_jobs/prepare_bbbd.py
```

Full ingest + preprocess + LSO on Modal (the actual gate run):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        modal_jobs/train.py \
        --config config/phase0.yaml \
        --out artifacts/phase0
```

Report:

```bash
python3 scripts/generate_report.py \
    --results artifacts/phase0 \
    --kill-criterion config/kill_criterion.yaml \
    --out artifacts/phase0/report.md
```

## Phase-0 checklist

See [PHASE0_TODO.md](PHASE0_TODO.md). Each item mirrors the implementation-guide
task-list. Nothing is scaffolded outside Phase 0 in this folder.

## References

- BBBD dataset: <https://doi.org/10.1038/s41597-026-07215-1> ·
  Zenodo <https://doi.org/10.5281/zenodo.19241964> ·
  code <https://github.com/madjens/bbbd-dataset>
- Tools: [mne-bids](https://mne.tools/mne-bids), [braindecode](https://braindecode.org),
  [pyRiemann](https://pyriemann.readthedocs.io),
  [MOABB](https://moabb.neurotechx.com)
