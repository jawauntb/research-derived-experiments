"""DCD1 pilot — Darwin / species-fixity, cheap sanity check.

Preregistered in DCD1_PILOT_PREREGISTRATION.md. Applies the DCR arc's
extraction + tagging + consensus discipline to a pilot subset of the
Darwin corpus (5 pre-1859 + 3 Origin chapters), with the D1/D2/D3
categories replacing T1/T2/T3.

Run:
    uv run --no-sync python -m experiments.darwin_species_fixity_corpus.run_dcd1_pilot
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Final, Sequence


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
DCD_DIR: Final[Path] = _PACKAGE / "results" / "dcd1_pilot"
CONSENSUS_DIR: Final[Path] = _PACKAGE / "extractions_dcd1_pilot_consensus"
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcd1_pilot_verdict.json"

PREREG_PATH: Final[Path] = _PACKAGE / "DCD1_PILOT_PREREGISTRATION.md"
D_CATEGORIES_PATH: Final[Path] = _PACKAGE / "DCD1_D_CATEGORIES.md"

VERIFIER_IDS: Final[tuple[str, ...]] = ("A", "B", "C")
CLASS_KEYS: Final[tuple[str, ...]] = ("D1", "D2", "D3")
CONSENSUS_MIN: Final[int] = 2

PILOT_DOCS: Final[tuple[str, ...]] = (
    "malthus_1798_essay_ch1",
    "herschel_1830_prelim_p1c1",
    "erasmus_darwin_1794_zoonomia_generation_39",
    "wallace_1855_sarawak",
    "darwin_1845_beagle_ch17",
    "darwin_1859_origin_introduction",
    "darwin_1859_origin_ch4",
    "darwin_1859_origin_ch14",
)
ORACLE_DOCS: Final[tuple[str, ...]] = tuple(
    d for d in PILOT_DOCS if d.startswith("darwin_1859_origin")
)
PRE_ORIGIN_DOCS: Final[tuple[str, ...]] = tuple(
    d for d in PILOT_DOCS if d not in ORACLE_DOCS
)


def _load_verifier(kind: str, vid: str) -> dict[str, Any]:
    path = DCD_DIR / f"{kind}_1859_{vid}.json"
    return dict(json.loads(path.read_text())["per_proposition"])


def _consensus_categories(
    verifiers: list[dict[str, Any]], pid: str, key: str
) -> list[str]:
    votes: Counter[str] = Counter()
    for v in verifiers:
        for c in v.get(pid, {}).get(key, []):
            votes[c] += 1
    return [c for c, n in votes.items() if n >= CONSENSUS_MIN]


def _is_prediction_consensus(
    verifiers: list[dict[str, Any]], pid: str
) -> bool:
    votes = sum(
        1 for v in verifiers if v.get(pid, {}).get("is_prediction", False)
    )
    return votes >= CONSENSUS_MIN


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DCD1 pilot scoring.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    use_verifiers = [_load_verifier("inferred", v) for v in VERIFIER_IDS]
    disc_verifiers = [_load_verifier("discussion", v) for v in VERIFIER_IDS]

    per_doc: dict[str, dict[str, Any]] = {
        d: {c: {"use": 0, "disc": 0} for c in CLASS_KEYS} for d in PILOT_DOCS
    }
    for d in PILOT_DOCS:
        per_doc[d]["n_pred"] = 0
        per_doc[d]["n_props"] = 0

    all_pids: set[str] = set()
    for v in use_verifiers + disc_verifiers:
        all_pids.update(v.keys())

    for pid in all_pids:
        doc = pid.split(":", 1)[0]
        if doc not in per_doc:
            continue
        per_doc[doc]["n_props"] += 1
        u_tags = _consensus_categories(use_verifiers, pid, "required_categories")
        d_tags = _consensus_categories(disc_verifiers, pid, "discussed_categories")
        is_pred = _is_prediction_consensus(use_verifiers, pid)
        if is_pred:
            per_doc[doc]["n_pred"] += 1
            for c in u_tags:
                if c in CLASS_KEYS:
                    per_doc[doc][c]["use"] += 1
        for c in d_tags:
            if c in CLASS_KEYS:
                per_doc[doc][c]["disc"] += 1

    def agg(docs: Sequence[str], klass: str, kind: str) -> int:
        return sum(per_doc[d][klass][kind] for d in docs)

    pre_D1_disc = agg(PRE_ORIGIN_DOCS, "D1", "disc")
    pre_D2_disc = agg(PRE_ORIGIN_DOCS, "D2", "disc")
    pre_D3_disc = agg(PRE_ORIGIN_DOCS, "D3", "disc")
    oracle_D1_disc = agg(ORACLE_DOCS, "D1", "disc")
    oracle_D2_disc = agg(ORACLE_DOCS, "D2", "disc")
    oracle_D3_disc = agg(ORACLE_DOCS, "D3", "disc")
    oracle_D1_use = agg(ORACLE_DOCS, "D1", "use")
    oracle_D2_use = agg(ORACLE_DOCS, "D2", "use")
    oracle_D3_use = agg(ORACLE_DOCS, "D3", "use")

    p1_avg = sum(per_doc[d]["n_props"] for d in PILOT_DOCS) / len(PILOT_DOCS)
    p1 = p1_avg >= 5
    p2 = (
        (pre_D1_disc + oracle_D1_disc) >= 3
        and (pre_D2_disc + oracle_D2_disc) >= 1
        and (pre_D3_disc + oracle_D3_disc) >= 1
    )
    p3 = oracle_D1_disc > pre_D1_disc
    p4 = oracle_D1_use == 0
    p5 = (
        oracle_D1_disc > 0
        and oracle_D2_disc > 0
        and oracle_D1_disc <= 2 * oracle_D2_disc
        and oracle_D2_disc <= 2 * oracle_D1_disc
    )
    overall = p1 and p2 and p3

    verdict: dict[str, Any] = {
        "kind": "dcd1_pilot_verdict",
        "purpose": (
            "Cheap sanity-check pilot for the Darwin case of the DCD "
            "multi-case test. Verifies the pipeline works on biology "
            "text and previews the two DCR4 structural signatures "
            "(prediction-independence, equalisation) on Darwin's Origin."
        ),
        "preregistration_sha256": hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest(),
        "d_categories_sha256": hashlib.sha256(D_CATEGORIES_PATH.read_bytes()).hexdigest(),
        "verifiers": list(VERIFIER_IDS),
        "pilot_docs": list(PILOT_DOCS),
        "oracle_docs": list(ORACLE_DOCS),
        "pre_origin_docs": list(PRE_ORIGIN_DOCS),
        "per_document": per_doc,
        "aggregates": {
            "pre_origin": {
                "D1_disc": pre_D1_disc,
                "D2_disc": pre_D2_disc,
                "D3_disc": pre_D3_disc,
            },
            "oracle": {
                "D1_disc": oracle_D1_disc,
                "D2_disc": oracle_D2_disc,
                "D3_disc": oracle_D3_disc,
                "D1_use": oracle_D1_use,
                "D2_use": oracle_D2_use,
                "D3_use": oracle_D3_use,
            },
        },
        "gates": {
            "P1_extraction_sanity": {
                "avg_props_per_doc": p1_avg,
                "threshold": 5,
                "decision": "GO" if p1 else "NO_GO",
            },
            "P2_d_signal_exists": {
                "D1_total": pre_D1_disc + oracle_D1_disc,
                "D2_total": pre_D2_disc + oracle_D2_disc,
                "D3_total": pre_D3_disc + oracle_D3_disc,
                "decision": "GO" if p2 else "NO_GO",
            },
            "P3_d1_signal_concentrated_in_origin": {
                "oracle_D1_disc": oracle_D1_disc,
                "pre_origin_D1_disc": pre_D1_disc,
                "decision": "GO" if p3 else "NO_GO",
            },
            "P4_prediction_independence_preview": {
                "oracle_D1_use": oracle_D1_use,
                "decision": "GO" if p4 else "NO_GO",
            },
            "P5_equalisation_preview": {
                "oracle_D1_disc": oracle_D1_disc,
                "oracle_D2_disc": oracle_D2_disc,
                "decision": "GO" if p5 else "NO_GO",
            },
        },
        "overall_core_decision": "GO" if overall else "NO_GO",
        "licensed_reading": (
            "Same shape as DCR4. P3 fails (discussion spike is in "
            "precursor era, not revolutionary paper); P4 and P5 fire, "
            "replicating the two structural signatures DCR4 named as "
            "uniquely characterising the revolutionary paper."
        ) if not overall and p4 and p5 else (
            "Full pilot GO — proceed to full DCD1 with same rubric."
            if overall else
            "Pipeline or rubric problem — diagnose before scaling."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
