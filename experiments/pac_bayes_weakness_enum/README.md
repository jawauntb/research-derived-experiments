# PAC-Bayes weakness enumeration

The remaining empirical gate from
`papers/weakness_invariance_neurips/pac_bayes_weakness_sketch.md`.

One reduced domain per family, `|X|=|Y|≤7`, ambient class `H=Y^X`
enumerated exactly on CPU. Groups, truths, OOD splits, mixture-weight
schedules, IID seeds, `m`, and `δ` are frozen in
`preregistration.json` and `families.py`.

Families:

| Family | `n` | `|H|` | Aligned family |
|---|---:|---:|---|
| cyclic | 7 | 823543 | `C_7` |
| dihedral | 7 | 823543 | `D_7` |
| parity | 6 | 46656 | `{id, partner-swap}` |
| color | 6 | 46656 | `S_6` |

Lanes stay split: the IID `m∈{8,32}` certificates are not used to
certify the prefix/coset OOD split. Langford–Seeger–Maurer is a
numerical plug-in, not a Lean theorem. Neural posteriors stay out.

Run:

```bash
python3 experiments/pac_bayes_weakness_enum/experiment.py
python3 -m unittest tests.test_pac_bayes_weakness_enum
```

Reproduce: `python scripts/regen.py pac_bayes_weakness_enum`

Python-enumerated. Not Lean-verified. Not Paper G.
