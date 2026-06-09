#!/usr/bin/env python3
"""Generate a clean publishable summary of a neural sweep JSON.

Usage: python -m experiments.symbolic_weakness.summarize_neural_sweep \
           --in artifacts/symbolic_weakness/neural_sweep_v2.json \
           --out experiments/symbolic_weakness/results/neural_sweep_summary.md
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, stdev


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx = mean(xs)
    my = mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denom = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return 0.0 if denom == 0 else num / denom


def _spearman(xs: list[float], ys: list[float]) -> float:
    def _rank(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(values):
            j = i
            while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
                j += 1
            r = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = r
            i = j + 1
        return ranks
    return _pearson(_rank(xs), _rank(ys))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    payload = json.loads(args.in_path.read_text())
    arts = payload["artifacts"]
    ood = [a["ood_accuracy"] for a in arts]
    n_models = len(arts)

    fields = [
        ("final_train_loss", lambda a: a["final_train_loss"]),
        ("parameter_l2", lambda a: a["parameter_l2"]),
        ("sharpness_proxy", lambda a: a["sharpness_proxy"]),
        ("abs_sharpness_proxy", lambda a: abs(a["sharpness_proxy"])),
        ("held_out_validation_accuracy", lambda a: a["held_out_validation_accuracy"]),
        (
            "weakness_oracle_norm",
            lambda a: float(a["weakness_oracle"]) / max(1, len(a["full_function_table"])),
        ),
        (
            "weakness_wrong_group_norm",
            lambda a: float(a["weakness_wrong_group"]) / max(1, len(a["full_function_table"])),
        ),
        (
            "weakness_partial_cyclic_norm",
            lambda a: float(a["weakness_partial_cyclic"]) / max(1, len(a["full_function_table"])),
        ),
    ]

    rows = []
    for name, accessor in fields:
        values = [accessor(a) for a in arts]
        rows.append((
            name,
            mean(values),
            stdev(values) if len(values) > 1 else 0.0,
            _pearson(values, ood),
            _spearman(values, ood),
        ))

    # Per-augmentation breakdown.
    by_aug: dict[str, list[float]] = {}
    by_aug_w: dict[str, list[float]] = {}
    for a in arts:
        aug = a.get("augmentation") or a.get("config", {}).get("augmentation", "unknown")
        by_aug.setdefault(aug, []).append(a["ood_accuracy"])
        by_aug_w.setdefault(aug, []).append(
            float(a["weakness_oracle"]) / max(1, len(a["full_function_table"]))
        )

    md = [
        "# Neural Symbolic Weakness Sweep Summary",
        "",
        f"Total models: {n_models}",
        f"Mean OOD accuracy: {mean(ood):.4f}",
        f"Fraction with perfect OOD (>0.99): "
        f"{sum(1 for o in ood if o > 0.99) / max(1, n_models):.4f}",
        f"Manifest: `{json.dumps(payload['manifest'])}`",
        "",
        "## Predictors of OOD accuracy",
        "",
        "| Predictor | Mean | Stdev | Pearson w/ OOD | Spearman w/ OOD |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    rows.sort(key=lambda r: -abs(r[3]))
    for name, m, s, p, sp in rows:
        md.append(f"| {name} | {m:.4f} | {s:.4f} | {p:+.4f} | {sp:+.4f} |")
    md += [
        "",
        "## Per-augmentation breakdown",
        "",
        "| Augmentation | n | Mean OOD | Mean weakness (norm) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for aug in sorted(by_aug):
        n = len(by_aug[aug])
        md.append(
            f"| {aug} | {n} | {mean(by_aug[aug]):.4f} | "
            f"{mean(by_aug_w[aug]):.4f} |"
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(md) + "\n")
    print(f"Wrote summary to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
