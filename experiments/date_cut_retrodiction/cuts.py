"""Date cuts, including the placebo cuts that decide whether this works.

The retrodiction asks whether an execution-free nominator, given only what was
public before 1905, ranks the deletion history actually made. The obvious
failure mode is that the *extractor* already knows the answer and hands it over
dressed as a candidate -- Spencer's candidate-selection circularity, which
killed COGR Wave 1a.

Placebo cuts are the control. Run the identical pipeline at 1880 and 1897. At
those dates the target repair was not available: Michelson-Morley had not been
performed (1880) or had been performed but Lorentz's 1904 corresponding-states
apparatus did not exist (1897). If the nominator "finds" the answer there too,
the signal is in the extractor, not in the corpus.

This is a stronger control than the vocabulary audit in ``residue.py``, because
it catches leakage by *selection* -- an extractor that surfaces only
period-appropriate words but chooses which commitments to surface using
knowledge of what came next.

One asymmetry to state plainly rather than hide: the cuts are nested, so the
1904 corpus contains everything the 1897 corpus does. A hit at 1904 and not at
1897 is evidence the 1898-1904 material carries the signal. A hit at *all three*
is evidence of extractor leakage. A hit at 1880 alone would mean something has
gone badly wrong with the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


__all__ = ["Cut", "CUTS", "TARGET_CUT", "PLACEBO_CUTS"]


@dataclass(frozen=True)
class Cut:
    year: int
    label: str
    is_placebo: bool
    rationale: str


CUTS: Final[tuple[Cut, ...]] = (
    Cut(
        1880,
        "deep placebo",
        True,
        "Maxwell only. No ether-drift null result exists yet: Michelson's first "
        "attempt is a year away and Michelson-Morley seven. Nothing in the "
        "corpus poses the problem the target deletion answers, so a hit here "
        "cannot be anything but leakage.",
    ),
    Cut(
        1897,
        "near placebo",
        True,
        "The null results are in -- Michelson 1881, Michelson-Morley 1887 -- and "
        "FitzGerald has proposed contraction. But Lorentz's 1904 "
        "corresponding-states paper and Poincare's 1904 statement of the "
        "principle of relativity are both absent. The problem is posed; the "
        "materials for the specific repair are not all present.",
    ),
    Cut(
        1904,
        "target",
        False,
        "Everything public before Einstein's June 1905 submission. Lorentz 1904 "
        "supplies local time as an explicitly mathematical artifice; Poincare's "
        "St Louis lecture of September 1904 states the principle of relativity "
        "verbatim and declines to give up the ether. Both halves of the "
        "tension are on the table and the deletion has not been made.",
    ),
)

TARGET_CUT: Final[Cut] = CUTS[-1]
PLACEBO_CUTS: Final[tuple[Cut, ...]] = tuple(c for c in CUTS if c.is_placebo)
