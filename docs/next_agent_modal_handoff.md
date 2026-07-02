# Start Here — Modal Handoff for a Fresh Agent (2026-07-01)

You are picking up an active research program. The human (Jawaun Brown) is now on a machine with
**Modal + Doppler access**, so the CPU-scale bottleneck is gone — the job is to run the three
flagship experiments **at scale on Modal, in parallel**, resolve the one open "Newton" question,
and rewrite the papers with the confirmed numbers. This note tells you exactly what's done, what
remains, how to run it, and where everything lives. Read it fully before acting.

## 0. Orient yourself first (5 minutes)

- **Program thesis:** adaptive systems keep rediscovering geometry because geometry is the portable
  language of constraints. Synthesis: [`notes/weakness_topology_program_synthesis.md`](../notes/weakness_topology_program_synthesis.md).
- **Verification/provenance system** (read this — it's how you keep the repo trustworthy):
  every experiment has `experiments/<name>/PROVENANCE.md`; the index is
  [`docs/verification.md`](verification.md); regenerate all cards with `python scripts/gen_provenance.py`;
  reproduce any experiment with `python scripts/regen.py <name>` (`... list` shows how each runs).
- **Papers as PDFs:** [`papers/pdf/`](../papers/pdf/), rebuilt by `scripts/build_weakness_pdf.py`,
  `scripts/build_gridcell_pdf.py`, `scripts/build_paperB_pdf.py` (toolkit `scripts/paperkit.py`).
- **Public site** (`sites/reafference_attribution/`) has a live `#findings` and `#verification`
  page; it auto-deploys from `main` on Railway.
- **House Modal pattern:** every sweep is a self-contained `@app.function` worker dispatched from a
  `@app.local_entrypoint` via `.map()`. Dispatch with:
  ```
  doppler --scope /Users/jawaun/superoptimizers run -- \
      uvx --python 3.12 --from modal modal run <entrypoint.py> <--flags>
  ```
- **Attribution/honesty rules:** results are AI-agent-generated under human direction — say so.
  Report honest negatives. Do **not** overclaim. Do **not** put model identifiers in committed
  artifacts. Pre-register before large sweeps; commit result reports (summaries), keep raw JSON
  gitignored.

## 1. The three experiments — current state

### Experiment 1 — Weakness Predicts OOD (flagship). STATUS: strong, ~submittable.
- Files: `papers/weakness_invariance_neurips/paper.md`, `papers/pdf/weakness_predicts_ood.pdf`,
  `experiments/symbolic_weakness/` (+ `modal_neural_sweep.py`, already run at 1024 models).
- Result: weakness (equivariance-count of the learned function) predicts OOD where loss/MDL/
  flatness/validation fail — 100% vs 0% on cyclic/dihedral; neural Pearson r ≈ +0.81 (256 & 1024
  models); **causal** +51.5pp from data-inferred augmentation; vision ℤ₈ r = +0.67. Honest
  negatives (parity, Sₙ; language latent→behavior fails at Pythia-70M).
- **Honest novelty caveat:** the neural correlation is close to prior art (Gruver et al. 2023, "Lie
  Derivative for Measuring Learned Equivariance") and is partly definitional on symmetry tasks. Its
  upgrade is (a) the PAC-Bayes/Fourier theory it lists as future work, and (b) the **grid-cell
  scale-up = Experiment A**, which is the genuinely novel extension.
- **Modal TODO:** low priority. Optionally derive the weakness↔PAC-Bayes bound (theory, no compute).

### Experiment A — Weakness Predicts Toroidal Topology (Paper A). STATUS: registered report; CPU-confirmed 2 of 6 gates.
- Files: `papers/pdf/weakness_predicts_topology.pdf`, `papers/grid_cell_weakness/preregistration.md`
  + `runbook.md`, `experiments/grid_cell_weakness/{core,run_local}.py`,
  **`modal_grid_cell_weakness_sweep.py` (ready to dispatch)**.
- CPU result (`results/local_cpu_sweep_2026_06_29.md`): **G5 confirmed** (weakness↔spectral
  concentration ρ=+0.89) and **G6 confirmed** (topology causal contrast: full-translation toroidal
  score 0.27 vs none 0.00). **NOT confirmed:** G2 (weakness↔topology, only ρ=+0.37 at n=6), G3
  (weakness↔OOD — the same-arena OOD proxy saturated at 0.95–0.98), G4 (topology mediates).
- **Modal TODO (ready now):** run the full sweep — it has larger-arena OOD (`--decode-arenas`), 2
  archs, 8 seeds, 4000 steps — which is exactly what G2/G3/G4 need:
  ```
  doppler --scope /Users/jawaun/superoptimizers run -- \
      uvx --python 3.12 --from modal modal run \
      experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py \
      --seeds 8 --steps 4000 --decode-arenas 1.0,1.25,1.5,2.0 \
      --out artifacts/grid_cell_weakness/sweep.json
  ```
  First run the emergence probe in the runbook (`--seeds 2 --steps 4000 --conditions
  full_translation`); if `betti_match_torus` is < ~0.6, raise steps / `--activity-reg` before trusting
  gates. Tune **only** against `betti_match_torus`, never the gate correlations.

### Experiment B — Concern Deforms the Metric (Paper B). STATUS: proof-of-concept n=3; big-n pending.
- Files: `papers/pdf/concern_deforms_metric.pdf`, `experiments/grid_cell_weakness/reward_deformation.py`
  (+ `dump_fields.py`, `dump_manifold.py`), `results/reward_deformation_2026_06_29.md`.
- Result (n=3, CPU): a reward **causally warps the induced metric at the rewarded location and
  tracks it when moved** — control-subtracted specificity +0.65 / +1.27, no-reward control flat
  +0.04; local resolution bought at the cost of larger-arena OOD (0.60 → 0.41–0.45). Honest
  negative: the local-*weakness* leg is confounded (positional baseline), not claimed. This is the
  program's one **non-circular** result (reward is an injected, independent variable).
- **Modal TODO (ready now):** the big-n validation is folded into the Newton sweep below (it reports
  specificity per seed with bootstrap CIs across many seeds + geometries).

## 2. The Newton experiment — the holy grail, already half-done

This is where the program either becomes Newtonian or stays Kepler. **Read
[`notes/reward_deformation_ratedistortion.md`](../notes/reward_deformation_ratedistortion.md) in full.**

**What's derived:** from value-weighted rate-distortion under a finite-capacity constraint, the
optimal induced metric obeys a **parameter-free law**
`√det g(x) ∝ w(x)^{d/(d+2)}` → **area-density exponent 1/2** in the 2-D arena (per-axis 1/4). This is
the first time the program predicts a geometric number *before* measuring it.

**What's tested (CPU):**
- No capacity constraint → exponent **+0.07** (fails; the network doesn't have to trade resolution).
- **+ capacity bottleneck** (unit-sphere state + finite-SNR channel) → exponent **+0.30, R²=0.44** —
  the capacity constraint is **causally validated** (0.07→0.30, ~4–5× toward 0.5, fit triples).
- **BUT the exponent plateaus at ~0.30 ≈ 1/3**, the *1-D* value, not the 2-D 1/2.
- Leading hypothesis: a radial reward drives **effectively 1-D** reallocation (d_eff ≈ 1 → 1/3).

**The decisive test (ready to dispatch — I wrote the entrypoint):**
`experiments/grid_cell_weakness/modal_reward_deformation_sweep.py` runs the capacity-bottleneck
exponent test **at scale** (Ng=256, steps=8000, finer grid, many seeds, bootstrap CIs) and sweeps
the two variables that resolve 1/3 vs 1/2:
- **Reward geometry** {`point` (radial), `stripe` (genuine 1-D), `aniso2d` (genuine 2-D)}. The
  effective-dimension hypothesis predicts **stripe → ~1/3, aniso2d → ~1/2**.
- **Implied d_eff = 2α/(1−α)**, read directly off each measured exponent.
- **Amplitude sweep** (`--amps`) to test the `(1+A)^{d/(d+2)}` peak-resolution scaling.
```
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/grid_cell_weakness/modal_reward_deformation_sweep.py \
    --seeds 10 --steps 8000 --ng 256 --np 256 \
    --geometries point,stripe,aniso2d --amps 3,6,12 \
    --out artifacts/grid_cell_weakness/reward_deformation_sweep.json
```
Smoke first: `--seeds 1 --steps 800 --geometries point --amps 6`.

**Interpretation gate (pre-register this before running):**
- If **aniso2d → α ≈ 0.5** (CI excludes 1/3) while **stripe → α ≈ 1/3**: the law is **confirmed**;
  d_eff explains the plateau; this is the program's **first confirmed out-of-sample geometric
  prediction — the Kepler→Newton step.** → write the Newton paper.
- If **all geometries plateau at ~1/3 regardless**: the 2-D law is **falsified** as stated; the code
  reallocates 1-D intrinsically. Report it honestly — that is still a real finding (a *measured*
  law, d_eff≈1), and the note's exponent should be revised to the 1-D form.
- Either way you get a clean, publishable result. Do **not** p-hack the exponent toward 0.5.

## 3. Run order (parallel — the three are independent Modal apps)

Dispatch all three in parallel (separate shells or `&`); they don't share state:
1. **Paper A gate sweep** — `modal_grid_cell_weakness_sweep.py` (validates G2/G3/G4).
2. **Newton + Paper B big-n** — `modal_reward_deformation_sweep.py` (exponent resolution +
   specificity CIs).
3. **(optional) Flagship rescale** — `symbolic_weakness/modal_neural_sweep.py` only if you want
   tighter CIs; not required.

## 4. After each sweep — the loop (do this every time)

1. Pull the JSON to `artifacts/...` (gitignored) and **write a committed result report**
   `experiments/grid_cell_weakness/results/<name>_<date>.md` with the headline numbers, the gate
   verdicts, and honest caveats (mirror the existing reports' style).
2. **Rebuild the affected PDF** and refresh committed copies:
   `python scripts/build_gridcell_pdf.py` (Paper A) / `python scripts/build_paperB_pdf.py` (Paper B),
   then `python scripts/regen.py grid_cell_weakness` copies them into `papers/pdf/` and the site.
   (Both builders read the committed result numbers / JSON; update the hardcoded prose/figures to
   the new confirmed values.)
3. **Regenerate provenance:** `python scripts/gen_provenance.py` (updates the cards + manifest + the
   site's verification page).
4. **Open a PR to `main` and merge it** (the workflow uses squash-merged PRs; keep the designated
   branch clean — reset to `origin/main` and cherry-pick your commit if it diverges).

## 5. Papers to rewrite (once the numbers are in)

- **Paper A → confirmatory.** With G2/G3/G4 filled from the Modal sweep, drop "Registered Report /
  Stage 1", report the real ρ(weakness,topology), ρ(weakness,OOD-geometry), and the mediation
  partial-correlation, with the gate-margin heatmap. Builder: `build_gridcell_pdf.py`.
- **Paper B → big-n + a derived law.** Replace n=3 with the multi-seed specificity + bootstrap CIs
  and a significance test; **and fold in the rate-distortion law** as the theoretical spine (this is
  the big upgrade — Paper B stops being "a phenomenon" and becomes "a phenomenon + a derived law +
  a measured exponent"). Builder: `build_paperB_pdf.py`.
- **New paper (if the exponent confirms): "A Rate-Distortion Law for Value-Driven Metric
  Deformation."** The Newton paper. Its abstract is the parameter-free prediction and the confirmed
  exponent across reward geometries. Only write it if aniso2d actually hits ~1/2 (or write the
  honest "measured d_eff≈1 law" version otherwise).
- **Flagship** stays as-is; optionally add the PAC-Bayes/Fourier theory section and cite Paper A as
  the scale-up.

## 6. Honest guardrails (carry these into the papers)

- The flagship's core correlation is partly circular and near prior art (Lie derivative) — the novel
  weight is in Papers A/B and the Newton law.
- Paper B's specificity result is the non-circular anchor; keep the local-weakness leg out until a
  positional control clears it.
- The Newton exponent is **not yet confirmed at 1/2**; do not claim a "law" until aniso2d clears
  the 1/3-vs-1/2 gate. A measured 1-D law is a fine, honest alternative outcome.
- Update `notes/reward_deformation_ratedistortion.md` §8 with whatever the Modal sweep actually
  shows, including a falsification if that's the result.

---
**One-line status:** all three sweeps are coded and dispatch-ready; the only thing between the
program and its first "Newton" (a confirmed, parameter-free geometric prediction) is running
`modal_reward_deformation_sweep.py` and seeing whether the `aniso2d` exponent reaches 1/2.
