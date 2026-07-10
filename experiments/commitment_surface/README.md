# commitment_surface

Severe pre-registered tests for the commitment-first reframe of the
research program. See
[`papers/commitment_surface/paper.md`](../../papers/commitment_surface/paper.md)
for the theory (Props 1+2, corollary, M4 anti-Goodhart loop) and
[`papers/commitment_surface/PLAN.md`](../../papers/commitment_surface/PLAN.md)
for the frozen pre-registration.

## Reframe

Old primitive (implicit throughout Papers 5–25 of the prior program):
availability of the right geometry / weakness ⇒ load-bearing at
deployment.

New primitive: a hypothesis `f` is *load-bearing at a commitment
surface* `Σ = (G_dep, C, T)` iff a train-time compatibility
intervention with the deployment generator lifts OOD, causal patching
of the aligned mechanism yields concern-weighted CE ≥ ε at the
commitment target, and the effect survives transport `t ∈ T`.

Weakness and concern geometry become diagnostics — powerful when
`G_probe = G_dep` (or weakness is restricted to `G_dep`; a strict
superset probe group does not suffice, see paper §3.4), footprints or
anti-correlates otherwise.

## Experiments

### E1 — Unequal-Consequence Concern-Weighted Selector

Extension arithmetic (stdlib only, CPU). Compares four selectors on
train-perfect candidate hypotheses over cyclic modular addition with a
concern-weighted deployment slice.

```bash
python3 -m experiments.commitment_surface.run_e1 \
    --moduli 7,11,13,17 --seeds 32 --n-candidates 300
```

Result: `results/e1_concern_weighted.{json,md}`. Well-specified
concern beats unweighted by +0.244; misspec (random `κ` with same
marginal) sits *below* unweighted at −0.054.

#### E1 follow-up — misspecification variance (CPU)

The timestamped addendum
[`e1_misspecification_variance_preregistration_2026-07-09.md`](../../papers/commitment_surface/e1_misspecification_variance_preregistration_2026-07-09.md)
freezes the original 96 candidate/deployment structures and redraws only the
misspecified assignment for 2,048 experiment-level replicates:

```bash
python3 -m experiments.commitment_surface.e1_misspecification_variance
```

Result: `results/e1_misspecification_variance.{json,md}`. Null mean gap
−0.058864 (SD 0.016100; central 95% [−0.091310, −0.029364]); the observed
−0.054159 has lower-tail probability 0.620117 (Wilson 95% CI
[0.598890, 0.640895]). All preregistered independence/exchangeability checks
pass. Verdict: **consistent with the random-assignment/selection null**, not
systematic anti-correlation. The original frozen ±0.05 gate remains failed.

### E2 / E3 — Compat Augmentation vs Readout, with Patch-CE

Neural MLP sweep on cyclic modular addition (requires torch, CPU is
fine). Four arms:

- A — no augmentation; select by post-hoc weakness readout.
- B — cyclic-orbit augmentation (true group).
- C — wrong-group augmentation `(π(x), π(y))` — same volume as B, but
  the augmented pair teaches the wrong equivariance
  `f(π(x)) = π(f(x))` for a random non-cyclic permutation `π`.
- D — no augmentation; select by lowest final train loss.

```bash
python3 -m experiments.commitment_surface.e2_e3_neural_sweep \
    --moduli 7,11,13 --train-fracs 0.4,0.55,0.7 --seeds 6 \
    --selector-pool 6 --epochs 1500 --hidden-width 96 --depth 2
```

Result: `results/e2_e3_neural.{json,md}`. In the aligned-generator
regime, B >> A on OOD (gap ≈ 1.0), B >> A on patch-CE Δ (gap ≈ 0.76),
and the anti-cheat gap B − C is at zero within noise (see the fixed
Arm C above — an earlier revision used a coverage-augmentation Arm C
that also succeeded because it added correct-labeled coverage of the
input space, and did not isolate group specificity from augmentation
volume; see paper §R2 for the transparent note).

### E4 — Pythia LoRA v2 External Contact (Modal L4)

Non-degenerate follow-up to the P1 hard kill in
`experiments/external_contact/`. Same four arms on Pythia
70m/160m/410m LoRA-fine-tuned on `f(x) = (x + offset) mod n`,
`n ∈ {13, 17, 23}`, `train_frac = 0.5`.

Smoke:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/commitment_surface/modal_e4_pythia_lora_v2.py \
        --sizes 70m --ns 13 --seeds 1 --arms A,B --epochs 80 \
        --out artifacts/commitment_surface/e4_smoke.json
```

Full grid:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/commitment_surface/modal_e4_pythia_lora_v2.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 --arms A,B,C,D \
        --epochs 160 --train-frac 0.5 --aug-multiplier 3 \
        --base-seed 20260709 \
        --out artifacts/commitment_surface/e4_pythia_lora_v2.json
```

Smoke result: Arm A OOD 0.0 (reproduces the P1 hard kill); Arm B OOD
0.714; patch-CE Δ +7.19; ρ(patch-CE, OOD) 1.0 vs ρ(weakness, OOD) 0.0
— a clean per-cell witness of Prop. 1 (probe readout does not identify
causal use) in the non-aligned regime.

Full-sweep result (108 cells): directionally decisive (Arm B 0.882 vs
Arm A 0.113 mean OOD; ρ(patch-CE, OOD)=0.853 vs ρ(weakness, OOD)=0.290),
but the strict pre-registered gate FAILED (A mean OOD 0.113 > 0.10).
Interpretation is also bounded by the label-exposure confound: cyclic
augmentation labels held-out-support points, so the sweep does not yet
separate generator learning from labeled orbit coverage (paper §6.5).
See `results/e4_pythia_lora_v2_summary.md`. The complete publication metrics
for all 108 cells are committed in
`results/e4_pythia_lora_v2_appendix.json`; large function tables and input lists
remain only in the gitignored raw payload. Regenerate the compact artifact with:

```bash
python3 scripts/export_commitment_surface_e4_appendix.py
```

### E5 — Generator Learning vs Labeled Orbit Coverage (Modal L4)

Explicitly post-hoc severe follow-up, frozen in the timestamped PLAN.md
addendum before E5 results. Five arms separate train-support-only generator
consistency (`G-reg`) from E4-style labeled orbit augmentation (`B-ref`), a
wrong-generator regularizer (`W-reg`), coverage-matched correct labels with no
group construction (`Cov`), and the unaugmented reference (`A-ref`).

The pure `e5_core.py` layer freezes support and intervention splits, constructs
typed exposure plans, rejects held-out truth-label leakage into G-reg/W-reg,
matches G-reg/W-reg consistency schedules and B-ref/Cov held-out exposure, and
applies the frozen analysis gates.
The Modal harness records the full exposure ledger, evaluates disjoint novel
shifts and prompt paraphrases, and patches a fixed fraction of each effective
LoRA update's spectral mass. Full-adapter disable is secondary only.

Validation smoke (not scientific evidence):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal==1.2.6 modal run \
        experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
        --sizes 70m --ns 13 --seeds 1 --arms G-reg,Cov,A-ref --epochs 20 \
        --run-kind smoke --execute --max-gpu-cells 3 \
        --out artifacts/commitment_surface/e5_smoke.json
```

The runner has three explicit result regimes: `smoke`, `development`, and
`confirmatory`. Only `confirmatory` can invoke the frozen gate, and that mode
rejects any drift in sizes, moduli, seeds, arms, epochs, split, augmentation,
LoRA, optimizer, or patch settings before remote work begins. Generate and
inspect the exact 135-cell manifest without allocating GPUs:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal==1.2.6 modal run \
        experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 \
        --arms G-reg,B-ref,W-reg,Cov,A-ref --epochs 160 \
        --train-frac 0.5 --train-shift-count 3 \
        --augmentation-multiplier 3 --spectral-mass-fraction 0.5 \
        --base-seed 20260709 --run-kind confirmatory --dry-run \
        --out artifacts/commitment_surface/e5_confirmatory_launch_manifest.json
```

Development calibration for the cost review (not scientific evidence; never
use it to change the frozen gate or confirmatory hyperparameters):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal==1.2.6 modal run \
        experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 1 \
        --arms G-reg,B-ref,W-reg,Cov,A-ref --epochs 160 \
        --train-frac 0.5 --train-shift-count 3 \
        --augmentation-multiplier 3 --spectral-mass-fraction 0.5 \
        --base-seed 20260709 --run-kind development \
        --execute --max-gpu-cells 45 \
        --out artifacts/commitment_surface/e5_development_calibration.json
```

Status-only checkpoint inspection (no model prefetch or GPU dispatch):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal==1.2.6 modal run \
        experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 \
        --arms G-reg,B-ref,W-reg,Cov,A-ref --epochs 160 \
        --train-frac 0.5 --train-shift-count 3 \
        --augmentation-multiplier 3 --spectral-mass-fraction 0.5 \
        --base-seed 20260709 --run-kind confirmatory --inspect \
        --out artifacts/commitment_surface/e5_confirmatory_status.json
```

Confirmatory grid (launch only after the smoke and cost review pass):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal==1.2.6 modal run \
        experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 \
        --arms G-reg,B-ref,W-reg,Cov,A-ref --epochs 160 \
        --train-frac 0.5 --train-shift-count 3 \
        --augmentation-multiplier 3 --spectral-mass-fraction 0.5 \
        --base-seed 20260709 --run-kind confirmatory \
        --execute --max-gpu-cells 135 \
        --expected-manifest-id "$E5_MANIFEST_ID" \
        --out artifacts/commitment_surface/e5_generator_vs_coverage.json
```

Set `E5_MANIFEST_ID` to the ID printed by the final dry run. The launcher
rejects execution unless exactly one of `--dry-run`, `--inspect`, or
`--execute` is present. Confirmatory execution also rejects an expected-ID
mismatch, and every execution refuses to submit more missing GPU cells than
the explicit `--max-gpu-cells` authorization.

The grid is dispatched as 135 separately checkpointed L4 cells, capped at 12
concurrent containers. Integrity-passing, finite cell payloads are keyed by a
manifest that includes exact package versions and immutable Pythia revisions,
then stored in the V2 `commitment-surface-e5-results-v2` Modal Volume. There
are no automatic L4 retries: after a cell failure, the partial artifact records
the error and missing IDs, and rerunning the identical command resumes only
those missing cells. Final analysis requires the exact Cartesian grid: any
missing, duplicate, unexpected, invalid-key, non-finite, or integrity-failed
cell blocks `confirmatory_ready` and leaves the verdict pending. Each payload
records measured worker runtime and its resource request for the development
cost calibration. The dry run executes a CPU-only pinned-image/Volume
round-trip preflight but no GPU training. A CPU control step scans checkpoints
before dispatch, so completed cells never consume L4 slots; `--inspect` exposes
reusable, invalid, missing, and actively leased cells without dispatch. An
atomic expiring lease prevents overlapping launches from training the same
manifest cell, and every checkpoint records its launch/lease attempt. Another
CPU step prefetches each missing immutable model snapshot once. Remaining
cells submit largest-model and regularizer work first to reduce the long tail,
while the available payload is restored to frozen manifest order.

Status: the 70m/n=13/one-seed validation smoke passed all integrity gates; see
`results/e5_smoke_summary.md`. It is not scientific evidence. E5 remains
confirmatory-pending, and no mechanism verdict is claimed. The no-compute
launch audit is recorded in `results/e5_launch_readiness_2026_07_10.md`.
### M4 — Suite C Allocate × Cool × Reopen Factorial

The timestamped follow-up addendum is
[`suite_c_factorial_ablation_preregistration_2026_07_09.md`](../world_responds/suite_c_factorial_ablation_preregistration_2026_07_09.md).
It crosses all eight component settings in the real existing
`burst_then_refractory` Suite C workflow over eight paired seeds, freezes
detect/saturate, and reruns all original controls with exact per-seed matched
probe budgets.

```bash
python3 -m experiments.world_responds.suite_c_factorial_ablation \
    --seeds 20260709,20261712,20262715,20263718,20264721,20265724,20266727,20267730 \
    --out artifacts/world_responds/suite_c_factorial_ablation_2026_07_09.json \
    --summary-json experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.json \
    --summary-md experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.md
```

**Strict verdict: FAIL.** All-on and transported controls pass, and removing
`reopen` kills terminal success (8/8 → 0/8; main effect +1.0). Removing either
`allocate` or `cool` leaves success at 8/8 (both terminal main effects 0.0);
all terminal interaction contrasts are 0.0. Allocation still improves
selectivity (17.188 vs 4.125) and probe cost (23.1 vs 27.1), but the current
criterion does not make it necessary. The strong M4 load-bearing subset claim
is rejected for this finite harness; only reopen is established as necessary.
See `results/m4_suite_c_factorial_ablation_2026_07_09.{json,md}`.

## Rebuild the paper PDF

```bash
python3 scripts/make_commitment_surface_figures.py
python3 scripts/build_commitment_surface_pdf.py
```

Reads committed result JSON from `results/` (local raw artifacts are fallback
inputs only), regenerates figures under
`papers/commitment_surface/figures/`, renders all E1–E4 cells in Appendix A.2,
and writes byte-identical outputs to `papers/commitment_surface/paper.pdf` and
`papers/pdf/commitment_surface.pdf`.
