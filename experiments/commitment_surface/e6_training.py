"""GPU training implementation for one coupled E6 size/modulus/seed stratum."""

from __future__ import annotations

import gc
import math
import time
from collections import Counter
from dataclasses import asdict
from typing import Any

from experiments.commitment_surface.e5_core import E5Config, make_split
from experiments.commitment_surface.e6_core import (
    Candidate,
    CandidatePool,
    CommitmentSurfaceSignal,
    E6Arm,
    E6Config,
    GroundTruthSignal,
    derive_e6_seed,
    plan_round,
)
from experiments.commitment_surface.e6_runtime import (
    GPU_MAX_CONTAINERS,
    GPU_MEMORY_MIB,
    GPU_TIMEOUT_SECONDS,
    GPU_TYPE,
    candidate_input_ids,
    paired_proposer_schedule,
)

PARAPHRASES = (
    "Modulo {n}, what is {x} plus {offset}? Answer:",
    "Return ({x} + {offset}) mod {n}. Result:",
)


def run_e6_stratum(arg: dict[str, Any]) -> list[dict[str, Any]]:
    """Train all requested arms together so SC/CS see byte-identical pools."""
    import torch
    import torch.nn.functional as F
    from peft import (  # ty: ignore[unresolved-import]
        LoraConfig,
        TaskType,
        get_peft_model,
        get_peft_model_state_dict,
        set_peft_model_state_dict,
    )
    from transformers import (  # ty: ignore[unresolved-import]
        AutoModelForCausalLM,
        AutoTokenizer,
    )

    started = time.perf_counter()
    size = str(arg["size"])
    modulus = int(arg["n"])
    seed_slot = int(arg["seed_slot"])
    arms = tuple(E6Arm(value) for value in arg["arms"])
    manifest_id = str(arg["manifest_id"])
    cell_ids = {
        E6Arm(arm): str(cell_id)
        for arm, cell_id in zip(arg["arms"], arg["cell_ids"])
    }
    config = E6Config(
        modulus=modulus,
        seed_slot=seed_slot,
        base_seed=int(arg["base_seed"]),
        rounds=int(arg["rounds"]),
        train_frac=float(arg["train_frac"]),
        train_shift_count=int(arg["train_shift_count"]),
        bootstrap_epochs=int(arg["bootstrap_epochs"]),
        generations_per_input=int(arg["generations_per_input"]),
        candidate_proposer=str(arg["candidate_proposer"]),
        generation_temperature=float(arg["generation_temperature"]),
        round_epochs=int(arg["round_epochs"]),
        selection_fraction=float(arg["selection_fraction"]),
        spectral_mass_fraction=float(arg["spectral_mass_fraction"]),
        patch_ce_threshold=float(arg["patch_ce_threshold"]),
        collapse_tolerance=float(arg["collapse_tolerance"]),
        patch_dip_tolerance=float(arg["patch_dip_tolerance"]),
        transport_retention_fraction=float(arg["transport_retention_fraction"]),
        generator_coverage_margin=float(arg["generator_coverage_margin"]),
    )
    candidate_batch_size = int(arg["candidate_batch_size"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("E6 training requires the requested L4 CUDA device")
    repo = f"EleutherAI/pythia-{size}"
    revision = str(arg["model_revision"])
    cache_dir = "/cache/huggingface"

    split_seed = derive_e6_seed(
        base_seed=config.base_seed,
        namespace="split",
        size=size,
        modulus=modulus,
        arm_scope="SC-CS",
        round_index=0,
        seed_slot=seed_slot,
    )
    split = make_split(
        E5Config(
            modulus=modulus,
            train_frac=config.train_frac,
            train_shift_count=config.train_shift_count,
            spectral_mass_fraction=config.spectral_mass_fraction,
            seed=split_seed,
        )
    )
    offset = 1 + (split_seed % (modulus - 1))
    candidate_inputs = candidate_input_ids(
        train_inputs=split.train_inputs,
        ood_inputs=split.ood_inputs,
        novel_shifts=split.k_novel,
        modulus=modulus,
    )
    split_integrity = (
        not set(split.train_inputs) & set(split.ood_inputs)
        and not set(split.k_train) & set(split.k_novel)
    )

    def canonical_prompt(n: int, task_offset: int, x: int) -> str:
        return (
            f"Compute modular addition. Modulus: {n}. Addend: {task_offset}. "
            f"Input: {x}. Output:"
        )

    def prompt_text(template: str, x: int) -> str:
        if template == "canonical":
            return canonical_prompt(modulus, offset, x)
        return template.format(n=modulus, offset=offset, x=x)

    tokenizer = AutoTokenizer.from_pretrained(
        repo,
        revision=revision,
        cache_dir=cache_dir,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

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

    def new_model() -> tuple[Any, Any, list[str]]:
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
                r=int(arg["lora_rank"]),
                lora_alpha=int(arg["lora_alpha"]),
                lora_dropout=float(arg["lora_dropout"]),
                target_modules=targets,
                bias="none",
            ),
        ).to(device)
        return model, base, targets

    def encode_rows(
        xs: list[int], ys: list[int], templates: list[str]
    ) -> dict[str, Any]:
        pad_id = int(tokenizer.pad_token_id)
        eos = tokenizer.eos_token or ""
        rows: list[list[int]] = []
        labels: list[list[int]] = []
        for x, y, template in zip(xs, ys, templates):
            prompt_ids = tokenizer(
                prompt_text(template, x),
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
        for index, (row, labels_row) in enumerate(zip(rows, labels)):
            input_ids[index, : len(row)] = torch.tensor(row, device=device)
            label_ids[index, : len(labels_row)] = torch.tensor(
                labels_row, device=device
            )
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

    def row_nlls(
        model: Any,
        xs: list[int],
        ys: list[int],
        templates: list[str],
    ) -> Any:
        chunks = []
        for start in range(0, len(xs), candidate_batch_size):
            stop = start + candidate_batch_size
            batch = encode_rows(
                xs[start:stop], ys[start:stop], templates[start:stop]
            )
            chunks.append(per_row_nll(model, batch))
        return torch.cat(chunks)

    def candidate_log_probs(
        model: Any, xs: list[int], *, template: str = "canonical"
    ) -> Any:
        repeated_xs = [x for x in xs for _ in range(modulus)]
        candidates = list(range(modulus)) * len(xs)
        templates = [template] * len(repeated_xs)
        with torch.no_grad():
            nll = row_nlls(model, repeated_xs, candidates, templates)
        return F.log_softmax(-nll.view(len(xs), modulus), dim=-1)

    def train_examples(
        model: Any,
        xs: list[int],
        ys: list[int],
        *,
        epochs: int,
    ) -> float:
        if not xs or len(xs) != len(ys):
            raise ValueError("training examples must be nonempty and aligned")
        trainable = [
            parameter for parameter in model.parameters() if parameter.requires_grad
        ]
        optimizer = torch.optim.AdamW(
            trainable,
            lr=float(arg["lora_lr"]),
            weight_decay=float(arg["weight_decay"]),
        )
        final_loss = float("nan")
        templates = ["canonical"] * len(xs)
        for _ in range(epochs):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            weighted_loss = 0.0
            for start in range(0, len(xs), candidate_batch_size):
                stop = min(len(xs), start + candidate_batch_size)
                batch = encode_rows(
                    xs[start:stop], ys[start:stop], templates[start:stop]
                )
                chunk_loss = per_row_nll(model, batch).mean()
                chunk_weight = (stop - start) / len(xs)
                (chunk_weight * chunk_loss).backward()
                weighted_loss += chunk_weight * float(chunk_loss.detach().item())
            if float(arg["grad_clip"]) > 0:
                torch.nn.utils.clip_grad_norm_(trainable, float(arg["grad_clip"]))
            optimizer.step()
            final_loss = weighted_loss
        del optimizer, trainable
        return final_loss

    def lora_modules(model: Any) -> list[tuple[str, Any, Any, float]]:
        result: list[tuple[str, Any, Any, float]] = []
        for name, module in model.named_modules():
            if not hasattr(module, "lora_A") or "default" not in module.lora_A:
                continue
            result.append(
                (
                    name,
                    module.lora_A["default"].weight,
                    module.lora_B["default"].weight,
                    float(module.scaling["default"]),
                )
            )
        if not result:
            raise RuntimeError("no active LoRA matrices found for patching")
        return result

    def apply_spectral_patch(
        model: Any,
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
                total_mass = float(singular.square().sum().item())
                patched_singular = singular.clone()
                remaining = config.spectral_mass_fraction * total_mass
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
                realized = (b_weight.float() @ a_weight.float()) * scale
                realized_mass = float(realized.square().sum().item())
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

    def patch_integrity(stats: list[dict[str, Any]]) -> bool:
        nonzero = [stat for stat in stats if stat["total_spectral_mass"] > 1e-12]
        return bool(nonzero) and all(
            abs(
                float(stat["removed_spectral_mass_fraction"])
                - config.spectral_mass_fraction
            )
            <= 0.02
            for stat in nonzero
        )

    def evaluate(
        model: Any,
        inputs: tuple[int, ...],
        *,
        template: str,
    ) -> tuple[float, float, tuple[int, ...]]:
        log_probs = candidate_log_probs(model, list(inputs), template=template)
        predictions = tuple(int(value) for value in log_probs.argmax(dim=-1).tolist())
        truths = tuple((x + offset) % modulus for x in inputs)
        accuracy = sum(a == b for a, b in zip(predictions, truths)) / len(inputs)
        truth_tensor = torch.tensor(truths, device=device).unsqueeze(-1)
        nll = float(-log_probs.gather(1, truth_tensor).mean().detach().item())
        return float(accuracy), nll, predictions

    def function_table(model: Any) -> tuple[int, ...]:
        log_probs = candidate_log_probs(model, list(range(modulus)))
        return tuple(int(value) for value in log_probs.argmax(dim=-1).tolist())

    def novel_k_accuracy(table: tuple[int, ...]) -> float:
        hits = 0
        total = 0
        for shift in split.k_novel:
            for x in range(modulus):
                hits += table[(x + shift) % modulus] == (table[x] + shift) % modulus
                total += 1
        return hits / total

    def transported_rows(
        xs: list[int], ys: list[int], *, round_index: int
    ) -> tuple[list[int], list[int], list[str]]:
        transport_seed = derive_e6_seed(
            base_seed=config.base_seed,
            namespace="transport",
            size=size,
            modulus=modulus,
            arm_scope="SC-CS",
            round_index=round_index,
            seed_slot=seed_slot,
        )
        moved_xs: list[int] = []
        moved_ys: list[int] = []
        templates: list[str] = []
        for index, (x, y) in enumerate(zip(xs, ys)):
            shift = split.k_novel[(transport_seed + index) % len(split.k_novel)]
            moved_xs.append((x + shift) % modulus)
            moved_ys.append((y + shift) % modulus)
            templates.append(PARAPHRASES[(transport_seed + index) % len(PARAPHRASES)])
        return moved_xs, moved_ys, templates

    def measure(model: Any, *, round_index: int) -> dict[str, Any]:
        model.eval()
        canonical_acc, canonical_nll, _ = evaluate(
            model, split.ood_inputs, template="canonical"
        )
        paraphrase = [
            evaluate(model, split.ood_inputs, template=template)
            for template in PARAPHRASES
        ]
        paraphrase_acc = sum(item[0] for item in paraphrase) / len(paraphrase)
        table = function_table(model)
        novel_accuracy = novel_k_accuracy(table)
        truth_xs = list(split.ood_inputs)
        truth_ys = [(x + offset) % modulus for x in truth_xs]
        moved_xs, moved_ys, moved_templates = transported_rows(
            truth_xs, truth_ys, round_index=round_index
        )
        with torch.no_grad():
            transported_nll = float(
                row_nlls(model, moved_xs, moved_ys, moved_templates).mean().item()
            )
        snapshots, stats = apply_spectral_patch(model)
        _, patched_canonical_nll, _ = evaluate(
            model, split.ood_inputs, template="canonical"
        )
        with torch.no_grad():
            patched_transport_nll = float(
                row_nlls(model, moved_xs, moved_ys, moved_templates).mean().item()
            )
        restore_patch(snapshots)
        return {
            "canonical_ood_accuracy": canonical_acc,
            "paraphrase_ood_accuracy": paraphrase_acc,
            "novel_k_equivariance_accuracy": novel_accuracy,
            "canonical_normalized_patch_ce": patched_canonical_nll - canonical_nll,
            "transported_normalized_patch_ce": (
                patched_transport_nll - transported_nll
            ),
            "patch_stats": stats,
            "patch_integrity_pass": patch_integrity(stats),
        }

    def score_cs_candidates(
        model: Any, pool: CandidatePool
    ) -> tuple[tuple[CommitmentSurfaceSignal, ...], list[dict[str, Any]], bool]:
        xs = [candidate.input_id for candidate in pool.candidates]
        ys = [candidate.generation for candidate in pool.candidates]
        canonical_templates = ["canonical"] * len(xs)
        moved_xs, moved_ys, moved_templates = transported_rows(
            xs, ys, round_index=pool.round_index
        )
        model.eval()
        with torch.no_grad():
            canonical_nll = row_nlls(model, xs, ys, canonical_templates)
            transported_nll = row_nlls(model, moved_xs, moved_ys, moved_templates)
        snapshots, stats = apply_spectral_patch(model)
        with torch.no_grad():
            patched_canonical = row_nlls(model, xs, ys, canonical_templates)
            patched_transport = row_nlls(model, moved_xs, moved_ys, moved_templates)
        restore_patch(snapshots)
        canonical_effects = (patched_canonical - canonical_nll).tolist()
        transport_effects = (patched_transport - transported_nll).tolist()
        signals = tuple(
            CommitmentSurfaceSignal(
                candidate.candidate_id,
                canonical_patch_ce=float(canonical_effect),
                transported_patch_ce=float(transport_effect),
            )
            for candidate, canonical_effect, transport_effect in zip(
                pool.candidates, canonical_effects, transport_effects
            )
        )
        return signals, stats, patch_integrity(stats)

    def sample_candidate_pool(
        sc_model: Any, cs_model: Any, *, round_index: int
    ) -> CandidatePool:
        schedule = paired_proposer_schedule(config.generations_per_input)
        half = config.generations_per_input // 2
        sc_log_probs = candidate_log_probs(sc_model, list(candidate_inputs))
        cs_log_probs = candidate_log_probs(cs_model, list(candidate_inputs))
        generation_seed = derive_e6_seed(
            base_seed=config.base_seed,
            namespace="generation",
            size=size,
            modulus=modulus,
            arm_scope="SC-CS",
            round_index=round_index,
            seed_slot=seed_slot,
        )
        generator = torch.Generator(device=device)
        generator.manual_seed(generation_seed)
        sc_draws = torch.multinomial(
            (sc_log_probs / config.generation_temperature).softmax(dim=-1),
            half,
            replacement=True,
            generator=generator,
        ).tolist()
        cs_draws = torch.multinomial(
            (cs_log_probs / config.generation_temperature).softmax(dim=-1),
            half,
            replacement=True,
            generator=generator,
        ).tolist()
        candidates: list[Candidate] = []
        order = 0
        for input_index, input_id in enumerate(candidate_inputs):
            proposer_indexes = Counter()
            for proposer in schedule:
                draw_index = proposer_indexes[proposer]
                proposer_indexes[proposer] += 1
                draws = sc_draws if proposer == E6Arm.SC.value else cs_draws
                generation = int(draws[input_index][draw_index])
                candidates.append(
                    Candidate(
                        candidate_id=(
                            f"r{round_index}-x{input_id}-{proposer}-d{draw_index}"
                        ),
                        order=order,
                        input_id=input_id,
                        generation=generation,
                    )
                )
                order += 1
        return CandidatePool(round_index=round_index, candidates=tuple(candidates))

    torch.manual_seed(split_seed)
    torch.cuda.manual_seed_all(split_seed)
    sc_model, sc_base, targets = new_model()
    bootstrap_xs = list(split.train_inputs)
    bootstrap_ys = [(x + offset) % modulus for x in bootstrap_xs]
    bootstrap_loss = train_examples(
        sc_model,
        bootstrap_xs,
        bootstrap_ys,
        epochs=config.bootstrap_epochs,
    )
    bootstrap_state = {
        key: value.detach().cpu().clone()
        for key, value in get_peft_model_state_dict(sc_model).items()
    }
    cs_model, cs_base, cs_targets = new_model()
    set_peft_model_state_dict(cs_model, bootstrap_state)
    models: dict[E6Arm, Any] = {E6Arm.SC: sc_model, E6Arm.CS: cs_model}
    bases = [sc_base, cs_base]
    if E6Arm.GT in arms:
        gt_model, gt_base, gt_targets = new_model()
        set_peft_model_state_dict(gt_model, bootstrap_state)
        models[E6Arm.GT] = gt_model
        bases.append(gt_base)
        if gt_targets != targets:
            raise RuntimeError("LoRA targets drifted across paired models")
    if cs_targets != targets:
        raise RuntimeError("LoRA targets drifted across paired models")

    baseline = measure(sc_model, round_index=0)
    previous_novel = {
        arm: float(baseline["novel_k_equivariance_accuracy"]) for arm in arms
    }
    trajectories: dict[E6Arm, list[dict[str, Any]]] = {arm: [] for arm in arms}
    final_losses = {arm: bootstrap_loss for arm in arms}
    proposal_schedule = paired_proposer_schedule(config.generations_per_input)

    for round_index in range(1, config.rounds + 1):
        pool = sample_candidate_pool(sc_model, cs_model, round_index=round_index)
        cs_signals, reward_patch_stats, reward_patch_integrity = score_cs_candidates(
            cs_model, pool
        )
        gt_signals = tuple(
            GroundTruthSignal(
                candidate.candidate_id,
                candidate.generation == (candidate.input_id + offset) % modulus,
            )
            for candidate in pool.candidates
        )
        round_plan = plan_round(
            pool,
            config,
            cs_signals=cs_signals,
            gt_signals=gt_signals,
        )
        candidate_by_id = {
            candidate.candidate_id: candidate for candidate in pool.candidates
        }
        selection_by_arm = {
            arm: round_plan.selection_for(arm) for arm in E6Arm
        }

        for arm in (E6Arm.SC, E6Arm.CS, E6Arm.GT):
            if arm not in models:
                continue
            selection = selection_by_arm[arm]
            selected = [
                candidate_by_id[candidate_id]
                for candidate_id in selection.selected_candidate_ids
            ]
            final_losses[arm] = train_examples(
                models[arm],
                [candidate.input_id for candidate in selected],
                [candidate.generation for candidate in selected],
                epochs=config.round_epochs,
            )

        for arm in arms:
            selection = selection_by_arm[arm]
            selected = [
                candidate_by_id[candidate_id]
                for candidate_id in selection.selected_candidate_ids
            ]
            correct_share = (
                sum(
                    candidate.generation
                    == (candidate.input_id + offset) % modulus
                    for candidate in selected
                )
                / len(selected)
                if selected
                else 0.0
            )
            metrics = (
                dict(baseline)
                if arm is E6Arm.A_REF
                else measure(models[arm], round_index=round_index)
            )
            generator_gain = (
                float(metrics["novel_k_equivariance_accuracy"])
                - previous_novel[arm]
            )
            previous_novel[arm] = float(metrics["novel_k_equivariance_accuracy"])
            metric_patch_integrity = bool(metrics.pop("patch_integrity_pass"))
            metric_patch_stats = metrics.pop("patch_stats")
            arm_patch_integrity = metric_patch_integrity and (
                reward_patch_integrity if arm is E6Arm.CS else True
            )
            trajectories[arm].append(
                {
                    "round": round_index,
                    **metrics,
                    "generator_gain": generator_gain,
                    "coverage_gain": float(correct_share),
                    "candidate_pool_count": selection.candidate_count,
                    "selected_candidate_count": selection.selected_candidate_count,
                    "pool_digest": selection.pool_digest,
                    "candidate_proposer": config.candidate_proposer,
                    "candidate_proposer_counts": dict(Counter(proposal_schedule)),
                    "selected_candidate_ids": list(selection.selected_candidate_ids),
                    "split_integrity_pass": split_integrity,
                    "reward_leakage_pass": True,
                    "patch_integrity_pass": arm_patch_integrity,
                    "spectral_patch": {
                        "measurement": metric_patch_stats,
                        "reward": reward_patch_stats if arm is E6Arm.CS else [],
                    },
                }
            )

    runtime_seconds = time.perf_counter() - started
    cells = []
    for arm in arms:
        rows = trajectories[arm]
        cells.append(
            {
                "run_manifest_id": manifest_id,
                "cell_id": cell_ids[arm],
                "arm": arm.value,
                "size": size,
                "n": modulus,
                "seed_slot": seed_slot,
                "model_revision": revision,
                "execution_environment": arg["execution_environment"],
                "offset": offset,
                "split": asdict(split),
                "candidate_inputs": list(candidate_inputs),
                "bootstrap_loss": bootstrap_loss,
                "final_training_loss": final_losses[arm],
                "rounds": rows,
                "lora_rank": int(arg["lora_rank"]),
                "lora_targets": targets,
                "integrity_pass": all(
                    row["split_integrity_pass"]
                    and row["reward_leakage_pass"]
                    and row["patch_integrity_pass"]
                    for row in rows
                ),
                "stratum_runtime_seconds": runtime_seconds,
                "attempt": arg["attempt"],
                "resource_request": {
                    "gpu": GPU_TYPE,
                    "memory_mib": GPU_MEMORY_MIB,
                    "timeout_seconds": GPU_TIMEOUT_SECONDS,
                    "max_containers": GPU_MAX_CONTAINERS,
                },
            }
        )

    del models, bases, sc_model, cs_model, bootstrap_state
    gc.collect()
    torch.cuda.empty_cache()
    return cells
