# Phase 5 live-model smoke study

This is a preregistered five-case operational integration test. It uses the
configured untrusted proposer, a hash-verified frozen Replogle 2022 pilot
world, and the deterministic verifier. It sets `max_repair_attempts=0`, so
the study does not make repair calls or claim repair effectiveness.
The runner verifies the committed question manifest's SHA-256 and requires
exactly the six preregistered pilot sources, so a changed question set or data
world cannot be labelled as this study.

Run a no-network prerequisite check first:

```bash
cd "/Users/jawaun/Research Derived Experiments/bio-claim-firewall"
uv run --with openai --with pyyaml --with jinja2 --with pydantic \
  python -m eval.smoke --preflight
```

The default data root is `bio-claim-firewall/data/`. In an isolated worktree,
point `--data-root` at a separately reproduced pilot-world cache. A successful
run writes an append-only trajectory JSONL file and a compact summary beneath
`eval/smoke_trajectories/`; both are local run artifacts and ignored by Git.
The run id is reserved atomically; if a process stops after reservation, choose
a fresh run id rather than reusing the partial receipt path.

See [`docs/preregistration/bio_claim_firewall_phase_5_smoke_2026-09-01.md`](../../../docs/preregistration/bio_claim_firewall_phase_5_smoke_2026-09-01.md)
for the decision boundary and fatal gates.
