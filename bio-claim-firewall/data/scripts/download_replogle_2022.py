#!/usr/bin/env python3
"""Download the small, processed effect-summary files from Replogle et al. 2022.

Paper: "Mapping information-rich genotype-phenotype landscapes with
genome-scale Perturb-seq", Replogle, J.M. et al., Cell 185(14):2559-2575.e28
(2022). DOI: 10.1016/j.cell.2022.05.013 (resolves via https://doi.org/... at
download time).

The full dataset (raw + normalized single-cell AnnData files) is ~10-80GB
and is NOT downloaded -- see this repo's task brief. Reading `.h5ad` files
also needs `anndata`/`h5py`, neither of which is an existing project
dependency, so h5ad sources are out of reach without adding a new
dependency (forbidden). Instead this script pulls the authors' own **small,
already-processed** "commonly requested supplemental files" release
(Figshare article 21632564, CC0-1.0), which ships plain CSV/CSV.GZ:

  - `clustered_mean_gene_expression_figs2-4.csv.gz` (~38MB): a
    gene-transcript x perturbation matrix of gemgroup Z-normalized mean
    pseudobulk expression (deviation from control), used to draw Figures 2
    and 4 of the paper. This is the K562 genome-scale (K562_gwps, day 8)
    screen. IMPORTANT: this is a Z-SCORE matrix, not a log2 fold-change
    table -- there is no publicly hosted per-perturbation-per-gene log2FC
    "MAGeCK-like" table for this dataset, so `sample_replogle_2022.py`
    honestly labels its derived records `magnitude_scale: "zscore_mean_expression"`,
    not `"log2fc"`.
  - `annotated_embedding_coordinates.csv` (~230KB): per-perturbation
    metadata including the Anderson-Darling differential-expression gene
    count (`anderson-darling de genes`), used by `sample_replogle_2022.py`
    to pick the top perturbations by phenotype strength without needing the
    488MB full Anderson-Darling p-value table (which is intentionally NOT
    downloaded -- it alone would exceed a reasonable single-source budget).

License: CC0 1.0 ("Public domain dedication"), as declared on the Figshare
article itself (https://plus.figshare.com/articles/dataset/.../21632564).

Output: data/raw/perturbseq.replogle_2022/
  clustered_mean_gene_expression_figs2-4.csv.gz
  annotated_embedding_coordinates.csv
"""

from __future__ import annotations

import json

from _common import (
    RAW_DIR,
    fetch_json,
    fetch_to_file,
    log,
    now_iso,
    sha256_file,
    write_license_text,
)

SOURCE = "perturbseq.replogle_2022"
FIGSHARE_ARTICLE_URL = "https://api.figshare.com/v2/articles/21632564"
LICENSE_TAG = "CC0-1.0"
FIGSHARE_HTML_URL = (
    "https://plus.figshare.com/articles/dataset/"
    "_Mapping_information-rich_genotype-phenotype_landscapes_with_genome-scale_"
    "Perturb-seq_Replogle_et_al_2022_-_commonly_requested_supplemental_files_/21632564"
)
WANTED_FILES = {
    "clustered_mean_gene_expression_figs2-4.csv.gz",
    "annotated_embedding_coordinates.csv",
}

RAW_OUT = RAW_DIR / SOURCE


def main() -> int:
    retrieved_at = now_iso()
    RAW_OUT.mkdir(parents=True, exist_ok=True)

    log(f"fetching Figshare article metadata: {FIGSHARE_ARTICLE_URL}")
    article = fetch_json(FIGSHARE_ARTICLE_URL, timeout=30)
    license_info = article.get("license", {})
    log(f"Figshare-reported license: {license_info}")

    downloaded = {}
    for file_info in article.get("files", []):
        name = file_info["name"]
        if name not in WANTED_FILES:
            continue
        url = file_info["download_url"]
        dest = RAW_OUT / name
        log(f"downloading {name} ({file_info['size']} bytes) from {url}")
        fetch_to_file(url, dest, timeout=180)
        downloaded[name] = sha256_file(dest)
        log(f"  sha256={downloaded[name]}  size_on_disk={dest.stat().st_size}")

    missing = WANTED_FILES - downloaded.keys()
    if missing:
        raise SystemExit(
            f"expected files not found in Figshare article 21632564: {missing}"
        )

    write_license_text(
        SOURCE,
        "Replogle et al. 2022 supplemental data license: Creative Commons Public Domain Dedication (CC0)",
        FIGSHARE_HTML_URL,
        "The Figshare article's own license metadata declares CC0 "
        f"({license_info.get('name', 'CC0')}, {license_info.get('url', '')}). "
        "See data/LICENSES/CC0-1.0.txt for the full CC0 legal text. "
        "Primary study citation: Replogle, J.M. et al. 'Mapping information-rich "
        "genotype-phenotype landscapes with genome-scale Perturb-seq.' Cell 185(14):2559-2575.e28 "
        "(2022). DOI: 10.1016/j.cell.2022.05.013.",
    )

    # Provenance sidecar for sample_replogle_2022.py / build_manifests.py.
    provenance = {
        "source": SOURCE,
        "figshare_article_id": 21632564,
        "figshare_article_url": FIGSHARE_HTML_URL,
        "retrieved_at": retrieved_at,
        "license": LICENSE_TAG,
        "files": {name: {"sha256": digest} for name, digest in downloaded.items()},
        "study_doi": "10.1016/j.cell.2022.05.013",
        "study_citation": (
            "Replogle, J.M. et al. Mapping information-rich genotype-phenotype landscapes "
            "with genome-scale Perturb-seq. Cell 185(14):2559-2575.e28 (2022)."
        ),
    }
    (RAW_OUT / "_provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    log(f"downloaded {len(downloaded)} files to {RAW_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
