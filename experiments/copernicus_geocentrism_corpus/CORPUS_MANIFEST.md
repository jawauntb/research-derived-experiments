# Copernicus / Geocentric-Priority Corpus Manifest

**Purpose.** Corpus scaffolding for Case 1 of the multi-case retrospective test
named in *The Dynamics of Conceptual Deletion*
(`papers/dynamics_of_conceptual_deletion/paper.md`) and elevated to the next
directional target by the DCD1 pilot (`papers/dcd1_pilot_darwin_replication/paper.md`,
merged 2026-07-27). The deleted commitment is **geocentric priority** — the
assumption that the Earth is at rest at the centre of the cosmos, that
celestial motions are literally motions of the celestial bodies around Earth,
and that the Earth's location is dynamically distinguished. The
pre-revolutionary corpus is pre-1543 astronomy and cosmology in English
translation on Wikisource main namespace. The intended oracle is Copernicus's
*De revolutionibus orbium coelestium* (1543), Book I; **that oracle is not
available on English Wikisource** and the fetch failure is recorded in the
committed summary rather than hidden.

This file inventories the sources that survived a fetch against Wikisource,
records the gaps where Wikisource did not carry a primary text, and states
what downstream tests may and may not do with the result.

**This package is corpus preparation only.** No extraction, no tagging, no
scoring runs. Nothing here defines what the P(t) test will measure. That is a
separate future task with its own preregistration.

## Headline finding

The corpus is rich enough to run a pre-revolutionary P(t) trajectory on
Aristotelian-Ptolemaic-Chaucerian geocentric cosmology, but the **oracle is
absent from English Wikisource**. Any downstream DCD1-pilot-scale test on this
corpus must first source Copernicus 1543 Book I outside Wikisource
(Charles Glenn Wallis's 1939 Great Books translation, or Edward Rosen's 1978
Foundations of Natural History translation, are the two standard modern
English renderings; both are still in copyright), or skip this case.

## What is in the corpus

Twelve source specifications; twelve fetches attempted on 2026-07-27; eleven
substantive documents (>= 2000 chars each) and one recorded oracle failure.
Cached under `data/` (gitignored per repository root `.gitignore`),
summarised by `results/fetch_summary.json` (committed). Each carries an
SHA-256 so a re-fetch can detect drift.

Total pre-1543 substantive characters: **1,152,421** (of which 1,130,866 are
in sources not flagged for provenance risk).

### Pre-revolutionary corpus (eleven substantive documents, four strata)

Chronological strata, chosen to cover the range specified by the DCD paper's
Case 1 sketch ("Ptolemaic astronomy 1400–1543, plus Renaissance mathematical
astronomers (Regiomontanus, Peurbach, early Copernicans)") to the extent that
Wikisource covers it (which is: almost none of the specifically Renaissance
material Wikisource actually carries, so the corpus reaches further back into
the ancient and medieval sources whose canonical status made them the
Renaissance astronomer's background).

| doc_id | author | year | Wikisource title (short) | approx. size |
| --- | --- | ---: | --- | ---: |
| `aristotle_de_caelo_book1` | Aristotle | c.350 BCE | On the Heavens/Book I (Stocks 1922 tr.) | 75 kB |
| `aristotle_de_caelo_book2` | Aristotle | c.350 BCE | On the Heavens/Book II (Stocks 1922 tr.) | 69 kB |
| `aristotle_de_caelo_book3` | Aristotle | c.350 BCE | On the Heavens/Book III (Stocks 1922 tr.) | 45 kB |
| `aristotle_de_caelo_book4` | Aristotle | c.350 BCE | On the Heavens/Book IV (Stocks 1922 tr.) | 31 kB |
| `boethius_consolation_bk3m9_true_sun_james_1897` (!) | Boethius | c.524 | Consolation III m.9 (James 1897 tr.) | 2 kB |
| `boethius_consolation_bk4m1_souls_flight_james_1897` (!) | Boethius | c.524 | Consolation IV m.1 (James 1897 tr.) | 4 kB |
| `boethius_consolation_bk3p11_universal_aim_james_1897` (!) | Boethius | c.524 | Consolation III pr.11 (James 1897 tr.) | 15 kB |
| `maimonides_guide_pt1_friedlander_1904` | Maimonides | c.1190 | Guide for the Perplexed, Part I (Friedlander 1904 tr.) | 451 kB |
| `maimonides_guide_pt2_propositions_friedlander_1904` | Maimonides | c.1190 | Guide for the Perplexed, Part II Propositions (Friedlander 1904 tr.) | 13 kB |
| `maimonides_guide_pt2_chapters_friedlander_1904` | Maimonides | c.1190 | Guide for the Perplexed, Part II Chapters (Friedlander 1904 tr.) | 354 kB |
| `chaucer_astrolabe_1391_skeat_1894` | Chaucer | 1391 | Treatise on the Astrolabe (Skeat 1894 ed. of ME text) | 92 kB |

`(!)` marks `provenance_risk=True`. The three Boethius excerpts carry the
flag because H. R. James's 1897 translation postdates the 1543 deletion event
by three and a half centuries, and its translation choices (which
seventeenth- and eighteenth-century astronomical vocabulary would James have
avoided? which post-Newtonian metaphors would he have unconsciously adopted?)
are unaudited. The Aristotle, Maimonides, and Chaucer sources are not
flagged; see the provenance section below for why the same or worse concern
applies to them but the flag is reserved for the specific case where a
short pre-selected excerpt in a modern translation is unlikely to reflect
the density of the source's own cosmological argument.

### Oracle corpus (one document, unavailable)

Copernicus's *De revolutionibus orbium coelestium* (Nuremberg, 1543), Book I,
which contains the heliocentric argument itself (later books are technical
planetary tables and less about the deletion). **Not available on English
Wikisource main namespace.**

| doc_id | Wikisource title (attempted) | fetch status |
| --- | --- | --- |
| `copernicus_1543_de_revolutionibus_book1` | `On the Revolutions of the Heavenly Spheres` | 404 (page does not exist) |

The `Author:Nicolaus Copernicus` Wikisource page (fetched 2026-07-27) lists
only:

- `[[:la:De_revolutionibus_orbium_coelestium]]` — a Latin-Wikisource
  interwiki link to the original 1543 Latin text (Latin Wikisource does carry
  the full work, but downstream analyses in this repository work in English
  and swapping to Latin would break the shared-language assumption of the
  three-case comparison with Darwin 1859 English and Lavoisier 1789 in Kerr's
  1790 English translation).
- `[[:de:Nicolaus Coppernicus aus Thorn über die Kreisbewegungen der Weltkörper]]`
  — the 1879 German translation on German Wikisource.
- An external link to Knickerbocker's 1927 *Classics of Modern Science*
  chapter "The New Idea of the Universe" (pp. 21–28), which is a
  seven-page excerpt, not the full Book I.

The English translations of the full work in scholarly use are Charles Glenn
Wallis's 1939 rendering (Great Books of the Western World, Vol. 16;
reprinted by Prometheus Books, 1995) and Edward Rosen's 1978 translation for
the Foundations of Natural History series. Neither is on Wikisource; both
are still in copyright. HathiTrust and Internet Archive do carry public-domain
digitisations of the Latin editions and of nineteenth-century commentary and
partial translations (Prowe's 1883–84 *Nicolaus Coppernicus*, Menzzer's 1879
German translation of Book I).

## Provenance risks

**The Copernicus corpus's provenance situation is structurally worse than the
Darwin, Lavoisier, or DCR corpora's.** Those three worked with primary texts
either in an author's native English (Darwin, Malthus, Herschel, Boyle) or an
English translation completed within one to two generations of the primary
text (Kerr's 1790 translation of Lavoisier 1789; Halsted's 1913 compilation
of Poincaré 1898–1904). The Copernicus corpus works with primary texts in
languages the author did not write in and whose English renderings sit
between 300 and 2,270 years after the source:

| author | source language | Wikisource English translation | vehicle year | years between content and vehicle |
| --- | --- | --- | ---: | ---: |
| Aristotle | Attic Greek | J. L. Stocks, *De Caelo* (Clarendon) | 1922 | ~2,270 |
| Boethius | Late Latin | H. R. James | 1897 | ~1,370 |
| Maimonides | Judeo-Arabic | Michael Friedlander (second edition) | 1904 | ~715 |
| Chaucer | Middle English | W. W. Skeat (Clarendon) preserves ME orthography | 1894 (edition of 1391 ME) | 0 for the language; 503 for the edition |

The three Boethius excerpts carry `provenance_risk=True` in `corpus.py` to
mark them as short pre-selected fragments in a modern translation, where the
translator's word-choice can dominate the semantic signal that downstream
extraction sees. The Aristotle, Maimonides, and Chaucer sources are not
flagged because the length of each source dilutes any single translation
choice's effect and because the Middle English of Chaucer's *Astrolabe* is
itself pre-1543.

**Any downstream P(t) analysis must decide, and preregister, how to handle
translation vintage.** Two reasonable positions:

1. **Treat as authoritative.** Trust that the translators (Stocks, James,
   Friedlander, Skeat) rendered the source's astronomical vocabulary
   faithfully. Then any signal of geocentric commitment or of pressure on it
   is a signal about the source, not about the translator's later idiom.
   Report the vehicle year as a known confound and move on.

2. **Restrict to Chaucer.** The only source whose vehicle is pre-1543 is
   Chaucer's own Middle English, preserved by Skeat's editorial normalisation.
   A P(t) trajectory restricted to Chaucer 1391 would be a claim about
   fourteenth-century English practical astronomy specifically, not about
   pre-1543 cosmology generally, but would be provenance-clean.

Position 1 preserves the corpus's scope; position 2 preserves its provenance
guarantee. Neither is a strict improvement on the other; the choice belongs
to the downstream test's preregistration, not to this corpus package.

## What is not in the corpus, and why

The DCD paper's Case 1 sketch names **Ptolemaic astronomy 1400–1543, plus
Renaissance mathematical astronomers (Regiomontanus, Peurbach, early
Copernicans)**. Wikisource's coverage of that specific window is essentially
nil in main namespace on 2026-07-27:

| author | intended text | status on Wikisource |
| --- | --- | --- |
| Claudius Ptolemy | *Almagest* (c.150) — the technical planetary-astronomy handbook that dominated 1,400 years of astronomical practice and whose cosmological frame Copernicus is displacing | **Absent from main namespace.** `Author:Ptolemy` lists `[[Almagest]]` but that link is a red-link; no English transcription exists in main namespace. The 1911 Britannica biography of Ptolemy and the Catholic Encyclopedia article are the only Ptolemy-adjacent transcribed texts on English Wikisource. |
| Johannes de Sacrobosco | *De Sphaera Mundi* (c.1230) — the standard medieval university-level astronomy textbook, in use for ~400 years, taught alongside Aristotle's *De Caelo* | **Absent.** `Author:Johannes de Sacrobosco` lists only "The Art of Nombryng" (Robert Steele's 1922 translation of *De arte numerandi*), not any of Sacrobosco's astronomical works. |
| Georg von Peurbach | *Theoricae novae planetarum* (1454) — Renaissance restatement of Ptolemaic planetary theory | **Empty author page.** `Author:Georg von Peurbach` exists but lists no works (`{{populate}}` template). |
| Regiomontanus | *Epytoma in Almagestum Ptolemei* (1496) — the accessible Latin epitome of the *Almagest* that trained Copernicus's generation | **Empty author page.** `Author:Regiomontanus` is a redirect to `Author:Johannes Müller von Königsberg`, which lists no works. |
| Nicholas of Cusa | *De docta ignorantia* (1440) — Cusa's speculative cosmology and the earliest medieval Latin argument that the Earth might not be at rest at the centre | **Absent.** `Author:Nicholas of Cusa` lists only "The Vision of God" (a 1928 devotional-selection edition), no cosmological works. |
| Alhazen (Ibn al-Haytham) | *Al-Shukūk ʿalā Baṭlamyūs* (*Doubts on Ptolemy*, c.1025) and *On the Configuration of the World* — the strongest medieval Islamic critique of Ptolemaic cosmology | **Absent.** `Author:Alhazen` lists 36 titles in Arabic transliteration but transcribes none in English. |
| Nasir al-Din al-Tusi | *Al-Tadhkirah fi ʿilm al-hayʾah* — the Maragha-school astronomical treatise containing the "Tusi couple" | **Author page absent.** No `Author:Nasir al-Din al-Tusi` or `Author:Al-Tusi` page exists. |
| Ibn al-Shatir | *Nihayat al-Sul* — fourteenth-century Damascus astronomer whose lunar model is structurally close to Copernicus's | **Author page absent.** |
| Aristarchus of Samos | *On the Sizes and Distances of the Sun and Moon* (Heath 1913 translation) | Author page lists Heath's 1913 translation as an Internet Archive external link (`{{IA small link|aristarchusofsam00heat}}`), but no main-namespace transcription. |
| Copernicus | *Commentariolus* (c.1514) — the short precursor manuscript circulated 30 years before *De revolutionibus* | **Absent.** No English transcription on Wikisource. |
| Georg Joachim Rheticus | *De libris revolutionum Copernici narratio prima* (1540) — the first published announcement of the heliocentric system, three years before *De revolutionibus* | **Absent.** `Author:Georg Joachim Rheticus` lists it but no transcription. |

The consequence is a corpus dominated by **canonical pre-Renaissance sources**
(Aristotle, Boethius, Maimonides, Chaucer) with **zero representation of the
fifteenth- and early-sixteenth-century mathematical astronomers Copernicus
actually read and worked against**. The Renaissance mathematical tradition
(Peurbach, Regiomontanus, Alhazen's *Doubts on Ptolemy* which reached Latin
Europe through Bernardus de Gordonio, Cusa's speculative cosmology,
Rheticus's 1540 *Narratio Prima*) is exactly the layer that would tell a
P(t) test whether geocentric-priority commitment was under pressure or
static in the century before Copernicus. That signal cannot be recovered
from this corpus. Any downstream analysis that requires it must either close
the gap by pulling transcriptions from a source other than Wikisource main
namespace (HathiTrust, Google Books, Internet Archive OCR) or restrict its
claim to what this corpus supports.

## What a downstream test may and may not do with this corpus

**May.**
- Extract commitments and count use / discussion mentions of geocentric
  priority in Aristotle *De Caelo*, Maimonides *Guide* Parts I–II, and
  Chaucer's *Astrolabe*.
- Use the three Boethius meters / prose sections as short cosmology-focused
  supplements (with the translation-vintage caveat flagged).
- Compare the density of use-vs-discussion of geocentrism across the four
  authors as a within-corpus check on the DCR4 prediction-independence /
  equalisation signatures observed on Darwin.
- Run a Chaucer-only sub-corpus P(t) trajectory as a provenance-clean but
  narrower-scope claim about fourteenth-century English practical astronomy.

**May not.**
- Run a full DCD1-pilot-scale test **without first sourcing the oracle
  outside Wikisource.** Without Copernicus 1543 there is no deletion event
  in the corpus to retrodict.
- Claim a signal absent from the corpus is absent from the record. The
  Ptolemy / Sacrobosco / Peurbach / Regiomontanus / Cusa / Alhazen / Tusi /
  Rheticus gaps mean the Renaissance mathematical-astronomy tradition (the
  actual pre-1543 fifteenth-century context) is not represented here.
- Draw a fifteenth-century P(t) point. The corpus jumps from Chaucer 1391 to
  Copernicus 1543 (unavailable) with nothing in the intervening 152 years.
- Treat the three Boethius excerpts as full-work signal. They are three
  pre-selected passages, not the whole *Consolation*; the full text on
  Wikisource is either fragmented into forty-eight individual sub-pages
  (James 1897) or transcluded from DjVu scans that yield no substantive
  text on fetch (King Alfred / Sedgefield 1900).

## Reproducing the fetch

```
uv run --no-sync python -m experiments.copernicus_geocentrism_corpus.fetch
```

The fetch is idempotent: cached files under `data/` are read from disk on
subsequent runs. Sources whose Wikisource page is missing (chiefly the
oracle) do not raise; they cache to an empty file, an `.error` sidecar file,
and their fetch-summary entry carries the error string. Passing `--refresh`
re-fetches every source (and would change the corpus of record, so it should
be paired with a fresh preregistration for any downstream test).

`data/` is gitignored per the repository's root `.gitignore` (the `data/`
rule matches at any depth), so the cached text files are local-only.
`results/fetch_summary.json` is committed and carries the SHA-256 of each
cached file, so drift on a re-fetch is detectable.
