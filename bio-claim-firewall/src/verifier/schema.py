"""JSON-Schema validation of an untrusted Claim dict against claim.schema.json.

`validate_claim` returns a single structured `SchemaFailure` (field_path +
constraint_kind) for the *first* violation found, or `None` if the instance
is schema-valid -- that's all `mapping.py` needs to decide REJECTED vs.
CHECKER_ERROR. It never raises on a malformed/non-dict `instance`; every
check is written to degrade to a `SchemaFailure` (or simply "does not
apply") rather than crash, since this is the very first thing `verify()`
runs on fully untrusted input.

# VERIFIER-DECISION: uses the real `jsonschema` package (Draft 2020-12)
# when importable, else a minimal hand-rolled validator covering exactly
# the keywords `claim.schema.json` actually uses: `type` (incl. union
# types), `const`, `enum`, `pattern`, `minLength`, `format` ("uuid"),
# `required`, `additionalProperties`, `properties`, `items`, `minItems`,
# `uniqueItems`, and a single-level `$ref` into `#/$defs/...` (the only
# `$ref` shape `claim.schema.json` contains, via `EntityRef`). This
# mirrors the same fallback pattern already used by
# `tests/fixtures/test_fixtures_self_consistent.py`. In this repository's
# actual `uv run --no-sync` environment `jsonschema` is NOT importable
# (confirmed), so the minimal validator is the path every test in this
# package actually exercises; the `jsonschema`-backed branch is kept
# correct-by-construction for an environment where the dependency is
# added later, but is not itself covered by this task's test suite.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    import jsonschema  # type: ignore[import-not-found]

    _HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover - environment-dependent
    _HAVE_JSONSCHEMA = False


@dataclass(frozen=True, slots=True)
class SchemaFailure:
    """One JSON-Schema constraint violation.

    Attributes:
        field_path: dotted path to the offending field (e.g. `"subject.id"`,
            `"relation"`, `"evidence_ids"`). Empty string means the
            violation is at the document root itself (e.g. the whole
            instance isn't even an object).
        constraint_kind: which JSON-Schema keyword failed -- one of
            `"enum"`, `"pattern"`, `"required"`, `"additional"`, `"type"`,
            or a small set of others (`"const"`, `"minLength"`, `"format"`,
            `"minItems"`, `"uniqueItems"`) for constraints `mapping.py`
            doesn't specifically route but that still need to surface as
            *some* structured failure rather than crash.
        message: human-readable detail, for verdict `reasons`/`checker_error`.
    """

    field_path: str
    constraint_kind: str
    message: str


@lru_cache(maxsize=8)
def load_claim_schema(schema_dir: Path) -> dict[str, Any]:
    """Load and cache `claim.schema.json` from `schema_dir`.

    Cached by `schema_dir` (a `Path`, hashable) since `VerifierConfig` is
    frozen and callers typically build one config and call `verify()` many
    times against it -- no reason to re-read+re-parse the same file off
    disk on every claim.
    """
    path = Path(schema_dir) / "claim.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Minimal fallback validator
# ---------------------------------------------------------------------------

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

_PY_TYPES: dict[str, type] = {
    "object": dict,
    "array": list,
    "string": str,
    "null": type(None),
}


def _instance_matches_type(instance: Any, type_name: str) -> bool:
    if type_name == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if type_name == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if type_name == "boolean":
        return isinstance(instance, bool)
    py_t = _PY_TYPES.get(type_name)
    if py_t is None:
        return False
    return isinstance(instance, py_t)


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _deref(schema: Any, root: dict[str, Any]) -> Any:
    """Resolve a single-level `{"$ref": "#/a/b/c"}` against `root`.

    `claim.schema.json` only ever uses local `#/$defs/...` refs (for
    `EntityRef`), and `EntityRef` itself contains no further `$ref`, so one
    resolution pass is sufficient. Any other/unsupported ref shape is
    returned unresolved rather than raising -- callers see an empty
    effective schema for that node (no constraints checked), never a crash.
    """
    if not isinstance(schema, dict) or "$ref" not in schema:
        return schema
    ref = schema["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return {}
    node: Any = root
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            return {}
        node = node[part]
    return node


def _minimal_validate(instance: Any, schema: Any, root: dict[str, Any], path: str) -> SchemaFailure | None:
    schema = _deref(schema, root)
    if not isinstance(schema, dict):
        return None

    if "const" in schema and instance != schema["const"]:
        return SchemaFailure(path, "const", f"expected const {schema['const']!r}, got {instance!r}")

    if "enum" in schema and instance not in schema["enum"]:
        return SchemaFailure(path, "enum", f"{instance!r} is not one of {schema['enum']!r}")

    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_instance_matches_type(instance, t) for t in types):
            return SchemaFailure(path, "type", f"{instance!r} does not match type(s) {types!r}")

    if "pattern" in schema and isinstance(instance, str):
        if not re.search(schema["pattern"], instance):
            return SchemaFailure(path, "pattern", f"{instance!r} does not match pattern {schema['pattern']!r}")

    if "minLength" in schema and isinstance(instance, str):
        if len(instance) < schema["minLength"]:
            return SchemaFailure(path, "minLength", f"{instance!r} is shorter than minLength {schema['minLength']}")

    if "format" in schema and isinstance(instance, str):
        fmt = schema["format"]
        if fmt == "uuid" and not _UUID_RE.match(instance):
            return SchemaFailure(path, "format", f"{instance!r} is not a uuid")
        if fmt == "date-time" and not _DATETIME_RE.match(instance):
            return SchemaFailure(path, "format", f"{instance!r} is not a date-time")

    if isinstance(instance, dict) and ("properties" in schema or schema.get("type") == "object"):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in instance:
                return SchemaFailure(_join(path, req), "required", f"missing required property {req!r}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(instance.keys()) - set(props.keys()))
            if extra:
                return SchemaFailure(_join(path, extra[0]), "additional", f"additional property {extra[0]!r} is not allowed")
        for key in sorted(instance.keys()):
            if key in props:
                failure = _minimal_validate(instance[key], props[key], root, _join(path, key))
                if failure is not None:
                    return failure

    if isinstance(instance, list) and schema.get("type") == "array":
        if "minItems" in schema and len(instance) < schema["minItems"]:
            return SchemaFailure(path, "minItems", f"array has fewer than minItems={schema['minItems']} items")
        if schema.get("uniqueItems"):
            seen = [json.dumps(x, sort_keys=True, default=str) for x in instance]
            if len(seen) != len(set(seen)):
                return SchemaFailure(path, "uniqueItems", "array items are not unique")
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(instance):
                failure = _minimal_validate(item, items_schema, root, f"{path}[{i}]")
                if failure is not None:
                    return failure

    return None


# ---------------------------------------------------------------------------
# jsonschema-backed validator (used only when the package is importable)
# ---------------------------------------------------------------------------


def _convert_jsonschema_error(error: Any) -> SchemaFailure:
    kind = error.validator
    path_parts = [str(p) for p in error.absolute_path]
    if kind == "required":
        match = re.search(r"'(.+?)' is a required property", str(error.message))
        path_parts = path_parts + [match.group(1) if match else "?"]
    elif kind == "additionalProperties":
        match = re.search(r"\('(.+?)' was unexpected\)", str(error.message))
        if match is None:
            all_quoted = re.findall(r"'(.+?)'", str(error.message))
            match_str = all_quoted[0] if all_quoted else "?"
        else:
            match_str = match.group(1)
        path_parts = path_parts + [match_str]
        kind = "additional"
    field_path = ".".join(path_parts)
    return SchemaFailure(field_path=field_path, constraint_kind=kind, message=str(error.message))


def _jsonschema_validate(instance: Any, schema: dict[str, Any]) -> SchemaFailure | None:
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: [str(p) for p in e.absolute_path])
    if not errors:
        return None
    return _convert_jsonschema_error(errors[0])


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def validate_claim(instance: Any, schema: dict[str, Any]) -> SchemaFailure | None:
    """Validate `instance` against `schema` (claim.schema.json).

    Returns the first `SchemaFailure` found, or `None` if `instance` is
    schema-valid. Never raises on malformed `instance` (any type, deeply
    nested, non-dict, etc.) -- see module docstring.
    """
    if _HAVE_JSONSCHEMA:
        return _jsonschema_validate(instance, schema)
    return _minimal_validate(instance, schema, schema, "")
