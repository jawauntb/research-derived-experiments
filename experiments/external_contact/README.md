# External Contact

Tests of the program's claims against systems **the lab did not build**.
Pre-registration: [`docs/external_contact_preregistration.md`](../../docs/external_contact_preregistration.md).

The run environment (verified 2026-06-18) has **no API keys and blocked network
egress** (Stanford/HuggingFace/PyPI return 403). Each prediction therefore has a
Tier A (offline, stdlib-only) and Tier B (fetch-when-unblocked) recipe.

## P3 — concept geometry on external GloVe vectors

`p3_glove_probe.py` is the Tier-A harness for Prediction 3. Pure standard
library (no numpy). It computes, after the All-but-the-Top anisotropy
correction:

- **P3a** within- vs across-category cosine margin + clustering NMI,
- **P3b** paraphrase-weakness vs wrong-orbit gap,
- **P3c** cross-model RSA between two GloVe dimensionalities.

**This is infrastructure, not a result.** It produces a scientific claim only
when fed real external vectors:

```bash
# Validate the math on synthetic vectors (NOT a scientific result):
python3 -m experiments.external_contact.p3_glove_probe --self-test

# Real external test (once GloVe vectors are available; egress was 403-blocked):
python3 -m experiments.external_contact.p3_glove_probe \
    --glove glove.6B.300d.txt --glove2 glove.6B.100d.txt \
    --out artifacts/external_contact/p3_glove.json
```

Reuses the committed `experiments/concept_geometry/concept_set.json` and
`concept_paraphrases.json`. Raw GloVe tables stay out of git (track policy:
"raw embeddings stay local").

P1 (weakness→OOD on Pythia) and P2 (uncertainty≠error on published ensemble/BALD
curves) remain Tier-B/transcription tasks pending network egress or vendored
public tables; see the pre-registration.
