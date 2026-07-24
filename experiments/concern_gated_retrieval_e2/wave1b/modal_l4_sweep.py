#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal L4 fan-out for the Concern-Gated Retrieval Wave 1b E2b confirmatory
crossed-factorial sweep.

Wave 1b operating rules (see
``docs/concern_gated_retrieval_research_program.md`` and
``experiments/concern_gated_retrieval_e2/wave1b/PREREGISTRATION.md``):

* L4 GPU only. Modal H100 is explicitly forbidden by the wave rule
  (``PREREGISTRATION.md`` §5).
* ``max_containers=64`` — the human director explicitly authorized scaling
  to 64 for Wave 1b (Wave 1a's ``32`` cap does not apply). One container
  per crossed cell is the natural granularity: 27 cells fit comfortably.
* ``single_use_containers=True``, ``retries=1``, ``cpu=4``,
  ``memory=16384``, ``timeout=1800`` per the build brief.
* Doppler scope: ``/Users/jawaun/superoptimizers``.
* Deploy the image before spawning (per the deployed-image rule); the
  deployed image digest is recorded in ``PROVENANCE.md`` §3.
* Budget guard: refuse to dispatch when the conservative timeout-based
  cost estimate exceeds ``$30`` (build brief; still under the 35% H100
  rate ceiling — each L4 worker holds ~30 min of runway with headroom).
* ``add_local_dir`` ignores the 7.4 GB worktrees tree, git/venv/cache
  clutter, papers/pdf, and reference archives so the Modal upload stays
  focused on the source tree (Wave 0 got stuck on this).

App name: ``research-derived-cogr-wave1b-e2b``.

Cell shape
----------

A cell is one ``(geometry, concern, family)`` triple in the wave 1b
crossed factorial. Geometry axis
:data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.GEOMETRY_AXIS`
is ``{LEARNED, FREQ_MATCHED_RANDOM, ORACLE_WITHHELD}``, concern axis
:data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.CONCERN_AXIS`
is ``{FROZEN_WRONG, ONLINE_LEARNED, ORACLE}``, family axis is
``{delayed_commitments, maintenance_fault, resource_constrained}`` — the
three ``wave1b.families.*_v2`` generators. 3 × 3 × 3 = **27 cells**,
each ``N = 300`` confirmatory seeds from the wave 1b per-family
seed slices in
:data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.FAMILY_SEED_RANGES`
(``delayed_commitments`` ``200000..200299``; ``maintenance_fault``
``200300..200599``; ``resource_constrained`` ``200600..200899``).

Every cell is dispatched to :func:`run_cell` as a single Modal task —
the ``ONLINE_LEARNED`` concern axis carries a running concern-anchor
prior across seeds in the cell, so per-cell batching would break the
sequential dependency. The frozen-wrong and oracle cells could in
principle be split, but running them whole keeps the fan-out shape
uniform and the per-cell provenance receipt unambiguous.

The raw receipt at ``artifacts/cogr_wave1b/rows.json`` is consumed by
:mod:`experiments.concern_gated_retrieval_e2.wave1b.run_confirmatory`
which runs the leakage audit + promotion harness and writes the L1 and
L2 verdict JSON files under
``experiments/concern_gated_retrieval_e2/wave1b/results/``.

Anti-leakage boundary
---------------------

This file is *evaluator-side* orchestration code. It composes
:func:`experiments.concern_gated_retrieval_e2.wave1b.crossed.run_cell`
which is the single choke point where the sealed
:class:`~experiments.concern_gated_retrieval_e2.wave0.sealed_env.SealedEnvironment`
is constructed and where the policy-side nomination callable is passed
through :meth:`IntegrityAudit.assert_clean`. The per-seed row and per-cell
aggregate returned by :func:`run_cell` are policy-visible; the sealed
answer-key nodes are NOT propagated into the row payload — the
aggregator recomputes them evaluator-side from the family generator so
the JSON transport carries no forbidden field.

Wave 1a and Wave 0 reuse
------------------------

* :func:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.run_cell`
  is the per-cell executor (imported, never edited).
* :class:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.CellSpec`
  is the per-cell spec (imported, never edited).
* :data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.FAMILY_SEED_RANGES`
  provides the per-family confirmatory seed slice (imported, never
  edited).
* No Wave 0 or Wave 1a module is edited.

Wave 1b scope
-------------

This sweep CAN reject the L1 or L2 claim (via the fatal gates the
downstream aggregator scores). It CANNOT establish semantic meaning,
selfhood, or an L3 transferable retrieval principle; those are Wave 3+
objects.
"""

from __future__ import annotations

import importlib
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence


# Extend ``sys.path`` for two runtimes:
#   * inside the Modal container the repo lives at ``/root/project`` (see
#     :func:`_image` below);
#   * locally (dry-run, ``modal deploy``) the repo root is the first
#     ancestor that contains ``experiments/``.
sys.path.insert(0, "/root/project")
for _parent in Path(__file__).resolve().parents:
    if (_parent / "experiments").exists():
        sys.path.insert(0, str(_parent))
        break


modal = importlib.import_module("modal")


# --------------------------------------------------------------------------- #
# Modal constants (frozen at the wave build brief)
# --------------------------------------------------------------------------- #


APP_NAME: Final[str] = "research-derived-cogr-wave1b-e2b"
GPU: Final[str] = "L4"
TIMEOUT_SECONDS: Final[int] = 1800
CPU: Final[int] = 4
MEMORY_MB: Final[int] = 16_384

#: Concurrent-container ceiling. Wave 1b explicitly authorises up to 64
#: containers (build brief); Wave 1a's ``32`` cap does not apply.
CONTAINER_CEILING: Final[int] = 64

#: Modal L4 rate approximation in USD per GPU-second (``$0.80/hr / 3600``).
#: Same reference rate the Wave 1a sweep uses so the two waves' cost
#: receipts stay comparable.
GPU_RATE_PER_SECOND: Final[float] = 0.80 / 3600.0

#: Budget hard cap. The Modal local entrypoint refuses to dispatch if the
#: conservative timeout-based estimate exceeds this value. Set at ``$30``
#: per the wave 1b build brief — the 27-cell plan sits well inside this
#: envelope (``27 × 1800 × 0.80/3600 ≈ $10.80`` at the ceiling).
HARD_CAP_USD: Final[float] = 30.0


#: Wave 1b confirmatory seed range. Documented on the payload manifest so
#: downstream provenance receipts can regression-check the sweep never
#: touched calibration seeds ``100000..100999``.
CONFIRMATORY_SEED_RANGE: Final[tuple[int, int]] = (200_000, 201_999)


#: Reserved replay range from ``PREREGISTRATION.md`` §5.  Only replayable
#: knobs (LoggedProbePolicy.epsilon in [0.05, 0.10], update_concern.eta
#: in [0.05, 0.20], cell-level rejection replay capped at 30%) may draw
#: seeds from here. Never entered by the default plan.
REPLAY_RESERVE_RANGE: Final[tuple[int, int]] = (200_900, 201_999)


DEFAULT_ARTIFACT_PATH: Final[Path] = Path("artifacts/cogr_wave1b/rows.json")


# --------------------------------------------------------------------------- #
# CellPlan — JSON-safe wrapper around wave1b.crossed.CellSpec
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CellPlan:
    """One crossed cell to run on Modal.

    Thin serialisable wrapper around
    :class:`experiments.concern_gated_retrieval_e2.wave1b.crossed.CellSpec`.
    Modal exchanges plain dicts across container boundaries;
    :meth:`to_dict` / :meth:`from_dict` are the only supported
    serialisation entry points.

    Attributes
    ----------
    geometry:
        Geometry axis level. One of
        :data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.GEOMETRY_AXIS`.
    concern:
        Concern axis level. One of
        :data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.CONCERN_AXIS`.
    family:
        Family axis level. One of
        :data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.FAMILY_AXIS`.
    n_seeds:
        Number of confirmatory seeds the cell iterates over. Must match
        ``seed_range[1] - seed_range[0] + 1``.
    seed_range:
        Inclusive ``(lo, hi)`` seed slice. Must lie inside the family's
        entry in
        :data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.FAMILY_SEED_RANGES`.
    cell_id:
        Stable identifier of the shape
        ``cogr-wave1b::{family}::{geometry}::{concern}::seeds{lo}-{hi}``;
        set from :attr:`CellSpec.cell_id` at build time so the receipt
        key is uniform across processes.
    """

    geometry: str
    concern: str
    family: str
    n_seeds: int
    seed_range: tuple[int, int]
    cell_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "geometry": self.geometry,
            "concern": self.concern,
            "family": self.family,
            "n_seeds": int(self.n_seeds),
            "seed_range": [int(self.seed_range[0]), int(self.seed_range[1])],
            "cell_id": self.cell_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CellPlan":
        lo, hi = data["seed_range"]
        return cls(
            geometry=str(data["geometry"]),
            concern=str(data["concern"]),
            family=str(data["family"]),
            n_seeds=int(data["n_seeds"]),
            seed_range=(int(lo), int(hi)),
            cell_id=str(data["cell_id"]),
        )


def build_cells(
    *,
    n_seeds: int | None = None,
    families: Sequence[str] | None = None,
    geometries: Sequence[str] | None = None,
    concerns: Sequence[str] | None = None,
) -> tuple[CellPlan, ...]:
    """Return the wave 1b confirmatory cell plan.

    Delegates to
    :func:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.build_all_cells`
    for the default 3 × 3 × 3 = 27-cell plan and wraps each
    :class:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.CellSpec`
    in a JSON-safe :class:`CellPlan`. Optional per-axis filters produce
    the smoke preset used to sanity-check the container image without
    burning the full confirmatory budget.

    Parameters
    ----------
    n_seeds:
        Override the default seeds-per-cell count. ``None`` (the default)
        uses
        :data:`~experiments.concern_gated_retrieval_e2.wave1b.crossed.DEFAULT_SEEDS_PER_CELL`
        (300). Smoke preset calls pass a small value.
    families, geometries, concerns:
        Optional axis filters. Passing a subset lets the smoke preset run
        one family, one geometry, and one concern level without running
        the full crossed lattice. ``None`` means "all levels on that axis".
    """
    from experiments.concern_gated_retrieval_e2.wave1b.crossed import (
        CONCERN_AXIS,
        DEFAULT_SEEDS_PER_CELL,
        FAMILY_AXIS,
        FAMILY_SEED_RANGES,
        GEOMETRY_AXIS,
        CellSpec,
    )

    seeds = int(n_seeds) if n_seeds is not None else DEFAULT_SEEDS_PER_CELL
    if seeds <= 0:
        raise ValueError(f"n_seeds must be positive; got {seeds}")

    fam_filter = tuple(families) if families is not None else FAMILY_AXIS
    geo_filter = tuple(geometries) if geometries is not None else GEOMETRY_AXIS
    con_filter = tuple(concerns) if concerns is not None else CONCERN_AXIS

    unknown_fam = tuple(f for f in fam_filter if f not in FAMILY_AXIS)
    if unknown_fam:
        raise ValueError(f"unknown families: {unknown_fam!r}")
    unknown_geo = tuple(g for g in geo_filter if g not in GEOMETRY_AXIS)
    if unknown_geo:
        raise ValueError(f"unknown geometries: {unknown_geo!r}")
    unknown_con = tuple(c for c in con_filter if c not in CONCERN_AXIS)
    if unknown_con:
        raise ValueError(f"unknown concerns: {unknown_con!r}")

    cells: list[CellPlan] = []
    for geometry in geo_filter:
        for concern in con_filter:
            for family in fam_filter:
                lo, hi = FAMILY_SEED_RANGES[family]
                requested_hi = lo + seeds - 1
                if requested_hi > hi:
                    raise ValueError(
                        f"n_seeds={seeds} exceeds family "
                        f"{family!r} confirmatory slice width "
                        f"{hi - lo + 1}"
                    )
                spec = CellSpec(
                    geometry=geometry,
                    concern=concern,
                    family=family,
                    n_seeds=seeds,
                    seed_range=(lo, requested_hi),
                )
                cells.append(
                    CellPlan(
                        geometry=spec.geometry,
                        concern=spec.concern,
                        family=spec.family,
                        n_seeds=spec.n_seeds,
                        seed_range=spec.seed_range,
                        cell_id=spec.cell_id,
                    )
                )
    return tuple(cells)


# --------------------------------------------------------------------------- #
# Budget guard
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BudgetEstimate:
    """Conservative Modal-cost estimate for one Wave 1b sweep dispatch."""

    n_cells: int
    max_containers: int
    cell_timeout_seconds: int
    gpu_rate_per_second: float
    conservative_cost_usd: float
    wallclock_upper_bound_seconds: float
    wallclock_upper_bound_cost_usd: float
    hard_cap_usd: float
    within_hard_cap: bool


def estimate_cost_usd(
    n_cells: int,
    *,
    hard_cap_usd: float = HARD_CAP_USD,
    max_containers: int = CONTAINER_CEILING,
    cell_timeout_seconds: int = TIMEOUT_SECONDS,
    gpu_rate_per_second: float = GPU_RATE_PER_SECOND,
) -> BudgetEstimate:
    """Return a conservative Modal-cost estimate for ``n_cells``.

    Two figures:

    * ``conservative_cost_usd`` — every cell burns its full timeout, sums
      linearly. Used to decide whether to refuse the run.
    * ``wallclock_upper_bound_cost_usd`` — cells fan out over
      ``max_containers`` in parallel; each wave burns its full timeout.

    ``within_hard_cap`` is true iff
    ``conservative_cost_usd <= hard_cap_usd``. The Modal entrypoint
    refuses to dispatch when this is false, per the build brief's ``$30``
    cap.
    """
    if n_cells < 0:
        raise ValueError("n_cells must be non-negative")
    if max_containers < 1:
        raise ValueError("max_containers must be positive")
    if cell_timeout_seconds < 1:
        raise ValueError("cell_timeout_seconds must be positive")
    if gpu_rate_per_second < 0:
        raise ValueError("gpu_rate_per_second must be non-negative")
    conservative = n_cells * cell_timeout_seconds * gpu_rate_per_second
    waves = math.ceil(n_cells / max_containers) if n_cells else 0
    wallclock_seconds = waves * cell_timeout_seconds
    wallclock_cost = (
        waves
        * min(n_cells, max_containers)
        * cell_timeout_seconds
        * gpu_rate_per_second
    )
    return BudgetEstimate(
        n_cells=n_cells,
        max_containers=max_containers,
        cell_timeout_seconds=cell_timeout_seconds,
        gpu_rate_per_second=gpu_rate_per_second,
        conservative_cost_usd=conservative,
        wallclock_upper_bound_seconds=float(wallclock_seconds),
        wallclock_upper_bound_cost_usd=wallclock_cost,
        hard_cap_usd=hard_cap_usd,
        within_hard_cap=conservative <= hard_cap_usd,
    )


# --------------------------------------------------------------------------- #
# Row / cell serialisation
# --------------------------------------------------------------------------- #


def _receipt_to_dict(receipt: Any) -> dict[str, Any]:
    """Flatten a :class:`ProbeReceipt` into a JSON-safe dict."""
    return {
        "episode_id": str(receipt.episode_id),
        "candidate": str(receipt.candidate),
        "selection_propensity": float(receipt.selection_propensity),
        "source_id": str(receipt.source_id),
        "template_family_split": str(receipt.template_family_split),
        "exploratory": bool(receipt.exploratory),
    }


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Flatten a :class:`CellRow` into a JSON-safe dict.

    The row payload carries only policy-visible quantities plus
    scalar-aggregate outcomes from the sealed environment
    (``realized_reward``, ``constraint_preserved``,
    ``misretrieval_cost``, ``wall_actions``). The sealed answer key is
    NOT propagated — the downstream aggregator regenerates each episode
    evaluator-side to recover any answer-set quantity it needs.
    """
    return {
        "seed": int(row.seed),
        "episode_id": str(row.episode_id),
        "family": str(row.family),
        "budget": int(row.budget),
        "selected": list(row.selected),
        "realized_reward": float(row.realized_reward),
        "constraint_preserved": bool(row.constraint_preserved),
        "misretrieval_cost": float(row.misretrieval_cost),
        "wall_actions": int(row.wall_actions),
        "concern_before": {str(k): float(v) for k, v in row.concern_before.items()},
        "concern_after": (
            {str(k): float(v) for k, v in row.concern_after.items()}
            if row.concern_after is not None
            else None
        ),
        "receipt": _receipt_to_dict(row.receipt),
        "sealed_env_evaluate_calls": int(row.sealed_env_evaluate_calls),
        "intervention_edge": (
            [str(row.intervention_edge[0]), str(row.intervention_edge[1])]
            if row.intervention_edge is not None
            else None
        ),
        "intervention_delta": (
            float(row.intervention_delta)
            if row.intervention_delta is not None
            else None
        ),
    }


def _cell_result_to_dict(result: Any, plan: CellPlan) -> dict[str, Any]:
    """Flatten a :class:`CellResult` into a JSON-safe dict."""
    return {
        "plan": plan.to_dict(),
        "aggregate": {str(k): float(v) for k, v in result.aggregate.items()},
        "sealed_env_evaluate_calls": int(result.sealed_env_evaluate_calls),
        "integrity_audit_passed": bool(result.integrity_audit_passed),
        "wall_seconds": float(result.wall_seconds),
        "rows": [_row_to_dict(r) for r in result.rows],
    }


# --------------------------------------------------------------------------- #
# Cell execution
# --------------------------------------------------------------------------- #


def execute_cell(cell_dict: Mapping[str, Any]) -> dict[str, Any]:
    """Run one Wave 1b crossed cell locally.

    Called by :func:`run_cell` on the Modal side and directly by tests /
    the local dispatch path. Delegates to
    :func:`experiments.concern_gated_retrieval_e2.wave1b.crossed.run_cell`
    which is the single choke point that constructs the sealed
    environment and audits the policy nomination callable via
    :meth:`IntegrityAudit.assert_clean`.

    The L1 edge-intervention diagnostic is enabled by default on the
    ``LEARNED`` geometry cells (``intervention_edge_index=0``, matching
    the wave 1b PREREGISTRATION.md §9 G2 default). Cells whose geometry
    axis is not ``LEARNED`` ignore the argument.
    """
    # Container-side import shim.
    import sys as _sys

    _sys.path.insert(0, "/root/project")

    from experiments.concern_gated_retrieval_e2.wave1b.crossed import (
        CellSpec,
        GEOM_LEARNED,
        run_cell as _run_cell,
    )

    plan = CellPlan.from_dict(cell_dict)
    spec = CellSpec(
        geometry=plan.geometry,
        concern=plan.concern,
        family=plan.family,
        n_seeds=plan.n_seeds,
        seed_range=plan.seed_range,
    )

    start = time.time()
    intervention_edge_index = 0 if spec.geometry == GEOM_LEARNED else None
    result = _run_cell(
        spec,
        intervention_edge_index=intervention_edge_index,
    )
    wall = float(time.time() - start)

    payload = _cell_result_to_dict(result, plan)
    payload["outer_wall_seconds"] = wall
    payload["cell_id"] = plan.cell_id
    return payload


# --------------------------------------------------------------------------- #
# Payload merge / write
# --------------------------------------------------------------------------- #


def merge_payloads(payloads: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Merge per-cell payloads into a single receipt.

    The receipt shape carries the flattened per-cell payload list plus
    a compact cell-receipts index so the aggregator can regression-check
    the total row count and identify missing cells.
    """
    cells: list[dict[str, Any]] = []
    cell_receipts: list[dict[str, Any]] = []
    total_rows = 0
    for payload in payloads:
        cells.append(dict(payload))
        n_rows = len(payload.get("rows", []))
        total_rows += n_rows
        cell_receipts.append(
            {
                "cell_id": payload.get("cell_id"),
                "plan": payload.get("plan"),
                "aggregate": payload.get("aggregate"),
                "wall_seconds": payload.get("wall_seconds"),
                "outer_wall_seconds": payload.get("outer_wall_seconds"),
                "sealed_env_evaluate_calls": payload.get(
                    "sealed_env_evaluate_calls"
                ),
                "integrity_audit_passed": payload.get(
                    "integrity_audit_passed"
                ),
                "n_rows": n_rows,
            }
        )
    return {
        "kind": "cogr_wave1b_e2b_run",
        "app_name": APP_NAME,
        "gpu": GPU,
        "cell_receipts": cell_receipts,
        "cells": cells,
        "n_cells": len(cells),
        "n_rows_total": total_rows,
    }


def write_rows(payload: Mapping[str, Any], out_path: Path) -> None:
    """Write the merged payload as pretty-printed JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# Modal function / entrypoint
# --------------------------------------------------------------------------- #


def _image() -> Any:
    """Return the Modal image the L4 workers run inside.

    Mirrors Wave 0 / Wave 1a image so container behaviour is stable
    across the three waves. ``add_local_dir(".")`` ships the local
    project into ``/root/project`` while ignoring the 7.4 GB worktrees
    tree (Wave 0 got stuck on this), git/venv/cache clutter, papers/pdf,
    and reference archives.
    """
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git")
        .pip_install(
            "numpy>=1.26,<2.2",
            "pytest>=8,<10",
            "ruff>=0.8,<1.0",
            "sentence-transformers>=3.0,<6",
            "torch>=2.3,<2.8",
            "uv>=0.7,<1.0",
        )
        .add_local_dir(
            ".",
            remote_path="/root/project",
            ignore=[
                ".git",
                ".worktrees",
                ".venv",
                "__pycache__",
                "*.pyc",
                "artifacts",
                "references/papers",
                "references/text",
                "references/html",
                "tmp",
                "output",
                "papers/*/paper.pdf",
                "papers/pdf",
                "**/*.png",
            ],
        )
    )


IMAGE = _image()
app = modal.App(name=APP_NAME)


@app.function(
    image=IMAGE,
    gpu=GPU,
    timeout=TIMEOUT_SECONDS,
    cpu=CPU,
    memory=MEMORY_MB,
    max_containers=CONTAINER_CEILING,
    single_use_containers=True,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> dict[str, Any]:
    """Run one Wave 1b crossed cell inside an L4 worker.

    ``arg`` is a plain dict shaped by :meth:`CellPlan.to_dict`. Returns
    the per-cell payload shaped by :func:`_cell_result_to_dict`. The
    container re-imports :func:`execute_cell` locally so the Modal
    deploy step and the fan-out step exchange only plain dicts.
    """
    import sys as _sys

    _sys.path.insert(0, "/root/project")
    from experiments.concern_gated_retrieval_e2.wave1b.modal_l4_sweep import (
        execute_cell as _execute_cell,
    )

    return _execute_cell(arg)


def _preset_cells(preset: str) -> tuple[CellPlan, ...]:
    """Return the cell plan for a named preset.

    ``confirmatory`` is the full 27-cell plan (default). ``smoke`` runs a
    single ``LEARNED × FROZEN_WRONG × delayed_commitments`` cell over 4
    seeds — enough to prove the container image, spawn path, and the
    aggregator pipeline without burning the full budget.
    """
    if preset == "confirmatory":
        return build_cells()
    if preset == "smoke":
        from experiments.concern_gated_retrieval_e2.wave1b.crossed import (
            CONCERN_FROZEN_WRONG,
            FAMILY_DELAYED,
            GEOM_LEARNED,
        )

        return build_cells(
            n_seeds=4,
            families=(FAMILY_DELAYED,),
            geometries=(GEOM_LEARNED,),
            concerns=(CONCERN_FROZEN_WRONG,),
        )
    raise SystemExit(f"unknown preset {preset!r}")


@app.local_entrypoint()
def main(
    preset: str = "confirmatory",
    out: str = str(DEFAULT_ARTIFACT_PATH),
    hard_cap_usd: float = HARD_CAP_USD,
    dry_run_budget: bool = False,
) -> None:
    """Modal local entrypoint. Fans out over cells and writes the rows JSON.

    Steps:

    1. Build the cell plan for ``preset``.
    2. Estimate cost. Refuse if the conservative timeout-based cost
       exceeds ``hard_cap_usd`` (default ``$30``).
    3. If ``dry_run_budget`` is truthy, print the plan+manifest and
       return.
    4. Fan out :func:`run_cell` across the cell list using ``.map`` and
       merge the per-cell payloads via :func:`merge_payloads`.
    5. Write the raw JSON receipt to ``out`` (default
       ``artifacts/cogr_wave1b/rows.json``, a gitignored raw-artifacts
       path per ``AGENTS.md``). The public verdicts are produced by
       :mod:`.run_confirmatory` from the raw receipt.
    """
    cells = _preset_cells(preset)
    estimate = estimate_cost_usd(
        len(cells),
        hard_cap_usd=hard_cap_usd,
        max_containers=CONTAINER_CEILING,
        cell_timeout_seconds=TIMEOUT_SECONDS,
        gpu_rate_per_second=GPU_RATE_PER_SECOND,
    )
    manifest = {
        "kind": "cogr_wave1b_modal_manifest",
        "app": APP_NAME,
        "preset": preset,
        "gpu": GPU,
        "cpu": CPU,
        "memory_mb": MEMORY_MB,
        "max_containers": CONTAINER_CEILING,
        "timeout_seconds": TIMEOUT_SECONDS,
        "gpu_rate_per_second": GPU_RATE_PER_SECOND,
        "n_cells": len(cells),
        "hard_cap_usd": hard_cap_usd,
        "confirmatory_seed_range": list(CONFIRMATORY_SEED_RANGE),
        "replay_reserve_range": list(REPLAY_RESERVE_RANGE),
        "estimate": {
            "conservative_cost_usd": estimate.conservative_cost_usd,
            "wallclock_upper_bound_cost_usd": (
                estimate.wallclock_upper_bound_cost_usd
            ),
            "wallclock_upper_bound_seconds": (
                estimate.wallclock_upper_bound_seconds
            ),
            "within_hard_cap": estimate.within_hard_cap,
        },
        "cells": [c.to_dict() for c in cells],
    }
    print(
        json.dumps(
            {"kind": "dry-run manifest", "manifest": manifest},
            indent=2,
            sort_keys=True,
        )
    )

    if not estimate.within_hard_cap:
        raise SystemExit(
            "Refusing to dispatch: conservative timeout-based Modal cost "
            f"${estimate.conservative_cost_usd:.2f} exceeds hard cap "
            f"${hard_cap_usd:.2f} (Wave 1b build brief)."
        )
    if dry_run_budget:
        return

    cell_args = [cell.to_dict() for cell in cells]
    payloads = list(run_cell.map(cell_args))
    merged = merge_payloads(payloads)
    merged["manifest"] = manifest

    raw_out_path = Path(out)
    write_rows(merged, raw_out_path)
    print(f"Wrote raw Wave 1b confirmatory rows to {raw_out_path}")


__all__ = [
    "APP_NAME",
    "BudgetEstimate",
    "CONFIRMATORY_SEED_RANGE",
    "CONTAINER_CEILING",
    "CPU",
    "CellPlan",
    "DEFAULT_ARTIFACT_PATH",
    "GPU",
    "GPU_RATE_PER_SECOND",
    "HARD_CAP_USD",
    "IMAGE",
    "MEMORY_MB",
    "REPLAY_RESERVE_RANGE",
    "TIMEOUT_SECONDS",
    "app",
    "build_cells",
    "estimate_cost_usd",
    "execute_cell",
    "main",
    "merge_payloads",
    "run_cell",
    "write_rows",
]
