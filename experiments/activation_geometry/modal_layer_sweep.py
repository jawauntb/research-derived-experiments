#!/usr/bin/env python3
"""Modal entrypoint for sweeping activation-geometry metrics across layers."""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

modal = importlib.import_module("modal")


DEFAULT_MODEL_ID = "EleutherAI/pythia-70m-deduped"
DEFAULT_LAYERS = "0,1,2,3,4,5,6"
IMAGE = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch>=2.5,<2.8",
    "transformers>=4.46,<5.0",
    "accelerate>=1.0,<2.0",
    "safetensors>=0.4,<1.0",
)

app = modal.App(name="research-derived-activation-layer-sweep")


@app.function(image=IMAGE, timeout=1800)
def extract_layer_sweep_remote(
    records: list[dict[str, Any]],
    model_id: str,
    layers: list[int],
    batch_size: int,
    max_length: int,
) -> dict[str, list[list[float]]]:
    torch = importlib.import_module("torch")
    transformers = importlib.import_module("transformers")

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    token = os.environ.get("HUGGINGFACE_TOKEN") or os.environ.get("HF_TOKEN") or None
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, token=token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.bfloat16 if device.type == "cuda" else torch.float32,
        token=token,
    )
    model.to(device)
    model.eval()

    activations_by_layer: dict[str, list[list[float]]] = {
        str(layer): [] for layer in layers
    }
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        encoded = tokenizer(
            [str(record["text"]) for record in batch],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        encoded = {name: value.to(device) for name, value in encoded.items()}
        with torch.inference_mode():
            outputs = model(**encoded, output_hidden_states=True, use_cache=False)
        hidden_states = outputs.hidden_states
        for layer in layers:
            if not -len(hidden_states) <= layer < len(hidden_states):
                raise ValueError(
                    f"Layer {layer} is outside hidden-state range "
                    f"[-{len(hidden_states)}, {len(hidden_states) - 1}]"
                )
            hidden = hidden_states[layer]
            mask = encoded["attention_mask"].to(hidden.device).unsqueeze(-1).type_as(hidden)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            activations_by_layer[str(layer)].extend(pooled.float().cpu().tolist())
    return activations_by_layer


@app.local_entrypoint()
def main(
    concepts: str = "experiments/concept_geometry/concept_set.json",
    paraphrases: str = "experiments/concept_geometry/concept_paraphrases.json",
    model_id: str = DEFAULT_MODEL_ID,
    layers: str = DEFAULT_LAYERS,
    batch_size: int = 8,
    max_length: int = 96,
    top_k: int = 3,
    out: str = "artifacts/activation_geometry/modal_pythia_70m_layer_sweep.json",
) -> None:
    resolved_path = Path(__file__).resolve()
    repo_root = resolved_path.parents[2] if len(resolved_path.parents) > 2 else Path.cwd()
    if str(repo_root) not in sys.path:
        sys.path.append(str(repo_root))
    from experiments.activation_geometry.activation_geometry_probe import (
        ActivationRecord,
        activation_records,
        load_concepts,
        parse_layers,
        payload_from_layer_activations,
        public_summary,
        write_payload,
    )

    parsed_layers = parse_layers(layers)
    concept_rows = load_concepts(Path(concepts))
    records = activation_records(concept_rows, Path(paraphrases))
    serializable_records = [
        {
            "id": record.id,
            "concept_id": record.concept_id,
            "label": record.label,
            "category": record.category,
            "variant_index": record.variant_index,
            "text": record.text,
        }
        for record in records
    ]
    layer_activations = extract_layer_sweep_remote.remote(
        serializable_records,
        model_id,
        parsed_layers,
        batch_size,
        max_length,
    )
    payload = payload_from_layer_activations(
        concepts=concept_rows,
        records=[
            ActivationRecord(
                id=str(record["id"]),
                concept_id=str(record["concept_id"]),
                label=str(record["label"]),
                category=str(record["category"]),
                variant_index=int(record["variant_index"]),
                text=str(record["text"]),
            )
            for record in serializable_records
        ],
        layer_activations=layer_activations,
        model_id=model_id,
        backend="modal-transformers",
        top_k=top_k,
        dry_run=False,
    )
    write_payload(Path(out), payload)
    print(json.dumps(public_summary(payload), indent=2, sort_keys=True))


if __name__ == "__main__":
    print(
        "Run with: modal run experiments/activation_geometry/modal_layer_sweep.py",
        file=sys.stderr,
    )
