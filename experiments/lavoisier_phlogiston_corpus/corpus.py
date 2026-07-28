"""Corpus scaffolding for the Lavoisier / phlogiston case of the DCD multi-case test.

The Dynamics of Conceptual Deletion paper names Case 3 as Lavoisier's chemical
revolution (1783-1789): the deleted commitment is phlogiston, the substance-of-
combustion picture that is silently load-bearing in every pre-Lavoisier
combustion account. The pre-revolutionary corpus is eighteenth-century
chemistry up to Lavoisier's *Traite Elementaire de Chimie* (1789).

This module names the documents. A separate future run would extract
commitments and score P(t); nothing here does that. Fetching / caching lives
in ``fetch.py``, and the human-readable inventory is ``CORPUS_MANIFEST.md``.

Each ``SourceSpec`` carries the year its *content* entered the public record.
When the *vehicle* (translation, compilation) postdates the content, that is
flagged with ``provenance_risk``, mirroring the convention used by the
electrodynamics corpus in ``experiments/date_cut_retrodiction/corpus.py``.

Wikisource coverage of eighteenth-century primary chemistry is thin. Priestley,
Cavendish, Scheele, Kirwan, Stahl, Black, and Hales all have main-namespace
Wikisource author pages, but their primary chemistry texts are either scanned
without a main-namespace transclusion (Cavendish's 1921 *Scientific Papers*
Volume I, Priestley's 1772 *Observations on different kinds of air*) or absent
entirely. ``CORPUS_MANIFEST.md`` documents each gap; this list contains only
sources that fetched to substantive chemistry content on inspection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


__all__ = [
    "SourceSpec",
    "SOURCES",
    "PRE_REVOLUTIONARY_SOURCES",
    "ORACLE_SOURCES",
]


@dataclass(frozen=True)
class SourceSpec:
    """A corpus document and the year its content became public.

    ``oracle`` marks Lavoisier's *Traite* (1789), the document whose deletion
    of phlogiston is the event the P(t) multi-case test tries to retrodict.
    The pre-revolutionary corpus is everything with ``oracle=False``.
    """

    doc_id: str
    wikisource_title: str
    author: str
    #: Year the content entered the public record. The cut compares against this.
    year: int
    #: Set when the *vehicle* carrying the content postdates the content itself.
    provenance_risk: bool = False
    #: True for Lavoisier 1789; False for every pre-revolutionary document.
    oracle: bool = False
    note: str = ""


#: Pre-revolutionary corpus (content <= 1789, excluding Lavoisier's *Traite*).
#:
#: The Wikisource collection of primary eighteenth-century chemistry documents
#: in English is dominated by Boyle's *Sceptical Chymist* (1661), the direct
#: precursor to the substance-based chemistry of the eighteenth century.
#: Boyle's analysis of the Peripatetic elements (earth / water / air / fire)
#: and of the Paracelsian tria prima (salt / sulphur / mercury) is the
#: intellectual background against which Stahl's phlogiston picture and its
#: eventual displacement by Lavoisier take place. It sits in the corpus in
#: that role, not as a claim that 1661 is eighteenth-century chemistry.
PRE_REVOLUTIONARY_SOURCES: Final[tuple[SourceSpec, ...]] = (
    SourceSpec(
        "boyle_1661_praeface_introductory",
        "Sceptical Chymist/Praeface Introductory",
        "Robert Boyle",
        1661,
        note="Boyle sets the terms of the whole book: what would count as evidence for or against the 'principles' of the chymists.",
    ),
    SourceSpec(
        "boyle_1661_physiological_considerations",
        "Sceptical Chymist/Physiological Considerations",
        "Robert Boyle",
        1661,
        note="Framing chapter on the philosophical status of the elements-vs-principles debate.",
    ),
    SourceSpec(
        "boyle_1661_part_1",
        "Sceptical Chymist/The First Part",
        "Robert Boyle",
        1661,
        note="Carneades opens the dialogue against the four Peripatetic elements as universal ingredients.",
    ),
    SourceSpec(
        "boyle_1661_part_2",
        "Sceptical Chymist/The Second Part",
        "Robert Boyle",
        1661,
        note="Attacks the assumption that fire is a universal analytical instrument, and that its products are the ingredients of the analysed body.",
    ),
    SourceSpec(
        "boyle_1661_part_3",
        "Sceptical Chymist/The Third Part",
        "Robert Boyle",
        1661,
        note="Argues that fire produces different resolutions in different bodies, undercutting the three-principle tria prima.",
    ),
    SourceSpec(
        "boyle_1661_part_4",
        "Sceptical Chymist/The Fourth Part",
        "Robert Boyle",
        1661,
        note="Extends the fire-produces-artifacts argument; contains calcinations and residues discussion directly relevant to phlogiston-era vocabulary.",
    ),
    SourceSpec(
        "boyle_1661_part_5",
        "Sceptical Chymist/The Fifth Part",
        "Robert Boyle",
        1661,
        note="Discusses the substances chymists call salt / sulphur / mercury and whether they are simple principles or already compounded.",
    ),
    SourceSpec(
        "boyle_1661_part_6",
        "Sceptical Chymist/The Sixth Part",
        "Robert Boyle",
        1661,
        note="Alternative corpuscular / textural account of chemical change - Boyle's positive proposal, forerunner of the phlogiston-era 'principle' vocabulary.",
    ),
    SourceSpec(
        "boyle_1661_conclusion",
        "Sceptical Chymist/The Conclusion",
        "Robert Boyle",
        1661,
        note="Carneades summarises. Short but explicit about what he did and did not intend to overthrow.",
    ),
)


#: Oracle: Lavoisier's *Traite* (1789), read via Kerr's 1790 English translation.
#:
#: The content date is 1789 (Paris edition). The vehicle is Kerr's *Elements of
#: Chemistry, in a New Systematic Order, containing all the modern Discoveries*
#: (Edinburgh, 1790). The gap is one year and the translator, Robert Kerr, is
#: producing a straight translation rather than a compilation. That is a
#: weaker provenance risk than the 1913 Halsted compilation carrying Poincare
#: 1898/1904 in the DCR corpus, so ``provenance_risk`` is left off; the one
#: year of vehicle drift is noted per document. Only the sections whose main-
#: namespace Wikisource transclusion is currently complete are included.
ORACLE_SOURCES: Final[tuple[SourceSpec, ...]] = (
    SourceSpec(
        "lavoisier_1789_preface_of_the_author",
        "Elements of Chemistry (Lavoisier, tr. Kerr)/Preface of the Author",
        "Antoine Lavoisier",
        1789,
        oracle=True,
        note="Lavoisier's own 1789 preface to the *Traite*, in Kerr's 1790 translation. States the new nomenclature program.",
    ),
    SourceSpec(
        "lavoisier_1789_part_1",
        "Elements of Chemistry (Lavoisier, tr. Kerr)/Part I",
        "Antoine Lavoisier",
        1789,
        oracle=True,
        note="Part I of the *Traite* in Kerr's 1790 translation. The core exposition of the oxygen theory of combustion and the direct attack on phlogiston.",
    ),
)


SOURCES: Final[tuple[SourceSpec, ...]] = PRE_REVOLUTIONARY_SOURCES + ORACLE_SOURCES
