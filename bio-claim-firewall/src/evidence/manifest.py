"""Frozen-source manifest: provenance + integrity metadata for one snapshot source."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]

    _HAVE_YAML = True
except ImportError:  # pyyaml is optional -- see load_manifest docstring.
    yaml = None  # type: ignore[assignment]
    _HAVE_YAML = False

# EVIDENCE-DECISION: `preprocessing_cmd` is the only optional field (the
# brief marks it `str | None`); every other field is required.
_REQUIRED_FIELDS = (
    "source",
    "source_url",
    "retrieved_at",
    "license",
    "sha256",
    "row_count",
    "schema_version",
)
_REQUIRED_STRING_FIELDS = (
    "source",
    "source_url",
    "retrieved_at",
    "license",
    "sha256",
    "schema_version",
)


@dataclass(frozen=True, slots=True)
class Manifest:
    """Provenance + integrity record for one frozen source under ``data_root/manifests/``."""

    source: str
    source_url: str
    retrieved_at: str
    license: str
    sha256: str
    row_count: int
    preprocessing_cmd: str | None
    schema_version: str


def _parse_manifest_text(text: str, suffix: str, path: Path) -> Any:
    if suffix == ".json":
        return json.loads(text)
    if suffix in (".yaml", ".yml"):
        if not _HAVE_YAML:
            # EVIDENCE-DECISION: pyyaml is optional per the brief ("do not
            # require yaml"). A .yaml manifest with no pyyaml importable is
            # a manifest-authoring/deployment problem, not a tamper signal,
            # so it is a plain ValueError -- not an EvidenceError, and not
            # one of the closed fault-taxonomy codes.
            raise ValueError(
                f"manifest {path} is YAML but pyyaml is not importable in this "
                "environment; install pyyaml or provide a JSON manifest instead"
            )
        return yaml.safe_load(text)
    raise ValueError(f"manifest {path} has unsupported extension {suffix!r}; expected .yaml, .yml, or .json")


def load_manifest(path: Path) -> Manifest:
    """Load and structurally validate one manifest file. Accepts YAML or JSON.

    # EVIDENCE-DECISION: structural problems here (missing/mistyped field,
    # unparseable file, wrong extension) raise plain ``ValueError``, not
    # ``EvidenceError``. Malformed-manifest is a manifest-authoring fault
    # with no corresponding entry in spec/fault_taxonomy.md's closed enum;
    # ``EvidenceError`` is reserved for the two signals this module is
    # chartered to raise: ``BAD_CITATION`` (ledger.py) and ``HASH_MISMATCH``
    # (loader.py's file-vs-manifest integrity check). This function does not
    # touch the filesystem beyond reading `path` itself -- it never checks
    # `sha256` against any referenced data file; that is loader.py's job.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    data = _parse_manifest_text(text, path.suffix.lower(), path)

    if not isinstance(data, dict):
        raise ValueError(f"manifest {path} did not parse to an object (got {type(data).__name__})")

    missing = [field for field in _REQUIRED_FIELDS if field not in data]
    if missing:
        raise ValueError(f"manifest {path} missing required field(s): {missing}")

    for field in _REQUIRED_STRING_FIELDS:
        if not isinstance(data[field], str):
            raise ValueError(f"manifest {path} field {field!r} must be a string")

    preprocessing_cmd = data.get("preprocessing_cmd")
    if preprocessing_cmd is not None and not isinstance(preprocessing_cmd, str):
        raise ValueError(f"manifest {path} field 'preprocessing_cmd' must be a string or null")

    row_count_raw = data["row_count"]
    if isinstance(row_count_raw, bool) or not isinstance(row_count_raw, int):
        raise ValueError(f"manifest {path} field 'row_count' must be an integer")

    return Manifest(
        source=data["source"],
        source_url=data["source_url"],
        retrieved_at=data["retrieved_at"],
        license=data["license"],
        sha256=data["sha256"],
        row_count=row_count_raw,
        preprocessing_cmd=preprocessing_cmd,
        schema_version=data["schema_version"],
    )
