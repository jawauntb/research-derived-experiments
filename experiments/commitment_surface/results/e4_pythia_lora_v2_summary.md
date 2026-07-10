# E4 — Pythia LoRA v2 Commitment-Pinned External Contact (Modal L4)

Date: 2026-07-09.
Code: `experiments/commitment_surface/modal_e4_pythia_lora_v2.py`
Pre-registration: `papers/commitment_surface/PLAN.md` §E4.
Raw payload: `artifacts/commitment_surface/e4_pythia_lora_v2.json` (gitignored;
209 KB).
Public-safe appendix export:
`experiments/commitment_surface/results/e4_pythia_lora_v2_appendix.json`
(108/108 cells; source SHA-256
`67e86aef888540ba70d013de6a2be2def1871aa0970134bd3d115e2f2dbc5428`;
no requested appendix fields unavailable).
Modal run: 3 L4 shards, one per Pythia size.

## Design

Non-degenerate follow-up to the P1 hard-kill in
`experiments/external_contact/results/p1_pythia_lora_2026_06_22.md`. Same
external system (Pythia LoRA on `(x + offset) mod n`), but with four arms
that discriminate the commitment-first frame from the old geometry / weakness
frame:

- **A** readout: standard LoRA-LM, no augmentation, post-hoc weakness score.
- **B** compatibility-augmented: LoRA-LM with cyclic-orbit augmentation of
  train pairs — for each `(x, y=(x+offset) mod n)`, add
  `((x+k) mod n, (y+k) mod n)` for random `k`.
- **C** wrong-group augmented: LoRA-LM with augmentation
  `(π(x), π(y))` for a random non-cyclic permutation `π`, teaching the
  model the wrong equivariance `f(π(x)) = π(f(x))`. Same augmentation
  *volume* as B; group specificity broken. Anti-cheat control.
- **D** loss selector: same as A on training; selected by lowest train loss.

Grid: 3 sizes × 3 moduli × 3 seeds × 4 arms = 108 cells. Train fraction 0.5;
LoRA rank 8, α 16, dropout 0.05, LR 5e-4; 160 epochs; augmentation multiplier
3 for B/C.

## Result (headline)

| Arm | n | OOD mean | OOD max | Cells ≤ 0.15 | Cells ≥ 0.5 | Patch-CE Δ mean | Weakness mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — readout | 27 | 0.113 | 1.000 | 22/27 | 2/27 | −0.742 | 0.095 |
| B — compat aug | 27 | **0.882** | 1.000 | **0/27** | **27/27** | **+4.862** | 0.305 |
| C — wrong-group aug | 27 | 0.071 | 0.222 | 26/27 | 0/27 | +1.445 | 0.060 |
| D — loss selector | 27 | 0.113 | 1.000 | 22/27 | 2/27 | −0.742 | 0.095 |

- `gap(B, A)` OOD: **+0.770**.
- `gap(B, A)` patch-CE Δ: **+5.604**.
- `gap(B, C)` patch-CE Δ (anti-cheat): **+3.417** (B causes load-bearing
  cyclic structure at the commitment surface; C does not).
- `ρ(patch-CE, OOD)` across cells: **+0.853**.
- `ρ(weakness_oracle_norm, OOD)` across cells: **+0.290**.

## Pre-registered gates

**E4 new-frame gate**: B mean OOD ≥ 0.50 AND B mean patch-CE Δ ≥ 0.05 AND
A mean OOD ≤ 0.10.
- B OOD 0.882 ✔
- B patch-CE Δ +4.86 ✔
- A OOD 0.113 ✘ (missed by 0.013; driven by 2/27 outliers, see below)

**Gate verdict: FAIL (directionally decisive, strict gate missed).** The
pre-registered A ≤ 0.10 condition failed at 0.113 and is recorded as a
failure — the outlier accounting below explains the miss, it does not
convert it into a pass. Twenty-two of twenty-seven Arm A cells sit at
OOD ≤ 0.15; two outliers stumbled into the aligned regime. The most
striking is 410m / n=17 / seed=20260709, which reaches OOD 1.000 and
weakness 1.000 without any augmentation — a textbook aligned-regime recovery
where weakness readout, patch-CE, and OOD all agree, confirming the theory at
the cell where it applies. The mean is dragged from 0.089 (excluding the 2
outliers) to 0.113 by these two cells.

**E4 old-frame gate**: A mean OOD ≥ 0.50 AND ρ(weakness, OOD) ≥ +0.5.
- A OOD 0.113 ✘
- ρ(weakness, OOD) 0.290 ✘

Old frame decisively fails.

## Interpretation

The non-aligned regime (Pythia LoRA on modular addition, LM objective) is
where Prop. 1 shows its teeth: probe/readout AUC is decoupled from causal
use. Weakness readout has *some* signal (ρ = 0.29) but is dominated by
patch-CE (ρ = 0.85). Compatibility-augmentation is the intervention that
recovers OOD, exactly as the commitment-first frame predicts (Prop. 2):
training the model to be equivariant under the deployment generator (the
cyclic group) causes load-bearing structure at the commitment surface. The
wrong-group augmentation Arm C isolates group specificity from volume: same
augmentation count, wrong group, and the model fails at both OOD and
patch-CE. Adapter LoRA is only load-bearing when what it teaches the model
is aligned with the deployment.

This substantially narrows the P1 external gap identified in the prior
program without retracting the cyclic/dihedral 100%-vs-0% weakness
positives — those become the aligned-generator special case (Prop. 2),
where E4 shows the two Arm A outliers as within-experiment witnesses.

## Interpretation caveat: label-exposure confound (open)

Arm B's cyclic augmentation `((x+k) mod n, (y+k) mod n)` produces
*correctly labeled* pairs at inputs in the held-out complement, so the
intervention arm was trained with direct labeled exposure to the OOD
support. Arm C matches augmentation volume but places *incorrect* labels
on held-out inputs; it therefore rules out generic augmentation volume,
not target-support label exposure. E4 does not yet separate "the model
learns a transportable generator and uses it at commitment" from
"aligned augmentation exposes the OOD orbit with correct labels."
The severe follow-up (train-support-only generator regularization,
coverage-matched control, evaluation on a group element/modulus not
used by the intervention, rank-normalized patching) is pre-registered
in paper §6.5 with kill criteria.

## Interpretation caveat: outlier accounting

We do not report a mean-with-outliers-removed number as the headline.
The pre-registered gate was frozen before the sweep; the honest report is
that the literal A ≤ 0.10 threshold was missed by 0.013 driven by 2/27
cells. We describe them here so any future replicator or reviewer can
locate them:

- 410m / n=17 / seed=20260709: OOD 1.000, weakness 1.000, patch-CE 4.14.
- 410m / n=23 / seed=20260809: OOD 0.455, weakness 0.043, patch-CE 2.42.

The first is the aligned-regime recovery described above. The second has
weakness at the floor (0.043) but non-zero OOD, likely a memorization /
partial-cover artifact — consistent with the prior P1 result's finding that
`ρ(ood_nll, OOD)` was the strongest classical predictor at |ρ|=0.455.

## Commands

Full sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/commitment_surface/modal_e4_pythia_lora_v2.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 --arms A,B,C,D \
        --epochs 160 --train-frac 0.5 --aug-multiplier 3 \
        --base-seed 20260709 \
        --out artifacts/commitment_surface/e4_pythia_lora_v2.json
```

Regenerate summary + figures:

```bash
python3 scripts/make_commitment_surface_figures.py
python3 scripts/build_commitment_surface_pdf.py
```
