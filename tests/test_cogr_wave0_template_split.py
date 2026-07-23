"""Tests for the Wave 0 template calibration/confirmatory split guard.

These four tests exercise the invariants named in the Wave 0 preregistration
(``PREREGISTRATION.md`` §4.3) and the promotion contract's G0_ANTI_LEAKAGE
and G4_SEED_INDEPENDENCE gates.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    CONFIRMATORY_RUN_ENV_VAR,
    LeakageError,
    TemplateBucket,
    TemplateRegistry,
    TemplateRow,
    assert_calibration_only,
    stable_template_id,
)


# --------------------------------------------------------------------------- #
# Fixture: a registry populated with three calibration rows (one per family)
# and two confirmatory rows. The confirmatory rows are only visible when both
# the flag and the env token are set.
# --------------------------------------------------------------------------- #


def _build_registry() -> TemplateRegistry:
    reg = TemplateRegistry()
    for family, seed in (
        ("delayed_commitments", 100000),
        ("maintenance_fault", 100001),
        ("resource_constrained", 100002),
    ):
        reg.register(family=family, seed=seed, bucket=TemplateBucket.CALIBRATION)
    for family, seed in (
        ("delayed_commitments", 200000),
        ("maintenance_fault", 200001),
    ):
        reg.register(family=family, seed=seed, bucket=TemplateBucket.CONFIRMATION)
    return reg


# --------------------------------------------------------------------------- #
# Test 1: calibration is the default surface
# --------------------------------------------------------------------------- #


def test_load_default_returns_calibration_only(monkeypatch: pytest.MonkeyPatch) -> None:
    # Even when the env token is set, the default surface still hides
    # confirmatory rows because the caller did not pass allow_confirmation.
    monkeypatch.setenv(CONFIRMATORY_RUN_ENV_VAR, "1")

    reg = _build_registry()
    rows = reg.load()

    assert len(rows) == 3, "default load must surface only the 3 calibration rows"
    assert all(isinstance(r, TemplateRow) for r in rows)
    assert {r.bucket for r in rows} == {TemplateBucket.CALIBRATION}
    assert {r.family for r in rows} == {
        "delayed_commitments",
        "maintenance_fault",
        "resource_constrained",
    }
    # And every returned row is admissible to calibration-only analysis.
    for row in rows:
        assert_calibration_only(row)


# --------------------------------------------------------------------------- #
# Test 2: confirmation surface is gated by the env token
# --------------------------------------------------------------------------- #


def test_load_confirmation_requires_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    reg = _build_registry()

    # Without the env token, allow_confirmation=True must raise.
    monkeypatch.delenv(CONFIRMATORY_RUN_ENV_VAR, raising=False)
    with pytest.raises(LeakageError):
        reg.load(allow_confirmation=True)

    # A falsy value ("0", "false", "") is also refused.
    for falsy in ("0", "false", "no", "off", ""):
        monkeypatch.setenv(CONFIRMATORY_RUN_ENV_VAR, falsy)
        with pytest.raises(LeakageError):
            reg.load(allow_confirmation=True)

    # With a truthy env token AND the flag, both families are visible.
    monkeypatch.setenv(CONFIRMATORY_RUN_ENV_VAR, "1")
    rows = reg.load(allow_confirmation=True)
    buckets = {r.bucket for r in rows}
    assert buckets == {TemplateBucket.CALIBRATION, TemplateBucket.CONFIRMATION}
    assert len(rows) == 5

    # The env token alone (without the flag) still hides confirmatory rows.
    default_rows = reg.load()
    assert {r.bucket for r in default_rows} == {TemplateBucket.CALIBRATION}


# --------------------------------------------------------------------------- #
# Test 3: the tripwire raises LeakageError on misuse
# --------------------------------------------------------------------------- #


def test_assert_calibration_only_raises_on_misuse() -> None:
    reg = TemplateRegistry()
    confirmation_row = reg.register(
        family="maintenance_fault",
        seed=200042,
        bucket=TemplateBucket.CONFIRMATION,
    )
    calibration_row = reg.register(
        family="maintenance_fault",
        seed=100042,
        bucket=TemplateBucket.CALIBRATION,
    )

    # Confirmation row must be refused.
    with pytest.raises(LeakageError):
        assert_calibration_only(confirmation_row)

    # An object without a bucket attribute must also be refused (defense in
    # depth: no silent pass-through of a plain dict or a stripped row).
    with pytest.raises(LeakageError):
        assert_calibration_only(object())
    with pytest.raises(LeakageError):
        assert_calibration_only({"template_id": "x", "bucket": "calibration"})

    # Idempotency: re-registering the same (family, seed, bucket) returns
    # the identical row, not a copy — the registry is a single source of
    # truth for template_id -> bucket.
    same_row = reg.register(
        family="maintenance_fault",
        seed=100042,
        bucket=TemplateBucket.CALIBRATION,
    )
    assert same_row is calibration_row

    # Calibration row is admitted with no raise.
    assert_calibration_only(calibration_row)


# --------------------------------------------------------------------------- #
# Test 4: bucket tag survives dataclass.replace() and is process-stable
# --------------------------------------------------------------------------- #


def test_bucket_tag_survives_dataclass_replace() -> None:
    reg = TemplateRegistry()
    row = reg.register(
        family="resource_constrained",
        seed=100777,
        bucket=TemplateBucket.CALIBRATION,
    )

    # Replacing an unrelated field must preserve the CALIBRATION tag.
    replaced = replace(row, seed=100778)
    assert replaced.bucket is TemplateBucket.CALIBRATION
    assert replaced.family == "resource_constrained"
    assert_calibration_only(replaced)  # tripwire must accept the replacement

    # A caller who explicitly rewrites the bucket to CONFIRMATION does NOT
    # escape the tripwire — the runtime guard still fires. (The tag is
    # "immutable" in the sense that its meaning cannot be laundered past
    # the guard, not that the field is unassignable at replace() time.)
    forged = replace(row, bucket=TemplateBucket.CONFIRMATION)
    with pytest.raises(LeakageError):
        assert_calibration_only(forged)

    # Determinism guarantee: the template id is stable across independent
    # registries (i.e., across processes) given the same (family, seed,
    # bucket). This is what the Wave 0 calibration receipt relies on when
    # it declares that "seed 100777 in resource_constrained" is the same
    # row on every host.
    reg2 = TemplateRegistry()
    row2 = reg2.register(
        family="resource_constrained",
        seed=100777,
        bucket=TemplateBucket.CALIBRATION,
    )
    assert row2.template_id == row.template_id
    assert row2.template_id == stable_template_id(
        "resource_constrained",
        100777,
        TemplateBucket.CALIBRATION,
    )
    # And the calibration-family id must never collide with its
    # confirmatory counterpart at the same seed.
    conf_id = stable_template_id(
        "resource_constrained",
        100777,
        TemplateBucket.CONFIRMATION,
    )
    assert conf_id != row.template_id
