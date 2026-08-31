"""Shared fixtures for src/normalize tests.

Puts `bio-claim-firewall/src` on `sys.path` (this directory owns no
pyproject.toml of its own, so there's no installed-package import path) and
provides `FakeSnapshot`, a tiny dict-backed `Snapshot` test double covering:

- 3 genes: HGNC:1097 (BRAF), HGNC:6407 (KRAS), HGNC:11998 (TP53)
- 2 cell types: CL:0000236 (B cell) -> ancestors (CL:0000738, CL:0000000);
  CL:0000988 (hematopoietic cell) -> ancestors (CL:0000000,)
- 1 species: NCBITaxon:9606
- 1 deprecated alias: HGNC:OLD1 -> HGNC:1097
"""

from __future__ import annotations

import pytest

# `bio-claim-firewall/conftest.py` puts `bio-claim-firewall/src/` on sys.path
# before any test module (including this conftest) is imported.
from normalize.errors import NormalizationError


class FakeSnapshot:
    """Dict-backed `Snapshot` test double over a tiny fixed universe."""

    _CANONICAL: frozenset[str] = frozenset(
        {
            "HGNC:1097",
            "HGNC:6407",
            "HGNC:11998",
            "CL:0000236",
            "CL:0000988",
            "CL:0000738",
            "CL:0000000",
            "NCBITaxon:9606",
        }
    )
    _ANCESTORS: dict[str, tuple[str, ...]] = {
        "CL:0000236": ("CL:0000738", "CL:0000000"),
        "CL:0000988": ("CL:0000000",),
    }
    _ALIASES: dict[str, str] = {
        "HGNC:OLD1": "HGNC:1097",
    }

    def contains(self, curie: str) -> bool:
        return curie in self._CANONICAL

    def canonicalize(self, curie: str) -> str:
        if curie in self._CANONICAL:
            return curie
        if curie in self._ALIASES:
            return self._ALIASES[curie]
        raise NormalizationError(
            f"{curie!r} does not resolve in the frozen snapshot",
            fault_code="UNKNOWN_ENTITY",
            curie=curie,
        )

    def ancestors(self, curie: str) -> tuple[str, ...]:
        if not curie.startswith("CL:"):
            return ()
        return self._ANCESTORS.get(curie, ())

    def aliases(self, curie: str) -> tuple[str, ...]:
        return tuple(alias for alias, target in self._ALIASES.items() if target == curie)


@pytest.fixture
def snapshot() -> FakeSnapshot:
    return FakeSnapshot()
