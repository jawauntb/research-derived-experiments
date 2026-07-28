"""Report writers for IDENT evaluations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# IDENT baseline summary",
        "",
        f"- split: `{summary.get('split')}`",
        f"- n_items: {summary.get('n_items')}",
        f"- status: **{summary.get('status')}**",
        "",
        "## Gates",
        "",
    ]
    for gate, ok in (summary.get("gates") or {}).items():
        lines.append(f"- {'PASS' if ok else 'FAIL'}: `{gate}`")
    lines.extend(["", "## Baselines", ""])
    baselines = summary.get("baselines") or {}
    for name, agg in baselines.items():
        lines.append(
            f"- `{name}`: separator_acc={agg.get('separator_accuracy'):.3f}, "
            f"false_certainty={agg.get('false_certainty_rate'):.3f}, "
            f"final_acc={agg.get('final_accuracy'):.3f}"
        )
    lines.append("")
    return "\n".join(lines)
