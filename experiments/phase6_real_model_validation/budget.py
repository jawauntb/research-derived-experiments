"""Budget helpers for the Phase 6 Modal L4 real-model suite."""

from __future__ import annotations

from typing import Any


def estimate_modal_cost(
    cells: int,
    budget_usd: float,
    *,
    gpu: str,
    timeout_seconds: int,
    max_containers: int,
    gpu_rate_per_second: float,
) -> dict[str, Any]:
    conservative = cells * timeout_seconds * gpu_rate_per_second
    return {
        "gpu": gpu,
        "cells": cells,
        "timeout_seconds": timeout_seconds,
        "max_containers": max_containers,
        "gpu_rate_per_second": gpu_rate_per_second,
        "conservative_cost_usd": conservative,
        "budget_usd": budget_usd,
        "within_budget": conservative <= budget_usd,
    }
