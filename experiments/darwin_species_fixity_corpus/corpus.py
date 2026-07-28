"""Corpus scaffolding for the Darwin / species-fixity case of the DCD multi-case test.

The Dynamics of Conceptual Deletion paper names Case 2 as Darwin's *On the
Origin of Species* (1859): the deleted commitment is **species fixity** — that
species are natural kinds with essential boundaries, permanent categories
created separately, immutable across generations. The pre-revolutionary corpus
is eighteenth- and early-nineteenth-century natural history, geology, and
philosophy of science, up to (but not including) Darwin's *Origin*.

This module names the documents. A separate future run would extract
commitments and score P(t); nothing here does that. Fetching / caching lives
in ``fetch.py``, and the human-readable inventory is ``CORPUS_MANIFEST.md``.

Each ``SourceSpec`` carries the year its *content* entered the public record.
When the *vehicle* (reprint, later edition, or joint publication) postdates
the content or sits close enough to the deletion event to constitute a leak
risk, that is flagged with ``provenance_risk``, mirroring the convention used
by the electrodynamics corpus in ``experiments/date_cut_retrodiction/corpus.py``
and the Lavoisier corpus in ``experiments/lavoisier_phlogiston_corpus/corpus.py``.

Wikisource coverage of pre-1859 biology is much richer than its coverage of
eighteenth-century chemistry: Erasmus Darwin's *Zoonomia* (1794-96), Malthus's
*Essay on the Principle of Population* (1798), Herschel's *Preliminary
Discourse* (1830), and Wallace's 1855 Sarawak-law paper are all in main
namespace and transcluded end-to-end. The big absences are Lyell's *Principles
of Geology* (1830-33), Chambers's *Vestiges* (1844), Cuvier, Lamarck, and
Whewell — every documented gap is in ``CORPUS_MANIFEST.md``.
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

    ``oracle`` marks Darwin's *On the Origin of Species* (1859), the document
    whose deletion of species fixity is the event the P(t) multi-case test
    tries to retrodict. The pre-revolutionary corpus is everything with
    ``oracle=False``.
    """

    doc_id: str
    wikisource_title: str
    author: str
    #: Year the content entered the public record. The cut compares against this.
    year: int
    #: Set when the *vehicle* carrying the content postdates the content itself,
    #: or when the document sits close enough to the deletion event that its
    #: inclusion at a cut before that event could leak post-cut material.
    provenance_risk: bool = False
    #: True for Darwin 1859; False for every pre-revolutionary document.
    oracle: bool = False
    note: str = ""


#: Pre-revolutionary corpus (content <= 1858, i.e. strictly before *Origin*).
#:
#: Four strata, chronological:
#:
#:   1794-1796  Erasmus Darwin, *Zoonomia*. Grandfather's book on generation;
#:              contains the earliest English-language transmutationist
#:              speculation, but is embedded in a Newtonian medical framework
#:              that treats species as generation-preserved kinds.
#:   1798       Malthus, *Essay on the Principle of Population*. Darwin's
#:              acknowledged direct inspiration for the mechanism of natural
#:              selection. Population pressure argued without any species
#:              change; the demographic frame presupposes species fixity.
#:   1830       Herschel, *A Preliminary Discourse on the Study of Natural
#:              Philosophy*. Darwin cited it as methodological inspiration.
#:              The book is about scientific method generally, not biology; it
#:              is included because it shaped Darwin's argumentative style and
#:              because it treats natural-history examples throughout.
#:   1839-1858  Immediate precursors: Darwin's *Journal of Researches* (1839;
#:              vehicle is the 1860 John Murray reprint of the 1845 second
#:              edition, so provenance_risk is set); Wallace's 1855 Sarawak-
#:              law paper; and the Wallace-Darwin 1858 joint communication to
#:              the Linnean Society (marked provenance_risk because it is the
#:              first public statement of natural selection and stands as the
#:              immediate germ of *Origin*).
PRE_REVOLUTIONARY_SOURCES: Final[tuple[SourceSpec, ...]] = (
    # --- Erasmus Darwin, Zoonomia (1794-1796) -----------------------------
    SourceSpec(
        "erasmus_darwin_1794_zoonomia_preface",
        "Zoonomia/I.Preface",
        "Erasmus Darwin",
        1794,
        note="Preface to Volume I of Zoonomia. Sets the medical / physiological programme within which the transmutationist speculation of Section XXXIX is later embedded.",
    ),
    SourceSpec(
        "erasmus_darwin_1794_zoonomia_generation_39",
        "Zoonomia/I.XXXIX",
        "Erasmus Darwin",
        1794,
        note="Section XXXIX 'Of Generation'. Contains the passages later cited as the earliest English-language transmutationist speculation; also contains the fixed-form assumptions that dominate the surrounding physiology.",
    ),
    SourceSpec(
        "erasmus_darwin_1794_zoonomia_generation_40",
        "Zoonomia/I.XL",
        "Erasmus Darwin",
        1794,
        note="Section XL 'Of Generation'. Continuation of the generation-and-heredity discussion.",
    ),
    # --- Malthus, Essay on the Principle of Population (1798, 1st edition) --
    SourceSpec(
        "malthus_1798_essay_ch1",
        "An Essay on the Principle of Population/Chapter I",
        "Thomas Robert Malthus",
        1798,
        note="Chapter I. The famous statement of the two-ratio principle (geometric population, arithmetic subsistence). Frame is human demographics; species fixity is presupposed.",
    ),
    SourceSpec(
        "malthus_1798_essay_ch2",
        "An Essay on the Principle of Population/Chapter II",
        "Thomas Robert Malthus",
        1798,
        note="Chapter II. Different states of society under the population principle. Darwin credited Chapters II-III with giving him the mechanism for natural selection.",
    ),
    SourceSpec(
        "malthus_1798_essay_ch3",
        "An Essay on the Principle of Population/Chapter III",
        "Thomas Robert Malthus",
        1798,
        note="Chapter III. Population pressure applied to the shepherd states of northern Europe.",
    ),
    SourceSpec(
        "malthus_1798_essay_ch5",
        "An Essay on the Principle of Population/Chapter V",
        "Thomas Robert Malthus",
        1798,
        note="Chapter V. The second of Malthus's chapters attacking Godwin; contains the vivid 'nature's mighty feast' passage that Darwin extended to non-human species.",
    ),
    SourceSpec(
        "malthus_1798_essay_ch7",
        "An Essay on the Principle of Population/Chapter VII",
        "Thomas Robert Malthus",
        1798,
        note="Chapter VII. On the 'positive checks' (famine, disease, war). This is the mechanism Darwin extends: differential survival under scarcity as a selection pressure.",
    ),
    # --- Herschel, Preliminary Discourse (1830) --------------------------
    SourceSpec(
        "herschel_1830_prelim_p1c1",
        "A Preliminary Discourse on the Study of Natural Philosophy/Part 1, chap. 1",
        "John Herschel",
        1830,
        note="Part I, Chapter 1. On the general utility of natural philosophy. Darwin cited the Preliminary Discourse as methodological inspiration.",
    ),
    SourceSpec(
        "herschel_1830_prelim_p1c2",
        "A Preliminary Discourse on the Study of Natural Philosophy/Part 1, chap. 2",
        "John Herschel",
        1830,
        note="Part I, Chapter 2. On the nature and analysis of physical science.",
    ),
    SourceSpec(
        "herschel_1830_prelim_p1c3",
        "A Preliminary Discourse on the Study of Natural Philosophy/Part 1, chap. 3",
        "John Herschel",
        1830,
        note="Part I, Chapter 3. Of the state of physical science generally at the present period.",
    ),
    SourceSpec(
        "herschel_1830_prelim_p2c6",
        "A Preliminary Discourse on the Study of Natural Philosophy/Part 2, chap. 6",
        "John Herschel",
        1830,
        note="Part II, Chapter 6. Of the higher degrees of inductive generalisation and the formation of theories. Explicit methodological arguments Darwin reused in *Origin*.",
    ),
    SourceSpec(
        "herschel_1830_prelim_p3c3",
        "A Preliminary Discourse on the Study of Natural Philosophy/Part 3, chap. 3",
        "John Herschel",
        1830,
        note="Part III, Chapter 3. Of the subdivision of physics into distinct branches and their mutual relations; discusses natural history and classification in the fixed-kind idiom.",
    ),
    # --- Darwin, Journal of Researches (1839; 1860 John Murray reprint) --
    # Vehicle for the Wikisource transcription is the 1860 John Murray printing
    # of the 1845 second edition, so provenance_risk is set: Darwin's 1845 text
    # was written by an author who already privately believed in transmutation,
    # and the 1860 reprint sits one year after *Origin*. Content year 1845.
    SourceSpec(
        "darwin_1845_beagle_ch8",
        "Journal of researches into the natural history and geology of the countries visited during the voyage of H.M.S. Beagle round the world/Chapter 8",
        "Charles Darwin",
        1845,
        provenance_risk=True,
        note="Chapter VIII. Patagonia and the extinct large quadrupeds. Fossil discoveries that later fed the succession-of-types argument in *Origin*. Provenance risk: 1860 John Murray reprint of the 1845 second edition; the author had privately abandoned species fixity by then.",
    ),
    SourceSpec(
        "darwin_1845_beagle_ch17",
        "Journal of researches into the natural history and geology of the countries visited during the voyage of H.M.S. Beagle round the world/Chapter 17",
        "Charles Darwin",
        1845,
        provenance_risk=True,
        note="Chapter XVII. The Galapagos Archipelago. The famous chapter on inter-island species differences; 1845 revisions introduced the closest-to-transmutation phrasing in the pre-*Origin* Darwin corpus. Provenance risk: 1860 John Murray reprint of the 1845 second edition.",
    ),
    # --- Wallace, Sarawak law paper (1855) -----------------------------
    SourceSpec(
        "wallace_1855_sarawak",
        "1855 The Annals and Magazine of Natural History/On the Law which has regulated the Introduction of New Species",
        "Alfred Russel Wallace",
        1855,
        note="Wallace's 'Sarawak law' paper in *Annals and Magazine of Natural History*, September 1855. Argues species arise in geographic and geologic proximity to closely allied pre-existing species -- a strong empirical challenge to independent-creation species fixity, but without a mechanism.",
    ),
    # --- Wallace-Darwin joint communication (1858) --------------------
    SourceSpec(
        "wallace_darwin_1858_linnean",
        "On the tendency of species to form varieties; and on the Perpetuation of Varieties and Species by Natural Means of Selection",
        "Alfred Russel Wallace and Charles Darwin",
        1858,
        provenance_risk=True,
        note="The joint Linnean Society communication of 1 July 1858 (Wallace's 1858 Ternate essay + Darwin's 1844 essay extract + Darwin's 1857 letter to Asa Gray). First public statement of natural selection. Provenance risk: immediate germ of *Origin*, published one year before the deletion event and by the deleters themselves.",
    ),
)


#: Oracle: Darwin's *On the Origin of Species*, John Murray, London, 1859
#: (first edition), Wikisource root ``On the Origin of Species (1859)``.
#:
#: The 1859 first edition transcription is complete in Wikisource main
#: namespace: Introduction + fourteen chapters + Index. The chapters together
#: are the direct articulation and defence of the transmutation-by-natural-
#: selection alternative to species fixity. No provenance risk (the vehicle IS
#: the content; John Murray, London, 1859, first printing).
ORACLE_SOURCES: Final[tuple[SourceSpec, ...]] = (
    SourceSpec(
        "darwin_1859_origin_introduction",
        "On the Origin of Species (1859)/Introduction",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Introduction. Darwin's own statement of the argument, the origin of the enquiry, and the acknowledgement of Wallace's independent arrival at the same theory.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch1",
        "On the Origin of Species (1859)/Chapter I",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter I. Variation under domestication. The evidence Darwin uses to open the case that species boundaries are not sharp.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch2",
        "On the Origin of Species (1859)/Chapter II",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter II. Variation under nature. Extends the argument from domestic breeds to wild populations.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch3",
        "On the Origin of Species (1859)/Chapter III",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter III. Struggle for existence. The Malthusian argument extended to all organic beings.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch4",
        "On the Origin of Species (1859)/Chapter IV",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter IV. Natural selection. The mechanism proper, and the first branching-tree argument for common descent.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch5",
        "On the Origin of Species (1859)/Chapter V",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter V. Laws of variation. Darwin's inheritance-and-development chapter, still without Mendelian genetics.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch6",
        "On the Origin of Species (1859)/Chapter VI",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter VI. Difficulties on theory. Darwin's explicit self-audit of the strongest objections to natural selection.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch7",
        "On the Origin of Species (1859)/Chapter VII",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter VII. Instinct. Extending the argument from morphology to behaviour.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch8",
        "On the Origin of Species (1859)/Chapter VIII",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter VIII. Hybridism. Directly confronts the standard fixity argument that species are defined by inter-fertility barriers.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch9",
        "On the Origin of Species (1859)/Chapter IX",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter IX. On the imperfection of the geological record. Darwin's answer to the missing-intermediates argument for species fixity.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch10",
        "On the Origin of Species (1859)/Chapter X",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter X. On the geological succession of organic beings. The palaeontological case for descent with modification.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch11",
        "On the Origin of Species (1859)/Chapter XI",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter XI. Geographical distribution. Biogeography as evidence against independent creation.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch12",
        "On the Origin of Species (1859)/Chapter XII",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter XII. Geographical distribution continued. Oceanic islands and their distinctive biota.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch13",
        "On the Origin of Species (1859)/Chapter XIII",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter XIII. Mutual affinities of organic beings: morphology, embryology, rudimentary organs. The comparative-anatomy case for common descent.",
    ),
    SourceSpec(
        "darwin_1859_origin_ch14",
        "On the Origin of Species (1859)/Chapter XIV",
        "Charles Darwin",
        1859,
        oracle=True,
        note="Chapter XIV. Recapitulation and conclusion. Darwin's own summary of the whole argument.",
    ),
)


SOURCES: Final[tuple[SourceSpec, ...]] = PRE_REVOLUTIONARY_SOURCES + ORACLE_SOURCES
