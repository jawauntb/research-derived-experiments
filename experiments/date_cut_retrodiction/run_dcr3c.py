"""DCR3c — score DCR1e consensus by LLM-inferred required assumptions.

Preregistered in DCR3C_PREREGISTRATION.md. The identifiability reframe
operationalisation on DCR: rather than counting citations (DCR3) or
LLM-judged in-corpus dependence (DCR3b), count how many empirical
predictions in the corpus REQUIRE each class of commitment to be a
valid inference.

Per cut: three sandboxed Claude subagents identify predictions and
inferred required-assumption categories. Consensus = a category is
tagged if >=2 of 3 verifiers tagged it. Multidoc gating applied on
prediction-carrying documents.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3c
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.corpus import sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.dcr1e import PRESUP_CONSENSUS_DIR
from experiments.date_cut_retrodiction.nominate_by_multidoc import MULTIDOC_MIN_DOCS
from experiments.date_cut_retrodiction.run_dcr1 import load_extractions


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
DCR3C_DIR: Final[Path] = _PACKAGE / "results" / "dcr3c"
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr3c_verdict.json"
PROMPT_PATH: Final[Path] = _PACKAGE / "DCR3C_PROMPT.md"

GROUND_TRUTH_CLASS: Final[str] = "T1"
M3_ALPHA: Final[float] = 0.01
NULL_SEED: Final[int] = 20260727
VERIFIER_IDS: Final[tuple[str, ...]] = ("A", "B", "C")
CLASS_KEYS: Final[tuple[str, ...]] = ("T1", "T2", "T3")
CONSENSUS_MIN_VERIFIERS: Final[int] = 2


def _proposition_id(p: dict[str, Any]) -> str:
    return f"{p.get('doc_id', '')}:{p.get('name', '')}"


def _load_verifier_outputs(year: int) -> list[dict[str, Any]]:
    outs: list[dict[str, Any]] = []
    for vid in VERIFIER_IDS:
        path = DCR3C_DIR / f"inferred_{year}_{vid}.json"
        if not path.is_file():
            raise SystemExit(f"missing verifier output: {path}")
        outs.append(json.loads(path.read_text()))
    return outs


def _consensus_prediction_tags(
    per_verifier: list[dict[str, Any]],
) -> dict[str, tuple[bool, tuple[str, ...]]]:
    """For each proposition id, return (is_prediction_consensus,
    categories_tagged_by_at_least_CONSENSUS_MIN_VERIFIERS)."""
    #: Aggregate across verifiers per prop.
    prediction_votes: Counter[str] = Counter()
    category_votes: dict[str, Counter[str]] = {}

    all_ids: set[str] = set()
    for v in per_verifier:
        per_prop = v.get("per_proposition", {})
        for pid, entry in per_prop.items():
            all_ids.add(pid)
            if bool(entry.get("is_prediction", False)):
                prediction_votes[pid] += 1
            cats = entry.get("required_categories", [])
            cat_counter = category_votes.setdefault(pid, Counter())
            for c in cats:
                if c in CLASS_KEYS:  # only track T1/T2/T3, not OTHER
                    cat_counter[c] += 1

    out: dict[str, tuple[bool, tuple[str, ...]]] = {}
    for pid in all_ids:
        is_pred = prediction_votes[pid] >= CONSENSUS_MIN_VERIFIERS
        counter = category_votes.get(pid, Counter())
        tags = tuple(
            sorted(c for c, n in counter.items() if n >= CONSENSUS_MIN_VERIFIERS)
        )
        out[pid] = (is_pred, tags)
    return out


def _score_cut(consensus: dict[str, list[dict[str, Any]]], year: int) -> dict[str, Any]:
    doc_ids = [s.doc_id for s in sources_at_or_before(year)]
    propositions: list[dict[str, Any]] = []
    for d in doc_ids:
        propositions.extend(consensus.get(d, []))

    per_verifier = _load_verifier_outputs(year)
    tags = _consensus_prediction_tags(per_verifier)

    #: For each class, count predictions requiring that class AND enumerate
    #: contributing documents.
    class_prediction_count: dict[str, int] = {c: 0 for c in CLASS_KEYS}
    class_docs: dict[str, set[str]] = {c: set() for c in CLASS_KEYS}
    predictions: list[dict[str, Any]] = []

    for p in propositions:
        pid = _proposition_id(p)
        is_pred, tag_tuple = tags.get(pid, (False, ()))
        if not is_pred:
            continue
        doc = str(p.get("doc_id", ""))
        predictions.append(
            {
                "id": pid,
                "doc_id": doc,
                "required_categories": list(tag_tuple),
            }
        )
        for cls in tag_tuple:
            class_prediction_count[cls] += 1
            if doc:
                class_docs[cls].add(doc)

    #: Multidoc gating: class score = count only if the required-assumption
    #: comes from >= MULTIDOC_MIN_DOCS distinct documents.
    class_scores: dict[str, int] = {}
    for cls in CLASS_KEYS:
        if len(class_docs[cls]) < MULTIDOC_MIN_DOCS:
            class_scores[cls] = 0
        else:
            class_scores[cls] = class_prediction_count[cls]

    ranked = sorted(class_scores.items(), key=lambda pair: (-pair[1], pair[0]))
    ranking = [{"class": k, "score": v} for k, v in ranked]

    t1_rank = next(
        (i + 1 for i, e in enumerate(ranking) if e["class"] == GROUND_TRUTH_CLASS),
        -1,
    )

    return {
        "cut_year": year,
        "n_documents": len(doc_ids),
        "n_propositions": len(propositions),
        "n_predictions": len(predictions),
        "class_prediction_count": class_prediction_count,
        "class_documents": {k: len(v) for k, v in class_docs.items()},
        "class_scores": class_scores,
        "ranking": ranking,
        "T1_rank": t1_rank,
        "predictions_sample": predictions[:10],
    }


def _null_p_of_T1_first(class_scores: dict[str, int], trials: int) -> float:
    keys = sorted(class_scores.keys())
    rng = random.Random(NULL_SEED)
    hits = 0
    for _ in range(trials):
        perm = keys[:]
        rng.shuffle(perm)
        if perm[0] == GROUND_TRUTH_CLASS:
            hits += 1
    return hits / trials


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DCR3c inferred-assumption scoring.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    parser.add_argument("--n-null-trials", type=int, default=10000)
    args = parser.parse_args(argv)

    consensus = load_extractions(PRESUP_CONSENSUS_DIR)

    by_cut: dict[str, Any] = {}
    for cut in CUTS:
        by_cut[str(cut.year)] = _score_cut(consensus, cut.year)

    target = by_cut["1904"]
    placebo = by_cut["1880"]

    m1 = target["T1_rank"] == 1
    m2 = placebo["T1_rank"] != 1
    null_p = _null_p_of_T1_first(target["class_scores"], args.n_null_trials)
    m3 = m1 and (null_p < M3_ALPHA)
    prompt_digest = hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()
    m4 = True

    overall_go = m1 and m2 and m3 and m4

    if overall_go:
        reading = (
            "identifiability_reframe_wins_on_DCR: inferred-required-assumption "
            "scoring ranks T1 first at 1904 where citation-frequency (DCR3) "
            "and within-corpus counterfactual (DCR3b) put T1 third. "
            f"Beats random null at p = {null_p:.4f}. Direct empirical support "
            "for the identifiability reframe operationalised on DCR."
        )
    elif not m1:
        reading = (
            f"fourth_serial_null_on_DCR: T1 rank {target['T1_rank']} under "
            "inferred-required-assumption scoring. Even the identifiability "
            "reframe's most direct DCR operationalisation does not recover "
            "T1. Four preregistered nulls on the DR-arc side."
        )
    elif not m2:
        reading = "placebo_leak"
    elif not m3:
        reading = f"chance_ranking (null p = {null_p:.4f})"
    else:
        reading = "mixed"

    verdict: dict[str, Any] = {
        "kind": "dcr3c_verdict",
        "purpose": (
            "Test the identifiability reframe on DCR: does scoring by "
            "inferred required assumptions of each empirical prediction "
            "rank T1 first where explicit citation-based scoring did not?"
        ),
        "prompt_sha256": prompt_digest,
        "verifiers": list(VERIFIER_IDS),
        "cuts": by_cut,
        "T1_rank_1904": target["T1_rank"],
        "T1_rank_1880": placebo["T1_rank"],
        "null_probability_T1_first_at_1904": null_p,
        "n_null_trials": args.n_null_trials,
        "gates": {
            "M1_T1_first_at_1904": {
                "T1_rank": target["T1_rank"],
                "top_class": target["ranking"][0]["class"] if target["ranking"] else None,
                "top_score": target["ranking"][0]["score"] if target["ranking"] else None,
                "decision": "GO" if m1 else "NO_GO",
            },
            "M2_T1_not_first_at_1880": {
                "T1_rank": placebo["T1_rank"],
                "top_class": placebo["ranking"][0]["class"] if placebo["ranking"] else None,
                "decision": "GO" if m2 else "NO_GO",
            },
            "M3_beats_random_null": {
                "p_value": null_p,
                "threshold": M3_ALPHA,
                "n_trials": args.n_null_trials,
                "decision": "GO" if m3 else "NO_GO",
            },
            "M4_prompt_committed": {"sha256": prompt_digest, "decision": "GO"},
        },
        "overall_decision": "GO" if overall_go else "NO_GO",
        "licensed_reading": reading,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
