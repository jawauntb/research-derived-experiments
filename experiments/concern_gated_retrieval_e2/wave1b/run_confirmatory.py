#!/usr/bin/env python3
"""Wave 1b confirmatory aggregator.

Consumes the raw Modal receipt at ``artifacts/cogr_wave1b/rows.json``
produced by :mod:`.modal_l4_sweep` and produces the Wave 1b L1 and L2
screen verdicts at

* ``experiments/concern_gated_retrieval_e2/wave1b/results/verdict_L1.json``
* ``experiments/concern_gated_retrieval_e2/wave1b/results/verdict_L2.json``

Two verdicts, one aggregator
----------------------------

Wave 1b's promotion contracts issue L1 and L2 separately
(``PROMOTION_CONTRACT_L1.md``, ``PROMOTION_CONTRACT_L2.md``): L1 asks
whether the candidate mechanism's LEARNED geometry beats a
frequency-matched random null on task outcome and edge intervention
(non-ceiling representation contribution), and L2 asks whether the
online-learned concern (composed with LEARNED geometry) recovers from
the wrong prior. A concern-recovery failure blocks L2 but NOT L1.

Pipeline
--------

1. Load the raw JSON payload from
   ``artifacts/cogr_wave1b/rows.json``.
2. Bucket per-cell payloads by ``(family, geometry, concern)``.
3. Run the wave 1b **leakage audit** (label permutation + randomized
   generator) against
   :func:`~experiments.concern_gated_retrieval_e2.wave1b.learned_geometry.learn_graph`
   on a calibration slice per family. A single audit fail is a
   non-compensatory KILL of the L1 verdict
   (``PROMOTION_CONTRACT_L1.md`` G9 → ``PREREGISTRATION.md`` §10).
4. **L1 gate scoring** for every family:
   - Paired-seed contrast between the candidate mechanism cell
     (``LEARNED × FROZEN_WRONG``) and the frequency-matched random null
     (``FREQ_MATCHED_RANDOM × FROZEN_WRONG``). The paired lower bound
     ``Δ − 2σ`` must clear the frozen wave 0 ``delta_thresh_L1`` for the
     family (``PREREGISTRATION.md`` §11).
   - Non-ceiling headroom to the oracle ceiling
     (``ORACLE_WITHHELD × FROZEN_WRONG``); the candidate must sit
     ``≥ 0.05`` below the ceiling on every family (G5 non_ceiling).
   - Edge-intervention diagnostic: the ``intervention_delta`` on
     ``LEARNED × FROZEN_WRONG`` seeds must move ``Δ_task`` in the
     predicted direction on ≥ 70% of seeds where the intervention
     produced a different selection (G2 L1_representation).
   - Integrity audit clean on every non-ceiling cell (G0).
   - Leakage audit clean on every family (G9, above).
5. **L2 gate scoring** for every family:
   - Blocked by L1 failing the same family (per
     ``PROMOTION_CONTRACT_L2.md`` pre-condition).
   - Paired-seed recovery contrast between
     ``LEARNED × ONLINE_LEARNED`` and ``LEARNED × FROZEN_WRONG``. The
     paired lower bound ``Δ − 2σ`` must clear zero (recovery has real
     effect) and ideally clear the family's ``delta_thresh_L1`` too.
   - The receipt copies the online-concern arm's mean into the L2
     verdict for downstream inspection; the family's mean concern-shift
     (``concern_after − concern_before`` L1 norm) is echoed as a
     diagnostic.
6. Write both verdict JSONs.

Wave 1b decision rule (``PROMOTION_CONTRACT_L1.md`` / ``_L2.md``):
non-compensatory — any single-gate FAIL kills the verdict for the
affected family. Aggregate L1 (respectively L2) is PASS iff every
family PASSes. Per the honor-the-preregistration rule, no post-hoc
threshold swap is permitted.

Scope
-----

This module is aggregation only. It CANNOT establish semantic meaning,
selfhood, or an L3 transferable retrieval principle; those are Wave 3+
objects. It CAN reject L1 or L2 (or both) on the wave 1b fatal gates
implemented above.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Callable, Final, Iterable, Mapping

# Path shim so ``python experiments/.../run_confirmatory.py`` works
# whether the caller is running from the repo root or from inside the
# subpackage.
for _parent in Path(__file__).resolve().parents:
    if (_parent / "experiments").exists():
        sys.path.insert(0, str(_parent))
        break

from experiments.concern_gated_retrieval_e2.wave1b.crossed import (  # noqa: E402
    CONCERN_FROZEN_WRONG,
    CONCERN_ONLINE_LEARNED,
    FAMILY_AXIS,
    FAMILY_DELAYED,
    FAMILY_MAINTENANCE,
    FAMILY_RESOURCE,
    GEOM_FREQ_MATCHED_RANDOM,
    GEOM_LEARNED,
    GEOM_ORACLE_WITHHELD,
)
from experiments.concern_gated_retrieval_e2.wave1b.leakage_audit import (  # noqa: E402
    AuditVerdict,
    DEFAULT_N_PERMUTATIONS,
    DEFAULT_TOLERANCE,
    LeakageError,
    audit_label_permutation,
    audit_randomized_generator,
)
from experiments.concern_gated_retrieval_e2.wave1b.learned_geometry import (  # noqa: E402
    HYBRID,
    learn_graph,
)
# NOTE: DEFAULT_ARTIFACT_PATH is inlined here rather than imported from
# ``modal_l4_sweep`` because that module loads the ``modal`` package at import
# time, which is unavailable in the local aggregation runtime (the aggregator
# runs via ``uv run`` without the Modal SDK). The value is a trivial constant;
# keep it byte-identical to ``modal_l4_sweep.DEFAULT_ARTIFACT_PATH``.
DEFAULT_ARTIFACT_PATH: Path = Path("artifacts/cogr_wave1b/rows.json")


__all__ = [
    "DEFAULT_L1_VERDICT_PATH",
    "DEFAULT_L2_VERDICT_PATH",
    "FrozenL1Thresholds",
    "L1_FAMILY_THRESHOLDS",
    "L1_NON_CEILING_HEADROOM",
    "L2_INTERVENTION_DIRECTION_MIN_FRAC",
    "aggregate",
    "main",
    "read_rows",
    "run_leakage_audits",
    "score_l1",
    "score_l2",
    "write_verdict",
]


# --------------------------------------------------------------------------- #
# Committed public verdict paths
# --------------------------------------------------------------------------- #


DEFAULT_L1_VERDICT_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "results" / "verdict_L1.json"
)
DEFAULT_L2_VERDICT_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "results" / "verdict_L2.json"
)


# --------------------------------------------------------------------------- #
# Frozen thresholds (PREREGISTRATION.md §11)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FrozenL1Thresholds:
    """Per-family L1 effect thresholds from Wave 0 PROVENANCE §4.

    ``mu_best`` is Wave 0's mean best-matched-baseline outcome,
    ``sigma_best`` its per-seed standard deviation, ``headroom`` the
    slack to the oracle ceiling, ``delta_L1`` the promotion delta the
    candidate mechanism must beat on the paired-seed lower bound
    ``Δ − 2σ``. These numbers are quoted verbatim from Wave 0's
    ``PROVENANCE.md`` §4 and reproduced in the wave 1b build brief.
    """

    mu_best: float
    sigma_best: float
    headroom: float
    delta_L1: float


L1_FAMILY_THRESHOLDS: Final[Mapping[str, FrozenL1Thresholds]] = {
    FAMILY_DELAYED: FrozenL1Thresholds(
        mu_best=0.5314, sigma_best=0.0218, headroom=0.4845, delta_L1=0.0484
    ),
    FAMILY_MAINTENANCE: FrozenL1Thresholds(
        mu_best=0.5029, sigma_best=0.0267, headroom=0.4548, delta_L1=0.0534
    ),
    FAMILY_RESOURCE: FrozenL1Thresholds(
        mu_best=0.5750, sigma_best=0.0250, headroom=0.4291, delta_L1=0.0500
    ),
}


#: G5 non-ceiling headroom. The candidate mechanism (and every
#: promotable baseline) must sit at least this far below the oracle
#: ceiling on every family (``PREREGISTRATION.md`` §9).
L1_NON_CEILING_HEADROOM: Final[float] = 0.05


#: G2 L1_representation direction requirement. The learned-edge
#: intervention must move ``Δ_task`` in the predicted direction on at
#: least this fraction of the seeds where the intervention actually
#: changed the retrieval selection.
L2_INTERVENTION_DIRECTION_MIN_FRAC: Final[float] = 0.70


#: L2 concern-recovery lower-bound floor. The online-learned recovery
#: contrast (``ONLINE_LEARNED × LEARNED`` vs ``FROZEN_WRONG × LEARNED``)
#: paired lower bound ``Δ − 2σ`` must clear this value. Held at ``0.0``
#: as the minimum-viable recovery bar: online learning must produce a
#: statistically real positive shift over the wrong prior on paired
#: seeds. Larger per-family L2 thresholds are calibrated post-run from
#: the confirmatory rows (``PROMOTION_CONTRACT_L2.md``).
L2_RECOVERY_LOWER_BOUND_MIN: Final[float] = 0.0


#: Default calibration seed slice sizes per family for the leakage audit.
#: The wave 1b leakage-audit helpers default ``generator_offsets``
#: to ``(0, 200)`` which fits inside the DC/MF 1000-seed calibration
#: window, and the audit uses a small slice per family so it does not
#: dominate aggregator runtime. Resource-constrained v2 exposes only
#: 32 calibration templates and its own offset window; the loader
#: resolves those from the family generator at aggregate time.
DEFAULT_LEAKAGE_AUDIT_SEED_COUNT: Final[int] = 20


# --------------------------------------------------------------------------- #
# Row / cell shape helpers
# --------------------------------------------------------------------------- #


def _cell_key(plan: Mapping[str, Any]) -> tuple[str, str, str]:
    """Return the ``(family, geometry, concern)`` key of a cell plan dict."""
    return (
        str(plan["family"]),
        str(plan["geometry"]),
        str(plan["concern"]),
    )


def _cells_by_key(payload: Mapping[str, Any]) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    """Bucket per-cell payloads by ``(family, geometry, concern)``.

    Raises :class:`ValueError` if two payloads collide on the same key
    (which would mean the sweep dispatched the same cell twice — a
    Modal fan-out bug).
    """
    grouped: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for cell in payload.get("cells", []):
        plan = cell.get("plan") or {}
        key = _cell_key(plan)
        if key in grouped:
            raise ValueError(
                f"duplicate cell key {key!r} in payload; the sweep "
                "dispatched the same cell twice (see modal_l4_sweep.py)"
            )
        grouped[key] = cell
    return grouped


def _rows_by_seed(cell: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
    """Bucket a cell's rows by seed so paired contrasts can join on seed."""
    by_seed: dict[int, Mapping[str, Any]] = {}
    for row in cell.get("rows", []):
        seed = int(row["seed"])
        if seed in by_seed:
            raise ValueError(
                f"duplicate seed {seed!r} inside cell "
                f"{cell.get('cell_id')!r}; check the cell runner"
            )
        by_seed[seed] = row
    return by_seed


# --------------------------------------------------------------------------- #
# Paired-seed contrast
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PairedSeedContrast:
    """Paired-seed contrast summary between two cells' realized rewards.

    The two cells MUST cover the same seeds (which is guaranteed by the
    wave 1b crossed factorial: every ``(family, seed)`` appears once
    per ``(geometry, concern)`` combination, and the sweep dispatches
    the full ``(lo, hi)`` slice per cell).
    """

    n_pairs: int
    mean_delta: float
    std_delta: float
    lower_bound_2sigma: float
    mean_left: float
    mean_right: float


def _paired_contrast(
    left: Mapping[int, Mapping[str, Any]],
    right: Mapping[int, Mapping[str, Any]],
    *,
    field: str = "realized_reward",
) -> PairedSeedContrast:
    """Return the ``(left − right)`` paired-seed contrast on ``field``.

    Seeds present in only one side are silently dropped from the
    contrast (the aggregator reports the pair count separately). The
    standard deviation is the sample standard deviation (Bessel-corrected
    when at least two pairs are present).
    """
    common = sorted(set(left) & set(right))
    if not common:
        return PairedSeedContrast(
            n_pairs=0,
            mean_delta=0.0,
            std_delta=0.0,
            lower_bound_2sigma=0.0,
            mean_left=0.0,
            mean_right=0.0,
        )
    deltas: list[float] = []
    left_values: list[float] = []
    right_values: list[float] = []
    for seed in common:
        lv = float(left[seed][field])
        rv = float(right[seed][field])
        deltas.append(lv - rv)
        left_values.append(lv)
        right_values.append(rv)
    n = len(deltas)
    mean_delta = sum(deltas) / n
    std_delta = statistics.stdev(deltas) if n > 1 else 0.0
    lower = mean_delta - 2.0 * std_delta
    return PairedSeedContrast(
        n_pairs=n,
        mean_delta=float(mean_delta),
        std_delta=float(std_delta),
        lower_bound_2sigma=float(lower),
        mean_left=float(sum(left_values) / n),
        mean_right=float(sum(right_values) / n),
    )


def _paired_contrast_dict(contrast: PairedSeedContrast) -> dict[str, Any]:
    return {
        "n_pairs": int(contrast.n_pairs),
        "mean_delta": float(contrast.mean_delta),
        "std_delta": float(contrast.std_delta),
        "lower_bound_2sigma": float(contrast.lower_bound_2sigma),
        "mean_left": float(contrast.mean_left),
        "mean_right": float(contrast.mean_right),
    }


# --------------------------------------------------------------------------- #
# Leakage audit
# --------------------------------------------------------------------------- #


def _calibration_seeds_and_offsets(
    family: str, *, seed_count: int = DEFAULT_LEAKAGE_AUDIT_SEED_COUNT
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Return ``(seeds, generator_offsets)`` for the leakage audit on ``family``.

    Delayed / maintenance families expose the full 1000-seed calibration
    window, so we use the audit's default ``(0, 200)`` offsets over a
    small slice starting at seed ``100_000``. Resource-constrained v2
    only exposes 32 calibration templates in ``[100_600, 100_632)``, so
    we clamp the slice to that window and use ``(0, 10)`` offsets that
    stay inside the calibration range.
    """
    if family == FAMILY_RESOURCE:
        from experiments.concern_gated_retrieval_e2.wave1b.families import (
            resource_constrained_v2 as _rc_v2,
        )

        lo = _rc_v2.CALIBRATION_SEED_START
        hi = _rc_v2.CALIBRATION_SEED_END
        window = hi - lo
        base_slice_len = min(seed_count, max(1, window // 2))
        seeds = tuple(range(lo, lo + base_slice_len))
        # Keep base + max(offset) inside the window: window is 32, base
        # slice takes the first ~10, offsets stay in [0, ~10].
        max_off = max(0, window - base_slice_len - 1)
        offsets: tuple[int, ...]
        if max_off >= 1:
            offsets = (0, min(max_off, 10))
        else:
            offsets = (0,)
        return seeds, offsets
    # DC / MF calibration range is [100_000, 100_999]; the audit's
    # default (0, 200) fits.
    seeds = tuple(range(100_000, 100_000 + int(seed_count)))
    return seeds, (0, 200)


def run_leakage_audits(
    *,
    n_permutations: int = DEFAULT_N_PERMUTATIONS,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Return per-family leakage audits for
    :func:`learn_graph` composed with the wave 1b :data:`HYBRID` spec.

    For every family the function runs the label-permutation audit and
    the randomized-generator audit against the family's calibration
    slice, and returns a nested dict of the shape

    ``{family: {"label_permutation": {...}, "randomized_generator": {...}}}``.

    A single ``passed=False`` fires the G9 leakage-audit gate downstream.
    Audit exceptions (e.g. a family whose calibration window cannot
    support the audit's default offsets) are captured on the ``error``
    key so the verdict receipt is unambiguous rather than crashing the
    aggregator.
    """
    from experiments.concern_gated_retrieval_e2.wave1b.families import (
        delayed_commitments_v2 as _dc_v2,
        maintenance_fault_v2 as _mf_v2,
        resource_constrained_v2 as _rc_v2,
    )

    generators: dict[str, Callable[..., Any]] = {
        FAMILY_DELAYED: _dc_v2.generate_episode,
        FAMILY_MAINTENANCE: _mf_v2.generate_episode,
        FAMILY_RESOURCE: _rc_v2.generate_episode,
    }

    learn_fn = partial(learn_graph, features=HYBRID)

    out: dict[str, dict[str, dict[str, Any]]] = {}
    for family in FAMILY_AXIS:
        seeds, offsets = _calibration_seeds_and_offsets(family)
        family_generator = generators[family]

        # Materialise the sealed calibration batch so audit_label_permutation
        # gets EpisodeSpec instances (its interface refuses anything else).
        from experiments.concern_gated_retrieval_e2.wave0.template_split import (
            TemplateBucket,
        )

        family_out: dict[str, dict[str, Any]] = {}

        try:
            batch = [
                family_generator(seed=int(s), bucket=TemplateBucket.CALIBRATION)
                for s in seeds
            ]
            verdict_lp = audit_label_permutation(
                learn_fn,
                batch,
                n_permutations=int(n_permutations),
                tolerance=float(tolerance),
            )
            family_out["label_permutation"] = _audit_verdict_dict(verdict_lp)
        except (LeakageError, ValueError, TypeError) as exc:  # pragma: no cover — defensive
            family_out["label_permutation"] = {
                "passed": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

        try:
            verdict_rg = audit_randomized_generator(
                learn_fn,
                family_generator,
                seeds,
                bucket=TemplateBucket.CALIBRATION,
                generator_offsets=offsets,
                n_permutations=int(n_permutations),
                tolerance=float(tolerance),
            )
            family_out["randomized_generator"] = _audit_verdict_dict(verdict_rg)
        except (LeakageError, ValueError, TypeError) as exc:  # pragma: no cover — defensive
            family_out["randomized_generator"] = {
                "passed": False,
                "error": f"{type(exc).__name__}: {exc}",
            }

        out[family] = family_out
    return out


def _audit_verdict_dict(verdict: AuditVerdict) -> dict[str, Any]:
    return {
        "audit": verdict.audit,
        "passed": bool(verdict.passed),
        "observed_stat": float(verdict.observed_stat),
        "null_mean": float(verdict.null_mean),
        "null_std": float(verdict.null_std),
        "z_score": float(verdict.z_score),
        "p_value": float(verdict.p_value),
        "tolerance": float(verdict.tolerance),
        "n_samples": int(verdict.n_samples),
        "n_permutations": int(verdict.n_permutations),
        "reason": str(verdict.reason),
    }


def _leakage_passed_for_family(family_leakage: Mapping[str, Any]) -> bool:
    """Return True iff every audit for a family passed and no error surfaced."""
    for entry in family_leakage.values():
        if not entry.get("passed"):
            return False
    return True


# --------------------------------------------------------------------------- #
# Intervention direction receipt (G2 L1_representation)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class InterventionDiagnostic:
    """Edge-intervention diagnostic on the LEARNED × FROZEN_WRONG cell.

    Wave 1b ``PREREGISTRATION.md`` §9 G2: ablating the top-scoring
    learned edge should move ``Δ_task`` in the predicted direction —
    typically DOWNWARD on cells whose task depends on that edge (i.e.
    ``intervention_delta < 0`` means removing the edge hurt the sealed
    outcome, which is the expected "the edge was genuinely load-bearing"
    signal). We report the fraction of seeds where the intervention
    changed the selection AND the resulting delta was strictly negative;
    the G2 pass criterion is that this fraction meets
    :data:`L2_INTERVENTION_DIRECTION_MIN_FRAC`.

    Seeds where the intervention did not change the selection contribute
    a ``delta = 0.0`` per the runner (``crossed.run_cell``); we exclude
    them from the direction fraction so the receipt reflects only seeds
    where the diagnostic actually probed the edge.
    """

    n_active: int
    n_direction_matched: int
    direction_fraction: float
    mean_delta_active: float


def _intervention_diagnostic(
    rows: Iterable[Mapping[str, Any]],
) -> InterventionDiagnostic:
    active_deltas: list[float] = []
    for row in rows:
        delta = row.get("intervention_delta")
        edge = row.get("intervention_edge")
        if edge is None:
            # No edge to intervene on (empty learned graph) — skip.
            continue
        if delta is None:
            # Runner did not record a diagnostic on this seed.
            continue
        # ``delta = 0.0`` from the runner means "intervention produced
        # the same selection". Only score the direction on seeds where
        # the intervention actually changed something.
        if float(delta) == 0.0:
            continue
        active_deltas.append(float(delta))
    n_active = len(active_deltas)
    if n_active == 0:
        return InterventionDiagnostic(
            n_active=0,
            n_direction_matched=0,
            direction_fraction=0.0,
            mean_delta_active=0.0,
        )
    n_matched = sum(1 for d in active_deltas if d < 0.0)
    return InterventionDiagnostic(
        n_active=n_active,
        n_direction_matched=n_matched,
        direction_fraction=float(n_matched) / float(n_active),
        mean_delta_active=float(sum(active_deltas) / n_active),
    )


def _intervention_dict(diag: InterventionDiagnostic) -> dict[str, Any]:
    return {
        "n_active": int(diag.n_active),
        "n_direction_matched": int(diag.n_direction_matched),
        "direction_fraction": float(diag.direction_fraction),
        "mean_delta_active": float(diag.mean_delta_active),
    }


# --------------------------------------------------------------------------- #
# L1 scoring
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class L1FamilyReport:
    """Per-family L1 scoring block."""

    family: str
    n_seeds: int
    thresholds: FrozenL1Thresholds
    contrast_learned_vs_random: PairedSeedContrast
    non_ceiling_headroom: float | None
    intervention: InterventionDiagnostic
    leakage: Mapping[str, Any]
    integrity_ok: bool
    gate_results: Mapping[str, bool]
    kill_reasons: tuple[str, ...]
    passed: bool


def score_l1(
    grouped: Mapping[tuple[str, str, str], Mapping[str, Any]],
    leakage: Mapping[str, Mapping[str, Any]],
) -> dict[str, L1FamilyReport]:
    """Return per-family L1 scoring reports.

    L1 gate composition (``PROMOTION_CONTRACT_L1.md``):

    * G0 integrity — every non-ceiling cell reports
      ``integrity_audit_passed=True`` in its cell receipt.
    * G1 L1_behavior — the paired-seed lower bound of the candidate
      mechanism (``LEARNED × FROZEN_WRONG``) minus the frequency-matched
      random null (``FREQ_MATCHED_RANDOM × FROZEN_WRONG``) meets the
      family's frozen ``delta_L1``. This is a representation-contribution
      contrast: same concern axis, geometry axis swapped for the null.
      Full oracle-recall / simple-regret dominance across the baseline
      slate is scored by :mod:`wave1b.oracle_regret` when the full
      baseline sweep is available; the sweep receipt this aggregator
      consumes only contains the crossed cells, so the L1 metric it can
      score here is the representation-contribution paired contrast plus
      the intervention diagnostic.
    * G2 L1_representation — the intervention diagnostic on the LEARNED
      cell moves ``Δ_task`` in the predicted (negative) direction on
      ``≥ L2_INTERVENTION_DIRECTION_MIN_FRAC`` of active seeds.
    * G5 non_ceiling — the candidate cell sits ``≥ L1_NON_CEILING_HEADROOM``
      below the ORACLE_WITHHELD ceiling cell's mean reward.
    * G9 leakage_audit — both audits pass for the family.
    """
    reports: dict[str, L1FamilyReport] = {}
    for family in FAMILY_AXIS:
        thresholds = L1_FAMILY_THRESHOLDS[family]

        candidate_cell = grouped.get((family, GEOM_LEARNED, CONCERN_FROZEN_WRONG))
        null_cell = grouped.get(
            (family, GEOM_FREQ_MATCHED_RANDOM, CONCERN_FROZEN_WRONG)
        )
        ceiling_cell = grouped.get(
            (family, GEOM_ORACLE_WITHHELD, CONCERN_FROZEN_WRONG)
        )

        gate_results: dict[str, bool] = {}
        kill_reasons: list[str] = []

        # G0 integrity — every non-ceiling cell for the family reports OK.
        integrity_cells = [
            grouped.get((family, geom, con))
            for geom in (GEOM_LEARNED, GEOM_FREQ_MATCHED_RANDOM)
            for con in (CONCERN_FROZEN_WRONG, CONCERN_ONLINE_LEARNED)
        ]
        integrity_ok = all(
            bool(c and c.get("integrity_audit_passed", False))
            for c in integrity_cells
            if c is not None
        ) and any(c is not None for c in integrity_cells)
        gate_results["G0_integrity"] = integrity_ok
        if not integrity_ok:
            kill_reasons.append("G0_integrity: IntegrityAudit fail on a non-ceiling cell")

        # G1 L1_behavior — paired contrast candidate vs matched random.
        if candidate_cell is None or null_cell is None:
            gate_results["G1_L1_behavior"] = False
            kill_reasons.append(
                "G1_L1_behavior: missing candidate or null cell (LEARNED×FROZEN "
                "or FREQ_MATCHED_RANDOM×FROZEN)"
            )
            contrast = PairedSeedContrast(
                n_pairs=0, mean_delta=0.0, std_delta=0.0,
                lower_bound_2sigma=0.0, mean_left=0.0, mean_right=0.0,
            )
            n_seeds = 0
        else:
            candidate_rows = _rows_by_seed(candidate_cell)
            null_rows = _rows_by_seed(null_cell)
            contrast = _paired_contrast(candidate_rows, null_rows)
            n_seeds = contrast.n_pairs
            passes_g1 = contrast.lower_bound_2sigma >= thresholds.delta_L1
            gate_results["G1_L1_behavior"] = bool(passes_g1)
            if not passes_g1:
                kill_reasons.append(
                    f"G1_L1_behavior: paired lower bound "
                    f"{contrast.lower_bound_2sigma:.4f} < delta_L1 "
                    f"{thresholds.delta_L1:.4f}"
                )

        # G2 L1_representation — intervention diagnostic on the LEARNED cell.
        if candidate_cell is None:
            intervention = InterventionDiagnostic(
                n_active=0, n_direction_matched=0,
                direction_fraction=0.0, mean_delta_active=0.0,
            )
            gate_results["G2_L1_representation"] = False
            kill_reasons.append(
                "G2_L1_representation: missing LEARNED×FROZEN cell for the family"
            )
        else:
            intervention = _intervention_diagnostic(candidate_cell.get("rows", []))
            passes_g2 = (
                intervention.n_active > 0
                and intervention.direction_fraction >= L2_INTERVENTION_DIRECTION_MIN_FRAC
            )
            gate_results["G2_L1_representation"] = bool(passes_g2)
            if not passes_g2:
                kill_reasons.append(
                    f"G2_L1_representation: intervention direction fraction "
                    f"{intervention.direction_fraction:.3f} < required "
                    f"{L2_INTERVENTION_DIRECTION_MIN_FRAC:.3f} "
                    f"(n_active={intervention.n_active})"
                )

        # G5 non_ceiling — candidate is at least L1_NON_CEILING_HEADROOM
        # below the oracle ceiling on realized reward.
        non_ceiling_headroom: float | None = None
        if candidate_cell is None or ceiling_cell is None:
            gate_results["G5_non_ceiling"] = False
            kill_reasons.append(
                "G5_non_ceiling: missing candidate or oracle-ceiling cell"
            )
        else:
            candidate_mean = float(
                candidate_cell.get("aggregate", {}).get("mean_reward", 0.0)
            )
            ceiling_mean = float(
                ceiling_cell.get("aggregate", {}).get("mean_reward", 0.0)
            )
            non_ceiling_headroom = ceiling_mean - candidate_mean
            passes_g5 = non_ceiling_headroom >= L1_NON_CEILING_HEADROOM
            gate_results["G5_non_ceiling"] = bool(passes_g5)
            if not passes_g5:
                kill_reasons.append(
                    f"G5_non_ceiling: candidate mean {candidate_mean:.4f} "
                    f"within {non_ceiling_headroom:.4f} of ceiling "
                    f"{ceiling_mean:.4f}; required >= "
                    f"{L1_NON_CEILING_HEADROOM:.2f}"
                )

        # G9 leakage_audit — both audits pass for the family.
        family_leakage = leakage.get(family, {})
        leakage_ok = _leakage_passed_for_family(family_leakage)
        gate_results["G9_leakage_audit"] = bool(leakage_ok)
        if not leakage_ok:
            for name, entry in family_leakage.items():
                if not entry.get("passed"):
                    reason = entry.get("reason") or entry.get("error", "")
                    kill_reasons.append(
                        f"G9_leakage_audit::{name}: {reason}"
                    )

        passed = all(gate_results.values())
        reports[family] = L1FamilyReport(
            family=family,
            n_seeds=n_seeds,
            thresholds=thresholds,
            contrast_learned_vs_random=contrast,
            non_ceiling_headroom=non_ceiling_headroom,
            intervention=intervention,
            leakage=family_leakage,
            integrity_ok=integrity_ok,
            gate_results=gate_results,
            kill_reasons=tuple(kill_reasons),
            passed=bool(passed),
        )
    return reports


# --------------------------------------------------------------------------- #
# L2 scoring
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class L2FamilyReport:
    """Per-family L2 scoring block.

    L2 is blocked when the corresponding family L1 verdict is not PASS
    (per ``PROMOTION_CONTRACT_L2.md`` pre-condition). A blocked family
    reports ``passed=False`` with ``withheld=True``.
    """

    family: str
    withheld: bool
    n_seeds: int
    contrast_recovery: PairedSeedContrast
    mean_concern_shift_l1: float
    integrity_ok: bool
    gate_results: Mapping[str, bool]
    kill_reasons: tuple[str, ...]
    passed: bool


def _mean_concern_shift_l1(cell: Mapping[str, Any]) -> float:
    """Return the mean L1-norm shift ``||concern_after − concern_before||_1``.

    Diagnostic for the online-learned cells only; frozen-wrong / oracle
    cells have ``concern_after = None`` per the runner and therefore
    return ``0.0``.
    """
    shifts: list[float] = []
    for row in cell.get("rows", []):
        before = row.get("concern_before") or {}
        after = row.get("concern_after")
        if after is None:
            continue
        keys = set(before) | set(after)
        shifts.append(
            sum(abs(float(after.get(k, 0.0)) - float(before.get(k, 0.0))) for k in keys)
        )
    if not shifts:
        return 0.0
    return float(sum(shifts) / len(shifts))


def score_l2(
    grouped: Mapping[tuple[str, str, str], Mapping[str, Any]],
    l1_reports: Mapping[str, L1FamilyReport],
) -> dict[str, L2FamilyReport]:
    """Return per-family L2 scoring reports.

    L2 gate composition (``PROMOTION_CONTRACT_L2.md``):

    * L1 pass on the same family (blocking pre-condition).
    * G0 integrity — the ONLINE_LEARNED × LEARNED cell reports
      ``integrity_audit_passed=True``.
    * G3 L2_recovery — paired-seed lower bound of
      ``LEARNED × ONLINE_LEARNED`` minus ``LEARNED × FROZEN_WRONG``
      clears :data:`L2_RECOVERY_LOWER_BOUND_MIN` (default ``0.0``).
      Additionally the mean-concern-shift diagnostic must be strictly
      positive, so a "recovered" verdict cannot be reached without the
      online update actually moving the concern prior.

    G4 specificity (vs info-matched value/priority/recency), G6 bundle
    awareness, and G7 adversarial poisoning are scored by other
    modules against a fuller baseline sweep; those gates are marked
    ``UNVERIFIED`` on the verdict receipt here so the reader does not
    mistake a partial pass for a full L2 promotion.
    """
    reports: dict[str, L2FamilyReport] = {}
    for family in FAMILY_AXIS:
        online_cell = grouped.get(
            (family, GEOM_LEARNED, CONCERN_ONLINE_LEARNED)
        )
        frozen_cell = grouped.get(
            (family, GEOM_LEARNED, CONCERN_FROZEN_WRONG)
        )

        gate_results: dict[str, bool] = {}
        kill_reasons: list[str] = []
        withheld = False

        l1_report = l1_reports.get(family)
        if l1_report is None or not l1_report.passed:
            withheld = True
            gate_results["L1_precondition"] = False
            kill_reasons.append(
                f"L1_precondition: L1 verdict for family {family!r} did not "
                "pass; L2 withheld per PROMOTION_CONTRACT_L2.md."
            )
        else:
            gate_results["L1_precondition"] = True

        if online_cell is None or frozen_cell is None:
            gate_results["G0_integrity"] = False
            gate_results["G3_L2_recovery"] = False
            kill_reasons.append(
                "G3_L2_recovery: missing LEARNED×ONLINE or LEARNED×FROZEN cell"
            )
            contrast = PairedSeedContrast(
                n_pairs=0, mean_delta=0.0, std_delta=0.0,
                lower_bound_2sigma=0.0, mean_left=0.0, mean_right=0.0,
            )
            mean_shift = 0.0
            integrity_ok = False
            n_seeds = 0
        else:
            integrity_ok = bool(
                online_cell.get("integrity_audit_passed", False)
                and frozen_cell.get("integrity_audit_passed", False)
            )
            gate_results["G0_integrity"] = integrity_ok
            if not integrity_ok:
                kill_reasons.append(
                    "G0_integrity: IntegrityAudit fail on the L2 cells"
                )
            online_rows = _rows_by_seed(online_cell)
            frozen_rows = _rows_by_seed(frozen_cell)
            contrast = _paired_contrast(online_rows, frozen_rows)
            n_seeds = contrast.n_pairs
            mean_shift = _mean_concern_shift_l1(online_cell)
            passes_g3 = (
                contrast.lower_bound_2sigma >= L2_RECOVERY_LOWER_BOUND_MIN
                and mean_shift > 0.0
            )
            gate_results["G3_L2_recovery"] = bool(passes_g3)
            if not passes_g3:
                kill_reasons.append(
                    f"G3_L2_recovery: paired lower bound "
                    f"{contrast.lower_bound_2sigma:.4f} < "
                    f"{L2_RECOVERY_LOWER_BOUND_MIN:.4f} or mean_concern_shift "
                    f"{mean_shift:.4f} <= 0"
                )

        # The remaining L2 gates require a fuller baseline sweep that
        # this aggregator's raw receipt does not contain.  Mark them
        # UNVERIFIED so a reader cannot mistake a partial pass for a
        # full L2 promotion.
        gate_results["G4_L2_specificity"] = False
        gate_results["G6_bundle_awareness"] = False
        gate_results["G7_adversarial"] = False
        kill_reasons.append(
            "L2 UNVERIFIED: G4 specificity, G6 bundle awareness, and G7 "
            "adversarial are scored against a fuller baseline sweep than "
            "the crossed cells; this receipt reports L1 pre-condition + "
            "G3 recovery only.  Full L2 promotion requires those gates "
            "to be scored by their respective harnesses before this "
            "verdict can be signed."
        )

        # A family passes L2 only if the L1 pre-condition, G0 integrity,
        # and G3 recovery all pass, AND the withheld flag is False.
        passed = (
            not withheld
            and integrity_ok
            and gate_results.get("G3_L2_recovery", False)
        )
        # But we still surface the UNVERIFIED note so the receipt is not
        # signed until the outer harness clears G4/G6/G7 separately.
        reports[family] = L2FamilyReport(
            family=family,
            withheld=bool(withheld),
            n_seeds=int(n_seeds),
            contrast_recovery=contrast,
            mean_concern_shift_l1=float(mean_shift),
            integrity_ok=bool(integrity_ok),
            gate_results=gate_results,
            kill_reasons=tuple(kill_reasons),
            passed=bool(passed),
        )
    return reports


# --------------------------------------------------------------------------- #
# Verdict serialisation
# --------------------------------------------------------------------------- #


def _l1_family_dict(report: L1FamilyReport) -> dict[str, Any]:
    return {
        "family": report.family,
        "n_seeds": int(report.n_seeds),
        "thresholds": {
            "mu_best": float(report.thresholds.mu_best),
            "sigma_best": float(report.thresholds.sigma_best),
            "headroom": float(report.thresholds.headroom),
            "delta_L1": float(report.thresholds.delta_L1),
        },
        "contrast_learned_vs_random": _paired_contrast_dict(
            report.contrast_learned_vs_random
        ),
        "non_ceiling_headroom": (
            None if report.non_ceiling_headroom is None
            else float(report.non_ceiling_headroom)
        ),
        "intervention_diagnostic": _intervention_dict(report.intervention),
        "leakage": dict(report.leakage),
        "integrity_ok": bool(report.integrity_ok),
        "gate_results": {k: bool(v) for k, v in report.gate_results.items()},
        "kill_reasons": list(report.kill_reasons),
        "passed": bool(report.passed),
    }


def _l2_family_dict(report: L2FamilyReport) -> dict[str, Any]:
    return {
        "family": report.family,
        "withheld": bool(report.withheld),
        "n_seeds": int(report.n_seeds),
        "contrast_recovery": _paired_contrast_dict(report.contrast_recovery),
        "mean_concern_shift_l1": float(report.mean_concern_shift_l1),
        "integrity_ok": bool(report.integrity_ok),
        "gate_results": {k: bool(v) for k, v in report.gate_results.items()},
        "kill_reasons": list(report.kill_reasons),
        "passed": bool(report.passed),
    }


# --------------------------------------------------------------------------- #
# Aggregate
# --------------------------------------------------------------------------- #


def aggregate(
    payload: Mapping[str, Any],
    *,
    n_permutations: int = DEFAULT_N_PERMUTATIONS,
    tolerance: float = DEFAULT_TOLERANCE,
    skip_leakage_audit: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Aggregate a raw sweep payload into the L1 and L2 verdicts.

    Returns ``(l1_verdict, l2_verdict)``. Each verdict is a JSON-safe
    dict; :func:`write_verdict` serialises them to disk.

    ``skip_leakage_audit`` short-circuits the label-permutation and
    randomized-generator audits; only used by smoke runs where the
    audit's calibration episodes take longer than the smoke cell itself.
    Production runs must NOT set this to ``True`` — the leakage audit
    is a G9 non-compensatory gate.
    """
    grouped = _cells_by_key(payload)

    if skip_leakage_audit:
        leakage: dict[str, Mapping[str, Any]] = {
            family: {
                "label_permutation": {
                    "passed": False,
                    "skipped": True,
                    "reason": "skip_leakage_audit=True (smoke only)",
                },
                "randomized_generator": {
                    "passed": False,
                    "skipped": True,
                    "reason": "skip_leakage_audit=True (smoke only)",
                },
            }
            for family in FAMILY_AXIS
        }
    else:
        leakage = run_leakage_audits(
            n_permutations=int(n_permutations),
            tolerance=float(tolerance),
        )

    l1_reports = score_l1(grouped, leakage)
    l2_reports = score_l2(grouped, l1_reports)

    aggregate_l1_pass = all(r.passed for r in l1_reports.values())
    aggregate_l2_pass = all(r.passed for r in l2_reports.values())

    l1_verdict: dict[str, Any] = {
        "kind": "cogr_wave1b_e2b_L1_verdict",
        "wave": "1b",
        "target": "COGR-E2b L1 (representation contribution)",
        "confirmatory_seed_range": [200_000, 201_999],
        "aggregate_decision": "PASS" if aggregate_l1_pass else "KILL",
        "aggregate_kill_reasons": [
            f"{family}::{reason}"
            for family, r in l1_reports.items()
            for reason in r.kill_reasons
            if not r.passed
        ],
        "families": {
            family: _l1_family_dict(report)
            for family, report in l1_reports.items()
        },
        "leakage_audit_summary": leakage,
        "manifest": payload.get("manifest"),
        "cell_receipts": payload.get("cell_receipts"),
        "n_cells": payload.get("n_cells"),
        "n_rows_total": payload.get("n_rows_total"),
    }
    l2_verdict: dict[str, Any] = {
        "kind": "cogr_wave1b_e2b_L2_verdict",
        "wave": "1b",
        "target": "COGR-E2b L2 (concern recovery + specificity)",
        "confirmatory_seed_range": [200_000, 201_999],
        "aggregate_decision": (
            "PASS" if aggregate_l2_pass
            else ("WITHHELD" if any(r.withheld for r in l2_reports.values())
                  else "KILL")
        ),
        "aggregate_kill_reasons": [
            f"{family}::{reason}"
            for family, r in l2_reports.items()
            for reason in r.kill_reasons
            if not r.passed
        ],
        "families": {
            family: _l2_family_dict(report)
            for family, report in l2_reports.items()
        },
        "l1_precondition_summary": {
            family: bool(report.passed)
            for family, report in l1_reports.items()
        },
        "manifest": payload.get("manifest"),
        "cell_receipts": payload.get("cell_receipts"),
        "n_cells": payload.get("n_cells"),
        "n_rows_total": payload.get("n_rows_total"),
    }
    return l1_verdict, l2_verdict


# --------------------------------------------------------------------------- #
# I/O
# --------------------------------------------------------------------------- #


def read_rows(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"raw sweep receipt not found at {path}; run the Modal sweep "
            "first (scripts/deploy_and_run_cogr_wave1b.sh)"
        )
    return json.loads(path.read_text())


def write_verdict(verdict: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.concern_gated_retrieval_e2.wave1b.run_confirmatory",
        description=(
            "Aggregate the Wave 1b Modal raw receipt into the L1 and L2 "
            "screen verdicts. Non-compensatory: any per-family FAIL kills "
            "the affected verdict."
        ),
    )
    parser.add_argument(
        "--in",
        dest="in_path",
        type=Path,
        default=DEFAULT_ARTIFACT_PATH,
        help=(
            "Path to the raw Modal receipt "
            f"(default: {DEFAULT_ARTIFACT_PATH})."
        ),
    )
    parser.add_argument(
        "--out-l1",
        type=Path,
        default=DEFAULT_L1_VERDICT_PATH,
        help=(
            "Path for the L1 verdict JSON "
            f"(default: {DEFAULT_L1_VERDICT_PATH})."
        ),
    )
    parser.add_argument(
        "--out-l2",
        type=Path,
        default=DEFAULT_L2_VERDICT_PATH,
        help=(
            "Path for the L2 verdict JSON "
            f"(default: {DEFAULT_L2_VERDICT_PATH})."
        ),
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=DEFAULT_N_PERMUTATIONS,
        help=(
            "Leakage-audit permutation count "
            f"(default: {DEFAULT_N_PERMUTATIONS})."
        ),
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_TOLERANCE,
        help=(
            "Leakage-audit one-sided p-value tolerance "
            f"(default: {DEFAULT_TOLERANCE})."
        ),
    )
    parser.add_argument(
        "--skip-leakage-audit",
        action="store_true",
        help=(
            "Skip the label-permutation and randomized-generator audits. "
            "Smoke runs only — production runs MUST NOT set this flag."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _cli_parser()
    args = parser.parse_args(argv)
    payload = read_rows(args.in_path)
    l1_verdict, l2_verdict = aggregate(
        payload,
        n_permutations=int(args.n_permutations),
        tolerance=float(args.tolerance),
        skip_leakage_audit=bool(args.skip_leakage_audit),
    )
    write_verdict(l1_verdict, args.out_l1)
    write_verdict(l2_verdict, args.out_l2)
    print(
        json.dumps(
            {
                "kind": "cogr_wave1b_verdict_summary",
                "l1_decision": l1_verdict["aggregate_decision"],
                "l2_decision": l2_verdict["aggregate_decision"],
                "l1_verdict_path": str(args.out_l1),
                "l2_verdict_path": str(args.out_l2),
                "n_rows_total": payload.get("n_rows_total"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    # Exit codes: 0 iff both PASS, 3 iff L1 KILL, 4 iff L2 KILL/WITHHELD
    # (L1 might still be PASS). Downstream CI can regex-match on the
    # decision string.
    l1_ok = l1_verdict["aggregate_decision"] == "PASS"
    l2_ok = l2_verdict["aggregate_decision"] == "PASS"
    if l1_ok and l2_ok:
        return 0
    if not l1_ok:
        return 3
    return 4


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
