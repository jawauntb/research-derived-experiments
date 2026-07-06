# Causally Grounded Agents Release Schema

Generated: 2026-07-06

This document defines the shared artifact shape for benchmark suites in
`docs/causally_grounded_agents_benchmark.md`.

The goal is simple: a new suite should not invent its own reporting language.
Every suite should emit comparable rows, summaries, gates, baselines, and
claim boundaries.

## Directory Layout

Recommended layout for each suite:

```text
experiments/<suite_name>/
  README.md
  BENCHMARK_CARD.md
  PROVENANCE.md
  results/
    <result_key>_<date>.md
papers/<suite_name>/
  paper.md
  paper.pdf
artifacts/<suite_name>/
  <run_key>_rows.jsonl       # gitignored raw rows
  <run_key>_summary.json     # gitignored raw summary unless intentionally committed
```

Small public examples or fixture summaries may be committed when they are
explicitly marked as examples. Provider outputs, raw prompts, and large Modal
payloads should remain under gitignored `artifacts/` unless summarized.

## JSONL Row Schema

Each row is one scored episode, probe, patch, or evaluation unit.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `suite` | string | Suite id, for example `long_horizon_moved_bottleneck` |
| `condition` | string | Experimental condition or prompt family |
| `model` | string | Model, agent, or baseline id |
| `seed` | integer | Seed or deterministic fixture id |
| `episode_id` | string/integer | Stable row id within the run |
| `split` | string | `train`, `id`, `ood`, `control`, `stress`, or `patch` |
| `metrics` | object | Numeric row-level measurements |
| `gates` | object | Row-local boolean or numeric gate components |
| `metadata` | object | Suite-specific variables such as critical slot or provider |

Recommended optional fields:

| Field | Type | Meaning |
|---|---|---|
| `provider` | string | API/provider adapter id |
| `prompt_family` | string | Prompt template id for language/API runs |
| `artifact_ref` | string | Relative path to a derived artifact |
| `raw_ref` | string | Local-only raw artifact pointer, omitted in public rows |
| `error` | object/null | Structured failure information |

Rows should not depend on natural-language parsing by downstream tooling. Put
the human-readable explanation in result reports; keep rows structured.

## Summary JSON Schema

The machine-readable summary schema lives in
`docs/causally_grounded_agents_release_schema.json`.

Every summary should include:

- run identity and date;
- suite id and suite version;
- behavior metrics;
- causal-structure gate metrics;
- anti-cheat controls;
- baseline comparisons;
- pass/fail verdict;
- allowed claim and non-claims;
- artifact pointers.

Artifact pointers should distinguish tracked release artifacts from local-only
raw material. For example, `summary_json` should point at the public tracked
summary when one exists, while `raw_summary_json` or `rows_jsonl` may point to
gitignored local `artifacts/` paths only when they are explicitly described as
local-only in the report/card ledger. Use `critical_review_md` for the tracked
paper or benchmark review when a release includes one.

## Gate Definitions

Each suite should define gates in the same shape:

```json
{
  "gate_id": "D2",
  "name": "moved_slot_specificity",
  "axis": "causal_representation",
  "threshold": "ci_lower > 0 and rank_percentile > 0.5",
  "value": 2.309,
  "passed": true,
  "evidence_ref": "experiments/long_horizon_bottleneck/results/..."
}
```

Gate axes must be one of:

- `behavior`
- `causal_representation`
- `attribution`
- `inquiry`
- `commitment`
- `generalization`
- `anti_cheat`

## Benchmark Card Schema

Each `BENCHMARK_CARD.md` should include:

1. Purpose.
2. Position in the causally grounded agents benchmark.
3. Current status.
4. Primary gates.
5. Anti-cheat controls.
6. Latest accepted result.
7. Failure boundaries.
8. Use.
9. Non-claims.
10. Reproduction commands or pointers.

## Baselines

Every suite should name lower and upper references.

Lower baselines:

- random policy or random encoder;
- sensory-only encoder;
- wrong-group compatibility;
- shuffled source labels;
- current-error proxy when probe value is the target;
- final-answer-only or shortcut prompt when appropriate.

Upper or diagnostic references:

- oracle source labels;
- visible-control condition;
- known transformation family;
- oracle critical slot;
- fixture provider;
- deterministic simulator oracle;
- causal patch with known donor/corrupted pair.

## Minimum Pass Record

A run summary should explicitly record whether the minimum pass rule is
satisfied:

```json
{
  "minimum_pass_rule": {
    "behavior_passed": true,
    "structure_gate_passed": true,
    "anti_cheat_controls_passed": true,
    "passed": true
  }
}
```

If any component is absent, mark it absent rather than silently passing it.

## Claim Levels

Allowed claim levels:

- `scaffold`
- `diagnostic`
- `generated-text result`
- `activation result`
- `cross-model activation result`
- `causal steering result`
- `human-validated result`
- `neural-validated result`

Most suites in this repo currently justify `diagnostic`, `activation result`,
or `cross-model activation result`. API-only runs are behavioral diagnostics and
do not establish hidden-state localization.

## Portable Source Index

Do not rely on local-only folder paths in public docs. Use repo-relative paths
plus archive names:

| Evidence | Repo path | Archive name |
|---|---|---|
| Planning from Concern | `papers/planning_from_concern/paper.pdf` | `10_Planning_from_Concern_v2_2026_07_06.pdf` |
| First-Order Self | `papers/first_order_self/paper.pdf` | `16_First_Order_Self_v2_2026_07_06.pdf` |
| World Responds | `papers/world_responds/paper.pdf` | `22_World_Responds_Reengagement_Floor_2026_07_06.pdf` |
| Probe Value Re-Engagement | `papers/probe_value_reengagement/paper.pdf` | `23A_Probe_Value_Reengagement_2026_06_12.pdf` |
| Habituated Re-Engagement | `papers/habituated_reengagement/paper.pdf` | `23B_Habituated_Reengagement_2026_06_12.pdf` |
| Metric Stack of Concern | `papers/metric_stack_synthesis/paper.pdf` | `26_Metric_Stack_of_Concern_v4_2026_07_06.pdf` |
| Long-Horizon Moved Bottleneck | `papers/long_horizon_bottleneck/paper.pdf` | `31_Future_Control_Moves_Memory_2026_07_06.pdf` |
| Causally Grounded Agents Benchmark | `papers/causally_grounded_agents_benchmark/paper.pdf` | `32_Benchmarking_Causally_Grounded_Finite_Agents_2026_07_06.pdf` |
| Suite C Re-Engagement | `papers/habituated_reengagement/suite_c_reengagement_under_world_change.pdf` | `33_Suite_C_Reengagement_Under_World_Change_2026_07_06.pdf` |

The public sharing bundle is indexed in `docs/publication_sharing_map.md`.
