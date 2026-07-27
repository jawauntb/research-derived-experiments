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


# --- DCR1b: the repaired instruments --------------------------------------


def test_v2_t1_rejects_every_known_false_positive() -> None:
    """The three hits DCR1's adjudication proved spurious must not fire."""
    from experiments.date_cut_retrodiction.target_v2 import match_facets_v2

    spurious = [
        "The duration of two identical phenomena is the same: the same causes "
        "take the same time to produce the same effects.",
        "Causes almost identical take almost the same time to produce almost "
        "the same effects.",
        "The ether is a medium that transmits at the same time the optical "
        "perturbations and the electrical perturbations.",
    ]
    for statement in spurious:
        hits = match_facets_v2([{"name": "p", "statement": statement, "doc_id": "d"}])
        assert not hits["T1_absolute_simultaneity"], statement


def test_v2_t1_still_matches_genuine_phrasings() -> None:
    from experiments.date_cut_retrodiction.target_v2 import match_facets_v2

    genuine = [
        "There is an absolute time common to all systems.",
        "Simultaneity is absolute.",
        "One single time for every observer everywhere.",
        "The time is the same for a stationary observer as for an observer "
        "carried along in uniform motion.",
    ]
    for statement in genuine:
        hits = match_facets_v2([{"name": "p", "statement": statement, "doc_id": "d"}])
        assert hits["T1_absolute_simultaneity"], statement


def test_v2_t1_declines_the_relativity_principle() -> None:
    """Poincaré states the principle without deleting absolute simultaneity.

    Conflating the two would make the corpus appear to contain the repair it
    conspicuously did not make.
    """
    from experiments.date_cut_retrodiction.target_v2 import match_facets_v2

    hits = match_facets_v2(
        [
            {
                "name": "principle_of_relativity",
                "statement": (
                    "The laws of physical phenomena must be the same for a "
                    "stationary observer as for an observer carried along in a "
                    "uniform motion of translation."
                ),
                "doc_id": "poincare_1904_stlouis",
            }
        ]
    )
    assert not hits["T1_absolute_simultaneity"]


def test_residue_v2_folds_accents() -> None:
    """`poincare` against a corpus writing `Poincaré` is an artefact, not residue."""
    from experiments.date_cut_retrodiction.residue_v2 import audit_residue_v2

    report = audit_residue_v2(
        ["poincare states the principle"],
        ["Poincaré states the principle of relativity."],
        cut_year=1904,
    )
    assert "poincare" not in report.residue_types


def test_residue_v2_strips_possessives_and_stems() -> None:
    from experiments.date_cut_retrodiction.residue_v2 import audit_residue_v2

    report = audit_residue_v2(
        ["abraham's theory communicates motion"],
        ["Abraham gives a theory in which bodies communicate their motion."],
        cut_year=1904,
    )
    assert report.clean, report.residue_types


def test_residue_v2_still_flags_genuinely_absent_vocabulary() -> None:
    """The repair must not blunt the measure into uselessness."""
    from experiments.date_cut_retrodiction.residue_v2 import audit_residue_v2

    report = audit_residue_v2(
        ["spacetime is a minkowski manifold"],
        ["The luminiferous aether is at rest in absolute space."],
        cut_year=1880,
    )
    assert "spacetime" in report.residue_types
    assert "minkowski" in report.residue_types


def test_consensus_requires_agreement_across_passes() -> None:
    from experiments.date_cut_retrodiction.consensus import PASS_DIRS, SUPPORT_THRESHOLD

    assert SUPPORT_THRESHOLD == len(PASS_DIRS)
    assert all("blind" in d.name or "pass3" in d.name for d in PASS_DIRS)


def test_consensus_excludes_the_unblinded_pass() -> None:
    """Pass 1's prompt did not forbid reading other repository files."""
    from experiments.date_cut_retrodiction.consensus import PASS_DIRS

    assert not any(d.name == "extractions" for d in PASS_DIRS)


def test_v1_matcher_is_not_edited_by_the_repair() -> None:
    """DCR1's published numbers must stay reproducible."""
    from experiments.date_cut_retrodiction.target import TARGET_FACETS as V1

    t1 = next(f for f in V1 if f.key == "T1_absolute_simultaneity")
    # The defect is preserved on purpose: v1 accepted a bare "same ... time".
    assert "same" in t1.pattern


# --- DCR1c: the polarity and referent vetoes -------------------------------


def test_v3_rejects_every_dcr1b_false_positive() -> None:
    """The four hits DCR1b's H5 failed on must not fire under v3."""
    from experiments.date_cut_retrodiction.target_v3 import match_facets_v3

    spurious = [
        ("stationary_ether_hypothesis_erroneous",
         "The hypothesis of a stationary ether is shown to be incorrect, and "
         "the hypothesis is erroneous."),
        ("stokes_ether_at_rest_at_earth_surface",
         "Stokes gives a theory of aberration which assumes the ether at the "
         "earth's surface to be at rest with regard to the earth's surface."),
        ("lorentz_theory_fails_if_ether_at_rest",
         "If the ether is at rest with regard to the earth's surface, then "
         "according to Lorentz there could not be a velocity potential, and "
         "Lorentz's own theory also fails."),
        ("electron_positions_correspond",
         "The corresponding positions of the electrons of the two systems, "
         "established up to the first order of v/c, are true up to the second "
         "order when the moving system is contracted in comparison with the "
         "fixed system."),
    ]
    for name, statement in spurious:
        hits = match_facets_v3(
            [{"name": name, "statement": statement, "doc_id": "d"}]
        )
        assert not hits["T2_privileged_frame"], name


def test_v3_keeps_every_dcr1b_genuine_hit() -> None:
    from experiments.date_cut_retrodiction.target_v3 import match_facets_v3

    genuine = [
        ("stationary_ether_hypothesis",
         "The ether is at rest while the earth moves through it."),
        ("aberration_presupposes_earth_moves_through_ether",
         "The generally accepted explanation of the phenomenon of aberration "
         "presupposes that the earth moves through the ether, the ether "
         "remaining at rest."),
        ("fresnel_ether_at_rest_outside_media",
         "The ether is supposed to be at rest except in the interior of "
         "transparent media."),
        ("velocity_relative_to_ether_determines_physical_effects",
         "Electric forces, molecular forces, and length are affected by motion "
         "relative to the ether."),
        ("dynamics_needs_absolute_positions",
         "It has not been found possible to construct a system of dynamics "
         "which has respect only to the relative positions of moving bodies."),
        ("stellar_aberration_favours_stationary_aether",
         "Stellar aberration favours the theory of a stationary aether."),
    ]
    for name, statement in genuine:
        hits = match_facets_v3(
            [{"name": name, "statement": statement, "doc_id": "d"}]
        )
        assert hits["T2_privileged_frame"], name


def test_polarity_veto_never_fires_on_bare_negation() -> None:
    """Larmor's absolute-space commitment is stated as "it has NOT been…".

    A naive negation veto would delete the strongest evidence the corpus offers.
    """
    from experiments.date_cut_retrodiction.target_v3 import match_facets_v3

    hits = match_facets_v3(
        [
            {
                "name": "dynamics_needs_absolute_positions",
                "statement": (
                    "It has not been found possible to construct a system of "
                    "dynamics which has respect only to the relative positions "
                    "of moving bodies."
                ),
                "doc_id": "larmor_1897_medium3",
            }
        ]
    )
    assert hits["T2_privileged_frame"]


def test_v3_leaves_t1_and_t3_patterns_untouched() -> None:
    """Vetoes apply to T2 only; the other facets had no false positives."""
    from experiments.date_cut_retrodiction.target_v2 import TARGET_FACETS_V2
    from experiments.date_cut_retrodiction.target_v3 import TARGET_FACETS_V3

    v2 = {f.key: f.pattern for f in TARGET_FACETS_V2}
    v3 = {f.key: f.pattern for f in TARGET_FACETS_V3}
    assert v2["T1_absolute_simultaneity"] == v3["T1_absolute_simultaneity"]
    assert v2["T3_local_time_artifice"] == v3["T3_local_time_artifice"]
    assert v2["T2_privileged_frame"] != v3["T2_privileged_frame"]


def test_dcr1c_uses_three_sandboxed_passes() -> None:
    from experiments.date_cut_retrodiction.run_dcr1c import (
        PASS_DIRS_V3,
        SUPPORT_THRESHOLD_V3,
    )

    assert len(PASS_DIRS_V3) == 3
    assert SUPPORT_THRESHOLD_V3 == 2
    assert not any(d.name == "extractions" for d in PASS_DIRS_V3)


def test_dcr1c_imports_thresholds_rather_than_restating_them() -> None:
    """The one guarantee the late preregistration still buys."""
    from experiments.date_cut_retrodiction import run_dcr1, run_dcr1c

    source = (
        __import__("pathlib").Path(run_dcr1c.__file__).read_text(encoding="utf-8")
    )
    assert "QUOTE_FIDELITY_GATE" in source
    assert "RESIDUE_RATE_GATE" in source
    assert run_dcr1.QUOTE_FIDELITY_GATE == 0.90
    assert run_dcr1.RESIDUE_RATE_GATE == 0.05


# --- DCR1d: positive control on Newton's Scholium ------------------------
#
# The whole point of DCR1d is that the positive control is *outside* the DCR1c
# corpus of record. If Newton ends up in ``SOURCES`` or the 1687 cut ends up in
# ``CUTS``, DCR1c's numbers change and the guarantee that its published paper is
# still reproducible dies. These tests are the guardrail.


def test_dcr1d_positive_control_is_not_in_main_sources() -> None:
    from experiments.date_cut_retrodiction.corpus import SOURCES
    from experiments.date_cut_retrodiction.dcr1d import NEWTON_SOURCE

    ids = {s.doc_id for s in SOURCES}
    assert NEWTON_SOURCE.doc_id not in ids, (
        "Newton belongs to DCR1d only. Adding it to SOURCES would drop it into "
        "the 1880/1897/1904 cuts and DCR1c's numbers would no longer reproduce."
    )


def test_dcr1d_positive_control_cut_is_not_in_main_cuts() -> None:
    from experiments.date_cut_retrodiction.cuts import CUTS
    from experiments.date_cut_retrodiction.dcr1d import POSITIVE_CONTROL_CUT

    years = {c.year for c in CUTS}
    assert POSITIVE_CONTROL_CUT.year not in years
    assert POSITIVE_CONTROL_CUT.is_placebo is False
    assert POSITIVE_CONTROL_CUT.label == "positive control"


def test_dcr1d_uses_three_sandboxed_passes_named_apart_from_dcr1c() -> None:
    from experiments.date_cut_retrodiction.dcr1d import (
        NEWTON_CONSENSUS_DIR,
        NEWTON_PASS_DIRS,
    )
    from experiments.date_cut_retrodiction.run_dcr1c import PASS_DIRS_V3

    assert len(NEWTON_PASS_DIRS) == 3
    assert NEWTON_CONSENSUS_DIR not in PASS_DIRS_V3
    assert set(NEWTON_PASS_DIRS).isdisjoint(set(PASS_DIRS_V3))


def test_dcr1d_imports_thresholds_rather_than_restating_them() -> None:
    """DCR1d carries every threshold as an imported constant, same discipline
    as DCR1c: what P3 measures is whether the matcher fires, not whether some
    knob can be turned to make it fire."""
    from experiments.date_cut_retrodiction import run_dcr1, run_dcr1d

    source = (
        __import__("pathlib").Path(run_dcr1d.__file__).read_text(encoding="utf-8")
    )
    assert "QUOTE_FIDELITY_GATE" in source
    assert "RESIDUE_RATE_GATE" in source
    assert run_dcr1.QUOTE_FIDELITY_GATE == 0.90
    assert run_dcr1.RESIDUE_RATE_GATE == 0.05


def test_t1_v2_pattern_fires_on_newtons_own_sentence() -> None:
    """The positive-control assumption stated as a test: if this ever fails,
    the whole DCR1d design is void and the T1 matcher was never going to work
    on Newton's scholium either."""
    from experiments.date_cut_retrodiction.target_v2 import match_facets_v2

    scholium_proposition = [
        {
            "doc_id": "newton_1687_scholium",
            "name": "absolute_time_flows_equably",
            "statement": (
                "Absolute, true, and mathematical time, of itself, and from "
                "its own nature, flows equably without regard to anything "
                "external, and by another name is called duration."
            ),
        }
    ]
    hits = match_facets_v2(scholium_proposition)
    assert hits["T1_absolute_simultaneity"], (
        "target_v2's T1 pattern is supposed to fire on 'absolute time'. "
        "If this ever fails, DCR1d cannot answer its question."
    )


def test_t1_v3_pattern_fires_on_newtons_own_sentence() -> None:
    from experiments.date_cut_retrodiction.target_v3 import match_facets_v3

    scholium_proposition = [
        {
            "doc_id": "newton_1687_scholium",
            "name": "absolute_time_flows_equably",
            "statement": (
                "Absolute, true, and mathematical time, of itself, and from "
                "its own nature, flows equably without regard to anything "
                "external, and by another name is called duration."
            ),
        }
    ]
    hits = match_facets_v3(scholium_proposition)
    assert hits["T1_absolute_simultaneity"]
