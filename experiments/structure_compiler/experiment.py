#!/usr/bin/env python3
"""Compile one abstract structure into several substrates and verify identity.

Writes a machine-readable summary plus small human-facing embodiments (an SVG
bar field, a poem, a note CSV, and a navigation DOT) to ``results/``. A real WAV
render is optional and goes to the gitignored ``artifacts/`` tree.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import wave
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.structure_compiler.core import (
        compile_music,
        compile_spatial,
        compile_text,
        compile_visual,
        evaluate_benchmark,
        run_structure,
    )
else:
    from .core import (
        compile_music,
        compile_spatial,
        compile_text,
        compile_visual,
        evaluate_benchmark,
        run_structure,
    )


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
RESULTS = ROOT / "results"
DEFAULT_OUTPUT = RESULTS / "structure_compiler_summary.json"


def write_svg(field: list[dict], path: Path) -> None:
    bar_w, gap, unit = 24, 6, 24
    width = len(field) * (bar_w + gap) + gap
    height = 6 * unit + 40
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#0b0f14"/>',
    ]
    for i, bar in enumerate(field):
        h = bar["height"] * unit
        x = gap + i * (bar_w + gap)
        y = height - 20 - h
        color = "#f2c14e" if bar["hue"] == "gold" else "#4a6070"
        parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="{color}"/>')
    parts.append("</svg>\n")
    path.write_text("\n".join(parts))


def write_poem(lines: list[str], path: Path) -> None:
    path.write_text("\n".join(lines) + "\n")


def write_notes_csv(notes: list[dict], path: Path) -> None:
    rows = ["step,midi,regime"]
    rows += [f"{i},{n['midi']},{n['regime']}" for i, n in enumerate(notes)]
    path.write_text("\n".join(rows) + "\n")


def write_dot(path_steps: list[dict], path: Path) -> None:
    lines = ["digraph navigation {", "  rankdir=LR;"]
    for i, step in enumerate(path_steps):
        lines.append(f'  s{i} [label="{step["node"]}/{step["gate"]}"];')
        if i:
            lines.append(f"  s{i - 1} -> s{i};")
    lines.append("}\n")
    path.write_text("\n".join(lines))


def render_wav(notes: list[dict], path: Path, *, rate: int = 16000, dur: float = 0.25) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = bytearray()
    for note in notes:
        freq = 440.0 * (2 ** ((int(note["midi"]) - 69) / 12))
        for i in range(int(rate * dur)):
            sample = int(12000 * math.sin(2 * math.pi * freq * (i / rate)))
            frames += struct.pack("<h", sample)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--wav", action="store_true", help="render audio to artifacts/")
    args = parser.parse_args()

    payload = evaluate_benchmark()
    RESULTS.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    traj = run_structure()
    write_svg(compile_visual(traj), RESULTS / "embodiment_visual.svg")
    write_poem(compile_text(traj), RESULTS / "embodiment_text.txt")
    write_notes_csv(compile_music(traj), RESULTS / "embodiment_music.csv")
    write_dot(compile_spatial(traj), RESULTS / "embodiment_spatial.dot")
    if args.wav:
        render_wav(
            compile_music(traj),
            REPO / "artifacts" / "structure_compiler" / "embodiment_music.wav",
        )

    print(json.dumps({"status": payload["status"], "gates": payload["gates"]}, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
