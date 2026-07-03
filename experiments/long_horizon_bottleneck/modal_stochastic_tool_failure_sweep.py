#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Stochastic tool-failure moved-bottleneck sweep on Modal L4 workers.

This is the regime after deterministic multifield tool schemas. The agent emits
separate opcode, slot-argument, and value-argument fields:

    call -> {"tool": "read_slot", "slot": 2, "value": 1}
    noop -> {"tool": "noop"}

The first tool call now fails stochastically per episode. On success, the agent
should no-op at the repair position; on failure, it must repair by re-emitting a
complete call for the moved bottleneck slot.

The alias conditions replace the compact slot argument with several equivalent
argument aliases per canonical slot. The parser maps aliases back to canonical
slots, so the gate asks whether the bottleneck survives a synonym-like argument
surface rather than a tiny slot-id field.

Recommended cheap pass:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
        experiments/long_horizon_bottleneck/modal_stochastic_tool_failure_sweep.py \\
        --seeds 4 --train-steps 900 --architectures transformer \\
        --conditions stochastic_failure_bottleneck,stochastic_visible_control \\
        --critical-slots 0,1,2,3 --budget-usd 25 \\
        --out artifacts/long_horizon_bottleneck/stochastic_tool_failure_l4.json
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

app = modal.App(name="research-derived-stochastic-tool-failure-bottleneck")


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
def run_stochastic_cell(arg: dict[str, Any]) -> dict[str, Any]:
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
    first_commit_position = int(arg["first_commit_position"])
    train_steps = int(arg["train_steps"])
    batch_size = int(arg["batch_size"])
    eval_batches = int(arg["eval_batches"])
    metric_batches = int(arg["metric_batches"])
    hidden_size = int(arg["hidden_size"])
    failure_probability = float(arg["failure_probability"])
    aliases_per_slot = int(arg.get("aliases_per_slot", 1))

    alias_conditions = {"alias_stochastic_bottleneck", "alias_visible_control"}
    bottleneck_conditions = {"stochastic_failure_bottleneck", "alias_stochastic_bottleneck"}
    visible_conditions = {"stochastic_visible_control", "alias_visible_control"}
    alias_surface = condition in alias_conditions
    if aliases_per_slot <= 0:
        raise ValueError("aliases_per_slot must be positive")

    call_opcode = 0
    noop_opcode = 1
    opcode_vocab_size = 3
    slot_argument_size = n_slots * aliases_per_slot if alias_surface else n_slots
    slot_missing_id = slot_argument_size
    slot_vocab_size = slot_argument_size + 2
    value_missing_id = 2
    value_vocab_size = 4

    torch.manual_seed(seed)
    torch.set_float32_matmul_precision("high")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    input_dim = 1 + n_slots + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 1
    clue_idx = 0
    slot_offset = 1
    bit_idx = slot_offset + n_slots
    first_commit_idx = bit_idx + 1
    error_idx = first_commit_idx + 1
    repair_commit_idx = error_idx + 1
    tool_return_idx = repair_commit_idx + 1
    tool_return_value_idx = tool_return_idx + 1
    query_idx = tool_return_value_idx + 1
    terminal_bit_idx = query_idx + 1
    first_return_position = first_commit_position + 1
    repair_commit_position = first_commit_position + 2
    repair_return_position = first_commit_position + 3

    def make_batch(batch: int, *, include_teacher_return: bool = True):
        x = torch.zeros(batch, sequence_length, input_dim, device=device)
        bits = torch.randint(0, 2, (batch, n_slots), device=device)
        terminal_bits = torch.randint(0, 2, (batch,), device=device)
        first_failed = torch.rand(batch, device=device) < failure_probability
        feedback_values = torch.randint(0, 2, (batch,), device=device)
        for slot, pos in enumerate(slot_positions):
            x[:, pos, clue_idx] = 1.0
            x[:, pos, slot_offset + slot] = 1.0
            x[:, pos, bit_idx] = bits[:, slot].float() * 2.0 - 1.0

        x[:, first_commit_position, first_commit_idx] = 1.0
        x[:, repair_commit_position, repair_commit_idx] = 1.0
        x[:, -1, query_idx] = 1.0
        x[:, -1, terminal_bit_idx] = terminal_bits.float() * 2.0 - 1.0

        crit_slot = torch.full((batch,), critical_slot, dtype=torch.long, device=device)
        crit_value = bits[:, critical_slot].long()
        call_op = torch.full((batch,), call_opcode, dtype=torch.long, device=device)
        noop_op = torch.full((batch,), noop_opcode, dtype=torch.long, device=device)
        noop_slot = torch.full((batch,), slot_missing_id, dtype=torch.long, device=device)
        noop_value = torch.full((batch,), value_missing_id, dtype=torch.long, device=device)

        if condition in bottleneck_conditions:
            final_target = bits[:, critical_slot].long()
            first_targets = (call_op, crit_slot, crit_value)
            repair_targets = (
                torch.where(first_failed, call_op, noop_op),
                torch.where(first_failed, crit_slot, noop_slot),
                torch.where(first_failed, crit_value, noop_value),
            )
            if include_teacher_return:
                first_succeeded = ~first_failed
                x[first_failed, first_return_position, error_idx] = 1.0
                x[first_succeeded, first_return_position, tool_return_idx] = 1.0
                x[first_succeeded, first_return_position, tool_return_value_idx] = (
                    crit_value[first_succeeded].float() * 2.0 - 1.0
                )
                x[first_failed, repair_return_position, tool_return_idx] = 1.0
                x[first_failed, repair_return_position, tool_return_value_idx] = (
                    crit_value[first_failed].float() * 2.0 - 1.0
                )
            train_first = True
            train_repair = True
        elif condition in visible_conditions:
            final_target = terminal_bits.long()
            first_targets = (noop_op, noop_slot, noop_value)
            repair_targets = (noop_op, noop_slot, noop_value)
            if include_teacher_return:
                first_succeeded = ~first_failed
                x[first_failed, first_return_position, error_idx] = 1.0
                x[first_succeeded, first_return_position, tool_return_idx] = 1.0
                x[first_succeeded, first_return_position, tool_return_value_idx] = (
                    feedback_values[first_succeeded].float() * 2.0 - 1.0
                )
            train_first = True
            train_repair = True
        else:
            raise ValueError(condition)
        return x, final_target, first_targets, repair_targets, crit_value, first_failed, feedback_values, train_first, train_repair

    class GRUAgent(nn.Module):
        def __init__(self):
            super().__init__()
            self.rnn = nn.GRU(input_dim, hidden_size, batch_first=True)
            self.final_head = nn.Linear(hidden_size, 2)
            self.opcode_head = nn.Linear(hidden_size, opcode_vocab_size)
            self.slot_head = nn.Linear(hidden_size, slot_vocab_size)
            self.value_head = nn.Linear(hidden_size, value_vocab_size)

        def forward(self, x):
            states, _ = self.rnn(x)
            first_state = states[:, first_commit_position]
            repair_state = states[:, repair_commit_position]
            return (
                self.final_head(states[:, -1]),
                self.opcode_head(first_state),
                self.slot_head(first_state),
                self.value_head(first_state),
                self.opcode_head(repair_state),
                self.slot_head(repair_state),
                self.value_head(repair_state),
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
            self.opcode_head = nn.Linear(hidden_size, opcode_vocab_size)
            self.slot_head = nn.Linear(hidden_size, slot_vocab_size)
            self.value_head = nn.Linear(hidden_size, value_vocab_size)
            mask = torch.triu(torch.ones(sequence_length, sequence_length), diagonal=1).bool()
            self.register_buffer("causal_mask", mask)

        def forward(self, x):
            states = self.encoder(self.inp(x) + self.pos.unsqueeze(0), mask=self.causal_mask)
            first_state = states[:, first_commit_position]
            repair_state = states[:, repair_commit_position]
            return (
                self.final_head(states[:, -1]),
                self.opcode_head(first_state),
                self.slot_head(first_state),
                self.value_head(first_state),
                self.opcode_head(repair_state),
                self.slot_head(repair_state),
                self.value_head(repair_state),
                states,
            )

    if architecture == "gru":
        model = GRUAgent().to(device)
    elif architecture == "transformer":
        model = TransformerAgent().to(device)
    else:
        raise ValueError(architecture)

    def slot_argument_loss(slot_logits, slot_target):
        if not alias_surface:
            return F.cross_entropy(slot_logits, slot_target)
        log_probs = F.log_softmax(slot_logits, dim=-1)
        losses = torch.empty(slot_target.shape, device=slot_target.device, dtype=log_probs.dtype)
        call_mask = slot_target < n_slots
        if call_mask.any():
            alias_offsets = torch.arange(aliases_per_slot, device=slot_target.device).unsqueeze(0)
            alias_ids = slot_target[call_mask].unsqueeze(1) * aliases_per_slot + alias_offsets
            losses[call_mask] = -torch.logsumexp(log_probs[call_mask].gather(1, alias_ids), dim=1)
        if (~call_mask).any():
            non_call_targets = slot_target[~call_mask]
            losses[~call_mask] = -log_probs[~call_mask].gather(1, non_call_targets.unsqueeze(1)).squeeze(1)
        return losses.mean()

    def field_loss(op_logits, slot_logits, value_logits, targets):
        op_target, slot_target, value_target = targets
        return (
            F.cross_entropy(op_logits, op_target)
            + slot_argument_loss(slot_logits, slot_target)
            + F.cross_entropy(value_logits, value_target)
        )

    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    t0 = time.time()
    losses = []
    model.train()
    for step in range(train_steps):
        (
            x,
            final_target,
            first_targets,
            repair_targets,
            _crit_value,
            _first_failed,
            _feedback_values,
            train_first,
            train_repair,
        ) = make_batch(batch_size)
        (
            final_logits,
            first_op,
            first_slot,
            first_value,
            repair_op,
            repair_slot,
            repair_value,
            _states,
        ) = model(x)
        loss = F.cross_entropy(final_logits, final_target)
        if train_first:
            loss = loss + 0.25 * field_loss(first_op, first_slot, first_value, first_targets)
        if train_repair:
            loss = loss + 0.25 * field_loss(repair_op, repair_slot, repair_value, repair_targets)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step == 0 or (step + 1) % max(1, train_steps // 5) == 0:
            losses.append(float(loss.detach().cpu().item()))

    def parse_fields(op_pred, slot_pred, value_pred):
        slot_is_argument = slot_pred < slot_argument_size
        parsed_argument_slot = torch.div(slot_pred, max(1, aliases_per_slot), rounding_mode="floor")
        if not alias_surface:
            parsed_argument_slot = slot_pred
        executable = (op_pred == call_opcode) & slot_is_argument & (value_pred < 2)
        valid_noop = (op_pred == noop_opcode) & (slot_pred == slot_missing_id) & (value_pred == value_missing_id)
        valid = executable | valid_noop
        parsed_slot = torch.where(executable, parsed_argument_slot, torch.full_like(slot_pred, n_slots))
        parsed_value = torch.where(executable, value_pred, torch.zeros_like(value_pred))
        return valid, executable, parsed_slot, parsed_value

    def field_exact(op_pred, slot_pred, value_pred, targets):
        op_target, slot_target, value_target = targets
        if alias_surface:
            _valid, _executable, parsed_slot, _parsed_value = parse_fields(op_pred, slot_pred, value_pred)
            slot_matches = torch.where(slot_target < n_slots, parsed_slot == slot_target, slot_pred == slot_target)
        else:
            slot_matches = slot_pred == slot_target
        return (op_pred == op_target) & slot_matches & (value_pred == value_target)

    model.eval()
    teacher_forced_final_correct = 0
    closed_loop_final_correct = 0
    first_field_correct = 0
    first_schema_valid = 0
    first_slot_correct = 0
    first_value_correct = 0
    first_total = 0
    repair_field_correct = 0
    repair_schema_valid = 0
    repair_total = 0
    repair_failed_field_correct = 0
    repair_failed_schema_valid = 0
    repair_failed_slot_correct = 0
    repair_failed_value_correct = 0
    repair_failed_total = 0
    repair_success_noop_correct = 0
    repair_success_schema_valid = 0
    repair_success_total = 0
    sampled_failures = 0
    sampled_total = 0
    total = 0
    is_bottleneck = condition in bottleneck_conditions
    with torch.no_grad():
        for _ in range(eval_batches):
            (
                x,
                final_target,
                first_targets,
                repair_targets,
                crit_value,
                first_failed,
                _feedback_values,
                _train_first,
                train_repair,
            ) = make_batch(batch_size)
            (
                final_logits,
                first_op_logits,
                first_slot_logits,
                first_value_logits,
                repair_op_logits,
                repair_slot_logits,
                repair_value_logits,
                _states,
            ) = model(x)
            teacher_forced_final_correct += int((final_logits.argmax(-1) == final_target).sum().item())

            first_op = first_op_logits.argmax(-1)
            first_slot = first_slot_logits.argmax(-1)
            first_value = first_value_logits.argmax(-1)
            first_valid, first_executable, parsed_first_slot, parsed_first_value = parse_fields(
                first_op,
                first_slot,
                first_value,
            )
            first_field_correct += int(field_exact(first_op, first_slot, first_value, first_targets).sum().item())
            first_schema_valid += int(first_valid.sum().item())
            if is_bottleneck:
                first_slot_correct += int(((parsed_first_slot == critical_slot) & first_executable).sum().item())
                first_value_correct += int(((parsed_first_value == crit_value) & first_executable).sum().item())
            first_total += int(first_op.numel())

            if train_repair:
                repair_op = repair_op_logits.argmax(-1)
                repair_slot = repair_slot_logits.argmax(-1)
                repair_value = repair_value_logits.argmax(-1)
                repair_valid, repair_executable, parsed_repair_slot, parsed_repair_value = parse_fields(
                    repair_op,
                    repair_slot,
                    repair_value,
                )
                repair_field_correct += int(
                    field_exact(repair_op, repair_slot, repair_value, repair_targets).sum().item()
                )
                repair_schema_valid += int(repair_valid.sum().item())
                if is_bottleneck:
                    failed = first_failed
                    succeeded = ~first_failed
                    failed_total = int(failed.sum().item())
                    success_total = int(succeeded.sum().item())
                    repair_failed_field_correct += int(
                        field_exact(repair_op, repair_slot, repair_value, repair_targets)[failed].sum().item()
                    )
                    repair_failed_schema_valid += int(repair_valid[failed].sum().item())
                    repair_failed_slot_correct += int(
                        ((parsed_repair_slot == critical_slot) & repair_executable)[failed].sum().item()
                    )
                    repair_failed_value_correct += int(
                        ((parsed_repair_value == crit_value) & repair_executable)[failed].sum().item()
                    )
                    repair_success_noop_correct += int(
                        field_exact(repair_op, repair_slot, repair_value, repair_targets)[succeeded].sum().item()
                    )
                    repair_success_schema_valid += int(repair_valid[succeeded].sum().item())
                    repair_failed_total += failed_total
                    repair_success_total += success_total
                repair_total += int(repair_op.numel())
            sampled_failures += int(first_failed.sum().item())
            sampled_total += int(first_failed.numel())

            open_batch = make_batch(batch_size, include_teacher_return=False)
            (
                x_open,
                closed_final_target,
                _open_first_targets,
                _open_repair_targets,
                _open_crit_value,
                open_failed,
                open_feedback_values,
                _open_train_first,
                _open_train_repair,
            ) = open_batch
            (
                _open_final,
                open_first_op,
                open_first_slot,
                open_first_value,
                _open_repair_op,
                _open_repair_slot,
                _open_repair_value,
                _open_states,
            ) = model(x_open)
            x_after_first = x_open.clone()
            first_op_pred = open_first_op.argmax(-1)
            first_slot_pred = open_first_slot.argmax(-1)
            first_value_pred = open_first_value.argmax(-1)
            if is_bottleneck:
                _valid, executable, parsed_slot, parsed_value = parse_fields(
                    first_op_pred,
                    first_slot_pred,
                    first_value_pred,
                )
                slot_matches = executable & (parsed_slot == critical_slot)
                first_success = (~open_failed) & slot_matches
                x_after_first[open_failed, first_return_position, error_idx] = 1.0
                x_after_first[first_success, first_return_position, tool_return_idx] = 1.0
                x_after_first[first_success, first_return_position, tool_return_value_idx] = (
                    parsed_value[first_success].float() * 2.0 - 1.0
                )
            else:
                first_success = ~open_failed
                x_after_first[open_failed, first_return_position, error_idx] = 1.0
                x_after_first[first_success, first_return_position, tool_return_idx] = 1.0
                x_after_first[first_success, first_return_position, tool_return_value_idx] = (
                    open_feedback_values[first_success].float() * 2.0 - 1.0
                )

            (
                _after_first_final,
                _after_first_op,
                _after_first_slot,
                _after_first_value,
                repair_op_logits_open,
                repair_slot_logits_open,
                repair_value_logits_open,
                _after_first_states,
            ) = model(x_after_first)
            x_closed = x_after_first.clone()
            if is_bottleneck:
                repair_op_pred = repair_op_logits_open.argmax(-1)
                repair_slot_pred = repair_slot_logits_open.argmax(-1)
                repair_value_pred = repair_value_logits_open.argmax(-1)
                _repair_valid, repair_executable, parsed_repair_slot, parsed_repair_value = parse_fields(
                    repair_op_pred,
                    repair_slot_pred,
                    repair_value_pred,
                )
                repair_slot_matches = open_failed & repair_executable & (parsed_repair_slot == critical_slot)
                x_closed[repair_slot_matches, repair_return_position, tool_return_idx] = 1.0
                x_closed[repair_slot_matches, repair_return_position, tool_return_value_idx] = (
                    parsed_repair_value[repair_slot_matches].float() * 2.0 - 1.0
                )
            closed_logits = model(x_closed)[0]
            closed_loop_final_correct += int((closed_logits.argmax(-1) == closed_final_target).sum().item())
            total += int(final_target.numel())

    teacher_forced_final_accuracy = teacher_forced_final_correct / total if total else float("nan")
    closed_loop_final_accuracy = closed_loop_final_correct / total if total else float("nan")
    first_field_accuracy = first_field_correct / first_total if first_total else float("nan")
    first_schema_validity = first_schema_valid / first_total if first_total else float("nan")
    repair_field_accuracy = repair_field_correct / repair_total if repair_total else float("nan")
    repair_schema_validity = repair_schema_valid / repair_total if repair_total else float("nan")
    repair_failed_field_accuracy = (
        repair_failed_field_correct / repair_failed_total if repair_failed_total else float("nan")
    )
    repair_failed_schema_validity = (
        repair_failed_schema_valid / repair_failed_total if repair_failed_total else float("nan")
    )
    repair_failed_parsed_slot_accuracy = (
        repair_failed_slot_correct / repair_failed_total if repair_failed_total else float("nan")
    )
    repair_failed_parsed_value_accuracy = (
        repair_failed_value_correct / repair_failed_total if repair_failed_total else float("nan")
    )
    repair_success_noop_field_accuracy = (
        repair_success_noop_correct / repair_success_total if repair_success_total else float("nan")
    )
    repair_success_schema_validity = (
        repair_success_schema_valid / repair_success_total if repair_success_total else float("nan")
    )
    sampled_failure_rate = sampled_failures / sampled_total if sampled_total else float("nan")
    if is_bottleneck:
        first_parsed_slot_accuracy = first_slot_correct / first_total if first_total else float("nan")
        first_parsed_value_accuracy = first_value_correct / first_total if first_total else float("nan")
    else:
        first_parsed_slot_accuracy = float("nan")
        first_parsed_value_accuracy = float("nan")

    decision_position = repair_commit_position

    def density_for_slot(slot: int) -> tuple[float, float, float, float]:
        memory_vals = []
        commit_vals = []
        final_logit_vals = []
        field_vals = []
        with torch.no_grad():
            for _ in range(metric_batches):
                x0 = make_batch(batch_size)[0]
                x1 = x0.clone()
                pos = slot_positions[slot]
                x1[:, pos, bit_idx] = -x1[:, pos, bit_idx]
                if is_bottleneck and slot == critical_slot:
                    x1[:, first_return_position, tool_return_value_idx] = -x1[
                        :, first_return_position, tool_return_value_idx
                    ]
                    x1[:, repair_return_position, tool_return_value_idx] = -x1[
                        :, repair_return_position, tool_return_value_idx
                    ]
                final0, first_op0, first_slot0, first_value0, repair_op0, repair_slot0, repair_value0, states0 = model(
                    x0
                )
                final1, first_op1, first_slot1, first_value1, repair_op1, repair_slot1, repair_value1, states1 = model(
                    x1
                )
                fields0 = torch.cat([repair_op0, repair_slot0, repair_value0], dim=-1)
                fields1 = torch.cat([repair_op1, repair_slot1, repair_value1], dim=-1)
                memory_vals.append((states1[:, -1] - states0[:, -1]).norm(dim=-1).mean())
                commit_vals.append((states1[:, decision_position] - states0[:, decision_position]).norm(dim=-1).mean())
                final_logit_vals.append((final1 - final0).norm(dim=-1).mean())
                field_vals.append((fields1 - fields0).norm(dim=-1).mean())
        return (
            float(torch.stack(memory_vals).mean().cpu().item()),
            float(torch.stack(commit_vals).mean().cpu().item()),
            float(torch.stack(final_logit_vals).mean().cpu().item()),
            float(torch.stack(field_vals).mean().cpu().item()),
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
        "first_commit_position": first_commit_position,
        "first_return_position": first_return_position,
        "repair_commit_position": repair_commit_position,
        "repair_return_position": repair_return_position,
        "argument_surface": "alias" if alias_surface else "slot",
        "aliases_per_slot": aliases_per_slot,
        "opcode_vocab_size": opcode_vocab_size,
        "slot_vocab_size": slot_vocab_size,
        "value_vocab_size": value_vocab_size,
        "train_steps": train_steps,
        "batch_size": batch_size,
        "eval_batches": eval_batches,
        "metric_batches": metric_batches,
        "hidden_size": hidden_size,
        "device": str(device),
        "runtime_seconds": runtime,
        "loss_trace": losses,
        "accuracy": closed_loop_final_accuracy,
        "final_accuracy": closed_loop_final_accuracy,
        "teacher_forced_final_accuracy": teacher_forced_final_accuracy,
        "closed_loop_final_accuracy": closed_loop_final_accuracy,
        "first_field_accuracy": first_field_accuracy,
        "first_schema_validity": first_schema_validity,
        "first_parsed_slot_accuracy": first_parsed_slot_accuracy,
        "first_parsed_value_accuracy": first_parsed_value_accuracy,
        "repair_field_accuracy": repair_field_accuracy,
        "repair_schema_validity": repair_schema_validity,
        "repair_failed_field_accuracy": repair_failed_field_accuracy,
        "repair_failed_schema_validity": repair_failed_schema_validity,
        "repair_failed_parsed_slot_accuracy": repair_failed_parsed_slot_accuracy,
        "repair_failed_parsed_value_accuracy": repair_failed_parsed_value_accuracy,
        "repair_success_noop_field_accuracy": repair_success_noop_field_accuracy,
        "repair_success_schema_validity": repair_success_schema_validity,
        "sampled_failure_rate": sampled_failure_rate,
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
    train_steps: int = 900,
    batch_size: int = 256,
    eval_batches: int = 4,
    metric_batches: int = 3,
    hidden_size: int = 64,
    sequence_length: int = 128,
    n_slots: int = 4,
    slot_gap: int = 8,
    first_commit_position: int = -1,
    architectures: str = "transformer",
    conditions: str = "stochastic_failure_bottleneck,stochastic_visible_control",
    critical_slots: str = "0,1,2,3",
    base_seed: int = 20260704,
    failure_probability: float = 0.5,
    aliases_per_slot: int = 1,
    budget_usd: float = 25.0,
    dry_run_budget: bool = False,
    out: str = "artifacts/long_horizon_bottleneck/stochastic_tool_failure_l4.json",
):
    from experiments.long_horizon_bottleneck.core import (
        build_cells,
        estimate_modal_cost,
        parse_csv,
        parse_int_csv,
        summarize_stochastic_rows,
    )

    arch_list = parse_csv(architectures)
    condition_list = parse_csv(conditions)
    slot_list = parse_int_csv(critical_slots)
    alias_conditions = {"alias_stochastic_bottleneck", "alias_visible_control"}
    compact_conditions = {"stochastic_failure_bottleneck", "stochastic_visible_control"}
    uses_alias_surface = any(condition in alias_conditions for condition in condition_list)
    uses_compact_surface = any(condition in compact_conditions for condition in condition_list)
    if uses_alias_surface and uses_compact_surface:
        raise SystemExit("Do not mix alias and compact-slot stochastic conditions in one sweep")
    if aliases_per_slot <= 0:
        raise SystemExit("aliases_per_slot must be positive")
    argument_surface = "alias" if uses_alias_surface else "slot"
    argument_vocab_size = n_slots * aliases_per_slot + 2 if uses_alias_surface else n_slots + 2
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
    resolved_first_commit = sequence_length // 2 if first_commit_position < 0 else first_commit_position
    max_slot_position = max(cells[0]["slot_positions"])
    if resolved_first_commit <= max_slot_position:
        raise SystemExit("first_commit_position must occur after all clue slots")
    if resolved_first_commit + 3 >= sequence_length - 1:
        raise SystemExit("first_commit_position must leave room for error, repair, return, and final query")
    if not 0.0 <= failure_probability <= 1.0:
        raise SystemExit("failure_probability must be between 0 and 1")
    for cell in cells:
        cell["first_commit_position"] = resolved_first_commit
        cell["failure_probability"] = failure_probability
        cell["aliases_per_slot"] = aliases_per_slot

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
        "failure_probability": failure_probability,
        "n_slots": n_slots,
        "sequence_length": sequence_length,
        "slot_gap": slot_gap,
        "opcode_vocab_size": 3,
        "argument_surface": argument_surface,
        "aliases_per_slot": aliases_per_slot,
        "slot_vocab_size": argument_vocab_size,
        "value_vocab_size": 4,
        "first_commit_position": resolved_first_commit,
        "error_position": resolved_first_commit + 1,
        "repair_commit_position": resolved_first_commit + 2,
        "repair_return_position": resolved_first_commit + 3,
        "train_steps": train_steps,
        "batch_size": batch_size,
        "eval_batches": eval_batches,
        "metric_batches": metric_batches,
        "hidden_size": hidden_size,
        "budget_estimate": estimate.__dict__,
    }
    run_label = "alias-argument-surface" if uses_alias_surface else "stochastic-tool-failure"
    payload_kind = (
        "alias argument-surface stochastic moved-bottleneck sweep"
        if uses_alias_surface
        else "stochastic tool failure moved-bottleneck sweep"
    )
    print(
        f"[{run_label}] "
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
        print(json.dumps({"kind": f"{payload_kind} dry run", "manifest": manifest}, indent=2))
        return

    rows = list(run_stochastic_cell.map(cells))
    summary = summarize_stochastic_rows(rows)
    payload = {
        "kind": payload_kind,
        "manifest": manifest,
        "summary": summary,
        "rows": rows,
    }
    op = Path(out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[{run_label}] wrote {op}")

    def fmt(stat: dict[str, Any]) -> str:
        value = float(stat["mean"])
        return f"{value:.3f}" if math.isfinite(value) else "n/a"

    for key, item in summary["groups"].items():
        final_acc = fmt(item["final_accuracy"])
        teacher_forced_acc = fmt(item["teacher_forced_final_accuracy"])
        first_field = fmt(item["first_field_accuracy"])
        first_schema = fmt(item["first_schema_validity"])
        repair_field = fmt(item["repair_field_accuracy"])
        repair_schema = fmt(item["repair_schema_validity"])
        failed_repair = fmt(item["repair_failed_field_accuracy"])
        success_noop = fmt(item["repair_success_noop_field_accuracy"])
        failure_rate = fmt(item["sampled_failure_rate"])
        spec = item["memory_specificity_z"]
        tool_spec = item["tool_value_specificity_z"]
        print(
            f"  {key:42s} final={final_acc} teacher_forced={teacher_forced_acc} "
            f"first_field={first_field} first_schema={first_schema} "
            f"repair_field={repair_field} repair_schema={repair_schema} "
            f"failed_repair={failed_repair} success_noop={success_noop} "
            f"failure_rate={failure_rate} "
            f"memory_spec={spec['mean']:+.3f} tool_spec={tool_spec['mean']:+.3f} "
            f"pass={item['gate']['pass']}"
        )
    pooled_key = "pooled_alias_stochastic_bottleneck" if uses_alias_surface else "pooled_stochastic_failure_bottleneck"
    if pooled_key in summary:
        pooled = summary[pooled_key]
        print(
            f"[{run_label}] {pooled_key} "
            f"final={fmt(pooled['final_accuracy'])}; "
            f"teacher_forced={fmt(pooled['teacher_forced_final_accuracy'])}; "
            f"first_field={fmt(pooled['first_field_accuracy'])}; "
            f"first_schema={fmt(pooled['first_schema_validity'])}; "
            f"first_slot={fmt(pooled['first_parsed_slot_accuracy'])}; "
            f"first_value={fmt(pooled['first_parsed_value_accuracy'])}; "
            f"failed_repair={fmt(pooled['repair_failed_field_accuracy'])}; "
            f"failed_schema={fmt(pooled['repair_failed_schema_validity'])}; "
            f"failed_slot={fmt(pooled['repair_failed_parsed_slot_accuracy'])}; "
            f"failed_value={fmt(pooled['repair_failed_parsed_value_accuracy'])}; "
            f"success_noop={fmt(pooled['repair_success_noop_field_accuracy'])}; "
            f"failure_rate={fmt(pooled['sampled_failure_rate'])}; "
            f"memory_spec={pooled['memory_specificity_z']['mean']:+.3f}; "
            f"tool_spec={pooled['tool_value_specificity_z']['mean']:+.3f}; "
            f"pass={pooled['gate']['pass']}"
        )
