"""Representation search: find the quotient in which a hidden invariant is manifest.

Exact, deterministic Fiber Finder over a lattice of candidate quotient maps. See
``notes/structural_intelligence_conjecture.md`` and
``notes/latent_structures_meta_framework.md``.
"""

from .core import evaluate_benchmark

__all__ = ["evaluate_benchmark"]
