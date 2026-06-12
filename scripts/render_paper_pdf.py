#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render a markdown paper to PDF using `markdown-pdf` (PyMuPDF-backed).

Run via uvx so we do not need a system pandoc/LaTeX install:

    uvx --from markdown-pdf python scripts/render_paper_pdf.py \
        --in papers/weakness_invariance_neurips/paper.md \
        --out papers/weakness_invariance_neurips/paper.pdf
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from markdown_pdf import MarkdownPdf, Section


# Lightweight LaTeX → Unicode substitutions so inline math reads cleanly
# without pulling in a full TeX toolchain. Block math uses centred display.
LATEX_REPLACEMENTS = [
    (r"\\mathcal\{X\}", "X"),
    (r"\\mathcal\{Y\}", "Y"),
    (r"\\mathbb\{Z\}_n", "Z_n"),
    (r"\\mathbb\{Z\}", "Z"),
    (r"\\mathbb\{R\}", "R"),
    (r"\\arg\\max", "argmax"),
    (r"\\arg\\min", "argmin"),
    (r"\\bmod\s*", " mod "),
    (r"\\cdot\s*", "·"),
    (r"\\to\s*", " → "),
    (r"\\in\s*", " ∈ "),
    (r"\\forall\s*", "∀"),
    (r"\\exists\s*", "∃"),
    (r"\\ge\s*", "≥"),
    (r"\\le\s*", "≤"),
    (r"\\ne\s*", "≠"),
    (r"\\approx\s*", "≈"),
    (r"\\rho", "ρ"),
    (r"\\sigma", "σ"),
    (r"\\pi", "π"),
    (r"\\Pi", "Π"),
    (r"\\Sigma", "Σ"),
    (r"\\Delta", "Δ"),
    (r"\\times", "×"),
    (r"\\big\|", "|"),
    (r"\\;", " "),
    (r"\\\\,", ", "),
    (r"\\text\{([^}]+)\}", lambda m: m.group(1).replace("_", "_")),
    (r"\\,", " "),
    (r"S_n", "S_n"),
    (r"D_n", "D_n"),
    (r"Z_n", "Z_n"),
    (r"\\hat\s*G", "Ĝ"),
    (r"\\hat\{G\}", "Ĝ"),
    (r"\\bar\{f\}", "f̄"),
    (r"\\nabla", "∇"),
    (r"\\partial", "∂"),
    (r"\^\{?([0-9])\}?", lambda m: "⁰¹²³⁴⁵⁶⁷⁸⁹"[int(m.group(1))]),
    (r"_\{?([0-9])\}?", lambda m: "₀₁₂₃₄₅₆₇₈₉"[int(m.group(1))]),
]


def _delatex(text: str) -> str:
    # Display math: $$ ... $$ → centred block.
    def display(m: re.Match) -> str:
        inner = m.group(1).strip()
        for pat, sub in LATEX_REPLACEMENTS:
            inner = re.sub(pat, sub, inner)
        # Final cleanup: remove remaining backslashes and braces.
        inner = re.sub(r"\\([a-zA-Z]+)", r"\1", inner)
        inner = inner.replace("{", "").replace("}", "")
        return f"\n\n<div style=\"text-align:center;font-family:'Menlo',monospace;margin:0.6em 0\">{inner}</div>\n\n"

    text = re.sub(r"\$\$(.+?)\$\$", display, text, flags=re.DOTALL)

    # Inline math: $ ... $ → plain text with substitutions.
    def inline(m: re.Match) -> str:
        inner = m.group(1)
        for pat, sub in LATEX_REPLACEMENTS:
            inner = re.sub(pat, sub, inner)
        # Drop any leftover backslash commands and braces.
        inner = re.sub(r"\\([a-zA-Z]+)", r"\1", inner)
        inner = inner.replace("{", "").replace("}", "")
        return inner

    text = re.sub(r"\$([^$\n]+?)\$", inline, text)
    return text


CSS = """
@page { size: Letter; margin: 0.85in 0.85in 0.85in 0.85in; }
body { font-family: "Helvetica", "Arial", sans-serif; font-size: 10.5pt; line-height: 1.45; color: #111; }
h1 { font-size: 18pt; margin-top: 0; }
h2 { font-size: 13pt; margin-top: 1.1em; border-bottom: 1px solid #ccc; padding-bottom: 0.1em; }
h3 { font-size: 11.5pt; margin-top: 1em; }
p, li { font-size: 10.5pt; }
code { font-family: "Menlo", "Courier New", monospace; font-size: 9.5pt; background: transparent; padding: 0; border-radius: 0; }
pre { background: #f4f4f4; padding: 8px 10px; border-radius: 3px; font-size: 9pt; overflow-x: auto; }
pre code { background: transparent; padding: 0; font-size: 9pt; }
table { border-collapse: collapse; margin: 0.5em 0; font-size: 10pt; }
th, td { border: 1px solid #bbb; padding: 4px 8px; text-align: left; }
th { background: #eee; }
blockquote { border-left: 3px solid #999; margin-left: 0; padding-left: 0.8em; color: #555; }
hr { border: 0; border-top: 1px solid #ccc; margin: 1em 0; }
img { max-width: 100%; height: auto; display: block; margin: 0.6em auto; }
figcaption, p > em { font-size: 10pt; color: #444; }
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", default="Weakness Invariance")
    parser.add_argument("--author", default="")
    args = parser.parse_args()

    import base64
    import mimetypes

    md_text = _delatex(args.in_path.read_text(encoding="utf-8"))
    paper_dir = args.in_path.resolve().parent

    # Inline images as data URIs — most reliable across markdown→PDF backends.
    def _inline_image(match: re.Match) -> str:
        alt = match.group(1)
        path = match.group(2)
        if path.startswith("http://") or path.startswith("https://") or path.startswith("data:"):
            return match.group(0)
        candidate = (paper_dir / path).resolve()
        if not candidate.exists():
            return match.group(0)
        mime = mimetypes.guess_type(str(candidate))[0] or "image/png"
        encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
        return f"![{alt}](data:{mime};base64,{encoded})"

    md_text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _inline_image, md_text)

    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.meta["title"] = args.title
    if args.author:
        pdf.meta["author"] = args.author
    pdf.add_section(Section(md_text, toc=False), user_css=CSS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pdf.save(str(args.out))
    print(f"Wrote {args.out} ({args.out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
