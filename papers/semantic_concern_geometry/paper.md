# A Semantic Boundary for Concern-Weighted Metric Deformation in Pretrained Transformers

This paper is a Paper B externality follow-up. It tests whether the spatial
metric-deformation result transports to real text semantics in pretrained
transformers.

The confirmatory answer is no. Across 256 seeds per family, two pretrained
encoders, classifier and JEPA-like objectives, four 20 Newsgroups targets, and
random-matched controls, the preregistered local semantic-margin gate fails in
the opposite direction:

- pooled lift vs uniform: -0.441, SE 0.007, 95% CI [-0.455, -0.427]
- pooled lift vs random matched: -0.441, SE 0.007, 95% CI [-0.455, -0.428]

Companion geometry is not null: centroid separation, kNN purity, and often
effective rank increase. But target F1 and the registered local margin decrease.
The right conclusion is that Paper B's spatial mechanism is real but not yet a
foundation-model/general-semantic result.

Build the PDF:

```bash
python scripts/build_semantic_concern_pdf.py
```

Result report:

`experiments/semantic_concern_geometry/results/semantic_concern_sweep_2026_07_02.md`

