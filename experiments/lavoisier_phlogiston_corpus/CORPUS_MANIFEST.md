# Lavoisier / Phlogiston Corpus Manifest

**Purpose.** Corpus scaffolding for Case 3 of the multi-case retrospective
test named in *The Dynamics of Conceptual Deletion* (`papers/dynamics_of_conceptual_deletion/paper.md`,
PR #451). The deleted commitment is **phlogiston** — the substance-of-combustion
picture. The pre-revolutionary corpus is eighteenth-century chemistry up to
Lavoisier's *Traite Elementaire de Chimie* (1789). The oracle is that Traite.

This file inventories the sources that survived a fetch against Wikisource,
records the gaps where Wikisource did not carry a primary text, and states
what downstream tests may and may not do with the result.

**This package is corpus preparation only.** No extraction, no tagging, no
scoring runs. Nothing here defines what the P(t) test will measure. That is a
separate future task with its own preregistration.

## What is in the corpus

Eleven documents fetched from Wikisource, cached under `data/` (gitignored),
summarised by `results/fetch_summary.json` (committed). Each carries an SHA-256
so a re-fetch can detect drift.

### Pre-revolutionary corpus (nine documents, one author, one year)

All nine are parts of Robert Boyle's *The Sceptical Chymist* (Oxford, second
edition 1680; content originally 1661). Boyle is present as the direct
precursor to substance-based eighteenth-century chemistry: his analysis of
the four Peripatetic elements and of the Paracelsian *tria prima* (salt,
sulphur, mercury) is the intellectual background against which Stahl's
phlogiston picture is later built and eventually displaced by Lavoisier.

| doc_id | Wikisource title | approximate size |
| --- | --- | ---: |
| `boyle_1661_praeface_introductory` | Sceptical Chymist/Praeface Introductory | 21 kB |
| `boyle_1661_physiological_considerations` | Sceptical Chymist/Physiological Considerations | 37 kB |
| `boyle_1661_part_1` | Sceptical Chymist/The First Part | 74 kB |
| `boyle_1661_part_2` | Sceptical Chymist/The Second Part | 67 kB |
| `boyle_1661_part_3` | Sceptical Chymist/The Third Part | 37 kB |
| `boyle_1661_part_4` | Sceptical Chymist/The Fourth Part | 94 kB |
| `boyle_1661_part_5` | Sceptical Chymist/The Fifth Part | 70 kB |
| `boyle_1661_part_6` | Sceptical Chymist/The Sixth Part | 87 kB |
| `boyle_1661_conclusion` | Sceptical Chymist/The Conclusion | 10 kB |

### Oracle corpus (two documents)

Lavoisier's *Traite Elementaire de Chimie* (1789), read via Robert Kerr's
1790 English translation, *Elements of Chemistry, in a New Systematic Order*
(Edinburgh, 1790). Only the sections whose main-namespace Wikisource
transclusion is currently complete are included.

| doc_id | Wikisource title | approximate size |
| --- | --- | ---: |
| `lavoisier_1789_preface_of_the_author` | Elements of Chemistry (Lavoisier, tr. Kerr)/Preface of the Author | 28 kB |
| `lavoisier_1789_part_1` | Elements of Chemistry (Lavoisier, tr. Kerr)/Part I | 160 kB |

Kerr's translation postdates the French content by one year. That is a
weaker provenance risk than the 1913 Halsted compilation that carries
Poincare's 1898 / 1904 essays in the DCR electrodynamics corpus (see
`experiments/date_cut_retrodiction/corpus.py`), so `provenance_risk` is
left off on these two SourceSpecs; the one-year drift is noted per document.

Parts II through V of Kerr's translation are not currently transcluded in
Wikisource's main namespace, only the underlying scan pages. Extending the
oracle corpus to cover them would require assembling `Page:` namespace
transcriptions and stitching them; that is not attempted here.

## What is not in the corpus, and why

The Dynamics of Conceptual Deletion paper's Case 3 sketch names Stahl,
Priestley, Cavendish, and Scheele. Wikisource's coverage of primary
eighteenth-century chemistry in English is thin: those authors have
main-namespace Wikisource author pages, but their primary texts either lack
main-namespace transclusions (only the raw scan is hosted) or are absent
entirely. Every documented gap below was probed against the Wikisource
`action=parse` endpoint on 2026-07-27; every negative below is a real
absence, not a spelling problem.

| author | intended text | status on Wikisource |
| --- | --- | --- |
| Georg Ernst Stahl | any foundational phlogiston work | **Absent.** No author page (`Author:Georg Ernst Stahl` does not exist). None of Stahl's writings are transcribed in English, Latin, or German. |
| Joseph Priestley (1733-1804) | *Observations on different kinds of air* (1772); *Experiments and Observations on Different Kinds of Air* (1774-1777, three volumes); *The Doctrine of Phlogiston Established* (1800) | **Scan hosted, not transcribed.** `Index:Observations on different kinds of air (IA observationson1472641prie).pdf` exists but has no main-namespace transclusion. The author page lists the multi-volume 1774-1777 work only as an external Archive.org link. |
| Henry Cavendish | *Three Papers, Containing Experiments on Factitious Air* (1766); *Experiments on Air* (1784) on hydrogen and water composition | **Scan hosted, not transcribed.** `Index:The Scientific Papers of the Honourable Henry Cavendish v1.djvu` (1921 Cambridge compilation) is uploaded and would carry both papers, but the main-namespace pages `The Scientific Papers of the Honourable Henry Cavendish FRS` and `.../Volume 1` do not exist yet. Individual `Page:` namespace transcriptions do exist and could in principle be stitched. |
| Carl Wilhelm Scheele | *Chemische Abhandlung von der Luft und dem Feuer* (1777) / English translation *Chemical Observations and Experiments on Air and Fire* (1780) | **Absent.** Author page exists but is empty (`{{populate}}` placeholder). No transcription, no scan. |
| Richard Kirwan | *An Essay on Phlogiston, and the Constitution of Acids* (1784, 1789 second edition with the French chemists' rebuttals) | **Absent.** Author page for `Author:Richard Kirwan (1733-1812)` exists but no work is transcribed. |
| Joseph Black | *Experiments upon Magnesia Alba, Quick-Lime, and other Alkaline Substances* (1756); *Lectures on the Elements of Chemistry* (1803) | **Absent.** Author page lists both titles but neither has a main-namespace page. |
| Stephen Hales | *Vegetable Staticks* (1727) — pneumatic chemistry precursor | **Absent.** Author page lists the work with only an external Archive.org link. No main-namespace page. |
| Thomas Fulhame | *Letter to Joseph Black* (1789) | **Cover-page only.** The main-namespace page exists but transcludes only the cover-page address block (Doctor Black, Professor of Chemistry, University of Edinburgh, Scotland). The letter body is not transcribed. Fetched to 114 characters and excluded from `corpus.SOURCES` for that reason. |
| Cavendish, Alexander Scott reprint | "On the Composition of Water by Volume" | **Wrong author.** `Philosophical Transactions of the Royal Society A/Volume 184/On the Composition of Water by Volume` is a fresh 1893 paper by Alexander Scott, not a reprint of Cavendish's 1784. Not a valid eighteenth-century source; excluded. |

The consequence is a lopsided pre-revolutionary corpus: nine parts of a
single 1661 dialogue by Boyle, then a 128-year gap, then the 1789 oracle.
The eighteenth century between Boyle and Lavoisier — the century in which
phlogiston was actually the working picture — is empty. Any downstream
inference that requires balanced coverage of that century must either close
the gap by pulling transcriptions from a source other than Wikisource
main-namespace, or restrict its claim to what this corpus supports.

## What a downstream test may and may not do with this corpus

**May.**
- Extract commitments and count use / discussion mentions in Boyle 1661 and
  Lavoisier 1789.
- Compare Boyle's positive proposals (the corpuscular alternative in Part VI)
  against Lavoisier's chemical revolution vocabulary.
- Study the framing sections of Kerr's translation for how Lavoisier
  himself explicitly names and attacks phlogiston (Preface, Part I chapters
  on combustion and calcination).

**May not.**
- Compute a temporal P(t) trajectory across the eighteenth century. Two
  effective years of data (1661 and 1789) cannot support a trajectory.
- Compare "Priestley on dephlogisticated air" to "Lavoisier on oxygen".
  Priestley's primary texts are not in the corpus.
- Claim that a signal absent from the corpus is absent from the record.

Any test that wants a real eighteenth-century pre-revolutionary corpus will
need to source Priestley, Cavendish, Scheele, and Kirwan from outside
Wikisource main-namespace — either by stitching Wikisource `Page:` namespace
transcriptions where they exist, or by pulling from an external transcription
project (Project Gutenberg, Internet Archive OCR, HathiTrust). That is a
separate task with its own provenance and its own risk profile; it is not
attempted here.

## Reproducing the fetch

```
uv run --no-sync python -m experiments.lavoisier_phlogiston_corpus.fetch
```

The fetch is idempotent: cached files under `data/` are read from disk on
subsequent runs. Passing `--refresh` re-fetches every source (and would
change the corpus of record, so it should be paired with a fresh
preregistration for any downstream test).

`data/` is gitignored per the repository's root `.gitignore` (the `data/`
rule matches at any depth), so the cached text files are local-only.
`results/fetch_summary.json` is committed and carries the SHA-256 of each
cached file, so drift on a re-fetch is detectable.
