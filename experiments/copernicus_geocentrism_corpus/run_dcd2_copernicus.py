"""DCD2 — Copernicus / geocentrism scorer (S1 and S2 as frozen primary gates).

Preregistered in ``DCD2_COPERNICUS_PREREGISTRATION.md``. Applies the DCR-arc
extraction + tagging + consensus discipline to this package's corpus, with the
C1/C2/C3 categories (``DCD2_C_CATEGORIES.md``) replacing T1/T2/T3, and scores the
two structural signatures as the PRIMARY gates:

    S1  equalisation            — oracle balances C1 and C2, uniquely in the corpus
    S2  prediction-independence — oracle predictions use no C-category, uniquely
    N1  discussion spike        — NEGATIVE CONTROL, expected NO_GO

plus the pre-tagging STOP gates C0 (coverage), P1 (extraction sanity), P2
(C-signal), a raw/normalised report, and a verifier-variance stability flag.

The uniqueness clause of S1/S2 is the crux the DCD1 specificity check (PR #463)
identified: it held on Einstein and failed on Darwin. DCD2 tests it on a fresh
case. NOTE: this package's committed fetch shows the oracle (De revolutionibus
Book I) is currently unavailable in public-domain English, so C0 STOPs until the
oracle is sourced outside Wikisource.

Inputs (produced by the network-gated fetch + tagging steps):

    results/fetch_summary.json                      — corpus coverage + char counts
    results/dcd2_tags/inferred_1543_{A,B,C}.json    — use taggers
    results/dcd2_tags/discussion_1543_{A,B,C}.json  — discussion taggers

Run (once the oracle is sourced and tagging is done):
    uv run --no-sync python -m experiments.copernicus_geocentrism_corpus.run_dcd2_copernicus
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.copernicus_geocentrism_corpus.corpus import (
    ORACLE_SOURCES,
    PRE_REVOLUTIONARY_SOURCES,
)


__all__ = ["main", "score"]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent
TAGS_DIR: Final[Path] = _PACKAGE / "results" / "dcd2_tags"
FETCH_SUMMARY: Final[Path] = _PACKAGE / "results" / "fetch_summary.json"
VERDICT_PATH: Final[Path] = _PACKAGE / "results" / "dcd2_verdict.json"

PREREG_PATH: Final[Path] = _PACKAGE / "DCD2_COPERNICUS_PREREGISTRATION.md"
C_CATEGORIES_PATH: Final[Path] = _PACKAGE / "DCD2_C_CATEGORIES.md"

VERIFIER_IDS: Final[tuple[str, ...]] = ("A", "B", "C")
CLASS_KEYS: Final[tuple[str, ...]] = ("C1", "C2", "C3")
CONSENSUS_MIN: Final[int] = 2

ORACLE_DOCS: Final[tuple[str, ...]] = tuple(s.doc_id for s in ORACLE_SOURCES)
#: Primary precursor set (informational): the geocentric-tradition sources not
#: leak-flagged. The actual run partition is taken from fetch_summary.json at
#: score time so it reflects what fetched substantively.
PRIMARY_PRECURSOR_DOCS: Final[tuple[str, ...]] = tuple(
    s.doc_id for s in PRE_REVOLUTIONARY_SOURCES if not s.provenance_risk
)


def _load_verifier(kind: str, vid: str, *, tags_dir: Path) -> dict[str, Any]:
    path = tags_dir / f"{kind}_1543_{vid}.json"
    return dict(json.loads(path.read_text())["per_proposition"])


def _disc_categories(verifier: dict[str, Any], pid: str) -> list[str]:
    return [c for c in verifier.get(pid, {}).get("discussed_categories", []) if c in CLASS_KEYS]


def _use_categories(verifier: dict[str, Any], pid: str) -> list[str]:
    return [c for c in verifier.get(pid, {}).get("required_categories", []) if c in CLASS_KEYS]


def _is_prediction(verifier: dict[str, Any], pid: str) -> bool:
    return bool(verifier.get(pid, {}).get("is_prediction", False))


def _consensus_disc(verifiers: list[dict[str, Any]], pid: str) -> list[str]:
    votes: Counter[str] = Counter()
    for v in verifiers:
        for c in _disc_categories(v, pid):
            votes[c] += 1
    return [c for c, n in votes.items() if n >= CONSENSUS_MIN]


def _consensus_use(verifiers: list[dict[str, Any]], pid: str) -> list[str]:
    votes: Counter[str] = Counter()
    for v in verifiers:
        for c in _use_categories(v, pid):
            votes[c] += 1
    return [c for c, n in votes.items() if n >= CONSENSUS_MIN]


def _consensus_pred(verifiers: list[dict[str, Any]], pid: str) -> bool:
    return sum(1 for v in verifiers if _is_prediction(v, pid)) >= CONSENSUS_MIN


def _per_doc_counts(
    pids: set[str],
    docs: Sequence[str],
    disc: list[dict[str, Any]],
    use: list[dict[str, Any]],
    *,
    disc_fn: Any,
    use_fn: Any,
    pred_fn: Any,
) -> dict[str, dict[str, Any]]:
    """Tabulate per-document C-disc / C-use / prediction counts.

    ``disc_fn(verifiers, pid)`` -> list[str], ``use_fn`` likewise, ``pred_fn``
    -> bool. Passing the consensus functions gives consensus counts; passing
    single-verifier functions gives that verifier's counts (variance check).
    """

    per_doc: dict[str, dict[str, Any]] = {
        d: {c: {"disc": 0, "use": 0} for c in CLASS_KEYS} for d in docs
    }
    for d in docs:
        per_doc[d]["n_pred"] = 0
        per_doc[d]["n_props"] = 0
    doc_set = set(docs)
    for pid in pids:
        doc = pid.split(":", 1)[0]
        if doc not in doc_set:
            continue
        per_doc[doc]["n_props"] += 1
        for c in disc_fn(disc, pid):
            per_doc[doc][c]["disc"] += 1
        if pred_fn(use, pid):
            per_doc[doc]["n_pred"] += 1
            for c in use_fn(use, pid):
                per_doc[doc][c]["use"] += 1
    return per_doc


def _gate_decisions(
    per_doc: dict[str, dict[str, Any]],
    oracle_docs: Sequence[str],
    precursor_docs: Sequence[str],
) -> dict[str, bool]:
    """Compute P2/S1/S2/N1 booleans from a per-document count table."""

    def agg(docs: Sequence[str], klass: str, kind: str) -> int:
        return sum(per_doc[d][klass][kind] for d in docs if d in per_doc)

    o_c1 = agg(oracle_docs, "C1", "disc")
    o_c2 = agg(oracle_docs, "C2", "disc")
    p_c1 = agg(precursor_docs, "C1", "disc")
    p_c2 = agg(precursor_docs, "C2", "disc")
    o_use = sum(agg(oracle_docs, c, "use") for c in CLASS_KEYS)

    corpus_c1 = o_c1 + p_c1
    corpus_c2 = o_c2 + p_c2
    corpus_c3 = agg(oracle_docs, "C3", "disc") + agg(precursor_docs, "C3", "disc")
    p2 = corpus_c1 >= 3 and corpus_c2 >= 3 and corpus_c3 >= 1

    balance = o_c1 >= 3 and o_c2 >= 3 and o_c1 <= 2 * o_c2 and o_c2 <= 2 * o_c1
    tau = min(o_c1, o_c2)
    uniqueness = not any(
        per_doc[d]["C1"]["disc"] >= tau and per_doc[d]["C2"]["disc"] >= tau
        for d in precursor_docs
        if d in per_doc
    )
    s1 = balance and uniqueness

    def use_frac(d: str) -> float:
        preds = per_doc[d]["n_pred"]
        if preds == 0:
            return 0.0
        used = sum(per_doc[d][c]["use"] for c in CLASS_KEYS)
        return used / preds

    every_precursor_uses = len(precursor_docs) > 0 and all(
        use_frac(d) > 0 for d in precursor_docs if d in per_doc
    )
    s2 = (o_use == 0) and every_precursor_uses

    n1 = o_c1 > p_c1  # negative control: expected False
    return {"P2": p2, "S1": s1, "S2": s2, "N1": n1}


def score(*, tags_dir: Path = TAGS_DIR, fetch_summary: Path = FETCH_SUMMARY) -> dict[str, Any]:
    """Score the DCD2 verdict from fetched coverage + consensus tags.

    Raises FileNotFoundError with an actionable message if the network-gated
    inputs are not present yet.
    """

    if not fetch_summary.is_file():
        raise FileNotFoundError(
            f"missing {fetch_summary} — run the fetch first "
            "(experiments.copernicus_geocentrism_corpus.fetch)."
        )
    summary = json.loads(fetch_summary.read_text())
    docs_meta = {d["doc_id"]: d for d in summary["documents"]}

    oracle_docs = [
        d for d in ORACLE_DOCS if docs_meta.get(d, {}).get("substantive")
    ]
    precursor_docs = [
        d
        for d, m in docs_meta.items()
        if not m["oracle"] and not m["provenance_risk"] and m["substantive"]
    ]
    run_docs = oracle_docs + precursor_docs

    # C0 coverage STOP gate (does not need tags).
    oracle_available = len(oracle_docs) >= 1
    c0 = oracle_available and len(precursor_docs) >= 3

    missing_tags = [
        f"{kind}_1543_{v}.json"
        for kind in ("inferred", "discussion")
        for v in VERIFIER_IDS
        if not (tags_dir / f"{kind}_1543_{v}.json").is_file()
    ]
    if missing_tags:
        raise FileNotFoundError(
            "missing tag files in "
            f"{tags_dir}: {', '.join(missing_tags)} — run the 3 use + 3 discussion "
            "tagging subagents first (see DCD2_COPERNICUS_PREREGISTRATION.md). "
            f"NOTE: C0 coverage is currently {'GO' if c0 else 'NO_GO'} "
            f"(oracle_available={oracle_available}, n_precursors={len(precursor_docs)})."
        )

    use_verifiers = [_load_verifier("inferred", v, tags_dir=tags_dir) for v in VERIFIER_IDS]
    disc_verifiers = [_load_verifier("discussion", v, tags_dir=tags_dir) for v in VERIFIER_IDS]

    all_pids: set[str] = set()
    for v in use_verifiers + disc_verifiers:
        all_pids.update(v.keys())

    consensus = _per_doc_counts(
        all_pids, run_docs, disc_verifiers, use_verifiers,
        disc_fn=_consensus_disc, use_fn=_consensus_use, pred_fn=_consensus_pred,
    )

    def agg(docs: Sequence[str], klass: str, kind: str) -> int:
        return sum(consensus[d][klass][kind] for d in docs if d in consensus)

    n_props_total = sum(consensus[d]["n_props"] for d in run_docs)
    p1_avg = n_props_total / len(run_docs) if run_docs else 0.0
    p1 = p1_avg >= 5

    decisions = _gate_decisions(consensus, oracle_docs, precursor_docs)

    unstable: set[str] = set()
    for i in range(len(VERIFIER_IDS)):
        single = _per_doc_counts(
            all_pids, run_docs, [disc_verifiers[i]], [use_verifiers[i]],
            disc_fn=lambda vs, pid: _disc_categories(vs[0], pid),
            use_fn=lambda vs, pid: _use_categories(vs[0], pid),
            pred_fn=lambda vs, pid: _is_prediction(vs[0], pid),
        )
        single_dec = _gate_decisions(single, oracle_docs, precursor_docs)
        for gate, val in single_dec.items():
            if val != decisions[gate]:
                unstable.add(gate)

    def norm_table(docs: Sequence[str]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for d in docs:
            chars = max(1, docs_meta.get(d, {}).get("chars", 1))
            out[d] = {
                c: {
                    "disc": consensus[d][c]["disc"],
                    "use": consensus[d][c]["use"],
                    "disc_per_1k_chars": round(consensus[d][c]["disc"] / chars * 1000, 4),
                }
                for c in CLASS_KEYS
            }
            out[d]["n_pred"] = consensus[d]["n_pred"]
            out[d]["n_props"] = consensus[d]["n_props"]
            out[d]["chars"] = docs_meta.get(d, {}).get("chars")
        return out

    o_c1, o_c2 = agg(oracle_docs, "C1", "disc"), agg(oracle_docs, "C2", "disc")
    verdict: dict[str, Any] = {
        "kind": "dcd2_copernicus_verdict",
        "purpose": (
            "First DCD study to run the two structural signatures (S1 equalisation, "
            "S2 prediction-independence) as frozen PRIMARY gates with an explicit "
            "uniqueness clause, on Copernicus 1543 as a fresh oracle — testing the "
            "question PR #463 opened (uniqueness held on Einstein, failed on Darwin). "
            "N1 (discussion spike) is the negative control."
        ),
        "preregistration_sha256": hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest(),
        "c_categories_sha256": hashlib.sha256(C_CATEGORIES_PATH.read_bytes()).hexdigest(),
        "verifiers": list(VERIFIER_IDS),
        "oracle_docs": oracle_docs,
        "primary_precursor_docs": precursor_docs,
        "per_document": norm_table(run_docs),
        "aggregates": {
            "oracle": {
                "C1_disc": o_c1, "C2_disc": o_c2, "C3_disc": agg(oracle_docs, "C3", "disc"),
                "C1_use": agg(oracle_docs, "C1", "use"),
                "C2_use": agg(oracle_docs, "C2", "use"),
                "C3_use": agg(oracle_docs, "C3", "use"),
                "n_pred": sum(consensus[d]["n_pred"] for d in oracle_docs),
            },
            "precursor": {
                "C1_disc": agg(precursor_docs, "C1", "disc"),
                "C2_disc": agg(precursor_docs, "C2", "disc"),
                "C3_disc": agg(precursor_docs, "C3", "disc"),
            },
        },
        "gates": {
            "C0_corpus_coverage": {
                "oracle_available": oracle_available,
                "n_primary_precursors": len(precursor_docs),
                "threshold": 3,
                "decision": "GO" if c0 else "NO_GO",
            },
            "P1_extraction_sanity": {
                "avg_props_per_doc": round(p1_avg, 3),
                "threshold": 5,
                "decision": "GO" if p1 else "NO_GO",
            },
            "P2_c_signal_exists": {
                "C1_total": o_c1 + agg(precursor_docs, "C1", "disc"),
                "C2_total": o_c2 + agg(precursor_docs, "C2", "disc"),
                "C3_total": agg(oracle_docs, "C3", "disc") + agg(precursor_docs, "C3", "disc"),
                "decision": "GO" if decisions["P2"] else "NO_GO",
            },
            "S1_equalisation_PRIMARY": {
                "oracle_C1_disc": o_c1,
                "oracle_C2_disc": o_c2,
                "tau": min(o_c1, o_c2),
                "decision": "GO" if decisions["S1"] else "NO_GO",
                "stable": "S1" not in unstable,
            },
            "S2_prediction_independence_PRIMARY": {
                "oracle_C_use": sum(agg(oracle_docs, c, "use") for c in CLASS_KEYS),
                "decision": "GO" if decisions["S2"] else "NO_GO",
                "stable": "S2" not in unstable,
            },
            "N1_discussion_spike_NEGATIVE_CONTROL": {
                "oracle_C1_disc": o_c1,
                "precursor_C1_disc": agg(precursor_docs, "C1", "disc"),
                "decision": "GO" if decisions["N1"] else "NO_GO",
                "expected": "NO_GO",
            },
        },
        "unstable_gates": sorted(unstable),
        "primary_verdict": (
            "S1_AND_S2_GO"
            if (decisions["S1"] and decisions["S2"] and not ({"S1", "S2"} & unstable))
            else "SPLIT_OR_NO_GO"
        ),
    }
    if not c0:
        verdict["primary_verdict"] = "C0_STOP"
    return verdict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DCD2 Copernicus scoring.")
    parser.add_argument("--out", type=Path, default=VERDICT_PATH)
    parser.add_argument("--tags-dir", type=Path, default=TAGS_DIR)
    parser.add_argument("--fetch-summary", type=Path, default=FETCH_SUMMARY)
    args = parser.parse_args(argv)

    verdict = score(tags_dir=args.tags_dir, fetch_summary=args.fetch_summary)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
