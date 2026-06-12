#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""One-off helper to renumber figure titles inside existing PNGs.

Used to migrate v2 figure numbering (out-of-order) to v3 (in-order)
WITHOUT re-running ~2 hours of Modal sweeps. The structural figures are
regenerated separately by make_metric_stack_synthesis_figures.py; this
script patches data-driven PNGs whose source artifacts are not on disk.

Patches:
  fig4_p23b_goldilocks.png        -> fig3_p23b_goldilocks.png         ("Figure 4" -> "Figure 3")
  fig5_architectural_ceiling.png  -> fig4_architectural_ceiling.png   ("Figure 5" -> "Figure 4")
  fig1_arc_food_attribution.png   -> fig6_arc_food_attribution.png    ("Figure 1" -> "Figure 6")
  fig_a5_p24_contrast_anti_cheats.png        <-> fig_a6_p24_contrast_anti_cheats.png
  fig_a6_p23b_re_engagement_dynamics.png     <-> fig_a5_p23b_re_engagement_dynamics.png
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "papers" / "metric_stack_synthesis" / "figures"


def _font(size: int) -> ImageFont.FreeTypeFont:
    for name in ("Helvetica.ttc", "Arial.ttf", "DejaVuSans-Bold.ttf",
                 "/System/Library/Fonts/Helvetica.ttc",
                 "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


TITLE_LOOKUP = {
    "fig3_p23b_goldilocks.png":
        "Figure 3.  The Goldilocks: re-engagement vs anxiety vs false calm (Paper 23B)",
    "fig4_architectural_ceiling.png":
        "Figure 4.  The architectural ceiling (Paper 25):  shared mediated head predictions for food vs medicine",
    "fig6_arc_food_attribution.png":
        "Figure 6.  Food self attribution across the autonomous-probing arc",
    "fig_a6_p24_contrast_anti_cheats.png":
        "Figure A6 (Paper 24).  Interventional contrast loss + anti-cheat controls",
    "fig_a5_p23b_re_engagement_dynamics.png":
        "Figure A5 (Paper 23B).  Re-engagement after the SECOND regime shift",
}


def patch(src_name: str, dst_name: str) -> None:
    src = FIG_DIR / src_name
    dst = FIG_DIR / dst_name
    if not src.exists():
        print(f"  skip: {src_name} not present")
        return
    img = Image.open(src).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    bar_h = max(70, int(h * 0.08))
    draw.rectangle([(0, 0), (w, bar_h)], fill="white")

    title_text = TITLE_LOOKUP[dst_name]
    font_size = max(20, int(h * 0.024))
    font = _font(font_size)
    bbox = draw.textbbox((0, 0), title_text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = max(10, (w - tw) // 2)
    y = max(8, (bar_h - th) // 2)
    draw.text((x, y), title_text, fill="black", font=font)

    img.save(dst, optimize=True)
    if src != dst:
        src.unlink()
    print(f"  patched: {src_name} -> {dst_name}")


def main() -> int:
    # A5<->A6 swap needs a temp shuffle so neither original is destroyed
    a5_p24 = FIG_DIR / "fig_a5_p24_contrast_anti_cheats.png"
    a6_p23 = FIG_DIR / "fig_a6_p23b_re_engagement_dynamics.png"
    tmp_a5 = FIG_DIR / "_swap_a5.png"
    tmp_a6 = FIG_DIR / "_swap_a6.png"
    if a5_p24.exists():
        a5_p24.rename(tmp_a5)
    if a6_p23.exists():
        a6_p23.rename(tmp_a6)
    if tmp_a6.exists():
        tmp_a6.rename(FIG_DIR / "fig_a6_p23b_re_engagement_dynamics.png")
        patch("fig_a6_p23b_re_engagement_dynamics.png",
              "fig_a5_p23b_re_engagement_dynamics.png")
    if tmp_a5.exists():
        tmp_a5.rename(FIG_DIR / "fig_a5_p24_contrast_anti_cheats.png")
        patch("fig_a5_p24_contrast_anti_cheats.png",
              "fig_a6_p24_contrast_anti_cheats.png")

    patch("fig4_p23b_goldilocks.png",       "fig3_p23b_goldilocks.png")
    patch("fig5_architectural_ceiling.png", "fig4_architectural_ceiling.png")
    patch("fig1_arc_food_attribution.png",  "fig6_arc_food_attribution.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
