"""Vocabulary residue: did the extractor use words the corpus did not have?

The obvious audit is a blocklist -- flag "relativity", "Einstein", "spacetime"
wherever they appear. Building the corpus proved that wrong twice, in opposite
directions:

* **False positive.** Larmor 1897 contains "any *special theory* of the
  constitution of matter". Period English, not the 1905 term. A blocklist
  would have scrubbed a genuine source sentence.
* **False negative in reverse.** Poincare's St Louis lecture of September 1904
  states "The principle of *relativity*, according to which the laws of
  physical phenomena must be the same for a stationary observer as for an
  observer carried along in a uniform motion of translation." He coined the
  phrase there. It is *in* the pre-cut corpus. Blocking it would delete the
  parent task from the very corpus that supplies it.

So residue is defined relationally rather than by list:

    residue(term) := term appears in the extractor's output
                     AND term does not appear in the corpus at that cut

That is mechanical, needs no judgment about which words "feel" anachronistic,
and it is the right question anyway. An extractor that only recombines words
the corpus already contains cannot be importing hindsight lexically. One that
introduces new vocabulary is doing something the corpus did not authorise, and
owes an explanation.

This catches lexical leakage only. An extractor can still leak by *selection* --
choosing which period-appropriate commitments to surface. That is what the
placebo cuts in ``cuts.py`` are for, and it is the stronger control.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Final, Iterable, Sequence


__all__ = [
    "normalise",
    "tokens",
    "corpus_vocabulary",
    "ResidueReport",
    "audit_residue",
    "SENTINEL_TERMS",
]

_WORD_RE: Final[re.Pattern[str]] = re.compile(r"[a-z][a-z'-]*")

#: Terms whose *absence* from a cut is expected, tracked so the report can say
#: which of them a given cut does and does not license. Purely diagnostic --
#: nothing is blocked on this list. Poincare 1904 puts "relativity" inside the
#: 1904 cut and outside the 1897 and 1880 cuts, which is exactly the kind of
#: fact the placebo design needs to be explicit about.
SENTINEL_TERMS: Final[tuple[str, ...]] = (
    "relativity",
    "einstein",
    "minkowski",
    "spacetime",
    "postulate",
    "simultaneity",
    "simultaneous",
    "synchronise",
    "synchronize",
    "invariant",
    "covariant",
    "kinematics",
)


def normalise(text: str) -> str:
    return text.lower().replace("’", "'").replace("æ", "ae")


def tokens(text: str) -> list[str]:
    return _WORD_RE.findall(normalise(text))


#: Ordered longest-first so "-ations" is stripped before "-s".
_SUFFIXES: Final[tuple[str, ...]] = (
    "ations", "ation", "ingly", "ements", "ement", "ences", "ence",
    "ances", "ance", "ities", "ity", "ously", "ous", "ives", "ive",
    "ings", "ing", "edly", "ed", "ers", "er", "est", "ly", "es", "s",
    "'s", "'",
)


def stem(token: str) -> str:
    """A deliberately crude suffix stripper, used only for diagnosis.

    This does **not** feed any gate. Its one job is to answer a question the
    raw residue measure cannot: is the residue made of anachronistic *concepts*,
    or merely of inflected forms of words the corpus already has? Those call for
    completely different repairs, and conflating them would be the DR3 mistake
    in a new costume.
    """
    token = token.rstrip("'")
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def stemmed_residue(
    outputs: Sequence[str],
    corpus_documents: Sequence[str],
    *,
    allow: Iterable[str] = (),
) -> tuple[str, ...]:
    """Residue types that survive stemming on both sides. Diagnostic only."""
    licensed = {stem(t) for d in corpus_documents for t in tokens(d)}
    licensed |= {stem(normalise(a)) for a in allow}
    emitted = {t for o in outputs for t in tokens(o)}
    return tuple(sorted({t for t in emitted if stem(t) not in licensed}))


def corpus_vocabulary(documents: Iterable[str]) -> set[str]:
    """Every word type the corpus contains, as the licensing set."""
    vocabulary: set[str] = set()
    for document in documents:
        vocabulary.update(tokens(document))
    return vocabulary


@dataclass(frozen=True)
class ResidueReport:
    cut_year: int
    n_output_tokens: int
    n_output_types: int
    #: Word types in the output that the corpus at this cut does not contain.
    residue_types: tuple[str, ...]
    residue_counts: dict[str, int]
    #: Which sentinel terms the corpus itself licenses at this cut.
    sentinels_in_corpus: tuple[str, ...]
    sentinels_absent: tuple[str, ...]

    @property
    def residue_rate(self) -> float:
        return 0.0 if not self.n_output_types else len(self.residue_types) / self.n_output_types

    @property
    def clean(self) -> bool:
        return not self.residue_types


def audit_residue(
    outputs: Sequence[str],
    corpus_documents: Sequence[str],
    *,
    cut_year: int,
    allow: Iterable[str] = (),
) -> ResidueReport:
    """Compare extractor output vocabulary against the corpus vocabulary.

    ``allow`` covers structural words the schema itself introduces (field
    names, connectives) that no source sentence would supply. Keep it short and
    keep it declared -- every entry is a hole in the audit.
    """
    licensed = corpus_vocabulary(corpus_documents) | {normalise(a) for a in allow}
    counts: Counter[str] = Counter()
    total = 0
    for output in outputs:
        for token in tokens(output):
            total += 1
            if token not in licensed:
                counts[token] += 1

    return ResidueReport(
        cut_year=cut_year,
        n_output_tokens=total,
        n_output_types=len({t for o in outputs for t in tokens(o)}),
        residue_types=tuple(sorted(counts)),
        residue_counts=dict(counts),
        sentinels_in_corpus=tuple(s for s in SENTINEL_TERMS if s in licensed),
        sentinels_absent=tuple(s for s in SENTINEL_TERMS if s not in licensed),
    )
