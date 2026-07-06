#!/usr/bin/env python3
"""Run the structure-compatible generalization suite.

This module is intentionally importable from Modal workers. Local execution is
supported for development, but the intended confirmatory path is
`modal_l4_suite.py`.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    rows_to_records,
    summarize_rows,
)


DOMAIN_ALIASES = {
    "symbolic": "symbolic_cyclic",
    "symbolic_cyclic": "symbolic_cyclic",
    "vision": "vision_rotation",
    "vision_rotation": "vision_rotation",
    "modular": "modular_neural",
    "modular_neural": "modular_neural",
}


def normalize_domains(domains: list[str]) -> list[str]:
    out: list[str] = []
    for raw in domains:
        key = raw.strip()
        if not key:
            continue
        if key not in DOMAIN_ALIASES:
            known = ", ".join(sorted(DOMAIN_ALIASES))
            raise ValueError(f"unknown domain {key!r}; known domains: {known}")
        normalized = DOMAIN_ALIASES[key]
        if normalized not in out:
            out.append(normalized)
    return out


def symbolic_rows(
    *,
    n_models: int,
    epochs: int,
    base_seed: int,
) -> list[DiagnosticRow]:
    from experiments.symbolic_weakness.neural import run_sweep

    artifacts = run_sweep(
        n_models=n_models,
        modulus=11,
        train_window=3,
        base_seed=base_seed,
        epochs=epochs,
    )
    rows: list[DiagnosticRow] = []
    for idx, artifact in enumerate(artifacts):
        n = max(1, len(artifact.full_function_table))
        rows.append(
            DiagnosticRow(
                domain="symbolic_cyclic",
                model_id=f"symbolic-{base_seed}-{idx}",
                train_accuracy=artifact.train_accuracy,
                id_validation_accuracy=artifact.held_out_validation_accuracy,
                ood_accuracy=artifact.ood_accuracy,
                compatibility_true=artifact.weakness_oracle / n,
                compatibility_wrong=artifact.weakness_wrong_group / n,
                compatibility_inferred=artifact.weakness_partial_cyclic / n,
                final_train_loss=artifact.final_train_loss,
                parameter_l2=artifact.parameter_l2,
                sharpness_proxy=artifact.sharpness_proxy,
                metadata={
                    "config": asdict(artifact.config),
                    "weakness_random_label_norm": artifact.weakness_random_label / n,
                    "function_table": list(artifact.full_function_table),
                },
            )
        )
    return rows


def vision_rows(
    *,
    n_models: int,
    epochs: int,
    base_seed: int,
) -> list[DiagnosticRow]:
    from experiments.rotation_weakness.neural import run_sweep

    artifacts = run_sweep(
        n_models=n_models,
        n_rotations=8,
        train_per_class=3,
        epochs=epochs,
        base_seed=base_seed,
    )
    rows: list[DiagnosticRow] = []
    for idx, artifact in enumerate(artifacts):
        rows.append(
            DiagnosticRow(
                domain="vision_rotation",
                model_id=f"vision-{base_seed}-{idx}",
                train_accuracy=artifact.train_accuracy,
                id_validation_accuracy=artifact.train_accuracy,
                ood_accuracy=artifact.ood_accuracy,
                compatibility_true=artifact.weakness_rotation_norm,
                compatibility_wrong=artifact.weakness_wrong_group_norm,
                final_train_loss=artifact.final_train_loss,
                parameter_l2=artifact.parameter_l2,
                sharpness_proxy=artifact.sharpness_proxy,
                metadata={"config": asdict(artifact.config)},
            )
        )
    return rows


def modular_rows(
    *,
    n_models: int,
    epochs: int,
    base_seed: int,
    device: str | None,
    include_exact: bool,
) -> list[DiagnosticRow]:
    from experiments.structure_compatible_generalization.modular_domain import run_sweep

    return run_sweep(
        n_models=n_models,
        epochs=epochs,
        base_seed=base_seed,
        device=device,
        include_exact=include_exact,
    )


def run_suite(
    *,
    domains: list[str],
    symbolic_models: int,
    vision_models: int,
    modular_models: int,
    symbolic_epochs: int,
    vision_epochs: int,
    modular_epochs: int,
    base_seed: int,
    device: str | None = None,
    include_exact: bool = True,
) -> dict[str, Any]:
    normalized = normalize_domains(domains)
    rows: list[DiagnosticRow] = []
    if "symbolic_cyclic" in normalized and symbolic_models > 0:
        rows.extend(
            symbolic_rows(
                n_models=symbolic_models,
                epochs=symbolic_epochs,
                base_seed=base_seed + 101,
            )
        )
    if "vision_rotation" in normalized and vision_models > 0:
        rows.extend(
            vision_rows(
                n_models=vision_models,
                epochs=vision_epochs,
                base_seed=base_seed + 202,
            )
        )
    if "modular_neural" in normalized and modular_models > 0:
        rows.extend(
            modular_rows(
                n_models=modular_models,
                epochs=modular_epochs,
                base_seed=base_seed + 303,
                device=device,
                include_exact=include_exact,
            )
        )

    return {
        "kind": "structure-compatible generalization suite",
        "manifest": {
            "domains": normalized,
            "symbolic_models": symbolic_models,
            "vision_models": vision_models,
            "modular_models": modular_models,
            "symbolic_epochs": symbolic_epochs,
            "vision_epochs": vision_epochs,
            "modular_epochs": modular_epochs,
            "base_seed": base_seed,
            "device": device,
            "include_exact": include_exact,
        },
        "summary": summarize_rows(rows),
        "rows": rows_to_records(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domains", default="symbolic,vision,modular")
    parser.add_argument("--symbolic-models", type=int, default=32)
    parser.add_argument("--vision-models", type=int, default=24)
    parser.add_argument("--modular-models", type=int, default=32)
    parser.add_argument("--symbolic-epochs", type=int, default=300)
    parser.add_argument("--vision-epochs", type=int, default=80)
    parser.add_argument("--modular-epochs", type=int, default=250)
    parser.add_argument("--base-seed", type=int, default=20260706)
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None)
    parser.add_argument("--no-exact", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    payload = run_suite(
        domains=args.domains.split(","),
        symbolic_models=args.symbolic_models,
        vision_models=args.vision_models,
        modular_models=args.modular_models,
        symbolic_epochs=args.symbolic_epochs,
        vision_epochs=args.vision_epochs,
        modular_epochs=args.modular_epochs,
        base_seed=args.base_seed,
        device=args.device,
        include_exact=not args.no_exact,
    )
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

