#!/usr/bin/env python3
"""Summarize the Modal paraphrase probe.

For each layer, compute:
- mean per-concept paraphrase weakness (in-orbit cosine)
- mean per-concept wrong-orbit control cosine
- (weakness - control) gap per layer
- Pearson/Spearman correlation of per-concept layer weakness with per-concept
  behavioral consistency

The headline questions are:
  (a) Does paraphrase weakness exceed wrong-orbit control at some layers?
  (b) Does per-concept weakness predict per-concept behavioral consistency?
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return 0.0 if den == 0 else num / den


def _spearman(xs: list[float], ys: list[float]) -> float:
    def rank(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(vals):
            j = i
            while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            rk = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = rk
            i = j + 1
        return r
    return _pearson(rank(xs), rank(ys))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.in_path.read_text())
    concepts = data["concepts"]
    n_layers = int(data["n_layers"])
    weak = {c: list(map(float, data["weakness_per_concept_layer"][c])) for c in concepts}
    ctrl = {c: list(map(float, data["control_per_concept_layer"][c])) for c in concepts}
    weak_centered = {
        c: list(map(float, data.get("weakness_centered_per_concept_layer", {}).get(c, [0.0] * n_layers)))
        for c in concepts
    }
    ctrl_centered = {
        c: list(map(float, data.get("control_centered_per_concept_layer", {}).get(c, [0.0] * n_layers)))
        for c in concepts
    }
    behavior = {c: float(data["behavior_per_concept"][c]) for c in concepts}

    rows: list[tuple[int, float, float, float, float, float, float, float, float, float]] = []
    for layer in range(n_layers):
        weak_layer = [weak[c][layer] for c in concepts]
        ctrl_layer = [ctrl[c][layer] for c in concepts]
        weak_c_layer = [weak_centered[c][layer] for c in concepts]
        ctrl_c_layer = [ctrl_centered[c][layer] for c in concepts]
        behavior_layer = [behavior[c] for c in concepts]
        pearson_raw = _pearson(weak_layer, behavior_layer)
        spearman_raw = _spearman(weak_layer, behavior_layer)
        pearson_c = _pearson(weak_c_layer, behavior_layer)
        spearman_c = _spearman(weak_c_layer, behavior_layer)
        rows.append(
            (
                layer,
                mean(weak_layer),
                mean(ctrl_layer),
                mean(weak_layer) - mean(ctrl_layer),
                pearson_raw,
                spearman_raw,
                mean(weak_c_layer),
                mean(ctrl_c_layer),
                pearson_c,
                spearman_c,
            )
        )

    md = [
        "# Paraphrase Weakness Summary",
        "",
        f"Model: `{data.get('model_id')}`",
        f"Layers: {n_layers}",
        f"Concepts: {len(concepts)}",
        f"Mean behavioral consistency: {mean(behavior.values()):.4f}",
        "",
        "## Raw cosine (anisotropy-confounded)",
        "",
        "| Layer | weak | ctrl | gap | Pearson | Spearman |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for layer, w, c, gap, p, s, *_ in rows:
        md.append(f"| {layer} | {w:.4f} | {c:.4f} | {gap:+.4f} | {p:+.4f} | {s:+.4f} |")

    md += [
        "",
        "## Centered cosine (anisotropy-corrected; per-layer mean subtracted)",
        "",
        "| Layer | weak_c | ctrl_c | gap_c | Pearson_c | Spearman_c |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for layer, _, _, _, _, _, wc, cc, pc, sc in rows:
        md.append(f"| {layer} | {wc:.4f} | {cc:.4f} | {wc - cc:+.4f} | {pc:+.4f} | {sc:+.4f} |")

    md += [
        "",
        "## Headline",
        "",
        f"- Best Pearson(weakness_raw, behavior): "
        f"{max((p for _, _, _, _, p, _, _, _, _, _ in rows), default=0):+.4f} "
        f"(layer {max(rows, key=lambda r: r[4])[0] if rows else -1})",
        f"- Best Pearson(weakness_centered, behavior): "
        f"{max((p for _, _, _, _, _, _, _, _, p, _ in rows), default=0):+.4f} "
        f"(layer {max(rows, key=lambda r: r[8])[0] if rows else -1})",
        f"- Largest centered (weakness − control) gap: "
        f"{max((wc - cc for _, _, _, _, _, _, wc, cc, _, _ in rows), default=0):+.4f}",
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md) + "\n")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
