"""Regression tests for DCR1 — the extractor-leak precondition check.

The load-bearing tests are the ones that pin the *anti-leak* properties, not
the ones that check arithmetic. If the corpus reacquires Wikisource chrome, or
the residue audit degenerates into a blocklist, or the cuts stop being nested,
the placebo comparison silently stops meaning anything — and a silently
meaningless control is worse than no control.
"""

from __future__ import annotations

from experiments.date_cut_retrodiction.corpus import SOURCES, sources_at_or_before
from experiments.date_cut_retrodiction.cuts import CUTS, PLACEBO_CUTS, TARGET_CUT
from experiments.date_cut_retrodiction.fetch import _drop_chrome, _extract_container
from experiments.date_cut_retrodiction.residue import (
    audit_residue,
    corpus_vocabulary,
    tokens,
)
from experiments.date_cut_retrodiction.target import (
    FACET_QUORUM,
    TARGET_FACETS,
    match_facets,
    surfaces_target,
)


# --- corpus and cuts -------------------------------------------------------


def test_every_source_predates_the_cut() -> None:
    """No document may postdate Einstein's June 1905 submission."""
    assert all(source.year <= 1904 for source in SOURCES)


def test_cuts_are_nested() -> None:
    """1880 ⊆ 1897 ⊆ 1904, or the placebo comparison is not a comparison."""
    ids = [
        {s.doc_id for s in sources_at_or_before(cut.year)}
        for cut in sorted(CUTS, key=lambda c: c.year)
    ]
    assert ids[0] < ids[1] < ids[2]


def test_deep_placebo_has_no_ether_drift_null_result() -> None:
    """The 1880 cut must not contain Michelson 1881 or Michelson-Morley 1887.

    If it did, the deep placebo would no longer be a world in which the problem
    the target deletion answers has not yet been posed.
    """
    doc_ids = {s.doc_id for s in sources_at_or_before(1880)}
    assert "michelson_1881" not in doc_ids
    assert "michelson_morley_1887" not in doc_ids


def test_near_placebo_excludes_the_1904_material() -> None:
    doc_ids = {s.doc_id for s in sources_at_or_before(1897)}
    assert "lorentz_1904" not in doc_ids
    assert "poincare_1904_stlouis" not in doc_ids


def test_target_cut_is_not_a_placebo() -> None:
    assert not TARGET_CUT.is_placebo
    assert all(cut.is_placebo for cut in PLACEBO_CUTS)


def test_provenance_risk_documents_are_flagged() -> None:
    """Both Poincare texts reach us through the 1913 compilation."""
    risky = {s.doc_id for s in SOURCES if s.provenance_risk}
    assert risky == {"poincare_1898_time", "poincare_1904_stlouis"}


def test_dropping_risky_documents_changes_the_target_cut() -> None:
    with_risk = sources_at_or_before(1904, allow_provenance_risk=True)
    without = sources_at_or_before(1904, allow_provenance_risk=False)
    assert len(without) == len(with_risk) - 2


# --- chrome removal --------------------------------------------------------


def test_chrome_removal_drops_the_relativity_portal_link() -> None:
    """The exact contamination found in eleven of fifteen documents."""
    markup = (
        '<div class="mw-parser-output">'
        '<ul><li class="sisitem"><a href="/wiki/Portal:Relativity">Relativity</a></li></ul>'
        "<p>The luminiferous aether is at rest.</p></div>"
    )
    cleaned = _drop_chrome(markup)
    assert "Relativity" not in cleaned
    assert "luminiferous aether" in cleaned


def test_body_container_extraction_is_depth_aware() -> None:
    markup = (
        '<div class="prp-pages-output"><div class="inner">body text</div></div>'
        "<div>trailing chrome</div>"
    )
    body = _extract_container(markup, "prp-pages-output")
    assert body is not None
    assert "body text" in body
    assert "trailing chrome" not in body


# --- residue ---------------------------------------------------------------


def test_residue_is_relational_not_a_blocklist() -> None:
    """A term the corpus contains is never residue, however modern it sounds.

    Poincare's September 1904 lecture states "the principle of relativity"
    verbatim. A blocklist would delete the parent task from the corpus that
    supplies it.
    """
    corpus = ["The principle of relativity holds for uniform motion of translation."]
    report = audit_residue(["relativity of uniform motion"], corpus, cut_year=1904)
    assert "relativity" not in report.residue_types
    assert report.clean


def test_residue_flags_vocabulary_the_corpus_lacks() -> None:
    corpus = ["The luminiferous aether is at rest in absolute space."]
    report = audit_residue(["spacetime is a minkowski manifold"], corpus, cut_year=1880)
    assert "spacetime" in report.residue_types
    assert "minkowski" in report.residue_types
    assert not report.clean


def test_period_english_is_not_treated_as_anachronism() -> None:
    """Larmor 1897's "any special theory of the constitution of matter"."""
    corpus = ["independent of any special theory of the constitution of matter"]
    report = audit_residue(["special theory of matter"], corpus, cut_year=1897)
    assert report.clean


def test_corpus_vocabulary_is_case_and_ligature_normalised() -> None:
    vocabulary = corpus_vocabulary(["The Æther Is At Rest"])
    assert "aether" in vocabulary
    assert "rest" in vocabulary


def test_tokens_ignore_digits_and_punctuation() -> None:
    assert tokens("velocity 3.5 km/s -- the aether!") == [
        "velocity",
        "km",
        "s",
        "the",
        "aether",
    ]


# --- target matcher --------------------------------------------------------


def test_matcher_reads_name_and_statement_but_never_quote() -> None:
    """A document must not score by discussing a topic.

    Only the extractor having isolated a commitment counts, so the quote --
    which is source text -- is out of scope for matching.
    """
    proposition = {
        "name": "apparatus_description",
        "statement": "The interferometer arms are of equal length.",
        "quote": "there exists an absolute time common to all observers",
        "doc_id": "d",
    }
    hits = match_facets([proposition])
    assert all(not value for value in hits.values())


def test_each_facet_matches_its_own_paradigm_case() -> None:
    cases = {
        "T1_absolute_simultaneity": "There is an absolute time common to all systems.",
        "T2_privileged_frame": "The aether is at rest and defines absolute rest.",
        "T3_local_time_artifice": "The local time is a mathematical auxiliary variable.",
    }
    for facet_key, statement in cases.items():
        hits = match_facets([{"name": "p", "statement": statement, "doc_id": "d"}])
        assert hits[facet_key], f"{facet_key} failed on its paradigm case"


def test_quorum_requires_two_distinct_facets() -> None:
    one = [{"name": "p", "statement": "The aether is at rest.", "doc_id": "d"}]
    hit, present = surfaces_target(one)
    assert present == 1
    assert not hit

    two = one + [
        {"name": "q", "statement": "The local time is a mathematical variable.", "doc_id": "d"}
    ]
    hit, present = surfaces_target(two)
    assert present == FACET_QUORUM
    assert hit


def test_three_facets_are_defined() -> None:
    assert len(TARGET_FACETS) == 3
    assert len({f.key for f in TARGET_FACETS}) == 3
