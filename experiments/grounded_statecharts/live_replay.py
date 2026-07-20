"""Render a static paired replay from sanitized live D2 result rows."""

from __future__ import annotations

import html
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from experiments.grounded_statecharts.replay_viewer import REQUIRED_SECTION_LABELS
from experiments.grounded_statecharts.sanitization import sanitize_public_row

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROWS = REPO_ROOT / "artifacts" / "grounded_statecharts" / "d2_pilot" / "rows.jsonl"
DEFAULT_OUTPUT = REPO_ROOT / "artifacts" / "grounded_statecharts" / "live_failure_replay"
DEFAULT_PUBLIC_OUTPUT = (
    Path(__file__).resolve().parent / "results" / "live_failure_replay"
)


def load_rows(path: Path) -> list[dict[str, Any]]:
    """Load JSONL rows while preserving only JSON-object entries."""

    if not path.is_file():
        raise FileNotFoundError(f"rows file does not exist: {path}")
    rows = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"row {line_number} is not a JSON object")
        rows.append(row)
    if not rows:
        raise ValueError("rows file contains no rows")
    return rows


def _pair_key(row: Mapping[str, Any]) -> tuple[object, object]:
    return row["task_id"], row["repeat_index"]


def select_failure_pair(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Prefer G0 false-completion/G3 success; then use a constraint contrast."""

    normalized = [dict(row) for row in rows]
    for failure in normalized:
        if not (
            failure.get("family") == "artifact_completion"
            and failure.get("condition") == "statechart_g0"
            and failure.get("false_completion") is True
        ):
            continue
        for success in normalized:
            if (
                _pair_key(success) == _pair_key(failure)
                and success.get("condition") == "statechart_g3"
                and success.get("joint_success") is True
            ):
                return failure, success, "artifact false-completion: G0 versus G3"

    for failure in normalized:
        if not (
            failure.get("family") == "recursive_constrained_tool_use"
            and failure.get("joint_success") is False
        ):
            continue
        for success in normalized:
            if (
                _pair_key(success) == _pair_key(failure)
                and success.get("family") == "recursive_constrained_tool_use"
                and success.get("joint_success") is True
            ):
                return failure, success, "constraint joint-success contrast"
    raise ValueError("no authentic failure/contrast pair found in rows")


def _escape(value: object) -> str:
    return html.escape(str(value))


def _row_facts(row: Mapping[str, Any]) -> str:
    fields = (
        "episode_id",
        "condition",
        "false_completion",
        "task_success",
        "joint_success",
        "refusal",
        "invalid_transition",
        "call_count",
        "tool_calls",
        "latency_ms",
        "estimated_cost_usd",
        "checkpoint_digest",
    )
    return "".join(
        f"<tr><th>{_escape(field)}</th><td>{_escape(row.get(field, '—'))}</td></tr>"
        for field in fields
    )


def render_live_failure_replay(
    failure: Mapping[str, Any], success: Mapping[str, Any], *, contrast: str
) -> str:
    """Render a compact, metadata-only replay with the public section labels."""

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grounded Harness Live Failure Replay</title>
<style>
:root {{ color-scheme: dark; font-family: ui-sans-serif, system-ui, sans-serif; }} body {{ margin:0; background:#0b1020; color:#eef2ff; }}
main {{ max-width:1100px; margin:auto; padding:40px 22px 60px; }} .eyebrow {{ color:#93c5fd; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }}
h1 {{ font-size:clamp(2rem,5vw,4rem); line-height:1; }} .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:18px; }}
.card {{ background:#111827; border:1px solid #334155; border-radius:16px; padding:20px; margin-top:18px; overflow:auto; }} .bad {{ color:#fda4af; }} .good {{ color:#86efac; }}
table {{ border-collapse:collapse; width:100%; }} th,td {{ border-bottom:1px solid #334155; padding:8px; text-align:left; overflow-wrap:anywhere; }} th {{ color:#93c5fd; }}
</style></head><body><main>
<div class="eyebrow">Live-row replay · metadata only</div><h1>One observed failure, one matched contrast.</h1>
<p>Selection: {_escape(contrast)}. This rendering includes public row metadata and digests only; it never renders prompts, transcripts, or provider payloads.</p>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[0]}</div><div class="grid">
<article><h2 class="bad">Failure</h2><table>{_row_facts(failure)}</table></article>
<article><h2 class="good">Contrast</h2><table>{_row_facts(success)}</table></article></div></section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[1]}</div><p>Compared conditions: <code>{_escape(failure["condition"])}</code> versus <code>{_escape(success["condition"])}</code>, matched by task and repeat index.</p></section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[2]}</div><p>This is an observational, matched-row contrast. It does not identify a causal mechanism because live episodes can differ beyond the condition label.</p></section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[3]}</div><p>One pair is a diagnostic example, not an effect estimate. Provider stochasticity, task heterogeneity, and unobserved execution state remain unresolved.</p></section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[4]}</div><p>Failure: {_escape(failure.get("call_count"))} calls / {_escape(failure.get("tool_calls"))} tools. Contrast: {_escape(success.get("call_count"))} calls / {_escape(success.get("tool_calls"))} tools.</p></section>
<section class="card"><div class="eyebrow">{REQUIRED_SECTION_LABELS[5]}</div><p>This replay records one authentic row-level contrast only. It is not proof that a harness surface caused the failure or that the contrast generalizes to other tasks, providers, or runs.</p></section>
</main></body></html>"""


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def generate_replay(
    rows_path: Path,
    output_dir: Path = DEFAULT_OUTPUT,
    *,
    publish_public: bool = False,
) -> dict[str, Any]:
    """Write an artifact replay, refusing public output for non-public rows."""

    rows = load_rows(rows_path)
    if publish_public and any(not sanitize_public_row(row).ok for row in rows):
        raise ValueError("public replay requires rows already matching the sanitized public schema")
    failure, success, contrast = select_failure_pair(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "replay.html").write_text(
        render_live_failure_replay(failure, success, contrast=contrast)
    )
    summary = {
        "schema_version": "1.0",
        "source_rows": str(rows_path),
        "output_tier": "public-stub" if publish_public else "artifact",
        "selection": contrast,
        "failure_episode_id": failure["episode_id"],
        "contrast_episode_id": success["episode_id"],
        "allowed_claim": "One matched live-row failure/contrast pair was rendered without raw provider material.",
        "non_claims": [
            "This observational contrast is not causal attribution.",
            "This replay is not an aggregate live D2 result.",
        ],
    }
    _write_json(output_dir / "summary.json", summary)
    return summary
