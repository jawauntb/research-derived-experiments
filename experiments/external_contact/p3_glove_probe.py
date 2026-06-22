#!/usr/bin/env python3
"""External Contact P3 — concept geometry on the external GloVe embedding family.

Pre-registration: docs/external_contact_preregistration.md (Prediction 3).
This is the Tier-A harness: it computes P3a (within- vs across-category cosine
margin + clustering NMI), P3b (paraphrase-weakness vs wrong-orbit gap), and P3c
(cross-model RSA), all after the All-but-the-Top anisotropy correction, in pure
Python standard library (no numpy).

IMPORTANT — this is INFRASTRUCTURE, not a result:

  * With `--glove PATH` it runs the real external test against public GloVe
    vectors (plain text: `word v1 v2 ... vd` per line). Stanford GloVe / fastText
    are external, public, and were not built by this lab.
  * With `--self-test` it runs on SYNTHETIC vectors with planted block structure
    purely to verify the math (centering removes anisotropy; cosine/RSA/NMI are
    correct). A self-test pass is NOT evidence for the concept-geometry claim.
  * With neither, it prints its status and exits without producing any claim.

As of 2026-06-18 the run environment has no GloVe vectors and network egress is
blocked (Stanford/HF/PyPI 403), so the real external test cannot be run here yet;
this harness makes it a one-command run the moment vectors are available.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
from pathlib import Path
from statistics import mean

Vector = list[float]

CONCEPT_SET = Path("experiments/concept_geometry/concept_set.json")
PARAPHRASES = Path("experiments/concept_geometry/concept_paraphrases.json")


# ----------------------------- linear algebra (stdlib) -----------------------------
def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: Vector) -> float:
    return math.sqrt(dot(a, a))


def cosine(a: Vector, b: Vector) -> float:
    na, nb = norm(a), norm(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot(a, b) / (na * nb)


def vsub(a: Vector, b: Vector) -> Vector:
    return [x - y for x, y in zip(a, b)]


def vmean(vectors: list[Vector]) -> Vector:
    n = len(vectors)
    dim = len(vectors[0])
    return [sum(v[i] for v in vectors) / n for i in range(dim)]


def top_principal_component(centered: list[Vector], iters: int = 100) -> Vector:
    """Top eigenvector of the covariance, via power iteration (stdlib)."""
    dim = len(centered[0])
    rng = random.Random(20260618)
    v = [rng.gauss(0, 1) for _ in range(dim)]
    n = norm(v) or 1.0
    v = [x / n for x in v]
    for _ in range(iters):
        # w = sum_i (x_i . v) x_i
        w = [0.0] * dim
        for x in centered:
            c = dot(x, v)
            for i in range(dim):
                w[i] += c * x[i]
        nw = norm(w)
        if nw == 0.0:
            break
        v = [x / nw for x in w]
    return v


def all_but_the_top(vectors: dict[str, Vector]) -> dict[str, Vector]:
    """Subtract the mean and remove the top principal component (Mu et al., 2018)."""
    keys = list(vectors)
    mat = [vectors[k] for k in keys]
    mu = vmean(mat)
    centered = [vsub(v, mu) for v in mat]
    pc = top_principal_component(centered)
    out = {}
    for k, v in zip(keys, centered):
        proj = dot(v, pc)
        out[k] = [v[i] - proj * pc[i] for i in range(len(v))]
    return out


# ----------------------------- ranking / info metrics -----------------------------
def rankdata(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(a: list[float], b: list[float]) -> float:
    ra, rb = rankdata(a), rankdata(b)
    mra, mrb = mean(ra), mean(rb)
    num = sum((x - mra) * (y - mrb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - mra) ** 2 for x in ra) * sum((y - mrb) ** 2 for y in rb))
    return num / den if den else 0.0


def nmi(true: list[str], pred: list[int]) -> float:
    n = len(true)
    from collections import Counter

    ct, cp = Counter(true), Counter(pred)

    def entropy(counter: Counter) -> float:
        return -sum((c / n) * math.log(c / n) for c in counter.values() if c)

    joint: dict[tuple, int] = {}
    for t, p in zip(true, pred):
        joint[(t, p)] = joint.get((t, p), 0) + 1
    mi = 0.0
    for (t, p), c in joint.items():
        pxy = c / n
        mi += pxy * math.log(pxy / ((ct[t] / n) * (cp[p] / n)))
    ht, hp = entropy(ct), entropy(cp)
    return mi / math.sqrt(ht * hp) if ht > 0 and hp > 0 else 0.0


def agglomerative(vectors: list[Vector], k: int) -> list[int]:
    """Average-linkage agglomerative clustering to k clusters (cosine distance)."""
    clusters: list[list[int]] = [[i] for i in range(len(vectors))]

    def cdist(a: list[int], b: list[int]) -> float:
        return mean(1.0 - cosine(vectors[i], vectors[j]) for i in a for j in b)

    while len(clusters) > k:
        best = None
        bi = bj = -1
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = cdist(clusters[i], clusters[j])
                if best is None or d < best:
                    best, bi, bj = d, i, j
        clusters[bi] = clusters[bi] + clusters[bj]
        del clusters[bj]
    labels = [0] * len(vectors)
    for cid, members in enumerate(clusters):
        for m in members:
            labels[m] = cid
    return labels


# ----------------------------- glove / pooling -----------------------------
def tokenize(text: str) -> list[str]:
    # Drop a leading "label:" gloss prefix if present, keep alphabetic tokens.
    text = text.split(":", 1)[-1] if ":" in text else text
    return [t for t in re.findall(r"[a-zA-Z]+", text.lower())]


def load_glove(path: Path, needed: set[str]) -> dict[str, Vector]:
    vecs: dict[str, Vector] = {}
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            sp = line.rstrip().split(" ")
            if sp[0] in needed:
                vecs[sp[0]] = [float(x) for x in sp[1:]]
    return vecs


def pool(tokens: list[str], glove: dict[str, Vector]) -> Vector | None:
    present = [glove[t] for t in tokens if t in glove]
    return vmean(present) if present else None


# ----------------------------- statistics -----------------------------
def within_across_margin(vecs: dict[str, Vector], category: dict[str, str]) -> float:
    ids = list(vecs)
    within, across = [], []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            c = cosine(vecs[ids[i]], vecs[ids[j]])
            (within if category[ids[i]] == category[ids[j]] else across).append(c)
    return mean(within) - mean(across)


def paraphrase_gap(variant_vecs: dict[str, list[Vector]]) -> float:
    ids = list(variant_vecs)
    weak, wrong = [], []
    for cid in ids:
        vs = variant_vecs[cid]
        weak += [cosine(vs[i], vs[j]) for i in range(len(vs)) for j in range(i + 1, len(vs))]
        for other in ids:
            if other == cid:
                continue
            wrong += [cosine(a, b) for a in vs for b in variant_vecs[other]]
    return mean(weak) - mean(wrong)


# ----------------------------- self-test (synthetic) -----------------------------
def self_test() -> dict:
    """Validate the math on synthetic vectors with planted block structure.

    NOT a scientific result. Builds 6 categories x 4 concepts where each concept
    is its category center + small noise, plus a large shared anisotropy bias
    added to every vector. The bias makes raw cosine near-uniform (small margin);
    All-but-the-Top should remove it and expose the block structure.
    """
    rng = random.Random(7)
    dim = 50
    bias = [rng.gauss(0, 1) * 5 for _ in range(dim)]  # dominant shared component
    cats = [f"cat{c}" for c in range(6)]
    centers = {c: [rng.gauss(0, 1) for _ in range(dim)] for c in cats}
    vecs, category, variant_vecs = {}, {}, {}
    for c in cats:
        for k in range(4):
            cid = f"{c}_{k}"
            base = [centers[c][i] + rng.gauss(0, 0.2) for i in range(dim)]
            vecs[cid] = [base[i] + bias[i] for i in range(dim)]
            category[cid] = c
            variant_vecs[cid] = [[base[i] + bias[i] + rng.gauss(0, 0.1) for i in range(dim)] for _ in range(3)]

    raw_margin = within_across_margin(vecs, category)
    centered = all_but_the_top(vecs)
    cen_margin = within_across_margin(centered, category)

    cen_variants = all_but_the_top({f"{c}#{i}": v for c, vs in variant_vecs.items() for i, v in enumerate(vs)})
    regrouped: dict[str, list[Vector]] = {}
    for key, v in cen_variants.items():
        regrouped.setdefault(key.split("#")[0], []).append(v)
    gap = paraphrase_gap(regrouped)

    labels = agglomerative([centered[k] for k in centered], 6)
    nmi_score = nmi([category[k] for k in centered], labels)

    checks = {
        "centering_beats_raw_margin": cen_margin > raw_margin,
        "centered_margin_positive": cen_margin > 0.1,
        "paraphrase_gap_positive": gap > 0.1,
        "clustering_recovers_blocks": nmi_score > 0.5,
    }
    return {
        "kind": "SELF_TEST (synthetic, NOT a scientific result)",
        "raw_margin": raw_margin,
        "centered_margin": cen_margin,
        "paraphrase_gap_centered": gap,
        "nmi": nmi_score,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


# ----------------------------- real external run -----------------------------
def run_glove(glove_path: Path, extra_paths: list[tuple[str, Path]]) -> dict:
    """P3 external run.

    `glove_path` carries P3a / P3b (within-across margin, NMI, paraphrase gap).
    `extra_paths` is a list of (label, path) pairs for additional external
    embedding families used in the P3c pairwise cross-model RSA. The primary
    family (`glove_path`) is included in the RSA panel as ``"glove"``.

    P3c-3way amendment (preregistered in the cloud agent's handoff before
    these vectors were fetched): when >= 3 external families are present, the
    pass threshold is the MINIMUM pairwise RSA >= 0.6 -- every pair must agree
    on the relational geometry, not just the original GloVe-300d / GloVe-100d
    pair. This strictly tightens the original P3c.
    """
    concepts = json.loads(CONCEPT_SET.read_text())
    paraphrases = {p["id"]: p["variants"] for p in json.loads(PARAPHRASES.read_text())}

    needed: set[str] = set()
    for c in concepts:
        needed.update(tokenize(c["label"]))
        for v in paraphrases.get(c["id"], []):
            needed.update(tokenize(v))

    def build(path: Path) -> tuple[dict[str, Vector], dict[str, str], dict[str, list[Vector]], list[str]]:
        glove = load_glove(path, needed)
        cvecs, category, variant_vecs = {}, {}, {}
        missing = []
        for c in concepts:
            cv = pool(tokenize(c["label"]), glove)
            if cv is None:
                missing.append(c["id"])
                continue
            cvecs[c["id"]] = cv
            category[c["id"]] = c["category"]
            vv = [pool(tokenize(v), glove) for v in paraphrases.get(c["id"], [])]
            variant_vecs[c["id"]] = [v for v in vv if v is not None]
        return cvecs, category, variant_vecs, missing

    cvecs, category, variant_vecs, missing = build(glove_path)
    cen = all_but_the_top(cvecs)

    raw_margin = within_across_margin(cvecs, category)
    cen_margin = within_across_margin(cen, category)
    labels = agglomerative([cen[k] for k in cen], min(6, len(cen)))
    nmi_score = nmi([category[k] for k in cen], labels)

    # P3b: centered variant vectors per concept.
    flat = {f"{cid}#{i}": v for cid, vs in variant_vecs.items() for i, v in enumerate(vs)}
    cen_flat = all_but_the_top(flat)
    regrouped: dict[str, list[Vector]] = {}
    for key, v in cen_flat.items():
        regrouped.setdefault(key.split("#")[0], []).append(v)
    raw_gap = paraphrase_gap(variant_vecs)
    cen_gap = paraphrase_gap(regrouped)

    result = {
        "kind": "REAL external GloVe run",
        "glove": str(glove_path),
        "n_concepts": len(cvecs),
        "missing_concepts": missing,
        "P3a_within_across_margin_raw": raw_margin,
        "P3a_within_across_margin_centered": cen_margin,
        "P3a_nmi_clusters_vs_categories": nmi_score,
        "P3a_pass": cen_margin >= 0.10 and nmi_score >= 0.25,
        "P3b_paraphrase_gap_raw": raw_gap,
        "P3b_paraphrase_gap_centered": cen_gap,
        "P3b_pass": cen_gap >= 0.15,
    }

    if extra_paths:
        # Build the panel of (label, concept-vectors) for the primary + every extra family.
        family_vecs: list[tuple[str, dict[str, Vector], list[str]]] = [
            ("glove", cvecs, list(missing))
        ]
        for label, p in extra_paths:
            cv_extra, _, _, m_extra = build(p)
            family_vecs.append((label, cv_extra, m_extra))

        # Concepts present in EVERY family (intersection over families' keys).
        shared = list(family_vecs[0][1])
        for _, cv, _ in family_vecs[1:]:
            shared = [k for k in shared if k in cv]
        shared.sort()

        # All-but-the-Top each family on the shared concept set.
        centered_per_family: list[tuple[str, dict[str, Vector]]] = []
        for label, cv, _ in family_vecs:
            centered_per_family.append((label, all_but_the_top({k: cv[k] for k in shared})))

        # Pairwise off-diagonal cosine matrices for every family, then Spearman RSA.
        def offdiag_cosines(vecs: dict[str, Vector]) -> list[float]:
            out: list[float] = []
            for i in range(len(shared)):
                for j in range(i + 1, len(shared)):
                    out.append(cosine(vecs[shared[i]], vecs[shared[j]]))
            return out

        cosines = {label: offdiag_cosines(vv) for label, vv in centered_per_family}
        pairs = []
        rsa_values: list[float] = []
        for i in range(len(centered_per_family)):
            for j in range(i + 1, len(centered_per_family)):
                la = centered_per_family[i][0]
                lb = centered_per_family[j][0]
                rho = spearman(cosines[la], cosines[lb])
                pairs.append((la, lb, rho))
                rsa_values.append(rho)

        n_families = len(centered_per_family)
        result["P3c_n_families"] = n_families
        result["P3c_families"] = [label for label, _ in centered_per_family]
        result["P3c_shared_concepts"] = shared
        result["P3c_pairwise_rsa"] = [
            {"a": a, "b": b, "rsa": rho} for a, b, rho in pairs
        ]
        result["P3c_missing_per_family"] = {label: m for label, _, m in family_vecs}
        if n_families == 2:
            result["P3c_cross_model_rsa"] = rsa_values[0]
            result["P3c_pass"] = rsa_values[0] >= 0.6
        else:
            result["P3c_min_pairwise_rsa"] = min(rsa_values) if rsa_values else None
            result["P3c_mean_pairwise_rsa"] = sum(rsa_values) / len(rsa_values) if rsa_values else None
            result["P3c_pass"] = bool(rsa_values) and min(rsa_values) >= 0.6
            result["P3c_threshold"] = (
                "P3c-3way: min pairwise RSA across all 3+ external families >= 0.6 (strictly "
                "tightens the original P3c, which only required GloVe-300d vs GloVe-100d RSA >= 0.6)"
            )

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glove", type=Path, help="Primary external vectors (P3a/P3b). Plain text 'word v1 ... vd' per line.")
    parser.add_argument("--glove2", type=Path, help="Second external family for the P3c cross-model RSA.")
    parser.add_argument(
        "--glove3", type=Path,
        help="Third external family for the P3c-3way amendment. Triggers the strict pass rule: "
        "min pairwise RSA across all three families >= 0.6.",
    )
    parser.add_argument("--label2", default="glove2", help="Label for the --glove2 family in the P3c panel (e.g. 'glove-100d').")
    parser.add_argument("--label3", default="fasttext", help="Label for the --glove3 family in the P3c panel.")
    parser.add_argument("--self-test", action="store_true", help="Validate the math on synthetic vectors.")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if args.self_test:
        payload = self_test()
    elif args.glove is not None:
        extras: list[tuple[str, Path]] = []
        if args.glove2 is not None:
            extras.append((args.label2, args.glove2))
        if args.glove3 is not None:
            extras.append((args.label3, args.glove3))
        payload = run_glove(args.glove, extras)
    else:
        payload = {
            "kind": "HARNESS ONLY — no result",
            "message": (
                "No external vectors supplied. This is infrastructure, not a result. "
                "Run `--self-test` to validate the math, or `--glove glove.6B.300d.txt "
                "[--glove2 glove.6B.100d.txt] [--glove3 fasttext.subset.txt]` to run the "
                "real external P3 test."
            ),
        }

    output = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
