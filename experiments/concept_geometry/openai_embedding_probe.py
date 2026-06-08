#!/usr/bin/env python3
"""Probe concept-set geometry with OpenAI embeddings.

Raw embeddings are written only to the requested output path, normally under
ignored `artifacts/`. The committed summaries should be human-scale metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "text-embedding-3-small"


@dataclass(frozen=True)
class Concept:
    id: str
    label: str
    category: str
    prompt: str


def load_concepts(path: Path) -> list[Concept]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Concept(**item) for item in data]


def deterministic_embedding(text: str, dimensions: int = 64) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        digest = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        for byte in digest:
            values.append((byte / 127.5) - 1.0)
            if len(values) == dimensions:
                break
        counter += 1
    norm = math.sqrt(sum(value * value for value in values))
    return [value / norm for value in values]


def openai_embeddings(concepts: list[Concept], model: str) -> list[list[float]]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required unless --dry-run is used")

    body = json.dumps(
        {
            "model": model,
            "input": [concept.prompt for concept in concepts],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        message = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI embeddings request failed: {error.code} {message}") from error

    return [item["embedding"] for item in sorted(payload["data"], key=lambda item: item["index"])]


def cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return dot / (left_norm * right_norm)


def pairwise_similarities(concepts: list[Concept], embeddings: list[list[float]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, left in enumerate(concepts):
        for j, right in enumerate(concepts):
            if i >= j:
                continue
            rows.append(
                {
                    "left": left.id,
                    "right": right.id,
                    "left_category": left.category,
                    "right_category": right.category,
                    "same_category": left.category == right.category,
                    "cosine": cosine(embeddings[i], embeddings[j]),
                }
            )
    return rows


def nearest_neighbors(
    concepts: list[Concept],
    embeddings: list[list[float]],
    top_k: int,
) -> dict[str, list[dict[str, Any]]]:
    neighbors: dict[str, list[dict[str, Any]]] = {}
    for i, concept in enumerate(concepts):
        scored = []
        for j, other in enumerate(concepts):
            if i == j:
                continue
            scored.append(
                {
                    "id": other.id,
                    "label": other.label,
                    "category": other.category,
                    "cosine": cosine(embeddings[i], embeddings[j]),
                }
            )
        neighbors[concept.id] = sorted(scored, key=lambda item: item["cosine"], reverse=True)[:top_k]
    return neighbors


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def summarize(concepts: list[Concept], embeddings: list[list[float]], top_k: int) -> dict[str, Any]:
    pairs = pairwise_similarities(concepts, embeddings)
    within = [row["cosine"] for row in pairs if row["same_category"]]
    across = [row["cosine"] for row in pairs if not row["same_category"]]
    neighbors = nearest_neighbors(concepts, embeddings, top_k)
    same_category_neighbor_hits = [
        sum(1 for neighbor in concept_neighbors if neighbor["category"] == concept.category) / len(concept_neighbors)
        for concept in concepts
        for concept_neighbors in [neighbors[concept.id]]
        if concept_neighbors
    ]
    return {
        "concept_count": len(concepts),
        "category_count": len({concept.category for concept in concepts}),
        "within_category_mean_cosine": mean(within),
        "across_category_mean_cosine": mean(across),
        "category_separation": mean(within) - mean(across),
        "mean_top_k_same_category_rate": mean(same_category_neighbor_hits),
        "nearest_neighbors": neighbors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts", type=Path, required=True)
    parser.add_argument("--model", default=os.environ.get("GEOMETRY_EMBEDDING_MODEL", DEFAULT_MODEL))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    concepts = load_concepts(args.concepts)
    embeddings = (
        [deterministic_embedding(concept.prompt) for concept in concepts]
        if args.dry_run
        else openai_embeddings(concepts, args.model)
    )
    summary = summarize(concepts, embeddings, args.top_k)
    payload = {
        "manifest": {
            "model": "deterministic-dry-run" if args.dry_run else args.model,
            "concept_source": str(args.concepts),
            "top_k": args.top_k,
            "dry_run": args.dry_run,
        },
        "concepts": [asdict(concept) for concept in concepts],
        "summary": summary,
        "embeddings": {
            concept.id: embedding for concept, embedding in zip(concepts, embeddings)
        },
    }
    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(json.dumps({"manifest": payload["manifest"], "summary": summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
