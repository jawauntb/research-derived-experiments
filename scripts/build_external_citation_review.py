#!/usr/bin/env python3
"""Resolve external citations into a running evidence ledger.

This is a second-stage enrichment pass over the exhaustive local citation audit.
It does not claim that every external work is available in full text. Instead it
records which cited works can be resolved to external scholarly metadata, which
ones expose abstracts, and which ones still require manual bibliographic repair.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "papers" / "exhaustive_literature_audit"
OUT_DIR = ROOT / "papers" / "external_citation_review"
CACHE_DIR = OUT_DIR / ".cache"
CITATION_LEDGER = AUDIT_DIR / "citation_ledger.json"

NON_EXTERNAL_KINDS = {"internal_repo"}
ARXIV_API = "https://export.arxiv.org/api/query"
OPENALEX_API = "https://api.openalex.org/works"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper"
MAILTO = "codex-audit@example.com"

TOPIC_KEYWORDS = {
    "causal_representation": [
        "causal",
        "intervention",
        "counterfactual",
        "identifiability",
        "mechanism",
    ],
    "agency_viability": [
        "agency",
        "agent",
        "viability",
        "autopoiesis",
        "adaptivity",
        "empowerment",
        "control",
    ],
    "uncertainty_inquiry": [
        "uncertainty",
        "active learning",
        "bayesian",
        "epistemic",
        "information",
        "exploration",
    ],
    "geometry_symmetry": [
        "geometry",
        "geometric",
        "symmetry",
        "equivariant",
        "invariant",
        "group",
        "manifold",
    ],
    "ood_generalization": [
        "generalization",
        "domain",
        "shortcut",
        "underspecification",
        "robust",
        "out-of-distribution",
    ],
    "meaning_mind": [
        "meaning",
        "mind",
        "conscious",
        "phenomenology",
        "cognition",
        "attention",
    ],
    "description_length": [
        "minimum description length",
        "mdl",
        "simplicity",
        "algorithmic probability",
        "inductive inference",
    ],
    "world_models": [
        "world model",
        "latent state",
        "representation",
        "object-centric",
        "planning",
    ],
}

FOUNDATIONAL_HINTS = {
    "active inference": "active inference and precision/value-of-information framing",
    "adaptive thresholds in change-point detection": "change-point detection and adaptive alarms",
    "ashby": "homeostasis, regulation, and requisite variety",
    "aubin": "viability theory and constrained dynamical systems",
    "bald": "Bayesian active learning and expected information gain",
    "canguilhem": "normativity, pathology, and organism-relative function",
    "contrastive predictive coding": "contrastive representation learning",
    "cusum": "sequential change detection",
    "dewey": "inquiry as situated corrective action",
    "friston": "free-energy principle and active inference",
    "gibson": "ecological perception and affordances",
    "goodhart": "measurement collapse under optimization pressure",
    "habituation": "response attenuation under repeated stimulation",
    "heidegger": "being-in-the-world and practical involvement",
    "jonas": "organism-centered value and biological normativity",
    "k-means": "online clustering and vector quantization",
    "maturana": "autopoiesis and self-producing organization",
    "page-hinkley": "online distribution-shift alarms",
    "pearl": "causal mediation and intervention calculus",
    "refractory": "post-activation suppression in neural systems",
    "settles": "active learning survey and query strategies",
    "simondon": "individuation and metastable systems",
    "uexkull": "umwelt and organism-relative worlds",
    "vervaeke": "relevance realization and meaning-making",
}

TITLE_ARXIV_OVERRIDES = {
    "agentbench: evaluating llms as agents": "2308.03688",
    "challenging common assumptions in the unsupervised learning of disentangled representations": "1811.12359",
    "concrete problems in ai safety": "1606.06565",
    "domain generalization: a survey": "2103.02503",
    "geometric deep learning": "2104.13478",
    "how to create conscious machines": "2403.00644",
    "invariant risk minimization": "1907.02893",
    "locating and editing factual associations in gpt": "2202.05262",
    "object-centric architectures enable efficient causal representation learning": "2310.19054",
    "on the ability of deep networks to learn symmetries from data": "2412.11521",
    "on the computation of meaning, language models and incomprehensible horrors": "2304.12686",
    "on the computation of meaning, language models, and incomprehensible horrors": "2304.12686",
    "osworld: benchmarking multimodal agents for open-ended tasks in real computer environments": "2404.07972",
    "react: synergizing reasoning and acting in language models": "2210.03629",
    "reflexion: language agents with verbal reinforcement learning": "2303.11366",
    "shortcut learning in deep neural networks": "2004.07780",
    "simple and scalable predictive uncertainty estimation using deep ensembles": "1612.01474",
    "swe-bench: can language models resolve real-world github issues?": "2310.06770",
    "toolformer: language models can teach themselves to use tools": "2302.04761",
    "tree of thoughts: deliberate problem solving with large language models": "2305.10601",
    "voyager: an open-ended embodied agent with large language models": "2305.16291",
    "webarena: a realistic web environment for building autonomous agents": "2307.13854",
    "weakly supervised causal representation learning": "2203.16437",
    "what uncertainties do we need in bayesian deep learning for computer vision?": "1703.04977",
    "world models": "1803.10122",
}

TITLE_DOI_OVERRIDES = {
    "technological approach to mind everywhere": "10.3389/fnsys.2022.768201",
    "technological approach to mind everywhere: an experimentally-grounded framework for understanding diverse bodies and minds": "10.3389/fnsys.2022.768201",
    "toward causal representation learning": "10.1109/JPROC.2021.3058954",
}


@dataclass
class SourceCandidate:
    candidate_id: str
    audit_ids: list[str]
    source_files: list[str]
    audit_kinds: list[str]
    raw_reference: str
    extracted_title: str
    year_hint: str
    arxiv_id: str
    doi_hint: str
    query: str


@dataclass
class EnrichedSource:
    candidate_id: str
    status: str
    evidence_level: str
    source_kind: str
    title: str
    authors: str
    year: str
    venue: str
    doi: str
    url: str
    arxiv_id: str
    topics: str
    abstract_available: bool
    abstract_summary: str
    relevance_to_corpus: str
    limitations: str
    audit_ids: str
    source_files: str
    raw_reference: str


def clean_text(text: str) -> str:
    replacements = {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def stable_id(prefix: str, text: str) -> str:
    digest = hashlib.sha1(clean_text(text).lower().encode("utf-8")).hexdigest()[:10]
    return f"{prefix}{digest}"


def split_bundled_references(raw: str) -> list[str]:
    raw = clean_text(raw)
    if len(raw) < 260:
        return [raw]

    starts = [0]
    pattern = re.compile(
        r"(?<=\.)\s+(?=[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]*[a-z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]*(?:,| and | & ).{0,180}?"
        r"(?:\(\d{4}\)|\(\)|arXiv:\s*\d{4}\.\d{4,5}))"
    )
    for match in pattern.finditer(raw):
        starts.append(match.end())
    starts = sorted(set(starts))
    if len(starts) == 1:
        return [raw]
    parts: list[str] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(raw)
        part = raw[start:end].strip()
        if part:
            parts.append(part)
    return parts


def extract_arxiv_id(text: str) -> str:
    match = re.search(r"arXiv:?\s*(\d{4}\.\d{4,5})(?:v\d+)?", text, re.IGNORECASE)
    return match.group(1) if match else ""


def extract_doi(text: str) -> str:
    match = re.search(r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", text, re.IGNORECASE)
    return match.group(1).rstrip(".") if match else ""


def extract_year(text: str) -> str:
    years = re.findall(r"(?:\(|\b)(19\d{2}|20\d{2})(?:\)|\b)", text)
    return years[-1] if years else ""


def extract_title(text: str) -> str:
    text = clean_text(text)
    arxiv_removed = re.sub(r"\barXiv preprint arXiv:?\s*\d{4}\.\d{4,5}\b", "", text, flags=re.I)
    after_year = re.search(r"\(\d{4}\)\.?\s+(.+?)(?:\.|$)", arxiv_removed)
    if after_year:
        return clean_text(after_year.group(1))

    # Pattern used by several BibTeX-ish fragments: "Authors (). Title. arXiv..."
    empty_year = re.search(r"\(\)\.?\s+(.+?)(?:\.|$)", arxiv_removed)
    if empty_year:
        return clean_text(empty_year.group(1))

    # Author initials often create short periods before the actual title. Take
    # the longest title-like segment before venue/year/arXiv markers.
    stripped = re.sub(r"\barXiv:?\s*\d{4}\.\d{4,5}.*$", "", arxiv_removed, flags=re.I)
    segments = [clean_text(s) for s in stripped.split(".") if clean_text(s)]
    titleish = [
        s
        for s in segments
        if len(s.split()) >= 4
        and not re.search(r"^[A-Z](?:,|$)", s)
        and not re.search(r"^(ICML|ICLR|NeurIPS|JMLR|MIT Press|Springer)$", s, re.I)
    ]
    if titleish:
        return max(titleish, key=len)
    return clean_text(stripped[:180])


def apply_identifier_overrides(raw: str, title: str, arxiv_id: str, doi: str) -> tuple[str, str]:
    haystack = clean_text(f"{title} {raw}").lower()
    if not arxiv_id:
        for phrase, override in TITLE_ARXIV_OVERRIDES.items():
            if phrase in haystack:
                arxiv_id = override
                break
    if not doi:
        for phrase, override in TITLE_DOI_OVERRIDES.items():
            if phrase in haystack:
                doi = override
                break
    return arxiv_id, doi


def make_query(raw: str, title: str) -> str:
    if title and len(title.split()) >= 3:
        return title
    without_arxiv = re.sub(r"arXiv.*$", "", raw, flags=re.I)
    without_authors = re.sub(r"^[^.]{0,160}\(\d{4}\)\.?\s*", "", without_arxiv)
    return clean_text(without_authors[:180] or raw[:180])


def title_tokens(text: str) -> set[str]:
    stop = {
        "and",
        "the",
        "for",
        "with",
        "from",
        "into",
        "that",
        "this",
        "what",
        "when",
        "using",
        "use",
        "are",
        "can",
        "how",
        "why",
        "via",
        "under",
        "toward",
        "towards",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in stop
    }


def metadata_match_ok(candidate: SourceCandidate, returned_title: str, exact_id: bool) -> bool:
    if exact_id:
        return True
    query = candidate.extracted_title or candidate.query
    if len(query.split()) < 3 or not returned_title:
        return False
    query_norm = clean_text(query).lower()
    title_norm = clean_text(returned_title).lower()
    ratio = SequenceMatcher(None, query_norm, title_norm).ratio()
    query_tokens = title_tokens(query_norm)
    returned_tokens = title_tokens(title_norm)
    if not query_tokens:
        return False
    overlap = len(query_tokens & returned_tokens) / len(query_tokens)
    return ratio >= 0.62 or (overlap >= 0.55 and len(query_tokens & returned_tokens) >= 3)


def build_candidates() -> list[SourceCandidate]:
    rows = json.loads(CITATION_LEDGER.read_text())
    grouped: dict[str, SourceCandidate] = {}
    for row in rows:
        if row["kind"] in NON_EXTERNAL_KINDS:
            continue
        for part in split_bundled_references(row["raw"]):
            if len(part) < 8:
                continue
            arxiv_id = extract_arxiv_id(part)
            doi = extract_doi(part)
            title = extract_title(part)
            arxiv_id, doi = apply_identifier_overrides(part, title, arxiv_id, doi)
            year = extract_year(part)
            query = make_query(part, title)
            key_text = arxiv_id or doi.lower() or title.lower() or part.lower()
            key = stable_id("S", key_text)
            if key not in grouped:
                grouped[key] = SourceCandidate(
                    candidate_id=key,
                    audit_ids=[],
                    source_files=[],
                    audit_kinds=[],
                    raw_reference=part,
                    extracted_title=title,
                    year_hint=year,
                    arxiv_id=arxiv_id,
                    doi_hint=doi,
                    query=query,
                )
            candidate = grouped[key]
            candidate.audit_ids.append(row["id"])
            candidate.audit_kinds.append(row["kind"])
            candidate.source_files.extend(row["source_files"])
    for candidate in grouped.values():
        candidate.audit_ids = sorted(set(candidate.audit_ids))
        candidate.audit_kinds = sorted(set(candidate.audit_kinds))
        candidate.source_files = sorted(set(candidate.source_files))
    return sorted(grouped.values(), key=lambda item: (item.extracted_title.lower(), item.candidate_id))


def fetch_url(url: str, cache_key: str, delay: float = 0.12) -> Any:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{cache_key}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "research-derived-experiments-citation-audit/1.0",
            "Accept": "application/json, application/atom+xml",
        },
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8", errors="replace")
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 2:
                time.sleep(2.5 * (attempt + 1))
                continue
            payload = {"error": f"{type(exc).__name__}: {exc}"}
            if exc.code != 429:
                cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
            return payload
        except Exception as exc:  # noqa: BLE001 - recorded in evidence ledger
            payload = {"error": f"{type(exc).__name__}: {exc}"}
            cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
            return payload
    time.sleep(delay)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = {"raw_xml": body}
    cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def abstract_from_openalex(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    positions: dict[int, str] = {}
    for word, indexes in inverted_index.items():
        for index in indexes:
            positions[index] = word
    return clean_text(" ".join(positions[index] for index in sorted(positions)))


def summarize_abstract(title: str, abstract: str, fallback: str) -> str:
    if not abstract:
        return fallback
    sentences = re.split(r"(?<=[.!?])\s+", clean_text(abstract))
    selected = []
    for sentence in sentences:
        lower = sentence.lower()
        if any(word in lower for word in ("show", "propose", "find", "demonstrate", "introduce", "argue")):
            selected.append(sentence)
        if len(selected) >= 2:
            break
    if not selected:
        selected = sentences[:2]
    summary = " ".join(selected)
    if len(summary) > 520:
        summary = summary[:517].rsplit(" ", 1)[0] + "..."
    return clean_text(summary or f"Metadata resolved for {title}, but the abstract did not parse cleanly.")


def classify_topics(text: str) -> list[str]:
    lower = text.lower()
    topics = [
        topic
        for topic, keywords in TOPIC_KEYWORDS.items()
        if any(keyword in lower for keyword in keywords)
    ]
    return topics or ["general_foundation"]


def relevance_note(topics: list[str]) -> str:
    notes = {
        "causal_representation": "Grounds claims that intervention, factorization, and object-level mechanisms are needed for representations to support counterfactual generalization.",
        "agency_viability": "Grounds the corpus's view of agents as bounded systems that preserve viability through regulation, control, and adaptive coupling.",
        "uncertainty_inquiry": "Grounds probe-value, reengagement, and inquiry claims in epistemic uncertainty, expected information gain, and active sampling.",
        "geometry_symmetry": "Grounds the geometric side of the corpus: invariances, equivariances, group actions, manifolds, and latent structure.",
        "ood_generalization": "Grounds warnings about shortcut solutions, underspecification, and failures of in-distribution success to imply robust transfer.",
        "meaning_mind": "Grounds the philosophical/neurobiological bridge from signal processing to meaning, relevance, attention, and organism-relative worlds.",
        "description_length": "Grounds simplicity, compression, and inductive-bias interpretations of generalization.",
        "world_models": "Grounds the world-model and latent-state framing used across intervention, planning, and causal representation papers.",
        "general_foundation": "Provides background literature context; its exact role needs manual section-level placement.",
    }
    return " ".join(notes[topic] for topic in topics[:3])


def manual_fallback(candidate: SourceCandidate) -> tuple[str, str]:
    text = f"{candidate.raw_reference} {candidate.extracted_title}".lower()
    for hint, note in FOUNDATIONAL_HINTS.items():
        if hint in text:
            return (
                "manual_foundational_reference",
                f"Resolved as a foundational topic rather than a single metadata record: {note}. Use as conceptual background and repair the exact bibliographic target before final publication.",
            )
    return (
        "unresolved_external_reference",
        "No reliable external metadata/abstract was recovered automatically. Keep this row in the running bibliography-repair queue.",
    )


def query_arxiv(arxiv_id: str) -> dict[str, str]:
    url = f"{ARXIV_API}?id_list={urllib.parse.quote(arxiv_id)}"
    payload = fetch_url(url, f"arxiv_{arxiv_id.replace('.', '_')}", delay=0.25)
    raw_xml = payload.get("raw_xml", "") if isinstance(payload, dict) else ""
    if not raw_xml:
        return {}
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw_xml)
    entry = root.find("atom:entry", ns)
    if entry is None:
        return {}
    authors = [
        clean_text(author.findtext("atom:name", default="", namespaces=ns))
        for author in entry.findall("atom:author", ns)
    ]
    return {
        "title": clean_text(entry.findtext("atom:title", default="", namespaces=ns)),
        "authors": "; ".join(author for author in authors if author),
        "year": clean_text((entry.findtext("atom:published", default="", namespaces=ns) or "")[:4]),
        "venue": "arXiv",
        "doi": "",
        "url": clean_text(entry.findtext("atom:id", default="", namespaces=ns)),
        "abstract": clean_text(entry.findtext("atom:summary", default="", namespaces=ns)),
    }


def semantic_fields() -> str:
    return "title,abstract,year,authors,venue,url,externalIds"


def semantic_to_metadata(result: dict[str, Any]) -> dict[str, str]:
    authors = [author.get("name", "") for author in result.get("authors", [])[:8]]
    external_ids = result.get("externalIds") or {}
    doi = external_ids.get("DOI", "")
    arxiv_id = external_ids.get("ArXiv", "")
    return {
        "title": clean_text(result.get("title") or ""),
        "authors": "; ".join(author for author in authors if author),
        "year": str(result.get("year") or ""),
        "venue": clean_text(result.get("venue") or ""),
        "doi": clean_text(doi),
        "url": clean_text(result.get("url") or ""),
        "abstract": clean_text(result.get("abstract") or ""),
        "arxiv_id": clean_text(arxiv_id),
    }


def query_semantic_scholar(candidate: SourceCandidate) -> dict[str, str]:
    exact_ids = []
    if candidate.arxiv_id:
        exact_ids.append(f"ARXIV:{candidate.arxiv_id}")
    if candidate.doi_hint:
        exact_ids.append(f"DOI:{candidate.doi_hint}")
    for exact_id in exact_ids:
        url = f"{SEMANTIC_SCHOLAR_API}/{urllib.parse.quote(exact_id, safe=':')}?fields={semantic_fields()}"
        payload = fetch_url(
            url,
            stable_id("s2_exact_", exact_id),
            delay=0.9,
        )
        if isinstance(payload, dict) and not payload.get("error") and payload.get("title"):
            return semantic_to_metadata(payload)
    return {}


def query_openalex(candidate: SourceCandidate) -> dict[str, str]:
    exact_id = bool(candidate.doi_hint)
    params = {
        "search": candidate.query,
        "per-page": "1",
        "mailto": MAILTO,
    }
    if candidate.doi_hint:
        params = {"filter": f"doi:{candidate.doi_hint}", "per-page": "1", "mailto": MAILTO}
    url = f"{OPENALEX_API}?{urllib.parse.urlencode(params)}"
    payload = fetch_url(url, stable_id("openalex_", json.dumps(params, sort_keys=True)))
    if not isinstance(payload, dict) or payload.get("error"):
        return {}
    results = payload.get("results") or []
    if not results:
        return {}
    result = results[0]
    returned_title = clean_text(result.get("title") or "")
    if not metadata_match_ok(candidate, returned_title, exact_id=exact_id):
        return {}
    authors = []
    for authorship in result.get("authorships", [])[:8]:
        author = authorship.get("author", {}).get("display_name", "")
        if author:
            authors.append(author)
    primary_location = result.get("primary_location") or {}
    venue = (
        (primary_location.get("source") or {}).get("display_name", "")
        or (result.get("host_venue") or {}).get("display_name", "")
    )
    return {
        "title": returned_title,
        "authors": "; ".join(authors),
        "year": str(result.get("publication_year") or ""),
        "venue": clean_text(venue),
        "doi": clean_text(result.get("doi") or ""),
        "url": clean_text(result.get("id") or result.get("doi") or ""),
        "abstract": abstract_from_openalex(result.get("abstract_inverted_index")),
    }


def enrich_candidate(candidate: SourceCandidate) -> EnrichedSource:
    arxiv = query_arxiv(candidate.arxiv_id) if candidate.arxiv_id else {}
    semantic = query_semantic_scholar(candidate) if not arxiv else {}
    openalex = query_openalex(candidate)
    metadata = arxiv or semantic or openalex
    fallback_status, fallback_note = manual_fallback(candidate)
    title = metadata.get("title") or candidate.extracted_title or candidate.query
    abstract = metadata.get("abstract", "")
    topics = classify_topics(" ".join([title, abstract, candidate.raw_reference]))
    if metadata:
        status = "resolved_with_abstract" if abstract else "resolved_metadata_only"
        evidence_level = "abstract_read" if abstract else "metadata_read"
        source_kind = "arxiv" if arxiv else "semantic_scholar" if semantic else "openalex"
        summary = summarize_abstract(title, abstract, fallback_note)
        limitations = (
            "Abstract metadata was available; full text was not automatically read in this pass."
            if abstract
            else "Metadata resolved, but no abstract was exposed by the queried endpoint."
        )
    else:
        status = fallback_status
        evidence_level = "topic_inferred_from_citation_fragment"
        source_kind = "manual_topic_seed"
        summary = fallback_note
        limitations = "Requires manual bibliographic resolution before it can support a strong literature-review claim."
    return EnrichedSource(
        candidate_id=candidate.candidate_id,
        status=status,
        evidence_level=evidence_level,
        source_kind=source_kind,
        title=title,
        authors=metadata.get("authors", ""),
        year=metadata.get("year") or candidate.year_hint,
        venue=metadata.get("venue", ""),
        doi=metadata.get("doi") or candidate.doi_hint,
        url=metadata.get("url", ""),
        arxiv_id=candidate.arxiv_id,
        topics=";".join(topics),
        abstract_available=bool(abstract),
        abstract_summary=summary,
        relevance_to_corpus=relevance_note(topics),
        limitations=limitations,
        audit_ids=";".join(candidate.audit_ids),
        source_files=";".join(candidate.source_files),
        raw_reference=candidate.raw_reference,
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_source_notes(enriched: list[EnrichedSource]) -> None:
    by_topic: dict[str, list[EnrichedSource]] = {}
    for source in enriched:
        for topic in source.topics.split(";"):
            by_topic.setdefault(topic, []).append(source)
    lines = [
        "# External Citation Source Notes",
        "",
        "This is the running evidence notebook for citations that appear inside the authored papers. It is generated from the local audit ledger plus external scholarly metadata/abstract lookups. Abstract summaries are paraphrased/condensed; the raw abstracts are not reproduced.",
        "",
        "## Coverage",
        "",
        f"- External/reference candidates after atomizing bundled rows: {len(enriched)}",
        f"- Resolved with abstracts: {sum(1 for row in enriched if row.status == 'resolved_with_abstract')}",
        f"- Resolved with metadata only: {sum(1 for row in enriched if row.status == 'resolved_metadata_only')}",
        f"- Foundational/manual topic seeds: {sum(1 for row in enriched if row.status == 'manual_foundational_reference')}",
        f"- Unresolved bibliographic fragments: {sum(1 for row in enriched if row.status == 'unresolved_external_reference')}",
        "",
        "## Topic Notes",
        "",
    ]
    for topic in sorted(by_topic):
        rows = sorted(by_topic[topic], key=lambda item: (item.year, item.title))
        lines.extend([f"### {topic.replace('_', ' ').title()}", ""])
        for row in rows:
            source_label = f"{row.title} ({row.year or 'n.d.'})"
            if row.authors:
                source_label = f"{row.authors.split(';')[0]} - {source_label}"
            lines.extend(
                [
                    f"#### {source_label}",
                    "",
                    f"- Status: {row.status}; evidence level: {row.evidence_level}.",
                    f"- Citation source rows: {row.audit_ids}.",
                    f"- What the abstract/metadata contributes: {row.abstract_summary}",
                    f"- Relevance to our corpus: {row.relevance_to_corpus}",
                    f"- Limitation: {row.limitations}",
                    f"- URL/DOI: {row.url or row.doi or row.arxiv_id or 'not resolved'}",
                    "",
                ]
            )
    (OUT_DIR / "source_notes.md").write_text("\n".join(lines) + "\n")


def write_claim_matrix(enriched: list[EnrichedSource]) -> None:
    claims = {
        "Viability and agency": "agency_viability",
        "Interventions expose latent structure": "causal_representation",
        "Probe value is expected information gain under cost": "uncertainty_inquiry",
        "Robust generalization requires invariants, not surface fit": "ood_generalization",
        "Geometry and symmetry compress model behavior": "geometry_symmetry",
        "Meaning is organism/world-relative relevance, not raw token prediction": "meaning_mind",
        "Simplicity and description length explain part of inductive bias": "description_length",
        "World models need sufficient latent state for planning": "world_models",
    }
    lines = [
        "# Claim Evidence Matrix",
        "",
        "| Review claim | Supporting citation evidence | Remaining caveat |",
        "|---|---|---|",
    ]
    for claim, topic in claims.items():
        rows = [row for row in enriched if topic in row.topics.split(";")]
        rows = sorted(
            rows,
            key=lambda row: (
                row.status != "resolved_with_abstract",
                row.status != "resolved_metadata_only",
                row.year,
                row.title,
            ),
        )[:8]
        support = "<br>".join(
            f"{row.title} ({row.year or 'n.d.'}) - {row.evidence_level}" for row in rows
        )
        if not support:
            support = "No resolved external source yet."
        caveat = "Use abstract-level support unless full text is locally available or manually read."
        if any(row.status == "unresolved_external_reference" for row in rows):
            caveat = "Some supporting rows are still unresolved fragments; repair bibliography before publication."
        lines.append(f"| {claim} | {support} | {caveat} |")
    (OUT_DIR / "claim_evidence_matrix.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidates = build_candidates()
    enriched = [enrich_candidate(candidate) for candidate in candidates]
    rows = [asdict(row) for row in enriched]
    (OUT_DIR / "external_citation_ledger.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )
    write_csv(OUT_DIR / "external_citation_ledger.csv", rows)
    write_source_notes(enriched)
    write_claim_matrix(enriched)
    summary = {
        "candidate_count": len(enriched),
        "status_counts": {
            status: sum(1 for row in enriched if row.status == status)
            for status in sorted({row.status for row in enriched})
        },
        "evidence_level_counts": {
            level: sum(1 for row in enriched if row.evidence_level == level)
            for level in sorted({row.evidence_level for row in enriched})
        },
        "topic_counts": {
            topic: sum(1 for row in enriched if topic in row.topics.split(";"))
            for topic in sorted({topic for row in enriched for topic in row.topics.split(";")})
        },
    }
    (OUT_DIR / "enrichment_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
