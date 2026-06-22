#!/usr/bin/env python3
"""Discovery EWS — a retrospective early-warning proxy over the program's own history.

Motivation (see results/ and the conversation that produced this):
The information-theoretic insight literature (Tabatabaeian et al., PNAS 2025) gives
a *non-specific* early-warning signal: behavioral surprisal rises before a creative
regime transition. But rising surprisal is structurally identical for (a) a genuine
breakthrough, (b) a stable delusion, and (c) losing the plot. The surprise signal
cannot tell them apart -- only the *new regime's* subsequent ability to survive
transfer and bear external load can, and that verdict is necessarily extrinsic and
lagging.

So this tool does NOT try to score "are we about to break through" in real time
(that is the seductive, flattering, motivated-reasoning version). Instead it scores,
*retrospectively*, the program's own history of destabilizations:

  1. It treats the repository's record (result reports + paper artifacts) as a
     symbolic time series of "inscriptions" (experiment families), ordered by the
     dates embedded in filenames (git commit dates are useless here: the repo was
     seeded in bulk).
  2. It computes the program-level surprisal trajectory and identifies
     destabilization episodes (a dormant/new family activating = bisociation).
  3. For each episode it applies a transparent LOAD-BEARING rubric to the artifacts
     that episode produced, classifying the resolution as load_bearing / self_sealing
     / dissipated.
  4. It reports the spike -> load-bearing CONVERSION RATE: the only honest,
     non-flattering estimate of how productively the program's destabilizations
     resolve.

The "no-false-insight" gate: a high-surprisal episode is NEVER counted as
breakthrough-shaped on surprisal alone. It counts only if it resolved into a regime
that shows transfer-survival AND (external anchoring OR downstream reuse) without
being dominated by failure markers. This bakes the non-identifiability in.

HEURISTIC CAVEAT: the load-bearing signals are regex over markdown. They are a
deliberately conservative proxy, not ground truth; matched strings are surfaced in
the output so every verdict can be audited. Pure standard library.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean

REPO = Path(__file__).resolve().parents[2]

# Meta-families whose artifacts are ABOUT the program rather than part of it.
# Excluded from the scanned corpus so the detector does not eat its own scan
# reports: those reports name every family (inflating `reuse`) and are full of
# "load_bearing/transfer/external" (tripping the rubric) -- a Goodhart feedback
# loop that would inflate the conversion rate every time a scan is recorded.
META_FAMILIES = {"discovery_ews"}

# ---- transparent load-bearing rubric ----
# NOTE: v1 of this rubric produced apophenia -- it labeled the activation_geometry
# graveyard "load_bearing" because bare "pythia"/"gpt-2" mentions (the probed
# substrate, not external contact) and an internal "...transfer..." method term
# fired the external/transfer signals, and "0.000" (a legitimate metric value)
# over-fired the failure signal. These patterns are deliberately tightened so the
# signals mean what they claim. The lesson -- the detector itself hallucinated and
# needed extrinsic correction -- is the point, not a footnote.
TRANSFER = re.compile(
    r"held[- ]?out|transfer gate|transfer[- ]slice|transfer[- ]repair|role[- ]equivariant", re.I
)
GATE_PASS = re.compile(r"all four gates pass|gates? pass|diagnostic tier|mechanism tier|gate pass rate", re.I)
# External = survived contact with something the lab did NOT build (not just "used an
# open model as a probe target"). Bare pythia/gpt-2/openai are excluded on purpose.
EXTERNAL = re.compile(
    r"\bglove\b|\bcifar\b|\bbatchbald\b|literature-nearest|external contact|"
    r"did not (build|train)|model (family|suite) (we|the lab) did not|public (benchmark|leaderboard|table)",
    re.I,
)
# Failure = explicit dead-end language only. "0.000" removed (it is a metric value).
FAILURE = re.compile(
    r"zero target hits|graveyard|\bhalt(ed|s)?\b|failed (the )?(alias|train|gate|transfer|to)|"
    r"did not (pass|recover|replicate)|all_pass.{0,8}False|claim_tier.{0,8}not_reached|\brejected\b",
    re.I,
)


@dataclass
class Artifact:
    family: str
    date: str
    path: str


@dataclass
class FamilyResolution:
    family: str
    n_artifacts: int
    transfer_hits: int
    gate_pass_hits: int
    external_hits: int
    failure_hits: int
    reuse_count: int  # how many OTHER families' artifacts reference this family
    verdict: str
    evidence: dict = field(default_factory=dict)


@dataclass
class Episode:
    onset_date: str
    family: str  # the (re)activating inscription
    dormancy: int  # artifacts since this family was last active (inf -> brand new)
    surprisal: float
    verdict: str  # inherited from the family's resolution


def collect_artifacts() -> list[Artifact]:
    arts: list[Artifact] = []
    date_re = re.compile(r"(2026[_-]\d\d[_-]\d\d)")
    for p in (REPO / "experiments").glob("*/results/*.md"):
        m = date_re.search(p.name)
        if not m:
            continue
        fam = p.relative_to(REPO / "experiments").parts[0]
        if fam in META_FAMILIES:
            continue  # do not let the detector scan its own scan reports
        arts.append(Artifact(fam, m.group(1).replace("-", "_"), str(p.relative_to(REPO))))
    for p in (REPO / "papers").glob("*/paper.md"):
        fam = "paper:" + p.relative_to(REPO / "papers").parts[0]
        # papers rarely carry a date in the filename; use the dir's own paper date if present
        txt = p.read_text(errors="ignore")[:400]
        m = date_re.search(txt)
        date = m.group(1).replace("-", "_") if m else "2026_06_18"
        arts.append(Artifact(fam, date, str(p.relative_to(REPO))))
    # deterministic order: by date then family then path
    arts.sort(key=lambda a: (a.date, a.family, a.path))
    return arts


def surprisal_trajectory(arts: list[Artifact], window: int) -> list[tuple[Artifact, float]]:
    out = []
    for i, a in enumerate(arts):
        ctx = [x.family for x in arts[max(0, i - window) : i]]
        # Laplace-smoothed P(family | recent context)
        n_fam = len(set(x.family for x in arts))
        count = ctx.count(a.family)
        p = (count + 1) / (len(ctx) + n_fam)
        out.append((a, -math.log2(p)))
    return out


def detect_episodes(traj: list[tuple[Artifact, float]], window: int) -> list[Episode]:
    """A destabilization episode = a family (re)activating after dormancy >= window,
    or appearing for the first time. We take the first such artifact per onset."""
    episodes: list[Episode] = []
    last_index: dict[str, int] = {}
    for i, (a, s) in enumerate(traj):
        prev = last_index.get(a.family)
        is_new_family = prev is None
        dormancy = 10**6 if is_new_family else i - prev
        if is_new_family or dormancy >= window:
            episodes.append(Episode(a.date, a.family, dormancy, s, "pending"))
        last_index[a.family] = i
    return episodes


def score_resolution(arts: list[Artifact]) -> dict[str, FamilyResolution]:
    by_fam: dict[str, list[Artifact]] = defaultdict(list)
    for a in arts:
        by_fam[a.family].append(a)
    # text per family
    text: dict[str, str] = {}
    for fam, items in by_fam.items():
        blob = []
        for a in items:
            try:
                blob.append((REPO / a.path).read_text(errors="ignore"))
            except OSError:
                pass
        text[fam] = "\n".join(blob)

    # reuse: count families whose text mentions another family's bare name
    def bare(fam: str) -> str:
        return fam.replace("paper:", "")

    reuse: dict[str, int] = defaultdict(int)
    for fam in by_fam:
        token = re.escape(bare(fam))
        for other, t in text.items():
            if other == fam:
                continue
            if re.search(rf"\b{token}\b", t):
                reuse[fam] += 1

    res: dict[str, FamilyResolution] = {}
    for fam, items in by_fam.items():
        t = text[fam]
        th = len(TRANSFER.findall(t))
        gp = len(GATE_PASS.findall(t))
        ex = len(EXTERNAL.findall(t))
        fa = len(FAILURE.findall(t))
        ru = reuse[fam]
        # verdict logic (the no-false-insight gate)
        failure_dominated = fa >= max(3, th + gp)  # mostly dead-ends
        has_transfer = th >= 1
        # external contact, or strong internal subsumption (raised bar: bare internal
        # cross-references inflate easily, so require >= 2 reusing families).
        has_anchor = ex >= 1 or ru >= 2
        if failure_dominated and not has_transfer:
            verdict = "dissipated"
        elif has_transfer and has_anchor and not failure_dominated:
            verdict = "load_bearing"
        elif gp >= 1 and not has_transfer:
            verdict = "self_sealing"  # passed gates only i.i.d., no transfer/external
        elif fa >= 1 and gp == 0 and th == 0:
            verdict = "dissipated"
        else:
            verdict = "self_sealing"
        res[fam] = FamilyResolution(
            family=fam,
            n_artifacts=len(items),
            transfer_hits=th,
            gate_pass_hits=gp,
            external_hits=ex,
            failure_hits=fa,
            reuse_count=ru,
            verdict=verdict,
            evidence={
                "transfer_sample": TRANSFER.findall(t)[:3],
                "failure_sample": FAILURE.findall(t)[:3],
            },
        )
    return res


def generativity_ratio() -> dict:
    fams = [d.name for d in (REPO / "experiments").glob("*") if d.is_dir() and (d / "results").exists()]
    fams += [d.name for d in (REPO / "experiments").glob("*") if d.is_dir() and not (d / "results").exists()]
    n_fam = len([d for d in (REPO / "experiments").glob("*") if d.is_dir() and d.name != "__pycache__"])
    n_paper = len([d for d in (REPO / "papers").glob("*") if d.is_dir()])
    return {
        "experiment_families": n_fam,
        "paper_artifacts": n_paper,
        "artifacts_per_family": round(n_paper / n_fam, 3) if n_fam else None,
        "reading": (
            "~1:1 artifacts-per-family is 'excessive agglomeration' (12 elements -> 12 spaces); "
            "a breakthrough is an 'informed simplicity' DOWNTURN where one weak principle subsumes "
            "many families. A FALLING ratio over time is the generativity signature."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window", type=int, default=6, help="context window (artifacts) for surprisal & dormancy")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    arts = collect_artifacts()
    traj = surprisal_trajectory(arts, args.window)
    episodes = detect_episodes(traj, args.window)
    resolutions = score_resolution(arts)

    # attach verdicts to episodes
    for e in episodes:
        e.verdict = resolutions[e.family].verdict

    # daily mean surprisal trajectory
    by_day: dict[str, list[float]] = defaultdict(list)
    for a, s in traj:
        by_day[a.date].append(s)
    daily = {d: round(mean(v), 3) for d, v in sorted(by_day.items())}

    # conversion rate over episodes (the headline, non-flattering number)
    counts = defaultdict(int)
    for e in episodes:
        counts[e.verdict] += 1
    total = len(episodes)
    conversion = round(counts["load_bearing"] / total, 3) if total else None

    payload = {
        "manifest": {
            "tool": "discovery_ews",
            "window": args.window,
            "n_artifacts": len(arts),
            "note": "Retrospective proxy. Surprisal alone is NOT scored as breakthrough; "
            "only load-bearing resolution (transfer-survival + external/reuse, not failure-dominated) counts.",
            "heuristic_caveat": "Load-bearing signals are regex over markdown; verdicts are auditable, not ground truth.",
        },
        "daily_mean_surprisal": daily,
        "episode_verdict_counts": dict(counts),
        "spike_to_load_bearing_conversion_rate": conversion,
        "generativity": generativity_ratio(),
        "family_resolutions": {k: asdict(v) for k, v in sorted(resolutions.items())},
        "episodes": [asdict(e) for e in episodes],
    }
    output = json.dumps(payload, indent=2, sort_keys=True, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
