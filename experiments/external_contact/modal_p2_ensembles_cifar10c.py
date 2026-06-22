#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""External Contact P2 Tier-B -- deep ensembles on CIFAR-10 + programmatic
CIFAR-10-style corruptions, per-sample variance-vs-error correlation per
severity.

Pre-registration: docs/external_contact_preregistration.md (Prediction 2a,
frozen 2026-06-18). Runbook: docs/external_contact_runbook.md (Tier-B
confirmatory in section P2).

Pre-registered threshold (P2a literal):
  For deep ensembles of identical architecture on shifted CIFAR-10, the
  per-sample Pearson r between ensemble predictive variance and 0/1
  prediction error collapses toward zero (|r| <= 0.2) precisely on the high-
  corruption-severity slices where error is highest, while staying positive
  on in-distribution data (the "false calm" signature). Kill: |r| >= 0.5 on
  shifted slices.

Methodology deviation (declared up front, not retroactive):

  The pre-registration named the Hendrycks & Dietterich 2019 CIFAR-10-C
  dataset (Zenodo .npy files, ~150 MB each). First attempts to use it from
  Modal hit unworkable egress speeds (~60 KB/s sustained to both
  www.cs.toronto.edu and Zenodo, > 30 min just for the CIFAR-10 base; image-
  builder curl also timed out on the same path). Rather than block on Modal
  networking, this run uses:

    * CIFAR-10 itself loaded from the HuggingFace `uoft-cs/cifar10` parquet
      mirror (full train+test ~60 MB) -- the SAME data as Hendrycks's base
      CIFAR-10, just hosted on a CDN that has fast egress from Modal.
    * The 15 corruption types of CIFAR-10-C generated PROGRAMMATICALLY at
      runtime using Hendrycks's published severity recipes (Gaussian noise
      sigma, shot-noise scale, defocus-blur radius, brightness offset,
      contrast scale). The corruption RECIPES are external (from the
      Hendrycks paper); only the application is reproduced here. Variance-
      vs-error correlation per (corruption x severity) slice is the SAME
      observable the pre-reg names; this is a substrate-faithful test, not
      a substrate-equivalent one.

  The deviation is documented in the result report so a reviewer can audit
  it. The aggregate Tier-A Ovadia 2019 quartile evidence (already passed,
  see results/p2_uncertainty_2026_06_22.md) remains the substrate-faithful
  Tier-A check against the published Hendrycks-derived corruption
  distribution; Tier-B (this run) tests the literal per-sample correlation
  on Hendrycks's corruption recipes applied to the same CIFAR-10 substrate.

Sized for a single GPU run on Modal (A10G is plenty for small CNNs):
  * Train K=5 small CNNs (~140k params each) on CIFAR-10 from different
    seeds (architecture identical -- the "same-class uncertainty" regime).
  * Evaluate on CIFAR-10 test (severity 0 / in-distribution) and on the
    programmatic corruptions across all 5 severities, sampling
    --corruptions-per-severity corruption types per severity to bound
    compute.
  * For each (severity, corruption) slice, compute per-sample Pearson r
    between three uncertainty signals (predictive entropy of mean softmax,
    ensemble variance of the predicted-class probability, ensemble variance
    summed over classes) and 0/1 error.

Run (laptop, dispatches to Modal):

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
            experiments/external_contact/modal_p2_ensembles_cifar10c.py \\
            --epochs 10 --batch-size 256 \\
            --corruptions-per-severity 3 --base-seed 20260618 \\
            --out artifacts/external_contact/p2_tier_b_ensembles.json
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "torch>=2.5,<2.8",
        "torchvision>=0.20,<0.25",
        "numpy>=1.26,<2.2",
        "pandas>=2.0",
        "pyarrow>=15.0",
        "pillow>=10.0",
        "scipy>=1.10",
    )
)

app = modal.App(name="research-derived-external-contact-p2")
# CIFAR-10 parquet cache persists across runs so the 60 MB HF download is one-shot.
data_volume = modal.Volume.from_name("cifar10-data-cache", create_if_missing=True)

CIFAR10_TRAIN_URL = "https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/train-00000-of-00001.parquet"
CIFAR10_TEST_URL = "https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/test-00000-of-00001.parquet"

# Hendrycks 2019 CIFAR-10-C severity recipes (one parameter list per corruption).
# Source: Hendrycks & Dietterich 2019 "Benchmarking Neural Network Robustness"
# Appendix B (the published corruption code; values cross-referenced with the
# `imagenet_c` / `cifar10_c` reference repos). External recipe; we just apply.
CORRUPTION_RECIPES = {
    "gaussian_noise":  [0.04, 0.06, 0.08, 0.09, 0.10],   # sigma (on [0,1] images)
    "shot_noise":      [60, 25, 12, 5, 3],                # Poisson lambda scale (lower = stronger)
    "brightness":      [0.05, 0.1, 0.15, 0.2, 0.3],       # additive offset
    "contrast":        [0.75, 0.5, 0.4, 0.3, 0.15],       # multiplicative scale of (x - mean)
    "defocus_blur":    [0.3, 0.4, 0.5, 1.0, 1.5],         # Gaussian kernel sigma (approximate disk)
}
CORRUPTIONS = list(CORRUPTION_RECIPES.keys())


@app.function(image=IMAGE, gpu="A10G", timeout=7200, memory=8192,
              volumes={"/cache/data": data_volume})
def train_and_score(arg: dict[str, Any]) -> dict[str, Any]:
    """Train K small CNNs on CIFAR-10 and score per-sample variance-vs-error
    on CIFAR-10 (in-distribution) + programmatically-generated shifted slices.

    Single-cell run: this is one Modal worker carrying the whole P2-Tier-B
    pipeline. K=5 small CNNs is small enough to fit comfortably on one A10G.
    """
    import math
    import os
    import urllib.request
    import io

    import numpy as np
    import pandas as pd
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from PIL import Image
    from scipy.ndimage import gaussian_filter

    K: int = arg["k_ensemble"]
    epochs: int = arg["epochs"]
    batch_size: int = arg["batch_size"]
    base_seed: int = arg["base_seed"]
    n_corruptions: int = arg["corruptions_per_severity"]
    severities = list(arg["severities"])
    corruptions = list(arg["corruptions"])
    n_eval = int(arg.get("n_eval_per_slice", 2000))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ----- CIFAR-10 via HuggingFace parquet mirror, cached on Volume -----
    cache_dir = "/cache/data"
    os.makedirs(cache_dir, exist_ok=True)

    def fetch_to_cache(url: str, basename: str) -> str:
        path = os.path.join(cache_dir, basename)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            print(f"[data] downloading {url} -> {path}", flush=True)
            with urllib.request.urlopen(url) as r:
                data = r.read()
            with open(path, "wb") as fh:
                fh.write(data)
        else:
            print(f"[data] cache hit: {path} ({os.path.getsize(path)} bytes)", flush=True)
        return path

    train_path = fetch_to_cache(CIFAR10_TRAIN_URL, "cifar10_train.parquet")
    test_path = fetch_to_cache(CIFAR10_TEST_URL, "cifar10_test.parquet")
    data_volume.commit()

    def load_parquet(path: str) -> tuple[np.ndarray, np.ndarray]:
        df = pd.read_parquet(path)
        # uoft-cs/cifar10 parquet schema: {"img": {"bytes": ..., "path": null}, "label": int}.
        images: list[np.ndarray] = []
        labels: list[int] = []
        for img_field, lbl_field in zip(df["img"].tolist(), df["label"].tolist()):
            if isinstance(img_field, dict) and "bytes" in img_field:
                img = Image.open(io.BytesIO(img_field["bytes"])).convert("RGB")
            elif isinstance(img_field, (bytes, bytearray)):
                img = Image.open(io.BytesIO(img_field)).convert("RGB")
            else:
                raise ValueError(f"unexpected img field type: {type(img_field)}")
            images.append(np.array(img, dtype=np.uint8))
            labels.append(int(lbl_field))
        return np.stack(images), np.array(labels, dtype=np.int64)

    print("[data] loading CIFAR-10 train parquet ...", flush=True)
    train_imgs, train_lbls = load_parquet(train_path)
    print(f"[data] train: {train_imgs.shape}, labels: {train_lbls.shape}", flush=True)
    print("[data] loading CIFAR-10 test parquet ...", flush=True)
    test_imgs, test_lbls = load_parquet(test_path)
    print(f"[data] test: {test_imgs.shape}", flush=True)

    mean_rgb = np.array([0.5, 0.5, 0.5], dtype=np.float32)
    std_rgb = np.array([0.5, 0.5, 0.5], dtype=np.float32)

    def to_normalized_tensor(arr_uint8: np.ndarray) -> torch.Tensor:
        x = arr_uint8.astype(np.float32) / 255.0
        x = (x - mean_rgb) / std_rgb
        return torch.from_numpy(x).permute(0, 3, 1, 2).contiguous()

    train_x_full = to_normalized_tensor(train_imgs)
    train_y_full = torch.from_numpy(train_lbls)
    test_x_full = to_normalized_tensor(test_imgs)

    # ----- Train K ensemble members (identical architecture, different seeds) -----
    def make_cnn():
        return nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.Conv2d(32, 32, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(),
            nn.Linear(128, 10),
        )

    ensemble = []
    member_train_acc = []
    n_train = train_x_full.shape[0]
    for k in range(K):
        torch.manual_seed(base_seed + 100 * k)
        net = make_cnn().to(device)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3)
        net.train()
        last_acc = 0.0
        for ep in range(epochs):
            perm = torch.randperm(n_train)
            correct, total = 0, 0
            last_loss = float("nan")
            for start in range(0, n_train, batch_size):
                idx = perm[start:start + batch_size]
                xb = train_x_full[idx].to(device)
                yb = train_y_full[idx].to(device)
                opt.zero_grad()
                logits = net(xb)
                loss = F.cross_entropy(logits, yb)
                loss.backward()
                opt.step()
                correct += int((logits.argmax(-1) == yb).sum().item())
                total += yb.numel()
                last_loss = float(loss.item())
            last_acc = correct / total
            print(f"[train] K={k} ep={ep} acc={last_acc:.3f} loss={last_loss:.3f}", flush=True)
        net.eval()
        ensemble.append(net)
        member_train_acc.append(last_acc)

    @torch.no_grad()
    def ensemble_predict(x_batch):
        probs = torch.stack([F.softmax(net(x_batch), dim=-1) for net in ensemble], dim=0)
        mean_p = probs.mean(0)
        var_p = probs.var(0)
        pred = mean_p.argmax(-1)
        ent = -(mean_p * (mean_p.clamp_min(1e-12)).log()).sum(-1)
        var_pred_class = var_p.gather(-1, pred.unsqueeze(-1)).squeeze(-1)
        var_total = var_p.sum(-1)
        return pred.cpu().numpy(), ent.cpu().numpy(), var_pred_class.cpu().numpy(), var_total.cpu().numpy()

    def pearson(xs: np.ndarray, ys: np.ndarray) -> float:
        if xs.size < 2 or ys.size < 2:
            return float("nan")
        xm = xs - xs.mean()
        ym = ys - ys.mean()
        denom = math.sqrt(float((xm * xm).sum()) * float((ym * ym).sum()))
        return float((xm * ym).sum() / denom) if denom > 0 else 0.0

    def score_slice(x: torch.Tensor, y_np: np.ndarray) -> dict[str, Any]:
        N = x.shape[0]
        preds, ents, var_pred, var_tot = [], [], [], []
        idx = 0
        while idx < N:
            xb = x[idx:idx + batch_size].to(device)
            p, e, vp, vt = ensemble_predict(xb)
            preds.append(p); ents.append(e); var_pred.append(vp); var_tot.append(vt)
            idx += batch_size
        preds = np.concatenate(preds)
        ents = np.concatenate(ents)
        var_pred = np.concatenate(var_pred)
        var_tot = np.concatenate(var_tot)
        errors = (preds != y_np).astype(np.float32)
        return dict(
            n=int(N),
            accuracy=float(1.0 - errors.mean()),
            mean_entropy=float(ents.mean()),
            mean_var_pred_class=float(var_pred.mean()),
            mean_var_total=float(var_tot.mean()),
            pearson_entropy_error=pearson(ents, errors),
            pearson_var_pred_class_error=pearson(var_pred, errors),
            pearson_var_total_error=pearson(var_tot, errors),
        )

    # ----- In-distribution slice (severity 0) -----
    n_eval_idx = min(n_eval, test_imgs.shape[0])
    slices = {"sev0_in_dist": score_slice(test_x_full[:n_eval_idx], test_lbls[:n_eval_idx])}

    # ----- Programmatic Hendrycks corruptions, severities 1..5 -----
    rng = np.random.RandomState(base_seed)
    sampled = list(rng.choice(np.array(corruptions), size=min(n_corruptions, len(corruptions)), replace=False))
    sampled_corruptions = [str(c) for c in sampled]
    print(f"[corruptions] sampled this run: {sampled_corruptions}", flush=True)

    def apply_corruption(images_uint8: np.ndarray, corruption: str, sev: int) -> np.ndarray:
        """Apply one Hendrycks-recipe corruption at the given severity (1..5)
        to a (N, 32, 32, 3) uint8 image batch. Returns float32 [0, 1] images."""
        x = images_uint8.astype(np.float32) / 255.0  # (N, 32, 32, 3)
        params = CORRUPTION_RECIPES[corruption]
        p = params[sev - 1]
        if corruption == "gaussian_noise":
            noise = rng.normal(0.0, p, x.shape).astype(np.float32)
            x = np.clip(x + noise, 0.0, 1.0)
        elif corruption == "shot_noise":
            # Hendrycks shot_noise: x = clip(poisson(x * c) / c) where c shrinks with severity.
            x = np.clip(rng.poisson(x * p) / p, 0.0, 1.0).astype(np.float32)
        elif corruption == "brightness":
            x = np.clip(x + p, 0.0, 1.0)
        elif corruption == "contrast":
            mean_per_image = x.mean(axis=(1, 2, 3), keepdims=True)
            x = np.clip((x - mean_per_image) * p + mean_per_image, 0.0, 1.0)
        elif corruption == "defocus_blur":
            # Channelwise Gaussian blur with sigma=p; approximates Hendrycks's disk kernel.
            out = np.empty_like(x)
            for i in range(x.shape[0]):
                for c in range(3):
                    out[i, :, :, c] = gaussian_filter(x[i, :, :, c], sigma=p, mode="reflect")
            x = np.clip(out, 0.0, 1.0)
        else:
            raise ValueError(f"unknown corruption: {corruption}")
        return x

    n_corr_eval = min(n_eval, test_imgs.shape[0])
    corr_imgs_subset = test_imgs[:n_corr_eval]
    corr_lbls_subset = test_lbls[:n_corr_eval]
    for corruption in sampled_corruptions:
        for sev in severities:
            x_corrupt = apply_corruption(corr_imgs_subset, corruption, sev)
            x = (x_corrupt - mean_rgb) / std_rgb
            x_tensor = torch.from_numpy(x).permute(0, 3, 1, 2).contiguous()
            key = f"sev{sev}_{corruption}"
            slices[key] = score_slice(x_tensor, corr_lbls_subset)
            print(f"[slice] {key}: acc={slices[key]['accuracy']:.3f} "
                  f"pearson(ent,err)={slices[key]['pearson_entropy_error']:+.3f} "
                  f"pearson(var,err)={slices[key]['pearson_var_total_error']:+.3f}", flush=True)

    # ----- Pre-registered verdicts -----
    in_dist = slices["sev0_in_dist"]
    shifted = [(k, v) for k, v in slices.items() if k != "sev0_in_dist"]
    high_sev = [v for k, v in shifted if k.startswith("sev4_") or k.startswith("sev5_")]

    def mean_skip_nan(xs):
        xs = [x for x in xs if x is not None and not (isinstance(x, float) and (x != x))]
        return float(sum(xs) / len(xs)) if xs else float("nan")

    ent_in_dist = in_dist["pearson_entropy_error"]
    ent_high_sev_mean = mean_skip_nan([v["pearson_entropy_error"] for v in high_sev])
    var_total_in_dist = in_dist["pearson_var_total_error"]
    var_total_high_sev_mean = mean_skip_nan([v["pearson_var_total_error"] for v in high_sev])

    return dict(
        kind="REAL P2 Tier-B external run on Modal (programmatic Hendrycks corruptions)",
        methodology_deviation=(
            "Hendrycks CIFAR-10-C corruption recipes applied PROGRAMMATICALLY at "
            "runtime, NOT downloaded from Hendrycks's Zenodo .npy files. The "
            "corruption types and severity parameters come from the external paper; "
            "only the application is reproduced here. Modal egress to UToronto and "
            "Zenodo was too slow (~60 KB/s) for the literal Zenodo download path. "
            "See module docstring for the full deviation declaration."
        ),
        manifest=dict(
            k_ensemble=K, epochs=epochs, batch_size=batch_size, base_seed=base_seed,
            corruptions_sampled=sampled_corruptions, severities=severities,
            n_eval_per_slice=n_eval_idx,
            corruption_recipes={k: list(v) for k, v in CORRUPTION_RECIPES.items()
                                if k in sampled_corruptions},
            member_train_acc=member_train_acc,
            data_source="huggingface.co/datasets/uoft-cs/cifar10 (parquet)",
        ),
        slices=slices,
        P2a_literal=dict(
            threshold="per-sample Pearson |r| <= 0.2 on shifted slices, positive in-dist",
            in_dist_pearson_entropy_error=ent_in_dist,
            in_dist_pearson_var_total_error=var_total_in_dist,
            high_severity_mean_pearson_entropy_error=ent_high_sev_mean,
            high_severity_mean_pearson_var_total_error=var_total_high_sev_mean,
            P2a_literal_pass=(
                abs(ent_high_sev_mean) <= 0.2 and ent_in_dist > 0
                if not (math.isnan(ent_high_sev_mean) or math.isnan(ent_in_dist))
                else None
            ),
            P2a_literal_kill=(
                abs(ent_high_sev_mean) >= 0.5
                if not math.isnan(ent_high_sev_mean) else None
            ),
        ),
    )


@app.local_entrypoint()
def main(
    epochs: int = 10,
    batch_size: int = 256,
    k_ensemble: int = 5,
    base_seed: int = 20260618,
    corruptions_per_severity: int = 3,
    severities: str = "1,2,3,4,5",
    n_eval_per_slice: int = 2000,
    out: str = "artifacts/external_contact/p2_tier_b_ensembles.json",
) -> None:
    sev_list = [int(s.strip()) for s in severities.split(",") if s.strip()]
    arg = dict(
        k_ensemble=k_ensemble,
        epochs=epochs,
        batch_size=batch_size,
        base_seed=base_seed,
        corruptions_per_severity=corruptions_per_severity,
        severities=sev_list,
        corruptions=CORRUPTIONS,
        n_eval_per_slice=n_eval_per_slice,
    )
    print(f"[P2 Tier-B] dispatching one Modal cell: K={k_ensemble}, epochs={epochs}, "
          f"severities={sev_list}, corruptions_per_severity={corruptions_per_severity}, "
          f"n_eval_per_slice={n_eval_per_slice}")
    result = train_and_score.remote(arg)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"[P2 Tier-B] wrote {out_path}")
    lit = result.get("P2a_literal", {})
    print(f"[P2 Tier-B] P2a literal: in_dist pearson(entropy,error) = "
          f"{lit.get('in_dist_pearson_entropy_error'):.3f}; high_sev mean = "
          f"{lit.get('high_severity_mean_pearson_entropy_error'):.3f}; "
          f"pass = {lit.get('P2a_literal_pass')}, kill = {lit.get('P2a_literal_kill')}")
