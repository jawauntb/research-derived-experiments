"""The pre-1905 electrodynamics corpus, with hard publication dates.

Every document carries the year its content entered the public record. The
whole retrodiction turns on that number being right, because a *date cut* keeps
only documents at or before a given year, and a leak of post-cut material is
indistinguishable from the nominator working.

Two documents carry ``provenance_risk``: Poincare's "The Measure of Time"
(1898) and "The Principles of Mathematical Physics" (delivered at St Louis in
September 1904) are only available through *The Foundations of Science*, a 1913
English compilation. The content predates the cut; the volume around it does
not, and a translator or editor in 1913 knew what happened in 1905. Every
analysis therefore runs twice, with and without them. See ``cuts.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


__all__ = ["SourceSpec", "SOURCES", "sources_at_or_before"]


@dataclass(frozen=True)
class SourceSpec:
    """A corpus document and the year its content became public."""

    doc_id: str
    wikisource_title: str
    author: str
    #: Year the content entered the public record. The cut compares against this.
    year: int
    #: Set when the *vehicle* carrying the content postdates the content itself.
    provenance_risk: bool = False
    note: str = ""


SOURCES: Final[tuple[SourceSpec, ...]] = (
    # --- the pre-1880 stratum: available at every cut -----------------------
    SourceSpec(
        "maxwell_1865_part1",
        "A Dynamical Theory of the Electromagnetic Field/Part I",
        "James Clerk Maxwell",
        1865,
        note="Read December 1864; published Phil. Trans. 1865.",
    ),
    SourceSpec(
        "maxwell_1865_part6",
        "A Dynamical Theory of the Electromagnetic Field/Part VI",
        "James Clerk Maxwell",
        1865,
        note="'Electromagnetic Theory of Light'.",
    ),
    SourceSpec(
        "maxwell_1878_ether",
        "Encyclopædia Britannica, Ninth Edition/Ether (2.)",
        "James Clerk Maxwell",
        1878,
    ),
    # --- 1881-1897 ----------------------------------------------------------
    SourceSpec(
        "michelson_1881",
        "The Relative Motion of the Earth and the Luminiferous Ether",
        "Albert Abraham Michelson",
        1881,
    ),
    SourceSpec(
        "michelson_morley_1887",
        "On the Relative Motion of the Earth and the Luminiferous Ether",
        "Albert Abraham Michelson and Edward Morley",
        1887,
    ),
    SourceSpec(
        "fitzgerald_1889",
        "The Ether and the Earth's Atmosphere",
        "George Francis FitzGerald",
        1889,
    ),
    SourceSpec(
        "larmor_1897_medium3",
        "Dynamical Theory of the Electric and Luminiferous Medium III",
        "Joseph Larmor",
        1897,
    ),
    SourceSpec(
        "lodge_1897_absence",
        "Experiments on the Absence of Mechanical Connexion between Ether and Matter",
        "Oliver Lodge",
        1897,
    ),
    # --- 1898-1904 ----------------------------------------------------------
    SourceSpec(
        "poincare_1898_time",
        "The Foundations of Science/The Value of Science/Chapter 2",
        "Henri Poincare",
        1898,
        provenance_risk=True,
        note="'The Measure of Time', 1898; reached via the 1913 compilation.",
    ),
    SourceSpec(
        "larmor_1900_ch10",
        "Aether and Matter/Chapter 10",
        "Joseph Larmor",
        1900,
    ),
    SourceSpec(
        "larmor_1900_ch11",
        "Aether and Matter/Chapter 11",
        "Joseph Larmor",
        1900,
    ),
    SourceSpec(
        "rayleigh_1902_refraction",
        "Does Motion through the Aether cause Double Refraction?",
        "Lord Rayleigh",
        1902,
    ),
    SourceSpec(
        "brace_1904_refraction",
        "On Double Refraction in Matter moving through the Aether",
        "DeWitt Bristol Brace",
        1904,
    ),
    SourceSpec(
        "poincare_1904_stlouis",
        "The Foundations of Science/The Value of Science/Chapter 7",
        "Henri Poincare",
        1904,
        provenance_risk=True,
        note="St Louis lecture, September 1904; reached via the 1913 compilation.",
    ),
    SourceSpec(
        "lorentz_1904",
        "Electromagnetic phenomena",
        "Hendrik Lorentz",
        1904,
        note="'...in a system moving with any velocity smaller than that of light'.",
    ),
)


def sources_at_or_before(year: int, *, allow_provenance_risk: bool = True):
    """Sources whose content entered the record at or before ``year``."""
    return tuple(
        s
        for s in SOURCES
        if s.year <= year and (allow_provenance_risk or not s.provenance_risk)
    )
