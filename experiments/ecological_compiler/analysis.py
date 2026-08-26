"""Preregistered D-PLACE analysis for Ecological Compiler Study I.

Raw third-party data stay in ``artifacts/ecological_compiler``. The module
emits only reduced summaries and a coefficient figure into the tracked result
directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from scipy.optimize import OptimizeResult, minimize
from scipy.special import expit, logit


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "ecological_compiler"
EA_ROOT = ARTIFACT_ROOT / "dplace-dataset-ea"
DPLACE_ROOT = ARTIFACT_ROOT / "dplace-data"
RESULTS_ROOT = ROOT / "experiments" / "ecological_compiler" / "results"

EA_COMMIT = "5aa46eea62815daa283ac67cc757065a1b3be16e"
DPLACE_COMMIT = "9bfed2c8c206be00f55f71516f262bbca2234e5a"
SEED = 20260826
MIN_CUTPOINT_GAP = 1e-4

EXPECTED_INPUT_SHA256 = {
    "artifacts/ecological_compiler/dplace-data/csv/glottolog.csv": (
        "49f164b5e729399586fe1fa15db1d7528cbdabd2a01d7cbcae47fe5821d4950e"
    ),
    "artifacts/ecological_compiler/dplace-data/datasets/GSHHS/data.csv": (
        "aa80ed44b4c271de2568f557b9f706465578f548b2fe439e08a2d7732023d7c2"
    ),
    "artifacts/ecological_compiler/dplace-data/datasets/MODIS/data.csv": (
        "f9bed7627da01d6df7d135a47ed8d30d01bccdbbddfda08c4cec2f314cc8e13b"
    ),
    "artifacts/ecological_compiler/dplace-data/datasets/ecoClimate/data.csv": (
        "faa1321d932e084a0781bcbfc2ed971fa58558a4062d22ac1736c3df5456e125"
    ),
    "artifacts/ecological_compiler/dplace-dataset-ea/cldf/codes.csv": (
        "a57cfd1a1ec35a5b7872700a10693a13e73b7d50fac40d5ce3976e5724c9c9e5"
    ),
    "artifacts/ecological_compiler/dplace-dataset-ea/cldf/data.csv": (
        "69c3ce90ae8a11ac9da8e773c09d2038537d100555e89b60bebba8f6db317990"
    ),
    "artifacts/ecological_compiler/dplace-dataset-ea/cldf/societies.csv": (
        "0c665e055fa1fa7358594c60e1fd5efd6c9da1fc5a222305e1c9d46a14716d2c"
    ),
}

GATE_IDS = (
    "EC_G0_PROVENANCE",
    "EC_G1_DATA_INTEGRITY",
    "EC_G2_ADJUSTED_ASSOCIATION",
    "EC_G3_COASTAL_SEPARATION",
    "EC_G4_SUBSISTENCE_SPECIFICITY",
    "EC_G5_COMPILER_PATTERN",
    "EC_G6_TRANSPORT",
    "EC_G7_ORDINAL_STABILITY",
)

EA_VARIABLES = {
    "EA001": "gathering",
    "EA002": "hunting",
    "EA003": "fishing",
    "EA004": "husbandry",
    "EA005": "agriculture",
    "EA030": "settlement",
    "EA031": "community_size",
    "EA033": "political_complexity",
    "EA202": "population",
}

CLIMATE_VARIABLES = {
    "AnnualMeanTemperature": "annual_temperature",
    "AnnualTemperatureVariance": "temperature_variance",
    "PrecipitationPredictability": "precipitation_predictability",
}
NPP_VARIABLE = "MonthlyMeanNetPrimaryProduction"
COAST_VARIABLE = "DistToCoast_km"


@dataclass(frozen=True)
class OrderedFit:
    success: bool
    coefficients: np.ndarray
    cutpoints: np.ndarray
    standard_errors: np.ndarray
    parameters: np.ndarray
    nll: float
    aic: float
    n_iter: int
    message: str


@dataclass(frozen=True)
class BinaryFit:
    success: bool
    coefficients: np.ndarray
    standard_errors: np.ndarray
    nll: float
    message: str


@dataclass(frozen=True)
class ModelData:
    x: np.ndarray
    y: np.ndarray
    society_ids: tuple[str, ...]
    feature_names: tuple[str, ...]
    family_clusters: tuple[str, ...]
    spatial_clusters: tuple[str, ...]
    macroregions: tuple[str, ...]
    exposure_sd: float


def _softplus(value: np.ndarray) -> np.ndarray:
    return np.logaddexp(0.0, value)


def _probabilities_from_cumulative(cumulative: np.ndarray) -> np.ndarray:
    first = cumulative[:, :1]
    middle = np.diff(cumulative, axis=1)
    last = 1.0 - cumulative[:, -1:]
    return np.clip(np.concatenate((first, middle, last), axis=1), 1e-12, 1.0)


def strictly_increasing_cutpoints(raw: np.ndarray) -> np.ndarray:
    """Convert an unconstrained vector into strictly increasing cutpoints."""

    values = np.asarray(raw, dtype=float)
    if values.ndim != 1 or len(values) < 2:
        raise ValueError("cutpoint parameter vector must be one-dimensional")
    increments = _softplus(values[1:]) + MIN_CUTPOINT_GAP
    return np.concatenate(([values[0]], values[0] + np.cumsum(increments)))


def _inverse_cutpoint_parameters(cutpoints: np.ndarray) -> np.ndarray:
    differences = np.maximum(np.diff(cutpoints) - MIN_CUTPOINT_GAP, 1e-8)
    raw_increments = np.log(np.expm1(differences))
    return np.concatenate(([cutpoints[0]], raw_increments))


def ordered_probabilities(eta: np.ndarray, cutpoints: np.ndarray) -> np.ndarray:
    """Return category probabilities for a proportional-odds logit."""

    linear = np.asarray(eta, dtype=float)
    cuts = np.asarray(cutpoints, dtype=float)
    cumulative = expit(cuts[:, None] - linear[None, :]).T
    return _probabilities_from_cumulative(cumulative)


def _initial_ordered_parameters(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    n_levels = int(y.max()) + 1
    proportions = np.array([(y <= level).mean() for level in range(n_levels - 1)])
    cutpoints = logit(np.clip(proportions, 0.02, 0.98))
    for index in range(1, len(cutpoints)):
        cutpoints[index] = max(cutpoints[index], cutpoints[index - 1] + 0.2)
    return np.concatenate(
        (np.zeros(x.shape[1]), _inverse_cutpoint_parameters(cutpoints))
    )


def _ordered_nll(parameters: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
    n_features = x.shape[1]
    coefficients = parameters[:n_features]
    cutpoints = strictly_increasing_cutpoints(parameters[n_features:])
    probabilities = ordered_probabilities(x @ coefficients, cutpoints)
    selected = probabilities[np.arange(len(y)), y]
    value = -float(np.log(selected).sum())
    return value if math.isfinite(value) else 1e100


def _ordered_nll_and_gradient(
    parameters: np.ndarray, x: np.ndarray, y: np.ndarray
) -> tuple[float, np.ndarray]:
    """Return ordered-logit NLL and its analytic parameter gradient."""

    n_features = x.shape[1]
    coefficients = parameters[:n_features]
    raw_cutpoints = parameters[n_features:]
    cutpoints = strictly_increasing_cutpoints(raw_cutpoints)
    cumulative = expit(cutpoints[:, None] - (x @ coefficients)[None, :]).T
    densities = cumulative * (1.0 - cumulative)
    probabilities = _probabilities_from_cumulative(cumulative)
    selected = probabilities[np.arange(len(y)), y]
    nll = -float(np.log(selected).sum())

    eta_gradient = np.empty(len(y), dtype=float)
    first = y == 0
    last = y == len(cutpoints)
    middle = ~(first | last)
    eta_gradient[first] = densities[first, 0] / selected[first]
    eta_gradient[last] = -densities[last, -1] / selected[last]
    middle_rows = np.flatnonzero(middle)
    middle_levels = y[middle]
    eta_gradient[middle] = (
        densities[middle_rows, middle_levels]
        - densities[middle_rows, middle_levels - 1]
    ) / selected[middle]

    cutpoint_gradient = np.zeros(len(cutpoints), dtype=float)
    for index in range(len(cutpoints)):
        upper_rows = y == index
        lower_rows = y == index + 1
        cutpoint_gradient[index] -= np.sum(
            densities[upper_rows, index] / selected[upper_rows]
        )
        cutpoint_gradient[index] += np.sum(
            densities[lower_rows, index] / selected[lower_rows]
        )

    raw_gradient = np.empty_like(raw_cutpoints)
    raw_gradient[0] = sum(float(value) for value in cutpoint_gradient)
    raw_gradient[1:] = (
        expit(raw_cutpoints[1:]) * np.cumsum(cutpoint_gradient[:0:-1])[::-1]
    )
    gradient = np.concatenate((x.T @ eta_gradient, raw_gradient))
    if not math.isfinite(nll) or not np.all(np.isfinite(gradient)):
        return 1e100, np.zeros_like(parameters)
    return nll, gradient


def _optimizer_standard_errors(result: OptimizeResult, n_parameters: int) -> np.ndarray:
    try:
        inverse_hessian = result.hess_inv.todense()
    except AttributeError:
        inverse_hessian = np.asarray(result.hess_inv)
    matrix = np.asarray(inverse_hessian, dtype=float)
    if matrix.shape != (n_parameters, n_parameters):
        return np.full(n_parameters, np.nan)
    diagonal = np.diag(matrix)
    return np.sqrt(np.where(diagonal >= 0, diagonal, np.nan))


def fit_ordered_logit(
    x: np.ndarray,
    y: np.ndarray,
    *,
    start: np.ndarray | None = None,
    maxiter: int = 1_000,
) -> OrderedFit:
    """Fit a proportional-odds ordered logit with five or more observations."""

    design = np.asarray(x, dtype=float)
    outcome = np.asarray(y, dtype=int)
    if design.ndim != 2 or outcome.ndim != 1 or len(design) != len(outcome):
        raise ValueError("ordered-logit inputs have incompatible shapes")
    if len(outcome) < 5 or not np.all(np.isfinite(design)):
        raise ValueError("ordered-logit inputs must be finite with at least five rows")
    levels = np.unique(outcome)
    if not np.array_equal(levels, np.arange(levels[-1] + 1)):
        raise ValueError("ordered outcome levels must be consecutive and start at zero")
    initial = _initial_ordered_parameters(design, outcome) if start is None else start
    n_cutpoints = len(levels) - 1
    expected = design.shape[1] + n_cutpoints
    if len(initial) != expected:
        initial = _initial_ordered_parameters(design, outcome)
    bounds = [(-12.0, 12.0)] * design.shape[1]
    bounds += [(-12.0, 12.0)] + [(-8.0, 8.0)] * (n_cutpoints - 1)
    result = minimize(
        _ordered_nll_and_gradient,
        initial,
        args=(design, outcome),
        method="L-BFGS-B",
        jac=True,
        bounds=bounds,
        options={
            "maxiter": maxiter,
            "maxfun": max(50_000, maxiter * (len(initial) + 1) * 4),
            "ftol": 1e-10,
            "gtol": 1e-6,
        },
    )
    parameters = np.asarray(result.x, dtype=float)
    coefficients = parameters[: design.shape[1]]
    cutpoints = strictly_increasing_cutpoints(parameters[design.shape[1] :])
    standard_errors = _optimizer_standard_errors(result, len(parameters))[
        : design.shape[1]
    ]
    success = bool(
        result.success
        and np.all(np.isfinite(parameters))
        and np.all(np.diff(cutpoints) > 0)
        and math.isfinite(float(result.fun))
    )
    return OrderedFit(
        success=success,
        coefficients=coefficients,
        cutpoints=cutpoints,
        standard_errors=standard_errors,
        parameters=parameters,
        nll=float(result.fun),
        aic=float(2 * len(parameters) + 2 * result.fun),
        n_iter=int(getattr(result, "nit", 0)),
        message=str(result.message),
    )


def _binary_nll(parameters: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
    intercept = parameters[0]
    coefficients = parameters[1:]
    eta = intercept + x @ coefficients
    probabilities = np.clip(expit(eta), 1e-12, 1.0 - 1e-12)
    return -float(
        (y * np.log(probabilities) + (1 - y) * np.log1p(-probabilities)).sum()
    )


def _binary_nll_and_gradient(
    parameters: np.ndarray, x: np.ndarray, y: np.ndarray
) -> tuple[float, np.ndarray]:
    """Return binary-logit NLL and its analytic parameter gradient."""

    intercept = parameters[0]
    coefficients = parameters[1:]
    probabilities = expit(intercept + x @ coefficients)
    clipped = np.clip(probabilities, 1e-12, 1.0 - 1e-12)
    nll = -float((y * np.log(clipped) + (1 - y) * np.log1p(-clipped)).sum())
    residual = probabilities - y
    gradient = np.concatenate(([residual.sum()], x.T @ residual))
    return nll, gradient


def fit_binary_logit(x: np.ndarray, y: np.ndarray) -> BinaryFit:
    design = np.asarray(x, dtype=float)
    outcome = np.asarray(y, dtype=int)
    result = minimize(
        _binary_nll_and_gradient,
        np.zeros(design.shape[1] + 1),
        args=(design, outcome),
        method="L-BFGS-B",
        jac=True,
        bounds=[(-12.0, 12.0)] * (design.shape[1] + 1),
        options={"maxiter": 3_000, "maxfun": 50_000, "ftol": 1e-10, "gtol": 1e-6},
    )
    standard_errors = _optimizer_standard_errors(result, len(result.x))[1:]
    return BinaryFit(
        success=bool(result.success and np.all(np.isfinite(result.x))),
        coefficients=np.asarray(result.x[1:], dtype=float),
        standard_errors=standard_errors,
        nll=float(result.fun),
        message=str(result.message),
    )


def read_cldf_values(
    data_path: Path,
    codes_path: Path,
    variable_ids: set[str],
) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
    """Read selected CLDF variables and reject conflicting society duplicates."""

    code_orders: dict[str, float] = {}
    with codes_path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            raw_order = (row.get("ord") or "").strip()
            code_id = row.get("ID", "")
            if (
                row.get("Var_ID") in variable_ids
                and raw_order
                and not code_id.endswith("-NA")
            ):
                code_orders[row["ID"]] = float(raw_order)

    values: dict[str, dict[str, float]] = {variable: {} for variable in variable_ids}
    duplicate_counts: Counter[str] = Counter()
    with data_path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            variable = row.get("Var_ID", "")
            if variable not in variable_ids:
                continue
            society = row.get("Soc_ID", "")
            code_id = (row.get("Code_ID") or "").strip()
            raw_value = (row.get("Value") or "").strip()
            if code_id in code_orders:
                value = code_orders[code_id]
            else:
                try:
                    value = float(raw_value)
                except ValueError:
                    continue
            existing = values[variable].get(society)
            if existing is not None:
                duplicate_counts[variable] += 1
                if not math.isclose(existing, value, rel_tol=0.0, abs_tol=1e-12):
                    raise ValueError(
                        f"conflicting duplicate for society={society} variable={variable}"
                    )
            values[variable][society] = value
    return values, dict(duplicate_counts)


def _read_long_numeric(
    path: Path, variable_ids: set[str]
) -> dict[str, dict[str, float]]:
    values: dict[str, dict[str, float]] = {variable: {} for variable in variable_ids}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            variable = row.get("var_id", "")
            if variable not in variable_ids:
                continue
            try:
                value = float(row.get("code", ""))
            except ValueError:
                continue
            society = row.get("soc_id", "")
            existing = values[variable].get(society)
            if existing is not None and not math.isclose(
                existing, value, abs_tol=1e-12
            ):
                raise ValueError(
                    f"conflicting environmental duplicate for {society} {variable}"
                )
            values[variable][society] = value
    return values


def _float_or_none(value: str | None) -> float | None:
    try:
        parsed = float(value or "")
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _is_europe_region(region: str) -> bool:
    """Identify D-PLACE regional labels assigned to Europe."""

    return region.endswith("Europe")


def _git_commit(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _git_worktree_clean(path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(path), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    return not result.stdout.strip()


def _glottolog_labels(
    society_id: str,
    glottocode: str,
    glottolog: Mapping[str, tuple[str | None, str | None]],
) -> tuple[str, str]:
    family, macroregion = glottolog.get(glottocode, (None, None))
    return family or f"Unknown:{society_id}", macroregion or "Unknown"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_society_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Join current EA cultural values to pinned D-PLACE support datasets."""

    ea_data = EA_ROOT / "cldf" / "data.csv"
    ea_codes = EA_ROOT / "cldf" / "codes.csv"
    ea_societies = EA_ROOT / "cldf" / "societies.csv"
    glottolog_path = DPLACE_ROOT / "csv" / "glottolog.csv"
    climate_path = DPLACE_ROOT / "datasets" / "ecoClimate" / "data.csv"
    npp_path = DPLACE_ROOT / "datasets" / "MODIS" / "data.csv"
    coast_path = DPLACE_ROOT / "datasets" / "GSHHS" / "data.csv"
    inputs = [
        ea_data,
        ea_codes,
        ea_societies,
        glottolog_path,
        climate_path,
        npp_path,
        coast_path,
    ]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing registered inputs: " + ", ".join(missing))

    ea_values, duplicate_counts = read_cldf_values(ea_data, ea_codes, set(EA_VARIABLES))
    climate = _read_long_numeric(climate_path, set(CLIMATE_VARIABLES))
    npp = _read_long_numeric(npp_path, {NPP_VARIABLE})
    coast = _read_long_numeric(coast_path, {COAST_VARIABLE})

    glottolog: dict[str, tuple[str | None, str | None]] = {}
    with glottolog_path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            glottolog[row["id"]] = (row.get("family_name"), row.get("macroarea"))

    rows: list[dict[str, Any]] = []
    with ea_societies.open(newline="") as stream:
        for society in csv.DictReader(stream):
            society_id = society["ID"]
            latitude = _float_or_none(society.get("Latitude"))
            longitude = _float_or_none(society.get("Longitude"))
            focal_year = _float_or_none(society.get("main_focal_year"))
            glottocode = society.get("Glottocode", "")
            family, macroregion = _glottolog_labels(society_id, glottocode, glottolog)
            row: dict[str, Any] = {
                "society_id": society_id,
                "name": society.get("Name", society_id),
                "latitude": latitude,
                "longitude": longitude,
                "abs_latitude": abs(latitude) if latitude is not None else None,
                "focal_year": focal_year,
                "region": society.get("region") or "Unknown",
                "macroregion": macroregion or "Unknown",
                "family": family or f"Unknown:{society_id}",
            }
            if latitude is None or longitude is None:
                row["spatial_block"] = "Unknown"
            else:
                lat_bin = math.floor((latitude + 90.0) / 20.0)
                lon_bin = math.floor((longitude + 180.0) / 20.0)
                row["spatial_block"] = f"{lat_bin}:{lon_bin}"
            for variable, name in EA_VARIABLES.items():
                row[name] = ea_values[variable].get(society_id)
            for variable, name in CLIMATE_VARIABLES.items():
                row[name] = climate[variable].get(society_id)
            row["net_primary_production"] = npp[NPP_VARIABLE].get(society_id)
            row["distance_to_coast"] = coast[COAST_VARIABLE].get(society_id)
            rows.append(row)

    provenance = {
        "ea_commit": _git_commit(EA_ROOT),
        "dplace_support_commit": _git_commit(DPLACE_ROOT),
        "ea_worktree_clean": _git_worktree_clean(EA_ROOT),
        "dplace_support_worktree_clean": _git_worktree_clean(DPLACE_ROOT),
        "input_sha256": {str(path.relative_to(ROOT)): _sha256(path) for path in inputs},
        "duplicate_counts": duplicate_counts,
        "societies_loaded": len(rows),
    }
    return rows, provenance


def _required_numeric_fields(model: str, exposure: str) -> list[str]:
    if exposure == "fishing":
        subsistence = ["fishing", "hunting", "husbandry", "agriculture"]
    elif exposure == "hunting":
        subsistence = ["hunting", "fishing", "husbandry", "agriculture"]
    elif exposure == "gathering":
        subsistence = ["gathering", "hunting", "husbandry", "agriculture"]
    else:
        raise ValueError(f"unsupported exposure: {exposure}")
    if model == "m0":
        return [exposure]
    common = subsistence + [
        "abs_latitude",
        "distance_to_coast",
        "annual_temperature",
        "temperature_variance",
        "precipitation_predictability",
        "net_primary_production",
        "focal_year",
    ]
    if model == "m1":
        return common
    if model == "m2":
        return common + ["community_size", "population"]
    raise ValueError(f"unsupported model: {model}")


def _standardize(column: np.ndarray) -> np.ndarray:
    deviation = float(column.std(ddof=0))
    if not math.isfinite(deviation) or deviation <= 0:
        return np.zeros_like(column)
    return (column - float(column.mean())) / deviation


def prepare_model_data(
    rows: Sequence[dict[str, Any]],
    model: str,
    *,
    exposure: str = "fishing",
    society_ids: set[str] | None = None,
    macroregion_levels: Sequence[str] | None = None,
    settlement_levels: Sequence[int] = tuple(range(1, 9)),
) -> ModelData:
    required = _required_numeric_fields(model, exposure)
    selected: list[dict[str, Any]] = []
    for row in rows:
        if society_ids is not None and row["society_id"] not in society_ids:
            continue
        if row.get("political_complexity") is None:
            continue
        if any(row.get(field) is None for field in required):
            continue
        if model == "m2" and row.get("settlement") is None:
            continue
        selected.append(row)
    if not selected:
        raise ValueError(f"no complete rows for {model}/{exposure}")

    columns: list[np.ndarray] = []
    feature_names: list[str] = []
    exposure_values = np.array([float(row[exposure]) for row in selected])
    columns.append(exposure_values)
    feature_names.append(exposure)

    for field in required[1:]:
        raw = np.array([float(row[field]) for row in selected])
        if field in {"distance_to_coast", "population"}:
            raw = np.log1p(np.maximum(raw, 0.0))
            name = f"log1p_{field}"
        else:
            name = field
        columns.append(_standardize(raw))
        feature_names.append(name)

    if model in {"m1", "m2"}:
        levels = (
            sorted({str(row["macroregion"]) for row in rows})
            if macroregion_levels is None
            else list(macroregion_levels)
        )
        for level in levels[1:]:
            columns.append(
                np.array([float(str(row["macroregion"]) == level) for row in selected])
            )
            feature_names.append(f"macroregion={level}")

    if model == "m2":
        for level in settlement_levels[1:]:
            columns.append(
                np.array(
                    [float(int(float(row["settlement"])) == level) for row in selected]
                )
            )
            feature_names.append(f"settlement={level}")

    x = np.column_stack(columns)
    y = np.array([int(float(row["political_complexity"])) - 1 for row in selected])
    return ModelData(
        x=x,
        y=y,
        society_ids=tuple(str(row["society_id"]) for row in selected),
        feature_names=tuple(feature_names),
        family_clusters=tuple(str(row["family"]) for row in selected),
        spatial_clusters=tuple(str(row["spatial_block"]) for row in selected),
        macroregions=tuple(str(row["macroregion"]) for row in selected),
        exposure_sd=float(exposure_values.std(ddof=0)),
    )


def _cluster_members(clusters: Sequence[str]) -> dict[str, np.ndarray]:
    members: dict[str, list[int]] = defaultdict(list)
    for index, cluster in enumerate(clusters):
        members[cluster].append(index)
    return {label: np.asarray(indices, dtype=int) for label, indices in members.items()}


def block_bootstrap(
    data: ModelData,
    fit: OrderedFit,
    clusters: Sequence[str],
    *,
    draws: int,
    seed: int,
) -> tuple[list[float], int, int, int]:
    rng = np.random.default_rng(seed)
    members = _cluster_members(clusters)
    labels = sorted(members)
    outcome_support = np.unique(data.y)
    coefficients: list[float] = []
    optimizer_failures = 0
    level_dropout_failures = 0
    attempts = 0
    max_attempts = max(draws * 10, draws + 10)
    while len(coefficients) < draws and attempts < max_attempts:
        attempts += 1
        sampled = rng.integers(0, len(labels), size=len(labels))
        indices = np.concatenate([members[labels[int(index)]] for index in sampled])
        if not np.array_equal(np.unique(data.y[indices]), outcome_support):
            level_dropout_failures += 1
            continue
        try:
            estimate = fit_ordered_logit(
                data.x[indices], data.y[indices], start=fit.parameters, maxiter=4_000
            )
        except ValueError:
            optimizer_failures += 1
            continue
        if estimate.success:
            coefficients.append(float(estimate.coefficients[0]))
        else:
            optimizer_failures += 1
    return coefficients, optimizer_failures, level_dropout_failures, attempts


def within_macroregion_permutation(
    data: ModelData,
    fit: OrderedFit,
    *,
    draws: int,
    seed: int,
) -> tuple[list[float], int, int]:
    rng = np.random.default_rng(seed)
    groups: dict[str, np.ndarray] = {}
    macroregion_array = np.asarray(data.macroregions)
    for macroregion in sorted(set(data.macroregions)):
        groups[macroregion] = np.flatnonzero(macroregion_array == macroregion)
    coefficients: list[float] = []
    failures = 0
    attempts = 0
    max_attempts = max(draws * 10, draws + 10)
    while len(coefficients) < draws and attempts < max_attempts:
        attempts += 1
        x = data.x.copy()
        for indices in groups.values():
            x[indices, 0] = rng.permutation(x[indices, 0])
        estimate = fit_ordered_logit(x, data.y, start=fit.parameters, maxiter=4_000)
        if estimate.success:
            coefficients.append(float(estimate.coefficients[0]))
        else:
            failures += 1
    return coefficients, failures, attempts


def _percentile_interval(values: Sequence[float]) -> list[float | None]:
    if not values:
        return [None, None]
    return [float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))]


def _fit_summary(fit: OrderedFit, data: ModelData) -> dict[str, Any]:
    coefficient = float(fit.coefficients[0])
    standard_error = float(fit.standard_errors[0])
    return {
        "n": len(data.y),
        "features": list(data.feature_names),
        "success": fit.success,
        "coefficient_per_category": coefficient,
        "standardized_coefficient": coefficient * data.exposure_sd,
        "approximate_standard_error": standard_error,
        "approximate_wald_95": [
            coefficient - 1.96 * standard_error,
            coefficient + 1.96 * standard_error,
        ],
        "aic": fit.aic,
        "nll": fit.nll,
        "cutpoints": fit.cutpoints.tolist(),
        "iterations": fit.n_iter,
        "message": fit.message,
    }


def _safe_point_fit(data: ModelData, *, start: np.ndarray | None = None) -> OrderedFit:
    fit = fit_ordered_logit(data.x, data.y, start=start)
    if not fit.success:
        raise RuntimeError(f"ordered-logit point fit failed: {fit.message}")
    return fit


def _status(pass_value: bool) -> str:
    return "PASS" if pass_value else "FAIL"


def registered_verdict(gates: dict[str, str]) -> str:
    """Apply the eight registered fatal gates noncompensatorily."""

    if set(gates) != set(GATE_IDS):
        raise ValueError("gate ledger must contain every registered gate exactly once")
    return "accepted" if all(gates[gate] == "PASS" for gate in GATE_IDS) else "rejected"


def provenance_gate_passes(provenance: dict[str, Any]) -> bool:
    """Check exact registered revisions, bytes, and source-tree cleanliness."""

    return bool(
        provenance["ea_commit"] == EA_COMMIT
        and provenance["dplace_support_commit"] == DPLACE_COMMIT
        and bool(provenance["ea_worktree_clean"])
        and bool(provenance["dplace_support_worktree_clean"])
        and provenance["input_sha256"] == EXPECTED_INPUT_SHA256
    )


def _serializable_fit(fit: OrderedFit) -> dict[str, Any]:
    payload = asdict(fit)
    for key in ("coefficients", "cutpoints", "standard_errors", "parameters"):
        payload[key] = payload[key].tolist()
    return payload


def run_analysis(
    *,
    family_draws: int = 300,
    spatial_draws: int = 300,
    permutation_draws: int = 500,
) -> dict[str, Any]:
    rows, provenance = load_society_rows()
    macroregions = sorted({str(row["macroregion"]) for row in rows})

    m0_data = prepare_model_data(rows, "m0", macroregion_levels=macroregions)
    m1_data = prepare_model_data(rows, "m1", macroregion_levels=macroregions)
    m2_data = prepare_model_data(rows, "m2", macroregion_levels=macroregions)
    common_ids = set(m2_data.society_ids)
    m1_common_data = prepare_model_data(
        rows, "m1", society_ids=common_ids, macroregion_levels=macroregions
    )

    m0_fit = _safe_point_fit(m0_data)
    m1_fit = _safe_point_fit(m1_data)
    m1_common_fit = _safe_point_fit(m1_common_data)
    m2_fit = _safe_point_fit(m2_data)

    family_values, family_failures, family_level_dropouts, family_attempts = (
        block_bootstrap(
            m1_data,
            m1_fit,
            m1_data.family_clusters,
            draws=family_draws,
            seed=SEED + 1,
        )
    )
    spatial_values, spatial_failures, spatial_level_dropouts, spatial_attempts = (
        block_bootstrap(
            m1_data,
            m1_fit,
            m1_data.spatial_clusters,
            draws=spatial_draws,
            seed=SEED + 2,
        )
    )
    permutation_values, permutation_failures, permutation_attempts = (
        within_macroregion_permutation(
            m1_data,
            m1_fit,
            draws=permutation_draws,
            seed=SEED + 3,
        )
    )
    observed = float(m1_fit.coefficients[0])
    permutation_p = (
        (1 + sum(value >= observed for value in permutation_values))
        / (1 + len(permutation_values))
        if permutation_values
        else None
    )

    substitute_results: dict[str, dict[str, Any]] = {}
    for exposure in ("hunting", "gathering"):
        substitute_data = prepare_model_data(
            rows,
            "m1",
            exposure=exposure,
            society_ids=set(m1_data.society_ids),
            macroregion_levels=macroregions,
        )
        substitute_fit = _safe_point_fit(substitute_data)
        substitute_results[exposure] = _fit_summary(substitute_fit, substitute_data)

    m1_common_coefficient = float(m1_common_fit.coefficients[0])
    m2_coefficient = float(m2_fit.coefficients[0])
    attenuation = (
        1.0 - abs(m2_coefficient) / abs(m1_common_coefficient)
        if m1_common_coefficient != 0
        else None
    )

    transport: dict[str, Any] = {}
    non_europe_ids = {
        str(row["society_id"])
        for row in rows
        if not _is_europe_region(str(row["region"]))
    }
    non_europe = prepare_model_data(
        rows, "m1", society_ids=non_europe_ids, macroregion_levels=macroregions
    )
    non_europe_fit = _safe_point_fit(non_europe, start=m1_fit.parameters)
    transport["non_europe"] = _fit_summary(non_europe_fit, non_europe)

    family_counts = Counter(m1_data.family_clusters)
    largest_families = [name for name, _ in family_counts.most_common(3)]
    without_largest_ids = {
        society_id
        for society_id, family in zip(
            m1_data.society_ids, m1_data.family_clusters, strict=True
        )
        if family not in largest_families
    }
    without_largest = prepare_model_data(
        rows, "m1", society_ids=without_largest_ids, macroregion_levels=macroregions
    )
    without_largest_fit = _safe_point_fit(without_largest, start=m1_fit.parameters)
    without_largest_summary = _fit_summary(without_largest_fit, without_largest)
    transport["without_three_largest_families"] = {
        "excluded_families": largest_families,
        **without_largest_summary,
    }

    leave_one_macroregion_out: dict[str, dict[str, Any]] = {}
    for macroregion in macroregions:
        ids = {
            str(row["society_id"])
            for row in rows
            if str(row["macroregion"]) != macroregion
        }
        subset = prepare_model_data(
            rows,
            "m1",
            society_ids=ids,
            macroregion_levels=macroregions,
        )
        subset_fit = _safe_point_fit(subset, start=m1_fit.parameters)
        leave_one_macroregion_out[macroregion] = _fit_summary(subset_fit, subset)
    transport["leave_one_macroregion_out"] = leave_one_macroregion_out

    cutpoint_sensitivity: list[dict[str, Any]] = []
    ordinal_se = float(m1_fit.standard_errors[0])
    for threshold in range(1, 5):
        binary = fit_binary_logit(m1_data.x, (m1_data.y >= threshold).astype(int))
        coefficient = float(binary.coefficients[0])
        standard_error = float(binary.standard_errors[0])
        pooled = math.sqrt(ordinal_se**2 + standard_error**2)
        cutpoint_sensitivity.append(
            {
                "threshold_ea033_at_least": threshold + 1,
                "success": binary.success,
                "coefficient": coefficient,
                "standard_error": standard_error,
                "same_sign": coefficient * observed > 0,
                "within_three_pooled_se": abs(coefficient - observed) <= 3 * pooled,
                "message": binary.message,
            }
        )

    supports_ok = all(
        row.get("fishing") is None or int(float(row["fishing"])) in range(10)
        for row in rows
    ) and all(
        row.get("political_complexity") is None
        or int(float(row["political_complexity"])) in range(1, 6)
        for row in rows
    )
    matrices_finite = all(
        np.all(np.isfinite(data.x)) and np.all(np.isfinite(data.y))
        for data in (m0_data, m1_data, m1_common_data, m2_data)
    )
    integrity = bool(
        supports_ok
        and matrices_finite
        and not provenance["duplicate_counts"]
        and len(m1_data.y) >= 600
        and len(np.unique(m1_data.y)) == 5
    )
    family_interval = _percentile_interval(family_values)
    enough_family = len(family_values) >= math.ceil(family_draws * 0.8)
    enough_spatial = len(spatial_values) >= math.ceil(spatial_draws * 0.8)
    enough_permutation = len(permutation_values) >= math.ceil(permutation_draws * 0.8)

    adjusted_association = bool(
        observed > 0
        and enough_family
        and family_interval[0] is not None
        and float(family_interval[0]) > 0
        and enough_permutation
        and permutation_p is not None
        and permutation_p <= 0.05
    )
    fishing_standardized = observed * m1_data.exposure_sd
    specificity = all(
        fishing_standardized
        > float(substitute_results[name]["standardized_coefficient"])
        for name in ("hunting", "gathering")
    )
    compiler_pattern = bool(
        attenuation is not None
        and attenuation >= 0.25
        and m2_fit.aic < m1_common_fit.aic
        and m2_coefficient * m1_common_coefficient > 0
    )
    loo_positive = sum(
        float(result["coefficient_per_category"]) > 0
        for result in leave_one_macroregion_out.values()
    )
    transport_gate = bool(
        float(transport["non_europe"]["coefficient_per_category"]) > 0
        and float(without_largest_summary["coefficient_per_category"]) > 0
        and loo_positive >= 6
    )
    ordinal_stability = all(
        bool(item["success"])
        and bool(item["same_sign"])
        and bool(item["within_three_pooled_se"])
        for item in cutpoint_sensitivity
    )
    provenance_ok = provenance_gate_passes(provenance)

    gates = {
        "EC_G0_PROVENANCE": _status(provenance_ok),
        "EC_G1_DATA_INTEGRITY": _status(integrity),
        "EC_G2_ADJUSTED_ASSOCIATION": _status(adjusted_association),
        "EC_G3_COASTAL_SEPARATION": _status(
            adjusted_association and "log1p_distance_to_coast" in m1_data.feature_names
        ),
        "EC_G4_SUBSISTENCE_SPECIFICITY": _status(specificity),
        "EC_G5_COMPILER_PATTERN": _status(compiler_pattern),
        "EC_G6_TRANSPORT": _status(transport_gate),
        "EC_G7_ORDINAL_STABILITY": _status(ordinal_stability),
    }
    verdict = registered_verdict(gates)

    missingness: dict[str, int] = {}
    for field in sorted(
        set(EA_VARIABLES.values())
        | set(CLIMATE_VARIABLES.values())
        | {"net_primary_production", "distance_to_coast"}
    ):
        missingness[field] = sum(row.get(field) is None for row in rows)

    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "ecological_compiler_study1_2026_08_26",
        "seed": SEED,
        "claim_tier": "descriptive",
        "verdict": verdict,
        "claim_ceiling": (
            "Cross-sectional association only; no causal, nutritional, neurobiological, "
            "genetic, or Europe-specific superiority inference."
        ),
        "gates": gates,
        "provenance": provenance,
        "data_audit": {
            "missingness": missingness,
            "macroregions": macroregions,
            "m1_outcome_counts": {
                str(level + 1): int((m1_data.y == level).sum()) for level in range(5)
            },
            "family_clusters": len(set(m1_data.family_clusters)),
            "spatial_clusters": len(set(m1_data.spatial_clusters)),
        },
        "models": {
            "m0": _fit_summary(m0_fit, m0_data),
            "m1": _fit_summary(m1_fit, m1_data),
            "m1_common_m2_sample": _fit_summary(m1_common_fit, m1_common_data),
            "m2": _fit_summary(m2_fit, m2_data),
        },
        "uncertainty": {
            "family_block": {
                "requested_draws": family_draws,
                "successful_draws": len(family_values),
                "failures": family_failures,
                "level_dropout_failures": family_level_dropouts,
                "attempts": family_attempts,
                "interval_95": family_interval,
            },
            "spatial_block": {
                "requested_draws": spatial_draws,
                "successful_draws": len(spatial_values),
                "failures": spatial_failures,
                "level_dropout_failures": spatial_level_dropouts,
                "attempts": spatial_attempts,
                "interval_95": _percentile_interval(spatial_values),
                "sufficient_draws": enough_spatial,
            },
            "within_macroregion_permutation": {
                "requested_draws": permutation_draws,
                "successful_draws": len(permutation_values),
                "failures": permutation_failures,
                "attempts": permutation_attempts,
                "one_sided_p": permutation_p,
                "null_interval_95": _percentile_interval(permutation_values),
            },
        },
        "subsistence_substitutes": substitute_results,
        "compiler_pattern": {
            "m1_common_coefficient": m1_common_coefficient,
            "m2_coefficient": m2_coefficient,
            "proportional_attenuation": attenuation,
            "aic_change_m2_minus_m1_common": m2_fit.aic - m1_common_fit.aic,
        },
        "transport": transport,
        "leave_one_macroregion_out_positive_count": loo_positive,
        "cutpoint_sensitivity": cutpoint_sensitivity,
    }

    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    raw_root = ARTIFACT_ROOT / "run_2026_08_26"
    raw_root.mkdir(parents=True, exist_ok=True)
    (raw_root / "resampling_draws.json").write_text(
        json.dumps(
            {
                "family_block": family_values,
                "spatial_block": spatial_values,
                "within_macroregion_permutation": permutation_values,
                "point_fit": _serializable_fit(m1_fit),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (RESULTS_ROOT / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    write_markdown_summary(summary, RESULTS_ROOT / "summary.md")
    write_coefficient_figure(summary, RESULTS_ROOT / "model_coefficients.png")
    return summary


def write_markdown_summary(summary: dict[str, Any], path: Path) -> None:
    models = summary["models"]
    uncertainty = summary["uncertainty"]
    compiler = summary["compiler_pattern"]
    lines = [
        "# Ecological Compiler Study I Results",
        "",
        f"**Verdict: {str(summary['verdict']).upper()} at the descriptive claim tier.**",
        "",
        str(summary["claim_ceiling"]),
        "",
        "## Gate ledger",
        "",
        "| Gate | Verdict |",
        "|---|---|",
    ]
    for gate, verdict in summary["gates"].items():
        lines.append(f"| {gate} | {verdict} |")
    lines += [
        "",
        "## Primary estimates",
        "",
        "| Model | n | Fishing coefficient | Standardized coefficient | AIC |",
        "|---|---:|---:|---:|---:|",
    ]
    for key in ("m0", "m1", "m1_common_m2_sample", "m2"):
        result = models[key]
        lines.append(
            f"| {key} | {result['n']} | {result['coefficient_per_category']:.4f} | "
            f"{result['standardized_coefficient']:.4f} | {result['aic']:.2f} |"
        )
    family = uncertainty["family_block"]
    spatial = uncertainty["spatial_block"]
    permutation = uncertainty["within_macroregion_permutation"]
    lines += [
        "",
        "## Dependence and null checks",
        "",
        f"- Language-family block 95% interval: `{family['interval_95']}` "
        f"({family['successful_draws']}/{family['requested_draws']} fits).",
        f"- Spatial-block 95% interval: `{spatial['interval_95']}` "
        f"({spatial['successful_draws']}/{spatial['requested_draws']} fits).",
        f"- Within-macroregion permutation p-value: `{permutation['one_sided_p']}` "
        f"({permutation['successful_draws']}/{permutation['requested_draws']} fits).",
        "",
        "## Compiler-pattern check",
        "",
        f"On the common M2 sample, the fishing coefficient changed from "
        f"`{compiler['m1_common_coefficient']:.4f}` to "
        f"`{compiler['m2_coefficient']:.4f}`. Proportional attenuation was "
        f"`{compiler['proportional_attenuation']}` and the M2 minus M1 AIC change was "
        f"`{compiler['aic_change_m2_minus_m1_common']:.2f}`.",
        "",
        "## Interpretation boundary",
        "",
        "EA003 measures dependence on fishing, shellfishing, and large aquatic animals. "
        "It does not measure vitamin D, omega-3 status, dopamine, cognition, seafaring, "
        "or trade-network position. EA033 is an ordinal coding of jurisdictional levels, "
        "not a scalar measure of civilizational worth. Failed gates remain failures.",
    ]
    path.write_text("\n".join(lines) + "\n")


def write_coefficient_figure(summary: dict[str, Any], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = summary["models"]
    labels = ["Unadjusted M0", "Adjusted M1", "M1 on M2 sample", "M2 + mediators"]
    keys = ["m0", "m1", "m1_common_m2_sample", "m2"]
    values = np.array([float(models[key]["coefficient_per_category"]) for key in keys])
    errors = np.array(
        [1.96 * float(models[key]["approximate_standard_error"]) for key in keys]
    )
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    positions = np.arange(len(labels))
    axis.errorbar(
        values,
        positions,
        xerr=errors,
        fmt="o",
        color="#174a5b",
        ecolor="#76a9b5",
        capsize=4,
    )
    family_interval = summary["uncertainty"]["family_block"]["interval_95"]
    if family_interval[0] is not None and family_interval[1] is not None:
        family_lower = float(family_interval[0])
        family_upper = float(family_interval[1])
        axis.plot(
            np.asarray([family_lower, family_upper], dtype=float),
            np.asarray([1.13, 1.13], dtype=float),
            color="#c55a11",
            linewidth=4,
            solid_capstyle="round",
        )
    axis.axvline(0.0, color="#333333", linewidth=1, linestyle="--")
    axis.set_yticks(positions, labels)
    axis.invert_yaxis()
    axis.set_xlabel("Ordered-logit coefficient per fishing-dependence category")
    axis.set_title("Fishing dependence and jurisdictional hierarchy")
    axis.grid(axis="x", alpha=0.18)
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    plt.close(figure)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family-draws", type=int, default=300)
    parser.add_argument("--spatial-draws", type=int, default=300)
    parser.add_argument("--permutation-draws", type=int, default=500)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_analysis(
        family_draws=args.family_draws,
        spatial_draws=args.spatial_draws,
        permutation_draws=args.permutation_draws,
    )
    print(
        json.dumps({"verdict": summary["verdict"], "gates": summary["gates"]}, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
