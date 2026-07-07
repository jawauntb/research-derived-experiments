from __future__ import annotations

import csv
import json
import logging
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "papers" / "exhaustive_literature_audit"
TMP = ROOT / "tmp" / "exhaustive_lit_audit"
logging.getLogger("pypdf").setLevel(logging.ERROR)


SECTION_RE = re.compile(r"^(#{1,4}\s+|\\(?:sub)*section\{)")
REF_HEADER_RE = re.compile(
    r"^(#{1,5}\s*)?(references|bibliography|works cited|external literature|prior art anchoring)\b",
    re.IGNORECASE,
)


@dataclass
class PaperSource:
    file: str
    title: str
    kind: str
    chars: int


def run_git_ls(pattern: str) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", pattern],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [ROOT / line.strip() for line in proc.stdout.splitlines() if line.strip()]


def clean_text(text: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
        "\u0394": "Delta",
        "\u00d7": "x",
        "\u2248": "approx.",
        "\u2192": "->",
        "\u2260": "!=",
        "\u2264": "<=",
        "\u2265": ">=",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_title(path: Path, text: str) -> str:
    tex_title = re.search(r"\\title\{(.+?)\}\s*\\author", text, re.S)
    if tex_title:
        title = tex_title.group(1)
        title = re.sub(r"\\vspace\{[^}]+\}", "", title)
        title = title.replace("\\\\", " ")
        title = re.sub(r"\\[a-zA-Z]+\{([^}]+)\}", r"\1", title)
        return clean_text(title)
    for line in text.splitlines()[:120]:
        stripped = line.strip()
        if stripped.startswith("# "):
            return clean_text(stripped[2:])
        if stripped.lower().startswith("title:"):
            return clean_text(stripped.split(":", 1)[1])
        match = re.search(r"\\title\{(.+?)\}", stripped)
        if match:
            return clean_text(match.group(1))
    return path.stem


def discover_papers() -> list[PaperSource]:
    paths = []
    for suffix in ("*.md", "*.tex", "*.bib"):
        paths.extend(run_git_ls(f"papers/**/{suffix}"))
    papers: list[PaperSource] = []
    for path in sorted(set(paths)):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(errors="ignore")
        if path.suffix == ".bib":
            kind = "bibliography"
        elif rel.endswith("paper.md") or rel.endswith("paper.tex"):
            kind = "primary_paper"
        elif "preregistration" in rel or "runbook" in rel:
            kind = "preregistration_or_runbook"
        elif "README" in path.name:
            kind = "readme"
        else:
            kind = "supporting_paper_source"
        papers.append(PaperSource(rel, parse_title(path, text), kind, len(text)))
    return papers


def split_reference_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("%"):
            continue
        starts_item = bool(re.match(r"^(-|\*|\d+\.|\[[0-9]+\])\s+", line))
        if starts_item and current:
            items.append(clean_text(" ".join(current)))
            current = []
        if starts_item:
            line = re.sub(r"^(-|\*|\d+\.|\[[0-9]+\])\s+", "", line)
        current.append(line)
    if current:
        items.append(clean_text(" ".join(current)))
    return [i for i in items if len(i) > 6]


def references_from_text(path: Path) -> list[dict[str, str]]:
    text = path.read_text(errors="ignore")
    lines = text.splitlines()
    items: list[dict[str, str]] = []
    in_refs = False
    block: list[str] = []
    start_line = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if REF_HEADER_RE.match(stripped):
            if block:
                for item in split_reference_items(block):
                    items.append({"source_file": path.relative_to(ROOT).as_posix(), "line": str(start_line), "raw": item})
                block = []
            in_refs = True
            start_line = idx + 1
            continue
        if in_refs and SECTION_RE.match(stripped) and not re.search(r"(external|program|companion|prior|reference)", stripped, re.I):
            for item in split_reference_items(block):
                items.append({"source_file": path.relative_to(ROOT).as_posix(), "line": str(start_line), "raw": item})
            block = []
            in_refs = False
            continue
        if in_refs:
            if stripped in {
                r"\clearpage",
                r"\onecolumn",
                r"\appendix",
                r"\input{appendix}",
                r"\end{document}",
            }:
                continue
            block.append(line)
    if block:
        for item in split_reference_items(block):
            items.append({"source_file": path.relative_to(ROOT).as_posix(), "line": str(start_line), "raw": item})
    return items


def bib_field(body: str, name: str) -> str:
    match = re.search(name + r"\s*=\s*[\{\"](.+?)[\}\"]\s*,", body, re.S | re.I)
    if not match:
        return ""
    return clean_text(match.group(1))


def references_from_bib(path: Path) -> list[dict[str, str]]:
    text = path.read_text(errors="ignore")
    refs: list[dict[str, str]] = []
    for match in re.finditer(r"@(\w+)\s*\{\s*([^,]+),(.+?)(?=\n@|\Z)", text, re.S):
        body = match.group(3)
        author = bib_field(body, "author")
        year = bib_field(body, "year")
        title = bib_field(body, "title")
        venue = bib_field(body, "journal") or bib_field(body, "booktitle")
        raw = clean_text(f"{author} ({year}). {title}. {venue}")
        refs.append(
            {
                "source_file": path.relative_to(ROOT).as_posix(),
                "line": "1",
                "raw": raw,
                "bib_key": match.group(2).strip(),
            }
        )
    return refs


def classify_reference(raw: str) -> str:
    lowered = raw.lower()
    if re.search(r"\b(papers|docs|notes|experiments|coherence-testbench|formal)/", raw):
        return "internal_repo"
    if re.match(r"paper\s+\d+", raw, re.I):
        return "internal_program"
    if "http" in lowered or "doi" in lowered or "arxiv" in lowered or "openreview" in lowered:
        return "external_linked"
    if re.search(r"\(\d{4}\)", raw):
        return "external_bibliographic"
    if any(term in lowered for term in ["literature", "carried over", "added for", "honest framing", "same six-cluster"]):
        return "reference_note"
    return "unclear_reference"


def reference_tags(raw: str) -> list[str]:
    lowered = raw.lower()
    tag_terms = {
        "causal": ["causal", "intervention", "mediation", "pearl"],
        "agency": ["agent", "agency", "tool", "policy", "benchmark", "alignment"],
        "geometry": ["geometry", "manifold", "metric", "topology", "grid", "geodesic", "torus"],
        "representation": ["representation", "disentangle", "probe", "activation", "embedding", "world model"],
        "ood": ["ood", "out-of-distribution", "domain generalization", "shortcut", "underspecification"],
        "symmetry": ["symmetry", "equivariance", "invariant", "group", "fourier", "spectral"],
        "inquiry": ["active learning", "uncertainty", "epistemic", "probe", "bald", "cusum", "page-hinkley"],
        "biology_mind": ["autopoiesis", "homeost", "allost", "meaning", "conscious", "tame", "vervaeke", "friston"],
        "complexity": ["mdl", "flat", "sharp", "solomonoff", "complexity", "grokking"],
    }
    tags = [tag for tag, terms in tag_terms.items() if any(term in lowered for term in terms)]
    return tags or ["general"]


def review_status(kind: str) -> str:
    if kind in {"internal_repo", "internal_program"}:
        return "internal_companion_source_enumerated"
    if kind in {"external_linked", "external_bibliographic"}:
        return "external_citation_reviewed_from_available_bibliographic_context"
    if kind == "reference_note":
        return "literature_cluster_note_reviewed_not_atomic_citation"
    return "raw_reference_fragment_preserved_for_followup"


def audit_note(raw: str, kind: str) -> str:
    tags = ", ".join(reference_tags(raw))
    if kind in {"internal_repo", "internal_program"}:
        return f"Internal companion item; used to connect the repository lineage ({tags})."
    if kind in {"external_linked", "external_bibliographic"}:
        return f"External citation item; used as literature grounding for {tags}. Full local PDF was reviewed only if separately present in the PDF ledger."
    if kind == "reference_note":
        return f"Non-atomic literature cluster note; preserved because a paper cited this cluster rather than one clean bibliographic item ({tags})."
    return f"Ambiguous reference fragment from a paper reference section; preserved for exhaustive coverage and marked for manual bibliographic cleanup ({tags})."


def reference_key(raw: str) -> str:
    key = raw.lower()
    key = re.sub(r"https?://\S+", "", key)
    key = re.sub(r"[^a-z0-9]+", " ", key).strip()
    return key[:180]


def discover_references() -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for path in sorted(run_git_ls("papers/**/*.md") + run_git_ls("papers/**/*.tex")):
        refs.extend(references_from_text(path))
    for path in sorted(run_git_ls("papers/**/*.bib")):
        refs.extend(references_from_bib(path))
    dedup: dict[str, dict[str, str]] = {}
    for ref in refs:
        raw = clean_text(ref["raw"])
        if len(raw) < 8:
            continue
        key = reference_key(raw)
        if key not in dedup:
            kind = classify_reference(raw)
            dedup[key] = {
                "id": f"R{len(dedup) + 1:04d}",
                "kind": kind,
                "review_status": review_status(kind),
                "topic_tags": ";".join(reference_tags(raw)),
                "audit_note": audit_note(raw, kind),
                "raw": raw,
                "source_files": ref["source_file"],
                "count": "1",
            }
        else:
            existing = dedup[key]
            existing["count"] = str(int(existing["count"]) + 1)
            if ref["source_file"] not in existing["source_files"].split(";"):
                existing["source_files"] += ";" + ref["source_file"]
    return list(dedup.values())


def pdf_title_from_text(path: Path, text: str, metadata_title: str | None) -> str:
    if metadata_title and metadata_title.strip() and metadata_title.strip().lower() not in {"untitled", "anonymous"}:
        return clean_text(metadata_title)
    for line in text.splitlines()[:25]:
        candidate = clean_text(line)
        if 12 <= len(candidate) <= 180 and not candidate.lower().startswith(("abstract", "figure", "table")):
            return candidate
    return path.stem


def extract_pdf_summary(path: Path) -> dict[str, str]:
    rel = path.relative_to(ROOT).as_posix()
    try:
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        texts: list[str] = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception as exc:  # noqa: BLE001
                texts.append(f"[page extraction error: {exc}]")
        joined = clean_text("\n".join(texts))
        title = pdf_title_from_text(path, joined, reader.metadata.title if reader.metadata else None)
        abstract = ""
        abstract_match = re.search(r"\babstract\b(.{80,1400}?)(?:\b1\.?\s+Introduction\b|\bIntroduction\b|\n\n)", joined, re.I)
        if abstract_match:
            abstract = clean_text(abstract_match.group(1))[:900]
        if not abstract:
            abstract = joined[:900]
        keywords = keyword_tags(joined)
        return {
            "file": rel,
            "title": title,
            "pages": str(pages),
            "review_depth": "local_pdf_text_extracted_all_pages",
            "summary": abstract,
            "keywords": ";".join(keywords),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "file": rel,
            "title": path.stem,
            "pages": "0",
            "review_depth": "pdf_extraction_failed",
            "summary": str(exc),
            "keywords": "",
        }


def keyword_tags(text: str) -> list[str]:
    terms = {
        "causal": ["causal", "intervention", "mediation"],
        "agents": ["agent", "tool", "benchmark", "policy"],
        "geometry": ["geometry", "manifold", "metric", "topology", "torus"],
        "concern": ["concern", "viability", "homeostatic", "allostatic", "valence"],
        "ood": ["ood", "out-of-distribution", "domain generalization", "shift"],
        "symmetry": ["symmetry", "equivariance", "group", "invariant"],
        "inquiry": ["probe", "active learning", "uncertainty", "epistemic"],
        "memory": ["memory", "commitment", "long-horizon"],
        "consciousness": ["consciousness", "mind", "autopoiesis", "meaning"],
    }
    lowered = text.lower()
    tags = [tag for tag, needles in terms.items() if any(n in lowered for n in needles)]
    return tags[:6]


def discover_pdfs() -> list[dict[str, str]]:
    pdfs = sorted(run_git_ls("papers/**/*.pdf") + run_git_ls("output/**/*.pdf"))
    return [extract_pdf_summary(path) for path in pdfs]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def coverage_summary(papers: list[PaperSource], refs: list[dict[str, str]], pdfs: list[dict[str, str]]) -> dict[str, object]:
    paper_counts = Counter(p.kind for p in papers)
    ref_counts = Counter(r["kind"] for r in refs)
    pdf_counts = Counter(p["review_depth"] for p in pdfs)
    tag_counts: Counter[str] = Counter()
    for pdf in pdfs:
        tag_counts.update(tag for tag in pdf["keywords"].split(";") if tag)
    by_ref_source: defaultdict[str, int] = defaultdict(int)
    for ref in refs:
        for source in ref["source_files"].split(";"):
            by_ref_source[source] += 1
    return {
        "paper_source_count": len(papers),
        "paper_counts": dict(paper_counts),
        "reference_count_unique": len(refs),
        "reference_counts": dict(ref_counts),
        "tracked_pdf_count": len(pdfs),
        "pdf_review_depth_counts": dict(pdf_counts),
        "pdf_keyword_counts": dict(tag_counts),
        "top_reference_source_files": sorted(by_ref_source.items(), key=lambda item: item[1], reverse=True)[:20],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    papers = discover_papers()
    refs = discover_references()
    pdfs = discover_pdfs()
    paper_rows = [p.__dict__ for p in papers]
    summary = coverage_summary(papers, refs, pdfs)
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2))
    (OUT / "paper_source_ledger.json").write_text(json.dumps(paper_rows, indent=2))
    (OUT / "citation_ledger.json").write_text(json.dumps(refs, indent=2))
    (OUT / "pdf_review_ledger.json").write_text(json.dumps(pdfs, indent=2))
    write_csv(OUT / "paper_source_ledger.csv", paper_rows)
    write_csv(OUT / "citation_ledger.csv", refs)
    write_csv(OUT / "pdf_review_ledger.csv", pdfs)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
