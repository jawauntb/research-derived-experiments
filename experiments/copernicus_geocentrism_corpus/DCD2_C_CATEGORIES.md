# DCD2 C-categories (Copernicus / geocentrism), frozen

Committed before any subagent tags any document. SHA-256 pinned in
`run_dcd2_copernicus.py`. These substitute for T1/T2/T3 (electrodynamics) and
D1/D2/D3 (Darwin) in the DCR-arc extraction and tagging prompts.

The deleted commitment is **geocentrism**. Following the framework's revised
reading (`papers/dynamics_of_conceptual_deletion/paper.md` §10; DCR4 + DCD1), the
deleted commitment is paired with a structural partner of matched form — each a
denied *absolute about the Earth*. The pairing is position and rest.

- **C1 — geocentric position.** The Earth is at the centre of the cosmos; its
  place is geometrically/dynamically privileged; heavy bodies move toward it as
  the middle of the universe. Discussing C1 = asserting or denying that the Earth
  is at the centre; arguing about the Earth's place among the spheres; treating
  the centre of the cosmos as a privileged location. (Analogue of T1 / D1 — the
  deleted commitment.)

- **C2 — geostatic rest.** The Earth is immobile: no daily rotation, no annual
  revolution; apparent celestial motion belongs to the heavens, not the Earth.
  Discussing C2 = asserting or denying that the Earth moves; arguing whether
  apparent motion belongs to the heavens or to a moving Earth. (Analogue of T2 /
  D2 — the paired structural partner.)

- **C3 — celestial/terrestrial essence distinction.** The heavens are a distinct
  incorruptible nature (a fifth element / aether) whose natural motion is uniform
  and circular, set against the corruptible sublunary realm and its rectilinear
  elemental motions. Discussing C3 = asserting or denying the heaven–earth
  dichotomy of substance or of natural motion. (Analogue of T3 / D3.)

- **OTHER** — everything else: mathematical/geometrical technique (trigonometry,
  tables, epicycle/eccentric constructions), specific observations, the calendar,
  instruments, incidental theology, and any commitment fitting none of C1/C2/C3.

## Fit to this corpus

The `copernicus_geocentrism_corpus` precursor set is cosmological-philosophical
rather than technical-astronomical (Aristotle's *On the Heavens*, Maimonides's
*Guide*, Boethius's *Consolation*, Chaucer's *Astrolabe*), because the standard
technical geocentric texts — Ptolemy's *Almagest*, Sacrobosco's *De sphaera* —
have no public-domain English transcription on Wikisource (see
`CORPUS_MANIFEST.md`). C1/C2/C3 are well-posed on this corpus: Aristotle *De
caelo* argues C2 and C3 directly; Maimonides discusses the central motionless
Earth and the celestial/terrestrial distinction; Chaucer's *Astrolabe*
*presupposes* the geocentric sphere as background (mostly C1/C2 *use*, not
discussion). The **oracle** — *De revolutionibus* Book I — is not yet available
(the corpus fetch confirmed it: 0 chars), so the C0 gate in the scorer STOPs the
run until a public-domain English Book I is sourced.

## Tagging conventions (identical discipline to DCR3c/DCR3d and DCD1)

- **DISCUSS** a category when the proposition takes it as its *subject*. A
  proposition that merely *uses* the commitment as background is not a discussion.
- **USE** a category when a proposition that is an empirical *prediction* requires
  the category as a background premise.
- C1 and C2 are distinct: a proposition about *where* the Earth is (centre) is C1;
  a proposition about *whether* the Earth moves is C2. A proposition arguing both
  at once may carry both tags — such joint propositions are exactly what the S1
  equalisation gate looks for in the oracle.
