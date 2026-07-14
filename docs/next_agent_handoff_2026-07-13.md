# Start Here — Handoff for Building the Self-Improvement / Continual-Learning Experiments (2026-07-13)

You are picking up the **commitment-surface** research program at the point where it
crosses from *static verification* into *learning dynamics*. Four experiments are
**pre-registered and frozen** but **not yet built or run**. Your job: implement each
harness, run the cheap calibration, then the confirmatory grid under the frozen gates,
summarize honestly, and update the paper + docs. Read this whole note before acting.

> **Execution update (audited 2026-07-14):** E7 is built and its frozen CPU
> confirmatory grid completed, but the original shared-barrier timing audit
> could not detect per-arm divergence. The recorded per-arm estimator fails
> 6/32 matched groups (maximum 8.53% versus 2%), so the run is **INVALID** and
> G1–G4 are withheld; there is no scientific verdict. See
> `experiments/commitment_surface/results/e7_selective_subspace_2026_07_13.md`.
> Treat the original “not yet built” language below as the historical handoff state.
>
> **M5 update (2026-07-14):** the five-arm, eight-seed CPU grid is complete
> with a byte-identical rerun. Strict verdict **FAIL**: F0/F1/F4/F5 pass; F2
> fails because periodic reopening ties commitment latency at zero, and F3
> fails because the normalized trigger ties zero false-reopen by never firing.
> Canonical result:
> `experiments/commitment_surface/results/m5_suite_c_reopen_reset_trigger_2026_07_14.md`.

> Human director: **Jawaun Brown**. All code/results are AI-agent-generated under his
> direction and review. Keep provenance honest, report negatives, do not overclaim, and
> never put model identifiers in committed artifacts.

---

## 0. Orient (10 minutes, in this order)

1. **Thesis.** Availability of a structure ≠ it being load-bearing. A representation is
   real for a deployment only if a train-time compatibility intervention with the
   deployment generator produces a causal **patch-CE** effect at a **commitment surface**
   that survives **gauge-fixing** and **change of commitment `T`**. Weakness/geometry are
   diagnostics, load-bearing only when the probe group equals the deployment generator.
2. **Read the paper:** `papers/commitment_surface/paper.md` (abstract + §3 formal reframe,
   §5 experiments E1–E4, §6 Suite C). This is the spine the four new experiments extend.
3. **Where the program stands (as of this handoff):**
   - E1–E4 done; two pre-registered gates *strictly failed* and are reported as failures
     (E1 ±0.05 band; E4 Arm-A ≤0.10 ceiling). Honesty discipline: failures stay failures.
   - **#344** landed a **width-stable, spectral-mass-normalized compatibility subspace**
     with a validated group-specific causal effect (widths 96/128). Code:
     `experiments/commitment_surface/e2_e3_neural_sweep.py`; prereg:
     `papers/commitment_surface/e2_e3_rank_normalized_patch_preregistration_2026-07-10.md`.
     **E7 protects exactly this subspace.**
   - **E5** (generator-vs-coverage) is complete: all 135 cells pass integrity
     and the strict verdict is **coverage**. Cov/B-ref canonical OOD is
     0.741/0.741 versus G-reg/A-ref 0.063/0.069; generator,
     group-specificity, and transport gates fail. E5-L and E6 reuse
     this harness. Code: `experiments/commitment_surface/e5_core.py`,
     `experiments/commitment_surface/modal_e5_generator_vs_coverage.py`.
   - **Suite C** 2³ factorial found **only `reopen` is necessary** (M4, strict FAIL of the
     strong decomposition). Code: `experiments/world_responds/suite_c_factorial_ablation.py`,
     `suite_c_contract.py`. **M5 tests `reopen` as a plasticity-reset trigger.**
4. **Verification/provenance system (how the repo stays trustworthy):** every experiment
   has `experiments/<name>/PROVENANCE.md`; index is `docs/verification.md`; regenerate all
   cards with `python scripts/gen_provenance.py`; reproduce with
   `python scripts/regen.py <name>` (`regen.py list` shows the command each runs).
5. **Doc-sync is mandatory** (`AGENTS.md`): any meaningful change updates
   `docs/system_design.md` AND `docs/module_explainer.md` in the same commit series.

---

## 1. The four frozen preregistrations (what to build)

All four freeze **strict gates, no post-hoc threshold retuning, explicit claim boundaries,
rejected alternatives**, and **authorize NO GPU/confirmatory spend** — you must run a cheap
dev calibration and cost it before any confirmatory grid. Build them in the order below;
E6 is the flagship (it's the one that answers "is this a self-improvement objective, not
just verification?").

### E6 — Commitment-surface reward vs self-consistency reward *(flagship, build first)*
- **Prereg:** `papers/commitment_surface/e6_commitment_reward_self_training_preregistration_2026-07-13.md`
- **Claim tested:** replacing a self-consistency reward with a *commitment-surface-survival*
  reward (patch-CE at the `(a+b) mod n` commitment surface, surviving change-of-commitment
  `T`) prevents the self-reward **collapse** that SRT (arXiv:2505.21444) reports.
- **Reuse:** E5 harness (Pythia-LoRA modular addition, arms/exposure ledger, spectral-mass
  patch), #344 normalized subspace patch-CE, E5 generator-vs-coverage separator.
- **Build:** a multi-round self-training loop (R=6) with arms **SC** (self-consistency,
  expected collapse), **CS** (commitment-surface reward), **GT** (ground-truth ceiling),
  **A-ref** (frozen no-train). SC and CS must consume the **identical frozen candidate
  pool `P_r`** each round and select the same candidate count — so any difference is the
  reward, not data volume.
- **Gates:** G1 no-collapse (CS final canonical OOD ≥ peak − 0.05; SC expected to fail) ·
  G2 load-bearing gain (CS normalized patch-CE non-decreasing, final ≥ 0.05) · G3 transport
  survival (paraphrase lift ≥75% of canonical) · G4 not-mere-coverage (per-round generator
  gain − coverage gain ≥ 0.10) · G5 exposure integrity (matched pools) · integrity I1–I4
  (split disjointness, zero held-out-label leakage into the CS reward, matched pools,
  spectral-mass ±0.02). Base seed `20260713`, SHA-256 namespaced per round.

### E5-L — Longitudinal generator-vs-coverage *(build second; shares E6 loop scaffolding)*
- **Prereg:** `papers/commitment_surface/e5_longitudinal_self_training_preregistration_2026-07-13.md`
- **Claim tested:** self-training collapse/plateau onset coincides with a round where
  **coverage-gain continues but generator-gain stalls/reverses** (compounding memorized
  coverage, not capability). Runs the E5 separator **per round** inside a STaR/ReST loop.
- **Reuse:** `e5_core.py` arms (G-reg/B-ref/W-reg/Cov/A-ref), leakage contract, novel-shift
  + paraphrase transport splits. Add a round index `r=1..6`.
- **Grid:** 810 cells (6 rounds × 3 sizes × 3 moduli × 3 seeds × 5 arms). Base seed `20260713`.
- **Gates:** G1 per-round separator integrity (else round is void, **rerun never relabel**) ·
  G2 predictive onset (a-priori detector on transport-enforced OOD; onset round has
  cov_gain > 0 AND gen_gain ≤ 0.02; Wilson 95% LB > 0.5 across cells) · G3 group-specificity
  (G-reg beats W-reg ≥ 0.10) · G4 transport (gains measured on novel-shift/paraphrase only).

### E7 — Selective load-bearing subspace continual learning *(build third; CPU-scale)*
- **Prereg:** `papers/commitment_surface/e7_selective_subspace_continual_learning_preregistration_2026-07-13.md`
- **Claim tested:** protecting **only** the #344 compatibility subspace across a task stream
  beats uniform EWC on the stability-plasticity frontier — i.e., the load-bearing/footprint
  asymmetry escapes the *uniform* trade-off.
- **Reuse:** `e2_e3_neural_sweep.py` MLP setup (widths {96,128}, depth 2), the identified
  between-orbit subspace fit + spectral-mass normalization.
- **Build:** a K-task sequential stream (moduli/group shifts). Arms: **P_sub** (protect the
  compatibility subspace), **P_ewc** (uniform Fisher baseline), **P_none** (forgetting
  floor), **P_wrong** (protect the a-only WRONG subspace; must NOT help). Match
  param/compute budget across arms. Base seed `202607131200`, 4 seeds/arm.
- **Gates:** G1 stability (P_sub retains earlier-task patch-CE over P_none ≥ +0.05, both
  widths) · G2 no plasticity tax (P_sub new-task OOD ≥ P_ewc − 0.02) · G3 joint frontier
  dominance · G4 specificity (P_wrong does not reproduce the stability edge). All at both widths.

### M5 — Suite C `reopen` as a plasticity-reset trigger *(build fourth; CPU-scale, cheapest)*
- **Prereg:** `experiments/world_responds/suite_c_reopen_reset_trigger_preregistration_2026-07-13.md`
- **Claim tested:** commitment-change `reopen` is a better plasticity-reset trigger than
  internal-statistic resets (continual-backprop utility, self-normalized, periodic).
- **Reuse:** existing `burst_then_refractory` Suite C workflow (`suite_c_factorial_ablation.py`,
  `suite_c_contract.py`), M4's 8 paired seeds `[20260709, 20261712, 20262715, 20263718,
  20264721, 20265724, 20266727, 20267730]`, matched per-seed probe budgets, transported
  C1–C6 + false-calm controls. Freeze detect+saturate ON, allocate=0/cool=0.
- **Build:** swap **only the reopen/reset TRIGGER**: **T_commit** (commitment-change),
  **T_util**, **T_norm**, **T_periodic**, **T_none** (floor, expect 0/8). Everything else identical.
- **Gates:** F0 integrity + matched budgets + transported controls · F1 T_commit 8/8 ·
  F2 latency ≤ each internal trigger by ≥1 step · F3 false-reopen rate on false-calm strictly
  below internal triggers by ≥0.10 (specificity) · F4 no internal trigger Pareto-dominates ·
  F5 T_none 0/8. Strict verdict from F0–Fn only.

---

## 2. How to run things (conventions you must follow)

### House Modal pattern (E6, E5-L; GPU)
Every sweep is a self-contained `@app.function` worker dispatched from a
`@app.local_entrypoint` via `.map()`. The E5 entrypoint
(`modal_e5_generator_vs_coverage.py`) is the template — copy its structure for E6/E5-L.
Dispatch:
```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run <entrypoint.py> <--flags>
```

### Confirmatory discipline (do NOT skip — it is the point of the program)
The E5 entrypoint enforces the pattern you must mirror in E6/E5-L:
- Exactly one of `--dry-run`, `--inspect`, `--execute` is required.
- `--execute` needs an explicit `--max-gpu-cells` cap; confirmatory execution also requires
  acknowledging the computed `--expected-manifest-id`.
- Only the exact frozen Cartesian grid may leave `verdict=pending_confirmatory_grid`; every
  cell needs valid metadata, finite/range-valid metrics, and passing integrity.
- **Sequence for each GPU experiment:** (1) `--dry-run` to freeze the manifest ID; (2) run
  the documented **dev calibration** (E5's is 45 cells: sizes×moduli×seeds subset, all 5
  arms, non-confirmatory) to prove non-floor behavior and get timing/billing; (3) cost the
  full grid; (4) only then `--execute` the confirmatory grid with the manifest ID.
- **Do not tune any gate threshold from the calibration.** A smoke/calibration can never
  promote a verdict.

### CPU-scale (E7, M5)
Run locally under `uvx --python 3.12 --with numpy ...`. M5 mirrors
`suite_c_factorial_ablation.py`'s local entrypoint (paired seeds, `--summary-json` +
`--summary-md`). Confirm **byte-identical SHA-256** on a rerun (M4 does this).

### Results / artifacts split (public-safe)
- Raw JSON → **gitignored** `artifacts/commitment_surface/…` and `artifacts/world_responds/…`.
- Committed human-readable summary → `experiments/<name>/results/*.md` (+ compact public JSON).
- **Never** commit raw function tables, input lists, truth vectors, or model metadata — see
  the E4 public-safe appendix export and `scripts/publication_guard.py` for the contract.

---

## 3. Definition of done (per experiment)

1. Harness implemented; deterministic; unit tests under `tests/` (mirror
   `tests/test_commitment_surface_e5.py`, `tests/test_world_responds_suite_c_factorial.py`).
2. Dev calibration run + costed (GPU experiments); confirmatory grid executed under the
   frozen gates; every gate verdict reported — **failures reported as failures**.
3. `experiments/<name>/results/<name>.md` written with the exact run command, gate verdicts,
   claim level, and claim boundary. Compact public JSON committed; raw JSON gitignored.
4. `paper.md` §5/§6 updated with the confirmed numbers (or the honest negative); figures +
   PDF rebuilt (`scripts/make_commitment_surface_figures.py`,
   `scripts/build_commitment_surface_pdf.py`); both PDF destinations byte-identical.
5. `python scripts/gen_provenance.py` run; `PROVENANCE.md` + `docs/verification.{md,json}`
   refreshed.
6. `docs/system_design.md` + `docs/module_explainer.md` updated (AGENTS.md requirement).
7. `python3 scripts/run_quality_checks.py` passes (unit tests + compileall + publication
   guard + Ruff + ty). Small reviewable commits.

---

## 4. Gotchas & pins

- **Modal client version is pinned** in the E5 entrypoint (`MODAL_CLIENT_VERSION`); invoke
  `uvx` with the pinned version or the run aborts. Model revisions are frozen in
  `MODEL_REVISIONS` — keep them immutable.
- **E5 memory:** the 410m grid only fits on L4 because consistency is backpropagated one
  pair-microbatch at a time and candidate evaluation is chunked (`#345`). Preserve this in
  E6/E5-L — do not accumulate the full graph.
- **W-reg must share G-reg's exact supervised exposure and `(source_input, intervention_id)`
  schedule** (`#346`), or a group-specificity win is confounded by regularization volume.
- **Publication guard false-positives:** three Inquiry test fixtures historically tripped
  the secret heuristic; `#341` fixed the signatures — if the guard fails on unrelated files,
  check it's not a regression before weakening any signature.
- **PDF builds** need `uvx --python 3.12 --with reportlab --with matplotlib --with numpy`.

---

## 5. Suggested first move

Build **E6** first: it reuses the most existing machinery (E5 loop + #344 subspace + E5
separator), and it is the single highest-signal test of whether the commitment-surface
criterion governs *learning dynamics* and not just static reasoning verification. Start by
copying `modal_e5_generator_vs_coverage.py` into `modal_e6_commitment_reward.py`, add the
R-round loop and the SC/CS/GT/A-ref reward arms, wire the dry-run→inspect→execute manifest
discipline, write `tests/test_commitment_surface_e6.py`, then run the dev calibration.

Everything you need is frozen. Do not retune gates. Report what happens.
