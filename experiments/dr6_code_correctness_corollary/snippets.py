"""DR6 snippets: 5 realisations of the naive-UTC commitment + 5 placebos.

The target commitment D is: "This Python code implicitly assumes that all
datetime values are timezone-naive and represent UTC." Each realisation
snippet embodies D in a specific surface form; each placebo does not
embody D, either because it is explicitly timezone-aware or because it
avoids datetime entirely.

Snippets are self-contained function definitions with 5-15 lines of
substantive logic. They are deliberately NOT one-liners: the verifier
has surrounding context that could support or defeat surface-level
matching.

Ground truth is committed here at file-write time. The verifier is given
only the snippet IDs and code, not the labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


__all__ = ["SNIPPETS", "Snippet"]


@dataclass(frozen=True)
class Snippet:
    snippet_id: str
    kind: str  # "realisation" or "placebo"
    surface_form: str  # one-line label for the surface form
    code: str


SNIPPETS: Final[tuple[Snippet, ...]] = (
    # ------------------------------------------------------------------
    # Realisations of D
    # ------------------------------------------------------------------
    Snippet(
        snippet_id="R1_utcnow_direct",
        kind="realisation",
        surface_form="datetime.utcnow() direct use",
        code="""\
from datetime import datetime, timedelta

def rate_limit_key(user_id: str, window_seconds: int = 60) -> str:
    \"\"\"Return a rate-limit bucket key for the current window.\"\"\"
    now = datetime.utcnow()
    bucket = now.replace(microsecond=0, second=(now.second // window_seconds) * window_seconds)
    key = f"rate:{user_id}:{bucket.isoformat()}"
    return key


def is_expired(created_at: datetime, ttl: timedelta) -> bool:
    now = datetime.utcnow()
    return (now - created_at) > ttl
""",
    ),
    Snippet(
        snippet_id="R2_replace_tzinfo_none",
        kind="realisation",
        surface_form=".replace(tzinfo=None) to strip timezone",
        code="""\
from datetime import datetime

def normalise_for_storage(dt: datetime) -> datetime:
    \"\"\"Prepare a datetime for storage in a naive-UTC-only column.\"\"\"
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt


def compare_windows(a: datetime, b: datetime) -> int:
    a = normalise_for_storage(a)
    b = normalise_for_storage(b)
    if a < b:
        return -1
    if a > b:
        return 1
    return 0
""",
    ),
    Snippet(
        snippet_id="R3_time_fromtimestamp",
        kind="realisation",
        surface_form="time.time() → fromtimestamp yields naive",
        code="""\
import time
from datetime import datetime, timedelta

def stamp_event(payload: dict) -> dict:
    \"\"\"Attach a timestamp to an event payload.\"\"\"
    stamped = dict(payload)
    stamped["ts"] = datetime.fromtimestamp(time.time())
    return stamped


def is_recent(event: dict, cutoff: timedelta) -> bool:
    ts = event.get("ts")
    if ts is None:
        return False
    return datetime.fromtimestamp(time.time()) - ts < cutoff
""",
    ),
    Snippet(
        snippet_id="R4_iso_parse_no_tz",
        kind="realisation",
        surface_form="ISO parse without timezone",
        code="""\
from datetime import datetime

def parse_log_line(line: str) -> tuple[datetime, str]:
    \"\"\"Parse a log line of the form 'YYYY-MM-DDTHH:MM:SS message'.\"\"\"
    ts_str, _, message = line.partition(" ")
    ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
    return ts, message


def latest_timestamp(lines: list[str]) -> datetime:
    timestamps = [parse_log_line(line)[0] for line in lines]
    return max(timestamps)
""",
    ),
    Snippet(
        snippet_id="R5_combine_utc_convention",
        kind="realisation",
        surface_form="combine(date, time) — UTC by convention",
        code="""\
from datetime import datetime, date, time, timedelta

DEFAULT_CUTOFF = time(hour=0, minute=0, second=0)


def day_boundary(d: date) -> datetime:
    \"\"\"Return the cutoff datetime for day d, assumed UTC by fleet convention.\"\"\"
    return datetime.combine(d, DEFAULT_CUTOFF)


def days_between(a: date, b: date) -> int:
    dt_a = day_boundary(a)
    dt_b = day_boundary(b)
    return (dt_b - dt_a).days
""",
    ),
    # ------------------------------------------------------------------
    # Placebos: DO NOT embody D
    # ------------------------------------------------------------------
    Snippet(
        snippet_id="P1_pytz_localize",
        kind="placebo",
        surface_form="pytz.utc.localize()",
        code="""\
from datetime import datetime
import pytz

def to_utc_aware(dt: datetime) -> datetime:
    \"\"\"Convert a naive datetime to a timezone-aware UTC datetime.\"\"\"
    if dt.tzinfo is not None:
        return dt.astimezone(pytz.utc)
    return pytz.utc.localize(dt)


def render_iso(dt: datetime) -> str:
    return to_utc_aware(dt).isoformat()
""",
    ),
    Snippet(
        snippet_id="P2_now_with_timezone_utc",
        kind="placebo",
        surface_form="datetime.now(timezone.utc)",
        code="""\
from datetime import datetime, timedelta, timezone

def is_stale(created_at: datetime, max_age: timedelta) -> bool:
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        raise ValueError("created_at must be timezone-aware")
    return (now - created_at) > max_age


def freshness_score(created_at: datetime, half_life: timedelta) -> float:
    now = datetime.now(timezone.utc)
    age = now - created_at
    return 0.5 ** (age / half_life)
""",
    ),
    Snippet(
        snippet_id="P3_zoneinfo_user_tz",
        kind="placebo",
        surface_form="zoneinfo user-supplied timezone",
        code="""\
from datetime import datetime
from zoneinfo import ZoneInfo


def local_time_of(user_tz_name: str, ts: datetime) -> datetime:
    \"\"\"Convert a timezone-aware ts to the user's local wall-clock time.\"\"\"
    tz = ZoneInfo(user_tz_name)
    if ts.tzinfo is None:
        raise ValueError("ts must carry its own timezone")
    return ts.astimezone(tz)


def format_for_user(user_tz_name: str, ts: datetime) -> str:
    return local_time_of(user_tz_name, ts).strftime("%Y-%m-%d %H:%M:%S %Z")
""",
    ),
    Snippet(
        snippet_id="P4_no_datetime_arithmetic",
        kind="placebo",
        surface_form="no datetime, arithmetic only",
        code="""\
def compound_interest(principal: float, rate: float, periods: int) -> float:
    balance = principal
    for _ in range(periods):
        balance *= (1 + rate)
    return balance


def median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        raise ValueError("empty list")
    if n % 2 == 1:
        return ordered[n // 2]
    return (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0
""",
    ),
    Snippet(
        snippet_id="P5_arrow_aware",
        kind="placebo",
        surface_form="arrow / third-party timezone-aware",
        code="""\
import arrow

def next_hour_boundary(now: 'arrow.Arrow') -> 'arrow.Arrow':
    \"\"\"Return the next top-of-the-hour after ``now``, timezone-aware.\"\"\"
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return now.shift(hours=+1).replace(minute=0, second=0, microsecond=0)


def format_since(then: 'arrow.Arrow') -> str:
    now = arrow.utcnow()
    return (now - then).humanize()
""",
    ),
)
