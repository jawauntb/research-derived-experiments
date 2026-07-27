"""DR6c regex verifier: proposition-independent surface-pattern scorer.

Scores each snippet 0-10 by counting hits from a set of regex patterns
hand-drafted from the 5 realisation surface-form LABELS committed in
DR6_PREREGISTRATION.md. The verifier has no access to $D$ semantically:
it counts matches and scales.

Patterns are drafted per surface form (one per realisation, one per
placebo family). The scorer sums matches, caps at 10, and returns the
integer.

This is what DR5 calls a proposition-independent nominator: N(p) depends
only on p (specifically, on which regex patterns fire in p), with no
access to any structural grouping over the snippet set and no semantic
model of D.
"""

from __future__ import annotations

import re
from typing import Final


__all__ = ["POSITIVE_PATTERNS", "NEGATIVE_PATTERNS", "score_snippet"]


#: Patterns hand-drafted from the realisation surface-form labels in
#: DR6_PREREGISTRATION.md. Each pattern targets one surface form. This is
#: how a matcher-designer with no access to the code would build the
#: recogniser.
POSITIVE_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    ("R1_utcnow", r"\bdatetime\.utcnow\s*\("),
    ("R2_replace_tzinfo_none", r"\.replace\s*\([^)]*tzinfo\s*=\s*None"),
    ("R3_time_fromtimestamp", r"\btime\.time\s*\(\s*\)|\bfromtimestamp\s*\("),
    ("R4_iso_parse_no_tz", r"\bstrptime\s*\([^)]*%Y-%m-%dT%H:%M:%S(?!.*%z)"),
    ("R5_combine_datetime", r"\bdatetime\.combine\s*\("),
)


#: Patterns that indicate explicit timezone awareness — a *negative* signal
#: for D. When these appear, the snippet is more likely a placebo.
NEGATIVE_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    ("PYTZ_UTC", r"\bpytz\.utc\b"),
    ("TIMEZONE_UTC_ARG", r"\btimezone\.utc\b"),
    ("ZONEINFO", r"\bZoneInfo\s*\("),
    ("ARROW", r"\barrow\.(utcnow|now)\s*\(|import\s+arrow"),
)


_POS_RE: Final[tuple[tuple[str, re.Pattern[str]], ...]] = tuple(
    (name, re.compile(pattern, re.MULTILINE)) for name, pattern in POSITIVE_PATTERNS
)
_NEG_RE: Final[tuple[tuple[str, re.Pattern[str]], ...]] = tuple(
    (name, re.compile(pattern, re.MULTILINE)) for name, pattern in NEGATIVE_PATTERNS
)


def score_snippet(code: str) -> int:
    """Return an integer 0-10 score for how strongly ``code`` embodies D.

    Rule (proposition-independent):

    - +2 per positive pattern that matches at least once (max 10).
    - -3 per negative pattern that matches at least once.
    - Clamped to [0, 10].

    Nothing in this function reads a class grouping or a corpus of other
    snippets; each snippet is scored in isolation.
    """
    positive_hits = sum(2 for _, regex in _POS_RE if regex.search(code))
    negative_hits = sum(3 for _, regex in _NEG_RE if regex.search(code))
    raw = positive_hits - negative_hits
    return max(0, min(10, raw))
