#!/usr/bin/env python3
"""Synthetic weakness-vs-simplicity benchmark."""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Callable, Iterable

World = tuple[int, ...]


@dataclass(frozen=True)
class Candidate:
    name: str
    extension: frozenset[World]
    form_length: int

    @property
    def weakness(self) -> int:
        return len(self.extension)


@dataclass(frozen=True)
class TrialResult:
    selector: str
    train_positives: int
    train_negatives: int
    target: str
    chosen: str
    chosen_form_length: int
    chosen_weakness: int
    jaccard: float
    accuracy: float


def all_worlds(features: int) -> list[World]:
    return [tuple((index >> bit) & 1 for bit in range(features)) for index in range(2**features)]


def rule_name(assignments: tuple[tuple[int, int], ...]) -> str:
    return " & ".join(f"x{feature}={value}" for feature, value in assignments)


def extension_for(worlds: Iterable[World], assignments: tuple[tuple[int, int], ...]) -> frozenset[World]:
    return frozenset(
        world
        for world in worlds
        if all(world[feature] == value for feature, value in assignments)
    )


def reusable_candidates(worlds: list[World], features: int) -> list[Candidate]:
    candidates: list[Candidate] = []
    for feature in range(features):
        for value in (0, 1):
            assignments = ((feature, value),)
            candidates.append(
                Candidate(
                    name=rule_name(assignments),
                    extension=extension_for(worlds, assignments),
                    form_length=4,
                )
            )

    for first in range(features):
        for second in range(first + 1, features):
            for first_value in (0, 1):
                for second_value in (0, 1):
                    assignments = ((first, first_value), (second, second_value))
                    candidates.append(
                        Candidate(
                            name=rule_name(assignments),
                            extension=extension_for(worlds, assignments),
                            form_length=7,
                        )
                    )
    return candidates


def add_memorizer(candidates: list[Candidate], positives: list[World]) -> list[Candidate]:
    return [
        *candidates,
        Candidate(
            name="memorize_observed_positives",
            extension=frozenset(positives),
            form_length=1,
        ),
    ]


def consistent(candidates: Iterable[Candidate], positives: list[World], negatives: list[World]) -> list[Candidate]:
    return [
        candidate
        for candidate in candidates
        if all(world in candidate.extension for world in positives)
        and all(world not in candidate.extension for world in negatives)
    ]


def choose_weakness(candidates: list[Candidate], rng: random.Random) -> Candidate:
    max_weakness = max(candidate.weakness for candidate in candidates)
    tied = [candidate for candidate in candidates if candidate.weakness == max_weakness]
    return rng.choice(tied)


def choose_simplicity(candidates: list[Candidate], rng: random.Random) -> Candidate:
    min_length = min(candidate.form_length for candidate in candidates)
    tied = [candidate for candidate in candidates if candidate.form_length == min_length]
    return rng.choice(tied)


def choose_random(candidates: list[Candidate], rng: random.Random) -> Candidate:
    return rng.choice(candidates)


def jaccard(left: frozenset[World], right: frozenset[World]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def accuracy(chosen: frozenset[World], target: frozenset[World], worlds: list[World]) -> float:
    correct = 0
    for world in worlds:
        correct += (world in chosen) == (world in target)
    return correct / len(worlds)


def run_trial(
    *,
    rng: random.Random,
    worlds: list[World],
    base_candidates: list[Candidate],
    selectors: Mapping[str, Callable[[list[Candidate], random.Random], Candidate]],
    train_positives: int,
    train_negatives: int,
    include_memorizer: bool,
) -> list[TrialResult]:
    one_feature_targets = [candidate for candidate in base_candidates if " & " not in candidate.name]
    target = rng.choice(one_feature_targets)
    positive_pool = list(target.extension)
    negative_pool = [world for world in worlds if world not in target.extension]
    positives = rng.sample(positive_pool, train_positives)
    negatives = rng.sample(negative_pool, train_negatives)
    candidate_pool = add_memorizer(base_candidates, positives) if include_memorizer else base_candidates
    candidates = consistent(candidate_pool, positives, negatives)

    results: list[TrialResult] = []
    for selector_name, selector in selectors.items():
        chosen = selector(candidates, rng)
        results.append(
            TrialResult(
                selector=selector_name,
                train_positives=train_positives,
                train_negatives=train_negatives,
                target=target.name,
                chosen=chosen.name,
                chosen_form_length=chosen.form_length,
                chosen_weakness=chosen.weakness,
                jaccard=jaccard(chosen.extension, target.extension),
                accuracy=accuracy(chosen.extension, target.extension, worlds),
            )
        )
    return results


def summarize(results: list[TrialResult]) -> dict[str, object]:
    by_selector: dict[str, list[TrialResult]] = {}
    for result in results:
        by_selector.setdefault(result.selector, []).append(result)

    return {
        selector: {
            "trials": len(items),
            "mean_jaccard": mean(item.jaccard for item in items),
            "mean_accuracy": mean(item.accuracy for item in items),
            "mean_form_length": mean(item.chosen_form_length for item in items),
            "mean_weakness": mean(item.chosen_weakness for item in items),
            "memorizer_rate": mean(1.0 if item.chosen == "memorize_observed_positives" else 0.0 for item in items),
        }
        for selector, items in sorted(by_selector.items())
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", type=int, default=6)
    parser.add_argument("--trials", type=int, default=500)
    parser.add_argument("--train-positives", type=int, default=3)
    parser.add_argument("--train-negatives", type=int, default=3)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-memorizer", action="store_true", help="Remove the short memorizer candidate.")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    worlds = all_worlds(args.features)
    base_candidates = reusable_candidates(worlds, args.features)
    selectors = {
        "random": choose_random,
        "simplicity": choose_simplicity,
        "weakness": choose_weakness,
    }

    results: list[TrialResult] = []
    for _ in range(args.trials):
        results.extend(
            run_trial(
                rng=rng,
                worlds=worlds,
                base_candidates=base_candidates,
                selectors=selectors,
                train_positives=args.train_positives,
                train_negatives=args.train_negatives,
                include_memorizer=not args.no_memorizer,
            )
        )

    payload = {
        "manifest": {
            "features": args.features,
            "trials": args.trials,
            "train_positives": args.train_positives,
            "train_negatives": args.train_negatives,
            "seed": args.seed,
            "world_count": len(worlds),
            "base_candidate_count": len(base_candidates),
            "include_memorizer": not args.no_memorizer,
        },
        "summary": summarize(results),
        "results": [asdict(result) for result in results],
    }

    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
