#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""External Contact P1 -- weakness -> OOD on the Pythia model family.

Pre-registration: docs/external_contact_preregistration.md (Prediction 1,
frozen 2026-06-18). Runbook: docs/external_contact_runbook.md (Tier-B P1).

External system: the Pythia model suite (EleutherAI; Biderman et al. 2023),
sizes pythia-70m, pythia-160m, pythia-410m. The 1.4b checkpoint is skipped on
the first pass to bound cost; add `--include-1-4b` to extend.

External task: partial-orbit modular addition mod n in {13, 17, 23} with a
strict subset of the Z_n translation orbit shown in training, OOD = the held-out
complement of the orbit. This is decidable from the model's argmax function
table over the full input domain.

Pre-registered P1 (literal):

    Spearman rho between **learned-function weakness under the true group Z_n**
    (weakness_oracle_norm, equivariance count of the linear-probe argmax
    function table) and held-out OOD accuracy >= +0.5 across the sweep, and
    strictly exceeds the |rho| of every classical predictor (final train loss,
    eval NLL on OOD inputs, parameter count, parameter L2 norm, Hutchinson
    sharpness proxy) by margin >= 0.25 in |rho|. Wrong-group control (random
    permutation of equal size) |rho| <= 0.15.

Recipe (per (size, n, seed) cell):
  * Load the public Pythia checkpoint via transformers, freeze it.
  * Encode each integer a in {0..n-1} as a string, take the last-layer hidden
    state of the last token as a fixed feature.
  * Train a small linear head (one Linear) on a **strict-subset** training
    orbit of size m = ceil(n * train_frac), targets (a + offset) mod n.
  * Apply the linear head over the full domain -> argmax function table
    (length n). Held-out OOD = the complement of the training subset.
  * Compute weakness under Z_n (true group, cyclic translations) and under a
    random wrong-group of equal size. Reuses the lab's equivariance-count
    logic from experiments/symbolic_weakness/selectors.py, re-implemented
    here (the Modal worker is intentionally self-contained).
  * Compute classical predictors: final head training loss, eval NLL on the
    OOD inputs, parameter count of the underlying Pythia model, parameter L2
    of the Pythia weights, Hutchinson sharpness proxy on the head loss.

The sweep is sharded by Pythia size (one Modal worker per size; the worker
loads the model once and runs all (n, seed) combos internally to amortize
the model-load cost).

Run (laptop, dispatches to Modal):

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
            experiments/external_contact/modal_p1_pythia_weakness.py \\
            --train-frac 0.5 --seeds 3 \\
            --base-seed 20260618 \\
            --out artifacts/external_contact/p1_pythia_weakness.json

Smoke test first with --seeds 1 and --ns 13 to validate the pipeline at one
small Pythia + one n before the full sweep.
"""

from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.45,<4.55",
    "numpy>=1.26,<2.2",
    "accelerate>=0.30,<1.5",
)

app = modal.App(name="research-derived-external-contact-p1")

PYTHIA_SIZES = ["70m", "160m", "410m"]  # add "1.4b" via --include-1-4b


@app.function(image=IMAGE, gpu="A10G", timeout=3600, memory=16384)
def run_size_shard(arg: dict[str, Any]) -> dict[str, Any]:
    """Run all (n, seed) cells for a single Pythia size on one Modal worker."""
    import random
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import AutoModelForCausalLM, AutoTokenizer

    size: str = arg["size"]
    ns: list[int] = list(arg["ns"])
    seeds: list[int] = list(arg["seeds"])
    train_frac: float = arg["train_frac"]
    head_epochs: int = arg["head_epochs"]
    head_lr: float = arg["head_lr"]

    repo = f"EleutherAI/pythia-{size}"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(repo)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(repo, output_hidden_states=False, torch_dtype=torch.float32)
    model.eval()
    model.to(device)
    for p in model.parameters():
        p.requires_grad_(False)

    # Cache last-hidden-state features per integer once -- features only depend on
    # the integer string, not on n or seed.
    @torch.no_grad()
    def features_for(a: int) -> torch.Tensor:
        toks = tokenizer(str(a), return_tensors="pt").to(device)
        out = model(**toks, output_hidden_states=True)
        h = out.hidden_states[-1][0, -1].detach()  # (hidden_dim,)
        return h.float().cpu()

    max_n = max(ns)
    feature_dim = None
    features: dict[int, torch.Tensor] = {}
    for a in range(max_n):
        f = features_for(a)
        if feature_dim is None:
            feature_dim = int(f.shape[0])
        features[a] = f

    # Hutchinson sharpness proxy on the head loss (Rademacher v.T H v) -- defined
    # on the linear-head parameters only (the Pythia weights are frozen).
    def sharpness_proxy(head: nn.Linear, x: torch.Tensor, y: torch.Tensor) -> float:
        head.zero_grad()
        loss = F.cross_entropy(head(x), y)
        params = [p for p in head.parameters() if p.requires_grad]
        v = [torch.randint(0, 2, p.shape, device=p.device).float() * 2 - 1 for p in params]
        grads = torch.autograd.grad(loss, params, create_graph=True)
        gv = sum((g * vv).sum() for g, vv in zip(grads, v))
        hv = torch.autograd.grad(gv, params, retain_graph=False)
        return float(sum((h * vv).sum().item() for h, vv in zip(hv, v)))

    # Equivariance count under a permutation group action.
    def equivariance_count(table: tuple[int, ...], group: tuple[tuple[int, ...], ...]) -> int:
        n = len(table)
        cnt = 0
        for g in group:
            induced = tuple(table[g[x]] for x in range(n))
            for h in group:
                if all(h[table[x]] == induced[x] for x in range(n)):
                    cnt += 1
                    break
        return cnt

    def cyclic_group(n: int) -> tuple[tuple[int, ...], ...]:
        return tuple(tuple((x + k) % n for x in range(n)) for k in range(n))

    def wrong_group(n: int, rng: random.Random, size_g: int) -> tuple[tuple[int, ...], ...]:
        identity = tuple(range(n))
        out: list[tuple[int, ...]] = [identity]
        cyc = set(cyclic_group(n))
        attempts = 0
        while len(out) < size_g and attempts < 2000:
            perm = list(range(n))
            rng.shuffle(perm)
            cand = tuple(perm)
            if cand not in cyc and cand not in out:
                out.append(cand)
            attempts += 1
        return tuple(out)

    cells = []
    for n in ns:
        for seed in seeds:
            torch.manual_seed(seed)
            rng = random.Random(seed)

            # Partial-orbit training -- pick an offset and a strict subset of inputs.
            offset = rng.randrange(1, n)
            truth = tuple((x + offset) % n for x in range(n))
            train_size = max(1, int(round(n * train_frac)))
            train_inputs = sorted(rng.sample(range(n), train_size))
            ood_inputs = [a for a in range(n) if a not in train_inputs]

            X_train = torch.stack([features[a] for a in train_inputs]).to(device)
            y_train = torch.tensor([truth[a] for a in train_inputs], dtype=torch.long, device=device)
            X_ood = torch.stack([features[a] for a in ood_inputs]).to(device) if ood_inputs else None
            y_ood = torch.tensor([truth[a] for a in ood_inputs], dtype=torch.long, device=device) if ood_inputs else None
            X_full = torch.stack([features[a] for a in range(n)]).to(device)

            head = nn.Linear(feature_dim, n).to(device)
            opt = torch.optim.Adam(head.parameters(), lr=head_lr)
            final_loss = math.inf
            for _ in range(head_epochs):
                opt.zero_grad()
                logits = head(X_train)
                loss = F.cross_entropy(logits, y_train)
                loss.backward()
                opt.step()
                final_loss = float(loss.item())

            head.eval()
            with torch.no_grad():
                table = tuple(int(p) for p in head(X_full).argmax(-1).cpu().tolist())
                train_acc = float((head(X_train).argmax(-1) == y_train).float().mean().item())
                if X_ood is not None:
                    ood_logits = head(X_ood)
                    ood_acc = float((ood_logits.argmax(-1) == y_ood).float().mean().item())
                    ood_nll = float(F.cross_entropy(ood_logits, y_ood).item())
                else:
                    ood_acc = float("nan")
                    ood_nll = float("nan")

            cyc = cyclic_group(n)
            w_oracle = equivariance_count(table, cyc)
            wrong = wrong_group(n, rng, n)
            w_wrong = equivariance_count(table, wrong)
            w_oracle_norm = w_oracle / max(1, len(cyc))
            w_wrong_norm = w_wrong / max(1, len(wrong))

            sharp = sharpness_proxy(head, X_train, y_train)
            pythia_l2 = math.sqrt(sum(float((p.detach() ** 2).sum().item()) for p in model.parameters()))
            pythia_param_count = int(sum(int(p.numel()) for p in model.parameters()))

            cells.append(dict(
                size=size, n=n, seed=seed, offset=offset,
                train_inputs=train_inputs, ood_inputs=ood_inputs,
                truth=list(truth), function_table=list(table),
                final_head_train_loss=final_loss, head_train_accuracy=train_acc,
                ood_accuracy=ood_acc, ood_nll=ood_nll,
                weakness_oracle=w_oracle, weakness_oracle_norm=w_oracle_norm,
                weakness_wrong_group=w_wrong, weakness_wrong_group_norm=w_wrong_norm,
                pythia_l2=pythia_l2, pythia_param_count=pythia_param_count,
                head_sharpness_proxy=sharp,
            ))

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return dict(size=size, cells=cells, feature_dim=int(feature_dim or 0))


def spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0

    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks

    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


@app.local_entrypoint()
def main(
    sizes: str = "70m,160m,410m",
    ns: str = "13,17,23",
    seeds: int = 3,
    train_frac: float = 0.5,
    head_epochs: int = 400,
    head_lr: float = 5e-3,
    base_seed: int = 20260618,
    out: str = "artifacts/external_contact/p1_pythia_weakness.json",
) -> None:
    size_list = [s.strip() for s in sizes.split(",") if s.strip()]
    n_list = [int(x.strip()) for x in ns.split(",") if x.strip()]
    seed_list = [base_seed + 100 * k for k in range(seeds)]

    shard_args = [
        dict(size=s, ns=n_list, seeds=seed_list, train_frac=train_frac,
             head_epochs=head_epochs, head_lr=head_lr)
        for s in size_list
    ]
    print(f"[P1] dispatching {len(shard_args)} Pythia-size shards in parallel: "
          f"sizes={size_list}, ns={n_list}, seeds={seed_list}, train_frac={train_frac}")
    results = list(run_size_shard.map(shard_args))

    all_cells = []
    for r in results:
        all_cells.extend(r["cells"])

    # ----- Spearman analysis across the full sweep -----
    if all_cells:
        oods = [c["ood_accuracy"] for c in all_cells if not math.isnan(c["ood_accuracy"])]
        valid = [c for c in all_cells if not math.isnan(c["ood_accuracy"])]
        oods = [c["ood_accuracy"] for c in valid]
        weakness = [c["weakness_oracle_norm"] for c in valid]
        wrong_group = [c["weakness_wrong_group_norm"] for c in valid]
        loss = [c["final_head_train_loss"] for c in valid]
        ood_nll = [c["ood_nll"] for c in valid]
        param_count = [c["pythia_param_count"] for c in valid]
        l2 = [c["pythia_l2"] for c in valid]
        sharp = [c["head_sharpness_proxy"] for c in valid]

        analysis = dict(
            n_cells=len(valid),
            rho_weakness_vs_ood=spearman(weakness, oods),
            rho_wrong_group_vs_ood=spearman(wrong_group, oods),
            rho_loss_vs_ood=spearman(loss, oods),
            rho_ood_nll_vs_ood=spearman(ood_nll, oods),
            rho_param_count_vs_ood=spearman(param_count, oods),
            rho_l2_vs_ood=spearman(l2, oods),
            rho_sharpness_vs_ood=spearman(sharp, oods),
        )

        rho_w = analysis["rho_weakness_vs_ood"]
        rivals = [abs(analysis[k]) for k in
                  ("rho_loss_vs_ood", "rho_ood_nll_vs_ood", "rho_param_count_vs_ood",
                   "rho_l2_vs_ood", "rho_sharpness_vs_ood")]
        best_rival = max(rivals) if rivals else 0.0
        analysis["best_classical_abs_rho"] = best_rival
        analysis["weakness_beats_best_classical_by_margin"] = abs(rho_w) - best_rival
        analysis["P1_pass"] = (
            rho_w >= 0.5
            and (abs(rho_w) - best_rival) >= 0.25
            and abs(analysis["rho_wrong_group_vs_ood"]) <= 0.15
        )
        analysis["P1_hard_kill"] = (
            rho_w < 0.3 or any(abs(rho_w) - r <= 0.10 for r in rivals)
        )
    else:
        analysis = dict(n_cells=0, P1_pass=None)

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(
        kind="REAL P1 Tier-B external run on Modal",
        manifest=dict(sizes=size_list, ns=n_list, seeds=seed_list,
                      train_frac=train_frac, head_epochs=head_epochs, head_lr=head_lr),
        analysis=analysis,
        cells=all_cells,
    )
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"[P1] wrote {out_path}")
    print(f"[P1] analysis: rho(weakness, OOD) = {analysis.get('rho_weakness_vs_ood'):.3f}; "
          f"best classical |rho| = {analysis.get('best_classical_abs_rho'):.3f}; "
          f"P1_pass = {analysis.get('P1_pass')}, hard_kill = {analysis.get('P1_hard_kill')}")
