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
