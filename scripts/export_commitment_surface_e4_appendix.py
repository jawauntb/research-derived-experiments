#!/usr/bin/env python3
"""Export a compact, public-safe E4 appendix artifact from the raw sweep."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "artifacts" / "commitment_surface" / "e4_pythia_lora_v2.json"
DEFAULT_OUTPUT = (
    ROOT
    / "experiments"
    / "commitment_surface"
    / "results"
    / "e4_pythia_lora_v2_appendix.json"
)
DEFAULT_ENVELOPE = (
    ROOT
    / "experiments"
    / "commitment_surface"
    / "results"
    / "e4_pythia_lora_v2_appendix.json.envelope.json"
)
E4_PRODUCER_MANIFEST = (
    "experiments/commitment_surface/manifests/e4/experiment_manifest.json"
)
E4_GENERATOR_VERSION = "commitment_surface.e4_public_export.v1"

PUBLIC_CONFIG_FIELDS = (
    "sizes",
    "ns",
    "seeds",
    "arms",
    "train_frac",
    "epochs",
    "lora_rank",
    "lora_alpha",
    "lora_dropout",
    "lora_lr",
    "weight_decay",
    "grad_clip",
    "aug_multiplier",
    "base_seed",
)

PUBLIC_CELL_FIELDS = (
    "arm",
    "size",
    "n",
    "seed",
    "offset",
    "train_frac",
    "n_augmented_train_pairs",
    "epochs",
    "final_train_loss",
    "train_accuracy",
    "ood_accuracy",
    "ablated_ood_accuracy",
    "ood_nll",
    "ablated_ood_nll",
    "patch_ce_delta",
    "weakness_oracle_norm",
    "weakness_wrong_group_norm",
    "trainable_lora_l2",
    "head_sharpness_proxy",
    "lora_rank",
)


def _select_fields(source: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: source[field] for field in fields if field in source}


def build_public_artifact(raw_bytes: bytes) -> dict[str, Any]:
    raw = json.loads(raw_bytes)
    cells = raw["cells"]
    config = raw["config"]
    expected_cells = (
        len(config["sizes"])
        * len(config["ns"])
        * len(config["seeds"])
        * len(config["arms"])
    )
    if len(cells) != expected_cells:
        raise ValueError(
            f"incomplete E4 grid: found {len(cells)} cells, expected {expected_cells}"
        )

    return {
        "schema_version": 1,
        "description": (
            "Public-safe compact E4 per-cell and aggregate appendix artifact. "
            "Large function tables, train/OOD input lists, and parameter metadata "
            "are intentionally omitted."
        ),
        "source": {
            "artifact": "artifacts/commitment_surface/e4_pythia_lora_v2.json",
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "bytes": len(raw_bytes),
            "public_safe_export": True,
        },
        "coverage": {
            "expected_cells": expected_cells,
            "exported_cells": len(cells),
            "complete": True,
            "unavailable_fields": [],
            "omitted_raw_fields": sorted(set(cells[0]) - set(PUBLIC_CELL_FIELDS)),
        },
        "config": _select_fields(config, PUBLIC_CONFIG_FIELDS),
        "analysis": raw["analysis"],
        "cells": [_select_fields(cell, PUBLIC_CELL_FIELDS) for cell in cells],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--envelope-output", type=Path, default=DEFAULT_ENVELOPE)
    return parser.parse_args()


def write_envelope(
    public_bytes: bytes,
    output: Path,
    *,
    artifact_path: str,
) -> dict[str, object]:
    try:
        from scripts.validate_public_artifact_envelopes import (
            build_envelope_from_public_artifact,
        )
    except ModuleNotFoundError:  # Direct execution
        from validate_public_artifact_envelopes import (  # type: ignore[no-redef]
            build_envelope_from_public_artifact,
        )

    envelope = build_envelope_from_public_artifact(
        artifact_path=artifact_path,
        public_bytes=public_bytes,
        producer_manifest_path=E4_PRODUCER_MANIFEST,
        claim_ids=[],
        evidence_ids=[],
        gate_verdict_paths=[],
        generator_version=E4_GENERATOR_VERSION,
        included_fields=list(PUBLIC_CELL_FIELDS),
        public_safety_classification="public_safe_appendix",
        public_safety_notes=(
            "Public-safe E4 appendix metrics. Raw function tables and input "
            "lists remain omitted; raw-source bytes are validated by embedded "
            "receipt only."
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return envelope


def main() -> int:
    args = parse_args()
    raw_bytes = args.input.read_bytes()
    public_artifact = build_public_artifact(raw_bytes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    public_text = json.dumps(public_artifact, indent=2, sort_keys=True) + "\n"
    args.output.write_text(public_text, encoding="utf-8")
    try:
        artifact_path = str(args.output.resolve().relative_to(ROOT))
    except ValueError:
        artifact_path = str(DEFAULT_OUTPUT.relative_to(ROOT))
    envelope = write_envelope(
        public_text.encode("utf-8"),
        args.envelope_output,
        artifact_path=artifact_path,
    )
    print(
        f"Wrote {args.output} "
        f"({public_artifact['coverage']['exported_cells']} cells)"
    )
    print(f"Wrote {args.envelope_output} ({envelope['artifact_sha256'][:12]}…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
