"""Provider-neutral executors for grounded live evaluation."""

from experiments.grounded_statecharts.adapters.fixture import FixtureExecutor
from experiments.grounded_statecharts.adapters.protocol import (
    ExecutorRequest,
    ExecutorResponse,
    ProviderExecutor,
)

__all__ = [
    "ExecutorRequest",
    "ExecutorResponse",
    "FixtureExecutor",
    "ProviderExecutor",
    "build_executor",
]


def build_executor(adapter_id: str) -> ProviderExecutor:
    """Construct an executor. Live adapters are opt-in and never default."""

    if adapter_id == "fixture":
        return FixtureExecutor()
    if adapter_id == "live":
        from experiments.grounded_statecharts.adapters.live import LiveExecutor

        return LiveExecutor.from_env()
    raise ValueError(f"unknown adapter_id: {adapter_id}")
