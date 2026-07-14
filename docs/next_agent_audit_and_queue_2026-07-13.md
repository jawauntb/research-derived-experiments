# Handoff — Audit What's Running, Then Queue What Isn't (2026-07-13)

**Purpose.** This is a copy-paste handoff for another agent. Its job is NOT to blindly
start work. It is to **first audit what is already in flight** — across git worktrees and
Modal — for the four self-improvement / continual-learning experiments, and **only queue or
launch the pieces that are not already being done.** Do not duplicate a run that is already
executing or already queued.

> Paste everything below the line into the receiving agent. It is self-contained.

---

## PASTE-TO-AGENT BEGINS

You are picking up the **commitment-surface** research program in
`jawauntb/research-derived-experiments`. Four experiments are pre-registered and frozen;
some harness/infra has been merged; **nothing has produced a scientific result yet.** Your
mission has two phases, in order:

1. **AUDIT** — determine what is actually running or queued right now (git worktrees + Modal
   apps + committed results). Report it.
2. **QUEUE** — for anything that is frozen-and-ready but NOT running and NOT queued, start it
   (or, if it needs a runner built first, build the runner). Never duplicate live work.

Human director: **Jawaun Brown**. All code/results are AI-agent-generated under his review.
Report honest negatives, do not overclaim, never put model identifiers in committed artifacts.

### 0. Context you need (thesis + state)

**Thesis.** Availability of a structure ≠ it being load-bearing. A representation is real for
a deployment only if a train-time compatibility intervention with the deployment generator
produces a causal **patch-CE** at a **commitment surface** that survives **gauge-fixing** and
**change of commitment `T`**. Paper: `papers/commitment_surface/paper.md`. Deep build handoff:
`docs/next_agent_handoff_2026-07-13.md` (read it — per-experiment build specs + gates).

**The four frozen preregistrations** (gates are frozen; do NOT retune thresholds):
- **E6** — commitment-surface reward vs self-consistency reward in a self-training loop
  (tests whether the criterion prevents self-reward collapse).
  `papers/commitment_surface/e6_commitment_reward_self_training_preregistration_2026-07-13.md`
- **E5-L** — longitudinal generator-vs-coverage per self-training round (tests whether
  collapse onset coincides with coverage-gain-without-generator-gain).
  `papers/commitment_surface/e5_longitudinal_self_training_preregistration_2026-07-13.md`
- **E7** — selective load-bearing subspace protection for continual learning (protect the
  #344 subspace vs uniform EWC).
  `papers/commitment_surface/e7_selective_subspace_continual_learning_preregistration_2026-07-13.md`
- **M5** — Suite C `reopen` as a plasticity-reset trigger.
  `experiments/world_responds/suite_c_reopen_reset_trigger_preregistration_2026-07-13.md`

**Known state as of this handoff (verify it — do not trust it blind):**
| Experiment | Prereg | Harness | Run/result |
|-----------|:------:|:-------:|:----------:|
| E6 | ✅ | ⚠️ CPU scaffold + tests only (`e6_core.py`, `e6_analysis.py`, `tests/test_commitment_surface_e6.py`); **no Modal runner** | ❌ none |
| E5 confirmatory (135-cell) | ✅ | ✅ runner + remote orchestrator | ✅ exact grid complete; strict verdict **coverage** |
| E5-L | ✅ | ❌ not built | ❌ |
| E7 | ✅ | ❌ not built | ❌ |
| M5 | ✅ | ❌ not built | ❌ |

E5 completed after the detached-orchestrator repair: 135/135 cells passed
integrity. Cov and B-ref match at 0.741 canonical OOD, G-reg/A-ref remain at
0.063/0.069, and generator, group-specificity, and transport gates fail. Do
not relaunch E5; use the committed public result.

---

### 1. PHASE 1 — AUDIT (run these, report findings, do not mutate anything)

**1a. Sync and see the repo's own record.**
```bash
git fetch origin --prune
git log --oneline origin/main -15
git ls-tree -r --name-only origin/main -- experiments/commitment_surface/results/ | sort
# Look for NEW result docs: e6_*, e5_generator_vs_coverage*, e5_confirmatory*, m5_*, e7_*.
# e5_generator_vs_coverage.{json,md} is the result; launch_readiness/smoke are provenance only.
```

**1b. Inspect git worktrees + in-flight branches (is a runner being built right now?).**
```bash
git worktree list                      # other worktrees = another agent may be mid-build
git branch -a --sort=-committerdate | head -30
# scan for active work per experiment:
git branch -a | grep -iE 'e6|e5.?l|longitudinal|e7|subspace|continual|m5|reopen|reset'
# for any candidate branch, how far ahead of main is it, and is it stale?
#   git log --oneline origin/main..origin/<branch>
```
Also check open PRs (these are the queued-for-merge work):
```bash
# via GitHub MCP: list open PRs for jawauntb/research-derived-experiments, state=open,
# sort=updated. An open PR touching e6_/e5_/e7_/suite_c_reopen is work already in flight.
```

**1c. Query Modal — is a grid actually computing right now?** (needs Doppler + Modal access.)
```bash
# All apps and their state (running / stopped) for the workspace:
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal==1.2.6 modal app list

# E5 confirmatory STATUS ONLY — no GPU dispatch, no model prefetch.
# Reports reusable / invalid / missing cells and active leases:
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal==1.2.6 modal run \
    experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
    --base-seed 20260709 --run-kind confirmatory --inspect \
    --out artifacts/commitment_surface/e5_confirmatory_status.json
```
Interpretation of the E5 `--inspect` output:
- **active leases > 0** → cells are being trained *right now*. Do NOT relaunch. Monitor.
- **missing = 135, 0 leases, 0 reusable** → nothing running, nothing done → it is NOT queued;
  proceed to launch (Phase 2, E5).
- **reusable = N (0 < N < 135), 0 leases** → a prior partial run exists but nothing is live;
  rerunning the identical `--execute` command submits ONLY the missing cells (idempotent).

**1d. Report the audit** before doing anything else: for each of E6 / E5 / E5-L / E7 / M5,
state one of: `RUNNING`, `QUEUED (open PR / worktree)`, `READY-NOT-STARTED`, or
`NEEDS-RUNNER-BUILT`. Include the evidence (app name + lease count, branch name, PR number).

---

### 2. PHASE 2 — QUEUE / LAUNCH (only for items the audit found NOT already in flight)

Apply per experiment. **Skip any experiment the audit marked RUNNING or QUEUED.**

**E5 confirmatory (if READY-NOT-STARTED):** follow the frozen launch discipline — never skip
a step, never tune a gate.
```bash
# 1) Freeze/confirm the manifest id (dry-run, no GPU):
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal==1.2.6 modal run \
    experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
    --base-seed 20260709 --run-kind confirmatory --dry-run \
    --out artifacts/commitment_surface/e5_confirmatory_launch_manifest.json
# 2) Run the 45-cell development calibration (non-confirmatory) to prove non-floor behavior
#    and get timing/billing. Do NOT tune any gate from it:
doppler ... modal run ... --base-seed 20260709 --run-kind development \
    --execute --max-gpu-cells 45 --out artifacts/commitment_surface/e5_development_calibration.json
# 3) Cost the full 135. Then execute the confirmatory grid, acknowledging the manifest id:
doppler ... modal run ... --base-seed 20260709 --run-kind confirmatory \
    --execute --max-gpu-cells 135 --out artifacts/commitment_surface/e5_generator_vs_coverage.json
```
Exactly one of `--dry-run|--inspect|--execute` is required; `--execute` needs
`--max-gpu-cells`; confirmatory also requires acknowledging the expected manifest id. Only the
exact 135-cell grid may leave `verdict=pending_confirmatory_grid`. A smoke/calibration can
NEVER promote a verdict.

**E6 (NEEDS-RUNNER-BUILT):** the CPU scaffold (`e6_core.py`, `e6_analysis.py`, tests) is
merged; the **Modal training runner does not exist**. Build `modal_e6_commitment_reward.py`
by copying `modal_e5_generator_vs_coverage.py` (reuse its dry-run/inspect/execute manifest
discipline, its microbatched-consistency memory path, and the pinned `modal==1.2.6` /
frozen `MODEL_REVISIONS`). Wire the R=6 SC/CS/GT/A-ref loop from `e6_core.py`; SC and CS must
consume the identical frozen candidate pool per round (assert equal pool digest + selected
count). Run `python3 -m unittest tests.test_commitment_surface_e6`, then the dev calibration
before any confirmatory spend. Open a PR when the runner + tests are green.

**E5-L (NEEDS-RUNNER-BUILT):** extend the E5 runner with a per-round separator emitting
generator-gain / coverage-gain / group-specificity / normalized patch-CE each round; 810
cells; keep the E5 anti-leakage contract every round. Prereg has the gates.

**E7 (NEEDS-RUNNER-BUILT, CPU):** build on `e2_e3_neural_sweep.py`; arms P_sub/P_ewc/P_none/
P_wrong over a K-task modular stream at widths {96,128}; protect the #344 subspace. CPU-scale
— can run without GPU access.

**M5 (NEEDS-RUNNER-BUILT, CPU, cheapest):** build on `suite_c_factorial_ablation.py`; swap
only the reopen/reset TRIGGER (T_commit/T_util/T_norm/T_periodic/T_none); reuse M4's 8 paired
seeds and matched budgets + false-calm control. Confirm byte-identical SHA-256 on rerun.

---

### 3. Rules that apply to everything (do not violate)

- **No gate retuning.** Every prereg's thresholds are frozen. A failed gate is reported as a
  failure, not repaired.
- **Confirmatory discipline.** dry-run → dev calibration → cost → execute-with-manifest-id.
  A smoke/calibration cannot emit a scientific verdict.
- **Public-safe split.** Raw JSON → gitignored `artifacts/…`; committed human summary →
  `experiments/<name>/results/*.md` (+ compact public JSON). Never commit raw function tables,
  input lists, or model metadata. `scripts/publication_guard.py` enforces this.
- **Definition of done** (per experiment): harness + unittests; dev calibration + confirmatory
  run under frozen gates; `results/<name>.md` with run command + gate verdicts + claim
  boundary; `paper.md` §5/§6 updated; figures + PDF rebuilt byte-identical;
  `python scripts/gen_provenance.py`; update `docs/system_design.md` + `docs/module_explainer.md`
  (AGENTS.md); `python3 scripts/run_quality_checks.py` green.
- **Pins/gotchas.** `modal==1.2.6`; frozen `MODEL_REVISIONS`; 410m only fits L4 via
  microbatched consistency + chunked candidate eval; W-reg must share G-reg's exact supervised
  exposure and `(source_input, intervention_id)` schedule; orchestrator caps 12 concurrent
  containers and de-dupes completed cells before dispatch.

### 4. First action
Do **Phase 1 (audit) in full and report it** before touching Phase 2. If the audit shows E5
already RUNNING (leases > 0) and E6 has an open PR, then the only NOT-in-flight, GPU-free work
is **E7 and M5** — start there. Pick the highest-value item that is genuinely idle. Never
launch a second copy of a grid that is already computing.

## PASTE-TO-AGENT ENDS
