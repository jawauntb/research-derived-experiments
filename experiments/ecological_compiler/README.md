# Ecological Compiler Study I

This package tests the first empirical question raised by the ecological
compiler argument: does reliance on fishing predict political complexity across
preindustrial societies once major ecological, geographic, subsistence, and
shared-history alternatives are measured?

The claim ceiling is descriptive. The Ethnographic Atlas contains no direct
measure of nutrient status, cognition, dopamine, or maritime network position.
The run therefore cannot establish a fish-to-cognition mechanism or explain a
continental hierarchy.

## Reproduce

Clone the exact public data inputs into the gitignored artifact store:

```bash
mkdir -p artifacts/ecological_compiler
git clone https://github.com/D-PLACE/dplace-dataset-ea.git \
  artifacts/ecological_compiler/dplace-dataset-ea
git -C artifacts/ecological_compiler/dplace-dataset-ea checkout \
  5aa46eea62815daa283ac67cc757065a1b3be16e
git clone https://github.com/D-PLACE/dplace-data.git \
  artifacts/ecological_compiler/dplace-data
git -C artifacts/ecological_compiler/dplace-data checkout \
  9bfed2c8c206be00f55f71516f262bbca2234e5a
```

Then run:

```bash
uv run --no-project --python 3.12 \
  --with numpy==2.5.1 --with scipy==1.18.0 --with matplotlib==3.11.0 \
  python3 -m experiments.ecological_compiler.analysis
uv run --no-project --python 3.12 \
  --with numpy==2.5.1 --with scipy==1.18.0 --with pytest==9.1.1 \
  python3 -m pytest tests/test_ecological_compiler.py -q
```

Raw source data and bootstrap draws stay under `artifacts/`. Public summaries,
the registered figure, and every failed gate are written to `results/`.

## Registered interpretation

- M0 measures the unadjusted association.
- M1 adds pre-treatment subsistence, ecology, geography, focal-year, and region
  controls.
- M2 adds settlement and population variables that may be mediators.
- Family and spatial block resampling test dependence; they do not turn the
  cross-sectional design into a causal experiment.

Pre-registration: `experiments/ecological_compiler/preregistration.md`.
