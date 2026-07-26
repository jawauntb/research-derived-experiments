"""Measure the repaired instruments before any DCR1b gate is written.

DR3 froze a 10x speedup gate against a toy whose base rate capped it at 7x. The
gate was unsatisfiable the moment the toy was written, and DR3's own paper named
the lesson: **calibrate, then freeze.** DR4 followed it and passed. DCR1 did not
have this problem for G1/G3/G4 but did for G2, whose 5% threshold was chosen
against a measure I had not characterised.

This script reports what the repaired instruments actually produce on the
consensus extraction. ``DCR1B_PREREGISTRATION.md`` is written afterwards, using
these numbers to pick thresholds that are reachable and non-trivial.

Nothing here decides anything. Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.calibrate_dcr1b
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.corpus import sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.fetch import DATA_DIR, load_document
from experiments.date_cut_retrodiction.residue import audit_residue
from experiments.date_cut_retrodiction.residue_v2 import audit_residue_v2
from experiments.date_cut_retrodiction.run_dcr1 import SCHEMA_WORDS, load_extractions
from experiments.date_cut_retrodiction.target import match_facets
from experiments.date_cut_retrodiction.target_v2 import compare_matchers, match_facets_v2


__all__ = ["main", "calibrate"]

CONSENSUS_DIR: Final[Path] = (
    Path(__file__).resolve().parent / "extractions_consensus"
)
RESULTS: Final[Path] = Path(__file__).resolve().parent / "results"


def calibrate(
    extraction_dir: Path = CONSENSUS_DIR, *, data_dir: Path = DATA_DIR
) -> dict[str, Any]:
    extractions = load_extractions(extraction_dir)
    rows: dict[str, Any] = {}

    for cut in CUTS:
        for allow_risk in (True, False):
            doc_ids = [
                s.doc_id
                for s in sources_at_or_before(
                    cut.year, allow_provenance_risk=allow_risk
                )
            ]
            propositions = [p for d in doc_ids for p in extractions.get(d, [])]
            documents = [load_document(d, data_dir=data_dir) for d in doc_ids]
            outputs = [
                f"{p.get('name', '')} {p.get('statement', '')}" for p in propositions
            ]

            v1 = audit_residue(outputs, documents, cut_year=cut.year, allow=SCHEMA_WORDS)
            v2 = audit_residue_v2(
                outputs, documents, cut_year=cut.year, allow=SCHEMA_WORDS
            )
            f1 = match_facets(propositions)
            f2 = match_facets_v2(propositions)

            rows[f"{cut.year}_{'all' if allow_risk else 'norisk'}"] = {
                "cut_year": cut.year,
                "is_placebo": cut.is_placebo,
                "allow_provenance_risk": allow_risk,
                "n_documents": len(doc_ids),
                "n_propositions": len(propositions),
                "residue_rate_v1": v1.residue_rate,
                "residue_rate_v2": v2.residue_rate,
                "n_residue_types_v2": len(v2.residue_types),
                "residue_types_v2": list(v2.residue_types)[:60],
                "facets_v1": sorted(k for k, v in f1.items() if v),
                "facets_v2": sorted(k for k, v in f2.items() if v),
                "facet_counts_v1": {k: len(v) for k, v in f1.items()},
                "facet_counts_v2": {k: len(v) for k, v in f2.items()},
            }

    target = [p for ps in extractions.values() for p in ps]
    return {
        "kind": "dcr1b_calibration",
        "note": (
            "Measured before DCR1B_PREREGISTRATION.md was written. No thresholds "
            "are set here."
        ),
        "extraction_dir": extraction_dir.name,
        "n_documents": len(extractions),
        "n_propositions": len(target),
        "cuts": rows,
        "matcher_comparison_1904": compare_matchers(
            [
                p
                for s in sources_at_or_before(1904)
                for p in extractions.get(s.doc_id, [])
            ]
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Calibrate DCR1b instruments.")
    parser.add_argument("--extractions", type=Path, default=CONSENSUS_DIR)
    parser.add_argument("--out", type=Path, default=RESULTS / "dcr1b_calibration.json")
    args = parser.parse_args(argv)

    report = calibrate(args.extractions)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"consensus: {report['n_documents']} docs, {report['n_propositions']} props\n")
    for key in sorted(report["cuts"], key=lambda k: report["cuts"][k]["cut_year"]):
        row = report["cuts"][key]
        tag = "all" if row["allow_provenance_risk"] else "norisk"
        print(
            f"{row['cut_year']} [{tag:6s}] props={row['n_propositions']:3d}  "
            f"residue v1={row['residue_rate_v1']*100:5.2f}%  "
            f"v2={row['residue_rate_v2']*100:5.2f}%"
        )
        print(f"          facets v1={row['facets_v1']}")
        print(f"          facets v2={row['facets_v2']}  counts={row['facet_counts_v2']}")
    print("\nmatcher repair at 1904:")
    comparison = report["matcher_comparison_1904"]
    print(f"  v1 {comparison['v1_counts']} -> v2 {comparison['v2_counts']}")
    for facet, dropped in comparison["dropped_by_repair"].items():
        if dropped:
            print(f"  dropped from {facet}: {len(dropped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
