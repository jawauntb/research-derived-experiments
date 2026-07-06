"""Shared dependency-light Suite C contract constants."""

from __future__ import annotations

from dataclasses import dataclass


CONDITIONS = (
    "p22_learned_current_replay",
    "two_timescale_plus_prediction_error",
    "fixed_surprise_decrement",
    "scheduled_null_anchor",
    "oracle_source",
    "decision_refractory",
    "burst_then_refractory",
    "learned_cooldown_head",
    "matched_random_time_budget",
)

CANDIDATE_CONDITIONS = (
    "decision_refractory",
    "burst_then_refractory",
    "learned_cooldown_head",
)

CONTROL_CONDITIONS = tuple(c for c in CONDITIONS if c not in CANDIDATE_CONDITIONS)

BUCKETS = (
    "food_low",
    "food_high",
    "medicine_low",
    "medicine_high",
    "poison_low",
    "neutral_low",
)
AFFECTED_BUCKETS = ("food_low", "medicine_low")
UNAFFECTED_BUCKETS = tuple(b for b in BUCKETS if b not in AFFECTED_BUCKETS)


@dataclass(frozen=True)
class SuiteCConfig:
    steps: int = 72
    first_shift: int = 24
    second_shift: int = 48
    pre_first_start: int = 12
    post_first_end: int = 36
    late_first_start: int = 40
    pre_second_start: int = 42
    post_second_end: int = 60
    final_start: int = 64
    recovery_threshold: float = 0.12
    reengagement_floor: float = 0.50
    selectivity_floor: float = 2.0
    reopen_floor: float = 1.0


DEFAULT_CONFIG = SuiteCConfig()
