# Grounded Statecharts and Constraint Transport Fixtures

This package is the first executable slice of the grounded-harness portfolio.
It records a typed append-only event stream, captures a pre-commit checkpoint,
proves exact no-op replay, and changes only the completion guard in a paired
counterfactual replay.

The committed fixture intentionally reports tool success without creating its
required artifact. A G0 self-report guard falsely authorizes `commit`. The
paired replay substitutes one G3 artifact-digest guard, routes the same run to
`repair`, creates the artifact, verifies it, and then commits.

The same dependency-free package now includes the first Constraint Transport
diagnostic. It carries immutable approval and evidence constraints through one
to four delegation levels, checks hash-linked envelope lineage, rejects
constraint removal and capability widening, and reports raw task success
separately from zero-violation joint success.

## Run

From the repository root:

```bash
python3 -m experiments.grounded_statecharts.run_fixture
python3 -m experiments.grounded_statecharts.run_constraint_transport
```

The command has no third-party or provider dependency. It regenerates the
public-safe replay bundle under `results/`:

- `summary.json`: exit gates, compact metrics, manifest/checkpoint hashes, and
  the allowed claim;
- `checkpoint.json`: the serialized pre-verification checkpoint;
- `original.jsonl`, `noop_replay.jsonl`, `guarded_replay.jsonl`: typed event
  streams;
- `replay.html`: static side-by-side visual explanation of false-completion
  prevention.

The transport command writes `results/constraint_transport/`:

- `summary.json`: depth-wise survival, violation, raw utility, and joint-success
  metrics plus the exact allowed claim;
- `episodes.jsonl`: one final outcome per condition, family, and depth;
- `lineage.jsonl`: per-delegation envelope lineage and known fault locations;
- `replay.html`: compact depth-wise comparison, not a general dashboard.

## Verify

```bash
python3 -m pytest -q tests/test_grounded_statecharts.py
```

## Scope boundary

These are deterministic fixture results, not estimates over live agents or a
confirmatory Constraint Transport benchmark. The controlled prompt condition
contains a registered summary-loss fault and does not represent optimized
verbatim copying. Its six localized failures are suitable inputs for the thin
Counterfactual Harness Search pilot; unlearning remains deferred until
causal-use testing is operational.
