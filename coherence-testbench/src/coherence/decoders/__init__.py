"""Decoder heads: per-subject baseline + cross-subject target."""

from .baseline import PerSubjectRiemannDecoder
from .cross_subject import CrossSubjectAdversarialDecoder

__all__ = ["PerSubjectRiemannDecoder", "CrossSubjectAdversarialDecoder"]
