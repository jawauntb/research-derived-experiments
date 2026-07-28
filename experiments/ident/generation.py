"""Deterministic IDENT dataset generation with fixed train/dev/test splits."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from experiments.ident.domains import (
    generate_boolean_causal_item,
    generate_finite_state_item,
    generate_small_program_item,
)
from experiments.ident.schemas import IdentItem
from experiments.ident.validation import validate_item, validate_split

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "splits"

DOMAIN_GENERATORS = {
    "boolean_causal": generate_boolean_causal_item,
    "finite_state": generate_finite_state_item,
    "small_programs": generate_small_program_item,
}

# Default v1 mix: Boolean-heavy, with two additional formal domains.
DEFAULT_DOMAIN_MIX = (
    ("boolean_causal", 0.60),
    ("finite_state", 0.20),
    ("small_programs", 0.20),
)


def _choose_domain(rng: random.Random) -> str:
    r = rng.random()
    acc = 0.0
    for name, weight in DEFAULT_DOMAIN_MIX:
        acc += weight
        if r <= acc:
            return name
    return DEFAULT_DOMAIN_MIX[-1][0]


def generate_item(
    *,
    item_id: str,
    seed: int,
    domain: str | None = None,
    k: int | None = None,
) -> IdentItem:
    rng = random.Random(seed)
    domain_name = domain or _choose_domain(rng)
    # Prefer pairs (k=2) so one-step separators identify; occasional k=3/4 stress items.
    hyp_k = k if k is not None else rng.choice([2, 2, 2, 2, 2, 3, 3, 4])
    gen = DOMAIN_GENERATORS[domain_name]
    for attempt in range(32):
        item = gen(item_id=item_id, rng=random.Random(seed + 1000 * attempt), k=hyp_k)
        result = validate_item(item)
        if result.ok:
            return item
    # Last attempt: raise with validation detail.
    item = gen(item_id=item_id, rng=random.Random(seed), k=2)
    result = validate_item(item)
    raise RuntimeError(
        f"could not generate valid item {item_id}: {result.errors}"
    )


def generate_split(
    *,
    n: int,
    seed: int,
    prefix: str,
) -> list[IdentItem]:
    items: list[IdentItem] = []
    for i in range(n):
        item_id = f"{prefix}_{i:06d}"
        items.append(generate_item(item_id=item_id, seed=seed + i))
    result = validate_split(items)
    if result.failed:
        # Surface first few errors.
        preview = "; ".join(result.errors[:5])
        raise RuntimeError(f"split validation failed: {preview}")
    return items


def write_jsonl(path: Path, items: list[IdentItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(item.to_annotated_dict(), sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[IdentItem]:
    from experiments.ident.schemas import item_from_dict

    items: list[IdentItem] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            items.append(item_from_dict(json.loads(line)))
    return items


def build_default_dataset(
    *,
    seed: int = 20260727,
    train_n: int = 700,
    dev_n: int = 150,
    test_n: int = 150,
    out_dir: Path | None = None,
) -> dict[str, Path]:
    """Produce the fixed v1 IDENT splits (1000 items total)."""
    out = out_dir or DATA_DIR
    train = generate_split(n=train_n, seed=seed, prefix="train")
    dev = generate_split(n=dev_n, seed=seed + 10_000, prefix="dev")
    test = generate_split(n=test_n, seed=seed + 20_000, prefix="test")

    paths = {
        "train": out / "train.jsonl",
        "dev": out / "dev.jsonl",
        "test": out / "test.jsonl",
    }
    write_jsonl(paths["train"], train)
    write_jsonl(paths["dev"], dev)
    write_jsonl(paths["test"], test)

    manifest = {
        "seed": seed,
        "counts": {"train": train_n, "dev": dev_n, "test": test_n},
        "domain_mix": dict(DEFAULT_DOMAIN_MIX),
        "paths": {k: str(v.relative_to(ROOT.parent.parent)) for k, v in paths.items()},
    }
    (out / "split_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate IDENT benchmark splits")
    parser.add_argument("--seed", type=int, default=20260727)
    parser.add_argument("--train-n", type=int, default=700)
    parser.add_argument("--dev-n", type=int, default=150)
    parser.add_argument("--test-n", type=int, default=150)
    parser.add_argument("--out-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args(argv)
    paths = build_default_dataset(
        seed=args.seed,
        train_n=args.train_n,
        dev_n=args.dev_n,
        test_n=args.test_n,
        out_dir=args.out_dir,
    )
    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
