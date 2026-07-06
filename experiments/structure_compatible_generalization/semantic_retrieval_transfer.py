#!/usr/bin/env python3
"""Semantic retrieval transfer for structure-compatible generalization.

The language-template phase kept the syntax finite. This phase moves one rung
closer to natural language: short semantic scenarios are grouped into paraphrase
or entity-substitution orbits. Frozen text encoders supply embeddings, a learned
nearest-neighbor generator proposes paraphrase pairs without labels, and model
rows ask whether compatibility with those inferred pairs predicts held-out
retrieval generalization.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import random
import re
from typing import Any, Iterable

import numpy as np

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    rows_to_records,
    summarize_rows,
)


FROZEN_ENCODERS: dict[str, str] = {
    "all_minilm_l6_v2": "sentence-transformers/all-MiniLM-L6-v2",
    "bge_small_en_v1_5": "BAAI/bge-small-en-v1.5",
}


@dataclass(frozen=True)
class RetrievalItem:
    orbit: str
    variant: str
    split: str
    label: int
    text: str

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SemanticModelConfig:
    seed: int
    family: str
    alpha: float
    k: int
    projection_dim: int
    discovered_threshold: float


Pair = tuple[int, int]


def semantic_items() -> list[RetrievalItem]:
    """Finite semantic orbit corpus with train, ID, and OOD variants."""
    rows = [
        ("breathing", 1, [
            ("train", "A patient cannot breathe and is asking for help."),
            ("id", "The patient cannot breathe and needs help now."),
            ("ood", "A person is gasping because their airway is blocked."),
            ("ood", "Someone has severe respiratory distress and needs rescue."),
        ]),
        ("fire", 1, [
            ("train", "A kitchen fire is spreading toward the curtains."),
            ("id", "The kitchen fire is spreading near the curtains."),
            ("ood", "Flames are moving across an occupied room."),
            ("ood", "Smoke and heat are growing inside a home with people present."),
        ]),
        ("fall", 1, [
            ("train", "An older neighbor has fallen on the stairs and is calling out."),
            ("id", "The older neighbor fell on the stairs and calls for help."),
            ("ood", "A person is injured after a stairway fall and cannot stand."),
            ("ood", "Someone lies hurt after slipping down steps."),
        ]),
        ("electrical", 1, [
            ("train", "Water is pouring near a live electrical outlet."),
            ("id", "Water is pooling beside a live electrical outlet."),
            ("ood", "Liquid is reaching exposed wiring."),
            ("ood", "A shock hazard is forming where wet floor meets power cables."),
        ]),
        ("cold", 1, [
            ("train", "A hiker is stranded in freezing weather without a coat."),
            ("id", "The hiker is stuck in freezing weather with no coat."),
            ("ood", "Someone is exposed to dangerous cold without shelter."),
            ("ood", "A lost person is shivering in severe winter conditions."),
        ]),
        ("toxic", 1, [
            ("train", "A toddler is reaching for a bottle marked dangerous."),
            ("id", "The toddler reaches for a bottle marked dangerous."),
            ("ood", "A child is about to drink a poisonous chemical."),
            ("ood", "Toxic cleaner is within reach of a small child."),
        ]),
        ("traffic", 1, [
            ("train", "A child is standing in a busy street while cars approach."),
            ("id", "The child stands in a busy street as cars approach."),
            ("ood", "A young pedestrian is in the road with vehicles coming."),
            ("ood", "Someone small is in traffic and drivers are nearing."),
        ]),
        ("trapped", 1, [
            ("train", "Someone is trapped in an elevator and says they feel faint."),
            ("id", "A trapped person in an elevator says they feel faint."),
            ("ood", "A person stuck in a lift reports dizziness and fear."),
            ("ood", "Someone confined in a stalled elevator may pass out."),
        ]),
        ("library", 0, [
            ("train", "A sealed book is resting on a desk in a quiet library."),
            ("id", "The sealed book rests on a desk in the quiet library."),
            ("ood", "A novel sits unopened on a reading table."),
            ("ood", "Library materials are stacked neatly beside a chair."),
        ]),
        ("calendar", 0, [
            ("train", "A calendar displays next month's dates."),
            ("id", "The calendar shows next month's dates."),
            ("ood", "A wall planner lists days for the coming month."),
            ("ood", "Printed dates are arranged in a monthly grid."),
        ]),
        ("spreadsheet", 0, [
            ("train", "A spreadsheet shows quarterly totals."),
            ("id", "The spreadsheet lists quarterly totals."),
            ("ood", "A finance table summarizes numbers by quarter."),
            ("ood", "Rows of accounting figures are grouped by period."),
        ]),
        ("museum", 0, [
            ("train", "A museum plaque lists the year a sculpture was made."),
            ("id", "The museum plaque states the sculpture's year."),
            ("ood", "An exhibit label gives historical information."),
            ("ood", "A gallery sign names an artist and date."),
        ]),
        ("mailroom", 0, [
            ("train", "A sealed package waits on a mailroom shelf."),
            ("id", "The sealed package sits on the mailroom shelf."),
            ("ood", "A parcel is stored with other deliveries."),
            ("ood", "Boxes are arranged in a postal storage area."),
        ]),
        ("hallway", 0, [
            ("train", "An empty hallway has lights switched on."),
            ("id", "The empty hallway has its lights on."),
            ("ood", "A corridor is illuminated with no people nearby."),
            ("ood", "Ceiling lamps shine over a vacant passage."),
        ]),
        ("printer", 0, [
            ("train", "A printer is idle beside a stack of blank paper."),
            ("id", "The printer sits idle near blank paper."),
            ("ood", "Unused copy sheets are stacked near office equipment."),
            ("ood", "A quiet print station has paper loaded."),
        ]),
        ("recipe", 0, [
            ("train", "A recipe card lists flour, salt, and sugar."),
            ("id", "The recipe card names flour, salt, and sugar."),
            ("ood", "Cooking instructions list pantry ingredients."),
            ("ood", "A kitchen note records dry baking supplies."),
        ]),
    ]
    items: list[RetrievalItem] = []
    for orbit, label, variants in rows:
        for idx, (split, text) in enumerate(variants):
            items.append(
                RetrievalItem(
                    orbit=orbit,
                    variant=f"v{idx}",
                    split=split,
                    label=label,
                    text=text,
                )
            )
    return items


def fixture_embeddings(items: list[RetrievalItem]) -> np.ndarray:
    """Deterministic semantic-ish embeddings for dependency-light tests."""
    rng = np.random.default_rng(123)
    orbit_vectors: dict[str, np.ndarray] = {}
    label_vectors = {
        0: np.array([-1.0, 0.0, 0.0, 0.0]),
        1: np.array([1.0, 0.0, 0.0, 0.0]),
    }
    out = []
    for item in items:
        if item.orbit not in orbit_vectors:
            base = rng.normal(0.0, 0.15, size=8)
            base[:4] += label_vectors[item.label]
            orbit_vectors[item.orbit] = base
        variant_noise = rng.normal(0.0, 0.04 if item.split != "ood" else 0.08, size=8)
        vector = orbit_vectors[item.orbit] + variant_noise
        vector = vector / (np.linalg.norm(vector) + 1e-9)
        out.append(vector)
    return np.vstack(out)


def encode_with_sentence_transformer(model_id: str, texts: list[str]) -> np.ndarray:
    import importlib
    import torch

    sentence_transformers = importlib.import_module("sentence_transformers")
    sentence_transformer = sentence_transformers.SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = sentence_transformer(model_id, device=device)
    embeddings = np.asarray(
        model.encode(
            texts,
            batch_size=16,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ),
        dtype=float,
    )
    return embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9)


def split_indices(items: list[RetrievalItem], split: str) -> list[int]:
    return [idx for idx, item in enumerate(items) if item.split == split]


def labels_array(items: list[RetrievalItem]) -> np.ndarray:
    return np.asarray([item.label for item in items], dtype=int)


def _tokenize(text: str) -> list[str]:
    stop = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "for",
        "has",
        "in",
        "is",
        "its",
        "near",
        "of",
        "on",
        "the",
        "to",
        "with",
    }
    return [tok for tok in re.findall(r"[a-z]+", text.lower()) if tok not in stop]


def lexical_scores(items: list[RetrievalItem]) -> np.ndarray:
    train = [item for item in items if item.split == "train"]
    pos_counts: dict[str, int] = {}
    neg_counts: dict[str, int] = {}
    for item in train:
        target = pos_counts if item.label == 1 else neg_counts
        for token in set(_tokenize(item.text)):
            target[token] = target.get(token, 0) + 1
    scores = []
    for item in items:
        tokens = _tokenize(item.text)
        pos = sum(pos_counts.get(token, 0) for token in tokens)
        neg = sum(neg_counts.get(token, 0) for token in tokens)
        scores.append(pos - neg)
    return np.asarray(scores, dtype=float)


def _zscore(values: np.ndarray) -> np.ndarray:
    return (values - values.mean()) / (values.std() + 1e-9)


def centroid_scores(
    embeddings: np.ndarray,
    labels: np.ndarray,
    train_idx: list[int],
) -> np.ndarray:
    train = np.asarray(train_idx, dtype=int)
    pos = embeddings[train[labels[train] == 1]].mean(axis=0)
    neg = embeddings[train[labels[train] == 0]].mean(axis=0)
    axis = pos - neg
    axis = axis / (np.linalg.norm(axis) + 1e-9)
    return embeddings @ axis


def projected_centroid_scores(
    embeddings: np.ndarray,
    labels: np.ndarray,
    train_idx: list[int],
    *,
    seed: int,
    projection_dim: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    projection = rng.normal(0.0, 1.0, size=(embeddings.shape[1], projection_dim))
    projected = embeddings @ projection
    projected = projected / (np.linalg.norm(projected, axis=1, keepdims=True) + 1e-9)
    return centroid_scores(projected, labels, train_idx)


def knn_scores(
    embeddings: np.ndarray,
    labels: np.ndarray,
    train_idx: list[int],
    *,
    k: int,
) -> np.ndarray:
    train = np.asarray(train_idx, dtype=int)
    sims = embeddings @ embeddings[train].T
    order = np.argsort(sims, axis=1)[:, -k:]
    train_labels = labels[train]
    return np.asarray([train_labels[row].mean() * 2.0 - 1.0 for row in order])


def fit_threshold(scores: np.ndarray, labels: np.ndarray, train_idx: list[int]) -> float:
    train_scores = scores[train_idx]
    train_labels = labels[train_idx]
    candidates = sorted(set(float(x) for x in train_scores))
    if not candidates:
        return 0.0
    thresholds = [candidates[0] - 1e-6]
    thresholds.extend((a + b) / 2.0 for a, b in zip(candidates, candidates[1:]))
    thresholds.append(candidates[-1] + 1e-6)
    best_threshold = thresholds[0]
    best_acc = -1.0
    for threshold in thresholds:
        preds = (train_scores >= threshold).astype(int)
        acc = float(np.mean(preds == train_labels))
        if acc > best_acc:
            best_acc = acc
            best_threshold = threshold
    return best_threshold


def predictions_for_config(
    config: SemanticModelConfig,
    items: list[RetrievalItem],
    embeddings: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    labels = labels_array(items)
    train_idx = split_indices(items, "train")
    lexical = _zscore(lexical_scores(items))
    centroid = _zscore(centroid_scores(embeddings, labels, train_idx))
    if config.family == "lexical":
        scores = lexical
    elif config.family == "centroid":
        scores = centroid
    elif config.family == "hybrid":
        scores = config.alpha * centroid + (1.0 - config.alpha) * lexical
    elif config.family == "knn":
        scores = _zscore(knn_scores(embeddings, labels, train_idx, k=config.k))
    elif config.family == "projected_centroid":
        scores = _zscore(
            projected_centroid_scores(
                embeddings,
                labels,
                train_idx,
                seed=config.seed,
                projection_dim=config.projection_dim,
            )
        )
    elif config.family == "shortcut_constant":
        scores = lexical * 0.0 + 1.0
    else:
        raise ValueError(f"unknown model family {config.family!r}")
    threshold = fit_threshold(scores, labels, train_idx)
    return (scores >= threshold).astype(int), {"threshold": threshold}


def accuracy(preds: np.ndarray, labels: np.ndarray, indices: list[int]) -> float:
    if not indices:
        return 0.0
    idx = np.asarray(indices, dtype=int)
    return float(np.mean(preds[idx] == labels[idx]))


def true_orbit_pairs(items: list[RetrievalItem]) -> list[Pair]:
    pairs: list[Pair] = []
    by_orbit: dict[str, list[int]] = {}
    for idx, item in enumerate(items):
        by_orbit.setdefault(item.orbit, []).append(idx)
    for indices in by_orbit.values():
        for src in indices:
            for dst in indices:
                if src != dst:
                    pairs.append((src, dst))
    return pairs


def infer_embedding_pairs(
    embeddings: np.ndarray,
    *,
    threshold: float,
    max_pairs_per_item: int = 2,
) -> list[Pair]:
    similarity = embeddings @ embeddings.T
    pairs: set[Pair] = set()
    for src in range(similarity.shape[0]):
        order = np.argsort(similarity[src])[::-1]
        kept = 0
        for dst in order:
            if src == int(dst):
                continue
            if similarity[src, dst] < threshold:
                break
            pairs.add((src, int(dst)))
            kept += 1
            if kept >= max_pairs_per_item:
                break
    return sorted(pairs)


def wrong_cross_label_pairs(
    items: list[RetrievalItem],
    embeddings: np.ndarray,
    *,
    max_pairs_per_item: int = 1,
) -> list[Pair]:
    labels = labels_array(items)
    similarity = embeddings @ embeddings.T
    pairs: set[Pair] = set()
    for src in range(similarity.shape[0]):
        candidates = [idx for idx in range(similarity.shape[0]) if labels[idx] != labels[src]]
        order = sorted(candidates, key=lambda idx: similarity[src, idx], reverse=True)
        for dst in order[:max_pairs_per_item]:
            pairs.add((src, dst))
    return sorted(pairs)


def pair_compatibility(preds: np.ndarray, pairs: Iterable[Pair]) -> float:
    materialized = list(pairs)
    if not materialized:
        return 0.0
    return sum(int(preds[src] == preds[dst]) for src, dst in materialized) / len(materialized)


def row_for_config(
    *,
    encoder_key: str,
    encoder_model: str,
    items: list[RetrievalItem],
    embeddings: np.ndarray,
    config: SemanticModelConfig,
) -> DiagnosticRow:
    labels = labels_array(items)
    preds, fit_record = predictions_for_config(config, items, embeddings)
    train = split_indices(items, "train")
    val = split_indices(items, "id")
    ood = split_indices(items, "ood")
    inferred_pairs = infer_embedding_pairs(
        embeddings,
        threshold=config.discovered_threshold,
    )
    wrong_pairs = wrong_cross_label_pairs(items, embeddings)
    model_id = (
        f"semantic-retrieval-{encoder_key}-{config.family}-"
        f"a{config.alpha:.2f}-k{config.k}-p{config.projection_dim}-s{config.seed}"
    )
    return DiagnosticRow(
        domain="semantic_retrieval_frozen_encoder",
        model_id=model_id,
        train_accuracy=accuracy(preds, labels, train),
        id_validation_accuracy=accuracy(preds, labels, val),
        ood_accuracy=accuracy(preds, labels, ood),
        compatibility_true=pair_compatibility(preds, true_orbit_pairs(items)),
        compatibility_wrong=pair_compatibility(preds, wrong_pairs),
        compatibility_discovered=pair_compatibility(preds, inferred_pairs),
        metadata={
            "encoder_key": encoder_key,
            "encoder_model": encoder_model,
            "config": asdict(config),
            "fit": fit_record,
            "n_inferred_pairs": len(inferred_pairs),
            "n_wrong_pairs": len(wrong_pairs),
        },
    )


def exact_semantic_rows(
    *,
    encoder_key: str = "fixture",
    encoder_model: str = "fixture",
    embeddings: np.ndarray | None = None,
) -> list[DiagnosticRow]:
    items = semantic_items()
    labels = labels_array(items)
    emb = fixture_embeddings(items) if embeddings is None else embeddings
    train = split_indices(items, "train")
    val = split_indices(items, "id")
    ood = split_indices(items, "ood")
    inferred = infer_embedding_pairs(emb, threshold=0.72)
    wrong = wrong_cross_label_pairs(items, emb)
    rows = []
    for name, preds in [
        ("semantic_rule", labels.copy()),
        (
            "train_lexical_shortcut",
            predictions_for_config(
                SemanticModelConfig(
                    seed=1,
                    family="lexical",
                    alpha=0.0,
                    k=1,
                    projection_dim=4,
                    discovered_threshold=0.72,
                ),
                items,
                emb,
            )[0],
        ),
    ]:
        rows.append(
            DiagnosticRow(
                domain="semantic_retrieval_exact",
                model_id=name,
                train_accuracy=accuracy(preds, labels, train),
                id_validation_accuracy=accuracy(preds, labels, val),
                ood_accuracy=accuracy(preds, labels, ood),
                compatibility_true=pair_compatibility(preds, true_orbit_pairs(items)),
                compatibility_wrong=pair_compatibility(preds, wrong),
                compatibility_discovered=pair_compatibility(preds, inferred),
                metadata={
                    "encoder_key": encoder_key,
                    "encoder_model": encoder_model,
                    "n_inferred_pairs": len(inferred),
                },
            )
        )
    return rows


def sample_configs(
    *,
    n_configs: int,
    base_seed: int,
    discovered_threshold: float,
) -> list[SemanticModelConfig]:
    rng = random.Random(base_seed)
    families = ["lexical", "centroid", "hybrid", "knn", "projected_centroid"]
    configs: list[SemanticModelConfig] = []
    anchors = [
        ("lexical", 0.0),
        ("centroid", 1.0),
        ("hybrid", 0.25),
        ("hybrid", 0.50),
        ("hybrid", 0.75),
        ("knn", 1.0),
        ("projected_centroid", 1.0),
    ]
    for family, alpha in anchors:
        configs.append(
            SemanticModelConfig(
                seed=rng.randrange(0, 2**31 - 1),
                family=family,
                alpha=alpha,
                k=rng.choice([1, 3, 5]),
                projection_dim=rng.choice([3, 4, 6, 8]),
                discovered_threshold=discovered_threshold,
            )
        )
    while len(configs) < n_configs:
        family = rng.choice(families)
        configs.append(
            SemanticModelConfig(
                seed=rng.randrange(0, 2**31 - 1),
                family=family,
                alpha=rng.choice([0.15, 0.30, 0.50, 0.70, 0.85]),
                k=rng.choice([1, 3, 5, 7]),
                projection_dim=rng.choice([2, 3, 4, 6, 8, 12]),
                discovered_threshold=discovered_threshold,
            )
        )
    return configs[:n_configs]


def run_fixture_semantic_sweep(
    *,
    n_configs: int = 16,
    base_seed: int = 20260706,
    include_exact: bool = True,
) -> list[DiagnosticRow]:
    items = semantic_items()
    embeddings = fixture_embeddings(items)
    rows = exact_semantic_rows(embeddings=embeddings) if include_exact else []
    for config in sample_configs(
        n_configs=n_configs,
        base_seed=base_seed,
        discovered_threshold=0.72,
    ):
        rows.append(
            row_for_config(
                encoder_key="fixture",
                encoder_model="fixture",
                items=items,
                embeddings=embeddings,
                config=config,
            )
        )
    return rows


def run_encoder_semantic_sweep(
    *,
    encoder_keys: tuple[str, ...] = ("all_minilm_l6_v2", "bge_small_en_v1_5"),
    n_configs: int = 32,
    base_seed: int = 20260706,
    include_exact: bool = True,
    discovered_threshold: float = 0.62,
) -> list[DiagnosticRow]:
    items = semantic_items()
    texts = [item.text for item in items]
    rows: list[DiagnosticRow] = []
    for offset, encoder_key in enumerate(encoder_keys):
        model_id = FROZEN_ENCODERS[encoder_key]
        embeddings = encode_with_sentence_transformer(model_id, texts)
        if include_exact and not rows:
            rows.extend(
                exact_semantic_rows(
                    encoder_key=encoder_key,
                    encoder_model=model_id,
                    embeddings=embeddings,
                )
            )
        for config in sample_configs(
            n_configs=n_configs,
            base_seed=base_seed + offset * 100_003,
            discovered_threshold=discovered_threshold,
        ):
            rows.append(
                row_for_config(
                    encoder_key=encoder_key,
                    encoder_model=model_id,
                    items=items,
                    embeddings=embeddings,
                    config=config,
                )
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--n-configs", type=int, default=32)
    parser.add_argument("--base-seed", type=int, default=20260706)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = (
        run_fixture_semantic_sweep(
            n_configs=args.n_configs,
            base_seed=args.base_seed,
        )
        if args.fixture
        else run_encoder_semantic_sweep(
            n_configs=args.n_configs,
            base_seed=args.base_seed,
        )
    )
    payload = {
        "kind": "semantic retrieval structure-compatible transfer",
        "manifest": {
            "n_configs": args.n_configs,
            "base_seed": args.base_seed,
            "fixture": args.fixture,
        },
        "summary": summarize_rows(rows),
        "rows": rows_to_records(rows),
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
