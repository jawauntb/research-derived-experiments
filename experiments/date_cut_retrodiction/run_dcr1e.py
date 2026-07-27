"""DCR1e — can any extraction surface an unstated presupposition?

Runs the presupposition-inferring extraction (see
``EXTRACTION_PROMPT_PRESUPPOSITION.md``) over the DCR1c corpus plus Newton,
builds a 2-of-3 consensus, scores the six Q-gates from
``DCR1E_PREREGISTRATION.md``. Every threshold is imported from DCR1's
runner as a constant so nothing here can be threshold-fitted.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr1e
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.consensus import build_consensus
from experiments.date_cut_retrodiction.corpus import sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.dcr1d import NEWTON_SOURCE, POSITIVE_CONTROL_CUT
from experiments.date_cut_retrodiction.dcr1e import (
    PRESUP_CONSENSUS_DIR,
    PRESUP_PASS_DIRS,
    SUPPORT_THRESHOLD_PRESUP,
)
from experiments.date_cut_retrodiction.fetch import DATA_DIR, load_document
from experiments.date_cut_retrodiction.residue_v2 import audit_residue_v2
from experiments.date_cut_retrodiction.run_dcr1 import (
    QUOTE_FIDELITY_GATE,
    RESIDUE_RATE_GATE,
    SCHEMA_WORDS,
    load_extractions,
    verify_quotes,
)
from experiments.date_cut_retrodiction.target_v3 import (
    match_facets_v3,
)


__all__ = ["main", "build_presup_consensus"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr1e_verdict.json"
ADJUDICATION_PATH: Final[Path] = _PACKAGE / "results" / "dcr1e_t1_adjudication.json"


def build_presup_consensus(out_dir: Path = PRESUP_CONSENSUS_DIR) -> dict[str, Any]:
    consensus, stats = build_consensus(
        PRESUP_PASS_DIRS, support_threshold=SUPPORT_THRESHOLD_PRESUP
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    for doc_id, propositions in consensus.items():
        (out_dir / f"{doc_id}.json").write_text(
            json.dumps(
                {
                    "doc_id": doc_id,
                    "propositions": [p.as_dict() for p in propositions],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    return stats


def _score_electrodynamics_cut(
    consensus: dict[str, list[dict[str, Any]]],
    year: int,
    *,
    allow_risk: bool,
    data_dir: Path,
) -> dict[str, Any]:
    """Score a DCR1c-era cut, deliberately EXCLUDING Newton from scope."""
    doc_ids = [
        s.doc_id
        for s in sources_at_or_before(year, allow_provenance_risk=allow_risk)
    ]
    propositions: list[dict[str, Any]] = []
    for doc_id in doc_ids:
        propositions.extend(consensus.get(doc_id, []))

    documents = [load_document(doc_id, data_dir=data_dir) for doc_id in doc_ids]
    outputs = [f"{p.get('name', '')} {p.get('statement', '')}" for p in propositions]
    residue = audit_residue_v2(outputs, documents, cut_year=year, allow=SCHEMA_WORDS)
    hits = match_facets_v3(propositions)

    return {
        "cut_year": year,
        "allow_provenance_risk": allow_risk,
        "n_documents": len(doc_ids),
        "n_propositions": len(propositions),
        "residue_rate": residue.residue_rate,
        "facet_counts": {k: len(v) for k, v in hits.items()},
        "facet_hits": {k: list(v) for k, v in hits.items() if v},
    }


def _score_newton(
    consensus: dict[str, list[dict[str, Any]]], *, data_dir: Path
) -> dict[str, Any]:
    doc_id = NEWTON_SOURCE.doc_id
    propositions = consensus.get(doc_id, [])
    document = load_document(doc_id, data_dir=data_dir)
    outputs = [f"{p.get('name', '')} {p.get('statement', '')}" for p in propositions]
    residue = audit_residue_v2(
        outputs, [document], cut_year=POSITIVE_CONTROL_CUT.year, allow=SCHEMA_WORDS
    )
    hits = match_facets_v3(propositions)
    return {
        "cut_year": POSITIVE_CONTROL_CUT.year,
        "n_documents": 1,
        "n_propositions": len(propositions),
        "residue_rate": residue.residue_rate,
        "facet_counts": {k: len(v) for k, v in hits.items()},
        "T1_hits": [
            {"name": h.get("name"), "statement": h["statement"]}
            for h in hits.get("T1_absolute_simultaneity", ())
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DCR1e presupposition extraction.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    consensus_stats = build_presup_consensus()
    consensus = load_extractions(PRESUP_CONSENSUS_DIR)
    quotes = verify_quotes(consensus, data_dir=args.data_dir)

    electrodynamics_cuts: dict[str, Any] = {}
    for cut in CUTS:
        for allow_risk in (True, False):
            row = _score_electrodynamics_cut(
                consensus, cut.year, allow_risk=allow_risk, data_dir=args.data_dir
            )
            row["label"] = cut.label
            row["is_placebo"] = cut.is_placebo
            electrodynamics_cuts[f"{cut.year}_{'all' if allow_risk else 'norisk'}"] = row

    newton = _score_newton(consensus, data_dir=args.data_dir)

    primary = {k: v for k, v in electrodynamics_cuts.items() if v["allow_provenance_risk"]}
    deep = next(v for v in primary.values() if v["cut_year"] == 1880)
    near = next(v for v in primary.values() if v["cut_year"] == 1897)
    target = next(v for v in primary.values() if v["cut_year"] == 1904)

    t1_1880 = deep["facet_hits"].get("T1_absolute_simultaneity", [])
    t1_1897 = near["facet_hits"].get("T1_absolute_simultaneity", [])
    t1_1904 = target["facet_hits"].get("T1_absolute_simultaneity", [])

    adjudication = (
        json.loads(ADJUDICATION_PATH.read_text())
        if ADJUDICATION_PATH.is_file()
        else None
    )

    q1 = quotes.fidelity >= QUOTE_FIDELITY_GATE
    q2 = all(v["residue_rate"] < RESIDUE_RATE_GATE for v in primary.values()) and (
        newton["residue_rate"] < RESIDUE_RATE_GATE
    )
    q3 = bool(t1_1897)
    q4 = not t1_1880
    q5 = bool(adjudication and adjudication.get("all_hits_genuine")) if t1_1897 else None
    q6 = bool(newton["T1_hits"])

    q5_decision: str
    if q5 is None:
        q5_decision = "N/A (Q3 NO_GO; nothing to adjudicate)"
    else:
        q5_decision = "GO" if q5 else "NO_GO"

    all_gates_pass = q1 and q2 and q3 and q4 and (q5 is True) and q6

    if all_gates_pass:
        reading = (
            "presupposition_extraction_works: DCR2 becomes meaningful on the "
            "enriched consensus"
        )
    elif q1 and q2 and q4 and not q3 and q6:
        reading = (
            "DR2_shaped_framework_limit: the prompt was strong enough to surface "
            "T1 on Newton but not on the electrodynamics corpus where the "
            "presupposition is used but not stated. Next paper is theorem-shaped."
        )
    elif q1 and q2 and q3 and not q4:
        reading = (
            "extractor_is_projecting: T1 fired at the 1880 deep placebo where "
            "the arguments requiring it do not exist. Q3 is uninterpretable. "
            "Prompt repair required."
        )
    elif not q6:
        reading = "prompt_broken: Newton sanity failed; repair prompt"
    else:
        reading = "mixed_or_inconclusive: see per-gate decisions"

    verdict: dict[str, Any] = {
        "kind": "dcr1e_verdict",
        "purpose": (
            "Can a presupposition-inferring extractor surface T1 (absolute "
            "simultaneity) from the electrodynamics corpus, where it is used "
            "but never stated?"
        ),
        "consensus_stats": consensus_stats,
        "n_documents": len(consensus),
        "n_propositions": sum(len(v) for v in consensus.values()),
        "quote_audit": {
            "n_total": quotes.n_total,
            "n_exact": quotes.n_exact,
            "n_normalised": quotes.n_normalised,
            "fidelity": quotes.fidelity,
        },
        "electrodynamics_cuts": electrodynamics_cuts,
        "newton_sanity": newton,
        "T1_hits_by_cut": {
            "1880": t1_1880,
            "1897": t1_1897,
            "1904": t1_1904,
        },
        "gates": {
            "Q1_quote_fidelity": {
                "value": quotes.fidelity,
                "threshold": QUOTE_FIDELITY_GATE,
                "decision": "GO" if q1 else "NO_GO",
            },
            "Q2_vocabulary_residue_v2": {
                "value_max_electrodynamics": max(
                    (v["residue_rate"] for v in primary.values()), default=0.0
                ),
                "value_newton": newton["residue_rate"],
                "threshold": RESIDUE_RATE_GATE,
                "decision": "GO" if q2 else "NO_GO",
            },
            "Q3_T1_fires_at_1897": {
                "n_hits": len(t1_1897),
                "decision": "GO" if q3 else "NO_GO",
            },
            "Q4_T1_silent_at_1880": {
                "n_hits": len(t1_1880),
                "decision": "GO" if q4 else "NO_GO",
            },
            "Q5_T1_hit_adjudicated_genuine": {
                "adjudication_present": adjudication is not None,
                "all_hits_genuine": q5,
                "decision": q5_decision,
            },
            "Q6_newton_sanity": {
                "n_hits": len(newton["T1_hits"]),
                "decision": "GO" if q6 else "NO_GO",
            },
        },
        "overall_decision": "GO" if all_gates_pass else "NO_GO",
        "licensed_reading": reading,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
