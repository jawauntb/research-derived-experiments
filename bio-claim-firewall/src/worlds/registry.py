"""The versioned evidence-world registry used by the claim checker."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from audit import canonicalize_for_hash


class WorldRegistryError(ValueError):
    """A world selection or registry entry is not safe to use."""


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SourceContract:
    """One exact source admitted to a world bundle."""

    source: str
    sha256: str | None = None
    license: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise WorldRegistryError("source contract requires a non-empty source")
        if self.sha256 is not None and not _SHA256_RE.fullmatch(self.sha256):
            raise WorldRegistryError(f"source {self.source!r} has a partial or invalid sha256")

    def as_dict(self) -> dict[str, str]:
        value = {"source": self.source}
        if self.sha256 is not None:
            value["sha256"] = self.sha256
        if self.license is not None:
            value["license"] = self.license
        return value


@dataclass(frozen=True, slots=True)
class World:
    """An immutable world contract and its closed parser/checker fields."""

    world_id: str
    version: str
    source_allowlist: tuple[str, ...] = ()
    source_contracts: tuple[SourceContract, ...] = ()
    modality: str = "unknown"
    description: str = ""
    claim_fields: tuple[str, ...] = ("subject", "object", "direction")
    capabilities: tuple[str, ...] = ("check_structured_claim",)
    adapter: str = "k562"
    parser_schema: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.world_id or not self.version:
            raise WorldRegistryError("world_id and version are required")
        sources = tuple(self.source_allowlist)
        contracts = tuple(self.source_contracts)
        if len(sources) != len(set(sources)):
            raise WorldRegistryError(f"world {self.world_id!r} has duplicate source allowlist entries")
        contract_names = tuple(contract.source for contract in contracts)
        if len(contract_names) != len(set(contract_names)):
            raise WorldRegistryError(f"world {self.world_id!r} has duplicate source contracts")
        if sources and contracts and set(sources) != set(contract_names):
            raise WorldRegistryError(f"world {self.world_id!r} source allowlist and contracts differ")
        if not self.claim_fields or len(set(self.claim_fields)) != len(self.claim_fields):
            raise WorldRegistryError(f"world {self.world_id!r} has invalid claim fields")
        object.__setattr__(self, "source_allowlist", sources)
        object.__setattr__(self, "source_contracts", contracts)
        object.__setattr__(self, "claim_fields", tuple(self.claim_fields))
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "parser_schema", MappingProxyType(dict(self.parser_schema)))

    @property
    def world_key(self) -> str:
        return f"{self.world_id}/{self.version}"

    @property
    def digest(self) -> str:
        """Stable digest of the registered contract, excluding run metadata."""
        payload = {
            "world_id": self.world_id,
            "version": self.version,
            "modality": self.modality,
            "description": self.description,
            "source_contracts": [c.as_dict() for c in sorted(self.source_contracts, key=lambda c: c.source)],
            "claim_fields": list(self.claim_fields),
            "capabilities": list(self.capabilities),
            "adapter": self.adapter,
            "parser_schema": dict(self.parser_schema),
        }
        return hashlib.sha256(canonicalize_for_hash(payload)).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return {
            "world_id": self.world_id,
            "version": self.version,
            "world_key": self.world_key,
            "world_digest": self.digest,
            "modality": self.modality,
            "description": self.description,
            "source_allowlist": list(self.source_allowlist),
            "source_contracts": [c.as_dict() for c in self.source_contracts],
            "claim_fields": list(self.claim_fields),
            "capabilities": list(self.capabilities),
            "adapter": self.adapter,
            "parser_schema": dict(self.parser_schema),
        }


# These are the exact source names in the frozen compatibility world.  The
# SHA-256 values are repeated here so a caller cannot replace one source with a
# same-named, differently-hashed snapshot and still satisfy world binding.
K562_WORLD = World(
    world_id="replogle-k562",
    version="2022-pilot",
    modality="perturbational",
    description="Human K562 CRISPRi perturbation-effect evidence from Replogle 2022.",
    source_allowlist=(
        "cellline.2026_pilot",
        "cellontology.2026_pilot",
        "hgnc.2026_pilot",
        "ncbitaxon.2026_pilot",
        "perturbseq.replogle_2022",
        "reactome.2026_pilot",
    ),
    source_contracts=(
        SourceContract("cellline.2026_pilot", "2812b130349fdf85a32ad4192064a14cc9a4241ec61eabb6dfefdebc6ffb7fee", "CC-BY-4.0"),
        SourceContract("cellontology.2026_pilot", "d0801ecac3cae19b03c6d2b839bc01914941c14de4c1abf4b0e33401e9e6e3d7", "CC-BY-4.0"),
        SourceContract("hgnc.2026_pilot", "8a3627d7257bf3787580c8737aefeaa8741213fe7e4725ccdd5a131734737bab", "CC0-1.0"),
        SourceContract("ncbitaxon.2026_pilot", "4bab09bbc0900954a13ab2fd396bf15047ca3e717aee550620ef2ab372cefc9b", "Public-Domain"),
        SourceContract("perturbseq.replogle_2022", "2f1a951c23b8685091ee3979300fce582c61cab1fa9970b5cad332872734bfb8", "CC0-1.0"),
        SourceContract("reactome.2026_pilot", "fa31cf7f2a994e27d1f33cd4f25b31fb5cb070e0a3aa645c80ea19565d79fdea", "CC0-1.0"),
    ),
    claim_fields=("subject", "object", "direction"),
    capabilities=("check_structured_claim", "check_natural_language", "resolve_hgnc_labels"),
    adapter="k562",
    parser_schema={
        "type": "object",
        "additionalProperties": False,
        "required": ["subject", "object", "direction"],
        "properties": {
            "subject": {"type": "string"},
            "object": {"type": "string"},
            "direction": {"type": "string", "enum": ["increases", "decreases"]},
        },
    },
)


class WorldRegistry:
    """Immutable lookup table keyed by the explicit ``(world_id, version)``."""

    def __init__(self, worlds: Iterable[World]) -> None:
        entries = tuple(worlds)
        seen: set[tuple[str, str]] = set()
        for world in entries:
            key = (world.world_id, world.version)
            if key in seen:
                raise WorldRegistryError(f"duplicate world registration: {world.world_key}")
            seen.add(key)
        self._worlds = entries
        self._by_key = MappingProxyType({(w.world_id, w.version): w for w in entries})

    @property
    def worlds(self) -> tuple[World, ...]:
        return self._worlds

    def resolve(self, world_id: str, world_version: str | None) -> World:
        if not isinstance(world_id, str) or not world_id.strip():
            raise WorldRegistryError("world_id is required")
        if not isinstance(world_version, str) or not world_version.strip():
            raise WorldRegistryError("world_version is required for explicit world binding")
        try:
            return self._by_key[(world_id, world_version)]
        except KeyError as exc:
            raise WorldRegistryError(f"unknown world or version: {world_id}/{world_version}") from exc


WORLD_REGISTRY = WorldRegistry((K562_WORLD,))


def get_world(world_id: str, world_version: str | None = None, *, registry: WorldRegistry = WORLD_REGISTRY) -> World:
    return registry.resolve(world_id, world_version)


def list_worlds(*, registry: WorldRegistry = WORLD_REGISTRY) -> tuple[World, ...]:
    return registry.worlds

