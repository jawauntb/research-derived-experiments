#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""E5: separate generator learning from labeled orbit coverage on Pythia LoRA.

Smoke (validation only; not scientific evidence):

    doppler --scope /Users/jawaun/superoptimizers run -- \
      uvx --python 3.12 --from modal==1.2.6 modal run \
      experiments/commitment_surface/modal_e5_generator_vs_coverage.py \
      --sizes 70m --ns 13 --seeds 1 --arms G-reg,Cov,A-ref --epochs 20 \
      --run-kind smoke --execute --max-gpu-cells 3 \
      --out artifacts/commitment_surface/e5_smoke.json

The regularizer arms receive supervised labels only on the frozen original
training support. Their equivariance losses compare model distributions at two
training-support inputs and never construct held-out truth labels.

Exactly one operational action is required: ``--dry-run`` validates the
manifest and CPU control path, ``--inspect`` reports checkpoint status, and
``--execute`` authorizes bounded GPU dispatch. Operational action flags are not
part of the frozen scientific manifest.
"""

from __future__ import annotations

import gc
import hashlib
import importlib
import json
import math
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from experiments.commitment_surface.e5_core import (
    E5Arm,
    E5Config,
    E5RunKind,
    analyze_e5,
    audit_exposure,
    build_run_manifest,
    build_exposure_plans,
    cell_is_reusable,
    exposure_ledger,
    grid_spec_for_run_kind,
    lease_record_is_active,
    make_split,
    prioritize_launch_cells,
)

modal = importlib.import_module("modal")

RUNTIME_LOCK_PATH = Path(__file__).with_name("e5_requirements.txt")
DEPENDENCY_VERSIONS = dict(
    line.split("==", maxsplit=1)
    for line in RUNTIME_LOCK_PATH.read_text(encoding="utf-8").splitlines()
    if line
)
MODAL_CLIENT_VERSION = "1.2.6"
MODEL_REVISIONS = {
    "70m": "a39f36b100fe8a5377810d56c3f4789b9c53ac42",
    "160m": "50f5173d932e8e61f858120bcb800b97af589f46",
    "410m": "9879c9b5f8bea9051dcb0e68dff21493d67e9d4f",
}
RESULT_VOLUME_NAME = "commitment-surface-e5-results-v2"
RESULT_VOLUME_VERSION = 2
CELL_LEASE_DICT_NAME = "commitment-surface-e5-cell-leases"
GPU_TYPE = "L4"
GPU_MEMORY_MIB = 24576
GPU_TIMEOUT_SECONDS = 6 * 60 * 60
GPU_MAX_CONTAINERS = 12
CELL_LEASE_TTL_SECONDS = GPU_TIMEOUT_SECONDS + 15 * 60
EXECUTION_ENVIRONMENT = {
    "python": "3.12",
    "modal_client": MODAL_CLIENT_VERSION,
    "dependencies": DEPENDENCY_VERSIONS,
    "model_revisions": MODEL_REVISIONS,
    "deployment": {
        "gpu": GPU_TYPE,
        "memory_mib": GPU_MEMORY_MIB,
        "timeout_seconds": GPU_TIMEOUT_SECONDS,
        "max_containers": GPU_MAX_CONTAINERS,
        "result_volume": RESULT_VOLUME_NAME,
        "result_volume_version": RESULT_VOLUME_VERSION,
        "cell_lease_dict": CELL_LEASE_DICT_NAME,
        "cell_lease_ttl_seconds": CELL_LEASE_TTL_SECONDS,
    },
}
CONTROL_IMAGE = modal.Image.debian_slim(
    python_version="3.12"
).add_local_python_source("experiments.commitment_surface.e5_core").add_local_file(
    str(RUNTIME_LOCK_PATH),
    "/root/e5_requirements.txt",
)
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements(str(RUNTIME_LOCK_PATH))
    .add_local_python_source("experiments.commitment_surface.e5_core")
    .add_local_file(str(RUNTIME_LOCK_PATH), "/root/e5_requirements.txt")
)
app = modal.App(name="research-derived-commitment-surface-e5")
hf_cache = modal.Volume.from_name("pythia-hf-cache", create_if_missing=True)
e5_results = modal.Volume.from_name(
    RESULT_VOLUME_NAME,
    create_if_missing=True,
    version=RESULT_VOLUME_VERSION,
)
e5_cell_leases = modal.Dict.from_name(
    CELL_LEASE_DICT_NAME,
    create_if_missing=True,
)

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


def _implementation_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in (
        Path(__file__),
        Path(__file__).with_name("e5_core.py"),
        RUNTIME_LOCK_PATH,
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _result_path(manifest_id: str, cell_id: str) -> Path:
    return Path("/results") / manifest_id / f"{cell_id}.json"


def _lease_key(manifest_id: str, cell_id: str) -> str:
    return f"{manifest_id}/{cell_id}"


def _pop_lease_if_present(key: str) -> object:
    try:
        return e5_cell_leases.pop(key)
    except KeyError:
        return None


def _acquire_cell_lease(
    manifest_id: str,
    cell_id: str,
    launch_id: str,
) -> dict[str, Any]:
    key = _lease_key(manifest_id, cell_id)
    now = time.time()
    record = {
        "key": key,
        "manifest_id": manifest_id,
        "cell_id": cell_id,
        "launch_id": launch_id,
        "attempt_number": 1,
        "acquired_at_unix": now,
        "expires_at_unix": now + CELL_LEASE_TTL_SECONDS,
    }
    if e5_cell_leases.put(key, record, skip_if_exists=True):
        return record
    existing = e5_cell_leases.get(key)
    if (
        isinstance(existing, dict)
        and float(existing.get("expires_at_unix", float("inf"))) <= now
        and _pop_lease_if_present(key) == existing
        and e5_cell_leases.put(key, record, skip_if_exists=True)
    ):
        return record
    raise RuntimeError(
        f"cell already has an active lease: {cell_id}; inspect or retry later"
    )


def _release_cell_lease(record: dict[str, Any]) -> None:
    key = str(record["key"])
    if e5_cell_leases.get(key) == record:
        _pop_lease_if_present(key)


def _read_reusable_cell(
    manifest_id: str, cell_id: str
) -> dict[str, Any] | None:
    try:
        cell = json.loads(
            _result_path(manifest_id, cell_id).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(cell, dict) or not cell_is_reusable(
        cell, manifest_id, cell_id
    ):
        return None
    return cell


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary_path.replace(path)


def _record_phase_failure(
    path: Path,
    payload: dict[str, Any],
    *,
    phase: str,
    error: BaseException,
) -> None:
    payload["status"] = f"failed during {phase}"
    payload["operation"]["phase"] = phase
    payload["diagnostics"] = {
        "failed_phase": phase,
        "error_type": type(error).__name__,
        "error": str(error),
    }
    _write_payload(path, payload)


@app.function(
    image=CONTROL_IMAGE,
    timeout=15 * 60,
    memory=1024,
    volumes={"/results": e5_results},
)
def inspect_cached_cells(arg: dict[str, Any]) -> dict[str, Any]:
    e5_results.reload()
    manifest_id = str(arg["manifest_id"])
    reusable: list[dict[str, Any]] = []
    invalid_cell_ids: list[str] = []
    missing_cell_ids: list[str] = []
    active_leases: list[dict[str, Any]] = []
    now = time.time()
    for cell in arg["cells"]:
        cell_id = str(cell["cell_id"])
        path = _result_path(manifest_id, cell_id)
        lease = e5_cell_leases.get(_lease_key(manifest_id, cell_id))
        if lease_record_is_active(lease, now_unix=now):
            active_leases.append(dict(lease))
        if not path.exists():
            missing_cell_ids.append(cell_id)
            continue
        cached = _read_reusable_cell(manifest_id, cell_id)
        if cached is None:
            invalid_cell_ids.append(cell_id)
            continue
        reusable.append(cached)
    return {
        "reusable_count": len(reusable),
        "reusable_cell_ids": [str(cell["cell_id"]) for cell in reusable],
        "invalid_count": len(invalid_cell_ids),
        "invalid_cell_ids": invalid_cell_ids,
        "missing_count": len(missing_cell_ids),
        "missing_cell_ids": missing_cell_ids,
        "active_lease_count": len(active_leases),
        "active_leases": active_leases,
        "reusable_cells": (
            reusable if bool(arg.get("include_reusable_cells", False)) else []
        ),
    }


@app.function(
    image=IMAGE,
    timeout=15 * 60,
    memory=1024,
    volumes={"/results": e5_results},
)
def control_preflight(arg: dict[str, Any]) -> dict[str, Any]:
    """Prove the pinned image and result-volume round trip without a GPU."""
    from importlib.metadata import version

    manifest_id = str(arg["manifest_id"])
    resolved_dependencies = {
        package: version(package) for package in DEPENDENCY_VERSIONS
    }
    record = {
        "manifest_id": manifest_id,
        "expected_cell_count": int(arg["expected_cell_count"]),
        "execution_environment": arg["execution_environment"],
    }
    path = Path("/results/preflight") / f"{manifest_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    temporary_path.replace(path)
    e5_results.commit()
    observed = json.loads(path.read_text(encoding="utf-8"))
    return {
        "pass": (
            observed == record
            and resolved_dependencies == DEPENDENCY_VERSIONS
        ),
        "resolved_dependencies": resolved_dependencies,
        "result_volume": RESULT_VOLUME_NAME,
        "result_volume_version": RESULT_VOLUME_VERSION,
        "record_path": str(path),
    }


@app.function(
    image=IMAGE,
    timeout=60 * 60,
    memory=4096,
    retries=2,
    volumes={"/cache/huggingface": hf_cache},
)
def prefetch_models(models: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    from huggingface_hub import snapshot_download

    hf_cache.reload()
    for size, revision in models:
        snapshot_download(
            repo_id=f"EleutherAI/pythia-{size}",
            revision=revision,
            cache_dir="/cache/huggingface",
        )
    hf_cache.commit()
    return tuple(size for size, _ in models)


def _run_cell_impl(arg: dict[str, Any]) -> dict[str, Any]:
    worker_started = time.perf_counter()
    size = str(arg["size"])
    modulus = int(arg["n"])
    seed = int(arg["seed"])
    arm_text = str(arg["arm"])
    manifest_id = str(arg["manifest_id"])
    cell_id = str(arg["cell_id"])
    e5_results.reload()
    hf_cache.reload()
    result_path = _result_path(manifest_id, cell_id)
    cached = _read_reusable_cell(manifest_id, cell_id)
    if cached is not None:
        return cached

    import torch
    import torch.nn.functional as F
    from peft import (  # ty: ignore[unresolved-import]
        LoraConfig,
        TaskType,
        get_peft_model,
    )
    from transformers import (  # ty: ignore[unresolved-import]
        AutoModelForCausalLM,
        AutoTokenizer,
    )

    run_config = E5RunConfig(
        sizes=(size,),
        moduli=(modulus,),
        seeds=(seed,),
        arms=(arm_text,),
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
    revision = str(arg["model_revision"])
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
        offset = random_seeded_offset(seed, n)
        plans = build_exposure_plans(split, design, offset)
        plan = plans[arm]
        audit = audit_exposure(plan, split)

        tokenizer = AutoTokenizer.from_pretrained(
            repo,
            revision=revision,
            cache_dir=cache_dir,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        base = AutoModelForCausalLM.from_pretrained(
            repo,
            revision=revision,
            cache_dir=cache_dir,
            dtype=torch.float32,
        )
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
            "run_manifest_id": manifest_id,
            "cell_id": cell_id,
            "arm": arm.value,
            "size": size,
            "n": n,
            "seed": seed,
            "model_revision": revision,
            "execution_environment": arg["execution_environment"],
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

    cell = train_cell(arm_text, modulus, seed)
    cell["cell_runtime_seconds"] = time.perf_counter() - worker_started
    cell["run_config"] = asdict(run_config)
    cell["attempt"] = arg["attempt"]
    cell["resource_request"] = {
        "gpu": GPU_TYPE,
        "memory_mib": GPU_MEMORY_MIB,
        "timeout_seconds": GPU_TIMEOUT_SECONDS,
        "max_containers": GPU_MAX_CONTAINERS,
    }
    result_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = result_path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps(cell, indent=2), encoding="utf-8")
    temporary_path.replace(result_path)
    e5_results.commit()
    return cell


@app.function(
    image=IMAGE,
    gpu=GPU_TYPE,
    timeout=GPU_TIMEOUT_SECONDS,
    memory=GPU_MEMORY_MIB,
    max_containers=GPU_MAX_CONTAINERS,
    volumes={
        "/cache/huggingface": hf_cache,
        "/results": e5_results,
    },
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    manifest_id = str(arg["manifest_id"])
    cell_id = str(arg["cell_id"])
    e5_results.reload()
    cached = _read_reusable_cell(manifest_id, cell_id)
    if cached is not None:
        return cached
    lease = _acquire_cell_lease(
        manifest_id,
        cell_id,
        str(arg["launch_id"]),
    )
    try:
        return _run_cell_impl({**arg, "attempt": lease})
    finally:
        _release_cell_lease(lease)


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
    run_kind: str = "development",
    dry_run: bool = False,
    inspect: bool = False,
    execute: bool = False,
    expected_manifest_id: str = "",
    max_gpu_cells: int = 0,
    out: str = "artifacts/commitment_surface/e5_generator_vs_coverage.json",
) -> None:
    if getattr(modal, "__version__", None) != MODAL_CLIENT_VERSION:
        raise RuntimeError(
            "E5 requires modal=="
            f"{MODAL_CLIENT_VERSION}; invoke uvx with the pinned version"
        )
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
    kind = E5RunKind(run_kind)
    config_dict = asdict(config)
    unsupported_sizes = sorted(set(config.sizes) - set(MODEL_REVISIONS))
    if unsupported_sizes:
        raise ValueError(
            "no frozen model revision for sizes: " + ", ".join(unsupported_sizes)
        )
    manifest = build_run_manifest(
        config_dict,
        run_kind=kind,
        implementation_fingerprint=_implementation_fingerprint(),
        execution_environment=EXECUTION_ENVIRONMENT,
    )
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    selected_actions = [
        name
        for name, selected in (
            ("dry_run", dry_run),
            ("inspect", inspect),
            ("execute", execute),
        )
        if selected
    ]
    if len(selected_actions) != 1:
        raise ValueError(
            "select exactly one action: --dry-run, --inspect, or --execute"
        )
    action = selected_actions[0]
    launch_id = str(uuid.uuid4())
    if execute and max_gpu_cells <= 0:
        raise ValueError("--execute requires a positive --max-gpu-cells")
    if execute and kind is E5RunKind.CONFIRMATORY:
        if not expected_manifest_id:
            raise ValueError(
                "confirmatory --execute requires --expected-manifest-id"
            )
        if expected_manifest_id != manifest["manifest_id"]:
            raise ValueError(
                "--expected-manifest-id does not match the computed manifest: "
                f"expected {manifest['manifest_id']}"
            )

    payload: dict[str, Any] = {
        "experiment": "E5 generator learning vs labeled orbit coverage",
        "status": "operation planned; no remote phase started",
        "run_kind": kind.value,
        "config": config_dict,
        "manifest": manifest,
        "operation": {
            "launch_id": launch_id,
            "action": action,
            "phase": "manifest_built",
            "max_gpu_cells": max_gpu_cells if execute else None,
            "expected_manifest_id": expected_manifest_id or None,
        },
        "cells": [],
        "analysis": {
            "confirmatory_ready": False,
            "verdict": "not_run",
        },
    }
    _write_payload(out_path, payload)

    if inspect:
        try:
            checkpoint_scan = inspect_cached_cells.remote(
                {
                    "manifest_id": manifest["manifest_id"],
                    "cells": manifest["cells"],
                }
            )
        except Exception as error:
            _record_phase_failure(
                out_path,
                payload,
                phase="checkpoint_inspection",
                error=error,
            )
            raise
        checkpoint_scan.pop("reusable_cells")
        payload["status"] = "checkpoint inspection complete; no GPU cells executed"
        payload["operation"]["phase"] = "complete"
        payload["checkpoint_inspection"] = checkpoint_scan
        _write_payload(out_path, payload)
        print(json.dumps(checkpoint_scan, indent=2))
        print(f"wrote {out_path}; inspection only")
        return

    try:
        preflight = control_preflight.remote(
            {
                "manifest_id": manifest["manifest_id"],
                "expected_cell_count": manifest["expected_cell_count"],
                "execution_environment": EXECUTION_ENVIRONMENT,
            }
        )
    except Exception as error:
        _record_phase_failure(
            out_path,
            payload,
            phase="control_preflight",
            error=error,
        )
        raise
    payload["control_preflight"] = preflight
    payload["operation"]["phase"] = "control_preflight_complete"
    _write_payload(out_path, payload)
    if preflight.get("pass") is not True:
        error = RuntimeError("E5 control preflight failed")
        _record_phase_failure(
            out_path,
            payload,
            phase="control_preflight",
            error=error,
        )
        raise error
    if dry_run:
        payload["status"] = "manifest and CPU preflight only; no GPU cells executed"
        payload["operation"]["phase"] = "complete"
        _write_payload(out_path, payload)
        print(
            json.dumps(
                {key: value for key, value in manifest.items() if key != "cells"},
                indent=2,
            )
        )
        print(f"wrote {out_path}; dry run only")
        return

    manifest_cells = list(manifest["cells"])
    try:
        initial_checkpoint_scan = inspect_cached_cells.remote(
            {
                "manifest_id": manifest["manifest_id"],
                "cells": manifest_cells,
                "include_reusable_cells": True,
            }
        )
    except Exception as error:
        _record_phase_failure(
            out_path,
            payload,
            phase="checkpoint_scan",
            error=error,
        )
        raise
    cached_cells = initial_checkpoint_scan.pop("reusable_cells")
    payload["initial_checkpoint_scan"] = initial_checkpoint_scan
    payload["operation"]["phase"] = "checkpoint_scan_complete"
    _write_payload(out_path, payload)
    cached_by_id = {str(cell["cell_id"]): cell for cell in cached_cells}
    missing_cells = [
        cell
        for cell in manifest_cells
        if str(cell["cell_id"]) not in cached_by_id
    ]
    if kind is E5RunKind.CONFIRMATORY and max_gpu_cells < len(missing_cells):
        error = ValueError(
            "confirmatory --max-gpu-cells must cover every missing cell: "
            f"need {len(missing_cells)}, received {max_gpu_cells}"
        )
        _record_phase_failure(
            out_path,
            payload,
            phase="execution_authorization",
            error=error,
        )
        raise error
    fresh_cells: list[dict[str, Any]] = []
    launch: dict[str, Any]
    if missing_cells:
        prioritized_cells = prioritize_launch_cells(missing_cells)[:max_gpu_cells]
        missing_sizes = tuple(
            dict.fromkeys(str(cell["size"]) for cell in prioritized_cells)
        )
        launch = {
            "launch_id": launch_id,
            "authorized_gpu_cell_count": max_gpu_cells,
            "selected_cell_count": len(prioritized_cells),
            "selected_cell_ids": [
                str(cell["cell_id"]) for cell in prioritized_cells
            ],
        }
        payload["launch"] = launch
        payload["operation"]["phase"] = "model_prefetch"
        _write_payload(out_path, payload)
        try:
            prefetch_models.remote(
                tuple((size, MODEL_REVISIONS[size]) for size in missing_sizes)
            )
        except Exception as error:
            _record_phase_failure(
                out_path,
                payload,
                phase="model_prefetch",
                error=error,
            )
            raise
        payload["operation"]["phase"] = "model_prefetch_complete"
        _write_payload(out_path, payload)
        shared_config = {
            key: value
            for key, value in config_dict.items()
            if key not in {"sizes", "moduli", "seeds", "arms"}
        }
        args = [
            {
                **shared_config,
                **cell,
                "manifest_id": manifest["manifest_id"],
                "model_revision": MODEL_REVISIONS[str(cell["size"])],
                "execution_environment": EXECUTION_ENVIRONMENT,
                "launch_id": launch_id,
            }
            for cell in prioritized_cells
        ]
        payload["operation"]["phase"] = "gpu_dispatch"
        _write_payload(out_path, payload)
        try:
            mapped = list(run_cell.map(args, return_exceptions=True))
        except Exception as error:
            _record_phase_failure(
                out_path,
                payload,
                phase="gpu_dispatch",
                error=error,
            )
            raise
        launch_failures = [
            {
                "cell_id": str(arg["cell_id"]),
                "launch_id": launch_id,
                "error_type": type(result).__name__,
                "error": str(result),
            }
            for arg, result in zip(args, mapped)
            if not isinstance(result, dict)
        ]
        fresh_cells = [
            result
            for result in mapped
            if isinstance(result, dict)
        ]
        launch["failures"] = launch_failures
        payload["operation"]["phase"] = "gpu_dispatch_complete"
        _write_payload(out_path, payload)
    else:
        launch_failures = []
        launch = {
            "launch_id": launch_id,
            "authorized_gpu_cell_count": max_gpu_cells,
            "selected_cell_count": 0,
            "selected_cell_ids": [],
            "failures": [],
        }
        payload["launch"] = launch
    try:
        final_checkpoint_scan = inspect_cached_cells.remote(
            {
                "manifest_id": manifest["manifest_id"],
                "cells": manifest_cells,
                "include_reusable_cells": True,
            }
        )
    except Exception as error:
        _record_phase_failure(
            out_path,
            payload,
            phase="final_checkpoint_scan",
            error=error,
        )
        raise
    checkpointed_cells = final_checkpoint_scan.pop("reusable_cells")
    cells_by_id = {
        str(cell["cell_id"]): cell
        for cell in [*cached_cells, *fresh_cells, *checkpointed_cells]
    }
    cells = [
        cells_by_id[str(cell["cell_id"])]
        for cell in manifest_cells
        if str(cell["cell_id"]) in cells_by_id
    ]
    missing_cell_ids = [
        str(cell["cell_id"])
        for cell in manifest_cells
        if str(cell["cell_id"]) not in cells_by_id
    ]
    payload.update(
        {
            "status": (
                "post-hoc preregistered follow-up complete"
                if not missing_cell_ids
                else "incomplete; rerun the identical command to resume missing cells"
            ),
            "control_preflight": preflight,
            "cells": cells,
            "analysis": analyze_e5(
                cells,
                grid_spec=grid_spec_for_run_kind(kind),
            ),
        }
    )
    launch.update(
        {
            "cached_cell_count": len(cached_cells),
            "completed_cell_count": len(cells),
            "missing_cell_ids": missing_cell_ids,
            "final_checkpoint_scan": final_checkpoint_scan,
            "failures": launch_failures,
        }
    )
    payload["operation"]["phase"] = "complete"
    _write_payload(out_path, payload)
    print(json.dumps(payload["analysis"], indent=2))
    print(f"wrote {out_path}")
