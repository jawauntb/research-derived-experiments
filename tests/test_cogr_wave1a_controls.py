"""Wave 1a fixed-prior control-runner regression tests.

Four tests, one per control, each exercising the two contracts
``wave1a/controls.py`` owns:

1. Byte-stable determinism: a repeat call to the runner with the same
   ``(family, seeds)`` yields a :class:`ControlTrace` equal on every
   field to the first call.  Determinism is a Wave 1a scaffolding
   contract, not an experiment outcome; it belongs on the audited
   surface.
2. Structural well-formedness: the trace's ``condition_name`` matches
   the runner, its ``results`` are aligned with the input seeds, and
   the sealed environment's single-shot invariant surfaces on
   :attr:`ControlTrace.sealed_env_evaluate_calls`.

The oracle-ceiling test additionally verifies that
:func:`promotion_admit_condition` refuses the oracle with
:class:`PromotionRefused` — the ceiling receipt is diagnostic only and
must never enter the Wave 1a screen or a Wave 1b promotion contest
(``wave1a/PREREGISTRATION.md`` §4 "Oracle is diagnostic").

No experiment logic is exercised.  Scaffolding scope.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave1a.conditions import (
    CONDITIONS,
    FROZEN_WRONG,
    ORACLE_CEILING,
    PromotionRefused,
    SHUFFLED,
    WRONG_AGENT,
    promotion_admit_condition,
)
from experiments.concern_gated_retrieval_e2.wave1a.controls import (
    ControlTrace,
    run_frozen_wrong,
    run_oracle_ceiling,
    run_shuffled,
    run_wrong_agent,
)
from experiments.concern_gated_retrieval_e2.wave1a.e2a_runner import (
    E2aEpisodeResult,
)


# Two confirmatory seeds — small enough to keep the test fast, large
# enough to catch a length mismatch between ``results`` and ``seeds``.
_SEEDS: tuple[int, ...] = (200_000, 200_001)
_FAMILY: str = "delayed_commitments"


def _assert_wellformed_trace(
    trace: ControlTrace,
    *,
    expected_condition_name: str,
    expected_promotable: bool,
) -> None:
    """Structural checks common to every control-runner trace."""

    assert isinstance(trace, ControlTrace)
    assert trace.condition_name == expected_condition_name
    assert trace.family == _FAMILY
    assert trace.seeds == _SEEDS
    assert len(trace.results) == len(_SEEDS)
    for result, seed in zip(trace.results, _SEEDS):
        assert isinstance(result, E2aEpisodeResult)
        assert result.condition_name == expected_condition_name
        assert result.rng_seed == seed
        assert result.family == _FAMILY
        assert result.template_family_split == "confirmatory"
        assert result.sealed_env_evaluate_calls == 1
    # Sealed-env single-shot invariant aggregated across the batch.
    assert trace.sealed_env_evaluate_calls == len(_SEEDS)
    assert trace.promotion_eligible is expected_promotable


def test_run_frozen_wrong_is_deterministic_and_wellformed():
    """C1 baseline runs twice → byte-identical trace; promotion-eligible."""
    first = run_frozen_wrong(_FAMILY, _SEEDS)
    second = run_frozen_wrong(_FAMILY, _SEEDS)

    _assert_wellformed_trace(
        first,
        expected_condition_name=FROZEN_WRONG,
        expected_promotable=True,
    )
    # Frozen conditions never fire the update rule; every result's
    # concern_after is None on the baseline.
    for result in first.results:
        assert result.concern_after is None
    # Deterministic replay: the two batches are equal on every field.
    assert first == second
    # And admissible to the promotion harness (round-trip).
    assert promotion_admit_condition(CONDITIONS[FROZEN_WRONG]) is CONDITIONS[FROZEN_WRONG]


def test_run_oracle_ceiling_deterministic_and_refused_by_promotion():
    """C3 ceiling runs twice → identical trace; promotion harness refuses.

    Two contracts on one condition:

    * The runner still executes the oracle for the diagnostic ceiling
      receipt (``PREREGISTRATION.md`` §4 "Oracle is diagnostic"), and
      the receipt is byte-stable across replays.
    * :func:`promotion_admit_condition` refuses the oracle with
      :class:`PromotionRefused`; the :class:`ControlTrace` mirrors this
      with ``promotion_eligible=False`` so a downstream promotion
      contest can gate on the flag before even calling into the
      harness.
    """
    first = run_oracle_ceiling(_FAMILY, _SEEDS)
    second = run_oracle_ceiling(_FAMILY, _SEEDS)

    _assert_wellformed_trace(
        first,
        expected_condition_name=ORACLE_CEILING,
        expected_promotable=False,
    )
    for result in first.results:
        # Oracle carries no update rule (frozen ceiling); concern_after is None.
        assert result.concern_after is None
    # Deterministic replay.
    assert first == second
    # Promotion harness refuses the oracle — the ceiling is diagnostic-only.
    with pytest.raises(PromotionRefused, match="oracle_ceiling"):
        promotion_admit_condition(CONDITIONS[ORACLE_CEILING])


def test_run_shuffled_is_deterministic_and_wellformed():
    """C4 shuffled-label control runs twice → byte-identical trace."""
    first = run_shuffled(_FAMILY, _SEEDS)
    second = run_shuffled(_FAMILY, _SEEDS)

    _assert_wellformed_trace(
        first,
        expected_condition_name=SHUFFLED,
        expected_promotable=True,
    )
    for result in first.results:
        assert result.concern_after is None
    assert first == second
    assert promotion_admit_condition(CONDITIONS[SHUFFLED]) is CONDITIONS[SHUFFLED]


def test_run_wrong_agent_is_deterministic_and_wellformed():
    """C5 wrong-agent control runs twice → byte-identical trace."""
    first = run_wrong_agent(_FAMILY, _SEEDS)
    second = run_wrong_agent(_FAMILY, _SEEDS)

    _assert_wellformed_trace(
        first,
        expected_condition_name=WRONG_AGENT,
        expected_promotable=True,
    )
    for result in first.results:
        assert result.concern_after is None
    assert first == second
    assert promotion_admit_condition(CONDITIONS[WRONG_AGENT]) is CONDITIONS[WRONG_AGENT]
