"""DCR1d — a positive control for the T1 matcher.

DCR1c passed every gate and reported one thing that did not fit: T1 (absolute
simultaneity) matched **zero** propositions at every cut, under both v2 and v3,
across all three sandboxed extractions. The paper refused to decide between
two readings -- the matcher can't do the job, or the commitment isn't stated
in the corpus.

This module owns the positive-control extension. It is deliberately additive:
DCR1c's ``SOURCES`` and ``CUTS`` are untouched, so ``run_dcr1c.py`` produces
byte-identical numbers to its published paper. DCR1d works from ``NEWTON_SOURCE``
and ``POSITIVE_CONTROL_CUT`` here.

The choice of positive control is not arbitrary. Newton's Scholium to the
Definitions in Book I of *Principia Mathematica* (Motte 1729 translation, 1846
Chittenden edition) states absolute time and absolute space in the exact
vocabulary the DCR1c matcher was written to catch. If the matcher does not
fire on this document, the T1 absence in DCR1c is uninterpretable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from experiments.date_cut_retrodiction.corpus import SourceSpec
from experiments.date_cut_retrodiction.cuts import Cut


__all__ = [
    "NEWTON_SOURCE",
    "POSITIVE_CONTROL_CUT",
    "NEWTON_PASS_DIRS",
    "NEWTON_CONSENSUS_DIR",
]


NEWTON_SOURCE: Final[SourceSpec] = SourceSpec(
    doc_id="newton_1687_scholium",
    wikisource_title="The Mathematical Principles of Natural Philosophy (1846)/Definitions",
    author="Isaac Newton (Motte 1729 translation)",
    year=1687,
    note=(
        "Book I: the eight Definitions followed by the Scholium on absolute vs. "
        "relative time, space, place and motion. Positive control for DCR1d: "
        "the passage 'Absolute, true, and mathematical time... flows equably "
        "without regard to anything external' is the T1 commitment as an "
        "explicit English sentence."
    ),
)


POSITIVE_CONTROL_CUT: Final[Cut] = Cut(
    year=1687,
    label="positive control",
    is_placebo=False,
    rationale=(
        "Not a placebo and not the DCR1 target. This cut isolates Newton, whose "
        "Scholium states absolute time and absolute space as explicit "
        "commitments. If the T1 matcher does not fire here, the T1 absence in "
        "DCR1c is an instrument artifact and cannot support historical claims."
    ),
)


_PACKAGE: Final[Path] = Path(__file__).resolve().parent

#: Three sandboxed passes, one at a time. Same methodology as DCR1c: the
#: extraction prompt with the pass-2 amendment forbidding any repository file
#: access. Directories named separately from DCR1c's so the two do not collide.
NEWTON_PASS_DIRS: Final[tuple[Path, ...]] = (
    _PACKAGE / "extractions_newton_pass1",
    _PACKAGE / "extractions_newton_pass2",
    _PACKAGE / "extractions_newton_pass3",
)

NEWTON_CONSENSUS_DIR: Final[Path] = _PACKAGE / "extractions_newton_consensus"
