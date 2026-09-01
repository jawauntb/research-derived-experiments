"""The nightly pass: summarise a day's notes in place, idempotently.

Default backend is ``none`` — pure heuristics, no network, no model. That
keeps the promise that gazenotes works fully offline; an LLM backend is an
opt-in upgrade, not a dependency.

The summary lives in a marked block above the first entry. Re-running replaces
that block; it never duplicates it and never touches an entry.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

from .config import Config, NightlyConfig
from .lock import notes_lock
from .notes import SUMMARY_END, SUMMARY_START, DailyNotes

log = logging.getLogger(__name__)

__all__ = ["summarise_day", "render_summary", "apply_summary", "run_nightly", "extract_todos"]

_STOPWORDS = {
    "about", "after", "again", "against", "already", "also", "although", "always",
    "and", "another", "any", "anything", "are", "around", "because", "been",
    "before", "being", "between", "both", "but", "can", "could", "did", "does",
    "doing", "done", "down", "each", "even", "ever", "every", "for", "from",
    "get", "gets", "getting", "going", "had", "has", "have", "here", "his",
    "how", "into", "its", "just", "kind", "like", "make", "makes", "many",
    "maybe", "might", "more", "most", "much", "must", "need", "not", "now",
    "off", "one", "only", "other", "our", "out", "over", "own", "really",
    "same", "say", "says", "see", "should", "since", "some", "something",
    "still", "such", "than", "that", "the", "their", "them", "then", "there",
    "these", "they", "thing", "things", "think", "this", "those", "though",
    "through", "thus", "too", "under", "until", "use", "used", "very", "was",
    "way", "well", "were", "what", "when", "where", "which", "while", "who",
    "why", "will", "with", "would", "you", "your",
}

_TODO_PATTERNS = (
    r"\bi should\b",
    r"\bi need to\b",
    r"\bneed to\b",
    r"\bremind me to\b",
    r"\bremember to\b",
    r"\bto ?do\b",
    r"\bfollow up\b",
    r"\bcheck (?:on|out|whether|if)\b",
    r"\blook (?:up|into)\b",
    r"\bworth (?:pairing|reading|trying|doing)\b",
    r"\bnext step\b",
    r"\blet's\b",
    r"\bwant to\b",
)
_TODO_RE = re.compile("|".join(_TODO_PATTERNS), re.IGNORECASE)


def keywords(text: str, *, limit: int = 8) -> list[str]:
    """Content words, longest-and-most-frequent first."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", text.lower())
    counts = Counter(t for t in tokens if t not in _STOPWORDS and len(t) > 3)
    return [word for word, _ in counts.most_common(limit)]


def extract_todos(transcripts: Sequence[str]) -> list[str]:
    """Sentences phrased as an intention, deduplicated, order preserved."""
    todos: list[str] = []
    seen: set[str] = set()
    for transcript in transcripts:
        for sentence in re.split(r"(?<=[.!?])\s+", transcript.strip()):
            sentence = " ".join(sentence.split())
            if not sentence or not _TODO_RE.search(sentence):
                continue
            key = sentence.lower().rstrip(".")
            if key in seen:
                continue
            seen.add(key)
            todos.append(sentence.rstrip("."))
    return todos


def _bullet(sidecar: dict) -> str:
    """One summary bullet: what was said, and where it was said about."""
    transcript = " ".join(str(sidecar.get("transcript", "")).split())
    if len(transcript) > 180:
        transcript = transcript[:179].rstrip() + "…"
    source = ""
    browser = sidecar.get("browser") or {}
    url = browser.get("url") or ""
    if url:
        from urllib.parse import urlsplit

        host = urlsplit(url).netloc
        source = f" ({host})" if host else ""
    elif sidecar.get("app"):
        source = f" ({sidecar['app'].get('name', '')})"
    return f"{transcript}{source}"


def summarise_day(sidecars: Sequence[dict], *, max_bullets: int = 6) -> dict:
    """Heuristic summary: representative bullets, to-dos, and keywords.

    Bullets favour the longest notes — a two-word aside is rarely the point of
    the day — but keep chronological order so the summary reads as a narrative.
    """
    transcripts = [str(s.get("transcript", "")) for s in sidecars]
    ranked = sorted(
        range(len(sidecars)),
        key=lambda i: len(transcripts[i]),
        reverse=True,
    )[:max_bullets]
    bullets = [_bullet(sidecars[i]) for i in sorted(ranked)]
    urls = sorted({(s.get("browser") or {}).get("url", "") for s in sidecars} - {""})
    return {
        "count": len(sidecars),
        "bullets": bullets,
        "todos": extract_todos(transcripts),
        "keywords": keywords(" ".join(transcripts)),
        "urls": urls,
    }


def related_days(
    notes: DailyNotes,
    day: date,
    summary: dict,
    *,
    lookback_days: int = 14,
    min_shared_keywords: int = 2,
) -> list[tuple[date, str]]:
    """Earlier days sharing a URL or at least two keywords with this one."""
    today_keywords = set(summary.get("keywords", []))
    today_urls = {u for u in summary.get("urls", []) if u}
    found: list[tuple[date, str]] = []
    for offset in range(1, lookback_days + 1):
        other = day - timedelta(days=offset)
        sidecars = notes.sidecars(other)
        if not sidecars:
            continue
        other_summary = summarise_day(sidecars)
        shared_urls = today_urls & {u for u in other_summary["urls"] if u}
        shared_keywords = today_keywords & set(other_summary["keywords"])
        if shared_urls:
            found.append((other, f"same source: {sorted(shared_urls)[0]}"))
        elif len(shared_keywords) >= min_shared_keywords:
            found.append((other, ", ".join(sorted(shared_keywords)[:3])))
    return found


def render_summary(
    day: date,
    summary: dict,
    related: Sequence[tuple[date, str]] = (),
) -> str:
    """Render the marked summary block."""
    lines = [SUMMARY_START, "", "## Summary", ""]
    if not summary["count"]:
        lines += ["_No notes captured._", ""]
    else:
        noun = "note" if summary["count"] == 1 else "notes"
        lines.append(f"_{summary['count']} {noun}._")
        lines.append("")
        lines += [f"- {bullet}" for bullet in summary["bullets"]]
        lines.append("")
    if summary.get("todos"):
        lines += ["### To-dos", ""]
        lines += [f"- [ ] {todo}" for todo in summary["todos"]]
        lines.append("")
    if related:
        lines += ["### Related", ""]
        lines += [f"- [{other.isoformat()}]({other.isoformat()}.md) — {why}" for other, why in related]
        lines.append("")
    lines += [SUMMARY_END, ""]
    return "\n".join(lines)


def apply_summary(document: str, block: str) -> str:
    """Insert or replace the summary block. Idempotent by construction."""
    start = document.find(SUMMARY_START)
    end = document.find(SUMMARY_END)
    if start != -1 and end != -1 and end > start:
        tail = document[end + len(SUMMARY_END):].lstrip("\n")
        # The same separator the insert path below uses, so re-running is a
        # fixed point rather than eating a blank line each time.
        return document[:start] + block + "\n" + tail

    lines = document.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("# "):
        insert_at = 1
        while insert_at < len(lines) and not lines[insert_at].strip():
            insert_at += 1
    head = "".join(lines[:insert_at])
    tail = "".join(lines[insert_at:])
    if head and not head.endswith("\n"):
        head += "\n"
    return f"{head}\n{block}\n{tail}" if head else f"{block}\n{tail}"


def llm_summary(summary: dict, config: NightlyConfig) -> dict:
    """Optionally refine the heuristic summary with a model.

    ``backend = "none"`` (the default) returns the heuristic summary unchanged
    and makes no network call. Other backends are opt-in; a failure falls back
    to the heuristics rather than losing the pass.
    """
    if config.backend == "none":
        return summary
    try:
        if config.backend == "local":
            from .nightly_backends import local_refine  # type: ignore[import-not-found]

            return local_refine(summary, config)
        if config.backend == "api":
            from .nightly_backends import api_refine  # type: ignore[import-not-found]

            return api_refine(summary, config)
    except Exception as exc:  # noqa: BLE001
        log.warning("nightly backend %s failed, using heuristics: %s", config.backend, exc)
        return summary
    log.warning("unknown nightly backend %r; using heuristics", config.backend)
    return summary


def run_nightly(config: Config, day: date | None = None) -> Path | None:
    """Summarise one day in place. Returns the file written, or ``None``."""
    day = day or date.today()
    notes = DailyNotes(config.notes_dir)
    path = notes.path_for(day)
    sidecars = notes.sidecars(day)
    if not path.exists() and not sidecars:
        log.info("nothing to summarise for %s", day)
        return None

    summary = llm_summary(summarise_day(sidecars), config.nightly)
    block = render_summary(day, summary, related_days(notes, day, summary))
    path.parent.mkdir(parents=True, exist_ok=True)
    # Re-read under the lock: a note captured while we were summarising must
    # survive the rewrite, even if it is not in this summary.
    with notes_lock(config.notes_dir):
        document = notes.read_day(day) or f"# {day.isoformat()}\n\n"
        path.write_text(apply_summary(document, block), encoding="utf-8")
    return path
