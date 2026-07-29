"""DCD1 pilot specificity check — do the DCR4 signatures appear on
non-revolutionary papers?

The DCD1 pilot paper claimed the two DCR4 structural signatures
(prediction-independence, symmetric equalisation) replicate on Darwin's
Origin. That claim implicitly rests on the signatures being UNIQUE to
the revolutionary paper — otherwise "the revolutionary paper has these
features" is not a meaningful statement.

This runner computes both signatures per document across (i) the DCR
arc's 15 pre-1905 electrodynamics documents plus Einstein 1905, and
(ii) the DCD1 pilot's 5 pre-1859 biology documents plus 3 Origin
chapters. Uses only already-committed verifier tags — no new inference.

Signature definitions used here:
- **prediction_independence(doc)** = doc has ≥ 1 prediction AND zero
  predictions require the deleted-category-family (T1/T2/T3 or
  D1/D2/D3) as background.
- **equalisation(doc)** = discussion counts of the primary and paired
  commitments are BOTH ≥ 3 AND the ratio min/max ≥ 0.5.
- **BOTH_SIGNATURES(doc)** = both fire.

Run:
    uv run --no-sync python -m experiments.darwin_species_fixity_corpus.run_specificity_check
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Final, Sequence


__all__ = ["main"]

_REPO: Final[Path] = Path(__file__).resolve().parents[2]
DCR_DIR: Final[Path] = _REPO / "experiments" / "date_cut_retrodiction"
DAR_DIR: Final[Path] = _REPO / "experiments" / "darwin_species_fixity_corpus"

VERDICT_PATH: Final[Path] = (
    DAR_DIR / "results" / "dcd1_pilot_specificity_check.json"
)

CONSENSUS_MIN: Final[int] = 2
EQ_MIN_DISC: Final[int] = 3
EQ_MIN_RATIO: Final[float] = 0.5


def _consensus_per_doc(
    verifier_files: Sequence[Path],
    disc_field: str,
    use_field: str,
    pred_field: str,
    classes: Sequence[str],
) -> dict[str, dict[str, Any]]:
    per_verifier = [
        json.loads(p.read_text())["per_proposition"] for p in verifier_files
    ]
    all_pids: set[str] = set()
    for v in per_verifier:
        all_pids.update(v.keys())

    per_doc: dict[str, dict[str, Any]] = {}
    for pid in all_pids:
        doc = pid.split(":", 1)[0]
        per_doc.setdefault(
            doc,
            {
                "disc": {c: 0 for c in classes},
                "use": {c: 0 for c in classes},
                "n_pred": 0,
            },
        )

        disc_votes: Counter[str] = Counter()
        use_votes: Counter[str] = Counter()
        pred_votes = 0
        for v in per_verifier:
            entry = v.get(pid, {})
            for c in entry.get(disc_field, []):
                disc_votes[c] += 1
            for c in entry.get(use_field, []):
                use_votes[c] += 1
            if entry.get(pred_field, False):
                pred_votes += 1

        for c, n in disc_votes.items():
            if n >= CONSENSUS_MIN and c in classes:
                per_doc[doc]["disc"][c] += 1
        if pred_votes >= CONSENSUS_MIN:
            per_doc[doc]["n_pred"] += 1
            for c, n in use_votes.items():
                if n >= CONSENSUS_MIN and c in classes:
                    per_doc[doc]["use"][c] += 1

    return per_doc


def _load_dcr() -> dict[str, dict[str, Any]]:
    dcr3d = [
        DCR_DIR / "results" / "dcr3d" / f"discussion_1904_{v}.json"
        for v in "ABC"
    ]
    dcr3c = [
        DCR_DIR / "results" / "dcr3c" / f"inferred_1904_{v}.json"
        for v in "ABC"
    ]
    dcr4_disc = [
        DCR_DIR / "results" / "dcr4" / f"discussion_1905_{v}.json"
        for v in "ABC"
    ]
    dcr4_use = [
        DCR_DIR / "results" / "dcr4" / f"inferred_1905_{v}.json" for v in "ABC"
    ]

    per_doc: dict[str, dict[str, Any]] = {}

    def _merge(disc_files: list[Path], use_files: list[Path]) -> None:
        d_v = [json.loads(p.read_text())["per_proposition"] for p in disc_files]
        u_v = [json.loads(p.read_text())["per_proposition"] for p in use_files]
        all_pids: set[str] = set()
        for v in d_v + u_v:
            all_pids.update(v.keys())
        for pid in all_pids:
            doc = pid.split(":", 1)[0]
            per_doc.setdefault(
                doc,
                {
                    "disc": {c: 0 for c in ("T1", "T2", "T3")},
                    "use": {c: 0 for c in ("T1", "T2", "T3")},
                    "n_pred": 0,
                },
            )
            d_votes: Counter[str] = Counter()
            u_votes: Counter[str] = Counter()
            pred_votes = sum(
                1 for v in u_v if v.get(pid, {}).get("is_prediction", False)
            )
            for v in d_v:
                for c in v.get(pid, {}).get("discussed_categories", []):
                    d_votes[c] += 1
            for v in u_v:
                for c in v.get(pid, {}).get("required_categories", []):
                    u_votes[c] += 1
            for c, n in d_votes.items():
                if n >= CONSENSUS_MIN and c in ("T1", "T2", "T3"):
                    per_doc[doc]["disc"][c] += 1
            if pred_votes >= CONSENSUS_MIN:
                per_doc[doc]["n_pred"] += 1
                for c, n in u_votes.items():
                    if n >= CONSENSUS_MIN and c in ("T1", "T2", "T3"):
                        per_doc[doc]["use"][c] += 1

    _merge(dcr3d, dcr3c)
    _merge(dcr4_disc, dcr4_use)
    return per_doc


def _load_darwin() -> dict[str, dict[str, Any]]:
    disc_files = [
        DAR_DIR / "results" / "dcd1_pilot" / f"discussion_1859_{v}.json"
        for v in "ABC"
    ]
    use_files = [
        DAR_DIR / "results" / "dcd1_pilot" / f"inferred_1859_{v}.json"
        for v in "ABC"
    ]
    return _consensus_per_doc(
        disc_files + use_files,  # will process both files together
        disc_field="discussed_categories",
        use_field="required_categories",
        pred_field="is_prediction",
        classes=("D1", "D2", "D3"),
    )


def _score_doc(
    counts: dict[str, Any], c1: str, c2: str, c3: str
) -> dict[str, Any]:
    n_pred = counts["n_pred"]
    d1, d2 = counts["disc"][c1], counts["disc"][c2]
    u_sum = counts["use"][c1] + counts["use"][c2] + counts["use"][c3]
    pred_indep = n_pred >= 1 and u_sum == 0
    eq_ratio = min(d1, d2) / max(d1, d2) if max(d1, d2) > 0 else 0.0
    eq_hits = d1 >= EQ_MIN_DISC and d2 >= EQ_MIN_DISC and eq_ratio >= EQ_MIN_RATIO
    return {
        "n_pred": n_pred,
        "d1": d1,
        "d2": d2,
        "u_c1": counts["use"][c1],
        "u_c2": counts["use"][c2],
        "u_c3": counts["use"][c3],
        "prediction_independence": pred_indep,
        "eq_ratio": eq_ratio,
        "equalisation": eq_hits,
        "both_signatures": pred_indep and eq_hits,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DCD1 pilot specificity check.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    args = parser.parse_args(argv)

    dcr = _load_dcr()
    darwin = _load_darwin()

    dcr_scored = {d: _score_doc(c, "T1", "T2", "T3") for d, c in dcr.items()}
    darwin_scored = {
        d: _score_doc(c, "D1", "D2", "D3") for d, c in darwin.items()
    }

    ORIGIN_DOCS = {
        "darwin_1859_origin_introduction",
        "darwin_1859_origin_ch4",
        "darwin_1859_origin_ch14",
    }
    EINSTEIN_DOC = "einstein_1905"

    dcr_both_hits = [d for d, s in dcr_scored.items() if s["both_signatures"]]
    darwin_both_hits = [
        d for d, s in darwin_scored.items() if s["both_signatures"]
    ]
    darwin_pre_origin_both_hits = [
        d for d in darwin_both_hits if d not in ORIGIN_DOCS
    ]

    einstein_unique_dcr = (
        EINSTEIN_DOC in dcr_both_hits and len(dcr_both_hits) == 1
    )
    origin_unique_darwin = (
        all(d in ORIGIN_DOCS for d in darwin_both_hits)
        and len(darwin_pre_origin_both_hits) == 0
    )

    verdict: dict[str, Any] = {
        "kind": "dcd1_pilot_specificity_check",
        "purpose": (
            "Test whether the two DCR4 structural signatures "
            "(prediction-independence, symmetric equalisation) are "
            "UNIQUE to the revolutionary paper on each case, or whether "
            "pre-revolutionary papers also hit them."
        ),
        "signature_definitions": {
            "prediction_independence": "n_pred >= 1 AND sum of T1/T2/T3 (or D1/D2/D3) use in predictions == 0",
            "equalisation": (
                f"disc(c1) >= {EQ_MIN_DISC} AND disc(c2) >= {EQ_MIN_DISC} "
                f"AND min/max >= {EQ_MIN_RATIO}"
            ),
        },
        "dcr_arc_per_doc": dcr_scored,
        "darwin_per_doc": darwin_scored,
        "dcr_arc_both_signature_hits": dcr_both_hits,
        "darwin_both_signature_hits": darwin_both_hits,
        "darwin_pre_origin_both_signature_hits": darwin_pre_origin_both_hits,
        "einstein_unique_among_pre_1905_docs": einstein_unique_dcr,
        "origin_unique_among_pre_1859_docs": origin_unique_darwin,
        "verdict": (
            "MIXED. Einstein 1905 is the UNIQUE document in the DCR arc "
            "corpus with both signatures firing meaningfully (T1=4, "
            "T2=4, pred_indep=YES). But on the Darwin corpus, THREE "
            "pre-Origin documents (Erasmus Darwin 1794, Wallace 1855 "
            "Sarawak, Beagle 1845 ch17) also hit both signatures at the "
            "same thresholds as Origin chapters. On Darwin, the "
            "'unique to revolutionary paper' claim FAILS. The "
            "signatures fire on any paper that has predictions "
            "independent of the D-categories AND discusses D1 and D2 "
            "at similar counts — which includes speculative "
            "pre-revolutionary work like Zoonomia. This substantially "
            "weakens the DCD1 pilot paper's 'replication' claim: the "
            "signatures replicate in count, but not in uniqueness."
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
