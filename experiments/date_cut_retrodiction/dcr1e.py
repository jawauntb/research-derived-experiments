"""DCR1e — can any extraction surface an unstated presupposition?

DCR1c/d left one question standing: if the load-bearing deletion is a
proposition no document states, can any extraction pipeline surface it?
DCR1e is the first experiment aimed directly at that question. It runs a
different extraction prompt against the same corpus, one that asks the
extractor to reverse-engineer commitments from arguments rather than
enumerate stated ones.

The prompt is in ``EXTRACTION_PROMPT_PRESUPPOSITION.md``. The corpus is the
fifteen DCR1c documents plus Newton (from DCR1d) as a sanity control.
Consensus is 2-of-3, same as DCR1c. The runner is ``run_dcr1e.py``.

DCR1c's ``SOURCES``/``CUTS`` are untouched. DCR1e composes its own corpus by
listing sources rather than editing the DCR1c tuple, so DCR1a/b/c/d
reproductions remain byte-identical.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from experiments.date_cut_retrodiction.corpus import SOURCES, SourceSpec
from experiments.date_cut_retrodiction.dcr1d import NEWTON_SOURCE


__all__ = [
    "DCR1E_SOURCES",
    "PRESUP_PASS_DIRS",
    "PRESUP_CONSENSUS_DIR",
    "SUPPORT_THRESHOLD_PRESUP",
]


#: The DCR1c corpus, plus Newton as a sanity control. Newton is included so
#: Q6 (the sanity gate) can be evaluated in the same pass. Q6 asks whether
#: the presupposition-inferring extractor produces T1 on a document that
#: explicitly states absolute time -- if it fails here, the prompt is broken
#: and the rest is uninterpretable.
DCR1E_SOURCES: Final[tuple[SourceSpec, ...]] = tuple(SOURCES) + (NEWTON_SOURCE,)


_PACKAGE: Final[Path] = Path(__file__).resolve().parent

#: Three sandboxed passes, distinct from every DCR1c/d directory so nothing
#: collides. The prompt used is ``EXTRACTION_PROMPT_PRESUPPOSITION.md``.
PRESUP_PASS_DIRS: Final[tuple[Path, ...]] = (
    _PACKAGE / "extractions_presup_pass1",
    _PACKAGE / "extractions_presup_pass2",
    _PACKAGE / "extractions_presup_pass3",
)

PRESUP_CONSENSUS_DIR: Final[Path] = _PACKAGE / "extractions_presup_consensus"

#: Same 2-of-3 discipline as DCR1c.
SUPPORT_THRESHOLD_PRESUP: Final[int] = 2
