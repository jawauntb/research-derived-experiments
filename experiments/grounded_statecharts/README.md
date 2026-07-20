# Grounded Statecharts: Deterministic Fixture Release

This package is the first executable slice of the grounded-harness portfolio.
It records a typed append-only event stream, captures a pre-commit checkpoint,
proves exact no-op replay, and changes only the completion guard in a paired
counterfactual replay.

The committed fixture intentionally reports tool success without creating its
required artifact. A G0 self-report guard falsely authorizes `commit`. The
paired replay substitutes one G3 artifact-digest guard, routes the same run to
`repair`, creates the artifact, verifies it, and then commits.

## Run

From the repository root:

```bash
python3 -m experiments.grounded_statecharts.run_fixture
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

## Verify

```bash
python3 -m pytest -q tests/test_grounded_statecharts.py
```

## Scope boundary

This is a deterministic fixture result, not a benchmark result over agents or
tasks. The next expansion should add Constraint Transport task families while
preserving this replay identity gate. Counterfactual search remains a thin
pilot until controlled fault fixtures exist; unlearning remains deferred until
causal-use testing is operational.
