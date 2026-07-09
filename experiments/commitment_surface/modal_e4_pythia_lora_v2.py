#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""E4 -- Pythia LoRA v2 Commitment-Pinned External Contact.

Non-degenerate follow-up to
``experiments/external_contact/modal_p1_pythia_lora.py`` that adds the
four commitment-surface arms and measures patch-CE (LoRA ablation) as the
load-bearing discriminator.

Arms:
- **A** readout: standard LoRA-LM training with NO orbit augmentation;
  post-hoc weakness selector across seeds picks the "winner".
- **B** compatibility-augmented: LoRA-LM training with cyclic-group orbit
  augmentation of training pairs -- for each (x, y=(x+offset) mod n), add
  ((x+k) mod n, (y+k) mod n) for random k, so the model is trained to be
  cyclic-shift-equivariant.
- **C** wrong-group augmented: LoRA-LM training with random non-cyclic
  permutation augmentation of the input. Same augmentation *volume* as B,
  but the group is wrong.
- **D** loss selector: same as A on training; selected by lowest final
  train loss instead of weakness.

Per cell we record:
- OOD accuracy on held-out complement.
- Patch-CE Δ: CE(OOD | full model) - CE(OOD | LoRA-adapter ablated).
  Big Δ means the LoRA update is load-bearing at deployment.
- Weakness / wrong-group compatibility of the learned function table.
- Classical baselines (train loss, sharpness proxy, param L2, OOD NLL).

Prediction (commitment-first):
- Arm B mean OOD >> Arm A mean OOD.
- Arm B patch-CE Δ >> Arm A patch-CE Δ.
- Arm C patch-CE Δ ~ 0 (wrong-group aug does not cause use of the
  deployment-generating structure).

Smoke:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
            experiments/commitment_surface/modal_e4_pythia_lora_v2.py \\
            --sizes 70m --ns 13 --seeds 1 --arms A,B --epochs 80 \\
            --out artifacts/commitment_surface/e4_smoke.json

Full pre-registered grid:
    doppler --scope /Users/jawaun/superoptimizers run -- \\
        uvx --python 3.12 --from modal modal run \\
            experiments/commitment_surface/modal_e4_pythia_lora_v2.py \\
            --sizes 70m,160m,410m --ns 13,17,23 --seeds 3 \\
            --train-frac 0.5 --epochs 160 --arms A,B,C,D --base-seed 20260709 \\
            --out artifacts/commitment_surface/e4_pythia_lora_v2.json
"""

from __future__ import annotations

import gc
import importlib
import json
import math
import random
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.45,<4.57",
    "peft>=0.13,<0.18",
    "accelerate>=0.30,<1.5",
    "numpy>=1.26,<2.3",
)

app = modal.App(name="research-derived-commitment-surface-e4")
hf_cache = modal.Volume.from_name("pythia-hf-cache", create_if_missing=True)


def _seed_list(base_seed: int, seeds: int) -> list[int]:
    return [base_seed + 100 * k for k in range(seeds)]


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


def _cyclic_group(n: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple((x + shift) % n for x in range(n)) for shift in range(n))


def _wrong_group(
    n: int, *, rng: random.Random, target_size: int | None = None
) -> tuple[tuple[int, ...], ...]:
    target = target_size if target_size is not None else n
    identity = tuple(range(n))
    cyclic = set(_cyclic_group(n))
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


def _equivariance_count(
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


@app.function(
    image=IMAGE,
    gpu="L4",
    timeout=6 * 60 * 60,
    memory=24576,
    volumes={"/cache/huggingface": hf_cache},
)
def run_shard(arg: dict[str, Any]) -> dict[str, Any]:
    """Run all (arm, n, seed) cells for one Pythia size on one L4 worker."""
    import torch
    import torch.nn.functional as F
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    size: str = arg["size"]
    ns: list[int] = list(arg["ns"])
    seeds: list[int] = list(arg["seeds"])
    arms: list[str] = list(arg["arms"])
    train_frac: float = arg["train_frac"]
    epochs: int = arg["epochs"]
    lora_rank: int = arg["lora_rank"]
    lora_alpha: int = arg["lora_alpha"]
    lora_dropout: float = arg["lora_dropout"]
    lora_lr: float = arg["lora_lr"]
    weight_decay: float = arg["weight_decay"]
    grad_clip: float = arg["grad_clip"]
    aug_multiplier: int = arg["aug_multiplier"]

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
            prompt_ids = tokenizer(prompt(n, offset, x), add_special_tokens=False)[
                "input_ids"
            ]
            answer_ids = tokenizer(f" {y}{eos}", add_special_tokens=False)["input_ids"]
            rows.append(prompt_ids + answer_ids)
            labels.append([-100] * len(prompt_ids) + answer_ids)
        max_len = max(len(row) for row in rows)
        input_ids = torch.full(
            (len(rows), max_len), pad_id, dtype=torch.long, device=device
        )
        label_ids = torch.full(
            (len(rows), max_len), -100, dtype=torch.long, device=device
        )
        attention = torch.zeros((len(rows), max_len), dtype=torch.long, device=device)
        for i, (row, label) in enumerate(zip(rows, labels)):
            input_ids[i, : len(row)] = torch.tensor(
                row, dtype=torch.long, device=device
            )
            label_ids[i, : len(label)] = torch.tensor(
                label, dtype=torch.long, device=device
            )
            attention[i, : len(row)] = 1
        return {"input_ids": input_ids, "attention_mask": attention, "labels": label_ids}

    def lm_loss(model: Any, batch: dict[str, Any]) -> Any:
        return model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
            use_cache=False,
        ).loss

    def build_augmented_train(
        n: int, offset: int, train_inputs: list[int], arm: str, rng: random.Random
    ) -> tuple[list[int], list[int]]:
        """Return (xs, ys) after augmentation. For A/D, no augmentation."""
        truth = tuple((x + offset) % n for x in range(n))
        xs = list(train_inputs)
        ys = [truth[x] for x in train_inputs]
        if arm == "A" or arm == "D":
            return xs, ys
        if arm == "B":
            # Cyclic-group orbit augmentation: for each train pair (x, y),
            # add ((x+k) mod n, (y+k) mod n) for random k in [1, n).
            for _ in range(aug_multiplier):
                for x in train_inputs:
                    y = truth[x]
                    k = rng.randrange(1, n)
                    xs.append((x + k) % n)
                    ys.append((y + k) % n)
            return xs, ys
        if arm == "C":
            # Wrong-group augmentation: pick random non-cyclic permutations,
            # apply to x, and use the *implied* label to keep the pair
            # train-perfect under that permutation. Same *volume* of augmented
            # samples as arm B.
            for _ in range(aug_multiplier):
                perm = list(range(n))
                rng.shuffle(perm)
                # Ensure not cyclic.
                if all(perm[i] == (i + perm[0]) % n for i in range(n)):
                    perm[0], perm[1] = perm[1], perm[0]
                for x in train_inputs:
                    xp = perm[x]
                    # Label follows the permuted input under the true rule.
                    yp = truth[xp]
                    xs.append(xp)
                    ys.append(yp)
            return xs, ys
        raise ValueError(f"unknown arm: {arm}")

    def lm_candidate_table(
        model: Any,
        tokenizer: Any,
        n: int,
        offset: int,
    ) -> tuple[tuple[int, ...], dict[int, float], dict[int, list[float]]]:
        """Return function table, per-x truth NLL, per-x candidate NLLs."""
        table: list[int] = []
        truth_nlls: dict[int, float] = {}
        cand_nlls: dict[int, list[float]] = {}
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
                cand_nlls[x] = [float(v) for v in nll.tolist()]
        return tuple(table), truth_nlls, cand_nlls

    def lm_finite_difference_sharpness(
        model: Any, batch: dict[str, Any], params: list[Any], epsilon: float = 1e-3
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

    def train_cell(arm: str, n: int, seed: int) -> dict[str, Any]:
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
            output_hidden_states=False,
            torch_dtype=torch.float32,
        )
        hf_cache.commit()
        base.config.use_cache = False
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

        aug_rng = random.Random(seed + 991)
        xs_train, ys_train = build_augmented_train(n, offset, train_inputs, arm, aug_rng)
        train_batch = encode_lm(tokenizer, n, offset, xs_train, ys_train)

        opt = torch.optim.AdamW(adapter_params, lr=lora_lr, weight_decay=weight_decay)
        final_loss = math.inf
        for _ in range(epochs):
            model.train()
            opt.zero_grad(set_to_none=True)
            loss = lm_loss(model, train_batch)
            loss.backward()
            if grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(adapter_params, grad_clip)
            opt.step()
            final_loss = float(loss.detach().item())

        table, truth_nlls, _cand = lm_candidate_table(model, tokenizer, n, offset)
        train_acc = (
            sum(1 for x in train_inputs if table[x] == truth[x]) / len(train_inputs)
        )
        if ood_inputs:
            ood_hits = sum(1 for x in ood_inputs if table[x] == truth[x])
            ood_acc = float(ood_hits / len(ood_inputs))
            ood_nll = float(
                sum(truth_nlls[x] for x in ood_inputs) / len(ood_inputs)
            )
        else:
            ood_acc = float("nan")
            ood_nll = float("nan")

        # Patch-CE: OOD NLL with the LoRA adapter disabled minus OOD NLL with
        # the adapter active. A big positive delta means the adapter update
        # is load-bearing at the commitment surface.
        with model.disable_adapter():
            ablated_table, ablated_truth_nlls, _ = lm_candidate_table(
                model, tokenizer, n, offset
            )
        if ood_inputs:
            ablated_ood_nll = float(
                sum(ablated_truth_nlls[x] for x in ood_inputs) / len(ood_inputs)
            )
            ablated_ood_hits = sum(1 for x in ood_inputs if ablated_table[x] == truth[x])
            ablated_ood_acc = float(ablated_ood_hits / len(ood_inputs))
        else:
            ablated_ood_nll = float("nan")
            ablated_ood_acc = float("nan")
        patch_ce_delta = ablated_ood_nll - ood_nll  # positive = LoRA helps OOD

        sharp = lm_finite_difference_sharpness(model, train_batch, adapter_params)
        trainable_l2 = math.sqrt(
            sum(float((p.detach().float() ** 2).sum().item()) for p in adapter_params)
        )

        group = _cyclic_group(n)
        wrong = _wrong_group(n, rng=random.Random(seed + 17), target_size=n)
        w_oracle = _equivariance_count(table, group)
        w_wrong = _equivariance_count(table, wrong)

        cell = {
            "arm": arm,
            "size": size,
            "n": n,
            "seed": seed,
            "offset": offset,
            "train_frac": train_frac,
            "train_inputs": train_inputs,
            "ood_inputs": ood_inputs,
            "n_augmented_train_pairs": len(xs_train),
            "truth": list(truth),
            "function_table": list(table),
            "ablated_function_table": list(ablated_table),
            "epochs": epochs,
            "final_train_loss": final_loss,
            "train_accuracy": train_acc,
            "ood_accuracy": ood_acc,
            "ablated_ood_accuracy": ablated_ood_acc,
            "ood_nll": ood_nll,
            "ablated_ood_nll": ablated_ood_nll,
            "patch_ce_delta": patch_ce_delta,
            "weakness_oracle": w_oracle,
            "weakness_oracle_norm": w_oracle / max(1, len(group)),
            "weakness_wrong_group": w_wrong,
            "weakness_wrong_group_norm": w_wrong / max(1, len(wrong)),
            "pythia_l2": pythia_l2,
            "pythia_param_count": pythia_param_count,
            "trainable_lora_l2": trainable_l2,
            "head_sharpness_proxy": sharp,
            "lora_rank": lora_rank,
            "lora_targets": targets,
        }

        del model, base, adapter_params, train_batch, opt
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return cell

    cells: list[dict[str, Any]] = []
    for arm in arms:
        for n in ns:
            for seed in seeds:
                cells.append(train_cell(arm, n, seed))
    return {"size": size, "cells": cells}


def analyze_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [c for c in cells if not math.isnan(float(c["ood_accuracy"]))]
    if not valid:
        return {"n_cells": 0}
    per_arm: dict[str, dict[str, Any]] = {}
    for arm in ("A", "B", "C", "D"):
        arm_cells = [c for c in valid if c["arm"] == arm]
        if not arm_cells:
            continue
        ood = [float(c["ood_accuracy"]) for c in arm_cells]
        patch = [float(c["patch_ce_delta"]) for c in arm_cells]
        weak = [float(c["weakness_oracle_norm"]) for c in arm_cells]
        per_arm[arm] = {
            "n": len(arm_cells),
            "ood_mean": sum(ood) / len(ood),
            "ood_max": max(ood),
            "patch_ce_delta_mean": sum(patch) / len(patch),
            "weakness_mean": sum(weak) / len(weak),
        }

    b_ood = per_arm.get("B", {}).get("ood_mean", 0.0)
    a_ood = per_arm.get("A", {}).get("ood_mean", 0.0)
    b_pce = per_arm.get("B", {}).get("patch_ce_delta_mean", 0.0)
    a_pce = per_arm.get("A", {}).get("patch_ce_delta_mean", 0.0)
    c_pce = per_arm.get("C", {}).get("patch_ce_delta_mean", 0.0)

    # Cross-arm cell-level correlations on ALL cells.
    weak_all = [float(c["weakness_oracle_norm"]) for c in valid]
    patch_all = [float(c["patch_ce_delta"]) for c in valid]
    ood_all = [float(c["ood_accuracy"]) for c in valid]
    return {
        "n_cells": len(valid),
        "per_arm": per_arm,
        "gap_B_minus_A_ood": b_ood - a_ood,
        "gap_B_minus_A_patch_ce": b_pce - a_pce,
        "gap_B_minus_C_patch_ce": b_pce - c_pce,
        "rho_weakness_ood_all_cells": _spearman(weak_all, ood_all),
        "rho_patch_ce_ood_all_cells": _spearman(patch_all, ood_all),
        # Gates from PLAN.md
        "e4_new_frame_pass": (
            b_ood >= 0.5 and b_pce >= 0.05 and a_ood <= 0.10
        ),
        "e4_old_frame_pass": (
            a_ood >= 0.5 and _spearman(weak_all, ood_all) >= 0.5
        ),
    }


@app.local_entrypoint()
def main(
    sizes: str = "70m,160m,410m",
    ns: str = "13,17,23",
    seeds: int = 3,
    train_frac: float = 0.5,
    epochs: int = 160,
    arms: str = "A,B,C,D",
    lora_rank: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    lora_lr: float = 5e-4,
    weight_decay: float = 0.0,
    grad_clip: float = 1.0,
    aug_multiplier: int = 3,
    base_seed: int = 20260709,
    out: str = "artifacts/commitment_surface/e4_pythia_lora_v2.json",
) -> None:
    size_list = [item.strip() for item in sizes.split(",") if item.strip()]
    n_list = [int(item.strip()) for item in ns.split(",") if item.strip()]
    arm_list = [item.strip() for item in arms.split(",") if item.strip()]
    seed_list = _seed_list(base_seed, seeds)

    args_list = [
        {
            "size": size,
            "ns": n_list,
            "seeds": seed_list,
            "arms": arm_list,
            "train_frac": train_frac,
            "epochs": epochs,
            "lora_rank": lora_rank,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout,
            "lora_lr": lora_lr,
            "weight_decay": weight_decay,
            "grad_clip": grad_clip,
            "aug_multiplier": aug_multiplier,
        }
        for size in size_list
    ]

    all_cells: list[dict[str, Any]] = []
    for shard_result in run_shard.map(args_list):
        all_cells.extend(shard_result["cells"])

    analysis = analyze_cells(all_cells)
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": {
            "sizes": size_list,
            "ns": n_list,
            "seeds": seed_list,
            "arms": arm_list,
            "train_frac": train_frac,
            "epochs": epochs,
            "lora_rank": lora_rank,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout,
            "lora_lr": lora_lr,
            "weight_decay": weight_decay,
            "grad_clip": grad_clip,
            "aug_multiplier": aug_multiplier,
            "base_seed": base_seed,
        },
        "cells": all_cells,
        "analysis": analysis,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(analysis, indent=2))
    print(f"wrote {out_path}")
