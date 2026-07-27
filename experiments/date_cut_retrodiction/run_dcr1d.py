"""DCR1d — positive control for the T1 matcher, on Newton's Scholium.

DCR1c passed every gate and reported one thing that did not fit: T1 matched
zero propositions at every cut, across all three sandboxed extractions. Two
readings, and DCR1c refused to decide between them: matcher can't do the job,
or the commitment isn't stated in the corpus.

DCR1d is the single experiment that discriminates them. It adds one document
that **does** state absolute time and absolute space in the exact vocabulary
the matcher was built to catch -- Newton's Scholium after the Definitions in
Book I of the Principia (Motte 1729 translation) -- and asks whether the
matcher fires. If it does, DCR1c's T1 absence is a fact about the
electrodynamics corpus. If it does not, DCR1c's T1 absence is a matcher
artifact and DCR2 is de-licensed pending repair.

Three gates, all must decide GO:

* **P1** quote fidelity on Newton >= 90%
* **P2** vocabulary residue on Newton < 5% (period-appropriate baseline)
* **P3** T1 fires at least once at the 1687 cut under either v2 or v3

DCR1c's ``SOURCES`` and ``CUTS`` are untouched; the positive-control source
and cut live in ``dcr1d.py``. DCR1c's numbers stay byte-identical.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr1d
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.consensus import build_consensus
from experiments.date_cut_retrodiction.dcr1d import (
    NEWTON_CONSENSUS_DIR,
    NEWTON_PASS_DIRS,
    NEWTON_SOURCE,
    POSITIVE_CONTROL_CUT,
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
from experiments.date_cut_retrodiction.target_v2 import (
    FACET_QUORUM_V2,
    match_facets_v2,
)
from experiments.date_cut_retrodiction.target_v3 import (
    FACET_QUORUM_V3,
    compare_v2_v3,
    match_facets_v3,
)


__all__ = ["main", "build_newton_consensus"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr1d_verdict.json"

#: 2 of 3 -- same as DCR1c. A commitment must be voted for by at least two of
#: the three sandboxed passes to survive as consensus.
SUPPORT_THRESHOLD_NEWTON: Final[int] = 2


def build_newton_consensus(
    out_dir: Path = NEWTON_CONSENSUS_DIR,
) -> dict[str, Any]:
    consensus, stats = build_consensus(
        NEWTON_PASS_DIRS, support_threshold=SUPPORT_THRESHOLD_NEWTON
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DCR1d positive control.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    consensus_stats = build_newton_consensus()
    consensus = load_extractions(NEWTON_CONSENSUS_DIR)
    quotes = verify_quotes(consensus, data_dir=args.data_dir)

    doc_id = NEWTON_SOURCE.doc_id
    propositions = consensus.get(doc_id, [])
    document = load_document(doc_id, data_dir=args.data_dir)

    outputs = [f"{p.get('name', '')} {p.get('statement', '')}" for p in propositions]
    residue = audit_residue_v2(
        outputs, [document], cut_year=POSITIVE_CONTROL_CUT.year, allow=SCHEMA_WORDS
    )

    hits_v2 = match_facets_v2(propositions)
    hits_v3 = match_facets_v3(propositions)

    #: T1 fires under either matcher counts as a fire. P3 asks whether the T1
    #: pattern can fire on the sentence it was written for, so restricting to
    #: v3 alone would over-index on a veto that does not touch T1.
    t1_v2 = list(hits_v2.get("T1_absolute_simultaneity", ()))
    t1_v3 = list(hits_v3.get("T1_absolute_simultaneity", ()))
    t1_fires = bool(t1_v2 or t1_v3)

    per_pass: dict[str, Any] = {}
    for directory in NEWTON_PASS_DIRS:
        single = load_extractions(directory)
        single_props = single.get(doc_id, [])
        per_pass[directory.name] = {
            "n_propositions": len(single_props),
            "T1_v3": [h["statement"] for h in match_facets_v3(single_props).get("T1_absolute_simultaneity", ())],
            "T2_v3": [h["statement"] for h in match_facets_v3(single_props).get("T2_privileged_frame", ())],
            "T3_v3": [h["statement"] for h in match_facets_v3(single_props).get("T3_local_time_artifice", ())],
        }

    p1 = quotes.fidelity >= QUOTE_FIDELITY_GATE
    p2 = residue.residue_rate < RESIDUE_RATE_GATE
    p3 = t1_fires

    verdict: dict[str, Any] = {
        "kind": "dcr1d_verdict",
        "purpose": (
            "Positive control for the T1 matcher on Newton's Scholium. "
            "DCR1c's T1 absence is either a matcher artifact or a fact about the "
            "electrodynamics corpus; this run decides."
        ),
        "cut_year": POSITIVE_CONTROL_CUT.year,
        "document": {
            "doc_id": doc_id,
            "author": NEWTON_SOURCE.author,
            "wikisource_title": NEWTON_SOURCE.wikisource_title,
            "chars": len(document),
        },
        "consensus_stats": consensus_stats,
        "n_propositions": len(propositions),
        "quote_audit": {
            "n_total": quotes.n_total,
            "n_exact": quotes.n_exact,
            "n_normalised": quotes.n_normalised,
            "fidelity": quotes.fidelity,
        },
        "residue": {
            "residue_rate": residue.residue_rate,
            "residue_types": list(residue.residue_types)[:60],
        },
        "matcher_v2_v3": compare_v2_v3(propositions),
        "T1_v2_hits": [{"name": h.get("name"), "statement": h["statement"]} for h in t1_v2],
        "T1_v3_hits": [{"name": h.get("name"), "statement": h["statement"]} for h in t1_v3],
        "T2_v3_hits": [{"name": h.get("name"), "statement": h["statement"]} for h in hits_v3.get("T2_privileged_frame", ())],
        "T3_v3_hits": [{"name": h.get("name"), "statement": h["statement"]} for h in hits_v3.get("T3_local_time_artifice", ())],
        "per_pass_facets": per_pass,
        "gates": {
            "P1_quote_fidelity": {
                "value": quotes.fidelity,
                "threshold": QUOTE_FIDELITY_GATE,
                "decision": "GO" if p1 else "NO_GO",
            },
            "P2_vocabulary_residue_v2": {
                "value": residue.residue_rate,
                "threshold": RESIDUE_RATE_GATE,
                "decision": "GO" if p2 else "NO_GO",
            },
            "P3_T1_fires": {
                "n_hits_v2": len(t1_v2),
                "n_hits_v3": len(t1_v3),
                "decision": "GO" if p3 else "NO_GO",
            },
        },
        "overall_decision": "GO" if all((p1, p2, p3)) else "NO_GO",
        "dcr1c_absence_reading": (
            "historical (matcher works, corpus stays silent)"
            if all((p1, p2, p3))
            else "instrument artifact (matcher does not fire on Newton)"
            if p1 and p2 and not p3
            else "inconclusive (P1 or P2 failed; P3 uninterpretable)"
        ),
    }

    _ = FACET_QUORUM_V2
    _ = FACET_QUORUM_V3

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
