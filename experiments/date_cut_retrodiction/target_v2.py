"""The target matcher, repaired.

DCR1 froze ``target.py`` before reading any extraction output. That was the
right discipline and it is why the defect below is reportable rather than
invisible — but freezing a matcher makes it honest, not correct.

Adjudicating every matched proposition by hand showed **all three** T1 hits at
the 1904 cut were false positives:

* "the same causes take **the same time** to produce the same effects" — a
  causal postulate about durations
* "causes almost identical take almost **the same time**…" — the same, hedged
* "the ether transmits **at the same time** the optical and the electrical
  perturbations" — the idiom for "both at once"

The v1 pattern accepted ``(absolute|universal|same|common|true)`` before a time
word, so it matched ordinary English. ``same`` and ``common`` are the culprits
and both are removed here. What replaces them is a requirement that the
statement carry an explicit **independence** clause: the claim must be that time
or simultaneity does not depend on the observer, the frame, or the motion. That
is what the historical deletion actually removed.

T2 and T3 survived adjudication unchanged — 17 of 17 and 1 of 1 genuine — and
are carried over with only the accent- and ligature-tolerance that v1 lacked.

The v1 matcher is **not** edited. It stays exactly as frozen so DCR1's published
numbers remain reproducible, and ``compare_matchers`` below quantifies what the
repair changes rather than leaving it to be taken on trust.
"""

from __future__ import annotations

from typing import Any, Final, Mapping, Sequence

from experiments.date_cut_retrodiction.residue_v2 import normalise_v2
from experiments.date_cut_retrodiction.target import TargetFacet, match_facets


__all__ = [
    "TARGET_FACETS_V2",
    "FACET_QUORUM_V2",
    "match_facets_v2",
    "surfaces_target_v2",
    "compare_matchers",
]

FACET_QUORUM_V2: Final[int] = 2

#: Words that make a time claim frame-relative rather than merely repeated.
_INDEPENDENCE = (
    r"(observer|frame|system|body|bodies|station|stationary|moving|motion|"
    r"translation|velocity|reference|everywhere|all\s+places|whatever)"
)

_TIME = r"(time|clock\w*|simultaneit\w*|duration)"
_SAMENESS = r"(same|identical|alike|independent|common)"

#: "the same time" on its own is ordinary English and no longer qualifies.
#: Each alternative below demands either an explicit absoluteness word or a
#: sameness claim tied to an independence clause, in either clause order.
_UNIQUENESS = r"(same|identical|alike|independent|common|one|single|universal)"

#: Every alternative is wrapped in its own group. Without that, an inner
#: alternation leaks past the intended boundary and a bare time word matches on
#: its own — which is precisely how the v1 pattern let "the same time" through.
_T1_PATTERN: Final[str] = "|".join(
    f"(?:{alternative})"
    for alternative in (
        rf"\b(?:absolute|universal)\s+{_TIME}\b",
        r"\bsimultaneit\w*\s+(?:is|are)\s+(?:absolute|universal|observer-independent)\b",
        rf"\b{_TIME}\b[^.]{{0,60}}\b{_INDEPENDENCE}\b[^.]{{0,40}}\b{_SAMENESS}\b",
        rf"\b{_UNIQUENESS}\s+{_TIME}\b[^.]{{0,50}}\b"
        rf"(?:for|in|to)\s+(?:all|every|any|each)\b[^.]{{0,20}}\b{_INDEPENDENCE}\b",
        # Clauses reversed: "the time is the same for a stationary observer as
        # for an observer carried along in uniform motion".
        rf"\b{_TIME}\s+(?:is|are)\s+(?:the\s+)?{_SAMENESS}\b[^.]{{0,60}}\b"
        rf"{_INDEPENDENCE}\b",
    )
)

TARGET_FACETS_V2: Final[tuple[TargetFacet, ...]] = (
    TargetFacet(
        "T1_absolute_simultaneity",
        "Time or simultaneity is observer-independent: one universal time, "
        "with 'at the same time' meaning the same thing for everyone.",
        _T1_PATTERN,
    ),
    TargetFacet(
        "T2_privileged_frame",
        "The aether defines absolute rest or a privileged frame of reference.",
        r"(absolute\s+(rest|motion|velocity|space|position))"
        r"|(aether|ether)\s+\w*\s*(at\s+rest|stationary|fixed|undisturbed)"
        r"|(stationary|fixed|privileged|preferred)\s+(aether|ether|frame|system)"
        r"|motion\s+(relative\s+)?to\s+the\s+(aether|ether)",
    ),
    TargetFacet(
        "T3_local_time_artifice",
        "Local time is a mathematical auxiliary, not the time clocks read.",
        r"local\s+time"
        r"|(auxiliar\w+|mathematical|fictitious|artificial|merely)\s+\w*\s*"
        r"(time|variable|quantit\w*)"
        r"|(time|variable)\s+\w*\s*(is|as)\s+\w*\s*(auxiliar\w+|mathematical|fictitious)",
    ),
)


def match_facets_v2(
    propositions: Sequence[Mapping[str, Any]],
) -> dict[str, tuple[dict[str, str], ...]]:
    """Group propositions by target facet under the repaired patterns."""
    hits: dict[str, list[dict[str, str]]] = {f.key: [] for f in TARGET_FACETS_V2}
    for proposition in propositions:
        name = str(proposition.get("name", "")).replace("_", " ")
        statement = str(proposition.get("statement", ""))
        haystack = normalise_v2(f"{name} {statement}")
        for facet in TARGET_FACETS_V2:
            if facet.regex.search(haystack):
                hits[facet.key].append(
                    {
                        "doc_id": str(proposition.get("doc_id", "")),
                        "name": str(proposition.get("name", "")),
                        "statement": statement,
                    }
                )
    return {key: tuple(value) for key, value in hits.items()}


def surfaces_target_v2(
    propositions: Sequence[Mapping[str, Any]],
) -> tuple[bool, int]:
    hits = match_facets_v2(propositions)
    present = sum(1 for value in hits.values() if value)
    return present >= FACET_QUORUM_V2, present


def compare_matchers(
    propositions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """What does the repair change on this proposition set?

    Reported rather than asserted. A matcher repair that silently altered the
    headline would be indistinguishable from fitting the matcher to the data.
    """
    v1 = match_facets(propositions)
    v2 = match_facets_v2(propositions)
    return {
        "v1_counts": {k: len(v) for k, v in v1.items()},
        "v2_counts": {k: len(v) for k, v in v2.items()},
        "v1_facets_present": sorted(k for k, v in v1.items() if v),
        "v2_facets_present": sorted(k for k, v in v2.items() if v),
        "dropped_by_repair": {
            key: [
                h.statement
                for h in v1[key]
                if h.statement not in {x["statement"] for x in v2[key]}
            ]
            for key in v1
            if v1[key]
        },
    }
