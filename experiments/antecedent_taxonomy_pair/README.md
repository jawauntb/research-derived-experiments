# Antecedent-Taxonomy Pair (Theorem SA-1 witness)

Companion instrument for
[`papers/sufficient_antecedents/paper.md`](../../papers/sufficient_antecedents/paper.md).

Hypothesis: Theorem SA-1 (Antecedent taxonomy) says four canonical
inductive-bias regimes — linear ICA, sparse-linear ICA, auxiliary-variable
iVAE, interventional CRL — each supply Conditions (I) local separation
and (II) cross-`u` coherence, and their finest common refinement equals
the latent `Z`-partition (or refines it, for the interventional case).

Method: on the 4-bit Boolean world of Instrument 4, enumerate each
antecedent's local screens exactly, compute the finest common
refinement, and compare to the ground-truth `Z`-partition.

Pre-registered gates (all four pass):

- `sa1_local_separation_at_every_antecedent`: each antecedent's local
  screens are non-trivial partitions of X.
- `sa1_cross_u_intersection_refines_true_Z`: the intersection refines
  the true `Z`-partition at every antecedent.
- `sa1_nontrivial_intersections_equal_true_Z`: for the three antecedents
  whose local screens do not already reveal `Z` observationally
  (LinearICA, SparseLinearICA, AuxIVAE), the intersection equals `Z`
  exactly.
- `sa1_interventional_intersection_refines_true_Z`: for the
  InterventionalCRL antecedent (which has an observational screen
  revealing `Z` directly), the intersection refines `Z`.

Result: all four gates pass exactly. Every antecedent's finest common
refinement equals the true `Z`, confirming that each row of the taxonomy
table populates Theorem SA-1's antecedent in the specific quantitative
sense the theorem requires.

Run:

```bash
python3 experiments/antecedent_taxonomy_pair/experiment.py
```
