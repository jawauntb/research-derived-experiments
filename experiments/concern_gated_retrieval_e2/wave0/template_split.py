"""Template calibration/confirmatory split guard for COGR-E2 Wave 0.

This module is the calibration/confirmatory family-split guard named in the
Wave 0 preregistration (``PREREGISTRATION.md`` §2, §4, and §10) and in the
Wave 0 promotion contract (``PROMOTION_CONTRACT.md`` gates G0_ANTI_LEAKAGE
and G4_SEED_INDEPENDENCE).

Design invariants (do not weaken without a Wave 0 redesign):

1. **Two disjoint families.** :class:`TemplateBucket` has exactly two members:
   ``CALIBRATION`` and ``CONFIRMATION``. There is no third bucket. A template
   id may be registered in exactly one bucket.
2. **Default-deny confirmatory.** :meth:`TemplateRegistry.load` returns only
   ``CALIBRATION`` rows unless the caller passes ``allow_confirmation=True``
   **and** the caller-side confirmatory-run env token
   (``COGR_WAVE0_CONFIRMATORY_RUN``) is truthy. Both must be true; either one
   alone is a :class:`LeakageError`.
3. **Immutable bucket tag on every row.** Rows returned by ``load()`` and
   ``register()`` are frozen dataclasses whose ``bucket`` field is set at
   construction. The tag survives :func:`dataclasses.replace` unchanged when
   callers omit it, so a caller who forgets to re-tag a row cannot silently
   reclassify it. Callers who explicitly pass a wrong bucket are caught by
   the runtime tripwire :func:`assert_calibration_only`.
4. **Runtime tripwire.** :func:`assert_calibration_only` raises
   :class:`LeakageError` when passed a ``CONFIRMATION`` row (or any object
   whose ``bucket`` attribute is not a valid :class:`TemplateBucket`). It is
   the canonical entry-point check for any calibration-only analysis path.
5. **Deterministic template ids.** :func:`_stable_template_id` derives a
   process-stable id from ``(bucket, family, seed)`` using SHA-256, so a
   calibration id computed in one process matches the id computed in
   another process from the same ``(family, seed)`` under the same bucket.

Wave 0 style boundary: this module does not describe learned memory,
concern recovery, meaning, or selfhood. It only enforces the family split.
"""

from __future__ import annotations

import enum
import hashlib
import os
from dataclasses import dataclass
from typing import Iterator

__all__ = [
    "CONFIRMATORY_RUN_ENV_VAR",
    "LeakageError",
    "TemplateBucket",
    "TemplateRow",
    "TemplateRegistry",
    "assert_calibration_only",
    "stable_template_id",
]


#: Environment variable that must be truthy for :meth:`TemplateRegistry.load`
#: to surface confirmatory rows. The variable name is stable and part of the
#: Wave 0 anti-leakage contract; do not rename it without a Wave 0 redesign.
CONFIRMATORY_RUN_ENV_VAR = "COGR_WAVE0_CONFIRMATORY_RUN"


class LeakageError(RuntimeError):
    """Raised when the calibration/confirmatory boundary is crossed.

    This is a hard integrity error: it is not silently caught anywhere in
    Wave 0 code, and its message intentionally omits the confirmatory
    template id or evaluator-only fields (see ``PREREGISTRATION.md`` §4.3(5)).
    """


class TemplateBucket(enum.Enum):
    """Disjoint template families for Wave 0.

    - :attr:`CALIBRATION` — the only family Wave 0 policy code may see. Its
      seeds live in the calibration seed range 100000..100999
      (``PREREGISTRATION.md`` §10).
    - :attr:`CONFIRMATION` — reserved for Wave 1 confirmatory rows. Its
      seeds live in 200000..201999. Wave 0 code may register these ids to
      keep the registry authoritative, but must not read them unless the
      caller has both flipped ``allow_confirmation=True`` and set the
      confirmatory-run env token.
    """

    CALIBRATION = "calibration"
    CONFIRMATION = "confirmatory"


def stable_template_id(family: str, seed: int, bucket: TemplateBucket) -> str:
    """Return a deterministic template id for ``(family, seed, bucket)``.

    Determinism guarantee: given the same ``(family, seed, bucket)`` triple,
    every process on every host returns the same string. This is used by the
    calibration receipt to check that seed 100042 in ``delayed_commitments``
    is the *same* template row across processes.

    The id shape is ``"{family}-{P}-{digest16}"`` where ``P`` is ``C`` for
    calibration rows and ``X`` for confirmatory rows, and ``digest16`` is
    the first 16 hex chars of ``sha256("{bucket}:{family}:{seed}")``.
    """
    if not isinstance(bucket, TemplateBucket):
        raise TypeError(
            f"bucket must be a TemplateBucket, got {type(bucket).__name__}"
        )
    if not isinstance(family, str) or not family:
        raise ValueError("family must be a non-empty string")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be a non-boolean int")
    key = f"{bucket.value}:{family}:{seed}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()[:16]
    prefix = "C" if bucket is TemplateBucket.CALIBRATION else "X"
    return f"{family}-{prefix}-{digest}"


# Internal alias for the module-private call sites below.
_stable_template_id = stable_template_id


def _confirmatory_run_token_present() -> bool:
    """Return True iff the caller-side confirmatory-run env token is truthy.

    The token is read from :data:`CONFIRMATORY_RUN_ENV_VAR`. Truthy values
    are ``"1"``, ``"true"``, ``"yes"``, and ``"on"`` (case-insensitive).
    Every other value, including the empty string, is falsy.
    """
    raw = os.environ.get(CONFIRMATORY_RUN_ENV_VAR, "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class TemplateRow:
    """A minimal, policy-visible template row with an immutable bucket tag.

    Wave 0 dataclasses that carry a template must inherit this shape:
    ``template_id``, ``family``, ``seed``, and ``bucket``. The ``bucket``
    field is a normal frozen-dataclass field, so :func:`dataclasses.replace`
    preserves it whenever the caller omits it. Callers who explicitly pass a
    wrong bucket are caught by :func:`assert_calibration_only` at the
    calibration entry points.

    The class is intentionally minimal. Wave 1 will add evaluator-only
    fields on a *separate*, evaluator-only dataclass; those fields never
    live on :class:`TemplateRow`.
    """

    template_id: str
    family: str
    seed: int
    bucket: TemplateBucket

    def __post_init__(self) -> None:
        if not isinstance(self.bucket, TemplateBucket):
            raise TypeError(
                "TemplateRow.bucket must be a TemplateBucket instance"
            )
        if not isinstance(self.template_id, str) or not self.template_id:
            raise ValueError("template_id must be a non-empty string")
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("family must be a non-empty string")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be a non-boolean int")


class TemplateRegistry:
    """Registry of ``template_id -> TemplateBucket`` with a gated ``load()``.

    Wave 0 calibration code constructs a single :class:`TemplateRegistry`,
    populates it with the calibration templates it plans to run, and
    optionally registers the confirmatory template ids that Wave 1 will
    use. Confirmatory rows are held here only so the registry can report
    that they exist and reject double-registrations; Wave 0 policy code
    never reaches them because :meth:`load` denies them by default.
    """

    def __init__(self) -> None:
        self._rows: dict[str, TemplateRow] = {}

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #

    def register(
        self,
        *,
        family: str,
        seed: int,
        bucket: TemplateBucket,
    ) -> TemplateRow:
        """Register (or re-fetch) a template row for ``(family, seed, bucket)``.

        Raises :class:`LeakageError` if the same ``template_id`` was already
        registered under a *different* bucket — that would mean the
        calibration and confirmatory families collided on a deterministic
        id, which is an integrity failure.
        """
        template_id = _stable_template_id(family, seed, bucket)
        existing = self._rows.get(template_id)
        if existing is not None:
            if existing.bucket is not bucket:
                raise LeakageError(
                    f"template_id {template_id!r} already registered under "
                    f"{existing.bucket.value!r}; refusing to reclassify to "
                    f"{bucket.value!r}"
                )
            return existing
        row = TemplateRow(
            template_id=template_id,
            family=family,
            seed=seed,
            bucket=bucket,
        )
        self._rows[template_id] = row
        return row

    # ------------------------------------------------------------------ #
    # Lookups
    # ------------------------------------------------------------------ #

    def bucket_of(self, template_id: str) -> TemplateBucket:
        """Return the bucket registered for ``template_id``.

        Raises :class:`KeyError` if the id is not registered. This is a
        lookup helper for the calibration receipt; it does not surface
        confirmatory rows to the policy — that is what :meth:`load` is for.
        """
        return self._rows[template_id].bucket

    def __contains__(self, template_id: object) -> bool:
        return isinstance(template_id, str) and template_id in self._rows

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self) -> Iterator[str]:
        return iter(self._rows)

    # ------------------------------------------------------------------ #
    # Gated surface
    # ------------------------------------------------------------------ #

    def load(
        self,
        *,
        allow_confirmation: bool = False,
    ) -> tuple[TemplateRow, ...]:
        """Return the rows visible to the caller.

        The default surface (``allow_confirmation=False``) is exactly the
        set of :attr:`TemplateBucket.CALIBRATION` rows. This is the only
        surface Wave 0 calibration code should ever call.

        When ``allow_confirmation=True``, the confirmatory-run env token
        (:data:`CONFIRMATORY_RUN_ENV_VAR`) must also be truthy; otherwise
        :class:`LeakageError` is raised. Both conditions must hold —
        neither the env token alone nor the flag alone unlocks confirmatory
        rows. When both hold, the returned tuple contains every registered
        row in insertion order (calibration + confirmation).
        """
        if allow_confirmation:
            if not _confirmatory_run_token_present():
                raise LeakageError(
                    "load(allow_confirmation=True) requires the caller-side "
                    f"env var {CONFIRMATORY_RUN_ENV_VAR!r} to be truthy; "
                    "refusing to surface confirmatory rows"
                )
            return tuple(self._rows.values())
        return tuple(
            row for row in self._rows.values()
            if row.bucket is TemplateBucket.CALIBRATION
        )


def assert_calibration_only(row: object) -> None:
    """Runtime tripwire for calibration-only analysis entry points.

    Raises :class:`LeakageError` unless ``row`` has a ``bucket`` attribute
    equal to :attr:`TemplateBucket.CALIBRATION`. This is the canonical
    guard Wave 0 calibration functions call on every incoming row.

    The guard accepts any object with a ``bucket`` attribute, not only
    :class:`TemplateRow`, so downstream Wave 0 dataclasses that embed a
    ``bucket`` field (again via :func:`dataclasses.replace` or via
    inheritance) are also protected.
    """
    bucket = getattr(row, "bucket", None)
    if not isinstance(bucket, TemplateBucket):
        raise LeakageError(
            "row has no valid TemplateBucket tag; refusing to admit it into "
            "calibration-only analysis"
        )
    if bucket is not TemplateBucket.CALIBRATION:
        raise LeakageError(
            "calibration-only analysis received a row from bucket "
            f"{bucket.value!r}; refusing to run"
        )
