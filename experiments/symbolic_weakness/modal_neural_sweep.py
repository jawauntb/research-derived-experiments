#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal entrypoint for the neural symbolic-weakness sweep.

Run with:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
            experiments/symbolic_weakness/modal_neural_sweep.py \
            --n-shards 8 --models-per-shard 64 --epochs 2000 \
            --base-seed 20260609 \
            --out artifacts/symbolic_weakness/modal_neural_sweep.json

Each shard runs an independent sub-sweep on a Modal worker (CPU is enough for
these tiny MLPs). The results are merged on the driver.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "numpy>=1.26,<2.0",
)

app = modal.App(name="research-derived-symbolic-weakness-neural")


@app.function(image=IMAGE, timeout=7200, cpu=4, max_containers=64, retries=1, nonpreemptible=True)
def shard_sweep(arg: dict[str, Any]) -> dict[str, Any]:
    models_per_shard = arg["models_per_shard"]
    base_seed = arg["base_seed"]
    epochs = arg["epochs"]
    shard_id = arg["shard_id"]
    """Run a single shard of the neural sweep. The sweep parameters are
    reproducible via base_seed + shard_id."""
    import sys
    sys.path.insert(0, "/root")
    sys.path.insert(0, "/workspace")
    # We re-implement the sweep inline so the function is self-contained on
    # the Modal worker. This is intentional: we do NOT mount the entire
    # research repo into the worker.
    import math
    import random

    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    def cyclic_prefix(rng: random.Random, modulus: int, train_window: int):
        offset = rng.randrange(1, modulus)
        truth = tuple((x + offset) % modulus for x in range(modulus))
        train_x = list(range(train_window))
        train_y = [truth[x] for x in train_x]
        return offset, truth, train_x, train_y

    def augment(rng, augmentation, count, modulus, truth, train_x, train_y):
        xs = list(train_x)
        ys = list(train_y)
        base = set(zip(xs, ys))
        if augmentation == "full_cyclic":
            for x in range(modulus):
                if (x, truth[x]) not in base:
                    xs.append(x)
                    ys.append(truth[x])
            return xs, ys
        if augmentation == "none" or count == 0:
            return xs, ys
        if augmentation == "partial_cyclic":
            cands = [x for x in range(modulus) if (x, truth[x]) not in base]
            rng.shuffle(cands)
            for x in cands[:count]:
                xs.append(x)
                ys.append(truth[x])
            return xs, ys
        if augmentation == "wrong_reflection":
            cands = [
                x for x in range(modulus)
                if (x, x) not in base and x != truth[x] and x not in xs
            ]
            rng.shuffle(cands)
            for x in cands[:count]:
                xs.append(x)
                ys.append(x)
            return xs, ys
        if augmentation == "wrong_random":
            attempts = 0
            added = 0
            while added < count and attempts < 200:
                x = rng.randrange(0, modulus)
                y = rng.randrange(0, modulus)
                if (x, y) not in base and x not in xs:
                    xs.append(x)
                    ys.append(y)
                    added += 1
                    base.add((x, y))
                attempts += 1
            return xs, ys
        raise ValueError(augmentation)

    def one_hot(values, n):
        out = torch.zeros(len(values), n)
        for r, v in enumerate(values):
            out[r, v] = 1.0
        return out

    def function_table(model, n):
        model.eval()
        with torch.no_grad():
            preds = model(one_hot(list(range(n)), n)).argmax(dim=-1).tolist()
        return tuple(int(p) for p in preds)

    def equiv_count(table, group):
        n = len(table)
        cnt = 0
        for g in group:
            induced = tuple(table[g[x]] for x in range(n))
            for h in group:
                if all(h[table[x]] == induced[x] for x in range(n)):
                    cnt += 1
                    break
        return cnt

    def cyclic_group(n):
        return tuple(tuple((x + k) % n for x in range(n)) for k in range(n))

    def wrong_group(n, rng, size):
        identity = tuple(range(n))
        out = [identity]
        cyc = set(cyclic_group(n))
        attempts = 0
        while len(out) < size and attempts < 200:
            p = list(range(n))
            rng.shuffle(p)
            cand = tuple(p)
            if cand not in cyc and cand not in out:
                out.append(cand)
            attempts += 1
        return tuple(out)

    def sharpness_proxy(model, inputs, targets):
        model.eval()
        params = [p for p in model.parameters() if p.requires_grad]
        vector = [torch.randint(0, 2, p.shape).float() * 2 - 1 for p in params]
        model.zero_grad()
        loss = F.cross_entropy(model(inputs), targets)
        grads = torch.autograd.grad(loss, params, create_graph=True)
        g_dot_v = sum((g * v).sum() for g, v in zip(grads, vector))
        hv = torch.autograd.grad(g_dot_v, params, retain_graph=False)
        return float(sum((h * v).sum().item() for h, v in zip(hv, vector)))

    rng = random.Random(base_seed + shard_id * 9999)
    artifacts = []
    for _ in range(models_per_shard):
        aug = rng.choice(["none", "partial_cyclic", "full_cyclic", "wrong_reflection", "wrong_random"])
        cnt = 0 if aug in ("none", "full_cyclic") else rng.choice([2, 4, 6, 8])
        trial_modulus = rng.choice([7, 11, 13])
        trial_window = rng.choice([2, 3, 4])
        seed = rng.randrange(0, 2**31 - 1)
        torch.manual_seed(seed)
        py_rng = random.Random(seed)
        offset, truth, train_x, train_y = cyclic_prefix(
            random.Random(seed + 12345), trial_modulus, trial_window
        )
        aug_x, aug_y = augment(py_rng, aug, cnt, trial_modulus, truth, train_x, train_y)
        inputs = one_hot(aug_x, trial_modulus)
        targets = torch.tensor(aug_y, dtype=torch.long)

        hidden = rng.choice([16, 32, 64, 128])
        depth = rng.choice([1, 2, 3])
        init_scale = rng.choice([0.3, 0.7, 1.0, 1.5])
        lr = rng.choice([1e-3, 3e-3, 1e-2, 3e-2])
        wd = rng.choice([0.0, 1e-4, 1e-2])
        optimizer_name = rng.choice(["adam", "sgd"])

        layers = []
        d_in = trial_modulus
        for _ in range(depth):
            lin = nn.Linear(d_in, hidden)
            with torch.no_grad():
                lin.weight.mul_(init_scale)
            layers.extend([lin, nn.ReLU()])
            d_in = hidden
        head = nn.Linear(d_in, trial_modulus)
        with torch.no_grad():
            head.weight.mul_(init_scale)
        layers.append(head)
        model = nn.Sequential(*layers)

        if optimizer_name == "adam":
            opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
        else:
            opt = torch.optim.SGD(
                model.parameters(), lr=lr, weight_decay=wd, momentum=0.9
            )

        final_loss = math.inf
        for _ in range(epochs):
            opt.zero_grad()
            loss = F.cross_entropy(model(inputs), targets)
            loss.backward()
            opt.step()
            final_loss = float(loss.item())

        table = function_table(model, trial_modulus)
        train_pred = [table[x] for x in train_x]
        train_acc = sum(int(p == y) for p, y in zip(train_pred, train_y)) / len(train_x)
        ood_inputs = list(range(trial_window, trial_modulus))
        ood_acc = sum(int(table[x] == truth[x]) for x in ood_inputs) / max(1, len(ood_inputs))
        held = (train_x[0], train_y[0])
        held_acc = float(table[held[0]] == held[1])

        cyc = cyclic_group(trial_modulus)
        w_oracle = equiv_count(table, cyc)
        wrong = wrong_group(trial_modulus, py_rng, trial_modulus)
        w_wrong = equiv_count(table, wrong)
        partial = cyc[: max(1, trial_modulus // 2)]
        w_partial = equiv_count(table, partial)

        param_l2 = math.sqrt(sum(float((p.detach()**2).sum().item()) for p in model.parameters()))
        sharp = sharpness_proxy(model, inputs, targets)

        artifacts.append({
            "seed": seed, "modulus": trial_modulus, "train_window": trial_window,
            "augmentation": aug, "augmentation_count": cnt,
            "hidden_width": hidden, "depth": depth, "init_scale": init_scale,
            "learning_rate": lr, "weight_decay": wd, "optimizer": optimizer_name,
            "epochs": epochs,
            "final_train_loss": final_loss, "train_accuracy": train_acc,
            "held_out_validation_accuracy": held_acc,
            "ood_accuracy": ood_acc, "parameter_l2": param_l2,
            "sharpness_proxy": sharp,
            "weakness_oracle": w_oracle, "weakness_wrong_group": w_wrong,
            "weakness_partial_cyclic": w_partial,
            "full_function_table": list(table),
        })
    return {"shard_id": shard_id, "artifacts": artifacts}


@app.local_entrypoint()
def main(
    n_shards: int = 8,
    models_per_shard: int = 64,
    modulus: int = 11,
    train_window: int = 3,
    epochs: int = 2000,
    base_seed: int = 20260609,
    out: str = "artifacts/symbolic_weakness/modal_neural_sweep.json",
) -> None:
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    shard_args = [
        {
            "models_per_shard": models_per_shard,
            "modulus": modulus,
            "train_window": train_window,
            "base_seed": base_seed,
            "epochs": epochs,
            "shard_id": i,
        }
        for i in range(n_shards)
    ]
    results = list(shard_sweep.map(shard_args))
    all_artifacts = []
    for r in results:
        all_artifacts.extend(r["artifacts"])
    payload = {
        "manifest": {
            "n_shards": n_shards,
            "models_per_shard": models_per_shard,
            "modulus": modulus,
            "train_window": train_window,
            "epochs": epochs,
            "base_seed": base_seed,
            "total_models": len(all_artifacts),
        },
        "artifacts": all_artifacts,
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Wrote {len(all_artifacts)} model artifacts to {out_path}")
