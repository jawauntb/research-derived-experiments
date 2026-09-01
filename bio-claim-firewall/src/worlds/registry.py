"""The versioned evidence-world registry used by the claim checker."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

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
    official_url: str | None = None
    terms_reference_url: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise WorldRegistryError("source contract requires a non-empty source")
        if self.sha256 is not None and not _SHA256_RE.fullmatch(self.sha256):
            raise WorldRegistryError(
                f"source {self.source!r} has a partial or invalid sha256"
            )
        for field_name in ("official_url", "terms_reference_url"):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, str) or not value.startswith("https://")
            ):
                raise WorldRegistryError(
                    f"source {self.source!r} has an invalid {field_name}"
                )

    def as_dict(self) -> dict[str, str]:
        value = {"source": self.source}
        if self.sha256 is not None:
            value["sha256"] = self.sha256
        if self.license is not None:
            value["license"] = self.license
        if self.official_url is not None:
            value["official_url"] = self.official_url
        if self.terms_reference_url is not None:
            value["terms_reference_url"] = self.terms_reference_url
        return value


@dataclass(frozen=True, slots=True)
class World:
    """An immutable world contract and its closed parser/checker fields."""

    world_id: str
    version: str
    source_allowlist: tuple[str, ...] = ()
    source_contracts: tuple[SourceContract, ...] = ()
    artifact_hashes: Mapping[str, str] = field(default_factory=dict)
    scenario_locators: Mapping[str, str] = field(default_factory=dict)
    modality: str = "unknown"
    description: str = ""
    claim_fields: tuple[str, ...] = ("subject", "object", "direction")
    capabilities: tuple[str, ...] = ("check_structured_claim",)
    adapter: str = "k562"
    parser_schema: Mapping[str, Any] = field(
        default_factory=dict, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not self.world_id or not self.version:
            raise WorldRegistryError("world_id and version are required")
        sources = tuple(self.source_allowlist)
        contracts = tuple(self.source_contracts)
        artifacts = dict(self.artifact_hashes)
        scenario_locators = dict(self.scenario_locators)
        if len(sources) != len(set(sources)):
            raise WorldRegistryError(
                f"world {self.world_id!r} has duplicate source allowlist entries"
            )
        contract_names = tuple(contract.source for contract in contracts)
        if len(contract_names) != len(set(contract_names)):
            raise WorldRegistryError(
                f"world {self.world_id!r} has duplicate source contracts"
            )
        if sources and contracts and set(sources) != set(contract_names):
            raise WorldRegistryError(
                f"world {self.world_id!r} source allowlist and contracts differ"
            )
        if not self.claim_fields or len(set(self.claim_fields)) != len(
            self.claim_fields
        ):
            raise WorldRegistryError(
                f"world {self.world_id!r} has invalid claim fields"
            )
        if any(
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(digest, str)
            or not _SHA256_RE.fullmatch(digest)
            for name, digest in artifacts.items()
        ):
            raise WorldRegistryError(
                f"world {self.world_id!r} has an invalid artifact hash contract"
            )
        if any(
            source not in sources
            or not isinstance(locator, str)
            or not locator.startswith("https://")
            for source, locator in scenario_locators.items()
        ):
            raise WorldRegistryError(
                f"world {self.world_id!r} has an invalid scenario locator contract"
            )
        object.__setattr__(self, "source_allowlist", sources)
        object.__setattr__(self, "source_contracts", contracts)
        object.__setattr__(self, "artifact_hashes", MappingProxyType(artifacts))
        object.__setattr__(
            self, "scenario_locators", MappingProxyType(scenario_locators)
        )
        object.__setattr__(self, "claim_fields", tuple(self.claim_fields))
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(
            self, "parser_schema", MappingProxyType(dict(self.parser_schema))
        )

    @property
    def world_key(self) -> str:
        return f"{self.world_id}/{self.version}"

    @property
    def digest(self) -> str:
        """Stable digest of the registered contract, excluding run metadata."""
        payload: dict[str, Any] = {
            "world_id": self.world_id,
            "version": self.version,
            "modality": self.modality,
            "description": self.description,
            "source_contracts": [
                c.as_dict()
                for c in sorted(self.source_contracts, key=lambda c: c.source)
            ],
            "claim_fields": list(self.claim_fields),
            "capabilities": list(self.capabilities),
            "adapter": self.adapter,
            "parser_schema": dict(self.parser_schema),
        }
        if self.artifact_hashes:
            payload["artifact_hashes"] = dict(sorted(self.artifact_hashes.items()))
        if self.scenario_locators:
            payload["scenario_locators"] = dict(sorted(self.scenario_locators.items()))
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
            "artifact_hashes": dict(sorted(self.artifact_hashes.items())),
            "scenario_locators": dict(sorted(self.scenario_locators.items())),
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
        SourceContract(
            "cellline.2026_pilot",
            "2812b130349fdf85a32ad4192064a14cc9a4241ec61eabb6dfefdebc6ffb7fee",
            "CC-BY-4.0",
        ),
        SourceContract(
            "cellontology.2026_pilot",
            "d0801ecac3cae19b03c6d2b839bc01914941c14de4c1abf4b0e33401e9e6e3d7",
            "CC-BY-4.0",
        ),
        SourceContract(
            "hgnc.2026_pilot",
            "8a3627d7257bf3787580c8737aefeaa8741213fe7e4725ccdd5a131734737bab",
            "CC0-1.0",
        ),
        SourceContract(
            "ncbitaxon.2026_pilot",
            "4bab09bbc0900954a13ab2fd396bf15047ca3e717aee550620ef2ab372cefc9b",
            "Public-Domain",
        ),
        SourceContract(
            "perturbseq.replogle_2022",
            "2f1a951c23b8685091ee3979300fce582c61cab1fa9970b5cad332872734bfb8",
            "CC0-1.0",
        ),
        SourceContract(
            "reactome.2026_pilot",
            "fa31cf7f2a994e27d1f33cd4f25b31fb5cb070e0a3aa645c80ea19565d79fdea",
            "CC0-1.0",
        ),
    ),
    claim_fields=("subject", "object", "direction"),
    capabilities=(
        "check_structured_claim",
        "check_natural_language",
        "resolve_hgnc_labels",
    ),
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


# These entries deliberately mirror the compact, real fixtures checked by the
# world adapters.  A source hash here is the hash of the retained source
# response/dataset bytes, not a hash of an arbitrary local fixture.  Keeping
# the contracts in this module means a caller cannot silently route one
# adapter through another world's snapshot.
ARC_VCC_WORLD = World(
    world_id="arc-vcc",
    version="2025-h1-measurements",
    modality="perturbational",
    description="Arc Institute H1 VCC 2025 real measurement subset.",
    source_allowlist=(
        "arc-cell-eval2-h1-vcc-real-subset",
        "arc-vcc-derived-ledger",
    ),
    source_contracts=(
        SourceContract(
            "arc-cell-eval2-h1-vcc-real-subset",
            "eb36c766cbf76353f9981cb3a3aa32137622d1de53b29d861c483742bcd4dec7",
            "MIT",
            "https://github.com/ArcInstitute/cell-eval2/blob/ddfc5df73c997b2f113a560bd863fb068f2b453a/docs/data/H1-VCC-2025-training.h5ad",
            "https://github.com/ArcInstitute/cell-eval2/blob/ddfc5df73c997b2f113a560bd863fb068f2b453a/LICENSE",
        ),
        SourceContract(
            "arc-vcc-derived-ledger",
            "4bd9c5fef5060ca500eac08af06ad9ecae3b4957382893f46e392c6193809853",
            "internal-derived",
        ),
    ),
    artifact_hashes={
        "arc-vcc-fixture-bundle": "2f226349ecfc9d5a598236342b3b35212d0531dd011573ffeb23317f067325b8",
    },
    claim_fields=(
        "perturbed_gene",
        "response_gene",
        "summary_statistic",
        "direction",
        "threshold",
        "assay",
        "split",
        "world_id",
        "world_version",
    ),
    capabilities=("check_structured_claim",),
    adapter="arc_vcc",
    parser_schema={
        "type": "object",
        "additionalProperties": False,
        "required": [
            "perturbed_gene",
            "response_gene",
            "summary_statistic",
            "direction",
            "threshold",
            "assay",
            "split",
        ],
        "properties": {
            "perturbed_gene": {"type": "string"},
            "response_gene": {"type": "string"},
            "summary_statistic": {"type": "string"},
            "direction": {"type": "string", "enum": ["increases", "decreases", "null"]},
            "threshold": {"type": "number"},
            "assay": {"type": "string"},
            "split": {"type": "string", "enum": ["development", "locked_holdout"]},
            "world_id": {"const": "arc-vcc"},
            "world_version": {"const": "2025-h1-measurements"},
        },
    },
)


OPEN_TARGETS_WORLD = World(
    world_id="open-targets",
    version="26.06",
    modality="translational_association",
    description="Open Targets 26.06 source-specific target-disease associations.",
    source_allowlist=("open-targets-graphql-26-06",),
    source_contracts=(
        SourceContract(
            "open-targets-graphql-26-06",
            "8e9299d18b7c9089b0cfe8c59183d9bedf1694cb69f8357fba580ec3a43badf4",
            "CC0-1.0",
            "https://platform-docs.opentargets.org/data-access/graphql-api",
            "https://platform-docs.opentargets.org/data-access/datasets",
        ),
    ),
    artifact_hashes={
        "open-targets-derived-ledger": "069f3db029b7ba3e6b21e682ae4b1c9448a227b3224853075e9b77b03704176e",
    },
    scenario_locators={
        "open-targets-graphql-26-06": "https://platform.opentargets.org/target/ENSG00000141510/associations/MONDO_0018875",
    },
    claim_fields=(
        "target_id",
        "disease_id",
        "evidence_source",
        "release",
        "claim_id",
        "score",
        "score_threshold",
        "assertion_type",
        "confidence_language",
        "world_id",
        "world_version",
    ),
    capabilities=("check_structured_claim",),
    adapter="open_targets",
    parser_schema={
        "type": "object",
        "additionalProperties": False,
        "required": ["target_id", "disease_id", "evidence_source", "release"],
        "properties": {
            "target_id": {"type": "string"},
            "disease_id": {"type": "string"},
            "evidence_source": {"type": "string"},
            "release": {"type": "string", "const": "26.06"},
            "claim_id": {"type": "string"},
            "score": {"type": "number"},
            "score_threshold": {"type": "number"},
            "assertion_type": {"type": "string"},
            "confidence_language": {"type": "string"},
            "world_id": {"const": "open-targets"},
            "world_version": {"const": "26.06"},
        },
    },
)


CLINICAL_TRIALS_WORLD = World(
    world_id="clinical-trials-sec",
    version="2025-09-01_2026-09-01",
    modality="translational_disclosure",
    description="Timestamped ClinicalTrials.gov and SEC disclosure identity consistency.",
    source_allowlist=(
        "clinicaltrials-gov-api-v2",
        "sec-edgar-submissions-and-archives",
    ),
    source_contracts=(
        SourceContract(
            "clinicaltrials-gov-api-v2",
            "1c04f811b0300bbba0b56caaade1dfb5c78808169c152924024594124493345e",
            "ClinicalTrials.gov-terms-2023-01-31",
            "https://clinicaltrials.gov/data-api/api",
            "https://clinicaltrials.gov/about-site/terms-conditions",
        ),
        SourceContract(
            "sec-edgar-submissions-and-archives",
            "873c321bc7a918f4e7ad2cee5cde2de814376a864f1fece3e0c483cc8911a80e",
            "SEC-EDGAR-public-access",
            "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
            "https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data",
        ),
    ),
    artifact_hashes={
        "clinical-trials-sec-derived-ledger": "fcd3a320b3488513b1f609ca279dab600aa49cc7a436165d8fef45f51b473c6c",
        "clinical-trials-sec-review": "0d389e7d00a70e104056ddc831e7f2ce086257ae8cc1e4f6648c330c438b74d2",
    },
    scenario_locators={
        "clinicaltrials-gov-api-v2": "https://clinicaltrials.gov/study/NCT06260774",
        "sec-edgar-submissions-and-archives": "https://www.sec.gov/Archives/edgar/data/1829635/000110465926069810/tm2616719d1_ex99-1.htm",
    },
    claim_fields=(
        "nct_id",
        "sponsor",
        "intervention",
        "sec_accession",
        "cik",
        "exhibit_locator",
        "asserted_span_sha256",
        "as_of",
        "claim_id",
        "world_id",
        "world_version",
    ),
    capabilities=("check_structured_claim",),
    adapter="clinical_trials",
    parser_schema={
        "type": "object",
        "additionalProperties": False,
        "required": [
            "nct_id",
            "sponsor",
            "intervention",
            "sec_accession",
            "exhibit_locator",
            "asserted_span_sha256",
            "as_of",
        ],
        "properties": {
            "nct_id": {"type": "string"},
            "sponsor": {"type": "string"},
            "intervention": {"type": "string"},
            "sec_accession": {"type": "string"},
            "cik": {"type": "string"},
            "exhibit_locator": {"type": "string"},
            "asserted_span_sha256": {"type": "string"},
            "as_of": {"type": "string"},
            "claim_id": {"type": "string"},
            "world_id": {"const": "clinical-trials-sec"},
            "world_version": {"const": "2025-09-01_2026-09-01"},
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
                raise WorldRegistryError(
                    f"duplicate world registration: {world.world_key}"
                )
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
            raise WorldRegistryError(
                "world_version is required for explicit world binding"
            )
        try:
            return self._by_key[(world_id, world_version)]
        except KeyError as exc:
            raise WorldRegistryError(
                f"unknown world or version: {world_id}/{world_version}"
            ) from exc


WORLD_REGISTRY = WorldRegistry(
    (K562_WORLD, ARC_VCC_WORLD, OPEN_TARGETS_WORLD, CLINICAL_TRIALS_WORLD)
)


def get_world(
    world_id: str,
    world_version: str | None = None,
    *,
    registry: WorldRegistry = WORLD_REGISTRY,
) -> World:
    return registry.resolve(world_id, world_version)


def list_worlds(*, registry: WorldRegistry = WORLD_REGISTRY) -> tuple[World, ...]:
    return registry.worlds


def receipt_world_digest(world: World, source_hashes: Mapping[str, str]) -> str:
    """Bind a receipt to both the registered contract and exact source bytes."""
    actual = dict(source_hashes)
    expected = {
        contract.source: contract.sha256
        for contract in world.source_contracts
        if contract.sha256 is not None
    }
    if actual != expected or set(actual) != set(world.source_allowlist):
        raise WorldRegistryError(
            f"source hashes do not exactly match registered world {world.world_key}"
        )
    payload = {
        "registered_world_digest": world.digest,
        "sources": dict(sorted(actual.items())),
    }
    return hashlib.sha256(canonicalize_for_hash(payload)).hexdigest()


def validate_world_artifacts(world: World, artifact_hashes: Mapping[str, str]) -> None:
    """Require loaded derived artifacts to equal the immutable world contract."""
    actual = dict(artifact_hashes)
    expected = dict(world.artifact_hashes)
    if actual != expected:
        raise WorldRegistryError(
            f"artifact hashes do not exactly match registered world {world.world_key}"
        )
