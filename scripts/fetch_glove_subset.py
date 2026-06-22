#!/usr/bin/env python3
"""Fetch GloVe 6B and vendor ONLY the word types Prediction 3 needs.

Pre-registration: docs/external_contact_preregistration.md (Prediction 3).
Runbook:          docs/external_contact_runbook.md

This is a laptop-runnable fetch helper for the externally-blocked P3 work. The
research container has no network egress (Stanford / HuggingFace / PyPI return
403), so this cannot run there. On a machine WITH network it:

  1. downloads GloVe 6B (a ~822 MB zip) into a gitignored tmp directory,
  2. unzips the requested dimensionality file(s) (default 300d, optionally 100d),
  3. extracts ONLY the word types referenced by the lab's 24-concept set
     (experiments/concept_geometry/concept_set.json `label` fields) and its
     paraphrases (concept_paraphrases.json `variants`), tokenized EXACTLY the way
     experiments/external_contact/p3_glove_probe.py does,
  4. writes the tiny subset to experiments/external_contact/p3_glove_subset_<D>d.txt
     (only the named word types ship; the full table stays out of git), and
  5. reports how many of the needed word types were found vs missing.

With `--run` it then invokes the P3 harness on the freshly built subset(s).

Pure standard library only (urllib, zipfile) — no third-party deps, matching the
P3 harness's stdlib discipline.

Example (on the user's laptop):

    python3 scripts/fetch_glove_subset.py --dims 300 100 --run

GloVe source URLs
-----------------
Primary (Stanford):
    https://nlp.stanford.edu/data/glove.6B.zip
HuggingFace mirror fallback (if Stanford is slow / 403):
    # https://huggingface.co/stanfordnlp/glove/resolve/main/glove.6B.zip
Both contain glove.6B.50d.txt / .100d.txt / .200d.txt / .300d.txt at the zip root.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# Primary download (Stanford). The HuggingFace mirror below is a documented
# fallback the user can swap in via --url if Stanford 403s or rate-limits.
GLOVE_URL = "https://nlp.stanford.edu/data/glove.6B.zip"
# HuggingFace mirror fallback (uncomment / pass via --url if Stanford fails):
#   https://huggingface.co/stanfordnlp/glove/resolve/main/glove.6B.zip

CONCEPT_SET = Path("experiments/concept_geometry/concept_set.json")
PARAPHRASES = Path("experiments/concept_geometry/concept_paraphrases.json")
OUT_DIR = Path("experiments/external_contact")
# Gitignored scratch space for the big zip + extracted full tables.
TMP_DIR = Path("tmp/glove")


# ----------------------------------------------------------------------------
# Tokenization — MUST stay byte-for-byte identical to
# experiments/external_contact/p3_glove_probe.py::tokenize so that the vendored
# subset contains exactly the word types the harness will look up.
# ----------------------------------------------------------------------------
def tokenize(text: str) -> list[str]:
    # Drop a leading "label:" gloss prefix if present, keep alphabetic tokens.
    text = text.split(":", 1)[-1] if ":" in text else text
    return [t for t in re.findall(r"[a-zA-Z]+", text.lower())]


def needed_word_types() -> set[str]:
    """All lowercased alphabetic tokens the P3 harness will request.

    Mirrors run_glove() in p3_glove_probe.py: tokenize every concept `label`
    and every paraphrase `variant`.
    """
    concepts = json.loads(CONCEPT_SET.read_text(encoding="utf-8"))
    paraphrases = {
        p["id"]: p["variants"] for p in json.loads(PARAPHRASES.read_text(encoding="utf-8"))
    }
    needed: set[str] = set()
    for c in concepts:
        needed.update(tokenize(c["label"]))
        for v in paraphrases.get(c["id"], []):
            needed.update(tokenize(v))
    return needed


# ----------------------------------------------------------------------------
# Download / unzip
# ----------------------------------------------------------------------------
def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest} already present ({dest.stat().st_size} bytes)")
        return dest
    print(f"[download] {url}\n           -> {dest}")
    # urlretrieve streams to disk; the zip is ~822 MB.
    tmp = dest.with_suffix(dest.suffix + ".part")

    def _progress(block: int, block_size: int, total: int) -> None:
        if total > 0 and block % 256 == 0:
            done = min(block * block_size, total)
            pct = 100.0 * done / total
            sys.stderr.write(f"\r           {done // (1 << 20)} / {total // (1 << 20)} MiB ({pct:.0f}%)")
            sys.stderr.flush()

    urllib.request.urlretrieve(url, tmp, reporthook=_progress)
    sys.stderr.write("\n")
    tmp.replace(dest)
    return dest


def extract_member(zip_path: Path, member: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest} already extracted")
        return dest
    print(f"[unzip] {member} from {zip_path} -> {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if member not in names:
            raise SystemExit(
                f"member {member!r} not in zip; available: {names}"
            )
        with zf.open(member) as src, dest.open("wb") as out:
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
    return dest


# ----------------------------------------------------------------------------
# Subset extraction
# ----------------------------------------------------------------------------
def build_subset(full_txt: Path, needed: set[str], out_path: Path) -> tuple[int, set[str]]:
    """Scan the full GloVe text file once, keep only lines whose word is needed.

    Matches load_glove() in p3_glove_probe.py: a line is `word v1 v2 ... vd`
    split on single spaces; the word is sp[0]. We write the original line
    verbatim so the harness parses it identically.
    """
    found: set[str] = set()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with full_txt.open(encoding="utf-8") as fh, out_path.open("w", encoding="utf-8") as out:
        for line in fh:
            # sp[0] is the word; mirror load_glove's split(" ").
            word = line.rstrip("\n").split(" ", 1)[0]
            if word in needed and word not in found:
                out.write(line if line.endswith("\n") else line + "\n")
                found.add(word)
    missing = needed - found
    print(
        f"[subset] {out_path}: {len(found)}/{len(needed)} needed word types found, "
        f"{len(missing)} missing"
    )
    if missing:
        print(f"[subset] missing word types: {sorted(missing)}")
    return len(found), missing


def run_harness(subset_300: Path | None, subset_100: Path | None) -> int:
    """Invoke the P3 harness on the freshly built subset(s)."""
    if subset_300 is None:
        print("[run] no 300d subset built; nothing to run")
        return 0
    cmd = [
        sys.executable,
        "-m",
        "experiments.external_contact.p3_glove_probe",
        "--glove",
        str(subset_300),
        "--out",
        "artifacts/external_contact/p3_glove.json",
    ]
    if subset_100 is not None:
        cmd += ["--glove2", str(subset_100)]
    print(f"[run] {' '.join(cmd)}")
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--dims",
        type=int,
        nargs="+",
        default=[300],
        choices=[50, 100, 200, 300],
        help="GloVe dimensionalities to extract (default: 300). Use `--dims 300 100` "
        "to also build the 100d subset needed for the P3c cross-model RSA.",
    )
    parser.add_argument("--url", default=GLOVE_URL, help="GloVe zip URL (override to use the HF mirror).")
    parser.add_argument("--tmp", type=Path, default=TMP_DIR, help="Gitignored scratch dir for the zip / full tables.")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="Where to write the vendored subset(s).")
    parser.add_argument("--run", action="store_true", help="After building, invoke the P3 harness on the subset(s).")
    parser.add_argument(
        "--from-zip",
        type=Path,
        default=None,
        help="Use an already-downloaded glove.6B.zip instead of fetching.",
    )
    args = parser.parse_args()

    needed = needed_word_types()
    print(f"[needed] {len(needed)} unique word types across concept labels + paraphrase variants")

    zip_path = args.from_zip if args.from_zip is not None else (args.tmp / "glove.6B.zip")
    if args.from_zip is None:
        download(args.url, zip_path)
    elif not zip_path.exists():
        raise SystemExit(f"--from-zip {zip_path} does not exist")

    subset_paths: dict[int, Path] = {}
    for dim in args.dims:
        member = f"glove.6B.{dim}d.txt"
        full_txt = args.tmp / member
        extract_member(zip_path, member, full_txt)
        out_path = args.out_dir / f"p3_glove_subset_{dim}d.txt"
        build_subset(full_txt, needed, out_path)
        subset_paths[dim] = out_path

    print("\n[done] vendored subsets:")
    for dim, p in sorted(subset_paths.items()):
        print(f"  {dim}d -> {p}")
    print(f"[note] full tables + zip kept in gitignored {args.tmp}/ (not committed)")

    if args.run:
        return run_harness(subset_paths.get(300), subset_paths.get(100))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
