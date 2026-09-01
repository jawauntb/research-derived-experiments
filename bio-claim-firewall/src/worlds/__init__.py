"""Explicit, immutable evidence-world contracts.

The registry is deliberately small and boring: a caller must select both a
world id and version before an adapter or evidence bundle can be used.  World
entries are data, not plugin discovery; adapters are registered explicitly.
"""

from .registry import (
    ARC_VCC_WORLD,
    CLINICAL_TRIALS_WORLD,
    K562_WORLD,
    OPEN_TARGETS_WORLD,
    WORLD_REGISTRY,
    SourceContract,
    World,
    WorldRegistry,
    WorldRegistryError,
    get_world,
    list_worlds,
)

__all__ = [
    "ARC_VCC_WORLD",
    "CLINICAL_TRIALS_WORLD",
    "K562_WORLD",
    "OPEN_TARGETS_WORLD",
    "WORLD_REGISTRY",
    "SourceContract",
    "World",
    "WorldRegistry",
    "WorldRegistryError",
    "get_world",
    "list_worlds",
]
