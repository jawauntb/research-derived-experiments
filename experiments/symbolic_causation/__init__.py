"""Symbolic causation and agency: separate signal, control, knowledge, and agency.

Exact finite-state benchmark that treats a symbolic model/intervention ``m`` as an
operation on a system's distribution over future trajectories, and measures the
distinct quantities the structural-realism ontology conflates under "influence".
See ``notes/structural_intelligence_conjecture.md``.
"""

from .core import evaluate_benchmark

__all__ = ["evaluate_benchmark"]
