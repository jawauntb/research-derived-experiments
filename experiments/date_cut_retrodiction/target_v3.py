"""The target matcher, with T2's polarity and referent defects repaired.

DCR1b's H5 failed: four of fifteen facet hits at the target cut did not state
the facet they matched. All four were T2, and they fail in three distinct ways
that a bare keyword pattern cannot distinguish:

* **Polarity.** "The hypothesis of a stationary ether is shown to be incorrect,
  and the hypothesis is erroneous." The pattern cannot tell assertion from
  refutation.
* **Referent.** "Stokes … assumes the ether at the earth's surface to be at rest
  with regard to the earth's surface." Ether at rest *relative to the earth* is
  the dragged-ether **rival**, which denies a privileged frame rather than
  asserting one. The pattern matched "at rest" without asking what it is at rest
  with respect to.
* **Label.** "…contracted in comparison with the fixed system." A coordinate
  label in the corresponding-states theorem, not a claim that any frame is
  privileged.

v3 adds two vetoes and narrows one alternative. The base patterns are otherwise
unchanged from v2, and T1 and T3 are carried over untouched — neither produced a
false positive under adjudication.

A veto is a blunt instrument and it can over-reject. The specific risk here is
real and worth naming: Larmor's "It has not been found possible to construct a
system of dynamics which has respect only to the relative positions of moving
bodies" is a *negative sentence* whose content is nonetheless exactly the
absolute-space commitment. So the polarity veto fires on targeted refutation
markers — `incorrect`, `erroneous`, `refuted` — never on bare negation. Tested
against all fifteen adjudicated hits before use.
"""

from __future__ import annotations

import re
from typing import Any, Final, Mapping, Sequence

from experiments.date_cut_retrodiction.residue_v2 import normalise_v2
from experiments.date_cut_retrodiction.target import TargetFacet
from experiments.date_cut_retrodiction.target_v2 import (
    FACET_QUORUM_V2,
    TARGET_FACETS_V2,
    match_facets_v2,
)


__all__ = [
    "TARGET_FACETS_V3",
    "FACET_QUORUM_V3",
    "match_facets_v3",
    "surfaces_target_v3",
    "compare_v2_v3",
]

FACET_QUORUM_V3: Final[int] = FACET_QUORUM_V2

#: Targeted refutation markers. Deliberately NOT bare negation -- Larmor's
#: absolute-space commitment is stated as "it has not been found possible…".
_POLARITY_VETO: Final[re.Pattern[str]] = re.compile(
    r"\b(incorrect|erroneous|refuted|disproved|disproven|untenable|abandoned"
    r"|shown to be false|is false)\b"
    r"|\b(theory|hypothesis)\b[^.]{0,40}\bfails?\b",
    re.IGNORECASE,
)

#: A rest claim made relative to the earth is the dragged-ether rival.
_REFERENT_VETO: Final[re.Pattern[str]] = re.compile(
    r"\b(at rest|stationary|fixed)\b[^.]{0,30}"
    r"\b(with (regard|respect) to|relative(ly)? to|in relation to)\s+"
    r"(the\s+)?(earth|earth's|apparatus|observer)",
    re.IGNORECASE,
)

_T2_V3_PATTERN: Final[str] = "|".join(
    (
        r"(?:absolute\s+(?:rest|motion|velocity|space|position))",
        r"(?:(?:aether|ether)\s+\w*\s*(?:at\s+rest|stationary|undisturbed))",
        # "fixed system" and "fixed frame" are dropped: they are coordinate
        # labels. "fixed aether" is kept, because that is a claim.
        r"(?:(?:stationary|privileged|preferred)\s+(?:aether|ether|frame|system))",
        r"(?:fixed\s+(?:aether|ether))",
        r"(?:motion\s+(?:relative\s+)?to\s+the\s+(?:aether|ether))",
    )
)

TARGET_FACETS_V3: Final[tuple[TargetFacet, ...]] = tuple(
    TargetFacet(
        facet.key,
        facet.description,
        _T2_V3_PATTERN if facet.key == "T2_privileged_frame" else facet.pattern,
    )
    for facet in TARGET_FACETS_V2
)


def _vetoed(haystack: str) -> bool:
    return bool(_POLARITY_VETO.search(haystack) or _REFERENT_VETO.search(haystack))


def match_facets_v3(
    propositions: Sequence[Mapping[str, Any]],
) -> dict[str, tuple[dict[str, str], ...]]:
    """Group propositions by facet, applying the polarity and referent vetoes.

    The vetoes apply to **T2 only**. T1 and T3 produced no false positives under
    adjudication, and applying an untested veto to a clean facet would be
    changing something that is not broken.
    """
    hits: dict[str, list[dict[str, str]]] = {f.key: [] for f in TARGET_FACETS_V3}
    for proposition in propositions:
        name = str(proposition.get("name", "")).replace("_", " ")
        statement = str(proposition.get("statement", ""))
        haystack = normalise_v2(f"{name} {statement}")
        for facet in TARGET_FACETS_V3:
            if not facet.regex.search(haystack):
                continue
            if facet.key == "T2_privileged_frame" and _vetoed(haystack):
                continue
            hits[facet.key].append(
                {
                    "doc_id": str(proposition.get("doc_id", "")),
                    "name": str(proposition.get("name", "")),
                    "statement": statement,
                }
            )
    return {key: tuple(value) for key, value in hits.items()}


def surfaces_target_v3(
    propositions: Sequence[Mapping[str, Any]],
) -> tuple[bool, int]:
    hits = match_facets_v3(propositions)
    present = sum(1 for value in hits.values() if value)
    return present >= FACET_QUORUM_V3, present


def compare_v2_v3(propositions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """What the veto changes, reported rather than asserted."""
    v2 = match_facets_v2(propositions)
    v3 = match_facets_v3(propositions)
    return {
        "v2_counts": {k: len(v) for k, v in v2.items()},
        "v3_counts": {k: len(v) for k, v in v3.items()},
        "v2_facets_present": sorted(k for k, v in v2.items() if v),
        "v3_facets_present": sorted(k for k, v in v3.items() if v),
        "dropped_by_veto": {
            key: [
                h["statement"]
                for h in v2[key]
                if h["statement"] not in {x["statement"] for x in v3[key]}
            ]
            for key in v2
            if v2[key]
        },
    }
