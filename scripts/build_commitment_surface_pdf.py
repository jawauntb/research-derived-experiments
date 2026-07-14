#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the commitment-surface paper PDF.

Reads:
- papers/commitment_surface/paper.md
- papers/commitment_surface/figures/*.png (produced by
  scripts/make_commitment_surface_figures.py)
- experiments/commitment_surface/results/*.json for embedded result and
  appendix tables (local artifacts are fallback inputs only)

Writes:
- papers/commitment_surface/paper.pdf
- papers/pdf/commitment_surface.pdf (copy)

Run:
    .venv/bin/python scripts/make_commitment_surface_figures.py
    .venv/bin/python scripts/build_commitment_surface_pdf.py
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Image,
    LongTable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "papers" / "commitment_surface"
PAPER_MD = PAPER_DIR / "paper.md"
FIG_DIR = PAPER_DIR / "figures"
OUT_PDF = PAPER_DIR / "paper.pdf"
COPY_PDF = ROOT / "papers" / "pdf" / "commitment_surface.pdf"

E1_JSON = ROOT / "experiments" / "commitment_surface" / "results" / "e1_concern_weighted.json"
E1_VARIANCE_JSON = (
    ROOT / "experiments" / "commitment_surface" / "results"
    / "e1_misspecification_variance.json"
)
E2E3_JSON = ROOT / "experiments" / "commitment_surface" / "results" / "e2_e3_neural.json"
E7_JSON = (
    ROOT / "experiments" / "commitment_surface" / "results"
    / "e7_selective_subspace_2026_07_13.json"
)
E4_JSON_CANDIDATES = [
    ROOT
    / "experiments"
    / "commitment_surface"
    / "results"
    / "e4_pythia_lora_v2_appendix.json",
    ROOT / "artifacts" / "commitment_surface" / "e4_pythia_lora_v2.json",
    ROOT / "artifacts" / "commitment_surface" / "e4_smoke.json",
]
E5_JSON = (
    ROOT / "experiments" / "commitment_surface" / "results"
    / "e5_generator_vs_coverage.json"
)
APPENDIX_TABLE_MARKER = "<!-- APPENDIX_A2_TABLES -->"


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title", parent=base["Title"], fontName="Times-Bold", fontSize=19,
            leading=22, alignment=TA_CENTER, spaceAfter=6,
            textColor=colors.HexColor("#111827"),
        ),
        "Meta": ParagraphStyle(
            "Meta", parent=base["BodyText"], fontName="Times-Roman", fontSize=10,
            leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#4b5563"),
            spaceAfter=2,
        ),
        "H2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Times-Bold", fontSize=12.6,
            leading=14, spaceBefore=9, spaceAfter=4,
            textColor=colors.HexColor("#111827"),
        ),
        "H3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName="Times-Bold", fontSize=11,
            leading=13, spaceBefore=6, spaceAfter=3,
            textColor=colors.HexColor("#1f2937"),
        ),
        "Body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Times-Roman", fontSize=9.4,
            leading=12.0, spaceAfter=4.2, alignment=TA_LEFT,
        ),
        "Bullet": ParagraphStyle(
            "Bullet", parent=base["BodyText"], fontName="Times-Roman", fontSize=9.1,
            leading=11.4, leftIndent=14, firstLineIndent=-8, spaceAfter=2.4,
        ),
        "Code": ParagraphStyle(
            "Code", parent=base["Code"], fontName="Courier", fontSize=7.7,
            leading=9.4, leftIndent=10, rightIndent=10, spaceBefore=3,
            spaceAfter=5, backColor=colors.HexColor("#f8fafc"),
            borderColor=colors.HexColor("#d1d5db"), borderWidth=0.4,
            borderPadding=5,
        ),
        "Caption": ParagraphStyle(
            "Caption", parent=base["BodyText"], fontName="Times-Italic",
            fontSize=8.2, leading=10, alignment=TA_CENTER,
            textColor=colors.HexColor("#4b5563"), spaceBefore=2, spaceAfter=7,
        ),
        "Ref": ParagraphStyle(
            "Ref", parent=base["BodyText"], fontName="Times-Roman", fontSize=8.3,
            leading=10.2, leftIndent=14, firstLineIndent=-14, spaceAfter=2.2,
        ),
    }


def inline_markup(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", text)
    return text


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(inline_markup(text), style)


def add_image(flow: list[Any], image_path: Path, caption: str,
              st: dict[str, ParagraphStyle], width_in: float = 6.4) -> None:
    if not image_path.exists():
        flow.append(para(f"[missing figure: {image_path.name}]", st["Body"]))
        return
    try:
        from PIL import Image as PILImage
        with PILImage.open(image_path) as im:
            w, h = im.size
    except Exception:
        w, h = 800, 400
    iw = width_in * inch
    flow.append(Spacer(1, 3))
    flow.append(Image(str(image_path), width=iw, height=iw * h / w))
    if caption:
        flow.append(para(caption, st["Caption"]))


def _table_style(header_rows: int = 1) -> TableStyle:
    return TableStyle([
        ("FONT", (0, 0), (-1, -1), "Times-Roman", 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.7,
         colors.HexColor("#111827")),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.HexColor("#111827")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("FONT", (0, 0), (-1, header_rows - 1), "Times-Bold", 8.6),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1),
         colors.HexColor("#2b6cb0")),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1),
         [colors.white, colors.HexColor("#f4f6f9")]),
    ])


def flush_paragraph(lines: list[str], flow: list[Any],
                    st: dict[str, ParagraphStyle]) -> None:
    if not lines:
        return
    text = " ".join(line.strip() for line in lines if line.strip())
    if text:
        flow.append(para(text, st["Body"]))
    lines.clear()


def flush_list(items: list[str], flow: list[Any],
               st: dict[str, ParagraphStyle]) -> None:
    if not items:
        return
    for item in items:
        flow.append(para("- " + item, st["Bullet"]))
    flow.append(Spacer(1, 2))
    items.clear()


def markdown_to_flow(text: str, st: dict[str, ParagraphStyle]) -> list[Any]:
    flow: list[Any] = []
    para_lines: list[str] = []
    list_items: list[str] = []
    code_lines: list[str] = []
    in_code = False
    title_seen = False

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                flow.append(Preformatted("\n".join(code_lines), st["Code"]))
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph(para_lines, flow, st)
                flush_list(list_items, flow, st)
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith("<!--"):
            # Skip HTML comments -- they are placeholder markers for the
            # results injector.
            continue
        if not line.strip():
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            continue
        if line.startswith("# "):
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            if title_seen:
                flow.append(PageBreak())
            title_seen = True
            flow.append(para(line[2:].strip(), st["Title"]))
            continue
        if line.startswith("**Author.**") or line.startswith("**Status.**"):
            flush_paragraph(para_lines, flow, st)
            flow.append(Paragraph(inline_markup(line), st["Meta"]))
            continue
        if line.startswith("## "):
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            flow.append(para(line[3:].strip(), st["H2"]))
            continue
        if line.startswith("### "):
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            flow.append(para(line[4:].strip(), st["H3"]))
            continue
        image_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if image_match:
            flush_paragraph(para_lines, flow, st)
            flush_list(list_items, flow, st)
            add_image(flow, PAPER_DIR / image_match.group(2),
                      image_match.group(1), st)
            continue
        if re.match(r"^\d+\. ", line):
            flush_paragraph(para_lines, flow, st)
            list_items.append(re.sub(r"^\d+\. ", "", line).strip())
            continue
        if line.startswith("- "):
            flush_paragraph(para_lines, flow, st)
            list_items.append(line[2:].strip())
            continue
        para_lines.append(line)

    flush_paragraph(para_lines, flow, st)
    flush_list(list_items, flow, st)
    return flow


def _fmt(x: float, precision: int = 3) -> str:
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "yes" if x else "no"
    return f"{x:.{precision}f}"


def _appendix_table(rows: list[list[str]], col_widths: list[float]) -> LongTable:
    table = LongTable(
        rows,
        colWidths=col_widths,
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Times-Roman", 6.4),
        ("FONT", (0, 0), (-1, 0), "Times-Bold", 6.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#111827")),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#111827")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f4f6f9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
    ]))
    return table


def build_appendix_flow(st: dict[str, ParagraphStyle]) -> list[Any]:
    """Build Appendix A.2 from committed public-safe result artifacts."""
    flow: list[Any] = []

    if E1_JSON.exists():
        e1 = json.loads(E1_JSON.read_text(encoding="utf-8"))
        cells = sorted(e1["cells"], key=lambda cell: (cell["modulus"], cell["seed"]))
        flow.append(para(
            f"**A.2.1 E1.** All {len(cells)} concern-weighted selector "
            "cells from `experiments/commitment_surface/results/"
            "e1_concern_weighted.json`.",
            st["Body"],
        ))
        rows = [["n", "Seed", "Unweighted", "Well-spec", "Misspec", "Loss", "Truth"]]
        rows.extend([
            [
                str(cell["modulus"]),
                str(cell["seed"]),
                _fmt(cell["unweighted_selector_acc"]),
                _fmt(cell["concern_wellspec_selector_acc"]),
                _fmt(cell["concern_misspec_selector_acc"]),
                _fmt(cell["loss_selector_acc"]),
                _fmt(cell["truth_selector_acc"]),
            ]
            for cell in cells
        ])
        flow.append(_appendix_table(
            rows,
            [0.45 * inch, 0.55 * inch, 0.95 * inch, 0.9 * inch,
             0.85 * inch, 0.75 * inch, 0.75 * inch],
        ))
        flow.append(PageBreak())
    else:
        flow.append(para("E1 per-cell source unavailable.", st["Body"]))

    if E2E3_JSON.exists():
        e2e3 = json.loads(E2E3_JSON.read_text(encoding="utf-8"))
        cells = sorted(
            e2e3["all_rows"],
            key=lambda cell: (
                cell["modulus"],
                cell["train_frac"],
                cell["seed"],
                cell["arm"],
            ),
        )
        flow.append(para(
            f"**A.2.2 E2/E3.** All {len(cells)} trained neural cells. "
            "E2 arm comparisons and E3 correlations use this same committed "
            "cell population from `experiments/commitment_surface/results/"
            "e2_e3_neural.json`.",
            st["Body"],
        ))
        rows = [[
            "Arm", "n", "Seed", "Train frac", "OOD", "Patch-CE",
            "Wrong patch", "Weakness",
        ]]
        rows.extend([
            [
                cell["arm"],
                str(cell["modulus"]),
                str(cell["seed"]),
                _fmt(cell["train_frac"], 2),
                _fmt(cell["ood_accuracy"]),
                _fmt(cell["patch_ce_delta"]),
                _fmt(cell["patch_ce_delta_wrong"]),
                _fmt(cell["weakness_true"]),
            ]
            for cell in cells
        ])
        flow.append(_appendix_table(
            rows,
            [0.4 * inch, 0.35 * inch, 0.8 * inch, 0.7 * inch,
             0.65 * inch, 0.75 * inch, 0.85 * inch, 0.7 * inch],
        ))
        flow.append(PageBreak())
    else:
        flow.append(para("E2/E3 per-cell source unavailable.", st["Body"]))

    e4_json = next((path for path in E4_JSON_CANDIDATES if path.exists()), None)
    if e4_json is not None:
        e4 = json.loads(e4_json.read_text(encoding="utf-8"))
        size_order = {"70m": 0, "160m": 1, "410m": 2}
        cells = sorted(
            e4["cells"],
            key=lambda cell: (
                size_order.get(cell["size"], 99),
                cell["n"],
                cell["seed"],
                cell["arm"],
            ),
        )
        coverage = e4.get("coverage", {})
        unavailable = coverage.get("unavailable_fields", [])
        availability = (
            "No requested appendix fields are unavailable."
            if not unavailable
            else "Unavailable fields: " + ", ".join(unavailable) + "."
        )
        flow.append(para(
            f"**A.2.3 E4.** All {len(cells)} Pythia LoRA cells from "
            f"`{e4_json.relative_to(ROOT)}`. "
            f"{availability}",
            st["Body"],
        ))
        rows = [[
            "Size", "Arm", "n", "Seed", "OOD", "Ablated OOD",
            "Patch-CE", "Weakness", "Wrong group",
        ]]
        rows.extend([
            [
                cell["size"],
                cell["arm"],
                str(cell["n"]),
                str(cell["seed"]),
                _fmt(cell["ood_accuracy"]),
                _fmt(cell["ablated_ood_accuracy"]),
                _fmt(cell["patch_ce_delta"]),
                _fmt(cell["weakness_oracle_norm"]),
                _fmt(cell["weakness_wrong_group_norm"]),
            ]
            for cell in cells
        ])
        flow.append(_appendix_table(
            rows,
            [0.55 * inch, 0.35 * inch, 0.35 * inch, 0.75 * inch,
             0.55 * inch, 0.75 * inch, 0.65 * inch, 0.65 * inch,
             0.7 * inch],
        ))
    else:
        flow.append(para(
            "E4 per-cell fields are unavailable: neither the committed "
            "public-safe appendix artifact nor a local raw/smoke artifact exists.",
            st["Body"],
        ))

    if E5_JSON.exists():
        e5 = json.loads(E5_JSON.read_text(encoding="utf-8"))
        size_order = {"70m": 0, "160m": 1, "410m": 2}
        cells = sorted(
            e5["cells"],
            key=lambda cell: (
                size_order.get(cell["size"], 99),
                cell["n"],
                cell["seed"],
                cell["arm"],
            ),
        )
        flow.append(PageBreak())
        flow.append(para(
            f"**A.2.4 E5.** All {len(cells)} confirmatory generator-versus-"
            "coverage cells from the committed public-safe result artifact.",
            st["Body"],
        ))
        rows = [[
            "Size", "Arm", "n", "Seed", "OOD", "Paraphrase",
            "Novel-k", "Patch-CE", "Para patch",
        ]]
        rows.extend([
            [
                cell["size"],
                cell["arm"],
                str(cell["n"]),
                str(cell["seed"]),
                _fmt(cell["canonical_ood_accuracy"]),
                _fmt(cell["paraphrase_ood_accuracy"]),
                _fmt(cell["novel_k_equivariance_accuracy"]),
                _fmt(cell["canonical_normalized_patch_ce"]),
                _fmt(cell["paraphrase_normalized_patch_ce"]),
            ]
            for cell in cells
        ])
        flow.append(_appendix_table(
            rows,
            [0.5 * inch, 0.5 * inch, 0.3 * inch, 0.7 * inch,
             0.5 * inch, 0.65 * inch, 0.55 * inch, 0.65 * inch,
             0.65 * inch],
        ))

    if E7_JSON.exists():
        e7 = json.loads(E7_JSON.read_text(encoding="utf-8"))
        flow.append(Spacer(1, 8))
        flow.append(para(
            f"**A.2.5 E7.** Public-safe aggregates from "
            f"{e7['valid_streams']} of 32 budget-valid streams. The timing "
            "gate invalidates the confirmatory run; these rows are diagnostic, "
            "not a scientific verdict. Raw checkpoints remain gitignored.",
            st["Body"],
        ))
        rows = [[
            "Width", "Arm", "Streams", "Retained OOD", "Patch/mass",
            "Final OOD", "Eff. rank", "Dead frac",
        ]]
        rows.extend([
            [
                str(row["width"]),
                row["arm"],
                str(row["valid_streams"]),
                _fmt(row["retained_ood_accuracy"], 4),
                _fmt(row["earlier_patch_ce_per_mass"], 4),
                _fmt(row["final_task_ood_accuracy"], 4),
                _fmt(row["effective_rank"], 2),
                _fmt(row["dead_unit_fraction"], 4),
            ]
            for row in e7["summary"]
        ])
        flow.append(_appendix_table(
            rows,
            [0.5 * inch, 0.65 * inch, 0.6 * inch, 0.8 * inch,
             0.8 * inch, 0.7 * inch, 0.7 * inch, 0.7 * inch],
        ))

    return flow


def build_results_flow(st: dict[str, ParagraphStyle]) -> list[Any]:
    """Assemble the concrete results section from JSONs + figures."""
    flow: list[Any] = []
    flow.append(para("5. Results", st["H2"]))
    flow.append(para(
        "Numbers are the pre-registered summary metrics from each "
        "experiment's committed JSON. Every table can be regenerated via "
        "`scripts/make_commitment_surface_figures.py` followed by "
        "`scripts/build_commitment_surface_pdf.py`.",
        st["Body"],
    ))

    # --- E1 ---
    flow.append(para("5.1 E1 — Concern-weighted selector", st["H3"]))
    if E1_JSON.exists():
        e1 = json.loads(E1_JSON.read_text())["summary"]
        e1_variance = json.loads(E1_VARIANCE_JSON.read_text())
        add_image(flow, FIG_DIR / "fig1_e1_selectors.png",
                  "Figure 1. Concern-weighted deployment accuracy of five "
                  "selectors on unequal-consequence modular addition. "
                  "Well-specified concern beats unweighted Bennett by "
                  f"+{e1['gap_wellspec_vs_unweighted']:.3f}; misspecified "
                  "concern is slightly *below* unweighted "
                  f"({e1['gap_misspec_vs_unweighted']:.3f}). The frozen "
                  "±0.05 equivalence gate fails; the separately "
                  "pre-registered randomization follow-up finds this gap "
                  "typical of the frozen design rather than systematic "
                  "anti-correlation.", st)
        table_data = [
            ["Selector", "Mean", "95% CI"],
            ["Concern-weighted (well-spec)",
             _fmt(e1["concern_wellspec"]["mean"]),
             f"[{_fmt(e1['concern_wellspec']['ci95_low'])}, "
             f"{_fmt(e1['concern_wellspec']['ci95_high'])}]"],
            ["Unweighted Bennett",
             _fmt(e1["unweighted"]["mean"]),
             f"[{_fmt(e1['unweighted']['ci95_low'])}, "
             f"{_fmt(e1['unweighted']['ci95_high'])}]"],
            ["Concern-weighted (misspec)",
             _fmt(e1["concern_misspec"]["mean"]),
             f"[{_fmt(e1['concern_misspec']['ci95_low'])}, "
             f"{_fmt(e1['concern_misspec']['ci95_high'])}]"],
            ["Train-loss selector",
             _fmt(e1["loss"]["mean"]),
             f"[{_fmt(e1['loss']['ci95_low'])}, "
             f"{_fmt(e1['loss']['ci95_high'])}]"],
            ["Truth (upper bound)",
             _fmt(e1["truth"]["mean"]),
             f"[{_fmt(e1['truth']['ci95_low'])}, "
             f"{_fmt(e1['truth']['ci95_high'])}]"],
        ]
        t = Table(table_data, colWidths=[2.6 * inch, 1.0 * inch, 1.8 * inch])
        t.setStyle(_table_style())
        flow.append(t)
        flow.append(Spacer(1, 4))
        flow.append(para(
            f"Cells: {e1['n_cells']}. Gate: well-spec vs unweighted "
            f"≥ 0.05 → **{_fmt(e1['gap_wellspec_vs_unweighted'])}** "
            f"(PASS = {_fmt(e1['commitment_first_pass_wellspec_beats_unweighted'])}). "
            f"Misspec vs unweighted within ±0.05 → "
            f"**{_fmt(e1['gap_misspec_vs_unweighted'])}** "
            f"(PASS = {_fmt(e1['commitment_first_pass_misspec_matches_unweighted'])}: "
            "outside the pre-registered equivalence band; this sub-gate "
            "strictly fails and remains failed).",
            st["Body"]))
        variance_null = e1_variance["null_distribution"]
        variance_gate = e1_variance["gate"]
        flow.append(para(
            "Timestamped E1 follow-up: 2,048 conditional randomization "
            "replicates give null mean gap "
            f"**{_fmt(variance_null['mean'], 4)}** (SD "
            f"{_fmt(variance_null['sd'], 4)}), with "
            f"P(Δ ≤ observed) = "
            f"**{_fmt(variance_null['probability_gap_le_observed'])}**. "
            f"Verdict: **{variance_gate['verdict']}**. All frozen "
            "independence/exchangeability checks pass. The score-level "
            "expectation identity therefore survives, but it does not "
            "commute through finite-pool argmax selection; see Section 3.5.",
            st["Body"]))
    else:
        flow.append(para("E1 result JSON not yet committed.", st["Body"]))

    # --- E2 / E3 ---
    flow.append(para("5.2 E2 — Compat augmentation vs weakness readout",
                     st["H3"]))
    if E2E3_JSON.exists():
        e2e3 = json.loads(E2E3_JSON.read_text())["summary"]
        add_image(flow, FIG_DIR / "fig2_e2_arms_ood.png",
                  "Figure 2. E2 arms on cyclic modular addition MLPs. "
                  "Compatibility-augmented training (Arm B) dominates the "
                  "readout selector (Arm A). Wrong-group augmentation "
                  "(Arm C) supplies the anti-cheat — same augmentation "
                  "volume, wrong group, patch-CE at ~zero. Left: OOD "
                  "accuracy. Right: patch-CE Δ under top-k "
                  "shift-equivariant unit ablation.", st)
        per_arm = e2e3["per_arm"]
        rows = [["Arm", "N selected", "OOD (mean)", "Patch-CE Δ",
                 "Weakness"]]
        for arm in ["A", "B", "C", "D"]:
            if arm not in per_arm:
                continue
            stats = per_arm[arm]
            rows.append([
                arm,
                str(stats["ood_accuracy"]["n"]),
                (f"{_fmt(stats['ood_accuracy']['mean'])} "
                 f"[{_fmt(stats['ood_accuracy']['ci95_low'])}, "
                 f"{_fmt(stats['ood_accuracy']['ci95_high'])}]"),
                _fmt(stats["patch_ce_delta"]["mean"]),
                _fmt(stats["weakness_true"]["mean"]),
            ])
        t = Table(rows, colWidths=[0.5 * inch, 0.9 * inch, 2.0 * inch,
                                    1.1 * inch, 1.0 * inch])
        t.setStyle(_table_style())
        flow.append(t)
        flow.append(Spacer(1, 4))
        b_patch = e2e3["per_arm"]["B"]["patch_ce_delta"]["mean"]
        a_patch = e2e3["per_arm"]["A"]["patch_ce_delta"]["mean"]
        c_patch = e2e3["per_arm"]["C"]["patch_ce_delta"]["mean"]
        flow.append(para(
            f"Total cells trained: {e2e3['n_total_cells']}. "
            f"Gate: B − A OOD gap ≥ 0.30 → "
            f"**{_fmt(e2e3['gap_B_minus_A_ood'])}** "
            f"(PASS = {_fmt(e2e3['e2_pass_B_beats_A_ood_0p3'])}). "
            f"B − A patch-CE gap ≥ 0.50 → "
            f"**{_fmt(e2e3['gap_B_minus_A_patch_ce'])}** "
            f"(PASS = {_fmt(e2e3['e2_pass_B_beats_A_patch_ce_0p5'])}). "
            f"B − C patch-CE gap = "
            f"{_fmt(e2e3['gap_B_minus_C_patch_ce'])} (anti-cheat: ~0 "
            "expected).",
            st["Body"]))
        flow.append(para(
            "Honest decomposition of the patch-CE gate: Arm B's absolute "
            f"patch-CE Δ is small (**{_fmt(b_patch)}**; Arm C "
            f"{_fmt(c_patch)}; B − C only "
            f"{_fmt(e2e3['gap_B_minus_C_patch_ce'])}), and the large "
            "B − A gap is mostly produced by Arm A's *negative* patch "
            f"score ({_fmt(a_patch)}). The result strongly supports "
            "\"B's mechanism differs from A's\" but only weakly supports "
            "\"B localizes a substantial mechanism in the top-k patched "
            "units\"; see the fixed-top-k power caveat in Section 6.5.",
            st["Body"]))
        flow.append(para("5.3 E3 — Patch-CE vs weakness as OOD predictor",
                         st["H3"]))
        add_image(flow, FIG_DIR / "fig3_e3_readout_vs_patch.png",
                  "Figure 3. Per-cell scatter of readout weakness (left) and "
                  "patch-CE Δ (right) against OOD. Colored by arm. Under a "
                  "generator-aligned probe group, weakness is a strong "
                  f"predictor (ρ={_fmt(e2e3['rho_weakness_ood'])}); "
                  "patch-CE is also strong "
                  f"(ρ={_fmt(e2e3['rho_patch_ce_ood'])}). The E4 "
                  "external contact shows the two decouple when the "
                  "generator differs — patch-CE keeps predicting, weakness "
                  "does not.", st)
    else:
        flow.append(para("E2/E3 result JSON not yet committed.", st["Body"]))

    # --- E4 ---
    flow.append(para("5.4 E4 — Pythia LoRA v2 external contact (Modal L4)",
                     st["H3"]))
    e4_json = next((p for p in E4_JSON_CANDIDATES if p.exists()), None)
    if e4_json is not None:
        e4 = json.loads(e4_json.read_text())
        analysis = e4["analysis"]
        add_image(flow, FIG_DIR / "fig4_e4_pythia_arms.png",
                  "Figure 4. E4 arms on Pythia 70m/160m/410m LoRA-fine-tuned "
                  "on modular addition (external contact). Compatibility-"
                  "augmented training (Arm B) is the only arm that clears "
                  "OOD accuracy; the readout arm (Arm A) reproduces the "
                  "P1 hard-kill from our prior program; wrong-group aug "
                  "(Arm C) supplies the anti-cheat. Weakness readout "
                  "(right panel) is uninformative across all arms.", st)
        per_arm = analysis["per_arm"]
        rows = [["Arm", "N", "OOD mean", "OOD max", "Patch-CE Δ",
                 "Weakness"]]
        for arm in ["A", "B", "C", "D"]:
            if arm not in per_arm:
                continue
            s = per_arm[arm]
            rows.append([
                arm,
                str(s["n"]),
                _fmt(s["ood_mean"]),
                _fmt(s["ood_max"]),
                _fmt(s["patch_ce_delta_mean"]),
                _fmt(s["weakness_mean"]),
            ])
        t = Table(rows, colWidths=[0.5 * inch, 0.5 * inch, 1.0 * inch,
                                    1.0 * inch, 1.3 * inch, 1.0 * inch])
        t.setStyle(_table_style())
        flow.append(t)
        flow.append(Spacer(1, 4))
        source_line = (
            f"Source: `{e4_json.relative_to(ROOT)}`."
        )
        if "smoke" in e4_json.name:
            source_line = (
                f"**SMOKE RUN (partial coverage)**: {source_line} "
                "Full sweep will replace this table when the Modal L4 job "
                "lands."
            )
        flow.append(para(source_line, st["Body"]))
        a_ood_mean = analysis["per_arm"].get("A", {}).get("ood_mean")
        flow.append(para(
            f"Cells: {analysis['n_cells']}. Gate (new frame): B mean "
            f"OOD ≥ 0.50, patch-CE ≥ 0.05, A mean OOD ≤ 0.10 → "
            f"**{_fmt(analysis.get('e4_new_frame_pass'))}**. Gate "
            f"(old frame): A mean OOD ≥ 0.50, ρ(weakness, OOD) ≥ 0.5 → "
            f"**{_fmt(analysis.get('e4_old_frame_pass'))}**. "
            f"ρ(patch-CE, OOD) = "
            f"{_fmt(analysis['rho_patch_ce_ood_all_cells'])}; "
            f"ρ(weakness, OOD) = "
            f"{_fmt(analysis['rho_weakness_ood_all_cells'])}.",
            st["Body"]))
        flow.append(para(
            "**Verdict: directionally decisive; strict pre-registered "
            "gate failed.** The A-mean-OOD ≤ 0.10 condition came in at "
            f"{_fmt(a_ood_mean)} and we record E4 as a gate failure by "
            "the standard this paper advocates (outlier accounting in "
            "Section 6.2 explains the miss; it does not convert it into "
            "a pass). Interpretation is further bounded by the "
            "label-exposure confound of Section 6.6: cyclic augmentation "
            "places correctly labeled examples on the held-out "
            "deployment support, so E4 alone cannot separate generator "
            "learning from labeled orbit coverage. E5 resolves that contrast "
            "below.",
            st["Body"]))
    else:
        flow.append(para("E4 result JSON not yet available.", st["Body"]))

    flow.append(para(
        "5.5 E5 — Generator learning vs labeled orbit coverage",
        st["H3"],
    ))
    if E5_JSON.exists():
        e5 = json.loads(E5_JSON.read_text(encoding="utf-8"))
        analysis = e5["analysis"]
        rows = [[
            "Arm", "OOD", "Paraphrase", "Novel-k", "Patch-CE", "Para patch",
        ]]
        for arm in ("G-reg", "B-ref", "W-reg", "Cov", "A-ref"):
            metrics = analysis["per_arm"][arm]
            rows.append([
                arm,
                _fmt(metrics["canonical_ood_accuracy"]),
                _fmt(metrics["paraphrase_ood_accuracy"]),
                _fmt(metrics["novel_k_equivariance_accuracy"]),
                _fmt(metrics["canonical_normalized_patch_ce"]),
                _fmt(metrics["paraphrase_normalized_patch_ce"]),
            ])
        table = Table(
            rows,
            colWidths=[
                0.7 * inch, 0.7 * inch, 0.9 * inch,
                0.75 * inch, 0.8 * inch, 0.85 * inch,
            ],
        )
        table.setStyle(_table_style())
        flow.append(table)
        flow.append(Spacer(1, 4))
        flow.append(para(
            f"Exact-grid integrity: **{_fmt(analysis['confirmatory_ready'])}**. "
            f"Strict verdict: **{analysis['verdict']}**. "
            f"Generator-learning gate: {_fmt(analysis['generator_learning_gate'])}; "
            f"coverage gate: {_fmt(analysis['coverage_gate'])}; "
            f"mixed gate: {_fmt(analysis['mixed_gate'])}; "
            f"group specificity: {_fmt(analysis['group_specificity_gate'])}; "
            f"transport: {_fmt(analysis['transport_gate'])}.",
            st["Body"],
        ))
        flow.append(para(
            "E5 is the severe follow-up to E4's labeled-support confound. "
            "Its mechanism verdict is restricted to this frozen Pythia modular-"
            "addition grid; Section 6.6 states the corresponding claim update.",
            st["Body"],
        ))
    else:
        flow.append(para(
            "Confirmatory E5 is running. No mechanism verdict is reported until "
            "the exact 135-cell grid passes integrity and is committed.",
            st["Body"],
        ))

    # --- E7 ---
    flow.append(para(
        "5.6 E7 — Selective load-bearing subspace protection",
        st["H3"],
    ))
    if E7_JSON.exists():
        e7 = json.loads(E7_JSON.read_text(encoding="utf-8"))
        if e7["status"] == "invalid":
            budget = e7["integrity"]["budget_detail"]
            add_image(
                flow,
                FIG_DIR / "fig6_e7_selective_subspace.png",
                "Figure 6. E7 confirmatory integrity audit. Six of 32 "
                "matched groups exceed the frozen 2% per-arm timing limit, "
                "leaving only 12 of 32 streams budget-valid and withholding "
                "all scientific gates.",
                st,
            )
            rows = [["Width", "Seed", "Task", "Timing range", "Gate"]]
            rows.extend([
                [
                    str(failure["key"][0]),
                    str(failure["key"][1]),
                    str(failure["key"][2]),
                    f"{failure['relative_wall_clock_range']:.2%}",
                    "FAIL",
                ]
                for failure in budget["failures"]
            ])
            table = Table(
                rows,
                colWidths=[0.8 * inch, 0.8 * inch, 0.8 * inch,
                           1.2 * inch, 0.8 * inch],
            )
            table.setStyle(_table_style())
            flow.append(table)
            flow.append(Spacer(1, 4))
            flow.append(para(
                "**Strict disposition: INVALID — no scientific verdict.** "
                "The original shared closing barrier made arm times nearly "
                "identical by construction. Re-audit with the already-recorded "
                "per-arm median-step estimator finds a maximum range of "
                f"{budget['max_relative_wall_clock_range']:.2%}. Seed, "
                "sequential-exposure, and exact-mass gates pass, but the frozen "
                "budget kill criterion fails; G1–G4 are not evaluated.",
                st["Body"],
            ))
        else:
            add_image(
                flow,
                FIG_DIR / "fig6_e7_selective_subspace.png",
                "Figure 6. E7 confirmatory continual-learning result. P_sub "
                "separates on the mechanism metric but not retained OOD.",
                st,
            )
            rows = [[
                "Width", "Arm", "Retained OOD", "Patch/mass", "Final OOD",
            ]]
            rows.extend([
                [
                    str(row["width"]),
                    row["arm"],
                    _fmt(row["retained_ood_accuracy"], 4),
                    _fmt(row["earlier_patch_ce_per_mass"], 4),
                    _fmt(row["final_task_ood_accuracy"], 4),
                ]
                for row in e7["summary"]
            ])
            table = Table(
                rows,
                colWidths=[0.7 * inch, 1.0 * inch, 1.15 * inch,
                           1.15 * inch, 1.0 * inch],
            )
            table.setStyle(_table_style())
            flow.append(table)
            flow.append(Spacer(1, 4))
            gate = e7["gate_analysis"]
            flow.append(para(
                f"**Strict verdict: {gate['strict_verdict']}.** See the "
                "committed public-safe report for frozen margins.",
                st["Body"],
            ))
    else:
        flow.append(para("E7 result JSON not yet available.", st["Body"]))

    flow.append(para("Frame-taxonomy schematic (Figure 5).", st["H3"]))
    add_image(flow, FIG_DIR / "fig5_frame_taxonomy.png",
              "Figure 5. The old-frame taxonomy of what structure means "
              "(footprint / selector / controller / anti-correlate) "
              "collapses into the new-frame primitive: load-bearing at a "
              "commitment surface Σ = (G_dep, C, T).", st)
    return flow


def _load_paper() -> str:
    return PAPER_MD.read_text(encoding="utf-8")


def _split_paper(text: str) -> tuple[str, str]:
    """Split at '## 5. Results' so the results section is injected from
    JSONs. Return (before_results, after_results)."""
    marker = "## 5. Results"
    idx = text.find(marker)
    if idx < 0:
        return text, ""
    end = text.find("## 6.", idx)
    if end < 0:
        end = len(text)
    return text[:idx], text[end:]


def _split_appendix_tables(text: str) -> tuple[str, str]:
    if APPENDIX_TABLE_MARKER not in text:
        raise ValueError(
            f"missing appendix marker {APPENDIX_TABLE_MARKER!r} in {PAPER_MD}"
        )
    before, after = text.split(APPENDIX_TABLE_MARKER, maxsplit=1)
    return before, after


def build_pdf() -> Path:
    st = styles()
    text = _load_paper()
    before, after = _split_paper(text)
    flow = markdown_to_flow(before, st)
    flow.extend(build_results_flow(st))
    before_appendix_tables, after_appendix_tables = _split_appendix_tables(after)
    flow.extend(markdown_to_flow(before_appendix_tables, st))
    flow.extend(build_appendix_flow(st))
    flow.extend(markdown_to_flow(after_appendix_tables, st))

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUT_PDF), pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.72 * inch, bottomMargin=0.72 * inch,
        title="The Commitment Surface",
        author="Jawaun Brown",
    )
    doc.build(flow)
    COPY_PDF.parent.mkdir(parents=True, exist_ok=True)
    COPY_PDF.write_bytes(OUT_PDF.read_bytes())
    return OUT_PDF


def main() -> int:
    out = build_pdf()
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
    print(f"Wrote {COPY_PDF} ({COPY_PDF.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
