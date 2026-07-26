"""The residue measure, repaired.

DCR1's ``residue.py`` failed its own gate at 5.49–7.05% against a 5% threshold.
Reading the residue showed why, and the diagnosis had two parts that call for
opposite responses:

* **Most of it was not leakage.** ``communicates`` against a corpus containing
  ``communicate``; ``Abraham's`` against ``Abraham``; ``poincare`` against
  ``Poincaré``, because DCR1 folded the ``æ`` ligature but not accents. These
  are artefacts of comparing surface forms, and a measure dominated by them
  answers a question nobody asked.
* **Some of it was real.** ``invariant``, ``subluminal``, ``nonlinear``,
  ``asymmetry``, ``adhoc`` survive stemming. The extractor does import a little
  modern vocabulary, and that is exactly what the measure exists to catch.

So v2 folds accents, strips possessives, and compares stems on both sides,
which removes the first category without touching the second.

**This module does not set a threshold.** DR3's H4″ was frozen at 10× against a
toy whose base rate capped it at 7×, and the lesson DR4 drew was: calibrate the
measure, *then* freeze the gate. ``calibrate_residue_v2.py`` measures what v2
reports on the actual corpus; ``DCR1B_PREREGISTRATION.md`` fixes the threshold
afterwards. Instruments here, thresholds there, in that order.

The relational definition is unchanged and is the part worth keeping: a term is
residue iff the extractor emits it and the corpus at that cut does not contain
it. The corpus proved a blocklist wrong in both directions — Larmor's "special
theory" is innocent, Poincaré's "relativity" is genuine and pre-cut.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Final, Iterable, Sequence

from experiments.date_cut_retrodiction.residue import SENTINEL_TERMS, stem as _stem_v1


__all__ = [
    "normalise_v2",
    "stem_v2",
    "tokens_v2",
    "corpus_vocabulary_v2",
    "ResidueReportV2",
    "audit_residue_v2",
]

_WORD_RE: Final[re.Pattern[str]] = re.compile(r"[a-z][a-z'-]*")
_POSSESSIVE: Final[re.Pattern[str]] = re.compile(r"'s\b|'\b")


def stem_v2(token: str) -> str:
    """v1's stemmer plus a trailing-``e`` rule, which v1 needed and lacked.

    v1 mapped ``communicates`` to ``communicat`` but left ``communicate``
    alone, so an inflected pair failed to match and counted as residue -- the
    very artefact v2 exists to remove. Folding the bare ``e`` makes the two
    sides symmetric. The four-character floor stops it eating short words:
    ``time`` is left intact.

    v1's ``stem`` is deliberately not edited; DCR1 published numbers computed
    with it.
    """
    stemmed = _stem_v1(token)
    if stemmed.endswith("e") and len(stemmed) - 1 >= 4:
        return stemmed[:-1]
    return stemmed


def normalise_v2(text: str) -> str:
    """Lowercase, fold accents and ligatures, drop possessives.

    Accent folding is the fix for ``poincare`` being reported as residue against
    a corpus that says ``Poincaré`` on every other page — a pure artefact that
    inflated DCR1's measure while telling us nothing.
    """
    text = text.lower().replace("’", "'").replace("æ", "ae").replace("œ", "oe")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return _POSSESSIVE.sub("", text)


def tokens_v2(text: str) -> list[str]:
    return _WORD_RE.findall(normalise_v2(text))


def corpus_vocabulary_v2(documents: Iterable[str]) -> set[str]:
    """Stems of every word type the corpus contains."""
    return {stem_v2(t) for document in documents for t in tokens_v2(document)}


@dataclass(frozen=True)
class ResidueReportV2:
    cut_year: int
    n_output_types: int
    residue_types: tuple[str, ...]
    residue_counts: dict[str, int]
    sentinels_in_corpus: tuple[str, ...]
    sentinels_absent: tuple[str, ...]

    @property
    def residue_rate(self) -> float:
        return 0.0 if not self.n_output_types else len(self.residue_types) / self.n_output_types

    @property
    def clean(self) -> bool:
        return not self.residue_types


def audit_residue_v2(
    outputs: Sequence[str],
    corpus_documents: Sequence[str],
    *,
    cut_year: int,
    allow: Iterable[str] = (),
) -> ResidueReportV2:
    licensed = corpus_vocabulary_v2(corpus_documents)
    licensed |= {stem_v2(normalise_v2(a)) for a in allow}

    counts: Counter[str] = Counter()
    emitted: set[str] = set()
    for output in outputs:
        for token in tokens_v2(output):
            emitted.add(token)
            if stem_v2(token) not in licensed:
                counts[token] += 1

    return ResidueReportV2(
        cut_year=cut_year,
        n_output_types=len(emitted),
        residue_types=tuple(sorted(counts)),
        residue_counts=dict(counts),
        sentinels_in_corpus=tuple(
            s for s in SENTINEL_TERMS if stem_v2(normalise_v2(s)) in licensed
        ),
        sentinels_absent=tuple(
            s for s in SENTINEL_TERMS if stem_v2(normalise_v2(s)) not in licensed
        ),
    )
