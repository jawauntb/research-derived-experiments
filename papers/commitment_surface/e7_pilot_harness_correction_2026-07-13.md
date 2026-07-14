# E7 Pilot Harness Correction

**Recorded 2026-07-13 after the first integrity pilot and before its rerun.**

The first frozen E7 CPU pilot was invalid, as required by the preregistration:
seed, sequential-exposure, and exact protected-mass checks passed, but measured
per-task wall-clock ranges across arms were 49.8% for T1 and 42.1% for T2,
well above the frozen 2% limit. Each task took only about one to two seconds,
and the default multithreaded BLAS runtime introduced thread-pool startup and
scheduling jitter large relative to that duration. All arms still executed
exactly 1,000 optimizer steps and the same shadow-graph tensor shapes.

This is classified as a harness/runtime integrity failure, not an E7 result.
The invalid raw receipt remains local at
`artifacts/commitment_surface/e7_pilot_2026_07_13.json` and cannot authorize a
confirmatory run.

Before rerunning, the CPU entrypoint is changed to set PyTorch intra-op and
inter-op thread counts to one before any stream executes. This removes
thread-pool scheduling as a timing confound for the small matrices. Nothing
scientific changes: λ remains the pre-run singleton 1.0; task stream, model,
splits, seeds, optimizer steps, arms, protection objects, metrics, mass rule,
and all frozen gates are unchanged. The rerun must independently pass every
integrity check before it can authorize confirmatory execution. If the 2%
wall-clock gate fails again, the pilot remains invalid and the confirmatory
grid stays blocked.

## Second invalid run and timing estimator correction

The single-thread rerun also failed closed. Its relative elapsed-time ranges
fell substantially, to 7.4% for T1 and 3.5% for T2, while exact step counts and
all non-timing integrity checks again passed. At roughly one millisecond per
step, whole-task elapsed time remains sensitive to a handful of scheduler
interruptions and does not stably estimate the matched per-step workload.

Before a third pilot, the harness is therefore frozen to record every one of
the 1,000 step durations and define the task's budget wall time as
`median_step_seconds × 1,000`. Raw start-to-finish elapsed time remains in each
checkpoint as a diagnostic and is never substituted for a scientific metric.
The unchanged 2% gate applies to this robust, per-arm wall-clock workload
estimate. This changes neither the amount of training nor the intervention;
it removes sparse operating-system pauses from the estimator of the matched
training budget. The second invalid raw receipt remains local at
`artifacts/commitment_surface/e7_pilot_rerun_2026_07_13.json`.

## Third invalid run and matched-group scheduler

The median-step pilot was also invalid: 5.3% at T1 and 4.4% at T2. The
persistent arm-order/frequency drift means a sequential four-arm scheduler
cannot demonstrate the frozen 2% wall-clock match on sub-millisecond CPU
steps, even though tensor shapes and optimizer-step counts are exact.

Before a fourth pilot, the execution scheduler is therefore changed to run the
four matched arms concurrently, one single-thread PyTorch worker per arm, with
a barrier immediately before and after each task's 1,000 updates. Each arm's
recorded task wall time is the real shared-barrier makespan from the same start
to the same completion boundary. Model construction is serialized under a
lock so the process-global PyTorch RNG still yields byte-matched
initialization. Evaluations occur after the ending barrier and all workers wait
at the next task's starting barrier, so no arm gains training steps or future
task exposure.

The audit returns to raw barrier-to-barrier elapsed time; per-step medians stay
diagnostic only. This is the direct execution of a matched four-arm compute
batch rather than a statistical correction to sequential runtimes. The third
invalid receipt remains local at
`artifacts/commitment_surface/e7_pilot_validated_2026_07_13.json`. As before,
all scientific settings and the 2% threshold remain frozen.

## Pre-confirmatory inheritance correction

The first barrier-scheduled pilot passed its four integrity gates. Its
integrity-only diagnostic metrics then made an implementation omission visible
before any confirmatory cell: the harness had trained each task without the
true cyclic compatibility augmentation. E7 explicitly inherits the #344
E2/E3 regime whose *Arm B* compatibility-aligned subspace was validated as
load-bearing. Plain strict-subset training instead produces the memorizing
control regime and does not instantiate the causal object E7 preregistered to
protect.

The harness is corrected to inherit #344's frozen `aug_orbit_size = 4`: every
epoch adds four current-task cyclic shifts with correct transported labels.
All arms receive the identical schedule from a local SHA-256-derived
`augmentation|task|matched|seed_index|width` RNG key. No earlier-task example
enters a later task's loss. The labeled-example count is recorded per
checkpoint, and the final epoch's current-task augmented batch is used for the
diagonal Fisher.

This correction is dictated by the preregistration's explicit relationship to
#344, not selected from the pilot outcome. It invalidates the otherwise-passing
receipt at `artifacts/commitment_surface/e7_pilot_passing_2026_07_13.json`; a
fresh pilot under the inherited training regime is required before the
confirmatory lock can open. λ remains 1.0 and no gate changes.

## Post-confirmatory audit: shared-makespan false pass

**Recorded 2026-07-14 during pre-PR code review, after the confirmatory cells
were visible. This is an invalidation record, not a new scientific analysis.**

The closing task barrier made the recorded `wall_clock_seconds` a shared group
makespan: faster arms waited inside the measured interval until the slowest arm
arrived. The four values were therefore nearly identical by construction. In
the completed grid their maximum relative range was only 0.0048%, so this
quantity could not meaningfully enforce the preregistered per-arm 2% limit.

Every checkpoint also retained the previously frozen robust per-arm workload
estimate, `median_step_seconds × optimizer_steps`. Reapplying the unchanged 2%
threshold to those recorded values fails 6 of 32 matched
`(width, seed, task-boundary)` groups; the maximum relative range is 8.53%.
Only 12 of 32 streams pass every task-level budget comparison. Seed,
sequential-exposure, exact protected-mass, checkpoint-count, and row-count
checks still pass.

The confirmatory artifact is therefore reclassified **INVALID — NO SCIENTIFIC
VERDICT**. G1–G4 are not evaluated, and the previously reported strict G3
failure is retracted. The all-stream metrics remain diagnostic data only and
cannot accept or reject `H_subspace`. No timing threshold, coefficient, arm,
or outcome margin is changed. A future replacement needs a new preregistration
with a non-tautological budget verifier frozen before any new outcomes are
inspected.
