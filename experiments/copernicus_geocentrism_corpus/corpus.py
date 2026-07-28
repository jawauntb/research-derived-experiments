"""Corpus scaffolding for the Copernicus / geocentric-priority case of the DCD multi-case test.

The Dynamics of Conceptual Deletion paper names Case 1 as Copernicus's
*De revolutionibus orbium coelestium* (1543): the deleted commitment is
**geocentric priority** -- the assumption that the Earth is at rest at the
centre of the cosmos, that celestial motions are literally motions of the
celestial bodies around Earth, and that the Earth's location is dynamically
distinguished. The pre-revolutionary corpus is pre-1543 astronomy and
cosmology: Aristotelian celestial physics, medieval Islamic and Jewish
commentaries on Aristotelian cosmology, and late-medieval practical astronomy.

This module names the documents. A separate future run would extract
commitments and score P(t); nothing here does that. Fetching / caching lives
in ``fetch.py``, and the human-readable inventory is ``CORPUS_MANIFEST.md``.

Each ``SourceSpec`` carries the year its *content* entered the public record.
When the *vehicle* (translation, compilation) postdates the content, that is
flagged with ``provenance_risk``, mirroring the convention used by the
electrodynamics corpus in ``experiments/date_cut_retrodiction/corpus.py``, the
Lavoisier corpus in ``experiments/lavoisier_phlogiston_corpus/corpus.py``, and
the Darwin corpus in ``experiments/darwin_species_fixity_corpus/corpus.py``.

**Provenance is worse here than in the other three corpora.** The other three
work with primary texts in an author's native English (Darwin, Malthus,
Herschel, Boyle) or an English translation completed within one to two
generations of the primary text (Kerr 1790 of Lavoisier 1789; Halsted 1913 of
Poincare 1898-1904). The Copernicus corpus works with primary texts in
languages the author did not write in: ancient Greek (Aristotle, c.350 BCE),
medieval Judeo-Arabic (Maimonides, c.1190), late Latin (Boethius, c.524), and
Middle English (Chaucer, 1391). Every English rendering on Wikisource is a
nineteenth- or early-twentieth-century academic translation whose vocabulary
was fixed after the deletion event of interest. That is a structural risk of
anachronistic vocabulary leaking into the pre-revolutionary corpus, and is
discussed explicitly in ``CORPUS_MANIFEST.md``.

**Wikisource coverage of pre-1543 astronomy is very thin.** Ptolemy's
*Almagest* is not transcribed in main namespace; Sacrobosco's *De Sphaera*
is not transcribed; Regiomontanus's *Epytoma in Almagestum* is not
transcribed; Peurbach's *Theoricae novae planetarum* is not transcribed;
Nicholas of Cusa's *De docta ignorantia* is not transcribed; Alhazen's
*Doubts on Ptolemy* is not transcribed; Copernicus's own *De revolutionibus*
(the oracle) is not transcribed in English on Wikisource main namespace
(only a Latin-Wikisource link and an 1879 German translation are named on
``Author:Nicolaus Copernicus``). Every documented gap and the specific
Wikisource evidence for it is in ``CORPUS_MANIFEST.md``. This list contains
only sources that fetched to substantive text on inspection.

**Oracle unavailable on Wikisource.** ``ORACLE_SOURCES`` still carries a
``SourceSpec`` for *De revolutionibus*, pointed at the best-guess English
title, so the fetch will attempt it and record the failure in
``results/fetch_summary.json``. Any downstream P(t) test on this corpus must
first source the oracle outside Wikisource (HathiTrust or Great Books of the
Western World both carry a Charles Glenn Wallis translation of Book I) or
skip this case; a P(t) test with no oracle has nothing to retrodict.
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

    ``oracle`` marks Copernicus's *De revolutionibus* (1543), the document
    whose deletion of geocentric priority is the event the P(t) multi-case
    test tries to retrodict. The pre-revolutionary corpus is everything with
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
    #: For this corpus, every source's English *translation* postdates 1543 by
    #: centuries; the flag is reserved for the stronger structural concerns
    #: documented in the note field and CORPUS_MANIFEST.md.
    provenance_risk: bool = False
    #: True for Copernicus 1543; False for every pre-revolutionary document.
    oracle: bool = False
    note: str = ""


#: Pre-revolutionary corpus (content <= 1542, i.e. strictly before *De revolutionibus*).
#:
#: Four strata, chronological:
#:
#:   c.350 BCE  Aristotle, *De Caelo* / *On the Heavens*, in J. L. Stocks's
#:              1922 Oxford translation. The founding statement of the
#:              geocentric-cosmos-as-nested-spheres picture and of the
#:              distinction between the eternal celestial and corruptible
#:              sublunary realms. Aristotle is the ambient default that every
#:              medieval and Renaissance astronomer had to either endorse or
#:              argue with; Ptolemy is technical calculation within Aristotle's
#:              cosmological frame.
#:   c.524      Boethius, *Consolation of Philosophy*, in H. R. James's 1897
#:              English translation. Only the individual poetic-meter and
#:              prose sub-pages fetch to substantive text on English
#:              Wikisource; the fuller King Alfred / Sedgefield 1900 rendering
#:              transcludes DjVu scans but does not carry the transcribed
#:              text in the transclusion (fetching it yields only page-index
#:              navigation, not prose). The three sub-pages included here are
#:              the passages most directly about the ordered geocentric-
#:              Ptolemaic cosmos.
#:   c.1190     Maimonides, *Guide for the Perplexed*, in Michael Friedlander's
#:              1904 English translation. Part II opens with 26 propositions
#:              summarising Aristotelian cosmological physics as the medieval
#:              tradition had received them, then works out the consequences
#:              for the eternity of the world, the celestial intelligences,
#:              and the doctrine of separate movers. The single most explicit
#:              medieval defence of geocentric-Aristotelian cosmology available
#:              on Wikisource main namespace in English.
#:   1391       Chaucer, *A Treatise on the Astrolabe*, in W. W. Skeat's 1894
#:              *Complete Works* edition of Chaucer's own Middle English text.
#:              A practical instrument manual for a fourteen-year-old, but
#:              built entirely on the assumption of a geocentric universe with
#:              a celestial equator, ecliptic, zodiac, and diurnal rotation
#:              of the fixed-star sphere. The nearest thing in the corpus to
#:              an unselfconscious statement of the geocentric picture as
#:              working background: no cosmological argument is being made,
#:              the geometry is simply assumed and used.
PRE_REVOLUTIONARY_SOURCES: Final[tuple[SourceSpec, ...]] = (
    # --- Aristotle, On the Heavens (De Caelo), c.350 BCE ---------------------
    # Content date c.350 BCE. Vehicle is J. L. Stocks's 1922 English translation
    # for the Clarendon Aristotle series (Oxford). Both the vehicle (1922) and
    # the intermediate manuscript tradition sit centuries after the deletion
    # event of interest (1543), so translation-vintage risk is inherent.
    SourceSpec(
        "aristotle_de_caelo_book1",
        "On the Heavens/Book I",
        "Aristotle",
        -350,
        note="Book I. The two-element cosmos: celestial aether moves naturally in circles; sublunary earth/water/air/fire move naturally in straight lines. Argues the cosmos is finite, spherical, unique. Establishes the geocentric framing that every subsequent Western astronomer inherits. Translation: J. L. Stocks, 1922 Clarendon (Oxford) edition.",
    ),
    SourceSpec(
        "aristotle_de_caelo_book2",
        "On the Heavens/Book II",
        "Aristotle",
        -350,
        note="Book II. The heavens are ungenerated and imperishable; the sphere of the fixed stars carries the diurnal motion; the planets have their own proper motions; explicit arguments against Pythagorean and Timaean cosmologies that make the Earth move. Contains the most direct pre-Copernican statement of geocentric priority. Translation: J. L. Stocks, 1922 Clarendon (Oxford) edition.",
    ),
    SourceSpec(
        "aristotle_de_caelo_book3",
        "On the Heavens/Book III",
        "Aristotle",
        -350,
        note="Book III. On the sublunary elements: their generation, coming-to-be, and passing-away. Cosmological consequence: the sublunary realm is corruption-and-change, the celestial realm is eternal circular motion. This asymmetry -- superlunary permanence vs sublunary flux -- is the deep commitment Copernicus dissolves. Translation: J. L. Stocks, 1922 Clarendon (Oxford) edition.",
    ),
    SourceSpec(
        "aristotle_de_caelo_book4",
        "On the Heavens/Book IV",
        "Aristotle",
        -350,
        note="Book IV. On the physics of the sublunary elements: heavy and light, natural place, and why heavy bodies fall toward the centre of the cosmos (which coincides with the Earth's centre). The physics that made the geocentric picture feel physically necessary and not just observationally convenient. Translation: J. L. Stocks, 1922 Clarendon (Oxford) edition.",
    ),
    # --- Boethius, Consolation of Philosophy, c.524 CE -----------------------
    # Content date c.524 (late Latin). Vehicle is H. R. James's 1897 English
    # translation, on Wikisource as forty-eight individual sub-pages (one per
    # poetic meter or prose section). The three included here are the passages
    # most directly about the ordered geocentric-Ptolemaic cosmos. Provenance
    # risk: late-Victorian English of a sixth-century Latin text; James's
    # vocabulary was fixed after the deletion event of interest.
    #
    # Note on rejected alternatives: the ``King Alfred's Version of the
    # Consolations of Boethius`` root fetches to 53 characters -- the
    # Wikisource page transcludes DjVu scans but the individual pages are not
    # transcribed into the transclusion. Chaucer's own Middle English *Boece*
    # translation (which would be a genuine pre-1543 English rendering) is not
    # on Wikisource at all. Both gaps are documented in CORPUS_MANIFEST.md.
    SourceSpec(
        "boethius_consolation_bk3m9_true_sun_james_1897",
        "The Consolation of Philosophy (James)/The True Sun",
        "Boethius",
        524,
        provenance_risk=True,
        note="Book III meter 9, 'The True Sun' in H. R. James's 1897 English translation. The most famous cosmological passage in the *Consolation*: a hymn to God as origin of the ordered cosmos, invoking the Timaean-Ptolemaic imagery of nested celestial spheres and the sun as visible image of the divine. Provenance risk: late-Victorian English vehicle.",
    ),
    SourceSpec(
        "boethius_consolation_bk4m1_souls_flight_james_1897",
        "The Consolation of Philosophy (James)/The Soul's Flight",
        "Boethius",
        524,
        provenance_risk=True,
        note="Book IV meter 1, 'The Soul's Flight' in H. R. James's 1897 English translation. The Neoplatonic ascent through the celestial spheres in explicit Ptolemaic geometry: Moon, Mercury, Venus, Sun, Mars, Jupiter, Saturn, the sphere of the fixed stars. Uses the geocentric ordering as unselfconscious poetic material. Provenance risk: late-Victorian English vehicle.",
    ),
    SourceSpec(
        "boethius_consolation_bk3p11_universal_aim_james_1897",
        "The Consolation of Philosophy (James)/The Universal Aim",
        "Boethius",
        524,
        provenance_risk=True,
        note="Book III prose 11, 'The Universal Aim' in H. R. James's 1897 English translation. Prose passage on the natural place each element seeks and the ordered directedness of the cosmos toward the good; the Aristotelian natural-place doctrine reappropriated as a theological argument. Provenance risk: late-Victorian English vehicle.",
    ),
    # --- Maimonides, Guide for the Perplexed, c.1190 -------------------------
    # Content date c.1190 (Judeo-Arabic). Vehicle is Michael Friedlander's 1904
    # second-edition English translation, based on Al-Harizi's medieval Hebrew
    # rendering. Translation-vintage risk applies but the *content* is the
    # single most explicit medieval defence of Aristotelian-Ptolemaic
    # cosmology that fetched to substantive text.
    SourceSpec(
        "maimonides_guide_pt1_friedlander_1904",
        "The Guide for the Perplexed (Friedlander)/Part I",
        "Moses Maimonides",
        1190,
        note="Guide for the Perplexed, Part I. The negative theology and the interpretation of scripture; chapters 68-72 introduce the metaphysics of separate intelligences and the celestial spheres, laying the ground for the cosmological argument of Part II. Translation: Michael Friedlander, 1904 second edition (London).",
    ),
    SourceSpec(
        "maimonides_guide_pt2_propositions_friedlander_1904",
        "The Guide for the Perplexed (Friedlander)/Part II/Propositions",
        "Moses Maimonides",
        1190,
        note="Part II Propositions. The 26 Aristotelian propositions Maimonides accepts as the physical basis of the theological argument. Propositions 1-25 are pure Aristotelian cosmology-physics (finite universe, no vacuum, celestial spheres, prime mover, incorruptibility of the heavens); proposition 26 is his single admitted point of Aristotelian doctrine he does *not* accept (eternity of the world). The most compressed statement of thirteenth-century geocentric-Aristotelian orthodoxy available on Wikisource. Translation: Michael Friedlander, 1904 second edition.",
    ),
    SourceSpec(
        "maimonides_guide_pt2_chapters_friedlander_1904",
        "The Guide for the Perplexed (Friedlander)/Part II/Chapters",
        "Moses Maimonides",
        1190,
        note="Part II Chapters. Working out of the 26 propositions: the celestial spheres and their intelligences, the arguments for and against the eternity of the world, the ordering of the heavens, and the puzzles the Aristotelian cosmological picture leaves unsolved (why does the sphere of the fixed stars rotate east-to-west while the planetary spheres rotate west-to-east? why do the planets have their peculiar epicycles?). Maimonides names the puzzles that Copernicus 1543 will claim to dissolve. Translation: Michael Friedlander, 1904 second edition.",
    ),
    # --- Chaucer, A Treatise on the Astrolabe, 1391 --------------------------
    # Content date 1391 (Middle English). Vehicle is W. W. Skeat's 1894
    # *Complete Works of Geoffrey Chaucer*, Volume III (Clarendon). Skeat's
    # edition preserves Chaucer's Middle English orthography; provenance
    # concern is editorial normalisation, not translation. The single
    # pre-1543 English-vernacular practical-astronomy text in the corpus.
    SourceSpec(
        "chaucer_astrolabe_1391_skeat_1894",
        "The Complete Works of Geoffrey Chaucer/Volume 3/A Treatise on the Astrolabe",
        "Geoffrey Chaucer",
        1391,
        note="Chaucer's *A Treatise on the Astrolabe*, written 1391 in Middle English for his ten-year-old son Lewis. Practical instrument-manual for the astrolabe, built entirely on the geocentric assumption: the celestial equator, ecliptic, zodiac, and the diurnal rotation of the fixed-star sphere. Assumes rather than argues geocentric priority; the nearest thing in the corpus to a use-without-defence source. Vehicle: W. W. Skeat's 1894 Clarendon *Complete Works of Geoffrey Chaucer* Volume III, preserving Chaucer's Middle English orthography.",
    ),
)


#: Oracle: Copernicus's *De revolutionibus orbium coelestium* (Nuremberg, 1543),
#: specifically Book I (which contains the heliocentric argument itself; later
#: books are technical planetary tables and less about the deletion).
#:
#: **This oracle is not transcribed on English Wikisource.** The
#: ``Author:Nicolaus Copernicus`` page (fetched 2026-07-27) lists only:
#:
#:   * a Latin-Wikisource link to ``la:De_revolutionibus_orbium_coelestium``
#:   * an 1879 German translation on German Wikisource
#:   * an external link to Knickerbocker's 1927 *Classics of Modern Science*
#:     chapter "The New Idea of the Universe" (pp. 21-28), which is a brief
#:     excerpt, not the full work
#:
#: The fetch attempt below will fail and be recorded as such in
#: ``results/fetch_summary.json``. Any P(t) test on this corpus must first
#: source Book I outside Wikisource -- Charles Glenn Wallis's 1939 English
#: translation (Great Books of the Western World, Vol. 16, and later Prometheus
#: Books 1995) is the standard modern English rendering, and Edward Rosen's
#: 1978 translation for the Foundations of Natural History series is the
#: standard scholarly rendering. Neither is on Wikisource, and both are still
#: in copyright.
ORACLE_SOURCES: Final[tuple[SourceSpec, ...]] = (
    SourceSpec(
        "copernicus_1543_de_revolutionibus_book1",
        "On the Revolutions of the Heavenly Spheres",
        "Nicolaus Copernicus",
        1543,
        provenance_risk=True,
        oracle=True,
        note="Placeholder for *De revolutionibus orbium coelestium* Book I (1543). No English transcription on Wikisource main namespace (see module docstring and CORPUS_MANIFEST.md for the evidence trail). The fetch will fail; the failure is the point -- it records that the oracle is unavailable and must be sourced outside Wikisource before any downstream P(t) test on this corpus can proceed. Marked provenance_risk=True as a further safeguard: any English rendering that does become available will be a post-1543 translation and must be flagged as such.",
    ),
)


SOURCES: Final[tuple[SourceSpec, ...]] = PRE_REVOLUTIONARY_SOURCES + ORACLE_SOURCES
