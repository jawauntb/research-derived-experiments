#!/usr/bin/env python3
"""Symbolic symmetry/weakness benchmark.

The benchmark constructs cyclic transformation tasks where a short local rule and a
global invariant rule have identical training loss. The global rule is selected by
symmetry weakness: how many transformations of the domain leave the candidate
function equivariant.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Callable


@dataclass(frozen=True)
class Example:
    x: int
    y: int


@dataclass(frozen=True)
class Candidate:
    name: str
    predictions: tuple[int, ...]
    form_length: int
    family: str

    def predict(self, x: int) -> int:
        return self.predictions[x]


@dataclass(frozen=True)
class Trial:
    modulus: int
    offset: int
    train_window: int
    train_examples: tuple[Example, ...]
    ood_inputs: tuple[int, ...]


@dataclass(frozen=True)
class CandidateMetrics:
    name: str
    family: str
    train_accuracy: float
    full_accuracy: float
    ood_accuracy: float
    form_length: int
    compression_length: int
    flatness_proxy: int
    equivariance_count: int
    weakness: int


@dataclass(frozen=True)
class SelectionResult:
    selector: str
    modulus: int
    offset: int
    train_window: int
    candidate: str
    family: str
    train_accuracy: float
    full_accuracy: float
    ood_accuracy: float
    form_length: int
    compression_length: int
    flatness_proxy: int
    equivariance_count: int
    weakness: int


def modular_shift(x: int, offset: int, modulus: int) -> int:
    return (x + offset) % modulus


def make_trial(*, rng: random.Random, modulus: int, train_window: int) -> Trial:
    if not 1 < train_window < modulus:
        raise ValueError("train_window must be in 2..modulus-1")
    offset = rng.randrange(1, modulus)
    train_examples = tuple(
        Example(x=x, y=modular_shift(x, offset, modulus))
        for x in range(train_window)
    )
    return Trial(
        modulus=modulus,
        offset=offset,
        train_window=train_window,
        train_examples=train_examples,
        ood_inputs=tuple(range(train_window, modulus)),
    )


def global_shift_candidate(modulus: int, offset: int) -> Candidate:
    return Candidate(
        name=f"global_shift_{offset}",
        predictions=tuple(modular_shift(x, offset, modulus) for x in range(modulus)),
        form_length=5,
        family="invariant",
    )


def local_prefix_patch_candidate(trial: Trial) -> Candidate:
    train_outputs = {example.x: example.y for example in trial.train_examples}
    predictions = tuple(
        train_outputs[x] if x in train_outputs else x
        for x in range(trial.modulus)
    )
    return Candidate(
        name="local_prefix_patch",
        predictions=predictions,
        form_length=3,
        family="local_patch",
    )


def memorizer_candidate(trial: Trial) -> Candidate:
    train_outputs = {example.x: example.y for example in trial.train_examples}
    predictions = tuple(
        train_outputs[x] if x in train_outputs else 0
        for x in range(trial.modulus)
    )
    return Candidate(
        name="memorize_train_examples",
        predictions=predictions,
        form_length=trial.train_window + 2,
        family="memorizer",
    )


def wrong_shift_candidates(trial: Trial) -> list[Candidate]:
    return [
        global_shift_candidate(trial.modulus, offset)
        for offset in range(1, trial.modulus)
        if offset != trial.offset
    ]


def candidate_pool(trial: Trial) -> list[Candidate]:
    return [
        local_prefix_patch_candidate(trial),
        memorizer_candidate(trial),
        global_shift_candidate(trial.modulus, trial.offset),
        *wrong_shift_candidates(trial),
    ]


def accuracy_on_inputs(
    candidate: Candidate,
    *,
    inputs: tuple[int, ...],
    offset: int,
    modulus: int,
) -> float:
    if not inputs:
        return 1.0
    correct = sum(
        1
        for x in inputs
        if candidate.predict(x) == modular_shift(x, offset, modulus)
    )
    return correct / len(inputs)


def train_accuracy(candidate: Candidate, trial: Trial) -> float:
    return accuracy_on_inputs(
        candidate,
        inputs=tuple(example.x for example in trial.train_examples),
        offset=trial.offset,
        modulus=trial.modulus,
    )


def full_accuracy(candidate: Candidate, trial: Trial) -> float:
    return accuracy_on_inputs(
        candidate,
        inputs=tuple(range(trial.modulus)),
        offset=trial.offset,
        modulus=trial.modulus,
    )


def ood_accuracy(candidate: Candidate, trial: Trial) -> float:
    return accuracy_on_inputs(
        candidate,
        inputs=trial.ood_inputs,
        offset=trial.offset,
        modulus=trial.modulus,
    )


def translation_equivariance_count(candidate: Candidate, modulus: int) -> int:
    count = 0
    for translation in range(modulus):
        is_equivariant = all(
            candidate.predict((x + translation) % modulus)
            == (candidate.predict(x) + translation) % modulus
            for x in range(modulus)
        )
        count += int(is_equivariant)
    return count


def metrics_for(candidate: Candidate, trial: Trial) -> CandidateMetrics:
    train_acc = train_accuracy(candidate, trial)
    equivariance_count = translation_equivariance_count(candidate, trial.modulus)
    train_errors = round((1.0 - train_acc) * len(trial.train_examples))
    compression_length = candidate.form_length + 20 * train_errors
    return CandidateMetrics(
        name=candidate.name,
        family=candidate.family,
        train_accuracy=train_acc,
        full_accuracy=full_accuracy(candidate, trial),
        ood_accuracy=ood_accuracy(candidate, trial),
        form_length=candidate.form_length,
        compression_length=compression_length,
        flatness_proxy=trial.modulus - len(trial.train_examples),
        equivariance_count=equivariance_count,
        weakness=equivariance_count,
    )


def consistent_metrics(trial: Trial) -> list[CandidateMetrics]:
    return [
        metrics
        for metrics in (metrics_for(candidate, trial) for candidate in candidate_pool(trial))
        if metrics.train_accuracy == 1.0
    ]


def choose_train_loss(metrics: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    max_train_accuracy = max(item.train_accuracy for item in metrics)
    tied = [item for item in metrics if item.train_accuracy == max_train_accuracy]
    return choose_simplicity(tied, rng)


def choose_simplicity(metrics: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    best = min(item.form_length for item in metrics)
    tied = [item for item in metrics if item.form_length == best]
    return rng.choice(tied)


def choose_compression(metrics: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    best = min(item.compression_length for item in metrics)
    tied = [item for item in metrics if item.compression_length == best]
    return rng.choice(tied)


def choose_flatness(metrics: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    best = max(item.flatness_proxy for item in metrics)
    tied = [item for item in metrics if item.flatness_proxy == best]
    return choose_simplicity(tied, rng)


def choose_weakness(metrics: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    best = max(item.weakness for item in metrics)
    tied = [item for item in metrics if item.weakness == best]
    return choose_compression(tied, rng)


def choose_random(metrics: list[CandidateMetrics], rng: random.Random) -> CandidateMetrics:
    return rng.choice(metrics)


SELECTORS: dict[str, Callable[[list[CandidateMetrics], random.Random], CandidateMetrics]] = {
    "train_loss": choose_train_loss,
    "simplicity": choose_simplicity,
    "compression": choose_compression,
    "flatness_proxy": choose_flatness,
    "weakness": choose_weakness,
    "random": choose_random,
}


def run_trial(*, trial: Trial, rng: random.Random) -> list[SelectionResult]:
    metrics = consistent_metrics(trial)
    results = []
    for selector_name, selector in SELECTORS.items():
        chosen = selector(metrics, rng)
        results.append(
            SelectionResult(
                selector=selector_name,
                modulus=trial.modulus,
                offset=trial.offset,
                train_window=trial.train_window,
                candidate=chosen.name,
                family=chosen.family,
                train_accuracy=chosen.train_accuracy,
                full_accuracy=chosen.full_accuracy,
                ood_accuracy=chosen.ood_accuracy,
                form_length=chosen.form_length,
                compression_length=chosen.compression_length,
                flatness_proxy=chosen.flatness_proxy,
                equivariance_count=chosen.equivariance_count,
                weakness=chosen.weakness,
            )
        )
    return results


def summarize(results: list[SelectionResult]) -> dict[str, dict[str, float | int]]:
    by_selector: dict[str, list[SelectionResult]] = {}
    for result in results:
        by_selector.setdefault(result.selector, []).append(result)
    return {
        selector: {
            "trials": len(items),
            "mean_train_accuracy": mean(item.train_accuracy for item in items),
            "mean_full_accuracy": mean(item.full_accuracy for item in items),
            "mean_ood_accuracy": mean(item.ood_accuracy for item in items),
            "mean_form_length": mean(item.form_length for item in items),
            "mean_compression_length": mean(item.compression_length for item in items),
            "mean_flatness_proxy": mean(item.flatness_proxy for item in items),
            "mean_equivariance_count": mean(item.equivariance_count for item in items),
            "mean_weakness": mean(item.weakness for item in items),
            "invariant_rate": mean(
                1.0 if item.family == "invariant" else 0.0 for item in items
            ),
            "local_patch_rate": mean(
                1.0 if item.family == "local_patch" else 0.0 for item in items
            ),
        }
        for selector, items in sorted(by_selector.items())
    }


def parse_moduli(value: str) -> list[int]:
    moduli = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not moduli:
        raise ValueError("At least one modulus must be provided")
    if any(modulus < 5 for modulus in moduli):
        raise ValueError("All moduli must be >= 5")
    return moduli


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--moduli", default="7,11,13")
    parser.add_argument("--train-window", type=int, default=3)
    parser.add_argument("--trials", type=int, default=300)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    moduli = parse_moduli(args.moduli)
    results: list[SelectionResult] = []
    for _ in range(args.trials):
        modulus = rng.choice(moduli)
        train_window = min(args.train_window, modulus - 1)
        trial = make_trial(rng=rng, modulus=modulus, train_window=train_window)
        results.extend(run_trial(trial=trial, rng=rng))

    payload = {
        "manifest": {
            "moduli": moduli,
            "train_window": args.train_window,
            "trials": args.trials,
            "seed": args.seed,
            "selectors": sorted(SELECTORS),
            "task": "cyclic_prefix_shift",
            "weakness_metric": "translation_equivariance_count",
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
