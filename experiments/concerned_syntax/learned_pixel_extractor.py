#!/usr/bin/env python3
"""Learned pixel-object extraction for Arc 2A concerned syntax.

The original pixel gate uses connected components as an algorithmic extractor.
This diagnostic replaces that extractor with a tiny learned foreground model
and slot-local center search, then reruns the same concerned-syntax agents on
the learned object features.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax.benchmark import make_trial
from experiments.concerned_syntax.learned_agents import LinearBinaryModel, train_linear_binary
from experiments.concerned_syntax.pixel_shapes import (
    BACKGROUND,
    IMAGE_SIZE,
    PIXEL_AGENTS,
    ExtractedComponent,
    PixelExample,
    PixelImage,
    evaluate_agents,
    render_pixel_surface,
    summarize_results,
    train_models,
)
from experiments.concerned_syntax.vector_shapes import vector_surface


@dataclass(frozen=True)
class LearnedPixelExtractor:
    foreground: LinearBinaryModel


def make_raw_pixel_examples(*, trials: int, seed: int) -> list[PixelExample]:
    rng = random.Random(seed)
    examples: list[PixelExample] = []
    for trial_id in range(trials):
        trial = make_trial(trial_id, rng)
        examples.append(
            PixelExample(
                trial=trial,
                image=render_pixel_surface(trial),
                components=(),
            )
        )
    return examples


def pixel_classifier_features(image: PixelImage, x: int, y: int) -> list[float]:
    pixel = image[y][x]
    intensity = sum(pixel) / (3.0 * 255.0)
    center = (IMAGE_SIZE - 1) / 2.0
    red = pixel[0] / 255.0
    green = pixel[1] / 255.0
    blue = pixel[2] / 255.0
    return [
        (x - center) / center,
        (center - y) / center,
        red,
        green,
        blue,
        intensity,
        max(pixel) / 255.0,
        abs(red - green),
        abs(red - blue),
        abs(green - blue),
        red * green,
        red * blue,
        green * blue,
    ]


def _sample_points(
    points: list[tuple[int, int]],
    *,
    count: int,
    rng: random.Random,
) -> list[tuple[int, int]]:
    if len(points) <= count:
        return list(points)
    return rng.sample(points, count)


def train_learned_extractor(
    examples: list[PixelExample],
    *,
    seed: int,
    epochs: int,
    samples_per_image: int = 96,
) -> LearnedPixelExtractor:
    rng = random.Random(seed)
    features: list[list[float]] = []
    labels: list[int] = []
    positive_count = max(12, samples_per_image // 3)
    negative_count = max(24, samples_per_image - positive_count)
    all_points = [(x, y) for y in range(IMAGE_SIZE) for x in range(IMAGE_SIZE)]

    for example in examples:
        foreground = [
            (x, y)
            for y, row in enumerate(example.image)
            for x, pixel in enumerate(row)
            if pixel != BACKGROUND
        ]
        background = [
            point
            for point in all_points
            if example.image[point[1]][point[0]] == BACKGROUND
        ]
        for x, y in _sample_points(foreground, count=positive_count, rng=rng):
            features.append(pixel_classifier_features(example.image, x, y))
            labels.append(1)
        for x, y in _sample_points(background, count=negative_count, rng=rng):
            features.append(pixel_classifier_features(example.image, x, y))
            labels.append(0)

    return LearnedPixelExtractor(
        foreground=train_linear_binary(
            features,
            labels,
            seed=seed + 601,
            epochs=epochs,
            learning_rate=0.06,
        )
    )


def _true_centers(example: PixelExample) -> tuple[tuple[int, int], ...]:
    center = (IMAGE_SIZE - 1) / 2.0
    centers: list[tuple[int, int]] = []
    for part in vector_surface(example.trial):
        scale = 15.0
        x = int(round(center + part.x * scale))
        y = int(round(center - part.y * scale))
        centers.append((max(6, min(IMAGE_SIZE - 7, x)), max(6, min(IMAGE_SIZE - 7, y))))
    return tuple(centers)


def _canonical_slot_centers() -> tuple[tuple[float, float], ...]:
    center = (IMAGE_SIZE - 1) / 2.0
    scale = 15.0
    return tuple(
        (
            center + math.cos(2.0 * math.pi * index / 6.0) * scale,
            center - math.sin(2.0 * math.pi * index / 6.0) * scale,
        )
        for index in range(6)
    )


def _order_by_canonical_slots(
    centers: list[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    remaining = list(centers)
    ordered: list[tuple[int, int]] = []
    for slot_x, slot_y in _canonical_slot_centers():
        choice = min(
            remaining,
            key=lambda point: (point[0] - slot_x) ** 2 + (point[1] - slot_y) ** 2,
        )
        ordered.append(choice)
        remaining.remove(choice)
    return tuple(ordered)


def _choose_centers(
    image: PixelImage,
    extractor: LearnedPixelExtractor,
    *,
    count: int = 6,
    search_radius: int = 5,
) -> tuple[tuple[int, int], ...]:
    selected: list[tuple[int, int]] = []
    for slot_x, slot_y in _canonical_slot_centers()[:count]:
        rounded_x = int(round(slot_x))
        rounded_y = int(round(slot_y))
        candidates: list[tuple[float, int, int]] = []
        for y in range(
            max(1, rounded_y - search_radius),
            min(IMAGE_SIZE - 1, rounded_y + search_radius + 1),
        ):
            for x in range(
                max(1, rounded_x - search_radius),
                min(IMAGE_SIZE - 1, rounded_x + search_radius + 1),
            ):
                score = extractor.foreground.score(pixel_classifier_features(image, x, y))
                distance_penalty = 0.01 * math.hypot(x - slot_x, y - slot_y)
                candidates.append((score - distance_penalty, x, y))
        _, x, y = max(candidates)
        selected.append((x, y))

    return tuple(selected)


def _component_from_center(
    image: PixelImage,
    extractor: LearnedPixelExtractor,
    center: tuple[int, int],
    *,
    radius: int = 5,
) -> ExtractedComponent:
    cx, cy = center
    weighted: list[tuple[int, int, tuple[int, int, int], float]] = []
    active_xs: list[int] = []
    active_ys: list[int] = []
    for y in range(max(0, cy - radius), min(IMAGE_SIZE, cy + radius + 1)):
        for x in range(max(0, cx - radius), min(IMAGE_SIZE, cx + radius + 1)):
            probability = extractor.foreground.probability(
                pixel_classifier_features(image, x, y)
            )
            weight = max(0.0, probability - 0.45)
            if weight > 0.02:
                active_xs.append(x)
                active_ys.append(y)
            if weight > 0.0:
                weighted.append((x, y, image[y][x], weight))

    if not weighted:
        weighted = [(cx, cy, image[cy][cx], 1.0)]
        active_xs = [cx]
        active_ys = [cy]

    total = sum(item[3] for item in weighted)
    mean_x = sum(x * weight for x, _, _, weight in weighted) / total
    mean_y = sum(y * weight for _, y, _, weight in weighted) / total
    mean_r = sum(pixel[0] * weight for _, _, pixel, weight in weighted) / total
    mean_g = sum(pixel[1] * weight for _, _, pixel, weight in weighted) / total
    mean_b = sum(pixel[2] * weight for _, _, pixel, weight in weighted) / total
    min_x, max_x = min(active_xs), max(active_xs)
    min_y, max_y = min(active_ys), max(active_ys)
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    area = len(active_xs)
    return ExtractedComponent(
        cx=mean_x,
        cy=mean_y,
        area=area,
        mean_r=mean_r,
        mean_g=mean_g,
        mean_b=mean_b,
        width=width,
        height=height,
        density=area / (width * height),
    )


def extract_learned_components(
    image: PixelImage,
    extractor: LearnedPixelExtractor,
) -> tuple[ExtractedComponent, ...]:
    return tuple(
        _component_from_center(image, extractor, center)
        for center in _choose_centers(image, extractor)
    )


def attach_learned_components(
    examples: list[PixelExample],
    extractor: LearnedPixelExtractor,
) -> list[PixelExample]:
    return [
        PixelExample(
            trial=example.trial,
            image=example.image,
            components=extract_learned_components(example.image, extractor),
        )
        for example in examples
    ]


def summarize_extractor(
    examples: list[PixelExample],
    *,
    tolerance: float = 5.0,
) -> dict[str, float]:
    slot_total = 0
    slot_correct = 0
    scene_correct = 0
    count_correct = 0
    mean_distance: list[float] = []
    for example in examples:
        count_correct += int(len(example.components) == 6)
        true_centers = _true_centers(example)
        distances: list[float] = []
        for component, true_center in zip(example.components, true_centers):
            distance = math.hypot(component.cx - true_center[0], component.cy - true_center[1])
            distances.append(distance)
            slot_total += 1
            slot_correct += int(distance <= tolerance)
        scene_correct += int(len(distances) == 6 and all(distance <= tolerance for distance in distances))
        mean_distance.extend(distances)
    n = len(examples) or 1
    return {
        "component_count_rate": count_correct / n,
        "slot_recovery_rate": slot_correct / slot_total if slot_total else 0.0,
        "scene_recovery_rate": scene_correct / n,
        "mean_center_error": mean(mean_distance) if mean_distance else 0.0,
    }


def summarize_seed_payloads(payloads: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for payload in payloads:
        for name, stats in payload[key].items():
            grouped.setdefault(name, []).append(stats)

    summary: dict[str, dict[str, Any]] = {}
    for name, rows in sorted(grouped.items()):
        metric_names = [
            metric
            for metric, value in rows[0].items()
            if isinstance(value, (int, float, bool))
        ]
        stats: dict[str, Any] = {}
        for metric in metric_names:
            values = [float(row[metric]) for row in rows]
            stats[metric] = mean(values)
            stats[f"{metric}_sd"] = pstdev(values) if len(values) > 1 else 0.0
        summary[name] = stats
    return summary


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
    extractor_samples_per_image: int = 96,
) -> dict[str, Any]:
    raw_train = make_raw_pixel_examples(trials=train_trials, seed=seed)
    raw_test = make_raw_pixel_examples(trials=test_trials, seed=seed + 700_000)
    extractor = train_learned_extractor(
        raw_train,
        seed=seed,
        epochs=max(10, epochs // 2),
        samples_per_image=extractor_samples_per_image,
    )
    train_examples = attach_learned_components(raw_train, extractor)
    test_examples = attach_learned_components(raw_test, extractor)
    models = train_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_agents(test_examples, models)
    return {
        "manifest": {
            "arc": "2A",
            "name": "learned_pixel_extractor",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "extractor_samples_per_image": extractor_samples_per_image,
            "agents": list(PIXEL_AGENTS),
            "image_size": IMAGE_SIZE,
            "perception": "learned_foreground_slots",
        },
        "extractor_summary": {"learned_foreground_slots": summarize_extractor(test_examples)},
        "agent_summary": summarize_results(rows),
        "results": [asdict(row) for row in rows],
    }


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seed" in manifest:
        return (
            f"{manifest['train_trials']} train trials, "
            f"{manifest['test_trials']} test trials, seed {manifest['seed']}, "
            f"{manifest['epochs']} SGD epochs, "
            f"{manifest['extractor_samples_per_image']} extractor samples/image, "
            f"{manifest['image_size']}x{manifest['image_size']} RGB images."
        )
    seeds = manifest.get("seeds", [])
    return (
        f"{len(seeds)} seeds, {manifest['train_trials']} train trials per seed, "
        f"{manifest['test_trials']} test trials per seed, "
        f"{manifest['epochs']} SGD epochs, "
        f"{manifest['extractor_samples_per_image']} extractor samples/image, "
        f"{manifest['image_size']}x{manifest['image_size']} RGB images."
    )


def write_agent_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    extractor = payload["extractor_summary"]["learned_foreground_slots"]
    manifest = payload["manifest"]
    lines = [
        "# Learned Pixel Extractor Concerned Syntax",
        "",
        "Date: 2026-06-17",
        "",
        (
            "Question: can a learned foreground/slot extractor replace the "
            "connected-component extractor while preserving the pixel-level "
            "concerned-syntax gate?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Extractor Summary",
        "",
        "| Count | Slot recovery | Scene recovery | Center error |",
        "|---:|---:|---:|---:|",
        (
            "| {count:.3f} | {slot:.3f} | {scene:.3f} | {error:.3f} |".format(
                count=extractor["component_count_rate"],
                slot=extractor["slot_recovery_rate"],
                scene=extractor["scene_recovery_rate"],
                error=extractor["mean_center_error"],
            )
        ),
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Parse high | Action | Subtree | Objects | High probe | "
            "Low probe | Regret | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        gate_pass = float(stats["gate_pass"]) >= 0.999
        lines.append(
            "| {agent} | {parse:.3f} | {action:.3f} | {subtree:.3f} | "
            "{objects:.3f} | {high:.3f} | {low:.3f} | {regret:.3f} | "
            "{gate} |".format(
                agent=agent,
                parse=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                subtree=stats["subtree_accuracy"],
                objects=stats["object_extraction_rate"],
                high=stats["high_concern_probe_rate"],
                low=stats["low_concern_probe_rate"],
                regret=stats["mean_regret"],
                gate="PASS" if gate_pass else "fail",
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This is a learned extractor diagnostic, not a full CNN or "
                "unsupervised object-slot model. The extractor learns foreground "
                "pixels from RGB values, uses slot-local search to produce six "
                "slots, and then the existing pixel concerned-syntax agents "
                "consume those learned slots. Passing this gate shows that the "
                "2A pixel result is not tied to direct connected-component "
                "features, while still leaving richer object-centric perception "
                "as future work."
            ),
            "",
            "Raw JSON remains local under `artifacts/concerned_syntax/`.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-trials", type=int, default=1200)
    parser.add_argument("--test-trials", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260617)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--extractor-samples-per-image", type=int, default=96)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--agent-report", type=Path)
    args = parser.parse_args()

    payload = run_experiment(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
        extractor_samples_per_image=args.extractor_samples_per_image,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.agent_report:
        write_agent_report(args.agent_report, payload)

    print("=== Learned Pixel Extractor Summary ===")
    extractor = payload["extractor_summary"]["learned_foreground_slots"]
    print(
        "extractor "
        f"slot={extractor['slot_recovery_rate']:.3f} "
        f"scene={extractor['scene_recovery_rate']:.3f} "
        f"error={extractor['mean_center_error']:.3f}"
    )
    for agent, stats in sorted(payload["agent_summary"].items()):
        print(
            f"{agent:24s} parse_high={stats['parse_accuracy_high_concern']:.3f} "
            f"action={stats['action_accuracy']:.3f} "
            f"objects={stats['object_extraction_rate']:.3f} "
            f"high_probe={stats['high_concern_probe_rate']:.3f} "
            f"low_probe={stats['low_concern_probe_rate']:.3f} "
            f"gate={stats['gate_pass']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
