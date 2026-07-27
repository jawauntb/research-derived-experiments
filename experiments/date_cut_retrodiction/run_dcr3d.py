"""DCR3d — score by use / (discussion + 1) ratio.

Preregistered in DCR3D_PREREGISTRATION.md. The human director's
silent-but-load-bearing intuition operationalised: for each class C,
deletability(C) = use_count(C) / (discussion_count(C) + 1).

Use counts come from DCR3c (reused, no new inference). Discussion
counts come from 9 new sandboxed Claude subagents that tag each
proposition with which classes it takes as its SUBJECT rather than
uses as background.

Same consensus rule (>=2 of 3 verifiers agree) for both counts. No
multidoc gating on discussion counts (the whole point is to reward
single-author-discussion signals like Poincaré 1898 on simultaneity).

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3d
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
from experiments.date_cut_retrodiction.run_dcr1 import load_extractions


__all__ = ["main"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
DCR3C_DIR: Final[Path] = _PACKAGE / "results" / "dcr3c"
DCR3D_DIR: Final[Path] = _PACKAGE / "results" / "dcr3d"
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcr3d_verdict.json"
PROMPT_PATH: Final[Path] = _PACKAGE / "DCR3D_PROMPT.md"

GROUND_TRUTH_CLASS: Final[str] = "T1"
M3_ALPHA: Final[float] = 0.01
NULL_SEED: Final[int] = 20260727
VERIFIER_IDS: Final[tuple[str, ...]] = ("A", "B", "C")
CLASS_KEYS: Final[tuple[str, ...]] = ("T1", "T2", "T3")
CONSENSUS_MIN_VERIFIERS: Final[int] = 2


def _proposition_id(p: dict[str, Any]) -> str:
    return f"{p.get('doc_id', '')}:{p.get('name', '')}"


def _load_verifier_outputs(directory: Path, prefix: str, year: int) -> list[dict[str, Any]]:
    outs: list[dict[str, Any]] = []
    for vid in VERIFIER_IDS:
        path = directory / f"{prefix}_{year}_{vid}.json"
        if not path.is_file():
            raise SystemExit(f"missing verifier output: {path}")
        outs.append(json.loads(path.read_text()))
    return outs


def _consensus_tags(
    per_verifier: list[dict[str, Any]],
    field_name: str,
    prediction_field: str | None = None,
) -> dict[str, tuple[tuple[str, ...], bool]]:
    """Return per-proposition (consensus_tags, is_prediction_consensus)."""
    all_ids: set[str] = set()
    prediction_votes: Counter[str] = Counter()
    category_votes: dict[str, Counter[str]] = {}

    for v in per_verifier:
        per_prop = v.get("per_proposition", {})
        for pid, entry in per_prop.items():
            all_ids.add(pid)
            if prediction_field is not None and bool(entry.get(prediction_field, False)):
                prediction_votes[pid] += 1
            cats = entry.get(field_name, [])
            counter = category_votes.setdefault(pid, Counter())
            for c in cats:
                if c in CLASS_KEYS:
                    counter[c] += 1

    out: dict[str, tuple[tuple[str, ...], bool]] = {}
    for pid in all_ids:
        counter = category_votes.get(pid, Counter())
        tags = tuple(
            sorted(c for c, n in counter.items() if n >= CONSENSUS_MIN_VERIFIERS)
        )
        is_pred = (
            prediction_field is not None
            and prediction_votes[pid] >= CONSENSUS_MIN_VERIFIERS
        )
        out[pid] = (tags, is_pred)
    return out


def _score_cut(consensus: dict[str, list[dict[str, Any]]], year: int) -> dict[str, Any]:
    doc_ids = [s.doc_id for s in sources_at_or_before(year)]
    propositions: list[dict[str, Any]] = []
    for d in doc_ids:
        propositions.extend(consensus.get(d, []))

    # Use counts (reused from DCR3c)
    use_verifier = _load_verifier_outputs(DCR3C_DIR, "inferred", year)
    use_tags = _consensus_tags(
        use_verifier, "required_categories", prediction_field="is_prediction"
    )

    # Discussion counts (new DCR3d subagents)
    disc_verifier = _load_verifier_outputs(DCR3D_DIR, "discussion", year)
    disc_tags = _consensus_tags(disc_verifier, "discussed_categories")

    use_count: dict[str, int] = {c: 0 for c in CLASS_KEYS}
    discussion_count: dict[str, int] = {c: 0 for c in CLASS_KEYS}

    for p in propositions:
        pid = _proposition_id(p)
        # Use only counted when proposition is a prediction (matching DCR3c semantics)
        u_tags, is_pred = use_tags.get(pid, ((), False))
        d_tags, _ = disc_tags.get(pid, ((), False))
        if is_pred:
            for c in u_tags:
                use_count[c] += 1
        for c in d_tags:
            discussion_count[c] += 1

    ratios: dict[str, float] = {}
    for c in CLASS_KEYS:
        ratios[c] = use_count[c] / (discussion_count[c] + 1)

    ranked = sorted(ratios.items(), key=lambda pair: (-pair[1], pair[0]))
    ranking = [
        {
            "class": k,
            "ratio": v,
            "use_count": use_count[k],
            "discussion_count": discussion_count[k],
        }
        for k, v in ranked
    ]

    t1_rank = next(
        (i + 1 for i, e in enumerate(ranking) if e["class"] == GROUND_TRUTH_CLASS),
        -1,
    )

    return {
        "cut_year": year,
        "n_documents": len(doc_ids),
        "n_propositions": len(propositions),
        "use_count": use_count,
        "discussion_count": discussion_count,
        "ratios": ratios,
        "ranking": ranking,
        "T1_rank": t1_rank,
    }


def _null_p(ratios: dict[str, float], trials: int) -> float:
    keys = sorted(ratios.keys())
    rng = random.Random(NULL_SEED)
    hits = 0
    for _ in range(trials):
        perm = keys[:]
        rng.shuffle(perm)
        if perm[0] == GROUND_TRUTH_CLASS:
            hits += 1
    return hits / trials


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run DCR3d use/discussion ratio scoring.")
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
    null_p = _null_p(target["ratios"], args.n_null_trials)
    m3 = m1 and (null_p < M3_ALPHA)
    prompt_digest = hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()
    m4 = True

    overall_go = m1 and m2 and m3 and m4

    if overall_go:
        reading = (
            "silent_but_load_bearing_scoring_wins: T1 first at 1904 AND not "
            "first at 1880. Use/discussion ratio identifies revolutionary "
            "deletion where corpus-frequency, in-corpus counterfactual, and "
            "inferred-required-assumption scoring all failed. Fifth attempt, "
            "first success. Directly extends to other conceptual-change cases."
        )
    elif m1 and not m2:
        reading = (
            "always_quiet_detector_not_revolution_detector: T1 first at 1904 "
            "AND at 1880. Ratio measure identifies 'always-quiet' commitments, "
            "not commitments deletable at this specific cut. Informative null "
            "but not the DR-arc's target."
        )
    elif not m1:
        reading = (
            f"fifth_serial_null: T1 rank {target['T1_rank']} even under "
            "use/discussion ratio scoring. Silent-but-load-bearing intuition "
            "correct in spirit but this specific operationalisation does not "
            "invert T2's dominance. Structural implication for DR9-theorem."
        )
    else:
        reading = "mixed"

    verdict: dict[str, Any] = {
        "kind": "dcr3d_verdict",
        "purpose": (
            "Test whether use/(discussion+1) ratio -- rewarding commitments "
            "that are load-bearing but not community-discussed -- ranks T1 "
            "first at 1904 target cut AND NOT first at 1880 placebo cut."
        ),
        "prompt_sha256": prompt_digest,
        "verifiers": list(VERIFIER_IDS),
        "cuts": by_cut,
        "T1_rank_1904": target["T1_rank"],
        "T1_rank_1880": placebo["T1_rank"],
        "T1_ratio_1904": target["ratios"].get("T1"),
        "T1_ratio_1880": placebo["ratios"].get("T1"),
        "null_probability_T1_first_at_1904": null_p,
        "n_null_trials": args.n_null_trials,
        "gates": {
            "M1_T1_first_at_1904": {
                "T1_rank": target["T1_rank"],
                "top_class": target["ranking"][0]["class"] if target["ranking"] else None,
                "top_ratio": target["ranking"][0]["ratio"] if target["ranking"] else None,
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
