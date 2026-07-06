#!/usr/bin/env python3
"""OOD-free semantic model selection for structure-compatible generalization."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    row_predictor_values,
    rows_to_records,
    summarize_rows,
)
from experiments.structure_compatible_generalization.semantic_retrieval_transfer import (
    FROZEN_ENCODERS,
    SemanticModelConfig,
    encode_with_sentence_transformer,
    fixture_embeddings,
    row_for_config,
    sample_configs,
    semantic_items,
)


SELECTION_PREDICTORS = [
    "compatibility_discovered",
    "compatibility_true",
    "id_validation_accuracy",
    "train_accuracy",
    "compatibility_wrong",
]
BASELINE_SELECTORS = ["random_candidate", "ood_oracle"]
DEFAULT_THRESHOLDS = (0.50, 0.56, 0.62, 0.68, 0.74)


@dataclass(frozen=True)
class SelectionRecord:
    zoo_id: str
    selector: str
    encoder_key: str
    discovered_threshold: float
    n_candidates: int
    tied_count: int
    selected_ood: float
    selected_train: float
    selected_id: float
    selected_discovered: float
    selected_wrong: float
    oracle_ood: float
    random_mean_ood: float
    regret: float
    lift_vs_random: float

    def to_record(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "SelectionRecord":
        return cls(
            zoo_id=str(record["zoo_id"]),
            selector=str(record["selector"]),
            encoder_key=str(record["encoder_key"]),
            discovered_threshold=float(record["discovered_threshold"]),
            n_candidates=int(record["n_candidates"]),
            tied_count=int(record["tied_count"]),
            selected_ood=float(record["selected_ood"]),
            selected_train=float(record["selected_train"]),
            selected_id=float(record["selected_id"]),
            selected_discovered=float(record["selected_discovered"]),
            selected_wrong=float(record["selected_wrong"]),
            oracle_ood=float(record["oracle_ood"]),
            random_mean_ood=float(record["random_mean_ood"]),
            regret=float(record["regret"]),
            lift_vs_random=float(record["lift_vs_random"]),
        )


def selection_records_from_dicts(records: list[dict[str, Any]]) -> list[SelectionRecord]:
    return [SelectionRecord.from_record(record) for record in records]


def _thresholds(values: tuple[float, ...] | list[float] | None) -> tuple[float, ...]:
    return tuple(values or DEFAULT_THRESHOLDS)


def _selection_zoo_id(
    *,
    encoder_key: str,
    threshold: float,
    threshold_index: int,
    zoo_index: int,
) -> str:
    return f"{encoder_key}:t{threshold_index}:{threshold:.2f}:z{zoo_index:02d}"


def _with_selection_metadata(
    row: DiagnosticRow,
    *,
    zoo_id: str,
    threshold_index: int,
    zoo_index: int,
    configs_per_zoo: int,
) -> DiagnosticRow:
    metadata = dict(row.metadata)
    metadata.update(
        {
            "selection_zoo": zoo_id,
            "selection_threshold_index": threshold_index,
            "selection_zoo_index": zoo_index,
            "selection_configs_per_zoo": configs_per_zoo,
        }
    )
    return replace(row, metadata=metadata)


def run_fixture_selection_control_sweep(
    *,
    thresholds: tuple[float, ...] | list[float] | None = None,
    n_zoos: int = 4,
    configs_per_zoo: int = 12,
    base_seed: int = 20260706,
) -> list[DiagnosticRow]:
    items = semantic_items()
    embeddings = fixture_embeddings(items)
    rows: list[DiagnosticRow] = []
    for threshold_index, threshold in enumerate(_thresholds(thresholds)):
        for zoo_index in range(n_zoos):
            zoo_id = _selection_zoo_id(
                encoder_key="fixture",
                threshold=threshold,
                threshold_index=threshold_index,
                zoo_index=zoo_index,
            )
            seed = base_seed + threshold_index * 100_003 + zoo_index * 10_007
            for config in sample_configs(
                n_configs=configs_per_zoo,
                base_seed=seed,
                discovered_threshold=threshold,
            ):
                row = row_for_config(
                    encoder_key="fixture",
                    encoder_model="fixture",
                    items=items,
                    embeddings=embeddings,
                    config=config,
                )
                rows.append(
                    _with_selection_metadata(
                        row,
                        zoo_id=zoo_id,
                        threshold_index=threshold_index,
                        zoo_index=zoo_index,
                        configs_per_zoo=configs_per_zoo,
                    )
                )
    return rows


def run_encoder_selection_control_sweep(
    *,
    encoder_keys: tuple[str, ...] = ("all_minilm_l6_v2", "bge_small_en_v1_5"),
    thresholds: tuple[float, ...] | list[float] | None = None,
    n_zoos: int = 12,
    configs_per_zoo: int = 12,
    base_seed: int = 20260706,
) -> list[DiagnosticRow]:
    items = semantic_items()
    texts = [item.text for item in items]
    rows: list[DiagnosticRow] = []
    for encoder_offset, encoder_key in enumerate(encoder_keys):
        model_id = FROZEN_ENCODERS[encoder_key]
        embeddings = encode_with_sentence_transformer(model_id, texts)
        for threshold_index, threshold in enumerate(_thresholds(thresholds)):
            for zoo_index in range(n_zoos):
                zoo_id = _selection_zoo_id(
                    encoder_key=encoder_key,
                    threshold=threshold,
                    threshold_index=threshold_index,
                    zoo_index=zoo_index,
                )
                seed = (
                    base_seed
                    + encoder_offset * 1_000_003
                    + threshold_index * 100_003
                    + zoo_index * 10_007
                )
                configs = sample_configs(
                    n_configs=configs_per_zoo,
                    base_seed=seed,
                    discovered_threshold=threshold,
                )
                for config in configs:
                    row = row_for_config(
                        encoder_key=encoder_key,
                        encoder_model=model_id,
                        items=items,
                        embeddings=embeddings,
                        config=config,
                    )
                    rows.append(
                        _with_selection_metadata(
                            row,
                            zoo_id=zoo_id,
                            threshold_index=threshold_index,
                            zoo_index=zoo_index,
                            configs_per_zoo=configs_per_zoo,
                        )
                    )
    return rows


def zoo_key(row: DiagnosticRow) -> str:
    value = row.metadata.get("selection_zoo")
    if value is None:
        raise ValueError(f"row {row.model_id} is missing selection_zoo metadata")
    return str(value)


def id_equivalent_candidates(
    rows: list[DiagnosticRow],
    *,
    train_floor: float = 0.95,
    id_band: float = 0.02,
    min_candidates: int = 3,
) -> list[DiagnosticRow]:
    train_ok = [row for row in rows if row.train_accuracy >= train_floor]
    if not train_ok:
        return []
    best_id = max(row.id_validation_accuracy for row in train_ok)
    candidates = [
        row
        for row in train_ok
        if row.id_validation_accuracy >= best_id - id_band
    ]
    if len(candidates) < min_candidates:
        return []
    return candidates


def _mean_metric(rows: list[DiagnosticRow], attr: str) -> float:
    return mean(float(getattr(row, attr)) for row in rows)


def _mean_discovered(rows: list[DiagnosticRow]) -> float:
    values = [row.compatibility_discovered or 0.0 for row in rows]
    return mean(values)


def _mean_wrong(rows: list[DiagnosticRow]) -> float:
    return mean(row.compatibility_wrong for row in rows)


def _selector_record(
    *,
    zoo_id: str,
    selector: str,
    encoder_key: str,
    discovered_threshold: float,
    candidates: list[DiagnosticRow],
    selected: list[DiagnosticRow],
    oracle_ood: float,
    random_mean_ood: float,
) -> SelectionRecord:
    selected_ood = _mean_metric(selected, "ood_accuracy")
    return SelectionRecord(
        zoo_id=zoo_id,
        selector=selector,
        encoder_key=encoder_key,
        discovered_threshold=discovered_threshold,
        n_candidates=len(candidates),
        tied_count=len(selected),
        selected_ood=selected_ood,
        selected_train=_mean_metric(selected, "train_accuracy"),
        selected_id=_mean_metric(selected, "id_validation_accuracy"),
        selected_discovered=_mean_discovered(selected),
        selected_wrong=_mean_wrong(selected),
        oracle_ood=oracle_ood,
        random_mean_ood=random_mean_ood,
        regret=oracle_ood - selected_ood,
        lift_vs_random=selected_ood - random_mean_ood,
    )


def _best_by_metric(
    candidates: list[DiagnosticRow],
    metric: str,
) -> list[DiagnosticRow]:
    if metric == "ood_accuracy":
        best = max(row.ood_accuracy for row in candidates)
        return [row for row in candidates if row.ood_accuracy == best]
    scored: list[tuple[float, DiagnosticRow]] = []
    for row in candidates:
        values = row_predictor_values(row)
        if metric not in values:
            continue
        value = values[metric]
        if math.isfinite(value):
            scored.append((value, row))
    if not scored:
        return []
    best = max(value for value, _row in scored)
    return [row for value, row in scored if value == best]


def selection_records(
    rows: list[DiagnosticRow],
    *,
    train_floor: float = 0.95,
    id_band: float = 0.02,
    min_candidates: int = 3,
) -> list[SelectionRecord]:
    by_zoo: dict[str, list[DiagnosticRow]] = {}
    for row in rows:
        if row.domain != "semantic_retrieval_frozen_encoder":
            continue
        by_zoo.setdefault(zoo_key(row), []).append(row)

    records: list[SelectionRecord] = []
    for zoo_id, zoo_rows in sorted(by_zoo.items()):
        candidates = id_equivalent_candidates(
            zoo_rows,
            train_floor=train_floor,
            id_band=id_band,
            min_candidates=min_candidates,
        )
        if not candidates:
            continue
        encoder_key = str(candidates[0].metadata.get("encoder_key", "unknown"))
        config = candidates[0].metadata.get("config")
        if isinstance(config, dict):
            threshold = float(config.get("discovered_threshold", 0.0))
        elif isinstance(config, SemanticModelConfig):
            threshold = config.discovered_threshold
        else:
            threshold = float(candidates[0].metadata.get("discovered_threshold", 0.0))
        random_mean_ood = mean(row.ood_accuracy for row in candidates)
        oracle_selected = _best_by_metric(candidates, "ood_accuracy")
        oracle_ood = _mean_metric(oracle_selected, "ood_accuracy")
        records.append(
            _selector_record(
                zoo_id=zoo_id,
                selector="random_candidate",
                encoder_key=encoder_key,
                discovered_threshold=threshold,
                candidates=candidates,
                selected=candidates,
                oracle_ood=oracle_ood,
                random_mean_ood=random_mean_ood,
            )
        )
        records.append(
            _selector_record(
                zoo_id=zoo_id,
                selector="ood_oracle",
                encoder_key=encoder_key,
                discovered_threshold=threshold,
                candidates=candidates,
                selected=oracle_selected,
                oracle_ood=oracle_ood,
                random_mean_ood=random_mean_ood,
            )
        )
        for predictor in SELECTION_PREDICTORS:
            selected = _best_by_metric(candidates, predictor)
            if not selected:
                continue
            records.append(
                _selector_record(
                    zoo_id=zoo_id,
                    selector=predictor,
                    encoder_key=encoder_key,
                    discovered_threshold=threshold,
                    candidates=candidates,
                    selected=selected,
                    oracle_ood=oracle_ood,
                    random_mean_ood=random_mean_ood,
                )
            )
    return records


def summarize_selection_records(records: list[SelectionRecord]) -> dict[str, Any]:
    grouped: dict[str, list[SelectionRecord]] = {}
    for record in records:
        grouped.setdefault(record.selector, []).append(record)

    by_selector = []
    for selector, group in sorted(grouped.items()):
        by_selector.append(
            {
                "selector": selector,
                "n_zoos": float(len(group)),
                "mean_candidates": mean(record.n_candidates for record in group),
                "mean_selected_ood": mean(record.selected_ood for record in group),
                "mean_selected_id": mean(record.selected_id for record in group),
                "mean_regret": mean(record.regret for record in group),
                "mean_lift_vs_random": mean(record.lift_vs_random for record in group),
                "mean_tied_count": mean(record.tied_count for record in group),
            }
        )

    by_encoder = []
    encoder_groups: dict[tuple[str, str], list[SelectionRecord]] = {}
    for record in records:
        encoder_groups.setdefault((record.encoder_key, record.selector), []).append(record)
    for (encoder, selector), group in sorted(encoder_groups.items()):
        by_encoder.append(
            {
                "encoder_key": encoder,
                "selector": selector,
                "n_zoos": float(len(group)),
                "mean_selected_ood": mean(record.selected_ood for record in group),
                "mean_lift_vs_random": mean(record.lift_vs_random for record in group),
            }
        )

    by_threshold = []
    threshold_groups: dict[tuple[float, str], list[SelectionRecord]] = {}
    for record in records:
        threshold_groups.setdefault(
            (record.discovered_threshold, record.selector),
            [],
        ).append(record)
    for (threshold, selector), group in sorted(threshold_groups.items()):
        by_threshold.append(
            {
                "threshold": threshold,
                "selector": selector,
                "n_zoos": float(len(group)),
                "mean_selected_ood": mean(record.selected_ood for record in group),
                "mean_lift_vs_random": mean(record.lift_vs_random for record in group),
            }
        )

    lookup = {row["selector"]: row for row in by_selector}
    discovered = lookup.get("compatibility_discovered")
    id_baseline = lookup.get("id_validation_accuracy")
    train_baseline = lookup.get("train_accuracy")
    wrong = lookup.get("compatibility_wrong")
    random_candidate = lookup.get("random_candidate")
    gates = {
        "min_zoo_count": bool(
            discovered is not None and float(discovered["n_zoos"]) >= 20.0
        ),
        "beats_id_validation": bool(
            discovered is not None
            and id_baseline is not None
            and float(discovered["mean_selected_ood"])
            > float(id_baseline["mean_selected_ood"]) + 0.05
        ),
        "beats_train_accuracy": bool(
            discovered is not None
            and train_baseline is not None
            and float(discovered["mean_selected_ood"])
            > float(train_baseline["mean_selected_ood"]) + 0.05
        ),
        "beats_random_candidate": bool(
            discovered is not None
            and random_candidate is not None
            and float(discovered["mean_selected_ood"])
            > float(random_candidate["mean_selected_ood"]) + 0.05
        ),
        "wrong_control_fails": bool(
            wrong is not None
            and random_candidate is not None
            and float(wrong["mean_selected_ood"])
            <= float(random_candidate["mean_selected_ood"]) + 0.02
        ),
    }
    gates["accepted"] = all(gates.values())
    return {
        "n_records": len(records),
        "selectors": SELECTION_PREDICTORS + BASELINE_SELECTORS,
        "by_selector": by_selector,
        "by_encoder": by_encoder,
        "by_threshold": by_threshold,
        "gates": gates,
    }


def semantic_selection_payload(
    *,
    rows: list[DiagnosticRow],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    records = selection_records(rows)
    return {
        "kind": "structure-compatible semantic selection control",
        "manifest": manifest,
        "summary": summarize_rows(rows),
        "selection_summary": summarize_selection_records(records),
        "selection_records": [record.to_record() for record in records],
        "rows": rows_to_records(rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--n-zoos", type=int, default=4)
    parser.add_argument("--configs-per-zoo", type=int, default=12)
    parser.add_argument("--thresholds", default="0.50,0.56,0.62,0.68,0.74")
    parser.add_argument("--base-seed", type=int, default=20260706)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    thresholds = tuple(float(part) for part in args.thresholds.split(",") if part)
    rows = (
        run_fixture_selection_control_sweep(
            thresholds=thresholds,
            n_zoos=args.n_zoos,
            configs_per_zoo=args.configs_per_zoo,
            base_seed=args.base_seed,
        )
        if args.fixture
        else run_encoder_selection_control_sweep(
            thresholds=thresholds,
            n_zoos=args.n_zoos,
            configs_per_zoo=args.configs_per_zoo,
            base_seed=args.base_seed,
        )
    )
    payload = semantic_selection_payload(
        rows=rows,
        manifest={
            "fixture": args.fixture,
            "n_zoos": args.n_zoos,
            "configs_per_zoo": args.configs_per_zoo,
            "thresholds": list(thresholds),
            "base_seed": args.base_seed,
        },
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["selection_summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
