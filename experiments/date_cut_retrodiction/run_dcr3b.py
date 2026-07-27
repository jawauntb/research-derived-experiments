"""DCR3b — score DCR1e consensus by LLM-based counterfactual dependence.

Preregistered in DCR3B_PREREGISTRATION.md. Replaces DCR3's
`kind_weight * degree` with a per-proposition LLM counterfactual score,
consensus median across three sandboxed subagents per cut. Everything
else (target_v4 classification, multidoc gating, random-null baseline)
identical to DCR3.

Reads scores from `results/dcr3b/scores_<YEAR>_<ID>.json`. Runner is
deterministic: same input → same verdict.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3b
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.corpus import sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.dcr1e import PRESUP_CONSENSUS_DIR
from experiments.date_cut_retrodiction.nominate_by_class import assign_classes
from experiments.date_cut_retrodiction.nominate_by_multidoc import MULTIDOC_MIN_DOCS
from experiments.date_cut_retrodiction.run_dcr1 import load_extractions


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
DCR3B_DIR: Final[Path] = _PACKAGE / "results" / "dcr3b"
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr3b_verdict.json"
PROMPT_PATH: Final[Path] = _PACKAGE / "DCR3B_PROMPT.md"

GROUND_TRUTH_CLASS: Final[str] = "T1_absolute_simultaneity"
M3_ALPHA: Final[float] = 0.01
NULL_SEED: Final[int] = 20260727
VERIFIER_IDS: Final[tuple[str, ...]] = ("A", "B", "C")


def _proposition_id(p: dict[str, Any]) -> str:
    return f"{p.get('doc_id', '')}:{p.get('name', '')}"


def _load_scores_for_cut(year: int) -> dict[str, list[int]]:
    """Return per-proposition list of scores from the three verifiers."""
    per_prop: dict[str, list[int]] = {}
    for vid in VERIFIER_IDS:
        path = DCR3B_DIR / f"scores_{year}_{vid}.json"
        if not path.is_file():
            raise SystemExit(f"missing verifier output: {path}")
        payload = json.loads(path.read_text())
        for pid, score in payload["scores"].items():
            per_prop.setdefault(pid, []).append(int(score))
    return per_prop


def _consensus_score(per_verifier: list[int]) -> int:
    if not per_verifier:
        return 0
    return int(round(statistics.median(per_verifier)))


def _score_cut(consensus: dict[str, list[dict[str, Any]]], year: int) -> dict[str, Any]:
    doc_ids = [s.doc_id for s in sources_at_or_before(year)]
    propositions: list[dict[str, Any]] = []
    for d in doc_ids:
        propositions.extend(consensus.get(d, []))

    #: Verifier scores by proposition id.
    per_verifier = _load_scores_for_cut(year)
    per_prop_consensus = {
        pid: _consensus_score(scores) for pid, scores in per_verifier.items()
    }

    classes, unclassified = assign_classes(propositions)
    all_classes = dict(classes)
    all_classes["unclassified"] = unclassified

    class_scores: dict[str, int] = {}
    for cls_key, members in all_classes.items():
        docs = {str(m.get("doc_id", "")) for m in members}
        if len(docs) < MULTIDOC_MIN_DOCS:
            class_scores[cls_key] = 0
        else:
            class_scores[cls_key] = sum(
                per_prop_consensus.get(_proposition_id(m), 0) for m in members
            )

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
        "class_sizes": {k: len(v) for k, v in all_classes.items()},
        "class_scores": class_scores,
        "ranking": ranking,
        "T1_rank": t1_rank,
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
    parser = argparse.ArgumentParser(description="Run DCR3b counterfactual scoring.")
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
    m4 = True  # digest recorded

    overall_go = m1 and m2 and m3 and m4

    reading: str
    if overall_go:
        reading = (
            "intervention_algebra_reframe_wins_on_DCR: counterfactual scoring "
            "ranks Einstein's actual deletion (T1) first at 1904, T1 not first "
            f"at 1880, beats random null at p = {null_p:.4f}. Direct empirical "
            "support for 'the object lives in the intervention algebra' on the "
            "DCR corpus."
        )
    elif not m1:
        reading = (
            "counterfactual_scoring_still_missed_T1: even LLM-based "
            "counterfactual dependence puts T1 at rank "
            f"{target['T1_rank']}. Third serial null on the "
            "intervention-algebra reframe on this arc."
        )
    elif not m2:
        reading = "counterfactual_scoring_leaks_at_placebo"
    elif not m3:
        reading = f"chance_ranking (null p = {null_p:.4f})"
    else:
        reading = "mixed"

    verdict: dict[str, Any] = {
        "kind": "dcr3b_verdict",
        "purpose": (
            "Test the intervention-algebra reframe on DCR: does LLM-based "
            "counterfactual dependence scoring rank Einstein's actual "
            "deletion (T1) first where DCR3's corpus-frequency scoring did "
            "not?"
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
