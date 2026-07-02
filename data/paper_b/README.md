# Paper B Aggregate CSV Snapshots

These CSV files are committed aggregate rows for the 2026-07-02 Paper B spatial
and semantic-boundary sweeps. They intentionally omit raw Modal logs and nested
per-class text metrics, but retain the per-run fields needed to recompute the
reported bootstrap summaries without rerunning the full jobs.

- `reward_location_sweep_2026_07_02_rows.csv`: 3,456 spatial rows, including
  matched uniform-control and concern-weighted rows for 64 seeds, three
  architectures, and nine registered locations.
- `semantic_concern_sweep_2026_07_02_rows.csv`: 12,288 semantic rows from the
  two 128-seed Modal waves, covering DistilBERT/MiniLM, classifier/JEPA-like
  objectives, concern/uniform/random-matched conditions, and four registered
  20 Newsgroups targets.

Recompute the paper summaries with:

```bash
python scripts/reproduce_paperB_stats.py
```
