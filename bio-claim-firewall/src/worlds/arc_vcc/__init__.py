"""Deterministic Arc VCC H1 measurement-world adapter.

Only compact measurement-derived fixtures from Arc's official real H1 sample
are handled here. State model code and weights are intentionally outside this
package and its fixture API.
"""

from .adapter import (
    ARC_VCC_OFFICIAL_URL,
    ARC_VCC_RULE_VERSION,
    ARC_VCC_SCHEMA_VERSION,
    ARC_VCC_SOURCE_COMMIT,
    ARC_VCC_SOURCE_ID,
    ArcVCCAdapter,
    ArcVCCClaim,
    ArcVCCIntegrityError,
    ArcVCCResult,
    FixtureMetadata,
    Measurement,
    check_arc_vcc_claim,
    load_fixture,
    validate_fixture,
)

__all__ = [
    "ARC_VCC_OFFICIAL_URL",
    "ARC_VCC_RULE_VERSION",
    "ARC_VCC_SCHEMA_VERSION",
    "ARC_VCC_SOURCE_COMMIT",
    "ARC_VCC_SOURCE_ID",
    "ArcVCCAdapter",
    "ArcVCCClaim",
    "ArcVCCIntegrityError",
    "ArcVCCResult",
    "FixtureMetadata",
    "Measurement",
    "check_arc_vcc_claim",
    "load_fixture",
    "validate_fixture",
]
