"""`MutationReport`: one outcome per mutant, and its Markdown/JSON rendering.

`MutationRunner` (see `runner.py`) yields exactly one `MutationReport` per
`(mutation site, mutation kind)` pair. `status` is the load-bearing field:

- `"killed"`    -- at least one test in `tests/rules/` newly failed against
                   the mutant. The mutation site is validated.
- `"survived"`  -- the mutant ran clean (or only reproduced pre-existing
                   baseline failures). This is the guardrail finding: a
                   fault code with a surviving mutant is unvalidated. Fix
                   it by adding a test, never by deleting the mutation
                   site or trusting the rule.
- `"skipped"`   -- the mutant could not be safely produced or executed
                   (unsupported statement shape, generated invalid syntax,
                   subprocess timeout, or another infra failure). Never
                   treated as "survived" -- an inconclusive mutant must
                   not silently count as covered.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

STATUSES: tuple[str, ...] = ("killed", "survived", "skipped")


@dataclass(frozen=True)
class MutationReport:
    rel_file: str
    hinge_lineno: int
    rule_ids: tuple[str, ...]
    mutation_kind: str
    status: str
    detail: str
    returncode: int | None
    duration_s: float

    @property
    def site_id(self) -> str:
        return f"{self.rel_file}:{self.hinge_lineno}"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["rule_ids"] = list(self.rule_ids)
        d["site_id"] = self.site_id
        return d


def summarize(reports: Sequence[MutationReport]) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for r in reports:
        counts[r.status] = counts.get(r.status, 0) + 1
    counts["total"] = len(reports)
    return counts


def surviving_sites(reports: Sequence[MutationReport]) -> list[MutationReport]:
    """Every mutant whose status is `"survived"` -- an UNTESTED rule per the
    Phase 5 guardrail: no test in `tests/rules/` broke when this decision
    hinge was mutated.
    """
    return [r for r in reports if r.status == "survived"]


def _escape_cell(text: str, *, max_len: int = 140) -> str:
    flat = " ".join(text.split())
    flat = flat.replace("|", "\\|")
    if len(flat) > max_len:
        flat = flat[: max_len - 3] + "..."
    return flat


def to_markdown(reports: Sequence[MutationReport]) -> str:
    counts = summarize(reports)
    lines = [
        "# Mutation test report",
        "",
        f"Total mutants: {counts['total']} -- "
        f"killed: {counts['killed']}, survived: {counts['survived']}, skipped: {counts['skipped']}",
        "",
        "| Site | Rule id(s) | Mutation | Status | Detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    ordered = sorted(reports, key=lambda r: (r.rel_file, r.hinge_lineno, r.mutation_kind))
    for r in ordered:
        rule_ids = ", ".join(r.rule_ids) or "?"
        lines.append(f"| `{r.site_id}` | {rule_ids} | {r.mutation_kind} | {r.status.upper()} | {_escape_cell(r.detail)} |")

    survivors = surviving_sites(reports)
    if survivors:
        lines += ["", "## Surviving mutants -- untested, fix by adding a test", ""]
        for r in survivors:
            rule_ids = ", ".join(r.rule_ids) or "?"
            lines.append(f"- `{r.site_id}` ({rule_ids}) -- {r.mutation_kind}")
    else:
        lines += ["", "No surviving mutants in this run."]
    return "\n".join(lines) + "\n"


def to_json(reports: Sequence[MutationReport]) -> str:
    payload = {"summary": summarize(reports), "mutants": [r.to_dict() for r in reports]}
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def write_report(reports: Sequence[MutationReport], markdown_path: Path) -> Path:
    """Writes `markdown_path` plus a sibling `.json` export. Returns the JSON path."""
    markdown_path = Path(markdown_path)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(to_markdown(reports), encoding="utf-8")
    json_path = markdown_path.with_suffix(".json")
    json_path.write_text(to_json(reports), encoding="utf-8")
    return json_path
