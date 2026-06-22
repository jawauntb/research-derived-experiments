#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""External Contact P2 Tier-B -- deep ensembles on CIFAR-10-C, per-sample
variance-vs-error correlation per severity.

Pre-registration: docs/external_contact_preregistration.md (Prediction 2a,
frozen 2026-06-18). Runbook: docs/external_contact_runbook.md (Tier-B
confirmatory in section P2).

Pre-registered threshold (P2a literal):
  For deep ensembles of identical architecture on CIFAR-10-C, the per-sample
  Pearson r between ensemble predictive variance and 0/1 prediction error
  collapses toward zero (|r| <= 0.2) precisely on the high-corruption-severity
  slices where error is highest, while staying positive on in-distribution data
  (the "false calm" signature). Kill: |r| >= 0.5 on shifted slices.

Sized for a single GPU run on Modal (A10G is plenty for small CNNs):
  * Train K=5 small CNNs (~140k params each) on CIFAR-10 from different seeds
    (architecture identical -- this is the "same-class uncertainty" regime the
    lab's metric-stack §4.3 named).
  * Evaluate on CIFAR-10 test (severity 0 / in-distribution) and on
    CIFAR-10-C across all 5 severities, sampling --corruptions-per-severity
    corruption types per severity to bound compute (the full set is 15 / 19
    corruptions depending on source).
  * For each (severity, corruption) slice, compute per-sample Pearson r
    between ensemble predictive variance (entropy of mean softmax, var of
    correct-class probability) and 0/1 error.

Run (laptop, will dispatch to Modal):

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
            experiments/external_contact/modal_p2_ensembles_cifar10c.py \\
            --epochs 12 --batch-size 256 \\
            --corruptions-per-severity 3 --base-seed 20260618 \\
            --out artifacts/external_contact/p2_tier_b_ensembles.json

Smoke test first with --epochs 1 --corruptions-per-severity 1 to validate the
pipeline at ~5 min cost before the full sweep.

External system: CIFAR-10 + CIFAR-10-C (Hendrycks & Dietterich 2019,
arXiv:1903.12261). The dataset and benchmark were built by other groups; this
harness uses them as a non-lab substrate for the P2a literal threshold.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


# CIFAR-10 baked into the image at build time so the per-run download (slow from
# Modal's egress to www.cs.toronto.edu, observed ~60 KB/s) happens ONCE during
# image construction and is reused on every subsequent run. CIFAR-10-C
# corruption files (~150 MB each) are too large to bake; they go on a Modal
# Volume populated on first run and cached for every run thereafter.
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("curl", "ca-certificates")
    .pip_install(
        "torch>=2.5,<2.8",
        "torchvision>=0.20,<0.25",
        "numpy>=1.26,<2.2",
        "requests>=2.31",
    )
    .run_commands(
        "mkdir -p /data && cd /data && "
        "curl -fsSL https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz "
        "-o cifar-10-python.tar.gz && "
        "tar -xzf cifar-10-python.tar.gz && rm cifar-10-python.tar.gz"
    )
)

app = modal.App(name="research-derived-external-contact-p2")
# Persistent cache for the CIFAR-10-C corruption .npy files (~50 MB each, 15
# corruptions x 5 severities encoded one .npy per corruption).
cifar10c_volume = modal.Volume.from_name("cifar10c-cache", create_if_missing=True)

# CIFAR-10-C download host (Zenodo). 15 corruption types as .npy files (50000x32x32x3
# for each, labels in labels.npy). Five severities are encoded in row order:
#   severity 1: rows [0:10000), 2: [10000:20000), ..., 5: [40000:50000).
CIFAR10C_BASE = "https://zenodo.org/records/2535967/files"
CORRUPTIONS = [
    "gaussian_noise", "shot_noise", "impulse_noise", "defocus_blur", "glass_blur",
    "motion_blur", "zoom_blur", "snow", "frost", "fog",
    "brightness", "contrast", "elastic_transform", "pixelate", "jpeg_compression",
]


@app.function(image=IMAGE, gpu="A10G", timeout=7200, memory=8192,
              volumes={"/cache/cifar10c": cifar10c_volume})
def train_and_score(arg: dict[str, Any]) -> dict[str, Any]:
    """Train K small CNNs on CIFAR-10 and score per-sample variance-vs-error
    on CIFAR-10 (in-distribution) + sampled CIFAR-10-C slices.

    Single-cell run: this is one Modal worker carrying the whole P2-Tier-B
    pipeline. K=5 small CNNs is small enough to fit comfortably on one A10G;
    sharding across workers would just inflate cost.
    """
    import math
    import os
    import urllib.request

    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torchvision
    import torchvision.transforms as T

    K: int = arg["k_ensemble"]
    epochs: int = arg["epochs"]
    batch_size: int = arg["batch_size"]
    base_seed: int = arg["base_seed"]
    n_corruptions: int = arg["corruptions_per_severity"]
    severities = list(arg["severities"])
    corruptions = list(arg["corruptions"])
    n_eval = int(arg.get("n_eval_per_slice", 2000))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # ----- CIFAR-10 train / clean test (baked into the image at /data) -----
    transform = T.Compose([T.ToTensor(), T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    train_set = torchvision.datasets.CIFAR10("/data", train=True, download=False, transform=transform)
    test_set = torchvision.datasets.CIFAR10("/data", train=False, download=False, transform=transform)
    train_loader = torch.utils.data.DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=2)

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

    # ----- Train K ensemble members (identical architecture, different seeds) -----
    ensemble = []
    member_train_acc = []
    for k in range(K):
        torch.manual_seed(base_seed + 100 * k)
        net = make_cnn().to(device)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3)
        net.train()
        last_acc = 0.0
        for _ in range(epochs):
            correct, total = 0, 0
            for x, y in train_loader:
                x, y = x.to(device), y.to(device)
                opt.zero_grad()
                logits = net(x)
                loss = F.cross_entropy(logits, y)
                loss.backward()
                opt.step()
                correct += int((logits.argmax(-1) == y).sum().item())
                total += y.numel()
            last_acc = correct / total
        net.eval()
        ensemble.append(net)
        member_train_acc.append(last_acc)

    @torch.no_grad()
    def ensemble_predict(x_batch):
        probs = torch.stack([F.softmax(net(x_batch), dim=-1) for net in ensemble], dim=0)  # (K, B, 10)
        mean_p = probs.mean(0)  # (B, 10)
        var_p = probs.var(0)    # (B, 10)
        pred = mean_p.argmax(-1)
        # uncertainty measures: predictive entropy of mean softmax; variance of correct-class prob (using pred).
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

    def score_slice(images: torch.Tensor, labels: torch.Tensor) -> dict[str, Any]:
        # images: (N, 3, 32, 32) normalized; labels: (N,)
        N = images.shape[0]
        preds, ents, var_pred, var_tot = [], [], [], []
        idx = 0
        while idx < N:
            xb = images[idx:idx + batch_size].to(device)
            p, e, vp, vt = ensemble_predict(xb)
            preds.append(p); ents.append(e); var_pred.append(vp); var_tot.append(vt)
            idx += batch_size
        preds = np.concatenate(preds)
        ents = np.concatenate(ents)
        var_pred = np.concatenate(var_pred)
        var_tot = np.concatenate(var_tot)
        errors = (preds != labels.numpy()).astype(np.float32)
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
    test_x = torch.stack([test_set[i][0] for i in range(min(n_eval, len(test_set)))])
    test_y = torch.tensor([test_set[i][1] for i in range(min(n_eval, len(test_set)))])
    slices = {"sev0_in_dist": score_slice(test_x, test_y)}

    # ----- CIFAR-10-C slices (per severity, per sampled corruption) -----
    # Cached on the persistent Modal Volume at /cache/cifar10c so the slow
    # Zenodo download (~150 MB per corruption) only happens once across runs.
    cache_dir = "/cache/cifar10c"
    os.makedirs(cache_dir, exist_ok=True)
    labels_url = f"{CIFAR10C_BASE}/labels.npy"
    rng = np.random.RandomState(base_seed)
    sampled_corruptions = list(rng.choice(np.array(corruptions), size=min(n_corruptions, len(corruptions)), replace=False))
    sampled_corruptions = [str(c) for c in sampled_corruptions]

    def cache_fetch(url: str, basename: str) -> np.ndarray:
        path = os.path.join(cache_dir, basename)
        if not os.path.exists(path):
            print(f"[cifar10c] downloading {url} -> {path}", flush=True)
            with urllib.request.urlopen(url) as r:
                data = r.read()
            with open(path, "wb") as fh:
                fh.write(data)
        else:
            print(f"[cifar10c] cache hit: {path}", flush=True)
        return np.load(path)

    # labels (50000,) -- same labels for every severity row block
    labels_full = cache_fetch(labels_url, "labels.npy")

    norm = T.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    for corruption in sampled_corruptions:
        url = f"{CIFAR10C_BASE}/{corruption}.npy"
        arr = cache_fetch(url, f"{corruption}.npy")  # (50000, 32, 32, 3) uint8
        for sev in severities:
            start = (sev - 1) * 10000
            end = start + 10000
            sub_imgs = arr[start:end]
            sub_lbls = labels_full[start:end]
            # take first n_eval samples per slice (deterministic) -- variance-vs-error
            # correlation is per-sample so larger n is better, but we cap to control cost.
            sub_imgs = sub_imgs[:n_eval]
            sub_lbls = sub_lbls[:n_eval]
            x = torch.from_numpy(sub_imgs.astype(np.float32) / 255.0).permute(0, 3, 1, 2)
            x = norm(x)
            y = torch.from_numpy(sub_lbls.astype(np.int64))
            key = f"sev{sev}_{corruption}"
            slices[key] = score_slice(x, y)

    # ----- Pre-registered verdicts -----
    in_dist = slices["sev0_in_dist"]
    shifted = [(k, v) for k, v in slices.items() if k != "sev0_in_dist"]
    high_sev = [v for k, v in shifted if k.startswith("sev4_") or k.startswith("sev5_")]

    def mean(xs):
        xs = [x for x in xs if x is not None and not (isinstance(x, float) and (x != x))]
        return float(sum(xs) / len(xs)) if xs else float("nan")

    ent_in_dist = in_dist["pearson_entropy_error"]
    ent_high_sev_mean = mean([v["pearson_entropy_error"] for v in high_sev])
    var_total_in_dist = in_dist["pearson_var_total_error"]
    var_total_high_sev_mean = mean([v["pearson_var_total_error"] for v in high_sev])

    # Persist any newly-cached corruption files so subsequent runs hit the cache.
    cifar10c_volume.commit()

    return dict(
        kind="REAL P2 Tier-B external run on Modal",
        manifest=dict(
            k_ensemble=K, epochs=epochs, batch_size=batch_size, base_seed=base_seed,
            corruptions_sampled=sampled_corruptions, severities=severities,
            n_eval_per_slice=n_eval,
            member_train_acc=member_train_acc,
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
    epochs: int = 12,
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
