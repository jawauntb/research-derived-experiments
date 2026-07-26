"""What counts as the historical deletion appearing in an extracted set.

Written and committed **before** any extraction output was read. That ordering
is not a nicety. Scoring a retrodiction requires knowing the answer -- that is
what retrodiction means -- so the only defence against fitting the matcher to
the outputs is to fix the matcher first and apply it identically at every cut.

The historical deletion Einstein made in June 1905 is not a single proposition.
It is a small entangled family, and the toys taught us to expect exactly that:

* **T1 -- absolute simultaneity.** That "at the same time" has an observer-
  independent meaning; that there is one universal time.
* **T2 -- privileged frame.** That the aether furnishes a state of absolute
  rest against which true motion is defined.
* **T3 -- local time as artifice.** That the auxiliary time variable appearing
  in the transformed equations is a mathematical convenience rather than what
  clocks in the moving system actually read.

A cut "surfaces the target family" when the extraction contains at least one
proposition matching each of at least two of the three. Requiring two rather
than one guards against a single generic aether mention scoring a hit;
requiring three would be unreasonable at the placebo cuts by construction,
which would make the control vacuous.

Matching is regex over ``name`` and ``statement`` only -- never over ``quote``,
because quotes are source text and would let a document score a hit merely by
discussing a topic rather than by the extractor having isolated a commitment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Iterable, Mapping, Sequence


__all__ = ["TargetFacet", "TARGET_FACETS", "FacetHit", "match_facets", "surfaces_target"]

#: At least this many of the three facets must be present to call it a hit.
FACET_QUORUM: Final[int] = 2


@dataclass(frozen=True)
class TargetFacet:
    key: str
    description: str
    pattern: str

    @property
    def regex(self) -> re.Pattern[str]:
        return re.compile(self.pattern, re.IGNORECASE)


TARGET_FACETS: Final[tuple[TargetFacet, ...]] = (
    TargetFacet(
        "T1_absolute_simultaneity",
        "Simultaneity or time itself is observer-independent and universal.",
        r"(absolute|universal|same|common|true)\s+\w*\s*"
        r"(time|simultaneit|instant|epoch)"
        r"|simultaneit\w*\s+is\s+(absolute|universal)"
        r"|(time|clock\w*)\s+\w*\s*(is|are)\s+the\s+same\s+(for|in)\b",
    ),
    TargetFacet(
        "T2_privileged_frame",
        "The aether defines absolute rest or a privileged frame of reference.",
        r"(absolute\s+(rest|motion|velocity|space|position))"
        r"|(aether|ether|æther)\s+\w*\s*(at\s+rest|stationary|fixed|undisturbed)"
        r"|(stationary|fixed|privileged|preferred)\s+(aether|ether|æther|frame|system)"
        r"|motion\s+(relative\s+)?to\s+the\s+(aether|ether|æther)",
    ),
    TargetFacet(
        "T3_local_time_artifice",
        "Local time is a mathematical auxiliary, not the time clocks read.",
        r"local\s+time"
        r"|(auxiliar\w+|mathematical|fictitious|artificial|merely)\s+\w*\s*"
        r"(time|variable|quantit)"
        r"|(time|variable)\s+\w*\s*(is|as)\s+\w*\s*(auxiliar\w+|mathematical|fictitious)",
    ),
)


@dataclass(frozen=True)
class FacetHit:
    facet: str
    doc_id: str
    name: str
    statement: str


def match_facets(
    propositions: Iterable[Mapping[str, object]],
) -> dict[str, tuple[FacetHit, ...]]:
    """Group propositions by which target facet they match, if any."""
    hits: dict[str, list[FacetHit]] = {facet.key: [] for facet in TARGET_FACETS}
    for proposition in propositions:
        name = str(proposition.get("name", ""))
        statement = str(proposition.get("statement", ""))
        haystack = f"{name.replace('_', ' ')} {statement}"
        for facet in TARGET_FACETS:
            if facet.regex.search(haystack):
                hits[facet.key].append(
                    FacetHit(
                        facet.key,
                        str(proposition.get("doc_id", "")),
                        name,
                        statement,
                    )
                )
    return {key: tuple(value) for key, value in hits.items()}


def surfaces_target(propositions: Sequence[Mapping[str, object]]) -> tuple[bool, int]:
    """Return ``(hit, n_facets_present)`` under the quorum rule."""
    hits = match_facets(propositions)
    present = sum(1 for value in hits.values() if value)
    return present >= FACET_QUORUM, present
