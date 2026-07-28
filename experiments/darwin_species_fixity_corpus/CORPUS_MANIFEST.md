# Darwin / Species-Fixity Corpus Manifest

**Purpose.** Corpus scaffolding for Case 2 of the multi-case retrospective test
named in *The Dynamics of Conceptual Deletion* (`papers/dynamics_of_conceptual_deletion/paper.md`,
PR #451). The deleted commitment is **species fixity** — the assumption that
species are permanent categories, created separately, immutable across
generations. The pre-revolutionary corpus is eighteenth- and early-nineteenth-
century natural history, geology, and philosophy of science, up to (but not
including) Darwin's *On the Origin of Species* (John Murray, London, 1859).
The oracle is that 1859 first edition.

This file inventories the sources that survived a fetch against Wikisource,
records the gaps where Wikisource did not carry a primary text, and states
what downstream tests may and may not do with the result.

**This package is corpus preparation only.** No extraction, no tagging, no
scoring runs. Nothing here defines what the P(t) test will measure. That is a
separate future task with its own preregistration.

## What is in the corpus

Thirty-two documents fetched from Wikisource on 2026-07-27, cached under
`data/` (gitignored), summarised by `results/fetch_summary.json` (committed).
Each carries an SHA-256 so a re-fetch can detect drift.

### Pre-revolutionary corpus (seventeen documents, four strata)

Chronological strata, chosen to cover the range specified by the DCD paper
("eighteenth- and early-nineteenth-century natural history, plus geological
and paleontological literature 1800–1859"). The four strata are: the eighteenth-
century transmutation-adjacent tradition (Erasmus Darwin); the demographic
argument Darwin credits as his direct mechanism inspiration (Malthus); the
philosophy-of-science treatise Darwin credits as his methodological inspiration
(Herschel); and the immediate 1839–1858 precursors (Darwin's *Beagle* journal
and Wallace).

| doc_id | author | year | Wikisource title (short) | approx. size |
| --- | --- | ---: | --- | ---: |
| `erasmus_darwin_1794_zoonomia_preface` | Erasmus Darwin | 1794 | Zoonomia/I.Preface | 4 kB |
| `erasmus_darwin_1794_zoonomia_generation_39` | Erasmus Darwin | 1794 | Zoonomia/I.XXXIX ("Of Generation") | 117 kB |
| `erasmus_darwin_1794_zoonomia_generation_40` | Erasmus Darwin | 1794 | Zoonomia/I.XL ("Of Generation") | 62 kB |
| `malthus_1798_essay_ch1` | T. R. Malthus | 1798 | Essay on Population/Chapter I | 13 kB |
| `malthus_1798_essay_ch2` | T. R. Malthus | 1798 | Essay on Population/Chapter II | 16 kB |
| `malthus_1798_essay_ch3` | T. R. Malthus | 1798 | Essay on Population/Chapter III | 11 kB |
| `malthus_1798_essay_ch5` | T. R. Malthus | 1798 | Essay on Population/Chapter V | 24 kB |
| `malthus_1798_essay_ch7` | T. R. Malthus | 1798 | Essay on Population/Chapter VII | 21 kB |
| `herschel_1830_prelim_p1c1` | John Herschel | 1830 | Preliminary Discourse/Part 1, chap. 1 | 25 kB |
| `herschel_1830_prelim_p1c2` | John Herschel | 1830 | Preliminary Discourse/Part 1, chap. 2 | 27 kB |
| `herschel_1830_prelim_p1c3` | John Herschel | 1830 | Preliminary Discourse/Part 1, chap. 3 | 59 kB |
| `herschel_1830_prelim_p2c6` | John Herschel | 1830 | Preliminary Discourse/Part 2, chap. 6 | 72 kB |
| `herschel_1830_prelim_p3c3` | John Herschel | 1830 | Preliminary Discourse/Part 3, chap. 3 | 40 kB |
| `darwin_1845_beagle_ch8` (!) | Charles Darwin | 1845 | Journal of Researches/Chapter 8 (Patagonia) | 81 kB |
| `darwin_1845_beagle_ch17` (!) | Charles Darwin | 1845 | Journal of Researches/Chapter 17 (Galapagos) | 66 kB |
| `wallace_1855_sarawak` | A. R. Wallace | 1855 | Sarawak-law paper (*Annals and Mag. Nat. Hist.*) | 35 kB |
| `wallace_darwin_1858_linnean` (!) | Wallace & Darwin | 1858 | Joint Linnean Society communication | 46 kB |

`(!)` marks `provenance_risk=True`. See the sections below for what those
flags mean here and how downstream analyses must treat them.

### Oracle corpus (fifteen documents)

Darwin's *On the Origin of Species*, John Murray, London, 1859, first edition.
Wikisource root `On the Origin of Species (1859)`. The transcription is
complete in main namespace: Introduction plus fourteen chapters. No provenance
risk (the vehicle is the content: 1859 first printing, contemporaneous with
the deletion event).

| doc_id | Wikisource title (short) | approx. size |
| --- | --- | ---: |
| `darwin_1859_origin_introduction` | Origin (1859)/Introduction | 10 kB |
| `darwin_1859_origin_ch1` | Origin (1859)/Chapter I (Variation under domestication) | 70 kB |
| `darwin_1859_origin_ch2` | Origin (1859)/Chapter II (Variation under nature) | 29 kB |
| `darwin_1859_origin_ch3` | Origin (1859)/Chapter III (Struggle for existence) | 36 kB |
| `darwin_1859_origin_ch4` | Origin (1859)/Chapter IV (Natural selection) | 71 kB |
| `darwin_1859_origin_ch5` | Origin (1859)/Chapter V (Laws of variation) | 73 kB |
| `darwin_1859_origin_ch6` | Origin (1859)/Chapter VI (Difficulties on theory) | 66 kB |
| `darwin_1859_origin_ch7` | Origin (1859)/Chapter VII (Instinct) | 69 kB |
| `darwin_1859_origin_ch8` | Origin (1859)/Chapter VIII (Hybridism) | 61 kB |
| `darwin_1859_origin_ch9` | Origin (1859)/Chapter IX (Imperfection of the geological record) | 58 kB |
| `darwin_1859_origin_ch10` | Origin (1859)/Chapter X (Geological succession of organic beings) | 62 kB |
| `darwin_1859_origin_ch11` | Origin (1859)/Chapter XI (Geographical distribution I) | 68 kB |
| `darwin_1859_origin_ch12` | Origin (1859)/Chapter XII (Geographical distribution II) | 51 kB |
| `darwin_1859_origin_ch13` | Origin (1859)/Chapter XIII (Mutual affinities, embryology, rudimentary organs) | 87 kB |
| `darwin_1859_origin_ch14` | Origin (1859)/Chapter XIV (Recapitulation) | 58 kB |

## Provenance risks

Three pre-1859 documents carry `provenance_risk=True`. In every case the
deeper structural reason is the same: the source was authored by (or in the
1858 case co-authored with) someone who had privately abandoned species
fixity by the time of writing. A P(t) test that treated these as "innocent"
pre-revolutionary sources would be leaking the revolution's own precursors
back into the pre-revolutionary corpus.

- **`darwin_1845_beagle_ch8` and `darwin_1845_beagle_ch17`**: Wikisource's
  transcription is drawn from the 1860 John Murray reprint of Darwin's 1845
  second edition of *Journal of Researches* (Index page:
  `Index:Darwin Journal of Researches.djvu`, `Year=1860`, `Publisher=John Murray`).
  Content year is 1845; vehicle year is 1860 (one year after *Origin*). The
  1845 revision of *Journal of Researches* introduced the closest-to-
  transmutation phrasings that appear in the pre-*Origin* Darwin corpus; by
  1845 Darwin had already privately drafted the 1844 essay on natural
  selection. The 1860 reprint sits post-*Origin*; while a straight reprint of
  the 1845 text, no page-by-page collation against a pre-1859 printing has
  been done here. Both risks are captured by a single `provenance_risk=True`
  flag; downstream analyses should run once with and once without these two
  chapters, as the DCR corpus does with the two Poincare / 1913 Halsted
  entries.
- **`wallace_darwin_1858_linnean`**: The 1858 joint communication is the
  first public statement of natural selection, delivered to the Linnean
  Society on 1 July 1858 and published as *"On the tendency of species to
  form varieties; and on the Perpetuation of Varieties and Species by Natural
  Means of Selection"* (Wallace's Ternate essay + Darwin's 1844 essay extract
  + Darwin's 1857 letter to Asa Gray). Content year 1858; vehicle year 1858.
  It sits one year before *Origin* and articulates the deletion itself; the
  authors are the deleters. Including it in a pre-revolutionary corpus is
  formally analogous to including a 1904 Einstein manuscript in the pre-1905
  physics corpus. Marked `provenance_risk=True` so downstream analyses can
  run with and without it.

The two Wallace 1855 paper (Sarawak law) is NOT flagged. Wallace in 1855 had
not yet named natural selection and was still framing his observations as a
law "regulating the introduction of new species" without a mechanism; the
paper is a strong empirical challenge to independent-creation species fixity
but does not itself state the alternative. It is the closest analogue in this
corpus to Larmor 1900 or Lorentz 1904 in the DCR corpus — approaching, but
not effecting, the deletion.

## What is not in the corpus, and why

The DCD paper's Case 2 sketch names Linnaeus-onward natural history and
geological / paleontological literature 1800-1859. Wikisource's coverage of
pre-1859 biology is much richer than its coverage of eighteenth-century
chemistry (Case 3), but four important primary sources are absent from main
namespace on 2026-07-27:

| author | intended text | status on Wikisource |
| --- | --- | --- |
| Charles Lyell | *Principles of Geology* (1830-33, three volumes) — the uniformitarian classic that undergirds Darwin's argument and whose author remained a species-fixity holdout well into the 1860s | **Absent from main namespace.** `Author:Charles Lyell` lists only *Geological Evidences of the Antiquity of Man* (1863, postdates *Origin*), *Student's Elements of Geology* (later), and a `Glossary of Geological and other Scientific terms used in Principles of Geology` (glossary only, not the text). No main-namespace transclusion of *Principles* itself. |
| Robert Chambers | *Vestiges of the Natural History of Creation* (Churchill, 1844, anonymous) — the pre-Darwinian transmutation bestseller that made naturalists comfortable arguing about species change in public before *Origin* | **Empty author page.** `Author:Robert Chambers` exists but lists no works. Neither *Vestiges* nor its 1845 sequel *Explanations* is transcribed. |
| Georges Cuvier | *Discours sur les révolutions de la surface du globe* (1812) / *Essay on the Theory of the Earth* (English tr. Robert Kerr, 1813) — catastrophist doctrine that made species-extinction-plus-recreation the pre-Darwinian orthodoxy | **No primary text.** Author page lists only the 1911 Britannica biography and a *Biographies of Scientific Men* entry. Neither the *Discours* nor its English translations is in main namespace. |
| Jean-Baptiste Lamarck | *Philosophie zoologique* (Paris 1809; English tr. Hugh Elliot, 1914) | **Empty author page.** `Author:Jean-Baptiste Lamarck` exists but lists no works. |
| William Whewell | *Philosophy of the Inductive Sciences* (1840) / *History of the Inductive Sciences* (1837) | **No primary text.** Author page lists only biographical / encyclopedic entries. |
| Richard Owen | *On the Nature of Limbs* (1849) or *On the Archetype and Homologies of the Vertebrate Skeleton* (1848) | **Empty author page.** `Author:Richard Owen` exists but lists no works. |
| Georges-Louis Leclerc de Buffon | *Histoire naturelle* (36 vols., 1749-1788) or its English translations | **Absent.** No author page exists. |

The consequence is a pre-revolutionary corpus that has good depth on the
mechanism-adjacent line (Erasmus Darwin's transmutation-adjacent generation
theory, Malthus's population mechanism, Herschel's methodology, Wallace's
biogeographic challenge, and Darwin's own pre-*Origin* travel journal) but no
representation of the catastrophist / creationist mainstream (Cuvier, Lyell's
uniformitarian species fixity, Owen's archetypes), no representation of the
independent-transmutationist tradition (Lamarck, *Vestiges*), and no
representation of the eighteenth-century Linnaean systematics that made
species-as-fixed-kind the ambient default. Any downstream inference that
requires balanced coverage of the pre-*Origin* biological landscape must
either close these gaps by pulling transcriptions from a source other than
Wikisource main namespace (Wikisource `Page:` namespace for texts that have
scans but no transclusion, Project Gutenberg, Internet Archive OCR,
HathiTrust) or restrict its claim to what this corpus supports.

## What a downstream test may and may not do with this corpus

**May.**
- Extract commitments and count use / discussion mentions in Erasmus Darwin
  1794, Malthus 1798, Herschel 1830, Wallace 1855, and Darwin 1859.
- Compare Wallace's 1855 empirical challenge to species fixity against
  Darwin's 1859 articulation of the transmutation-plus-selection alternative.
- Study the framing sections of *Origin* (Introduction, Chapter VI on
  "Difficulties on theory", Chapter XIV recapitulation) for how Darwin himself
  explicitly names and attacks species fixity.
- Run a P(t) trajectory with cuts at 1798, 1830, 1855, 1858 and compare to a
  no-cut baseline, treating `wallace_darwin_1858_linnean` and both
  `darwin_1845_beagle_*` chapters as leak-risk material to be included and
  excluded separately.

**May not.**
- Claim a signal absent from the corpus is absent from the record. The
  Lyell / Chambers / Cuvier / Lamarck / Owen / Whewell / Buffon gaps mean
  that the catastrophist and independent-transmutationist strands of the
  pre-*Origin* debate are not represented here.
- Compute a P(t) trajectory across the eighteenth century as a whole. The
  Erasmus Darwin 1794 stratum is the only eighteenth-century biology
  represented; Malthus 1798 is demography, not natural history. Any claim
  about the eighteenth-century pre-*Origin* corpus is a claim about
  Erasmus Darwin plus Malthus, not a claim about eighteenth-century biology.
- Treat Darwin's 1845 *Journal of Researches* chapters or the 1858 joint
  communication as unproblematic pre-1859 data. See the provenance section.

## Reproducing the fetch

```
uv run --no-sync python -m experiments.darwin_species_fixity_corpus.fetch
```

The fetch is idempotent: cached files under `data/` are read from disk on
subsequent runs. Passing `--refresh` re-fetches every source (and would
change the corpus of record, so it should be paired with a fresh
preregistration for any downstream test).

`data/` is gitignored per the repository's root `.gitignore` (the `data/`
rule matches at any depth), so the cached text files are local-only.
`results/fetch_summary.json` is committed and carries the SHA-256 of each
cached file, so drift on a re-fetch is detectable.
