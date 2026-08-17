# EML US-4′ (frozen-leaf discrete rewrite)

Unknown-skeleton GD could retune every `1`-leaf, so both targets
became reachable from 7 trees. This process freezes leaves. Moves are
flip one leaf or swap one internal pair. Greedy descent from every
size-3 start.

Exact unweighted hits stay 2 vs 1. That is the control. The claim is
the extra-basin ranking: zero 43, thin 28, verdict `phi_holds`.

All extras terminate on an exact registered formula. No grid-only hits.

```bash
python3 experiments/eml_us4_discrete/experiment.py
python3 -m unittest tests.test_eml_us4_discrete
```
