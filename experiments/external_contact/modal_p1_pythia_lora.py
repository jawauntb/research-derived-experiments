#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""External Contact P1 -- LoRA Tier-B weakness -> OOD on Pythia.

This is the non-degenerate follow-up to
`experiments/external_contact/modal_p1_pythia_weakness.py`. The earlier run
froze Pythia and trained only a linear head; every cell had OOD accuracy 0.0.
Here the Pythia representation itself can adapt through LoRA adapters. The
default objective trains the causal LM to emit the answer token and extracts
the function table by answer-candidate NLL; an optional classifier-head
objective is kept only for diagnostics.

Run a smoke cell first:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
            experiments/external_contact/modal_p1_pythia_lora.py \
            --sizes 70m --ns 13 --seeds 1 --epochs 80 --objective lm \
            --out artifacts/external_contact/p1_pythia_lora_smoke.json

Then run the pre-registered Tier-B grid:

    doppler --scope /Users/jawaun/superoptimizers run -- \
        uvx --python 3.12 --from modal modal run \
            experiments/external_contact/modal_p1_pythia_lora.py \
            --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 \
            --epochs 160 --objective lm --base-seed 20260618 \
            --out artifacts/external_contact/p1_pythia_lora.json
"""

from __future__ import annotations

import gc
import importlib
import json
import math
import random
from pathlib import Path
from typing import Any

try:
    from experiments.external_contact.p1_lora_metrics import (
        analyze_cells,
        cyclic_group,
        equivariance_count,
        wrong_group,
    )
except ModuleNotFoundError:
    # Modal mounts this file as a standalone module. Keep the worker
    # self-contained there while local tests exercise the shared module.
    def _spearman(xs: list[float], ys: list[float]) -> float:
        if len(xs) != len(ys) or len(xs) < 2:
            return 0.0

        def rank(vals: list[float]) -> list[float]:
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

    def cyclic_group(n: int) -> tuple[tuple[int, ...], ...]:
        return tuple(tuple((x + shift) % n for x in range(n)) for shift in range(n))

    def wrong_group(
        n: int,
        *,
        rng: random.Random,
        target_size: int | None = None,
    ) -> tuple[tuple[int, ...], ...]:
        target = target_size if target_size is not None else n
        identity = tuple(range(n))
        cyclic = set(cyclic_group(n))
        out: list[tuple[int, ...]] = [identity]
        attempts = 0
        while len(out) < target and attempts < 5000:
            perm = list(range(n))
            rng.shuffle(perm)
            candidate = tuple(perm)
            if candidate not in cyclic and candidate not in out:
                out.append(candidate)
            attempts += 1
        return tuple(out)

    def equivariance_count(
        table: tuple[int, ...],
        group: tuple[tuple[int, ...], ...],
    ) -> int:
        n = len(table)
        count = 0
        for g in group:
            induced = tuple(table[g[x]] for x in range(n))
            for h in group:
                if all(h[table[x]] == induced[x] for x in range(n)):
                    count += 1
                    break
        return count

    def analyze_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
        valid = [cell for cell in cells if not math.isnan(float(cell["ood_accuracy"]))]
        if not valid:
            return {"n_cells": 0, "P1_pass": None, "P1_hard_kill": None}
        ood = [float(cell["ood_accuracy"]) for cell in valid]
        analysis: dict[str, Any] = {
            "n_cells": len(valid),
            "ood_unique_values": len(set(ood)),
            "P1_degenerate_ood_column": len(set(ood)) < 2,
            "rho_weakness_vs_ood": _spearman(
                [float(cell["weakness_oracle_norm"]) for cell in valid], ood
            ),
            "rho_wrong_group_vs_ood": _spearman(
                [float(cell["weakness_wrong_group_norm"]) for cell in valid], ood
            ),
            "rho_loss_vs_ood": _spearman(
                [float(cell["final_train_loss"]) for cell in valid], ood
            ),
            "rho_ood_nll_vs_ood": _spearman([float(cell["ood_nll"]) for cell in valid], ood),
            "rho_param_count_vs_ood": _spearman(
                [float(cell["pythia_param_count"]) for cell in valid], ood
            ),
            "rho_l2_vs_ood": _spearman([float(cell["pythia_l2"]) for cell in valid], ood),
            "rho_sharpness_vs_ood": _spearman(
                [float(cell["head_sharpness_proxy"]) for cell in valid], ood
            ),
        }
        rho_w = float(analysis["rho_weakness_vs_ood"])
        rivals = [
            abs(float(analysis[key]))
            for key in (
                "rho_loss_vs_ood",
                "rho_ood_nll_vs_ood",
                "rho_param_count_vs_ood",
                "rho_l2_vs_ood",
                "rho_sharpness_vs_ood",
            )
        ]
        best_rival = max(rivals) if rivals else 0.0
        analysis["best_classical_abs_rho"] = best_rival
        analysis["weakness_beats_best_classical_by_margin"] = abs(rho_w) - best_rival
        analysis["P1_pass"] = (
            rho_w >= 0.5
            and (abs(rho_w) - best_rival) >= 0.25
            and abs(float(analysis["rho_wrong_group_vs_ood"])) <= 0.15
        )
        analysis["P1_hard_kill"] = rho_w < 0.3 or any(
            abs(rho_w) - rival <= 0.10 for rival in rivals
        )
        analysis["P1_soft_kill_wrong_group"] = abs(
            float(analysis["rho_wrong_group_vs_ood"])
        ) > 0.25
        return analysis


modal = importlib.import_module("modal")

IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.45,<4.57",
    "peft>=0.13,<0.18",
    "accelerate>=0.30,<1.5",
    "numpy>=1.26,<2.3",
)

app = modal.App(name="research-derived-external-contact-p1-lora")
hf_cache = modal.Volume.from_name("pythia-hf-cache", create_if_missing=True)


def _seed_list(base_seed: int, seeds: int) -> list[int]:
    return [base_seed + 100 * k for k in range(seeds)]


@app.function(
    image=IMAGE,
    gpu="A10G",
    timeout=4 * 60 * 60,
    memory=24576,
    volumes={"/cache/huggingface": hf_cache},
)
def run_size_shard(arg: dict[str, Any]) -> dict[str, Any]:
    """Run all (n, seed) LoRA cells for one Pythia size on one Modal worker."""
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    size: str = arg["size"]
    ns: list[int] = list(arg["ns"])
    seeds: list[int] = list(arg["seeds"])
    train_frac: float = arg["train_frac"]
    epochs: int = arg["epochs"]
    lora_rank: int = arg["lora_rank"]
    lora_alpha: int = arg["lora_alpha"]
    lora_dropout: float = arg["lora_dropout"]
    lora_lr: float = arg["lora_lr"]
    head_lr: float = arg["head_lr"]
    weight_decay: float = arg["weight_decay"]
    grad_clip: float = arg["grad_clip"]
    objective: str = arg["objective"]

    repo = f"EleutherAI/pythia-{size}"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cache_dir = "/cache/huggingface"

    def prompt(n: int, offset: int, x: int) -> str:
        return f"Compute modular addition. Modulus: {n}. Addend: {offset}. Input: {x}. Output:"

    def choose_lora_targets(model: Any) -> list[str]:
        preferred = ("query_key_value", "dense_h_to_4h", "dense_4h_to_h", "dense")
        present: set[str] = set()
        for name, module in model.named_modules():
            leaf = name.rsplit(".", 1)[-1]
            if leaf in preferred and hasattr(module, "weight"):
                present.add(leaf)
        targets = [leaf for leaf in preferred if leaf in present]
        if not targets:
            raise RuntimeError("could not infer LoRA target modules for Pythia")
        return targets

    def encode(tokenizer: Any, n: int, offset: int, xs: list[int]) -> dict[str, Any]:
        texts = [prompt(n, offset, x) for x in xs]
        batch = tokenizer(texts, return_tensors="pt", padding=True)
        return {key: value.to(device) for key, value in batch.items()}

    def final_hidden(model: Any, batch: dict[str, Any]) -> Any:
        out = model(**batch, output_hidden_states=True, use_cache=False)
        hidden = out.hidden_states[-1]
        last_index = batch["attention_mask"].sum(dim=1) - 1
        rows = torch.arange(hidden.shape[0], device=hidden.device)
        return hidden[rows, last_index].float()

    def head_sharpness(head: nn.Linear, features: Any, targets: Any) -> float:
        head.zero_grad(set_to_none=True)
        logits = head(features)
        loss = F.cross_entropy(logits, targets)
        params = [p for p in head.parameters() if p.requires_grad]
        vectors = [
            torch.randint(0, 2, p.shape, device=p.device).float() * 2 - 1
            for p in params
        ]
        grads = torch.autograd.grad(loss, params, create_graph=True)
        g_dot_v = sum((grad * vector).sum() for grad, vector in zip(grads, vectors))
        hv = torch.autograd.grad(g_dot_v, params, retain_graph=False)
        return float(sum((h * vector).sum().item() for h, vector in zip(hv, vectors)))

    def encode_lm(
        tokenizer: Any,
        n: int,
        offset: int,
        xs: list[int],
        ys: list[int],
    ) -> dict[str, Any]:
        pad_id = int(tokenizer.pad_token_id)
        eos = tokenizer.eos_token or ""
        rows: list[list[int]] = []
        labels: list[list[int]] = []
        for x, y in zip(xs, ys):
            prompt_ids = tokenizer(prompt(n, offset, x), add_special_tokens=False)["input_ids"]
            answer_ids = tokenizer(f" {y}{eos}", add_special_tokens=False)["input_ids"]
            rows.append(prompt_ids + answer_ids)
            labels.append([-100] * len(prompt_ids) + answer_ids)
        max_len = max(len(row) for row in rows)
        input_ids = torch.full((len(rows), max_len), pad_id, dtype=torch.long, device=device)
        label_ids = torch.full((len(rows), max_len), -100, dtype=torch.long, device=device)
        attention = torch.zeros((len(rows), max_len), dtype=torch.long, device=device)
        for i, (row, label) in enumerate(zip(rows, labels)):
            input_ids[i, : len(row)] = torch.tensor(row, dtype=torch.long, device=device)
            label_ids[i, : len(label)] = torch.tensor(label, dtype=torch.long, device=device)
            attention[i, : len(row)] = 1
        return {"input_ids": input_ids, "attention_mask": attention, "labels": label_ids}

    def lm_loss(model: Any, batch: dict[str, Any]) -> Any:
        return model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
            use_cache=False,
        ).loss

    def lm_candidate_table(
        model: Any,
        tokenizer: Any,
        n: int,
        offset: int,
    ) -> tuple[tuple[int, ...], dict[int, float]]:
        table: list[int] = []
        truth_nlls: dict[int, float] = {}
        model.eval()
        for x in range(n):
            candidates = list(range(n))
            batch = encode_lm(tokenizer, n, offset, [x] * n, candidates)
            with torch.no_grad():
                out = model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    use_cache=False,
                )
                logits = out.logits[:, :-1, :].contiguous()
                labels = batch["labels"][:, 1:].contiguous()
                mask = labels != -100
                safe_labels = labels.masked_fill(~mask, 0)
                token_loss = F.cross_entropy(
                    logits.view(-1, logits.shape[-1]),
                    safe_labels.view(-1),
                    reduction="none",
                ).view(labels.shape)
                denom = mask.sum(dim=1).clamp_min(1)
                nll = (token_loss * mask).sum(dim=1) / denom
                table.append(int(torch.argmin(nll).item()))
                truth_nlls[x] = float(nll[(x + offset) % n].item())
        return tuple(table), truth_nlls

    def lm_finite_difference_sharpness(
        model: Any,
        batch: dict[str, Any],
        params: list[Any],
        epsilon: float = 1e-3,
    ) -> float:
        model.eval()
        with torch.no_grad():
            base_loss = float(lm_loss(model, batch).item())
        vectors = [
            torch.randint(0, 2, p.shape, device=p.device).float() * 2 - 1
            for p in params
        ]
        with torch.no_grad():
            for p, vector in zip(params, vectors):
                p.add_(epsilon * vector)
            plus = float(lm_loss(model, batch).item())
            for p, vector in zip(params, vectors):
                p.add_(-2 * epsilon * vector)
            minus = float(lm_loss(model, batch).item())
            for p, vector in zip(params, vectors):
                p.add_(epsilon * vector)
        return float((plus + minus - 2 * base_loss) / (epsilon * epsilon))

    def train_cell(n: int, seed: int) -> dict[str, Any]:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        rng = random.Random(seed)
        offset = rng.randrange(1, n)
        truth = tuple((x + offset) % n for x in range(n))
        train_size = min(n - 1, max(1, int(round(n * train_frac))))
        train_inputs = sorted(rng.sample(range(n), train_size))
        ood_inputs = [x for x in range(n) if x not in train_inputs]

        tokenizer = AutoTokenizer.from_pretrained(repo, cache_dir=cache_dir)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        base = AutoModelForCausalLM.from_pretrained(
            repo,
            cache_dir=cache_dir,
            output_hidden_states=True,
            torch_dtype=torch.float32,
        )
        hf_cache.commit()
        base.config.use_cache = False
        hidden_dim = int(getattr(base.config, "hidden_size"))
        pythia_param_count = int(sum(int(p.numel()) for p in base.parameters()))
        pythia_l2 = math.sqrt(
            sum(float((p.detach().float() ** 2).sum().item()) for p in base.parameters())
        )

        targets = choose_lora_targets(base)
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=lora_rank,
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            target_modules=targets,
            bias="none",
        )
        model = get_peft_model(base, lora_config).to(device)
        adapter_params = [p for p in model.parameters() if p.requires_grad]
        cleanup: list[Any] = []

        if objective == "classifier":
            head = nn.Linear(hidden_dim, n).to(device)
            train_batch = encode(tokenizer, n, offset, train_inputs)
            full_batch = encode(tokenizer, n, offset, list(range(n)))
            y_train = torch.tensor(
                [truth[x] for x in train_inputs], dtype=torch.long, device=device
            )

            opt = torch.optim.AdamW(
                [
                    {"params": adapter_params, "lr": lora_lr},
                    {"params": list(head.parameters()), "lr": head_lr},
                ],
                weight_decay=weight_decay,
            )

            final_loss = math.inf
            for _ in range(epochs):
                model.train()
                head.train()
                opt.zero_grad(set_to_none=True)
                logits = head(final_hidden(model, train_batch))
                loss = F.cross_entropy(logits, y_train)
                loss.backward()
                if grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(
                        adapter_params + list(head.parameters()), grad_clip
                    )
                opt.step()
                final_loss = float(loss.detach().item())

            model.eval()
            head.eval()
            with torch.no_grad():
                train_features = final_hidden(model, train_batch).detach()
                full_features = final_hidden(model, full_batch).detach()
                full_logits = head(full_features)
                table = tuple(int(x) for x in full_logits.argmax(dim=-1).cpu().tolist())
                train_preds = head(train_features).argmax(dim=-1)
                train_acc = float((train_preds == y_train).float().mean().item())

                if ood_inputs:
                    ood_index = torch.tensor(ood_inputs, dtype=torch.long, device=device)
                    ood_logits = full_logits.index_select(0, ood_index)
                    y_ood = torch.tensor(
                        [truth[x] for x in ood_inputs], dtype=torch.long, device=device
                    )
                    ood_acc = float((ood_logits.argmax(dim=-1) == y_ood).float().mean().item())
                    ood_nll = float(F.cross_entropy(ood_logits, y_ood).item())
                else:
                    ood_acc = float("nan")
                    ood_nll = float("nan")

            sharp = head_sharpness(head, train_features.detach(), y_train)
            trainable_params_for_l2 = adapter_params + list(head.parameters())
            sharpness_scope = "classifier_head_only"
            cleanup.extend([head, opt, train_batch, full_batch])

        elif objective == "lm":
            train_batch_lm = encode_lm(
                tokenizer,
                n,
                offset,
                train_inputs,
                [truth[x] for x in train_inputs],
            )
            opt = torch.optim.AdamW(adapter_params, lr=lora_lr, weight_decay=weight_decay)

            final_loss = math.inf
            for _ in range(epochs):
                model.train()
                opt.zero_grad(set_to_none=True)
                loss = lm_loss(model, train_batch_lm)
                loss.backward()
                if grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(adapter_params, grad_clip)
                opt.step()
                final_loss = float(loss.detach().item())

            table, truth_nlls = lm_candidate_table(model, tokenizer, n, offset)
            train_acc = sum(1 for x in train_inputs if table[x] == truth[x]) / len(train_inputs)
            if ood_inputs:
                ood_hits = sum(1 for x in ood_inputs if table[x] == truth[x])
                ood_acc = float(ood_hits / len(ood_inputs))
                ood_nll = float(sum(truth_nlls[x] for x in ood_inputs) / len(ood_inputs))
            else:
                ood_acc = float("nan")
                ood_nll = float("nan")

            sharp = lm_finite_difference_sharpness(model, train_batch_lm, adapter_params)
            trainable_params_for_l2 = adapter_params
            sharpness_scope = "lora_adapter_lm_loss_finite_difference"
            cleanup.extend([opt, train_batch_lm])

        else:
            raise ValueError(f"unknown objective: {objective}")

        group = cyclic_group(n)
        wrong = wrong_group(n, rng=random.Random(seed + 17), target_size=n)
        w_oracle = equivariance_count(table, group)
        w_wrong = equivariance_count(table, wrong)
        trainable_l2 = math.sqrt(
            sum(
                float((p.detach().float() ** 2).sum().item())
                for p in trainable_params_for_l2
            )
        )

        cell = {
            "size": size,
            "n": n,
            "seed": seed,
            "offset": offset,
            "train_frac": train_frac,
            "train_inputs": train_inputs,
            "ood_inputs": ood_inputs,
            "truth": list(truth),
            "function_table": list(table),
            "objective": objective,
            "lora_rank": lora_rank,
            "lora_targets": targets,
            "epochs": epochs,
            "final_train_loss": final_loss,
            "head_train_accuracy": train_acc,
            "train_accuracy": train_acc,
            "ood_accuracy": ood_acc,
            "ood_nll": ood_nll,
            "weakness_oracle": w_oracle,
            "weakness_oracle_norm": w_oracle / max(1, len(group)),
            "weakness_wrong_group": w_wrong,
            "weakness_wrong_group_norm": w_wrong / max(1, len(wrong)),
            "pythia_l2": pythia_l2,
            "pythia_param_count": pythia_param_count,
            "trainable_lora_head_l2": trainable_l2,
            "head_sharpness_proxy": sharp,
            "sharpness_scope": sharpness_scope,
        }

        del model, base
        del cleanup
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return cell

    cells = [train_cell(n, seed) for n in ns for seed in seeds]
    return {"size": size, "cells": cells}


@app.local_entrypoint()
def main(
    sizes: str = "70m,160m,410m",
    ns: str = "13,17,23",
    seeds: int = 3,
    train_frac: float = 0.5,
    epochs: int = 160,
    lora_rank: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    lora_lr: float = 5e-4,
    head_lr: float = 5e-3,
    weight_decay: float = 0.0,
    grad_clip: float = 1.0,
    objective: str = "lm",
    base_seed: int = 20260618,
    out: str = "artifacts/external_contact/p1_pythia_lora.json",
) -> None:
    size_list = [item.strip() for item in sizes.split(",") if item.strip()]
    n_list = [int(item.strip()) for item in ns.split(",") if item.strip()]
    seed_values = _seed_list(base_seed, seeds)

    shard_args = [
        {
            "size": size,
            "ns": n_list,
            "seeds": seed_values,
            "train_frac": train_frac,
            "epochs": epochs,
            "lora_rank": lora_rank,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout,
            "lora_lr": lora_lr,
            "head_lr": head_lr,
            "weight_decay": weight_decay,
            "grad_clip": grad_clip,
            "objective": objective,
        }
        for size in size_list
    ]

    print(
        "[P1-LoRA] dispatching "
        f"{len(shard_args)} size shards: sizes={size_list}, ns={n_list}, "
        f"seeds={seed_values}, train_frac={train_frac}, epochs={epochs}, "
        f"rank={lora_rank}, objective={objective}"
    )
    results = list(run_size_shard.map(shard_args))
    cells = [cell for result in results for cell in result["cells"]]
    analysis = analyze_cells(cells)

    payload = {
        "kind": "REAL P1 Tier-B external LoRA run on Modal",
        "manifest": {
            "sizes": size_list,
            "ns": n_list,
            "seeds": seed_values,
            "train_frac": train_frac,
            "epochs": epochs,
            "lora_rank": lora_rank,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout,
            "lora_lr": lora_lr,
            "head_lr": head_lr,
            "weight_decay": weight_decay,
            "grad_clip": grad_clip,
            "objective": objective,
            "sharpness_scope": (
                "lora_adapter_lm_loss_finite_difference"
                if objective == "lm"
                else "classifier_head_only"
            ),
        },
        "analysis": analysis,
        "cells": cells,
    }
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"[P1-LoRA] wrote {out_path}")
    print(
        "[P1-LoRA] analysis: "
        f"rho(weakness, OOD)={analysis.get('rho_weakness_vs_ood')}; "
        f"best classical |rho|={analysis.get('best_classical_abs_rho')}; "
        f"P1_pass={analysis.get('P1_pass')}; hard_kill={analysis.get('P1_hard_kill')}"
    )
