# External Contact Runbook (laptop / network-enabled)

**Purpose.** The research container has **no network egress** (Stanford / HuggingFace /
PyPI return 403), so the three pre-registered external-contact predictions cannot be
executed there. This runbook is the step-by-step recipe to run them on a machine that
**has** network, `pip`/`uvx`, Modal, and Doppler — i.e. the user's laptop.

- Pre-registration (frozen 2026-06-18): [`docs/external_contact_preregistration.md`](external_contact_preregistration.md)
- Predictions: **P1** weakness→OOD on Pythia, **P2** uncertainty≠error on published
  ensemble/BALD curves, **P3** concept-geometry on GloVe.

**Run all commands from the repo root** (`research-derived-experiments/`).

Anti-cheat discipline carries over from the prereg (§"Shared anti-cheat discipline"):
1. No-false-calm — report every kill-criterion control alongside the headline metric.
2. Wrong-X controls are mandatory (P1 wrong-group, P2 in-dist vs shift, P3 wrong-orbit
   + All-but-the-Top centering).
3. Frozen-now numbers — all transcribed public numbers committed *before* the comparison.
4. Honest-negative is a result — a latent-signal-without-behavioral-transfer outcome is
   recorded, never silently dropped.

---

## P3 — Concept geometry on external GloVe (Tier A, fully runnable today)

### Frozen prediction (prereg P3a/P3b/P3c)

> **P3a.** GloVe-300d mean within-category cosine exceeds mean across-category cosine by
> **margin ≥ +0.10** after All-but-the-Top centering; clustering NMI vs the 6 authored
> categories **≥ 0.25**.
> **P3b.** Per-concept paraphrase weakness exceeds the wrong-orbit control by **gap ≥ +0.15**
> after centering.
> **P3c.** GloVe-100d and GloVe-300d concept×concept cosine matrices agree with
> **RSA/Spearman ρ ≥ +0.6** off-diagonal.

### Commands

The fetch helper is pure stdlib (urllib + zipfile), downloads GloVe 6B into a gitignored
`tmp/glove/`, and vendors **only the ~399 word types** the 24 concepts + paraphrases need
into `experiments/external_contact/p3_glove_subset_<D>d.txt` (the raw full table never
touches git). Tokenization is byte-for-byte identical to the harness's `tokenize()`.

```bash
# Build BOTH the 300d (P3a/P3b) and 100d (P3c cross-model RSA) subsets, then run:
python3 scripts/fetch_glove_subset.py --dims 300 100 --run
```

This downloads `https://nlp.stanford.edu/data/glove.6B.zip` (~822 MB). If Stanford 403s
or rate-limits, use the HuggingFace mirror:

```bash
python3 scripts/fetch_glove_subset.py --dims 300 100 --run \
    --url https://huggingface.co/stanfordnlp/glove/resolve/main/glove.6B.zip
```

Already have the zip? Skip the download:

```bash
python3 scripts/fetch_glove_subset.py --from-zip ~/Downloads/glove.6B.zip --dims 300 100 --run
```

The fetch step prints **how many of the needed word types were found vs missing** — note
any missing types (multi-word concepts like "basin of attraction" pool over their tokens,
so a few missing tokens is tolerable as long as each concept keeps ≥1 token).

`--run` invokes the harness; or run it by hand:

```bash
python3 -m experiments.external_contact.p3_glove_probe \
    --glove experiments/external_contact/p3_glove_subset_300d.txt \
    --glove2 experiments/external_contact/p3_glove_subset_100d.txt \
    --out artifacts/external_contact/p3_glove.json
```

Sanity-check the math first if desired (NOT a scientific result):
`python3 -m experiments.external_contact.p3_glove_probe --self-test`

### Pass / fail (per harness output JSON)

| Field | Pass when | Kill when |
|---|---|---|
| `P3a_within_across_margin_centered` + `P3a_nmi_clusters_vs_categories` | `P3a_pass == true` (margin ≥ 0.10 **and** NMI ≥ 0.25) | margin < 0.05 after centering OR NMI < 0.10 |
| `P3b_paraphrase_gap_centered` | `P3b_pass == true` (gap ≥ 0.15) | gap ≤ 0.05 after centering, OR raw gap large but vanishes after centering |
| `P3c_cross_model_rsa` | `P3c_pass == true` (ρ ≥ 0.6) | ρ < 0.3 |

Report **raw vs centered** for P3a/P3b (the prereg's strongest shortcut is raw anisotropic
cosine — credit only counts if the signal survives All-but-the-Top centering).

### Claim tier a pass earns

**Mechanism → regime transition.** A clean Tier-A pass (all three survive centering) shows
the concept-geometry claim is not an OpenAI-probe artifact. It is *not* a field claim on
its own (static word vectors are a limited substrate; full P3c convergence wants ≥3 model
families) — but it is the first concept-geometry result with genuine external contact.

---

## P1 — Weakness → OOD on the Pythia model family (Tier B, fetch-when-unblocked)

### Frozen prediction (prereg P1)

> Spearman ρ between **learned-function weakness under the true group `Z_n`**
> (`weakness_oracle_norm`, computed on the model's argmax function table over the input
> domain) and **held-out OOD accuracy** will be **ρ ≥ +0.5** and will **strictly exceed**
> the |ρ| of every classical predictor — final training loss, eval loss, parameter count,
> parameter L₂ norm, and a Hutchinson sharpness proxy — by **≥ 0.25 in |ρ|**.
> Directional: higher weakness → higher OOD. **Wrong-group control** (random permutation of
> equal size) has **|ρ| ≤ 0.15**.

### Tier-B recipe

External system: the **Pythia suite** (`pythia-70m`, `-160m`, `-410m`, `-1.4b`;
EleutherAI). External task: partial-orbit modular addition mod `n ∈ {13, 17, 23}`, train
window a strict subset of the `Z_n` translation orbit, OOD = held-out complement.

Steps (frozen seed **20260618**):

1. **Load checkpoints** via `transformers` and fine-tune a small head (linear / LoRA) on
   partial-orbit mod-`n` for each Pythia size × each `n`.
2. **Extract the argmax function table** over the full input domain `{0..n-1}²` — the
   model's learned function `f`, the same object the lab's symbolic sweep produces.
3. **Compute weakness with the lab's existing selectors, unchanged.** Feed each model's
   argmax table in as a `Candidate` and score with
   `experiments/symbolic_weakness/selectors.py`:
   - `weakness_oracle` = `equivariance_count_with_action(candidate, trial.group, trial.group)`
     under the true cyclic group `Z_n` — this is `weakness_oracle_norm` for P1.
   - `weakness_wrong_group` (its `_wrong_group_for_trial`, random equal-size permutations)
     is the **wrong-group null**.
   This reuses the lab code verbatim; only the function table now comes from an external
   model rather than a hand-built candidate.
4. **Compute the classical predictors** per model: final training loss, eval/NLL on the
   OOD inputs, parameter count, parameter **L₂** norm, and a **Hutchinson sharpness proxy**
   (Rademacher `vᵀHv`).
5. **Regress** all predictors against **held-out OOD accuracy** (Spearman ρ across the
   sweep), including the wrong-group null.

Local quick driver (CPU is enough for tiny heads):

```bash
uvx --python 3.12 --with torch --with transformers python - <<'PY'
# load Pythia, fine-tune partial-orbit mod-n head, extract argmax table,
# then: from experiments.symbolic_weakness.selectors import candidate_metrics, SELECTORS
# score weakness_oracle / weakness_wrong_group on the external function table.
PY
```

**Modal option** (mirrors `experiments/symbolic_weakness/modal_neural_sweep.py`, which
already runs sharded neural sweeps on Modal):

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/symbolic_weakness/modal_neural_sweep.py \
        --n-shards 8 --models-per-shard 64 --epochs 2000 \
        --base-seed 20260618 \
        --out artifacts/external_contact/p1_pythia_sweep.json
```

(Extend that module's image with `transformers` and swap the inline tiny-MLP for the
Pythia checkpoint load to make this the P1 external sweep; keep the sharding/merge logic.)

### Tier-A fallback (degraded, stdlib, runnable today)

Transcribe published per-model OOD accuracy from a grokking / modular-arithmetic table into
`experiments/external_contact/p1_pythia_grok_public.csv` (columns: model size, train
fraction, reported OOD accuracy). Compute a **proxy weakness** = published orbit-coverage
fraction (monotone surrogate; prereg notes none 0.14 → partial 0.32 → full 0.95).
Pre-registered: proxy-weakness Spearman ρ with published OOD **≥ +0.6**, strictly above
param-count ρ.

### Kill criterion

- **Hard kill:** any classical predictor reaches |ρ| within **0.10** of weakness's ρ, OR
  weakness ρ < +0.3 → "weakness beats classical heuristics" does not survive external contact.
- **Soft kill:** wrong-group control |ρ| > 0.25 → result is volume-dominated, not symmetry-specific.
- **Honest-negative:** latent weakness signal present but not predictive of behavioral OOD
  (the §10.2 Pythia-70M failure) → partial result, not a pass.

### Claim tier a pass earns

**Field claim** if Tier B passes (weakness on an external model's learned function beats
loss/scale/L₂/sharpness with the wrong-group null holding). **Tier A alone earns at most
regime-transition / diagnostic** (orbit-coverage surrogate, not measured neural weakness).

---

## P2 — Uncertainty ≠ error on published ensemble / BALD curves (Tier A, transcription)

### Frozen prediction (prereg P2a/P2b)

> **P2a.** For deep ensembles of *identical architecture* on CIFAR-10-C, the per-sample
> correlation between ensemble predictive variance and actual error **collapses toward zero
> (Pearson |r| ≤ 0.2)** on the high-corruption-severity / shifted slices where error is
> highest — even while positive in-distribution ("false calm").
> **P2b.** For BALD/BatchBALD on MNIST/FashionMNIST, naive-uncertainty acquisition
> underperforms an information-gain / expected-error-reduction oracle, and batch-naive BALD
> redundantly samples near-duplicates; the gap is non-zero and in the predicted direction.

### Which public tables/figures to transcribe

Frozen-now into `experiments/external_contact/p2_uncertainty_public.csv` **before** running
the check:

1. **CIFAR-10-C ensemble variance-vs-error correlation by corruption severity** — from the
   public deep-ensembles / corruption-robustness tables (Lakshminarayanan et al., 2017;
   Hendrycks & Dietterich, 2019; Ovadia et al., 2019 "Can You Trust Your Model's
   Uncertainty?"). Columns suggested: `source, system, slice (in-dist / severity 1..5),
   variance_error_corr, n`.
2. **BALD vs BatchBALD vs random accuracy-per-label-budget** — from the BatchBALD paper's
   published figures (Kirsch et al., 2019) on MNIST/FashionMNIST. Columns: `source, method,
   labels, accuracy`.

Record source citation + figure/table number per row so the transcription is auditable.

### Stdlib check to run

A pure-stdlib script (no third-party deps; same discipline as `p3_glove_probe.py`) over the
CSV computes the pre-registered comparisons:

- P2a: Pearson |r| on the shifted/high-severity slices ≤ 0.2 (and positive in-distribution).
- P2b: BatchBALD accuracy-per-budget > naive-BALD (redundancy gap > 0); naive-BALD <
  value-of-information / oracle.

(If a P2 harness does not yet exist, add `experiments/external_contact/p2_uncertainty_check.py`
reading the CSV with the `csv` module and computing Pearson r / the budget-gap in stdlib.)

### Tier-B confirmatory

```bash
uvx --with torch --with torchvision python - <<'PY'
# load / train 5 small CIFAR-10 CNNs, evaluate on CIFAR-10-C,
# compute per-severity variance-vs-error correlation directly
# (spirit of experiments/ensemble_uncertainty/).
PY
```

### Kill criterion

- **Kills P2a:** external ensemble variance stays well-correlated with error on shifted
  slices (Pearson |r| ≥ 0.5 there).
- **Kills P2b:** published BALD acquisition matches a value-of-information oracle within noise.
- **Weakens both:** the only systems showing the pattern are themselves toy → diagnostic, not field claim.

### Claim tier a pass earns

**Regime transition → field claim (methodology).** A clean Tier-A pass against published
curves is already a field claim about methodology ("the lab's anti-cheat gates catch real
failures in deployed active learning"); Tier B strengthens it to mechanism on external weights.

---

## Outputs summary

| Prediction | Builds / writes | Committed? |
|---|---|---|
| P3 | `tmp/glove/glove.6B.zip` + full `.txt` (gitignored), `experiments/external_contact/p3_glove_subset_{300,100}d.txt` (gitignored), `artifacts/external_contact/p3_glove.json` (gitignored artifact) | subsets/zip NOT committed (raw embeddings stay local) |
| P1 | `artifacts/external_contact/p1_pythia_sweep.json` (B) and/or `experiments/external_contact/p1_pythia_grok_public.csv` (A) | the transcribed public CSV is committed (frozen-now) |
| P2 | `experiments/external_contact/p2_uncertainty_public.csv` | committed (frozen-now public numbers) |
