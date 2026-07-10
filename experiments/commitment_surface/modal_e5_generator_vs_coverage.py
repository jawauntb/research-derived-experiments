#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""E5: separate generator learning from labeled orbit coverage on Pythia LoRA.

Smoke (validation only; not scientific evidence):

    doppler --scope /Users/jawaun/superoptimizers run -- \
      uvx --python 3.12 --from modal modal run \
      experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
      --sizes 70m --ns 13 --seeds 1 --arms G-reg,Cov,A-ref --epochs 20 \
      --out artifacts/commitment_surface/e5_smoke.json

The regularizer arms receive supervised labels only on the frozen original
training support. Their equivariance losses compare model distributions at two
training-support inputs and never construct held-out truth labels.
"""

from __future__ import annotations

import gc
import importlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from experiments.commitment_surface.e5_core import (
    E5Arm,
    E5Config,
    analyze_e5,
    audit_exposure,
    build_exposure_plans,
    exposure_ledger,
    make_split,
)

modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.45,<4.57",
    "peft>=0.13,<0.18",
    "accelerate>=0.30,<1.5",
).add_local_python_source("experiments.commitment_surface.e5_core")
app = modal.App(name="research-derived-commitment-surface-e5")
hf_cache = modal.Volume.from_name("pythia-hf-cache", create_if_missing=True)

PARAPHRASES = (
    "Modulo {n}, what is {x} plus {offset}? Answer:",
    "Return ({x} + {offset}) mod {n}. Result:",
)


@dataclass(frozen=True)
class E5RunConfig:
    sizes: tuple[str, ...]
    moduli: tuple[int, ...]
    seeds: tuple[int, ...]
    arms: tuple[str, ...]
    train_frac: float
    train_shift_count: int
    augmentation_multiplier: int
    epochs: int
    consistency_weight: float
    lora_rank: int
    lora_alpha: int
    lora_dropout: float
    lora_lr: float
    weight_decay: float
    grad_clip: float
    spectral_mass_fraction: float


def _seed_list(base_seed: int, count: int) -> tuple[int, ...]:
    return tuple(base_seed + 100 * index for index in range(count))


@app.function(
    image=IMAGE,
    gpu="L4",
    timeout=6 * 60 * 60,
    memory=24576,
    volumes={"/cache/huggingface": hf_cache},
)
def run_shard(arg: dict[str, Any]) -> dict[str, Any]:
    import torch
    import torch.nn.functional as F
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    size = str(arg["size"])
    run_config = E5RunConfig(
        sizes=(size,),
        moduli=tuple(int(value) for value in arg["moduli"]),
        seeds=tuple(int(value) for value in arg["seeds"]),
        arms=tuple(str(value) for value in arg["arms"]),
        train_frac=float(arg["train_frac"]),
        train_shift_count=int(arg["train_shift_count"]),
        augmentation_multiplier=int(arg["augmentation_multiplier"]),
        epochs=int(arg["epochs"]),
        consistency_weight=float(arg["consistency_weight"]),
        lora_rank=int(arg["lora_rank"]),
        lora_alpha=int(arg["lora_alpha"]),
        lora_dropout=float(arg["lora_dropout"]),
        lora_lr=float(arg["lora_lr"]),
        weight_decay=float(arg["weight_decay"]),
        grad_clip=float(arg["grad_clip"]),
        spectral_mass_fraction=float(arg["spectral_mass_fraction"]),
    )
    repo = f"EleutherAI/pythia-{size}"
    cache_dir = "/cache/huggingface"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def canonical_prompt(n: int, offset: int, x: int) -> str:
        return (
            f"Compute modular addition. Modulus: {n}. Addend: {offset}. "
            f"Input: {x}. Output:"
        )

    def prompt_text(template: str, n: int, offset: int, x: int) -> str:
        if template == "canonical":
            return canonical_prompt(n, offset, x)
        return template.format(n=n, offset=offset, x=x)

    def choose_lora_targets(model: Any) -> list[str]:
        preferred = ("query_key_value", "dense_h_to_4h", "dense_4h_to_h", "dense")
        present = {
            name.rsplit(".", 1)[-1]
            for name, module in model.named_modules()
            if hasattr(module, "weight")
        }
        targets = [name for name in preferred if name in present]
        if not targets:
            raise RuntimeError("could not infer LoRA target modules for Pythia")
        return targets

    def encode_rows(
        tokenizer: Any,
        n: int,
        offset: int,
        xs: list[int],
        ys: list[int],
        *,
        template: str = "canonical",
    ) -> dict[str, Any]:
        pad_id = int(tokenizer.pad_token_id)
        eos = tokenizer.eos_token or ""
        rows: list[list[int]] = []
        labels: list[list[int]] = []
        for x, y in zip(xs, ys):
            prompt_ids = tokenizer(
                prompt_text(template, n, offset, x),
                add_special_tokens=False,
            )["input_ids"]
            answer_ids = tokenizer(f" {y}{eos}", add_special_tokens=False)[
                "input_ids"
            ]
            rows.append(prompt_ids + answer_ids)
            labels.append([-100] * len(prompt_ids) + answer_ids)
        max_len = max(map(len, rows))
        input_ids = torch.full(
            (len(rows), max_len), pad_id, dtype=torch.long, device=device
        )
        label_ids = torch.full(
            (len(rows), max_len), -100, dtype=torch.long, device=device
        )
        attention = torch.zeros(
            (len(rows), max_len), dtype=torch.long, device=device
        )
        for index, (row, label) in enumerate(zip(rows, labels)):
            input_ids[index, : len(row)] = torch.tensor(row, device=device)
            label_ids[index, : len(label)] = torch.tensor(label, device=device)
            attention[index, : len(row)] = 1
        return {
            "input_ids": input_ids,
            "attention_mask": attention,
            "labels": label_ids,
        }

    def per_row_nll(model: Any, batch: dict[str, Any]) -> Any:
        output = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            use_cache=False,
        )
        logits = output.logits[:, :-1, :].contiguous()
        labels = batch["labels"][:, 1:].contiguous()
        mask = labels != -100
        safe_labels = labels.masked_fill(~mask, 0)
        token_loss = F.cross_entropy(
            logits.view(-1, logits.shape[-1]),
            safe_labels.view(-1),
            reduction="none",
        ).view(labels.shape)
        return (token_loss * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1)

    def supervised_loss(model: Any, batch: dict[str, Any]) -> Any:
        return per_row_nll(model, batch).mean()

    def candidate_log_probs(
        model: Any,
        tokenizer: Any,
        n: int,
        offset: int,
        xs: list[int],
        *,
        template: str = "canonical",
    ) -> Any:
        repeated_xs = [x for x in xs for _ in range(n)]
        candidates = list(range(n)) * len(xs)
        batch = encode_rows(
            tokenizer,
            n,
            offset,
            repeated_xs,
            candidates,
            template=template,
        )
        return F.log_softmax(-per_row_nll(model, batch).view(len(xs), n), dim=-1)

    def consistency_loss(
        model: Any,
        tokenizer: Any,
        n: int,
        offset: int,
        plan: Any,
    ) -> Any:
        if not plan.consistency:
            return torch.zeros((), device=device)
        source_x = [pair.source_input for pair in plan.consistency]
        target_x = [pair.target_input for pair in plan.consistency]
        source = candidate_log_probs(model, tokenizer, n, offset, source_x)
        target = candidate_log_probs(model, tokenizer, n, offset, target_x)
        desired = torch.empty_like(source)
        for row, pair in enumerate(plan.consistency):
            permutation = torch.tensor(pair.output_permutation, device=device)
            desired[row, permutation] = source[row].detach().exp()
        return F.kl_div(target, desired, reduction="batchmean")

    def evaluate(
        model: Any,
        tokenizer: Any,
        n: int,
        offset: int,
        inputs: tuple[int, ...],
        *,
        template: str,
    ) -> tuple[float, float, tuple[int, ...]]:
        with torch.no_grad():
            log_probs = candidate_log_probs(
                model, tokenizer, n, offset, list(inputs), template=template
            )
        predictions = tuple(int(value) for value in log_probs.argmax(dim=-1).tolist())
        truths = tuple((x + offset) % n for x in inputs)
        accuracy = sum(a == b for a, b in zip(predictions, truths)) / len(inputs)
        truth_tensor = torch.tensor(truths, device=device).unsqueeze(-1)
        nll = float(
            -log_probs.gather(dim=-1, index=truth_tensor).mean().detach().item()
        )
        return float(accuracy), nll, predictions

    def function_table(
        model: Any, tokenizer: Any, n: int, offset: int
    ) -> tuple[int, ...]:
        with torch.no_grad():
            log_probs = candidate_log_probs(
                model, tokenizer, n, offset, list(range(n))
            )
        return tuple(int(value) for value in log_probs.argmax(dim=-1).tolist())

    def novel_k_accuracy(
        table: tuple[int, ...], n: int, novel_shifts: tuple[int, ...]
    ) -> float:
        hits = 0
        total = 0
        for k in novel_shifts:
            for x in range(n):
                hits += table[(x + k) % n] == (table[x] + k) % n
                total += 1
        return hits / total

    def lora_modules(model: Any) -> list[tuple[str, Any, Any, float]]:
        result: list[tuple[str, Any, Any, float]] = []
        for name, module in model.named_modules():
            if not hasattr(module, "lora_A") or "default" not in module.lora_A:
                continue
            scale = float(module.scaling["default"])
            result.append(
                (
                    name,
                    module.lora_A["default"].weight,
                    module.lora_B["default"].weight,
                    scale,
                )
            )
        if not result:
            raise RuntimeError("no active LoRA matrices found for patching")
        return result

    def apply_spectral_patch(
        model: Any, target_fraction: float
    ) -> tuple[list[tuple[Any, Any, Any, Any]], list[dict[str, Any]]]:
        snapshots: list[tuple[Any, Any, Any, Any]] = []
        stats: list[dict[str, Any]] = []
        with torch.no_grad():
            for name, a_weight, b_weight, scale in lora_modules(model):
                snapshots.append(
                    (
                        a_weight,
                        b_weight,
                        a_weight.detach().clone(),
                        b_weight.detach().clone(),
                    )
                )
                delta = (b_weight.float() @ a_weight.float()) * scale
                u, singular, vh = torch.linalg.svd(delta, full_matrices=False)
                total_mass = float((singular.square()).sum().item())
                patched_singular = singular.clone()
                remaining = target_fraction * total_mass
                touched = 0
                for index in range(len(singular)):
                    component_mass = float(singular[index].square().item())
                    if remaining <= 0:
                        break
                    removed = min(remaining, component_mass)
                    patched_singular[index] = math.sqrt(
                        max(0.0, component_mass - removed)
                    )
                    remaining -= removed
                    touched += 1
                patched = (u * patched_singular.unsqueeze(0)) @ vh
                rank = a_weight.shape[0]
                pu, ps, pvh = torch.linalg.svd(patched, full_matrices=False)
                kept = min(rank, len(ps))
                new_a = torch.zeros_like(a_weight, dtype=torch.float32)
                new_b = torch.zeros_like(b_weight, dtype=torch.float32)
                new_a[:kept] = pvh[:kept]
                new_b[:, :kept] = (pu[:, :kept] * ps[:kept]) / scale
                a_weight.copy_(new_a.to(a_weight.dtype))
                b_weight.copy_(new_b.to(b_weight.dtype))
                realized_delta = (b_weight.float() @ a_weight.float()) * scale
                realized_mass = float(realized_delta.square().sum().item())
                realized_fraction = (
                    1.0 - realized_mass / total_mass if total_mass > 0 else 0.0
                )
                stats.append(
                    {
                        "module": name,
                        "effective_rank": int((singular > 1e-8).sum().item()),
                        "patched_components": touched,
                        "total_spectral_mass": total_mass,
                        "removed_spectral_mass_fraction": realized_fraction,
                    }
                )
        return snapshots, stats

    def restore_patch(snapshots: list[tuple[Any, Any, Any, Any]]) -> None:
        with torch.no_grad():
            for a_weight, b_weight, old_a, old_b in snapshots:
                a_weight.copy_(old_a)
                b_weight.copy_(old_b)

    def train_cell(arm_text: str, n: int, seed: int) -> dict[str, Any]:
        arm = E5Arm(arm_text)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        design = E5Config(
            modulus=n,
            train_frac=run_config.train_frac,
            train_shift_count=run_config.train_shift_count,
            augmentation_multiplier=run_config.augmentation_multiplier,
            spectral_mass_fraction=run_config.spectral_mass_fraction,
            seed=seed,
        )
        split = make_split(design)
        offset = random_offset = random_seeded_offset(seed, n)
        plans = build_exposure_plans(split, design, offset)
        plan = plans[arm]
        audit = audit_exposure(plan, split)

        tokenizer = AutoTokenizer.from_pretrained(repo, cache_dir=cache_dir)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        base = AutoModelForCausalLM.from_pretrained(
            repo,
            cache_dir=cache_dir,
            dtype=torch.float32,
        )
        hf_cache.commit()
        base.config.use_cache = False
        targets = choose_lora_targets(base)
        model = get_peft_model(
            base,
            LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                r=run_config.lora_rank,
                lora_alpha=run_config.lora_alpha,
                lora_dropout=run_config.lora_dropout,
                target_modules=targets,
                bias="none",
            ),
        ).to(device)
        trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
        supervised_batch = encode_rows(
            tokenizer,
            n,
            offset,
            [row.input_id for row in plan.supervised],
            [row.label for row in plan.supervised],
        )
        optimizer = torch.optim.AdamW(
            trainable,
            lr=run_config.lora_lr,
            weight_decay=run_config.weight_decay,
        )
        final_supervised_loss = float("nan")
        final_consistency_loss = 0.0
        for _ in range(run_config.epochs):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            sup_loss = supervised_loss(model, supervised_batch)
            reg_loss = consistency_loss(model, tokenizer, n, offset, plan)
            loss = sup_loss + run_config.consistency_weight * reg_loss
            loss.backward()
            if run_config.grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(trainable, run_config.grad_clip)
            optimizer.step()
            final_supervised_loss = float(sup_loss.detach().item())
            final_consistency_loss = float(reg_loss.detach().item())

        model.eval()
        canonical_acc, canonical_nll, _ = evaluate(
            model,
            tokenizer,
            n,
            offset,
            split.ood_inputs,
            template="canonical",
        )
        paraphrase_results = [
            evaluate(
                model,
                tokenizer,
                n,
                offset,
                split.ood_inputs,
                template=template,
            )
            for template in PARAPHRASES
        ]
        paraphrase_acc = sum(item[0] for item in paraphrase_results) / len(
            paraphrase_results
        )
        paraphrase_nll = sum(item[1] for item in paraphrase_results) / len(
            paraphrase_results
        )
        table = function_table(model, tokenizer, n, offset)
        novel_accuracy = novel_k_accuracy(table, n, split.k_novel)

        snapshots, patch_stats = apply_spectral_patch(
            model, run_config.spectral_mass_fraction
        )
        _, patched_canonical_nll, _ = evaluate(
            model,
            tokenizer,
            n,
            offset,
            split.ood_inputs,
            template="canonical",
        )
        patched_paraphrase = [
            evaluate(
                model,
                tokenizer,
                n,
                offset,
                split.ood_inputs,
                template=template,
            )[1]
            for template in PARAPHRASES
        ]
        patched_paraphrase_nll = sum(patched_paraphrase) / len(patched_paraphrase)
        restore_patch(snapshots)

        with model.disable_adapter():
            _, disabled_nll, _ = evaluate(
                model,
                tokenizer,
                n,
                offset,
                split.ood_inputs,
                template="canonical",
            )

        nonzero_patch_stats = [
            stat for stat in patch_stats if stat["total_spectral_mass"] > 1e-12
        ]
        patch_integrity = bool(nonzero_patch_stats) and all(
            abs(
                float(stat["removed_spectral_mass_fraction"])
                - run_config.spectral_mass_fraction
            )
            <= 0.02
            for stat in nonzero_patch_stats
        )
        exposure_integrity = (
            audit.consistency_outside_train == 0
            and not (
                arm in (E5Arm.G_REG, E5Arm.W_REG)
                and audit.supervised_heldout_events
            )
            and not set(audit.used_intervention_ids) & set(split.k_novel)
        )
        cell = {
            "arm": arm.value,
            "size": size,
            "n": n,
            "seed": seed,
            "offset": offset,
            "split": asdict(split),
            "exposure_audit": asdict(audit),
            "exposure_plan": {
                "supervised": [asdict(row) for row in plan.supervised],
                "consistency": [asdict(row) for row in plan.consistency],
            },
            "all_arm_exposure_ledger": exposure_ledger(plans, split),
            "final_supervised_loss": final_supervised_loss,
            "final_consistency_loss": final_consistency_loss,
            "canonical_ood_accuracy": canonical_acc,
            "canonical_ood_nll": canonical_nll,
            "paraphrase_ood_accuracy": paraphrase_acc,
            "paraphrase_ood_nll": paraphrase_nll,
            "paraphrase_templates": list(PARAPHRASES),
            "novel_k_equivariance_accuracy": novel_accuracy,
            "canonical_normalized_patch_ce": patched_canonical_nll - canonical_nll,
            "paraphrase_normalized_patch_ce": (
                patched_paraphrase_nll - paraphrase_nll
            ),
            "full_adapter_disable_ce": disabled_nll - canonical_nll,
            "spectral_patch": {
                "target_removed_mass_fraction": run_config.spectral_mass_fraction,
                "modules": patch_stats,
            },
            "lora_rank": run_config.lora_rank,
            "lora_targets": targets,
            "exposure_integrity_pass": exposure_integrity,
            "patch_integrity_pass": patch_integrity,
            "integrity_pass": exposure_integrity and patch_integrity,
        }
        del model, base, trainable, supervised_batch, optimizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return cell

    def random_seeded_offset(seed: int, n: int) -> int:
        # Local deterministic arithmetic avoids sharing any global RNG state
        # between arms while keeping their task and split exactly matched.
        return 1 + ((seed * 1103515245 + 12345) % (n - 1))

    cells: list[dict[str, Any]] = []
    for n in run_config.moduli:
        for seed in run_config.seeds:
            for arm in run_config.arms:
                cells.append(train_cell(arm, n, seed))
    return {"size": size, "cells": cells}


@app.local_entrypoint()
def main(
    sizes: str = "70m,160m,410m",
    ns: str = "13,17,23",
    seeds: int = 3,
    arms: str = "G-reg,B-ref,W-reg,Cov,A-ref",
    train_frac: float = 0.5,
    train_shift_count: int = 3,
    augmentation_multiplier: int = 3,
    epochs: int = 160,
    consistency_weight: float = 1.0,
    lora_rank: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    lora_lr: float = 5e-4,
    weight_decay: float = 0.0,
    grad_clip: float = 1.0,
    spectral_mass_fraction: float = 0.5,
    base_seed: int = 20260709,
    out: str = "artifacts/commitment_surface/e5_generator_vs_coverage.json",
) -> None:
    config = E5RunConfig(
        sizes=tuple(item.strip() for item in sizes.split(",") if item.strip()),
        moduli=tuple(int(item.strip()) for item in ns.split(",") if item.strip()),
        seeds=_seed_list(base_seed, seeds),
        arms=tuple(E5Arm(item.strip()).value for item in arms.split(",") if item.strip()),
        train_frac=train_frac,
        train_shift_count=train_shift_count,
        augmentation_multiplier=augmentation_multiplier,
        epochs=epochs,
        consistency_weight=consistency_weight,
        lora_rank=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        lora_lr=lora_lr,
        weight_decay=weight_decay,
        grad_clip=grad_clip,
        spectral_mass_fraction=spectral_mass_fraction,
    )
    args = [
        {
            **asdict(config),
            "size": size,
        }
        for size in config.sizes
    ]
    cells: list[dict[str, Any]] = []
    for result in run_shard.map(args):
        cells.extend(result["cells"])
    payload = {
        "experiment": "E5 generator learning vs labeled orbit coverage",
        "status": "post-hoc preregistered follow-up",
        "config": asdict(config),
        "cells": cells,
        "analysis": analyze_e5(cells),
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["analysis"], indent=2))
    print(f"wrote {out_path}")
