#!/usr/bin/env python3
"""Export the complete E5 run as compact public-safe JSON and Markdown."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT / "artifacts" / "commitment_surface" / "e5_generator_vs_coverage.json"
)
RESULTS_DIR = ROOT / "experiments" / "commitment_surface" / "results"
DEFAULT_JSON = RESULTS_DIR / "e5_generator_vs_coverage.json"
DEFAULT_MARKDOWN = RESULTS_DIR / "e5_generator_vs_coverage.md"
DEFAULT_ENVELOPE = RESULTS_DIR / "e5_generator_vs_coverage.json.envelope.json"
E5_PRODUCER_MANIFEST = (
    "experiments/commitment_surface/experiment_manifest.json"
)
E5_GENERATOR_VERSION = "commitment_surface.e5_public_export.v1"
PAPER = ROOT / "papers" / "commitment_surface" / "paper.md"
ABSTRACT_MARKERS = ("<!-- E5_ABSTRACT_START -->", "<!-- E5_ABSTRACT_END -->")
CLAIM_MARKERS = (
    "<!-- E5_CLAIM_UPDATE_START -->",
    "<!-- E5_CLAIM_UPDATE_END -->",
)

PUBLIC_CELL_FIELDS = (
    "cell_id",
    "arm",
    "size",
    "n",
    "seed",
    "offset",
    "canonical_ood_accuracy",
    "canonical_ood_nll",
    "paraphrase_ood_accuracy",
    "paraphrase_ood_nll",
    "novel_k_equivariance_accuracy",
    "canonical_normalized_patch_ce",
    "paraphrase_normalized_patch_ce",
    "full_adapter_disable_ce",
    "final_supervised_loss",
    "final_consistency_loss",
    "exposure_integrity_pass",
    "patch_integrity_pass",
    "integrity_pass",
    "worker_elapsed_seconds",
)

METRICS = (
    "canonical_ood_accuracy",
    "paraphrase_ood_accuracy",
    "novel_k_equivariance_accuracy",
    "canonical_normalized_patch_ce",
    "paraphrase_normalized_patch_ce",
)


def _select(source: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: source[field] for field in fields if field in source}


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def build_public_artifact(raw_bytes: bytes) -> dict[str, Any]:
    raw = json.loads(raw_bytes)
    analysis = raw["analysis"]
    cells = raw["cells"]
    grid = analysis["grid_audit"]
    if not analysis.get("confirmatory_ready"):
        raise ValueError("E5 result is not confirmatory-ready")
    if not grid.get("grid_complete") or not grid.get("cell_data_complete"):
        raise ValueError("E5 Cartesian grid or cell metrics are incomplete")
    if len(cells) != 135 or analysis.get("n_cells") != 135:
        raise ValueError(f"expected 135 E5 cells, found {len(cells)}")
    if not all(cell.get("integrity_pass") is True for cell in cells):
        raise ValueError("E5 contains an integrity-failed cell")

    public_cells = [_select(cell, PUBLIC_CELL_FIELDS) for cell in cells]
    return {
        "schema_version": 1,
        "description": (
            "Public-safe E5 confirmatory aggregate and per-cell metrics. "
            "Prompts, support lists, model internals, and spectral module "
            "details are intentionally omitted."
        ),
        "source": {
            "artifact": "artifacts/commitment_surface/e5_generator_vs_coverage.json",
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "bytes": len(raw_bytes),
            "manifest_id": raw["manifest"]["manifest_id"],
            "implementation_fingerprint": raw["manifest"][
                "implementation_fingerprint"
            ],
            "public_safe_export": True,
        },
        "coverage": {
            "expected_cells": 135,
            "exported_cells": len(public_cells),
            "complete": True,
            "omitted_raw_fields": sorted(set(cells[0]) - set(PUBLIC_CELL_FIELDS)),
        },
        "config": _json_safe(raw["config"]),
        "analysis": _json_safe(analysis),
        "cells": public_cells,
    }


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if value is None:
        return "not evaluated"
    return f"{float(value):.3f}"


def render_markdown(public: dict[str, Any]) -> str:
    analysis = public["analysis"]
    verdict = analysis["verdict"]
    claim = {
        "generator_learning": (
            "Train-support-only generator regularization survives the frozen "
            "coverage, group-specificity, patch, and transport controls."
        ),
        "coverage": (
            "The E4 lift is best explained by correctly labeled deployment-"
            "support coverage; the transportable-generator interpretation is "
            "materially weakened."
        ),
        "mixed": (
            "Both generator regularization and labeled coverage contribute; "
            "neither single-mechanism interpretation is sufficient."
        ),
        "kill_or_draw": (
            "The frozen test supports neither the generator-learning nor the "
            "coverage-only mechanism claim."
        ),
    }.get(verdict, "No confirmatory mechanism claim is permitted.")

    lines = [
        "# E5 — Generator Learning vs Labeled Orbit Coverage",
        "",
        f"**Strict verdict: `{verdict}`.**",
        "",
        claim,
        "",
        "## Per-arm confirmatory means",
        "",
        "| Arm | Canonical OOD | Paraphrase OOD | Novel-k equivariance | "
        "Canonical patch-CE | Paraphrase patch-CE |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for arm in ("G-reg", "B-ref", "W-reg", "Cov", "A-ref"):
        metrics = analysis["per_arm"][arm]
        lines.append(
            f"| {arm} | " + " | ".join(_fmt(metrics[metric]) for metric in METRICS)
            + " |"
        )
    lines.extend(
        [
            "",
            "## Frozen gates",
            "",
            f"- Exact 135-cell grid and integrity: "
            f"**{_fmt(analysis['confirmatory_ready'])}**.",
            f"- Generator-learning gate: "
            f"**{_fmt(analysis['generator_learning_gate'])}**.",
            f"- Coverage gate: **{_fmt(analysis['coverage_gate'])}**.",
            f"- Mixed-mechanism gate: **{_fmt(analysis['mixed_gate'])}**.",
            f"- Group-specificity gate: "
            f"**{_fmt(analysis['group_specificity_gate'])}**.",
            f"- Transport gate: **{_fmt(analysis['transport_gate'])}**.",
            "",
            "## Key contrasts",
            "",
            f"- G-reg − A-ref canonical OOD: "
            f"`{_fmt(analysis['canonical_G_minus_A'])}`.",
            f"- G-reg − Cov canonical OOD: "
            f"`{_fmt(analysis['canonical_G_minus_Cov'])}`.",
            f"- G-reg − A-ref novel-k equivariance: "
            f"`{_fmt(analysis['novel_k_G_minus_A'])}`.",
            f"- Paraphrase lift retained: "
            f"`{_fmt(analysis['paraphrase_lift_retained'])}`.",
            "",
            "## Claim boundary",
            "",
            "This result adjudicates the frozen Pythia modular-addition E5 "
            "mechanism contrast. It does not establish the same mechanism in "
            "language, vision, other groups, or open-world deployment.",
            "",
            f"Source manifest: `{public['source']['manifest_id']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def _replace_marked_block(
    text: str, markers: tuple[str, str], replacement: str
) -> str:
    start, end = markers
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"expected exactly one marker pair: {markers}")
    before, remainder = text.split(start, maxsplit=1)
    _, after = remainder.split(end, maxsplit=1)
    return f"{before}{start}\n{replacement.strip()}\n{end}{after}"


def update_paper(public: dict[str, Any], paper_text: str) -> str:
    analysis = public["analysis"]
    verdict = analysis["verdict"]
    g = analysis["per_arm"]["G-reg"]
    cov = analysis["per_arm"]["Cov"]
    b_ref = analysis["per_arm"]["B-ref"]
    abstract = (
        f"The exact 135-cell E5 grid returns strict verdict **{verdict}**: "
        f"G-reg/Cov/B-ref mean canonical OOD is "
        f"{g['canonical_ood_accuracy']:.3f}/"
        f"{cov['canonical_ood_accuracy']:.3f}/"
        f"{b_ref['canonical_ood_accuracy']:.3f}; "
        f"generator/coverage/transport gates are "
        f"{analysis['generator_learning_gate']}/"
        f"{analysis['coverage_gate']}/"
        f"{analysis['transport_gate']}."
    )
    interpretation = {
        "generator_learning": (
            "E5 resolves the labeled-support confound in favor of the "
            "commitment-first mechanism on this frozen grid: train-support-only "
            "generator regularization beats coverage, transfers to novel shifts "
            "and paraphrases, and survives normalized patching."
        ),
        "coverage": (
            "E5 resolves the frozen mechanism contrast in favor of labeled "
            "coverage: train-support-only generator regularization remains near "
            "the readout baseline while coverage-matched labels perform with the "
            "E4-style orbit-label arm. This materially weakens the claim that E4 "
            "demonstrated a transportable generator; E4 remains evidence that "
            "aligned labeled intervention beats post-hoc readout selection."
        ),
        "mixed": (
            "E5 supports a mixed mechanism on this grid: both train-support-only "
            "generator regularization and labeled coverage contribute, so neither "
            "the generator-only nor coverage-only reading is sufficient."
        ),
        "kill_or_draw": (
            "E5 supports neither frozen mechanism claim. The paper therefore "
            "retains E4's directional intervention result but withdraws any "
            "mechanism attribution between transportable generator and coverage."
        ),
    }[verdict]
    claim = (
        f"**E5 confirmatory verdict: {verdict}.** {interpretation} "
        f"Mean canonical OOD for G-reg/Cov/B-ref/A-ref is "
        f"{g['canonical_ood_accuracy']:.3f}/"
        f"{cov['canonical_ood_accuracy']:.3f}/"
        f"{b_ref['canonical_ood_accuracy']:.3f}/"
        f"{analysis['per_arm']['A-ref']['canonical_ood_accuracy']:.3f}. "
        f"Generator, coverage, group-specificity, and transport gates are "
        f"{analysis['generator_learning_gate']}, "
        f"{analysis['coverage_gate']}, "
        f"{analysis['group_specificity_gate']}, and "
        f"{analysis['transport_gate']}, respectively. The claim remains bounded "
        "to the frozen Pythia modular-addition grid."
    )
    updated = _replace_marked_block(paper_text, ABSTRACT_MARKERS, abstract)
    return _replace_marked_block(updated, CLAIM_MARKERS, claim)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--envelope-output", type=Path, default=DEFAULT_ENVELOPE)
    parser.add_argument("--paper", type=Path, default=PAPER)
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
        producer_manifest_path=E5_PRODUCER_MANIFEST,
        claim_ids=["COMMITMENT_GENERATOR_GENERALIZATION"],
        evidence_ids=["EVID-COMMITMENT-E5-COVERAGE"],
        gate_verdict_paths=[
            "experiments/commitment_surface/results/gate_verdicts/e5_strict_coverage.json"
        ],
        generator_version=E5_GENERATOR_VERSION,
        included_fields=list(PUBLIC_CELL_FIELDS),
        public_safety_notes=(
            "Public-safe E5 confirmatory aggregate and per-cell metrics. "
            "Raw prompts, support lists, and model internals remain omitted; "
            "raw-source bytes are validated by embedded receipt only."
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return envelope


def main() -> int:
    args = parse_args()
    public = build_public_artifact(args.input.read_bytes())
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    public_text = json.dumps(public, indent=2, sort_keys=True) + "\n"
    args.json_output.write_text(public_text, encoding="utf-8")
    args.markdown_output.write_text(render_markdown(public), encoding="utf-8")
    try:
        artifact_path = str(args.json_output.resolve().relative_to(ROOT))
    except ValueError:
        artifact_path = str(DEFAULT_JSON.relative_to(ROOT))
    envelope = write_envelope(
        public_text.encode("utf-8"),
        args.envelope_output,
        artifact_path=artifact_path,
    )
    args.paper.write_text(
        update_paper(public, args.paper.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print(f"Wrote {args.json_output} ({len(public['cells'])} cells)")
    print(f"Wrote {args.markdown_output}")
    print(f"Wrote {args.envelope_output} ({envelope['artifact_sha256'][:12]}…)")
    print(f"Updated {args.paper}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
