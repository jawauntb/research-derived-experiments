# E5 confirmatory-grid launch readiness

Status: **launch manifest validated; GPU grid not launched; scientific verdict
still pending**.

This note audits what the frozen E5 confirmatory grid requires and records the
no-compute launch validation. It is an operational artifact, not an E5 result.
The 70m/n=13 smoke remains integrity-only evidence, and no generator-learning,
coverage, group-specificity, patch, or transport claim is promoted here.

## Frozen workload

- Models: Pythia 70m, 160m, and 410m.
- Moduli: 13, 17, and 23.
- Seeds: 20260709, 20260809, and 20260909.
- Arms: G-reg, B-ref, W-reg, Cov, and A-ref.
- Training: 160 full epochs at `train_frac=0.5`, three train shifts, augmentation
  multiplier 3, candidate batch size 32, consistency-pair batch size 1, and the
  frozen LoRA/optimizer settings.
- Patch: 0.50 spectral-mass removal with the existing ±0.02 integrity tolerance.
- Total: **3 × 3 × 3 × 5 = 135 cells**.

## Launch audit

The prior runner dispatched one shard per model size, leaving 45 sequential
cells inside each six-hour L4 function. It also treated three observations per
arm as sufficient for `confirmatory_ready`, without proving the full matched
Cartesian grid. Those conditions were unsafe for the frozen claim.

The hardened path now:

1. Requires `--run-kind confirmatory`; smoke and development runs cannot emit a
   confirmatory verdict.
2. Rejects pre-launch drift in every frozen axis and training/patch parameter.
   G-reg and W-reg now share the exact supervised exposure and
   `(source_input, intervention_id)` consistency schedule in all nine frozen
   modulus/seed strata; the wrong control changes only the support-preserving
   non-cyclic generator relation.
3. Builds a deterministic 135-cell manifest and dispatches one L4 function per
   cell, with at most 12 containers active concurrently. L4 calls do not retry
   automatically; the six-hour timeout is therefore a one-attempt ceiling.
   Candidate evaluation is chunked and the consistency objective is
   backpropagated as the same weighted mean one pair-microbatch at a time, so
   410m cells do not retain the full consistency graph on L4 memory.
4. Binds the manifest and checkpoints to Python 3.12, Modal client 1.2.6, a
   complete 43-package Linux/Python runtime lock (including torch 2.7.1,
   transformers 4.56.2, PEFT 0.17.1, and accelerate 1.4.0), and immutable
   Hugging Face revisions for every model size. Results live in the V2
   `commitment-surface-e5-results-v2` Modal Volume. Reissuing the identical
   command resumes finite, integrity-passing cells rather than retraining them.
   Each cell records its measured worker runtime and resource request for cost
   calibration.
5. Requires all 135 expected keys exactly once. Missing, duplicate, unexpected,
   invalid-key, non-finite, out-of-range accuracy, or integrity-failed cells block
   `confirmatory_ready`; none can be repaired by post-hoc relabeling.
6. Builds the pinned image and proves a CPU-only V2 Volume write/read round trip
   during `--dry-run`, then scans checkpoints in a CPU control function before
   allocating GPUs. A separate CPU function prefetches each needed immutable
   Pythia snapshot once. Fresh workers consume the committed container-start
   cache snapshot without reloading the shared Hugging Face Volume while model
   files may be open. Missing largest-model/regularizer cells dispatch first.
   Completed cells do not consume L4 slots, and available output is reconstructed
   in frozen manifest order.
7. Collects mapped-cell exceptions instead of discarding successful siblings.
   A partial artifact names every failure and missing cell; the unchanged
   command is the explicit retry/resume mechanism.
8. Requires an explicit dry-run, inspect, or execute action. Inspection reports
   reusable, invalid, missing, and active-lease state without GPU work.
   Execution is capped by an explicit cell authorization, confirmatory
   execution must acknowledge the computed manifest ID, and an atomic expiring
   per-cell lease prevents overlapping launches from duplicating training.

No-compute validation:

- Final dry-run: <https://modal.com/apps/generalintelligencecompany/main/ap-Hx2Om89zykjdD9Lbft7E9A>
- Status-only inspection: <https://modal.com/apps/generalintelligencecompany/main/ap-pHhEE1JplOciZ7gFq2ilTL>
- Manifest ID: `e1db57affdf272b5e4f017641ecdcc54b06d7b7921465e1d116bd9c83dea497e`
- Implementation fingerprint: `63479e2e0a6a70b7304f287141dae8960d139a0285307dff687a4472bfb2c683`.
- Exact cell count: 135.
- Frozen-config mismatches: none.
- CPU pinned-image/Volume preflight: passed; all 43 resolved package versions
  matched the lock and the V2 result Volume write/read round trip succeeded.
- Checkpoint inspection: 0 reusable, 0 invalid, 135 missing, 0 active leases.
- Remote GPU training cells executed: 0.

The first confirmatory execution attempt exposed an operational defect before
producing a reusable cell: workers concurrently called `hf_cache.reload()` and
Modal rejected the reload because Transformers held cache files open; the local
client subsequently lost DNS and canceled the map. The unsafe worker reload was
removed without changing the frozen scientific parameters, which necessarily
changed the implementation fingerprint and therefore the manifest ID. The
replacement dry-run and inspection above passed, with no old-manifest result
reused or relabeled.

## Resource and cost review

Each cell requests one L4, 24 GiB memory, and a six-hour timeout. Modal is
currently priced at $0.000222/L4-second and $0.00000222/GiB-second, so the
requested GPU plus memory is approximately **$0.991 per cell-hour**, before CPU
usage. At the 12-container cap, the maximum active burn rate is approximately
$11.89/hour before CPU. Source: [Modal pricing](https://modal.com/pricing),
checked 2026-07-10.

The smoke did not retain defensible per-cell billable-duration telemetry, so a
full-grid point estimate would be false precision. Automatic L4 retries are
disabled, so the per-attempt cost formula is:

`135 × mean cell runtime in hours × $0.991`, plus CPU.

For orientation only, a 10-minute mean cell runtime is about $22.30, 30 minutes
is about $66.89, and one hour is about $133.79, before CPU. The six-hour timeout
is a failure ceiling, not a forecast; if every cell reached it, GPU plus memory
would approach $802.72 before CPU.

Run the frozen-parameter development calibration across all three sizes, all
three moduli, one seed, all five arms, and 160 epochs before authorizing the
135-cell spend. It is 45 cells (one third of the confirmatory workload), must
remain tagged `development`, and must use Modal billing telemetry to estimate
each size/modulus/arm runtime stratum. Its outcomes may calibrate runtime and
cost only; they must not change gates, hyperparameters, prompts, arms, or the
confirmatory manifest.

## Discovery-regime audit

- Current regime: E5 can represent leakage-audited exposures, novel-shift and
  paraphrase transport, normalized patches, and frozen mechanism gates.
- Action class: search inside the frozen E5 schema, not discovery.
- Accepted artifact: integrity-valid smoke plus exact no-compute launch manifest.
- Withheld artifact: every generator-learning or coverage mechanism verdict.
- Gate: only the exact 135-cell, three-seed, all-arm grid with complete finite
  metrics and all integrity checks may leave `pending_confirmatory_grid`.
- Next move: execute the development timing calibration, set an explicit spend
  ceiling from measured per-size runtimes, then launch the unchanged
  confirmatory manifest.
