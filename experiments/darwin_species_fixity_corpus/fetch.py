"""Fetch and cache the Darwin / species-fixity corpus from Wikisource.

The fetch logic is identical to ``experiments/date_cut_retrodiction/fetch.py``
-- the container extraction, chrome removal, HTML stripping, and throttling
were tuned once against Wikisource's Proofread-Page templates and are imported
as-is so this corpus shares provenance with the DCR electrodynamics corpus and
the Lavoisier chemistry corpus. The only per-package concerns are the source
list, the data directory, and a committed summary of what fetched vs. what did
not.

Run:
    uv run --no-sync python -m experiments.darwin_species_fixity_corpus.fetch
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Final, Sequence

from experiments.darwin_species_fixity_corpus.corpus import SOURCES, SourceSpec
from experiments.date_cut_retrodiction.fetch import THROTTLE_S, _fetch_plain


__all__ = ["fetch_all", "load_document", "DATA_DIR", "RESULTS_DIR"]


DATA_DIR: Final[Path] = Path(__file__).resolve().parent / "data"
RESULTS_DIR: Final[Path] = Path(__file__).resolve().parent / "results"
#: A cached text below this many characters is not considered substantive.
#: Origin (1859) chapters run 20k-40k characters after HTML stripping; Malthus
#: chapters run 8k-20k; the shortest Zoonomia section (I.Preface) is about
#: 3k. Anything below 2000 is a Wikisource stub, an address block, or a page
#: that transcludes an untranscribed scan. Matches the Lavoisier corpus's
#: threshold so both packages fail on the same regressions.
MIN_SUBSTANTIVE_CHARS: Final[int] = 2_000


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
    """

    data_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, Any]] = {}

    for spec in specs:
        path = data_dir / f"{spec.doc_id}.txt"
        if path.exists() and not refresh:
            text = path.read_text(encoding="utf-8")
            resolved = spec.wikisource_title
            fetched = False
        else:
            resolved, text = _fetch_plain(spec.wikisource_title)
            path.write_text(text, encoding="utf-8")
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
        }
        marker = "*" if spec.oracle else ("!" if spec.provenance_risk else " ")
        source = "network" if fetched else "cache"
        print(f"  {marker} {spec.year}  {chars:>7d} chars  ({source})  {spec.doc_id}")

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
    pre_1859 = [e for e in entries if not e["oracle"]]
    pre_1859_substantive = [e for e in pre_1859 if e["substantive"]]
    pre_1859_no_leak = [
        e for e in pre_1859_substantive if not e["provenance_risk"]
    ]
    oracle = [e for e in entries if e["oracle"]]
    summary = {
        "kind": "darwin species-fixity corpus fetch summary",
        "n_sources": len(entries),
        "n_substantive": len(substantive),
        "n_thin": len(thin),
        "n_pre_1859_sources": len(pre_1859),
        "n_pre_1859_substantive": len(pre_1859_substantive),
        "n_pre_1859_substantive_no_leak_risk": len(pre_1859_no_leak),
        "n_oracle_sources": len(oracle),
        "min_substantive_chars": MIN_SUBSTANTIVE_CHARS,
        "total_chars": total_chars,
        "total_pre_1859_chars": sum(e["chars"] for e in pre_1859),
        "total_pre_1859_no_leak_chars": sum(e["chars"] for e in pre_1859_no_leak),
        "total_oracle_chars": sum(e["chars"] for e in oracle),
        "documents": entries,
    }
    summary_path = results_dir / "fetch_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fetch the Darwin / species-fixity corpus.",
    )
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args(argv)

    manifest = fetch_all(data_dir=args.data_dir, refresh=args.refresh)
    total = sum(entry["chars"] for entry in manifest.values())
    summary_path = write_summary(manifest, results_dir=args.results_dir)

    thin = [e for e in manifest.values() if not e["substantive"]]
    print(f"\n{len(manifest)} documents, {total:,} chars -> {args.data_dir}")
    if thin:
        print(f"WARNING: {len(thin)} source(s) below {MIN_SUBSTANTIVE_CHARS} chars:")
        for entry in thin:
            print(f"  {entry['doc_id']}  {entry['chars']} chars")
    print(f"summary -> {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
