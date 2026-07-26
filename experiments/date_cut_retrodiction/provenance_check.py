"""Corroborate the two translation-risk documents against their French originals.

Two corpus documents reach us through *The Foundations of Science* (New York,
1913), George Bruce Halsted's English compilation of Poincare. Their content is
pre-cut -- "La mesure du temps" is 1898, the St Louis lecture is September 1904
-- but the vehicle is not, and Halsted translated knowing what happened in 1905.

This matters more than it first appears. At the 1904 cut, **every** sentinel
term in the corpus (``relativity``, ``postulate``, ``simultaneity``,
``simultaneous``) comes from these two documents and no other. Drop them and
the target vocabulary vanishes entirely. So if Halsted's word choices were
shaped by hindsight, the corpus would be handing the extractor its answer
through a 1913 translator.

The check: do the French originals, both indisputably pre-cut, contain the
corresponding terms? If yes, the English is faithful and the vocabulary is
genuinely period. If no, these documents must be dropped and the target cut
rebuilt without them.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.provenance_check
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.fetch import DATA_DIR, _drop_chrome, _strip_html


__all__ = ["FrenchSource", "FRENCH_SOURCES", "check_provenance"]

FR_API: Final[str] = "https://fr.wikisource.org/w/api.php"


@dataclass(frozen=True)
class FrenchSource:
    doc_id: str
    corroborates: str
    title: str
    year: int
    #: French terms whose presence would exonerate the English translation.
    expect_terms: tuple[str, ...]


FRENCH_SOURCES: Final[tuple[FrenchSource, ...]] = (
    FrenchSource(
        "fr_poincare_1898_mesure_du_temps",
        "poincare_1898_time",
        "La mesure du temps (Poincaré)",
        1898,
        ("simultanéité", "simultané", "postulat"),
    ),
    FrenchSource(
        "fr_poincare_1904_crise",
        "poincare_1904_stlouis",
        "La Valeur de la Science/Chapitre VIII. La crise actuelle de la physique mathématique",
        1904,
        ("relativité", "principe de relativité", "temps local", "éther"),
    ),
)


def _fetch_fr(title: str) -> str:
    payload = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "redirects": "1",
        "format": "json",
        "formatversion": "2",
    }
    import urllib.parse
    import urllib.request

    url = f"{FR_API}?{urllib.parse.urlencode(payload)}"
    request = urllib.request.Request(url, headers={"User-Agent": "rde-research/0.1"})
    with urllib.request.urlopen(request, timeout=60) as handle:
        markup = json.loads(handle.read().decode("utf-8"))["parse"]["text"]
    return _strip_html(_drop_chrome(markup))


def check_provenance(*, data_dir: Path = DATA_DIR) -> dict[str, Any]:
    fr_dir = data_dir / "corroboration"
    fr_dir.mkdir(parents=True, exist_ok=True)

    findings: list[dict[str, Any]] = []
    for source in FRENCH_SOURCES:
        path = fr_dir / f"{source.doc_id}.txt"
        text = path.read_text(encoding="utf-8") if path.exists() else _fetch_fr(source.title)
        if not path.exists():
            path.write_text(text, encoding="utf-8")

        lowered = text.lower()
        counts = {term: lowered.count(term.lower()) for term in source.expect_terms}
        findings.append(
            {
                "doc_id": source.doc_id,
                "corroborates": source.corroborates,
                "title": source.title,
                "year": source.year,
                "chars": len(text),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "term_counts": counts,
                "all_terms_present": all(n > 0 for n in counts.values()),
            }
        )

    verdict: dict[str, Any] = {
        "kind": "provenance_corroboration",
        "question": (
            "Do the pre-cut French originals contain the terms Halsted's 1913 "
            "English translation uses, or did the translator supply them?"
        ),
        "findings": findings,
        "translation_exonerated": all(f["all_terms_present"] for f in findings),
    }
    (data_dir / "provenance_check.json").write_text(
        json.dumps(verdict, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return verdict


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corroborate Poincare translations.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args(argv)

    verdict = check_provenance(data_dir=args.data_dir)
    for finding in verdict["findings"]:
        print(f"  {finding['doc_id']}  ({finding['chars']:,} chars)")
        for term, count in finding["term_counts"].items():
            flag = "ok " if count else "MISSING"
            print(f"      {flag} {term}: {count}")
    print(f"\ntranslation_exonerated = {verdict['translation_exonerated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
