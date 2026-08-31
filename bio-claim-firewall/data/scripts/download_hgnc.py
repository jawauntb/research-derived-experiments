#!/usr/bin/env python3
"""Download and convert the HGNC complete gene set into the frozen pilot-world schema.

Source: HGNC (HUGO Gene Nomenclature Committee) complete set TSV, mirrored by
EBI at the URL below. License: CC0 1.0 (Public Domain), per
https://www.genenames.org/about/license/.

Output: data/ontology_snapshots/hgnc.2026_pilot/
  curies.txt    one `HGNC:<id>` per line, one per approved gene record
  labels.jsonl  {"curie": "HGNC:<id>", "label": "<approved symbol>"}
  aliases.jsonl {"deprecated": "HGNC:<old_id>", "canonical": "HGNC:<new_id>"}
                for HGNC ids that were merged into a still-current id
                (from HGNC's own withdrawn.txt; ids withdrawn with no
                successor are NOT included -- there is no canonical to
                point to, so no alias row is authored for them)

No sampling: the complete set (~45k rows) is small on disk (a few MB) so it
is kept in full rather than subsampled, per the "small ontology snapshot"
brief -- HGNC is comfortably small already.
"""

from __future__ import annotations

import csv
import io
import json
import re
from pathlib import Path

from _common import RAW_DIR, log, now_iso, write_license_text, write_ontology_manifest

SOURCE = "hgnc.2026_pilot"
COMPLETE_SET_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"
WITHDRAWN_URL = (
    "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/withdrawn.txt"
)
LICENSE_TAG = "CC0-1.0"
LICENSE_URL = "https://www.genenames.org/about/license/"

OUT_DIR = Path(__file__).resolve().parent.parent / "ontology_snapshots" / SOURCE
RAW_OUT = RAW_DIR / SOURCE


def _fetch_text(url: str) -> str:
    import urllib.request

    from _common import USER_AGENT

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return resp.read().decode("utf-8")


def main() -> int:
    retrieved_at = now_iso()
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log(f"fetching {COMPLETE_SET_URL}")
    complete_text = _fetch_text(COMPLETE_SET_URL)
    (RAW_OUT / "hgnc_complete_set.txt").write_text(complete_text, encoding="utf-8")

    log(f"fetching {WITHDRAWN_URL}")
    withdrawn_text = _fetch_text(WITHDRAWN_URL)
    (RAW_OUT / "withdrawn.txt").write_text(withdrawn_text, encoding="utf-8")

    reader = csv.DictReader(io.StringIO(complete_text), delimiter="\t")
    curies: list[str] = []
    labels: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in reader:
        curie = row.get("hgnc_id", "").strip()
        symbol = row.get("symbol", "").strip()
        if not curie or not symbol or curie in seen:
            continue
        seen.add(curie)
        curies.append(curie)
        labels.append({"curie": curie, "label": symbol})

    # withdrawn.txt: HGNC_ID  STATUS  WITHDRAWN_SYMBOL  MERGED_INTO_REPORT(S)
    # Only rows with a MERGED_INTO_REPORT(S) value carry a live successor id
    # (format: "HGNC:5|SYMBOL|Approved", possibly multiple '|'-joined groups
    # separated by ", "). We take the first successor id listed.
    aliases: list[dict[str, str]] = []
    withdrawn_reader = csv.DictReader(io.StringIO(withdrawn_text), delimiter="\t")
    for row in withdrawn_reader:
        old_id = (row.get("HGNC_ID") or "").strip()
        merged = (
            row.get("MERGED_INTO_REPORT(S) (i.e HGNC_ID|SYMBOL|STATUS)") or ""
        ).strip()
        if not old_id or not merged:
            continue
        first_group = merged.split(",")[0].strip()
        m = re.match(r"^(HGNC:\d+)\|", first_group)
        if not m:
            continue
        new_id = m.group(1)
        if new_id in seen:  # only alias to ids that actually exist in this snapshot
            aliases.append({"deprecated": old_id, "canonical": new_id})

    (OUT_DIR / "curies.txt").write_text("\n".join(curies) + "\n", encoding="utf-8")
    with (OUT_DIR / "labels.jsonl").open("w", encoding="utf-8") as f:
        for row in labels:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")
    with (OUT_DIR / "aliases.jsonl").open("w", encoding="utf-8") as f:
        for row in aliases:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")

    log(f"{len(curies)} approved HGNC ids, {len(aliases)} merged-alias rows")

    write_license_text(
        SOURCE,
        "HGNC data license: Creative Commons Public Domain (CC0)",
        LICENSE_URL,
        "HGNC (HUGO Gene Nomenclature Committee) data files are released under CC0 1.0 "
        "(Public Domain Dedication). See data/LICENSES/CC0-1.0.txt for the full legal text, "
        f"and {LICENSE_URL} for HGNC's own license statement.",
    )

    write_ontology_manifest(
        source=SOURCE,
        source_url=f"{COMPLETE_SET_URL} ; {WITHDRAWN_URL}",
        retrieved_at=retrieved_at,
        license_tag=LICENSE_TAG,
        preprocessing_cmd=(
            "python3 data/scripts/download_hgnc.py -- parses hgnc_complete_set.txt "
            "(tab-separated, full unsampled set) into curies.txt (hgnc_id) + "
            "labels.jsonl (hgnc_id -> symbol); parses withdrawn.txt into "
            "aliases.jsonl (deprecated hgnc_id -> canonical hgnc_id) for entries "
            "with a live MERGED_INTO_REPORT(S) successor only."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
