"""Common analysis helpers for structure-compatible generalization.

The central object is a domain-agnostic diagnostic row. Each row describes one
trained model or exact candidate with train/ID metrics, an OOD metric, and
compatibility measurements under the true and wrong transformation families.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from statistics import mean
from typing import Any, Iterable


@dataclass(frozen=True)
class DiagnosticRow:
    domain: str
    model_id: str
    train_accuracy: float
    id_validation_accuracy: float
    ood_accuracy: float
    compatibility_true: float
    compatibility_wrong: float
    final_train_loss: float | None = None
    parameter_l2: float | None = None
    sharpness_proxy: float | None = None
    compatibility_inferred: float | None = None
    train_loss_score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "DiagnosticRow":
        return cls(
            domain=str(record["domain"]),
            model_id=str(record["model_id"]),
            train_accuracy=float(record["train_accuracy"]),
            id_validation_accuracy=float(record["id_validation_accuracy"]),
            ood_accuracy=float(record["ood_accuracy"]),
            compatibility_true=float(record["compatibility_true"]),
            compatibility_wrong=float(record["compatibility_wrong"]),
            final_train_loss=_optional_float(record.get("final_train_loss")),
            parameter_l2=_optional_float(record.get("parameter_l2")),
            sharpness_proxy=_optional_float(record.get("sharpness_proxy")),
            compatibility_inferred=_optional_float(record.get("compatibility_inferred")),
            train_loss_score=_optional_float(record.get("train_loss_score")),
            metadata=dict(record.get("metadata") or {}),
        )


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def pearson(xs: Iterable[float], ys: Iterable[float]) -> float:
    x = list(xs)
    y = list(ys)
    if len(x) != len(y):
        raise ValueError("pearson inputs must have the same length")
    if len(x) < 2:
        return 0.0
    mx = mean(x)
    my = mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den_x = sum((a - mx) ** 2 for a in x)
    den_y = sum((b - my) ** 2 for b in y)
    denom = math.sqrt(den_x * den_y)
    return 0.0 if denom == 0.0 else num / denom


def ranks(values: Iterable[float]) -> list[float]:
    vals = list(values)
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    out = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = rank
        i = j + 1
    return out


def spearman(xs: Iterable[float], ys: Iterable[float]) -> float:
    return pearson(ranks(xs), ranks(ys))


def row_predictor_values(row: DiagnosticRow) -> dict[str, float]:
    """Return predictor scores where larger is intended to be better.

    Loss-like fields are negated so selection and ranking can use one
    consistent direction.
    """
    out: dict[str, float] = {
        "compatibility_true": row.compatibility_true,
        "compatibility_wrong": row.compatibility_wrong,
        "train_accuracy": row.train_accuracy,
        "id_validation_accuracy": row.id_validation_accuracy,
    }
    if row.compatibility_inferred is not None:
        out["compatibility_inferred"] = row.compatibility_inferred
    if row.final_train_loss is not None:
        out["negative_train_loss"] = -row.final_train_loss
    if row.train_loss_score is not None:
        out["train_loss_score"] = row.train_loss_score
    if row.parameter_l2 is not None:
        out["negative_parameter_l2"] = -row.parameter_l2
    if row.sharpness_proxy is not None:
        out["negative_abs_sharpness"] = -abs(row.sharpness_proxy)
    return out


def _finite_pairs(rows: list[DiagnosticRow], predictor: str) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for row in rows:
        values = row_predictor_values(row)
        if predictor not in values:
            continue
        value = values[predictor]
        if math.isfinite(value) and math.isfinite(row.ood_accuracy):
            xs.append(value)
            ys.append(row.ood_accuracy)
    return xs, ys


def available_predictors(rows: Iterable[DiagnosticRow]) -> list[str]:
    names: set[str] = set()
    for row in rows:
        names.update(row_predictor_values(row))
    return sorted(names)


def predictor_correlations(rows: Iterable[DiagnosticRow]) -> dict[str, dict[str, float]]:
    materialized = list(rows)
    out: dict[str, dict[str, float]] = {}
    for predictor in available_predictors(materialized):
        xs, ys = _finite_pairs(materialized, predictor)
        out[predictor] = {
            "n": float(len(xs)),
            "pearson": pearson(xs, ys),
            "spearman": spearman(xs, ys),
        }
    return out


def id_equivalent_rows(
    rows: Iterable[DiagnosticRow],
    *,
    train_floor: float = 0.95,
    id_band: float = 0.02,
) -> list[DiagnosticRow]:
    materialized = [row for row in rows if row.train_accuracy >= train_floor]
    if not materialized:
        return []
    best_id = max(row.id_validation_accuracy for row in materialized)
    return [
        row
        for row in materialized
        if row.id_validation_accuracy >= best_id - id_band
    ]


def selection_analysis(
    rows: Iterable[DiagnosticRow],
    *,
    train_floor: float = 0.95,
    id_band: float = 0.02,
) -> dict[str, Any]:
    """Select one ID-equivalent row per domain by each predictor.

    OOD labels are used only after selection to evaluate the selector.
    """
    by_domain: dict[str, list[DiagnosticRow]] = {}
    for row in rows:
        if row.domain.endswith("_exact"):
            continue
        by_domain.setdefault(row.domain, []).append(row)

    selections: dict[str, dict[str, dict[str, Any]]] = {}
    for domain, domain_rows in sorted(by_domain.items()):
        eligible = id_equivalent_rows(
            domain_rows, train_floor=train_floor, id_band=id_band
        )
        domain_out: dict[str, dict[str, Any]] = {}
        for predictor in available_predictors(eligible):
            scored = [
                (row_predictor_values(row)[predictor], row)
                for row in eligible
                if predictor in row_predictor_values(row)
            ]
            if not scored:
                continue
            _score, selected = max(scored, key=lambda item: (item[0], item[1].model_id))
            domain_out[predictor] = {
                "model_id": selected.model_id,
                "ood_accuracy": selected.ood_accuracy,
                "train_accuracy": selected.train_accuracy,
                "id_validation_accuracy": selected.id_validation_accuracy,
                "eligible_count": len(eligible),
            }
        selections[domain] = domain_out

    aggregate: dict[str, dict[str, float]] = {}
    all_predictors = sorted({p for domain in selections.values() for p in domain})
    for predictor in all_predictors:
        oods = [
            domain[predictor]["ood_accuracy"]
            for domain in selections.values()
            if predictor in domain
        ]
        if oods:
            aggregate[predictor] = {
                "domains": float(len(oods)),
                "mean_selected_ood": mean(oods),
            }
    return {
        "train_floor": train_floor,
        "id_band": id_band,
        "by_domain": selections,
        "aggregate": aggregate,
    }


def summarize_rows(rows: Iterable[DiagnosticRow]) -> dict[str, Any]:
    materialized = list(rows)
    by_domain: dict[str, list[DiagnosticRow]] = {}
    for row in materialized:
        by_domain.setdefault(row.domain, []).append(row)

    domain_summaries: dict[str, Any] = {}
    for domain, domain_rows in sorted(by_domain.items()):
        correlations = predictor_correlations(domain_rows)
        ranking = sorted(
            correlations.items(),
            key=lambda item: (item[1]["pearson"], item[1]["spearman"]),
            reverse=True,
        )
        domain_summaries[domain] = {
            "n_rows": len(domain_rows),
            "mean_ood_accuracy": mean(row.ood_accuracy for row in domain_rows),
            "mean_train_accuracy": mean(row.train_accuracy for row in domain_rows),
            "mean_id_validation_accuracy": mean(
                row.id_validation_accuracy for row in domain_rows
            ),
            "correlations": correlations,
            "predictor_ranking": [
                {
                    "predictor": predictor,
                    "pearson": stats["pearson"],
                    "spearman": stats["spearman"],
                    "n": int(stats["n"]),
                }
                for predictor, stats in ranking
            ],
        }

    pooled = predictor_correlations(materialized)
    pooled_ranking = sorted(
        pooled.items(),
        key=lambda item: (item[1]["pearson"], item[1]["spearman"]),
        reverse=True,
    )
    return {
        "n_rows": len(materialized),
        "domains": sorted(by_domain),
        "by_domain": domain_summaries,
        "pooled_correlations": pooled,
        "pooled_predictor_ranking": [
            {
                "predictor": predictor,
                "pearson": stats["pearson"],
                "spearman": stats["spearman"],
                "n": int(stats["n"]),
            }
            for predictor, stats in pooled_ranking
        ],
        "selection": selection_analysis(materialized),
    }


def rows_to_records(rows: Iterable[DiagnosticRow]) -> list[dict[str, Any]]:
    return [row.to_record() for row in rows]


def rows_from_records(records: Iterable[dict[str, Any]]) -> list[DiagnosticRow]:
    return [DiagnosticRow.from_record(record) for record in records]
