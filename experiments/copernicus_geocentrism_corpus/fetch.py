"""Fetch and cache the Copernicus / geocentric-priority corpus from Wikisource.

The fetch logic is identical to ``experiments/date_cut_retrodiction/fetch.py``
- the container extraction, chrome removal, HTML stripping, and throttling
were tuned once against Wikisource's Proofread-Page templates and are
imported as-is so all four corpora (DCR, Lavoisier, Darwin, Copernicus)
share provenance. The only per-package concerns are the source list, the
data directory, tolerant handling of missing pages (necessary here because
the Copernicus oracle is not on English Wikisource; see ``corpus.py``), and
a committed summary of what fetched vs. what did not.

Run:
    uv run --no-sync python -m experiments.copernicus_geocentrism_corpus.fetch
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.copernicus_geocentrism_corpus.corpus import SOURCES, SourceSpec
from experiments.date_cut_retrodiction.fetch import THROTTLE_S, _fetch_plain


__all__ = ["fetch_all", "load_document", "DATA_DIR", "RESULTS_DIR"]


DATA_DIR: Final[Path] = Path(__file__).resolve().parent / "data"
RESULTS_DIR: Final[Path] = Path(__file__).resolve().parent / "results"
#: A cached text below this many characters is not considered substantive.
#: Matches the Darwin and Lavoisier thresholds so all three corpora fail on
#: the same regressions. Aristotle's *On the Heavens* Books I-IV run 33k-77k
#: characters after HTML stripping; Maimonides's *Guide* Part I is ~450k;
#: Chaucer's *Astrolabe* is ~93k. Anything below 2000 is a Wikisource stub,
#: a page that transcludes an untranscribed scan, or an oracle-failed fetch.
MIN_SUBSTANTIVE_CHARS: Final[int] = 2_000


def _try_fetch_plain(title: str) -> tuple[str, str, str | None]:
    """Return ``(resolved_title, plain_text, error_message)``.

    ``error_message`` is ``None`` on success and a short human-readable string
    when Wikisource returned an error (e.g. missing page). The Copernicus
    corpus needs this softer semantics because *De revolutionibus* Book I is
    not transcribed on English Wikisource; the fetch is expected to fail and
    the failure must be recorded, not raised.
    """

    try:
        resolved, text = _fetch_plain(title)
        return resolved, text, None
    except Exception as exc:  # includes KeyError on parsed["parse"] when the
        # Wikisource API returns {"error": ...} for a missing page, and
        # urllib errors for transport failures. The error message is preserved
        # verbatim so the fetch summary can distinguish "page missing" from
        # "network flake".
        return title, "", f"{type(exc).__name__}: {exc}"


def fetch_all(
    specs: Sequence[SourceSpec] = SOURCES,
    *,
    data_dir: Path = DATA_DIR,
    refresh: bool = False,
) -> dict[str, dict[str, Any]]:
    """Fetch every source, cache to ``data_dir``, and return a manifest.

    The cache is the corpus of record: on a repeat run every source that is
    already on disk is loaded from disk. Set ``refresh=True`` to force a
    re-fetch, but that changes the corpus of record and should be paired with
    a fresh preregistration for any downstream test.

    Sources whose Wikisource page is missing (chiefly the oracle) do not
    raise; they cache to an empty file and their fetch summary carries the
    error string. Downstream analyses check ``substantive`` and
    ``fetch_error`` before using a document.
    """

    data_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, Any]] = {}

    for spec in specs:
        path = data_dir / f"{spec.doc_id}.txt"
        error_path = data_dir / f"{spec.doc_id}.error"
        if path.exists() and not refresh:
            text = path.read_text(encoding="utf-8")
            resolved = spec.wikisource_title
            error = error_path.read_text(encoding="utf-8").strip() if error_path.exists() else None
            fetched = False
        else:
            resolved, text, error = _try_fetch_plain(spec.wikisource_title)
            path.write_text(text, encoding="utf-8")
            if error is not None:
                error_path.write_text(error + "\n", encoding="utf-8")
            elif error_path.exists():
                error_path.unlink()
            fetched = True
            time.sleep(THROTTLE_S)

        chars = len(text)
        manifest[spec.doc_id] = {
            "doc_id": spec.doc_id,
            "author": spec.author,
            "year": spec.year,
            "oracle": spec.oracle,
            "provenance_risk": spec.provenance_risk,
            "wikisource_title": spec.wikisource_title,
            "resolved_title": resolved,
            "note": spec.note,
            "chars": chars,
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "substantive": chars >= MIN_SUBSTANTIVE_CHARS,
            "fetch_error": error,
        }
        if error is not None:
            marker = "X"
        elif spec.oracle:
            marker = "*"
        elif spec.provenance_risk:
            marker = "!"
        else:
            marker = " "
        source = "network" if fetched else "cache"
        print(f"  {marker} {spec.year:>5d}  {chars:>7d} chars  ({source})  {spec.doc_id}")
        if error is not None:
            print(f"    fetch error: {error}")

    (data_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def load_document(doc_id: str, *, data_dir: Path = DATA_DIR) -> str:
    """Load a cached document's plain text. Raises if the fetch was not run."""

    return (data_dir / f"{doc_id}.txt").read_text(encoding="utf-8")


def write_summary(
    manifest: dict[str, dict[str, Any]],
    *,
    results_dir: Path = RESULTS_DIR,
) -> Path:
    """Write a committed summary of what fetched vs. what fell short.

    The cached text files live under ``data/`` and are gitignored (per the
    root ``.gitignore``'s ``data/`` rule), so the summary is the only in-repo
    trace of what the fetch produced. It carries a per-document character
    count and sha256, enough to detect drift on a re-fetch.
    """

    results_dir.mkdir(parents=True, exist_ok=True)
    entries = sorted(manifest.values(), key=lambda e: (e["oracle"], e["year"], e["doc_id"]))
    total_chars = sum(e["chars"] for e in entries)
    substantive = [e for e in entries if e["substantive"]]
    thin = [e for e in entries if not e["substantive"]]
    failed = [e for e in entries if e.get("fetch_error") is not None]
    pre_1543 = [e for e in entries if not e["oracle"]]
    pre_1543_substantive = [e for e in pre_1543 if e["substantive"]]
    pre_1543_no_leak = [e for e in pre_1543_substantive if not e["provenance_risk"]]
    oracle = [e for e in entries if e["oracle"]]
    oracle_substantive = [e for e in oracle if e["substantive"]]
    summary = {
        "kind": "copernicus geocentric-priority corpus fetch summary",
        "n_sources": len(entries),
        "n_substantive": len(substantive),
        "n_thin": len(thin),
        "n_fetch_errors": len(failed),
        "n_pre_1543_sources": len(pre_1543),
        "n_pre_1543_substantive": len(pre_1543_substantive),
        "n_pre_1543_substantive_no_leak_risk": len(pre_1543_no_leak),
        "n_oracle_sources": len(oracle),
        "n_oracle_substantive": len(oracle_substantive),
        "min_substantive_chars": MIN_SUBSTANTIVE_CHARS,
        "total_chars": total_chars,
        "total_pre_1543_chars": sum(e["chars"] for e in pre_1543),
        "total_pre_1543_no_leak_chars": sum(e["chars"] for e in pre_1543_no_leak),
        "total_oracle_chars": sum(e["chars"] for e in oracle),
        "documents": entries,
    }
    summary_path = results_dir / "fetch_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch the Copernicus / geocentric-priority corpus.",
    )
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args(argv)

    manifest = fetch_all(data_dir=args.data_dir, refresh=args.refresh)
    total = sum(entry["chars"] for entry in manifest.values())
    summary_path = write_summary(manifest, results_dir=args.results_dir)

    thin = [e for e in manifest.values() if not e["substantive"]]
    failed = [e for e in manifest.values() if e.get("fetch_error") is not None]
    print(f"\n{len(manifest)} documents, {total:,} chars -> {args.data_dir}")
    if failed:
        print(f"WARNING: {len(failed)} source(s) failed to fetch:")
        for entry in failed:
            print(f"  {entry['doc_id']}: {entry['fetch_error']}")
    if thin:
        print(f"WARNING: {len(thin)} source(s) below {MIN_SUBSTANTIVE_CHARS} chars:")
        for entry in thin:
            print(f"  {entry['doc_id']}  {entry['chars']} chars")
    print(f"summary -> {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
