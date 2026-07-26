"""Fetch and cache the corpus from Wikisource.

Deliberately boring: rendered text, HTML stripped, throttled, cached on disk so
the corpus is fixed after the first run and every later analysis reads bytes
rather than the network. The cached files are the corpus of record.

Run:
    uv run --no-sync python -m experiments.date_cut_retrodiction.fetch
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.date_cut_retrodiction.corpus import SOURCES, SourceSpec


__all__ = ["fetch_all", "load_document", "DATA_DIR"]

API: Final[str] = "https://en.wikisource.org/w/api.php"
UA: Final[str] = "rde-research/0.1 (deletion-repair retrodiction; jawaun@generalintelligencecompany.com)"
THROTTLE_S: Final[float] = 2.0
DATA_DIR: Final[Path] = Path(__file__).resolve().parent / "data"


def _api(params: dict[str, str]) -> dict[str, Any]:
    payload = {**params, "format": "json", "formatversion": "2"}
    url = f"{API}?{urllib.parse.urlencode(payload)}"
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=60) as handle:
        return json.loads(handle.read().decode("utf-8"))


#: Wikisource navigation chrome. This is not incidental noise -- the header
#: template links every one of these papers to ``Portal:Relativity``, a
#: category that did not exist when they were written. Left in, the corpus
#: would hand the extractor the answer in the first line of every document.
_CHROME_CLASSES: Final[tuple[str, ...]] = (
    "ws-header",
    "headertemplate",
    "ws-noexport",
    "noprint",
    "searchaux",
    "catlinks",
    "printfooter",
    "sisitem",
    "mw-editsection",
    "reflist",
    "references",
)

#: The Proofread-Page extension wraps the transcribed scan in this container.
#: When present it *is* the source text, and nothing outside it is.
_BODY_CLASS: Final[str] = "prp-pages-output"

_TAG_RE: Final[re.Pattern[str]] = re.compile(r"<(/?)(\w+)([^>]*)>")


def _extract_container(markup: str, class_name: str) -> str | None:
    """Return the inner HTML of the first ``<div>`` carrying ``class_name``.

    A depth-tracking scan rather than a regex, because these containers nest.
    """
    opener = re.search(rf'<div[^>]*class="[^"]*\b{class_name}\b[^"]*"[^>]*>', markup)
    if opener is None:
        return None
    start = opener.end()
    depth = 1
    for match in _TAG_RE.finditer(markup, start):
        if match.group(2).lower() != "div":
            continue
        depth += -1 if match.group(1) else 1
        if depth == 0:
            return markup[start : match.start()]
    return markup[start:]


def _drop_chrome(markup: str) -> str:
    for class_name in _CHROME_CLASSES:
        while True:
            opener = re.search(
                rf'<(div|table|ul|li|span|sup)[^>]*class="[^"]*\b{class_name}\b[^"]*"[^>]*>',
                markup,
            )
            if opener is None:
                break
            tag = opener.group(1).lower()
            depth, end = 1, len(markup)
            for match in _TAG_RE.finditer(markup, opener.end()):
                if match.group(2).lower() != tag:
                    continue
                depth += -1 if match.group(1) else 1
                if depth == 0:
                    end = match.end()
                    break
            markup = markup[: opener.start()] + " " + markup[end:]
    return markup


def _strip_html(markup: str) -> str:
    # <sup> carries footnote markers that fragment sentences; tables are
    # numeric data that no proposition should be anchored to.
    markup = re.sub(r"(?s)<(script|style|table|sup)\b.*?</\1>", " ", markup)
    markup = re.sub(r"(?s)<!--.*?-->", " ", markup)
    markup = re.sub(r"<[^>]+>", " ", markup)
    text = html.unescape(markup)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()


def _fetch_plain(title: str) -> tuple[str, str]:
    """Return ``(resolved_title, plain_text)``, following one redirect.

    Chrome is removed *structurally*, before any text extraction. A keyword
    filter would be the wrong tool: "special theory" appears innocently in
    Larmor 1897 ("any special theory of the constitution of matter"), so
    scrubbing by vocabulary would corrupt the source while still missing
    chrome that happens to use period-appropriate words.
    """
    parsed = _api({"action": "parse", "page": title, "prop": "text", "redirects": "1"})
    resolved = parsed["parse"]["title"]
    markup = parsed["parse"]["text"]
    body = _extract_container(markup, _BODY_CLASS)
    return resolved, _strip_html(_drop_chrome(body if body is not None else markup))


def fetch_all(
    specs: Sequence[SourceSpec] = SOURCES,
    *,
    data_dir: Path = DATA_DIR,
    refresh: bool = False,
) -> dict[str, dict[str, Any]]:
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, Any]] = {}

    for spec in specs:
        path = data_dir / f"{spec.doc_id}.txt"
        if path.exists() and not refresh:
            text = path.read_text(encoding="utf-8")
            resolved = spec.wikisource_title
        else:
            resolved, text = _fetch_plain(spec.wikisource_title)
            path.write_text(text, encoding="utf-8")
            time.sleep(THROTTLE_S)

        manifest[spec.doc_id] = {
            "doc_id": spec.doc_id,
            "author": spec.author,
            "year": spec.year,
            "provenance_risk": spec.provenance_risk,
            "wikisource_title": spec.wikisource_title,
            "resolved_title": resolved,
            "note": spec.note,
            "chars": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
        print(f"  {spec.year}  {len(text):7d} chars  {spec.doc_id}")

    (data_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def load_document(doc_id: str, *, data_dir: Path = DATA_DIR) -> str:
    return (data_dir / f"{doc_id}.txt").read_text(encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch the pre-1905 corpus.")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args(argv)

    manifest = fetch_all(data_dir=args.data_dir, refresh=args.refresh)
    total = sum(entry["chars"] for entry in manifest.values())
    print(f"\n{len(manifest)} documents, {total:,} chars -> {args.data_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
