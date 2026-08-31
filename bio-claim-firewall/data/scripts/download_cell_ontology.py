#!/usr/bin/env python3
"""Download the Cell Ontology (CL) basic release and convert it to the pilot-world schema.

Source: `cl-basic.obo`, the OBO Foundry PURL for the Cell Ontology's basic
(no cross-ontology imports) release. License: CC BY 4.0, per the
`terms:license` property_value embedded in the OBO file header itself
(https://obofoundry.org/ontology/cl.html confirms the same).

Output: data/ontology_snapshots/cellontology.2026_pilot/
  curies.txt         one `CL:<id>` per line, for every [Term] stanza with a
                      CL: id (obsolete terms excluded)
  labels.jsonl        {"curie": "CL:<id>", "label": "<name>"}
  cell_ontology.jsonl {"curie": "CL:<id>", "ancestors": [...]} -- the is_a
                      closure computed to 3 levels deep, matching the
                      loader's expectations (evidence/loader.py reads this
                      file's `ancestors` field verbatim into
                      SnapshotBundle.ancestor_map; R-CTX-02 walks it).

No sampling: cl-basic.obo (~3.3MB, ~3k terms) is already small.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from _common import (
    RAW_DIR,
    fetch_bytes,
    log,
    now_iso,
    write_license_text,
    write_ontology_manifest,
)

SOURCE = "cellontology.2026_pilot"
CL_URL = "https://purl.obolibrary.org/obo/cl/cl-basic.obo"
LICENSE_TAG = "CC-BY-4.0"
LICENSE_URL = "https://obofoundry.org/ontology/cl.html"
ANCESTOR_DEPTH = 3

OUT_DIR = Path(__file__).resolve().parent.parent / "ontology_snapshots" / SOURCE
RAW_OUT = RAW_DIR / SOURCE

_TERM_STANZA_RE = re.compile(r"^\[Term\]\n(.*?)(?=\n\[|\Z)", re.S | re.M)
_ID_RE = re.compile(r"^id:\s*(CL:\d+)\s*$", re.M)
_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.M)
_IS_A_RE = re.compile(r"^is_a:\s*(CL:\d+)\b", re.M)
_OBSOLETE_RE = re.compile(r"^is_obsolete:\s*true\s*$", re.M)


def _parse_obo(text: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    names: dict[str, str] = {}
    parents: dict[str, list[str]] = {}
    for stanza_match in _TERM_STANZA_RE.finditer(text):
        stanza = stanza_match.group(1)
        if _OBSOLETE_RE.search(stanza):
            continue
        id_match = _ID_RE.search(stanza)
        if not id_match:
            continue
        curie = id_match.group(1)
        name_match = _NAME_RE.search(stanza)
        names[curie] = name_match.group(1) if name_match else curie
        parents[curie] = _IS_A_RE.findall(stanza)
    return names, parents


def _ancestors_to_depth(
    curie: str, parents: dict[str, list[str]], depth: int
) -> list[str]:
    """BFS over is_a edges, unique CURIEs, up to `depth` levels, closest-first."""
    seen: set[str] = set()
    ordered: list[str] = []
    frontier = [curie]
    for _level in range(depth):
        next_frontier: list[str] = []
        for node in frontier:
            for parent in parents.get(node, []):
                if parent not in seen:
                    seen.add(parent)
                    ordered.append(parent)
                    next_frontier.append(parent)
        frontier = next_frontier
        if not frontier:
            break
    return ordered


def main() -> int:
    retrieved_at = now_iso()
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log(f"fetching {CL_URL}")
    obo_bytes = fetch_bytes(CL_URL, timeout=90)
    (RAW_OUT / "cl-basic.obo").write_bytes(obo_bytes)
    text = obo_bytes.decode("utf-8", errors="replace")

    names, parents = _parse_obo(text)
    curies = sorted(names)
    if not curies:
        raise SystemExit(
            "parsed zero CL terms from cl-basic.obo -- refusing to write an empty snapshot"
        )

    (OUT_DIR / "curies.txt").write_text("\n".join(curies) + "\n", encoding="utf-8")
    with (OUT_DIR / "labels.jsonl").open("w", encoding="utf-8") as f:
        for curie in curies:
            f.write(json.dumps({"curie": curie, "label": names[curie]}, sort_keys=True))
            f.write("\n")
    with (OUT_DIR / "cell_ontology.jsonl").open("w", encoding="utf-8") as f:
        for curie in curies:
            ancestors = _ancestors_to_depth(curie, parents, ANCESTOR_DEPTH)
            f.write(
                json.dumps({"curie": curie, "ancestors": ancestors}, sort_keys=True)
            )
            f.write("\n")

    log(f"{len(curies)} CL terms parsed (is_a closure depth={ANCESTOR_DEPTH})")

    write_license_text(
        SOURCE,
        "Cell Ontology (CL) license: Creative Commons Attribution 4.0 International",
        LICENSE_URL,
        "The Cell Ontology's own OBO file header declares "
        "`property_value: terms:license http://creativecommons.org/licenses/by/4.0/`. "
        "See data/LICENSES/CC-BY-4.0.txt for the full legal text.",
    )

    write_ontology_manifest(
        source=SOURCE,
        source_url=CL_URL,
        retrieved_at=retrieved_at,
        license_tag=LICENSE_TAG,
        preprocessing_cmd=(
            "python3 data/scripts/download_cell_ontology.py -- parses [Term] stanzas from "
            "cl-basic.obo with a stdlib regex OBO parser (no pronto/owlready2 dependency); "
            "drops is_obsolete=true stanzas; writes curies.txt + labels.jsonl (id -> name) + "
            f"cell_ontology.jsonl (is_a closure via BFS, depth={ANCESTOR_DEPTH})."
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
