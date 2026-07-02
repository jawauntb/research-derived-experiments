#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Long-horizon moved-bottleneck sweep on Modal L4 workers.

This is the temporal analogue of Paper B's moved-location intervention. Four
early clue slots are matched for frequency and salience; only one slot is
future-critical for a delayed final decision. The critical slot is moved across
registered values, and the primary metric asks whether final memory-state
sensitivity moves with it.

Smoke:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_moved_bottleneck_sweep.py \\
        --seeds 1 --train-steps 120 --architectures gru \\
        --conditions bottleneck,visible_control --budget-usd 10 \\
        --out artifacts/long_horizon_bottleneck/smoke.json

Default:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_moved_bottleneck_sweep.py \\
        --seeds 8 --train-steps 700 --budget-usd 100 \\
        --out artifacts/long_horizon_bottleneck/moved_bottleneck_sweep.json

Horizon stress:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_moved_bottleneck_sweep.py \\
        --seeds 4 --train-steps 700 --architectures transformer \\
        --conditions bottleneck,visible_control --critical-slots 0,1,2,3 \\
        --sequence-lengths 128,256,384 --budget-usd 50 \\
        --out artifacts/long_horizon_bottleneck/horizon_transformer_l4.json
"""

from __future__ import annotations

import importlib
import json
import math
import time
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

GPU = "L4"
TIMEOUT_SECONDS = 900

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "numpy>=1.26,<2.2",
)

app = modal.App(name="research-derived-long-horizon-bottleneck")


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=4,
    memory=8192,
    max_containers=32,
    single_use_containers=True,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    architecture = str(arg["architecture"])
    condition = str(arg["condition"])
    critical_slot = int(arg["critical_slot"])
    seed = int(arg["seed"])
    n_slots = int(arg["n_slots"])
    sequence_length = int(arg["sequence_length"])
    slot_positions = [int(x) for x in arg["slot_positions"]]
    train_steps = int(arg["train_steps"])
    batch_size = int(arg["batch_size"])
    eval_batches = int(arg["eval_batches"])
    metric_batches = int(arg["metric_batches"])
    hidden_size = int(arg["hidden_size"])

    torch.manual_seed(seed)
    torch.set_float32_matmul_precision("high")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    input_dim = 1 + n_slots + 1 + 1 + 1
    clue_idx = 0
    slot_offset = 1
    bit_idx = slot_offset + n_slots
    query_idx = bit_idx + 1
    terminal_bit_idx = query_idx + 1

    def make_batch(batch: int):
        x = torch.zeros(batch, sequence_length, input_dim, device=device)
        bits = torch.randint(0, 2, (batch, n_slots), device=device)
        terminal_bits = torch.randint(0, 2, (batch,), device=device)
        for slot, pos in enumerate(slot_positions):
            x[:, pos, clue_idx] = 1.0
            x[:, pos, slot_offset + slot] = 1.0
            x[:, pos, bit_idx] = bits[:, slot].float() * 2.0 - 1.0
        x[:, -1, query_idx] = 1.0
        x[:, -1, terminal_bit_idx] = terminal_bits.float() * 2.0 - 1.0
        if condition == "bottleneck":
            target = bits[:, critical_slot].long()
        elif condition == "visible_control":
            target = terminal_bits.long()
        else:
            raise ValueError(condition)
        return x, target

    class GRUAgent(nn.Module):
        def __init__(self):
            super().__init__()
            self.rnn = nn.GRU(input_dim, hidden_size, batch_first=True)
            self.head = nn.Linear(hidden_size, 2)

        def forward(self, x):
            states, _ = self.rnn(x)
            return self.head(states[:, -1]), states

    class TransformerAgent(nn.Module):
        def __init__(self):
            super().__init__()
            self.inp = nn.Linear(input_dim, hidden_size)
            self.pos = nn.Parameter(torch.randn(sequence_length, hidden_size) * 0.02)
            layer = nn.TransformerEncoderLayer(
                d_model=hidden_size,
                nhead=4,
                dim_feedforward=4 * hidden_size,
                dropout=0.0,
                activation="gelu",
                batch_first=True,
                norm_first=True,
            )
            self.encoder = nn.TransformerEncoder(layer, num_layers=2)
            self.head = nn.Linear(hidden_size, 2)
            mask = torch.triu(torch.ones(sequence_length, sequence_length), diagonal=1).bool()
            self.register_buffer("causal_mask", mask)

        def forward(self, x):
            h = self.inp(x) + self.pos.unsqueeze(0)
            states = self.encoder(h, mask=self.causal_mask)
            return self.head(states[:, -1]), states

    if architecture == "gru":
        model = GRUAgent().to(device)
    elif architecture == "transformer":
        model = TransformerAgent().to(device)
    else:
        raise ValueError(architecture)

    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    t0 = time.time()
    losses = []
    model.train()
    for step in range(train_steps):
        x, y = make_batch(batch_size)
        logits, _ = model(x)
        loss = F.cross_entropy(logits, y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step == 0 or (step + 1) % max(1, train_steps // 5) == 0:
            losses.append(float(loss.detach().cpu().item()))

    model.eval()
    total = 0
    correct = 0
    with torch.no_grad():
        for _ in range(eval_batches):
            x, y = make_batch(batch_size)
            logits, _ = model(x)
            pred = logits.argmax(-1)
            correct += int((pred == y).sum().item())
            total += int(y.numel())
    accuracy = correct / total if total else float("nan")

    def density_for_slot(slot: int) -> tuple[float, float, float]:
        memory_vals = []
        local_vals = []
        logit_vals = []
        with torch.no_grad():
            for _ in range(metric_batches):
                x0, _ = make_batch(batch_size)
                x1 = x0.clone()
                pos = slot_positions[slot]
                x1[:, pos, bit_idx] = -x1[:, pos, bit_idx]
                logits0, states0 = model(x0)
                logits1, states1 = model(x1)
                memory_vals.append((states1[:, -1] - states0[:, -1]).norm(dim=-1).mean())
                local_vals.append((states1[:, pos] - states0[:, pos]).norm(dim=-1).mean())
                logit_vals.append((logits1 - logits0).norm(dim=-1).mean())
        return (
            float(torch.stack(memory_vals).mean().cpu().item()),
            float(torch.stack(local_vals).mean().cpu().item()),
            float(torch.stack(logit_vals).mean().cpu().item()),
        )

    densities = [density_for_slot(slot) for slot in range(n_slots)]
    memory_density = [x[0] for x in densities]
    local_density = [x[1] for x in densities]
    logit_density = [x[2] for x in densities]

    def specificity(values: list[float]) -> dict[str, float]:
        vals = torch.tensor(values, dtype=torch.float64)
        z = (vals - vals.mean()) / (vals.std(unbiased=False) + 1e-9)
        crit = float(z[critical_slot].item())
        wrong = [float(z[i].item()) for i in range(n_slots) if i != critical_slot]
        crit_raw = float(vals[critical_slot].item())
        less = sum(1 for value in values if value < crit_raw)
        equal = sum(1 for value in values if value == crit_raw)
        rank = (less + 0.5 * equal) / len(values)
        return {
            "critical_z": crit,
            "wrong_z_mean": sum(wrong) / len(wrong),
            "specificity_z": crit - (sum(wrong) / len(wrong)),
            "rank_percentile": rank,
        }

    mem = specificity(memory_density)
    loc = specificity(local_density)
    logit = specificity(logit_density)
    if device.type == "cuda":
        torch.cuda.synchronize()
    runtime = time.time() - t0

    return {
        "architecture": architecture,
        "condition": condition,
        "critical_slot": critical_slot,
        "seed": seed,
        "sequence_length": sequence_length,
        "slot_positions": slot_positions,
        "train_steps": train_steps,
        "batch_size": batch_size,
        "eval_batches": eval_batches,
        "metric_batches": metric_batches,
        "hidden_size": hidden_size,
        "device": str(device),
        "runtime_seconds": runtime,
        "loss_trace": losses,
        "accuracy": accuracy,
        "memory_density": memory_density,
        "local_density": local_density,
        "logit_density": logit_density,
        "memory_critical_z": mem["critical_z"],
        "memory_wrong_z_mean": mem["wrong_z_mean"],
        "memory_specificity_z": mem["specificity_z"],
        "memory_rank_percentile": mem["rank_percentile"],
        "local_specificity_z": loc["specificity_z"],
        "local_rank_percentile": loc["rank_percentile"],
        "logit_specificity_z": logit["specificity_z"],
        "logit_rank_percentile": logit["rank_percentile"],
    }


@app.local_entrypoint()
def main(
    seeds: int = 8,
    train_steps: int = 700,
    batch_size: int = 256,
    eval_batches: int = 4,
    metric_batches: int = 3,
    hidden_size: int = 64,
    sequence_length: int = 128,
    sequence_lengths: str = "",
    n_slots: int = 4,
    slot_gap: int = 8,
    architectures: str = "gru,transformer",
    conditions: str = "bottleneck,visible_control",
    critical_slots: str = "0,1,2,3",
    base_seed: int = 20260702,
    budget_usd: float = 100.0,
    dry_run_budget: bool = False,
    out: str = "artifacts/long_horizon_bottleneck/moved_bottleneck_sweep.json",
):
    from experiments.long_horizon_bottleneck.core import (
        build_cells,
        build_horizon_cells,
        estimate_modal_cost,
        parse_csv,
        parse_int_csv,
        summarize_rows,
    )

    arch_list = parse_csv(architectures)
    condition_list = parse_csv(conditions)
    slot_list = parse_int_csv(critical_slots)
    sequence_length_list = parse_int_csv(sequence_lengths) if sequence_lengths else [sequence_length]
    seed_values = list(range(seeds))
    if len(sequence_length_list) == 1:
        cells = build_cells(
            seeds=seed_values,
            architectures=arch_list,
            conditions=condition_list,
            critical_slots=slot_list,
            n_slots=n_slots,
            sequence_length=sequence_length_list[0],
            slot_gap=slot_gap,
            train_steps=train_steps,
            batch_size=batch_size,
            eval_batches=eval_batches,
            metric_batches=metric_batches,
            hidden_size=hidden_size,
            base_seed=base_seed,
        )
    else:
        cells = build_horizon_cells(
            sequence_lengths=sequence_length_list,
            seeds=seed_values,
            architectures=arch_list,
            conditions=condition_list,
            critical_slots=slot_list,
            n_slots=n_slots,
            slot_gap=slot_gap,
            train_steps=train_steps,
            batch_size=batch_size,
            eval_batches=eval_batches,
            metric_batches=metric_batches,
            hidden_size=hidden_size,
            base_seed=base_seed,
        )
    estimate = estimate_modal_cost(
        cells=len(cells),
        gpu=GPU,
        timeout_seconds=TIMEOUT_SECONDS,
        budget_usd=budget_usd,
    )
    manifest = {
        "gpu": GPU,
        "timeout_seconds": TIMEOUT_SECONDS,
        "max_containers": 32,
        "single_use_containers": True,
        "seeds": seeds,
        "base_seed": base_seed,
        "architectures": arch_list,
        "conditions": condition_list,
        "critical_slots": slot_list,
        "n_slots": n_slots,
        "sequence_length": sequence_length_list[0],
        "sequence_lengths": sequence_length_list,
        "slot_gap": slot_gap,
        "train_steps": train_steps,
        "batch_size": batch_size,
        "eval_batches": eval_batches,
        "metric_batches": metric_batches,
        "hidden_size": hidden_size,
        "budget_estimate": estimate.__dict__,
    }
    print(
        "[moved-bottleneck] "
        f"cells={len(cells)} gpu={GPU} timeout={TIMEOUT_SECONDS}s "
        f"conservative_cost=${estimate.conservative_cost_usd:.2f} "
        f"budget=${budget_usd:.2f}"
    )
    if not estimate.within_budget:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate.conservative_cost_usd:.2f} exceeds budget ${budget_usd:.2f}."
        )
    if dry_run_budget:
        print(json.dumps({"kind": "long-horizon moved-bottleneck dry run", "manifest": manifest}, indent=2))
        return

    rows = list(run_cell.map(cells))
    summary = summarize_rows(rows)
    payload = {
        "kind": "long-horizon moved-bottleneck sweep",
        "manifest": manifest,
        "summary": summary,
        "rows": rows,
    }
    op = Path(out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[moved-bottleneck] wrote {op}")
    for key, item in summary["groups"].items():
        acc = item["accuracy"]
        spec = item["memory_specificity_z"]
        rank = item["memory_rank_percentile"]
        print(
            f"  {key:28s} acc={acc['mean']:.3f} "
            f"spec={spec['mean']:+.3f} CI[{spec['ci95'][0]:+.3f},{spec['ci95'][1]:+.3f}] "
            f"rank={rank['mean']:.3f} pass={item['gate']['pass']}"
        )
    if summary["horizon_groups"]:
        print("[moved-bottleneck] horizon groups")
        for key, item in summary["horizon_groups"].items():
            acc = item["accuracy"]
            spec = item["memory_specificity_z"]
            rank = item["memory_rank_percentile"]
            print(
                f"  {key:39s} acc={acc['mean']:.3f} "
                f"spec={spec['mean']:+.3f} CI[{spec['ci95'][0]:+.3f},{spec['ci95'][1]:+.3f}] "
                f"rank={rank['mean']:.3f} pass={item['gate']['pass']}"
            )
    if "pooled_bottleneck" in summary:
        pooled = summary["pooled_bottleneck"]
        print(
            "[moved-bottleneck] pooled bottleneck "
            f"acc={pooled['accuracy']['mean']:.3f}; "
            f"spec={pooled['memory_specificity_z']['mean']:+.3f}; "
            f"rank={pooled['memory_rank_percentile']['mean']:.3f}; "
            f"pass={pooled['gate']['pass']}"
        )
