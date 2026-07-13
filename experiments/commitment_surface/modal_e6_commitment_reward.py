#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""E6: compare commitment-surface and self-consistency self-training rewards.

Exactly one action is required. ``--dry-run`` validates the deterministic
manifest and pinned CPU control path, ``--inspect`` reports resumable cell
state, and ``--execute`` authorizes a bounded number of coupled L4 strata.
SC and CS always execute inside the same worker and consume one symmetric,
byte-identical candidate pool per round.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from experiments.commitment_surface.e6_analysis import (
    analyze_e6,
    build_run_manifest,
    cell_is_reusable,
    grid_spec_for_run_kind,
)
from experiments.commitment_surface.e6_core import E6Arm, E6RunKind
from experiments.commitment_surface.e6_runtime import (
    CELL_LEASE_TTL_SECONDS,
    GPU_MAX_CONTAINERS,
    GPU_MEMORY_MIB,
    GPU_TIMEOUT_SECONDS,
    GPU_TYPE,
    PYTORCH_CUDA_ALLOC_CONF,
    E6ModalRunConfig,
    build_execution_strata,
    lease_record_is_active,
    prioritize_strata,
    validate_runtime_arms,
)
modal = importlib.import_module("modal")

RUNTIME_LOCK_PATH = Path(__file__).with_name("e6_requirements.txt")
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
RESULT_VOLUME_NAME = "commitment-surface-e6-results-v1"
RESULT_VOLUME_VERSION = 2
STRATUM_LEASE_DICT_NAME = "commitment-surface-e6-stratum-leases"
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
        "stratum_lease_dict": STRATUM_LEASE_DICT_NAME,
        "stratum_lease_ttl_seconds": CELL_LEASE_TTL_SECONDS,
        "pytorch_cuda_alloc_conf": PYTORCH_CUDA_ALLOC_CONF,
        "analytical_cells_per_confirmatory_grid": 108,
        "coupled_gpu_strata_per_confirmatory_grid": 27,
    },
}

CONTROL_IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .add_local_python_source("experiments.commitment_surface.e6_core")
    .add_local_python_source("experiments.commitment_surface.e6_analysis")
    .add_local_python_source("experiments.commitment_surface.e6_runtime")
    .add_local_file(str(RUNTIME_LOCK_PATH), "/root/e6_requirements.txt")
)
IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements(str(RUNTIME_LOCK_PATH))
    .env({"PYTORCH_CUDA_ALLOC_CONF": PYTORCH_CUDA_ALLOC_CONF})
    .add_local_python_source("experiments.commitment_surface.e5_core")
    .add_local_python_source("experiments.commitment_surface.e6_core")
    .add_local_python_source("experiments.commitment_surface.e6_analysis")
    .add_local_python_source("experiments.commitment_surface.e6_runtime")
    .add_local_python_source("experiments.commitment_surface.e6_training")
    .add_local_file(str(RUNTIME_LOCK_PATH), "/root/e6_requirements.txt")
)
app = modal.App(name="research-derived-commitment-surface-e6")
hf_cache = modal.Volume.from_name("pythia-hf-cache", create_if_missing=True)
e6_results = modal.Volume.from_name(
    RESULT_VOLUME_NAME,
    create_if_missing=True,
    version=RESULT_VOLUME_VERSION,
)
e6_stratum_leases = modal.Dict.from_name(
    STRATUM_LEASE_DICT_NAME,
    create_if_missing=True,
)


def _implementation_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in (
        Path(__file__),
        Path(__file__).with_name("e6_training.py"),
        Path(__file__).with_name("e6_runtime.py"),
        Path(__file__).with_name("e6_core.py"),
        Path(__file__).with_name("e6_analysis.py"),
        Path(__file__).with_name("e5_core.py"),
        RUNTIME_LOCK_PATH,
    ):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _result_path(manifest_id: str, cell_id: str) -> Path:
    return Path("/results") / manifest_id / f"{cell_id}.json"


def _lease_key(manifest_id: str, stratum_id: str) -> str:
    return f"{manifest_id}/{stratum_id}"


def _pop_lease_if_present(key: str) -> object:
    try:
        return e6_stratum_leases.pop(key)
    except KeyError:
        return None


def _acquire_stratum_lease(
    manifest_id: str,
    stratum_id: str,
    launch_id: str,
) -> dict[str, Any]:
    key = _lease_key(manifest_id, stratum_id)
    now = time.time()
    record = {
        "key": key,
        "manifest_id": manifest_id,
        "stratum_id": stratum_id,
        "launch_id": launch_id,
        "attempt_number": 1,
        "acquired_at_unix": now,
        "expires_at_unix": now + CELL_LEASE_TTL_SECONDS,
    }
    if e6_stratum_leases.put(key, record, skip_if_exists=True):
        return record
    existing = e6_stratum_leases.get(key)
    if (
        isinstance(existing, dict)
        and float(existing.get("expires_at_unix", float("inf"))) <= now
        and _pop_lease_if_present(key) == existing
        and e6_stratum_leases.put(key, record, skip_if_exists=True)
    ):
        return record
    raise RuntimeError(
        f"stratum already has an active lease: {stratum_id}; inspect or retry later"
    )


def _release_stratum_lease(record: dict[str, Any]) -> None:
    key = str(record["key"])
    if e6_stratum_leases.get(key) == record:
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


def _read_reusable_stratum(arg: dict[str, Any]) -> list[dict[str, Any]] | None:
    cells = [
        _read_reusable_cell(str(arg["manifest_id"]), str(cell_id))
        for cell_id in arg["cell_ids"]
    ]
    if any(cell is None for cell in cells):
        return None
    return [cell for cell in cells if cell is not None]


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
    volumes={"/results": e6_results},
)
def inspect_cached_cells(arg: dict[str, Any]) -> dict[str, Any]:
    e6_results.reload()
    manifest_id = str(arg["manifest_id"])
    reusable: list[dict[str, Any]] = []
    invalid_cell_ids: list[str] = []
    missing_cell_ids: list[str] = []
    active_by_key: dict[str, dict[str, Any]] = {}
    now = time.time()
    for cell in arg["cells"]:
        cell_id = str(cell["cell_id"])
        stratum_id = cell_id.rsplit("__", maxsplit=1)[0]
        lease = e6_stratum_leases.get(_lease_key(manifest_id, stratum_id))
        if lease_record_is_active(lease, now_unix=now):
            active_by_key[str(lease["key"])] = dict(lease)
        path = _result_path(manifest_id, cell_id)
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
        "active_lease_count": len(active_by_key),
        "active_leases": list(active_by_key.values()),
        "reusable_cells": (
            reusable if bool(arg.get("include_reusable_cells", False)) else []
        ),
    }


@app.function(
    image=IMAGE,
    timeout=15 * 60,
    memory=1024,
    volumes={"/results": e6_results},
)
def control_preflight(arg: dict[str, Any]) -> dict[str, Any]:
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
    e6_results.commit()
    observed = json.loads(path.read_text(encoding="utf-8"))
    return {
        "pass": observed == record and resolved_dependencies == DEPENDENCY_VERSIONS,
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


@app.function(
    image=IMAGE,
    gpu=GPU_TYPE,
    timeout=GPU_TIMEOUT_SECONDS,
    memory=GPU_MEMORY_MIB,
    max_containers=GPU_MAX_CONTAINERS,
    volumes={
        "/cache/huggingface": hf_cache,
        "/results": e6_results,
    },
)
def run_stratum(arg: dict[str, Any]) -> list[dict[str, Any]]:
    from experiments.commitment_surface.e6_training import run_e6_stratum

    e6_results.reload()
    cached = _read_reusable_stratum(arg)
    if cached is not None:
        return cached
    lease = _acquire_stratum_lease(
        str(arg["manifest_id"]),
        str(arg["stratum_id"]),
        str(arg["launch_id"]),
    )
    try:
        cells = run_e6_stratum({**arg, "attempt": lease})
        manifest_id = str(arg["manifest_id"])
        for cell in cells:
            path = _result_path(manifest_id, str(cell["cell_id"]))
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = path.with_suffix(".tmp")
            temporary_path.write_text(json.dumps(cell, indent=2), encoding="utf-8")
            temporary_path.replace(path)
        e6_results.commit()
        return cells
    finally:
        _release_stratum_lease(lease)


@app.local_entrypoint()
def main(
    sizes: str = "70m,160m,410m",
    ns: str = "13,17,23",
    seed_slots: int = 3,
    arms: str = "SC,CS,GT,A-ref",
    base_seed: int = 20260713,
    rounds: int = 6,
    train_frac: float = 0.5,
    train_shift_count: int = 3,
    bootstrap_epochs: int = 160,
    generations_per_input: int = 8,
    candidate_proposer: str = "paired_half_mix",
    generation_temperature: float = 0.8,
    round_epochs: int = 40,
    selection_fraction: float = 0.5,
    lora_rank: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    lora_lr: float = 5e-4,
    weight_decay: float = 0.0,
    grad_clip: float = 1.0,
    spectral_mass_fraction: float = 0.5,
    patch_ce_threshold: float = 0.05,
    collapse_tolerance: float = 0.05,
    patch_dip_tolerance: float = 0.01,
    transport_retention_fraction: float = 0.75,
    generator_coverage_margin: float = 0.10,
    candidate_batch_size: int = 32,
    run_kind: str = "development",
    dry_run: bool = False,
    inspect: bool = False,
    execute: bool = False,
    expected_manifest_id: str = "",
    max_gpu_cells: int = 0,
    out: str = "artifacts/commitment_surface/e6_commitment_reward.json",
) -> None:
    if getattr(modal, "__version__", None) != MODAL_CLIENT_VERSION:
        raise RuntimeError(
            "E6 requires modal=="
            f"{MODAL_CLIENT_VERSION}; invoke uvx with the pinned version"
        )
    kind = E6RunKind(run_kind)
    arm_values = tuple(
        E6Arm(item.strip()).value for item in arms.split(",") if item.strip()
    )
    validate_runtime_arms(arm_values, run_kind=kind)
    config = E6ModalRunConfig(
        sizes=tuple(item.strip() for item in sizes.split(",") if item.strip()),
        moduli=tuple(int(item.strip()) for item in ns.split(",") if item.strip()),
        seed_slots=tuple(range(seed_slots)),
        arms=arm_values,
        base_seed=base_seed,
        rounds=rounds,
        train_frac=train_frac,
        train_shift_count=train_shift_count,
        bootstrap_epochs=bootstrap_epochs,
        generations_per_input=generations_per_input,
        candidate_proposer=candidate_proposer,
        generation_temperature=generation_temperature,
        round_epochs=round_epochs,
        selection_fraction=selection_fraction,
        lora_rank=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        lora_lr=lora_lr,
        weight_decay=weight_decay,
        grad_clip=grad_clip,
        spectral_mass_fraction=spectral_mass_fraction,
        patch_ce_threshold=patch_ce_threshold,
        collapse_tolerance=collapse_tolerance,
        patch_dip_tolerance=patch_dip_tolerance,
        transport_retention_fraction=transport_retention_fraction,
        generator_coverage_margin=generator_coverage_margin,
        candidate_batch_size=candidate_batch_size,
    )
    unsupported_sizes = sorted(set(config.sizes) - set(MODEL_REVISIONS))
    if unsupported_sizes:
        raise ValueError(
            "no frozen model revision for sizes: " + ", ".join(unsupported_sizes)
        )
    config_dict = config.scientific_config()
    manifest = build_run_manifest(
        config_dict,
        run_kind=kind,
        implementation_fingerprint=_implementation_fingerprint(),
        execution_environment=EXECUTION_ENVIRONMENT,
    )
    strata = build_execution_strata(manifest["cells"])
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
        raise ValueError("select exactly one action: --dry-run, --inspect, or --execute")
    action = selected_actions[0]
    launch_id = str(uuid.uuid4())
    if execute and max_gpu_cells <= 0:
        raise ValueError("--execute requires a positive --max-gpu-cells")
    if execute and kind is E6RunKind.CONFIRMATORY:
        if not expected_manifest_id:
            raise ValueError("confirmatory --execute requires --expected-manifest-id")
        if expected_manifest_id != manifest["manifest_id"]:
            raise ValueError(
                "--expected-manifest-id does not match the computed manifest: "
                f"expected {manifest['manifest_id']}"
            )

    payload: dict[str, Any] = {
        "experiment": "E6 commitment-surface reward self-training",
        "status": "operation planned; no remote phase started",
        "run_kind": kind.value,
        "config": config_dict,
        "manifest": manifest,
        "operation": {
            "launch_id": launch_id,
            "action": action,
            "phase": "manifest_built",
            "max_gpu_strata": max_gpu_cells if execute else None,
            "expected_manifest_id": expected_manifest_id or None,
        },
        "cells": [],
        "analysis": {"confirmatory_ready": False, "verdict": "not_run"},
    }
    _write_payload(out_path, payload)

    if inspect:
        checkpoint_scan = inspect_cached_cells.remote(
            {"manifest_id": manifest["manifest_id"], "cells": manifest["cells"]}
        )
        checkpoint_scan.pop("reusable_cells")
        payload["status"] = "checkpoint inspection complete; no GPU strata executed"
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
        _record_phase_failure(out_path, payload, phase="control_preflight", error=error)
        raise
    payload["control_preflight"] = preflight
    payload["operation"]["phase"] = "control_preflight_complete"
    _write_payload(out_path, payload)
    if preflight.get("pass") is not True:
        error = RuntimeError("E6 control preflight failed")
        _record_phase_failure(out_path, payload, phase="control_preflight", error=error)
        raise error
    if dry_run:
        payload["status"] = "manifest and CPU preflight only; no GPU strata executed"
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

    try:
        initial_scan = inspect_cached_cells.remote(
            {
                "manifest_id": manifest["manifest_id"],
                "cells": manifest["cells"],
                "include_reusable_cells": True,
            }
        )
    except Exception as error:
        _record_phase_failure(out_path, payload, phase="checkpoint_scan", error=error)
        raise
    cached_cells = initial_scan.pop("reusable_cells")
    cached_by_id = {str(cell["cell_id"]): cell for cell in cached_cells}
    missing_strata = [
        stratum
        for stratum in strata
        if any(str(cell_id) not in cached_by_id for cell_id in stratum["cell_ids"])
    ]
    if kind is E6RunKind.CONFIRMATORY and max_gpu_cells < len(missing_strata):
        error = ValueError(
            "confirmatory --max-gpu-cells must cover every missing coupled stratum: "
            f"need {len(missing_strata)}, received {max_gpu_cells}"
        )
        _record_phase_failure(
            out_path, payload, phase="execution_authorization", error=error
        )
        raise error
    selected_strata = prioritize_strata(missing_strata)[:max_gpu_cells]
    payload["initial_checkpoint_scan"] = initial_scan
    payload["launch"] = {
        "launch_id": launch_id,
        "authorized_gpu_stratum_count": max_gpu_cells,
        "selected_stratum_count": len(selected_strata),
        "selected_stratum_ids": [
            str(stratum["stratum_id"]) for stratum in selected_strata
        ],
    }
    fresh_cells: list[dict[str, Any]] = []
    launch_failures: list[dict[str, Any]] = []
    if selected_strata:
        missing_sizes = tuple(dict.fromkeys(str(item["size"]) for item in selected_strata))
        payload["operation"]["phase"] = "model_prefetch"
        _write_payload(out_path, payload)
        try:
            prefetch_models.remote(
                tuple((size, MODEL_REVISIONS[size]) for size in missing_sizes)
            )
        except Exception as error:
            _record_phase_failure(out_path, payload, phase="model_prefetch", error=error)
            raise
        shared_config = {
            key: value
            for key, value in config_dict.items()
            if key not in {"sizes", "moduli", "seed_slots", "arms"}
        }
        args = [
            {
                **shared_config,
                **stratum,
                "manifest_id": manifest["manifest_id"],
                "model_revision": MODEL_REVISIONS[str(stratum["size"])],
                "execution_environment": EXECUTION_ENVIRONMENT,
                "launch_id": launch_id,
            }
            for stratum in selected_strata
        ]
        payload["operation"]["phase"] = "gpu_dispatch"
        _write_payload(out_path, payload)
        mapped = list(
            run_stratum.map(
                args,
                return_exceptions=True,
                wrap_returned_exceptions=False,
            )
        )
        for stratum_arg, result in zip(args, mapped):
            if isinstance(result, list) and all(isinstance(cell, dict) for cell in result):
                fresh_cells.extend(result)
            else:
                launch_failures.append(
                    {
                        "stratum_id": str(stratum_arg["stratum_id"]),
                        "launch_id": launch_id,
                        "error_type": type(result).__name__,
                        "error": str(result),
                    }
                )

    final_scan = inspect_cached_cells.remote(
        {
            "manifest_id": manifest["manifest_id"],
            "cells": manifest["cells"],
            "include_reusable_cells": True,
        }
    )
    checkpointed_cells = final_scan.pop("reusable_cells")
    cells_by_id = {
        str(cell["cell_id"]): cell
        for cell in [*cached_cells, *fresh_cells, *checkpointed_cells]
    }
    cells = [
        cells_by_id[str(cell["cell_id"])]
        for cell in manifest["cells"]
        if str(cell["cell_id"]) in cells_by_id
    ]
    missing_cell_ids = [
        str(cell["cell_id"])
        for cell in manifest["cells"]
        if str(cell["cell_id"]) not in cells_by_id
    ]
    payload.update(
        {
            "status": (
                "run complete"
                if not missing_cell_ids
                else "incomplete; rerun the identical command to resume missing strata"
            ),
            "cells": cells,
            "analysis": analyze_e6(cells, grid_spec=grid_spec_for_run_kind(kind)),
        }
    )
    payload["launch"].update(
        {
            "cached_cell_count": len(cached_cells),
            "completed_cell_count": len(cells),
            "missing_cell_ids": missing_cell_ids,
            "final_checkpoint_scan": final_scan,
            "failures": launch_failures,
        }
    )
    payload["operation"]["phase"] = "complete"
    _write_payload(out_path, payload)
    print(json.dumps(payload["analysis"], indent=2))
    print(f"wrote {out_path}")
    if launch_failures:
        raise RuntimeError(
            f"{len(launch_failures)} E6 GPU stratum launch(es) failed; "
            f"resume details are recorded in {out_path}"
        )
