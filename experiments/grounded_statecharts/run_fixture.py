"""Regenerate the deterministic grounded-statechart replay bundle."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.runtime import (
    EpisodeOutcome,
    Event,
    Fixture,
    HarnessManifest,
    ReplayEngine,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKAGE_ROOT / "results"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, events: tuple[Event, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.dumps(event.to_dict(), sort_keys=True) for event in events]
    path.write_text("\n".join(rows) + "\n")


def event_path(outcome: EpisodeOutcome) -> list[str]:
    return [event.proposed_transition for event in outcome.events]


def validate_event_shape(events: tuple[Event, ...], schema: dict[str, Any]) -> bool:
    required = set(schema["required"])
    properties = set(schema["properties"])
    return required == properties and all(set(event.to_dict()) == required for event in events)


def _event_rows(outcome: EpisodeOutcome) -> str:
    rows = []
    for event in outcome.events:
        guard = event.guard_results[0] if event.guard_results else None
        guard_text = "—"
        if guard is not None:
            decision = "PASS" if guard.passed else "FAIL"
            guard_text = f"{decision} · {guard.independence_level} · {guard.explanation}"
        rows.append(
            "<tr>"
            f"<td>{event.event_index}</td>"
            f"<td><code>{html.escape(event.proposed_transition)}</code></td>"
            f"<td>{html.escape(event.event_type)}</td>"
            f"<td>{html.escape(guard_text)}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_viewer(
    *,
    fixture: Fixture,
    original: EpisodeOutcome,
    guarded: EpisodeOutcome,
    summary: dict[str, Any],
) -> str:
    original_label = "FALSE COMPLETION" if original.false_completion else "GROUNDED COMMIT"
    guarded_label = "FALSE COMPLETION" if guarded.false_completion else "GROUNDED COMMIT"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grounded Statechart Replay</title>
<style>
:root {{ color-scheme: dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; background: #0b1020; color: #eef2ff; }}
main {{ max-width: 1120px; margin: auto; padding: 40px 22px 60px; }}
.eyebrow {{ color: #93c5fd; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ font-size: clamp(2rem, 5vw, 4rem); line-height: 1; margin: 10px 0 16px; }}
.lede {{ color: #cbd5e1; max-width: 760px; font-size: 1.08rem; }}
.chart {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 30px 0; }}
.state {{ border: 1px solid #475569; border-radius: 999px; padding: 8px 13px; background: #111827; }}
.arrow {{ color: #60a5fa; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
.card {{ background: #111827; border: 1px solid #334155; border-radius: 16px; padding: 20px; overflow: auto; }}
.bad {{ color: #fda4af; }} .good {{ color: #86efac; }}
table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
th, td {{ border-bottom: 1px solid #334155; padding: 10px 8px; text-align: left; vertical-align: top; }}
th {{ color: #93c5fd; }} code {{ color: #fde68a; }}
.boundary {{ margin-top: 18px; border-left: 3px solid #a78bfa; padding: 2px 0 2px 14px; color: #ddd6fe; }}
</style>
</head>
<body><main>
<div class="eyebrow">Deterministic fixture · observed replay</div>
<h1>A success report is not a completion receipt.</h1>
<p class="lede">{html.escape(fixture.task)} The original G0 self-report commits while the artifact is absent. Replaying the same checkpoint with only the guard changed to a G3 artifact digest routes through repair before commit.</p>
<div class="chart"><span class="state">Observe</span><span class="arrow">→</span><span class="state">Act</span><span class="arrow">→</span><span class="state">Verify</span><span class="arrow">→</span><span class="state">Commit</span><span>or</span><span class="state">Repair</span></div>
<section class="grid">
<article class="card"><div class="eyebrow">Original · observed</div><h2 class="bad">{original_label}</h2>
<table><thead><tr><th>#</th><th>Edge</th><th>Event</th><th>Guard receipt</th></tr></thead><tbody>{_event_rows(original)}</tbody></table></article>
<article class="card"><div class="eyebrow">Guard intervention · observed</div><h2 class="good">{guarded_label}</h2>
<table><thead><tr><th>#</th><th>Edge</th><th>Event</th><th>Guard receipt</th></tr></thead><tbody>{_event_rows(guarded)}</tbody></table></article>
</section>
<section class="card" style="margin-top:18px"><div class="eyebrow">Replay evidence</div>
<p><strong>Checkpoint:</strong> <code>{summary['checkpoint_digest']}</code></p>
<p><strong>No-op identity:</strong> {str(summary['gates']['noop_replay_identity']).lower()} — event stream and outcome match byte-for-byte.</p>
<p><strong>Changed component:</strong> <code>guard</code> only; all chart, repair, task, and checkpoint inputs are held fixed.</p>
<div class="boundary"><strong>Claim boundary:</strong> {html.escape(summary['allowed_claim'])} This fixture does not establish model-level or OOD reliability.</div>
</section>
</main></body></html>
"""


def generate_results(output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    fixture = Fixture.load(PACKAGE_ROOT / "fixtures" / "false_success.json")
    self_report = HarnessManifest.load(PACKAGE_ROOT / "manifests" / "self_report.json")
    independent = HarnessManifest.load(
        PACKAGE_ROOT / "manifests" / "independent_artifact.json"
    )
    schema = json.loads((PACKAGE_ROOT / "schemas" / "event.schema.json").read_text())
    engine = ReplayEngine()
    checkpoint = engine.checkpoint_before_verification(fixture, self_report)
    original = engine.replay(checkpoint, fixture, self_report)
    noop = engine.replay(checkpoint, fixture, self_report)
    guarded = engine.replay(checkpoint, fixture, self_report, independent)

    changed_components = self_report.changed_components(independent)
    noop_identity = original == noop
    schema_complete = all(
        validate_event_shape(outcome.events, schema) for outcome in (original, noop, guarded)
    )
    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": "grounded_statecharts_fixture_2026_07_20",
        "fixture": fixture.episode_id,
        "checkpoint_digest": checkpoint.checkpoint_digest,
        "manifest_digests": {
            "self_report": self_report.manifest_digest,
            "independent_artifact": independent.manifest_digest,
        },
        "changed_components": list(changed_components),
        "gates": {
            "typed_event_schema": schema_complete,
            "manifest_single_component_delta": changed_components == ("guard",),
            "noop_replay_identity": noop_identity,
            "minimal_statechart": set(self_report.chart)
            == {"observe", "act", "verify", "commit", "repair"},
            "false_completion_prevented": original.false_completion
            and not guarded.false_completion,
            "repair_reaches_grounded_commit": guarded.task_success
            and guarded.repair_count == 1,
        },
        "metrics": {
            "original_false_completion": int(original.false_completion),
            "guarded_false_completion": int(guarded.false_completion),
            "original_task_success": int(original.task_success),
            "guarded_task_success": int(guarded.task_success),
            "guarded_repairs": guarded.repair_count,
        },
        "outcomes": {
            "original": original.to_dict(),
            "noop_replay": noop.to_dict(),
            "guarded_replay": guarded.to_dict(),
        },
        "paths": {
            "original": event_path(original),
            "guarded_replay": event_path(guarded),
        },
        "allowed_claim": (
            "On the committed deterministic false-success fixture, no-op replay is exact "
            "and replacing only a G0 self-report guard with a G3 artifact-digest guard "
            "prevents premature commit and triggers a successful repair."
        ),
        "non_claims": [
            "No live model or provider was evaluated.",
            "One deterministic fixture does not estimate a population effect.",
            "The result does not establish Constraint Transport, counterfactual search, or unlearning claims.",
        ],
    }
    if not all(summary["gates"].values()):
        raise RuntimeError("fixture exit gate failed; refusing to publish replay bundle")

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "checkpoint.json", checkpoint.to_dict())
    write_jsonl(output_dir / "original.jsonl", original.events)
    write_jsonl(output_dir / "noop_replay.jsonl", noop.events)
    write_jsonl(output_dir / "guarded_replay.jsonl", guarded.events)
    (output_dir / "replay.html").write_text(
        render_viewer(fixture=fixture, original=original, guarded=guarded, summary=summary)
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    summary = generate_results(args.out_dir)
    print(
        json.dumps(
            {
                "run_id": summary["run_id"],
                "gates": summary["gates"],
                "out_dir": str(args.out_dir),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
