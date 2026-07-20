"""Opt-in live provider adapter.

This module is never imported by the default fixture path. Construction requires
an explicit environment opt-in and fails closed without credentials. Provider
SDK imports stay lazy so clean-clone tests do not need network packages.
"""

from __future__ import annotations

import os

from experiments.grounded_statecharts.adapters.protocol import (
    ExecutorRequest,
    ExecutorResponse,
)

LIVE_OPT_IN_ENV = "GROUNDED_HARNESS_LIVE"
LIVE_PROVIDER_ENV = "GROUNDED_HARNESS_PROVIDER"
LIVE_MODEL_ENV = "GROUNDED_HARNESS_MODEL"


class LiveExecutor:
    """Thin boundary for credentialed live runs.

    The default implementation refuses to execute until a concrete provider
    backend is wired. That keeps the shared contract frozen without making a
    paid API the only testable path.
    """

    adapter_id = "live"

    def __init__(self, *, provider_id: str, model_id: str) -> None:
        if not provider_id or not model_id:
            raise ValueError("provider_id and model_id must be non-empty")
        self.provider_id = provider_id
        self.model_id = model_id

    @classmethod
    def from_env(cls) -> LiveExecutor:
        if os.environ.get(LIVE_OPT_IN_ENV, "").strip() != "1":
            raise RuntimeError(
                f"live adapter requires {LIVE_OPT_IN_ENV}=1; use the fixture adapter by default"
            )
        provider = os.environ.get(LIVE_PROVIDER_ENV, "").strip()
        model = os.environ.get(LIVE_MODEL_ENV, "").strip()
        if not provider or not model:
            raise RuntimeError(
                f"live adapter requires {LIVE_PROVIDER_ENV} and {LIVE_MODEL_ENV}"
            )
        return cls(provider_id=provider, model_id=model)

    def complete(self, request: ExecutorRequest) -> ExecutorResponse:
        del request
        raise RuntimeError(
            "live provider backend is not wired in this tranche; "
            "credentialed smoke tests must supply a concrete LiveExecutor subclass "
            "or wait for the provider backend PR"
        )
