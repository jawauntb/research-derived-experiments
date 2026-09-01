#!/usr/bin/env python3
"""Build the bounded Arc VCC fixture from Arc's official real H1 sample.

The pinned ~5 MB H5AD contains 600 real cells (five perturbations plus
non-targeting controls) and 1,000 genes. This script verifies the source bytes,
derives six preregistered mean-count log2-fold-change records, and retains only
the compact JSON ledger. It never downloads or executes STATE model artifacts.

Analysis-only dependency: ``pip install anndata``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.request
from pathlib import Path
from typing import Any

SOURCE_COMMIT = "ddfc5df73c997b2f113a560bd863fb068f2b453a"
SOURCE_URL = (
    "https://raw.githubusercontent.com/ArcInstitute/cell-eval2/"
    f"{SOURCE_COMMIT}/docs/data/H1-VCC-2025-training.h5ad"
)
SOURCE_SHA256 = "eb36c766cbf76353f9981cb3a3aa32137622d1de53b29d861c483742bcd4dec7"
SOURCE_BYTES = 4_991_092
RETRIEVAL_AT = "2026-09-01T22:22:00Z"
STATISTIC = "log2_fold_change_mean_raw_counts_pseudocount_1"
THRESHOLD = 0.25
EXPECTED_LABELS = {
    "MED12": 100,
    "SRC": 100,
    "STAT1": 100,
    "TET1": 100,
    "TMSB4X": 100,
    "non-targeting": 100,
}
# This list is the locked evaluation object. TMSB4X is the development control;
# the remaining rows were selected before adapter/rule tuning.
MEASUREMENT_PLAN = (
    ("TMSB4X", "TMSB4X", "development"),
    ("STAT1", "TAGLN", "locked_holdout"),
    ("STAT1", "HADHA", "locked_holdout"),
    ("MED12", "PODXL", "locked_holdout"),
    ("TET1", "TAGLN", "locked_holdout"),
    ("SRC", "TAGLN", "locked_holdout"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_source(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
            payload = response.read(SOURCE_BYTES + 1)
        if len(payload) != SOURCE_BYTES:
            raise ValueError(f"Arc source byte count changed: {len(payload)}")
        destination.write_bytes(payload)
    if (
        destination.stat().st_size != SOURCE_BYTES
        or sha256(destination) != SOURCE_SHA256
    ):
        raise ValueError("Arc source bytes do not match the pinned official sample")
    return destination


def _direction(value: float) -> str:
    if value > THRESHOLD:
        return "increases"
    if value < -THRESHOLD:
        return "decreases"
    return "null"


def derive_rows(source: Path) -> list[dict[str, Any]]:
    try:
        import anndata as ad
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Arc fixture derivation requires `pip install anndata`"
        ) from exc

    dataset = ad.read_h5ad(source)
    if dataset.shape != (600, 1000):
        raise ValueError(f"unexpected Arc sample shape: {dataset.shape}")
    if "target_gene" not in dataset.obs or not dataset.var_names.is_unique:
        raise ValueError("Arc sample is missing unique gene or perturbation identities")
    labels = dataset.obs["target_gene"].astype(str).to_numpy()
    counts = {label: int((labels == label).sum()) for label in sorted(set(labels))}
    if counts != EXPECTED_LABELS:
        raise ValueError(f"Arc sample label counts changed: {counts}")
    matrix = (
        dataset.X.toarray().astype(float)
        if hasattr(dataset.X, "toarray")
        else np.asarray(dataset.X, dtype=float)
    )
    if not np.isfinite(matrix).all() or (matrix < 0).any():
        raise ValueError("Arc sample must contain finite non-negative raw counts")
    control_mask = labels == "non-targeting"
    control_mean = matrix[control_mask].mean(axis=0)
    gene_index = {str(gene): index for index, gene in enumerate(dataset.var_names)}
    rows: list[dict[str, Any]] = []
    for ordinal, (perturbed_gene, response_gene, split) in enumerate(
        MEASUREMENT_PLAN, start=1
    ):
        if response_gene not in gene_index:
            raise ValueError(f"planned response gene disappeared: {response_gene}")
        perturbed_mask = labels == perturbed_gene
        index = gene_index[response_gene]
        perturbed_mean = float(matrix[perturbed_mask, index].mean())
        baseline_mean = float(control_mean[index])
        value = math.log2((perturbed_mean + 1.0) / (baseline_mean + 1.0))
        rows.append(
            {
                "measurement_id": f"arc-h1-real-{ordinal:03d}",
                "perturbed_gene": perturbed_gene,
                "response_gene": response_gene,
                "assay": "H1",
                "split": split,
                "summary_statistic": STATISTIC,
                "value": round(value, 12),
                "direction": _direction(value),
                "source_row": (
                    f"H1-VCC-2025-training.h5ad:target_gene={perturbed_gene};"
                    f"response_gene={response_gene};var_index={index}"
                ),
                "perturbed_cells": int(perturbed_mask.sum()),
                "control_cells": int(control_mask.sum()),
            }
        )
    return rows


def build_fixture(source: Path, destination: Path) -> dict[str, Any]:
    if sha256(source) != SOURCE_SHA256 or source.stat().st_size != SOURCE_BYTES:
        raise ValueError("Arc source bytes do not match the pinned official sample")
    rows = derive_rows(source)
    destination.mkdir(parents=True, exist_ok=True)
    ledger = destination / "measurements.jsonl"
    payload = "".join(
        json.dumps(row, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"
        for row in rows
    )
    ledger.write_text(payload, encoding="utf-8")
    metadata = {
        "world_id": "arc-vcc",
        "world_version": "2025-h1-measurements",
        "schema_version": "arc-vcc-measurement-ledger-0.1",
        "source_id": "arc-cell-eval2-h1-vcc-real-subset",
        "official_url": SOURCE_URL,
        "license": "MIT",
        "release": "cell-eval2 0.16.0 / H1-VCC-2025 real training subset",
        "retrieval_at": RETRIEVAL_AT,
        "measurement_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "raw_source_sha256": SOURCE_SHA256,
        "raw_source_bytes": SOURCE_BYTES,
        "source_commit": SOURCE_COMMIT,
        "row_count": len(rows),
        "assay": "H1",
        "statistic": STATISTIC,
        "threshold": THRESHOLD,
        "tuning_split": "development",
        "evaluation_split": "locked_holdout",
        "source_kind": "official_real_subset",
        "provenance_note": (
            "Six deterministic records derived from ArcInstitute/cell-eval2's "
            "committed real 600-cell H1 sample; no model predictions, STATE "
            "code, weights, or challenge answer files are included."
        ),
    }
    (destination / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    source = (
        args.source or args.destination.parent / "raw" / "H1-VCC-2025-training.h5ad"
    )
    if args.source is None:
        download_source(source)
    metadata = build_fixture(source, args.destination)
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
