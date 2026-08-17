# EML US-4′ (unknown-skeleton recovery)

Does Φ still rank the fat zero target above the thin singleton when
the search process is *not* told the matching tree?

No at this bound. Blind GD on all 80 size-3 skeletons recovers both
targets from 7 skeletons. Verdict: `min_size_governs`.

Exact unweighted hits remain 2 vs 1. That is the Gibbs control, not
the headline. Matching-skeleton GD (#483) is a different process and
stays banked.

```bash
python3 experiments/eml_us4_search/experiment.py
python3 -m unittest tests.test_eml_us4_search
```
