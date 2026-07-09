#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the commitment-surface paper PDF.

Reads:
- papers/commitment_surface/paper.md
- papers/commitment_surface/figures/*.png (produced by
  scripts/make_commitment_surface_figures.py)
- experiments/commitment_surface/results/*.json and
  artifacts/commitment_surface/*.json for embedded result tables

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
E2E3_JSON = ROOT / "experiments" / "commitment_surface" / "results" / "e2_e3_neural.json"
E4_JSON_CANDIDATES = [
    ROOT / "artifacts" / "commitment_surface" / "e4_pythia_lora_v2.json",
    ROOT / "artifacts" / "commitment_surface" / "e4_smoke.json",
]


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


def build_results_flow(st: dict[str, ParagraphStyle]) -> list[Any]:
    """Assemble the concrete results section from JSONs + figures."""
    flow: list[Any] = []
    flow.append(para("5. Results", st["H2"]))
    flow.append(para(
        "Numbers are the pre-registered summary metrics from each "
        "experiment's committed JSON. Every table can be regenerated via "
        "<font name='Courier'>scripts/make_commitment_surface_figures.py</font> "
        "followed by <font name='Courier'>scripts/build_commitment_surface_pdf.py</font>.",
        st["Body"],
    ))

    # --- E1 ---
    flow.append(para("5.1 E1 — Concern-weighted selector", st["H3"]))
    if E1_JSON.exists():
        e1 = json.loads(E1_JSON.read_text())["summary"]
        add_image(flow, FIG_DIR / "fig1_e1_selectors.png",
                  "Figure 1. Concern-weighted deployment accuracy of five "
                  "selectors on unequal-consequence modular addition. "
                  "Well-specified concern beats unweighted Bennett by "
                  f"+{e1['gap_wellspec_vs_unweighted']:.3f}; misspecified "
                  "concern is slightly *below* unweighted "
                  f"({e1['gap_misspec_vs_unweighted']:.3f}), confirming "
                  "the corollary that a random concern weighting is not "
                  "helpful.", st)
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
            f"≥ 0.05 → <b>{_fmt(e1['gap_wellspec_vs_unweighted'])}</b> "
            f"(PASS = {_fmt(e1['commitment_first_pass_wellspec_beats_unweighted'])}). "
            f"Misspec vs unweighted within ±0.05 → "
            f"<b>{_fmt(e1['gap_misspec_vs_unweighted'])}</b>.",
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
        flow.append(para(
            f"Total cells trained: {e2e3['n_total_cells']}. "
            f"Gate: B − A OOD gap ≥ 0.30 → "
            f"<b>{_fmt(e2e3['gap_B_minus_A_ood'])}</b> "
            f"(PASS = {_fmt(e2e3['e2_pass_B_beats_A_ood_0p3'])}). "
            f"B − A patch-CE gap ≥ 0.50 → "
            f"<b>{_fmt(e2e3['gap_B_minus_A_patch_ce'])}</b> "
            f"(PASS = {_fmt(e2e3['e2_pass_B_beats_A_patch_ce_0p5'])}). "
            f"B − C patch-CE gap = "
            f"{_fmt(e2e3['gap_B_minus_C_patch_ce'])} (anti-cheat: ~0 "
            "expected).",
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
            f"Source: <font name='Courier'>{e4_json.relative_to(ROOT)}</font>."
        )
        if "smoke" in e4_json.name:
            source_line = (
                f"<b>SMOKE RUN (partial coverage)</b>: {source_line} "
                "Full sweep will replace this table when the Modal L4 job "
                "lands."
            )
        flow.append(para(source_line, st["Body"]))
        flow.append(para(
            f"Cells: {analysis['n_cells']}. Gate (new frame): B mean "
            f"OOD ≥ 0.50, patch-CE ≥ 0.05, A mean OOD ≤ 0.10 → "
            f"<b>{_fmt(analysis.get('e4_new_frame_pass'))}</b>. Gate "
            f"(old frame): A mean OOD ≥ 0.50, ρ(weakness, OOD) ≥ 0.5 → "
            f"<b>{_fmt(analysis.get('e4_old_frame_pass'))}</b>. "
            f"ρ(patch-CE, OOD) = "
            f"{_fmt(analysis['rho_patch_ce_ood_all_cells'])}; "
            f"ρ(weakness, OOD) = "
            f"{_fmt(analysis['rho_weakness_ood_all_cells'])}.",
            st["Body"]))
    else:
        flow.append(para("E4 result JSON not yet available.", st["Body"]))

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


def build_pdf() -> Path:
    st = styles()
    text = _load_paper()
    before, after = _split_paper(text)
    flow = markdown_to_flow(before, st)
    flow.extend(build_results_flow(st))
    flow.extend(markdown_to_flow(after, st))

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
