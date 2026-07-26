"""DCR1b — the same question, with repaired instruments.

Gates frozen in ``DCR1B_PREREGISTRATION.md``, whose §0 states exactly which of
them were seen before freezing and which were not. Local CPU, seconds.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr1b
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.consensus import PASS_DIRS
from experiments.date_cut_retrodiction.corpus import sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.fetch import DATA_DIR, load_document
from experiments.date_cut_retrodiction.residue_v2 import audit_residue_v2
from experiments.date_cut_retrodiction.run_dcr1 import (
    QUOTE_FIDELITY_GATE,
    RESIDUE_RATE_GATE,
    SCHEMA_WORDS,
    load_extractions,
    verify_quotes,
)
from experiments.date_cut_retrodiction.target_v2 import (
    FACET_QUORUM_V2,
    TARGET_FACETS_V2,
    match_facets_v2,
)


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
CONSENSUS_DIR: Final[Path] = _PACKAGE / "extractions_consensus"
ADJUDICATION: Final[Path] = _PACKAGE / "results" / "dcr1b_facet_adjudication.json"


def _facets_for(
    extractions: dict[str, list[dict[str, Any]]], year: int, *, allow_risk: bool = True
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    doc_ids = [
        s.doc_id for s in sources_at_or_before(year, allow_provenance_risk=allow_risk)
    ]
    propositions = [p for d in doc_ids for p in extractions.get(d, [])]
    hits = match_facets_v2(propositions)
    return sorted(k for k, v in hits.items() if v), propositions, doc_ids


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DCR1b.")
    parser.add_argument("--extractions", type=Path, default=CONSENSUS_DIR)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--out", type=Path, default=_PACKAGE / "results" / "dcr1b_verdict.json")
    args = parser.parse_args(argv)

    consensus = load_extractions(args.extractions)
    quotes = verify_quotes(consensus, data_dir=args.data_dir)

    by_cut: dict[str, Any] = {}
    for cut in CUTS:
        for allow_risk in (True, False):
            facets, propositions, doc_ids = _facets_for(
                consensus, cut.year, allow_risk=allow_risk
            )
            documents = [load_document(d, data_dir=args.data_dir) for d in doc_ids]
            outputs = [
                f"{p.get('name', '')} {p.get('statement', '')}" for p in propositions
            ]
            residue = audit_residue_v2(
                outputs, documents, cut_year=cut.year, allow=SCHEMA_WORDS
            )
            hits = match_facets_v2(propositions)
            by_cut[f"{cut.year}_{'all' if allow_risk else 'norisk'}"] = {
                "cut_year": cut.year,
                "label": cut.label,
                "is_placebo": cut.is_placebo,
                "allow_provenance_risk": allow_risk,
                "n_documents": len(doc_ids),
                "n_propositions": len(propositions),
                "residue_rate": residue.residue_rate,
                "residue_types": list(residue.residue_types)[:60],
                "facets_present": facets,
                "surfaces_target": len(facets) >= FACET_QUORUM_V2,
                "facet_counts": {k: len(v) for k, v in hits.items()},
                "facet_hits": {k: list(v) for k, v in hits.items() if v},
            }

    primary = {k: v for k, v in by_cut.items() if v["allow_provenance_risk"]}
    deep = next(v for v in primary.values() if v["cut_year"] == 1880)
    target = next(v for v in primary.values() if v["cut_year"] == 1904)

    # H6 -- does the verdict survive using each sandboxed pass alone?
    per_pass: dict[str, Any] = {}
    for directory in PASS_DIRS:
        single = load_extractions(directory)
        per_pass[directory.name] = {
            str(cut.year): _facets_for(single, cut.year)[0] for cut in CUTS
        }
    consensus_facets = {str(v["cut_year"]): v["facets_present"] for v in primary.values()}
    h6 = all(rows == consensus_facets for rows in per_pass.values())

    # H5 -- adjudication is a human read, recorded as an artifact.
    adjudication = (
        json.loads(ADJUDICATION.read_text()) if ADJUDICATION.is_file() else None
    )
    h5 = bool(adjudication and adjudication.get("all_hits_genuine") is True)

    h1 = quotes.fidelity >= QUOTE_FIDELITY_GATE
    h2 = all(v["residue_rate"] < RESIDUE_RATE_GATE for v in primary.values())
    h3 = not deep["surfaces_target"]
    h4 = target["surfaces_target"]

    verdict: dict[str, Any] = {
        "kind": "dcr1b_verdict",
        "extraction": "consensus over sandboxed passes",
        "n_documents": len(consensus),
        "n_propositions": sum(len(v) for v in consensus.values()),
        "quote_audit": {
            "n_total": quotes.n_total,
            "n_exact": quotes.n_exact,
            "n_normalised": quotes.n_normalised,
            "fidelity": quotes.fidelity,
        },
        "cuts": by_cut,
        "facet_definitions": {f.key: f.description for f in TARGET_FACETS_V2},
        "per_pass_facets": per_pass,
        "consensus_facets": consensus_facets,
        "H1_quote_fidelity": {
            "value": quotes.fidelity,
            "threshold": QUOTE_FIDELITY_GATE,
            "decision": "GO" if h1 else "NO_GO",
        },
        "H2_vocabulary_residue_v2": {
            "max_rate": max((v["residue_rate"] for v in primary.values()), default=0.0),
            "threshold": RESIDUE_RATE_GATE,
            "decision": "GO" if h2 else "NO_GO",
        },
        "H3_deep_placebo_silent": {
            "facets_present_1880": deep["facets_present"],
            "decision": "GO" if h3 else "NO_GO",
        },
        "H4_target_cut_not_silent": {
            "facets_present_1904": target["facets_present"],
            "decision": "GO" if h4 else "NO_GO",
        },
        "H5_matcher_soundness": {
            "adjudication_present": adjudication is not None,
            "all_hits_genuine": bool(adjudication and adjudication.get("all_hits_genuine")),
            "decision": "GO" if h5 else "NO_GO",
        },
        "H6_robustness_across_passes": {
            "per_pass": per_pass,
            "consensus": consensus_facets,
            "decision": "GO" if h6 else "NO_GO",
        },
        "overall_decision": "GO" if all((h1, h2, h3, h4, h5, h6)) else "NO_GO",
        "dcr2_licensed": all((h1, h2, h3, h4, h5, h6)),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
