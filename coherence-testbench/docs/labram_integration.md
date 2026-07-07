# LaBraM Integration Brief

**Status:** LaBraM is usable. MIT-licensed, weights are public (Base only), and a maintained `braindecode` wrapper handles the fiddly bits. Recommended path: **LaBraM-Base via braindecode**, frozen encoder + small head.

Sources: [935963004/LaBraM](https://github.com/935963004/LaBraM) (canonical repo), [braindecode.models.Labram docs](https://braindecode.org/dev/generated/braindecode.models.Labram.html), [braindecode/labram-pretrained on HF](https://huggingface.co/braindecode/labram-pretrained), [ICLR paper 2405.18765](https://arxiv.org/html/2405.18765v1).

---

## 1. Access

- **Weights host:** Base checkpoint is committed in-repo at `checkpoints/labram-base.pth` (~23 MB). Braindecode also mirrors it on HF at `braindecode/labram-pretrained` and `braindecode/Labram-Braindecode`.
- **Sizes:** Base 5.8M, Large 46M, Huge 369M params. **Only Base is publicly released.** Large/Huge weights are not in the repo and have not been published; do not plan around them.
- **Auth:** No HF_TOKEN, no email agreement, no gating. Public download.
- **License:** MIT, verified by fetching `LICENSE` (Copyright 2024 Weibang Jiang). Commercial use permitted with copyright notice retained.
- **Recommendation:** Start with **Base**. It's the only public option and is well-suited to small-data cross-subject BCI.

## 2. Input format

- **Sample rate:** 200 Hz (resample from BBBD's 128 Hz).
- **Channels:** Variable via channel-aware embeddings. BBBD's 64-ch 10-20 BioSemi is fine — pass a `ch_names` list matching LaBraM's electrode vocabulary (uppercase, `FP1`/`FPZ` style; check `standard_1020` alias table in the repo).
- **Window:** 4 s at 200 Hz → **800 samples**, chunked into 200-sample patches (patch size = 200).
- **Preprocessing (BBBD → LaBraM):**
  1. Bandpass 0.1–75 Hz.
  2. Notch 50 Hz. *(BBBD is EU; if any US recordings creep in use 60 Hz. Safe default: 50 Hz.)*
  3. Resample 128 → 200 Hz.
  4. Amplitude scaling: paper sets "unit to 0.1 mV" so signal ≈ [−1, 1]. In practice: `x_uV / 100.0`.
  5. Slice to 4 s epochs (800 samples).
- **Average reference:** Not required by LaBraM; use whatever BBBD's existing pipeline uses.

## 3. Encoder invocation

Cleanest API is via braindecode (avoids reimplementing the repo's training scaffolding):

```python
from braindecode.models import Labram
import torch

model = Labram.from_pretrained("braindecode/labram-pretrained")
model.eval()

# x: (batch, n_chans, n_times) — e.g. (B, 64, 800) after preprocessing
with torch.no_grad():
    out = model(x, return_features=True)
cls = out["cls_token"]     # (B, 200) — use this as the epoch embedding
patches = out["features"]  # (B, n_patches, 200) — for temporal-pool heads
```

- **Embedding dim:** 200 (Base).
- **Hardware:** Base is CPU-viable but slow. Recommend `modal.gpu.T4` (cheapest GPU on Modal, ~10x faster). A10G is overkill for Base.

## 4. Fine-tune vs frozen

- **Original paper:** Reports only full fine-tune. Peak LR 5e-4, layer decay 0.65, warmup 5, cosine to 1e-6, weight decay 0.05, drop-path 0.1, batch 64, 50 epochs.
- **External benchmarks (AdaBrain-Bench, OmniEEG-Bench, NeuroAtlas):** LaBraM ranks strongly on frozen cross-subject linear probing across most tasks, though it underperforms on emotion (SEED-V, FACED). BBBD tasks look more like abnormality / event classification, where LaBraM is competitive.
- **Frozen probe LR:** No paper number; safe default **1e-3, AdamW, cosine, 30–50 epochs, batch 64**. If the head plateaus at chance, drop to 3e-4 before unfreezing.

## 5. Time budget

- 200 recordings × 32 epochs × 4s = 6,400 forward passes on Base (5.8M params).
- CPU: **~5–10 minutes** end-to-end.
- T4 GPU: **under a minute** for inference. Head training adds a few minutes.
- Order of magnitude: **single-digit minutes on GPU** for the full experiment.

## 6. Next-step blueprint

1. **Deps in Modal image:** `pip install braindecode>=0.9 huggingface_hub torch mne scipy` (mne+scipy for filtering/resample; braindecode pulls in einops).
2. **Weights:** No manual download. `Labram.from_pretrained("braindecode/labram-pretrained")` handles caching. Cache dir: mount a Modal `Volume` at `~/.cache/huggingface` to persist across cold starts.
3. **GPU:** Swap shard function decorator to `@app.function(gpu="T4", ...)`. Base fits comfortably in 16 GB.
4. **Preprocess** each BBBD recording per §2, chunk into non-overlapping 4-s epochs, stack `(N_epochs, 64, 800)`, cast float32.
5. **Extract embeddings** per §3. Save `(N_epochs, 200)` per recording to artifact store.
6. **Head:** 2-layer MLP `Linear(200, 64) → GELU → Dropout(0.2) → Linear(64, 2 or 1)`. Aggregate epoch-level to recording-level by mean-pool of embeddings before the head, OR mean-pool of logits after — both are legitimate; try mean-of-embeddings first. Cross-subject LSO split identical to the current EEG bench for direct comparability with the 50.0% baseline.

**Ambiguity flag:** BBBD's exact channel-name convention needs a one-time check against LaBraM's electrode vocab before the first run — mismatches silently degrade the channel-aware embedding. Safe default: rename channels to LaBraM's `standard_1020` set with a lookup dict; log any electrodes that fall through as `unknown`.
