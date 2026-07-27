"""The T1 matcher, widened for presuppositional phrasings.

DCR1e ran a presupposition-inferring extractor and produced five T1-content
propositions target_v3 rejected:

* Larmor 1900: "There is a common time t in which the position of an
  electron in the moving medium can be compared to its position in the
  medium at rest at time t minus vx over c squared."
* Lodge 1897: "The time of journey of light along any given path through
  any kind of material is perfectly definite and independent of the motion
  of the material."
* Maxwell 1865 pt1: "There is an instant at which the amount of energy in
  the whole medium is a definite quantity equally divided."
* Poincaré 1898: "The astronomers suppose that an eclipse of the moon is
  perceived simultaneously from all points of the earth."
* Poincaré 1898: "In general the duration of the transmission of a signal
  is neglected and the two events are regarded as simultaneous."

target_v3's failure modes were spacing (60/40-char windows too tight for
prose), vocabulary (SAMENESS list did not include "definite"), and
construction (no alternative for "common time X in which…", "regarded as
simultaneous", "instant across the whole X").

v4 adds four new alternatives targeting these constructions, widens the
character windows in the existing spacing alternative, and adds a polarity
veto so that relativity-of-simultaneity denials do not fire. Every
existing v3 alternative is carried over unchanged so Newton's Q6 hits
survive.

target_v3 is NOT edited. DCR1a/b/c/d/e reproductions remain byte-identical.

The construction of this module happened *before* the DCR1f held-out
validation set was read — the constructions above and the DCR1e-observed
gaps are the drafting inputs, not the held-out sentences themselves. See
`DCR1F_PREREGISTRATION.md`.
"""

from __future__ import annotations

import re
from typing import Any, Final, Mapping, Sequence

from experiments.date_cut_retrodiction.residue_v2 import normalise_v2
from experiments.date_cut_retrodiction.target import TargetFacet
from experiments.date_cut_retrodiction.target_v2 import FACET_QUORUM_V2
from experiments.date_cut_retrodiction.target_v3 import (
    TARGET_FACETS_V3,
    _POLARITY_VETO,
    _REFERENT_VETO,
)


__all__ = [
    "TARGET_FACETS_V4",
    "FACET_QUORUM_V4",
    "match_facets_v4",
    "surfaces_target_v4",
    "compare_v3_v4",
]

FACET_QUORUM_V4: Final[int] = FACET_QUORUM_V2

_TIME = r"(?:time|clock\w*|simultaneit\w*|duration|instant|moment|now|epoch)"
_SAMENESS = (
    r"(?:same|identical|alike|independent|common|shared|definite|"
    r"well[-\s]defined|absolute|universal|one|single)"
)
_UNIQUENESS = _SAMENESS
_INDEPENDENCE = (
    r"(?:observer|observers|frame|frames|system|systems|body|bodies|station|"
    r"stationary|moving|motion|translation|velocity|reference|everywhere|"
    r"all\s+places|whatever|whole|entire|every|any|throughout|all\s+points|"
    r"any\s+point|both|two)"
)

#: The five DCR1e-observed T1 constructions, plus target_v3's existing five
#: alternatives (carried forward so Newton and DCR1c's explicit phrasings
#: still fire). Order and content follow the DCR1F_PREREGISTRATION §1
#: linguistic-analysis specification.
_T1_V4_PATTERN: Final[str] = "|".join(
    f"(?:{alternative})"
    for alternative in (
        # --- carried from v2/v3, unchanged --------------------------------
        rf"\b(?:absolute|universal)\s+{_TIME}\b",
        r"\bsimultaneit\w*\s+(?:is|are)\s+(?:absolute|universal|observer[-\s]independent)\b",
        # widened window: real prose is longer than 60/40
        rf"\b{_TIME}\b[^.]{{0,120}}\b{_INDEPENDENCE}\b[^.]{{0,80}}\b{_SAMENESS}\b",
        rf"\b{_UNIQUENESS}\s+{_TIME}\b[^.]{{0,80}}\b"
        rf"(?:for|in|to)\s+(?:all|every|any|each|both|two)\b[^.]{{0,40}}\b{_INDEPENDENCE}\b",
        rf"\b{_TIME}\s+(?:is|are)\s+(?:the\s+)?{_SAMENESS}\b[^.]{{0,100}}\b{_INDEPENDENCE}\b",
        # --- new: "common time t in which …" -------------------------------
        # Larmor's exact construction. Requires SAMENESS-ish quantifier
        # before time, then an "in which" or "at which" or "for which"
        # relative pronoun, then some independence marker within 120 chars.
        rf"\b{_UNIQUENESS}\s+{_TIME}\b[^.]{{0,20}}\b(?:in|at|for|to)\s+which\b[^.]{{0,120}}\b{_INDEPENDENCE}\b",
        # --- new: "time is definite / well-defined / independent of X" ----
        # Lodge's exact construction: time predicated as definite, then a
        # motion/observer independence clause.
        rf"\b{_TIME}\b[^.]{{0,60}}\b(?:is|are)\s+(?:perfectly\s+)?(?:definite|well[-\s]defined|the\s+same|invariant)\b[^.]{{0,80}}\b(?:independent|regardless|whatever|whether|of\s+the\s+{_INDEPENDENCE})\b",
        # --- new: "regarded/perceived/treated/taken as simultaneous" ------
        # Poincaré 1898 (twice). The phrase "regarded as simultaneous"
        # asserts a simultaneity relation across observers or events.
        r"\b(?:regarded|perceived|treated|taken|considered|deemed|held)\s+(?:as|to\s+be)\s+simultaneous\b",
        # --- new: "instant across the whole / all / entire / every X" ------
        # Maxwell 1865: "instant at which … the whole medium".
        # A single instant applied to a spatially extended domain.
        rf"\b(?:instant|moment|epoch|time)\b[^.]{{0,60}}\b(?:at|in|for|to)\s+which\b[^.]{{0,60}}\b(?:whole|entire|all|every|both|throughout)\b",
        # --- new: "same time / same instant for/from/at all X" -------------
        # Catches "simultaneously from all points of the earth" and its
        # kin — the same simultaneity relation across a quantifier.
        r"\bsimultaneous(?:ly)?\b[^.]{0,40}\b(?:from|at|for|in|across|to|over)\s+(?:all|every|the\s+whole|each|any|both|two)\b",
    )
)

#: Relativity-of-simultaneity denials must NOT fire. Extracted from the
#: standard rhetoric of relativity-of-simultaneity: "in one frame … not in
#: another", "depends on the frame", "matter of convention". Applied as
#: a T1 veto only.
_RELATIVITY_VETO: Final[re.Pattern[str]] = re.compile(
    r"\b(?:in\s+one\s+frame|in\s+one\s+system|in\s+one\s+reference)\b[^.]{0,80}"
    r"\b(?:not|need\s+not|another|different|distinct)\b"
    r"|"
    r"\bsimultaneit\w*\b[^.]{0,60}"
    r"\b(?:convention\w*|frame[-\s]dependent|relative\s+to\s+(?:a|the|any)\s+(?:frame|observer|reference)"
    r"|depends?\s+on\s+(?:the\s+)?(?:observer|frame|state\s+of\s+motion|velocity|reference))\b"
    r"|"
    r"\bno\s+(?:absolute|universal|invariant|frame[-\s]independent)\s+"
    r"(?:simultaneit\w*|now|present|time\s+order)\b"
    r"|"
    r"\b(?:events?|processes?)\b[^.]{0,60}"
    r"\bsimultaneous\s+in\s+(?:one|a)\s+(?:frame|system|reference)\b[^.]{0,60}"
    r"\b(?:not|need\s+not)\b",
    re.IGNORECASE,
)


TARGET_FACETS_V4: Final[tuple[TargetFacet, ...]] = tuple(
    TargetFacet(
        facet.key,
        facet.description,
        _T1_V4_PATTERN if facet.key == "T1_absolute_simultaneity" else facet.pattern,
    )
    for facet in TARGET_FACETS_V3
)


def _t1_vetoed(haystack: str) -> bool:
    return bool(_RELATIVITY_VETO.search(haystack))


def match_facets_v4(
    propositions: Sequence[Mapping[str, Any]],
) -> dict[str, tuple[dict[str, str], ...]]:
    """Group propositions by facet under target_v4.

    T2 keeps v3's polarity + referent vetoes. T1 adds a relativity-of-
    simultaneity veto so that the denial does not fire. T3 is untouched.
    """
    hits: dict[str, list[dict[str, str]]] = {f.key: [] for f in TARGET_FACETS_V4}
    for proposition in propositions:
        name = str(proposition.get("name", "")).replace("_", " ")
        statement = str(proposition.get("statement", ""))
        haystack = normalise_v2(f"{name} {statement}")
        for facet in TARGET_FACETS_V4:
            if not facet.regex.search(haystack):
                continue
            if facet.key == "T1_absolute_simultaneity" and _t1_vetoed(haystack):
                continue
            if facet.key == "T2_privileged_frame" and (
                _POLARITY_VETO.search(haystack) or _REFERENT_VETO.search(haystack)
            ):
                continue
            hits[facet.key].append(
                {
                    "doc_id": str(proposition.get("doc_id", "")),
                    "name": str(proposition.get("name", "")),
                    "statement": statement,
                }
            )
    return {key: tuple(value) for key, value in hits.items()}


def surfaces_target_v4(
    propositions: Sequence[Mapping[str, Any]],
) -> tuple[bool, int]:
    hits = match_facets_v4(propositions)
    present = sum(1 for value in hits.values() if value)
    return present >= FACET_QUORUM_V4, present


def compare_v3_v4(
    propositions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """What v4 changes on this proposition set. Reported rather than asserted."""
    from experiments.date_cut_retrodiction.target_v3 import match_facets_v3

    v3 = match_facets_v3(propositions)
    v4 = match_facets_v4(propositions)
    return {
        "v3_counts": {k: len(v) for k, v in v3.items()},
        "v4_counts": {k: len(v) for k, v in v4.items()},
        "v3_facets_present": sorted(k for k, v in v3.items() if v),
        "v4_facets_present": sorted(k for k, v in v4.items() if v),
        "new_in_v4": {
            key: [
                h["statement"]
                for h in v4[key]
                if h["statement"] not in {x["statement"] for x in v3[key]}
            ]
            for key in v3
            if v4[key]
        },
    }
