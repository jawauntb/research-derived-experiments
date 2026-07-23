"""Wave 1a arm / condition constants.

Extracted from :mod:`.modal_l4_sweep` so downstream aggregation code
(``run_confirmatory``) can import the arm names without triggering the
Modal decorator chain at module load time. The Modal sweep re-exports
these constants for backward compatibility with the on-worker code path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, Mapping


def _resolve_family_seed_ranges() -> Mapping[str, tuple[int, ...]]:
    """Return the per-family confirmatory seed tuples used by the sweep."""

    from experiments.concern_gated_retrieval_e2.wave0.families import (
        resource_constrained as _rc_family,
    )

    return {
        "delayed_commitments": tuple(range(200_000, 200_299 + 1)),
        "maintenance_fault": tuple(range(200_300, 200_599 + 1)),
        "resource_constrained": _rc_family.confirmatory_seeds(),
    }


FAMILY_SEED_RANGES: Final[Mapping[str, tuple[int, ...]]] = _resolve_family_seed_ranges()

PREREGISTERED_RESOURCE_CONSTRAINED_RANGE: Final[tuple[int, int]] = (200_600, 200_899)

REPLAY_RESERVE_RANGE: Final[tuple[int, int]] = (200_900, 201_999)

DEFAULT_ARTIFACT_PATH: Final[Path] = Path("artifacts/cogr_wave1a/e2a_rows.json")

ARM_FROZEN_WRONG: Final[str] = "frozen_wrong"
ARM_ONLINE_IPS: Final[str] = "online_learned_ips"
ARM_ONLINE_DR: Final[str] = "online_learned_dr"
COMPARATOR_INFO_MATCHED_VALUE: Final[str] = "info_matched_value"
COMPARATOR_INFO_MATCHED_PRIORITY: Final[str] = "info_matched_priority"
COMPARATOR_INFO_MATCHED_RECENCY: Final[str] = "info_matched_recency"
COMPARATOR_WRONG_AGENT: Final[str] = "wrong_agent"
CONDITION_ARM_SHUFFLED: Final[str] = "condition::shuffled"
CONDITION_ARM_WRONG_AGENT: Final[str] = "condition::wrong_agent"
CONDITION_ARM_ORACLE: Final[str] = "condition::oracle_ceiling"

SPECIFICITY_ARMS: Final[tuple[str, ...]] = (
    ARM_FROZEN_WRONG,
    ARM_ONLINE_IPS,
    ARM_ONLINE_DR,
    COMPARATOR_INFO_MATCHED_VALUE,
    COMPARATOR_INFO_MATCHED_PRIORITY,
    COMPARATOR_INFO_MATCHED_RECENCY,
    COMPARATOR_WRONG_AGENT,
)

COVERAGE_AUDIT_ARMS: Final[tuple[str, ...]] = (
    ARM_ONLINE_IPS,
    ARM_ONLINE_DR,
    CONDITION_ARM_SHUFFLED,
    CONDITION_ARM_WRONG_AGENT,
)
