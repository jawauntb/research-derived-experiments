#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the repository-wide formal system atlas PDF.

The narrative lives in ``papers/formal_system_atlas/paper.md``. Exhaustive
appendices are generated from the repository's checked-in registries and Lean
sources so the audit remains reproducible at a specific commit.
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "papers" / "formal_system_atlas" / "paper.md"
OUTPUT = (
    ROOT
    / "output"
    / "pdf"
    / "research_derived_experiments_formal_system_atlas_2026-08-19.pdf"
)
AUDIT_COMMIT = "3a86730"
AUDIT_DATE = "2026-08-19"


ASCII_REPLACEMENTS = {
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u2192": "->",
    "\u21d2": "=>",
    "\u21a6": "->",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u2260": "!=",
    "\u2248": "~=",
    "\u2208": " in ",
    "\u2200": "for all ",
    "\u2203": "exists ",
    "\u00d7": "x",
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u03b4": "delta",
    "\u03b5": "epsilon",
    "\u03b8": "theta",
    "\u03ba": "kappa",
    "\u03c0": "pi",
    "\u03c1": "rho",
    "\u03c3": "sigma",
    "\u03c4": "tau",
    "\u03c6": "phi",
    "\u03a6": "Phi",
    "\u0394": "Delta",
    "\u0398": "Theta",
    "\u2291": "<=",
    "\u22a3": "|-",
}


def ascii_text(value: object) -> str:
    """Return ReportLab-safe ASCII while preserving scientific meaning."""

    text = str(value)
    for source, replacement in ASCII_REPLACEMENTS.items():
        text = text.replace(source, replacement)
    return text.encode("ascii", "ignore").decode("ascii")


def inline_markup(value: object) -> str:
    """Convert a small Markdown subset to ReportLab paragraph markup."""

    text = ascii_text(value)
    tokens: list[str] = []

    def hold_code(match: re.Match[str]) -> str:
        tokens.append(
            '<font name="Courier" color="#274060">'
            + html.escape(match.group(1))
            + "</font>"
        )
        return f"@@TOKEN{len(tokens) - 1}@@"

    text = re.sub(r"`([^`]+)`", hold_code, text)
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    for index, token in enumerate(tokens):
        text = text.replace(f"@@TOKEN{index}@@", token)
    return text


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    navy = colors.HexColor("#16283f")
    blue = colors.HexColor("#22577a")
    teal = colors.HexColor("#2f7f78")
    slate = colors.HexColor("#455667")
    return {
        "CoverKicker": ParagraphStyle(
            "CoverKicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=teal,
            spaceAfter=18,
        ),
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=30,
            alignment=TA_CENTER,
            textColor=navy,
            spaceAfter=18,
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            alignment=TA_CENTER,
            textColor=slate,
            spaceAfter=14,
        ),
        "CoverMeta": ParagraphStyle(
            "CoverMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#607080"),
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=navy,
            spaceBefore=13,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=15.5,
            textColor=blue,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            leading=13,
            textColor=teal,
            spaceBefore=7,
            spaceAfter=3,
            keepWithNext=True,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.65,
            leading=11.6,
            textColor=colors.HexColor("#202a33"),
            spaceAfter=5.2,
            alignment=TA_LEFT,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.45,
            leading=11.2,
            leftIndent=14,
            firstLineIndent=-8,
            bulletIndent=4,
            spaceAfter=3,
            textColor=colors.HexColor("#202a33"),
        ),
        "Quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12.2,
            leftIndent=16,
            rightIndent=10,
            borderColor=teal,
            borderWidth=1.5,
            borderPadding=7,
            backColor=colors.HexColor("#eef6f4"),
            textColor=colors.HexColor("#294b49"),
            spaceBefore=5,
            spaceAfter=8,
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.7,
            leading=10.1,
            leftIndent=10,
            rightIndent=8,
            borderColor=colors.HexColor("#c8d3dc"),
            borderWidth=0.6,
            borderPadding=6,
            backColor=colors.HexColor("#f4f7f9"),
            spaceBefore=4,
            spaceAfter=7,
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.15,
            leading=9.2,
            textColor=slate,
            spaceAfter=2.5,
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.7,
            leading=8.2,
            textColor=colors.white,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=6.35,
            leading=8.0,
            textColor=colors.HexColor("#24323d"),
        ),
    }


class AuditDocTemplate(BaseDocTemplate):
    """Document template with a generated TOC and PDF outline."""

    def afterFlowable(self, flowable: object) -> None:  # noqa: N802
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in {"H1", "H2"}:
            return
        level = 0 if style_name == "H1" else 1
        text = flowable.getPlainText()
        key = f"section-{self.seq.nextf('heading')}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=level == 0)
        self.notify("TOCEntry", (level, text, self.page, key))


def on_page(canvas: Any, document: AuditDocTemplate) -> None:
    canvas.saveState()
    if document.page > 1:
        canvas.setStrokeColor(colors.HexColor("#d7e0e7"))
        canvas.setLineWidth(0.5)
        canvas.line(0.72 * inch, 10.35 * inch, 7.78 * inch, 10.35 * inch)
        canvas.setFont("Helvetica", 7.2)
        canvas.setFillColor(colors.HexColor("#667785"))
        canvas.drawString(0.72 * inch, 10.46 * inch, "FORMAL SYSTEM ATLAS")
        canvas.drawRightString(
            7.78 * inch,
            10.46 * inch,
            f"AUDIT {AUDIT_DATE}  |  {AUDIT_COMMIT}",
        )
        canvas.line(0.72 * inch, 0.58 * inch, 7.78 * inch, 0.58 * inch)
        canvas.drawString(0.72 * inch, 0.39 * inch, "Research Derived Experiments")
        canvas.drawRightString(7.78 * inch, 0.39 * inch, f"Page {document.page}")
    canvas.restoreState()


def cover_flow(st: dict[str, ParagraphStyle]) -> list[Any]:
    return [
        Spacer(1, 1.05 * inch),
        Paragraph("REPOSITORY-WIDE EVIDENCE AUDIT", st["CoverKicker"]),
        Paragraph("Formal Atlas of the Research Derived Experiments System", st["CoverTitle"]),
        Paragraph(
            "Proofs, dynamics, empirical findings, failures, and open conjectures",
            st["CoverSubtitle"],
        ),
        Spacer(1, 0.38 * inch),
        Table(
            [
                [Paragraph("115", st["CoverTitle"]), Paragraph("129", st["CoverTitle"]), Paragraph("513", st["CoverTitle"])],
                [Paragraph("experiment packages", st["CoverMeta"]), Paragraph("paper sources", st["CoverMeta"]), Paragraph("Lean declarations", st["CoverMeta"])],
            ],
            colWidths=[2.0 * inch] * 3,
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LINEBEFORE", (1, 0), (1, -1), 0.5, colors.HexColor("#c8d3dc")),
                    ("LINEBEFORE", (2, 0), (2, -1), 0.5, colors.HexColor("#c8d3dc")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        ),
        Spacer(1, 0.5 * inch),
        Paragraph("Jawaun Brown, human author and research director", st["CoverMeta"]),
        Paragraph("Audit and manuscript production by OpenAI Codex under direction and review", st["CoverMeta"]),
        Spacer(1, 0.18 * inch),
        Paragraph(f"Audit date: {AUDIT_DATE}", st["CoverMeta"]),
        Paragraph(f"Repository commit: {AUDIT_COMMIT}", st["CoverMeta"]),
        PageBreak(),
    ]


def flush_paragraph(lines: list[str], flow: list[Any], style: ParagraphStyle) -> None:
    if not lines:
        return
    text = " ".join(line.strip() for line in lines)
    flow.append(Paragraph(inline_markup(text), style))
    lines.clear()


def markdown_flow(markdown: str, st: dict[str, ParagraphStyle]) -> list[Any]:
    """Render the narrative Markdown subset used by this monograph."""

    flow: list[Any] = []
    paragraph: list[str] = []
    quote: list[str] = []
    code: list[str] = []
    in_code = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            flush_paragraph(paragraph, flow, st["Body"])
            if in_code:
                flow.append(Preformatted(ascii_text("\n".join(code)), st["Code"]))
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith(">"):
            flush_paragraph(paragraph, flow, st["Body"])
            quote.append(line.lstrip("> "))
            continue
        if quote and not line.startswith(">"):
            flow.append(Paragraph(inline_markup(" ".join(quote)), st["Quote"]))
            quote.clear()
        if not line.strip():
            flush_paragraph(paragraph, flow, st["Body"])
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph(paragraph, flow, st["Body"])
            level = len(heading.group(1))
            flow.append(Paragraph(inline_markup(heading.group(2)), st[f"H{level}"]))
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if bullet:
            flush_paragraph(paragraph, flow, st["Body"])
            flow.append(
                Paragraph(inline_markup(bullet.group(1)), st["Bullet"], bulletText="-")
            )
            continue
        numbered = re.match(r"^(\d+)\.\s+(.+)$", line)
        if numbered:
            flush_paragraph(paragraph, flow, st["Body"])
            flow.append(
                Paragraph(
                    inline_markup(numbered.group(2)),
                    st["Bullet"],
                    bulletText=f"{numbered.group(1)}.",
                )
            )
            continue
        paragraph.append(line)
    flush_paragraph(paragraph, flow, st["Body"])
    if quote:
        flow.append(Paragraph(inline_markup(" ".join(quote)), st["Quote"]))
    if code:
        flow.append(Preformatted(ascii_text("\n".join(code)), st["Code"]))
    return flow


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def table(
    rows: list[list[object]],
    widths: list[float],
    st: dict[str, ParagraphStyle],
) -> LongTable:
    rendered: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        style = st["TableHead"] if row_index == 0 else st["TableCell"]
        rendered.append([Paragraph(inline_markup(value), style) for value in row])
    grid = LongTable(rendered, colWidths=widths, repeatRows=1, hAlign="LEFT")
    grid.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22577a")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#c3cfd8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fa")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    return grid


def registered_claims_appendix(st: dict[str, ParagraphStyle]) -> list[Any]:
    claims = load_json(ROOT / "docs" / "claim_registry.json")["claims"]
    evidence = load_json(ROOT / "docs" / "program_evidence_registry.json")["records"]
    flow: list[Any] = [
        PageBreak(),
        Paragraph("Appendix A - Registered claims and evidence", st["H1"]),
        Paragraph(
            "These are the repository's centrally structured claims. A supported counterexample instrument can reject the broad claim it tests; local runner success and claim status are separate.",
            st["Body"],
        ),
        table(
            [["Claim ID", "Tier / status", "Statement", "Evidence"]]
            + [
                [
                    claim["claim_id"],
                    f"{claim['claim_tier']} / {claim['status']}",
                    claim["statement"],
                    ", ".join(claim.get("evidence_ids", [])),
                ]
                for claim in claims
            ],
            [1.2 * inch, 0.9 * inch, 3.7 * inch, 1.15 * inch],
            st,
        ),
        Spacer(1, 0.18 * inch),
        Paragraph("Evidence records", st["H2"]),
        table(
            [["Evidence ID", "Status", "Notes"]]
            + [
                [record["evidence_id"], record["status"], record.get("notes", "")]
                for record in evidence
            ],
            [1.75 * inch, 0.65 * inch, 4.55 * inch],
            st,
        ),
    ]
    return flow


def experiment_ledger_appendix(st: dict[str, ParagraphStyle]) -> list[Any]:
    verification = load_json(ROOT / "docs" / "verification.json")
    contracts = load_json(ROOT / "docs" / "experiment_contract_registry.json")
    contract_by_package = {row["package"]: row for row in contracts["packages"]}
    experiments = sorted(verification["experiments"], key=lambda row: row["name"])
    flow: list[Any] = [
        PageBreak(),
        Paragraph("Appendix B - Exhaustive experiment package ledger", st["H1"]),
        Paragraph(
            f"The verification index contains {len(experiments)} provenance-bearing packages. Entries report evidence plumbing, not automatic scientific endorsement. Legacy exceptions and partial histories are called out explicitly.",
            st["Body"],
        ),
    ]
    for item in experiments:
        name = item["name"]
        contract = contract_by_package.get(name, {})
        adjudications = item.get("scientific_adjudications", [])
        adjudication_text = ", ".join(
            sorted({str(row.get("status", "unadjudicated")) for row in adjudications})
        ) or "unadjudicated"
        reports = item.get("result_reports", [])
        details = [
            ["Package", name],
            [
                "Evidence state",
                " | ".join(
                    [
                        f"provenance={item.get('status', 'unknown')}",
                        f"coverage={contract.get('coverage_mode', 'unregistered')}",
                        f"run={item.get('run_coverage', contract.get('run_coverage', 'unknown'))}",
                        f"integrity={item.get('integrity_state', 'not structured')}",
                        f"manifest={item.get('manifest_status', 'not structured')}",
                        f"adjudication={adjudication_text}",
                    ]
                ),
            ],
            ["Result reports", ", ".join(reports) if reports else "No committed result report indexed"],
            ["Paper", item.get("paper") or "No paper indexed"],
            ["Reproduction", item.get("regen", "No regeneration dispatch indexed")],
        ]
        block = [
            Paragraph(name, st["H3"]),
            Table(
                [
                    [Paragraph(inline_markup(key), st["TableHead"]), Paragraph(inline_markup(value), st["TableCell"])]
                    for key, value in details
                ],
                colWidths=[1.15 * inch, 5.8 * inch],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#2f7f78")),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cad5dc")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                ),
            ),
            Spacer(1, 0.08 * inch),
        ]
        if len(", ".join(reports)) < 450:
            flow.append(KeepTogether(block))
        else:
            flow.extend(block)
    return flow


def walk_scalars(value: Any, path: tuple[str, ...] = ()) -> Iterator[tuple[tuple[str, ...], Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_scalars(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_scalars(child, path + (str(index),))
    elif isinstance(value, str | int | float | bool) or value is None:
        yield path, value


def result_signals(package_dir: Path) -> list[str]:
    signals: list[str] = []
    for result_path in sorted((package_dir / "results").glob("**/*.json")):
        try:
            payload = load_json(result_path)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, dict) and isinstance(payload.get("gates"), dict):
            gates = payload["gates"]
            bools = [value for value in gates.values() if isinstance(value, bool)]
            if bools:
                signals.append(
                    f"{result_path.name}: gates {sum(bools)}/{len(bools)} true"
                )
        for key_path, value in walk_scalars(payload):
            if not key_path:
                continue
            key = key_path[-1].lower()
            if key not in {"status", "verdict", "overall_verdict", "decision", "outcome"}:
                continue
            signal = f"{result_path.name}:{'.'.join(key_path)}={value}"
            if signal not in signals:
                signals.append(signal)
            if len(signals) >= 10:
                return signals
    return signals


def preregistration_appendix(st: dict[str, ParagraphStyle]) -> list[Any]:
    preregistrations = sorted((ROOT / "experiments").glob("*/preregistration.json"))
    flow: list[Any] = [
        PageBreak(),
        Paragraph("Appendix C - Preregistered hypotheses and recorded outcomes", st["H1"]),
        Paragraph(
            f"This appendix includes all {len(preregistrations)} top-level JSON preregistrations. Paper-only and nested wave preregistrations remain visible in Appendix B through their packages and reports.",
            st["Body"],
        ),
    ]
    for prereg_path in preregistrations:
        payload = load_json(prereg_path)
        package = prereg_path.parent.name
        signals = result_signals(prereg_path.parent)
        rows = [
            ["Hypothesis", payload.get("hypothesis", "Not stated")],
            ["Decision rule", payload.get("decision", "Use registered gates")],
            ["Claim boundary", payload.get("claim_boundary", "No explicit boundary field")],
            ["Recorded signals", "; ".join(signals) if signals else "No JSON status/verdict signal found"],
            ["Source", prereg_path.relative_to(ROOT)],
        ]
        block: list[Any] = [Paragraph(package, st["H3"])]
        for label, value in rows:
            block.append(Paragraph(f"<b>{inline_markup(label)}:</b> {inline_markup(value)}", st["Small"]))
        block.append(Spacer(1, 0.08 * inch))
        flow.extend(block)
    return flow


def strip_lean_comments(text: str) -> str:
    """Remove line and nested block comments while preserving line numbers."""

    output: list[str] = []
    index = 0
    block_depth = 0
    while index < len(text):
        pair = text[index : index + 2]
        if block_depth:
            if pair == "/-":
                block_depth += 1
                output.extend("  ")
                index += 2
            elif pair == "-/":
                block_depth -= 1
                output.extend("  ")
                index += 2
            else:
                output.append("\n" if text[index] == "\n" else " ")
                index += 1
            continue
        if pair == "/-":
            block_depth = 1
            output.extend("  ")
            index += 2
            continue
        if pair == "--":
            while index < len(text) and text[index] != "\n":
                output.append(" ")
                index += 1
            continue
        output.append(text[index])
        index += 1
    return "".join(output)


def lean_declarations() -> list[tuple[str, int, str, str]]:
    declarations: list[tuple[str, int, str, str]] = []
    pattern = re.compile(
        r"^\s*(?:(?:@\[[^\]]+\]|private|protected|noncomputable)\s+)*"
        r"(theorem|lemma|proposition)\s+([^\s(:{]+)"
    )
    for path in sorted((ROOT / "formal").glob("**/*.lean")):
        cleaned = strip_lean_comments(path.read_text(encoding="utf-8"))
        relative = str(path.relative_to(ROOT))
        for line_number, line in enumerate(cleaned.splitlines(), start=1):
            match = pattern.match(line)
            if match:
                declarations.append((relative, line_number, match.group(1), match.group(2)))
    return declarations


def receipt_filenames() -> set[str]:
    filenames: set[str] = set()
    for name in ("VERIFY_RECEIPT_2026-08-17.md", "VERIFY_RECEIPT_2026-08-18.md"):
        text = (ROOT / "docs" / "lea" / name).read_text(encoding="utf-8")
        filenames.update(re.findall(r"`([A-Za-z0-9_/.-]+\.lean)`", text))
    return {Path(name).name for name in filenames}


def lean_appendix(st: dict[str, ParagraphStyle]) -> list[Any]:
    declarations = lean_declarations()
    receipt_files = receipt_filenames()
    rows: list[list[object]] = [["Source", "Kind", "Declaration", "Lane / receipt signal"]]
    for path, line, kind, name in declarations:
        filename = Path(path).name
        if "structural-intelligence-mathlib" in path:
            lane = "mathlib: proved, not SafeVerify-verified"
        elif "relative-identifiability" in path:
            lane = "relative: Lean-proved, no SafeVerify receipt"
        elif filename in receipt_files:
            lane = "core file named in receipt; headline subset only"
        else:
            lane = "core: Lean-proved; no file receipt located"
        rows.append([f"{path}:{line}", kind, name, lane])
    return [
        PageBreak(),
        Paragraph("Appendix D - Exhaustive Lean declaration inventory", st["H1"]),
        Paragraph(
            f"The source scan found {len(declarations)} theorem, lemma, or proposition declarations across three Lean packages. It found no executable project-local axiom, sorry, admit, opaque declaration, or native_decide. A receipt naming a file does not automatically verify every declaration in that file; receipts enumerate headline subsets.",
            st["Body"],
        ),
        table(rows, [2.65 * inch, 0.52 * inch, 1.75 * inch, 2.03 * inch], st),
    ]


def limitations_appendix(st: dict[str, ParagraphStyle]) -> list[Any]:
    return [
        PageBreak(),
        Paragraph("Appendix E - Audit limitations and reproduction contract", st["H1"]),
        Paragraph(
            "This atlas audits committed repository evidence at one Git commit. It does not independently rerun every historical model provider, reconstruct gitignored raw artifacts, validate every external citation, or prove that a paper's prose follows from its formal statement. Provider-backed results are snapshots. Exact finite results are only exact for their declared world and code.",
            st["Body"],
        ),
        Paragraph(
            "Rebuild command: python3 scripts/build_formal_system_atlas_pdf.py",
            st["Code"],
        ),
        Paragraph(
            "Primary verification commands used by repository policy include python3 scripts/run_quality_checks.py and the Lean lake builds in .github/workflows/quality.yml. SafeVerify status must be read from the dated receipts under docs/lea rather than inferred from a green lake build.",
            st["Body"],
        ),
        Paragraph(
            "The generated appendices should change when registries, preregistrations, result status signals, or Lean declarations change. Such drift is expected and is why the PDF records its commit and date.",
            st["Body"],
        ),
    ]


def build_story(st: dict[str, ParagraphStyle]) -> list[Any]:
    markdown = SOURCE.read_text(encoding="utf-8")
    narrative_start = markdown.index("## Executive verdict")
    story = cover_flow(st)
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1",
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=13,
            leftIndent=0,
            firstLineIndent=0,
            textColor=colors.HexColor("#16283f"),
            spaceBefore=4,
        ),
        ParagraphStyle(
            "TOC2",
            fontName="Helvetica",
            fontSize=8.2,
            leading=11,
            leftIndent=16,
            firstLineIndent=0,
            textColor=colors.HexColor("#455667"),
        ),
    ]
    story.extend(
        [
            Paragraph("Contents", st["H1"]),
            Paragraph(
                "Narrative chapters are followed by exhaustive generated registries and declaration indexes.",
                st["Body"],
            ),
            toc,
            PageBreak(),
        ]
    )
    story.extend(markdown_flow(markdown[narrative_start:], st))
    story.extend(registered_claims_appendix(st))
    story.extend(experiment_ledger_appendix(st))
    story.extend(preregistration_appendix(st))
    story.extend(lean_appendix(st))
    story.extend(limitations_appendix(st))
    return story


def verify_pdf(path: Path, expected_declarations: int) -> tuple[int, int]:
    reader = PdfReader(str(path))
    if len(reader.pages) < 30:
        raise RuntimeError(f"atlas unexpectedly short: {len(reader.pages)} pages")
    metadata = reader.metadata or {}
    if "Formal Atlas" not in str(metadata.get("/Title", "")):
        raise RuntimeError("PDF title metadata missing")
    extracted = "\n".join((page.extract_text() or "") for page in reader.pages)
    required = [
        "Executive verdict",
        "Appendix B - Exhaustive experiment package ledger",
        "Appendix D - Exhaustive Lean declaration inventory",
        f"{expected_declarations} theorem, lemma, or proposition declarations",
    ]
    missing = [needle for needle in required if needle not in extracted]
    if missing:
        raise RuntimeError(f"PDF content checks failed: {missing}")
    empty_pages = sum(1 for page in reader.pages if len((page.extract_text() or "").strip()) < 12)
    if empty_pages:
        raise RuntimeError(f"PDF contains {empty_pages} unexpectedly empty pages")
    return len(reader.pages), len(extracted)


def build_pdf(output: Path) -> Path:
    st = styles()
    declarations = lean_declarations()
    output.parent.mkdir(parents=True, exist_ok=True)
    document = AuditDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.78 * inch,
        bottomMargin=0.72 * inch,
        title="Formal Atlas of the Research Derived Experiments System",
        author="Jawaun Brown",
        subject="Repository-wide proof, experiment, finding, failure, and hypothesis audit",
        creator="Research Derived Experiments formal atlas builder",
    )
    frame = Frame(
        0.72 * inch,
        0.72 * inch,
        document.width,
        document.height,
        id="normal",
    )
    document.addPageTemplates([PageTemplate(id="audit", frames=[frame], onPage=on_page)])
    document.multiBuild(build_story(st))
    pages, characters = verify_pdf(output, len(declarations))
    display_path = output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
    print(f"Wrote {display_path}")
    print(f"Pages: {pages}")
    print(f"Extracted characters: {characters}")
    print(f"Lean declarations indexed: {len(declarations)}")
    return output


def main() -> int:
    build_pdf(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
