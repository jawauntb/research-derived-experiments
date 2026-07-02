#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Tool-commitment moved-bottleneck sweep on Modal L4 workers.

This extends the synthetic sequence result into a tool/API-like regime. The
agent sees early clue bits, reaches a commit token, and must emit a tool slot
plus tool value. The environment then returns the committed value on a later
tool-return token before the final query. The moved bottleneck is now the
future-critical external commitment, not only hidden-state memory.

Recommended cheap pass:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_tool_commitment_sweep.py \\
        --seeds 4 --train-steps 700 --architectures transformer \\
        --conditions tool_bottleneck,visible_control --critical-slots 0,1,2,3 \\
        --budget-usd 25 \\
        --out artifacts/long_horizon_bottleneck/tool_commitment_l4.json
"""

from __future__ import annotations

import importlib
import json
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

app = modal.App(name="research-derived-tool-commitment-bottleneck")


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
def run_tool_cell(arg: dict[str, Any]) -> dict[str, Any]:
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
    commit_position = int(arg["commit_position"])
    train_steps = int(arg["train_steps"])
    batch_size = int(arg["batch_size"])
    eval_batches = int(arg["eval_batches"])
    metric_batches = int(arg["metric_batches"])
    hidden_size = int(arg["hidden_size"])

    torch.manual_seed(seed)
    torch.set_float32_matmul_precision("high")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    input_dim = 1 + n_slots + 1 + 1 + 1 + 1 + 1 + 1
    clue_idx = 0
    slot_offset = 1
    bit_idx = slot_offset + n_slots
    commit_idx = bit_idx + 1
    tool_return_idx = commit_idx + 1
    tool_return_value_idx = tool_return_idx + 1
    query_idx = tool_return_value_idx + 1
    terminal_bit_idx = query_idx + 1
    null_tool_slot = n_slots
    tool_return_position = commit_position + 1

    def make_batch(batch: int):
        x = torch.zeros(batch, sequence_length, input_dim, device=device)
        bits = torch.randint(0, 2, (batch, n_slots), device=device)
        terminal_bits = torch.randint(0, 2, (batch,), device=device)
        for slot, pos in enumerate(slot_positions):
            x[:, pos, clue_idx] = 1.0
            x[:, pos, slot_offset + slot] = 1.0
            x[:, pos, bit_idx] = bits[:, slot].float() * 2.0 - 1.0

        x[:, commit_position, commit_idx] = 1.0
        x[:, -1, query_idx] = 1.0
        x[:, -1, terminal_bit_idx] = terminal_bits.float() * 2.0 - 1.0

        if condition == "tool_bottleneck":
            final_target = bits[:, critical_slot].long()
            tool_slot_target = torch.full((batch,), critical_slot, dtype=torch.long, device=device)
            tool_value_target = bits[:, critical_slot].long()
            x[:, tool_return_position, tool_return_idx] = 1.0
            x[:, tool_return_position, tool_return_value_idx] = tool_value_target.float() * 2.0 - 1.0
            train_tool_value = True
        elif condition == "visible_control":
            final_target = terminal_bits.long()
            tool_slot_target = torch.full((batch,), null_tool_slot, dtype=torch.long, device=device)
            tool_value_target = torch.zeros(batch, dtype=torch.long, device=device)
            train_tool_value = False
        else:
            raise ValueError(condition)
        return x, final_target, tool_slot_target, tool_value_target, train_tool_value

    class GRUAgent(nn.Module):
        def __init__(self):
            super().__init__()
            self.rnn = nn.GRU(input_dim, hidden_size, batch_first=True)
            self.final_head = nn.Linear(hidden_size, 2)
            self.tool_slot_head = nn.Linear(hidden_size, n_slots + 1)
            self.tool_value_head = nn.Linear(hidden_size, 2)

        def forward(self, x):
            states, _ = self.rnn(x)
            commit_state = states[:, commit_position]
            return (
                self.final_head(states[:, -1]),
                self.tool_slot_head(commit_state),
                self.tool_value_head(commit_state),
                states,
            )

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
            self.final_head = nn.Linear(hidden_size, 2)
            self.tool_slot_head = nn.Linear(hidden_size, n_slots + 1)
            self.tool_value_head = nn.Linear(hidden_size, 2)
            mask = torch.triu(torch.ones(sequence_length, sequence_length), diagonal=1).bool()
            self.register_buffer("causal_mask", mask)

        def forward(self, x):
            states = self.encoder(self.inp(x) + self.pos.unsqueeze(0), mask=self.causal_mask)
            commit_state = states[:, commit_position]
            return (
                self.final_head(states[:, -1]),
                self.tool_slot_head(commit_state),
                self.tool_value_head(commit_state),
                states,
            )

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
        x, final_target, tool_slot_target, tool_value_target, train_tool_value = make_batch(batch_size)
        final_logits, tool_slot_logits, tool_value_logits, _ = model(x)
        loss = F.cross_entropy(final_logits, final_target)
        loss = loss + 0.5 * F.cross_entropy(tool_slot_logits, tool_slot_target)
        if train_tool_value:
            loss = loss + 0.5 * F.cross_entropy(tool_value_logits, tool_value_target)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step == 0 or (step + 1) % max(1, train_steps // 5) == 0:
            losses.append(float(loss.detach().cpu().item()))

    model.eval()
    final_correct = 0
    slot_correct = 0
    value_correct = 0
    value_total = 0
    total = 0
    with torch.no_grad():
        for _ in range(eval_batches):
            x, final_target, tool_slot_target, tool_value_target, train_tool_value = make_batch(batch_size)
            final_logits, tool_slot_logits, tool_value_logits, _ = model(x)
            final_correct += int((final_logits.argmax(-1) == final_target).sum().item())
            slot_correct += int((tool_slot_logits.argmax(-1) == tool_slot_target).sum().item())
            if train_tool_value:
                value_correct += int((tool_value_logits.argmax(-1) == tool_value_target).sum().item())
                value_total += int(tool_value_target.numel())
            total += int(final_target.numel())
    final_accuracy = final_correct / total if total else float("nan")
    tool_slot_accuracy = slot_correct / total if total else float("nan")
    tool_value_accuracy = value_correct / value_total if value_total else float("nan")

    def density_for_slot(slot: int) -> tuple[float, float, float, float]:
        memory_vals = []
        commit_vals = []
        final_logit_vals = []
        tool_value_vals = []
        with torch.no_grad():
            for _ in range(metric_batches):
                x0, _, _, _, _ = make_batch(batch_size)
                x1 = x0.clone()
                pos = slot_positions[slot]
                x1[:, pos, bit_idx] = -x1[:, pos, bit_idx]
                if condition == "tool_bottleneck" and slot == critical_slot:
                    x1[:, tool_return_position, tool_return_value_idx] = -x1[
                        :, tool_return_position, tool_return_value_idx
                    ]
                final0, _, tool_value0, states0 = model(x0)
                final1, _, tool_value1, states1 = model(x1)
                memory_vals.append((states1[:, -1] - states0[:, -1]).norm(dim=-1).mean())
                commit_vals.append((states1[:, commit_position] - states0[:, commit_position]).norm(dim=-1).mean())
                final_logit_vals.append((final1 - final0).norm(dim=-1).mean())
                tool_value_vals.append((tool_value1 - tool_value0).norm(dim=-1).mean())
        return (
            float(torch.stack(memory_vals).mean().cpu().item()),
            float(torch.stack(commit_vals).mean().cpu().item()),
            float(torch.stack(final_logit_vals).mean().cpu().item()),
            float(torch.stack(tool_value_vals).mean().cpu().item()),
        )

    densities = [density_for_slot(slot) for slot in range(n_slots)]
    memory_density = [x[0] for x in densities]
    commit_density = [x[1] for x in densities]
    final_logit_density = [x[2] for x in densities]
    tool_value_density = [x[3] for x in densities]

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
    commit = specificity(commit_density)
    final_logit = specificity(final_logit_density)
    tool_value = specificity(tool_value_density)
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
        "commit_position": commit_position,
        "train_steps": train_steps,
        "batch_size": batch_size,
        "eval_batches": eval_batches,
        "metric_batches": metric_batches,
        "hidden_size": hidden_size,
        "device": str(device),
        "runtime_seconds": runtime,
        "loss_trace": losses,
        "accuracy": final_accuracy,
        "final_accuracy": final_accuracy,
        "tool_slot_accuracy": tool_slot_accuracy,
        "tool_value_accuracy": tool_value_accuracy,
        "memory_density": memory_density,
        "commit_density": commit_density,
        "final_logit_density": final_logit_density,
        "tool_value_density": tool_value_density,
        "memory_critical_z": mem["critical_z"],
        "memory_wrong_z_mean": mem["wrong_z_mean"],
        "memory_specificity_z": mem["specificity_z"],
        "memory_rank_percentile": mem["rank_percentile"],
        "commit_specificity_z": commit["specificity_z"],
        "commit_rank_percentile": commit["rank_percentile"],
        "final_logit_specificity_z": final_logit["specificity_z"],
        "final_logit_rank_percentile": final_logit["rank_percentile"],
        "tool_value_specificity_z": tool_value["specificity_z"],
        "tool_value_rank_percentile": tool_value["rank_percentile"],
    }


@app.local_entrypoint()
def main(
    seeds: int = 4,
    train_steps: int = 700,
    batch_size: int = 256,
    eval_batches: int = 4,
    metric_batches: int = 3,
    hidden_size: int = 64,
    sequence_length: int = 128,
    n_slots: int = 4,
    slot_gap: int = 8,
    commit_position: int = -1,
    architectures: str = "transformer",
    conditions: str = "tool_bottleneck,visible_control",
    critical_slots: str = "0,1,2,3",
    base_seed: int = 20260702,
    budget_usd: float = 25.0,
    dry_run_budget: bool = False,
    out: str = "artifacts/long_horizon_bottleneck/tool_commitment_l4.json",
):
    from experiments.long_horizon_bottleneck.core import (
        build_cells,
        estimate_modal_cost,
        parse_csv,
        parse_int_csv,
        summarize_tool_rows,
    )

    arch_list = parse_csv(architectures)
    condition_list = parse_csv(conditions)
    slot_list = parse_int_csv(critical_slots)
    seed_values = list(range(seeds))
    cells = build_cells(
        seeds=seed_values,
        architectures=arch_list,
        conditions=condition_list,
        critical_slots=slot_list,
        n_slots=n_slots,
        sequence_length=sequence_length,
        slot_gap=slot_gap,
        train_steps=train_steps,
        batch_size=batch_size,
        eval_batches=eval_batches,
        metric_batches=metric_batches,
        hidden_size=hidden_size,
        base_seed=base_seed,
    )
    resolved_commit_position = sequence_length // 2 if commit_position < 0 else commit_position
    max_slot_position = max(cells[0]["slot_positions"])
    if resolved_commit_position <= max_slot_position:
        raise SystemExit("commit_position must occur after all clue slots")
    if resolved_commit_position + 1 >= sequence_length - 1:
        raise SystemExit("commit_position must leave room for tool return before the final query")
    for cell in cells:
        cell["commit_position"] = resolved_commit_position

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
        "sequence_length": sequence_length,
        "slot_gap": slot_gap,
        "commit_position": resolved_commit_position,
        "train_steps": train_steps,
        "batch_size": batch_size,
        "eval_batches": eval_batches,
        "metric_batches": metric_batches,
        "hidden_size": hidden_size,
        "budget_estimate": estimate.__dict__,
    }
    print(
        "[tool-commitment] "
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
        print(json.dumps({"kind": "tool-commitment bottleneck dry run", "manifest": manifest}, indent=2))
        return

    rows = list(run_tool_cell.map(cells))
    summary = summarize_tool_rows(rows)
    payload = {
        "kind": "tool-commitment moved-bottleneck sweep",
        "manifest": manifest,
        "summary": summary,
        "rows": rows,
    }
    op = Path(out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[tool-commitment] wrote {op}")
    for key, item in summary["groups"].items():
        final_acc = item["final_accuracy"]
        slot_acc = item["tool_slot_accuracy"]
        spec = item["memory_specificity_z"]
        tool_spec = item["tool_value_specificity_z"]
        print(
            f"  {key:32s} final={final_acc['mean']:.3f} slot={slot_acc['mean']:.3f} "
            f"memory_spec={spec['mean']:+.3f} tool_spec={tool_spec['mean']:+.3f} "
            f"pass={item['gate']['pass']}"
        )
    if "pooled_tool_bottleneck" in summary:
        pooled = summary["pooled_tool_bottleneck"]
        print(
            "[tool-commitment] pooled tool_bottleneck "
            f"final={pooled['final_accuracy']['mean']:.3f}; "
            f"slot={pooled['tool_slot_accuracy']['mean']:.3f}; "
            f"value={pooled['tool_value_accuracy']['mean']:.3f}; "
            f"memory_spec={pooled['memory_specificity_z']['mean']:+.3f}; "
            f"tool_spec={pooled['tool_value_specificity_z']['mean']:+.3f}; "
            f"pass={pooled['gate']['pass']}"
        )
