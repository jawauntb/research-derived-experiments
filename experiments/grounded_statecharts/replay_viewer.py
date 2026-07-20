"""Static public viewer for the grounded-statechart paired replay."""

from __future__ import annotations

import html
from collections.abc import Mapping, Sequence
from typing import Any


REQUIRED_SECTION_LABELS = (
    "Observed events",
    "Intervention",
    "Inferred causal credit",
    "Uncertainty",
    "Cost / budget",
    "Claim boundary",
)


def _escape(value: object) -> str:
    return html.escape(str(value))


def _event_rows(events: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for event in events:
        guard_results = event["guard_results"]
        guard_text = "—"
        if guard_results:
            guard = guard_results[0]
            decision = "PASS" if guard["passed"] else "FAIL"
            guard_text = (
                f"{decision} · {guard['independence_level']} · {guard['explanation']}"
            )
        rows.append(
            "<tr>"
            f"<td>{event['event_index']}</td>"
            f"<td><code>{_escape(event['proposed_transition'])}</code></td>"
            f"<td>{_escape(event['event_type'])}</td>"
            f"<td>{_escape(guard_text)}</td>"
            "</tr>"
        )
    return "".join(rows)


def render_unified_replay(
    *,
    summary: Mapping[str, Any],
    original_events: Sequence[Mapping[str, Any]],
    guarded_events: Sequence[Mapping[str, Any]],
) -> str:
    """Render the public, fixture-only explanation without executing a provider."""
    intervention = next(event["intervention"] for event in guarded_events if event["intervention"])
    original = summary["outcomes"]["original"]
    guarded = summary["outcomes"]["guarded_replay"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grounded Harness Failure Replay</title>
<style>
:root {{ color-scheme: dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; background: #0b1020; color: #eef2ff; }}
main {{ max-width: 1120px; margin: auto; padding: 40px 22px 60px; }}
.eyebrow {{ color: #93c5fd; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
h1 {{ font-size: clamp(2rem, 5vw, 4rem); line-height: 1; margin: 10px 0 16px; }}
h2 {{ margin: 0 0 12px; font-size: 1.15rem; }}
.lede, .muted {{ color: #cbd5e1; max-width: 820px; }}
.chart {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 30px 0; }}
.state {{ border: 1px solid #475569; border-radius: 999px; padding: 8px 13px; background: #111827; }}
.arrow {{ color: #60a5fa; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
.card {{ background: #111827; border: 1px solid #334155; border-radius: 16px; padding: 20px; overflow: auto; }}
.card + .card {{ margin-top: 18px; }}
.bad {{ color: #fda4af; }} .good {{ color: #86efac; }}
table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
th, td {{ border-bottom: 1px solid #334155; padding: 10px 8px; text-align: left; vertical-align: top; }}
th {{ color: #93c5fd; }} code {{ color: #fde68a; overflow-wrap: anywhere; }}
.facts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }}
.fact {{ border-left: 3px solid #60a5fa; padding-left: 12px; }}
.boundary {{ border-left-color: #fbbf24; }}
ul {{ margin: 8px 0 0; padding-left: 20px; }}
</style>
</head>
<body><main>
<div class="eyebrow">Deterministic fixture · public failure replay</div>
<h1>A success report is not a completion receipt.</h1>
<p class="lede">The same committed checkpoint is replayed twice. The original self-report guard commits without the required artifact; an independently checked artifact guard routes to repair before commit.</p>
<div class="chart"><span class="state">Observe</span><span class="arrow">→</span><span class="state">Act</span><span class="arrow">→</span><span class="state">Verify</span><span class="arrow">→</span><span class="state">Commit</span><span>or</span><span class="state">Repair</span></div>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[0]}</div>
<div class="grid">
<article><h2 class="bad">Original · false completion</h2><table><thead><tr><th>#</th><th>Edge</th><th>Event</th><th>Guard receipt</th></tr></thead><tbody>{_event_rows(original_events)}</tbody></table></article>
<article><h2 class="good">Guarded replay · grounded commit</h2><table><thead><tr><th>#</th><th>Edge</th><th>Event</th><th>Guard receipt</th></tr></thead><tbody>{_event_rows(guarded_events)}</tbody></table></article>
</div></section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[1]}</div>
<p><strong>Changed component:</strong> <code>{_escape(intervention['component'])}</code> only.</p>
<p class="muted">{_escape(intervention['reason'])}</p>
<p><strong>Original receipt:</strong> <code>{_escape(intervention['original_digest'])}</code><br><strong>Replacement receipt:</strong> <code>{_escape(intervention['replacement_digest'])}</code></p>
</section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[2]}</div>
<p>Within this paired deterministic fixture, changing only the guard changes the terminal outcome from false completion to grounded commit. This is causal credit for the registered guard intervention in this fixture, not a general attribution claim.</p>
<div class="facts"><div class="fact"><strong>Original</strong><br>{_escape(original['terminal_state'])}; false completion = {_escape(original['false_completion'])}</div><div class="fact"><strong>Guarded</strong><br>{_escape(guarded['terminal_state'])}; false completion = {_escape(guarded['false_completion'])}</div><div class="fact"><strong>No-op identity</strong><br>{_escape(str(summary['gates']['noop_replay_identity']).lower())}</div></div>
</section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[3]}</div>
<p>This replay has one committed deterministic fixture, no sampling distribution, and no confidence interval. Its uncertainty is external validity: no live model, provider, stochastic replay, or OOD reliability was evaluated.</p>
</section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[4]}</div>
<div class="facts"><div class="fact"><strong>Provider calls</strong><br>0</div><div class="fact"><strong>Original event budget</strong><br>{_escape(original['event_count'])} logical events</div><div class="fact"><strong>Guarded event budget</strong><br>{_escape(guarded['event_count'])} logical events; {_escape(guarded['repair_count'])} repair</div></div>
<p class="muted">The public replay is rendered only from committed summary and event rows; it does not invoke a live provider or network.</p>
</section>
<section class="card boundary"><div class="eyebrow">{REQUIRED_SECTION_LABELS[5]}</div>
<p>{_escape(summary['allowed_claim'])}</p><ul>{"".join(f"<li>{_escape(item)}</li>" for item in summary["non_claims"])}</ul>
</section>
</main></body></html>
"""
