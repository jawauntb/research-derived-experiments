"""DCR1 — is the extractor leaking?

Gates frozen in ``DCR1_PREREGISTRATION.md``, written before any extraction
output was read. Local CPU, seconds.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr1
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.corpus import sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.fetch import DATA_DIR, load_document
from experiments.date_cut_retrodiction.residue import audit_residue, stemmed_residue
from experiments.date_cut_retrodiction.target import (
    FACET_QUORUM,
    TARGET_FACETS,
    match_facets,
)


__all__ = ["main", "verify_quotes", "load_extractions"]

EXTRACTION_DIR: Final[Path] = Path(__file__).resolve().parent / "extractions"
RESULTS_DIR: Final[Path] = Path(__file__).resolve().parent / "results"

QUOTE_FIDELITY_GATE: Final[float] = 0.90
RESIDUE_RATE_GATE: Final[float] = 0.05

#: Words the extraction schema itself introduces. Every entry is a declared
#: hole in the residue audit, so the list stays short.
SCHEMA_WORDS: Final[tuple[str, ...]] = (
    "asserted",
    "presupposed",
    "definitional",
    "commitment",
    "commitments",
)

_WS = re.compile(r"\s+")


def _normalise_ws(text: str) -> str:
    return _WS.sub(" ", text).strip().lower()


def load_extractions(directory: Path = EXTRACTION_DIR) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        doc_id = payload.get("doc_id", path.stem)
        propositions = payload.get("propositions", [])
        for proposition in propositions:
            proposition.setdefault("doc_id", doc_id)
        out[doc_id] = propositions
    return out


@dataclass(frozen=True)
class QuoteAudit:
    n_total: int
    n_exact: int
    n_normalised: int
    failures: tuple[tuple[str, str], ...]

    @property
    def fidelity(self) -> float:
        return 0.0 if not self.n_total else self.n_normalised / self.n_total


def verify_quotes(
    extractions: dict[str, list[dict[str, Any]]],
    *,
    data_dir: Path = DATA_DIR,
) -> QuoteAudit:
    """Check every quote against its source. No agent is trusted to have copied."""
    total = exact = normalised = 0
    failures: list[tuple[str, str]] = []

    for doc_id, propositions in extractions.items():
        source = load_document(doc_id, data_dir=data_dir)
        source_norm = _normalise_ws(source)
        for proposition in propositions:
            total += 1
            quote = str(proposition.get("quote", ""))
            if quote and quote in source:
                exact += 1
                normalised += 1
            elif quote and _normalise_ws(quote) in source_norm:
                normalised += 1
            else:
                failures.append((doc_id, str(proposition.get("name", ""))))

    return QuoteAudit(total, exact, normalised, tuple(failures))


def _cut_propositions(
    extractions: dict[str, list[dict[str, Any]]],
    year: int,
    *,
    allow_risk: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    doc_ids = [s.doc_id for s in sources_at_or_before(year, allow_provenance_risk=allow_risk)]
    propositions: list[dict[str, Any]] = []
    for doc_id in doc_ids:
        propositions.extend(extractions.get(doc_id, []))
    return propositions, doc_ids


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DCR1.")
    parser.add_argument("--extractions", type=Path, default=EXTRACTION_DIR)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "dcr1_verdict.json")
    args = parser.parse_args(argv)

    extractions = load_extractions(args.extractions)
    quotes = verify_quotes(extractions, data_dir=args.data_dir)

    by_cut: dict[str, Any] = {}
    for cut in CUTS:
        for allow_risk in (True, False):
            propositions, doc_ids = _cut_propositions(
                extractions, cut.year, allow_risk=allow_risk
            )
            documents = [load_document(d, data_dir=args.data_dir) for d in doc_ids]
            outputs = [
                f"{p.get('name', '')} {p.get('statement', '')}" for p in propositions
            ]
            residue = audit_residue(
                outputs, documents, cut_year=cut.year, allow=SCHEMA_WORDS
            )
            stemmed = stemmed_residue(outputs, documents, allow=SCHEMA_WORDS)
            facets = match_facets(propositions)
            present = [key for key, value in facets.items() if value]

            # The sharpest question the residue audit can answer: are the
            # propositions that MATCHED the target family themselves written in
            # words the corpus licenses? A leak elsewhere in the extraction is a
            # quality problem. A leak inside the facet hits would mean the target
            # signal is the model's vocabulary rather than the corpus's.
            facet_outputs = [
                f"{h.name} {h.statement}" for value in facets.values() for h in value
            ]
            facet_residue = stemmed_residue(
                facet_outputs, documents, allow=SCHEMA_WORDS
            )

            by_cut[f"{cut.year}_{'all' if allow_risk else 'norisk'}"] = {
                "cut_year": cut.year,
                "label": cut.label,
                "is_placebo": cut.is_placebo,
                "allow_provenance_risk": allow_risk,
                "n_documents": len(doc_ids),
                "n_propositions": len(propositions),
                "residue_rate": residue.residue_rate,
                "residue_types": list(residue.residue_types)[:80],
                "n_residue_types": len(residue.residue_types),
                "n_residue_types_stemmed": len(stemmed),
                "residue_types_stemmed": list(stemmed)[:80],
                "residue_rate_stemmed": (
                    0.0
                    if not residue.n_output_types
                    else len(stemmed) / residue.n_output_types
                ),
                "n_facet_hits": len(facet_outputs),
                "facet_hit_residue_types": list(facet_residue),
                "facet_hits_fully_licensed": not facet_residue,
                "sentinels_in_corpus": list(residue.sentinels_in_corpus),
                "facets_present": present,
                "n_facets_present": len(present),
                "surfaces_target": len(present) >= FACET_QUORUM,
                "facet_examples": {
                    key: [
                        {"doc_id": h.doc_id, "name": h.name, "statement": h.statement}
                        for h in value[:4]
                    ]
                    for key, value in facets.items()
                    if value
                },
            }

    primary = {k: v for k, v in by_cut.items() if v["allow_provenance_risk"]}
    deep = next(v for v in primary.values() if v["cut_year"] == 1880)
    target = next(v for v in primary.values() if v["cut_year"] == 1904)

    g1 = quotes.fidelity >= QUOTE_FIDELITY_GATE
    g2 = all(v["residue_rate"] < RESIDUE_RATE_GATE for v in primary.values())
    g3 = not deep["surfaces_target"]
    g4 = target["surfaces_target"]

    verdict: dict[str, Any] = {
        "kind": "dcr1_verdict",
        "n_documents_extracted": len(extractions),
        "quote_audit": {
            "n_total": quotes.n_total,
            "n_exact": quotes.n_exact,
            "n_normalised": quotes.n_normalised,
            "fidelity": quotes.fidelity,
            "failures": [list(f) for f in quotes.failures[:40]],
        },
        "cuts": by_cut,
        "facet_definitions": {f.key: f.description for f in TARGET_FACETS},
        "G1_quote_fidelity": {
            "value": quotes.fidelity,
            "threshold": QUOTE_FIDELITY_GATE,
            "decision": "GO" if g1 else "NO_GO",
        },
        "G2_vocabulary_residue": {
            "max_rate": max((v["residue_rate"] for v in primary.values()), default=0.0),
            "threshold": RESIDUE_RATE_GATE,
            "decision": "GO" if g2 else "NO_GO",
        },
        "G3_deep_placebo_silent": {
            "facets_present_1880": deep["facets_present"],
            "decision": "GO" if g3 else "NO_GO",
        },
        "G4_target_cut_not_silent": {
            "facets_present_1904": target["facets_present"],
            "decision": "GO" if g4 else "NO_GO",
        },
        "overall_decision": "GO" if (g1 and g2 and g3 and g4) else "NO_GO",
        "dcr2_licensed": bool(g1 and g2 and g3 and g4),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
