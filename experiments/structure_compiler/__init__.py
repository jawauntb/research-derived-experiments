"""Ensemble-first structure compiler: one invariant, many verified embodiments.

Defines a substrate-independent dynamical structure (accumulation -> phase
transition -> hysteresis memory), compiles it into several substrates via
explicit functors, and verifies that each embodiment preserves the abstract
trajectory by reading it back. See ``notes/structural_intelligence_conjecture.md``.
"""

from .core import compile_all, evaluate_benchmark

__all__ = ["compile_all", "evaluate_benchmark"]
