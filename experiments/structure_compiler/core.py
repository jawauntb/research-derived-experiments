"""A substrate-independent dynamical structure compiled into many substrates.

The abstract structure ``S`` is a small automaton exhibiting three motifs the
directing thread asked for: **accumulation** (a level integrates an input),
**phase transition** (a regime flips when the level crosses a threshold), and
**memory as hysteresis** (the down-threshold is below the up-threshold, so the
regime remembers its history). From a fixed input schedule it produces a
deterministic abstract trajectory of ``(level, regime)`` pairs.

Compilation functors ``F_i : S -> R_i`` map that trajectory into concrete
substrates -- music (pitch/octave), a visual field (bar heights/colors), text
(regime-keyed lexicon, line length ~ level), and spatial navigation (a corridor
path with regime-gated edges). Each substrate has a readback ``q_i : R_i -> S``.
The benchmark verifies **structural identity**: ``q_i o F_i = id`` on the
trajectory, i.e. every medium is genuinely the same work, not merely
mood-matched. Fidelity is reported per medium (1.0 == the diagram commutes).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Abstract structure S
# ---------------------------------------------------------------------------

LEVEL_MAX = 6
THETA_UP = 5
THETA_DOWN = 2
Regime = str  # "low" | "high"


@dataclass(frozen=True)
class Node:
    level: int
    regime: Regime


# A deterministic input schedule: accumulate, cross up, drain, cross down, rise.
DEFAULT_INPUTS: tuple[int, ...] = (2, 2, 2, -1, -2, -2, 2, 3, -3, 1)


def run_structure(
    inputs: Sequence[int] = DEFAULT_INPUTS, *, level0: int = 0, regime0: Regime = "low"
) -> list[Node]:
    """Evolve the accumulator-with-hysteresis automaton; return the trajectory."""
    level, regime = level0, regime0
    traj = [Node(level, regime)]
    for delta in inputs:
        level = max(0, min(LEVEL_MAX, level + delta))
        if regime == "low" and level >= THETA_UP:
            regime = "high"
        elif regime == "high" and level <= THETA_DOWN:
            regime = "low"
        traj.append(Node(level, regime))
    return traj


# ---------------------------------------------------------------------------
# Compilers F_i and readbacks q_i
# ---------------------------------------------------------------------------

_BASE_PITCH = 48  # C3 in MIDI
_LOW_WORDS = ("still", "grey", "waiting", "under")
_HIGH_WORDS = ("bright", "ringing", "open", "above")


def compile_music(traj: Sequence[Node]) -> list[dict]:
    """Level -> semitone within an octave; regime -> octave shift."""
    notes = []
    for node in traj:
        octave = 12 if node.regime == "high" else 0
        notes.append({"midi": _BASE_PITCH + octave + node.level, "regime": node.regime})
    return notes


def readback_music(notes: Sequence[dict]) -> list[Node]:
    out = []
    for note in notes:
        rel = int(note["midi"]) - _BASE_PITCH
        regime = "high" if rel >= 12 else "low"
        level = rel - (12 if regime == "high" else 0)
        out.append(Node(level, regime))
    return out


def compile_visual(traj: Sequence[Node]) -> list[dict]:
    """A bar field: height == level, hue keyed by regime."""
    return [
        {"height": node.level, "hue": "gold" if node.regime == "high" else "slate"}
        for node in traj
    ]


def readback_visual(field: Sequence[dict]) -> list[Node]:
    return [
        Node(int(bar["height"]), "high" if bar["hue"] == "gold" else "low")
        for bar in field
    ]


def compile_text(traj: Sequence[Node]) -> list[str]:
    """One line per step: regime picks the lexicon, level sets the word count."""
    lines = []
    for i, node in enumerate(traj):
        lexicon = _HIGH_WORDS if node.regime == "high" else _LOW_WORDS
        word = lexicon[i % len(lexicon)]
        count = node.level + 1  # >= 1 word so empty lines never appear
        lines.append(" ".join([word] * count))
    return lines


def readback_text(lines: Sequence[str]) -> list[Node]:
    out = []
    for line in lines:
        words = line.split()
        regime = "high" if words[0] in _HIGH_WORDS else "low"
        out.append(Node(len(words) - 1, regime))
    return out


def compile_spatial(traj: Sequence[Node]) -> list[dict]:
    """A corridor path: node index == level; regime marks which gate is open."""
    return [
        {"node": f"n{node.level}", "gate": "upper" if node.regime == "high" else "lower"}
        for node in traj
    ]


def readback_spatial(path: Sequence[dict]) -> list[Node]:
    return [
        Node(int(step["node"][1:]), "high" if step["gate"] == "upper" else "low")
        for step in path
    ]


@dataclass(frozen=True)
class Medium:
    name: str
    compile_fn: Callable[..., list]
    readback_fn: Callable[..., list[Node]]


MEDIA: tuple[Medium, ...] = (
    Medium("music", compile_music, readback_music),
    Medium("visual", compile_visual, readback_visual),
    Medium("text", compile_text, readback_text),
    Medium("spatial", compile_spatial, readback_spatial),
)


def compile_all(traj: Sequence[Node]) -> dict[str, list]:
    return {m.name: m.compile_fn(traj) for m in MEDIA}


def _fidelity(reference: Sequence[Node], recovered: Sequence[Node]) -> float:
    if len(reference) != len(recovered):
        return 0.0
    matches = sum(1 for a, b in zip(reference, recovered, strict=True) if a == b)
    return matches / len(reference)


def evaluate_benchmark(inputs: Sequence[int] = DEFAULT_INPUTS) -> dict:
    traj = run_structure(inputs)
    abstract = [{"level": n.level, "regime": n.regime} for n in traj]

    verification: dict[str, dict] = {}
    recovered_all: list[list[Node]] = []
    for medium in MEDIA:
        embodiment = medium.compile_fn(traj)
        recovered = medium.readback_fn(embodiment)
        recovered_all.append(recovered)
        verification[medium.name] = {
            "fidelity": round(_fidelity(traj, recovered), 12),
            "commutes": recovered == list(traj),
            "length": len(embodiment),
        }

    # Every medium must recover the *same* trajectory: they are one work.
    cross_medium_identical = all(rec == list(traj) for rec in recovered_all)
    exhibits_phase_transition = any(n.regime == "high" for n in traj) and any(
        n.regime == "low" for n in traj
    )
    # Hysteresis witness: a level in [THETA_DOWN+1, THETA_UP-1] occurs in both regimes.
    ambiguous = {
        n.regime for n in traj if THETA_DOWN < n.level < THETA_UP
    }
    exhibits_hysteresis = ambiguous == {"low", "high"}

    gates = {
        "all_media_commute": all(v["commutes"] for v in verification.values()),
        "cross_medium_structural_identity": cross_medium_identical,
        "structure_exhibits_phase_transition": exhibits_phase_transition,
        "structure_exhibits_hysteresis": exhibits_hysteresis,
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "abstract_trajectory": abstract,
        "verification": verification,
    }
