#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modal sweep for semantic concern geometry in pretrained transformers.

The experiment asks whether a semantic loss-weight intervention moves a
representation-geometry effect to the upweighted class in a non-spatial text
setting. See `papers/semantic_concern_geometry/preregistration.md`.

Smoke:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
      uvx --python 3.12 --from modal modal run \\
        experiments/semantic_concern_geometry/modal_semantic_concern_sweep.py \\
        --seeds 1 --steps 4 --models sentence-transformers/all-MiniLM-L6-v2 \\
        --objectives classifier --out artifacts/semantic_concern_geometry/smoke.json

Scale:

    doppler --scope /Users/jawaun/superoptimizers run -- \\
      uvx --python 3.12 --from modal modal run \\
        experiments/semantic_concern_geometry/modal_semantic_concern_sweep.py \\
        --seeds 64 --steps 90 --batch-size 32 --target-se 0.02 \\
        --out artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02.json
"""

from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")

DEFAULT_MODELS = (
    "sentence-transformers/all-MiniLM-L6-v2",
    "distilbert-base-uncased",
)

IMAGE = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "torch>=2.5,<2.8",
        "numpy>=1.26,<2.2",
        "scikit-learn>=1.4,<1.8",
        "transformers>=4.45,<5",
        "accelerate>=0.30,<2",
    )
    .run_commands(
        "python - <<'PY'\n"
        "from transformers import AutoModel, AutoTokenizer\n"
        f"models = {list(DEFAULT_MODELS)!r}\n"
        "for model_id in models:\n"
        "    AutoTokenizer.from_pretrained(model_id)\n"
        "    AutoModel.from_pretrained(model_id)\n"
        "PY"
    )
)

app = modal.App(name="research-derived-semantic-concern-geometry")

REGISTERED_CATEGORIES = [
    "sci.space",
    "sci.med",
    "rec.sport.hockey",
    "comp.graphics",
]


def _slug(text: str) -> str:
    return text.replace("/", "__").replace("-", "_").replace(".", "_")


def _synthetic_fallback(seed: int, train_per_class: int, test_per_class: int) -> dict[str, Any]:
    import numpy as np

    rng = np.random.default_rng(seed)
    topics = {
        "sci.space": ["orbit", "telescope", "lunar", "rocket", "cosmos", "satellite"],
        "sci.med": ["clinic", "therapy", "immune", "diagnosis", "patient", "dosage"],
        "rec.sport.hockey": ["rink", "goalie", "puck", "skater", "playoff", "stick"],
        "comp.graphics": ["render", "shader", "pixel", "mesh", "texture", "vector"],
    }
    templates = [
        "A discussion about {a}, {b}, and {c} in a detailed technical forum.",
        "The article compares {a} with {b} while answering questions about {c}.",
        "Several participants debate whether {a} changes the interpretation of {b}.",
        "This note gives a practical example involving {a}, {b}, and {c}.",
    ]

    def make_split(n_per_class: int) -> tuple[list[str], list[int]]:
        texts: list[str] = []
        labels: list[int] = []
        for label, category in enumerate(REGISTERED_CATEGORIES):
            words = topics[category]
            for _ in range(n_per_class):
                a, b, c = rng.choice(words, size=3, replace=True)
                template = rng.choice(templates)
                texts.append(template.format(a=a, b=b, c=c))
                labels.append(label)
        order = rng.permutation(len(texts))
        return [texts[i] for i in order], [int(labels[i]) for i in order]

    train_texts, train_labels = make_split(train_per_class)
    test_texts, test_labels = make_split(test_per_class)
    return {
        "dataset_kind": "synthetic_fallback",
        "target_names": REGISTERED_CATEGORIES,
        "train_texts": train_texts,
        "train_labels": train_labels,
        "test_texts": test_texts,
        "test_labels": test_labels,
    }


def _load_dataset(seed: int, train_per_class: int, test_per_class: int, allow_fallback: bool) -> dict[str, Any]:
    import numpy as np
    from sklearn.datasets import fetch_20newsgroups

    rng = np.random.default_rng(seed)
    try:
        train = fetch_20newsgroups(
            subset="train",
            categories=REGISTERED_CATEGORIES,
            remove=("headers", "footers", "quotes"),
        )
        test = fetch_20newsgroups(
            subset="test",
            categories=REGISTERED_CATEGORIES,
            remove=("headers", "footers", "quotes"),
        )
    except Exception:
        if not allow_fallback:
            raise
        return _synthetic_fallback(seed, train_per_class, test_per_class)

    def sample_split(data, n_per_class: int) -> tuple[list[str], list[int]]:
        texts: list[str] = []
        labels: list[int] = []
        for label in range(len(data.target_names)):
            candidates = [
                i for i, y in enumerate(data.target)
                if int(y) == label and len(data.data[i].strip()) >= 80
            ]
            rng.shuffle(candidates)
            chosen = candidates[:n_per_class]
            texts.extend(data.data[i].strip().replace("\x00", " ") for i in chosen)
            labels.extend([label] * len(chosen))
        order = rng.permutation(len(texts))
        return [texts[i] for i in order], [int(labels[i]) for i in order]

    train_texts, train_labels = sample_split(train, train_per_class)
    test_texts, test_labels = sample_split(test, test_per_class)
    return {
        "dataset_kind": "20newsgroups",
        "target_names": list(train.target_names),
        "train_texts": train_texts,
        "train_labels": train_labels,
        "test_texts": test_texts,
        "test_labels": test_labels,
    }


def _mean_pool(last_hidden_state, attention_mask):
    mask = attention_mask.unsqueeze(-1).to(last_hidden_state.dtype)
    pooled = (last_hidden_state * mask).sum(1) / mask.sum(1).clamp(min=1.0)
    return pooled


def _class_metrics(embeddings, labels, logits, target_idx: int, target_names: list[str], k: int) -> dict[str, Any]:
    import numpy as np

    z = np.asarray(embeddings, dtype=float)
    y = np.asarray(labels, dtype=int)
    z = z / (np.linalg.norm(z, axis=1, keepdims=True) + 1e-9)
    sim = z @ z.T
    dist = 1.0 - sim
    np.fill_diagonal(dist, np.inf)
    classes = list(range(len(target_names)))
    margins = []
    centroid_margins = []
    purities = []
    eranks = []
    class_rows: dict[str, dict[str, float]] = {}
    centroids = []
    for c in classes:
        idx = np.flatnonzero(y == c)
        centroids.append(z[idx].mean(0))
    centroids = np.asarray(centroids)
    centroid_dist = 1.0 - centroids @ centroids.T
    np.fill_diagonal(centroid_dist, np.inf)

    for c in classes:
        idx = np.flatnonzero(y == c)
        same = y == c
        within_vals = []
        between_vals = []
        purity_vals = []
        for i in idx:
            same_dist = dist[i, same]
            same_dist = same_dist[np.isfinite(same_dist)]
            other_dist = dist[i, ~same]
            kk_same = min(k, same_dist.size)
            kk_other = min(k, other_dist.size)
            if kk_same and kk_other:
                within_vals.append(float(np.partition(same_dist, kk_same - 1)[:kk_same].mean()))
                between_vals.append(float(np.partition(other_dist, kk_other - 1)[:kk_other].mean()))
            row = dist[i].copy()
            nn = np.argsort(row)[: min(k, row.size - 1)]
            purity_vals.append(float((y[nn] == c).mean()))
        within = float(np.mean(within_vals))
        between = float(np.mean(between_vals))
        margin = between - within
        radius = float(np.mean(1.0 - z[idx] @ centroids[c]))
        centroid_margin = float(np.min(centroid_dist[c]) - radius)
        centered = z[idx] - z[idx].mean(0, keepdims=True)
        cov = centered.T @ centered / max(1, len(idx) - 1)
        eig = np.linalg.eigvalsh(cov)
        eig = np.maximum(eig, 0)
        if float(eig.sum()) <= 0:
            erank = 0.0
        else:
            p = eig / eig.sum()
            erank = float(np.exp(-(p[p > 0] * np.log(p[p > 0])).sum()) / min(len(idx) - 1, z.shape[1]))
        purity = float(np.mean(purity_vals))
        margins.append(margin)
        centroid_margins.append(centroid_margin)
        purities.append(purity)
        eranks.append(erank)
        class_rows[target_names[c]] = {
            "margin": margin,
            "centroid_margin": centroid_margin,
            "knn_purity": purity,
            "effective_rank": erank,
            "within_knn_distance": within,
            "between_knn_distance": between,
        }

    def zscore(vals: list[float]) -> list[float]:
        arr = np.asarray(vals, dtype=float)
        return list((arr - arr.mean()) / (arr.std() + 1e-9))

    margin_z = zscore(margins)
    centroid_z = zscore(centroid_margins)
    purity_z = zscore(purities)
    erank_z = zscore(eranks)
    for i, name in enumerate(target_names):
        class_rows[name].update({
            "margin_z": float(margin_z[i]),
            "centroid_margin_z": float(centroid_z[i]),
            "knn_purity_z": float(purity_z[i]),
            "effective_rank_z": float(erank_z[i]),
        })

    pred = np.asarray(logits).argmax(1)
    accuracy = float((pred == y).mean())
    target_mask = y == target_idx
    true_positive = float(((pred == target_idx) & target_mask).sum())
    false_positive = float(((pred == target_idx) & ~target_mask).sum())
    false_negative = float(((pred != target_idx) & target_mask).sum())
    precision = true_positive / max(1.0, true_positive + false_positive)
    recall = true_positive / max(1.0, true_positive + false_negative)
    target_f1 = 2 * precision * recall / max(1e-9, precision + recall)
    target_name = target_names[target_idx]
    target_margin = class_rows[target_name]["margin"]
    return {
        "target": target_name,
        "target_idx": target_idx,
        "target_margin": target_margin,
        "target_margin_z": class_rows[target_name]["margin_z"],
        "specificity_z": class_rows[target_name]["margin_z"] - float(
            np.mean([class_rows[n]["margin_z"] for n in target_names if n != target_name])
        ),
        "target_rank_percentile": float((np.asarray(margins) <= target_margin).mean()),
        "target_centroid_margin_z": class_rows[target_name]["centroid_margin_z"],
        "target_knn_purity_z": class_rows[target_name]["knn_purity_z"],
        "target_effective_rank_z": class_rows[target_name]["effective_rank_z"],
        "target_knn_purity": class_rows[target_name]["knn_purity"],
        "target_f1": float(target_f1),
        "accuracy": accuracy,
        "class_metrics": class_rows,
    }


@app.function(
    image=IMAGE,
    # Stable PyTorch 2.7 wheels used here support Hopper (H100/H200) but not
    # Blackwell sm_100 kernels, so B200 is intentionally excluded.
    gpu=["H200", "H100"],
    timeout=7200,
    memory=32768,
    max_containers=1024,
    retries=1,
)
def run_cell(arg: dict[str, Any]) -> list[dict[str, Any]]:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import AutoModel, AutoTokenizer

    torch.set_float32_matmul_precision("high")
    seed = int(arg["seed"])
    model_id = arg["model_id"]
    objective = arg["objective"]
    condition = arg["condition"]
    target_idx = int(arg.get("target_idx", 0))
    steps = int(arg["steps"])
    batch_size = int(arg["batch_size"])
    max_length = int(arg["max_length"])
    geom_dim = int(arg["geom_dim"])
    concern_weight = float(arg["concern_weight"])
    train_per_class = int(arg["train_per_class"])
    test_per_class = int(arg["test_per_class"])
    allow_fallback = bool(arg["allow_fallback"])
    k_neighbors = int(arg["k_neighbors"])
    jepa_lambda = float(arg["jepa_lambda"])

    torch.manual_seed(seed)
    np_rng = np.random.default_rng(seed + 17 * (target_idx + 1))
    device = "cuda" if torch.cuda.is_available() else "cpu"

    data = _load_dataset(seed, train_per_class, test_per_class, allow_fallback)
    target_names = data["target_names"]
    n_classes = len(target_names)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    train_tok = tokenizer(
        data["train_texts"],
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    test_tok = tokenizer(
        data["test_texts"],
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    train_labels = torch.tensor(data["train_labels"], dtype=torch.long)
    test_labels = torch.tensor(data["test_labels"], dtype=torch.long)

    weights = torch.ones(len(train_labels), dtype=torch.float32)
    if condition == "concern":
        weights[train_labels == target_idx] = concern_weight
    elif condition == "random_matched":
        target_count = int((train_labels == target_idx).sum().item())
        chosen = np_rng.choice(len(train_labels), size=target_count, replace=False)
        weights[torch.tensor(chosen, dtype=torch.long)] = concern_weight
    weights = weights / weights.mean()

    label_to_indices = {
        c: np.flatnonzero(np.asarray(data["train_labels"], dtype=int) == c)
        for c in range(n_classes)
    }

    class SemanticModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.encoder = AutoModel.from_pretrained(model_id)
            hidden = int(self.encoder.config.hidden_size)
            self.geom = nn.Sequential(
                nn.Linear(hidden, geom_dim),
                nn.GELU(),
                nn.LayerNorm(geom_dim),
            )
            self.classifier = nn.Linear(geom_dim, n_classes)
            self.predictor = nn.Sequential(
                nn.Linear(geom_dim, geom_dim),
                nn.GELU(),
                nn.Linear(geom_dim, geom_dim),
            )

        def embed(self, input_ids, attention_mask):
            out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
            pooled = _mean_pool(out.last_hidden_state, attention_mask)
            return F.normalize(self.geom(pooled), dim=-1)

        def forward(self, input_ids, attention_mask):
            z = self.embed(input_ids, attention_mask)
            return self.classifier(z), z

    model = SemanticModel().to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=float(arg["lr"]), weight_decay=0.01)

    train_ids = train_tok["input_ids"]
    train_mask = train_tok["attention_mask"]
    all_indices = np.arange(len(train_labels))
    final_loss = math.inf
    for _ in range(steps):
        batch_idx = np_rng.choice(all_indices, size=batch_size, replace=True)
        xb = train_ids[batch_idx].to(device)
        mb = train_mask[batch_idx].to(device)
        yb = train_labels[batch_idx].to(device)
        wb = weights[batch_idx].to(device)
        logits, z = model(xb, mb)
        ce = F.cross_entropy(logits, yb, reduction="none")
        loss = (wb * ce).mean()
        if objective == "jepa":
            pos_idx = []
            for y_val in yb.detach().cpu().numpy():
                choices = label_to_indices[int(y_val)]
                pos_idx.append(int(np_rng.choice(choices)))
            pos_idx_arr = np.asarray(pos_idx, dtype=int)
            xp = train_ids[pos_idx_arr].to(device)
            mp = train_mask[pos_idx_arr].to(device)
            with torch.no_grad():
                z_pos = model.embed(xp, mp)
            pred = F.normalize(model.predictor(z), dim=-1)
            pred_loss = 1.0 - (pred * z_pos).sum(-1)
            loss = loss + jepa_lambda * (wb * pred_loss).mean()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        final_loss = float(loss.detach().cpu().item())

    model.eval()
    zs = []
    logits_all = []
    with torch.no_grad():
        for start in range(0, len(test_labels), batch_size):
            sl = slice(start, start + batch_size)
            logits, z = model(test_tok["input_ids"][sl].to(device), test_tok["attention_mask"][sl].to(device))
            zs.append(z.detach().cpu())
            logits_all.append(logits.detach().cpu())
    embeddings = torch.cat(zs, 0).numpy()
    logits_np = torch.cat(logits_all, 0).numpy()

    targets = range(n_classes) if condition == "uniform" else [target_idx]
    rows = []
    for t_idx in targets:
        metrics = _class_metrics(
            embeddings,
            data["test_labels"],
            logits_np,
            int(t_idx),
            target_names,
            k_neighbors,
        )
        rows.append({
            "model_id": model_id,
            "model_slug": _slug(model_id),
            "objective": objective,
            "condition": condition,
            "seed": seed,
            "target": metrics["target"],
            "target_idx": int(t_idx),
            "dataset_kind": data["dataset_kind"],
            "train_per_class": train_per_class,
            "test_per_class": test_per_class,
            "steps": steps,
            "batch_size": batch_size,
            "geom_dim": geom_dim,
            "concern_weight": concern_weight,
            "final_loss": final_loss,
            **metrics,
        })
    return rows


def _parse_csv(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


@app.local_entrypoint()
def main(
    seeds: int = 64,
    steps: int = 90,
    batch_size: int = 32,
    train_per_class: int = 96,
    test_per_class: int = 96,
    max_length: int = 160,
    geom_dim: int = 32,
    concern_weight: float = 8.0,
    lr: float = 2e-5,
    jepa_lambda: float = 0.35,
    k_neighbors: int = 8,
    base_seed: int = 20260702,
    models: str = ",".join(DEFAULT_MODELS),
    objectives: str = "classifier,jepa",
    allow_fallback: bool = False,
    target_se: float = 0.02,
    out: str = "artifacts/semantic_concern_geometry/semantic_concern_sweep_2026_07_02.json",
):
    model_list = _parse_csv(models)
    objective_list = _parse_csv(objectives)
    cells: list[dict[str, Any]] = []
    common = {
        "steps": steps,
        "batch_size": batch_size,
        "train_per_class": train_per_class,
        "test_per_class": test_per_class,
        "max_length": max_length,
        "geom_dim": geom_dim,
        "concern_weight": concern_weight,
        "lr": lr,
        "jepa_lambda": jepa_lambda,
        "k_neighbors": k_neighbors,
        "allow_fallback": allow_fallback,
    }
    for model_id in model_list:
        for objective in objective_list:
            for seed_i in range(seeds):
                seed = base_seed + seed_i
                cells.append({
                    **common,
                    "model_id": model_id,
                    "objective": objective,
                    "condition": "uniform",
                    "seed": seed,
                    "target_idx": 0,
                })
                for target_idx in range(len(REGISTERED_CATEGORIES)):
                    for condition in ("concern", "random_matched"):
                        cells.append({
                            **common,
                            "model_id": model_id,
                            "objective": objective,
                            "condition": condition,
                            "seed": seed,
                            "target_idx": target_idx,
                        })
    print(
        "[semantic-concern] dispatching "
        f"{len(cells)} cells; models={model_list}; objectives={objective_list}; "
        f"seeds={seeds}; steps={steps}; target_se={target_se}"
    )
    chunks = [chunk for chunk in run_cell.map(cells) if chunk]
    rows = [row for chunk in chunks for row in chunk]
    payload = {
        "kind": "semantic concern geometry sweep",
        "manifest": {
            "models": model_list,
            "objectives": objective_list,
            "registered_categories": REGISTERED_CATEGORIES,
            "seeds": seeds,
            "base_seed": base_seed,
            "steps": steps,
            "batch_size": batch_size,
            "train_per_class": train_per_class,
            "test_per_class": test_per_class,
            "max_length": max_length,
            "geom_dim": geom_dim,
            "concern_weight": concern_weight,
            "lr": lr,
            "jepa_lambda": jepa_lambda,
            "k_neighbors": k_neighbors,
            "allow_fallback": allow_fallback,
            "target_bootstrap_se": target_se,
        },
        "rows": rows,
    }
    op = Path(out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"[semantic-concern] wrote {op}")
    print(
        "[semantic-concern] next: python scripts/summarize_semantic_concern_sweep.py "
        f"--input {op} --report experiments/semantic_concern_geometry/results/"
        "semantic_concern_sweep_2026_07_02.md"
    )


if __name__ == "__main__":
    main()
