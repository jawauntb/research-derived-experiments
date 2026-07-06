"""Regenerate and publish row ledgers for SCG phases 1-5."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    rows_to_records,
    summarize_rows,
)
from experiments.structure_compatible_generalization.modular_domain import (
    run_intervention_sweep,
)
from experiments.structure_compatible_generalization.phase3_learned_generators import (
    run_phase3_suite,
)
from experiments.structure_compatible_generalization.run_suite import run_suite
from experiments.structure_compatible_generalization.semantic_retrieval_transfer import (
    run_encoder_semantic_sweep,
    run_fixture_semantic_sweep,
)
from experiments.structure_compatible_generalization.template_language_domain import (
    run_language_template_sweep,
)

LEDGER_DIR = Path("experiments/structure_compatible_generalization/results/row_ledgers")
LEDGER_REPORT = Path(
    "experiments/structure_compatible_generalization/results/"
    "phase_row_ledgers_2026_07_06.md"
)
LEDGER_MANIFEST = Path(
    "experiments/structure_compatible_generalization/results/"
    "phase_row_ledgers_manifest_2026_07_06.json"
)


def _payload(kind: str, manifest: dict[str, Any], rows: list[DiagnosticRow]) -> dict[str, Any]:
    return {
        "kind": kind,
        "manifest": manifest,
        "summary": summarize_rows(rows),
        "rows": rows_to_records(rows),
    }


def build_phase_payloads(
    *,
    profile: str = "compact",
    base_seed: int = 20260706,
    device: str | None = None,
    semantic_fixture: bool = False,
) -> dict[str, dict[str, Any]]:
    if profile == "smoke":
        phase1 = run_suite(
            domains=["symbolic", "modular"],
            symbolic_models=4,
            vision_models=0,
            modular_models=4,
            symbolic_epochs=20,
            vision_epochs=20,
            modular_epochs=20,
            base_seed=base_seed,
            device=device,
            include_exact=True,
        )
        phase2_rows = run_intervention_sweep(
            n_configs=3,
            epochs=20,
            base_seed=base_seed,
            device=device,
            include_exact=True,
        )
        phase3_rows = run_phase3_suite(
            modular_configs=3,
            vision_base=1,
            modular_epochs=20,
            vision_epochs=20,
            base_seed=base_seed,
            device=device,
            include_exact=True,
        )
        phase4_rows = run_language_template_sweep(
            n_configs=3,
            epochs=20,
            base_seed=base_seed,
            device=device,
            include_exact=True,
        )
        phase5_rows = run_fixture_semantic_sweep(n_configs=4, base_seed=base_seed)
    elif profile == "compact":
        phase1 = run_suite(
            domains=["symbolic", "vision", "modular"],
            symbolic_models=24,
            vision_models=12,
            modular_models=24,
            symbolic_epochs=180,
            vision_epochs=60,
            modular_epochs=160,
            base_seed=base_seed,
            device=device,
            include_exact=True,
        )
        phase2_rows = run_intervention_sweep(
            n_configs=36,
            epochs=160,
            base_seed=base_seed,
            device=device,
            include_exact=True,
        )
        phase3_rows = run_phase3_suite(
            modular_configs=24,
            vision_base=10,
            modular_epochs=180,
            vision_epochs=110,
            base_seed=base_seed,
            device=device,
            include_exact=True,
        )
        phase4_rows = run_language_template_sweep(
            n_configs=28,
            epochs=180,
            base_seed=base_seed,
            device=device,
            include_exact=True,
        )
        phase5_rows = (
            run_fixture_semantic_sweep(n_configs=32, base_seed=base_seed)
            if semantic_fixture
            else run_encoder_semantic_sweep(n_configs=32, base_seed=base_seed)
        )
    else:
        raise ValueError(f"unknown row-ledger profile: {profile}")

    return {
        "phase1_l4": phase1,
        "phase2_transformations": _payload(
            "phase2 inferred transformations local row ledger",
            {
                "profile": profile,
                "n_configs": len(phase2_rows),
                "base_seed": base_seed,
                "device": device,
                "provenance": "local_regeneration",
            },
            phase2_rows,
        ),
        "phase3_learned_generators": _payload(
            "phase3 learned generators local row ledger",
            {
                "profile": profile,
                "n_rows": len(phase3_rows),
                "base_seed": base_seed,
                "device": device,
                "provenance": "local_regeneration",
            },
            phase3_rows,
        ),
        "phase4_language_templates": _payload(
            "phase4 language templates local row ledger",
            {
                "profile": profile,
                "n_rows": len(phase4_rows),
                "base_seed": base_seed,
                "device": device,
                "provenance": "local_regeneration",
            },
            phase4_rows,
        ),
        "phase5_semantic_retrieval": _payload(
            "phase5 semantic retrieval local row ledger",
            {
                "profile": profile,
                "n_rows": len(phase5_rows),
                "base_seed": base_seed,
                "device": device,
                "semantic_fixture": semantic_fixture,
                "provenance": "local_regeneration",
            },
            phase5_rows,
        ),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with path.open("w") as f:
        for row in rows:
            line = json.dumps(row, sort_keys=True)
            h.update(line.encode("utf-8"))
            h.update(b"\n")
            f.write(line + "\n")
    return h.hexdigest()


def write_ledgers(
    payloads: dict[str, dict[str, Any]],
    *,
    out_root: Path = Path("."),
) -> list[Path]:
    artifacts: dict[str, Any] = {}
    written: list[Path] = []
    for phase, payload in payloads.items():
        rows = list(payload["rows"])
        row_path = out_root / LEDGER_DIR / f"{phase}_rows_2026_07_06.jsonl"
        row_hash = _write_jsonl(row_path, rows)
        written.append(row_path)
        artifacts[row_path.relative_to(out_root).as_posix()] = {
            "rows": len(rows),
            "sha256": row_hash,
            "kind": payload["kind"],
            "manifest": payload.get("manifest", {}),
        }
    manifest = {
        "run_id": "phase_row_ledgers_2026_07_06",
        "artifact_type": "local_regenerated_row_ledgers",
        "claim_boundary": (
            "These ledgers provide row-level regenerated evidence for phases 1-5. "
            "They are not claimed to be byte-identical restorations of prior Modal payloads."
        ),
        "artifacts": artifacts,
    }
    manifest_path = out_root / LEDGER_MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    report_path = out_root / LEDGER_REPORT
    lines = [
        "# SCG Phase 1-5 Row Ledgers",
        "",
        "Date: 2026-07-06",
        "",
        "These are local regenerated row ledgers for the evidence-ladder phases.",
        "They are not byte-identical restorations of the original Modal payloads.",
        "",
        "| Phase | Rows | Artifact |",
        "| --- | ---: | --- |",
    ]
    for artifact, meta in artifacts.items():
        lines.append(f"| `{meta['kind']}` | {meta['rows']} | `{artifact}` |")
    report_path.write_text("\n".join(lines) + "\n")
    written.extend([manifest_path, report_path])
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["smoke", "compact"], default="compact")
    parser.add_argument("--base-seed", type=int, default=20260706)
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None)
    parser.add_argument("--semantic-fixture", action="store_true")
    parser.add_argument("--out-root", type=Path, default=Path("."))
    args = parser.parse_args()
    payloads = build_phase_payloads(
        profile=args.profile,
        base_seed=args.base_seed,
        device=args.device,
        semantic_fixture=args.semantic_fixture,
    )
    for path in write_ledgers(payloads, out_root=args.out_root):
        print(path)


if __name__ == "__main__":
    main()
