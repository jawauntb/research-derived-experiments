"""How much did the blinding breach actually change the extraction?

Pass 1 ran a prompt that named one file to read but did not forbid reading
others. At least one agent — the one handling the most consequential document —
used this repository's own ``residue.py`` to self-check, and that module's
docstring names 1905, names Einstein, and states what the experiment is looking
for. Others may have done the same silently.

Pass 2 re-runs every document with one added paragraph forbidding any file
access beyond the named document. DCR1's gates are evaluated on pass 2.

Keeping pass 1 and comparing is more informative than deleting it. "The breach
changed nothing measurable" and "the breach moved the target facets" are very
different findings, and only the comparison distinguishes them.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.compare_passes
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.cuts import CUTS
from experiments.date_cut_retrodiction.fetch import DATA_DIR
from experiments.date_cut_retrodiction.residue import stem, tokens
from experiments.date_cut_retrodiction.run_dcr1 import (
    EXTRACTION_DIR,
    RESULTS_DIR,
    _cut_propositions,
    load_extractions,
    verify_quotes,
)
from experiments.date_cut_retrodiction.target import match_facets


__all__ = ["main", "compare"]

BLIND_DIR: Final[Path] = Path(__file__).resolve().parent / "extractions_blind"


#: Function words carry no content, so leaving them in would inflate every
#: similarity score toward "these are both English sentences".
_STOPWORDS: Final[frozenset[str]] = frozenset(
    "the a an of in to is are and or that this it as by for with be was were "
    "on at from which its not no but if then than so such".split()
)

#: A pass-1 proposition counts as reproduced when some pass-2 proposition shares
#: at least this fraction of its content stems.
SEMANTIC_MATCH_THRESHOLD: Final[float] = 0.5


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def _content(text: str) -> set[str]:
    return {stem(t) for t in tokens(text) if t not in _STOPWORDS and len(t) > 2}


def _semantic_match_rate(
    left: list[dict[str, Any]], right: list[dict[str, Any]]
) -> tuple[int, int]:
    """How many of ``left``'s statements have a counterpart in ``right``?

    Name equality is far too strict -- the two passes name the same commitment
    differently almost every time -- and raw vocabulary overlap is far too
    loose. This asks the question that actually bears on DCR2: would the same
    candidate be in the candidate set on a second run?
    """
    targets = [c for c in (_content(str(p.get("statement", ""))) for p in right) if c]
    matched = 0
    total = 0
    for proposition in left:
        source = _content(str(proposition.get("statement", "")))
        if not source:
            continue
        total += 1
        best = max((_jaccard(source, t) for t in targets), default=0.0)
        if best >= SEMANTIC_MATCH_THRESHOLD:
            matched += 1
    return matched, total


def compare(
    unblinded: dict[str, list[dict[str, Any]]],
    blind: dict[str, list[dict[str, Any]]],
    *,
    data_dir: Path = DATA_DIR,
) -> dict[str, Any]:
    per_document: dict[str, Any] = {}
    for doc_id in sorted(set(unblinded) | set(blind)):
        a, b = unblinded.get(doc_id, []), blind.get(doc_id, [])
        a_names = {str(p.get("name", "")) for p in a}
        b_names = {str(p.get("name", "")) for p in b}
        a_vocab = {t for p in a for t in tokens(str(p.get("statement", "")))}
        b_vocab = {t for p in b for t in tokens(str(p.get("statement", "")))}
        matched, total = _semantic_match_rate(a, b)
        per_document[doc_id] = {
            "n_unblinded": len(a),
            "n_blind": len(b),
            "name_jaccard": _jaccard(a_names, b_names),
            "statement_vocab_jaccard": _jaccard(a_vocab, b_vocab),
            "semantic_matched": matched,
            "semantic_total": total,
            "semantic_match_rate": (matched / total) if total else 0.0,
        }

    per_cut: dict[str, Any] = {}
    for cut in CUTS:
        row: dict[str, Any] = {"cut_year": cut.year, "is_placebo": cut.is_placebo}
        for label, extractions in (("unblinded", unblinded), ("blind", blind)):
            propositions, _ = _cut_propositions(extractions, cut.year, allow_risk=True)
            facets = match_facets(propositions)
            row[label] = {
                "n_propositions": len(propositions),
                "facets_present": sorted(k for k, v in facets.items() if v),
            }
        row["facets_agree"] = (
            row["unblinded"]["facets_present"] == row["blind"]["facets_present"]
        )
        per_cut[str(cut.year)] = row

    return {
        "kind": "dcr1_pass_comparison",
        "quote_fidelity": {
            "unblinded": verify_quotes(unblinded, data_dir=data_dir).fidelity,
            "blind": verify_quotes(blind, data_dir=data_dir).fidelity,
        },
        "per_document": per_document,
        "per_cut": per_cut,
        "all_cuts_agree_on_facets": all(v["facets_agree"] for v in per_cut.values()),
        "mean_name_jaccard": (
            sum(v["name_jaccard"] for v in per_document.values()) / len(per_document)
            if per_document
            else 0.0
        ),
        "overall_semantic_match_rate": (
            sum(v["semantic_matched"] for v in per_document.values())
            / sum(v["semantic_total"] for v in per_document.values())
            if any(v["semantic_total"] for v in per_document.values())
            else 0.0
        ),
        "mean_statement_vocab_jaccard": (
            sum(v["statement_vocab_jaccard"] for v in per_document.values())
            / len(per_document)
            if per_document
            else 0.0
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare the two extraction passes.")
    parser.add_argument("--unblinded", type=Path, default=EXTRACTION_DIR)
    parser.add_argument("--blind", type=Path, default=BLIND_DIR)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--out", type=Path, default=RESULTS_DIR / "dcr1_pass_comparison.json")
    args = parser.parse_args(argv)

    report = compare(
        load_extractions(args.unblinded),
        load_extractions(args.blind),
        data_dir=args.data_dir,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"mean name jaccard      {report['mean_name_jaccard']:.3f}")
    print(f"mean vocab jaccard     {report['mean_statement_vocab_jaccard']:.3f}")
    print(f"semantic match rate    {report['overall_semantic_match_rate']:.3f}")
    print(f"all cuts agree         {report['all_cuts_agree_on_facets']}")
    for year, row in sorted(report["per_cut"].items()):
        print(
            f"  {year}: unblinded={row['unblinded']['facets_present']} "
            f"blind={row['blind']['facets_present']} agree={row['facets_agree']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
