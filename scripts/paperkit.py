#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Minimal LaTeX-free academic-paper PDF toolkit (reportlab + matplotlib).

A `Paper` wraps a reportlab Platypus document with an academic stylesheet, and
`chart_*` helpers render publication-style matplotlib figures to PNG for embedding.
Used by scripts/build_*_pdf.py. No system LaTeX/pandoc required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable)
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402


def _register_fonts():
    """Register DejaVu serif/sans (ship with matplotlib) for Unicode (ρ, ℤ, ≤, →)."""
    base = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    fonts = {"BodyFont": "DejaVuSerif.ttf", "BodyFont-Bold": "DejaVuSerif-Bold.ttf",
             "BodyFont-Italic": "DejaVuSerif-Italic.ttf", "SansFont": "DejaVuSans.ttf",
             "SansFont-Bold": "DejaVuSans-Bold.ttf"}
    ok = True
    for name, fn in fonts.items():
        p = base / fn
        if p.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(p)))
            except Exception:
                ok = False
        else:
            ok = False
    if ok:
        pdfmetrics.registerFontFamily("BodyFont", normal="BodyFont", bold="BodyFont-Bold",
                                      italic="BodyFont-Italic", boldItalic="BodyFont-Bold")
    return ok


_HAS_TTF = _register_fonts()
F_BODY = "BodyFont" if _HAS_TTF else "Times-Roman"
F_BOLD = "BodyFont-Bold" if _HAS_TTF else "Times-Bold"
F_ITAL = "BodyFont-Italic" if _HAS_TTF else "Times-Italic"

INK = colors.HexColor("#1a1a1a")
ACCENT = colors.HexColor("#2b6cb0")
MUTED = colors.HexColor("#6b7280")
GRID = "#d9dde3"

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "font.size": 9,
    "font.family": "DejaVu Sans", "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.titlesize": 10,
    "axes.titleweight": "bold", "legend.frameon": False, "figure.autolayout": True,
})


class Paper:
    def __init__(self, out_path: str, figdir: str):
        self.out = Path(out_path)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.figdir = Path(figdir); self.figdir.mkdir(parents=True, exist_ok=True)
        self.flow: list[Any] = []
        ss = getSampleStyleSheet()
        self.s_title = ParagraphStyle("t", parent=ss["Title"], fontName=F_BOLD,
                                      fontSize=17, leading=21, textColor=INK, spaceAfter=6)
        self.s_authors = ParagraphStyle("au", parent=ss["Normal"], fontName=F_BODY,
                                         fontSize=11, leading=14, alignment=TA_CENTER,
                                         textColor=MUTED, spaceAfter=2)
        self.s_h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName=F_BOLD,
                                   fontSize=12.5, leading=15, textColor=INK, spaceBefore=12, spaceAfter=4)
        self.s_h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName=F_BOLD,
                                   fontSize=11, leading=13, textColor=INK, spaceBefore=8, spaceAfter=3)
        self.s_body = ParagraphStyle("b", parent=ss["Normal"], fontName=F_BODY,
                                     fontSize=9.6, leading=13.2, alignment=TA_JUSTIFY,
                                     textColor=INK, spaceAfter=5)
        self.s_abs = ParagraphStyle("abs", parent=self.s_body, fontSize=9.2, leading=12.6,
                                     leftIndent=14, rightIndent=14, textColor=colors.HexColor("#33373d"))
        self.s_cap = ParagraphStyle("cap", parent=ss["Normal"], fontName=F_ITAL,
                                    fontSize=8.4, leading=10.5, alignment=TA_CENTER,
                                    textColor=MUTED, spaceBefore=2, spaceAfter=8)
        self.s_ref = ParagraphStyle("ref", parent=self.s_body, fontSize=8.6, leading=11,
                                    leftIndent=14, firstLineIndent=-14, spaceAfter=2, alignment=TA_JUSTIFY)
        self.s_small = ParagraphStyle("sm", parent=self.s_body, fontSize=8.6, leading=11)

    # ---- content ----
    def title(self, text): self.flow += [Paragraph(text, self.s_title)]
    def authors(self, text): self.flow += [Paragraph(text, self.s_authors)]

    def rule(self): self.flow += [Spacer(1, 3), HRFlowable(width="100%", thickness=0.6,
                                                           color=GRID), Spacer(1, 5)]

    def abstract(self, text):
        self.flow += [Spacer(1, 6), Paragraph("<b>Abstract</b>", self.s_h2),
                      Paragraph(text, self.s_abs), Spacer(1, 2)]

    def h1(self, text): self.flow += [Paragraph(text, self.s_h1)]
    def h2(self, text): self.flow += [Paragraph(text, self.s_h2)]
    def para(self, text): self.flow += [Paragraph(text, self.s_body)]
    def small(self, text): self.flow += [Paragraph(text, self.s_small)]

    def figure(self, png_path: str, caption: str, width_in: float = 6.4):
        from PIL import Image as PILImage
        w, h = PILImage.open(png_path).size
        iw = width_in * inch
        self.flow += [Spacer(1, 2), Image(png_path, width=iw, height=iw * h / w),
                      Paragraph(caption, self.s_cap)]

    def table(self, data, caption: str = "", col_widths=None, header=True):
        t = Table(data, colWidths=col_widths, hAlign="CENTER")
        style = [
            ("FONT", (0, 0), (-1, -1), F_BODY, 8.4),
            ("TEXTCOLOR", (0, 0), (-1, -1), INK),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK if header else GRID),
            ("LINEBELOW", (0, -1), (-1, -1), 0.7, INK),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f9")]),
        ]
        if header:
            style += [("FONT", (0, 0), (-1, 0), F_BOLD, 8.4),
                      ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT)]
        t.setStyle(TableStyle(style))
        self.flow += [Spacer(1, 2), t]
        if caption:
            self.flow += [Paragraph(caption, self.s_cap)]
        self.flow += [Spacer(1, 4)]

    def references(self, refs: list[str]):
        self.h1("References")
        for r in refs:
            self.flow += [Paragraph(r, self.s_ref)]

    def build(self):
        doc = SimpleDocTemplate(str(self.out), pagesize=letter,
                                leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                                topMargin=0.8 * inch, bottomMargin=0.8 * inch,
                                title=self.out.stem)
        doc.build(self.flow)
        return self.out


# --------------------------------------------------------------------------- #
# Chart helpers (return PNG path)
# --------------------------------------------------------------------------- #

def _save(fig, path: Path) -> str:
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def chart_hbar(figpath, labels, values, *, highlight=None, title="", xlabel="",
               vmin=None, vmax=None, colors_=None, value_fmt="{:.2f}", figsize=(6.2, None)):
    n = len(labels)
    fig, ax = plt.subplots(figsize=(figsize[0], figsize[1] or max(1.6, 0.42 * n + 0.6)))
    ys = range(n)
    bar_colors = []
    for i, lab in enumerate(labels):
        if colors_ is not None:
            bar_colors.append(colors_[i])
        elif highlight and lab in highlight:
            bar_colors.append("#2b6cb0")
        elif values[i] < 0:
            bar_colors.append("#c0392b")
        else:
            bar_colors.append("#9aa6b2")
    ax.barh(list(ys), values, color=bar_colors, height=0.66)
    ax.set_yticks(list(ys)); ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_title(title); ax.set_xlabel(xlabel)
    if vmin is not None:
        ax.set_xlim(vmin, vmax)
    ax.axvline(0, color="#444", lw=0.8)
    for i, v in enumerate(values):
        ax.text(v + (0.01 if v >= 0 else -0.01), i, value_fmt.format(v),
                va="center", ha="left" if v >= 0 else "right", fontsize=7.6,
                color="#222")
    ax.grid(axis="y", visible=False)
    return _save(fig, Path(figpath))


def chart_scatter_gradient(figpath, x, y, labels=None, *, title="", xlabel="", ylabel="",
                           annotate=None, figsize=(5.0, 3.4)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(x, y, s=46, c=x, cmap="viridis", edgecolor="#222", linewidth=0.5, zorder=3)
    if labels:
        for xi, yi, li in zip(x, y, labels):
            ax.annotate(li, (xi, yi), fontsize=7, xytext=(4, 4), textcoords="offset points",
                        color="#333")
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    return _save(fig, Path(figpath))


def chart_grouped_bar(figpath, groups, series: dict[str, list[float]], *, title="",
                      ylabel="", colors_=None, figsize=(5.6, 3.3), ymax=None):
    import numpy as np
    fig, ax = plt.subplots(figsize=figsize)
    n = len(groups); k = len(series); width = 0.8 / k
    x = np.arange(n)
    palette = colors_ or ["#2b6cb0", "#9aa6b2", "#c0392b", "#2f9e44", "#e8a13a"]
    for i, (name, vals) in enumerate(series.items()):
        ax.bar(x + (i - (k - 1) / 2) * width, vals, width, label=name, color=palette[i % len(palette)])
    ax.set_xticks(x); ax.set_xticklabels(groups)
    ax.set_title(title); ax.set_ylabel(ylabel)
    if ymax is not None:
        ax.set_ylim(0, ymax)
    ax.legend(fontsize=7.6, ncol=min(k, 3))
    ax.grid(axis="x", visible=False)
    return _save(fig, Path(figpath))


def chart_line(figpath, x, ys: dict[str, list[float]], *, title="", xlabel="", ylabel="",
               figsize=(5.4, 3.2), markers=True):
    fig, ax = plt.subplots(figsize=figsize)
    palette = ["#2b6cb0", "#c0392b", "#2f9e44", "#e8a13a"]
    for i, (name, y) in enumerate(ys.items()):
        ax.plot(x, y, marker="o" if markers else None, label=name, color=palette[i % len(palette)], lw=1.6)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.legend(fontsize=7.6)
    return _save(fig, Path(figpath))
