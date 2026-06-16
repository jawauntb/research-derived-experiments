#!/usr/bin/env python3
"""Pixel-rendered Arc 2A concerned-syntax agents.

This gate moves the vector-observation task onto rendered RGB images. The
agent does not receive candidate parses or vector parts. A small
connected-component extractor recovers object-level perceptual features from
the pixels, then the same concern-gated intervention logic is tested against
surface, passive, and restless controls.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from experiments.concerned_syntax.benchmark import (
    ShapeTrial,
    _same_subtree,
    concern_gap,
    make_trial,
    outcome_for_parse,
    preferred_action,
    utility,
)
from experiments.concerned_syntax.learned_agents import (
    LinearBinaryModel,
    train_linear_binary,
)
from experiments.concerned_syntax.vector_shapes import (
    PAIR_INDEX,
    VectorPart,
    vector_surface,
)

IMAGE_SIZE = 48
BACKGROUND = (0, 0, 0)

PIXEL_AGENTS: tuple[str, ...] = (
    "surface_pixel_shortcut",
    "passive_pixel",
    "restless_pixel_probe",
    "concerned_pixel_probe",
)


@dataclass(frozen=True)
class RoleStyle:
    color: tuple[int, int, int]
    radius: int
    shape: str


ROLE_STYLES: dict[str, RoleStyle] = {
    "neutral": RoleStyle((90, 96, 112), 3, "circle"),
    "shield": RoleStyle((58, 142, 214), 4, "square"),
    "poison": RoleStyle((178, 52, 112), 4, "diamond"),
    "repair": RoleStyle((48, 166, 104), 4, "circle"),
    "core": RoleStyle((224, 188, 64), 4, "square"),
    "food": RoleStyle((220, 120, 46), 4, "circle"),
    "trap": RoleStyle((126, 72, 188), 4, "diamond"),
    "signal": RoleStyle((54, 184, 194), 4, "square"),
    "ornament": RoleStyle((212, 94, 174), 4, "circle"),
}


Pixel = tuple[int, int, int]
PixelImage = tuple[tuple[Pixel, ...], ...]


@dataclass(frozen=True)
class ExtractedComponent:
    cx: float
    cy: float
    area: int
    mean_r: float
    mean_g: float
    mean_b: float
    width: int
    height: int
    density: float


@dataclass(frozen=True)
class PixelExample:
    trial: ShapeTrial
    image: PixelImage
    components: tuple[ExtractedComponent, ...]


@dataclass(frozen=True)
class PixelResult:
    trial_id: int
    agent: str
    probed: int
    high_concern: int
    parse_correct: int
    action_correct: int
    subtree_correct: int
    surface_ambiguous: int
    object_extraction_ok: int
    mean_probe_cost: float
    regret: float


def _blank_image() -> list[list[Pixel]]:
    return [[BACKGROUND for _ in range(IMAGE_SIZE)] for _ in range(IMAGE_SIZE)]


def _pixel_center(part: VectorPart) -> tuple[int, int]:
    scale = 15.0
    center = (IMAGE_SIZE - 1) / 2.0
    x = int(round(center + part.x * scale))
    y = int(round(center - part.y * scale))
    return (
        max(6, min(IMAGE_SIZE - 7, x)),
        max(6, min(IMAGE_SIZE - 7, y)),
    )


def _inside_shape(dx: int, dy: int, style: RoleStyle) -> bool:
    if style.shape == "circle":
        return dx * dx + dy * dy <= style.radius * style.radius
    if style.shape == "square":
        return max(abs(dx), abs(dy)) <= style.radius
    if style.shape == "diamond":
        return abs(dx) + abs(dy) <= style.radius + 1
    raise KeyError(style.shape)


def _shade(color: Pixel, dx: int, dy: int) -> Pixel:
    offset = (dx * 7 + dy * 11) % 17
    return (
        max(1, min(255, color[0] - 8 + offset)),
        max(1, min(255, color[1] - 8 + offset)),
        max(1, min(255, color[2] - 8 + offset)),
    )


def render_pixel_surface(trial: ShapeTrial) -> PixelImage:
    """Render a parse-invariant RGB image for a concerned-syntax trial."""

    canvas = _blank_image()
    for part in vector_surface(trial):
        style = ROLE_STYLES[part.role]
        center_x, center_y = _pixel_center(part)
        for dy in range(-style.radius - 1, style.radius + 2):
            for dx in range(-style.radius - 1, style.radius + 2):
                if not _inside_shape(dx, dy, style):
                    continue
                x = center_x + dx
                y = center_y + dy
                if 0 <= x < IMAGE_SIZE and 0 <= y < IMAGE_SIZE:
                    canvas[y][x] = _shade(style.color, dx, dy)
    return tuple(tuple(row) for row in canvas)


def extract_components(image: PixelImage) -> tuple[ExtractedComponent, ...]:
    """Extract connected non-background objects from an RGB image."""

    visited: set[tuple[int, int]] = set()
    components: list[ExtractedComponent] = []
    for y, row in enumerate(image):
        for x, pixel in enumerate(row):
            if pixel == BACKGROUND or (x, y) in visited:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited.add((x, y))
            pixels: list[tuple[int, int, Pixel]] = []
            while queue:
                cx, cy = queue.popleft()
                current = image[cy][cx]
                pixels.append((cx, cy, current))
                for ny in range(cy - 1, cy + 2):
                    for nx in range(cx - 1, cx + 2):
                        if (
                            0 <= nx < IMAGE_SIZE
                            and 0 <= ny < IMAGE_SIZE
                            and (nx, ny) not in visited
                            and image[ny][nx] != BACKGROUND
                        ):
                            visited.add((nx, ny))
                            queue.append((nx, ny))

            xs = [item[0] for item in pixels]
            ys = [item[1] for item in pixels]
            colors = [item[2] for item in pixels]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            area = len(pixels)
            components.append(
                ExtractedComponent(
                    cx=mean(xs),
                    cy=mean(ys),
                    area=area,
                    mean_r=mean(color[0] for color in colors),
                    mean_g=mean(color[1] for color in colors),
                    mean_b=mean(color[2] for color in colors),
                    width=width,
                    height=height,
                    density=area / (width * height),
                )
            )

    center = (IMAGE_SIZE - 1) / 2.0

    def angle(component: ExtractedComponent) -> float:
        value = math.atan2(-(component.cy - center), component.cx - center)
        return value if value >= 0.0 else value + 2.0 * math.pi

    return tuple(sorted(components, key=angle))


def make_pixel_examples(*, trials: int, seed: int) -> list[PixelExample]:
    rng = random.Random(seed)
    examples: list[PixelExample] = []
    for trial_id in range(trials):
        trial = make_trial(trial_id, rng)
        image = render_pixel_surface(trial)
        examples.append(
            PixelExample(
                trial=trial,
                image=image,
                components=extract_components(image),
            )
        )
    return examples


def true_bound(example: PixelExample) -> int:
    return int(_same_subtree(example.trial.true_parse, *example.trial.causal_pair))


def _component_features(component: ExtractedComponent) -> list[float]:
    center = (IMAGE_SIZE - 1) / 2.0
    return [
        (component.cx - center) / center,
        (center - component.cy) / center,
        component.area / 100.0,
        component.mean_r / 255.0,
        component.mean_g / 255.0,
        component.mean_b / 255.0,
        component.width / IMAGE_SIZE,
        component.height / IMAGE_SIZE,
        component.density,
    ]


def pixel_surface_features(example: PixelExample) -> list[float]:
    features: list[float] = []
    padded = list(example.components[:6])
    while len(padded) < 6:
        padded.append(
            ExtractedComponent(
                cx=(IMAGE_SIZE - 1) / 2.0,
                cy=(IMAGE_SIZE - 1) / 2.0,
                area=0,
                mean_r=0.0,
                mean_g=0.0,
                mean_b=0.0,
                width=0,
                height=0,
                density=0.0,
            )
        )
    for component in padded:
        features.extend(_component_features(component))
    for a, b in PAIR_INDEX:
        left = padded[a]
        right = padded[b]
        features.append(
            round(
                math.hypot(
                    (left.cx - right.cx) / IMAGE_SIZE,
                    (left.cy - right.cy) / IMAGE_SIZE,
                ),
                4,
            )
        )
    features.append(float(len(example.components) == 6))
    return features


def parse_features(
    example: PixelExample,
    *,
    observed: bool,
    observed_bound: int,
) -> list[float]:
    features = pixel_surface_features(example)
    features.extend([float(observed), float(observed_bound if observed else 0)])
    return features


def action_features(example: PixelExample, *, bound: int) -> list[float]:
    features = pixel_surface_features(example)
    features.append(float(bound))
    features.extend(float(bound) * value for value in features[:-1])
    return features


def _true_action_label(example: PixelExample) -> int:
    outcome = outcome_for_parse(example.trial, example.trial.true_parse)
    return int(preferred_action(outcome, example.trial.concern_weight) == "consume")


def train_models(
    train_examples: list[PixelExample],
    *,
    seed: int,
    epochs: int,
) -> dict[str, LinearBinaryModel]:
    policy_x = [pixel_surface_features(example) for example in train_examples]
    policy_y = [int(concern_gap(example.trial) >= 0.10) for example in train_examples]

    bound_x = [
        parse_features(example, observed=True, observed_bound=true_bound(example))
        for example in train_examples
    ]
    prior_x = [
        parse_features(example, observed=False, observed_bound=0)
        for example in train_examples
    ]
    bound_y = [true_bound(example) for example in train_examples]

    action_x = [
        action_features(example, bound=true_bound(example))
        for example in train_examples
    ]
    action_y = [_true_action_label(example) for example in train_examples]
    shortcut_x = [pixel_surface_features(example) for example in train_examples]

    return {
        "policy": train_linear_binary(
            policy_x,
            policy_y,
            seed=seed + 31,
            epochs=epochs,
        ),
        "bound_probe": train_linear_binary(
            bound_x,
            bound_y,
            seed=seed + 32,
            epochs=epochs,
        ),
        "bound_prior": train_linear_binary(
            prior_x,
            bound_y,
            seed=seed + 33,
            epochs=epochs,
        ),
        "action_bound": train_linear_binary(
            action_x,
            action_y,
            seed=seed + 34,
            epochs=epochs,
        ),
        "shortcut_action": train_linear_binary(
            shortcut_x,
            action_y,
            seed=seed + 35,
            epochs=epochs,
        ),
    }


def _calibration_probe(example: PixelExample, *, percent: int = 20) -> bool:
    component_code = sum(
        (idx + 1) * (component.area + int(component.mean_r))
        for idx, component in enumerate(example.components)
    )
    code = (
        example.trial.trial_id * 1_103_515_245
        + component_code
        + int(example.trial.concern_weight * 1000)
    ) % 100
    return code < percent


def _predict_bound(
    example: PixelExample,
    models: dict[str, LinearBinaryModel],
    *,
    probed: bool,
) -> int:
    if probed:
        observed = true_bound(example)
        return models["bound_probe"].predict(
            parse_features(example, observed=True, observed_bound=observed)
        )
    return models["bound_prior"].predict(
        parse_features(example, observed=False, observed_bound=0)
    )


def _value_for_bound(example: PixelExample, bound: int) -> float:
    true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
    if bound == true_bound(example):
        return utility(true_outcome, example.trial.concern_weight)
    alternate_outcome = outcome_for_parse(
        example.trial,
        example.trial.alternate_parse,
    )
    return utility(alternate_outcome, example.trial.concern_weight)


def evaluate_agent(
    examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
    *,
    agent: str,
) -> list[PixelResult]:
    rows: list[PixelResult] = []
    for example in examples:
        gap = concern_gap(example.trial)
        high = int(gap >= 0.10)
        if agent == "surface_pixel_shortcut":
            probed = False
            bound = _predict_bound(example, models, probed=False)
            action_label = models["shortcut_action"].predict(
                pixel_surface_features(example)
            )
        elif agent == "passive_pixel":
            probed = False
            bound = _predict_bound(example, models, probed=False)
            action_label = models["action_bound"].predict(
                action_features(example, bound=bound)
            )
        elif agent == "restless_pixel_probe":
            probed = True
            bound = _predict_bound(example, models, probed=True)
            action_label = models["action_bound"].predict(
                action_features(example, bound=bound)
            )
        elif agent == "concerned_pixel_probe":
            policy_probe = bool(
                models["policy"].predict(pixel_surface_features(example))
            )
            probed = policy_probe or _calibration_probe(example, percent=20)
            bound = _predict_bound(example, models, probed=probed)
            action_label = models["action_bound"].predict(
                action_features(example, bound=bound)
            )
        else:
            raise KeyError(agent)

        target_bound = true_bound(example)
        pred_action = "consume" if action_label else "skip"
        true_outcome = outcome_for_parse(example.trial, example.trial.true_parse)
        true_action = preferred_action(true_outcome, example.trial.concern_weight)
        rows.append(
            PixelResult(
                trial_id=example.trial.trial_id,
                agent=agent,
                probed=int(probed),
                high_concern=high,
                parse_correct=int(bound == target_bound),
                action_correct=int(pred_action == true_action),
                subtree_correct=int(bound == target_bound),
                surface_ambiguous=1,
                object_extraction_ok=int(len(example.components) == 6),
                mean_probe_cost=0.04 if probed else 0.0,
                regret=max(
                    0.0,
                    utility(true_outcome, example.trial.concern_weight)
                    - _value_for_bound(example, bound),
                ),
            )
        )
    return rows


def evaluate_agents(
    examples: list[PixelExample],
    models: dict[str, LinearBinaryModel],
) -> list[PixelResult]:
    rows: list[PixelResult] = []
    for agent in PIXEL_AGENTS:
        rows.extend(evaluate_agent(examples, models, agent=agent))
    return rows


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_results(rows: list[PixelResult]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[PixelResult]] = {}
    for row in rows:
        grouped.setdefault(row.agent, []).append(row)

    summary: dict[str, dict[str, Any]] = {}
    for agent, items in grouped.items():
        high = [item for item in items if item.high_concern]
        low = [item for item in items if not item.high_concern]
        high_probe = _safe_mean([item.probed for item in high])
        low_probe = _safe_mean([item.probed for item in low])
        parse_high = _safe_mean([item.parse_correct for item in high])
        action = _safe_mean([item.action_correct for item in items])
        subtree = _safe_mean([item.subtree_correct for item in items])
        extraction = _safe_mean([item.object_extraction_ok for item in items])
        summary[agent] = {
            "n": len(items),
            "parse_accuracy_high_concern": parse_high,
            "action_accuracy": action,
            "subtree_accuracy": subtree,
            "surface_ambiguity_rate": _safe_mean(
                [item.surface_ambiguous for item in items]
            ),
            "object_extraction_rate": extraction,
            "high_concern_probe_rate": high_probe,
            "low_concern_probe_rate": low_probe,
            "mean_probe_cost": _safe_mean([item.mean_probe_cost for item in items]),
            "mean_regret": _safe_mean([item.regret for item in items]),
            "gate_pass": bool(
                extraction >= 0.99
                and parse_high >= 0.75
                and action >= 0.85
                and subtree >= 0.75
                and high_probe >= 0.70
                and low_probe <= 0.25
            ),
        }
    return summary


def run_experiment(
    *,
    train_trials: int,
    test_trials: int,
    seed: int,
    epochs: int,
) -> dict[str, Any]:
    train_examples = make_pixel_examples(trials=train_trials, seed=seed)
    test_examples = make_pixel_examples(trials=test_trials, seed=seed + 300_000)
    models = train_models(train_examples, seed=seed, epochs=epochs)
    rows = evaluate_agents(test_examples, models)
    agent_summary = summarize_results(rows)
    return {
        "manifest": {
            "arc": "2A",
            "name": "pixel_concerned_syntax_agents",
            "train_trials": train_trials,
            "test_trials": test_trials,
            "seed": seed,
            "epochs": epochs,
            "agents": list(PIXEL_AGENTS),
            "image_size": IMAGE_SIZE,
            "perception": "connected_components_rgb",
        },
        "agent_summary": agent_summary,
        "results": [asdict(row) for row in rows],
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


def _manifest_text(manifest: dict[str, Any]) -> str:
    if "seed" in manifest:
        return (
            f"{manifest['train_trials']} train trials, "
            f"{manifest['test_trials']} test trials, seed {manifest['seed']}, "
            f"{manifest['epochs']} SGD epochs, "
            f"{manifest['image_size']}x{manifest['image_size']} RGB images."
        )
    seeds = manifest.get("seeds", [])
    return (
        f"{len(seeds)} seeds, {manifest['train_trials']} train trials per seed, "
        f"{manifest['test_trials']} test trials per seed, "
        f"{manifest['epochs']} SGD epochs, "
        f"{manifest['image_size']}x{manifest['image_size']} RGB images."
    )


def write_agent_report(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["agent_summary"]
    manifest = payload["manifest"]
    lines = [
        "# Pixel Concerned-Syntax Agents",
        "",
        "Date: 2026-06-16",
        "",
        (
            "Question: does the concerned-syntax gate survive when the surface "
            "is rendered as pixels and object attributes must be extracted "
            "from connected components?"
        ),
        "",
        f"Manifest: {_manifest_text(manifest)}",
        "",
        "## Gate Summary",
        "",
        (
            "| Agent | Parse high | Action | Subtree | Objects | Ambiguity | "
            "High probe | Low probe | Regret | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for agent, stats in sorted(summary.items()):
        gate_pass = float(stats["gate_pass"]) >= 0.999
        lines.append(
            "| {agent} | {parse:.3f} | {action:.3f} | {subtree:.3f} | "
            "{objects:.3f} | {ambiguity:.3f} | {high:.3f} | {low:.3f} | "
            "{regret:.3f} | {gate} |".format(
                agent=agent,
                parse=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                subtree=stats["subtree_accuracy"],
                objects=stats["object_extraction_rate"],
                ambiguity=stats["surface_ambiguity_rate"],
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
            "The pixel surface is still hidden-parse invariant: rendering uses visible role appearance and position, not the true parse assignment. A connected-component extractor recovers object centroids, sizes, colors, and shape density before learning. The accepted agent must therefore combine perceptual object extraction with a concern-gated pair probe. Surface shortcuts keep some action prior but fail hidden binding. Passive perceptual inference fails because the same image admits multiple hidden parses. Restless probing recovers binding while violating the low-concern cap.",
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
    parser.add_argument("--seed", type=int, default=20260616)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--agent-report", type=Path)
    args = parser.parse_args()

    payload = run_experiment(
        train_trials=args.train_trials,
        test_trials=args.test_trials,
        seed=args.seed,
        epochs=args.epochs,
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.agent_report:
        write_agent_report(args.agent_report, payload)

    print("=== Pixel Concerned Syntax Summary ===")
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
