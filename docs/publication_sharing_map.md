# Publication Sharing Map

Generated: 2026-07-06

This is the exact share plan for the causally grounded agents benchmark work and
for a similar benchmark package aimed at publication.

## What To Share First

Share a small, legible bundle. Do not send the whole local
`/Users/jawaun/Metaphysics of Intelligence` folder as the first object.

Minimum public bundle:

1. GitHub repository root:
   `https://github.com/jawauntb/research-derived-experiments`
2. Umbrella benchmark doc:
   `docs/causally_grounded_agents_benchmark.md`
3. Shared schema:
   `docs/causally_grounded_agents_release_schema.md`
4. Machine-readable schema:
   `docs/causally_grounded_agents_release_schema.json`
5. Suite D/E hardened card:
   `experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`
6. Suite C frontier card:
   `experiments/world_responds/BENCHMARK_CARD.md`
7. Suite C status report:
   `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`
8. Publication sharing map:
   `docs/publication_sharing_map.md`

Paper PDFs to share as the first reading packet:

| Use | Repo path | Local archive path |
|---|---|---|
| Benchmark umbrella | `papers/causally_grounded_agents_benchmark/paper.pdf` | `/Users/jawaun/Metaphysics of Intelligence/32_Benchmarking_Causally_Grounded_Finite_Agents_2026_07_06.pdf` |
| Hardened moved-bottleneck Suite D/E evidence | `papers/long_horizon_bottleneck/paper.pdf` | `/Users/jawaun/Metaphysics of Intelligence/31_Future_Control_Moves_Memory_2026_07_06.pdf` |
| Suite C failure/repair frontier | `papers/habituated_reengagement/paper.pdf` | `/Users/jawaun/Metaphysics of Intelligence/23B_Habituated_Reengagement_2026_06_12.pdf` |
| General metric-stack framing | `papers/metric_stack_synthesis/paper.pdf` | `/Users/jawaun/Metaphysics of Intelligence/26_Metric_Stack_of_Concern_v4_2026_07_06.pdf` |
| Source failure before Suite C repair | `papers/world_responds/paper.pdf` | `/Users/jawaun/Metaphysics of Intelligence/22_World_Responds_Reengagement_Floor_2026_07_06.pdf` |
| Probe-value anxiety result | `papers/probe_value_reengagement/paper.pdf` | `/Users/jawaun/Metaphysics of Intelligence/23A_Probe_Value_Reengagement_2026_06_12.pdf` |

Optional supporting PDFs:

| Use | Repo path |
|---|---|
| Planning from concern | `papers/planning_from_concern/paper.pdf` |
| First-order self attribution | `papers/first_order_self/paper.pdf` |
| Null intervention | `papers/null_intervention/paper.pdf` |
| Structure-compatible OOD | `papers/weakness_invariance_neurips/paper.pdf`; local archive `/Users/jawaun/Metaphysics of Intelligence/Structure_Compatible_Generalization_2026_07_06/structure_compatible_generalization.pdf` |

## How To Pitch It

Use this one-sentence frame:

> This is a proxy-resistant benchmark stack for finite agents: final success is
> not enough; a suite only passes when behavior survives a causal-structure gate
> and an anti-cheat control.

Use this claim boundary:

> The current strongest suite is the long-horizon moved-bottleneck/tool
> commitment suite. Suite C re-engagement is packaged as a frontier: it has a
> positive mechanism and a caught anti-cheat failure, but it is not a terminal
> pass yet.

Do not lead with "consciousness" or "AGI." Lead with benchmark methodology:
behavior plus structure gate, proxy resistance, anti-cheat controls, JSONL rows,
summary schema, and benchmark cards.

## Where To Share It

### GitHub Release

Use GitHub as the canonical code and artifact index.

Release title:

`Causally Grounded Finite Agents Benchmark v0.1`

Release assets:

- `papers/causally_grounded_agents_benchmark/paper.pdf`
- `papers/long_horizon_bottleneck/paper.pdf`
- `papers/habituated_reengagement/paper.pdf`
- `docs/causally_grounded_agents_benchmark.md`
- `docs/causally_grounded_agents_release_schema.md`
- `docs/causally_grounded_agents_release_schema.json`
- `experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`
- `experiments/world_responds/BENCHMARK_CARD.md`
- `experiments/world_responds/results/suite_c_reengagement_2026_07_06.json`

Release notes should say:

- what the minimum pass rule is;
- which suites are hardened versus partial;
- how to run the public fixture smoke test;
- what the benchmark does not certify.

### Hugging Face Dataset

Use Hugging Face for the benchmark data card once public JSONL fixtures exist.
The dataset repository should include a `README.md` dataset card with YAML
metadata; Hugging Face renders a dataset repo README as the dataset card and
uses the YAML metadata for discoverability.

Suggested dataset repo name:

`jawauntb/causally-grounded-agents-benchmark`

Initial files:

- `README.md` dataset card;
- `schema/causally_grounded_agents_release_schema.json`;
- `suite_d_e/fixture_public_smoke_rows.jsonl`;
- `suite_d_e/fixture_public_smoke_summary.json`;
- `suite_c/suite_c_reengagement_2026_07_06.json`;
- `cards/long_horizon_bottleneck_BENCHMARK_CARD.md`;
- `cards/world_responds_BENCHMARK_CARD.md`.

Do not upload raw provider outputs, secret-bearing logs, or uncurated Modal
payloads.

Reference: Hugging Face documents dataset cards at
https://huggingface.co/docs/hub/en/datasets-cards.

### arXiv

Use arXiv for the polished benchmark paper once the abstract, related work,
limitations, and reproducibility appendix are tight. arXiv prefers source
formats such as TeX/LaTeX when source exists; PDF-only submissions are allowed
for some cases, but arXiv states that PDF generated from TeX is typically
rejected in favor of source. Include all figures in the submission package.

Primary arXiv paper to submit after polish:

- `papers/causally_grounded_agents_benchmark/paper.md`
- generated/edited PDF:
  `papers/causally_grounded_agents_benchmark/paper.pdf`

Reference:

- https://info.arxiv.org/help/submit/index.html
- https://info.arxiv.org/help/submit_pdf.html

### OpenReview Venues And Workshops

Use OpenReview venues for peer review. Prepare the OpenReview profile early:
OpenReview says profile moderation can take up to two weeks for public or
non-institutional email domains.

Best-fit venue types:

- evaluation and datasets tracks;
- agent evaluation workshops;
- benchmark/reproducibility workshops;
- ML systems or ML safety workshops if the framing is "proxy-resistant evals."

As of 2026-07-06, NeurIPS 2026 Evaluations and Datasets main deadlines have
passed: the official dates page lists May 04, 2026 for abstracts and May 06,
2026 for full papers. Treat NeurIPS E&D as a next-cycle or workshop target, not
a current main-track submission.

References:

- https://docs.openreview.net/getting-started/frequently-asked-questions/why-does-it-take-two-weeks-to-moderate-my-profile
- https://neurips.cc/Conferences/2026/Dates

## Similar Benchmark Publication Template

If you are building a similar benchmark for publication, make the public package
look like this:

```text
benchmark_name/
  README.md
  docs/
    benchmark_charter.md
    release_schema.md
    publication_sharing_map.md
  schema/
    benchmark_summary.schema.json
  experiments/
    suite_a/
      BENCHMARK_CARD.md
      README.md
      results/
        suite_a_<date>.md
        suite_a_<date>.json
  artifacts/
    suite_a/
      public_fixture_rows.jsonl
      public_fixture_summary.json
  papers/
    benchmark_paper/
      paper.md
      paper.pdf
```

Every suite should have:

- behavior gate;
- one structure-specific gate;
- one anti-cheat control;
- lower baseline;
- upper or diagnostic reference;
- JSONL rows;
- summary JSON;
- benchmark card;
- "what this does not certify" section.

The reusable minimum pass rule:

> No suite passes on final behavior alone. A pass requires behavior plus at
> least one structure-specific gate plus anti-cheat controls.

## What Not To Share First

Do not lead with:

- the entire local PDF archive;
- raw Modal payloads;
- unreviewed provider transcripts;
- local-only paths as the only source references;
- a single scalar leaderboard;
- broad claims about consciousness, AGI, or production reliability.

Those are either too noisy or invite the wrong review frame.
