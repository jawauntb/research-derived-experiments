# IDENT baseline summary

- split: `test`
- n_items: 150
- status: **pass**

## Gates

- PASS: `G1_formal_ambiguity`
- PASS: `G2_separability`
- PASS: `G3_passive_bound`
- PASS: `G4_oracle_solvability`
- PASS: `G6_nontriviality`

## Baselines

- `answer_now`: separator_acc=0.000, false_certainty=1.000, final_acc=0.500
- `random_intervention`: separator_acc=0.553, false_certainty=0.000, final_acc=0.693
- `max_output_variance`: separator_acc=1.000, false_certainty=0.000, final_acc=0.920
- `expected_information_gain`: separator_acc=1.000, false_certainty=0.000, final_acc=0.933
- `oracle_weakest_separator`: separator_acc=1.000, false_certainty=0.000, final_acc=1.000
