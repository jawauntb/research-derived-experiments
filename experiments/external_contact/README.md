# External Contact

Tests of the program's claims against systems **the lab did not build**.
Pre-registration: [`docs/external_contact_preregistration.md`](../../docs/external_contact_preregistration.md).

The original environment note in the preregistration said the research
container had blocked network egress. The current laptop/Modal path is used for
Tier-B runs that require public checkpoints.

## P1 — Pythia weakness -> OOD

Files:

- `modal_p1_pythia_weakness.py`: completed frozen-Pythia linear-probe variant.
  See `results/p1_pythia_2026_06_22.md`; all 27 cells had OOD accuracy 0.0, so
  the literal P1 threshold was unevaluable rather than cleanly falsified.
- `modal_p1_pythia_lora.py`: LoRA repair. It fine-tunes public Pythia
  checkpoints with LoRA adapters, extracts the argmax function table on
  `{0..n-1}` by answer-token NLL (`--objective lm`, default) or by an optional
  diagnostic classifier head (`--objective classifier`), and scores the same
  weakness, wrong-group, and classical-predictor gates.
- `p1_lora_metrics.py`: stdlib acceptance scorer shared by the Modal worker,
  tests, and result summaries.
- `results/p1_pythia_lora_2026_06_22.md`: full 27-cell LM-LoRA Tier-B result.
  It is evaluable and negative: weakness rho `-0.0817`, best classical
  `|rho|=0.4550`, P1 hard kill.

Run a smoke cell:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/external_contact/modal_p1_pythia_lora.py \
        --sizes 70m --ns 13 --seeds 1 --epochs 80 --objective lm \
        --out artifacts/external_contact/p1_pythia_lora_smoke.json
```

Run the full pre-registered LoRA grid:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/external_contact/modal_p1_pythia_lora.py \
        --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 \
        --train-frac 0.5 --epochs 160 --objective lm --base-seed 20260618 \
        --out artifacts/external_contact/p1_pythia_lora.json
```

JSON artifacts stay under `artifacts/` and are not committed. Claim-ready
summaries belong under `experiments/external_contact/results/`.
