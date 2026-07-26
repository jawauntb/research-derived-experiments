"""Consensus extraction over k independent passes.

DCR1 measured something it was not looking for. Two runs of a byte-identical
prompt on a byte-identical document agree on only **67.7%** of propositions by
content. A third of the candidate set is different every time.

For DCR1's question — does the target family appear at this cut? — that did not
matter, because the facet-level answer was stable across both passes. For DCR2's
question it would matter enormously: ranking a *specific* candidate deletion is
partly measuring which draw of the extractor you happened to get.

So the candidate set has to be a consensus rather than a single draw. A
proposition survives when a semantically equivalent proposition appears in at
least ``m`` of ``k`` passes. Everything below ``m`` is extraction noise by
definition, and saying so in advance is what makes it a filter rather than an
excuse.

Equivalence is content-stem Jaccard, not name equality. Names overlap only 7%
across passes — the extractor renames the same commitment almost every time —
so matching on names would discard nearly everything.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.residue_v2 import stem_v2 as stem
from experiments.date_cut_retrodiction.residue_v2 import tokens_v2


__all__ = [
    "PASS_DIRS",
    "SUPPORT_THRESHOLD",
    "EQUIVALENCE_THRESHOLD",
    "ConsensusProposition",
    "build_consensus",
    "main",
]

_PACKAGE: Final[Path] = Path(__file__).resolve().parent

#: Pass 1 is deliberately excluded: its prompt did not forbid reading other
#: files, and at least one agent read this repository's own code. Consensus is
#: built only from sandboxed passes.
PASS_DIRS: Final[tuple[Path, ...]] = (
    _PACKAGE / "extractions_blind",
    _PACKAGE / "extractions_pass3",
)

#: A proposition must appear in at least this many passes to survive.
SUPPORT_THRESHOLD: Final[int] = 2

#: Content-stem Jaccard at or above this counts two statements as the same
#: commitment. Calibrated in DCR1 against hand-read pairs, where 0.5 separated
#: rephrasings of one commitment from genuinely different ones.
EQUIVALENCE_THRESHOLD: Final[float] = 0.5

_STOPWORDS: Final[frozenset[str]] = frozenset(
    "the a an of in to is are and or that this it as by for with be was were "
    "on at from which its not no but if then than so such".split()
)


def _content(text: str) -> frozenset[str]:
    return frozenset(
        stem(t) for t in tokens_v2(text) if t not in _STOPWORDS and len(t) > 2
    )


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = left | right
    return 0.0 if not union else len(left & right) / len(union)


@dataclass(frozen=True)
class ConsensusProposition:
    doc_id: str
    name: str
    statement: str
    quote: str
    kind: str
    definitional: bool
    support: int
    n_passes: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "name": self.name,
            "statement": self.statement,
            "quote": self.quote,
            "kind": self.kind,
            "definitional": self.definitional,
            "support": self.support,
            "n_passes": self.n_passes,
        }


def _load_pass(directory: Path) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        doc_id = payload.get("doc_id", path.stem)
        propositions = payload.get("propositions", [])
        for proposition in propositions:
            proposition.setdefault("doc_id", doc_id)
        out[doc_id] = propositions
    return out


def build_consensus(
    pass_dirs: Sequence[Path] = PASS_DIRS,
    *,
    support_threshold: int = SUPPORT_THRESHOLD,
    equivalence_threshold: float = EQUIVALENCE_THRESHOLD,
) -> tuple[dict[str, list[ConsensusProposition]], dict[str, Any]]:
    passes = [_load_pass(directory) for directory in pass_dirs]
    n_passes = len(passes)
    doc_ids = sorted({d for p in passes for d in p})

    consensus: dict[str, list[ConsensusProposition]] = {}
    stats: dict[str, Any] = {
        "n_passes": n_passes,
        "pass_dirs": [str(d.name) for d in pass_dirs],
        "support_threshold": support_threshold,
        "equivalence_threshold": equivalence_threshold,
        "per_document": {},
    }

    for doc_id in doc_ids:
        # The first pass supplies the representatives; later passes vote.
        anchors = passes[0].get(doc_id, [])
        anchor_content = [(_content(str(p.get("statement", ""))), p) for p in anchors]

        kept: list[ConsensusProposition] = []
        for content, proposition in anchor_content:
            if not content:
                continue
            support = 1
            for other in passes[1:]:
                candidates = (
                    _content(str(q.get("statement", ""))) for q in other.get(doc_id, [])
                )
                if any(
                    _jaccard(content, c) >= equivalence_threshold
                    for c in candidates
                    if c
                ):
                    support += 1
            if support >= support_threshold:
                kept.append(
                    ConsensusProposition(
                        doc_id=doc_id,
                        name=str(proposition.get("name", "")),
                        statement=str(proposition.get("statement", "")),
                        quote=str(proposition.get("quote", "")),
                        kind=str(proposition.get("kind", "")),
                        definitional=bool(proposition.get("definitional", False)),
                        support=support,
                        n_passes=n_passes,
                    )
                )

        consensus[doc_id] = kept
        stats["per_document"][doc_id] = {
            "n_per_pass": [len(p.get(doc_id, [])) for p in passes],
            "n_consensus": len(kept),
            "retention_rate": len(kept) / len(anchors) if anchors else 0.0,
        }

    total_anchor = sum(len(passes[0].get(d, [])) for d in doc_ids)
    total_kept = sum(len(v) for v in consensus.values())
    stats["n_anchor_propositions"] = total_anchor
    stats["n_consensus_propositions"] = total_kept
    stats["overall_retention_rate"] = total_kept / total_anchor if total_anchor else 0.0
    return consensus, stats


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the consensus extraction.")
    parser.add_argument("--out", type=Path, default=_PACKAGE / "extractions_consensus")
    parser.add_argument("--stats", type=Path, default=_PACKAGE / "results" / "consensus_stats.json")
    args = parser.parse_args(argv)

    consensus, stats = build_consensus()
    args.out.mkdir(parents=True, exist_ok=True)
    for doc_id, propositions in consensus.items():
        (args.out / f"{doc_id}.json").write_text(
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
    args.stats.parent.mkdir(parents=True, exist_ok=True)
    args.stats.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n")

    print(f"passes: {stats['pass_dirs']}  support >= {stats['support_threshold']}")
    for doc_id in sorted(stats["per_document"]):
        row = stats["per_document"][doc_id]
        print(
            f"  {doc_id:26s} per-pass={row['n_per_pass']} "
            f"consensus={row['n_consensus']:3d} ({row['retention_rate']*100:5.1f}%)"
        )
    print(
        f"\n{stats['n_consensus_propositions']}/{stats['n_anchor_propositions']} kept "
        f"= {stats['overall_retention_rate']*100:.1f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
