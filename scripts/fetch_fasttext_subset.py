#!/usr/bin/env python3
"""Fetch fastText English vectors and vendor ONLY the word types Prediction 3 needs.

Pre-registration: docs/external_contact_preregistration.md (Prediction 3).
P3c-3way amendment (cloud-agent handoff 2026-06-22): a third external embedding
family is added BEFORE running, strictly tightening P3c to require the MINIMUM
pairwise RSA across all three families >= 0.6.

Mirrors scripts/fetch_glove_subset.py exactly. The harness's tokenize()
function and the fastText file format are byte-compatible with GloVe (plain
text, "word v1 v2 ... vd" per line), so the same load_glove() / pool() path
in experiments/external_contact/p3_glove_probe.py reads the vendored subset
without modification.

The fastText 1M-word "wiki-news-300d-1M" English vectors are ~600 MB zipped,
small enough to be tractable on a laptop, large enough to cover the lab's 24
concept set. Source URL:

    https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M.vec.zip

Pure standard library only (urllib, zipfile). The full unpacked .vec file
(~2 GB) stays in tmp/fasttext/ (gitignored); only the ~400-word subset is
written to experiments/external_contact/.

Example:

    python3 scripts/fetch_fasttext_subset.py --run
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

FASTTEXT_URL = "https://dl.fbaipublicfiles.com/fasttext/vectors-english/wiki-news-300d-1M.vec.zip"
FASTTEXT_MEMBER = "wiki-news-300d-1M.vec"

CONCEPT_SET = Path("experiments/concept_geometry/concept_set.json")
PARAPHRASES = Path("experiments/concept_geometry/concept_paraphrases.json")
OUT_DIR = Path("experiments/external_contact")
TMP_DIR = Path("tmp/fasttext")


def tokenize(text: str) -> list[str]:
    # Byte-identical to p3_glove_probe.py::tokenize.
    text = text.split(":", 1)[-1] if ":" in text else text
    return [t for t in re.findall(r"[a-zA-Z]+", text.lower())]


def needed_word_types() -> set[str]:
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


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest} already present ({dest.stat().st_size} bytes)")
        return dest
    print(f"[download] {url}\n           -> {dest}")
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
            raise SystemExit(f"member {member!r} not in zip; available: {names}")
        with zf.open(member) as src, dest.open("wb") as out:
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
    return dest


def build_subset(full_txt: Path, needed: set[str], out_path: Path) -> tuple[int, set[str]]:
    """Scan the fastText file once, keep only lines whose word is needed.

    fastText's .vec file has a header line "n_words dim" before the vectors,
    which we skip; everything else mirrors load_glove() in p3_glove_probe.py
    (single-space split, word at sp[0], vector follows).
    """
    found: set[str] = set()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with full_txt.open(encoding="utf-8") as fh, out_path.open("w", encoding="utf-8") as out:
        for i, line in enumerate(fh):
            if i == 0 and len(line.split(" ")) == 2:
                continue  # header
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


def run_harness(
    glove300: Path,
    glove100: Path | None,
    fasttext: Path,
) -> int:
    """Invoke the P3 harness on the GloVe-300 (primary) + GloVe-100 + fastText panel."""
    cmd = [
        sys.executable, "-m", "experiments.external_contact.p3_glove_probe",
        "--glove", str(glove300),
        "--glove3", str(fasttext),
        "--label3", "fasttext-300d",
        "--out", "artifacts/external_contact/p3_glove_three_family.json",
    ]
    if glove100 is not None:
        cmd += ["--glove2", str(glove100), "--label2", "glove-100d"]
    print(f"[run] {' '.join(cmd)}")
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=FASTTEXT_URL, help="fastText zip URL.")
    parser.add_argument("--tmp", type=Path, default=TMP_DIR, help="Gitignored scratch dir for the zip / full table.")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="Where to write the vendored subset.")
    parser.add_argument("--run", action="store_true", help="After fetching, invoke the P3 harness on the 3-family panel.")
    parser.add_argument("--from-zip", type=Path, default=None, help="Use an already-downloaded fastText zip instead of fetching.")
    args = parser.parse_args()

    needed = needed_word_types()
    print(f"[needed] {len(needed)} unique word types across concept labels + paraphrase variants")

    zip_path = args.from_zip if args.from_zip is not None else (args.tmp / "fasttext.zip")
    if args.from_zip is None:
        download(args.url, zip_path)
    elif not zip_path.exists():
        raise SystemExit(f"--from-zip {zip_path} does not exist")

    full_txt = args.tmp / FASTTEXT_MEMBER
    extract_member(zip_path, FASTTEXT_MEMBER, full_txt)
    out_path = args.out_dir / "p3_fasttext_subset_300d.txt"
    build_subset(full_txt, needed, out_path)

    print(f"\n[done] vendored subset -> {out_path}")
    print(f"[note] full table + zip kept in gitignored {args.tmp}/ (not committed)")

    if args.run:
        glove300 = args.out_dir / "p3_glove_subset_300d.txt"
        glove100 = args.out_dir / "p3_glove_subset_100d.txt"
        if not glove300.exists():
            print(f"[skip] {glove300} not present; run scripts/fetch_glove_subset.py first")
            return 0
        if not glove100.exists():
            print(f"[warn] {glove100} not present; running 2-family panel (glove-300 + fasttext)")
            glove100 = None
        return run_harness(glove300, glove100, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
