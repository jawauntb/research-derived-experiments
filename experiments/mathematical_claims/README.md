# Mathematical assumption audit (M-201)

This local CPU experiment makes the assumptions behind the core theorem bridge
executable. Each row in `theorem_assumption_matrix.json` has one satisfying
example and one case where the named assumption or bridge predicate fails.
This is a consistency audit of the assumptions, not a proof that any assumption
is necessary for a broader theorem or that each failure case is minimal.

Run the deterministic suite from the repository root:

```bash
python experiments/mathematical_claims/experiment.py
```

The runner writes `results/mathematical_claims_summary.json`.  It contains no
timestamps, random draws, or host paths, so rerunning it produces identical
bytes.  The package uses only the Python standard library.

Assumption families audited: block disjointness, equal block mass, complete
block coverage, coherent output action, bounded transport loss, gauge
separation, and nonzero commitment effect.
